"""Observation vector is a pure function of the JS snapshot."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from slither_gym.spec import FOOD_DIM, N_FOOD, OBS_DIM, SELF_DIM, WORLD_DIM, decode_action, vectorize


def test_decode_covers_headings_and_boost():
    angle, boost = decode_action(0)
    assert angle == 0.0 and boost is False
    angle, boost = decode_action(8)
    assert angle == 0.0 and boost is True
    angle, boost = decode_action(1)
    assert math.isclose(angle, math.pi / 4) and boost is False


def test_vector_uses_js_fields_not_a_fixed_placeholder():
    js = {
        "grd": 1000.0,
        "flux_grd": 400.0,
        "rank": 3,
        "slither_count": 20,
        "foods_c": 8,
        "gsc": 0.9,
        "score": 100.0,
        "self": {
            "xx": 500.0,
            "yy": 500.0,
            "ang": 0.0,
            "eang": math.pi / 2,
            "sp": 7.0,
            "sc": 2.0,
            "sct": 10,
            "fam": 0.5,
            "md": True,
        },
        "foods": [{"xx": 700.0, "yy": 500.0, "sz": 15.0}],
        "snakes": [
            {
                "xx": 500.0,
                "yy": 800.0,
                "ang": math.pi,
                "sc": 1.5,
                "pts": [{"xx": 500.0, "yy": 650.0}],
            }
        ],
        "preys": [{"xx": 500.0, "yy": 400.0}],
    }
    obs = vectorize(js)
    assert obs.shape == (OBS_DIM,)
    assert obs[0] == 1.0
    assert obs[1] == 0.5 and obs[2] == 0.5
    assert obs[3] == 1.0 and abs(obs[4]) < 1e-6
    assert abs(obs[5]) < 1e-6 and obs[6] == 1.0
    assert obs[12] == 1.0
    food = obs[SELF_DIM + WORLD_DIM : SELF_DIM + WORLD_DIM + 3]
    assert food[0] == 0.2 and food[1] == 0.0 and food[2] == 0.5
    snake = obs[SELF_DIM + WORLD_DIM + FOOD_DIM : SELF_DIM + WORLD_DIM + FOOD_DIM + 6]
    assert snake[1] == 0.3
    assert snake[5] == 0.15
    dead = vectorize(js, dead=True)
    assert dead[0] == 0.0
    assert dead[SELF_DIM + 4] == 1.0
    assert N_FOOD == 16


if __name__ == "__main__":
    test_decode_covers_headings_and_boost()
    test_vector_uses_js_fields_not_a_fixed_placeholder()
    print("obs tests passed")
