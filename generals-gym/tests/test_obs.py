"""Observation / fog-of-war tests."""

from __future__ import annotations

import jax
import numpy as np

from game import (
    GRID_CHANNELS,
    NUM_GRID_CHANNELS,
    NUM_SCALARS,
    EnvConfig,
    GeneralsEnv,
    visible_mask,
)
from game.obs import batch_observation


def _env(rows, **kw):
    h, w = len(rows), len(rows[0].split())
    env = GeneralsEnv(EnvConfig(height=h, width=w, **kw))
    return env, env.make_state(rows)


def test_shapes_and_finiteness():
    env = GeneralsEnv()
    state = env.reset(jax.random.PRNGKey(0))
    obs = env.observe(state, 0)
    assert obs.grid.shape == (NUM_GRID_CHANNELS, 21, 21)
    assert obs.scalars.shape == (NUM_SCALARS,)
    assert obs.grid.dtype == np.float32
    assert np.isfinite(np.asarray(obs.grid)).all()
    assert np.isfinite(np.asarray(obs.scalars)).all()
    assert np.asarray(obs.grid).min() >= 0.0
    assert len(GRID_CHANNELS) == NUM_GRID_CHANNELS

    both = batch_observation(state, env.config, env.tables)
    assert both.grid.shape == (2, NUM_GRID_CHANNELS, 21, 21)
    assert both.scalars.shape == (2, NUM_SCALARS)


def test_fog_reveals_own_tiles_and_eight_neighbour_ring():
    rows = [
        "g0:5 . . . .",
        ". . . . .",
        ". . . . .",
        ". . . . .",
        ". . . . g1:5",
    ]
    env, s = _env(rows)
    vis = np.asarray(visible_mask(s, 0, env.config))
    expected = np.zeros((5, 5), dtype=bool)
    expected[0:2, 0:2] = True  # own tile + diagonal ring
    assert np.array_equal(vis, expected)


def test_enemy_general_is_hidden_in_fog():
    hidden = ["g0:5 . .", ". . .", ". . g1:5"]
    env, s = _env(hidden, fog=True)
    obs = env.observe(s, 0)
    assert np.asarray(obs.grid[GRID_CHANNELS.index("enemy_general")]).sum() == 0
    assert np.asarray(obs.grid[GRID_CHANNELS.index("enemy_land")]).sum() == 0

    seen = ["g0:5 . .", ". g1:5 .", ". . ."]
    env, s = _env(seen, fog=True)
    obs = env.observe(s, 0)
    gen_channel = np.asarray(obs.grid[GRID_CHANNELS.index("enemy_general")])
    assert gen_channel[1, 1] == 1.0
    assert gen_channel.sum() == 1.0


def test_no_fog_reveals_everything():
    rows = ["g0:5 . .", ". # .", ". . g1:5"]
    env, s = _env(rows, fog=False)
    obs = env.observe(s, 0)
    grid = np.asarray(obs.grid)
    assert grid[GRID_CHANNELS.index("visible")].all()
    assert grid[GRID_CHANNELS.index("enemy_general")].sum() == 1.0
    assert grid[GRID_CHANNELS.index("mountain")].sum() == 1.0
    assert grid[GRID_CHANNELS.index("enemy_land")].sum() == 1.0


def test_scalars_track_the_scoreboard():
    env, s = _env(
        ["g0:5 0:9 .", ". . .", ". . g1:2"], fog=True, city_count=4, max_turns=100
    )
    obs = env.observe(s, 0)
    scalars = np.asarray(obs.scalars)
    assert np.isclose(scalars[1], 2 / 9)   # own land fraction
    assert np.isclose(scalars[2], 1 / 9)   # enemy land fraction
    assert np.isclose(scalars[0], 0.0)     # turn / max_turns


def test_turn_scalar_tracks_half_turn_progress():
    env = GeneralsEnv(EnvConfig(height=3, width=3, max_turns=10))
    state = env.make_state(
        ["g0:1 . .", ". . .", ". . g1:1"], turn=4, half_turn=1
    )
    obs = np.asarray(env.observe(state, 0).scalars)
    assert np.isclose(obs[0], 4.5 / 10)


def test_enemy_observations_are_mirrored():
    grid = [["."] * 9 for _ in range(9)]
    grid[0][0], grid[0][1], grid[1][1] = "g0:5", "0:3", "0:2"
    grid[7][6], grid[8][8] = "1:2", "g1:5"
    rows = [" ".join(r) for r in grid]
    env, s = _env(rows)
    o0 = env.observe(s, 0)
    o1 = env.observe(s, 1)
    own0 = np.asarray(o0.grid[GRID_CHANNELS.index("own_land")])
    own1 = np.asarray(o1.grid[GRID_CHANNELS.index("own_land")])
    enemy1 = np.asarray(o1.grid[GRID_CHANNELS.index("enemy_land")])
    state_owner = np.asarray(s.owner)
    assert np.array_equal(own0, (state_owner == 0).astype(np.float32))
    assert np.array_equal(own1, (state_owner == 1).astype(np.float32))
    # the generals are far apart: neither player can see the other's land
    assert enemy1.sum() == 0
    assert np.asarray(o0.grid[GRID_CHANNELS.index("enemy_general")]).sum() == 0
    assert np.asarray(o1.grid[GRID_CHANNELS.index("enemy_general")]).sum() == 0
    # own land is always visible to its owner, whatever the fog says
    assert (own0 + 1e-6 >= enemy1).all()
    assert np.asarray(o0.grid[GRID_CHANNELS.index("own_general")]).sum() == 1.0
    assert np.asarray(o1.grid[GRID_CHANNELS.index("own_general")]).sum() == 1.0


def test_fog_reveals_distant_mountains_and_castles_as_obstacles():
    rows = [
        "g0:5 C:40 . . . . #",
        "#    .    . . . . .",
        ".    .    . . . . .",
        ".    .    . . . . .",
        ".    .    . . . . c1:15",
        ".    .    . . . 1:10 .",
        "C:42 .    . . . . g1:5",
    ]
    env, s = _env(rows, fog=True)
    grid = np.asarray(env.observe(s, 0).grid)

    vis = grid[GRID_CHANNELS.index("visible")]
    mountain = grid[GRID_CHANNELS.index("mountain")]
    neutral_castle = grid[GRID_CHANNELS.index("neutral_castle")]
    enemy_land = grid[GRID_CHANNELS.index("enemy_land")]
    enemy_army = grid[GRID_CHANNELS.index("enemy_army")]
    enemy_general = grid[GRID_CHANNELS.index("enemy_general")]

    # Visible adjacent neutral castle (0, 1) and visible adjacent mountain (1, 0).
    assert vis[0, 1] == 1.0 and neutral_castle[0, 1] == 1.0 and mountain[0, 1] == 0.0
    assert vis[1, 0] == 1.0 and mountain[1, 0] == 1.0 and neutral_castle[1, 0] == 0.0

    # Distant mountain (0, 6), distant neutral castle (6, 0), and distant enemy
    # castle (4, 6) are all marked on the obstacle/mountain channel without
    # leaking castle type, ownership, or army.
    for r, c in ((0, 6), (6, 0), (4, 6)):
        assert vis[r, c] == 0.0
        assert mountain[r, c] == 1.0
        assert neutral_castle[r, c] == 0.0
        assert enemy_land[r, c] == 0.0
        assert enemy_army[r, c] == 0.0

    # Distant plain land, enemy normal land (5, 5), and enemy general (6, 6) stay hidden.
    for r, c in ((3, 3), (5, 5), (6, 6)):
        assert vis[r, c] == 0.0
        assert mountain[r, c] == 0.0
        assert enemy_land[r, c] == 0.0
        assert enemy_general[r, c] == 0.0


def test_ascii_state_marks_fog_obstacles():
    from game import ascii_state

    env, s = _env(
        [
            "g0:5 . . . #",
            ".    . . . .",
            ".    . . . .",
            ".    . . . .",
            "C:40 . . . g1:5",
        ],
        fog=True,
    )
    rendered = ascii_state(s, env.config, player=0)
    board_lines = rendered.splitlines()[1:6]
    # Distant mountain at (0, 4) and distant castle at (4, 0) show as '^',
    # while distant plain/general tiles remain '?'.
    assert "^" in board_lines[0]
    assert "^" in board_lines[4]
    assert "?" in board_lines[2]


