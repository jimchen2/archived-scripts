"""Border encoding, shield, and wall-death attribution unit tests.

Includes a regression test for the out-of-bounds bug: spec.py used to
measure clearance from (grd/2, grd/2) while the live client keeps the border
circle at (grd, grd) radius flux_grd.  A live probe on 2026-09-27 measured
grd=32550, flux=9506, snake at (33486, 26724):
  true clearance  = +3605 units (safe)   -> old obs[13] = -0.33 ("critical")
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from slither_gym import qstate
from slither_gym.qstate import N_STATES, advise_center, border_geometry, border_shield, discretize, wall_death
from slither_gym.spec import vectorize

GRD, FLUX = 32550.0, 9506.0
CENTER = (GRD, GRD)


def mkjs(x, y, ang=0.0, sp=6.0, score=None):
    js = {
        "grd": GRD,
        "flux_grd": FLUX,
        "score": score if score is not None else 100.0,
        "self": {"xx": x, "yy": y, "ang": ang, "eang": ang, "sp": sp, "sc": 1.0, "sct": 2, "fam": 5.0},
        "foods": [],
        "snakes": [],
        "preys": [],
    }
    return js


def true_clear(x, y):
    return FLUX - math.hypot(x - CENTER[0], y - CENTER[1])


# ---------------------------------------------------------------------------
# geometry regression
# ---------------------------------------------------------------------------

def test_live_probe_geometry():
    """The exact numbers from the live probe: mid-map must read as SAFE."""
    x, y = 33486.0, 26724.0  # measured live position
    assert true_clear(x, y) > 3500.0  # very safe in reality
    obs = vectorize(mkjs(x, y))
    # new encoding: obs[13] is clearance / flux
    assert abs(float(obs[13]) - true_clear(x, y) / FLUX) < 1e-6
    s, feats = discretize(obs, FLUX)
    assert feats["border_bin"] == 0, f"mid-map must be border bin 0, got {feats['border_bin']}"
    assert feats["clearance"] > 3500.0


def test_old_encoding_was_wrong():
    """The pre-fix formula (center at grd/2, grd/2) reports garbage."""
    x, y = 33486.0, 26724.0
    old_clear = FLUX - math.hypot(x - GRD / 2, y - GRD / 2)
    assert old_clear < 0, "the old feature said 'critical' while truly safe"


def test_near_wall_reads_critical_with_correct_center_direction():
    # 200 units inside the wall, on the +x side of the circle, heading +x (out)
    r = FLUX - 200.0
    x, y = CENTER[0] + r, CENTER[1]
    assert true_clear(x, y) == 200.0
    obs = vectorize(mkjs(x, y, ang=0.0))
    s, feats = discretize(obs, FLUX)
    assert feats["border_bin"] >= 3, "200 units from the wall must be critical"
    # direction to center relative to heading(0) is pi -> sector 4
    assert feats["border_bin"] == 3 + 4, "center is directly behind: sector 4"
    # heading inward (pi) instead: center dead ahead -> sector 0
    obs2 = vectorize(mkjs(x, y, ang=math.pi))
    _, feats2 = discretize(obs2, FLUX)
    assert feats2["border_bin"] == 3 + 0
    # heading tangentially (pi/2): center is to the right -> sector 2
    obs3 = vectorize(mkjs(x, y, ang=math.pi / 2))
    _, feats3 = discretize(obs3, FLUX)
    assert feats3["border_bin"] == 3 + 2


def test_border_bin_bands():
    for clear, bin_ in [(2500.0, 0), (1500.0, 1), (600.0, 2), (100.0, 3)]:
        x = CENTER[0] + (FLUX - clear)
        obs = vectorize(mkjs(x, CENTER[1]))
        _, feats = discretize(obs, FLUX)
        assert feats["border_bin"] == bin_ or (bin_ == 3 and feats["border_bin"] >= 3), (
            f"clearance {clear} expected bin>={bin_}, got {feats['border_bin']}"
        )


# ---------------------------------------------------------------------------
# shield
# ---------------------------------------------------------------------------

def test_shield_off_midmap():
    geo = border_geometry(mkjs(CENTER[0], CENTER[1]))
    allowed, level = border_shield(geo)
    assert level == "soft"
    assert allowed == set(range(16)), "mid-map everything is allowed"


def test_shield_blocks_outward_near_wall():
    # 250 units inside the +x wall, cruising speed 300
    r = FLUX - 250.0
    geo = border_geometry(mkjs(CENTER[0] + r, CENTER[1]), speed_hint=300.0)
    allowed, level = border_shield(geo)
    assert level == "hard"
    assert 8 not in allowed and 9 not in allowed, "no boost in the hard zone"
    # outward headings (k=0 is +x) must be vetoed
    assert 0 not in allowed
    # inward heading (k=4, -x) must survive
    assert 4 in allowed
    # tangential (k=2, +y) is allowed: cos(90-0)=0 <= 0.25
    assert 2 in allowed


def test_shield_soft_vetoes_exiting_lookahead():
    # 1200 units from the wall heading straight at it: soft zone, the
    # look-ahead (300*1.7+120=630 -> still inside) - heading allowed;
    # boost doubles-ish distance, still allowed. At 700 units the plain
    # heading probe exits -> vetoed, inward survives.
    r = FLUX - 700.0
    geo = border_geometry(mkjs(CENTER[0] + r, CENTER[1]), speed_hint=300.0)
    allowed, level = border_shield(geo)
    assert level == "soft"
    assert 0 not in allowed, "heading straight out at 700 units must be vetoed"
    assert 4 in allowed, "inward heading must stay legal"
    # boost variants of allowed headings are still fine this far out
    assert 4 + 8 in allowed


def test_shield_adapts_to_map_size():
    """Small server map (grd=16384, flux=7000): bins must be unit-based."""
    js = {"grd": 16384.0, "flux_grd": 7000.0,
          "self": {"xx": 16384.0 + 6900.0, "yy": 16384.0, "ang": 0.0, "sp": 6.0, "sc": 1.0}}
    geo = border_geometry(js, speed_hint=300.0)
    assert abs(geo.clearance - 100.0) < 1e-6
    allowed, level = border_shield(geo)
    assert level == "hard" and 0 not in allowed and 4 in allowed


def test_advise_center_points_inward():
    r = FLUX - 300.0
    a = advise_center(mkjs(CENTER[0] + r, CENTER[1]))
    assert a == 4, "on the +x side of the circle, steer -x (action 4, 180deg)"
    # action k points at k*45deg; on the -y side the center lies in +y (90deg)
    a2 = advise_center(mkjs(CENTER[0], CENTER[1] - r))
    assert a2 == 2


def test_wall_death_attribution():
    r = FLUX - 90.0
    assert wall_death(mkjs(CENTER[0] + r, CENTER[1])) is True
    assert wall_death(mkjs(CENTER[0], CENTER[1])) is False
    assert wall_death(None) is False


def test_state_space_size():
    assert N_STATES == 9 * 3 * 11 * 3 * 9 * 2


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  {fn.__name__} ok")
    print(f"{len(fns)} qstate tests passed")
