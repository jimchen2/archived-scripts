"""Pre-computed lookup tables (static, numpy) shared by the JAX kernels."""

from __future__ import annotations

from typing import NamedTuple

import jax.numpy as jnp
import numpy as np

from .config import DOWN, LEFT, PASS, RIGHT, UP, EnvConfig


class Tables(NamedTuple):
    """Static arrays closed over by the jitted step/reset functions."""

    dst: jnp.ndarray       # (dir_actions, num_tiles) int32, -1 for pass / off-board
    half: jnp.ndarray      # (dir_actions,) bool
    adjacent: jnp.ndarray  # (num_tiles, num_tiles) bool, 4-neighbour adjacency
    distances: jnp.ndarray  # (num_tiles, num_tiles) int32 Manhattan distance
    coords: tuple  # (rows, cols) int32, tile coordinates


def build_tables(cfg: EnvConfig) -> Tables:
    h, w, n = cfg.height, cfg.width, cfg.num_tiles
    rows = np.repeat(np.arange(h), w)
    cols = np.tile(np.arange(w), h)

    dst = np.full((cfg.dir_actions, n), -1, dtype=np.int32)
    half = np.zeros((cfg.dir_actions,), dtype=bool)

    # Direction codes 1..4 (and 5..8 for the half-army variants).
    base_dirs = {UP: (-1, 0), DOWN: (1, 0), LEFT: (0, -1), RIGHT: (0, 1)}
    for code, (dr, dc) in base_dirs.items():
        r = rows + dr
        c = cols + dc
        ok = (r >= 0) & (r < h) & (c >= 0) & (c < w)
        dst[code] = np.where(ok, r * w + c, -1).astype(np.int32)
    if cfg.half_moves:
        for code in base_dirs:
            dst[code + 4] = dst[code]
            half[code + 4] = True
    assert dst[PASS].max() == -1 and not half[PASS]

    dr = np.abs(rows[:, None] - rows[None, :])
    dc = np.abs(cols[:, None] - cols[None, :])
    dist = (dr + dc).astype(np.int32)
    adjacent = dist == 1

    return Tables(
        dst=jnp.asarray(dst),
        half=jnp.asarray(half),
        adjacent=jnp.asarray(adjacent),
        distances=jnp.asarray(dist),
        coords=(jnp.asarray(rows, dtype=jnp.int32), jnp.asarray(cols, dtype=jnp.int32)),
    )


def shift_radius_one(mask: jnp.ndarray) -> jnp.ndarray:
    """8-neighbourhood dilation of a (H, W) boolean mask (keeps the centre)."""
    h, w = mask.shape
    p = jnp.pad(mask, 1, mode="constant", constant_values=False)
    out = p[0:h, 0:w]
    for dr in range(3):
        for dc in range(3):
            if dr == 1 and dc == 1:
                continue
            out = out | p[dr : dr + h, dc : dc + w]
    return out
