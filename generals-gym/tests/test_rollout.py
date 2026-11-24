"""Tests for rollout helpers: reward potentials and auto-reset."""

from __future__ import annotations

import jax
import jax.numpy as jnp
import numpy as np

from game import EnvConfig, GeneralsEnv
from src.rollout import _general_distance, _potential


def test_general_distance_decreases_when_closer():
    env = GeneralsEnv(EnvConfig(height=5, width=5), map_pool_size=0)

    far = env.make_state([
        "g0:1 . . . .",
        ". . . . .",
        ". . . . .",
        ". . . . .",
        ". . . . g1:1",
    ])
    near = env.make_state([
        "g0:1 . . . .",
        ". . . . .",
        ". . . . .",
        ". . . . 0:1",
        ". . . . g1:1",
    ])
    d_far = _general_distance(far, env.tables, 0)
    d_near = _general_distance(near, env.tables, 0)
    assert int(d_far) == 8          # (0,0) -> (4,4)
    assert int(d_near) == 1         # (3,4) -> (4,4)


def test_potential_rewards_closeness():
    env = GeneralsEnv(EnvConfig(height=5, width=5), map_pool_size=0)
    far = env.make_state([
        "g0:1 . . . .",
        ". . . . .",
        ". . . . .",
        ". . . . .",
        ". . . . g1:1",
    ])
    near = env.make_state([
        "g0:1 . . . .",
        ". . . . .",
        ". . . . .",
        ". . . . 0:1",
        ". . . . g1:1",
    ])
    cfg = EnvConfig(height=5, width=5)
    p_far = _potential(far, cfg, env.tables, distance_coef=1.0)
    p_near = _potential(near, cfg, env.tables, distance_coef=1.0)
    assert float(p_near[0]) > float(p_far[0])


def test_reset_where_resets_only_finished_envs():
    env = GeneralsEnv(EnvConfig(height=5, width=5), map_pool_size=8, seed=0)
    states = env.reset_batch(jax.random.split(jax.random.PRNGKey(0), 2))
    states = states._replace(turn=jnp.asarray([5, 7], dtype=jnp.int32))

    reset = env.reset_where(states, jnp.asarray([True, False]))
    assert int(reset.turn[0]) == 0
    assert int(reset.turn[1]) == 7
    assert np.array_equal(np.asarray(reset.owner[1]), np.asarray(states.owner[1]))
