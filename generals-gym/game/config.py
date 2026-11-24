"""Static configuration for the 1v1 generals.io simulator.

Everything in here is *static* (Python ints / bools), so a config can be closed
over by ``jax.jit`` without retracing every step.
"""

from __future__ import annotations

from dataclasses import dataclass

# Tile ownership encoding (owner array).
MOUNTAIN = -2
NEUTRAL = -1

NUM_PLAYERS = 2

# Direction codes inside a cell's action block.
#   0       = pass / no-op
#   1..4    = move the whole army (minus the 1 unit that always stays home)
#   5..8    = move half the army, rounded down (generals.io "50%" move)
PASS = 0
UP = 1
DOWN = 2
LEFT = 3
RIGHT = 4
DIR_NAMES = ("pass", "up", "down", "left", "right")


@dataclass(frozen=True)
class EnvConfig:
    """Configuration of a 1v1 game.

    Defaults model a standard generals.io duel: a 21x21 map with ~20% of tiles
    turned into mountains, 10 neutral castles holding 40-50 armies, two generals
    at least ``general_min_dist`` (Manhattan) apart, two simultaneous action
    slots per displayed turn, +1 army per turn on castles and generals, and +1
    army on every owned tile every 25 displayed turns.
    """

    # --- board ---
    height: int = 21
    width: int = 21

    # --- map generation ---
    mountain_frac: float = 0.20
    city_count: int = 10
    city_min_army: int = 40
    city_max_army: int = 50
    # Desired Manhattan distance between the two generals. It is capped at the
    # largest distance the board allows, so small boards still work.
    general_min_dist: int = 14
    city_general_min_dist: int = 3  # Manhattan distance from any city to a general
    city_city_min_dist: int = 2     # Manhattan distance between castles

    # --- rules ---
    land_growth_period: int = 25  # displayed turns between land-growth ticks
    general_start_army: int = 1   # every tile starts with 1 army on the general
    half_moves: bool = False      # expose the "50%" move as extra actions
    max_turns: int = 1000         # displayed turns; running out is a double loss

    # --- observation ---
    fog: bool = True
    army_norm: float = 50.0       # log1p army scaling for observations

    def __post_init__(self) -> None:
        if self.height < 2 or self.width < 2:
            raise ValueError("board must be at least 2x2")
        if not 0.0 <= self.mountain_frac < 1.0:
            raise ValueError("mountain_frac must be in [0, 1)")
        if self.city_count < 0:
            raise ValueError("city_count must be >= 0")
        if self.city_min_army < 1 or self.city_max_army < self.city_min_army:
            raise ValueError("bad city army range")
        if self.land_growth_period < 1:
            raise ValueError("land_growth_period must be >= 1")
        if self.max_turns < 1:
            raise ValueError("max_turns must be >= 1")


    # ---- derived, cached properties -------------------------------------
    @property
    def num_tiles(self) -> int:
        return self.height * self.width

    @property
    def dir_actions(self) -> int:
        """Number of direction codes per cell (5, or 9 with half moves)."""
        return 9 if self.half_moves else 5

    @property
    def num_actions(self) -> int:
        """Size of the per-player discrete action space.

        ``action = src_tile * dir_actions + dir``.
        """
        return self.num_tiles * self.dir_actions

    @property
    def num_players(self) -> int:
        return NUM_PLAYERS

    def replace(self, **kwargs) -> EnvConfig:
        from dataclasses import replace

        return replace(self, **kwargs)
