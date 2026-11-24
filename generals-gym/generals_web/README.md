# generals_web — play in the browser

A dependency-free web front-end for `generals_jax`: a small `http.server`
JSON API wrapped around the JIT-compiled engine, plus a canvas client with
generals.io-style controls.

```bash
pip install -e .
python -m generals_web          # == generals-web
# open http://localhost:8000
```

Options: `--host 0.0.0.0` (default), `--port 8000`, `--verbose`,
`--no-warm` (skip compiling the default boards at startup), `--run-dir` and
`--checkpoint` (enable a trained opponent).

## Play against a trained checkpoint

First install the project as above. For example, download the `final` weights and
configuration from the [15×15 run on Hugging Face](https://huggingface.co/datasets/jimchen2/generals-gym-runs/tree/main/15x15/checkpoints):

```bash
pip install huggingface_hub
python -c "from huggingface_hub import hf_hub_download; [hf_hub_download(repo_id='jimchen2/generals-gym-runs', repo_type='dataset', filename='15x15/checkpoints/final.' + ext, local_dir='runs/hf') for ext in ('json', 'npz')]"
python -m generals_web --run-dir runs/hf/15x15 --checkpoint final
```

Open **http://localhost:8000**, select **Trained checkpoint** under Opponent,
and play as the blue human player. The browser talks to the Python server; the
checkpoint is loaded on the server, not in the browser. The first game may take
longer to start while JAX compiles the engine and policy.

For your own training run, use `--run-dir runs/<name> --checkpoint latest`
(or `--checkpoint step_000050`, etc.). The run directory must contain
`checkpoints/<tag>.npz` and `checkpoints/<tag>.json`; `latest` also needs
`checkpoints/latest.json` and the files for the tag it names. A checkpoint
game uses its training board size, fog, map settings and turn limit; the human
can still use split moves even though the trained bot uses its original five
move directions. Square checkpoint boards from 5×5 through 31×31 are supported.
The bot chooses the highest-probability legal move and keeps separate recurrent
memory for each game. Without `--run-dir` the baseline opponents still work,
but choosing the checkpoint opponent shows an error.

The server has no authentication: run it only on a trusted network, or bind to
`--host 127.0.0.1` for local use. It does not download checkpoints automatically.

## Controls

| input | action |
| --- | --- |
| click a tile | select it |
| click an adjacent tile | send the selected tile's army there |
| **W A S D** / **arrow keys** | send the selected army one tile and move the selection along; tap several times to queue a path |
| `Z` then a direction | split: move half the army ("50 %" move) |
| `Space` | deselect |
| `Q` / right click | clear the queued moves |
| `P` | pause / resume (the clock also pauses when the tab is hidden) |
| ⤓ (top bar) | save the game as a replay: downloads a self-contained HTML player |
| `N` | new game |

Moves are queued and executed at most one per half-turn, giving each player
two move slots per displayed turn. At the default 1-second turn speed, slots
are 500 ms apart. At each slot, the client skips queued moves that cannot be
played on the current board (such as a stack of 1, a mountain, or a tile you no
longer own), then plays the next valid move. If none remain, that slot passes.
Direct illegal actions sent to the API are still treated as a pass by the engine.

## Match settings

* board 11×11, 15×15, 21×21 or 25×25
* opponent `checkpoint` (when configured), `easy` (random legal), `normal` (greedy but **fog-honest** — it only
  reacts to tiles it can see) or `hard` (the JAX greedy baseline, also fog-honest)
* land growth: fixed at +1 army on every owned tile every **25 displayed turns**
  (castles and generals also produce +1 per displayed turn)
* fog of war on/off (default off for a friendlier first game; generals.io-style
  vision of own tiles + the 8-neighbour ring when on)
* full-turn duration: **2 s / 1 s / 0.5 s / 0.25 s**, default 1 s; each turn has
  two half-turn action slots, so the default move interval is 500 ms

Settings are stored in `localStorage`; changing a match setting starts a new
game.

## Replays

Every live game is recorded server-side.  The ⤓ button (and *Save replay* on
the game-over card) downloads `/api/games/<id>/replay.html`: one standalone HTML
file with the whole game inlined and a play / pause / scrub / speed player, so
you can keep it, mail it or open it offline. Replay files contain the full board, including hidden tiles, even during a fogged game.  `GET /api/games/<id>/replay`
returns the same data as JSON, which `python -m src.video replay.json -o
game.mp4` turns into a video (see the main README).

## HTTP API

The client is a thin shell over five endpoints. Everything is JSON, no auth, no
cookies; a game lives in server memory until it is replaced or 6 hours pass.

| route | body | returns |
| --- | --- | --- |
| `GET /api/health` | – | `{"ok": true, "games": n, "configs": n}` |
| `POST /api/games` | `{"size":21,"fog":false,"opponent":"normal"}` | snapshot |
| `GET /api/games/<id>` | – | snapshot |
| `POST /api/games/<id>/turn` | `{"action": 123}` or `{}` to pass | snapshot after one half-turn |
| `DELETE /api/games/<id>` | – | `{"deleted": true}` |
| `GET /api/games/<id>/replay` | – | replay JSON (every half-turn so far) |
| `GET /api/games/<id>/replay.html` | – | single-file HTML replay player |

`action` is the engine's flat action index (`src_tile * dir_actions + dir`), with
`dir_actions = 9` because half-army moves are enabled. Each request advances one
half-turn; two requests make a displayed turn. Omit `action` (or pass `null`) to
pass for that half-turn.

### Snapshot

```json
{
  "id": "9f2c…", "turn": 12, "half_turn": 1, "max_turns": 1000,
  "done": false, "winner": -1,
  "you": 0, "opponent": "normal", "h": 21, "w": 21, "dir_actions": 9,
  "owner": [ … 441 ints … ], "army": [ … ], "city": [0/1 …], "vis": [0/1 …],
  "generals": {"you": [20, 3], "enemy": null},
  "score": {"land": [41, 39], "army": [512, 488], "cities": [3, 2]},
  "revealed": true,
  "settings": {"size": 21, "fog": false, "opponent": "normal", "growth": 25,
               "max_turns": 1000},
  "mountain": -2
}
```

Fog is applied **server-side**: while `revealed` is false, tiles the player
cannot see come through with `owner = -3` (unknown) or `owner = -4` (fogged
mountain/castle obstacle, matching generals.io), `city = 0`, and `army = 0`, so
the browser never receives hidden information. `generals.enemy` is `null` until
the enemy general is visible (or the game ends and the board is revealed).

## Implementation notes

* `generals_web/game.py` — one live match, opponent action, fogged snapshots.
* `generals_web/bots.py` — the three opponent policies (numpy, one move/half-turn).
* `generals_web/server.py` — `http.server` routes, static files, an environment
  cache keyed by `EnvConfig` (so the jitted kernels are compiled once per board
  configuration) and a startup warm-up thread.
* `generals_web/static/` — `index.html`, `style.css`, `app.js` (canvas renderer,
  keyboard/mouse input, turn clock).
