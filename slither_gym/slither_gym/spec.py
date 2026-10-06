"""Flat observation built only from the JavaScript state dict.

Nothing here reads pixels. Missing entities are zeros. Distances are in
game units divided by VIEW_SCALE so nearby food and snakes are not washed
out by the 16384-wide map.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

N_DIRS = 8
N_FOOD = 16
N_SNAKES = 8
N_PREY = 4
VIEW_SCALE = 1000.0

SELF_DIM = 14
WORLD_DIM = 6
FOOD_DIM = N_FOOD * 3
SNAKE_DIM = N_SNAKES * 6
PREY_DIM = N_PREY * 2
OBS_DIM = SELF_DIM + WORLD_DIM + FOOD_DIM + SNAKE_DIM + PREY_DIM

# Layout, in order:
# self[14]: in_match, x/grd, y/grd, cos(ang), sin(ang), cos(eang), sin(eang),
#           sp/14, sc, sct/200, fam, score/5000, boost, border_clearance/flux_grd
#           (border = circle at (grd, grd) radius flux_grd; clearance is the
#            fraction of the radius left, 0 = touching the wall)
# world[6]: rank/100, slither_count/200, foods_c/800, gsc, dead_flag, orphan_flag
# food[16*3]: dx/VIEW_SCALE, dy/VIEW_SCALE, sz/30
# snakes[8*6]: dx, dy, cos(ang), sin(ang), sc, nearest_body/VIEW_SCALE
# prey[4*2]: dx, dy


def decode_action(action: int) -> tuple[float, bool]:
    """Map Discrete(16) to (angle radians, boost).

    0..7  are eight headings, no boost.
    8..15 are the same headings with boost held.
    Angle 0 points to the right, matching the client's atan2(ym, xm).
    """
    action = int(action)
    if action < 0 or action >= N_DIRS * 2:
        raise ValueError(f"action must be in [0, {N_DIRS * 2}), got {action}")
    direction = action % N_DIRS
    boost = action >= N_DIRS
    return direction * (2.0 * math.pi / N_DIRS), boost


def _f(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(out):
        return default
    return out


def _dist(ax: float, ay: float, bx: float, by: float) -> float:
    return math.hypot(ax - bx, ay - by)


def _nearest_body(snake: dict, sx: float, sy: float) -> float:
    best = _dist(sx, sy, _f(snake.get("xx")), _f(snake.get("yy")))
    for pt in snake.get("pts") or []:
        best = min(best, _dist(sx, sy, _f(pt.get("xx")), _f(pt.get("yy"))))
    return best


def vectorize(js: dict | None, *, dead: bool = False, orphan: bool = False) -> np.ndarray:
    """Project a JS snapshot into the fixed observation vector."""
    obs = np.zeros(OBS_DIM, dtype=np.float32)
    if not js:
        if dead:
            obs[SELF_DIM + 4] = 1.0
        if orphan:
            obs[SELF_DIM + 5] = 1.0
        return obs

    self_ = js.get("self") or None
    # Border geometry, verified against the live client (s/game1107249518.js):
    # the playable area is a circle CENTERED AT (grd, grd) with RADIUS flux_grd.
    #   minimap:  mmrad*(slither.xx-grd)/flux_grd
    #   border:   xx = grd + cos(view_ang +/- ...)*flux_grd
    #   view:     sqrt((view_xx-grd)^2 + (view_yy-grd)^2)
    # flux_grd arrives in the welcome packet (default grd*.98) and can be
    # resized later through "z" packets.  It is NOT centered at (grd/2, grd/2).
    grd = _f(js.get("grd"), 0.0)
    if grd <= 0.0:
        grd = 16384.0
    flux = _f(js.get("flux_grd"), 0.0)
    if flux <= 0.0:
        flux = grd * 0.98
    cursor = 0

    if self_:
        xx = _f(self_.get("xx"))
        yy = _f(self_.get("yy"))
        ang = _f(self_.get("ang"))
        eang = _f(self_.get("eang"), ang)
        cx = grd
        cy = grd
        clearance = flux - math.hypot(xx - cx, yy - cy)
        obs[0] = 0.0 if dead else 1.0
        obs[1] = xx / grd
        obs[2] = yy / grd
        obs[3] = math.cos(ang)
        obs[4] = math.sin(ang)
        obs[5] = math.cos(eang)
        obs[6] = math.sin(eang)
        obs[7] = _f(self_.get("sp")) / 14.0
        obs[8] = _f(self_.get("sc"), 1.0)
        obs[9] = _f(self_.get("sct")) / 200.0
        obs[10] = _f(self_.get("fam"))
        obs[11] = _f(js.get("score")) / 5000.0
        obs[12] = 1.0 if (self_.get("md") or self_.get("wmd")) else 0.0
        # Fraction of the border RADIUS remaining (1.0 = centered, 0 = on the
        # wall, negative = outside).  Normalized by flux, not grd, so the
        # meaning is stable across servers that send different map sizes.
        obs[13] = clearance / flux
    cursor = SELF_DIM

    obs[cursor + 0] = _f(js.get("rank")) / 100.0
    obs[cursor + 1] = _f(js.get("slither_count")) / 200.0
    obs[cursor + 2] = _f(js.get("foods_c")) / 800.0
    obs[cursor + 3] = _f(js.get("gsc"))
    obs[cursor + 4] = 1.0 if dead else 0.0
    obs[cursor + 5] = 1.0 if orphan else 0.0
    cursor += WORLD_DIM

    if self_:
        sx = _f(self_.get("xx"))
        sy = _f(self_.get("yy"))
        for i, food in enumerate((js.get("foods") or [])[:N_FOOD]):
            base = cursor + i * 3
            obs[base] = (_f(food.get("xx")) - sx) / VIEW_SCALE
            obs[base + 1] = (_f(food.get("yy")) - sy) / VIEW_SCALE
            obs[base + 2] = _f(food.get("sz")) / 30.0
        cursor += FOOD_DIM
        for i, snake in enumerate((js.get("snakes") or [])[:N_SNAKES]):
            base = cursor + i * 6
            obs[base] = (_f(snake.get("xx")) - sx) / VIEW_SCALE
            obs[base + 1] = (_f(snake.get("yy")) - sy) / VIEW_SCALE
            ang = _f(snake.get("ang"))
            obs[base + 2] = math.cos(ang)
            obs[base + 3] = math.sin(ang)
            obs[base + 4] = _f(snake.get("sc"), 1.0)
            obs[base + 5] = _nearest_body(snake, sx, sy) / VIEW_SCALE
        cursor += SNAKE_DIM
        for i, prey in enumerate((js.get("preys") or [])[:N_PREY]):
            base = cursor + i * 2
            obs[base] = (_f(prey.get("xx")) - sx) / VIEW_SCALE
            obs[base + 1] = (_f(prey.get("yy")) - sy) / VIEW_SCALE
    return obs
