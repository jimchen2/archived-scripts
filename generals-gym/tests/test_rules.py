"""Rule-level tests on hand-built boards."""

from __future__ import annotations

import jax
import jax.numpy as jnp
import numpy as np

from game import EnvConfig, GeneralsEnv
from game.config import DOWN, LEFT, MOUNTAIN, NEUTRAL, PASS, RIGHT, UP


def make_env(rows, **cfg_kwargs):
    """Build an env + a state from an ASCII layout (see maps.parse_rows)."""
    h = len(rows)
    w = len(rows[0].split())
    cfg = EnvConfig(height=h, width=w, **cfg_kwargs)
    env = GeneralsEnv(cfg)
    return env, env.make_state(rows)


def a(env, row, col, direction):
    """Flat action index for moving from (row, col) in ``direction``."""
    w = env.config.width
    return (row * w + col) * env.config.dir_actions + direction


def step(env, state, a0, a1):
    """Convenience helper: play one displayed turn, passing on slot two."""
    state, rewards, info = env.step(state, jnp.asarray([a0, a1], dtype=jnp.int32))
    if not bool(state.done):
        state, rewards, info = env.step(
            state, jnp.asarray([PASS, PASS], dtype=jnp.int32)
        )
    return state, rewards, info


def army_of(state, r, c):
    return int(state.army[r, c])


def owner_of(state, r, c):
    return int(state.owner[r, c])


# ---------------------------------------------------------------------------
# movement
# ---------------------------------------------------------------------------
def test_two_actions_complete_one_displayed_turn():
    env, state = make_env(["g0:5 . . . . g1:1", ". . . . . ."])

    state, _, info = env.step(
        state, jnp.asarray([a(env, 0, 0, RIGHT), PASS], dtype=jnp.int32)
    )
    assert int(state.turn) == 0 and int(state.half_turn) == 1
    assert int(info["turn"]) == 1
    assert owner_of(state, 0, 1) == 0

    state, _, info = env.step(
        state, jnp.asarray([a(env, 0, 1, RIGHT), PASS], dtype=jnp.int32)
    )
    assert int(state.turn) == 1 and int(state.half_turn) == 0
    assert int(info["turn"]) == 1
    assert owner_of(state, 0, 2) == 0
    assert army_of(state, 0, 2) == 3
    assert army_of(state, 0, 0) == 2  # left 1, then +1 general production


def test_move_leaves_one_behind_and_adds_to_own_tile():
    env, s = make_env(["g0:3 . .", ". . .", ". . g1:3"])
    s2, rew, _ = step(env, s, a(env, 0, 0, RIGHT), a(env, 2, 2, PASS))
    # 3 armies: 1 stays, 2 move.  The general then produces +1 at end of turn.
    assert army_of(s2, 0, 0) == 2
    assert owner_of(s2, 0, 1) == 0
    assert army_of(s2, 0, 1) == 2
    assert int(s2.turn) == 1
    assert not bool(s2.done)
    assert np.allclose(np.asarray(rew), 0.0)


def test_move_onto_own_tile_reinforces():
    env, s = make_env(["g0:5 0:2 .", ". . .", ". . g1:3"])
    s2, _, _ = step(env, s, a(env, 0, 0, RIGHT), a(env, 2, 2, PASS))
    assert army_of(s2, 0, 0) == 2      # 1 left + 1 general production
    assert army_of(s2, 0, 1) == 2 + 4  # 2 + 4 moved


def test_army_one_cannot_move():
    env, s = make_env(["g0:1 . .", ". . .", ". . g1:3"])
    s2, _, _ = step(env, s, a(env, 0, 0, RIGHT), a(env, 2, 2, PASS))
    assert army_of(s2, 0, 1) == 0
    assert owner_of(s2, 0, 1) == NEUTRAL
    assert army_of(s2, 0, 0) == 2  # untouched, then +1 production


def test_mountains_cannot_be_entered():
    env, s = make_env(["g0:9 # .", ". . .", ". . g1:3"])
    s2, _, _ = step(env, s, a(env, 0, 0, RIGHT), a(env, 2, 2, PASS))
    assert owner_of(s2, 0, 1) == MOUNTAIN
    assert army_of(s2, 0, 1) == 0
    assert army_of(s2, 0, 0) == 10  # move rejected, then +1 production


def test_off_board_move_is_a_pass():
    env, s = make_env(["g0:9 . .", ". . .", ". . g1:3"])
    s2, _, _ = step(env, s, a(env, 0, 0, UP), a(env, 2, 2, DOWN))
    assert army_of(s2, 0, 0) == 10
    assert army_of(s2, 2, 2) == 4
    assert int(s2.turn) == 1


def test_unowned_tile_cannot_move():
    env, s = make_env(["g0:9 . .", ". -1:7 .", ". . g1:3"])
    s2, _, _ = step(env, s, a(env, 1, 1, RIGHT), a(env, 2, 2, PASS))
    assert army_of(s2, 1, 1) == 7
    assert army_of(s2, 1, 2) == 0
    assert owner_of(s2, 1, 2) == NEUTRAL


# ---------------------------------------------------------------------------
# combat
# ---------------------------------------------------------------------------
def test_attack_captures_only_on_strict_majority():
    env, s = make_env(["g0:5 1:4 .", ". . .", ". . g1:3"])
    s2, _, _ = step(env, s, a(env, 0, 0, RIGHT), a(env, 2, 2, PASS))
    # 4 vs 4 -> no capture, the defender keeps a tile with 0 armies
    assert owner_of(s2, 0, 1) == 1
    assert army_of(s2, 0, 1) == 0


def test_attack_wins_with_survivors():
    env, s = make_env(["g0:6 1:4 .", ". . .", ". . g1:3"])
    s2, _, _ = step(env, s, a(env, 0, 0, RIGHT), a(env, 2, 2, PASS))
    # 5 vs 4 -> capture with 1 survivor (plain land does not produce)
    assert owner_of(s2, 0, 1) == 0
    assert army_of(s2, 0, 1) == 1
    assert army_of(s2, 0, 0) == 2  # 1 left behind + 1 general production


def test_attack_wins_against_neutral_land():
    env, s = make_env(["g0:6 . .", ". . .", ". . g1:3"])
    s2, _, _ = step(env, s, a(env, 0, 0, RIGHT), a(env, 2, 2, PASS))
    assert owner_of(s2, 0, 1) == 0
    assert army_of(s2, 0, 1) == 5


def test_equal_attackers_destroy_each_other():
    env, s = make_env(["0:6 . 1:6", "g0:1 . g1:1"])
    s2, _, _ = step(env, s, a(env, 0, 0, RIGHT), a(env, 0, 2, LEFT))
    assert owner_of(s2, 0, 1) == NEUTRAL
    assert army_of(s2, 0, 1) == 0
    assert army_of(s2, 0, 0) == 1
    assert army_of(s2, 0, 2) == 1


def test_stronger_attacker_then_fights_the_weaker_one():
    env, s = make_env(["0:6 . 1:12", "g0:1 . g1:1"])
    s2, _, _ = step(env, s, a(env, 0, 0, RIGHT), a(env, 0, 2, LEFT))
    # P1 brings 11, captures the empty tile, then beats P0's 5: 11 - 5 = 6
    assert owner_of(s2, 0, 1) == 1
    assert army_of(s2, 0, 1) == 6
    assert army_of(s2, 0, 0) == 1
    assert army_of(s2, 0, 2) == 1


def test_armies_leave_before_arrivals_are_resolved():
    # P0 abandons a tile that P1 is attacking: the defenders are gone.
    env, s = make_env(["0:5 1:9", "g0:1 g1:1"])
    s2, _, _ = step(env, s, a(env, 0, 0, DOWN), a(env, 0, 1, LEFT))
    assert owner_of(s2, 0, 0) == 1
    assert army_of(s2, 0, 0) == 9 - 1 - 1  # 8 attackers vs 1 defender, then +1 prod
    assert army_of(s2, 1, 0) == 1 + 4 + 1  # transferred armies + general production


def test_reinforcement_counts_against_an_attack():
    # P0 reinforces (0,1) while P1 attacks it: the transferred armies defend.
    env, s = make_env(["0:9 0:1 1:5", "g0:1 . g1:1"])
    s2, _, _ = step(env, s, a(env, 0, 0, RIGHT), a(env, 0, 2, LEFT))
    assert owner_of(s2, 0, 1) == 0
    assert army_of(s2, 0, 1) == 1 + 8 - 4  # 9 defenders, 4 attackers survive


def test_attack_on_a_reinforced_general():
    env, s = make_env(["0:5 g0:9 1:20", ". . g1:1"], max_turns=50)
    s2, rew, _ = step(env, s, a(env, 0, 0, RIGHT), a(env, 0, 2, LEFT))
    # P0 reinforces its general with 4 (9 + 4 = 13 defenders), P1 brings 19
    # and captures it with 6 left over.
    assert bool(s2.done)
    assert int(s2.winner) == 1
    assert owner_of(s2, 0, 1) == 1
    assert army_of(s2, 0, 1) == 6
    assert bool(s2.city[0, 1])
    assert owner_of(s2, 0, 0) == 1
    assert army_of(s2, 0, 0) == 1  # round(1 * 0.5) = 1
    assert np.allclose(np.asarray(rew), [-1.0, 1.0])


# ---------------------------------------------------------------------------
# production
# ---------------------------------------------------------------------------
def test_production_waits_until_both_half_turns_finish():
    env, state = make_env(["g0:1 c0:10 .", ". . .", ". . g1:1"])
    state, _, _ = env.step(state, jnp.asarray([PASS, PASS], dtype=jnp.int32))
    assert army_of(state, 0, 0) == 1
    assert army_of(state, 0, 1) == 10
    assert int(state.half_turn) == 1

    state, _, _ = env.step(state, jnp.asarray([PASS, PASS], dtype=jnp.int32))
    assert army_of(state, 0, 0) == 2
    assert army_of(state, 0, 1) == 11
    assert int(state.turn) == 1 and int(state.half_turn) == 0


def test_generals_and_castles_produce_every_turn():
    env, s = make_env(["g0:1 C:40 .", ". . .", ". . g1:1"])
    s2, _, _ = step(env, s, PASS, PASS)
    assert army_of(s2, 0, 0) == 2
    assert army_of(s2, 0, 1) == 40
    assert army_of(s2, 2, 2) == 2


def test_owned_castles_produce():
    env, s = make_env(["g0:1 c0:10 .", ". . .", ". . g1:1"])
    s2, _, _ = step(env, s, PASS, PASS)
    assert army_of(s2, 0, 1) == 11


def test_land_grows_every_twenty_five_turns():
    env, s = make_env(
        ["g0:1 0:3 .", ". . .", ". . g1:1"], land_growth_period=3
    )
    # plain land only grows on multiples of land_growth_period
    for turn in range(1, 7):
        s, _, _ = step(env, s, PASS, PASS)
        expected = 3 + turn // 3
        assert army_of(s, 0, 1) == expected, f"turn {turn}"


# ---------------------------------------------------------------------------
# half moves
# ---------------------------------------------------------------------------
def test_half_move_leaves_half_behind():
    env, s = make_env(
        ["g0:7 . .", ". . .", ". . g1:1"], half_moves=True
    )
    s2, _, _ = step(env, s, a(env, 0, 0, RIGHT + 4), PASS)
    assert army_of(s2, 0, 0) == 4 + 1  # ceil(7/2) + general production
    assert army_of(s2, 0, 1) == 3


def test_half_move_reserve_is_ceil():
    env, s = make_env(["g0:8 . .", ". . .", ". . g1:1"], half_moves=True)
    s2, _, _ = step(env, s, a(env, 0, 0, RIGHT + 4), PASS)
    assert army_of(s2, 0, 0) == 4 + 1
    assert army_of(s2, 0, 1) == 4


# ---------------------------------------------------------------------------
# generals
# ---------------------------------------------------------------------------
def test_capturing_a_general_wins_and_absorbs_land():
    env, s = make_env(
        ["g0:1 1:9 .", "0:7 . .", ". . g1:1"]
    )
    s2, rew, info = step(env, s, a(env, 1, 0, PASS), a(env, 0, 1, LEFT))
    assert bool(s2.done)
    assert int(s2.winner) == 1
    assert np.allclose(np.asarray(rew), [-1.0, 1.0])
    # the general tile itself falls to the attacker with 8 - 1 = 7 armies
    assert owner_of(s2, 0, 0) == 1
    assert army_of(s2, 0, 0) == 7
    # the loser's land is absorbed at half strength, rounded up
    assert owner_of(s2, 1, 0) == 1
    assert army_of(s2, 1, 0) == 4
    # and the dead general becomes a castle
    assert bool(s2.city[0, 0])
    assert not bool(s2.alive[0])


def test_general_capture_absorbs_castles_too():
    env, s = make_env(["g0:1 1:9 .", "c0:10 . .", ". . g1:1"])
    s2, _, _ = step(env, s, PASS, a(env, 0, 1, LEFT))
    assert owner_of(s2, 1, 0) == 1
    assert army_of(s2, 1, 0) == 5


def test_stepping_a_finished_game_is_a_noop():
    env, s = make_env(["g0:1 1:9 .", "0:7 . .", ". . g1:1"])
    s2, rew, _ = step(env, s, PASS, a(env, 0, 1, LEFT))
    s3, rew2, _ = step(env, s2, PASS, PASS)
    assert np.allclose(np.asarray(rew2), 0.0)
    assert np.array_equal(np.asarray(s3.army), np.asarray(s2.army))
    assert int(s3.turn) == int(s2.turn)


# ---------------------------------------------------------------------------
# termination
# ---------------------------------------------------------------------------
def test_turn_limit_is_a_double_loss():
    # P0 owns strictly more land, but running out the clock must not win it.
    env, s = make_env(
        ["g0:1 0:3 .", ". . .", ". . g1:1"], max_turns=2
    )
    s, _, _ = step(env, s, PASS, PASS)
    assert not bool(s.done)
    s, rew, _ = step(env, s, PASS, PASS)
    assert bool(s.done)
    assert int(s.winner) == -1
    assert np.allclose(np.asarray(rew), [0.0, 0.0])


def test_turn_limit_can_draw():
    env, s = make_env(["g0:1 .", ". g1:1"], max_turns=1)
    s, rew, _ = step(env, s, PASS, PASS)
    assert bool(s.done)
    assert int(s.winner) == -1
    assert np.allclose(np.asarray(rew), [0.0, 0.0])


# ---------------------------------------------------------------------------
# action mask
# ---------------------------------------------------------------------------
def test_action_mask_matches_legality():
    env, s = make_env(["g0:1 . #", ". 0:5 .", ". . g1:4"])
    mask = np.asarray(env.action_mask(s))
    assert mask.shape == (2, env.num_actions)

    def legal(p, r, c, d):
        return bool(mask[p, a(env, r, c, d)])

    # exactly one canonical pass action (action 0) is offered
    assert legal(0, 0, 0, PASS)
    passes = [
        legal(p, r, c, PASS) for p in range(2) for r in range(3) for c in range(3)
    ]
    assert sum(passes) == 2  # one per living player
    # a general with a single army cannot move
    assert not legal(0, 0, 0, RIGHT)
    # player 0's 5-army land can move in every direction
    assert all(legal(0, 1, 1, d) for d in (UP, DOWN, LEFT, RIGHT))
    # unowned tiles cannot move, even with armies on them
    assert not legal(0, 2, 0, DOWN)
    # player 1 can step off its 4-army general, but not onto the mountain
    assert legal(1, 2, 2, UP) and legal(1, 2, 2, LEFT)
    assert not legal(1, 2, 2, DOWN) and not legal(1, 2, 2, RIGHT)
    # ... and cannot enter the mountain at (0, 2)
    assert not legal(1, 1, 1, UP)


def test_action_mask_and_step_agree_on_random_policies():
    """Every masked-in action leads to a valid, advanced state."""
    env, s = make_env(
        ["g0:6 0:4 1:3 .", ". . . .", ". . . .", ". . . g1:6"]
    )
    mask = np.asarray(env.action_mask(s))
    acts = np.argwhere(mask)  # (k, 2) -> (player, action)
    counts = np.bincount(acts[:, 0], minlength=2)
    assert counts[0] > 3 and counts[1] > 3
    for p, action in acts[:40]:
        other = int(jax.random.categorical(
            jax.random.PRNGKey(int(action)), jnp.where(mask[1 - p], 0.0, -jnp.inf)))
        acts_pair = [0, 0]
        acts_pair[p] = int(action)
        acts_pair[1 - p] = other
        s2, _, _ = env.step(s, jnp.asarray(acts_pair, dtype=jnp.int32))
        assert 2 * int(s2.turn) + int(s2.half_turn) == (
            2 * int(s.turn) + int(s.half_turn) + 1
        )
        assert bool((np.asarray(s2.army) >= 0).all())
        assert bool((np.asarray(s2.owner) >= -2).all())
