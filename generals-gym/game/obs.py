"""Observations (with optional fog of war) built from the full game state."""

from __future__ import annotations

from typing import NamedTuple

import jax.numpy as jnp

from .config import MOUNTAIN, NUM_PLAYERS, EnvConfig
from .state import State
from .tables import Tables, shift_radius_one

GRID_CHANNELS = (
    "visible",        # 0  tile is inside my vision
    "own_land",       # 1
    "own_army",       # 2  log-scaled, 0 where not mine
    "enemy_land",     # 3  fogged out when invisible
    "enemy_army",     # 4  log-scaled, fogged out when invisible
    "neutral_castle", # 5  neutral castle (fogged out when invisible)
    "mountain",       # 6  mountain, or unseen mountain/castle obstacle under fog
    "own_general",    # 7
    "enemy_general",  # 8  only when visible (this is the thing you hunt)
    "own_castle",     # 9
)
NUM_GRID_CHANNELS = len(GRID_CHANNELS)

SCALAR_FEATURES = (
    "turn_frac",
    "own_land_frac",
    "enemy_land_frac",
    "own_army_frac",
    "enemy_army_frac",
    "own_castle_frac",
    "done",
)
NUM_SCALARS = len(SCALAR_FEATURES)


class Observation(NamedTuple):
    grid: jnp.ndarray      # (C, H, W) float32
    scalars: jnp.ndarray   # (S,) float32


def visible_mask(state: State, player: int, cfg: EnvConfig) -> jnp.ndarray:
    """Tiles seen by ``player``: its own tiles plus the 8-neighbourhood ring."""
    own = state.owner == player
    return shift_radius_one(own) | own


def observation(
    state: State, player: int, cfg: EnvConfig, tables: Tables
) -> Observation:
    """Everything ``player`` is allowed to know about ``state``."""
    p = int(player)
    q = 1 - p
    h, w = cfg.height, cfg.width

    vis = jnp.ones((h, w), dtype=bool) if not cfg.fog else visible_mask(state, p, cfg)

    own = state.owner == p
    enemy = (state.owner == q) & vis
    neutral_castle = state.city & (state.owner < 0) & vis
    castle = state.city & (state.owner == p)
    # Just like generals.io's TILE_FOG_OBSTACLE, mountains and castles outside
    # vision are shown as obstacles without revealing which is which.
    mountain = (state.owner == MOUNTAIN) | (state.city & ~vis)

    log_army = jnp.log1p(state.army.astype(jnp.float32)) / jnp.log1p(cfg.army_norm)

    gen_tiles = jnp.arange(cfg.num_tiles).reshape(h, w)
    enemy_general = vis & state.alive[q] & (gen_tiles == state.general[q])

    grid = jnp.stack(
        [
            vis.astype(jnp.float32),
            own.astype(jnp.float32),
            jnp.where(own, log_army, 0.0),
            enemy.astype(jnp.float32),
            jnp.where(enemy, log_army, 0.0),
            neutral_castle.astype(jnp.float32),
            mountain.astype(jnp.float32),
            (own & (gen_tiles == state.general[p])).astype(jnp.float32),
            enemy_general.astype(jnp.float32),
            castle.astype(jnp.float32),
        ],
        axis=0,
    )

    own_land = jnp.sum(own)
    enemy_land = jnp.sum(state.owner == q)
    own_army = jnp.sum(jnp.where(own, state.army, 0))
    enemy_army = jnp.sum(jnp.where(state.owner == q, state.army, 0))
    own_castles = jnp.sum(castle)
    denom = jnp.log1p(cfg.army_norm * cfg.num_tiles)

    scalars = jnp.stack(
        [
            (state.turn.astype(jnp.float32) + 0.5 * state.half_turn) / cfg.max_turns,
            own_land.astype(jnp.float32) / cfg.num_tiles,
            enemy_land.astype(jnp.float32) / cfg.num_tiles,
            jnp.log1p(own_army.astype(jnp.float32)) / denom,
            jnp.log1p(enemy_army.astype(jnp.float32)) / denom,
            own_castles.astype(jnp.float32) / max(cfg.city_count, 1),
            state.done.astype(jnp.float32),
        ]
    )
    return Observation(grid=grid, scalars=scalars)


def batch_observation(state: State, cfg: EnvConfig, tables: Tables) -> Observation:
    """Both players' observations stacked on a leading player axis."""
    obs = [observation(state, p, cfg, tables) for p in range(NUM_PLAYERS)]
    return Observation(
        grid=jnp.stack([o.grid for o in obs]),
        scalars=jnp.stack([o.scalars for o in obs]),
    )
