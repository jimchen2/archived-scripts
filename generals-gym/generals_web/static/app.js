/* generals.jax browser client
 * Canvas board + time-driven turns.  Keyboard: WASD / arrows move the selected
 * tile (and queue a path), Z splits, Space deselects, Q clears, P pauses.
 */
(() => {
  'use strict';

  const OBSTACLE = -4;
  const UNKNOWN = -3;
  const MOUNTAIN = -2;
  const NEUTRAL = -1;

  const DIRS = { 1: [-1, 0], 2: [1, 0], 3: [0, -1], 4: [0, 1] };
  const KEY_DIR = {
    ArrowUp: 1, KeyW: 1,
    ArrowDown: 2, KeyS: 2,
    ArrowLeft: 3, KeyA: 3,
    ArrowRight: 4, KeyD: 4,
  };
  const SPEEDS = [2000, 1000, 500, 250];
  const SIZES = [11, 15, 21, 25];
  const LAND_GROWTH = 25; // fixed classic rule, not user-selectable
  const STORAGE_KEY = 'generals-jax.settings.v2';

  // Map palette follows the generals.io tile stylesheet.
  const COLORS = {
    board: '#222222',
    fog: '#393939',
    mountain: '#acacac',
    neutral: '#dcdcdc',
    city: '#808080',
    you: '#2792ff',
    enemy: '#ff0000',
    text: '#ffffff',
  };

  const tileImages = {};
  function loadTileImages() {
    for (const name of ['mountain', 'city', 'crown']) {
      const image = new Image();
      image.onload = markBoardDirty;
      image.src = `/${name}.png`;
      tileImages[name] = image;
    }
  }

  function drawTileImage(ctx, name, x, y, cell) {
    const image = tileImages[name];
    if (!image || !image.complete || !image.naturalWidth) return;
    const size = cell * 0.78125;
    ctx.drawImage(image, x + (cell - size) / 2, y + (cell - size) / 2, size, size);
  }

  const $ = (id) => document.getElementById(id);
  const el = {
    canvas: $('board'),
    wrap: $('board-wrap'),
    turn: $('turn'),
    youLand: $('you-land'),
    youArmy: $('you-army'),
    enemyLand: $('enemy-land'),
    enemyArmy: $('enemy-army'),
    enemyName: $('enemy-name'),
    pause: $('pause'),
    restart: $('restart'),
    saveReplay: $('save-replay'),
    saveReplayOver: $('save-replay-over'),
    pauseBadge: $('pause-badge'),
    loading: $('loading'),
    gameover: $('gameover'),
    goTitle: $('go-title'),
    goKicker: $('go-kicker'),
    goSub: $('go-sub'),
    again: $('again'),
    queue: $('queue'),
    size: $('size'),
    opponent: $('opponent'),
    fog: $('fog'),
    speed: $('speed'),
    toast: $('toast'),
  };

  const S = {
    id: null,
    snap: null,
    settings: null,
    queue: [],
    selected: null,
    hover: null,
    split: false,
    paused: false,
    over: false,
    starting: false,
    ticking: false,
    tickTimer: null,
    cssSize: 0,
    ctx: null,
    boardDirty: true,
    toastTimer: null,
    startToken: 0,
  };

  /* ------------------------------------------------------------------ utils */
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

  function api(path, method = 'GET', body) {
    const init = { method, headers: {} };
    if (body !== undefined) {
      init.headers['Content-Type'] = 'application/json';
      init.body = JSON.stringify(body);
    }
    return fetch(path, init).then(async (res) => {
      let data = {};
      try {
        data = await res.json();
      } catch (_) { /* ignore */ }
      if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
      return data;
    });
  }

  function toast(message) {
    el.toast.textContent = message;
    el.toast.classList.remove('hidden');
    clearTimeout(S.toastTimer);
    S.toastTimer = setTimeout(() => el.toast.classList.add('hidden'), 2800);
  }

  function moveIntervalMs() {
    return Math.max(1, Math.round(S.settings.tick_ms / 2));
  }

  function armCount(value) {
    if (value >= 10000) return `${Math.round(value / 1000)}k`;
    if (value >= 1000) return `${(value / 1000).toFixed(1)}k`;
    return String(value);
  }

  /* --------------------------------------------------------------- settings */
  function loadSettings() {
    const defaults = { size: 21, fog: false, opponent: 'normal', tick_ms: 1000 };
    let saved = {};
    try {
      saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') || {};
    } catch (_) { saved = {}; }
    const out = { ...defaults, growth: LAND_GROWTH };
    if (SIZES.includes(Number(saved.size))) out.size = Number(saved.size);
    if (SPEEDS.includes(Number(saved.tick_ms))) out.tick_ms = Number(saved.tick_ms);
    if (['easy', 'normal', 'hard', 'checkpoint'].includes(saved.opponent)) out.opponent = saved.opponent;
    if (typeof saved.fog === 'boolean') out.fog = saved.fog;
    return out;
  }

  function saveSettings() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(S.settings));
    } catch (_) { /* private mode */ }
  }

  function syncControls() {
    el.size.value = String(S.settings.size);
    el.opponent.value = S.settings.opponent;
    el.fog.checked = S.settings.fog;
    el.size.disabled = S.settings.opponent === 'checkpoint';
    el.fog.disabled = S.settings.opponent === 'checkpoint';
    $('settings-hint').textContent = S.settings.opponent === 'checkpoint'
      ? 'Checkpoint games use the training board and fog settings.'
      : 'Changing the match starts a new game.';
    for (const button of el.speed.querySelectorAll('button')) {
      button.classList.toggle('active', Number(button.dataset.ms) === S.settings.tick_ms);
    }
    const names = { easy: 'Bot · easy', normal: 'Bot · normal', hard: 'Bot · hard', checkpoint: 'Trained checkpoint' };
    el.enemyName.textContent = names[S.settings.opponent] || 'Bot';
  }

  /* ------------------------------------------------------------------ clock */
  function restartClock(delay = moveIntervalMs()) {
    clearTimeout(S.tickTimer);
    S.tickTimer = null;
    if (S.paused || S.over || !S.id) {
      return;
    }
    S.tickTimer = setTimeout(tick, delay);
  }

  async function tick() {
    S.tickTimer = null;
    if (!S.id || S.over || S.paused) return;
    if (S.ticking) { restartClock(60); return; }

    S.ticking = true;
    const gameId = S.id;
    // Validate against the latest board, not the board when the path was
    // queued: earlier moves (or the opponent) may have changed it. Discard
    // no-ops without spending a half-turn, then send at most one playable move.
    let move = null;
    while (S.queue.length && !move) {
      const candidate = S.queue.shift();
      if (isPlayableMove(candidate, S.snap)) move = candidate;
    }
    updateQueueUI();
    try {
      const snap = await api(
        `/api/games/${gameId}/turn`,
        'POST',
        move ? { action: move.action } : {},
      );
      // Ignore a response that belongs to a game we already replaced.
      if (S.id === gameId) applySnapshot(snap);
    } catch (err) {
      if (S.id === gameId) toast(`Turn failed: ${err.message}`);
    } finally {
      S.ticking = false;
      if (!S.over && !S.paused) restartClock();
    }
  }

  function setPaused(value) {
    if (S.paused === value) return;
    S.paused = value;
    if (value) {
      clearTimeout(S.tickTimer);
      S.tickTimer = null;
    } else if (!S.over) {
      restartClock();
    }
    el.pause.textContent = value ? '▶' : '❚❚';
    el.pause.classList.toggle('active', value);
    el.pauseBadge.classList.toggle('hidden', !value || S.over || !S.id);
  }

  function togglePause() {
    if (!S.id || S.over) return;
    setPaused(!S.paused);
  }

  /* -------------------------------------------------------------- game flow */
  async function newGame() {
    if (S.starting) return;
    const token = ++S.startToken;
    S.starting = true;
    S.over = false;
    S.queue = [];
    S.split = false;
    S.hover = null;
    S.snap = null;
    S.selected = null;
    markBoardDirty();
    clearTimeout(S.tickTimer);
    S.tickTimer = null;
    if (S.id) {
      api(`/api/games/${S.id}`, 'DELETE').catch(() => {});
      S.id = null;
    }
    el.gameover.classList.add('hidden');
    el.pauseBadge.classList.add('hidden');
    el.loading.classList.remove('hidden');
    el.pause.textContent = '❚❚';
    el.pause.classList.remove('active');
    S.paused = false;
    syncControls();
    updateQueueUI();

    try {
      const snap = await api('/api/games', 'POST', {
        size: S.settings.size,
        fog: S.settings.fog,
        opponent: S.settings.opponent,
        growth: S.settings.growth,
      });
      if (token !== S.startToken) return;
      S.id = snap.id;
      if (snap.opponent === 'checkpoint') {
        S.settings.size = snap.h;
        S.settings.fog = snap.settings.fog;
        if (![...el.size.options].some(option => Number(option.value) === snap.h)) {
          el.size.add(new Option(`${snap.h} × ${snap.h}`, String(snap.h)));
        }
        syncControls();
      }
      applySnapshot(snap, true);
      // Small grace period on a fresh board so the first turn doesn't start
      // before the player has even found their general.
      restartClock(Math.max(2500, S.settings.tick_ms));
    } catch (err) {
      toast(`Could not start a game: ${err.message}`);
    } finally {
      S.starting = false;
      if (token === S.startToken) el.loading.classList.add('hidden');
    }
  }

  function applySnapshot(snap, initial = false) {
    S.snap = snap;
    S.hover = null;
    markBoardDirty();

    if (initial || S.selected == null) {
      focusGeneral();
    }
    S.split = initial ? false : S.split;

    updateHUD();
    if (snap.done) endGame(snap);
    else el.gameover.classList.add('hidden');
  }

  function focusGeneral() {
    const snap = S.snap;
    if (!snap || !snap.generals || !snap.generals.you) return;
    const [r, c] = snap.generals.you;
    S.selected = r * snap.w + c;
    markBoardDirty();
  }

  function endGame(snap) {
    S.over = true;
    S.queue = [];
    clearTimeout(S.tickTimer);
    S.tickTimer = null;
    el.pauseBadge.classList.add('hidden');
    el.pause.classList.remove('active');
    updateQueueUI();

    const you = snap.you;
    const bot = 1 - you;
    const draw = snap.winner === -1;
    const win = snap.winner === you;
    const reason = snap.reason || (snap.turn >= snap.max_turns ? 'turn limit' : 'general captured');
    el.goKicker.textContent = reason === 'turn limit'
      ? 'Turn limit reached' : reason === 'draw' ? 'Mutual capture' : 'General captured';
    el.goTitle.textContent = reason === 'turn limit'
      ? 'No winner' : draw ? 'Draw' : win ? 'Victory' : 'Defeat';
    el.goTitle.className = `go-title ${draw ? 'draw' : win ? 'win' : 'lose'}`;
    el.goSub.textContent =
      `Turn ${snap.turn} · land ${snap.score.land[you]}–${snap.score.land[bot]}` +
      ` · army ${snap.score.army[you]}–${snap.score.army[bot]}`;
    el.gameover.classList.remove('hidden');
  }

  function setTextIfChanged(node, value) {
    const text = String(value);
    if (node.textContent !== text) node.textContent = text;
  }

  function updateHUD() {
    const snap = S.snap;
    if (!snap) return;
    const you = snap.you;
    const bot = 1 - you;
    setTextIfChanged(el.turn, snap.turn);
    setTextIfChanged(el.youLand, snap.score.land[you]);
    setTextIfChanged(el.youArmy, snap.score.army[you]);
    setTextIfChanged(el.enemyLand, snap.score.land[bot]);
    setTextIfChanged(el.enemyArmy, snap.score.army[bot]);
  }

  function updateQueueUI() {
    markBoardDirty();
    const count = S.queue.length;
    if (!count) {
      el.queue.textContent = S.split ? 'Split armed — pick a direction' : 'Queue empty';
      el.queue.classList.remove('active');
      el.queue.classList.toggle('active', !!S.split);
      return;
    }
    el.queue.textContent = `${count} move${count === 1 ? '' : 's'} queued` +
      (S.split ? ' · split armed' : '');
    el.queue.classList.add('active');
  }

  /* ------------------------------------------------------------------ input */
  function isPlayableMove(move, snap) {
    if (!snap || move.src < 0 || move.src >= snap.h * snap.w || !DIRS[move.dir]) return false;
    if (snap.owner[move.src] !== snap.you || snap.army[move.src] <= 1) return false;

    const r = Math.floor(move.src / snap.w);
    const c = move.src % snap.w;
    const [dr, dc] = DIRS[move.dir];
    const rr = r + dr;
    const cc = c + dc;
    return rr >= 0 && rr < snap.h && cc >= 0 && cc < snap.w &&
      snap.owner[rr * snap.w + cc] !== MOUNTAIN;
  }

  function queueMove(dir) {
    const snap = S.snap;
    if (!snap || !S.id || S.over || S.starting) return;
    if (S.selected == null) { focusGeneral(); return; }

    const n = snap.w;
    const r = Math.floor(S.selected / n);
    const c = S.selected % n;
    const [dr, dc] = DIRS[dir];
    const rr = r + dr;
    const cc = c + dc;
    if (rr < 0 || rr >= snap.h || cc < 0 || cc >= n) return;

    const target = rr * n + cc;
    if (snap.owner[target] === MOUNTAIN) return; // known mountain: no move

    const half = S.split;
    S.queue.push({
      action: S.selected * snap.dir_actions + dir + (half ? 4 : 0),
      src: S.selected,
      dir,
      half,
    });
    S.selected = target;
    S.split = false;
    updateQueueUI();
  }

  function clearQueue() {
    if (!S.queue.length && !S.split) return;
    S.queue = [];
    S.split = false;
    updateQueueUI();
  }

  function deselect() {
    if (S.selected == null) return;
    S.selected = null;
    markBoardDirty();
  }

  function idxFromEvent(event) {
    const snap = S.snap;
    if (!snap) return null;
    const rect = el.canvas.getBoundingClientRect();
    if (!rect.width || !rect.height) return null;
    const x = (event.clientX - rect.left) / rect.width;
    const y = (event.clientY - rect.top) / rect.height;
    if (x < 0 || y < 0 || x >= 1 || y >= 1) return null;
    const c = clamp(Math.floor(x * snap.w), 0, snap.w - 1);
    const r = clamp(Math.floor(y * snap.h), 0, snap.h - 1);
    return r * snap.w + c;
  }

  function onPointerDown(event) {
    if (event.button !== undefined && event.button !== 0) return;
    const idx = idxFromEvent(event);
    if (idx == null || !S.snap || S.over) return;
    event.preventDefault();
    const snap = S.snap;

    if (S.selected != null && idx !== S.selected) {
      const r0 = Math.floor(S.selected / snap.w);
      const c0 = S.selected % snap.w;
      const r1 = Math.floor(idx / snap.w);
      const c1 = idx % snap.w;
      const dr = r1 - r0;
      const dc = c1 - c0;
      if (Math.abs(dr) + Math.abs(dc) === 1) {
        const dir = dr === -1 ? 1 : dr === 1 ? 2 : dc === -1 ? 3 : 4;
        queueMove(dir);
        return;
      }
      S.selected = idx;
      updateQueueUI();
      return;
    }

    S.selected = S.selected === idx ? null : idx;
    updateQueueUI();
  }

  function onPointerMove(event) {
    const hover = idxFromEvent(event);
    if (S.hover !== hover) {
      S.hover = hover;
      markBoardDirty();
    }
  }

  function attachInput() {
    el.canvas.addEventListener('pointerdown', onPointerDown);
    el.canvas.addEventListener('pointermove', onPointerMove);
    el.canvas.addEventListener('pointerleave', () => {
      if (S.hover != null) {
        S.hover = null;
        markBoardDirty();
      }
    });
    el.canvas.addEventListener('contextmenu', (event) => {
      event.preventDefault();
      clearQueue();
      deselect();
    });

    window.addEventListener('keydown', (event) => {
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      const tag = (event.target && event.target.tagName || '').toLowerCase();
      if (tag === 'input' || tag === 'select' || tag === 'textarea') return;

      const dir = KEY_DIR[event.code];
      if (dir) {
        event.preventDefault();
        if (!event.repeat) queueMove(dir);
        return;
      }

      switch (event.code) {
        case 'Space':
          event.preventDefault();
          if (!event.repeat) deselect();
          break;
        case 'KeyQ':
          if (!event.repeat) clearQueue();
          break;
        case 'KeyZ':
          if (!event.repeat) {
            S.split = !S.split;
            updateQueueUI();
          }
          break;
        case 'KeyP':
          if (!event.repeat) togglePause();
          break;
        case 'KeyN':
          if (!event.repeat) newGame();
          break;
        case 'Escape':
          clearQueue();
          deselect();
          break;
        default:
          break;
      }
    });

    document.addEventListener('visibilitychange', () => {
      if (document.hidden && S.id && !S.over && !S.paused) setPaused(true);
    });
  }

  function attachControls() {
    const matchChanged = () => {
      S.settings.size = Number(el.size.value);
      S.settings.opponent = el.opponent.value;
      S.settings.fog = el.fog.checked;
      saveSettings();
      syncControls();
      newGame();
    };
    el.size.addEventListener('change', matchChanged);
    el.opponent.addEventListener('change', matchChanged);
    el.fog.addEventListener('change', matchChanged);

    for (const button of el.speed.querySelectorAll('button')) {
      button.addEventListener('click', () => {
        S.settings.tick_ms = Number(button.dataset.ms);
        saveSettings();
        syncControls();
        if (!S.over && !S.paused) restartClock();
      });
    }

    const saveReplay = () => {
      if (!S.id) return;
      window.open(`/api/games/${S.id}/replay.html`, '_blank');
      toast('Replay download started');
    };
    el.saveReplay.addEventListener('click', saveReplay);
    el.saveReplayOver.addEventListener('click', saveReplay);

    el.pause.addEventListener('click', togglePause);
    el.restart.addEventListener('click', newGame);
    el.again.addEventListener('click', newGame);
  }

  /* --------------------------------------------------------------- painting */
  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    if (typeof ctx.roundRect === 'function') {
      ctx.roundRect(x, y, w, h, r);
      return;
    }
    const rr = Math.min(r, w / 2, h / 2);
    ctx.moveTo(x + rr, y);
    ctx.arcTo(x + w, y, x + w, y + h, rr);
    ctx.arcTo(x + w, y + h, x, y + h, rr);
    ctx.arcTo(x, y + h, x, y, rr);
    ctx.arcTo(x, y, x + w, y, rr);
    ctx.closePath();
  }

  function drawArrow(ctx, cx, cy, cell, dir, alpha) {
    const angle = { 1: -Math.PI / 2, 2: Math.PI / 2, 3: Math.PI, 4: 0 }[dir];
    const d = cell * 0.3;
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.translate(cx, cy);
    ctx.rotate(angle);
    ctx.beginPath();
    ctx.moveTo(d * 0.62, 0);
    ctx.lineTo(-d * 0.12, -d * 0.62);
    ctx.lineTo(-d * 0.12, -d * 0.24);
    ctx.lineTo(-d * 0.7, -d * 0.24);
    ctx.lineTo(-d * 0.7, d * 0.24);
    ctx.lineTo(-d * 0.12, d * 0.24);
    ctx.lineTo(-d * 0.12, d * 0.62);
    ctx.closePath();
    ctx.fillStyle = '#ffffff';
    ctx.fill();
    ctx.restore();
  }

  function markBoardDirty() {
    S.boardDirty = true;
  }

  function drawBoard() {
    const ctx = S.ctx;
    const size = S.cssSize;
    if (!ctx || !size || !S.boardDirty) return;

    const snap = S.snap;
    ctx.clearRect(0, 0, size, size);
    ctx.fillStyle = COLORS.board;
    ctx.fillRect(0, 0, size, size);
    if (!snap) {
      S.boardDirty = false;
      return;
    }

    const n = snap.w;
    const cell = size / n;
    const gap = 0.5;
    const radius = 0;
    const me = snap.you;
    const fontFamily = 'Arial, sans-serif';

    for (let r = 0; r < snap.h; r += 1) {
      for (let c = 0; c < n; c += 1) {
        const i = r * n + c;
        const owner = snap.owner[i];
        const army = snap.army[i];
        const x = c * cell;
        const y = r * cell;
        const isCity = !!snap.city[i];
        const gen = generalAt(snap, r, c);

        let fill = COLORS.fog;
        if (owner === MOUNTAIN) fill = COLORS.mountain;
        else if (owner === NEUTRAL) fill = isCity ? COLORS.city : COLORS.neutral;
        else if (owner === me) fill = COLORS.you;
        else if (owner !== UNKNOWN && owner !== OBSTACLE) fill = COLORS.enemy;

        // Contiguous square tiles with a thin black grid, like the reference.
        ctx.fillStyle = fill;
        ctx.fillRect(x, y, cell, cell);
        if (owner !== UNKNOWN && owner !== OBSTACLE) {
          ctx.strokeStyle = '#000';
          ctx.lineWidth = 1;
          ctx.strokeRect(x + gap, y + gap, cell - 1, cell - 1);
        }

        if (owner === UNKNOWN) continue;
        if (owner === MOUNTAIN || owner === OBSTACLE) {
          drawTileImage(ctx, 'mountain', x, y, cell);
          continue;
        }
        if (gen != null) drawTileImage(ctx, 'crown', x, y, cell);
        else if (isCity) drawTileImage(ctx, 'city', x, y, cell);

        if (army > 0) {
          const label = armCount(army);
          const fs = Math.max(7, cell * (label.length >= 3 ? 0.31 : 0.375));
          ctx.font = `bold ${fs}px ${fontFamily}`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          const cx = x + cell / 2;
          const cy = y + cell / 2;
          ctx.lineWidth = Math.max(2, cell * 0.07);
          ctx.strokeStyle = '#000';
          ctx.lineJoin = 'round';
          ctx.strokeText(label, cx, cy);
          ctx.fillStyle = COLORS.text;
          ctx.fillText(label, cx, cy);
        }
      }
    }

    /* hover */
    if (S.hover != null && S.hover !== S.selected) {
      const hr = Math.floor(S.hover / n);
      const hc = S.hover % n;
      roundRect(ctx, hc * cell + gap, hr * cell + gap, cell - 2 * gap, cell - 2 * gap, radius);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.08)';
      ctx.fill();
    }

    /* selection */
    if (S.selected != null && S.selected >= 0 && S.selected < snap.owner.length) {
      const sr = Math.floor(S.selected / n);
      const sc = S.selected % n;
      roundRect(ctx, sc * cell + gap, sr * cell + gap, cell - 2 * gap, cell - 2 * gap, radius);
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = Math.max(1, cell * 0.04);
      ctx.stroke();
    }

    /* queued path */
    S.queue.forEach((move, index) => {
      const qr = Math.floor(move.src / n);
      const qc = move.src % n;
      drawArrow(
        ctx,
        qc * cell + cell / 2,
        qr * cell + cell / 2,
        cell,
        move.dir,
        index === 0 ? 0.75 : 0.32,
      );
    });

    // Keep the completed frame until the board actually changes. Redrawing and
    // flashing every changed tile made armies, cities, and generals pulse on
    // every server snapshot.
    S.boardDirty = false;
  }

  function generalAt(snap, r, c) {
    const mine = snap.generals.you;
    if (mine && mine[0] === r && mine[1] === c) return 0;
    const theirs = snap.generals.enemy;
    if (theirs && theirs[0] === r && theirs[1] === c) return 1;
    return null;
  }

  function loop() {
    drawBoard();
    requestAnimationFrame(loop);
  }

  /* ----------------------------------------------------------------- sizing */
  function resize() {
    const rect = el.wrap.getBoundingClientRect();
    const available = Math.min(rect.width, rect.height || rect.width);
    const size = Math.max(180, Math.floor(available));
    if (size === S.cssSize && S.ctx) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2.5);
    S.cssSize = size;
    el.canvas.style.width = `${size}px`;
    el.canvas.style.height = `${size}px`;
    el.canvas.width = Math.round(size * dpr);
    el.canvas.height = Math.round(size * dpr);
    S.ctx = el.canvas.getContext('2d');
    S.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    markBoardDirty();
  }

  /* ------------------------------------------------------------------- boot */
  function init() {
    loadTileImages();
    S.settings = loadSettings();
    syncControls();
    attachControls();
    attachInput();
    resize();
    new ResizeObserver(resize).observe(el.wrap);
    window.addEventListener('orientationchange', () => setTimeout(resize, 120));
    requestAnimationFrame(loop);
    newGame();
  }

  init();
})();
