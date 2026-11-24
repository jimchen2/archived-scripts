"""Opponent policies for the browser game.

Three difficulties:

``easy``
    A uniformly random legal move.

``normal``
    A small greedy heuristic that only reasons about tiles player 1 can
    actually *see*, so it cannot cheat through the fog of war.  It expands into
    neutral land, grabs castles it can afford, reinforces its frontier and
    pounces on the enemy general when it stumbles into it.

``hard``
    The JAX greedy baseline. Like ``normal``, it respects fog of war and uses
    only visible tiles; the game engine handles general capture.

Everything here works on numpy arrays converted from the JAX state; one action
per half-turn is a few hundred microseconds at most.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np

from bot.baselines import greedy_action
from game.config import DOWN, LEFT, MOUNTAIN, PASS, RIGHT, UP

DIFFICULTIES = ("easy", "normal", "hard")

# direction code -> (dr, dc)
DIRS = {UP: (-1, 0), DOWN: (1, 0), LEFT: (0, -1), RIGHT: (0, 1)}


def visible_from_owner(owner: np.ndarray, player: int) -> np.ndarray:
    """Boolean ``(H, W)`` mask: my tiles plus the 8-neighbour ring around them."""
    own = owner == player
    h, w = own.shape
    padded = np.pad(own, 1, mode="constant", constant_values=False)
    vis = np.zeros((h, w), dtype=bool)
    for dr in range(3):
        for dc in range(3):
            vis |= padded[dr : dr + h, dc : dc + w]
    return vis


def legal_actions(army: np.ndarray, owner: np.ndarray, player: int, dir_actions: int) -> list[int]:
    """Every legal ``src * dir_actions + dir`` action for ``player`` (plus pass)."""
    h, w = army.shape
    out = [PASS]
    rows, cols = np.nonzero((owner == player) & (army > 1))
    for r, c in zip(rows.tolist(), cols.tolist()):
        src = r * w + c
        for code, (dr, dc) in DIRS.items():
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and owner[rr, cc] != MOUNTAIN:
                out.append(src * dir_actions + code)
    return out


def heuristic_action(
    army: np.ndarray,
    owner: np.ndarray,
    city: np.ndarray,
    vis: np.ndarray,
    player: int,
    enemy_general: int,
    enemy_alive: bool,
    dir_actions: int,
    rng: np.random.Generator,
) -> int:
    """Pick the best-looking move using only what ``player`` can see."""
    h, w = army.shape
    enemy = 1 - player
    best_score = -1e18
    best_action = PASS

    rows, cols = np.nonzero((owner == player) & (army > 1))
    if len(rows) == 0:
        return PASS

    for r, c in zip(rows.tolist(), cols.tolist()):
        stack = int(army[r, c])
        attack = stack - 1
        src = r * w + c
        for code, (dr, dc) in DIRS.items():
            rr, cc = r + dr, c + dc
            if not (0 <= rr < h and 0 <= cc < w):
                continue
            tile = rr * w + cc
            if vis[rr, cc]:
                who = int(owner[rr, cc])
                if who == MOUNTAIN:
                    continue
                if who == player:
                    # Mild pull towards stacking the frontier; never beat a
                    # free neutral tile.
                    score = 0.25 * (int(army[rr, cc]) + attack) + 0.5
                else:
                    defence = int(army[rr, cc])
                    if attack <= defence:
                        continue  # would just feed the defender
                    score = 12.0 + defence - 0.06 * attack
                    if city[rr, cc]:
                        score += 260.0
                    if who == enemy:
                        score += 18.0
                    if enemy_alive and tile == enemy_general:
                        score += 5000.0
            else:
                # Fog: probing is cheap with small stacks and wasted with big
                # ones, so prefer to explore with modest forces.
                score = 4.0 if 3 <= attack <= 12 else 0.4
            score += float(rng.random()) * 2.0
            if score > best_score:
                best_score = score
                best_action = src * dir_actions + code
    return best_action


def choose_action(env, state, player: int, difficulty: str, rng: np.random.Generator) -> int:
    """Return an action index for ``player`` (0 = pass)."""
    cfg = env.config
    if difficulty == "hard":
        return int(greedy_action(state, player, cfg, env.tables))

    army = np.asarray(state.army)
    owner = np.asarray(state.owner)
    city = np.asarray(state.city)

    if difficulty == "easy":
        actions: Sequence[int] = legal_actions(army, owner, player, cfg.dir_actions)
        # A pass now and then keeps the easy bot from feeling like a wall.
        if rng.random() < 0.15:
            return PASS
        return int(actions[int(rng.integers(0, len(actions)))])

    vis = np.ones_like(army, dtype=bool) if not cfg.fog else visible_from_owner(owner, player)
    general = np.asarray(state.general)
    alive = np.asarray(state.alive)
    return heuristic_action(
        army,
        owner,
        city,
        vis,
        player,
        int(general[1 - player]),
        bool(alive[1 - player]),
        cfg.dir_actions,
        rng,
    )
