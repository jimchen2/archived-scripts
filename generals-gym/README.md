# generals-gym

A fast, fully vectorised **JAX simulator for 1v1 [generals.io](https://generals.io)**
plus a **PPO self-play agent** that learns to play it.

```
game/   the simulator: rules, maps, fog of war, observations, rendering
bot/    the agent:     SE-ResNet + ConvGRU policy/value network, PPO, checkpoints
src/    the trainer:  rollout collection, training loop, evaluation, play script
```

Everything is a pure function of its inputs, so the whole game – map
generation, movement, combat, production, auto-reset – runs inside
`jax.jit` / `jax.vmap` / `jax.lax.scan` with no Python loops and no
host round-trips. Throughput on a **2-core CPU**: **~260k game-steps/s**
for 1024 parallel 21×21 games, **~850k/s** on 11×11 boards, ~15 µs for a
single environment step.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[test]"

# 1. watch a random game
python examples/play_game.py --size 9 --every 10 --fog

# 2. train the agent (smoke preset: tiny board, a few seconds per update on CPU)
python -m src.train --preset smoke --total-updates 5

# 3. train the full architecture from the README (GPU recommended)
python -m src.train --preset default --total-updates 2000

# 4. evaluate the newest checkpoint against the fog-honest greedy baseline
python -m src.evaluate --run-dir runs/default --games 128

# 5. watch the agent play
python -m src.play --run-dir runs/default --opponent greedy --every 5

# 6. ... or save a replay and video
python -m src.play --run-dir runs/default --opponent greedy \
    --save-replay replays/game.json --video replays/game.mp4
```

## Play it in the browser

```bash
pip install -e .
python -m generals_web            # or: generals-web
# -> http://localhost:8000
```

A live 1v1 game against a bot with the real engine behind it: canvas-rendered
board, castles, fog and a **one-second turn clock** (2s / 1s / 0.5s / 0.25s).
Each displayed turn has two moves, one every half-turn (500ms apart at the
default speed). **W A S D or the arrow keys** send the selected tile's army one
square and move the selection along, so tapping a direction queues a path — just
generals.io. `Z` splits the stack, `Space` deselects, `Q` clears the queue,
`P` pauses, `N` starts a new game; clicking a tile selects it and clicking an
adjacent tile moves.

Owned land grows +1 army every **25 displayed turns** (the classic rule, fixed),
boards run 11×11 → 25×25, fog of war is a toggle, and the opponent can be a
random mover or a fog-honest greedy bot. To play against a
trained checkpoint, start the server with a run directory and checkpoint tag:

```bash
python -m generals_web --run-dir runs/default --checkpoint latest
```

Select **Trained checkpoint** in the opponent menu. See the
[checkpoint instructions](generals_web/README.md#play-against-a-trained-checkpoint)
for downloading the example 15×15 checkpoint from Hugging Face and for the JSON API.

## What you get

| feature | |
| --- | --- |
| 1v1 generals.io rules | movement, splitting, combat, castles, general capture (land absorbed at half armies), +1/turn on castles & generals, +1/25 turns on land — see [`RULES.md`](RULES.md) |
| random maps | generals.io-style terrain: ~20 % mountains, 10 castles with 40–50 armies, generals far apart, generated inside `jit` |
| simultaneous turns | each displayed turn has two half-turns; both players choose one action per half-turn (`source_tile * 5 + dir`), plus the "50 %" move variants |
| action masking | `env.action_mask(state) -> (2, num_actions)` |
| fog of war | observation tensors with visibility, own/enemy land & armies, castles, general positions |
| batching | `env.reset_batch(keys)`, `env.step_batch(states, actions)` with automatic per-env reset |
| fast sampling | uniform sampling over *legal* actions without a giant categorical draw |
| baselines | a fog-honest greedy bot and a random-legal bot for smoke tests (`bot.baselines`) |
| browser UI | `python -m generals_web` — canvas board, WASD/arrow keys, fog, 1 s turns, three bot difficulties (`generals_web/`) |

## Rules in one paragraph

Each displayed turn has two half-turns; on each one both players choose a move
simultaneously. A move sends all but one army from a tile to a neighbouring tile
(1 army stays home). Moving onto your own land reinforces it; moving onto neutral
land or an enemy fights: the tile only changes hands if the attack is *strictly*
stronger, and the survivors are `attack - defence`. Armies leave their source
before arrivals are resolved. After each full turn, every owned castle and
general gains +1 army; every owned tile gains +1 army every 25 full turns.
Capturing the enemy general wins the game and converts all of the loser's land
(armies halved). Full details, including the exact ordering, are in
[`RULES.md`](RULES.md).

Every run writes ``runs/<name>/metrics.csv``, ``config.json`` and
``checkpoints/`` (``latest.json`` points at the newest checkpoint).  Add
``--save-replay-every N`` and every N updates one game is recorded to
``runs/<name>/replays/step_XXXXXX.json`` — pass ``--replay-video`` to render an
MP4 next to it as well.

## Replays and videos

Instead of printing every board to the terminal, record the game and watch it
later — as an MP4, a GIF, or a scrubbable HTML page:

```bash
# 1. play a game and record every half-turn (agent vs greedy / random / another checkpoint)
python -m src.play --run-dir runs/default --opponent greedy \
    --save-replay replays/game.json --video replays/game.mp4

# 2. or render a saved replay afterwards, at whatever speed you like
python -m src.video replays/game.json -o replays/game.mp4 --view all --fps 15
python -m src.video replays/game.json -o replays/game.gif --cell 22   # no ffmpeg needed

# 3. or turn it into a single self-contained HTML player (no server, no deps)
python -c "from game.replay import Replay; from game.replay_html import write_html_player; \
           write_html_player(Replay.load('replays/game.json'), 'replays/game.html')"

# baseline-vs-baseline games work too
python -m examples.play_game --size 15 --quiet \
    --save-replay replays/bots.json --video replays/bots.mp4
```

The renderer draws the same board as the [browser client](#play-it-in-the-browser)
(rounded tiles, castles, general stars, fog, live army counters) plus a
land-share scoreboard, the turn counter, white flashes on tiles that just
changed, the last move of each player as an arrow, and an end card with the
result.  `--view seat0|seat1|all` picks the camera: one seat's fogged view, or
the omniscient board.

Install the video dependencies with `pip install -e ".[video]"`. MP4 output needs
`ffmpeg` on `PATH` or the bundled binary from `imageio-ffmpeg`; choose a `.gif`
output for an animated GIF using Pillow only. Recording a replay or video suppresses
turn-by-turn printing by default; use `--every N` to also print boards.

### The replay file

`game/replay.py` writes a plain JSON document (`"format": "generals-gym-replay"`)
that stores the board after *every half-turn*, run-length encoded: owner, armies,
castles and the two general positions, plus each player's move, the reward and
(for agent games) the value / entropy of the step. It is self-describing (board
size, fog, turn cadence, action configuration, player names, training metadata)
so it renders without the checkpoint
that produced it:

```python
from game.replay import Replay, ReplayRecorder
from src.video import VideoOptions, render_replay

replay = Replay.load("replays/game.json")
replay.result          # {'winner': 0, 'turns': 214, 'reason': 'general captured'}
replay.frame_owner(10) # (H, W) int32 board, -2 mountain, -1 neutral, 0 / 1 players
replay.visible(10, 0)  # (H, W) bool fog mask for seat 0
render_replay(replay, "replays/game.mp4", VideoOptions(view="seat1"))
```

**In the browser** every live game is recorded too: the ⤓ button in the
top bar (and *Save replay* on the game-over card) downloads the game as the same
single-file HTML player. Replay files contain the complete board, including hidden
tiles, even when the game uses fog. `GET /api/games/<id>/replay` /
`GET /api/games/<id>/replay.html` return the raw JSON / the player.

## The environment (`game/`)

```python
import jax
from game import GeneralsEnv

env = GeneralsEnv()                                # 21x21, fog of war, 1v1
state = env.reset(jax.random.PRNGKey(0))           # a fresh random map
mask = env.action_mask(state)                      # (2, 2205) legal actions
actions = env.sample_actions(jax.random.PRNGKey(1), state)
state, rewards, info = env.step(state, actions)    # one simultaneous half-turn
obs = env.observe(state, player=0)                 # fogged (10, 21, 21) tensor
```

| call | returns |
| --- | --- |
| `env.reset(key)` | `State` |
| `env.step(state, actions)` | one half-turn; two calls complete a displayed turn; rewards only at game end |
| `env.step(state, actions, auto_reset=True)` | same, but a finished game restarts immediately |
| `env.action_mask(state)` | `(2, num_actions)` bool |
| `env.sample_actions(key, state)` | `(2,)` uniform legal action per player |
| `env.observe(state, p)` / `env.observations(state)` | observations for one / both players |
| `env.reset_batch(keys)` / `env.step_batch(states, actions)` | vmapped versions (`actions` is `(B, 2)`) |
| `env.observations_batch(states)` | `(B, 2, C, H, W)` grids and `(B, 2, S)` scalars |
| `env.make_state(rows)` | build an explicit board from ASCII |

`State` is a `NamedTuple` of jnp arrays: `army (H,W)`, `owner (H,W)`
(`-2` mountain, `-1` neutral, `0/1`), `city (H,W)` bool, `general (2,)`,
`alive (2,)`, `turn` (completed displayed turns), `half_turn` (next slot: 0 or 1),
`winner`, `done`, `key`. `info` holds the current displayed `turn`, `half_turn`,
`done`, `winner`, `land (2,)`, and `army (2,)`.

**Observations.** `grid` has 10 channels: `visible, own_land, own_army,
enemy_land, enemy_army, neutral_castle, mountain, own_general, enemy_general,
own_castle`. `scalars` has 7: `turn/max_turns, own_land, enemy_land,
own_army, enemy_army, own_castles, done`. Under fog a player sees its own
tiles plus the 8-neighbour ring; army and land totals of both players stay
public, as on the scoreboard.

**Explicit boards** (tests, puzzles, fixed maps):

```python
env = GeneralsEnv(EnvConfig(height=3, width=4))
state = env.make_state([
    "g0:5 . # C:41",
    "c1:3 0:12 -1:7 .",
    "g1:2 . . .",
])
```

`#` mountain, `.` neutral, `C[:army]` neutral castle, `c<owner>:<army>` owned
castle, `g<player>[:army]` general, `<owner>:<army>` land.

Full rules and the exact turn ordering are in
[`RULES.md`](RULES.md).

## The agent (`bot/`)

The network is the architecture described in the project brief, implemented
in pure JAX (no Flax/optax dependency).

### 1. Input encoding

The 10-channel fogged board and the 7 scalars are concatenated into a
`(17, H, W)` tensor: each scalar is broadcast to `(H, W)` and stacked as an
extra channel. Two optional normalised row/column planes can be appended
with `use_coords=True` (off by default, so the default input is exactly
`(17, 21, 21)`).

Because the backbone's LayerNorm normalises over the whole feature map, a
constant scalar plane can be normalised away. The scalars are therefore also
**concatenated directly into both heads** (broadcast spatially for the policy
head, appended to the pooled vector for the value head), so global state
always reaches the decision layers.

### 2. Backbone: SE-ResNet + global context

```
x ── 3x3 conv ── LayerNorm ── SiLU ──┐
                                     │
   ┌─────────────────────────────────┘
   │  residual block (× num_blocks)
   │    h = SiLU(LN(conv3x3(x)))
   │    h =      LN(conv3x3(h))
   │    h =      SE(h)                 # channel gate from global average pool
   │    x = SiLU(x + h)
   │    [every global_context_every blocks]
   │      g = MLP(GAP(x))              # board-level summary
   │      x = conv1x1(concat([x, broadcast(g)]))
   └──► features (C, H, W)
```

* 3×3 convolutions with **LayerNorm** (not BatchNorm) so statistics do not
  depend on the batch dimension – important under PPO and inside `lax.scan`.
* **Squeeze-and-Excitation** in every block: global pooling produces a
  channel gate, giving each local filter a view of the whole board.
* **Global context** every `k` blocks: the pooled vector is concatenated
  back onto the spatial map and projected with a 1×1 convolution, the
  KataGo / Lux AI trick for letting a 3×3 receptive field plan globally.

### 3. Memory for fog of war

| `memory` | what it does |
| --- | --- |
| `"gru"` (default) | a **ConvGRU** after the backbone; memory stays spatial `(C_mem, H, W)`, so the agent can remember where it last saw enemy castles/borders |
| `"stack"` | frame-stack the last `stack_frames` observations along channels (fast, stateless, short-term memory) |
| `"none"` | feed-forward policy (memoryless) |

Memory is carried through `lax.scan` and **zeroed at episode boundaries**
(which matches the simulator's `auto_reset`). During PPO updates the memory
is recomputed from the stored observations for every epoch, so the replay
buffer never has to store hidden states.

### 4. Heads

* **Policy head (fully convolutional):** 1×1 conv → LayerNorm → SiLU, with
  the broadcast scalars concatenated, then a 1×1 conv producing
  `(dir_actions, H, W)`. The map is transposed to
  `(H, W, dir_actions)` and flattened to `(H·W·dir_actions,)`, which is
  exactly the simulator's `action = tile * dir_actions + direction` layout.
  Illegal actions get `-1e9` before the softmax, so the agent can only pick
  legal moves (and always has the pass action available).
* **Value head:** global average pool, concatenated with the scalars →
  LayerNorm → 2-layer MLP → scalar `V(s)`.

```python
from bot import NetConfig, PolicyValueNet

net = PolicyValueNet(NetConfig(channels=64, num_blocks=6, memory="gru"),
                     grid_channels=10, num_scalars=7, height=21, width=21)
params = net.init(jax.random.PRNGKey(0))
out = net.step(params, obs.grid, obs.scalars, mask, net.initial_memory(),
               key=jax.random.PRNGKey(1))
out.action, out.log_prob, out.value, out.entropy
```

`NetConfig` fields: `channels`, `num_blocks`, `use_se`, `se_ratio`,
`global_context_every`, `memory`, `memory_channels`, `stack_frames`,
`use_coords`, `dir_actions`.

## Training (`src/`)

### PPO with shared-parameter self-play

The trainer controls **both seats with the same network**, so every
environment step yields two training samples (one per player's fogged view).
The rollout runs `num_envs` games in lockstep inside a single `lax.scan`;
finished games auto-reset, and the memory is cleared at the boundary.

A useful curriculum is `--train-opponent random` (learn to expand and capture
a passive opponent) followed by `--train-opponent self` (the default), where
both seats are trained.

#### Historical opponent pool

Use `--train-opponent pool` to train seat 0 against frozen historical versions
of the policy. The pool starts with the initial policy and adds a snapshot
*after* every `--opponent-snapshot-every` updates (default 25). It retains the
newest `--opponent-pool-size` snapshots (default 8, FIFO). Each new game
samples uniformly from the pool; its opponent and recurrent memory stay with it
until the game ends, even if that snapshot is evicted. Only seat 0 contributes
PPO samples. Pool mode keeps one copy of opponent parameters per environment,
so it uses more memory than shared self-play. Evaluation remains against the
selected random or greedy baseline.

```bash
python -m src.train --preset small --train-opponent pool \
    --opponent-pool-size 8 --opponent-snapshot-every 25 --out runs/pool
python -m src.train --resume --out runs/pool --total-updates 2000
```

Each pool-mode checkpoint has a `pool_<tag>.npz` companion containing its
snapshots; keep these files together when moving or resuming a run. Resuming
restores the pool but, like other modes, starts fresh games and optimizer state.
Switching an existing non-pool run to pool mode seeds it from the resumed
policy; changing pool size on resume retains the newest snapshots that fit.

```python
states = env.reset_batch(keys)
memory = net.batched_initial_memory((num_envs, 2))

for update in range(total_updates):
    traj, states, memory, last_values = collect(states, memory, key)
    batch = make_batch(traj, last_values, ppo_cfg)   # GAE + flatten (T, B*P)
    train_state, metrics = ppo_update(train_state, batch)
```

PPO details (`bot/ppo.py`):

* **GAE** (`γ`, `λ`) with per-trajectory bootstrapping from `last_values`.
* **Clipped surrogate** policy loss, **clipped value loss**, **entropy bonus**.
* Advantages normalised per minibatch.
* **AdamW** implemented in pure JAX, global-gradient-norm clipping, and
  learning-rate scheduling (`linear`, `cosine`, or `constant`, with optional
  linear warmup) starting from `--lr` (default `3e-4`).
* Minibatches are drawn along the trajectory axis only; each minibatch keeps
  its full `T`-step sequence so ConvGRU/frame-stack memories are exact.
* **Gradient checkpointing** (`remat`) is on for the `default` preset: BPTT
  through a 32-step scan would otherwise save every layer's activations for
  every timestep.  It is off for `smoke`/`small` (small nets, faster); use
  `--no-remat` to disable it anywhere.

### Reward shaping

A generals.io game only rewards the final general capture, which is far too
sparse for PPO on a 21×21 board. The collector adds **potential-based
shaping**:

```
F(s, s') = shaping_coef * (phi(s') - phi(s)) * (1 - done)

phi(s) = land(s)/num_tiles
       + 0.5 * log1p(army(s)) / log1p(army_norm * num_tiles)
       - general_distance_coef * dist_to_enemy_general(s) / (H + W)
```

The first two terms reward expansion and army growth. The third rewards
moving territory toward the enemy general; it uses the simulator's omniscient
general position, which the agent cannot see under fog of war. That is
*privileged reward shaping* – legal in the reward, and a standard trick for
partially observed games.

Because it is the difference of a state potential, it does not change the
optimal policy (for γ < 1) but gives a dense learning signal. Set `--shaping 0`
for the pure game reward, or `--distance-shaping 0` to drop the distance term.

### Presets and command line

| preset | board | network | envs × steps | epochs × minibatches | use |
| --- | --- | --- | --- | --- | --- |
| `smoke` | 9×9 | 16 ch × 2 blocks, no memory | 8 × 8 | 2 × 2 | plumbing check, seconds/update on CPU |
| `small` | 11×11 | 32 ch × 3 blocks, ConvGRU | 16 × 16 | 3 × 4 | realistic CPU run |
| `default` | 21×21 | 64 ch × 6 blocks, SE + context, ConvGRU | 64 × 32 | 4 × 4 | the full architecture, GPU recommended |

```bash
python -m src.train --preset default \
    --total-updates 2000 --num-envs 128 --rollout-len 32 \
    --channels 128 --blocks 8 --memory gru \
    --lr 3e-4 --shaping 0.5 --out runs/exp1

# resume the newest checkpoint in a run directory
python -m src.train --resume --out runs/exp1 --total-updates 4000
```

Useful flags: `--train-opponent {self,random,greedy,pool}`, `--opponent-pool-size`,
`--opponent-snapshot-every`, `--size`,
`--max-turns`, `--memory {none,gru,stack}`,
`--channels`, `--blocks`, `--num-envs`, `--rollout-len`, `--epochs`,
`--minibatches`, `--lr`, `--lr-end`, `--lr-schedule {linear,cosine,constant}`,
`--lr-warmup-updates`, `--weight-decay`, `--gamma`, `--shaping`,
`--distance-shaping`, `--ent-coef`, `--eval-every`, `--checkpoint-every`,
`--eval-games`, `--eval-opponent {greedy,random}`, `--no-remat`, `--resume`,
`--seed`, `--out`.

`metrics.csv` contains, per update: `lr`, `loss`, `policy_loss`, `value_loss`,
`entropy`, `approx_kl`, `clip_frac`, `grad_norm`, `episodes`,
`mean_length`, `win_rate_p0/p1`, `sps`, and (when evaluated)
`eval_win_rate`, `eval_loss_rate`, `eval_draw_rate`, `eval_mean_length`.

### Training tips

* **Start with `--train-opponent random`.** It is a much easier curriculum:
  the agent learns to expand and capture a passive opponent in a few hundred
  updates on CPU. Then switch to `self` (the default) for self-play.
* **Scale the batch, not just the learning rate.** PPO on a 21×21 board needs
  thousands of samples per update; `--num-envs 128 --rollout-len 32` is a
  good GPU starting point.
* **Watch `approx_kl` and `clip_frac`.** A healthy run has
  `approx_kl ~ 0.01-0.05` and `clip_frac ~ 0.1-0.3`. If the KL is ~1e-5, the
  policy is barely moving: raise `--lr`, add `--epochs`, or use a larger
  batch.
* **Entropy is masked entropy**, so it naturally grows as the agent acquires
  more legal actions; it is not a direct measure of exploration.
* **Evaluation is noisy** with few games: use `--games 128` or more for a
  stable win rate.
* **CPU vs GPU**: `smoke` and `small` run on CPU; `default` is intended for a
  GPU (the 21×21, 64-channel backbone is ~100× more compute than `smoke`).

### Checkpoints

Checkpoints are plain `.npz` files with a JSON sidecar:

```
runs/default/checkpoints/step_000050.npz
runs/default/checkpoints/step_000050.json   # config + metadata
runs/default/checkpoints/latest.json
```

```python
from bot.checkpoint import Checkpoint
ckpt = Checkpoint("runs/default")
arrays, payload = ckpt.load("latest")
params = ckpt.restore(arrays, net.init(jax.random.PRNGKey(0)))
```

## Evaluation and play

```bash
# agent (seat 0) vs the fog-honest greedy / random bot (seat 1)
python -m src.evaluate --run-dir runs/default --opponent greedy --games 128

# print the board from the agent's fogged point of view
python -m src.play --run-dir runs/default --opponent greedy --every 5
python -m src.play --run-dir runs/default --show-all      # omniscient view
```

The `greedy` baseline respects fog of war. It only scores visible neighboring
tiles and never reads the hidden enemy-general location; capturing the general
is handled naturally by the game rules once it becomes visible.

## Layout

```
game/                the simulator (was `generals_jax`)
  config.py          static env config + tile/action constants
  tables.py          neighbour / distance lookup tables
  maps.py            JAX map generation, map pool, ASCII parser
  engine.py          reset / step / action mask / legal sampling
  state.py           State NamedTuple and score helpers
  obs.py             fog-of-war observation tensors
  render.py          ASCII renderer
  replay.py          replay recording / loading (JSON, run-length encoded)
  replay_html.py     single-file HTML replay player
  env.py             GeneralsEnv: jitted, vmapped, auto-reset wrapper
bot/                 the agent
  nn.py              conv / dense / LayerNorm / SE / ConvGRU layers
  network.py         PolicyValueNet: SE-ResNet + context + memory + heads
  ppo.py             GAE, clipped PPO loss, AdamW, scan-based update
  checkpoint.py      .npz checkpoints + JSON config
  baselines.py       fog-honest greedy + random-legal policies
src/                 training entrypoints (python -m src.<module>)
  config.py          TrainConfig, presets, CLI mapping
  rollout.py         trajectory collection + reward shaping
  train.py           PPO self-play training loop
  evaluate.py        evaluation against the reference bots
  play.py            watch a checkpoint play, with --save-replay / --video
  video.py           render a replay to MP4 / GIF (Pillow + ffmpeg)
  replay_tools.py    record a game with a checkpoint (used by src.train)
  logger.py          CSV/JSON logging
tests/               simulator + network + PPO + replays + web, end to end
examples/            terminal game, batched rollout loop
benchmarks/          throughput sweep
```

## Performance

Simulator, 2 vCPU sandbox, CPU-only JAX, 21×21 board, 1024 parallel games,
`lax.scan` rollouts. `python benchmarks/bench.py`:

| setup | env-steps/s | per half-turn (1024 games) |
| --- | --- | --- |
| engine only (all passes) | 343,000 | 3.0 ms |
| greedy bot, fresh random map per episode | 45,600 | 22.5 ms |
| greedy bot, 1024-map pool | 261,000 | 3.9 ms |
| masked random policy, map pool | 80,500 | 12.7 ms |
| 11×11, greedy bot, map pool | 848,000 | 1.2 ms |
| single environment | 64,000 | 15 µs/step |

The only expensive part of the hot path is generating a fresh map (~27 µs
each on CPU); with `map_pool_size=N` episodes are drawn from `N`
pre-generated maps and auto-reset costs essentially nothing.

Agent training throughput depends almost entirely on the conv backbone. On
the 2-core CPU sandbox: the `smoke` preset runs at ~260 env-steps/s, the
`small` preset (32 ch × 3 blocks, ConvGRU, 11×11) at ~35 env-steps/s
(~20 s/update with 16 envs × 24 steps). The `default` preset is intended
for a GPU.

A sample CPU run (2 cores) with the `smoke` preset:

```bash
python -m src.train --preset smoke --train-opponent random \
    --lr 2e-3 --epochs 4 --minibatches 4 --num-envs 32 \
    --total-updates 150 --eval-every 15 --out runs/vs-random
```

improved the agent from **67.7 % to 81.1 %** win rate against the random bot
(128-game evaluation, 9×9 board). That is the expected scale of progress for
a few minutes of CPU training; greedy self-play and larger runs benefit from GPU-scale
runs.

## Tests
## How it works

* **No per-tile Python loops.** A half-turn is a handful of whole-board array ops:
  decode the two actions, scatter the departures (`army.at[src].add(-moved)`,
  which is safe when both players name the same source tile), scatter the
  reinforcements, then resolve every tile's battle with a branchless
  "strongest force first, then the weaker one" formula.
* **Total functions.** Illegal actions become passes, so there is no
  data-dependent shape or exception, and `jit`/`vmap` see one static program.
* **Terminal handling** uses a single `lax.cond`, moved to the batch level in
  `step_batch` so map generation only runs on half-turns where a game actually ended.
* **Map generation** is a fixed number of vectorised greedy picks (2 generals,
  N castles) over a random priority order — no rejection sampling loops.
* **Tests:** 79 pytest tests including a differential test that runs the JAX
  engine side by side with a deliberately naive Python implementation of the same
  rules on thousands of random steps, plus rule-by-rule tests on hand-built
  boards, map statistics, fog-of-war, batching and auto-reset.

```bash
pytest -q                    # 95 tests, ~4 min on CPU
python benchmarks/bench.py   # simulator throughput sweep
```

The suite includes a differential test that runs the JAX engine side by side
with a deliberately naive Python implementation of the same rules on
thousands of random steps, rule-by-rule tests on hand-built boards, map
statistics, fog-of-war, batching and auto-reset, plus network shape/masking/
memory tests, GAE and AdamW reference checks, and an end-to-end PPO smoke
test.

## Limitations

* **1v1 only** (the rules and vectorised combat resolution assume two players).
* Fog of war affects observations only, not dynamics – which matches the real
  game, where hidden information is a UI concern.
* No AFK/quit handling, no in-game chat, no 2v2 teams, no
  "no-attack-in-50-turns" surrender rule.
* Simultaneous collisions use the documented strongest-first rule rather than
  the server's rotating move order; the two agree except in rare same-tile
  collisions, which are decided symmetrically here.
* Truncation (`max_turns`) is a **double loss**: if nobody captured the enemy
  general, both players get reward 0 and `winner = -1`. No land/army tiebreak
  is applied, so the only way to win is to take the general. The real server
  has no turn limit; training uses `max_turns = 1000` (the two-half-turns-per-
  turn convention) simply to bound episode length.
* No AFK/quit handling, no in-game chat, no 2v2 teams, no "no-attack-in-50-turns"
  surrender rule.
* Simultaneous collisions are resolved with the documented strongest-first rule
  rather than the server's rotating move order; the two agree except in rare
  same-tile collisions, which are decided symmetrically here (never favouring a
  seat).
* Truncation (`max_turns`) is a double loss (reward 0 for both players). The
  real server has no turn limit.

## Layout

```
generals_jax/
  config.py    static env config + tile/action constants
  tables.py    neighbour / distance lookup tables (numpy, built once)
  maps.py      JAX map generation, map pool, ASCII layout parser
  engine.py    reset / step / action mask / legal-action sampling
  state.py     State NamedTuple and score helpers
  obs.py       fog-of-war observation tensors
  render.py    ASCII renderer
  bots.py      browser opponent policies (including fog-honest greedy)
  env.py       GeneralsEnv: jitted, vmapped, auto-reset wrapper
tests/         79 tests, including the reference implementation for differential testing
examples/      play a game in the terminal, batched rollout loop
generals_web/  browser game: JSON API (stdlib http.server) + canvas client
benchmarks/    throughput sweep
```

MIT licensed.
