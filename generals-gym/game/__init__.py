"""``game`` - a fast, fully vectorised JAX simulator for 1v1 generals.io.

This package is the environment half of the project (rules, maps, fog of war,
rendering).  The learning agent lives in :mod:`bot` and the training scripts
in :mod:`src`.

Quick start
-----------
>>> import jax
>>> from game import GeneralsEnv
>>> env = GeneralsEnv()
>>> state = env.reset(jax.random.PRNGKey(0))
>>> state, rewards, info = env.step(state, env.sample_actions(jax.random.PRNGKey(1), state))
"""

from . import engine, maps, obs, render, tables
from .config import (
    DIR_NAMES,
    MOUNTAIN,
    NEUTRAL,
    NUM_PLAYERS,
    EnvConfig,
)
from .env import GeneralsEnv, from_numpy, make_env, to_numpy
from .obs import (
    GRID_CHANNELS,
    NUM_GRID_CHANNELS,
    NUM_SCALARS,
    SCALAR_FEATURES,
    Observation,
    batch_observation,
    observation,
    visible_mask,
)
from .render import ascii_state, print_state
from .replay import Replay, ReplayRecorder
from .state import State, army_total, city_count, land_count

__all__ = [
    "DIR_NAMES",
    "GRID_CHANNELS",
    "MOUNTAIN",
    "NEUTRAL",
    "NUM_GRID_CHANNELS",
    "NUM_PLAYERS",
    "NUM_SCALARS",
    "SCALAR_FEATURES",
    "EnvConfig",
    "GeneralsEnv",
    "Observation",
    "Replay",
    "ReplayRecorder",
    "State",
    "army_total",
    "ascii_state",
    "batch_observation",
    "city_count",
    "engine",
    "from_numpy",
    "land_count",
    "make_env",
    "maps",
    "obs",
    "observation",
    "print_state",
    "render",
    "tables",
    "to_numpy",
    "visible_mask",
]

__version__ = "0.2.0"
