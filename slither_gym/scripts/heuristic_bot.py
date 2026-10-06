"""Heuristic slither.io policy + recorded-episode runner.

Strategy, in priority order:
  1. Survive  - steer away from the map border and other snakes' bodies.
                Bodies are checked as segments between the bridge's sampled
                points, so long snakes cannot slip through sampling gaps.
  2. Eat      - drift toward nearby food, skipping food that sits in a danger
                zone next to an enemy body (classic trap bait).
  3. Boost    - only with a clear lane and fuel (fam), or to escape.

Consumes info["js"] (self / foods / snakes / grd / flux_grd) and returns a
Discrete(16) action for SlitherIOEnv. Records the browser viewport to webm.
"""

from __future__ import annotations

import argparse
import math
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from slither_gym import SlitherIOEnv

# ---------------------------------------------------------------------------
# tuning constants (game units; map is ~16384 wide)
# ---------------------------------------------------------------------------
N_CANDIDATES = 8                      # one per action direction
PROBES = (60.0, 140.0, 240.0, 360.0, 500.0)   # look-ahead points along a heading
PROBE_W = (3.2, 2.4, 1.6, 1.0, 0.55)          # nearer probes matter more
LOOKAHEAD = 520.0                     # ignore enemy geometry beyond this
WALL_MARGIN = 300.0                   # start avoiding border this far out
W_WALL = 60.0
W_BODY = 26.0
W_FOOD = 7.0
W_CENTER = 3.0
W_SMOOTH = 1.4
BODY_R = 13.0                         # snake radius ~= 13 * sc
COLLIDE_PAD = 16.0                    # safety padding around bodies
PANIC_DIST = 8.0                      # extra pad that triggers flee mode

TWO_PI = 2.0 * math.pi
SECTOR = math.pi / 4.0


def _wrap(a: float) -> float:
    """Wrap angle to [-pi, pi)."""
    return (a + math.pi) % TWO_PI - math.pi


def _seg_dist(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    """Distance from point p to segment ab."""
    vx, vy = bx - ax, by - ay
    wx, wy = px - ax, py - ay
    denom = vx * vx + vy * vy
    t = 0.0 if denom == 0.0 else max(0.0, min(1.0, (wx * vx + wy * vy) / denom))
    return math.hypot(wx - t * vx, wy - t * vy)


class World:
    """Enemy geometry + border extracted from one js snapshot."""

    def __init__(self, js: dict):
        self_ = js.get("self") or {}
        self.hx = float(self_.get("xx") or 0.0)
        self.hy = float(self_.get("yy") or 0.0)
        self.ang = float(self_.get("ang") or 0.0)
        self.sc = max(0.4, float(self_.get("sc") or 1.0))
        self.fam = float(self_.get("fam") or 0.0)
        self.own_r = BODY_R * self.sc

        # The live client (s/game1107249518.js) keeps the border as a circle
        # centered at (grd, grd) with radius flux_grd, which pulses over time:
        # minimap uses mmrad*(slither.xx-grd)/flux_grd, view code measures
        # sqrt((xx-grd)^2+(yy-grd)^2).  NOT centered at grd/2.
        grd = float(js.get("grd") or 16384.0)
        self.cx, self.cy = grd, grd
        self.flux = float(js.get("flux_grd") or 0.0) or grd * 0.98

        # enemy bodies as (ax, ay, bx, by, radius, head_weight) segments
        self.segs: list[tuple[float, float, float, float, float, float]] = []
        for sn in js.get("snakes") or []:
            if sn.get("dead"):
                continue
            r = BODY_R * max(0.4, float(sn.get("sc") or 1.0))
            pts = [(float(p["xx"]), float(p["yy"]))
                   for p in (sn.get("pts") or [])
                   if p.get("xx") is not None and p.get("yy") is not None]
            head = (float(sn.get("xx")), float(sn.get("yy")))
            pts.append(head)
            # heads that point roughly at us deserve extra respect
            dang = _wrap(math.atan2(self.hy - head[1], self.hx - head[0])
                         - float(sn.get("ang") or 0.0))
            head_w = 1.6 if abs(dang) < 0.6 else 1.0
            for i in range(len(pts) - 1):
                w = head_w if i >= len(pts) - 2 else 1.0
                self.segs.append((pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], r, w))
            if len(pts) == 1:
                p = pts[0]
                self.segs.append((p[0], p[1], p[0], p[1], r, head_w))

        # nearest-food list, with trap detection against enemy geometry
        self.foods: list[tuple[float, float, float, bool]] = []
        for f in (js.get("foods") or [])[:12]:
            fx, fy = float(f.get("xx") or 0.0), float(f.get("yy") or 0.0)
            sz = float(f.get("sz") or 0.0)
            trapped = any(
                _seg_dist(fx, fy, a, b, c, d) < r + 90.0
                for (a, b, c, d, r, _w) in self.segs
            )
            self.foods.append((fx, fy, sz, trapped))

    # ------------------------------------------------------------------
    def seg_distance(self, px: float, py: float) -> float:
        """Distance from a point to the nearest enemy body segment."""
        best = 1e18
        for (a, b, c, d, _r, _w) in self.segs:
            dist = _seg_dist(px, py, a, b, c, d)
            if dist < best:
                best = dist
        return best

    def border_clearance(self, px: float, py: float) -> float:
        return self.flux - math.hypot(px - self.cx, py - self.cy)


class HeuristicPolicy:
    """Greedy direction scoring over the 8 action headings."""

    def __init__(self) -> None:
        self._last_action = 0
        self._last_angle = 0.0

    # ------------------------------------------------------------------
    def act(self, js: dict) -> tuple[int, dict]:
        if not js or not js.get("self"):
            return self._last_action, {"mode": "blind"}
        w = World(js)

        # --- panic: contact imminent -> run perpendicular to the threat
        nearest = w.seg_distance(w.hx, w.hy)
        touch = min((s[4] for s in w.segs), default=0.0)
        clearance = w.border_clearance(w.hx, w.hy)
        if w.segs and nearest < w.own_r + touch + PANIC_DIST:
            away = self._flee_angle(w)
            action = self._sector(away, boost=True)
            return self._remember(action, away), {"mode": "panic", "dist": nearest}
        if clearance < w.own_r + 20.0:  # hugging the border
            toward_center = math.atan2(w.cy - w.hy, w.cx - w.hx)
            action = self._sector(toward_center, boost=False)
            return self._remember(action, toward_center), {"mode": "border", "clear": clearance}

        # --- score every candidate heading
        best_score, best_ang, best_dbg = -1e18, w.ang, {}
        food_ang, food_gain = self._best_food(w)
        for i in range(N_CANDIDATES):
            ang = i * SECTOR
            score, dbg = self._score_direction(w, ang, food_ang, food_gain)
            if score > best_score:
                best_score, best_ang, best_dbg = score, ang, dbg

        boost = self._boost_decision(w, best_ang, best_dbg, food_gain)
        action = self._sector(best_ang, boost=boost)
        return self._remember(action, best_ang), {
            "mode": "boost" if boost else "cruise",
            "score": round(best_score, 1),
            "nearest_danger": round(best_dbg.get("nearest", 1e9), 1),
            "food": bool(food_ang is not None),
        }

    # ------------------------------------------------------------------
    def _score_direction(self, w: World, ang: float,
                         food_ang: float | None, food_gain: float) -> tuple[float, dict]:
        cos_a, sin_a = math.cos(ang), math.sin(ang)
        score = 0.0
        nearest = 1e18
        lane_clear = True

        for u, pw in zip(PROBES, PROBE_W):
            px, py = w.hx + cos_a * u, w.hy + sin_a * u

            # border: quadratic-ish penalty once inside the margin
            clear = w.border_clearance(px, py)
            if clear <= 0:
                score -= 1e6
            elif clear < WALL_MARGIN:
                score -= W_WALL * pw * ((WALL_MARGIN - clear) / WALL_MARGIN) ** 1.5

            # enemy bodies: angular-width test, penalty grows as we close in
            for (a, b, c, d, r, seg_w) in w.segs:
                dist = _seg_dist(px, py, a, b, c, d)
                if dist < nearest:
                    nearest = dist
                reach = w.own_r + r + COLLIDE_PAD
                if dist < reach:
                    score -= 1e6            # probe lands on a body: fatal lane
                elif dist < reach * 3.0 and u < LOOKAHEAD:
                    score -= W_BODY * pw * seg_w * (1.0 - dist / (reach * 3.0))
                    if u <= PROBES[2] and dist < 140.0:
                        lane_clear = False

        # food attraction inside a +/-28-degree cone of this heading
        if food_ang is not None:
            delta = abs(_wrap(food_ang - ang))
            if delta < 0.5:
                score += W_FOOD * food_gain * math.cos(delta)

        # gentle pull toward the middle of the map
        to_c = w.border_clearance(w.hx, w.hy) / max(w.flux, 1.0)
        mid_ang = math.atan2(w.cy - w.hy, w.cx - w.hx)
        score += W_CENTER * max(0.0, math.cos(_wrap(mid_ang - ang))) * (1.0 - to_c)

        # slight preference for the current heading (less jitter)
        score += W_SMOOTH * math.cos(_wrap(ang - w.ang))

        return score, {"nearest": nearest, "lane_clear": lane_clear}

    def _best_food(self, w: World) -> tuple[float | None, float]:
        """Angle + value of the most attractive safe food, or (None, 0)."""
        best_gain, best_ang = 0.0, None
        for fx, fy, sz, trapped in w.foods:
            dx, dy = fx - w.hx, fy - w.hy
            dist = math.hypot(dx, dy)
            if dist < 5.0 or dist > 520.0:
                continue
            gain = (0.35 + sz / 5.0) * (1.0 - dist / 620.0)
            if trapped:
                gain *= 0.15
            if gain > best_gain:
                best_gain, best_ang = gain, math.atan2(dy, dx)
        return best_ang, best_gain

    def _boost_decision(self, w: World, ang: float, dbg: dict, food_gain: float) -> bool:
        if w.fam < 10.0:
            return False
        # never boost into a busy lane
        if not dbg.get("lane_clear", False):
            return False
        nearest = dbg.get("nearest", 1e18)
        if nearest < 300.0:
            return False
        # boost toward a rewarding food patch, otherwise hold fuel
        if food_gain > 0.35:
            cos_a, sin_a = math.cos(ang), math.sin(ang)
            px, py = w.hx + cos_a * 260.0, w.hy + sin_a * 260.0
            if w.border_clearance(px, py) > WALL_MARGIN * 0.6:
                return True
        return False

    def _flee_angle(self, w: World) -> float:
        """Head away from the nearest body segment, biased toward open space."""
        best_ang, best_score = w.ang, -1e18
        for i in range(N_CANDIDATES):
            ang = i * SECTOR
            cos_a, sin_a = math.cos(ang), math.sin(ang)
            px, py = w.hx + cos_a * 120.0, w.hy + sin_a * 120.0
            s = w.seg_distance(px, py) * 2.0 + w.border_clearance(px, py) * 0.5
            if s > best_score:
                best_score, best_ang = s, ang
        return best_ang

    # ------------------------------------------------------------------
    def _remember(self, action: int, ang: float) -> int:
        self._last_action = action
        self._last_angle = ang
        return action

    @staticmethod
    def _sector(angle: float, boost: bool = False) -> int:
        sector = int(round(angle / SECTOR)) % N_CANDIDATES
        return sector + (8 if boost else 0)


# ---------------------------------------------------------------------------
def run_episode(args: argparse.Namespace) -> bool:
    root = Path(__file__).resolve().parents[1]
    raw_dir = root / "videos" / "raw"
    env = SlitherIOEnv(
        headless=True,
        url=args.url,
        nickname=args.nickname,
        step_seconds=args.step_seconds,
        enter_timeout=70.0,
        enter_attempts=3,
        record_video_dir=str(raw_dir),
        viewport=(1280, 720),
    )
    policy = HeuristicPolicy()
    started = time.time()
    best_score = 0.0
    steps = 0
    death = None
    blackbox: list[str] = []
    try:
        _obs, info = env.reset()
        js = info.get("js") or {}
        print(f"ENTER reason={(info.get('lifecycle') or {}).get('enter')} "
              f"pos=({(js.get('self') or {}).get('xx')}, {(js.get('self') or {}).get('yy')})",
              flush=True)
        deadline = time.time() + args.duration
        while time.time() < deadline:
            pre_js = info.get("js") or {}
            action, dbg = policy.act(pre_js)
            pre_self = pre_js.get("self") or {}
            pre_w = World(pre_js) if pre_self else None
            _obs, _reward, terminated, _truncated, info = env.step(action)
            steps += 1
            js = info.get("js") or {}
            score = js.get("score")
            if score:
                best_score = max(best_score, score)
            blackbox.append(
                f"t={time.time() - started:5.1f}s act={action:2d} "
                f"mode={str(dbg.get('mode')):6s} pos=({pre_self.get('xx', 0):.0f},"
                f"{pre_self.get('yy', 0):.0f}) ang={math.degrees(pre_self.get('ang', 0) or 0):6.1f} "
                f"near={pre_w.seg_distance(pre_w.hx, pre_w.hy) if pre_w and pre_w.segs else -1:7.1f} "
                f"wall={pre_w.border_clearance(pre_w.hx, pre_w.hy) if pre_w else -1:7.1f} "
                f"snakes={len(pre_js.get('snakes') or [])} score={score}"
            )
            del blackbox[:-40]
            if steps % 20 == 0:
                self_ = js.get("self") or {}
                alive_s = time.time() - started
                print(f"t={alive_s:5.1f}s step={steps:4d} score={score} "
                      f"len={self_.get('sct')} rank={js.get('rank')} "
                      f"mode={dbg.get('mode')}", flush=True)
            if terminated:
                death = info
                print(f"DEAD after {time.time() - started:.1f}s "
                      f"reason={info.get('end_reason')} "
                      f"record={(info.get('lifecycle') or {}).get('death')}", flush=True)
                print("--- last decisions ---", flush=True)
                for line in blackbox[-14:]:
                    print("  " + line, flush=True)
                break
        else:
            print(f"still alive after {time.time() - started:.1f}s "
                  f"(script limit {args.duration}s); recording the life so far", flush=True)
        time.sleep(2.5)  # let the death/continue screen appear in the video
    finally:
        saved = env.close()

    if saved is None or not Path(saved).exists():
        print(f"NO VIDEO (close returned {saved})", flush=True)
        return False
    out = root / "videos" / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(saved, out)
    print(f"VIDEO {out} bytes={out.stat().st_size} "
          f"life={time.time() - started:.1f}s best_score={best_score} "
          f"died={'yes' if death else 'no'}", flush=True)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=200.0,
                        help="stop stepping after this many seconds (snake keeps living)")
    parser.add_argument("--step-seconds", type=float, default=0.15)
    parser.add_argument("--nickname", default="heuristic-bot")
    parser.add_argument("--url", default="http://slither.io/")
    parser.add_argument("--out", default="heuristic_game.webm")
    parser.add_argument("--tries", type=int, default=2,
                        help="retries if entering a match fails")
    args = parser.parse_args()

    for attempt in range(1, args.tries + 1):
        try:
            if run_episode(args):
                return
        except TimeoutError as exc:
            print(f"attempt {attempt}: {exc}", flush=True)
    raise SystemExit("could not record an episode")


if __name__ == "__main__":
    main()
