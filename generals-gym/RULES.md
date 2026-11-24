# Rules implemented by `game`

This is a 1v1 [generals.io](https://generals.io) simulator. The rules below match
the real game as closely as possible; anything that is approximated or
configurable is called out explicitly.

Terminology: a **tile** holds `army` units, belongs to `owner` (`0`, `1`, `-1` for
neutral, `-2` for a mountain) and may be a **castle** (city). Each player has one
**general**.

## Board and map

| thing | default | notes |
| --- | --- | --- |
| board | 21 × 21 | configurable (`EnvConfig(height=..., width=...)`) |
| mountains | ~20 % of tiles | impassable, never hold armies |
| castles | 10 | neutral, **40–50** armies, ≥ 3 tiles (Manhattan) from any general and ≥ 2 from each other |
| generals | 2 | ≥ 14 tiles apart when the board allows it, each starts with **1** army |
| turn limit | 1000 displayed turns | each displayed turn has two half-turn action slots; reaching the limit without a general capture is a **double loss** — nobody wins, both get reward 0 |

The map generator reproduces the terrain statistics of the web game
(~20 % mountains, 9–11 castles with 40–50 armies). On small boards the requested
general separation is automatically capped at what the board allows.

## Turns and moves

A displayed turn has **two half-turns**. On each half-turn, both players submit
exactly one action simultaneously, so each player gets up to **two moves per
displayed turn**. One call to `env.step` advances one half-turn; production and
the displayed turn counter advance after the second call. In the browser game,
the default 1-second turn therefore gives a move slot every 500 ms.

`action = source_tile * dir_actions + direction`, with
`direction ∈ {0 = pass, 1 = up, 2 = down, 3 = left, 4 = right}` and, when
`half_moves=True`, `5..8` = the same four directions using the "50 %" move.
Illegal actions are silently treated as a pass, so the engine is total.

Resolution order within each half-turn:

1. **Departure.** Every moving tile sends `army - 1` units (`army // 2` for a half
   move) and keeps exactly 1 (`ceil(army/2)` for a half move). A tile with a
   single army cannot move. All departures happen *before* any arrival, so
   abandoning a tile does not save it from an incoming attack.
2. **Reinforcement.** A move onto a tile you already own adds the moving armies
   to it. This happens before combat, so reinforcing a tile under attack helps.
3. **Combat**, per destination tile, against the defenders present after step 2:
   * the tile only changes hands if the attacking force is **strictly greater**
     than the defending armies; the survivors are `attack - defence`,
   * if the attack is equal or weaker, the tile keeps its owner and loses
     `attack` armies (possibly down to 0),
   * a neutral tile is defended by its armies (0 for plain land, 40–50 for an
     untouched castle),
   * if both players attack the same **neutral** tile with the same force, both
     attacking armies annihilate and the tile stays neutral with 0 armies,
   * if both players attack the same neutral tile with different forces, the
     stronger one takes the tile first and then fights the weaker one in the same
     half-turn (e.g. 12 vs 6 on an empty tile → the 12-army player ends up holding it
     with 6).
4. **General capture.** If a general's tile changes hands, the game ends
   immediately:
   * the capturing player wins (reward `+1`, the other player gets `-1`),
   * all of the loser's tiles become the winner's with their armies **halved**
     (rounded half up, as in the official replay engine),
   * the captured general tile becomes a castle,
   * if both generals fall in the same half-turn (possible only with mutual attacks)
     the game is a draw (`winner = -1`, rewards 0).
5. **Production.** After the second half-turn completes a displayed turn, each
   owned castle and each owned general gains **+1** army; every owned tile gains
   **+1** army every **25 displayed turns** (`land_growth_period`). Production
   does not run on the turn the game ends.
6. **Turn limit.** After `max_turns` displayed turns the game ends. There is **no
   tiebreak**: unless one general was captured, *both* players lose and both get reward
   `0` (`winner = -1`). Land and army totals are scoreboard information only — they never
   decide a game, so stalling cannot win.

Notes:

* Because each player submits one move per half-turn, a defended tile can only
  ever face one attacker in 1v1; the multi-attacker rules above matter for
  neutral tiles.
* Castles do not "regenerate" towards 40 armies (the pre-2018 behaviour).
* A player who loses their general loses even if they still own land.

## Action space

```
num_actions = height * width * dir_actions          # dir_actions = 5, or 9 with half moves
```

`env.action_mask(state)` returns a `(2, num_actions)` boolean mask. Exactly one
pass action is offered (action `0`, i.e. pass from tile 0); the engine also
accepts any other direction-0 action as a pass, but masks it out.

## Observations

`env.observe(state, player)` returns

* `grid`: `(10, H, W)` float32 with channels
  `visible, own_land, own_army, enemy_land, enemy_army, neutral_castle, mountain,
  own_general, enemy_general, own_castle`,
* `scalars`: `(7,)` float32 with
  `turn/max_turns, own_land, enemy_land, own_army, enemy_army, own_castles, done`,
  scaled to roughly `[0, 1]`. The turn fraction includes progress through the
  current half-turn.

With `fog=True` a player sees its own tiles and the **8-neighbourhood** ring
around them; unseen plain/enemy tiles are zeroed out, while mountains and
castles outside vision appear as obstacles on the `mountain` channel (just like
in generals.io, without revealing whether an unseen obstacle is a mountain or a
castle). Land and army totals of both players are always visible (like the
in-game scoreboard); the enemy general and its land are not.

## Rewards

`step` advances one half-turn and returns `(state, rewards, info)` with
`rewards` of shape `(2,)`:
`+1` for the winner, `-1` for the loser, `0` on every non-terminal transition and
on draws. No reward shaping is applied — add your own on top of `info`.

## Data types and determinism

Armies are `int32`, ownership is `int32` (`-2` mountain, `-1` neutral, `0/1`
players). Maps are a pure function of the reset key, so every episode is
reproducible from its key. Games are symmetric: with identical policies the two
seats win equally often (measured: 47–51 % for the greedy bot over thousands of
games).
