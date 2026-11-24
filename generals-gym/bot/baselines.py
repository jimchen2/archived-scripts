"""A couple of cheap reference policies.

They are handy for smoke tests, benchmarks and as baselines to beat.  The
greedy bot is *fog-honest*: it only reasons about tiles ``player`` can
actually see (own tiles plus the 8-neighbour ring, or the whole board when
``cfg.fog`` is off).  It never uses the true location of the enemy general
unless that tile is visible, so it cannot cheat through the fog of war.
"""

from __future__ import annotations

import jax
import jax.numpy as jnp

from game.config import MOUNTAIN, NUM_PLAYERS, PASS, EnvConfig
from game.obs import visible_mask
from game.state import State
from game.tables import Tables


def greedy_action(state: State, player: int, cfg: EnvConfig, tables: Tables) -> jax.Array:
    """Pick the best-looking frontier move using only visible tiles.

    Every candidate is a full move (codes 1..4) from one of ``player``'s
    movable tiles to an adjacent tile.  Adjacent tiles are always visible
    under fog (own tiles plus the 8-neighbour ring), so the bot can see
    exactly what it is about to attack.  Scoring mirrors the browser
    ``normal`` heuristic:

    * visible neutral/enemy tile with ``attack > defence``: prefer taking
      land over moving armies around at home, with a bonus for castles and
      enemy territory;
    * own tile: a small, capped stacking score, well below a legal capture;
    * invisible tile: cheap probing with modest stacks. (With the current
      vision rule adjacent destinations are visible.)

    No general coordinates are consulted. If the enemy general becomes
    visible, it is simply another visible enemy tile; the game engine handles
    the win when it is captured.

    Moves into visible mountains, off the board, or into a visible
    defender that is not strictly weaker are illegal and never chosen.
    When nothing legal exists the canonical pass (0) is returned.
    """
    n = cfg.num_tiles
    army = state.army.reshape(n)
    owner = state.owner.reshape(n)
    city = state.city.reshape(n)

    if cfg.fog:
        vis = visible_mask(state, player, cfg).reshape(n)
    else:
        vis = jnp.ones((n,), dtype=bool)

    enemy = 1 - player

    movable = (owner == player) & (army > 1) & state.alive[player]  # (N,)

    # Full moves only: codes 1..4 (UP, DOWN, LEFT, RIGHT).  ``tables.dst``
    # is (dir_actions, N); slice the first four rows and transpose to (N, 4).
    dst = tables.dst[1:5].T  # (N, 4)
    dst_ok = dst >= 0
    dst_safe = jnp.maximum(dst, 0)

    vis_dst = vis[dst_safe]
    # Do not let hidden tile contents leak into even intermediate scores.
    # Adjacent destinations are visible with the current vision rule, but the
    # masking also keeps this policy safe if that rule changes later.
    owner_dst = jnp.where(vis_dst, owner[dst_safe], -1)  # (N, 4)
    army_dst = jnp.where(vis_dst, army[dst_safe], 0)
    city_dst = vis_dst & city[dst_safe]

    attack = (army - 1)[:, None]  # (N, 1), broadcast over the 4 dirs

    is_own = owner_dst == player
    is_mountain_vis = vis_dst & (owner_dst == MOUNTAIN)
    is_enemy = owner_dst == enemy
    defence = army_dst

    # A legal expansion/capture must beat local reinforcement, even when the
    # source stack is large.  Cap army-dependent terms to keep this ordering
    # stable over long games.
    capture_score = (
        20.0
        - 0.1 * jnp.minimum(defence, 30).astype(jnp.float32)
        - 0.02 * jnp.minimum(attack, 40).astype(jnp.float32)
    )
    capture_score = capture_score + jnp.where(city_dst, 260.0, 0.0)
    capture_score = capture_score + jnp.where(is_enemy, 18.0, 0.0)

    own_score = (
        0.5 + 0.1 * jnp.minimum(army_dst + attack, 12).astype(jnp.float32)
    )
    fog_score = jnp.where((attack >= 3) & (attack <= 12), 4.0, 0.4)

    score = jnp.where(
        ~vis_dst, fog_score, jnp.where(is_own, own_score, capture_score)
    )

    # Illegal: immovable source, off-board, visible mountain, or a visible
    # non-own tile that is not strictly weaker (would just feed it).
    illegal = (
        (~movable)[:, None]
        | (~dst_ok)
        | is_mountain_vis
        | (vis_dst & ~is_own & (owner_dst != MOUNTAIN) & (attack <= defence))
    )
    score = jnp.where(illegal, jnp.float32(-1e18), score)

    flat_score = score.reshape(-1)  # (N * 4,)
    best_idx = jnp.argmax(flat_score)
    best_score = flat_score[best_idx]
    src = best_idx // 4
    code = (best_idx % 4) + 1  # 1..4
    action = src * cfg.dir_actions + code
    return jnp.where(best_score > jnp.float32(-1e17), action, jnp.int32(PASS))


def greedy_actions(state: State, cfg: EnvConfig, tables: Tables) -> jax.Array:
    """``(2,)`` action array, one greedy action per player."""
    return jax.vmap(lambda p: greedy_action(state, p, cfg, tables))(
        jnp.arange(NUM_PLAYERS)
    )


def random_legal_actions(
    key: jax.Array, masks: jax.Array, cfg: EnvConfig
) -> jax.Array:
    """Uniformly sample legal actions from a ``(P, A)`` or ``(B, P, A)`` mask."""
    from game.engine import sample_actions, sample_actions_batch

    if masks.ndim == 2:
        return sample_actions(key, masks, cfg)
    return sample_actions_batch(key, masks, cfg)
