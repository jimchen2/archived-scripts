"""The canonical vectorised rollout loop (the pattern an RL trainer needs).

Everything below lives inside a single ``jax.lax.scan``: N games run in
lockstep, finished games restart automatically, and only one host<->device
round-trip is made per scan chunk.

    python examples/batched_rollout.py --envs 1024 --steps 200  # half-turns
"""

from __future__ import annotations

import argparse
import time

import jax
import jax.numpy as jnp

from game import EnvConfig, GeneralsEnv
from bot.baselines import greedy_actions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--envs", type=int, default=1024)
    ap.add_argument("--steps", type=int, default=200, help="environment half-turns to scan")
    ap.add_argument("--pool", type=int, default=512, help="map pool size")
    ap.add_argument("--size", type=int, default=21)
    args = ap.parse_args()

    cfg = EnvConfig(height=args.size, width=args.size)
    # A map pool makes auto-reset almost free; use map_pool_size=0 to generate
    # a brand new map for every episode instead.
    env = GeneralsEnv(cfg, map_pool_size=args.pool)

    def rollout(keys):
        """keys: (B,) -> per-env statistics after `steps` half-turns."""
        state = env.reset_batch(keys)

        def body(carry, key):
            state, returns, episodes, wins, lengths = carry
            # 1. observations (fog of war) for the policy
            obs = env.observations_batch(state)              # (B, 2, C, H, W)
            del obs  # (a real trainer feeds `obs` into its policy network)
            # 2. a policy would go here; fog-honest greedy keeps this demo simple
            actions = jax.vmap(lambda s: greedy_actions(s, cfg, env.tables))(state)
            # 3. environment step (with auto-reset of finished games)
            state, rewards, info = env.step_batch(state, actions, auto_reset=True)
            done = info["done"]
            returns = returns * (1.0 - done[:, None]) + rewards
            episodes = episodes + done.astype(jnp.int32)
            wins = wins + jnp.where(done, (info["winner"] == 0), False).astype(jnp.int32)
            lengths = lengths + jnp.where(done, info["turn"], 0)
            return (state, returns, episodes, wins, lengths), (rewards, info["done"])

        init = (
            state,
            jnp.zeros((args.envs, 2), dtype=jnp.float32),
            jnp.zeros((args.envs,), dtype=jnp.int32),
            jnp.zeros((args.envs,), dtype=jnp.int32),
            jnp.zeros((args.envs,), dtype=jnp.int32),
        )
        (state, returns, episodes, wins, lengths), (rewards, dones) = jax.lax.scan(
            body, init, jax.random.split(keys[0], args.steps)
        )
        return {
            "episodes": episodes.sum(),
            "win_rate_p0": wins.sum() / jnp.maximum(episodes.sum(), 1),
            "mean_length": lengths.sum() / jnp.maximum(episodes.sum(), 1),
            "return_p0": returns[:, 0].mean(),
            "obs_shape": jnp.asarray(env.observations_batch(state).grid.shape),
        }

    keys = jax.random.split(jax.random.PRNGKey(0), args.envs)
    run = jax.jit(rollout)

    t0 = time.perf_counter()
    out = jax.block_until_ready(run(keys))              # compile + run
    first = time.perf_counter() - t0

    t0 = time.perf_counter()
    out = jax.block_until_ready(run(keys))
    best = time.perf_counter() - t0

    steps = args.envs * args.steps
    print(f"board {cfg.height}x{cfg.width}, {args.envs} envs, {args.steps} half-turns")
    print(f"compile+run {first:5.1f}s | steady state {best:5.2f}s "
          f"-> {steps / best:,.0f} env-steps/s")
    print(f"episodes finished: {int(out['episodes'])}, "
          f"mean length {float(out['mean_length']):.1f} turns, "
          f"P0 win rate {float(out['win_rate_p0']):.1%}")
    print(f"observation tensor per env: {tuple(int(x) for x in out['obs_shape'])}")


if __name__ == "__main__":
    main()
