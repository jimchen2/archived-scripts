#!/usr/bin/env python3
"""
Long-running Q-learning for slither_gym with Behavioral Cloning warm-start.

This is the "train for a day on a server" script.

What it does:
  1. BC PHASE (optional but recommended): runs the heuristic bot for N episodes,
     records (discretized_state -> action) counts, and builds an initial Q-table
     that prefers the heuristic's choices. This gives Q-learning a quick start
     instead of starting from zeros and dying in 5 seconds for hours.

  2. Q-LEARNING PHASE: runs tabular Q-learning for up to --max-minutes (e.g. 1440
     for 24h) with robust checkpointing, auto-resume, signal handling, file logging,
     hourly snapshots, and video eval every K episodes.

Why BC helps:
  - Tabular Q starts at 0. Without BC, eps=1.0 random actions -> very short lives,
    very sparse reward, Q-table fills slowly.
  - With BC, Q(s, a_heuristic) is initialized to ~+2, others ~0, so greedy policy
    already does something sensible. You can then start epsilon at 0.5 not 1.0,
    and decay slower. Training still explores but doesn't waste a day learning
    that walls kill you.

Usage - quick start (BC + 24h Q):
  pip install -r requirements.txt
  python -m playwright install chromium --with-deps   # or chromium only
  python scripts/train_long.py --run-dir runs/q_bc_long --bc-episodes 60 --max-minutes 1440

Timed BC followed by a very long Q-learning ceiling:
  python scripts/train_long.py --run-dir runs/bc30m_qtrain --bc-episodes 1000000000 --bc-minutes 30 --max-minutes 52594920 --max-episodes 1000000000000

Resume after crash / stop:
  python scripts/train_long.py --run-dir runs/q_bc_long --max-minutes 1440
  # it auto-loads q_table.npy, state.json, bc_dataset.npz if present

Server / tmux:
  bash scripts/run_bc_then_train.sh   # launches in detached tmux session 'slither' by default
  # or manual tmux:
  tmux new -s slither -d "python scripts/train_long.py --run-dir runs/q_bc_long --bc-episodes 60 --max-minutes 1440 --video-every 25 2>&1 | tee -a runs/q_bc_long/tmux.log"
  tmux attach -t slither
  # or nohup:
  nohup python scripts/train_long.py --run-dir runs/q_bc_long --max-minutes 1440 > runs/q_bc_long/nohup.log 2>&1 &

BC collection and Q-learning both use slither_gym/qstate.py for the
border-aware state encoding.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import signal
import sys
import time
from pathlib import Path
from typing import Dict

import numpy as np

# make slither_gym importable when running as script
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from slither_gym import SlitherIOEnv  # noqa: E402
from slither_gym.spec import OBS_DIM  # noqa: E402
from slither_gym import qstate
from slither_gym.qstate import N_ACT, N_STATES, GEOM_VERSION, discretize, flux_from_info  # noqa: E402
from scripts.heuristic_bot import HeuristicPolicy  # noqa: E402


# ---------------------------------------------------------------------------
# Q Agent
# ---------------------------------------------------------------------------
class QAgent:
    def __init__(self, alpha=0.15, gamma=0.97, eps=1.0, eps_min=0.05, eps_decay=0.995):
        self.q = np.zeros((N_STATES, N_ACT), dtype=np.float32)
        self.alpha, self.gamma = alpha, gamma
        self.eps, self.eps_min, self.eps_decay = eps, eps_min, eps_decay

    def act(self, s: int, greedy: bool = False, allowed=None, advice: int | None = None) -> int:
        """Pick an action, restricted to ``allowed`` (the border shield).

        - exploration samples uniformly from the allowed set only, so
          epsilon-greedy can never ram the wall while learning.
        - for unvisited states (all-zero row) the fallback is ``advice``
          (steer to center near the border) instead of a uniform random
          action, which used to be a reliable way to die.
        """
        allowed = list(allowed) if allowed else list(range(N_ACT))
        if not allowed:
            allowed = list(range(N_ACT))
        if not greedy and np.random.random() < self.eps:
            return int(allowed[np.random.randint(len(allowed))])
        row = self.q[s]
        best, best_v = None, -np.inf
        for a in allowed:
            v = float(row[a])
            if v > best_v:
                best, best_v = a, v
        if best is None or abs(best_v) < 1e-8:
            if advice is not None and advice in allowed:
                return int(advice)
            return int(allowed[np.random.randint(len(allowed))])
        return int(best)

    def update(self, s, a, r, s2, terminal: bool):
        target = r
        if not terminal:
            target += self.gamma * float(np.max(self.q[s2]))
        self.q[s, a] += self.alpha * (target - float(self.q[s, a]))

    def decay(self):
        self.eps = max(self.eps_min, self.eps * self.eps_decay)


# ---------------------------------------------------------------------------
# BC collection
# ---------------------------------------------------------------------------
def collect_heuristic_dataset(
    run_dir: Path,
    bc_episodes: int,
    step_seconds: float,
    truncate_after: int,
    episode_minutes: float,
    log_fn,
    bc_minutes: float | None = None,
    stop_requested: dict[str, bool] | None = None,
) -> Path:
    """
    Run the heuristic bot and collect state->action counts.

    Collection stops at ``bc_episodes`` or, when set, the wall-clock
    ``bc_minutes`` budget. A time limit can end a life partway through; those
    state/action pairs are still valid BC examples. Returns the saved npz path.
    """
    dataset_path = run_dir / "bc_dataset.npz"
    counts = np.zeros((N_STATES, N_ACT), dtype=np.int32)
    visits = np.zeros((N_STATES,), dtype=np.int32)

    policy = HeuristicPolicy()
    env = None
    total_steps = 0
    episodes_done = 0
    started = time.monotonic()
    deadline = started + bc_minutes * 60.0 if bc_minutes is not None else None

    def stop_reason() -> str | None:
        if stop_requested and stop_requested.get("flag"):
            return "signal"
        if deadline is not None and time.monotonic() >= deadline:
            return "time budget"
        return None

    budget = f" or {bc_minutes:g} minutes" if bc_minutes is not None else ""
    log_fn(f"[BC] starting collection for up to {bc_episodes} episodes{budget}")

    while episodes_done < bc_episodes and stop_reason() is None:
        episodes_done += 1
        if env is None:
            env = SlitherIOEnv(
                headless=True,
                nickname=f"bc-collect-{episodes_done}",
                step_seconds=step_seconds,
                truncate_after=truncate_after,
            )
        try:
            obs, info = env.reset()
            t0 = time.time()
            ep_steps = 0
            ep_score = 0.0
            prev_pos = None
            speed_ema = qstate.DEFAULT_SPEED_U
            stopped_mid_episode = False
            while True:
                if stop_reason() is not None:
                    stopped_mid_episode = True
                    break
                js = info.get("js") or {}
                # heuristic decides from js
                action, dbg = policy.act(js)
                # border shield: never let the teacher (or the dataset) fly out
                geo = qstate.border_geometry(js, speed_hint=speed_ema)
                allowed, level = qstate.border_shield(geo)
                if action not in allowed:
                    fixed = qstate.advise_center(js)
                    action = fixed if fixed is not None and fixed in allowed else (sorted(allowed)[0] if allowed else action)
                flux = flux_from_info(info)
                s, _ = discretize(obs, flux)
                counts[s, action] += 1
                visits[s] += 1
                total_steps += 1
                ep_steps += 1

                obs, reward, terminated, truncated, info = env.step(action)
                # live speed estimate for the shield's look-ahead distance
                cur = ((info.get("js") or {}).get("self") or {})
                if cur.get("xx") is not None and prev_pos is not None:
                    dt = step_seconds
                    v = math.hypot(float(cur["xx"]) - prev_pos[0], float(cur["yy"]) - prev_pos[1]) / max(dt, 1e-3)
                    if v < 1500.0:
                        speed_ema = 0.8 * speed_ema + 0.2 * v
                if cur.get("xx") is not None:
                    prev_pos = (float(cur["xx"]), float(cur["yy"]))
                ep_score = max(ep_score, float((info.get("js") or {}).get("score") or 0.0))

                episode_limit = (time.time() - t0) > episode_minutes * 60
                stop_cause = stop_reason()
                if terminated or truncated or episode_limit or stop_cause is not None:
                    stopped_mid_episode = stop_cause is not None and not (terminated or truncated or episode_limit)
                    log_fn(
                        f"[BC ep {episodes_done:03d}] steps={ep_steps:4d} score={ep_score:6.1f} "
                        f"mode={dbg.get('mode')} total_collected={total_steps}"
                        f"{' partial=' + stop_cause if stopped_mid_episode else ''}"
                    )
                    break
            if stopped_mid_episode and ep_steps == 0:
                log_fn(f"[BC ep {episodes_done:03d}] stopped before first action ({stop_reason()})")
        except Exception as exc:
            log_fn(f"[BC ep {episodes_done:03d}] FAILED {type(exc).__name__}: {exc} - retrying after 5s")
            try:
                if env is not None:
                    env.close()
            except Exception:
                pass
            env = None
            episodes_done -= 1  # don't count failed
            if stop_reason() is None:
                time.sleep(5)
            continue

        # save incremental every episode
        np.savez_compressed(
            dataset_path,
            counts=counts,
            visits=visits,
            episodes=episodes_done,
            total_steps=total_steps,
        )

    if env is not None:
        try:
            env.close()
        except Exception:
            pass

    if total_steps == 0:
        raise RuntimeError("BC collected no state/action pairs; check that the game connection is working")

    log_fn(
        f"[BC] done. saved {dataset_path} - states covered "
        f"{np.count_nonzero(visits)}/{N_STATES} steps {total_steps} "
        f"elapsed={(time.monotonic() - started) / 60.0:.1f}min"
    )
    return dataset_path


def build_q_from_counts(
    counts: np.ndarray,
    scale: float = 2.0,
    bonus: float = 1.0,
    smoothing: float = 0.0,
) -> np.ndarray:
    """
    Convert count matrix [N_STATES, N_ACT] to initial Q-table.

    - For each state with visits, Q = (count / total) * scale
    - Best action gets extra bonus
    - smoothing adds uniform small mass to avoid zero ties (optional)

    This is behavioral cloning via Q-initialization, not a full policy network,
    but very effective for tabular Q.
    """
    q = np.zeros((N_STATES, N_ACT), dtype=np.float32)
    for s in range(N_STATES):
        total = int(np.sum(counts[s]))
        if total == 0:
            continue
        # normalized frequencies
        freq = counts[s].astype(np.float32) / total
        q[s] = freq * scale
        best_a = int(np.argmax(counts[s]))
        q[s, best_a] += bonus
        if smoothing > 0:
            q[s] += smoothing
            q[s, best_a] += bonus * 0.5  # keep best distinct
    return q


# ---------------------------------------------------------------------------
# Training loop helpers
# ---------------------------------------------------------------------------
def make_logger(log_file: Path):
    log_file.parent.mkdir(parents=True, exist_ok=True)
    fh = open(log_file, "a", buffering=1)

    def log(msg: str):
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
        print(line, flush=True)
        try:
            fh.write(line + "\n")
            fh.flush()
        except Exception:
            pass

    return log, fh


def save_all(run_dir: Path, agent: QAgent, state: dict, log_fn=None):
    # atomic save
    tmp = run_dir / "q_table.tmp.npy"
    np.save(tmp, agent.q)
    os.replace(tmp, run_dir / "q_table.npy")
    (run_dir / "state.json").write_text(json.dumps(state, indent=2))
    if log_fn:
        log_fn(f"[ckpt] saved episode={state['episode']} eps={agent.eps:.4f} best={state['best_score']:.1f}")


def play_episode(env, agent, *, greedy: bool, max_seconds: float, use_shield: bool = True):
    """One episode of (shielded) Q-learning.

    Out-of-bounds protection, three layers:
      1. the shield vetoes any action whose look-ahead path exits the border
         circle (soft far away, hard + no-boost when critical);
      2. unvisited border-critical states fall back to "steer to center"
         instead of a random action;
      3. the shaped reward penalizes proximity to the wall and tags deaths
         that happen on the border as wall deaths (extra penalty), so the
         Q-values themselves learn to keep away even without the shield.
    """
    obs, info = env.reset()
    flux = flux_from_info(info)
    s, feats = discretize(obs, flux)
    total, start = 0.0, time.time()
    prev_score = float((info.get("js") or {}).get("score") or 0.0)
    steps = 0
    prev_pos = None
    speed_ema = qstate.DEFAULT_SPEED_U
    stats = {
        "shield_overrides": 0,     # policy/exploration wanted a vetoed action
        "shield_hard_steps": 0,    # steps spent inside the hard zone
        "border_steps": 0,         # steps with border bin >= 1
        "min_clearance": 1e9,      # game units
        "wall_death": False,
    }
    while True:
        js = info.get("js") or {}
        geo = qstate.border_geometry(js, speed_hint=speed_ema)
        if use_shield:
            allowed, level = qstate.border_shield(geo)
        else:
            allowed, level = None, "off"
        if level == "hard":
            stats["shield_hard_steps"] += 1
        advice = qstate.advise_center(js) if feats.get("border_bin", 0) >= 3 else None

        a = agent.act(s, greedy=greedy, allowed=allowed, advice=advice)
        if allowed is not None and a not in allowed:
            # numerically impossible, but never trust a wall
            a = sorted(allowed)[0]
        if allowed is not None:
            # "policy wanted out of bounds": the greedy choice was vetoed
            row = agent.q[s]
            if float(np.abs(row).sum()) > 1e-8 and int(np.argmax(row)) not in allowed:
                stats["shield_overrides"] += 1

        obs, r, term, trunc, info = env.step(a)
        flux = flux_from_info(info)
        s2, feats2 = discretize(obs, flux)
        if feats2.get("border_bin", 0) >= 1:
            stats["border_steps"] += 1
        clear2 = feats2.get("clearance", 1e9)
        stats["min_clearance"] = min(stats["min_clearance"], clear2)

        # live speed estimate for the shield's look-ahead distance
        cur = (info.get("js") or {}).get("self") or {}
        if cur.get("xx") is not None and prev_pos is not None:
            v = math.hypot(float(cur["xx"]) - prev_pos[0], float(cur["yy"]) - prev_pos[1]) / max(env.step_seconds, 1e-3)
            if v < 1500.0:
                speed_ema = 0.8 * speed_ema + 0.2 * v
        if cur.get("xx") is not None:
            prev_pos = (float(cur["xx"]), float(cur["yy"]))

        # --- shaped reward -------------------------------------------------
        # env: survival + score + death.  extra: enemy-proximity danger,
        # boost cost, wall proximity, and an extra penalty for dying ON the
        # border so wall deaths are strictly worse than snake deaths.
        shaped = r - 0.03 * feats2.get("danger_frac", 0.0) - (0.004 if a >= 8 else 0.0)
        if clear2 < 1000.0:
            shaped -= 0.05 * max(0.0, (1000.0 - clear2) / 1000.0)
        if term and qstate.wall_death(info.get("js")):
            shaped -= 2.0
            stats["wall_death"] = True
        total += shaped
        if not greedy:
            agent.update(s, a, shaped, s2, terminal=term)
        s = s2
        feats = feats2
        steps += 1
        if term or trunc or (time.time() - start) > max_seconds:
            js = info.get("js") or {}
            return {
                "steps": info["steps"],
                "score": float(js.get("score") or prev_score),
                "return": total,
                "terminated": term,
                "truncated": trunc,
                "end_reason": info.get("end_reason"),
                "shield_overrides": stats["shield_overrides"],
                "shield_hard_steps": stats["shield_hard_steps"],
                "border_steps": stats["border_steps"],
                "min_clearance": None if stats["min_clearance"] > 1e8 else round(stats["min_clearance"], 1),
                "wall_death": stats["wall_death"],
            }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--run-dir", default="runs/q_bc_long", help="where to save q_table, logs, scores")
    ap.add_argument("--video-dir", default="videos", help="where to save eval videos")
    # BC
    ap.add_argument("--bc-episodes", type=int, default=50, help="maximum heuristic episodes for BC init (0 to skip)")
    ap.add_argument("--bc-minutes", type=float, default=None,
                    help="wall-clock budget for BC collection; collection stops at this or --bc-episodes")
    ap.add_argument("--bc-scale", type=float, default=2.0, help="scale for BC Q init: Q = freq * scale")
    ap.add_argument("--bc-bonus", type=float, default=1.5, help="extra bonus for most frequent heuristic action")
    ap.add_argument("--bc-smooth", type=float, default=0.05, help="uniform smoothing added")
    ap.add_argument("--skip-bc", action="store_true", help="skip BC even if no q_table exists")
    ap.add_argument("--bc-only", action="store_true", help="only do BC and exit")
    ap.add_argument("--bc-dataset", default=None, help="path to existing bc_dataset.npz to init from")
    # Q params
    ap.add_argument("--alpha", type=float, default=0.15)
    ap.add_argument("--gamma", type=float, default=0.97)
    ap.add_argument("--eps-start", type=float, default=0.5, help="starting epsilon after BC (0.5 recommended, 1.0 if no BC)")
    ap.add_argument("--eps-min", type=float, default=0.05)
    ap.add_argument("--eps-decay", type=float, default=0.995, help="per-episode decay, 0.995 for long runs (0.94 for short)")
    ap.add_argument("--truncate-after", type=int, default=600, help="max steps per episode")
    ap.add_argument("--episode-minutes", type=float, default=6.0, help="wall time cap per episode")
    ap.add_argument("--max-episodes", type=int, default=10000, help="max episodes total")
    ap.add_argument("--max-minutes", type=float, default=1440.0,
                    help="max Q-learning wall minutes for this invocation (timer starts after BC; 1440=24h)")
    ap.add_argument("--video-every", type=int, default=25, help="record greedy eval video every N episodes")
    ap.add_argument("--keep-videos", type=int, default=10)
    ap.add_argument("--keep-snapshots", type=int, default=24,
                    help="keep this many hourly Q-table snapshots (0 disables them)")
    ap.add_argument("--step-seconds", type=float, default=0.15)
    ap.add_argument("--nickname", default="q-bc-bot")
    ap.add_argument("--no-shield", action="store_true",
                    help="disable the border safety shield (ablation only: the snake can and will run out of bounds)")
    args = ap.parse_args()
    if args.bc_minutes is not None and (not math.isfinite(args.bc_minutes) or args.bc_minutes <= 0):
        ap.error("--bc-minutes must be a finite positive number")
    if args.bc_minutes is not None and (args.bc_episodes <= 0 or args.skip_bc):
        ap.error("--bc-minutes requires BC to be enabled and --bc-episodes to be positive")
    if args.keep_snapshots < 0:
        ap.error("--keep-snapshots must be non-negative")

    run_dir = Path(args.run_dir)
    video_dir = Path(args.video_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)
    scores_path = run_dir / "scores.jsonl"
    log_path = run_dir / "train.log"

    log, log_fh = make_logger(log_path)
    log(
        f"=== train_long start run_dir={run_dir} bc_episodes={args.bc_episodes} "
        f"bc_minutes={args.bc_minutes} max_minutes={args.max_minutes} ==="
    )
    log(f"args: {vars(args)}")

    # signal handling for graceful save
    stop_requested = {"flag": False}

    def handle_sig(signum, frame):
        log(f"[signal] received {signum}, will save and exit after current episode")
        stop_requested["flag"] = True

    signal.signal(signal.SIGINT, handle_sig)
    signal.signal(signal.SIGTERM, handle_sig)

    # Load or init agent
    agent = QAgent(alpha=args.alpha, gamma=args.gamma, eps=args.eps_start, eps_min=args.eps_min, eps_decay=args.eps_decay)
    state = {"episode": 0, "total_steps": 0, "best_score": 0.0, "best_eval_score": 0.0, "bc_done": False}

    if (run_dir / "q_table.npy").exists() and (run_dir / "state.json").exists():
        try:
            loaded_q = np.load(run_dir / "q_table.npy")
            loaded_state = json.loads((run_dir / "state.json").read_text())
            if loaded_q.shape != (N_STATES, N_ACT) or loaded_state.get("geom_version") != GEOM_VERSION:
                # Tables trained with the pre-fix state encoding (wrong border
                # circle at (grd/2, grd/2)) are not compatible and not worth
                # keeping in the loop: shelve them and start fresh.
                legacy = run_dir / f"q_table_legacy_{int(time.time())}.npy"
                os.replace(run_dir / "q_table.npy", legacy)
                if loaded_state.get("bc_done"):
                    legacy_bc = run_dir / f"bc_dataset_legacy_{int(time.time())}.npz"
                    if (run_dir / "bc_dataset.npz").exists():
                        os.replace(run_dir / "bc_dataset.npz", legacy_bc)
                log(
                    f"[resume] checkpoint uses the OLD state encoding (shape {loaded_q.shape} vs "
                    f"({N_STATES}, {N_ACT}) or geom_version mismatch); moved to {legacy.name} and "
                    f"starting fresh - the old border feature could not see the real wall"
                )
            else:
                agent.q = loaded_q
                state.update(loaded_state)
                # restore eps from state if saved
                if "eps" in loaded_state:
                    agent.eps = loaded_state["eps"]
                log(f"[resume] loaded q_table {agent.q.shape} episode={state['episode']} eps={agent.eps:.4f} best={state['best_score']:.1f}")
        except Exception as exc:
            log(f"[resume] failed to load checkpoint: {exc}, starting fresh")
    else:
        log("[init] no checkpoint, starting fresh Q-table zeros")
    state["geom_version"] = GEOM_VERSION

    # BC phase if needed
    bc_dataset_path = Path(args.bc_dataset) if args.bc_dataset else run_dir / "bc_dataset.npz"

    if args.bc_dataset and Path(args.bc_dataset).exists():
        log(f"[BC] loading provided dataset {args.bc_dataset}")
        data = np.load(bc_dataset_path)
        counts = data["counts"]
        if counts.shape != (N_STATES, N_ACT):
            raise SystemExit(
                f"bc_dataset {args.bc_dataset} has shape {counts.shape}, expected {(N_STATES, N_ACT)}: "
                "it was collected with the old (broken-border) state encoding and cannot be reused"
            )
        q_init = build_q_from_counts(counts, scale=args.bc_scale, bonus=args.bc_bonus, smoothing=args.bc_smooth)
        # only overwrite where we have data, keep existing Q for resumed runs?
        if not (run_dir / "q_table.npy").exists():
            agent.q = q_init
            log(f"[BC] initialized Q from {args.bc_dataset} states_covered={np.count_nonzero(np.sum(counts, axis=1))}")
        else:
            log("[BC] q_table exists, not overwriting with provided dataset (use --skip-bc=False and delete q_table.npy to force)")
        state["bc_done"] = True

    elif not state.get("bc_done") and not args.skip_bc and args.bc_episodes > 0 and not (run_dir / "q_table.npy").exists():
        # run collection
        try:
            dataset_path = collect_heuristic_dataset(
                run_dir,
                bc_episodes=args.bc_episodes,
                step_seconds=args.step_seconds,
                truncate_after=args.truncate_after,
                episode_minutes=args.episode_minutes,
                log_fn=log,
                bc_minutes=args.bc_minutes,
                stop_requested=stop_requested,
            )
            data = np.load(dataset_path)
            counts = data["counts"]
            q_init = build_q_from_counts(counts, scale=args.bc_scale, bonus=args.bc_bonus, smoothing=args.bc_smooth)
            agent.q = q_init
            state["bc_done"] = True
            log(f"[BC] Q-table initialized: maxQ={np.max(q_init):.2f} meanQ={np.mean(q_init):.4f} covered={np.count_nonzero(np.sum(counts, axis=1))}")
            # save BC init as q_table if no training yet
            save_all(run_dir, agent, {**state, "eps": agent.eps}, log_fn=log)
        except Exception as exc:
            log(f"[BC] failed: {exc}")
            import traceback
            traceback.print_exc()
            if args.bc_minutes is not None:
                log_fh.close()
                raise SystemExit(1)

        if args.bc_only:
            log("[BC] --bc-only set, exiting after BC phase")
            log_fh.close()
            return
    else:
        if (run_dir / "bc_dataset.npz").exists():
            log(f"[BC] dataset already exists {run_dir / 'bc_dataset.npz'}, skipping collection")
            state["bc_done"] = True
        elif args.skip_bc:
            log("[BC] skipped via --skip-bc")
        else:
            log("[BC] skipped (q_table exists or bc_episodes=0)")

    if args.bc_only:
        log("[BC] --bc-only but BC was already done, exiting")
        log_fh.close()
        return

    # If no BC at all, use higher eps start
    if not state.get("bc_done") and agent.eps < 0.9:
        log(f"[info] no BC was done, bumping eps_start from {agent.eps} to 1.0 for better exploration")
        agent.eps = 1.0

    # Training loop
    t_start = time.time()
    last_hourly_save = t_start
    env = None
    import shutil

    def prune_videos():
        vids = sorted(video_dir.glob("eval_*.webm"), key=lambda p: p.stat().st_mtime)
        for old in vids[:-args.keep_videos] if args.keep_videos > 0 else vids:
            try:
                old.unlink(missing_ok=True)
            except Exception:
                pass

    def prune_snapshots():
        snapshots = sorted(run_dir.glob("q_table_ep*.npy"), key=lambda p: p.stat().st_mtime)
        old_snapshots = snapshots[:-args.keep_snapshots] if args.keep_snapshots > 0 else snapshots
        for old in old_snapshots:
            try:
                old.unlink(missing_ok=True)
            except Exception:
                pass

    prune_snapshots()
    log(f"[train] starting main loop for up to {args.max_minutes} min / {args.max_episodes} episodes")
    while state["episode"] < args.max_episodes and (time.time() - t_start) < args.max_minutes * 60:
        if stop_requested["flag"]:
            log("[train] stop requested, breaking")
            break

        state["episode"] += 1
        ep = state["episode"]
        want_video = ep == 1 or (ep % args.video_every == 0)

        if want_video:
            if env is not None:
                try:
                    env.close()
                except Exception:
                    pass
            env = SlitherIOEnv(
                headless=True,
                nickname=f"{args.nickname}-{ep}",
                step_seconds=args.step_seconds,
                truncate_after=args.truncate_after,
                record_video_dir=str(video_dir / "raw"),
                viewport=(1280, 720),
            )
        elif env is None:
            env = SlitherIOEnv(
                headless=True,
                nickname=f"{args.nickname}-{ep}",
                step_seconds=args.step_seconds,
                truncate_after=args.truncate_after,
            )

        greedy = want_video
        kind = "EVAL " if greedy else "TRAIN"
        t0 = time.time()
        try:
            result = play_episode(
                env,
                agent,
                greedy=greedy,
                max_seconds=args.episode_minutes * 60.0,
                use_shield=not args.no_shield,
            )
        except Exception as exc:
            log(f"[ep {ep:04d}] FAILED: {type(exc).__name__}: {exc}")
            state["episode"] -= 1
            try:
                if env is not None:
                    env.close()
            except Exception:
                pass
            env = None
            time.sleep(5 + random.uniform(0, 3))
            continue

        eps_now = 0.0 if greedy else agent.eps
        elapsed = time.time() - t0
        wall = "WALL-DEATH" if result.get("wall_death") else ("wall" if (result.get("min_clearance") or 1e9) < 350 else "")
        log(
            f"[ep {ep:04d}] {kind} steps={result['steps']:4d} score={result['score']:7.1f} "
            f"return={result['return']:7.2f} eps={eps_now:.3f} term={result['terminated']} "
            f"trunc={result['truncated']} reason={result['end_reason']} ({elapsed:.0f}s) "
            f"border={result.get('border_steps', 0)} hard={result.get('shield_hard_steps', 0)} "
            f"veto={result.get('shield_overrides', 0)} minclear={result.get('min_clearance')} {wall} "
            f"elapsed_total={(time.time() - t_start)/60:.1f}min"
        )

        record = {
            "episode": ep,
            "kind": kind.strip(),
            "eps": eps_now,
            "ts": time.time(),
            "elapsed_min": (time.time() - t_start) / 60.0,
            **result,
        }
        try:
            with scores_path.open("a") as fh:
                fh.write(json.dumps(record) + "\n")
        except Exception as exc:
            log(f"[warn] failed to write scores: {exc}")

        if greedy:
            state["best_eval_score"] = max(state["best_eval_score"], result["score"])
            raw = video_dir / "raw"
            vids = sorted(raw.glob("*.webm"), key=lambda p: p.stat().st_mtime) if raw.exists() else []
            if vids:
                name = f"eval_ep{ep:04d}_score{int(result['score'])}.webm"
                try:
                    shutil.move(str(vids[-1]), str(video_dir / name))
                    log(f"          video -> {video_dir / name}")
                except Exception as exc:
                    log(f"          video move failed: {exc}")
            prune_videos()
            try:
                env.close()
            except Exception:
                pass
            env = None
        else:
            agent.decay()
            state["best_score"] = max(state["best_score"], result["score"])

        state["total_steps"] += result["steps"]
        state["eps"] = float(agent.eps)

        # save every episode
        try:
            save_all(run_dir, agent, state, log_fn=log)
        except Exception as exc:
            log(f"[warn] save failed: {exc}")

        # hourly snapshot, with bounded retention for very long runs
        if time.time() - last_hourly_save > 3600:
            if args.keep_snapshots > 0:
                snap = run_dir / f"q_table_ep{ep:05d}.npy"
                try:
                    np.save(snap, agent.q)
                    prune_snapshots()
                    log(f"[snapshot] hourly snapshot {snap}")
                except Exception as exc:
                    log(f"[warn] snapshot failed: {exc}")
            last_hourly_save = time.time()

        # small pause to be nice to slither.io servers
        time.sleep(0.5 + random.uniform(0, 1.0))

    if env is not None:
        try:
            env.close()
        except Exception:
            pass

    log(
        f"[done] episodes={state['episode']} best_train={state['best_score']:.1f} "
        f"best_eval={state['best_eval_score']:.1f} elapsed={(time.time() - t_start)/60:.1f}min"
    )
    try:
        save_all(run_dir, agent, state, log_fn=log)
    except Exception:
        pass
    log_fh.close()


if __name__ == "__main__":
    main()
