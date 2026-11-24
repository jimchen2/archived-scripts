"""The agent network: SE-ResNet + global context + ConvGRU + convolutional heads.

This is the architecture described in the project README:

1. **Input encoding** – the 10-channel fogged board plus 7 scalars broadcast to
   ``(H, W)`` (and optionally 2 coordinate channels), concatenated to
   ``(17, H, W)``.
2. **Backbone** – a stack of residual blocks built from 3x3 convolutions with
   LayerNorm and SiLU.  Every block has a Squeeze-and-Excitation gate, and
   every ``global_context_every`` blocks a global-context block concatenates a
   pooled board vector back onto the feature map so 3x3 filters can "see"
   the whole board.
3. **Memory** – a ConvGRU over the backbone features (spatial memory, ideal
   for fog of war), or a frame-stack, or nothing.
4. **Heads** – a fully convolutional policy head (1x1 conv -> one logit per
   ``(tile, direction)``) and a global-average-pooled value head.  The global
   scalars are concatenated into both heads as well as the input, because the
   backbone's LayerNorm would otherwise normalise away their constant planes.

Everything is a pure function of ``(params, arrays)``, so the network can be
used inside ``jax.vmap`` / ``jax.lax.scan`` without any Python state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

import jax
import jax.numpy as jnp

from . import nn

# ---------------------------------------------------------------------------
# configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NetConfig:
    """Static architecture hyper-parameters.

    Attributes
    ----------
    channels:
        Width of the residual backbone (64 or 128 are the usual choices).
    num_blocks:
        Number of residual blocks (6-10 in the README).
    use_se, se_ratio:
        Squeeze-and-Excitation inside each residual block and its reduction
        ratio.
    global_context_every:
        Insert a global-context block after every ``k`` residual blocks
        (0 disables it).
    memory:
        ``"gru"`` (ConvGRU, default), ``"stack"`` (frame-stack the last
        ``stack_frames`` observations) or ``"none"``.
    memory_channels:
        Hidden width of the ConvGRU; 0 means ``channels``.
    stack_frames:
        Number of observations concatenated when ``memory == "stack"``.
    use_coords:
        Append normalised row/column planes to the input.  Off by default to
        match the ``(17, H, W)`` encoding in the README exactly.
    dir_actions:
        Number of direction codes per tile (5, or 9 with half moves).
    """

    channels: int = 64
    num_blocks: int = 6
    use_se: bool = True
    se_ratio: int = 4
    global_context_every: int = 2
    memory: str = "gru"
    memory_channels: int = 0
    stack_frames: int = 4
    use_coords: bool = False
    dir_actions: int = 5

    def __post_init__(self) -> None:
        if self.channels < 1:
            raise ValueError("channels must be >= 1")
        if self.num_blocks < 0:
            raise ValueError("num_blocks must be >= 0")
        if self.memory not in ("none", "gru", "stack"):
            raise ValueError("memory must be 'none', 'gru' or 'stack'")
        if self.memory == "stack" and self.stack_frames < 1:
            raise ValueError("stack_frames must be >= 1")
        if self.dir_actions < 1:
            raise ValueError("dir_actions must be >= 1")

    @property
    def memory_width(self) -> int:
        return self.memory_channels or self.channels


class Memory(NamedTuple):
    """Recurrent state carried between consecutive observations.

    Unused fields are zero-length dummy arrays so the pytree structure is
    identical for every memory mode (which keeps ``jax.jit`` happy).
    """

    hidden: jax.Array   # (C_mem, H, W) for the ConvGRU
    frames: jax.Array   # (k, C_frame, H, W) for frame-stacking


class StepOutput(NamedTuple):
    """Result of a single policy/value evaluation."""

    action: jax.Array
    log_prob: jax.Array
    value: jax.Array
    entropy: jax.Array
    logits: jax.Array
    memory: Memory


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _broadcast_reset(reset: jax.Array, ref: jax.Array) -> jax.Array:
    """Reshape a boolean reset flag so it broadcasts against ``ref``."""
    reset = jnp.asarray(reset, dtype=bool)
    if reset.ndim == 0:
        return reset
    pad = (1,) * (ref.ndim - reset.ndim)
    return reset.reshape(reset.shape + pad)


def reset_memory(memory: Memory, reset: jax.Array) -> Memory:
    """Zero the memory wherever ``reset`` is true (episode boundary)."""
    return jax.tree_util.tree_map(
        lambda x: jnp.where(_broadcast_reset(reset, x), jnp.zeros_like(x), x),
        memory,
    )


def param_count(params: dict) -> int:
    return sum(int(leaf.size) for leaf in jax.tree_util.tree_leaves(params))


# ---------------------------------------------------------------------------
# the network
# ---------------------------------------------------------------------------


class PolicyValueNet:
    """A residual policy/value network for a 1v1 generals.io board.

    Parameters
    ----------
    config:
        :class:`NetConfig` architecture settings.
    grid_channels, num_scalars:
        Number of channels in the observation grid / scalars.  The defaults
        match :mod:`game.obs`.
    height, width:
        Board size.
    """

    def __init__(
        self,
        config: NetConfig | None = None,
        grid_channels: int = 10,
        num_scalars: int = 7,
        height: int = 21,
        width: int = 21,
    ) -> None:
        self.config = config or NetConfig()
        self.grid_channels = grid_channels
        self.num_scalars = num_scalars
        self.height = height
        self.width = width

    # ------------------------------------------------------------ properties
    @property
    def frame_channels(self) -> int:
        """Channels per observation after encoding (grid + scalars + coords)."""
        return self.grid_channels + self.num_scalars + (2 if self.config.use_coords else 0)

    @property
    def input_channels(self) -> int:
        """Channels fed into the stem convolution."""
        if self.config.memory == "stack":
            return self.frame_channels * self.config.stack_frames
        return self.frame_channels

    @property
    def num_actions(self) -> int:
        return self.height * self.width * self.config.dir_actions

    # --------------------------------------------------------------- memory
    def initial_memory(self) -> Memory:
        cfg = self.config
        hidden = (
            jnp.zeros((cfg.memory_width, self.height, self.width), dtype=jnp.float32)
            if cfg.memory == "gru"
            else jnp.zeros((0,), dtype=jnp.float32)
        )
        frames = (
            jnp.zeros((cfg.stack_frames, self.frame_channels, self.height, self.width),
                      dtype=jnp.float32)
            if cfg.memory == "stack"
            else jnp.zeros((0,), dtype=jnp.float32)
        )
        return Memory(hidden=hidden, frames=frames)

    # ---------------------------------------------------------------- init
    def init(self, key: jax.Array) -> dict:
        cfg = self.config
        c = cfg.channels

        k_stem, k_blocks, k_gru, k_policy, k_value = jax.random.split(key, 5)
        params: dict = {
            "stem": {
                "conv": nn.conv_init(k_stem, self.input_channels, c, 3),
                "ln": nn.layer_norm_init(c),
            },
            "blocks": [],
        }

        for i, kb in enumerate(jax.random.split(k_blocks, cfg.num_blocks)):
            ks = jax.random.split(kb, 4)
            block = {
                "c1": nn.conv_init(ks[0], c, c, 3),
                "ln1": nn.layer_norm_init(c),
                "c2": nn.conv_init(ks[1], c, c, 3),
                "ln2": nn.layer_norm_init(c),
            }
            if cfg.use_se:
                block["se"] = nn.se_init(ks[2], c, cfg.se_ratio)
            if cfg.global_context_every and (i + 1) % cfg.global_context_every == 0:
                block["context"] = nn.context_init(ks[3], c)
            params["blocks"].append(block)

        if cfg.memory == "gru":
            params["gru"] = nn.conv_gru_init(k_gru, c, cfg.memory_width)

        kp1, kp2 = jax.random.split(k_policy)
        params["policy"] = {
            "conv1": nn.conv_init(kp1, c, c, 1),
            "ln": nn.layer_norm_init(c),
            # The scalars are concatenated directly into the head: the trunk's
            # LayerNorm would otherwise normalise away their constant planes.
            "conv2": nn.conv_init(kp2, c + self.num_scalars, cfg.dir_actions, 1,
                                  scale=0.01),
        }

        kv1, kv2 = jax.random.split(k_value)
        value_hidden = max(c // 2, 32)
        params["value"] = {
            "ln": nn.layer_norm_vec_init(c + self.num_scalars),
            "w1": nn.dense_init(kv1, c + self.num_scalars, value_hidden),
            "w2": nn.dense_init(kv2, value_hidden, 1, scale=0.01),
        }
        return params

    # ------------------------------------------------------------- encoding
    def encode_frame(self, grid: jax.Array, scalars: jax.Array) -> jax.Array:
        """Build one ``(frame_channels, H, W)`` observation from grid + scalars."""
        planes = [grid]
        for i in range(self.num_scalars):
            planes.append(
                jnp.broadcast_to(scalars[i], (1, self.height, self.width))
            )
        if self.config.use_coords:
            rows = jnp.linspace(-1.0, 1.0, self.height, dtype=jnp.float32)
            cols = jnp.linspace(-1.0, 1.0, self.width, dtype=jnp.float32)
            planes.append(jnp.broadcast_to(rows[:, None], (1, self.height, self.width)))
            planes.append(jnp.broadcast_to(cols[None, :], (1, self.height, self.width)))
        return jnp.concatenate(planes, axis=0)

    def _push_memory(
        self, memory: Memory, grid: jax.Array, scalars: jax.Array
    ) -> tuple[jax.Array, Memory]:
        """Encode an observation and fold it into the memory."""
        frame = self.encode_frame(grid, scalars)
        if self.config.memory == "stack":
            frames = jnp.concatenate([memory.frames[1:], frame[None]], axis=0)
            x = frames.reshape((self.input_channels, self.height, self.width))
            return x, Memory(hidden=memory.hidden, frames=frames)
        return frame, memory

    # ----------------------------------------------------------------- trunk
    def _residual_block(self, p: dict, x: jax.Array) -> jax.Array:
        cfg = self.config
        h = nn.silu(nn.layer_norm(p["ln1"], nn.conv(p["c1"], x)))
        h = nn.layer_norm(p["ln2"], nn.conv(p["c2"], h))
        if cfg.use_se:
            h = nn.se_apply(p["se"], h)
        out = nn.silu(x + h)
        if "context" in p:
            out = nn.context_apply(p["context"], out)
        return out

    def _trunk(self, params: dict, x: jax.Array) -> jax.Array:
        stem = params["stem"]
        h = nn.silu(nn.layer_norm(stem["ln"], nn.conv(stem["conv"], x)))
        for block in params["blocks"]:
            h = self._residual_block(block, h)
        return h

    def _apply_memory(
        self, params: dict, h: jax.Array, memory: Memory
    ) -> tuple[jax.Array, Memory]:
        if self.config.memory == "gru":
            # The GRU output replaces the trunk features, so the heads see the
            # recurrent state rather than only the current frame.
            hidden = nn.conv_gru_apply(params["gru"], h, memory.hidden)
            return hidden, Memory(hidden=hidden, frames=memory.frames)
        return h, Memory(hidden=memory.hidden, frames=memory.frames)

    # ----------------------------------------------------------------- heads
    def _policy_logits(
        self, p: dict, h: jax.Array, mask: jax.Array, scalars: jax.Array
    ) -> jax.Array:
        """Fully convolutional policy head -> flat ``(num_actions,)`` logits.

        The map is transposed to ``(H, W, dir_actions)`` before flattening, so
        flat index ``tile * dir_actions + direction`` matches the simulator's
        action encoding.  The global scalars are broadcast and concatenated
        onto the head input so the policy can condition on board-level state.
        """
        z = nn.silu(nn.layer_norm(p["ln"], nn.conv(p["conv1"], h)))
        s = jnp.broadcast_to(scalars[:, None, None], (self.num_scalars,) + h.shape[1:])
        z = jnp.concatenate([z, s], axis=0)
        logits = nn.conv(p["conv2"], z)                    # (dir, H, W)
        logits = jnp.transpose(logits, (1, 2, 0)).reshape(-1)
        return jnp.where(mask, logits, -1e9)

    def _value(self, p: dict, h: jax.Array, scalars: jax.Array) -> jax.Array:
        z = jnp.mean(h, axis=(1, 2))                       # global average pool
        z = jnp.concatenate([z, scalars], axis=0)          # + board-level state
        z = nn.layer_norm_vec(p["ln"], z)
        z = jax.nn.silu(nn.dense(p["w1"], z))
        return nn.dense(p["w2"], z)[0]

    # ------------------------------------------------------------------ step
    def step(
        self,
        params: dict,
        grid: jax.Array,
        scalars: jax.Array,
        mask: jax.Array,
        memory: Memory,
        *,
        key: jax.Array | None = None,
        sample: bool = True,
        action: jax.Array | None = None,
    ) -> StepOutput:
        """Evaluate one observation.

        With ``sample=True`` an action is drawn from the masked categorical
        distribution (``key`` is required).  With ``sample=False`` the caller
        may supply ``action``; if it is omitted the argmax action is used.
        """
        x, memory = self._push_memory(memory, grid, scalars)
        h = self._trunk(params, x)
        h, memory = self._apply_memory(params, h, memory)
        logits = self._policy_logits(params["policy"], h, mask, scalars)
        value = self._value(params["value"], h, scalars)

        if sample:
            if key is None:
                raise ValueError("key is required when sample=True")
            action = jax.random.categorical(key, logits)
        elif action is None:
            action = jnp.argmax(logits)

        log_probs = jax.nn.log_softmax(logits)
        log_prob = log_probs[action]
        probs = jax.nn.softmax(logits)
        entropy = -jnp.sum(probs * log_probs)

        return StepOutput(
            action=action.astype(jnp.int32),
            log_prob=log_prob,
            value=value,
            entropy=entropy,
            logits=logits,
            memory=memory,
        )

    def value(
        self,
        params: dict,
        grid: jax.Array,
        scalars: jax.Array,
        mask: jax.Array,
        memory: Memory,
    ) -> jax.Array:
        """Value of a single observation (used for GAE bootstrapping)."""
        x, memory = self._push_memory(memory, grid, scalars)
        h = self._trunk(params, x)
        h, _ = self._apply_memory(params, h, memory)
        return self._value(params["value"], h, scalars)

    # -------------------------------------------------------------- sequence
    def sequence_forward(
        self,
        params: dict,
        grids: jax.Array,
        scalars: jax.Array,
        masks: jax.Array,
        dones: jax.Array,
        *,
        actions: jax.Array | None = None,
        key: jax.Array | None = None,
        remat: bool = True,
        initial_memory: Memory | None = None,
    ) -> tuple[jax.Array, jax.Array, jax.Array]:
        """Roll the network over one ``T``-step trajectory.

        Parameters
        ----------
        grids, scalars, masks:
            Observations with a leading time axis ``(T, ...)``.
        dones:
            ``(T,)`` boolean flags.  ``dones[t]`` means the transition *out of*
            step ``t`` ended the episode, so the memory is cleared before
            step ``t + 1`` (matching the simulator's auto-reset).
        actions:
            ``(T,)`` actions to score, or ``None`` to sample.
        key:
            PRNG key used when sampling.

        Returns ``(log_probs, values, entropies)`` each of shape ``(T,)``.
        ``remat`` enables gradient checkpointing (recommended for large
        backbones, where BPTT through the scan would otherwise save every
        layer's activations for every timestep).
        """
        t = grids.shape[0]
        resets = jnp.concatenate(
            [jnp.zeros((1,), dtype=bool), jnp.asarray(dones[:-1], dtype=bool)],
            axis=0,
        )
        sample = actions is None
        if actions is None:
            if key is None:
                raise ValueError("key is required when actions is None")
            keys = jax.random.split(key, t)
            actions = jnp.zeros((t,), dtype=jnp.int32)
        else:
            keys = jnp.zeros((t, 2), dtype=jnp.uint32)

        # Gradient checkpointing: PPO differentiates through the whole T-step
        # scan, which would otherwise save every layer's activations for every
        # timestep.  Rematerialising them in the backward pass trades ~2x
        # compute for O(1) memory in T.  `sample` is closed over (a Python
        # bool), so it stays static under the remat transform.
        def _step(p, g, s, m, mem, k, a):
            return self.step(p, g, s, m, mem, key=k, sample=sample, action=a)

        step_fn = jax.checkpoint(_step) if remat else _step

        def body(carry: Memory, inputs):
            mem = carry
            grid, scalar, mask, action, reset, step_key = inputs
            mem = reset_memory(mem, reset)
            out = step_fn(
                params, grid, scalar, mask, mem, step_key, action
            )
            return out.memory, (out.log_prob, out.value, out.entropy)

        _, (log_probs, values, entropies) = jax.lax.scan(
            body,
            self.initial_memory() if initial_memory is None else initial_memory,
            (grids, scalars, masks, actions, resets, keys),
        )
        return log_probs, values, entropies

    # --------------------------------------------------------------- utility
    def batched_initial_memory(self, batch_shape: tuple[int, ...]) -> Memory:
        """Broadcast the zero memory to ``batch_shape + (C, H, W)``."""
        memory = self.initial_memory()
        return jax.tree_util.tree_map(
            lambda x: jnp.broadcast_to(x, batch_shape + x.shape), memory
        )
