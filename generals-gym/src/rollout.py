"""Rollout collection for PPO.

The collector runs ``num_envs`` games in lockstep inside a single
``jax.lax.scan``. Shared self-play trains both seats; fixed opponents and
historical pool opponents train only seat 0.

Reward shaping
--------------
A generals.io game only rewards the winning general capture, which is far too
sparse for PPO on a 21x21 board.  We add potential-based shaping:

    F(s, s') = shaping_coef * (phi(s') - phi(s)) * (1 - done)

with a state potential built from three terms:

* normalised land difference,
* log-scaled army difference,
* (optionally) the Manhattan distance from the player's territory to the
  enemy general – privileged information the agent cannot see under fog of
  war, but perfectly legal in a reward.

Because it is the difference of a state potential, it does not change the
optimal policy (for gamma < 1) but gives a dense learning signal.  Set
``shaping_coef=0`` for the pure game reward, and ``general_distance_coef=0``
to drop the distance term.
"""

from __future__ import annotations

import jax
import jax.numpy as jnp

from bot.baselines import greedy_actions
from bot.network import Memory, PolicyValueNet, reset_memory
from bot.ppo import Trajectory
from game import EnvConfig, GeneralsEnv, Observation

from .config import TrainConfig
from .opponent_pool import sample_opponents


def _land_army(state) -> tuple[jax.Array, jax.Array]:
    """Per-player land and army totals, summed over the board axes."""
    land = jnp.stack(
        [(state.owner == p).sum(axis=(-2, -1)) for p in range(2)], axis=-1
    )
    army = jnp.stack(
        [jnp.where(state.owner == p, state.army, 0).sum(axis=(-2, -1)) for p in range(2)],
        axis=-1,
    )
    return land, army


def _general_distance(state, tables, player: int) -> jax.Array:
    """Manhattan distance from ``player``'s closest tile to the enemy general."""
    own = (state.owner == player).reshape(state.owner.shape[:-2] + (-1,))
    target = state.general[..., 1 - player]
    dist = jnp.take(tables.distances, target, axis=1)   # (n,) or (n, B)
    if dist.ndim == 2:
        dist = dist.T                                    # (B, n)
    return jnp.where(own, dist, 1e6).min(axis=-1)


def _potential(state, env_cfg: EnvConfig, tables, distance_coef: float) -> jax.Array:
    """Board potential for both players: ``(B, 2)``."""
    land, army = _land_army(state)
    tiles = env_cfg.height * env_cfg.width
    base = land.astype(jnp.float32) / tiles
    base = base + 0.5 * jnp.log1p(army.astype(jnp.float32)) / jnp.log1p(
        env_cfg.army_norm * tiles
    )
    if distance_coef:
        dist = jnp.stack(
            [_general_distance(state, tables, p) for p in range(2)], axis=-1
        ).astype(jnp.float32) / (env_cfg.height + env_cfg.width)
        base = base - distance_coef * dist
    return base


def collect_trajectory(
    env: GeneralsEnv,
    net: PolicyValueNet,
    params: dict,
    states,
    memory: Memory,
    key: jax.Array,
    cfg: TrainConfig,
    env_cfg: EnvConfig,
    pool_params=None,
    pool_count=None,
    opponent_params=None,
):
    """Run ``rollout_len`` half-turns and return the PPO trajectory.

    Returns ``(trajectory, states, memory, last_values)`` where ``states`` and
    ``memory`` are ready for the next rollout and ``last_values`` is the
    bootstrap value of the final state (zero where the episode ended).
    In pool mode, a fifth result contains the per-environment frozen opponent
    parameters, which must be passed back on the next call.
    """
    if cfg.train_opponent == "pool" and (pool_params is None or pool_count is None
                                         or opponent_params is None):
        raise ValueError("pool mode requires pool_params, pool_count and opponent_params")
    num_envs = states.owner.shape[0]
    ppo_cfg = cfg.ppo_config()
    initial_memory = memory

    def actor(grid, scalar, mask, mem, step_key):
        return net.step(params, grid, scalar, mask, mem, key=step_key, sample=True)

    def body(carry, step_key):
        states, memory, active_opponents = carry
        obs: Observation = env.observations_batch(states)      # (B, P, C, H, W)
        masks = jax.vmap(env.action_mask)(states)              # (B, P, A)

        k_agent, _ = jax.random.split(step_key)
        keys = jax.random.split(k_agent, (num_envs, 2))
        out = jax.vmap(jax.vmap(actor))(
            obs.grid, obs.scalars, masks, memory, keys
        )

        # Pool policies have independent parameters and recurrent memory.
        if cfg.train_opponent == "pool":
            opp_out = jax.vmap(lambda p, g, s, m, mem, k: net.step(
                p, g, s, m, mem, key=k, sample=True
            ))(active_opponents, obs.grid[:, 1], obs.scalars[:, 1], masks[:, 1],
               jax.tree_util.tree_map(lambda x: x[:, 1], memory), keys[:, 1])
            next_memory = jax.tree_util.tree_map(
                lambda agent, opponent: agent.at[:, 1].set(opponent),
                out.memory, opp_out.memory)
        else:
            next_memory = out.memory

        # Seat 1 is either the same network (self-play) or a fixed opponent.
        if cfg.train_opponent == "pool":
            opp = opp_out.action
        elif cfg.train_opponent == "random":
            k_opp = jax.random.fold_in(step_key, 1)
            opp = env.sample_actions_batch(k_opp, states)[:, 1]
        elif cfg.train_opponent == "greedy":
            opp = jax.vmap(
                lambda s: greedy_actions(s, env_cfg, env.tables)
            )(states)[:, 1]
        else:
            opp = out.action[:, 1]
        actions = jnp.stack([out.action[:, 0], opp], axis=1)

        pre_potential = _potential(
            states, env_cfg, env.tables, cfg.general_distance_coef
        )
        new_states, rewards, info = env.step_batch(states, actions, auto_reset=False)
        done = info["done"]                                   # (B,)

        post_potential = _potential(
            new_states, env_cfg, env.tables, cfg.general_distance_coef
        )
        shaping = cfg.shaping_coef * (post_potential - pre_potential)
        shaped = rewards + shaping * (1.0 - done.astype(jnp.float32))[:, None]

        # Restart finished games only after the terminal state has been used
        # for the post-step potential.  The batch-level condition keeps map
        # generation off the hot path when no game ended this turn.
        new_states = jax.lax.cond(
            jnp.any(done),
            lambda _: env.reset_where(new_states, done),
            lambda _: new_states,
            None,
        )
        memory = reset_memory(next_memory, done)
        if cfg.train_opponent == "pool":
            fresh = sample_opponents(pool_params, pool_count,
                                     jax.random.fold_in(step_key, 2), num_envs)
            active_opponents = jax.tree_util.tree_map(
                lambda old, new: jnp.where(
                    done.reshape((num_envs,) + (1,) * (old.ndim - 1)), new, old),
                active_opponents, fresh)
        return (new_states, memory, active_opponents), (
            obs.grid,
            obs.scalars,
            masks,
            actions,
            out.log_prob,
            out.value,
            shaped,
            done,
            jnp.where(done, info["turn"], 0),
        )

    (states, memory, opponent_params), outputs = jax.lax.scan(
        body, (states, memory, opponent_params), jax.random.split(key, ppo_cfg.rollout_len)
    )
    grids, scalars, masks, actions, log_probs, values, rewards, dones, lengths = outputs

    traj = Trajectory(
        grids=grids,
        scalars=scalars,
        masks=masks,
        actions=actions,
        log_probs=log_probs,
        values=values,
        rewards=rewards,
        dones=jnp.broadcast_to(dones[:, :, None], rewards.shape),
        lengths=lengths,
        initial_memory=initial_memory,
    )

    # Bootstrap value for the state after the last transition.  When that
    # transition ended the episode the simulator has already reset the state,
    # so the value is masked to zero.
    obs = env.observations_batch(states)
    masks = jax.vmap(env.action_mask)(states)
    final_value = jax.vmap(
        jax.vmap(lambda g, s, m, mem: net.value(params, g, s, m, mem))
    )(obs.grid, obs.scalars, masks, memory)
    last_values = final_value * (1.0 - dones[-1].astype(jnp.float32))[:, None]

    # When training against a fixed opponent, only seat 0's transitions are
    # on-policy, so keep just that player's slice of the trajectory.
    if cfg.train_opponent != "self":
        traj = traj._replace(
            grids=traj.grids[:, :, :1],
            scalars=traj.scalars[:, :, :1],
            masks=traj.masks[:, :, :1],
            actions=traj.actions[:, :, :1],
            log_probs=traj.log_probs[:, :, :1],
            values=traj.values[:, :, :1],
            rewards=traj.rewards[:, :, :1],
            dones=traj.dones[:, :, :1],
            initial_memory=jax.tree_util.tree_map(lambda x: x[:, :1], initial_memory),
        )
        last_values = last_values[:, :1]

    if cfg.train_opponent == "pool":
        return traj, states, memory, last_values, opponent_params
    return traj, states, memory, last_values


def rollout_stats(traj: Trajectory) -> dict:
    """Cheap diagnostics for the logger (computed outside the jit)."""
    dones = traj.dones[:, :, 0]                 # (T, B); identical for both players
    episodes = jnp.maximum(jnp.sum(dones), 1)
    terminal = traj.rewards * traj.dones        # terminal ±1, shaping is 0 there
    stats = {
        "episodes": float(jnp.sum(dones)),
        "mean_length": float(jnp.sum(traj.lengths) / episodes),
        "win_rate_p0": float(jnp.sum(terminal[:, :, 0]) / episodes),
        "mean_reward": float(jnp.mean(traj.rewards)),
    }
    if traj.dones.shape[2] > 1:
        stats["win_rate_p1"] = float(jnp.sum(terminal[:, :, 1]) / episodes)
    return stats
