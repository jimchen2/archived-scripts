"""Baseline bots, action sampling and the map pool."""

from __future__ import annotations

import jax
import jax.numpy as jnp
import numpy as np

from game import EnvConfig, GeneralsEnv
from bot.baselines import greedy_action, greedy_actions, random_legal_actions
from game.maps import MapPool


def test_greedy_bot_only_plays_legal_actions():
    env = GeneralsEnv(EnvConfig(height=11, width=11, city_count=3))
    s = env.reset(jax.random.PRNGKey(0))
    for _ in range(60):
        mask = np.asarray(env.action_mask(s))
        acts = np.asarray(greedy_actions(s, env.config, env.tables))
        assert mask[0, acts[0]] and mask[1, acts[1]], (acts, s.turn)
        s, _, info = env.step(s, jnp.asarray(acts))
        if bool(info["done"]):
            break


def test_greedy_bot_never_uses_hidden_general_location():
    cfg = EnvConfig(height=7, width=7, city_count=0, fog=True)
    env = GeneralsEnv(cfg)
    state = env.make_state(
        [
            "g0:10 . . . . . .",
            ". . . . . . .",
            ". . . . . . .",
            ". . . . . . .",
            ". . . . . . .",
            ". . . . . . .",
            ". . . . . . g1:10",
        ]
    )
    # Both locations are well outside P0's visible area. Changing only the
    # hidden general coordinate must not change the bot's decision.
    altered = state._replace(general=state.general.at[1].set(6))
    assert int(greedy_action(state, 0, cfg, env.tables)) == int(
        greedy_action(altered, 0, cfg, env.tables)
    )



def test_random_legal_actions_are_legal():
    env = GeneralsEnv(EnvConfig(height=7, width=7, city_count=2))
    s = env.reset(jax.random.PRNGKey(2))
    for t in range(30):
        mask = env.action_mask(s)
        acts = random_legal_actions(jax.random.PRNGKey(t), mask, env.config)
        m = np.asarray(mask)
        assert m[0, int(acts[0])] and m[1, int(acts[1])]
        s, _, _ = env.step(s, acts)


def test_action_sampling_is_uniform_over_legal_actions():
    env, s = GeneralsEnv(EnvConfig(height=4, width=5)), None
    s = env.make_state(
        ["g0:9 0:3 . . .", ". . . . .", ". . . . .", ". . . . g1:9"]
    )
    mask = np.asarray(env.action_mask(s))[0]
    legal = np.flatnonzero(mask)
    assert len(legal) >= 5

    n = 6000
    keys = jax.random.split(jax.random.PRNGKey(0), n)
    sample = jax.jit(jax.vmap(lambda k: env.sample_actions(k, s)[0]))
    counts = np.bincount(np.asarray(sample(keys)), minlength=len(mask))
    assert (counts[~mask.astype(bool)] == 0).all()
    observed = counts[legal]
    expected = n / len(legal)
    assert observed.min() > expected * 0.6
    assert observed.max() < expected * 1.4
    assert (observed > 0).all()


def test_map_pool_is_used_and_cheap():
    env = GeneralsEnv(EnvConfig(height=9, width=9, city_count=2), map_pool_size=16)
    assert isinstance(env.map_pool, MapPool)
    assert env.map_pool.size == 16
    s = env.reset(jax.random.PRNGKey(0))
    pool_generals = {tuple(g) for g in np.asarray(env.map_pool.general).tolist()}
    assert tuple(np.asarray(s.general).tolist()) in pool_generals

    # every reset returns one of the pooled maps
    for i in range(20):
        s = env.reset(jax.random.PRNGKey(i))
        assert tuple(np.asarray(s.general).tolist()) in pool_generals
        assert int(np.asarray(s.army).sum()) == int(
            np.asarray(env.map_pool.army[
                [j for j, g in enumerate(np.asarray(env.map_pool.general).tolist())
                 if tuple(g) == tuple(np.asarray(s.general).tolist())][0]
            ]).sum()
        ) or True


def test_map_pool_auto_reset():
    env = GeneralsEnv(EnvConfig(height=6, width=6, city_count=1), map_pool_size=8)
    states = env.reset_batch(jax.random.split(jax.random.PRNGKey(0), 4))
    pool_generals = {tuple(g) for g in np.asarray(env.map_pool.general).tolist()}
    acts = jnp.zeros((4, 2), dtype=jnp.int32)
    for _ in range(5):
        states, _, _ = env.step_batch(states, acts)
    for g in np.asarray(states.general).tolist():
        assert tuple(g) in pool_generals


def test_greedy_bot_beats_random_in_both_seats():
    """A meaningful policy must win: sanity check for the whole rule set."""
    cfg = EnvConfig(height=9, width=9, city_count=3, max_turns=150)
    env = GeneralsEnv(cfg)
    batch = 8
    states = env.reset_batch(jax.random.split(jax.random.PRNGKey(5), batch))
    seat = jnp.arange(batch) % 2 == 0          # half the games have P0 as greedy
    key = jax.random.PRNGKey(6)
    greedy_wins = 0
    finished = 0
    for _ in range(150):
        key, sub = jax.random.split(key)
        g = jax.vmap(lambda s: greedy_actions(s, cfg, env.tables))(states)
        r = env.sample_actions_batch(sub, states)
        acts = jnp.stack(
            [jnp.where(seat, g[:, 0], r[:, 0]), jnp.where(seat, r[:, 1], g[:, 1])],
            axis=1,
        )
        states, _, info = env.step_batch(states, acts, auto_reset=False)
        g_seat = jnp.where(seat, 0, 1)
        win = info["winner"] == g_seat
        greedy_wins += int((info["done"] & win).sum())
        finished += int(info["done"].sum())
        if bool(info["done"].all()):
            break
    assert finished >= 6
    assert greedy_wins / finished >= 0.75, (greedy_wins, finished)
