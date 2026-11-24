"""Tiny ASCII renderer for debugging games."""

from __future__ import annotations

import numpy as np

from .config import MOUNTAIN, EnvConfig
from .obs import visible_mask
from .state import State

_PLAIN = {-1: ".", 0: "0", 1: "1"}
_CASTLE = {-1: "c", 0: "C", 1: "D"}
_GENERAL = {0: "A", 1: "B"}


def _cell(
    army: int, owner: int, is_city: bool, general: int | None, hidden: bool, width: int
) -> str:
    if hidden:
        if owner == MOUNTAIN or is_city:
            return "^".rjust(width)
        return "?" .rjust(width)
    if owner == MOUNTAIN:
        return "#".rjust(width)
    if general is not None:
        marker = _GENERAL[general]
    elif is_city:
        marker = _CASTLE.get(owner, "c")
    else:
        marker = _PLAIN.get(owner, "?")
    return f"{int(army):{width}d}" + marker


def ascii_state(state: State, cfg: EnvConfig, player: int | None = None) -> str:
    """Render the board.

    If ``player`` is given (and fog is enabled) tiles the player cannot see are
    drawn as ``?``.
    """
    army = np.asarray(state.army)
    owner = np.asarray(state.owner)
    city = np.asarray(state.city)
    general = np.asarray(state.general)
    alive = np.asarray(state.alive)
    h, w = army.shape
    width = max(2, len(str(int(army.max())) if army.size else 2))
    cw = width + 1  # one marker column

    if player is not None and cfg.fog:
        mask = np.asarray(visible_mask(state, player, cfg))
    else:
        mask = np.ones((h, w), dtype=bool)

    gen_at = {
        (int(general[p]) // w, int(general[p]) % w): p
        for p in range(len(general))
        if alive[p]
        and int(general[p]) >= 0
        and owner.reshape(-1)[int(general[p])] == p
    }

    lines = ["     " + "".join(f"{c % 10}".ljust(cw) for c in range(w))]
    for r in range(h):
        cells = [
            _cell(
                army[r, c],
                int(owner[r, c]),
                bool(city[r, c]),
                gen_at.get((r, c)),
                hidden=not mask[r, c],
                width=width,
            ).ljust(cw)
            for c in range(w)
        ]
        lines.append(f"{r:4d} " + "".join(cells))

    land = [int((owner == p).sum()) for p in range(2)]
    total = [int(np.where(owner == p, army, 0).sum()) for p in range(2)]
    display_turn = int(state.turn + state.half_turn)
    move_slot = int(state.half_turn) + 1
    lines.append(
        f"turn {display_turn:4d} (move {move_slot}/2) | P0 land {land[0]:3d} army {total[0]:5d} "
        f"| P1 land {land[1]:3d} army {total[1]:5d} "
        f"| done={bool(state.done)} winner={int(state.winner)}"
    )
    return "\n".join(lines)


def print_state(state: State, cfg: EnvConfig, player: int | None = None) -> None:
    print(ascii_state(state, cfg, player))
