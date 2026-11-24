"""A tiny stdlib HTTP server that plays ``generals_jax`` in the browser.

No web framework, no extra dependencies -- just ``http.server``, JSON and a few
static files.  Start it with::

    python -m generals_web --port 8000

and open http://localhost:8000.

API
---
``GET  /api/health``                 -> ``{"ok": true, ...}``
``POST /api/games``                  -> create a game, returns a snapshot
``GET  /api/games/<id>``             -> current snapshot
``POST /api/games/<id>/turn``        -> advance one half-turn, returns a snapshot
``DELETE /api/games/<id>``           -> forget a game
``GET  /api/games/<id>/replay``       -> every half-turn so far, as replay JSON
``GET  /api/games/<id>/replay.html``  -> single-file HTML replay player

A snapshot is the board as *player 0* is allowed to see it: tiles hidden by fog
come through with ``owner = -3`` (or ``-4`` for an unseen mountain/castle
obstacle), ``city = 0``, and no armies, so the client cannot cheat by looking at
the JSON.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
import re
import threading
import time
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import jax
import jax.numpy as jnp

from bot.baselines import greedy_action
from game import GeneralsEnv

from .game import Game, GameSettings

STATIC_DIR = Path(__file__).resolve().parent / "static"
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".json": "application/json",
}

MAX_BODY = 1 << 20  # 1 MiB is plenty for a move
MAX_GAMES = 64
GAME_TTL = 6 * 3600.0  # seconds

GAME_PATH = re.compile(r"^/api/games/([A-Za-z0-9]+)$")
TURN_PATH = re.compile(r"^/api/games/([A-Za-z0-9]+)/turn$")
REPLAY_PATH = re.compile(r"^/api/games/([A-Za-z0-9]+)/replay$")
REPLAY_HTML_PATH = re.compile(r"^/api/games/([A-Za-z0-9]+)/replay\.html$")


class Store:
    """Live games plus a cache of compiled environments (one per config)."""

    def __init__(self, policy=None) -> None:
        self.policy = policy
        self.games: Dict[str, Game] = {}
        self.created: Dict[str, float] = {}
        self.envs: Dict[Any, GeneralsEnv] = {}
        self.lock = threading.RLock()
        self.warm_lock = threading.Lock()
        self.warmed: set = set()

    # -------------------------------------------------------------- env cache
    def env_for(self, settings: GameSettings) -> GeneralsEnv:
        cfg = self.policy.env_config if settings.opponent == "checkpoint" else settings.config()
        with self.lock:
            env = self.envs.get(cfg)
            if env is not None:
                return env
        # Build outside the lock; compilation happens in ensure_ready().
        env = GeneralsEnv(cfg)
        with self.lock:
            self.envs.setdefault(cfg, env)
            return self.envs[cfg]

    def ensure_ready(self, settings: GameSettings) -> GeneralsEnv:
        """Environment for ``settings``, compiled for this opponent once."""
        env = self.env_for(settings)
        key = (env.config, settings.opponent)
        if key in self.warmed:
            return env
        with self.warm_lock:
            if key not in self.warmed:
                warm_env(env, settings.opponent)
                self.warmed.add(key)
        return env

    # ------------------------------------------------------------------ games
    def new_game(self, settings: GameSettings) -> Game:
        if settings.opponent == "checkpoint":
            if self.policy is None:
                raise ValueError("no checkpoint configured; start the server with --run-dir")
            cfg = self.policy.cfg
            settings = replace(settings, size=cfg.height, fog=cfg.fog, max_turns=cfg.max_turns)
        env = self.ensure_ready(settings)
        game_id = uuid.uuid4().hex[:12]
        game = Game(game_id, settings, env, policy=self.policy if settings.opponent == "checkpoint" else None)
        if game.policy is not None:
            # Compile inference before the turn clock starts; do not advance memory.
            game.policy.action(env, game.state, game.bot_memory)
        with self.lock:
            self._gc_locked()
            self.games[game_id] = game
            self.created[game_id] = time.time()
        return game

    def get(self, game_id: str) -> Optional[Game]:
        with self.lock:
            return self.games.get(game_id)

    def drop(self, game_id: str) -> bool:
        with self.lock:
            self.created.pop(game_id, None)
            return self.games.pop(game_id, None) is not None

    def _gc_locked(self) -> None:
        now = time.time()
        for game_id, born in list(self.created.items()):
            if now - born > GAME_TTL:
                self.games.pop(game_id, None)
                self.created.pop(game_id, None)
        while len(self.games) > MAX_GAMES:
            oldest = min(self.created, key=self.created.get)
            self.games.pop(oldest, None)
            self.created.pop(oldest, None)


def warm_env(env: GeneralsEnv, opponent: str) -> None:
    """Pay the jit-compilation cost up front so the first turn is instant."""
    state = env.reset(jax.random.PRNGKey(0))
    state, _rewards, _info = env.step(state, jnp.zeros((2,), dtype=jnp.int32))
    if opponent == "hard":
        greedy_action(state, 1, env.config, env.tables)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "generals-web/0.1"
    sys_version = ""

    # ------------------------------------------------------------- plumbing
    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        if getattr(self.server, "verbose", False):
            super().log_message(fmt, *args)

    @property
    def store(self) -> Store:
        return self.server.store  # type: ignore[attr-defined]

    def _send(
        self,
        body: bytes,
        status: int = 200,
        content_type: str = "application/json; charset=utf-8",
        cache: str = "no-store",
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache)
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, payload: Dict[str, Any], status: int = 200) -> None:
        self._send(json.dumps(payload, separators=(",", ":")).encode(), status)

    def _error(self, status: int, message: str) -> None:
        self._json({"error": message, "status": int(status)}, status)

    def _body(self) -> Dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        if length > MAX_BODY:
            raise ValueError("request body too large")
        raw = self.rfile.read(length)
        if not raw.strip():
            return {}
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    # ----------------------------------------------------------------- routes
    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path == "/api/health":
                self._json(
                    {
                        "ok": True,
                        "games": len(self.store.games),
                        "configs": len(self.store.envs),
                        "checkpoint": self.store.policy.tag if self.store.policy else None,
                    }
                )
                return
            match = GAME_PATH.match(path)
            if match:
                game = self.store.get(match.group(1))
                if game is None:
                    self._error(HTTPStatus.NOT_FOUND, "unknown game")
                else:
                    self._json(game.snapshot())
                return
            match = REPLAY_HTML_PATH.match(path)
            if match:
                game = self.store.get(match.group(1))
                if game is None:
                    self._error(HTTPStatus.NOT_FOUND, "unknown game")
                    return
                body = game.replay_html().encode("utf-8")
                self._send(
                    body,
                    content_type="text/html; charset=utf-8",
                    extra_headers={
                        "Content-Disposition": f'attachment; filename="replay-{game.id}.html"'
                    },
                )
                return
            match = REPLAY_PATH.match(path)
            if match:
                game = self.store.get(match.group(1))
                if game is None:
                    self._error(HTTPStatus.NOT_FOUND, "unknown game")
                    return
                body = json.dumps(game.replay_document(), separators=(",", ":")).encode()
                self._send(
                    body,
                    extra_headers={
                        "Content-Disposition": f'attachment; filename="replay-{game.id}.json"'
                    },
                )
                return
            if path.startswith("/api/"):
                self._error(HTTPStatus.NOT_FOUND, "unknown endpoint")
                return
            self._serve_static(path)
        except Exception as exc:  # pragma: no cover - defensive
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def do_HEAD(self) -> None:  # noqa: N802
        self.do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path == "/api/games":
                settings = GameSettings.from_payload(self._body())
                game = self.store.new_game(settings)
                self._json(game.snapshot())
                return
            match = TURN_PATH.match(path)
            if match:
                game = self.store.get(match.group(1))
                if game is None:
                    self._error(HTTPStatus.NOT_FOUND, "unknown game")
                    return
                body = self._body()
                action = body.get("action")
                if action is not None:
                    try:
                        action = int(action)
                    except (TypeError, ValueError):
                        self._error(HTTPStatus.BAD_REQUEST, "action must be an integer")
                        return
                game.step(action)
                self._json(game.snapshot())
                return
            self._error(HTTPStatus.NOT_FOUND, "unknown endpoint")
        except ValueError as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))
        except Exception as exc:  # pragma: no cover - defensive
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def do_DELETE(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        match = GAME_PATH.match(path)
        if not match:
            self._error(HTTPStatus.NOT_FOUND, "unknown endpoint")
            return
        removed = self.store.drop(match.group(1))
        self._json({"deleted": removed})

    # ----------------------------------------------------------------- static
    def _serve_static(self, path: str) -> None:
        rel = "index.html" if path in ("", "/") else path.lstrip("/")
        candidate = (STATIC_DIR / rel).resolve()
        if (
            not str(candidate).startswith(str(STATIC_DIR.resolve()) + "/")
            or not candidate.is_file()
        ):
            self._error(HTTPStatus.NOT_FOUND, "not found")
            return
        body = candidate.read_bytes()
        self._send(
            body,
            content_type=CONTENT_TYPES.get(candidate.suffix, "application/octet-stream"),
            cache="no-cache",
        )


class GeneralsHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, store: Store, verbose: bool = False):
        super().__init__(address, Handler)
        self.store = store
        self.verbose = verbose


def create_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    verbose: bool = False,
    warm: bool = True,
    policy=None,
) -> GeneralsHTTPServer:
    """Bind (but do not start) the web server."""
    server = GeneralsHTTPServer((host, port), Store(policy), verbose=verbose)
    if warm:
        threading.Thread(target=_warm_defaults, args=(server.store,), daemon=True).start()
    return server


def _warm_defaults(store: Store) -> None:
    """Pre-compile the boards the UI opens with, in the background."""
    for settings in (
        GameSettings(fog=False),
        GameSettings(size=15, fog=False),
        GameSettings(size=11, fog=False),
        GameSettings(opponent="hard", fog=False),
    ):
        try:
            store.ensure_ready(settings)
        except Exception:  # pragma: no cover - warming is best effort
            pass


def main(argv: Optional[list] = None) -> None:
    parser = argparse.ArgumentParser(
        prog="generals-web",
        description="Play generals_jax in the browser (WASD / arrow keys).",
    )
    parser.add_argument("--host", default="0.0.0.0", help="bind address (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="port (default 8000)")
    parser.add_argument("--verbose", action="store_true", help="log every request")
    parser.add_argument("--no-warm", action="store_true", help="skip the background warm-up")
    parser.add_argument("--run-dir", help="training run directory containing checkpoints/ (enables checkpoint opponent)")
    parser.add_argument("--checkpoint", default="latest", help="checkpoint tag (default: latest)")
    args = parser.parse_args(argv)
    policy = None
    if args.run_dir:
        from .checkpoint import CheckpointPolicy
        try:
            policy = CheckpointPolicy(args.run_dir, args.checkpoint)
        except ValueError as exc:
            parser.error(str(exc))

    server = create_server(
        host=args.host, port=args.port, verbose=args.verbose, warm=not args.no_warm, policy=policy
    )
    shown_host = "localhost" if args.host in ("0.0.0.0", "::") else args.host
    print(f"generals_jax web server  ->  http://{shown_host}:{args.port}", flush=True)
    if policy:
        print(f"Checkpoint opponent: {policy.tag} ({policy.cfg.height}x{policy.cfg.width})", flush=True)
    print("WASD / arrows to move, Z to split, Space to deselect, Q to clear.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
