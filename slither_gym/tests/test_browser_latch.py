"""The injected bridge latches enter and death inside a real browser page."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from playwright.sync_api import sync_playwright

from slither_gym.controller import BRIDGE_JS


def test_page_latch():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context()
        context.add_init_script(BRIDGE_JS)
        page = context.new_page()
        page.set_content("<!doctype html><html><body></body></html>")

        page.evaluate(
            """() => {
                window.playing = false;
                window.connected = false;
                window.connecting = false;
                window.want_play = false;
                window.choosing_skin = false;
                window.dead_mtm = -1;
                window.slither = null;
                window.ws = null;
                window.__slitherGym.arm();
            }"""
        )
        menu = page.evaluate("() => window.__slitherGym.read()")
        assert menu["lifecycle"]["phase"] == "menu"
        assert menu["lifecycle"]["entered"] is False

        page.evaluate(
            """() => {
                window.playing = true;
                window.connected = true;
                window.choosing_skin = true;
                window.ws = {};
                window.slither = { id: 1, xx: 10, yy: 20, dead: false };
            }"""
        )
        preview = page.evaluate("() => window.__slitherGym.read().lifecycle")
        assert preview["phase"] == "preview"
        assert preview["entered"] is False

        page.evaluate(
            """() => {
                window.choosing_skin = false;
                window.ws = new WebSocket("ws://127.0.0.1:1");
                window.slither = { id: 4, xx: 30, yy: 40, dead: false, ang: 0 };
                window.dead_mtm = -1;
            }"""
        )
        entered = page.evaluate("() => window.__slitherGym.read()")
        assert entered["lifecycle"]["phase"] == "entered"
        assert entered["lifecycle"]["enter"]["slither_id"] == 4
        assert entered["js"]["self"]["xx"] == 30
        assert entered["lifecycle"]["dead"] is False

        page.evaluate(
            """() => {
                window.slithers = [{ id: 9, xx: 80, yy: 40, dead: true, pts: [] }];
            }"""
        )
        still = page.evaluate("() => window.__slitherGym.read().lifecycle")
        assert still["phase"] == "entered" and still["dead"] is False

        page.evaluate("() => { window.dead_mtm = Date.now(); }")
        dead = page.evaluate("() => window.__slitherGym.read()")
        assert dead["lifecycle"]["phase"] == "dead"
        assert dead["lifecycle"]["death"]["reason"] == "dead_mtm"
        assert dead["js"]["self"]["id"] == 4

        page.evaluate(
            """() => {
                window.dead_mtm = -1;
                window.playing = false;
                window.slither = null;
            }"""
        )
        latched = page.evaluate("() => window.__slitherGym.read().lifecycle")
        assert latched["phase"] == "dead" and latched["dead"] is True
        browser.close()


if __name__ == "__main__":
    test_page_latch()
    print("browser latch test passed")
