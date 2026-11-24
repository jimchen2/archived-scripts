"""Map generation and layout parsing tests."""

from __future__ import annotations

import jax
import numpy as np

from game import EnvConfig, GeneralsEnv
from game.config import MOUNTAIN, NEUTRAL
from game.maps import generate_map, parse_rows
from game.tables import build_tables


def _batch_of_maps(cfg, n=24):
    tables = build_tables(cfg)
    keys = jax.random.split(jax.random.PRNGKey(0), n)
    return jax.vmap(lambda k: generate_map(k, cfg, tables))(keys)


def test_map_properties():
    cfg = EnvConfig()
    army, owner, city, general = _batch_of_maps(cfg)
    army = np.asarray(army)
    owner = np.asarray(owner)
    city = np.asarray(city)
    general = np.asarray(general)

    n, h, w = owner.shape
    assert army.shape == owner.shape == city.shape == (n, h, w)
    assert general.shape == (n, 2)

    for i in range(n):
        g = general[i]
        flat_owner = owner[i].reshape(-1)
        assert g[0] != g[1]
        assert flat_owner[g[0]] == 0 and flat_owner[g[1]] == 1
        assert flat_owner[g[0]] != MOUNTAIN and flat_owner[g[1]] != MOUNTAIN

        r0, c0 = divmod(int(g[0]), w)
        r1, c1 = divmod(int(g[1]), w)
        assert abs(r0 - r1) + abs(c0 - c1) >= cfg.general_min_dist

        cities = np.argwhere(city[i])
        assert len(cities) == cfg.city_count
        for r, c in cities:
            idx = r * w + c
            assert idx not in (g[0], g[1])
            assert owner[i, r, c] == NEUTRAL
            assert cfg.city_min_army <= army[i, r, c] <= cfg.city_max_army
            assert abs(r - r0) + abs(c - c0) >= cfg.city_general_min_dist
            assert abs(r - r1) + abs(c - c1) >= cfg.city_general_min_dist

        mountains = (owner[i] == MOUNTAIN).mean()
        assert 0.10 <= mountains <= 0.32, mountains
        # generals start with one army, everything else is untouched
        assert army[i].reshape(-1)[g[0]] == 1
        assert army[i].reshape(-1)[g[1]] == 1
        neutral = owner[i] == NEUTRAL
        assert (army[i][neutral] == 0).sum() == int(neutral.sum()) - cfg.city_count


def test_same_key_same_map():
    cfg = EnvConfig()
    tables = build_tables(cfg)
    a = generate_map(jax.random.PRNGKey(7), cfg, tables)
    b = generate_map(jax.random.PRNGKey(7), cfg, tables)
    for x, y in zip(a, b):
        assert np.array_equal(np.asarray(x), np.asarray(y))


def test_small_board_with_many_castles():
    cfg = EnvConfig(
        height=8,
        width=8,
        city_count=6,
        general_min_dist=3,
        city_general_min_dist=1,
        city_city_min_dist=1,
        mountain_frac=0.1,
    )
    army, owner, city, general = _batch_of_maps(cfg, n=4)
    for i in range(4):
        assert int(city[i].sum()) == cfg.city_count
        assert len(set(np.asarray(general[i]).tolist())) == 2


def test_parse_rows_roundtrip():
    rows = [
        "g0:5 . # C:41",
        "c1:3 0:12 -1:7 .",
        "g1:2 . . .",
    ]
    parsed = parse_rows(rows)
    cfg = EnvConfig(height=3, width=4)
    env = GeneralsEnv(cfg)
    state = env.make_state(rows)
    assert np.asarray(state.owner).tolist() == [
        [0, NEUTRAL, MOUNTAIN, NEUTRAL],
        [1, 0, NEUTRAL, NEUTRAL],
        [1, NEUTRAL, NEUTRAL, NEUTRAL],
    ]
    assert np.asarray(state.army).tolist() == [
        [5, 0, 0, 41],
        [3, 12, 7, 0],
        [2, 0, 0, 0],
    ]
    assert np.asarray(state.city).tolist() == [
        [False, False, False, True],
        [True, False, False, False],
        [False, False, False, False],
    ]
    assert np.asarray(state.general).tolist() == [0, 8]
    assert parsed["general"].tolist() == [0, 8]
