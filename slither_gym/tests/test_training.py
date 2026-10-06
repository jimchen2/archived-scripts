"""Offline regression checks for BC timing/init and shielded action selection."""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import scripts.train_long as training
from scripts.train_long import QAgent, build_q_from_counts
from slither_gym.qstate import N_ACT, N_STATES
from slither_gym.spec import OBS_DIM


def test_bc_counts_initialize_policy():
    counts = np.zeros((N_STATES, N_ACT), dtype=np.int32)
    counts[7, 2] = 3
    counts[7, 5] = 1
    q = build_q_from_counts(counts, scale=2.0, bonus=1.5, smoothing=0.05)
    assert q.shape == counts.shape
    assert np.all(q[0] == 0)  # unseen states stay uninitialized
    assert np.argmax(q[7]) == 2
    assert np.isclose(q[7, 2], 0.75 * 2.0 + 1.5 + 0.05 + 0.75)
    assert np.isclose(q[7, 5], 0.25 * 2.0 + 0.05)


def test_agent_respects_shield_and_inward_advice():
    agent = QAgent(eps=0.0)
    agent.q[0, 3] = 10.0  # best action would fly out of bounds
    agent.q[0, 4] = 1.0
    assert agent.act(0, greedy=True, allowed={4, 5}) == 4
    assert agent.act(1, greedy=True, allowed={4, 5}, advice=5) == 5

    agent.eps = 1.0
    for _ in range(100):
        assert agent.act(0, allowed={4, 5}) in {4, 5}


def test_bc_wall_clock_budget_saves_partial_dataset():
    obs = np.zeros(OBS_DIM, dtype=np.float32)
    info = {
        "js": {
            "self": {"xx": 16384.0, "yy": 16384.0, "ang": 0.0, "sc": 1.0, "fam": 0.0},
            "grd": 16384.0,
            "flux_grd": 16000.0,
            "foods": [],
            "snakes": [],
        }
    }

    class FakeEnv:
        def __init__(self, **_kwargs):
            pass

        def reset(self):
            return obs, info

        def step(self, _action):
            time.sleep(0.01)
            return obs, 0.0, False, False, info

        def close(self):
            pass

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.object(training, "SlitherIOEnv", FakeEnv):
            dataset_path = training.collect_heuristic_dataset(
                Path(tmpdir),
                bc_episodes=1000,
                step_seconds=0.15,
                truncate_after=1000,
                episode_minutes=1.0,
                log_fn=lambda _message: None,
                bc_minutes=0.002,
            )
        with np.load(dataset_path) as data:
            assert 0 < int(data["total_steps"]) < 1000
            assert np.sum(data["counts"]) == int(data["total_steps"])


def test_run_bc_then_train_tmux_launcher():
    repo_dir = Path(__file__).resolve().parents[1]
    script_path = repo_dir / "scripts" / "run_bc_then_train.sh"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        fake_bin = tmp_path / "bin"
        fake_bin.mkdir()

        log_file = tmp_path / "tmux.log"
        fake_tmux = fake_bin / "tmux"
        fake_tmux.write_text(f"""#!/usr/bin/env bash
echo "$@" >> "{log_file}"
if [[ "$1" == "has-session" ]]; then
    exit 1
elif [[ "$1" == "ls" ]]; then
    echo "session: 1 windows"
    exit 0
fi
exit 0
""")
        fake_tmux.chmod(0o755)

        env = os.environ.copy()
        env["PATH"] = f"{fake_bin}:{env['PATH']}"
        env["RUN_DIR"] = str(tmp_path / "run_tmux")
        env["TMUX_SESSION"] = "custom_slither"

        # Check tmux launch behavior
        res = subprocess.run(["bash", str(script_path)], env=env, capture_output=True, text=True)
        assert res.returncode == 0, f"Script failed: {res.stderr}"
        tmux_calls = log_file.read_text().splitlines()
        assert any("new-session -d -s custom_slither" in line for line in tmux_calls)
        assert any("ls" in line for line in tmux_calls)

        # Check USE_TMUX=0 foreground behavior (pass --help to exit immediately)
        env["USE_TMUX"] = "0"
        res_fg = subprocess.run(["bash", str(script_path), "--help"], env=env, capture_output=True, text=True)
        assert res_fg.returncode == 0
        assert "usage: train_long.py" in res_fg.stdout


if __name__ == "__main__":
    test_bc_counts_initialize_policy()
    test_agent_respects_shield_and_inward_advice()
    test_bc_wall_clock_budget_saves_partial_dataset()
    test_run_bc_then_train_tmux_launcher()
    print("training tests passed")
