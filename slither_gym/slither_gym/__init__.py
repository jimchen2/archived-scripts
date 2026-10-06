"""Gymnasium pipeline for slither.io driven by JavaScript variables, not pixels."""

from slither_gym.env import SlitherIOEnv
from slither_gym.spec import OBS_DIM, decode_action, vectorize

__all__ = ["SlitherIOEnv", "OBS_DIM", "decode_action", "vectorize"]

try:
    from gymnasium.envs.registration import register

    register(
        id="SlitherIO-v0",
        entry_point="slither_gym.env:SlitherIOEnv",
    )
except Exception:
    pass
