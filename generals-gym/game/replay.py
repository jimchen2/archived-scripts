"""Record games into a small, portable replay file.

A replay is a plain JSON document (``generals-gym-replay``) that holds the
*complete* state after every half-turn, so it can be rendered long after the game ran:
into a video, into the browser, or back into an ASCII board::

    from game.replay import ReplayRecorder

    rec = ReplayRecorder(env.config, players=[("agent", "agent"), ("greedy", "bot")])
    rec.add(state)                       # turn 0
    for _ in range(200):  # 200 half-turns = 100 displayed turns
        state, rewards, info = env.step(state, actions)
        rec.add(state, actions=actions, rewards=rewards)
        if bool(info["done"]):
            break
    rec.save("replays/game.json")

Every frame stores the tile ``owner`` grid, the ``army`` grid, the castle mask
and the two general positions, run-length encoded. A 21x21 game of 500 displayed
turns can contain up to 1,000 half-turn frames; file size depends on how much the
board changes, and playback needs no extra dependency.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from .config import MOUNTAIN, NEUTRAL, NUM_PLAYERS, EnvConfig

FORMAT = "generals-gym-replay"
VERSION = 2

#: ``owner`` values that are real players (0 and 1).  ``owner`` uses -2 for a
#: mountain and -1 for neutral ground, exactly like :mod:`game.state`.
PLAYER_IDS = tuple(range(NUM_PLAYERS))


# --------------------------------------------------------------------- helpers
def encode_rle(values: Iterable[int]) -> list[list[int]]:
    """Run-length encode a flat sequence as ``[[value, count], ...]``."""
    out: list[list[int]] = []
    for value in values:
        value = int(value)
        if out and out[-1][0] == value:
            out[-1][1] += 1
        else:
            out.append([value, 1])
    return out


def decode_rle(pairs: Sequence[Sequence[int]], size: int) -> np.ndarray:
    """Inverse of :func:`encode_rle`; returns an ``(size,)`` int32 array."""
    out = np.empty(size, dtype=np.int32)
    at = 0
    for value, count in pairs:
        count = int(count)
        if count <= 0 or at + count > size:
            raise ValueError("invalid run-length count")
        out[at : at + count] = int(value)
        at += count
    if at != size:
        raise ValueError(f"run-length data covers {at} cells, expected {size}")
    return out


def _as_grid(values: Any, h: int, w: int, dtype=np.int32) -> np.ndarray:
    array = np.asarray(values, dtype=dtype)
    if array.size != h * w:
        raise ValueError(f"expected {h * w} cells, got {array.size}")
    return array.reshape(h, w)


def _general_cells(state) -> list[list[int] | None]:
    """``[[row, col] | None, ...]`` for both seats (``None`` when dead)."""
    h, w = int(state.owner.shape[-2]), int(state.owner.shape[-1])
    out: list[list[int] | None] = []
    for seat in range(NUM_PLAYERS):
        if not bool(state.alive[seat]):
            out.append(None)
            continue
        flat = int(state.general[seat])
        if flat < 0:
            out.append(None)
            continue
        out.append([flat // w, flat % w])
    return out


# ------------------------------------------------------------------------ data
class ReplayRecorder:
    """Collect the frames of one game and serialise them.

    Parameters
    ----------
    config:
        The :class:`~game.EnvConfig` the game ran with (board shape and rules
        are stored so the replay is self-describing).
    players:
        One ``(name, kind)`` pair per seat, e.g.
        ``[("checkpoint step_000200", "agent"), ("greedy", "bot")]``.
    seed, meta:
        Optional provenance stored in the header (training run, update, ...).
    """

    def __init__(
        self,
        config: EnvConfig,
        players: Sequence[tuple[str, str]] | None = None,
        seed: int | None = None,
        meta: dict | None = None,
    ) -> None:
        self._dst: np.ndarray | None = None
        if players is None:
            players = [(f"player {seat}", "human") for seat in range(NUM_PLAYERS)]
        if len(players) != NUM_PLAYERS:
            raise ValueError(f"need {NUM_PLAYERS} players, got {len(players)}")
        self.config = config
        self.players = [
            {"seat": seat, "name": str(name), "kind": str(kind)}
            for seat, (name, kind) in enumerate(players)
        ]
        self.seed = None if seed is None else int(seed)
        self.meta = dict(meta or {})
        self.frames: list[dict] = []

    # ------------------------------------------------------------------ record
    @property
    def h(self) -> int:
        return self.config.height

    @property
    def w(self) -> int:
        return self.config.width

    def _move(self, player: int, action: int) -> dict | None:
        """Describe one action as ``{"p", "from", "to", "half"}``.

        ``None`` for a pass or an action the engine would ignore (a move off the
        board or onto a mountain), so the video only draws real moves.
        """
        cfg = self.config
        src = action // cfg.dir_actions
        code = action % cfg.dir_actions
        if code == 0 or src < 0 or src >= cfg.num_tiles:
            return None
        if self._dst is None:
            h, w = cfg.height, cfg.width
            rows, cols = np.divmod(np.arange(cfg.num_tiles), w)
            dst = np.full((cfg.dir_actions, cfg.num_tiles), -1, dtype=np.int32)
            offsets = {1: (-1, 0), 2: (1, 0), 3: (0, -1), 4: (0, 1)}
            for base, (dr, dc) in offsets.items():
                r = rows + dr
                c = cols + dc
                ok = (r >= 0) & (r < h) & (c >= 0) & (c < w)
                dst[base] = np.where(ok, r * w + c, -1)
            if cfg.half_moves:
                for base in offsets:
                    dst[base + 4] = dst[base]
            self._dst = dst
        to = int(self._dst[code, src])
        if to < 0:
            return None
        return {"p": int(player), "from": int(src), "to": to, "half": bool(code > 4)}

    def add(
        self,
        state,
        actions: Any | None = None,
        rewards: Any | None = None,
    ) -> dict:
        """Append one frame (usually right after ``env.step`` or ``env.reset``)."""
        if len(self.frames) >= 1_000_000:  # pragma: no cover - sanity guard
            raise RuntimeError("replay is absurdly long")
        owner = np.asarray(state.owner, dtype=np.int32).reshape(-1)
        army = np.asarray(state.army, dtype=np.int32).reshape(-1)
        city = np.asarray(state.city, dtype=bool).reshape(-1).astype(np.int32)

        frame = {
            # Display turn number plus the phase (two action frames share a
            # displayed turn).
            "t": int(state.turn + state.half_turn),
            "half_turn": int(state.half_turn),
            "o": encode_rle(owner),
            "a": encode_rle(army),
            "c": encode_rle(city),
            "g": _general_cells(state),
            "alive": [int(bool(state.alive[p])) for p in range(NUM_PLAYERS)],
            "winner": int(state.winner),
            "done": bool(state.done),
        }
        if actions is not None:
            acted = [int(a) for a in np.asarray(actions).reshape(-1)]
            moves = [self._move(p, a) for p, a in enumerate(acted)][:NUM_PLAYERS]
            if self.frames:
                previous = self.frames[-1]
                prev_owner = decode_rle(previous["o"], self.config.num_tiles)
                prev_army = decode_rle(previous["a"], self.config.num_tiles)
                for p, move in enumerate(moves):
                    if move and (prev_owner[move["from"]] != p or
                                 prev_army[move["from"]] <= 1 or
                                 prev_owner[move["to"]] == MOUNTAIN):
                        moves[p] = None
            frame["moves"] = moves
            frame["acts"] = acted
        if rewards is not None:
            frame["r"] = [float(r) for r in np.asarray(rewards, dtype=np.float32).reshape(-1)]
        self.frames.append(frame)
        return frame

    # ---------------------------------------------------------------- serialise
    def result(self) -> dict:
        """Winner / length summary, taken from the last recorded frame."""
        if not self.frames:
            return {"winner": -1, "turns": 0, "reason": "empty"}
        last = self.frames[-1]
        winner = int(last["winner"])
        if not last["done"]:
            reason = "unfinished"
        elif not all(last["alive"]):
            reason = "general captured" if winner >= 0 else "draw"
        elif last["t"] >= self.config.max_turns:
            reason = "turn limit"
        else:
            reason = "draw"
        return {"winner": winner, "turns": int(last["t"]), "reason": reason}

    def to_dict(self) -> dict:
        cfg = self.config
        payload = {
            "format": FORMAT,
            "version": VERSION,
            "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "game": {
                "h": cfg.height,
                "w": cfg.width,
                "fog": bool(cfg.fog),
                "half_moves": bool(cfg.half_moves),
                "dir_actions": int(cfg.dir_actions),
                "moves_per_turn": 2,
                "max_turns": int(cfg.max_turns),
                "land_growth_period": int(cfg.land_growth_period),
                "city_count": int(cfg.city_count),
                "mountain": MOUNTAIN,
                "neutral": NEUTRAL,
            },
            "players": self.players,
            "seed": self.seed,
            "meta": self.meta,
            "result": self.result(),
            "frames": self.frames,
        }
        return payload

    def save(self, path: str | Path, indent: int | None = None) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.to_dict()
        path.write_text(json.dumps(payload, separators=None if indent else (",", ":"),
                                   indent=indent))
        return path


class Replay:
    """A loaded replay: decoded frames plus a little metadata sugar."""

    def __init__(self, payload: dict) -> None:
        if payload.get("format") != FORMAT:
            raise ValueError("not a generals-gym replay")
        if int(payload.get("version", 0)) > VERSION:
            raise ValueError(
                f"replay version {payload['version']} is newer than {VERSION}"
            )
        self.payload = payload
        game = payload["game"]
        self.h = int(game["h"])
        self.w = int(game["w"])
        self.size = self.h * self.w
        self.fog = bool(game.get("fog", False))
        self.half_moves = bool(game.get("half_moves", False))
        self.dir_actions = int(game.get("dir_actions", 9 if self.half_moves else 5))
        self.moves_per_turn = int(game.get("moves_per_turn", 1))
        self.max_turns = int(game.get("max_turns", 0))
        self.players = list(payload.get("players") or [])
        self.meta = dict(payload.get("meta") or {})
        self.result = dict(payload.get("result") or {})
        self.frames: list[dict] = list(payload.get("frames") or [])

    # ---------------------------------------------------------------- loading
    @classmethod
    def from_dict(cls, payload: dict) -> "Replay":
        return cls(payload)

    def to_dict(self) -> dict:
        """The raw replay document (JSON-ready)."""
        return self.payload

    def save(self, path: str | Path, indent: int | None = None) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.payload, separators=None if indent else (",", ":"),
                       indent=indent)
        )
        return path

    @classmethod
    def load(cls, path: str | Path) -> "Replay":
        return cls(json.loads(Path(path).read_text()))

    # ----------------------------------------------------------------- frames
    def __len__(self) -> int:
        return len(self.frames)

    def names(self) -> list[str]:
        return [p.get("name", f"player {i}") for i, p in enumerate(self.players)]

    def player(self, seat: int) -> dict:
        """The ``{"seat", "name", "kind"}`` record stored for a seat."""
        if 0 <= seat < len(self.players):
            return dict(self.players[seat])
        return {"seat": seat, "name": f"player {seat}", "kind": "bot"}

    def player_name(self, seat: int) -> str:
        names = self.names()
        return names[seat] if 0 <= seat < len(names) else f"player {seat}"

    def grid(self, index: int, key: str = "o") -> np.ndarray:
        """Decoded ``(H, W)`` array for frame ``index``: ``o``, ``a`` or ``c``."""
        frame = self.frames[index]
        return decode_rle(frame[key], self.size).reshape(self.h, self.w)

    def frame_owner(self, index: int) -> np.ndarray:
        return self.grid(index, "o")

    def frame_army(self, index: int) -> np.ndarray:
        return self.grid(index, "a")

    def frame_city(self, index: int) -> np.ndarray:
        return self.grid(index, "c")

    def generals(self, index: int) -> list[list[int] | None]:
        """``[[row, col] | None, None]`` for the two seats at ``index``."""
        return [list(g) if g else None for g in self.frames[index].get("g") or []]

    def scores(self, index: int) -> dict:
        """Land / army / castle totals per seat (computed from the frame)."""
        owner = self.frame_owner(index)
        army = self.frame_army(index)
        city = self.frame_city(index)
        return {
            "land": [int((owner == p).sum()) for p in PLAYER_IDS],
            "army": [int(np.where(owner == p, army, 0).sum()) for p in PLAYER_IDS],
            "cities": [int(((city != 0) & (owner == p)).sum()) for p in PLAYER_IDS],
        }

    # ------------------------------------------------------------- rendering
    def visible(self, index: int, seat: int = 0) -> np.ndarray:
        """``(H, W)`` bool mask of the tiles ``seat`` can see at ``index``."""
        if not self.fog:
            return np.ones((self.h, self.w), dtype=bool)
        own = self.frame_owner(index) == seat
        padded = np.pad(own, 1, mode="constant", constant_values=False)
        vis = np.zeros_like(own)
        for dr in range(3):
            for dc in range(3):
                vis |= padded[dr : dr + self.h, dc : dc + self.w]
        return vis


def load(path: str | Path) -> Replay:
    """Shorthand for :meth:`Replay.load`."""
    return Replay.load(path)
