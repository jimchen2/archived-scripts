"""Vectorisation, jit and auto-reset tests."""

from __future__ import annotations

import jax
import jax.numpy as jnp
import numpy as np

from game import EnvConfig, GeneralsEnv
from game.engine import decode_action, encode_action
from game.env import from_numpy, to_numpy


def _masked_sample(key, mask):
    logits = jnp.where(mask, 0.0, -jnp.inf)
    return jax.random.categorical(key, logits)


def test_encode_decode_roundtrip():
    cfg = EnvConfig(height=5, width=7)
    assert cfg.num_actions == 35 * cfg.dir_actions
    for src in (0, 7, 34):
        for d in range(cfg.dir_actions):
            act = encode_action(src, d, cfg)
            assert decode_action(act, cfg) == (src, d)


def test_state_numpy_roundtrip_preserves_half_turn_phase():
    env = GeneralsEnv(EnvConfig(height=2, width=2))
    state = env.make_state(["g0:1 .", ". g1:1"], turn=7, half_turn=1)
    restored = from_numpy(to_numpy(state))
    assert int(restored.turn) == 7
    assert int(restored.half_turn) == 1


def test_batched_step_equals_individual_steps():
    env = GeneralsEnv(EnvConfig(height=9, width=9, city_count=3))
    keys = jax.random.split(jax.random.PRNGKey(0), 8)
    states = env.reset_batch(keys)
    assert states.army.shape == (8, 9, 9)
    assert states.general.shape == (8, 2)

    acts = jax.random.randint(jax.random.PRNGKey(1), (8, 2), 0, env.num_actions)
    batched, batched_rew, _ = env.step_batch(states, acts, auto_reset=False)

    for i in range(8):
        single, single_rew, _ = env.step(
            jax.tree_util.tree_map(lambda x, i=i: x[i], states), acts[i]
        )
        assert np.array_equal(np.asarray(single.army), np.asarray(batched.army[i]))
        assert np.array_equal(np.asarray(single.owner), np.asarray(batched.owner[i]))
        assert np.allclose(np.asarray(single_rew), np.asarray(batched_rew[i]))


def test_reset_is_deterministic_per_key():
    env = GeneralsEnv()
    a = env.reset(jax.random.PRNGKey(42))
    b = env.reset(jax.random.PRNGKey(42))
    c = env.reset(jax.random.PRNGKey(43))
    for field in ("army", "owner", "city", "general"):
        assert np.array_equal(np.asarray(getattr(a, field)), np.asarray(getattr(b, field)))
    assert not np.array_equal(np.asarray(a.owner), np.asarray(c.owner))


def test_auto_reset_only_resets_finished_envs():
    # A position where player 1 wins immediately.
    env = GeneralsEnv(EnvConfig(height=2, width=3))
    state = env.make_state(["g0:1 1:9 .", ". . g1:1"])
    action_p1 = (0 * 3 + 1) * env.config.dir_actions + 3  # (0,1) -> left
    state, rew, info = env.step(state, jnp.asarray([0, action_p1], dtype=jnp.int32))
    assert bool(state.done)
    assert np.allclose(np.asarray(rew), [-1.0, 1.0])

    fresh, rew2, info2 = env.step(
        state, jnp.asarray([0, 0], dtype=jnp.int32), auto_reset=True
    )
    assert not bool(fresh.done)
    assert int(fresh.turn) == 0
    assert np.allclose(np.asarray(rew2), 0.0)  # the finished episode's reward is gone
    # ... but ``info`` still describes the transition that just happened
    assert int(info2["winner"]) == 1
    assert bool(info2["done"])


def test_auto_reset_in_a_scan_loop():
    env = GeneralsEnv(EnvConfig(height=6, width=6, city_count=2, max_turns=5))
    B, T = 4, 40

    def body(carry, _):
        states, key = carry
        key, k = jax.random.split(key)
        masks = jax.vmap(env.action_mask)(states)
        logits = jnp.where(masks, 0.0, -jnp.inf).reshape(-1, masks.shape[-1])
        keys = jax.random.split(k, logits.shape[0])
        acts = jax.vmap(jax.random.categorical)(keys, logits).reshape(B, 2)
        states, rewards, _ = env.step_batch(states, acts, auto_reset=True)
        return (states, key), (rewards.sum(), states.turn)

    keys = jax.random.split(jax.random.PRNGKey(0), B)
    states = env.reset_batch(keys)
    (states, _), (rewards, turns) = jax.lax.scan(body, (states, jax.random.PRNGKey(1)), None, T)
    assert np.isfinite(np.asarray(rewards)).all()
    assert np.asarray(turns).min() >= 0
    # games are 5 turns long, so the batch must have reset many times
    assert np.asarray(turns).max() <= 5


def test_jit_and_eager_agree():
    env = GeneralsEnv(EnvConfig(height=7, width=7, city_count=2))
    s = env.reset(jax.random.PRNGKey(0))
    acts = jnp.asarray([3, 17], dtype=jnp.int32)
    a, ra, _ = env.step(s, acts)
    b, rb, _ = jax.jit(lambda st, ac: env.step(st, ac))(s, acts)
    assert np.array_equal(np.asarray(a.army), np.asarray(b.army))
    assert np.allclose(np.asarray(ra), np.asarray(rb))


def test_half_move_action_space():
    env = GeneralsEnv(EnvConfig(height=5, width=5, half_moves=True))
    assert env.config.dir_actions == 9
    assert env.num_actions == 25 * 9
    s = env.reset(jax.random.PRNGKey(0))
    assert np.asarray(env.action_mask(s)).shape == (2, 25 * 9)
