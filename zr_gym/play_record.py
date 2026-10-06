#!/usr/bin/env python3
"""Play a full ZombsRoyale solo round and record video of the whole process.

Video: Playwright's built-in context recorder -> videos/zombs_round.webm
Screenshots: periodic PNGs in shots_round/ for debugging the bot's progress.
"""
import os, shutil, subprocess, time
from playwright.sync_api import sync_playwright

W, H = 640, 400
VIDEOS = "videos"
SHOTS = "shots_round"

AD_KILLER_JS = """
() => {
  const kill = () => document.querySelectorAll(
    '[id^=cdm-zone], .lngtd-ad-wrapper, ins.adsbygoogle, [id^=aswift], [id^=google_ads], [id^=div-gpt-ad]'
  ).forEach(e => e.remove());
  kill();
  new MutationObserver(() => kill()).observe(document.documentElement, { childList: true, subtree: true });
  return 'ok';
}
"""

def dismiss_consent(page):
    for _ in range(4):
        for fr in page.frames:
            try:
                el = fr.locator("text=/^OK$/i").last
                if el.is_visible(timeout=300):
                    el.click(timeout=2000)
                    return True
            except Exception:
                continue
        time.sleep(1)
    return False

def shot(page, name):
    try:
        page.screenshot(path=f"{SHOTS}/{name}.png", timeout=8000)
    except Exception as e:
        print(f"   [shot fail {name}: {str(e)[:40]}]", flush=True)

def main():
    os.makedirs(VIDEOS, exist_ok=True)
    os.makedirs(SHOTS, exist_ok=True)

    xvfb = subprocess.Popen(["Xvfb", ":95", "-screen", "0", f"{W}x{H}x24", "-nolisten", "tcp"])
    time.sleep(1.5)
    try:
        with sync_playwright() as p:
            env = dict(os.environ, DISPLAY=":95", LIBGL_ALWAYS_SOFTWARE="1")
            browser = p.firefox.launch(headless=False, env=env,
                firefox_user_prefs={"gfx.webrender.software": True, "fission.autostart": False, "dom.ipc.processCount": 1})
            context = browser.new_context(
                viewport={"width": W, "height": H},
                record_video_dir=VIDEOS,
                record_video_size={"width": W, "height": H},
            )
            page = context.new_page()
            page.set_default_timeout(8000)
            page.on("crash", lambda: print(">>> page crash!", flush=True))

            print("[menu] loading zombsroyale.io ...", flush=True)
            page.goto("https://zombsroyale.io/", wait_until="domcontentloaded", timeout=60000)

            t0 = time.time()
            while time.time() - t0 < 240:
                time.sleep(4)
                try:
                    if page.evaluate("() => !document.body.innerText.includes('The game is loading')"):
                        print(f"[menu] game loaded in {time.time()-t0:.0f}s", flush=True)
                        break
                except Exception:
                    pass
            time.sleep(8)

            if dismiss_consent(page):
                print("[menu] consent dismissed", flush=True)
            page.evaluate(AD_KILLER_JS)
            time.sleep(2)
            shot(page, "01_menu")

            print("[queue] clicking SOLO ...", flush=True)
            page.mouse.click(215, 227)
            time.sleep(4)
            page.evaluate(AD_KILLER_JS)
            shot(page, "02_lobby")

            # wait for match: lobby text eventually disappears when the plane spawns
            print("[queue] waiting for match to fill ...", flush=True)
            t0 = time.time()
            in_plane = False
            while time.time() - t0 < 150:
                time.sleep(5)
                try:
                    txt = page.evaluate("() => document.body.innerText.slice(0, 200)")
                    if "Waiting for Players" not in txt and "Starting in" not in txt:
                        in_plane = True
                        print(f"[match] lobby closed after {time.time()-t0:.0f}s — should be in the plane", flush=True)
                        break
                except Exception:
                    pass
            if not in_plane:
                print("[match] timeout waiting — going with the flow", flush=True)
            shot(page, "03_plane")

            print("[drop] riding the plane 7s, then SPACE to deploy ...", flush=True)
            time.sleep(7)
            page.keyboard.press("Space")
            shot(page, "04_jump")

            print("[drop] parachuting — holding W ...", flush=True)
            page.keyboard.down("w")
            time.sleep(6)
            page.keyboard.up("w")
            shot(page, "05_landed")

            print("[play] roaming: WASD + E (doors/chests) + LMB bursts + reload ...", flush=True)
            t0 = time.time()
            DURATION = 200
            i = 0
            last_burst = 0
            last_reload = 0
            while time.time() - t0 < DURATION:
                i += 1
                # movement pattern: mostly forward, weave left/right
                k = "w"
                if i % 5 in (3, 4):
                    k = "a" if (i // 5) % 2 == 0 else "d"
                try:
                    page.keyboard.down(k)
                    time.sleep(1.1)
                    page.keyboard.up(k)
                except Exception:
                    pass

                # interact (open doors / loot chests) every other step
                if i % 2 == 0:
                    try: page.keyboard.press("e")
                    except Exception: pass

                # fire a burst every ~8s, reload every ~25s
                now = time.time() - t0
                if now - last_burst > 8:
                    last_burst = now
                    for _ in range(3):
                        try: page.mouse.click(330, 180)
                        except Exception: pass
                        time.sleep(0.15)
                if now - last_reload > 25:
                    last_reload = now
                    try: page.keyboard.press("r")
                    except Exception: pass

                if i % 12 == 0:
                    shot(page, f"06_live_{i:03d}")
                    print(f"[play] t+{now:.0f}s, step {i}", flush=True)

            shot(page, "07_end")
            print("[end] closing context to flush video ...", flush=True)
            video = page.video
            context.close()
            vpath = video.path()
            browser.close()
    finally:
        xvfb.terminate()

    out = os.path.join(VIDEOS, "zombs_round.webm")
    shutil.move(vpath, out)
    sz = os.path.getsize(out) / 1e6
    print(f"saved video: {out} ({sz:.1f} MB)")
    print("done")

if __name__ == "__main__":
    main()
