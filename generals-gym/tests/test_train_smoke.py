"""End-to-end smoke test: collect a rollout and run one PPO update."""

from __future__ import annotations

import jax
import numpy as np

from bot.network import PolicyValueNet
from bot.ppo import init_train_state, make_batch, ppo_update
from game import NUM_GRID_CHANNELS, NUM_SCALARS, GeneralsEnv
from src.config import TrainConfig
from src.evaluate import evaluate_policy
from src.rollout import collect_trajectory, rollout_stats


def test_collect_and_update_smoke():
    cfg = TrainConfig.from_preset(
        "smoke",
        num_envs=2,
        rollout_len=3,
        epochs=1,
        num_minibatches=1,
        channels=4,
        num_blocks=1,
        max_turns=40,
        eval_games=2,
        map_pool_size=8,
    )
    env = GeneralsEnv(cfg.env_config(), map_pool_size=cfg.map_pool_size, seed=0)
    net = PolicyValueNet(
        cfg.net_config(),
        grid_channels=NUM_GRID_CHANNELS,
        num_scalars=NUM_SCALARS,
        height=cfg.height,
        width=cfg.width,
    )
    state = init_train_state(net, jax.random.PRNGKey(0))
    states = env.reset_batch(jax.random.split(jax.random.PRNGKey(0), cfg.num_envs))
    memory = net.batched_initial_memory((cfg.num_envs, 2))

    traj, states, memory, last_values = collect_trajectory(
        env, net, state.params, states, memory, jax.random.PRNGKey(1),
        cfg, cfg.env_config(),
    )
    assert traj.grids.shape == (cfg.rollout_len, cfg.num_envs, 2, 10, cfg.height, cfg.width)
    assert traj.actions.shape == (cfg.rollout_len, cfg.num_envs, 2)
    assert last_values.shape == (cfg.num_envs, 2)

    stats = rollout_stats(traj)
    assert stats["episodes"] >= 0

    batch = make_batch(traj, last_values, cfg.ppo_config())
    assert batch.actions.shape == (cfg.rollout_len, cfg.num_envs * 2)
    new_state, metrics = ppo_update(state, batch, net, cfg.ppo_config())
    for value in jax.tree_util.tree_leaves(metrics):
        assert np.isfinite(np.asarray(value)).all()

    eval_stats = evaluate_policy(
        env, net, new_state.params, jax.random.PRNGKey(2), cfg, games=2
    )
    assert 0.0 <= float(eval_stats["win_rate"]) <= 1.0


def test_train_main_logs_scheduled_lr(tmp_path):
    import csv

    from src.train import main

    out_dir = tmp_path / "run"
    main([
        "--preset", "smoke",
        "--out", str(out_dir),
        "--total-updates", "3",
        "--num-envs", "2",
        "--rollout-len", "2",
        "--epochs", "1",
        "--minibatches", "1",
        "--channels", "4",
        "--blocks", "1",
        "--size", "7",
        "--max-turns", "20",
        "--eval-every", "0",
        "--checkpoint-every", "0",
        "--lr", "3e-4",
        "--lr-schedule", "linear",
        "--lr-end", "0.0",
    ])

    with (out_dir / "metrics.csv").open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 3
    assert "lr" in rows[0]
    lrs = [float(r["lr"]) for r in rows]
    np.testing.assert_allclose(lrs, [3e-4, 2e-4, 1e-4], rtol=1e-4)
