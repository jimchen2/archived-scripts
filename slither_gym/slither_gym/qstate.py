"""Shared Q-learning state encoding + border safety for slither_gym.

``scripts/train_long.py`` imports this module for BC collection and Q-learning,
so both phases use the same border-aware state encoding.

Why this module exists
----------------------
The original discretization read ``obs[13]`` (border clearance) computed by
``spec.vectorize`` with the border circle assumed to be centered at
``(grd/2, grd/2)``.  The live client keeps the border at ``(grd, grd)`` with
radius ``flux_grd`` (see the comment in spec.py), so the old feature was
saturated at "critical" for most of the map and read "safe" near part of the
actual wall.  A live probe on 2026-09-27 (grd=32550, flux=9506) showed a true
clearance of +3605 units reported as obs[13] = -0.33.  The Q-learner could not
tell the middle of the map from the wall, which is why snakes kept dying out
of bounds.

This module provides:

  discretize(obs, flux)   fixed state encoding; border bins are in GAME UNITS
                          (speed x reaction time), not fractions of a map that
                          changes size between servers.
  border_geometry(js)     live circle/pos/heading/speed from a JS snapshot.
  border_shield(geo, ...) action mask that makes running out of bounds
                          impossible: any heading whose near-future path exits
                          the circle is vetoed while the snake is close.
  advise_center(js)       fallback action for unvisited border-critical
                          states: steer toward the map center.
  wall_death(js)          attributes a death to the border (clearance ~ 0).

Thresholds are grounded in measured gameplay: cruise speed ~270 units/s
(~40 units per 0.15 s step); a snake needs roughly 1-2 s to turn around.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np

# ---------------------------------------------------------------------------
# Action space (must match spec.decode_action)
# ---------------------------------------------------------------------------
N_ACT = 16
N_DIRS = 8
SECTOR = math.pi / 4.0

# ---------------------------------------------------------------------------
# Discretization
#   food_dir(9) x food_dist(3) x border(11) x threat_dist(3) x threat_dir(9) x size(2)
#
#   food_dir    8 sectors relative to heading + "no food seen"
#   food_dist   near <300 / mid <800 / far            (game units)
#   border      0: clear   > 1800 u  (~6.7 s of cruise)
#               1: warn    900-1800  (~3.3-6.7 s)
#               2: near    350-900   (~1.3-3.3 s)
#               3..10: critical <350 u, split by the 8 sectors of
#                      "direction to map center" relative to heading
#               (sector 0 = center is dead ahead, 4 = heading straight out)
#   threat_dist nearest enemy body: close <300 / mid <800 / far
#   threat_dir  8 sectors to that body + none
#   size        score < 100 / >= 100
# ---------------------------------------------------------------------------
FOOD_DIR_N, FOOD_DIST_N, BORDER_N, THREAT_DIST_N, THREAT_DIR_N, SIZE_N = 9, 3, 11, 3, 9, 2
N_STATES = FOOD_DIR_N * FOOD_DIST_N * BORDER_N * THREAT_DIST_N * THREAT_DIR_N * SIZE_N

FOOD0, SNAKE0 = 14 + 6, 14 + 6 + 16 * 3  # obs offsets from spec.py
VIEW_SCALE = 1000.0

# border bins in game units (cruise ~270 u/s)
BORDER_SAFE_U = 1800.0
BORDER_WARN_U = 900.0
BORDER_NEAR_U = 350.0

# shield tuning (game units / seconds)
SHIELD_REACTION_S = 1.7      # how far ahead the veto looks, in travel time
SHIELD_MARGIN_U = 130.0      # probes must stay this far inside the wall
SHIELD_HARD_U = 300.0        # inside this: only inward/tangential headings
SHIELD_HARD_MAX_OUT = 0.25   # allowed outward radial component in hard mode
SHIELD_NO_BOOST_U = 600.0    # never boost below this clearance
SHIELD_MAX_LOOKAHEAD_U = 1100.0
DEFAULT_SPEED_U = 300.0      # used until a live speed estimate exists
GEOM_VERSION = 2             # bump when the state encoding changes


def _sector(rel: float) -> int:
    """Relative angle -> one of 8 sectors matching decode_action's headings."""
    return int(round(rel / SECTOR)) % 8


@dataclass
class BorderGeometry:
    cx: float
    cy: float
    flux: float
    x: float
    y: float
    ang: float
    speed: float

    @property
    def clearance(self) -> float:
        return self.flux - math.hypot(self.x - self.cx, self.y - self.cy)

    @property
    def radial_angle(self) -> float:
        """Angle pointing OUT of the map (center -> head direction)."""
        return math.atan2(self.y - self.cy, self.x - self.cx)

    def clearance_at(self, px: float, py: float) -> float:
        return self.flux - math.hypot(px - self.cx, py - self.cy)


def border_geometry(js: dict | None, speed_hint: float | None = None) -> Optional[BorderGeometry]:
    """Extract the live border circle + own motion from a JS snapshot.

    ``speed_hint`` is a measured units/second estimate (the training loop keeps
    one); without it we fall back to a conservative default.
    """
    if not js:
        return None
    self_ = js.get("self") or None
    if not self_:
        return None
    grd = float(js.get("grd") or 0.0)
    flux = float(js.get("flux_grd") or 0.0)
    if grd <= 0.0:
        grd = 16384.0
    if flux <= 0.0:
        flux = grd * 0.98
    speed = float(speed_hint or DEFAULT_SPEED_U)
    if not math.isfinite(speed) or speed <= 0.0:
        speed = DEFAULT_SPEED_U
    return BorderGeometry(
        cx=grd,
        cy=grd,
        flux=flux,
        x=float(self_.get("xx") or 0.0),
        y=float(self_.get("yy") or 0.0),
        ang=float(self_.get("ang") or 0.0),
        speed=min(speed, 900.0),
    )


def border_shield(geo: Optional[BorderGeometry]) -> tuple[set[int], str]:
    """Veto every action whose near-future path exits the border circle.

    Returns (allowed_actions, level):
      level "off"    geo missing -> everything allowed
      level "soft"   probe-based veto (look-ahead along each heading)
      level "hard"   clearance < SHIELD_HARD_U: only inward/tangential
                     headings survive; boost is disabled; if nothing
                     survives, the single most inward heading is kept.
    """
    all_actions = set(range(N_ACT))
    if geo is None:
        return all_actions, "off"

    clear = geo.clearance
    if not math.isfinite(clear):
        return all_actions, "off"

    look = min(SHIELD_REACTION_S * geo.speed + 120.0, SHIELD_MAX_LOOKAHEAD_U)
    allowed: set[int] = set()
    for k in range(N_DIRS):
        theta = k * SECTOR
        px = geo.x + math.cos(theta) * look
        py = geo.y + math.sin(theta) * look
        if geo.clearance_at(px, py) > SHIELD_MARGIN_U:
            allowed.add(k)

    level = "soft"
    if not allowed:
        # pathological tiny map: keep the most inward heading rather than
        # returning an empty set
        rad = geo.radial_angle
        allowed = {min(range(N_DIRS), key=lambda k: math.cos(k * SECTOR - rad))}
    if clear < SHIELD_HARD_U:
        level = "hard"
        rad = geo.radial_angle
        keep = {
            k
            for k in allowed
            if math.cos(k * SECTOR - rad) <= SHIELD_HARD_MAX_OUT
        }
        if not keep:
            # everything points badly out: keep the single most inward heading
            best = min(range(N_DIRS), key=lambda k: math.cos(k * SECTOR - rad))
            keep = {best}
        allowed = keep

    if clear < SHIELD_NO_BOOST_U:
        # boost narrows the options and doubles the speed: forbid it
        return allowed, level
    return allowed | {k + N_DIRS for k in allowed}, level


def advise_center(js: dict | None) -> Optional[int]:
    """Action that steers straight toward the map center (no boost)."""
    geo = border_geometry(js)
    if geo is None:
        return None
    to_center = math.atan2(geo.cy - geo.y, geo.cx - geo.x)
    return _sector(to_center)  # absolute action sector, no boost


def wall_death(js: dict | None) -> bool:
    """True if the last known position was essentially on the border."""
    geo = border_geometry(js)
    if geo is None:
        return False
    return geo.clearance < 200.0


def discretize(obs: np.ndarray, flux: float) -> tuple[int, dict]:
    """Fixed projection of an observation vector into a tabular state id.

    ``flux`` is the live border radius in game units (info["js"]["flux_grd"]);
    it converts obs[13] (clearance / flux) back into game units so the border
    bins mean the same physical warning time on every server.
    """
    obs = np.asarray(obs, dtype=np.float64)
    heading = math.atan2(float(obs[4]), float(obs[3]))

    # --- nearest "worthwhile" food (value = size / distance) ---------------
    food_dir, food_dist = 8, 2
    best_val = -1.0
    for i in range(16):
        b = FOOD0 + i * 3
        dx, dy, sz = float(obs[b]), float(obs[b + 1]), float(obs[b + 2])
        if abs(dx) < 1e-6 and abs(dy) < 1e-6:
            continue  # empty slot (spec zeroes missing entities)
        dist = math.hypot(dx, dy) * VIEW_SCALE
        val = (0.25 + sz) / (0.15 + dist / VIEW_SCALE)
        if val > best_val:
            best_val = val
            food_dir = _sector(math.atan2(dy, dx) - heading)
            food_dist = 0 if dist < 300 else (1 if dist < 800 else 2)

    # --- border: clearance bins in game units; critical bin keeps the
    #     direction back to the center (the real center is (grd, grd), i.e.
    #     normalized (1, 1), NOT (0.5, 0.5)) --------------------------------
    clearance = float(obs[13]) * flux  # fraction of radius -> game units
    if clearance > BORDER_SAFE_U:
        border = 0
    elif clearance > BORDER_WARN_U:
        border = 1
    elif clearance > BORDER_NEAR_U:
        border = 2
    else:
        to_center = math.atan2(1.0 - float(obs[2]), 1.0 - float(obs[1])) - heading
        border = 3 + _sector(to_center)

    # --- nearest enemy body -------------------------------------------------
    threat_dist, threat_dir = 2, 8
    min_body = 1e18
    hx = hy = 0.0
    for i in range(8):
        b = SNAKE0 + i * 6
        dx, dy, nb = float(obs[b]), float(obs[b + 1]), float(obs[b + 5])
        if abs(dx) < 1e-6 and abs(dy) < 1e-6:
            continue
        d = nb * VIEW_SCALE
        if d < min_body:
            min_body = d
            hx, hy = dx, dy
    if min_body < 1e17:
        min_body = max(0.0, min_body)
        threat_dist = 0 if min_body < 300 else (1 if min_body < 800 else 2)
        if threat_dist < 2:
            threat_dir = _sector(math.atan2(hy, hx) - heading)
    danger_frac = max(0.0, (300.0 - min(min_body, 300.0)) / 300.0) if min_body < 1e17 else 0.0
    danger_frac = min(1.0, danger_frac)

    size = 0 if float(obs[11]) < 0.02 else 1

    idx = food_dir
    idx = idx * FOOD_DIST_N + food_dist
    idx = idx * BORDER_N + border
    idx = idx * THREAT_DIST_N + threat_dist
    idx = idx * THREAT_DIR_N + threat_dir
    idx = idx * SIZE_N + size
    return idx, {
        "danger_frac": danger_frac,
        "clearance": clearance,
        "border_bin": border,
    }


def flux_from_info(info: dict) -> float:
    """Live border radius from an env info dict, with sane fallbacks."""
    js = (info or {}).get("js") or {}
    grd = float(js.get("grd") or 0.0)
    flux = float(js.get("flux_grd") or 0.0)
    if grd <= 0.0:
        grd = 16384.0
    if flux <= 0.0:
        flux = grd * 0.98
    return flux
