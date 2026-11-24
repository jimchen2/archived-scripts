"""Train the generals.io agent with PPO self-play.

Usage
-----
    python -m src.train --preset smoke --total-updates 5
    python -m src.train --preset default --total-updates 2000
    python -m src.train --preset small --memory stack --shaping 0.2

The run directory (default ``runs/<preset>``) contains ``metrics.csv``,
``config.json`` and ``checkpoints/`` (``latest.json`` points at the newest).
Every ``eval_every`` updates the agent is evaluated against the fog-honest
greedy baseline and the win rate is logged.
"""

from __future__ import annotations

import argparse
import time

import jax
import jax.numpy as jnp

from bot.checkpoint import Checkpoint
from bot.network import PolicyValueNet
from bot.ppo import (
    LR_SCHEDULES,
    init_train_state,
    make_batch,
    ppo_update,
    scheduled_lr,
)
from game import NUM_GRID_CHANNELS, NUM_SCALARS, GeneralsEnv

from .config import TrainConfig, print_config
from .evaluate import evaluate_policy
from .replay_tools import record_game
from .logger import RunLogger, print_row
from .rollout import collect_trajectory, rollout_stats
from .opponent_pool import OpponentPool, sample_opponents


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--preset", default="default",
                    choices=["smoke", "small", "default"],
                    help="hyper-parameter preset to start from")
    ap.add_argument("--total-updates", type=int, default=None,
                    help="number of PPO updates (default from the preset)")
    ap.add_argument("--out", type=str, default=None, help="run directory")
    ap.add_argument("--seed", type=int, default=None)

    # environment
    ap.add_argument("--size", type=int, default=None,
                    help="square board size (overrides height/width)")
    ap.add_argument("--max-turns", type=int, default=None)

    # network
    ap.add_argument("--memory", choices=["none", "gru", "stack"], default=None)
    ap.add_argument("--channels", type=int, default=None)
    ap.add_argument("--blocks", type=int, default=None)

    # ppo
    ap.add_argument("--num-envs", type=int, default=None)
    ap.add_argument("--rollout-len", type=int, default=None)
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--minibatches", type=int, default=None)
    ap.add_argument("--lr", type=float, default=None,
                    help="starting learning rate for AdamW (default: 3e-4)")
    ap.add_argument("--lr-end", type=float, default=None,
                    help="final learning rate for scheduled decay (default: 0.0)")
    ap.add_argument("--lr-schedule", choices=list(LR_SCHEDULES), default=None,
                    help="learning rate schedule: linear, cosine or constant")
    ap.add_argument("--lr-warmup-updates", type=int, default=None,
                    help="number of linear warmup updates before decay")
    ap.add_argument("--weight-decay", type=float, default=None,
                    help="AdamW weight decay (0.0 = standard Adam)")
    ap.add_argument("--gamma", type=float, default=None)
    ap.add_argument("--shaping", type=float, default=None,
                    help="potential-based shaping coefficient (0 = sparse only)")
    ap.add_argument("--distance-shaping", type=float, default=None,
                    help="weight of the general-distance shaping term")
    ap.add_argument("--ent-coef", type=float, default=None)

    # logging / evaluation
    ap.add_argument("--eval-every", type=int, default=None)
    ap.add_argument("--checkpoint-every", type=int, default=None)
    ap.add_argument("--eval-games", type=int, default=None)
    ap.add_argument("--eval-opponent", choices=["greedy", "random"], default=None)
    ap.add_argument("--train-opponent", choices=["self", "random", "greedy", "pool"],
                    default=None, help="opponent used during data collection")
    ap.add_argument("--opponent-pool-size", type=int, default=None,
                    help="maximum number of historical opponents (default: 8)")
    ap.add_argument("--opponent-snapshot-every", type=int, default=None,
                    help="add a policy to the pool every N updates (default: 25)")
    ap.add_argument("--log-every", type=int, default=None)
    ap.add_argument("--save-replay-every", type=int, default=0, metavar="N",
                    help="every N updates, play one game and save it as a replay "
                         "under <run-dir>/replays (0 disables; default 0)")
    ap.add_argument("--replay-video", action="store_true",
                    help="also render each saved replay to an MP4 (or a GIF when "
                         "ffmpeg is missing)")
    ap.add_argument("--replay-view", choices=["seat0", "seat1", "all"],
                    default="all", help="camera for the rendered replay video")
    ap.add_argument("--resume", action="store_true",
                    help="load the latest checkpoint in --out and continue")
    ap.add_argument("--no-remat", action="store_true",
                    help="disable gradient checkpointing (faster, more memory)")
    return ap


def overrides_from_args(args: argparse.Namespace) -> dict:
    """Collect the explicitly-passed CLI flags as config overrides."""
    mapping = {
        "total_updates": args.total_updates,
        "out_dir": args.out,
        "seed": args.seed,
        "max_turns": args.max_turns,
        "memory": args.memory,
        "channels": args.channels,
        "num_blocks": args.blocks,
        "num_envs": args.num_envs,
        "rollout_len": args.rollout_len,
        "epochs": args.epochs,
        "num_minibatches": args.minibatches,
        "lr": args.lr,
        "lr_end": args.lr_end,
        "lr_schedule": args.lr_schedule,
        "lr_warmup_updates": args.lr_warmup_updates,
        "weight_decay": args.weight_decay,
        "gamma": args.gamma,
        "shaping_coef": args.shaping,
        "general_distance_coef": args.distance_shaping,
        "ent_coef": args.ent_coef,
        "eval_every": args.eval_every,
        "checkpoint_every": args.checkpoint_every,
        "eval_games": args.eval_games,
        "eval_opponent": args.eval_opponent,
        "train_opponent": args.train_opponent,
        "opponent_pool_size": args.opponent_pool_size,
        "opponent_snapshot_every": args.opponent_snapshot_every,
        "log_every": args.log_every,
        "save_replay_every": args.save_replay_every,
        "replay_view": args.replay_view,
    }
    overrides = {k: v for k, v in mapping.items() if v is not None}
    if args.size is not None:
        overrides["height"] = args.size
        overrides["width"] = args.size
    if args.no_remat:
        overrides["remat"] = False
    if args.replay_video:
        overrides["replay_video"] = True
    return overrides


def config_from_args(args: argparse.Namespace) -> TrainConfig:
    return TrainConfig.from_preset(args.preset, **overrides_from_args(args))


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    resume_from = 1
    resumed_params = None
    resumed_pool_path = None
    if args.resume:
        run_dir = args.out or f"runs/{args.preset}"
        checkpoint = Checkpoint(run_dir)
        arrays, payload = checkpoint.load("latest")
        cfg = TrainConfig(**payload["config"]).replace(**overrides_from_args(args))
        resume_from = int(payload.get("metadata", {}).get("update", 0)) + 1
        resumed_params = (checkpoint, arrays)
        if payload["config"].get("train_opponent") == "pool" and cfg.train_opponent == "pool":
            resumed_pool_path = checkpoint.dir / f"pool_{payload['tag']}.npz"
        print(f"resuming {payload['tag']} (update {resume_from}) from {run_dir}")
    else:
        cfg = config_from_args(args)
    print_config(cfg)

    key = jax.random.PRNGKey(cfg.seed)
    env_cfg = cfg.env_config()
    env = GeneralsEnv(
        env_cfg, map_pool_size=cfg.map_pool_size, seed=cfg.seed
    )
    net = PolicyValueNet(
        cfg.net_config(),
        grid_channels=NUM_GRID_CHANNELS,
        num_scalars=NUM_SCALARS,
        height=cfg.height,
        width=cfg.width,
    )
    train_state = init_train_state(net, key)
    if resumed_params is not None:
        checkpoint, arrays = resumed_params
        train_state = train_state._replace(
            params=checkpoint.restore(arrays, train_state.params)
        )

    states = env.reset_batch(jax.random.split(key, cfg.num_envs))
    memory = net.batched_initial_memory((cfg.num_envs, 2))
    ppo_cfg = cfg.ppo_config()

    pool = None
    if cfg.train_opponent == "pool":
        if resumed_pool_path is not None:
            pool = OpponentPool.load(resumed_pool_path, cfg.opponent_pool_size,
                                     train_state.params)
        else:
            pool = OpponentPool(cfg.opponent_pool_size, train_state.params)
        active_opponents = sample_opponents(
            pool.stacked(), len(pool.snapshots), jax.random.PRNGKey(cfg.seed + 2),
            cfg.num_envs)
        collect = jax.jit(
            lambda params, s, m, k, p, n, active: collect_trajectory(
                env, net, params, s, m, k, cfg, env_cfg, p, n, active)
        )
    else:
        collect = jax.jit(
            lambda params, s, m, k: collect_trajectory(
                env, net, params, s, m, k, cfg, env_cfg
            )
        )
    batch_fn = jax.jit(lambda traj, last: make_batch(traj, last, ppo_cfg))
    update = jax.jit(
        lambda ts, batch, lr: ppo_update(ts, batch, net, ppo_cfg, lr=lr)
    )
    evaluate = jax.jit(
        lambda params, k: evaluate_policy(env, net, params, k, cfg)
    )

    logger = RunLogger(cfg.out_dir, append=args.resume)
    logger.write_config(cfg.to_dict())
    checkpoint = Checkpoint(cfg.out_dir)

    steps_per_update = cfg.num_envs * cfg.rollout_len * 2
    key_train = jax.random.PRNGKey(cfg.seed + 1)
    print(f"params: {sum(int(x.size) for x in jax.tree_util.tree_leaves(train_state.params)):,}")
    print("compiling collect/update ...", flush=True)

    for update_idx in range(resume_from, cfg.total_updates + 1):
        t0 = time.perf_counter()
        current_lr = scheduled_lr(
            update_idx,
            cfg.total_updates,
            cfg.lr,
            schedule=cfg.lr_schedule,
            lr_end=cfg.lr_end,
            warmup_updates=cfg.lr_warmup_updates,
        )
        if pool is not None:
            traj, states, memory, last_values, active_opponents = collect(
                train_state.params, states, memory, key_train, pool.stacked(),
                jnp.asarray(len(pool.snapshots), dtype=jnp.int32), active_opponents)
        else:
            traj, states, memory, last_values = collect(
                train_state.params, states, memory, key_train
            )
        key_train, _ = jax.random.split(key_train)
        batch = batch_fn(traj, last_values)
        train_state, metrics = update(
            train_state, batch, jnp.asarray(current_lr, dtype=jnp.float32)
        )
        jax.block_until_ready(train_state.params)
        if pool is not None and update_idx % cfg.opponent_snapshot_every == 0:
            pool.add(train_state.params)
        elapsed = time.perf_counter() - t0

        row = {
            "update": update_idx,
            "steps": update_idx * steps_per_update,
            "sps": steps_per_update / max(elapsed, 1e-9),
            "time": elapsed,
            **{k: float(v) for k, v in metrics.items()},
            **rollout_stats(traj),
        }

        if cfg.eval_every and (update_idx == 1 or update_idx % cfg.eval_every == 0):
            t_eval = time.perf_counter()
            stats = evaluate(
                train_state.params,
                jax.random.PRNGKey(cfg.seed + 10_000 + update_idx),
            )
            row.update({f"eval_{k}": float(v) for k, v in stats.items()})
            row["eval_time"] = time.perf_counter() - t_eval

        if cfg.checkpoint_every and (
            update_idx == 1 or update_idx % cfg.checkpoint_every == 0
        ):
            if pool is not None:
                pool.save(checkpoint.dir / f"pool_step_{update_idx:06d}.npz")
            checkpoint.save(
                f"step_{update_idx:06d}",
                train_state.params,
                cfg.to_dict(),
                {"update": update_idx, "metrics": {
                    k: float(v) for k, v in row.items() if isinstance(v, float)
                }},
            )

        if (
            cfg.save_replay_every
            and update_idx % cfg.save_replay_every == 0
        ):
            try:
                paths = record_game(
                    cfg,
                    net,
                    train_state.params,
                    f"step_{update_idx:06d}",
                    jax.random.PRNGKey(cfg.seed + 70_000 + update_idx),
                    tag=f"step_{update_idx:06d}",
                    run_dir=cfg.out_dir,
                    meta={"update": update_idx},
                    video=cfg.replay_video,
                    view=cfg.replay_view,
                )
                if paths:
                    print("replay " + " ".join(str(p) for p in paths), flush=True)
            except Exception as exc:  # pragma: no cover - recording is optional
                print(f"replay failed: {exc}", flush=True)

        logger.log(row)
        if cfg.log_every and (update_idx % cfg.log_every == 0 or update_idx == 1):
            keys = ["update", "lr", "loss", "policy_loss", "value_loss", "entropy",
                    "approx_kl", "clip_frac", "episodes", "mean_length",
                    "win_rate_p0", "eval_win_rate", "sps", "time"]
            print_row(row, keys)

    if pool is not None:
        pool.save(checkpoint.dir / "pool_final.npz")
    checkpoint.save(
        "final", train_state.params, cfg.to_dict(), {"update": cfg.total_updates}
    )
    print(f"done. checkpoints in {checkpoint.dir}")


if __name__ == "__main__":
    main()
