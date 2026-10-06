"""Headless Chromium driver. Talks to the page only through JS evaluate."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

BRIDGE_JS = Path(__file__).with_name("bridge.js").read_text(encoding="utf-8")

DEFAULT_URL = "http://slither.io/"
DESKTOP_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)


class SlitherBrowser:
    """One official client page. State comes back as JSON, never as a bitmap.

    `record_video_dir` records the browser viewport for a human watching the
    session. It is not read back as an observation.
    """

    def __init__(
        self,
        *,
        headless: bool = True,
        url: str = DEFAULT_URL,
        nickname: str = "gym-bot",
        viewport: tuple[int, int] = (1100, 700),
        record_video_dir: str | Path | None = None,
    ) -> None:
        self.headless = headless
        self.url = url
        self.nickname = nickname[:24]
        self.viewport = viewport
        self.record_video_dir = Path(record_video_dir) if record_video_dir else None
        self._pw: Playwright | None = None
        self._browser: Browser | None = None
        self._context = None
        self.page: Page | None = None
        self.console: list[str] = []
        self.video_path: Path | None = None

    def start(self) -> None:
        if self.page is not None:
            return
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context_kwargs: dict[str, Any] = {
            "viewport": {"width": self.viewport[0], "height": self.viewport[1]},
            "user_agent": DESKTOP_UA,
        }
        if self.record_video_dir is not None:
            self.record_video_dir.mkdir(parents=True, exist_ok=True)
            context_kwargs["record_video_dir"] = str(self.record_video_dir)
            context_kwargs["record_video_size"] = {
                "width": self.viewport[0],
                "height": self.viewport[1],
            }
        context = self._browser.new_context(**context_kwargs)
        self._context = context
        context.add_init_script(BRIDGE_JS)
        self.page = context.new_page()
        self.page.on("console", lambda msg: self._remember_console(msg.text))
        self.page.on("pageerror", lambda err: self._remember_console(f"pageerror: {err}"))
        self.page.on("dialog", lambda dialog: dialog.dismiss())
        self.page.goto(self.url, wait_until="domcontentloaded", timeout=60_000)
        self.wait_until_client_ready()

    def _remember_console(self, text: str) -> None:
        self.console.append(text)
        del self.console[:-30]

    def close(self) -> Path | None:
        page = self.page
        video = None
        if page is not None:
            try:
                video = page.video
            except Exception:
                video = None
            try:
                page.close()
            except Exception:
                pass
        if self._context is not None:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None
        if video is not None:
            try:
                self.video_path = Path(video.path())
            except Exception:
                self.video_path = None
        try:
            if self._browser is not None:
                self._browser.close()
        finally:
            self._browser = None
            self.page = None
            if self._pw is not None:
                self._pw.stop()
                self._pw = None
        return self.video_path

    def _eval(self, expression: str, arg: Any = None) -> Any:
        if self.page is None:
            raise RuntimeError("browser is not started")
        if arg is None:
            return self.page.evaluate(expression)
        return self.page.evaluate(expression, arg)

    def wait_until_client_ready(self, timeout: float = 30.0) -> None:
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            last = self._eval(
                """() => ({
                    ready: !!(window.__slitherGym && window.__slitherGym.ready()),
                    href: location.href
                })"""
            )
            if last and last.get("ready"):
                return
            time.sleep(0.1)
        raise TimeoutError(
            "slither.io client globals never appeared "
            f"(playing/dead_mtm). last={last} console={self.console[-8:]}"
        )

    def in_match(self) -> bool:
        return bool(
            self._eval(
                """() => !!(
                    window.playing === true &&
                    window.connected === true &&
                    window.slither &&
                    window.dead_mtm === -1 &&
                    window.ws instanceof WebSocket
                )"""
            )
        )

    def reload(self) -> None:
        if self.page is None:
            raise RuntimeError("browser is not started")
        self.page.reload(wait_until="domcontentloaded", timeout=60_000)
        self.wait_until_client_ready()

    def read(self) -> dict:
        packet = self._eval("() => window.__slitherGym.read()")
        if not isinstance(packet, dict):
            raise RuntimeError(f"bridge returned {type(packet).__name__}, expected object")
        return packet

    def arm_and_enter(self, nickname: str | None = None) -> dict:
        nick = (nickname or self.nickname)[:24]
        return self._eval(
            """(nick) => {
                const armed = window.__slitherGym.arm();
                const entered = window.__slitherGym.enter(nick);
                return { armed, entered };
            }""",
            nick,
        )

    def act_and_read(self, angle: float, boost: bool, wait_ms: int) -> dict:
        packet = self._eval(
            """async ({ angle, boost, waitMs }) => {
                window.__slitherGym.act(angle, boost);
                await new Promise((resolve) => setTimeout(resolve, waitMs));
                return window.__slitherGym.read();
            }""",
            {"angle": float(angle), "boost": bool(boost), "waitMs": int(wait_ms)},
        )
        if not isinstance(packet, dict):
            raise RuntimeError(f"bridge returned {type(packet).__name__}, expected object")
        return packet

    def wait_until_entered(self, timeout: float) -> dict:
        """Block until the in-page latch says the snake has entered.

        A death that happens before we ever observe `entered` is not returned
        as a starting state. The caller decides whether to retry.
        """
        deadline = time.time() + timeout
        last: dict | None = None
        while time.time() < deadline:
            last = self.read()
            life = last.get("lifecycle") or {}
            if life.get("phase") == "entered" and life.get("entered") and not life.get("dead"):
                return last
            if life.get("dead"):
                raise RuntimeError(
                    "match ended before a live enter was observed: "
                    f"death={life.get('death')} enter={life.get('enter')}"
                )
            time.sleep(0.1)
        life = (last or {}).get("lifecycle") or {}
        raise TimeoutError(
            "timed out waiting to enter the match. "
            f"phase={life.get('phase')} enter={life.get('enter')} "
            f"dead_mtm={(last or {}).get('js', {}).get('dead_mtm') if last else None} "
            f"console={self.console[-8:]}"
        )
