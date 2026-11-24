"""Edge cases and reproducibility."""

from __future__ import annotations

import jax
import jax.numpy as jnp
import numpy as np

from game import EnvConfig, GeneralsEnv
from bot.baselines import greedy_actions
from game.config import LEFT, RIGHT


def _step(env, state, a0, a1):
    return env.step(state, jnp.asarray([a0, a1], dtype=jnp.int32))


def test_mutual_general_capture_is_a_draw():
    env = GeneralsEnv(EnvConfig(height=2, width=3))
    s = env.make_state(["g0:1 1:9 .", "g1:1 0:9 ."])
    D = env.config.dir_actions
    # P0 (1,1) -> left onto P1's general; P1 (0,1) -> left onto P0's general
    s2, rew, info = _step(env, s, (1 * 3 + 1) * D + LEFT, (0 * 3 + 1) * D + LEFT)
    assert bool(s2.done)
    assert int(s2.winner) == -1
    assert np.allclose(np.asarray(rew), 0.0)
    assert not bool(s2.alive[0]) and not bool(s2.alive[1])
    # both generals became castles
    assert bool(s2.city[0, 0]) and bool(s2.city[1, 0])


def test_general_falling_on_the_last_owned_tile_ends_the_game():
    env = GeneralsEnv(EnvConfig(height=2, width=2))
    s = env.make_state(["g0:8 g1:1", ". ."])
    D = env.config.dir_actions
    s2, rew, info = _step(env, s, 0 * 2 * D + 0 + RIGHT, 0)
    assert bool(s2.done)
    assert int(s2.winner) == 0
    assert np.allclose(np.asarray(rew), [1.0, -1.0])
    assert int(np.asarray(s2.alive).sum()) == 1


def test_parse_general_without_army_token():
    env = GeneralsEnv(EnvConfig(height=2, width=2))
    s = env.make_state(["g0 .", ". g1"])
    assert np.asarray(s.army).tolist() == [[1, 0], [0, 1]]
    assert np.asarray(s.general).tolist() == [0, 3]


def test_same_key_and_actions_reproduce_the_same_game():
    cfg = EnvConfig(height=9, width=9, city_count=3, max_turns=120)
    env = GeneralsEnv(cfg)

    def play(seed):
        s = env.reset(jax.random.PRNGKey(seed))
        frames = []
        for step in range(120):
            m = env.action_mask(s)
            # a deterministic "policy": keys derived from the turn number only
            acts = jnp.asarray(
                [
                    int(
                        jax.random.categorical(
                            jax.random.PRNGKey(step * 2 + p),
                            jnp.where(m[p], 0.0, -jnp.inf),
                        )
                    )
                    for p in range(2)
                ]
            )
            s, _, info = env.step(s, acts)
            frames.append((np.asarray(s.army).copy(), int(info["turn"]), int(info["winner"])))
            if bool(info["done"]):
                break
        return frames

    a, b = play(3), play(3)
    assert len(a) == len(b)
    for (fa, ta, wa), (fb, tb, wb) in zip(a, b):
        assert np.array_equal(fa, fb) and ta == tb and wa == wb


def test_truncation_on_a_real_map():
    cfg = EnvConfig(height=9, width=9, city_count=3, max_turns=5)
    env = GeneralsEnv(cfg)
    s = env.reset(jax.random.PRNGKey(0))
    for _ in range(10):  # two action half-turns per displayed turn
        s, rew, info = env.step(s, jnp.zeros((2,), dtype=jnp.int32))
    assert bool(info["done"])
    assert int(info["turn"]) == 5
    assert int(info["winner"]) in (-1, 0, 1)
    # no capture before the limit -> double loss, i.e. no winner
    assert int(info["winner"]) == -1


def test_dead_player_has_no_legal_actions():
    env = GeneralsEnv(EnvConfig(height=2, width=3))
    s = env.make_state(["g0:8 g1:1 .", ". . ."])
    D = env.config.dir_actions
    s2, _, _ = _step(env, s, (0 * 3 + 0) * D + RIGHT, 0)
    assert int(s2.winner) == 0
    mask = np.asarray(env.action_mask(s2))
    assert mask[1].sum() == 0


def test_zero_cost_pass_is_always_legal_even_when_boxed_in():
    env = GeneralsEnv(EnvConfig(height=3, width=3))
    s = env.make_state(["g0:1 # #", "# # #", "# # g1:1"])
    mask = np.asarray(env.action_mask(s))
    assert mask[0, 0] and mask[1, 0]
    assert mask.sum() == 2  # nothing else can move


def test_greedy_bot_is_deterministic_and_seat_symmetric():
    cfg = EnvConfig(height=11, width=11, city_count=3)
    env = GeneralsEnv(cfg)
    for seed in range(12):
        state = env.reset(jax.random.PRNGKey(seed))
        actions = greedy_actions(state, cfg, env.tables)
        np.testing.assert_array_equal(actions, greedy_actions(state, cfg, env.tables))

        swapped_owner = jnp.where(state.owner == 0, 1,
                                  jnp.where(state.owner == 1, 0, state.owner))
        swapped = state._replace(
            owner=swapped_owner,
            general=state.general[::-1],
            alive=state.alive[::-1],
        )
        np.testing.assert_array_equal(
            np.asarray(greedy_actions(swapped, cfg, env.tables)),
            np.asarray(actions)[::-1],
        )
