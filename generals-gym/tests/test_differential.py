"""Differential test: the vectorised engine vs the naive reference engine."""

from __future__ import annotations

import jax
import jax.numpy as jnp
import numpy as np
import pytest

from game import GeneralsEnv, State
from tests.reference import make_random_game


def to_state(game, key):
    return State(
        army=jnp.asarray(game.army, dtype=jnp.int32),
        owner=jnp.asarray(game.owner, dtype=jnp.int32),
        city=jnp.asarray(game.city),
        general=jnp.asarray(game.general, dtype=jnp.int32),
        alive=jnp.asarray(game.alive),
        turn=jnp.int32(game.turn),
        half_turn=jnp.int32(game.half_turn),
        winner=jnp.int32(game.winner),
        done=jnp.asarray(game.done),
        key=key,
    )


def sample(rng, mask):
    legal = np.flatnonzero(mask)
    return int(legal[rng.integers(len(legal))])


@pytest.mark.parametrize("half_moves", [False, True])
def test_random_games_match_reference(half_moves):
    steps = 0
    finished = 0
    for seed in range(8):
        rng = np.random.default_rng(seed)
        cfg, ref = make_random_game(
            rng, h=6, w=7, half_moves=half_moves, turn=int(seed % 3) * 5
        )
        env = GeneralsEnv(cfg)
        state = to_state(ref, jax.random.PRNGKey(seed))

        for _ in range(120):  # preserve 60 displayed turns at two half-turns each
            if ref.done:
                break
            jax_mask = np.asarray(env.action_mask(state))
            ref_mask = np.stack([ref.action_mask(0), ref.action_mask(1)])
            assert np.array_equal(jax_mask, ref_mask), "action masks disagree"

            acts = np.asarray(
                [sample(rng, jax_mask[0]), sample(rng, jax_mask[1])], dtype=np.int32
            )
            state, rew, _ = env.step(state, jnp.asarray(acts))
            ref_rew, _ = ref.step(acts)
            steps += 1

            assert np.array_equal(np.asarray(state.army), ref.army), "armies differ"
            assert np.array_equal(np.asarray(state.owner), ref.owner), "owners differ"
            assert np.array_equal(np.asarray(state.city), ref.city), "castles differ"
            assert np.array_equal(np.asarray(state.alive), np.asarray(ref.alive))
            assert int(state.turn) == ref.turn
            assert int(state.half_turn) == ref.half_turn
            assert bool(state.done) == ref.done
            assert int(state.winner) == ref.winner
            assert np.allclose(np.asarray(rew), ref_rew)
        finished += int(ref.done)

    assert steps > 150
    assert finished >= 6, "the random policy should finish most small games"


def test_no_army_or_ownership_corruption():
    """Fuzz with illegal actions too: state invariants must always hold."""
    cfg, _ = make_random_game(np.random.default_rng(0), h=7, w=7)
    env = GeneralsEnv(cfg)
    state = env.reset(jax.random.PRNGKey(0))
    key = jax.random.PRNGKey(1)
    for _ in range(150):
        key, k = jax.random.split(key)
        acts = jax.random.randint(k, (2,), 0, env.num_actions)  # includes illegal
        state, _, _ = env.step(state, acts)
        army = np.asarray(state.army).reshape(-1)
        owner = np.asarray(state.owner).reshape(-1)
        assert (army >= 0).all()
        assert (owner >= -2).all() and (owner <= 1).all()
        assert (army[owner == -2] == 0).all()
        general = np.asarray(state.general).reshape(-1)
        # a captured general tile is handed to the opponent (or becomes neutral
        # only if both generals fall in the same turn, which can happen).
        assert owner[general[0]] in (0, 1, -1)
        assert owner[general[1]] in (0, 1, -1)
        alive = np.asarray(state.alive)
        for p in range(2):
            assert bool(owner[general[p]] == p) == bool(alive[p])
