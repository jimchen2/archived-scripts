"""Gymnasium environment. Episode starts on enter, ends only on death."""

from __future__ import annotations

from typing import Any

import gymnasium as gym
import numpy as np

from slither_gym.controller import SlitherBrowser
from slither_gym.spec import N_DIRS, OBS_DIM, decode_action, vectorize


class SlitherIOEnv(gym.Env):
    """slither.io with observations taken from the client's JavaScript memory.

    `reset()` does not return until you have entered a live match
    (`playing`, a real WebSocket, and `slither`). Clicking Play is not the
    start. The skin-preview snake is not the start.

    `step()` sets `terminated=True` only when you are dead (`gameOver`,
    `dead_mtm !== -1`, or `slither.dead`). Time limits and a match that
    vanishes without a death signal are `truncated`, and only if you opt in.
    The default is that the episode does not end until death.

    Render modes that would screenshot the canvas are rejected.
    """

    metadata = {"render_modes": []}

    def __init__(
        self,
        *,
        headless: bool = True,
        url: str = "http://slither.io/",
        nickname: str = "gym-bot",
        step_seconds: float = 0.2,
        enter_timeout: float = 60.0,
        enter_attempts: int = 3,
        truncate_after: int | None = None,
        truncate_on_orphan: bool = False,
        survival_reward: float = 0.01,
        score_reward: float = 0.002,
        death_reward: float = -1.0,
        render_mode: str | None = None,
        record_video_dir: str | None = None,
        viewport: tuple[int, int] = (1100, 700),
    ) -> None:
        if render_mode is not None:
            raise ValueError(
                "SlitherIOEnv has no pixel renderer. "
                "Pass render_mode=None. State is the page's JavaScript variables."
            )
        super().__init__()
        self.headless = headless
        self.url = url
        self.nickname = nickname
        self.step_seconds = step_seconds
        self.enter_timeout = enter_timeout
        self.enter_attempts = enter_attempts
        self.truncate_after = truncate_after
        self.truncate_on_orphan = truncate_on_orphan
        self.survival_reward = survival_reward
        self.score_reward = score_reward
        self.death_reward = death_reward

        self.action_space = gym.spaces.Discrete(N_DIRS * 2)
        self.observation_space = gym.spaces.Box(
            low=-np.inf, high=np.inf, shape=(OBS_DIM,), dtype=np.float32
        )
        self.browser = SlitherBrowser(
            headless=headless,
            url=url,
            nickname=nickname,
            viewport=viewport,
            record_video_dir=record_video_dir,
        )
        self._steps = 0
        self._prev_score = 0.0
        self._closed = False

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict | None = None,
    ) -> tuple[np.ndarray, dict]:
        super().reset(seed=seed)
        options = options or {}
        nickname = str(options.get("nickname", self.nickname))[:24]
        timeout = float(options.get("timeout", self.enter_timeout))
        attempts = int(options.get("attempts", self.enter_attempts))
        self.browser.nickname = nickname
        self.browser.start()

        last_error: Exception | None = None
        packet: dict | None = None
        for attempt in range(max(1, attempts)):
            try:
                if attempt > 0 or self.browser.in_match():
                    self.browser.reload()
                self.browser.arm_and_enter(nickname)
                packet = self.browser.wait_until_entered(timeout)
                break
            except Exception as exc:
                last_error = exc
                packet = None
        if packet is None:
            raise TimeoutError(
                f"could not enter a slither.io match after {attempts} attempts"
            ) from last_error

        life = packet["lifecycle"]
        js = packet.get("js") or {}
        self._steps = 0
        self._prev_score = float(js.get("score") or 0.0)
        obs = vectorize(js, dead=False, orphan=False)
        return obs, self._info(life, js, died=False)

    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, dict]:
        angle, boost = decode_action(int(action))
        packet = self.browser.act_and_read(angle, boost, int(self.step_seconds * 1000))
        life = packet.get("lifecycle") or {}
        js = packet.get("js") or {}
        died = bool(life.get("dead"))
        orphan = bool(life.get("orphan"))
        score = float(js.get("score") or 0.0)
        delta = max(0.0, score - self._prev_score)
        self._prev_score = max(self._prev_score, score)
        self._steps += 1

        reward = self.survival_reward
        reward += self.score_reward * delta
        if died:
            reward += self.death_reward

        terminated = died
        truncated = False
        if not terminated and self.truncate_after is not None and self._steps >= self.truncate_after:
            truncated = True
        if not terminated and self.truncate_on_orphan and orphan:
            truncated = True

        obs = vectorize(js, dead=died, orphan=orphan)
        return obs, float(reward), terminated, truncated, self._info(life, js, died=died)

    def read_js(self) -> dict:
        """Latest JavaScript snapshot, including the latched enter/death records."""
        packet = self.browser.read()
        return {
            "lifecycle": packet.get("lifecycle"),
            "js": packet.get("js"),
        }

    def close(self):
        if self._closed:
            return self.browser.video_path
        self._closed = True
        return self.browser.close()

    def _info(self, life: dict, js: dict, *, died: bool) -> dict[str, Any]:
        death = life.get("death") or None
        return {
            "source": "javascript",
            "phase": life.get("phase"),
            "episode_started": bool(life.get("entered")),
            "episode_ended": died,
            "end_reason": (death or {}).get("reason") if died else None,
            "highscore": (death or {}).get("highscore") if died else None,
            "orphan": bool(life.get("orphan")),
            "steps": self._steps,
            "lifecycle": life,
            "js": js,
        }
