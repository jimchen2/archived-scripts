"""Historical opponent sampling, lifecycle and training integration."""
import jax
import jax.numpy as jnp
import numpy as np
import pytest

from bot.network import PolicyValueNet
from bot.ppo import init_train_state, make_batch, ppo_loss
from game import NUM_GRID_CHANNELS, NUM_SCALARS, GeneralsEnv
from src.config import TrainConfig
from src.opponent_pool import OpponentPool, sample_opponents
from src.rollout import collect_trajectory
from src.train import build_parser, config_from_args, main


def test_pool_fifo_sampling_and_roundtrip(tmp_path):
    def params(value):
        return {"x": jnp.asarray([value], dtype=jnp.float32)}

    pool = OpponentPool(2, params(0))
    pool.add(params(1))
    pool.add(params(2))
    assert [int(p["x"][0]) for p in pool.snapshots] == [1, 2]
    sampled = sample_opponents(pool.stacked(), 2, jax.random.PRNGKey(4), 128)
    assert set(np.asarray(sampled["x"]).ravel()) == {1, 2}
    np.testing.assert_array_equal(sampled["x"], sample_opponents(
        pool.stacked(), 2, jax.random.PRNGKey(4), 128)["x"])
    path = tmp_path / "pool.npz"
    pool.save(path)
    restored = OpponentPool.load(path, 1, params(0))
    assert len(restored.snapshots) == 1
    assert int(restored.snapshots[0]["x"][0]) == 2
    assert OpponentPool.load(path, 4, params(0)).stacked()["x"].shape == (4, 1)
    with pytest.raises(ValueError):
        OpponentPool.load(path, 2, {"x": jnp.zeros(3)})


def test_pool_config_and_cli():
    cfg = config_from_args(build_parser().parse_args([
        "--train-opponent", "pool", "--opponent-pool-size", "3",
        "--opponent-snapshot-every", "2"]))
    assert (cfg.train_opponent, cfg.opponent_pool_size, cfg.opponent_snapshot_every) == ("pool", 3, 2)
    for field in ("opponent_pool_size", "opponent_snapshot_every"):
        with pytest.raises(ValueError):
            cfg.replace(**{field: 0})


def test_pool_rollout_keeps_opponent_until_done_and_reconstructs_memory():
    cfg = TrainConfig.from_preset("smoke", height=7, width=7, channels=4,
        num_blocks=1, num_envs=2, rollout_len=2, epochs=1, num_minibatches=1,
        map_pool_size=4, max_turns=20, memory="gru", train_opponent="pool")
    env = GeneralsEnv(cfg.env_config(), map_pool_size=cfg.map_pool_size, seed=0)
    net = PolicyValueNet(cfg.net_config(), grid_channels=NUM_GRID_CHANNELS,
                         num_scalars=NUM_SCALARS, height=7, width=7)
    params = init_train_state(net, jax.random.PRNGKey(0)).params
    historical = jax.tree_util.tree_map(lambda x: x + 0.1, params)
    pool = OpponentPool(1, historical)
    active = jax.tree_util.tree_map(lambda x: jnp.broadcast_to(x, (2,) + x.shape), params)
    states = env.reset_batch(jax.random.split(jax.random.PRNGKey(1), 2))
    memory = net.batched_initial_memory((2, 2))
    collect = jax.jit(lambda s, m, a, k: collect_trajectory(
        env, net, params, s, m, k, cfg, cfg.env_config(), pool.stacked(),
        jnp.int32(1), a))
    traj, states, memory, _, active_after = collect(states, memory, active, jax.random.PRNGKey(2))
    assert traj.actions.shape == (2, 2, 1)
    for before, after in zip(jax.tree_util.tree_leaves(active), jax.tree_util.tree_leaves(active_after)):
        np.testing.assert_array_equal(before, after)
    # A second rollout starts with nonzero recurrent memory. Its old policy
    # probabilities must match PPO's sequence reconstruction exactly.
    traj, states, memory, last, active_after = collect(states, memory, active_after, jax.random.PRNGKey(3))
    batch = make_batch(traj, last, cfg.ppo_config())
    _, metrics = ppo_loss(params, net, batch, cfg.ppo_config())
    assert abs(float(metrics["approx_kl"])) < 1e-6
    # Force only one environment to end; it samples the current pool while
    # the other continues using its original, now evicted opponent.
    states = states._replace(turn=jnp.array([2 * cfg.max_turns - 1, 0], dtype=jnp.int32))
    traj, _, _, _, next_active = collect(states, memory, active_after, jax.random.PRNGKey(4))
    assert bool(jnp.any(traj.dones[:, 0, 0]))
    assert not bool(jnp.any(traj.dones[:, 1, 0]))
    for old, new, expected in zip(jax.tree_util.tree_leaves(active_after),
                                  jax.tree_util.tree_leaves(next_active),
                                  jax.tree_util.tree_leaves(historical)):
        np.testing.assert_array_equal(new[0], expected)
        np.testing.assert_array_equal(new[1], old[1])


def test_pool_train_and_resume(tmp_path):
    out = str(tmp_path / "run")
    common = ["--out", out, "--total-updates", "1", "--eval-every", "0",
              "--checkpoint-every", "1"]
    main(["--preset", "smoke", "--num-envs", "1", "--rollout-len", "2",
          "--epochs", "1", "--minibatches", "1", "--channels", "4",
          "--blocks", "1", "--size", "7", "--max-turns", "5",
          "--train-opponent", "pool", "--opponent-pool-size", "2",
          "--opponent-snapshot-every", "1", *common])
    path = tmp_path / "run" / "checkpoints" / "pool_final.npz"
    with np.load(path) as data:
        assert int(data["count"]) == 2
    main(["--resume", "--out", out, "--total-updates", "2"])
    with np.load(path) as data:
        assert int(data["count"]) == 2


def test_pool_opponent_controls_seat_one():
    cfg = TrainConfig.from_preset("smoke", height=7, width=7, channels=4,
        num_blocks=1, num_envs=1, rollout_len=1, map_pool_size=4,
        max_turns=20, train_opponent="pool")
    env = GeneralsEnv(cfg.env_config(), map_pool_size=4, seed=1)
    net = PolicyValueNet(cfg.net_config(), grid_channels=NUM_GRID_CHANNELS,
                         num_scalars=NUM_SCALARS, height=7, width=7)
    params = net.init(jax.random.PRNGKey(0))
    opponent = net.init(jax.random.PRNGKey(9))
    pool = OpponentPool(1, opponent)
    states = env.reset_batch(jax.random.split(jax.random.PRNGKey(1), 1))
    # Make both players able to move so action selection is meaningful.
    states = states._replace(army=jnp.where(states.owner >= 0, 10, states.army))
    memory = net.batched_initial_memory((1, 2))
    key = jax.random.PRNGKey(5)
    step_key = jax.random.split(key, 1)[0]
    k_agent, _ = jax.random.split(step_key)
    keys = jax.random.split(k_agent, (1, 2))
    obs = env.observations_batch(states)
    masks = jax.vmap(env.action_mask)(states)
    action0 = net.step(params, obs.grid[0, 0], obs.scalars[0, 0], masks[0, 0],
                       jax.tree_util.tree_map(lambda x: x[0, 0], memory), key=keys[0, 0]).action
    action1 = net.step(opponent, obs.grid[0, 1], obs.scalars[0, 1], masks[0, 1],
                       jax.tree_util.tree_map(lambda x: x[0, 1], memory), key=keys[0, 1]).action
    expected, _, _ = env.step_batch(states, jnp.array([[action0, action1]]), auto_reset=False)
    active = sample_opponents(pool.stacked(), 1, jax.random.PRNGKey(8), 1)
    traj, actual, _, _, _ = collect_trajectory(env, net, params, states, memory,
        key, cfg, cfg.env_config(), pool.stacked(), jnp.int32(1), active)
    assert int(traj.actions[0, 0, 0]) == int(action0)
    for a, b in zip(jax.tree_util.tree_leaves(actual), jax.tree_util.tree_leaves(expected)):
        np.testing.assert_array_equal(a, b)
