"""A deliberately naive, loop-based implementation of the same rules.

It exists purely so the vectorised JAX engine can be differentially tested
against an implementation that is easy to read and obviously correct.

Do not use this in training loops: it is slow on purpose.
"""

from __future__ import annotations

import numpy as np

from game.config import MOUNTAIN, NEUTRAL, EnvConfig

DELTA = {1: (-1, 0), 2: (1, 0), 3: (0, -1), 4: (0, 1)}


class RefGame:
    def __init__(self, army, owner, city, general, cfg: EnvConfig, turn=0):
        self.cfg = cfg
        self.army = np.array(army, dtype=np.int64).copy()
        self.owner = np.array(owner, dtype=np.int64).copy()
        self.city = np.array(city, dtype=bool).copy()
        self.general = list(np.asarray(general, dtype=int))
        self.alive = [True, True]
        self.turn = int(turn)
        self.half_turn = 0
        self.done = False
        self.winner = -1
        self.h, self.w = self.owner.shape

    # -------------------------------------------------------------- helpers
    def flat(self, r, c):
        return r * self.w + c

    def rc(self, idx):
        return divmod(int(idx), self.w)

    def neighbors(self, idx):
        r, c = self.rc(idx)
        for d, (dr, dc) in DELTA.items():
            rr, cc = r + dr, c + dc
            if 0 <= rr < self.h and 0 <= cc < self.w:
                yield d, self.flat(rr, cc)

    def action_mask(self, player):
        mask = np.zeros((self.h * self.w * self.cfg.dir_actions), dtype=bool)
        # one canonical pass action: tile 0, direction 0
        mask[0] = self.alive[player]
        for idx in range(self.h * self.w):
            r, c = self.rc(idx)
            for d in range(self.cfg.dir_actions):
                act = idx * self.cfg.dir_actions + d
                if d == 0:
                    continue  # pass is only offered as action 0
                if not self.alive[player]:
                    continue
                if self.owner[r, c] != player or self.army[r, c] <= 1:
                    continue
                base = d if d <= 4 else d - 4
                dr, dc = DELTA[base]
                rr, cc = r + dr, c + dc
                if not (0 <= rr < self.h and 0 <= cc < self.w):
                    continue
                if self.owner[rr, cc] == MOUNTAIN:
                    continue
                mask[act] = True
        return mask

    def legal_actions(self, player):
        return np.flatnonzero(self.action_mask(player))

    # ----------------------------------------------------------------- step
    def step(self, actions):
        """``actions``: two flat action indices. Returns (reward, done)."""
        assert not self.done
        cfg = self.cfg
        moves = []
        for p, act in enumerate(actions):
            src, code = divmod(int(act), cfg.dir_actions)
            moved = 0
            dst = -1
            valid = False
            reserve = 1
            if code != 0 and self.owner.flat[src] == p and self.army.flat[src] > 1:
                base = code if code <= 4 else code - 4
                dr, dc = DELTA[base]
                r, c = self.rc(src)
                rr, cc = r + dr, c + dc
                if 0 <= rr < self.h and 0 <= cc < self.w:
                    cand = self.flat(rr, cc)
                    if self.owner.flat[cand] != MOUNTAIN:
                        dst = cand
                        valid = True
                        half = code > 4
                        reserve = int(np.ceil(self.army.flat[src] / 2)) if half else 1
                        moved = int(self.army.flat[src]) - reserve
            moves.append(dict(p=p, src=src, dst=dst, moved=moved, valid=valid, reserve=reserve))

        owner_before = self.owner.flat.copy()

        # 1. departures (simultaneous)
        for mv in moves:
            if mv["valid"]:
                self.army.flat[mv["src"]] = mv["reserve"]

        # 2. reinforcements into own tiles
        for mv in moves:
            if mv["valid"] and owner_before[mv["dst"]] == mv["p"]:
                self.army.flat[mv["dst"]] += mv["moved"]

        # 3. attacks
        attacks = {}
        for mv in moves:
            if mv["valid"] and owner_before[mv["dst"]] != mv["p"]:
                attacks.setdefault(mv["dst"], []).append((mv["p"], mv["moved"]))

        for dst, lst in attacks.items():
            self._resolve(dst, lst)

        # 4. general captures
        lost = [
            self.owner.flat[self.general[p]] != p if self.alive[p] else False
            for p in range(2)
        ]
        if lost[0] and not lost[1]:
            self._transfer_land(0, 1)
        elif lost[1] and not lost[0]:
            self._transfer_land(1, 0)
        for p in range(2):
            if lost[p]:
                self.alive[p] = False
                self.city.flat[self.general[p]] = True

        # 5. displayed-turn boundary and production
        completes_turn = self.half_turn == 1
        self.half_turn = 1 - self.half_turn
        if completes_turn:
            self.turn += 1
        dead = lost[0] or lost[1]
        time_up = completes_turn and self.turn >= cfg.max_turns and not dead
        self.done = bool(dead or time_up)
        if completes_turn and not self.done:
            owned = self.owner >= 0
            gen_mask = np.zeros((self.h, self.w), dtype=bool)
            for p in range(2):
                if self.alive[p]:
                    gen_mask.flat[self.general[p]] = True
            produced = (owned & (self.city | gen_mask)).astype(np.int64)
            self.army += produced
            if self.turn % cfg.land_growth_period == 0:
                self.army += owned.astype(np.int64)

        if lost[0] and not lost[1]:
            self.winner = 1
        elif lost[1] and not lost[0]:
            self.winner = 0
        else:
            # Truncation without a capture is a double loss; exact same
            # draw/no-winner behaviour as a mutual general capture.
            self.winner = -1
        rewards = [0.0, 0.0]
        if self.done:
            if self.winner == 0:
                rewards = [1.0, -1.0]
            elif self.winner == 1:
                rewards = [-1.0, 1.0]
        return np.array(rewards, dtype=np.float32), self.done

    # -------------------------------------------------------------- battles
    def _resolve(self, dst, lst):
        """lst: [(player, amount), ...] incoming attack forces at tile ``dst``."""
        defence = int(self.army.flat[dst])
        owner = int(self.owner.flat[dst])

        if len(lst) == 2 and lst[0][1] == lst[1][1] and lst[0][1] > 0:
            # two equal attackers destroy each other, the tile is untouched
            return

        lst = sorted(lst, key=lambda pa: -pa[1])
        for p, amount in lst:
            if amount <= 0:
                continue
            if amount > defence:
                owner = p
                defence = amount - defence
            else:
                defence = defence - amount
        self.owner.flat[dst] = owner
        self.army.flat[dst] = defence

    def _transfer_land(self, loser, winner):
        mask = self.owner == loser
        self.army[mask] = np.floor(self.army[mask] * 0.5 + 0.5).astype(np.int64)
        self.owner[mask] = winner


def make_random_game(rng: np.random.Generator, h=6, w=6, half_moves=False, turn=0):
    """Build a small, valid, random position (mountains, cities, two generals)."""
    cfg = EnvConfig(
        height=h,
        width=w,
        half_moves=half_moves,
        city_count=2,
        city_min_army=3,
        city_max_army=9,
        general_min_dist=1,
        city_general_min_dist=1,
        city_city_min_dist=1,
        mountain_frac=0.15,
        land_growth_period=3,
        max_turns=40,
    )
    owner = np.full((h, w), NEUTRAL, dtype=np.int64)
    army = np.zeros((h, w), dtype=np.int64)

    mountains = rng.random((h, w)) < 0.15
    owner[mountains] = MOUNTAIN

    free = [(r, c) for r in range(h) for c in range(w) if not mountains[r, c]]
    rng.shuffle(free)
    g0 = free[0]
    g1 = free[1]
    owner[g0] = 0
    owner[g1] = 1
    army[g0] = rng.integers(1, 6)
    army[g1] = rng.integers(1, 6)
    free = [t for t in free[2:]]

    city = np.zeros((h, w), dtype=bool)
    for _ in range(min(2, len(free))):
        r, c = free.pop()
        city[r, c] = True
        army[r, c] = rng.integers(3, 10)

    for r, c in free:
        u = rng.random()
        if u < 0.25:
            owner[r, c] = 0
            army[r, c] = rng.integers(1, 12)
        elif u < 0.5:
            owner[r, c] = 1
            army[r, c] = rng.integers(1, 12)
        elif u < 0.7:
            army[r, c] = rng.integers(0, 4)

    return cfg, RefGame(
        army,
        owner,
        city,
        [g0[0] * w + g0[1], g1[0] * w + g1[1]],
        cfg,
        turn=turn,
    )
