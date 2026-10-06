#!/usr/bin/env bash
# Collect heuristic demonstrations for a fixed wall-clock budget, then run
# shielded Q-learning from the BC-initialized Q-table.
# Supports running inside a detached tmux session or foreground.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

RUN_DIR="${RUN_DIR:-runs/bc30m_qtrain}"
BC_MINUTES="${BC_MINUTES:-30}"
BC_MAX_EPISODES="${BC_MAX_EPISODES:-1000000000}"
TRAIN_YEARS="${TRAIN_YEARS:-100}"
MAX_EPISODES="${MAX_EPISODES:-1000000000000}"
EPISODE_MINUTES="${EPISODE_MINUTES:-6}"
STEP_SECONDS="${STEP_SECONDS:-0.15}"
VIDEO_EVERY="${VIDEO_EVERY:-100}"
KEEP_VIDEOS="${KEEP_VIDEOS:-10}"
KEEP_SNAPSHOTS="${KEEP_SNAPSHOTS:-24}"
TMUX="${TMUX:-0}"
TMUX_SESSION="${TMUX_SESSION:-slither-bc-train}"

# Set TMUX=1 to start this launcher in its own detached tmux session. The
# environment settings above are forwarded so custom run limits still apply.
if [[ "${TMUX_LAUNCHED:-0}" != "1" && "$TMUX" == "1" ]]; then
  if ! command -v tmux >/dev/null 2>&1; then
    echo "TMUX=1 requested, but tmux is not installed." >&2
    exit 1
  fi
  if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
    echo "tmux session '$TMUX_SESSION' already exists; attach with: tmux attach -t '$TMUX_SESSION'" >&2
    exit 1
  fi
  args=()
  for name in RUN_DIR BC_MINUTES BC_MAX_EPISODES TRAIN_YEARS MAX_EPISODES EPISODE_MINUTES STEP_SECONDS VIDEO_EVERY KEEP_VIDEOS KEEP_SNAPSHOTS; do
    printf -v quoted '%q' "${!name}"
    args+=("$name=$quoted")
  done
  printf -v root_q '%q' "$ROOT"
  printf -v session_q '%q' "$TMUX_SESSION"
  printf -v script_q '%q' "$ROOT/scripts/run_bc_then_train.sh"
  command="cd $root_q && env TMUX_LAUNCHED=1 ${args[*]} bash $script_q"
  tmux new-session -d -s "$TMUX_SESSION" "$command"
  echo "Started tmux session '$TMUX_SESSION'. Attach with: tmux attach -t '$TMUX_SESSION'"
  exit 0
fi

USE_TMUX="${USE_TMUX:-1}"
TMUX_SESSION="${TMUX_SESSION:-slither}"
TMUX_ATTACH="${TMUX_ATTACH:-0}"

# Convert average Gregorian years to minutes (365.2425 days/year).
TRAIN_MINUTES="$(python3 - "$TRAIN_YEARS" "$BC_MINUTES" <<'PY'
import math
import sys

years, bc_minutes = map(float, sys.argv[1:])
if not math.isfinite(years) or years <= 0:
    raise SystemExit("TRAIN_YEARS must be a positive number")
if not math.isfinite(bc_minutes) or bc_minutes <= 0:
    raise SystemExit("BC_MINUTES must be a positive number")
print(f"{years * 365.2425 * 24 * 60:.6f}")
PY
)"

printf 'Run directory: %s\nBC collection: %s minutes (max %s episodes)\nQ-learning: %s minutes (~%s years; max %s episodes)\n' \
  "$RUN_DIR" "$BC_MINUTES" "$BC_MAX_EPISODES" "$TRAIN_MINUTES" "$TRAIN_YEARS" "$MAX_EPISODES"
echo "The Q-learning timer starts after BC finishes. Existing checkpoints auto-resume and skip BC."

# Create the project environment if needed and make sure Playwright's browser exists.
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium || echo "[warn] playwright chromium installation failed; continuing if browser is already installed"
mkdir -p "$RUN_DIR" videos

CMD=(
  python scripts/train_long.py
  --run-dir "$RUN_DIR"
  --bc-episodes "$BC_MAX_EPISODES"
  --bc-minutes "$BC_MINUTES"
  --max-minutes "$TRAIN_MINUTES"
  --max-episodes "$MAX_EPISODES"
  --episode-minutes "$EPISODE_MINUTES"
  --step-seconds "$STEP_SECONDS"
  --video-every "$VIDEO_EVERY"
  --keep-videos "$KEEP_VIDEOS"
  --keep-snapshots "$KEEP_SNAPSHOTS"
  "$@"
)

# Determine whether tmux execution is possible.
if [[ "$USE_TMUX" == "1" ]]; then
  if ! command -v tmux >/dev/null 2>&1; then
    echo "[warn] tmux is not installed on this system; falling back to foreground execution." >&2
    echo "[warn] Install tmux to run in a detached background session, or set USE_TMUX=0 to suppress this warning." >&2
    USE_TMUX=0
  elif [[ -n "${TMUX:-}" ]]; then
    CURRENT_SESSION="$(tmux display-message -p '#S' 2>/dev/null || true)"
    if [[ "$CURRENT_SESSION" == "$TMUX_SESSION" ]]; then
      echo "[launch] Already running inside target tmux session '$TMUX_SESSION'; running directly in current pane."
      USE_TMUX=0
    fi
  fi
fi

if [[ "$USE_TMUX" == "1" ]]; then
  CMD_STR="$(printf '%q ' "${CMD[@]}")"
  TMUX_EXEC="source \"$ROOT/.venv/bin/activate\" && $CMD_STR 2>&1 | tee -a \"$RUN_DIR/tmux.log\"; echo \"exit code: \$?\" | tee -a \"$RUN_DIR/tmux.log\"; sleep 5"

  if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
    echo "[launch] Existing tmux session '$TMUX_SESSION' found. Restarting..."
    tmux kill-session -t "$TMUX_SESSION"
  fi

  tmux new-session -d -s "$TMUX_SESSION" -c "$ROOT" "$TMUX_EXEC"
  echo "[launch] Started training in detached tmux session '$TMUX_SESSION'."
  echo "[launch] Session list:"
  tmux ls || true
  echo ""
  echo "Monitor & control:"
  echo "  Attach session:  tmux attach -t $TMUX_SESSION"
  echo "  Detach session:  press Ctrl+b then d"
  echo "  Live log tail:   tail -f $RUN_DIR/train.log"
  echo "                   tail -f $RUN_DIR/tmux.log"
  echo "  Scores log:      tail -f $RUN_DIR/scores.jsonl"
  echo "  Saved videos:    ls -lh videos/"
  echo "  Stop training:   tmux kill-session -t $TMUX_SESSION (or attach and Ctrl+C)"
  echo "  Auto-resume:     run this script again to resume from checkpoint"

  if [[ "$TMUX_ATTACH" == "1" ]]; then
    tmux attach-session -t "$TMUX_SESSION"
  fi
else
  exec "${CMD[@]}"
fi
