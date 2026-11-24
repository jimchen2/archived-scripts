"""Throughput benchmark for the 1v1 JAX simulator.

Runs fully jitted + vmapped rollouts (policy sampling included) and reports
environment-steps per second.

    python benchmarks/bench.py                       # default sweep
    python benchmarks/bench.py --envs 4096 --steps 200
    python benchmarks/bench.py --size 11 --steps 300  # small-board sweep
    python benchmarks/bench.py --no-auto-reset        # engine only
"""

from __future__ import annotations

import argparse
import time

import jax
import jax.numpy as jnp

from game import EnvConfig, GeneralsEnv
from bot.baselines import greedy_actions
from game.engine import sample_actions_batch


def make_rollout(env, batch, steps, auto_reset, policy_name):
    """Return a jitted ``fn(keys) -> carry`` running ``steps`` half-turns."""

    cfg, tables = env.config, env.tables

    def policy(state, key):
        if policy_name == "greedy":
            # Fog-honest baseline: also makes episodes terminate, so the benchmark
            # measures the simulator rather than the policy.
            return jax.vmap(lambda s: greedy_actions(s, cfg, tables))(state)
        if policy_name == "random":
            masks = jax.vmap(env.action_mask)(state)              # (B, 2, A)
            return sample_actions_batch(key, masks, cfg)
        if policy_name == "pass":
            return jnp.zeros((batch, 2), dtype=jnp.int32)
        raise ValueError(policy_name)

    def body(carry, key):
        state, episodes, turns, wins = carry
        key, pk = jax.random.split(key)
        actions = policy(state, pk)
        state, rewards, info = env.step_batch(state, actions, auto_reset=auto_reset)
        done = info["done"]
        episodes = episodes + done.astype(jnp.int32)
        turns = turns + jnp.where(done, info["turn"], 0)
        wins = wins + jnp.where(done, (info["winner"] == 0).astype(jnp.int32), 0)
        return (state, episodes, turns, wins), info["turn"]

    def run(keys):
        state = env.reset_batch(keys)
        carry = (
            state,
            jnp.zeros((batch,), dtype=jnp.int32),
            jnp.zeros((batch,), dtype=jnp.int32),
            jnp.zeros((batch,), dtype=jnp.int32),
        )
        return jax.lax.scan(body, carry, jax.random.split(keys[0], steps))[0]

    return jax.jit(run)


def benchmark(batch, steps, auto_reset, cfg, pool_size, policy_name):
    env = GeneralsEnv(cfg, map_pool_size=pool_size)
    run = make_rollout(env, batch, steps, auto_reset, policy_name)
    keys = jax.random.split(jax.random.PRNGKey(0), batch)

    t0 = time.perf_counter()
    out = run(keys)                      # compiles and runs
    jax.block_until_ready(out)
    compile_s = time.perf_counter() - t0

    timings = []
    for _ in range(3):
        t0 = time.perf_counter()
        out = run(keys)
        jax.block_until_ready(out)
        timings.append(time.perf_counter() - t0)
    best = min(timings)
    _, episodes, turns, wins = out
    episodes = int(episodes.sum())
    return {
        "steps_per_sec": batch * steps / best,
        "ms_per_step": 1000 * best / steps,
        "compile_s": compile_s,
        "episodes": episodes,
        "mean_length": float(turns.sum()) / max(episodes, 1),
        "p0_win_rate": float(wins.sum()) / max(episodes, 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--envs", type=int, default=None, help="single batch size")
    ap.add_argument("--steps", type=int, default=100)
    ap.add_argument("--size", type=int, default=21, help="board size (NxN)")
    ap.add_argument("--no-auto-reset", action="store_true")
    ap.add_argument("--pool", type=int, default=0, help="map pool size")
    ap.add_argument(
        "--policy", choices=("greedy", "random", "pass"), default="greedy"
    )
    args = ap.parse_args()

    cfg = EnvConfig(height=args.size, width=args.size)
    batches = [args.envs] if args.envs else [1, 32, 256, 1024, 4096]
    auto_reset = not args.no_auto_reset

    print(f"jax {jax.__version__} | {jax.devices()[0]} | "
          f"board {cfg.height}x{cfg.width} | auto_reset={auto_reset} "
          f"| map_pool={args.pool} | policy={args.policy}")
    print(f"{'envs':>6} {'steps/s':>12} {'ms/step':>9} {'episodes':>9} "
          f"{'len':>6} {'P0 win%':>8} {'compile':>8}")
    for b in batches:
        r = benchmark(b, args.steps, auto_reset, cfg, args.pool, args.policy)
        print(
            f"{b:6d} {r['steps_per_sec']:12,.0f} {r['ms_per_step']:9.2f} "
            f"{r['episodes']:9d} {r['mean_length']:6.1f} "
            f"{100 * r['p0_win_rate']:7.1f}% {r['compile_s']:7.1f}s"
        )


if __name__ == "__main__":
    main()
