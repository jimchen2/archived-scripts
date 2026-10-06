# ZombsRoyale Gymnasium env

`zombs_env.py` — a `gymnasium.Env` for **ZombsRoyale.io solo**. The observation
comes from **real-time JavaScript state scraping** (WebSocket hooks injected
before page load), never from screenshots. Video/stills are optional debug
output (`record=True`).

## The explicit phase machine

The game only "starts" after a specific chain, so the env models it directly —
every transition is tied to a measured protocol signal:

```
MENU       page + Unity loaded, consent dismissed, ad zones stripped
   |  click SOLO
LOBBY      mason (socket.io): we send createParty / setPartyGameMode:"Solo" /
   |       setReady; server: partyJoinServer, partyStateUpdated cycles
   |       waiting -> matchmaking -> ingame (per round; re-fires on rotation)
PLANE      round joined for us: mason "ingame" (or tick avg >= 90B fallback).
   |       SPACE pressed, re-pressed every 7 s (no-op in a countdown lobby)
AIRBORNE   held-W 1.5 s echoes <= 1 input send: falling suppresses input
   |       (walking and even seated-in-plane both echo; only falling doesn't)
LANDED     two-stage proof of walking: W-tap answered (>= 5 sends) AND held-W
   |       produces a CONTINUOUS stream (>= 8 sends / 1.5 s). Spectate mode
   |       only echoes key-down edges (1-6 sends) and is rejected here.
ALIVE      <<<< gym.reset() returns; the episode starts HERE >>>>
   |
ELIMINATED detected in step(), terminate within a step or two of death:
             [a] client SENDS 42["setIsInRound", false]   (explicit, fastest)
             [b] mason 42["partyStateUpdated","waiting"]  (round ended)
             [c] match socket closed
             [d] ~5 s send-silence + unanswered W-tap probe (fallback;
                 live-but-idle players answer the probe, dead ones can't)
```

Rotation limbo (the server parks you in spectate/lobby between rounds) is
handled: the phase machine demotes to LOBBY on mason "waiting" / 120 s without
a confirmed jump, and the landing gate rejects spectate taps — it keeps cycling
until it gets a real jump and a real touchdown.

## Spaces / reward
- action `Discrete(8)`: W/A/S/D, interact(E), reload(R), jump(Space), fire(LMB)
- observation `Box(12,)`: ground time, tick totals, tick rate/size (1-2 s
  windows), sends/s, elimination flag, send-silence, phase one-hot, prev action
- reward: +0.1/step alive, +2.0 per 30 s milestone, -25 on elimination

## Usage
```python
from zombs_env import ZombsRoyaleEnv
env = ZombsRoyaleEnv(record=True)          # video + menu/jump/landed/end stills
obs, info = env.reset(seed=42)             # blocks until ON THE GROUND (alive)
obs, r, term, trunc, info = env.step(0)    # info["phase"], info["elim_reason"]
env.close()                                # flushes video + zombs_ws_capture.json
```

One recorded round with a heuristic policy: `python3 run_episode.py`

A validated run's phase trace (episode log, all signals from JS):
```
PHASE -> LOBBY (clicking SOLO)
PHASE -> PLANE (tick avg 299B, 1s after SOLO click)
PHASE -> LOBBY (no jump within 120s of ingame — round cycled?)   x2 (spectate)
PHASE -> PLANE (tick avg 121B, 283s after SOLO click)
PHASE -> AIRBORNE (held W 1.5s, 1 input echoes — falling)
PHASE -> LANDED (tap 8 sends + held-W stream 24 sends, air 46.3s)
PHASE -> ALIVE (332s from SOLO click to on the ground)
PHASE -> ELIMINATED (client sent setIsInRound:false (eliminated))  # placed #11
```

## Sandbox notes
Install Python dependencies with `pip install -r requirements.txt`, then install
Firefox with `playwright install --with-deps firefox`. The sandbox resets between
sessions — Firefox may need 3 GB of swap and `xvfb`; `_ensure_stack()`
re-creates the swap + Xvfb itself.

## Supporting tools
- `play_zombs.py` — standalone solo/duo browser play smoke test.
- `play_record.py` — standalone round recorder with screenshots and video.

Recordings and runtime captures are generated locally and excluded from Git by
`.gitignore`.

## Next steps
Decode the binary game-tick frames (opcodes captured in
`zombs_ws_capture.json`) to read health/position/entities into the obs —
that enables damage/kill rewards and real aiming.
