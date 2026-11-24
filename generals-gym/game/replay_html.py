"""Turn a saved replay into one self-contained HTML file.

    from game.replay import Replay
    from game.replay_html import write_html_player

    write_html_player(Replay.load("replays/game.json"), "replays/game.html")

The result is a single ``.html`` file with the replay inlined as JSON and a
tiny canvas player (play / pause / scrub / speed).  No server, no network, no
dependencies -- open it with a double click and it plays.
"""

from __future__ import annotations

import json
from pathlib import Path

from .replay import Replay

_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>__TITLE__</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body {
    margin: 0; min-height: 100vh; display: grid; place-items: center;
    background: radial-gradient(900px 500px at 20% -10%, rgba(76,141,255,.14), transparent 60%),
                radial-gradient(800px 480px at 100% 0%, rgba(255,95,95,.10), transparent 60%),
                #090c11;
    color: #e9eef7; font: 14px/1.4 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  }
  #app { width: min(94vmin, 900px); padding: 18px; }
  h1 { font-size: 17px; margin: 0 0 10px; letter-spacing: -.01em; }
  .scores { display: flex; justify-content: space-between; gap: 12px; margin-bottom: 8px;
            font-weight: 600; font-size: 13px; }
  .s0 { color: #a0cdff; } .s1 { color: #ffa5a5; }
  .bar { height: 8px; border-radius: 99px; background: #1e2736; overflow: hidden;
         display: flex; margin-bottom: 12px; }
  .bar i { display: block; height: 100%; }
  canvas { width: 100%; height: auto; display: block; border-radius: 12px; background: #0c1119; }
  .controls { display: flex; align-items: center; gap: 10px; margin-top: 12px; flex-wrap: wrap; }
  button, select {
    background: #16202c; color: #e9eef7; border: 1px solid #2b3b52; border-radius: 9px;
    padding: 7px 12px; font: inherit; font-weight: 600; cursor: pointer;
  }
  button:hover, select:hover { background: #1d2a39; }
  input[type=range] { flex: 1; accent-color: #4c8dff; min-width: 160px; }
  .turn { font-variant-numeric: tabular-nums; color: #8d9aae; min-width: 96px; text-align: right; }
  .muted { color: #667287; font-size: 12px; margin-top: 8px; }
</style>
</head>
<body>
<div id="app">
  <h1>__TITLE__</h1>
  <div class="scores"><span class="s0" id="l0"></span><span class="s1" id="l1"></span></div>
  <div class="bar"><i id="b0" style="background:#4c8dff"></i><i id="b1" style="background:#ff5f5f"></i></div>
  <canvas id="board"></canvas>
  <div class="controls">
    <button id="play">Pause</button>
    <input type="range" id="scrub" min="0" max="0" value="0" />
    <span class="turn" id="turn"></span>
    <select id="speed">
      <option value="6">0.5x</option>
      <option value="12" selected>1x</option>
      <option value="24">2x</option>
      <option value="48">4x</option>
    </select>
  </div>
  <div class="muted" id="foot"></div>
</div>
<script>
const REPLAY = __DATA__;
(() => {
  const R = REPLAY;
  const COLORS = { board:'#0c1119', fog:'#141b25', mountain:'#2b3440', neutral:'#8a93a2',
                   you:'#4c8dff', enemy:'#ff5f5f', text:'#f6f9ff', dark:'#151b24' };
  const UNKNOWN = -3, MOUNTAIN = -2, NEUTRAL = -1;
  const canvas = document.getElementById('board');
  const ctx = canvas.getContext('2d');
  const el = {
    play: document.getElementById('play'), scrub: document.getElementById('scrub'),
    turn: document.getElementById('turn'), speed: document.getElementById('speed'),
    l0: document.getElementById('l0'), l1: document.getElementById('l1'),
    b0: document.getElementById('b0'), b1: document.getElementById('b1'),
    foot: document.getElementById('foot'),
  };

  let frames = R.frames.map((f) => ({
    t: f.t, o: expand(f.o), a: expand(f.a), c: expand(f.c),
    g: f.g || [null, null], done: !!f.done, moves: f.moves || [],
  }));
  function expand(rle) {
    const out = new Array(R.game.h * R.game.w);
    let at = 0;
    for (const [v, n] of rle) { out.fill(v, at, at + n); at += n; }
    return out;
  }

  const state = { i: 0, playing: true, fps: 12, last: null, acc: 0 };
  el.scrub.max = String(Math.max(0, frames.length - 1));

  function visibility(frame) {
    return null;
  }

  function roundRect(x, y, w, h, r) {
    ctx.beginPath();
    if (ctx.roundRect) { ctx.roundRect(x, y, w, h, r); return; }
    ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
  }

  function drawArrow(cx, cy, cell, dir) {
    const angle = { 1: -Math.PI / 2, 2: Math.PI / 2, 3: Math.PI, 4: 0 }[dir];
    const d = cell * 0.30;
    ctx.save(); ctx.globalAlpha = 0.92; ctx.translate(cx, cy); ctx.rotate(angle);
    ctx.beginPath();
    ctx.moveTo(d * 0.66, 0);
    ctx.lineTo(-d * 0.12, -d * 0.34);
    ctx.lineTo(-d * 0.12, -d * 0.13);
    ctx.lineTo(-d * 0.7, -d * 0.13);
    ctx.lineTo(-d * 0.7, d * 0.13);
    ctx.lineTo(-d * 0.12, d * 0.13);
    ctx.lineTo(-d * 0.12, d * 0.34);
    ctx.closePath(); ctx.fillStyle = '#ffffff'; ctx.fill(); ctx.restore();
  }

  function draw() {
    const frame = frames[state.i];
    if (!frame) return;
    const h = R.game.h, w = R.game.w;
    const size = Math.max(320, Math.min(900, Math.floor(window.innerWidth - 80)));
    const cell = Math.floor(size / w);
    const px = cell * w;
    if (canvas.width !== px) { canvas.width = px; canvas.height = cell * h; }
    const vis = visibility(frame);
    const gap = Math.max(0.6, cell * 0.045);
    const radius = Math.max(1.5, cell * 0.16);

    ctx.fillStyle = COLORS.board; ctx.fillRect(0, 0, px, cell * h);
    let land = [0, 0], army = [0, 0];
    for (let r = 0; r < h; r += 1) {
      for (let c = 0; c < w; c += 1) {
        const i = r * w + c;
        const owner = vis && !vis[i] ? UNKNOWN : frame.o[i];
        const count = vis && !vis[i] ? 0 : frame.a[i];
        if (owner === 0) land[0] += 1;
        if (owner === 1) land[1] += 1;
        if (owner === 0) army[0] += count;
        if (owner === 1) army[1] += count;
        const x = c * cell, y = r * cell;
        let fill = COLORS.neutral;
        if (owner === UNKNOWN) fill = COLORS.fog;
        else if (owner === MOUNTAIN) fill = COLORS.mountain;
        else if (owner === 0) fill = COLORS.you;
        else if (owner === 1) fill = COLORS.enemy;
        roundRect(x + gap, y + gap, cell - 2 * gap, cell - 2 * gap, radius);
        ctx.fillStyle = fill; ctx.fill();
        if (owner === UNKNOWN || owner === MOUNTAIN) continue;
        if (frame.c[i]) {
          const inset = Math.max(1, cell * 0.07);
          roundRect(x + gap + inset, y + gap + inset, cell - 2 * gap - 2 * inset,
                    cell - 2 * gap - 2 * inset, radius * 0.7);
          ctx.strokeStyle = 'rgba(255,214,130,.9)';
          ctx.lineWidth = Math.max(1, cell * 0.045); ctx.stroke();
        }
        if ((frame.g[0] && frame.g[0][0] === r && frame.g[0][1] === c) ||
            (frame.g[1] && frame.g[1][0] === r && frame.g[1][1] === c)) {
          ctx.fillStyle = 'rgba(255,255,255,.55)';
          ctx.beginPath(); ctx.arc(x + cell / 2, y + cell / 2, cell * 0.2, 0, 7); ctx.fill();
        }
        if (count > 0) {
          const label = count >= 10000 ? `${Math.round(count / 1000)}k`
            : count >= 1000 ? `${(count / 1000).toFixed(1)}k` : String(count);
          const fs = Math.max(7, Math.floor(cell * (label.length >= 3 ? 0.34 : 0.44)));
          ctx.font = `700 ${fs}px ui-monospace, Menlo, Consolas, monospace`;
          ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
          ctx.fillStyle = owner === NEUTRAL ? COLORS.dark : COLORS.text;
          ctx.fillText(label, x + cell / 2, y + cell / 2 + cell * 0.02);
        }
      }
    }

    for (const move of frame.moves) {
      if (!move) continue;
      if (vis && !vis[move.from]) continue;
      const sr = Math.floor(move.from / w), sc = move.from % w;
      const dr = Math.floor(move.to / w), dc = move.to % w;
      const dir = dr < sr ? 1 : dr > sr ? 2 : dc < sc ? 3 : 4;
      drawArrow(sc * cell + cell / 2, sr * cell + cell / 2, cell, dir);
    }

    const total = Math.max(1, land[0] + land[1]);
    el.b0.style.width = `${(100 * land[0]) / total}%`;
    el.b1.style.width = `${(100 * land[1]) / total}%`;
    const names = (R.players || []).map((p) => p.name);
    el.l0.textContent = `You · ${names[0] || 'player 0'} · ${land[0]} land · ${army[0]} army`;
    el.l1.textContent = `Enemy · ${names[1] || 'player 1'} · ${land[1]} land · ${army[1]} army`;
    const moveSlot = frame.half_turn ? 1 : 2;
    const phase = R.game.moves_per_turn === 2 && frame.t > 0
      ? ` · move ${moveSlot}/2` : '';
    el.turn.textContent = `turn ${frame.t}${phase}`;
    el.scrub.value = String(state.i);
  }

  function tick(now) {
    if (state.last === null) state.last = now;
    const dt = (now - state.last) / 1000;
    state.last = now;
    if (state.playing) {
      state.acc += dt;
      const step = 1 / state.fps;
      while (state.acc >= step) {
        state.acc -= step;
        if (state.i < frames.length - 1) state.i += 1;
        else state.playing = false;
      }
      draw();
    }
    requestAnimationFrame(tick);
  }

  el.play.addEventListener('click', () => {
    if (!state.playing && state.i >= frames.length - 1) state.i = 0;
    state.playing = !state.playing;
    el.play.textContent = state.playing ? 'Pause' : 'Play';
  });
  el.scrub.addEventListener('input', () => {
    state.i = Number(el.scrub.value);
    state.playing = false;
    el.play.textContent = 'Play';
    draw();
  });
  el.speed.addEventListener('change', () => { state.fps = Number(el.speed.value); });
  window.addEventListener('keydown', (event) => {
    if (event.code === 'Space') { event.preventDefault(); el.play.click(); }
    if (event.code === 'ArrowRight') { state.i = Math.min(frames.length - 1, state.i + 1); draw(); }
    if (event.code === 'ArrowLeft') { state.i = Math.max(0, state.i - 1); draw(); }
  });

  const meta = R.meta && Object.keys(R.meta).length ? ` · ${JSON.stringify(R.meta)}` : '';
  el.foot.textContent =
    `${R.result.reason} · turn ${R.result.turns} · ${R.game.h}x${R.game.w}` +
    ` · full board · space to pause, arrows to step${meta}`;
  requestAnimationFrame(tick);
})();
</script>
</body>
</html>
"""


def player_html(replay: Replay, title: str | None = None) -> str:
    """Return the standalone HTML player for ``replay`` as a string."""
    if not len(replay):
        raise ValueError("replay has no frames")
    names = replay.names()
    title = title or f"{names[0]} vs {names[1]}"
    data = json.dumps(replay.to_dict(), separators=(",", ":")).replace("<", "\\u003c")
    return (
        _TEMPLATE.replace("__TITLE__", _escape(title))
        .replace("__DATA__", data)
    )


def write_html_player(replay: Replay, path: str | Path, title: str | None = None) -> Path:
    """Write the standalone HTML player to ``path``."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(player_html(replay, title), encoding="utf-8")
    return path


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
