"""
ZombsRoyale solo — Gymnasium environment with real-time JS state scraping.

The game flow is modeled EXPLICITLY as a phase machine; every transition is
tied to a measurable signal from the page's JavaScript (WebSocket traffic),
never to screenshots:

    MENU      page loaded, Unity booted, consent dismissed, ads stripped
    LOBBY     SOLO clicked -> mason (socket.io) party frames:
                 we send 42["createParty"], 42["setPartyGameMode","Solo"],
                 42["setReady",true]; server sends 42["partyJoinServer",...],
                 42["partyStateUpdated","ingame"] -> joined match server
    PLANE     game-socket tick avg size jumps to >= 90 B (players boarding /
              round loaded). We press SPACE. (Pressed again every 7 s; harmless
              in a countdown lobby where there is nothing to jump from.)
    AIRBORNE  physical input probe: HOLD W for 1.5 s — walking (lobby island)
              and even a seated plane passenger echo input sends; only FALLING
              suppresses them (physics overrides input). <= 1 echo == airborne.
    LANDED    physical input probe: tap W every 2.5 s — the first tap answered
              by a dense input burst (>= 5 sends) means we can walk == touchdown.
    ALIVE     the Gymnasium episode starts HERE (reset() returns).
    ELIMINATED detected in step() via, in order of authority:
                 [a] client SENDS 42["setIsInRound", false]   (elimination UI)
                 [b] mason recv 42["partyStateUpdated","waiting"] while alive
                     (round ended server-side)
                 [c] match socket closed
                 [d] send-silence ~5 s + tap-probe unanswered (dead players
                     emit no input; live-but-standing-still players answer)
               -> terminate within a few seconds of elimination.

Reward: +0.1/step alive, +2.0 per 30s survived, -25 on elimination.
Action:  Discrete(8): W/A/S/D, interact(E), reload(R), jump(Space), fire(LMB).
Observation: Box(12,) JS-state features (tick rate/size, send rates, phase).

record=True -> per-episode webm + menu/jump/landed/end stills (debug only).
Every episode dumps the raw WS event stream to zombs_ws_capture.json.
"""
import json
import os
import re
import shutil
import subprocess
import time

import gymnasium as gym
import numpy as np

W, H = 640, 400
DISPLAY = ":95"

# ---------------------------------------------------------------- page hooks
WS_HOOK_JS = r"""
(() => {
  window.__wsEvents = [];
  const ev = (o) => { o.t = Date.now(); if (window.__wsEvents.length < 60000) window.__wsEvents.push(o); };
  const OrigWS = window.WebSocket;
  function WS(url, protocols) {
    const ws = protocols === undefined ? new OrigWS(url) : new OrigWS(url, protocols);
    const u = String(url);
    ev({ kind: 'ctor', url: u });
    ws.addEventListener('message', (m) => {
      let bytes = 0, txt = null;
      if (typeof m.data === 'string') { bytes = m.data.length; txt = m.data.slice(0, 400); }
      else if (m.data && m.data.size !== undefined) bytes = m.data.size;
      else if (m.data && m.data.byteLength !== undefined) bytes = m.data.byteLength;
      ev({ kind: 'msg', url: u, bytes, txt });
    });
    ws.addEventListener('close', (c) => ev({ kind: 'close', url: u, code: c.code }));
    const send = ws.send.bind(ws);
    ws.send = (d) => {
      let bytes = 0, txt = null;
      if (typeof d === 'string') { bytes = d.length; txt = d.slice(0, 200); }
      else if (d && d.byteLength !== undefined) bytes = d.byteLength;
      ev({ kind: 'send', url: u, bytes, txt });
      return send(d);
    };
    return ws;
  }
  WS.prototype = OrigWS.prototype;
  ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'].forEach(k => WS[k] = OrigWS[k]);
  window.WebSocket = WS;
})()
"""

PULL_JS = "() => { const e = window.__wsEvents || []; window.__wsEvents = []; return e; }"

AD_KILLER_JS = """
() => {
  const kill = () => document.querySelectorAll(
    '[id^=cdm-zone], .lngtd-ad-wrapper, ins.adsbygoogle, [id^=aswift], [id^=google_ads], [id^=div-gpt-ad]'
  ).forEach(e => e.remove());
  kill();
  new MutationObserver(() => kill()).observe(document.documentElement, { childList: true, subtree: true });
}
"""

# ------------------------------------------------------------------- actions
ACTIONS = ["W", "A", "S", "D", "interact_E", "reload_R", "jump_deploy", "fire_LMB"]
N_ACTIONS = len(ACTIONS)
OBS_DIM = 12
W_A, A_A, S_A, D_A, E_A, R_A, JUMP_A, FIRE_A = range(N_ACTIONS)

# -------------------------------------------------------------------- phases
MENU, LOBBY, PLANE, AIRBORNE, LANDED, ALIVE, ELIMINATED = range(7)
PHASE_NAMES = ["menu", "lobby", "plane", "airborne", "landed", "alive", "eliminated"]

GAME_RE = re.compile(r"eggs\.gg", re.I)
MASON_RE = re.compile(r"zombsroyale\.io", re.I)


def is_game_socket(url):
    u = url or ""
    return bool(GAME_RE.search(u)) and "pinger" not in u.lower()


def is_mason_socket(url):
    u = (url or "").lower()
    return bool(MASON_RE.search(u)) and "gateway" in u


class ZombsRoyaleEnv(gym.Env):
    """One episode = one solo match, starting ON THE GROUND after the drop,
    ending shortly after the local player is ELIMINATED."""

    metadata = {"render_modes": []}

    def __init__(self, record=False, max_steps=250, step_seconds=0.9,
                 plane_ride=(4.0, 7.0), debug_dir="shots_debug", video_dir="videos",
                 capture_file="zombs_ws_capture.json", verbose=True):
        super().__init__()
        self.record = record
        self.max_steps = max_steps
        self.step_seconds = step_seconds
        self.plane_ride = plane_ride
        self.debug_dir = debug_dir
        self.video_dir = video_dir
        self.capture_file = capture_file
        self.verbose = verbose

        self.action_space = gym.spaces.Discrete(N_ACTIONS)
        self.observation_space = gym.spaces.Box(low=0.0, high=np.inf, shape=(OBS_DIM,), dtype=np.float32)

        self._xvfb = None
        self._browser = None
        self._context = None
        self._page = None
        self._pw = None
        self._episode_no = 0

        # per-episode
        self._phase = MENU
        self._phase_history = []       # [(phase, unix_t)]
        self._events = []
        self._mason_frames = []
        self._elim_reason = None
        self._t_click = None
        self._t_jump = None
        self._t_land = None
        self._last_step_time = None
        self._step = 0
        self._prev_action = N_ACTIONS - 1
        self._saw_send_activity = False
        self._last_send_activity_t = None
        self._last_probe_t = 0.0
        self._plane_entered_t = None

    # ------------------------------------------------------------ plumbing
    def _log(self, msg):
        if self.verbose:
            print(msg, flush=True)

    def _set_phase(self, phase, note=""):
        if phase == self._phase:
            return
        self._phase = phase
        self._phase_history.append((PHASE_NAMES[phase], time.time()))
        self._log(f"[ep{self._episode_no}] PHASE -> {PHASE_NAMES[phase].upper()} {note}")

    def _shot(self, page, name):
        if self.record:
            try:
                page.screenshot(path=os.path.join(self.debug_dir, f"ep{self._episode_no}_{name}.png"), timeout=8000)
            except Exception:
                pass

    def _ensure_stack(self):
        need_swap = subprocess.run(
            ["sh", "-c", "test $(awk '/^SwapTotal/{print int($2/1024)}' /proc/meminfo) -lt 2000"]
        ).returncode == 0
        if need_swap:
            for cmd in (
                ["sudo", "dd", "if=/dev/zero", "of=/swapfile", "bs=1M", "count=3072", "status=none"],
                ["sudo", "chmod", "600", "/swapfile"],
                ["sudo", "mkswap", "-q", "/swapfile"],
                ["sudo", "swapon", "/swapfile"],
            ):
                subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if self._xvfb is None:
            self._xvfb = subprocess.Popen(
                ["Xvfb", DISPLAY, "-screen", "0", f"{W}x{H}x24", "-nolisten", "tcp"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            time.sleep(1.5)

    # ------------------------------------------------- JS-derived statistics
    def _game_stats(self, window_s):
        cutoff = (time.time() - window_s) * 1000
        sizes = [e.get("bytes", 0) for e in self._events
                 if e["kind"] == "msg" and is_game_socket(e.get("url")) and e["t"] >= cutoff]
        n = len(sizes)
        return {"rate": n / window_s, "avg_size": (sum(sizes) / n) if n else 0.0}

    def _sends_in(self, since_s, until_s=None):
        lo = since_s * 1000
        hi = (until_s or time.time()) * 1000
        return [e for e in self._events
                if e["kind"] == "send" and is_game_socket(e.get("url")) and lo <= e["t"] <= hi]

    def _scan_mason(self, new_events):
        """Collect socket.io frames; return dict of notable markers found."""
        markers = {}
        for e in new_events:
            t = e.get("txt")
            if not t:
                continue
            if is_mason_socket(e.get("url")) and t.startswith("42["):
                self._mason_frames.append({"t": e["t"], "dir": e["kind"], "frame": t[:400]})
                if '"setIsInRound", false' in t or "setIsInRound\",false" in t:
                    markers["isInRound_false"] = e["t"]
                if '"partyStateUpdated","waiting"' in t or '"partyStateUpdated", "waiting"' in t:
                    markers["party_waiting"] = e["t"]
                if "partyJoinServer" in t:
                    self._log(f"[ep{self._episode_no}] mason: {t[:130]}")
                if '"partyStateUpdated","ingame"' in t or '"partyStateUpdated", "ingame"' in t:
                    markers["party_ingame"] = e["t"]
        return markers

    # ------------------------------------------------------------ gym: reset
    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self._episode_no += 1
        self._phase = MENU
        self._phase_history = [(PHASE_NAMES[MENU], time.time())]
        self._events = []
        self._mason_frames = []
        self._elim_reason = None
        self._t_click = None
        self._t_jump = None
        self._t_land = None
        self._last_step_time = None
        self._step = 0
        self._prev_action = N_ACTIONS - 1
        self._saw_send_activity = False
        self._last_send_activity_t = None
        self._last_probe_t = 0.0
        self._plane_entered_t = None

        self._ensure_stack()
        os.makedirs(self.debug_dir, exist_ok=True)
        os.makedirs(self.video_dir, exist_ok=True)

        from playwright.sync_api import sync_playwright
        if self._pw is None:
            self._pw = sync_playwright().start()

        env = dict(os.environ, DISPLAY=DISPLAY, LIBGL_ALWAYS_SOFTWARE="1")
        self._browser = self._pw.firefox.launch(
            headless=False, env=env,
            firefox_user_prefs={"gfx.webrender.software": True, "fission.autostart": False, "dom.ipc.processCount": 1},
        )
        ctx_kw = dict(viewport={"width": W, "height": H})
        if self._record_on():
            ctx_kw.update(record_video_dir=self.video_dir, record_video_size={"width": W, "height": H})
        self._context = self._browser.new_context(**ctx_kw)
        page = self._context.new_page()
        page.set_default_timeout(8000)
        page.add_init_script(WS_HOOK_JS)
        self._page = page
        page.on("crash", lambda: self._log("   !! page crash"))

        # ---- MENU: load + wait for Unity ----
        self._log(f"[ep{self._episode_no} reset] loading zombsroyale.io ...")
        page.goto("https://zombsroyale.io/", wait_until="domcontentloaded", timeout=60000)
        t0 = time.time()
        while time.time() - t0 < 200:
            time.sleep(4)
            try:
                if page.evaluate("() => !document.body.innerText.includes('The game is loading')"):
                    break
            except Exception:
                pass
        self._log(f"[ep{self._episode_no} reset] game loaded in {time.time()-t0:.0f}s")
        time.sleep(8)
        self._drain()

        for _ in range(4):
            done = False
            for fr in page.frames:
                try:
                    el = fr.locator("text=/^OK$/i").last
                    if el.is_visible(timeout=300):
                        el.click(timeout=2000)
                        done = True
                        break
                except Exception:
                    continue
            if done:
                break
            time.sleep(1)
        page.evaluate(AD_KILLER_JS)
        time.sleep(2)
        self._shot(page, "menu")
        self._drain()

        # ---- LOBBY: click SOLO -> matchmaking ----
        self._set_phase(LOBBY, "(clicking SOLO)")
        page.mouse.click(215, 227)
        time.sleep(4)
        page.evaluate(AD_KILLER_JS)
        self._t_click = time.time()
        self._drain()

        # ---- PLANE -> AIRBORNE -> LANDED: unified wait ----
        last_space = 0.0
        last_probe = 0.0
        last_air_test = 0.0
        airborne = False
        land_t = None
        while time.time() - self._t_click < 420:
            time.sleep(1)
            new = self._drain()
            markers = self._scan_mason(new)

            # round ended server-side while we are still pre-ALIVE (we were
            # cycling/spectating) -> mason says back to the lobby
            if "party_waiting" in markers and self._phase in (LOBBY, PLANE, AIRBORNE):
                self._set_phase(LOBBY, "(mason: partyStateUpdated waiting — round cycled)")
                self._t_jump = None
                self._plane_entered_t = None
                airborne = False

            # LOBBY -> PLANE: a fresh round is joined for us. Primary signal:
            # mason partyStateUpdated "ingame" (fires again for every new
            # round after a "waiting"). Fallback: busy tick signature.
            if self._phase == LOBBY:
                st = self._game_stats(5.0)
                if "party_ingame" in markers:
                    self._set_phase(PLANE, f"(mason ingame, {time.time()-self._t_click:.0f}s after SOLO click)")
                    self._plane_entered_t = time.time()
                elif st["rate"] >= 10.0 and st["avg_size"] >= 90.0:
                    self._set_phase(PLANE, f"(tick avg {st['avg_size']:.0f}B, "
                                           f"{time.time()-self._t_click:.0f}s after SOLO click)")
                    self._plane_entered_t = time.time()

            if self._phase == PLANE:
                # re-press SPACE periodically; first press records t_jump
                if time.time() - last_space >= 7.0:
                    page.keyboard.press("Space")
                    last_space = time.time()
                    if self._t_jump is None:
                        self._t_jump = last_space
                        self._shot(page, "jump")
                        self._log(f"[ep{self._episode_no} reset] SPACE pressed — trying to jump ...")
                # safety: no airborne confirmation for a whole round length ->
                # we must be spectating; demote and wait for the next round
                if (self._plane_entered_t is not None
                        and time.time() - self._plane_entered_t > 120):
                    self._set_phase(LOBBY, "(no jump within 120s of ingame — round cycled?)")
                    self._plane_entered_t = None
                    self._t_jump = None
                    airborne = False

            # PLANE -> AIRBORNE: falling suppresses held-W input echoes
            if self._phase == PLANE and self._t_jump is not None:
                if time.time() - last_air_test >= 4.0:
                    last_air_test = time.time()
                    page.keyboard.down("w")
                    time.sleep(1.5)
                    page.keyboard.up("w")
                    new += self._drain()
                    during = len(self._sends_in(last_air_test - 0.1))
                    if during <= 1:
                        self._set_phase(AIRBORNE, f"(held W 1.5s, {during} input echoes — falling)")

            # AIRBORNE -> LANDED: two-stage physical proof of walking:
            #   (i) W-tap answered by a dense input burst (>= 5 sends)
            #   (ii) HELD W produces a CONTINUOUS movement stream (>= 8 sends
            #       over 1.5 s). Spectate mode only echoes key-down EDGES
            #       (1-6 sends) and never a continuous stream, so this rejects
            #       tapping along with a spectated round.
            if self._phase == AIRBORNE and time.time() - last_probe >= 2.5:
                last_probe = time.time()
                page.keyboard.down("w")
                time.sleep(0.5)
                page.keyboard.up("w")
                time.sleep(1.0)
                new += self._drain()
                resp = len(self._sends_in(last_probe - 0.1))
                if resp >= 5:
                    t_hold = time.time()
                    page.keyboard.down("w")
                    time.sleep(1.5)
                    page.keyboard.up("w")
                    new += self._drain()
                    stream = len(self._sends_in(t_hold - 0.1))
                    if stream >= 8:
                        land_t = time.time()
                        self._set_phase(LANDED, f"(tap {resp} sends + held-W stream {stream} sends, "
                                                f"air {land_t-self._t_jump:.1f}s)")
                        break
                    else:
                        self._log(f"[ep{self._episode_no} reset] tap answered ({resp}) but no movement "
                                  f"stream ({stream} sends) — spectating, keep waiting")

        if land_t is None:
            land_t = time.time()
            self._log(f"[ep{self._episode_no} reset] landing not confirmed within 150s — forcing LANDED")
            self._set_phase(LANDED, "(timeout)")
        if self._t_jump is None:
            self._t_jump = self._t_click
        self._t_land = land_t
        self._shot(page, "landed")

        # ---- ALIVE: the Gymnasium episode starts on the ground ----
        self._set_phase(ALIVE, f"({land_t-self._t_click:.0f}s from SOLO click to on the ground)")
        obs = self._observe()
        return obs, {"phase": self._phase_name(),
                     "click_to_land_seconds": round(land_t - self._t_click, 1),
                     "air_seconds": round(land_t - self._t_jump, 1),
                     "phase_history": [p for p, _ in self._phase_history]}

    def _record_on(self):
        return self.record

    # ------------------------------------------------------------- gym: step
    def step(self, action):
        assert self.action_space.contains(int(action))
        self._step += 1
        page = self._page
        terminated = False
        truncated = False
        reward = 0.1  # survival per step
        if self._step % 30 == 0:
            reward += 2.0

        # ---- act ----
        a = int(action)
        try:
            if a in (W_A, A_A, S_A, D_A):
                page.keyboard.down(ACTIONS[a].lower())
                time.sleep(self.step_seconds * 0.75)
                page.keyboard.up(ACTIONS[a].lower())
            elif a in (E_A, R_A, JUMP_A):
                page.keyboard.press(ACTIONS[a].split("_")[1])
                time.sleep(self.step_seconds * 0.4)
            elif a == FIRE_A:
                page.mouse.click(int(W * 0.52), int(H * 0.45))
                time.sleep(self.step_seconds * 0.4)
            else:
                time.sleep(self.step_seconds * 0.4)
        except Exception:
            pass
        self._prev_action = a

        elapsed = time.time() - (self._last_step_time or self._t_land)
        if elapsed < self.step_seconds:
            time.sleep(self.step_seconds - elapsed)
        self._last_step_time = time.time()

        # ---- scrape state ----
        new = self._drain()
        markers = self._scan_mason(new)
        closed = any(e["kind"] == "close" and is_game_socket(e.get("url")) for e in new)

        # track send activity (live players emit input constantly)
        recent_sends = self._sends_in(time.time() - 1.0)
        if recent_sends:
            self._saw_send_activity = True
            self._last_send_activity_t = time.time()

        # ---- ELIMINATED? explicit markers first, then physical probe ----
        elim_reason = None
        if "isInRound_false" in markers:
            elim_reason = "client sent setIsInRound:false (eliminated)"
        elif "party_waiting" in markers:
            elim_reason = "mason: round ended (partyStateUpdated waiting)"
        elif closed:
            elim_reason = "match socket closed"
        else:
            # fast fallback: ~5s of send silence, then a tap probe that must
            # be answered within ~2s — dead players emit nothing at all.
            silence = time.time() - (self._last_send_activity_t or time.time())
            if self._saw_send_activity and silence >= 5.0 and time.time() - self._last_probe_t >= 3.0:
                self._last_probe_t = time.time()
                page.keyboard.down("w")
                time.sleep(0.5)
                page.keyboard.up("w")
                time.sleep(1.2)
                new += self._drain()
                resp = len(self._sends_in(self._last_probe_t - 0.1))
                if resp >= 3:
                    self._last_send_activity_t = time.time()  # alive, was just quiet
                    self._log(f"[ep{self._episode_no}] silence probe answered ({resp} sends) — still alive")
                else:
                    elim_reason = "send silence + unanswered input probe"

        if elim_reason and self._phase != ELIMINATED:
            self._set_phase(ELIMINATED, f"({elim_reason})")
            self._elim_reason = elim_reason
            reward -= 25.0
            terminated = True
            self._shot(page, "end")
            self._log(f"[ep{self._episode_no}] ELIMINATED at step {self._step} "
                      f"({time.time()-self._t_land:.0f}s ground time)")

        if not terminated and self._step >= self.max_steps:
            truncated = True

        obs = self._observe()
        st = self._game_stats(2.0)
        info = {
            "phase": self._phase_name(),
            "ground_time": round(time.time() - self._t_land, 1),
            "tick_rate": round(st["rate"], 1),
            "tick_avg_size": round(st["avg_size"], 1),
            "sends_1s": len(recent_sends),
            "mason_events": len(self._mason_frames),
            "send_rate12": round(len(self._sends_in(time.time() - 12.0)) / 12.0, 2),
            "last_action": ACTIONS[a],
            "elim_reason": self._elim_reason,
            "phase_history": [p for p, _ in self._phase_history],
        }
        return obs, reward, terminated, truncated, info

    # ------------------------------------------------------------ gym: close
    def close(self):
        try:
            if self._context is not None:
                video = self._page.video
                self._context.close()
                if video is not None and self.record:
                    try:
                        vpath = video.path()
                        out = os.path.join(self.video_dir, f"gym_episode_{self._episode_no}.webm")
                        shutil.move(vpath, out)
                        self._log(f"[ep{self._episode_no}] video saved: {out}")
                    except Exception:
                        pass
            if self._browser is not None:
                self._browser.close()
        except Exception:
            pass
        self._browser = self._context = self._page = None
        self._dump_capture()

    # ------------------------------------------------------------- internals
    def _phase_name(self):
        return PHASE_NAMES[self._phase]

    def _drain(self):
        try:
            new = self._page.evaluate(PULL_JS)
        except Exception as e:
            self._log(f"   [drain fail: {str(e)[:60]}]")
            return []
        self._events.extend(new)
        return new

    def _observe(self):
        now = time.time()
        st1 = self._game_stats(1.0)
        send_1s = len(self._sends_in(now - 1.0))
        total_msgs = sum(1 for e in self._events if e["kind"] == "msg" and is_game_socket(e.get("url")))
        ground_t = (now - self._t_land) if self._t_land else 0.0
        send_silence = min(now - (self._last_send_activity_t or now), 30.0)
        if ground_t < 3:
            phase = [1, 0, 0, 0]
        elif ground_t < 30:
            phase = [0, 1, 0, 0]
        elif ground_t < 90:
            phase = [0, 0, 1, 0]
        else:
            phase = [0, 0, 0, 1]
        return np.array([ground_t, total_msgs, st1["rate"], send_1s, st1["avg_size"],
                         1.0 if self._phase == ELIMINATED else 0.0, send_silence, *phase,
                         self._prev_action / (N_ACTIONS - 1)], dtype=np.float32)

    def _dump_capture(self):
        try:
            with open(self.capture_file, "w") as f:
                json.dump({
                    "phases": [{"phase": p, "t": t} for p, t in self._phase_history],
                    "elim_reason": self._elim_reason,
                    "n_events": len(self._events),
                    "mason_frames": self._mason_frames[-200:],
                    "events": self._events[-30000:],
                }, f, indent=1)
        except Exception:
            pass
