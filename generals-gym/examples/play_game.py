"""Render a game between two baseline bots, turn by turn.

    python -m examples.play_game                 # 9x9, greedy vs greedy
    python -m examples.play_game --size 21 --every 25
    python -m examples.play_game --fog           # show player 0's fogged view
    python -m examples.play_game --random        # random legal actions

Save the game (and watch it as a video) instead of scrolling the terminal:

    python -m examples.play_game --save-replay replays/bots.json
    python -m examples.play_game --save-replay replays/bots.json \
        --video replays/bots.mp4
    python -m examples.play_game --save-replay replays/bots.json \
        --video replays/bots.gif --video-view all
"""

from __future__ import annotations

import argparse

import jax
import jax.numpy as jnp

from game import EnvConfig, GeneralsEnv, ascii_state
from game.replay import Replay, ReplayRecorder
from bot.baselines import greedy_actions, random_legal_actions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=9)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--every", type=int, default=10, help="frames to print")
    ap.add_argument("--fog", action="store_true", help="render player 0's view")
    ap.add_argument("--random", action="store_true", help="random instead of greedy")
    ap.add_argument("--max-turns", type=int, default=300)
    ap.add_argument("--save-replay", metavar="PATH", default=None,
                    help="record the whole game to a replay JSON file")
    ap.add_argument("--video", metavar="PATH", default=None,
                    help="also render the replay to this MP4/GIF")
    ap.add_argument("--video-view", choices=["seat0", "all"], default="all",
                    help="camera for the rendered video (default: full board)")
    ap.add_argument("--quiet", action="store_true",
                    help="do not print the board every --every turns")
    args = ap.parse_args()

    cfg = EnvConfig(
        height=args.size,
        width=args.size,
        city_count=max(2, args.size // 2),
        max_turns=args.max_turns,
        fog=args.fog,
    )
    env = GeneralsEnv(cfg)
    state = env.reset(jax.random.PRNGKey(args.seed))
    label = "random" if args.random else "greedy"
    recorder = None
    if args.save_replay or args.video:
        recorder = ReplayRecorder(
            cfg, players=[(f"{label} (seat 0)", "bot"), (f"{label} (seat 1)", "bot")],
            seed=args.seed, meta={"source": "examples/play_game.py"},
        )
        recorder.add(state)
    if not args.quiet:
        print(ascii_state(state, cfg, player=0 if args.fog else None))

    key = jax.random.PRNGKey(1)
    for _half_turn in range(2 * args.max_turns):
        if args.random:
            key, sub = jax.random.split(key)
            actions = random_legal_actions(sub, env.action_mask(state), cfg)
        else:
            actions = greedy_actions(state, cfg, env.tables)
        state, rewards, info = env.step(state, jnp.asarray(actions))
        if recorder is not None:
            recorder.add(state, actions=jnp.asarray(actions), rewards=rewards)
        at_turn_boundary = int(state.half_turn) == 0
        if (bool(info["done"]) or (
            at_turn_boundary and int(info["turn"]) % args.every == 0
        )) and not args.quiet:
            print()
            print(ascii_state(state, cfg, player=0 if args.fog else None))
        if bool(info["done"]):
            print()
            if int(info["winner"]) < 0:
                print(f"draw after {int(info['turn'])} turns")
            else:
                print(f"player {int(info['winner'])} wins on turn {int(info['turn'])}"
                      f"   rewards={list(map(float, rewards))}")
            break

    if recorder is not None:
        from pathlib import Path

        replay_path = Path(args.save_replay or "replays/bots.json")
        recorder.save(replay_path)
        print(f"replay saved -> {replay_path}")
        if args.video:
            from src.video import VideoOptions, render_replay

            out = Path(args.video)
            fmt = "gif" if out.suffix.lower() == ".gif" else None
            render_replay(
                Replay.from_dict(recorder.to_dict()),
                out,
                VideoOptions(view=args.video_view),
                fmt=fmt,
            )
            print(f"video saved  -> {out}")


if __name__ == "__main__":
    main()
