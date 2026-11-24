"""Map generation and map parsing.

Maps are generated to look like generals.io duel maps:

* ~20% of the tiles are mountains,
* a handful of neutral castles with 40-50 armies each,
* two generals that are far apart, with no castle right next to a general.

The generator uses a *fixed* number of vectorised greedy picks instead of
rejection-sampling loops, so a whole batch of maps can be regenerated inside a
``jax.lax.cond`` (auto-reset) without dominating the runtime.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import NamedTuple

import jax
import jax.numpy as jnp
import numpy as np

from .config import MOUNTAIN, NEUTRAL, EnvConfig
from .tables import Tables

_BIG = 1_000_000.0


class MapPool(NamedTuple):
    """A batch of pre-generated maps.

    Sampling episodes from a pool makes ``auto_reset`` essentially free: no map
    has to be generated on the hot path.
    """

    army: jax.Array    # (P, H, W) int32
    owner: jax.Array   # (P, H, W) int32
    city: jax.Array    # (P, H, W) bool
    general: jax.Array  # (P, 2) int32

    @property
    def size(self) -> int:
        return int(self.army.shape[0])


def _greedy_pick(score, valid0, coords, min_distance, count, n):
    """Pick ``count`` tiles greedily from a random priority order.

    ``valid0`` is the initial legality mask (passable, far from generals, ...).
    ``coords`` is ``(rows, cols)`` tile coordinates; each pick must be at least
    ``min_distance`` (Manhattan) away from every earlier pick.
    Returns the ``(n,)`` boolean mask of the chosen tiles and their ``(count,)``
    indices (``-1`` for picks that could not be placed).
    """
    min_d = jnp.int32(min_distance)
    rows, cols = coords

    def body(i, carry):
        taken, picked, valid, indices = carry
        free = valid & ~taken
        # Relaxed fallback: if the distance constraint makes a pick impossible
        # (tiny boards, high mountain density), ignore it rather than fail.
        relaxed = valid0 & ~taken
        use_relaxed = ~free.any() & relaxed.any()
        choices = jnp.where(use_relaxed, relaxed, free)
        idx = jnp.argmax(jnp.where(choices, score, -1.0))
        take = choices.any()

        taken = taken.at[idx].set(taken[idx] | take)
        picked = picked.at[idx].set(take)
        indices = indices.at[i].set(jnp.where(take, idx, -1))
        # Cheaper than gathering a whole row of the N x N distance matrix.
        d = jnp.abs(rows - rows[idx]) + jnp.abs(cols - cols[idx])
        valid = valid & (d >= min_d)
        return taken, picked, valid, indices

    taken = jnp.zeros((n,), dtype=bool)
    picked = jnp.zeros((n,), dtype=bool)
    indices = jnp.full((count,), -1, dtype=jnp.int32)
    _, picked, _, indices = jax.lax.fori_loop(
        0, count, body, (taken, picked, valid0, indices)
    )
    return picked, indices


def generate_map(key: jax.Array, cfg: EnvConfig, tables: Tables):
    """Generate a random generals.io style map.

    Returns ``(army, owner, city, general)`` with shapes ``(H, W) int32``,
    ``(H, W) int32``, ``(H, W) bool`` and ``(2,) int32``.
    """
    n = cfg.num_tiles
    k_terrain, k_gen, k_city, k_army = jax.random.split(key, 4)
    coords = tables.coords

    mountains = jax.random.uniform(k_terrain, (n,)) < cfg.mountain_frac
    passable = ~mountains

    # --- generals: two far-apart picks -----------------------------------
    general_score = jax.random.uniform(k_gen, (n,))
    max_dist = (cfg.height - 1) + (cfg.width - 1)
    generals, general_idx = _greedy_pick(
        general_score, passable, coords, min(cfg.general_min_dist, max_dist), 2, n
    )

    # --- castles: kept away from the generals and from each other --------
    g0, g1 = general_idx[0], general_idx[1]
    rows, cols = coords
    d_gen = jnp.minimum(
        jnp.abs(rows - rows[g0]) + jnp.abs(cols - cols[g0]),
        jnp.abs(rows - rows[g1]) + jnp.abs(cols - cols[g1]),
    )
    valid_cities = passable & ~generals & (d_gen >= cfg.city_general_min_dist)
    city_score = jax.random.uniform(k_city, (n,))
    city, _ = _greedy_pick(
        city_score, valid_cities, coords, cfg.city_city_min_dist, cfg.city_count, n
    )

    # --- armies ----------------------------------------------------------
    lo, hi = cfg.city_min_army, cfg.city_max_army
    # ``uniform`` + floor is much cheaper than ``randint`` (which rejection
    # samples internally); the distribution is identical for a small range.
    city_army = (
        lo + jnp.floor(jax.random.uniform(k_army, (n,)) * (hi - lo + 1))
    ).astype(jnp.int32)

    tile_ids = jnp.arange(n)
    owner = jnp.full((n,), NEUTRAL, dtype=jnp.int32)
    owner = jnp.where(mountains, MOUNTAIN, owner)
    army = jnp.where(city, city_army, jnp.int32(0))
    army = jnp.where(mountains, jnp.int32(0), army)

    is_g0 = tile_ids == g0
    is_g1 = tile_ids == g1
    owner = jnp.where(is_g0, 0, jnp.where(is_g1, 1, owner))
    army = jnp.where(
        is_g0 | is_g1, cfg.general_start_army, army
    )

    city = city & ~mountains & ~is_g0 & ~is_g1

    shape = (cfg.height, cfg.width)
    return (
        army.reshape(shape),
        owner.reshape(shape),
        city.reshape(shape),
        jnp.stack([g0, g1]).astype(jnp.int32),
    )


def generate_pool(size: int, cfg: EnvConfig, tables: Tables, key: jax.Array) -> MapPool:
    """Generate ``size`` maps in one go (see :class:`MapPool`)."""
    if size < 1:
        raise ValueError("map pool size must be >= 1")
    keys = jax.random.split(key, size)
    army, owner, city, general = jax.vmap(lambda k: generate_map(k, cfg, tables))(keys)
    return MapPool(army=army, owner=owner, city=city, general=general)


# ---------------------------------------------------------------------------
# Explicit maps (handy for tests / reproducible experiments)
# ---------------------------------------------------------------------------
_NEUTRAL_TOKENS = {".", "-"}


def parse_rows(rows: Sequence[str]) -> dict:
    """Parse a compact ASCII layout into ``owner`` / ``army`` / ``city`` / ``general``.

    Tokens are whitespace separated, one per tile::

        "#"        mountain
        "."        neutral, 0 armies
        "C"        neutral castle holding 40 armies ("C:43" for another value)
        "c1:6"     castle owned by player 1 holding 6 armies
        "g0:12"    general of player 0 holding 12 armies   ("g1:7", "g0" == 1 army)
        "0:12"     player 0 land holding 12 armies
        "-1:5"     neutral land holding 5 armies

    Example::

        rows = [
            "g0:1 . # .",
            ".    C . g1:1",
        ]
    """
    grid = [row.split() for row in rows]
    h = len(grid)
    w = len(grid[0])
    if any(len(r) != w for r in grid):
        raise ValueError("all rows must have the same number of tiles")

    owner = np.full((h, w), NEUTRAL, dtype=np.int32)
    army = np.zeros((h, w), dtype=np.int32)
    city = np.zeros((h, w), dtype=bool)
    general = [-1, -1]

    for r, row in enumerate(grid):
        for c, tok in enumerate(row):
            if tok == "#":
                owner[r, c] = MOUNTAIN
            elif tok in _NEUTRAL_TOKENS:
                pass
            elif tok == "C" or tok.startswith("C:"):
                city[r, c] = True
                army[r, c] = int(tok[2:]) if tok.startswith("C:") else 40
            elif tok[0] == "c":
                city[r, c] = True
                o, a = tok[1:].split(":") if ":" in tok else (tok[1:], "40")
                owner[r, c] = int(o)
                army[r, c] = int(a)
            elif tok[0] == "g":
                player = int(tok[1])
                army[r, c] = int(tok[3:]) if tok[2:3] == ":" else 1
                owner[r, c] = player
                general[player] = r * w + c
            else:
                o, a = tok.split(":")
                owner[r, c] = int(o)
                army[r, c] = int(a)

    if min(general) < 0:
        raise ValueError("layout must contain a general for each player (g0 / g1)")
    return {
        "army": jnp.asarray(army),
        "owner": jnp.asarray(owner),
        "city": jnp.asarray(city),
        "general": jnp.asarray(general, dtype=jnp.int32),
    }
