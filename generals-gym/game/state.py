"""Game state container and small state utilities."""

from __future__ import annotations

from typing import NamedTuple

import jax.numpy as jnp

from .config import NUM_PLAYERS, EnvConfig


class State(NamedTuple):
    """Full (omniscient) state of a 1v1 generals.io game.

    Attributes
    ----------
    army:    (H, W) int32  armies on each tile (0 for mountains).
    owner:   (H, W) int32  -2 mountain, -1 neutral, 0 / 1 player.
    city:    (H, W) bool   true for castles (including captured generals).
    general: (P,)  int32   flat index of each player's general.
    alive:   (P,)  bool    whether the player still has a general.
    turn:      ()    int32   number of completed displayed turns.
    half_turn: ()    int32   0 or 1; action slot within the current turn.
    winner:    ()    int32   -1 while running / draw, 0 or 1 once decided.
    done:      ()    bool    episode finished.
    key:       ()    uint32  PRNG key, split on auto-reset.
    """

    army: jnp.ndarray
    owner: jnp.ndarray
    city: jnp.ndarray
    general: jnp.ndarray
    alive: jnp.ndarray
    turn: jnp.ndarray
    half_turn: jnp.ndarray
    winner: jnp.ndarray
    done: jnp.ndarray
    key: jnp.ndarray


def land_count(state: State) -> jnp.ndarray:
    """(P,) number of tiles owned by each player."""
    return jnp.stack([jnp.sum(state.owner == p) for p in range(NUM_PLAYERS)]).astype(jnp.int32)


def army_total(state: State) -> jnp.ndarray:
    """(P,) total armies owned by each player."""
    return jnp.stack(
        [jnp.sum(jnp.where(state.owner == p, state.army, 0)) for p in range(NUM_PLAYERS)]
    ).astype(jnp.int32)


def city_count(state: State) -> jnp.ndarray:
    """(P,) number of castles owned by each player (general excluded)."""
    return jnp.stack(
        [jnp.sum(state.city & (state.owner == p)) for p in range(NUM_PLAYERS)]
    ).astype(jnp.int32)


def general_mask(state: State, cfg: EnvConfig) -> jnp.ndarray:
    """(H, W) bool marking the generals of *alive* players."""
    flat = jnp.zeros((cfg.num_tiles,), dtype=bool)
    flat = flat.at[state.general].set(state.alive)
    return flat.reshape(cfg.height, cfg.width)


def score(state: State) -> jnp.ndarray:
    """(P, 2) -> (land, army) per player, for scoreboard display."""
    return jnp.stack([land_count(state), army_total(state)], axis=1)


def owned_mask(state: State) -> jnp.ndarray:
    return state.owner >= 0
