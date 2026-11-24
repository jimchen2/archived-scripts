"""Game sessions and JSON snapshots for the browser client.

One :class:`Game` is one live 1v1 match against a bot.  The class is a thin
stateful wrapper around the pure JAX engine: it keeps the current ``State``,
asks :mod:`generals_web.bots` for the opponent's move and hides everything the
human player is not allowed to see before serialising the board.
"""

from __future__ import annotations

import threading
import copy
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

import jax
import jax.numpy as jnp
import numpy as np

from game import EnvConfig, GeneralsEnv, MOUNTAIN
from game.obs import visible_mask
from game.replay import Replay, ReplayRecorder

from .bots import DIFFICULTIES, choose_action

OPPONENTS = DIFFICULTIES + ("checkpoint",)

#: ``owner`` value used on the wire for a tile hidden by the fog of war.
UNKNOWN = -3
#: ``owner`` value used on the wire for a fogged mountain or castle obstacle.
OBSTACLE = -4

MAX_PLAYERS = 2
YOU = 0
OPPONENT = 1


def _clamp_int(value: Any, default: int, low: int, high: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, number))


LAND_GROWTH = 25  # +1 army on owned land every 25 displayed turns


@dataclass(frozen=True)
class GameSettings:
    """Everything that changes the board / rules of a match.

    ``size`` is the side of the square board, ``opponent`` one of ``easy``/``normal``/
    ``hard`` and ``fog`` toggles fog of war. Land growth is fixed at
    ``LAND_GROWTH`` displayed turns (every owned tile gains +1 army then;
    castles and generals also gain +1 after every full displayed turn).
    """

    size: int = 21
    fog: bool = True
    opponent: str = "normal"
    growth: int = LAND_GROWTH
    max_turns: int = 1000

    def __post_init__(self) -> None:
        if self.opponent not in OPPONENTS:
            raise ValueError(f"opponent must be one of {OPPONENTS}")
        if self.growth != LAND_GROWTH:
            raise ValueError(
                f"land growth is fixed at {LAND_GROWTH} displayed turns"
            )

    @classmethod
    def from_payload(cls, payload: Optional[Dict[str, Any]]) -> "GameSettings":
        payload = payload or {}
        opponent = str(payload.get("opponent", "normal")).lower()
        if opponent not in OPPONENTS:
            opponent = "normal"
        return cls(
            size=_clamp_int(payload.get("size"), 21, 5, 31),
            fog=bool(payload.get("fog", True)),
            opponent=opponent,
            growth=LAND_GROWTH,  # not configurable; any payload value is ignored
            max_turns=_clamp_int(payload.get("max_turns"), 1000, 20, 5000),
        )

    def config(self) -> EnvConfig:
        """The static :class:`~generals_jax.EnvConfig` this session runs."""
        size = int(self.size)
        return EnvConfig(
            height=size,
            width=size,
            city_count=max(2, size // 2),
            land_growth_period=int(self.growth),
            fog=bool(self.fog),
            half_moves=True,  # enables the generals.io "Z" split move
            max_turns=int(self.max_turns),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Game:
    """A live match: the JAX state plus the opponent policy."""

    def __init__(
        self,
        game_id: str,
        settings: GameSettings,
        env: GeneralsEnv,
        seed: Optional[int] = None,
        policy=None,
    ) -> None:
        self.id = game_id
        self.settings = settings
        self.env = env
        self.policy = policy
        if settings.opponent == "checkpoint" and policy is None:
            raise ValueError("no checkpoint configured; start the server with --run-dir")
        self.bot_memory = policy.initial_memory() if policy else None
        self.player = YOU
        self.rng = np.random.default_rng(seed)
        self.lock = threading.Lock()
        self.state = env.reset(jax.random.PRNGKey(int(self.rng.integers(0, 2**31 - 1))))
        self.last_player_action: int = 0
        self.last_bot_action: int = 0
        self.steps: int = 0
        self.recorder = ReplayRecorder(
            self.env.config,
            players=[("you", "human"), (f"bot ({settings.opponent})", "bot")],
            meta={"source": "generals_web", "opponent": settings.opponent},
        )
        self.recorder.add(self.state)

    # ------------------------------------------------------------------ play
    def step(self, action: Optional[int]) -> None:
        """Advance one half-turn: the human's action plus the bot's reply."""
        with self.lock:
            if bool(self.state.done):
                return

            number = 0 if action is None else _clamp_int(action, 0, 0, self.env.num_actions - 1)
            if self.policy is not None:
                bot_action, self.bot_memory = self.policy.action(self.env, self.state, self.bot_memory)
            else:
                bot_action = int(choose_action(
                    self.env, self.state, OPPONENT, self.settings.opponent, self.rng
                ))
            actions = jnp.asarray(
                [number, bot_action],
                dtype=jnp.int32,
            )
            self.state, rewards, _info = self.env.step(self.state, actions)
            self.last_player_action = number
            self.last_bot_action = bot_action
            self.steps += 1
            self.recorder.add(self.state, actions=actions, rewards=rewards)

    def reset(self) -> None:
        with self.lock:
            self.state = self.env.reset(
                jax.random.PRNGKey(int(self.rng.integers(0, 2**31 - 1)))
            )
            self.steps = 0
            if self.policy is not None:
                self.bot_memory = self.policy.initial_memory()
            self.last_player_action = 0
            self.last_bot_action = 0
            self.recorder = ReplayRecorder(
                self.env.config,
                players=[("you", "human"), (f"bot ({self.settings.opponent})", "bot")],
                meta={"source": "generals_web", "opponent": self.settings.opponent},
            )
            self.recorder.add(self.state)

    # --------------------------------------------------------------- replays
    def replay(self) -> Replay:
        """The game so far, as a renderable :class:`~game.replay.Replay`."""
        with self.lock:
            self.recorder.result()
            return Replay.from_dict(copy.deepcopy(self.recorder.to_dict()))

    def replay_document(self) -> Dict[str, Any]:
        """The raw replay JSON (what ``GET /api/games/<id>/replay`` returns)."""
        with self.lock:
            self.recorder.result()
            return copy.deepcopy(self.recorder.to_dict())

    def replay_html(self) -> str:
        """A single-file HTML player of this game (no server required)."""
        from game.replay_html import player_html

        return player_html(self.replay())

    # ------------------------------------------------------------- snapshots
    def snapshot(self) -> Dict[str, Any]:
        """The board as the human player is allowed to see it, JSON-ready."""
        with self.lock:
            return self._snapshot_locked()

    def _snapshot_locked(self) -> Dict[str, Any]:
        cfg = self.env.config
        state = self.state
        h, w = cfg.height, cfg.width

        army = np.asarray(state.army, dtype=np.int32)
        owner = np.asarray(state.owner, dtype=np.int32)
        city = np.asarray(state.city, dtype=bool)
        general = np.asarray(state.general, dtype=np.int32)
        alive = np.asarray(state.alive, dtype=bool)
        done = bool(state.done)
        winner = int(state.winner)
        if not done:
            reason = None
        elif bool(alive.all()):
            reason = "turn limit"
        elif winner < 0:
            reason = "draw"
        else:
            reason = "general captured"

        revealed = done or not cfg.fog
        if revealed:
            vis = np.ones((h, w), dtype=bool)
        else:
            vis = np.asarray(visible_mask(state, self.player, cfg), dtype=bool)

        obstacle = (owner == MOUNTAIN) | city
        shown_owner = np.where(vis, owner, np.where(obstacle, OBSTACLE, UNKNOWN))
        shown_army = np.where(vis, army, 0)
        shown_city = np.where(vis, city, False)

        generals: Dict[str, Optional[list]] = {"you": None, "enemy": None}
        me = self.player
        if alive[me]:
            generals["you"] = [int(general[me]) // w, int(general[me]) % w]
        enemy_tile = int(general[OPPONENT])
        enemy_row, enemy_col = divmod(enemy_tile, w)
        if alive[OPPONENT] and (revealed or vis[enemy_row, enemy_col]):
            # Under fog the enemy general leaks only once it is actually in
            # sight, exactly like the engine's observation channel.
            generals["enemy"] = [enemy_row, enemy_col]

        land = [int(np.sum(owner == p)) for p in range(MAX_PLAYERS)]
        total_army = [
            int(np.sum(np.where(owner == p, army, 0))) for p in range(MAX_PLAYERS)
        ]
        castles = [
            int(np.sum(city & (owner == p))) for p in range(MAX_PLAYERS)
        ]

        return {
            "id": self.id,
            "turn": int(state.turn + state.half_turn),
            "half_turn": int(state.half_turn),
            "max_turns": int(cfg.max_turns),
            "done": done,
            "winner": winner,
            "reason": reason,
            "you": me,
            "opponent": self.settings.opponent,
            "h": h,
            "w": w,
            "dir_actions": int(cfg.dir_actions),
            "owner": shown_owner.reshape(-1).tolist(),
            "army": shown_army.reshape(-1).tolist(),
            "city": shown_city.reshape(-1).astype(np.int8).tolist(),
            "vis": vis.reshape(-1).astype(np.int8).tolist(),
            "generals": generals,
            "score": {"land": land, "army": total_army, "cities": castles},
            "revealed": bool(revealed),
            "settings": self.settings.to_dict(),
            "mountain": int(MOUNTAIN),
            "obstacle": int(OBSTACLE),
        }


def snapshots(games) -> list:
    """Snapshot helper used by tests / debugging."""
    return [game.snapshot() for game in games]
