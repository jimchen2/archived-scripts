"""High-level, jitted environment interface."""

from __future__ import annotations

from collections.abc import Sequence

import jax
import jax.numpy as jnp
import numpy as np

from . import engine
from .config import NUM_PLAYERS, EnvConfig
from .maps import MapPool, generate_pool, parse_rows
from .obs import Observation, batch_observation, observation
from .state import State
from .tables import Tables, build_tables


class GeneralsEnv:
    """A fast, fully jittable 1v1 generals.io environment.

    Example
    -------
    >>> import jax, jax.numpy as jnp
    >>> from game import GeneralsEnv
    >>> env = GeneralsEnv()
    >>> state = env.reset(jax.random.PRNGKey(0))
    >>> mask = env.action_mask(state)          # (2, num_actions) bool
    >>> actions = env.sample_actions(jax.random.PRNGKey(1), state)
    >>> state, reward, info = env.step(state, actions)

    Parameters
    ----------
    config:
        Static :class:`~game.EnvConfig`.
    map_pool_size:
        If non-zero, pre-generate this many maps and draw episode maps from
        that pool instead of generating a fresh map on every reset. This makes
        ``auto_reset`` almost free (a fresh random map costs ~25us on CPU).
    seed:
        Seed used to build the map pool.
    """

    def __init__(
        self,
        config: EnvConfig | None = None,
        map_pool_size: int = 0,
        seed: int = 0,
    ):
        self.config = config or EnvConfig()
        self.tables: Tables = build_tables(self.config)
        cfg, tables = self.config, self.tables

        self.map_pool: MapPool | None = None
        if map_pool_size:
            self.map_pool = generate_pool(
                map_pool_size, cfg, tables, jax.random.PRNGKey(seed)
            )

        if self.map_pool is None:
            reset_fn = lambda key: engine.reset(key, cfg, tables, None)
            self._reset = jax.jit(reset_fn)
            self._reset_batch = jax.jit(jax.vmap(reset_fn))
        else:
            reset_fn = lambda key, pool: engine.reset(key, cfg, tables, pool)
            self._reset = jax.jit(reset_fn)
            self._reset_batch = jax.jit(jax.vmap(reset_fn, in_axes=(0, None)))
        self._step = jax.jit(lambda s, a: engine.step(s, a, cfg, tables))
        self._mask = jax.jit(lambda s: engine.action_mask(s, cfg, tables))
        self._step_auto = jax.jit(lambda s, a: self._step_auto_impl(s, a))
        self._step_batch = jax.jit(
            lambda s, a, auto: self._step_batch_impl(s, a, auto),
            static_argnums=(2,),
        )
        self._obs = jax.jit(lambda s: batch_observation(s, cfg, tables))
        self._obs_batch = jax.jit(
            jax.vmap(lambda s: batch_observation(s, cfg, tables))
        )

    # ------------------------------------------------------------------ core
    @property
    def num_actions(self) -> int:
        return self.config.num_actions

    @property
    def num_players(self) -> int:
        return NUM_PLAYERS

    def reset(self, key: jax.Array) -> State:
        """Start a new game (random map, or one drawn from the map pool)."""
        if self.map_pool is None:
            return self._reset(key)
        return self._reset(key, self.map_pool)

    def step(self, state: State, actions: jax.Array, auto_reset: bool = False):
        """Advance one half-turn (one simultaneous action per player).

        Two calls complete one displayed turn. ``actions`` is a ``(2,)`` int32
        array. ``action = src * dir_actions + dir`` where ``dir`` is 0 for pass,
        1..4 for up/down/left/right (and 5..8 for the half-army variants when
        ``config.half_moves`` is on).

        Illegal actions pass. Returns ``(state, rewards, info)``; ``rewards`` is
        only non-zero on the transition that ends the episode.
        """
        if auto_reset:
            return self._step_auto(state, actions)
        return self._step(state, actions)

    def action_mask(self, state: State) -> jax.Array:
        """``(2, num_actions)`` boolean mask of legal actions."""
        return self._mask(state)

    def sample_actions(self, key: jax.Array, state: State) -> jax.Array:
        """Uniformly sample one legal action per player."""
        return engine.sample_actions(key, self._mask(state), self.config)

    def sample_actions_batch(self, key: jax.Array, states: State) -> jax.Array:
        """Uniformly sample legal actions for a batch of states -> ``(B, 2)``."""
        masks = jax.vmap(self._mask)(states)
        return engine.sample_actions_batch(key, masks, self.config)

    def observe(self, state: State, player: int) -> Observation:
        """Fog-of-war observation for a single player."""
        return observation(state, player, self.config, self.tables)

    def observations(self, state: State) -> Observation:
        """Both players' observations, stacked on a leading axis."""
        return self._obs(state)

    def observations_batch(self, states: State) -> Observation:
        """Batched observations: ``(B, 2, C, H, W)`` grids and ``(B, 2, S)``."""
        return self._obs_batch(states)

    # ------------------------------------------------------- vectorised sugar
    def reset_batch(self, keys: jax.Array) -> State:
        """``keys``: ``(B,)`` PRNG keys -> batched ``State``."""
        if self.map_pool is None:
            return self._reset_batch(keys)
        return self._reset_batch(keys, self.map_pool)

    def step_batch(
        self, states: State, actions: jax.Array, auto_reset: bool = True
    ):
        """Batched half-turn step with ``auto_reset`` on by default.

        ``actions`` is ``(B, 2)``, rewards come back as ``(B, 2)``. Finished
        environments are restarted from a fresh map (or from the pool), and
        ``info`` still describes the transition that just happened, so the
        terminal reward and winner are not lost.
        """
        return self._step_batch(states, actions, auto_reset)

    # ------------------------------------------------------------- utilities
    def _reset_keys(self, keys: jax.Array) -> State:
        if self.map_pool is None:
            return self._reset_batch(keys)
        return self._reset_batch(keys, self.map_pool)

    def reset_where(self, states: State, done: jax.Array) -> State:
        """Restart the environments whose ``done`` flag is true.

        Public version of the auto-reset used by :meth:`step_batch`.  Useful
        when a trainer wants to inspect the terminal state *before* it is
        replaced (for example to compute reward shaping potentials).
        """
        return self._batch_auto_reset(states, done)

    def _batch_auto_reset(self, states: State, done: jax.Array) -> State:
        keys = jax.vmap(lambda k: jax.random.split(k, 2)[0])(states.key)
        fresh = self._reset_keys(keys)
        keep_shape = lambda x: done.reshape((-1,) + (1,) * (x.ndim - 1))
        return jax.tree_util.tree_map(
            lambda f, s: jnp.where(keep_shape(f), f, s), fresh, states
        )

    def _step_auto_impl(self, state: State, actions: jax.Array):
        new_state, rewards, info = engine.step(state, actions, self.config, self.tables)

        def _reset_now(_):
            sub = jax.random.split(new_state.key, 2)[0]
            if self.map_pool is None:
                fresh = engine.reset(sub, self.config, self.tables, None)
            else:
                fresh = engine.reset(sub, self.config, self.tables, self.map_pool)
            return fresh

        new_state = jax.lax.cond(new_state.done, _reset_now, lambda _: new_state, None)
        return new_state, rewards, info

    def _step_batch_impl(self, states: State, actions: jax.Array, auto_reset: bool):
        step = jax.vmap(
            lambda s, a: engine.step(s, a, self.config, self.tables)
        )
        new_states, rewards, info = step(states, actions)
        if auto_reset:
            # Batch-level condition: the (expensive) map generation only runs on
            # turns where at least one episode actually finished.
            new_states = jax.lax.cond(
                jnp.any(info["done"]),
                lambda _: self._batch_auto_reset(new_states, info["done"]),
                lambda _: new_states,
                None,
            )
        return new_states, rewards, info

    def make_state(
        self, rows: Sequence[str], turn: int = 0, half_turn: int = 0
    ) -> State:
        """Build an explicit (non-random) state from an ASCII layout.

        ``turn`` counts completed displayed turns and ``half_turn`` selects the
        next action slot (0 or 1). See :func:`game.maps.parse_rows` for the
        token grammar. The layout must match the configured board size.
        """
        if half_turn not in (0, 1):
            raise ValueError("half_turn must be 0 or 1")
        parsed = parse_rows(rows)
        if parsed["owner"].shape != (self.config.height, self.config.width):
            raise ValueError(
                f"layout is {parsed['owner'].shape}, env expects "
                f"{(self.config.height, self.config.width)}"
            )
        return State(
            army=parsed["army"],
            owner=parsed["owner"],
            city=parsed["city"],
            general=parsed["general"],
            alive=jnp.ones((NUM_PLAYERS,), dtype=bool),
            turn=jnp.int32(turn),
            half_turn=jnp.int32(half_turn),
            winner=jnp.int32(-1),
            done=jnp.zeros((), dtype=bool),
            key=jax.random.PRNGKey(0),
        )


def make_env(**kwargs) -> GeneralsEnv:
    """Shorthand: ``make_env(height=9, width=9, fog=False)``."""
    return GeneralsEnv(EnvConfig(**kwargs))


def to_numpy(state: State) -> dict:
    """Convert a (possibly batched) state to numpy for inspection."""
    return {k: np.asarray(v) for k, v in state._asdict().items()}


def from_numpy(d: dict) -> State:
    """Inverse of :func:`to_numpy`."""
    return State(
        army=jnp.asarray(d["army"], dtype=jnp.int32),
        owner=jnp.asarray(d["owner"], dtype=jnp.int32),
        city=jnp.asarray(d["city"], dtype=bool),
        general=jnp.asarray(d["general"], dtype=jnp.int32),
        alive=jnp.asarray(d["alive"], dtype=bool),
        turn=jnp.asarray(d["turn"], dtype=jnp.int32),
        half_turn=jnp.asarray(d.get("half_turn", 0), dtype=jnp.int32),
        winner=jnp.asarray(d["winner"], dtype=jnp.int32),
        done=jnp.asarray(d["done"], dtype=bool),
        key=jnp.asarray(d["key"]),
    )
