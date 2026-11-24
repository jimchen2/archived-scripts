"""Tests for GAE, AdamW and the PPO update."""

from __future__ import annotations

import jax
import jax.numpy as jnp
import numpy as np
import pytest

from bot.network import NetConfig, PolicyValueNet
from bot.ppo import (
    PPOBatch,
    PPOConfig,
    TrainState,
    adamw_init,
    adamw_update,
    compute_gae,
    init_train_state,
    ppo_loss,
    ppo_update,
    scheduled_lr,
)


def make_net(memory="gru", channels=8, height=5, width=5):
    cfg = NetConfig(
        channels=channels,
        num_blocks=1,
        memory=memory,
        stack_frames=2,
        global_context_every=1,
    )
    return PolicyValueNet(cfg, grid_channels=10, num_scalars=7,
                          height=height, width=width)


def random_batch(net, t=3, n=4, key=jax.random.PRNGKey(0)):
    k1, k2, k3, k4, k5 = jax.random.split(key, 5)
    grids = jax.random.uniform(k1, (t, n, 10, net.height, net.width))
    scalars = jax.random.uniform(k2, (t, n, net.num_scalars))
    masks = jax.random.bernoulli(k3, 0.2, (t, n, net.num_actions))
    masks = masks.at[..., 0].set(True)                    # keep pass legal
    actions = jax.random.randint(k4, (t, n), 0, net.num_actions)
    log_probs = jax.random.normal(k5, (t, n)) * 0.01
    values = jax.random.normal(jax.random.PRNGKey(6), (t, n)) * 0.1
    return PPOBatch(
        grids=grids,
        scalars=scalars,
        masks=masks,
        actions=actions,
        old_log_probs=log_probs,
        old_values=values,
        advantages=jnp.zeros((t, n)),
        returns=values,
        dones=jnp.zeros((t, n)),
    )


# ---------------------------------------------------------------------------
# GAE
# ---------------------------------------------------------------------------


def naive_gae(rewards, values, last_values, dones, gamma, lam):
    t, n = rewards.shape
    adv = np.zeros((t, n), dtype=np.float64)
    for i in reversed(range(t)):
        next_v = last_values if i == t - 1 else values[i + 1]
        nonterminal = 1.0 - dones[i]
        delta = rewards[i] + gamma * next_v * nonterminal - values[i]
        nxt = adv[i + 1] if i + 1 < t else 0.0
        adv[i] = delta + gamma * lam * nonterminal * nxt
    return adv


def test_gae_matches_naive_loop():
    rng = np.random.default_rng(0)
    t, n = 6, 3
    rewards = rng.normal(size=(t, n)).astype(np.float32)
    values = rng.normal(size=(t, n)).astype(np.float32)
    last = rng.normal(size=(n,)).astype(np.float32)
    dones = (rng.random((t, n)) < 0.2).astype(np.float32)

    adv, returns = compute_gae(
        jnp.asarray(rewards), jnp.asarray(values), jnp.asarray(last),
        jnp.asarray(dones), gamma=0.97, gae_lambda=0.9,
    )
    expected = naive_gae(rewards, values, last, dones, 0.97, 0.9)
    np.testing.assert_allclose(np.asarray(adv), expected, rtol=1e-4, atol=1e-5)
    np.testing.assert_allclose(np.asarray(returns), expected + values, rtol=1e-4, atol=1e-5)


def test_gae_zero_on_terminal_bootstrap():
    rewards = np.ones((2, 1), dtype=np.float32)
    values = np.zeros((2, 1), dtype=np.float32)
    dones = np.array([[1.0], [0.0]], dtype=np.float32)
    adv, returns = compute_gae(
        jnp.asarray(rewards), jnp.asarray(values),
        jnp.asarray([5.0]), jnp.asarray(dones), gamma=0.9, gae_lambda=0.9,
    )
    # done at t=0 -> no bootstrap, no propagation of the next advantage
    assert float(adv[0, 0]) == pytest.approx(1.0, abs=1e-6)


# ---------------------------------------------------------------------------
# AdamW
# ---------------------------------------------------------------------------


def test_adamw_first_step_is_sign_step():
    params = {"w": jnp.array([1.0, -2.0])}
    grads = {"w": jnp.array([0.5, -0.1])}
    opt = adamw_init(params)
    new_params, new_opt = adamw_update(
        grads, opt, params, PPOConfig(lr=0.1)
    )
    expected = 1.0 - 0.1 * np.sign(0.5)
    assert float(new_params["w"][0]) == pytest.approx(expected, abs=1e-6)
    assert int(new_opt.step) == 1


def test_adamw_lr_override():
    params = {"w": jnp.array([1.0, -2.0])}
    grads = {"w": jnp.array([0.5, -0.1])}
    opt = adamw_init(params)
    new_params, new_opt = adamw_update(
        grads, opt, params, PPOConfig(lr=0.1), lr=jnp.asarray(0.02)
    )
    expected = 1.0 - 0.02 * np.sign(0.5)
    assert float(new_params["w"][0]) == pytest.approx(expected, abs=1e-6)
    assert int(new_opt.step) == 1

    # Zero LR leaves params untouched while still advancing Adam moments/step.
    zero_params, zero_opt = adamw_update(
        grads, opt, params, PPOConfig(lr=0.1), lr=0.0
    )
    np.testing.assert_allclose(np.asarray(zero_params["w"]), [1.0, -2.0])
    assert int(zero_opt.step) == 1


def test_scheduled_lr_profiles():
    # Linear: starts at lr on update 1, decreases monotonically, clamps at lr_end.
    assert scheduled_lr(1, 10, 3e-4, schedule="linear") == pytest.approx(3e-4)
    assert scheduled_lr(6, 10, 3e-4, schedule="linear") == pytest.approx(1.5e-4)
    assert scheduled_lr(10, 10, 3e-4, schedule="linear") == pytest.approx(3e-5)
    assert scheduled_lr(11, 10, 3e-4, schedule="linear") == pytest.approx(0.0)
    assert scheduled_lr(11, 10, 3e-4, schedule="linear", lr_end=1e-5) == pytest.approx(1e-5)

    # Cosine: starts at lr, hits midpoint at 50%, smoothly approaches lr_end.
    assert scheduled_lr(1, 10, 3e-4, schedule="cosine", lr_end=1e-5) == pytest.approx(3e-4)
    assert scheduled_lr(6, 10, 3e-4, schedule="cosine", lr_end=1e-5) == pytest.approx(1.55e-4)
    assert scheduled_lr(10, 10, 3e-4, schedule="cosine", lr_end=1e-5) < 2e-5
    assert scheduled_lr(15, 10, 3e-4, schedule="cosine", lr_end=1e-5) == pytest.approx(1e-5)

    # Constant: unchanged across all updates.
    for u in (1, 5, 10, 50):
        assert scheduled_lr(u, 10, 3e-4, schedule="constant") == pytest.approx(3e-4)

    # Warmup ramps linearly up to lr, then decays.
    assert scheduled_lr(1, 10, 3e-4, schedule="linear", warmup_updates=3) == pytest.approx(1e-4)
    assert scheduled_lr(2, 10, 3e-4, schedule="linear", warmup_updates=3) == pytest.approx(2e-4)
    assert scheduled_lr(3, 10, 3e-4, schedule="linear", warmup_updates=3) == pytest.approx(3e-4)
    after_warmup = scheduled_lr(4, 10, 3e-4, schedule="linear", warmup_updates=3)
    assert 0.0 < after_warmup < 3e-4

    # Single-update run keeps the starting lr.
    assert scheduled_lr(1, 1, 3e-4, schedule="linear") == pytest.approx(3e-4)
    assert scheduled_lr(1, 1, 3e-4, schedule="cosine") == pytest.approx(3e-4)

    with pytest.raises(ValueError):
        scheduled_lr(1, 10, 3e-4, schedule="unknown")
    with pytest.raises(ValueError):
        scheduled_lr(1, 10, -1e-4, schedule="linear")


# ---------------------------------------------------------------------------
# PPO loss / update
# ---------------------------------------------------------------------------


def test_ppo_loss_at_old_policy_is_pure_entropy_bonus():
    net = make_net()
    params = net.init(jax.random.PRNGKey(0))
    batch = random_batch(net)

    # Recompute the "old" log-probs/values with the same parameters.
    logps, values, _ = jax.vmap(
        lambda g, s, m, d, a: net.sequence_forward(params, g, s, m, d, actions=a),
        in_axes=1, out_axes=1,
    )(batch.grids, batch.scalars, batch.masks, batch.dones.astype(jnp.bool_), batch.actions)
    batch = batch._replace(
        old_log_probs=logps, old_values=values, returns=values,
    )
    cfg = PPOConfig(clip_eps=0.2, ent_coef=0.01, vf_coef=0.5)
    total, metrics = ppo_loss(params, net, batch, cfg)
    assert float(metrics["approx_kl"]) == pytest.approx(0.0, abs=1e-6)
    assert float(metrics["policy_loss"]) == pytest.approx(0.0, abs=1e-6)
    assert float(metrics["value_loss"]) == pytest.approx(0.0, abs=1e-6)
    assert float(total) == pytest.approx(-0.01 * float(metrics["entropy"]), abs=1e-6)


def test_ppo_update_runs_and_changes_params():
    net = make_net()
    state = init_train_state(net, jax.random.PRNGKey(0))
    batch = random_batch(net)
    cfg = PPOConfig(epochs=1, num_minibatches=2, lr=1e-3)
    new_state, metrics = ppo_update(state, batch, net, cfg)

    for value in jax.tree_util.tree_leaves(metrics):
        assert np.isfinite(np.asarray(value)).all()
    assert float(metrics["lr"]) == pytest.approx(1e-3, rel=1e-5)
    changed = sum(
        float(jnp.sum(jnp.abs(a - b)))
        for a, b in zip(
            jax.tree_util.tree_leaves(new_state.params),
            jax.tree_util.tree_leaves(state.params),
        )
    )
    assert changed > 0

    # Dynamic lr override works inside jax.jit and is reported in metrics.
    jitted = jax.jit(lambda ts, b, lr: ppo_update(ts, b, net, cfg, lr=lr))
    _, m_sched = jitted(new_state, batch, jnp.asarray(2.5e-4, dtype=jnp.float32))
    assert float(m_sched["lr"]) == pytest.approx(2.5e-4, rel=1e-5)


def test_ppo_update_minibatch_shapes():
    """A 3-step / 5-trajectory batch must work with any minibatch count."""
    net = make_net()
    state = init_train_state(net, jax.random.PRNGKey(0))
    batch = random_batch(net, t=3, n=5)
    cfg = PPOConfig(epochs=2, num_minibatches=3)
    _, metrics = ppo_update(state, batch, net, cfg)
    assert np.isfinite(np.asarray(metrics["loss"]))


def test_ratio_is_one_on_first_epoch():
    """Log-prob recomputation at the collection params must reproduce them."""
    net = make_net("gru")
    params = net.init(jax.random.PRNGKey(0))
    batch = random_batch(net, t=4, n=3)
    logps, values, _ = jax.vmap(
        lambda g, s, m, d, a: net.sequence_forward(params, g, s, m, d, actions=a),
        in_axes=1, out_axes=1,
    )(batch.grids, batch.scalars, batch.masks, batch.dones.astype(jnp.bool_), batch.actions)
    batch = batch._replace(old_log_probs=logps, old_values=values, returns=values)
    total, metrics = ppo_loss(params, net, batch, PPOConfig())
    assert float(metrics["approx_kl"]) < 1e-6
    assert float(metrics["clip_frac"]) < 1e-6
