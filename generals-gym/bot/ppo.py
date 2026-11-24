"""Proximal Policy Optimisation (PPO) for the generals.io agent.

The implementation is deliberately small and self-contained:

* **GAE** (`compute_gae`) with per-trajectory bootstrapping,
* a **clipped surrogate** policy loss plus a clipped value loss and an
  entropy bonus,
* **AdamW** written in pure JAX (no optax dependency),
* a **scan-based update loop** so any number of epochs/minibatches compiles
  into a single device program.

The recurrent (ConvGRU) and frame-stacking variants are handled by
``net.sequence_forward``, which recomputes the memory from the stored
observations during every PPO epoch.  That keeps the trajectory buffer small
(no per-step hidden states) at the cost of one extra forward pass per epoch.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import NamedTuple

import jax
import jax.numpy as jnp

from .network import Memory, PolicyValueNet

LR_SCHEDULES = ("linear", "cosine", "constant")

# ---------------------------------------------------------------------------
# configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PPOConfig:
    """PPO + optimiser hyper-parameters."""

    num_envs: int = 64
    rollout_len: int = 32
    epochs: int = 4
    num_minibatches: int = 4

    lr: float = 3e-4
    lr_end: float = 0.0
    lr_schedule: str = "linear"
    lr_warmup_updates: int = 0
    betas: tuple[float, float] = (0.9, 0.999)
    eps: float = 1e-8
    weight_decay: float = 0.0

    gamma: float = 0.995
    gae_lambda: float = 0.95
    clip_eps: float = 0.2
    clip_value: bool = True
    ent_coef: float = 0.001
    vf_coef: float = 0.5
    max_grad_norm: float = 0.5
    normalize_advantage: bool = True
    # Gradient checkpointing for BPTT through the rollout scan.  Leave on for
    # large backbones (64+ channels on 21x21); turn off to double the speed
    # on small models where activation memory is not a constraint.
    remat: bool = True

    def __post_init__(self) -> None:
        if self.lr_schedule not in LR_SCHEDULES:
            raise ValueError(
                f"lr_schedule must be one of {LR_SCHEDULES}, got {self.lr_schedule!r}"
            )
        if self.lr < 0 or self.lr_end < 0:
            raise ValueError("lr and lr_end must be non-negative")
        if self.lr_warmup_updates < 0:
            raise ValueError("lr_warmup_updates must be non-negative")


def scheduled_lr(
    update_idx: int,
    total_updates: int,
    lr: float,
    schedule: str = "linear",
    lr_end: float = 0.0,
    warmup_updates: int = 0,
) -> float:
    """Return the AdamW learning rate for 1-indexed ``update_idx``.

    ``lr`` is the starting (peak) learning rate.  With ``warmup_updates > 0``
    the rate ramps linearly up to ``lr`` over the first ``warmup_updates``
    updates, then decays toward ``lr_end`` according to ``schedule``
    (``"linear"``, ``"cosine"`` or ``"constant"``).
    """
    if schedule not in LR_SCHEDULES:
        raise ValueError(
            f"lr_schedule must be one of {LR_SCHEDULES}, got {schedule!r}"
        )
    if lr < 0 or lr_end < 0:
        raise ValueError("lr and lr_end must be non-negative")
    if warmup_updates < 0:
        raise ValueError("lr_warmup_updates must be non-negative")

    if warmup_updates > 0 and update_idx <= warmup_updates:
        return float(lr * max(1, update_idx) / warmup_updates)

    if schedule == "constant":
        return float(lr)

    if warmup_updates > 0:
        decay_updates = max(1, total_updates - warmup_updates + 1)
        step = max(0, update_idx - warmup_updates)
    else:
        decay_updates = max(1, total_updates)
        step = max(0, update_idx - 1)

    progress = min(1.0, step / decay_updates)
    if schedule == "linear":
        factor = 1.0 - progress
    else:  # "cosine"
        factor = 0.5 * (1.0 + math.cos(math.pi * progress))
    return float(lr_end + (lr - lr_end) * factor)


# ---------------------------------------------------------------------------
# AdamW
# ---------------------------------------------------------------------------


class OptState(NamedTuple):
    step: jax.Array
    mu: dict
    nu: dict


class TrainState(NamedTuple):
    params: dict
    opt: OptState
    key: jax.Array


def adamw_init(params: dict) -> OptState:
    return OptState(
        step=jnp.zeros((), dtype=jnp.int32),
        mu=jax.tree_util.tree_map(jnp.zeros_like, params),
        nu=jax.tree_util.tree_map(jnp.zeros_like, params),
    )


def init_train_state(net: PolicyValueNet, key: jax.Array) -> TrainState:
    k_init, k_train = jax.random.split(key)
    params = net.init(k_init)
    return TrainState(params=params, opt=adamw_init(params), key=k_train)


def adamw_update(
    grads: dict,
    opt: OptState,
    params: dict,
    cfg: PPOConfig,
    lr: float | jax.Array | None = None,
):
    """One AdamW step, applied leaf-wise to a parameter pytree."""
    beta1, beta2 = cfg.betas
    step = opt.step + 1
    step_lr = cfg.lr if lr is None else lr

    mu = jax.tree_util.tree_map(lambda g, m: beta1 * m + (1 - beta1) * g, grads, opt.mu)
    nu = jax.tree_util.tree_map(
        lambda g, v: beta2 * v + (1 - beta2) * jnp.square(g), grads, opt.nu
    )

    def apply(m, v, p):
        m_hat = m / (1 - beta1 ** step)
        v_hat = v / (1 - beta2 ** step)
        update = m_hat / (jnp.sqrt(v_hat) + cfg.eps)
        if cfg.weight_decay:
            update = update + cfg.weight_decay * p
        return p - step_lr * update

    new_params = jax.tree_util.tree_map(apply, mu, nu, params)
    return new_params, OptState(step=step, mu=mu, nu=nu)


def clip_grad_global_norm(grads: dict, max_norm: float):
    """Scale gradients so their global L2 norm is at most ``max_norm``."""
    total = sum(jnp.sum(jnp.square(g)) for g in jax.tree_util.tree_leaves(grads))
    gnorm = jnp.sqrt(total)
    scale = jnp.minimum(1.0, max_norm / (gnorm + 1e-6))
    clipped = jax.tree_util.tree_map(lambda g: g * scale, grads)
    return clipped, gnorm


# ---------------------------------------------------------------------------
# GAE
# ---------------------------------------------------------------------------


def compute_gae(
    rewards: jax.Array,
    values: jax.Array,
    last_values: jax.Array,
    dones: jax.Array,
    gamma: float,
    gae_lambda: float,
) -> tuple[jax.Array, jax.Array]:
    """Generalised Advantage Estimation.

    Parameters
    ----------
    rewards, values, dones:
        ``(T, N)`` arrays.  ``dones[t]`` marks transitions that ended an
        episode; no bootstrapping happens across such a boundary.
    last_values:
        ``(N,)`` value of the state *after* the last stored step, already
        multiplied by ``(1 - dones[-1])`` by the caller.

    Returns ``(advantages, returns)`` of shape ``(T, N)``.
    """
    next_values = jnp.concatenate([values[1:], last_values[None]], axis=0)

    def body(adv_next, inputs):
        reward, value, next_value, done = inputs
        not_done = 1.0 - done
        delta = reward + gamma * next_value * not_done - value
        adv = delta + gamma * gae_lambda * not_done * adv_next
        return adv, adv

    _, advantages = jax.lax.scan(
        body,
        jnp.zeros_like(last_values),
        (rewards, values, next_values, dones.astype(jnp.float32)),
        reverse=True,
    )
    return advantages, advantages + values


# ---------------------------------------------------------------------------
# trajectory / batch containers
# ---------------------------------------------------------------------------


class Trajectory(NamedTuple):
    """A rollout produced by the collector.

    All arrays have a leading ``(T, B, P)`` layout (time, environment, player),
    except ``lengths`` which is ``(T, B)`` (the turn count of a finishing game).
    """

    grids: jax.Array        # (T, B, P, C, H, W)
    scalars: jax.Array      # (T, B, P, S)
    masks: jax.Array        # (T, B, P, A)
    actions: jax.Array      # (T, B, P)
    log_probs: jax.Array    # (T, B, P)
    values: jax.Array       # (T, B, P)
    rewards: jax.Array      # (T, B, P)
    dones: jax.Array        # (T, B, P)
    lengths: jax.Array      # (T, B)
    initial_memory: Memory | None = None  # (B, P, ...)


class PPOBatch(NamedTuple):
    """Flattened ``(T, N)`` batch fed to the PPO update (``N = B * P``)."""

    grids: jax.Array
    scalars: jax.Array
    masks: jax.Array
    actions: jax.Array
    old_log_probs: jax.Array
    old_values: jax.Array
    advantages: jax.Array
    returns: jax.Array
    dones: jax.Array
    initial_memory: Memory | None = None  # (1, N, ...)


def make_batch(
    traj: Trajectory,
    last_values: jax.Array,
    cfg: PPOConfig,
) -> PPOBatch:
    """Flatten ``(T, B, P)`` trajectories to ``(T, B*P)`` and run GAE."""
    t, b, p = traj.actions.shape
    n = b * p

    def flat(x):
        return x.reshape((t, n) + x.shape[3:])

    last = last_values.reshape((n,))
    dones = flat(traj.dones).astype(jnp.float32)
    advantages, returns = compute_gae(
        flat(traj.rewards), flat(traj.values), last, dones,
        cfg.gamma, cfg.gae_lambda,
    )
    return PPOBatch(
        grids=flat(traj.grids),
        scalars=flat(traj.scalars),
        masks=flat(traj.masks),
        actions=flat(traj.actions),
        old_log_probs=flat(traj.log_probs),
        old_values=flat(traj.values),
        advantages=advantages.astype(jnp.float32),
        returns=returns.astype(jnp.float32),
        dones=dones,
        initial_memory=(None if traj.initial_memory is None else
                        jax.tree_util.tree_map(
                            lambda x: x.reshape((1, n) + x.shape[2:]),
                            traj.initial_memory)),
    )


# ---------------------------------------------------------------------------
# loss and update
# ---------------------------------------------------------------------------


def _sequence_outputs(params: dict, net: PolicyValueNet, batch: PPOBatch,
                      remat: bool = True):
    memory = batch.initial_memory
    if memory is None:
        memory = net.batched_initial_memory((batch.actions.shape[1],))
    else:
        memory = jax.tree_util.tree_map(lambda x: x[0], memory)
    return jax.vmap(
        lambda g, s, m, d, a, mem: net.sequence_forward(
            params, g, s, m, d, actions=a, remat=remat, initial_memory=mem
        ), in_axes=(1, 1, 1, 1, 1, 0), out_axes=1
    )(
        batch.grids,
        batch.scalars,
        batch.masks,
        batch.dones.astype(jnp.bool_),
        batch.actions,
        memory,
    )


def ppo_loss(params: dict, net: PolicyValueNet, batch: PPOBatch, cfg: PPOConfig):
    """Clipped PPO objective; returns ``(total_loss, metrics_dict)``."""
    log_probs, values, entropies = _sequence_outputs(
        params, net, batch, remat=cfg.remat
    )

    advantages = batch.advantages
    if cfg.normalize_advantage:
        advantages = (advantages - jnp.mean(advantages)) / (
            jnp.std(advantages) + 1e-8
        )

    log_ratio = log_probs - batch.old_log_probs
    ratio = jnp.exp(log_ratio)
    surr1 = ratio * advantages
    surr2 = jnp.clip(ratio, 1.0 - cfg.clip_eps, 1.0 + cfg.clip_eps) * advantages
    policy_loss = -jnp.mean(jnp.minimum(surr1, surr2))

    if cfg.clip_value:
        value_clipped = batch.old_values + jnp.clip(
            values - batch.old_values, -cfg.clip_eps, cfg.clip_eps
        )
        value_loss = jnp.mean(
            jnp.maximum(
                jnp.square(values - batch.returns),
                jnp.square(value_clipped - batch.returns),
            )
        )
    else:
        value_loss = jnp.mean(jnp.square(values - batch.returns))

    entropy = jnp.mean(entropies)
    total = (
        policy_loss
        + cfg.vf_coef * 0.5 * value_loss
        - cfg.ent_coef * entropy
    )

    metrics = {
        "loss": total,
        "policy_loss": policy_loss,
        "value_loss": value_loss,
        "entropy": entropy,
        # Schulman's k3 estimator: E[(r - 1) - log r] >= 0, cheap and stable.
        "approx_kl": jnp.mean((ratio - 1.0) - log_ratio),
        "clip_frac": jnp.mean(jnp.abs(ratio - 1.0) > cfg.clip_eps),
    }
    return total, metrics


def ppo_update(
    state: TrainState,
    batch: PPOBatch,
    net: PolicyValueNet,
    cfg: PPOConfig,
    lr: float | jax.Array | None = None,
) -> tuple[TrainState, dict]:
    """Run ``epochs * num_minibatches`` PPO gradient steps.

    Minibatches are drawn along the ``N`` axis only; each minibatch keeps its
    full ``T``-step sequences so recurrent memories are reconstructed exactly.
    """
    n = batch.actions.shape[1]
    minibatch_size = max(1, n // cfg.num_minibatches)
    total_steps = cfg.epochs * cfg.num_minibatches
    step_lr = jnp.asarray(cfg.lr if lr is None else lr, dtype=jnp.float32)

    def body(carry: TrainState, _):
        key, sub = jax.random.split(carry.key)
        perm = jax.random.permutation(sub, n)
        idx = perm[:minibatch_size]
        mb = jax.tree_util.tree_map(lambda x: jnp.take(x, idx, axis=1), batch)

        # `net` is closed over (not passed as an argument) so JAX never tries
        # to treat the Python object as a pytree leaf.
        def loss_fn(params: dict):
            return ppo_loss(params, net, mb, cfg)

        (loss, metrics), grads = jax.value_and_grad(loss_fn, has_aux=True)(
            carry.params
        )
        grads, grad_norm = clip_grad_global_norm(grads, cfg.max_grad_norm)
        new_params, new_opt = adamw_update(
            grads, carry.opt, carry.params, cfg, lr=step_lr
        )
        new_state = TrainState(params=new_params, opt=new_opt, key=key)

        metrics = dict(metrics)
        metrics["grad_norm"] = grad_norm
        metrics["loss"] = loss
        metrics["lr"] = step_lr
        return new_state, metrics

    new_state, metrics = jax.lax.scan(body, state, None, length=total_steps)
    return new_state, jax.tree_util.tree_map(jnp.mean, metrics)
