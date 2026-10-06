#!/usr/bin/env python3
"""
Join and play ZombsRoyale.io from a headless browser (Firefox + Xvfb + Mesa llvmpipe).

Usage:
  python3 play_zombs.py                # join solo match, spectate 60s
  python3 play_zombs.py --move         # join, then wander with WASD
  python3 play_zombs.py --mode duo     # duo queue (bots fill if solo partner)
Requires: playwright (firefox), Xvfb, mesa (llvmpipe). ~2.5GB RAM w/ swap recommended.
"""
import argparse, os, subprocess, sys, time

W, H = 640, 400
SHOTS = "shots"

AD_KILLER_JS = """
() => {
  const kill = () => {
    let n = 0;
    document.querySelectorAll('[id^=cdm-zone], .lngtd-ad-wrapper, ins.adsbygoogle, [id^=aswift], [id^=google_ads], [id^=div-gpt-ad]').forEach(e => { e.remove(); n++; });
    return n;
  };
  kill();
  const mo = new MutationObserver(() => kill());
  mo.observe(document.documentElement, { childList: true, subtree: true });
  return 'ok';
}
"""

def wait_loading_done(page, timeout=240):
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(4)
        try:
            if page.evaluate("() => !document.body.innerText.includes('The game is loading')"):
                return time.time() - t0
        except Exception:
            pass
    return -1

def dismiss_consent(page):
    for _ in range(3):
        for fr in page.frames:
            try:
                el = fr.locator("text=/^OK$/i").last
                if el.is_visible(timeout=300):
                    el.click(timeout=2000)
                    return True
            except Exception:
                continue
    return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="solo", choices=["solo", "duo"])
    ap.add_argument("--move", action="store_true", help="wander with WASD once the match starts")
    ap.add_argument("--duration", type=int, default=120, help="seconds to stay in the match")
    args = ap.parse_args()

    os.makedirs(SHOTS, exist_ok=True)
    xvfb = subprocess.Popen(["Xvfb", ":95", "-screen", "0", f"{W}x{H}x24", "-nolisten", "tcp"])
    time.sleep(1.5)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            env = dict(os.environ, DISPLAY=":95", LIBGL_ALWAYS_SOFTWARE="1")
            browser = p.firefox.launch(headless=False, env=env,
                firefox_user_prefs={"gfx.webrender.software": True, "fission.autostart": False, "dom.ipc.processCount": 1})
            page = browser.new_page(viewport={"width": W, "height": H})
            page.on("crash", lambda: print(">>> page crash", flush=True))

            print("[1/6] loading zombsroyale.io ...", flush=True)
            page.goto("https://zombsroyale.io/", wait_until="domcontentloaded", timeout=60000)

            print("[2/6] waiting for Unity game to finish loading ...", flush=True)
            took = wait_loading_done(page)
            print(f"      loaded in {took:.0f}s", flush=True)
            time.sleep(8)  # menu settle

            if dismiss_consent(page):
                print("      consent dialog dismissed", flush=True)
            page.evaluate(AD_KILLER_JS)
            time.sleep(2)
            page.screenshot(path=f"{SHOTS}/z_1_menu.png")

            print(f"[3/6] clicking {args.mode.upper()} ...", flush=True)
            page.mouse.click(215, 227)  # Solo button at default 640x400 layout
            time.sleep(4)
            page.evaluate(AD_KILLER_JS)
            page.screenshot(path=f"{SHOTS}/z_2_lobby.png")
            print("      in lobby (see shots/z_2_lobby.png)", flush=True)

            print("[4/6] waiting for match to start (watching for countdown to hit 0) ...", flush=True)
            t0 = time.time()
            started = False
            while time.time() - t0 < 180:
                time.sleep(5)
                try:
                    txt = page.evaluate("() => document.body.innerText.slice(0, 200)")
                    page.screenshot(path=f"{SHOTS}/z_3_ingame.png", timeout=8000)
                    # once the match starts the 'Waiting for Players'/'Starting in' text disappears
                    if "Waiting for Players" not in txt and "Starting in" not in txt:
                        started = True
                        print(f"      match started after ~{time.time()-t0:.0f}s in lobby", flush=True)
                        break
                except Exception:
                    pass
            if not started:
                print("      (countdown text gone or timeout — checking screenshot)", flush=True)

            print(f"[5/6] IN MATCH — staying {args.duration}s" + (" and wandering with WASD" if args.move else ""), flush=True)
            t0 = time.time()
            keys = ["w", "a", "s", "d"]
            i = 0
            while time.time() - t0 < args.duration:
                if args.move:
                    k = keys[i % 4]
                    page.keyboard.down(k)
                    time.sleep(1.2)
                    page.keyboard.up(k)
                else:
                    time.sleep(1.2)
                i += 1
                if i % 10 == 0:
                    try:
                        page.screenshot(path=f"{SHOTS}/z_4_live_{i:03d}.png", timeout=8000)
                        print(f"      t+{time.time()-t0:.0f}s alive, shot saved", flush=True)
                    except Exception as e:
                        print(f"      shot fail: {str(e)[:50]}", flush=True)

            page.screenshot(path=f"{SHOTS}/z_5_final.png")
            print("[6/6] done — final screenshot shots/z_5_final.png", flush=True)
            browser.close()
    finally:
        xvfb.terminate()

if __name__ == "__main__":
    main()
