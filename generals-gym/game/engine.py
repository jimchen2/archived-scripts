"""The core 1v1 generals.io rules, written as pure JAX functions.

The rules implemented here follow the official generals.io engine (see
``RULES.md`` for the exact ordering and the edge cases):

* a move takes ``army - 1`` units out of the source tile (or ``army // 2`` with
  a half move) and leaves 1 unit behind,
* moving onto your own tile reinforces it,
* moving onto a neutral/enemy tile fights the defenders: the tile only changes
  hands if the attackers are *strictly* stronger, in which case the survivors
  are ``attack - defence``,
* a displayed turn contains two half-turns; each player submits one
  simultaneous action on each half-turn,
* all moves in a half-turn happen simultaneously: armies leave their source
  before any arrival is resolved, so moving out of a tile that is being
  attacked does not save it,
* generals and castles produce +1 army after each displayed turn, every owned
  tile produces +1 army every 25 displayed turns,
* capturing a general wins the game and converts the loser's land (armies
  halved) to the winner.

Every function is jit- and vmap-friendly: no Python loops over board tiles, no
data-dependent control flow.
"""

from __future__ import annotations

import jax
import jax.numpy as jnp

from .config import MOUNTAIN, NUM_PLAYERS, EnvConfig
from .maps import MapPool, generate_map
from .state import State
from .tables import Tables


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------
def reset(
    key: jax.Array,
    cfg: EnvConfig,
    tables: Tables,
    pool: MapPool | None = None,
) -> State:
    """Start a new game.

    Maps are generated on the fly, unless ``pool`` is given, in which case a
    random map is drawn from the pool (much cheaper on the hot path).
    """
    key, map_key, next_key = jax.random.split(key, 3)
    if pool is None:
        army, owner, city, general = generate_map(map_key, cfg, tables)
    else:
        # Any 32 random bits mod the pool size; cheap and unbiased enough.
        idx = jax.random.bits(map_key, (), dtype=jnp.uint32) % jnp.uint32(pool.size)
        idx = idx.astype(jnp.int32)
        army, owner, city, general = (
            pool.army[idx],
            pool.owner[idx],
            pool.city[idx],
            pool.general[idx],
        )
    return State(
        army=army.astype(jnp.int32),
        owner=owner.astype(jnp.int32),
        city=city,
        general=general,
        alive=jnp.ones((NUM_PLAYERS,), dtype=bool),
        turn=jnp.int32(0),
        half_turn=jnp.int32(0),
        winner=jnp.int32(-1),
        done=jnp.zeros((), dtype=bool),
        key=next_key,
    )


# ---------------------------------------------------------------------------
# step
# ---------------------------------------------------------------------------
def _info(state: State) -> dict:
    return {
        # ``turn`` is the visible/current turn number; half_turn identifies
        # which of its two simultaneous action slots is next.
        "turn": state.turn + state.half_turn,
        "half_turn": state.half_turn,
        "done": state.done,
        "winner": state.winner,
        "land": jnp.stack([jnp.sum(state.owner == p) for p in range(NUM_PLAYERS)]).astype(
            jnp.int32
        ),
        "army": jnp.stack(
            [jnp.sum(jnp.where(state.owner == p, state.army, 0)) for p in range(NUM_PLAYERS)]
        ).astype(jnp.int32),
    }


def step(state: State, actions: jax.Array, cfg: EnvConfig, tables: Tables):
    """Advance one half-turn (one action slot per player).

    Two calls to :func:`step` complete one displayed turn. Production and the
    displayed turn counter advance after the second call.

    Parameters
    ----------
    state:   current :class:`State`.
    actions: ``(2,)`` int32 array, one simultaneous action per player
             (``action = source_tile * dir_actions + direction``).

    Returns ``(new_state, rewards, info)`` where ``rewards`` is ``(2,)`` float32
    (only non-zero on the terminal transition) and ``info`` is a dict of
    per-transition diagnostics. ``info["turn"]`` is the current displayed turn
    number and ``info["half_turn"]`` is the next action slot (0 or 1).

    Illegal actions are silently treated as a pass, so the engine is total.
    """

    def _play(_):
        h, w = cfg.height, cfg.width
        n = cfg.num_tiles
        d_acts = cfg.dir_actions
        pids = jnp.arange(NUM_PLAYERS, dtype=jnp.int32)

        army = state.army.reshape(n)
        owner = state.owner.reshape(n)
        city = state.city.reshape(n)

        # --- decode actions -------------------------------------------------
        acts = jnp.clip(
            jnp.asarray(actions, dtype=jnp.int32).reshape(NUM_PLAYERS),
            0,
            cfg.num_actions - 1,
        )
        src = acts // d_acts
        code = acts % d_acts
        dst = tables.dst[code, src]          # (P,) -1 = off board / pass
        dst_ok = dst >= 0
        dst_safe = jnp.maximum(dst, 0)
        half = tables.half[code]

        src_army = army[src]
        src_owner = owner[src]
        dst_owner = owner[dst_safe]

        reserve = jnp.where(half, (src_army + 1) // 2, jnp.ones_like(src_army))
        can_move = (
            (src_owner == pids)
            & (src_army > 1)
            & dst_ok
            & (dst_owner != MOUNTAIN)
            & state.alive[pids]
        )
        moved = jnp.where(can_move, src_army - reserve, jnp.zeros_like(src_army))

        # --- 1. every army leaves its source simultaneously -----------------
        # ``add`` instead of ``set``: the two players may name the same source
        # tile (e.g. when one of them passes), and a scatter with duplicate
        # indices has unspecified ordering. ``moved`` is 0 for a non-move, so
        # additive updates are safe.
        army = army.at[src].add(-moved)

        # --- 2. reinforcements into own tiles -------------------------------
        to_own = can_move & (dst_owner == pids)
        army = army.at[dst_safe].add(jnp.where(to_own, moved, 0))

        # --- 3. attacks -----------------------------------------------------
        to_enemy = can_move & (dst_owner != pids)
        atk = jnp.stack(
            [
                jnp.zeros((n,), dtype=jnp.int32).at[dst_safe[p]].add(
                    jnp.where(to_enemy[p], moved[p], 0)
                )
                for p in range(NUM_PLAYERS)
            ]
        )  # (P, n)

        a0, a1 = atk[0], atk[1]
        hi = jnp.maximum(a0, a1)
        lo = jnp.minimum(a0, a1)
        hi_p = jnp.where(a0 >= a1, 0, 1).astype(jnp.int32)
        lo_p = 1 - hi_p
        # Two equally strong attackers wipe each other out; the tile is unharmed.
        clash = (a0 > 0) & (a0 == a1)

        defence = army                          # includes reinforcements
        hi_wins = hi > defence
        o1 = jnp.where(hi_wins, hi_p, owner)
        amt1 = jnp.where(hi_wins, hi - defence, defence - hi)
        o1 = jnp.where(clash, owner, o1)
        amt1 = jnp.where(clash, defence, amt1)

        lo_wins = lo > amt1
        o2 = jnp.where(lo_wins, lo_p, o1)
        amt2 = jnp.where(lo_wins, lo - amt1, amt1 - lo)
        o2 = jnp.where(clash, owner, o2)
        amt2 = jnp.where(clash, defence, amt2)

        new_owner = o2
        new_army = amt2

        # --- 4. generals ----------------------------------------------------
        g = state.general
        lost = jnp.stack(
            [new_owner[g[0]] != 0, new_owner[g[1]] != 1]
        ) & state.alive

        halved = jnp.floor(new_army * 0.5 + 0.5).astype(jnp.int32)
        only0 = lost[0] & ~lost[1]
        only1 = lost[1] & ~lost[0]
        take0 = only0 & (new_owner == 0)
        take1 = only1 & (new_owner == 1)
        new_owner = jnp.where(take0, 1, jnp.where(take1, 0, new_owner))
        new_army = jnp.where(take0 | take1, halved, new_army)

        tile_ids = jnp.arange(n)
        new_city = (
            city
            | ((tile_ids == g[0]) & lost[0])
            | ((tile_ids == g[1]) & lost[1])
        )

        # --- 5. turn boundary and production -------------------------------
        # Each call handles one half-turn. Production runs only after the
        # second action slot, once per displayed turn.
        turn_completed = state.half_turn == 1
        turn = state.turn + turn_completed.astype(jnp.int32)
        half_turn = jnp.int32(1) - state.half_turn
        owned = new_owner >= 0
        general_tiles = jnp.zeros((n,), dtype=bool).at[g].set(True)
        produces_each_turn = (
            turn_completed & owned & (new_city | general_tiles)
        )
        produced = new_army + produces_each_turn.astype(jnp.int32)
        land_growth = turn_completed & (turn % cfg.land_growth_period == 0)
        proposed = produced + (owned & land_growth).astype(jnp.int32)

        # --- 6. termination -------------------------------------------------
        # Only a general capture decides the game.  Reaching the turn limit
        # without one is a *double loss*: neither player wins, both get
        # reward 0 (see ``winner`` below), so running out the clock is never
        # preferable to attacking.
        dead = lost[0] | lost[1]
        time_up = turn_completed & (turn >= cfg.max_turns) & ~dead
        done = dead | time_up

        winner = jnp.where(
            lost[0] & ~lost[1],
            jnp.int32(1),
            jnp.where(lost[1] & ~lost[0], jnp.int32(0), jnp.int32(-1)),
        )

        new_state = State(
            army=jnp.where(done, new_army, proposed).reshape(h, w),
            owner=new_owner.reshape(h, w),
            city=new_city.reshape(h, w),
            general=g,
            alive=state.alive & ~lost,
            turn=turn,
            half_turn=half_turn,
            winner=winner,
            done=done,
            key=state.key,
        )
        rewards = jnp.stack(
            [
                jnp.where(winner == 0, 1.0, jnp.where(winner == 1, -1.0, 0.0)),
                jnp.where(winner == 1, 1.0, jnp.where(winner == 0, -1.0, 0.0)),
            ]
        )
        rewards = jnp.where(done, rewards, 0.0).astype(jnp.float32)
        return new_state, rewards, _info(new_state)

    def _noop(_):
        return state, jnp.zeros((NUM_PLAYERS,), dtype=jnp.float32), _info(state)

    return jax.lax.cond(state.done, _noop, _play, operand=None)


# ---------------------------------------------------------------------------
# action space helpers
# ---------------------------------------------------------------------------
def action_mask(state: State, cfg: EnvConfig, tables: Tables) -> jax.Array:
    """``(2, num_actions)`` boolean mask of legal actions per player."""
    n = cfg.num_tiles
    owner = state.owner.reshape(n)
    army = state.army.reshape(n)
    dst = tables.dst                                   # (dir_actions, n)
    dst_safe = jnp.maximum(dst, 0)
    tgt_owner = owner[dst_safe]
    base = (dst >= 0) & (tgt_owner != MOUNTAIN) & (army > 1)[None, :]

    # Only one of the n identical "pass" actions (action 0) is masked in; the
    # engine still treats *any* direction-0 action as a pass.
    owner_t = owner[:, None]
    base_t = base.T
    masks = []
    for p in range(NUM_PLAYERS):
        legal = base_t & (owner_t == p) & state.alive[p]  # (n, dir_actions)
        legal = legal.at[0, 0].set(state.alive[p])
        masks.append(legal.reshape(-1))
    return jnp.stack(masks)


def _searchsorted(rows, targets):
    return jax.vmap(lambda c, t: jnp.searchsorted(c, t, side="right"))(rows, targets)


def _pick(keys, mask):
    """Uniformly sample a ``True`` entry per row of a boolean ``(M, K)`` mask.

    One uniform draw per row plus a search in the cumulative mask, which is far
    cheaper than ``jax.random.categorical`` over a wide action space.
    """
    cdf = jnp.cumsum(mask.astype(jnp.int32), axis=-1)
    u = jax.vmap(lambda k: jax.random.uniform(k))(keys)
    total = jnp.maximum(cdf[:, -1], 1)
    target = jnp.minimum(jnp.floor(u * total).astype(jnp.int32), cdf[:, -1] - 1)
    return _searchsorted(cdf, target)  # side="right" skips runs of illegal actions


def _sample_rows(keys: jax.Array, mask: jax.Array, n: int, d: int) -> jax.Array:
    """Uniform sample over the legal entries of a ``(M, n*d)`` mask.

    The mask is laid out as ``src * d + dir``, so we sample a tile first (a
    cumsum over ``n`` entries) and then a direction (a cumsum over ``d``).
    Same uniform distribution over legal actions, ~4x less work than a single
    cumsum over the whole action space.
    """
    m = mask.reshape(mask.shape[0], n, d)
    tile_ok = m.any(axis=-1)
    k_tile, k_dir = jax.random.split(keys[0], 2)
    tile = _pick(jax.random.split(k_tile, mask.shape[0]), tile_ok)
    dirs = m[jnp.arange(m.shape[0]), tile]
    direction = _pick(jax.random.split(k_dir, mask.shape[0]), dirs)
    return tile * d + direction


def sample_actions(key: jax.Array, mask: jax.Array, cfg: EnvConfig) -> jax.Array:
    """Sample a legal action per player from a boolean mask ``(P, A)``."""
    keys = jax.random.split(key, mask.shape[0])
    return _sample_rows(keys, mask, cfg.num_tiles, cfg.dir_actions)


def sample_actions_batch(key: jax.Array, masks: jax.Array, cfg: EnvConfig) -> jax.Array:
    """Sample legal actions for a ``(B, P, A)`` mask; returns ``(B, P)``."""
    flat = masks.reshape(-1, masks.shape[-1])
    keys = jax.random.split(key, flat.shape[0])
    out = _sample_rows(keys, flat, cfg.num_tiles, cfg.dir_actions)
    return out.reshape(masks.shape[:-1])


def decode_action(action: int, cfg: EnvConfig) -> tuple[int, int]:
    """Convert a flat action index into ``(source_tile, direction_code)``."""
    return int(action) // cfg.dir_actions, int(action) % cfg.dir_actions


def encode_action(src: int, dir_code: int, cfg: EnvConfig) -> int:
    """Inverse of :func:`decode_action`."""
    return int(src) * cfg.dir_actions + int(dir_code)
