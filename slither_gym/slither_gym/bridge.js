/*
 * Slither.io JavaScript-variable bridge.
 *
 * Reads the official client's own globals. Does not screenshot the canvas
 * and does not speak the game protocol. Episode boundaries are latched here
 * so a slow Python poll cannot miss them:
 *
 *   START  only when you have actually entered a live match
 *   END    only when you are dead
 *
 * Enter (all required):
 *   playing === true          server init packet "a" accepted the join
 *   connected === true
 *   ws is a real WebSocket    skin preview sets playing with a stub ws = {}
 *   choosing_skin is false    that preview is not a match
 *   slither exists            your snake is in the world
 *   slither.dead !== true
 *   dead_mtm === -1           not already on the death screen
 *
 * Dead (any one, and only after enter):
 *   gameOver() was called     packet "v" death, or the socket dropped mid-life
 *   dead_mtm !== -1           same paths stamp this timestamp
 *   slither.dead === true     local snake flagged dead
 *
 * Clicking Play, want_play, connecting, spawning, and the skin preview do
 * not start an episode. Another snake dying does not end yours. A socket
 * close that the client does not treat as death (packet "v" type 2) does
 * not end the episode either; that case is reported as orphaned.
 */
(function (root) {
  "use strict";

  function finite(v, fallback) {
    return typeof v === "number" && isFinite(v) ? v : fallback;
  }

  function liveSocket(g) {
    var ws = g.ws;
    if (!ws || typeof ws !== "object") return false;
    if (ws.__slitherLiveSocket === true) return true;
    try {
      if (typeof WebSocket !== "undefined" && ws instanceof WebSocket) return true;
    } catch (e) {}
    return false;
  }

  function realEnter(g) {
    if (g.playing !== true) return false;
    if (g.connected !== true) return false;
    if (g.choosing_skin === true) return false;
    if (g.building_skin === true) return false;
    if (g.selecting_cosmetic === true) return false;
    if (!liveSocket(g)) return false;
    if (g.dead_mtm !== -1) return false;
    var s = g.slither;
    if (!s || s.dead === true) return false;
    if (!isFinite(s.xx) || !isFinite(s.yy)) return false;
    return true;
  }

  function deathSignal(g, armT) {
    var go = g.__gymGameOver;
    if (go && typeof go.t === "number" && (armT == null || go.t >= armT)) {
      return {
        reason: "gameOver",
        highscore: go.highscore === true,
        dead_mtm: g.dead_mtm,
      };
    }
    if (typeof g.dead_mtm === "number" && g.dead_mtm !== -1) {
      return { reason: "dead_mtm", highscore: null, dead_mtm: g.dead_mtm };
    }
    if (g.slither && g.slither.dead === true) {
      return { reason: "slither.dead", highscore: null, dead_mtm: g.dead_mtm };
    }
    return null;
  }

  function preEnterPhase(g) {
    if (g.choosing_skin === true || g.building_skin === true) return "preview";
    if (typeof g.dead_mtm === "number" && g.dead_mtm !== -1) return "waiting_respawn";
    if (g.playing === true && g.connected === true && liveSocket(g) && !g.slither) return "spawning";
    if (g.want_play === true || g.connecting === true) return "connecting";
    return "menu";
  }

  function samplePoints(pts, n) {
    var out = [];
    if (!pts || !pts.length) return out;
    var m = Math.min(n, pts.length);
    for (var i = 0; i < m; i++) {
      var idx = m === 1 ? 0 : Math.round((i * (pts.length - 1)) / (m - 1));
      var p = pts[idx];
      if (!p || typeof p.xx !== "number" || typeof p.yy !== "number") continue;
      out.push({ xx: p.xx, yy: p.yy });
    }
    return out;
  }

  function nearest(list, origin, limit, accept) {
    if (!origin || !list) return [];
    var scored = [];
    for (var i = 0; i < list.length; i++) {
      var item = list[i];
      if (!item) continue;
      var mapped = accept(item);
      if (!mapped) continue;
      var dx = mapped.xx - origin.xx;
      var dy = mapped.yy - origin.yy;
      scored.push({ d: dx * dx + dy * dy, v: mapped });
    }
    scored.sort(function (a, b) { return a.d - b.d; });
    var out = [];
    for (var j = 0; j < scored.length && j < limit; j++) out.push(scored[j].v);
    return out;
  }

  function lengthScore(g, s) {
    if (!s || !g.fpsls || !g.fmlts) return null;
    var sct = (s.sct || 0) + (s.rsc || 0);
    var fpsl = g.fpsls[sct];
    var fmlt = g.fmlts[sct];
    if (typeof fpsl !== "number" || typeof fmlt !== "number" || fmlt === 0) return null;
    return Math.floor((fpsl + (s.fam || 0) / fmlt - 1) * 15 - 5) / 1;
  }

  function readSlitherJsState(g) {
    g = g || root;
    var s = g.slither || null;
    var origin = s && isFinite(s.xx) && isFinite(s.yy) ? { xx: s.xx, yy: s.yy } : null;
    var self = null;
    if (s && origin) {
      self = {
        id: s.id,
        nk: s.nk || "",
        xx: s.xx,
        yy: s.yy,
        fx: finite(s.fx, 0),
        fy: finite(s.fy, 0),
        ang: finite(s.ang, 0),
        wang: finite(s.wang, 0),
        eang: finite(s.eang, 0),
        sp: finite(s.sp, 0),
        tsp: finite(s.tsp, 0),
        sc: finite(s.sc, 1),
        sct: finite(s.sct, 0),
        fam: finite(s.fam, 0),
        rsc: finite(s.rsc, 0),
        md: s.md === true,
        wmd: s.wmd === true,
        dead: s.dead === true,
        alive_amt: finite(s.alive_amt, 1),
        pts: samplePoints(s.pts, 12),
      };
    }
    var selfId = self ? self.id : null;
    return {
      t: Date.now(),
      playing: g.playing === true,
      connected: g.connected === true,
      connecting: g.connecting === true,
      want_play: g.want_play === true,
      choosing_skin: g.choosing_skin === true,
      dead_mtm: typeof g.dead_mtm === "number" ? g.dead_mtm : null,
      live_socket: liveSocket(g),
      animating: g.animating === true,
      grd: finite(g.grd, 0),
      flux_grd: finite(g.flux_grd, 0),
      gsc: finite(g.gsc, 0),
      rank: finite(g.rank, 0),
      best_rank: finite(g.best_rank, 0),
      slither_count: finite(g.slither_count, 0),
      foods_c: finite(g.foods_c, 0),
      xm: finite(g.xm, 0),
      ym: finite(g.ym, 0),
      score: lengthScore(g, s),
      self: self,
      foods: nearest(g.foods, origin, 24, function (f) {
        if (f.eaten || typeof f.xx !== "number" || typeof f.yy !== "number") return null;
        return { id: f.id, xx: f.xx, yy: f.yy, sz: finite(f.sz, 0), cv: finite(f.cv, 0) };
      }),
      preys: nearest(g.preys, origin, 8, function (p) {
        if (typeof p.xx !== "number" || typeof p.yy !== "number") return null;
        return {
          id: p.id,
          xx: p.xx,
          yy: p.yy,
          sz: finite(p.sz, 0),
          ang: finite(p.ang, 0),
          sp: finite(p.sp, 0),
        };
      }),
      snakes: nearest(g.slithers, origin, 12, function (sn) {
        if (!sn || sn.id === selfId) return null;
        if (typeof sn.xx !== "number" || typeof sn.yy !== "number") return null;
        return {
          id: sn.id,
          nk: sn.nk || "",
          xx: sn.xx,
          yy: sn.yy,
          ang: finite(sn.ang, 0),
          sc: finite(sn.sc, 1),
          sp: finite(sn.sp, 0),
          dead: sn.dead === true,
          pts: samplePoints(sn.pts, 8),
        };
      }),
    };
  }

  function createSlitherMonitor() {
    var mon = {
      armed: false,
      phase: "idle",
      entered: false,
      dead: false,
      orphan: false,
      enter: null,
      death: null,
      lastJs: null,
      deathJs: null,
      armT: 0,
    };

    mon.arm = function (g) {
      mon.armed = true;
      mon.entered = false;
      mon.dead = false;
      mon.orphan = false;
      mon.phase = "menu";
      mon.enter = null;
      mon.death = null;
      mon.deathJs = null;
      mon.armT = Date.now();
      if (g) g.__gymGameOver = null;
      return mon.view();
    };

    mon.disarm = function () {
      mon.armed = false;
      mon.phase = "idle";
      return mon.view();
    };

    mon.tick = function (g, now) {
      g = g || root;
      now = now || Date.now();
      var js = readSlitherJsState(g);
      if (!mon.armed) {
        mon.phase = "idle";
        mon.lastJs = js;
        return mon.view(js);
      }
      if (mon.dead) {
        mon.phase = "dead";
        return mon.view(mon.deathJs || js);
      }
      if (!mon.entered) {
        if (realEnter(g)) {
          mon.entered = true;
          mon.orphan = false;
          mon.phase = "entered";
          mon.enter = {
            t: now,
            reason: "entered_match",
            playing: true,
            connected: true,
            dead_mtm: g.dead_mtm,
            live_socket: true,
            slither_id: g.slither.id,
            xx: g.slither.xx,
            yy: g.slither.yy,
          };
          mon.lastJs = js;
        } else {
          mon.phase = preEnterPhase(g);
          mon.lastJs = js;
        }
        return mon.view(js);
      }

      if (js.self) mon.lastJs = js;
      var sig = deathSignal(g, mon.armT);
      if (sig) {
        mon.dead = true;
        mon.orphan = false;
        mon.phase = "dead";
        mon.death = {
          t: now,
          reason: sig.reason,
          highscore: sig.highscore,
          dead_mtm: g.dead_mtm,
          playing: g.playing === true,
          slither_dead: !!(g.slither && g.slither.dead),
        };
        mon.deathJs = js.self ? js : (mon.lastJs || js);
        return mon.view(mon.deathJs);
      }

      var gone = g.playing !== true && g.dead_mtm === -1 && !g.slither;
      mon.orphan = gone;
      mon.phase = "entered";
      return mon.view(mon.lastJs || js);
    };

    mon.view = function (js) {
      return {
        armed: mon.armed,
        phase: mon.phase,
        entered: mon.entered,
        dead: mon.dead,
        orphan: mon.orphan,
        enter: mon.enter,
        death: mon.death,
        rules: {
          start: "playing + connected + live WebSocket + slither, not skin preview, dead_mtm === -1",
          end: "gameOver() or dead_mtm !== -1 or slither.dead, only after enter",
        },
        js: js || mon.deathJs || mon.lastJs || null,
      };
    };

    return mon;
  }

  function applyAction(g, angle, boost) {
    var mag = 500;
    g.xm = Math.cos(angle) * mag;
    g.ym = Math.sin(angle) * mag;
    if (typeof g.setAcceleration === "function") {
      g.setAcceleration(boost ? 1 : 0);
    } else if (g.slither) {
      g.slither.wmd = !!boost;
    }
    return { xm: g.xm, ym: g.ym, boost: !!boost };
  }

  function requestEnter(g, nick) {
    if (nick != null && g.document && typeof g.document.getElementById === "function") {
      var el = g.document.getElementById("nick");
      if (el) {
        el.disabled = false;
        el.value = String(nick).slice(0, 24);
      }
    }
    if (g.shoa) g.shoa = false;
    var clicked = false;
    var btn = g.play_btn;
    if (btn && !btn.disabled && btn.elem && typeof btn.elem.onclick === "function") {
      try {
        btn.elem.onclick();
        clicked = true;
      } catch (e) {}
    }
    if (g.want_play !== true && g.playing !== true) g.want_play = true;
    return { clicked: clicked, want_play: g.want_play === true };
  }

  function installSlitherGymBridge(win) {
    if (win.__slitherGym && win.__slitherGym.__installed) return win.__slitherGym;
    var mon = createSlitherMonitor();
    mon.__installed = true;
    win.__slitherGymBoot = Date.now();
    win.__slitherGym = {
      arm: function () { return mon.arm(win); },
      disarm: function () { return mon.disarm(); },
      tick: function () { return mon.tick(win); },
      read: function () {
        const view = mon.tick(win);
        const js = view.js || null;
        const lifecycle = {};
        for (const key in view) {
          if (key !== "js") lifecycle[key] = view[key];
        }
        return { lifecycle: lifecycle, js: js };
      },
      act: function (angle, boost) { return applyAction(win, Number(angle) || 0, !!boost); },
      enter: function (nick) { return requestEnter(win, nick); },
      ready: function () {
        return typeof win.playing === "boolean" && typeof win.dead_mtm === "number";
      },
      kickLoop: function () {
        // The client starts its loop from image onload. If an image hangs,
        // connect() never runs. Kick once, and only after a long wait, so a
        // slow-but-healthy load is not double-started.
        if (win.animating !== false) return;
        if (typeof win.startAnimation !== "function") return;
        if (Date.now() - win.__slitherGymBoot < 12000) return;
        win.startAnimation();
      },
    };

    function tryWrapGameOver() {
      if (typeof win.gameOver !== "function" || win.gameOver.__slitherGymWrapped) return;
      var orig = win.gameOver;
      function wrapped(v) {
        try {
          win.__gymGameOver = {
            t: Date.now(),
            highscore: v === true || v === 1,
            arg: v == null ? null : v,
          };
        } catch (e) {}
        return orig.apply(this, arguments);
      }
      wrapped.__slitherGymWrapped = true;
      win.gameOver = wrapped;
    }

    win.__slitherGymTimer = win.setInterval(function () {
      try {
        tryWrapGameOver();
        win.__slitherGym.kickLoop();
        mon.tick(win);
      } catch (e) {}
    }, 20);
    return win.__slitherGym;
  }

  root.createSlitherMonitor = createSlitherMonitor;
  root.readSlitherJsState = readSlitherJsState;
  root.installSlitherGymBridge = installSlitherGymBridge;
  root.slitherRealEnter = realEnter;
  root.slitherDeathSignal = deathSignal;

  if (typeof module !== "undefined" && module.exports) {
    module.exports = {
      createSlitherMonitor: createSlitherMonitor,
      readSlitherJsState: readSlitherJsState,
      installSlitherGymBridge: installSlitherGymBridge,
      realEnter: realEnter,
      deathSignal: deathSignal,
      applyAction: applyAction,
    };
  }

  if (typeof window !== "undefined" && root === window) {
    installSlitherGymBridge(window);
  }
})(typeof window !== "undefined" ? window : globalThis);
