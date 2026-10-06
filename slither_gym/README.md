# Slither.io Gymnasium pipeline

A headless Chromium Gymnasium environment for the official [slither.io](http://slither.io/) client, with a heuristic teacher, behavioral-cloning (BC) warm-start for tabular Q-learning, and a border safety shield. Observations come from the client's JavaScript state, not screenshots.

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

## Train

The main entry point is `scripts/train_long.py`. It collects state/action counts from `scripts/heuristic_bot.py`, initializes the Q-table from those counts, then trains with shielded Q-learning. It saves `q_table.npy`, `bc_dataset.npz`, `state.json`, `scores.jsonl`, and `train.log` under the run directory; evaluation videos go under `videos/`.

```bash
# New run: collect 60 BC episodes, then train for up to 24 hours
python scripts/train_long.py --run-dir runs/q_bc_long --bc-episodes 60 --max-minutes 1440

# Only collect the BC dataset and initialize the Q-table
python scripts/train_long.py --run-dir runs/my_bc_run --bc-episodes 60 --bc-only

# Resume an existing run (loads its checkpoint and skips completed BC)
python scripts/train_long.py --run-dir runs/q_bc_long --max-minutes 1440

# Timed BC followed by long Q-learning launcher (launches in detached tmux by default)
bash scripts/run_bc_then_train.sh
# Customize duration, run folder, or tmux session:
BC_MINUTES=30 TRAIN_YEARS=1 RUN_DIR=runs/bc30m_q1y TMUX_SESSION=slither bash scripts/run_bc_then_train.sh
# Run in foreground without tmux:
USE_TMUX=0 bash scripts/run_bc_then_train.sh

# Attach to the running session or monitor logs:
tmux attach -t slither
tail -f runs/bc30m_qtrain/train.log
```

`--bc-minutes` adds a wall-clock limit to heuristic collection; collection ends at whichever comes first, `--bc-minutes` or `--bc-episodes`. The Q-learning `--max-minutes` timer starts **after BC** and applies to this invocation, not cumulatively across resumes. `scripts/run_bc_then_train.sh` defaults to 30 minutes of BC followed by a 100-year Q-learning ceiling, with a high episode cap so the episode limit does not end training first. That 100-year value is only a very large upper bound, not a practical runtime; rerunning after a restart starts a fresh per-invocation time budget. Set `--bc-episodes 0` or `--skip-bc` to start without a BC warm-start. `--bc-dataset PATH` initializes from a compatible dataset in a new run. Other controls: `--episode-minutes`, `--truncate-after`, `--video-every`, `--eps-start`, `--eps-min`, `--eps-decay`, and `--keep-snapshots` (see `--help`). Long runs retain at most 24 hourly Q-table snapshots by default. The launcher creates a new run at `runs/q_bc_long` by default. To resume the one retained, compatible example checkpoint, use `--run-dir runs/q_fixed`; its `q_table.npy`, BC dataset, scores, and state were kept. Older run artifacts using the broken border encoding were removed.

Monitor with `tail -f runs/<run>/train.log` or inspect `runs/<run>/scores.jsonl` (`wall_death`, `min_clearance`, `border_steps`, `shield_overrides`). Runtime logs, checkpoints, and videos are ignored by Git unless already tracked.

## Border protection

The client map is a circle centered at `(grd, grd)` with radius `flux_grd` (not `(grd/2, grd/2)`). `slither_gym/spec.py` computes normalized clearance from that circle; `slither_gym/qstate.py` bins the clearance and provides `border_geometry()`, `border_shield()`, `advise_center()`, and `wall_death()`. The shield vetoes headings that would exit the circle on look-ahead, disables boost close to the wall, and restricts headings to inward/tangential ones in the hard zone. Training also steers unvisited border-critical states toward the center and penalizes wall proximity/death. `--no-shield` is for ablation only, not safe training.

The heuristic teacher independently avoids the border, enemy bodies, and dangerous food; BC collection also applies the shield so unsafe teacher actions are not recorded. Tables/datasets with the old state shape or geometry version must not be reused: the trainer checks checkpoint shape/version on resume and shelves incompatible checkpoints. For the full bin layout and thresholds, see `slither_gym/qstate.py`.

## Environment and episode boundary

The environment is `SlitherIOEnv` (`gymnasium.make("SlitherIO-v0")` after importing `slither_gym`). Actions are `Discrete(16)`: eight absolute headings, each with or without boost. `info["js"]` contains the player, food, other snakes, map geometry and score; `reset()`/`step()` also return a fixed-length observation described in `slither_gym/spec.py`.

An episode starts only after the live match is entered (`playing && connected && ws instanceof WebSocket && slither && dead_mtm === -1`, not a skin preview). It ends on the player's death (`gameOver`, `dead_mtm`, or `slither.dead`); other snakes dying do not end it. The 20 ms page-side latch in `slither_gym/bridge.js` preserves death signals that the client clears before Python can poll. An orphaned match is reported separately. Time limits are `truncated`, not death. The browser controller in `slither_gym/controller.py` steers using the game's `xm`, `ym`, and acceleration globals.

```python
from slither_gym import SlitherIOEnv

env = SlitherIOEnv(headless=True, nickname="gym-bot")
try:
    obs, info = env.reset()
    obs, reward, terminated, truncated, info = env.step(0)
    print(info["js"]["self"], terminated, truncated)
finally:
    env.close()
```

## Files and tests

- `slither_gym/`: browser bridge, environment, observation spec, and border-aware Q-state.
- `scripts/heuristic_bot.py`: BC teacher; can also run a standalone recorded life.
- `scripts/train_long.py`: BC collection, training, shield, checkpoint/resume.
- `scripts/run_bc_then_train.sh`: timed BC followed by long-duration Q-learning (launches in tmux by default).
- `runs/q_fixed/`: compatible sample checkpoint and training history.
- `tests/`: lifecycle, observation, browser latch, and border-safety regression tests.

```bash
node tests/test_lifecycle.cjs
python tests/test_obs.py
python tests/test_qstate.py
python tests/test_training.py
python tests/test_browser_latch.py
```

The browser-latch test needs Playwright Chromium but does not require a live game. Live training connects to public slither.io servers as a normal client; respect the game's terms and avoid excessive concurrent runs.
