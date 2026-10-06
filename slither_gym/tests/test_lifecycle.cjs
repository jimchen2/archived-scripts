const { createSlitherMonitor } = require("../slither_gym/bridge.js");

function assert(cond, msg) {
  if (!cond) {
    console.error("FAIL:", msg);
    process.exit(1);
  }
}

function live() {
  return { __slitherLiveSocket: true };
}

function snake(extra = {}) {
  return { id: 7, xx: 1000, yy: 2000, ang: 0.4, dead: false, ...extra };
}

function globals(extra = {}) {
  return {
    playing: false,
    connected: false,
    connecting: false,
    want_play: false,
    choosing_skin: false,
    dead_mtm: -1,
    ws: null,
    slither: null,
    slithers: [],
    foods: [],
    preys: [],
    grd: 16384,
    flux_grd: 16000,
    __gymGameOver: null,
    ...extra,
  };
}

function enteredGlobals(extra = {}) {
  return globals({
    playing: true,
    connected: true,
    ws: live(),
    slither: snake(),
    dead_mtm: -1,
    ...extra,
  });
}

let mon = createSlitherMonitor();
let g = globals();

assert(mon.tick(g).phase === "idle", "unarmed monitor stays idle");
mon.arm(g);
assert(mon.tick(g).phase === "menu", "armed on the login screen is menu, not started");
assert(mon.entered === false, "menu is not an enter");

g.want_play = true;
assert(mon.tick(g).phase === "connecting", "Play click is connecting, not start");
assert(mon.entered === false, "want_play must not start the episode");

g.playing = true;
g.connected = true;
g.choosing_skin = true;
g.ws = {};
g.slither = snake();
assert(mon.tick(g).phase === "preview", "skin preview must not count as entering");
assert(mon.entered === false, "preview snake is not a match");

g.choosing_skin = false;
g.ws = {};
assert(mon.tick(g).phase !== "entered", "stub websocket must not count as a live match");
assert(mon.entered === false, "still not entered");

g.ws = live();
g.slither = null;
g.want_play = false;
assert(mon.tick(g).phase === "spawning", "server accepted us but the snake is not in yet");
assert(mon.entered === false, "spawning is not the start");

g.slither = snake();
g.dead_mtm = 12345;
assert(mon.tick(g).phase === "waiting_respawn", "death screen is not a new enter");
assert(mon.entered === false, "dead_mtm blocks the start");

g.dead_mtm = -1;
const started = mon.tick(g, 1000);
assert(started.phase === "entered", "live socket + slither starts the episode");
assert(started.entered === true, "entered latch");
assert(started.dead === false, "enter is not death");
assert(started.enter.reason === "entered_match", "enter reason");
assert(started.enter.slither_id === 7, "enter records the snake id");

g.slithers = [{ id: 9, xx: 1100, yy: 2100, dead: true, pts: [] }];
assert(mon.tick(g, 1100).phase === "entered", "another snake dying does not end you");
assert(mon.dead === false, "still alive");

g.playing = false;
g.slither = null;
g.dead_mtm = -1;
const orphan = mon.tick(g, 1200);
assert(orphan.phase === "entered", "disconnect without a death signal does not end");
assert(orphan.dead === false, "orphan is not death");
assert(orphan.orphan === true, "orphan is reported separately");

g.playing = true;
g.connected = true;
g.ws = live();
g.slither = snake();
g.dead_mtm = -1;
assert(mon.tick(g, 1300).dead === false, "returning to the match is not death");
assert(mon.orphan === false, "orphan clears when the match is back");

g.dead_mtm = mon.armT + 50;
g.__gymGameOver = { t: mon.armT + 50, highscore: true };
const ended = mon.tick(g, mon.armT + 60);
assert(ended.phase === "dead", "death ends the episode");
assert(ended.dead === true, "dead latch");
assert(ended.death.reason === "gameOver", "gameOver is the preferred death signal");
assert(ended.death.highscore === true, "highscore flag is kept");

g.dead_mtm = -1;
g.__gymGameOver = null;
g.playing = false;
g.slither = null;
const stayed = mon.tick(g, mon.armT + 5000);
assert(stayed.phase === "dead", "death stays latched after the client clears dead_mtm");
assert(stayed.dead === true, "latch ignores the login fade");

mon.arm(g);
g = globals({ want_play: true });
assert(mon.tick(g).phase === "connecting", "re-arm starts a fresh watch");
assert(mon.entered === false && mon.dead === false, "re-arm clears both latches");

g.__gymGameOver = { t: mon.armT - 10, highscore: false };
g.playing = true;
g.connected = true;
g.ws = live();
g.slither = snake();
g.dead_mtm = -1;
mon.tick(g);
const stale = mon.tick(g);
assert(stale.phase === "entered" && stale.dead === false, "stale gameOver from the previous life is ignored");

g.slither.dead = true;
const byFlag = mon.tick(g);
assert(byFlag.dead === true && byFlag.death.reason === "slither.dead", "slither.dead ends the episode");

mon = createSlitherMonitor();
mon.arm(g);
g = enteredGlobals({
  slither: snake({ id: 3, xx: 50, yy: 60, sct: 2, fam: 0, rsc: 0 }),
  foods: [
    null,
    { id: 1, xx: 80, yy: 60, sz: 8 },
    { id: 2, xx: 5000, yy: 60, sz: 2, eaten: true },
  ],
  slithers: [
    { id: 3, xx: 50, yy: 60 },
    { id: 4, xx: 90, yy: 60, ang: 1, sc: 2, dead: false, pts: [{ xx: 70, yy: 60 }] },
  ],
  fpsls: [0, 1, 2],
  fmlts: [1, 1, 1],
});
const snap = mon.tick(g);
assert(snap.phase === "entered", "state snapshot still enters");
assert(snap.js.self.xx === 50, "self coordinates come from slither");
assert(snap.js.foods.length === 1 && snap.js.foods[0].id === 1, "null and eaten food dropped");
assert(snap.js.snakes.length === 1 && snap.js.snakes[0].id === 4, "own snake excluded from enemies");
assert(snap.js.score === 10, "length score uses the client formula");

console.log("lifecycle tests passed");
