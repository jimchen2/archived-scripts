"""Watch a trained agent play, and optionally save the game as a replay.

    python -m src.play --run-dir runs/default --opponent greedy --every 5

Prints the board from the agent's (fogged) point of view, plus the action it
chose on each half-turn.

Add ``--save-replay replays/game.json`` to record every half-turn.  The replay can
then be turned into a video without re-running anything::

    python -m src.video replays/game.json -o replays/game.mp4

or ``--video replays/game.mp4`` to render it as soon as the game ends.

Besides playing the reference bots you can pit the checkpoint against another
checkpoint (``--opponent agent --opponent-run-dir runs/other``), which is handy
for watching training progress::

    python -m src.play --run-dir runs/default --opponent agent \\
        --opponent-run-dir runs/default --opponent-checkpoint step_000500
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import jax
import jax.numpy as jnp

from bot.baselines import greedy_action
from bot.checkpoint import Checkpoint
from bot.network import PolicyValueNet
from game import NUM_GRID_CHANNELS, NUM_SCALARS, GeneralsEnv, ascii_state, engine
from game.replay import Replay, ReplayRecorder

from .config import TrainConfig

OPPONENTS = ("greedy", "random", "agent")


def load_policy(run_dir: str, checkpoint_tag: str, seed: int = 0):
    """Rebuild ``(cfg, env_cfg, net, params, tag)`` from a checkpoint directory."""
    checkpoint = Checkpoint(run_dir)
    arrays, payload = checkpoint.load(checkpoint_tag)
    cfg = TrainConfig(**payload["config"])
    net = PolicyValueNet(
        cfg.net_config(),
        grid_channels=NUM_GRID_CHANNELS,
        num_scalars=NUM_SCALARS,
        height=cfg.height,
        width=cfg.width,
    )
    params = checkpoint.restore(arrays, net.init(jax.random.PRNGKey(seed)))
    tag = str(payload.get("tag", checkpoint_tag))
    return cfg, net, params, tag


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run-dir", default="runs/default")
    ap.add_argument("--checkpoint", default="latest")
    ap.add_argument("--opponent", choices=list(OPPONENTS), default="greedy",
                    help="fog-honest greedy, random legal or another checkpoint")
    ap.add_argument("--opponent-run-dir", default=None,
                    help="run directory of the opponent checkpoint (default: --run-dir)")
    ap.add_argument("--opponent-checkpoint", default="latest",
                    help="checkpoint tag of the opponent network")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--every", type=int, default=None, help="print every N turns (default: 1; silent when saving a replay)")
    ap.add_argument("--dry-run", action="store_true",
                    help="do not print every board, only the result")
    ap.add_argument("--show-all", action="store_true",
                    help="print the omniscient board instead of the agent's view")
    ap.add_argument("--sample", action="store_true",
                    help="sample from the policy instead of taking the argmax")
    ap.add_argument("--save-replay", metavar="PATH", default=None,
                    help="write the whole game to a replay JSON file")
    ap.add_argument("--video", metavar="PATH", default=None,
                    help="also render the replay to this MP4/GIF when the game ends")
    ap.add_argument("--video-view", choices=["seat0", "all"], default="seat0",
                    help="whose eyes the video shows (default: the agent's)")
    ap.add_argument("--gif", action="store_true",
                    help="render a GIF instead of an MP4 (no ffmpeg needed)")
    return ap


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    if args.every is not None and args.every < 1:
        raise ValueError("--every must be positive")
    every = args.every if args.every is not None else (0 if args.save_replay or args.video else 1)

    cfg, net, params, agent_tag = load_policy(args.run_dir, args.checkpoint, args.seed)
    env_cfg = cfg.env_config()

    env = GeneralsEnv(env_cfg, map_pool_size=0, seed=args.seed)
    key = jax.random.PRNGKey(args.seed)
    state = env.reset(key)
    memory = net.batched_initial_memory(())

    names = [f"agent {agent_tag}", args.opponent]
    if args.opponent == "agent":
        opp_dir = args.opponent_run_dir or args.run_dir
        _opp_cfg, opp_net, opp_params, opp_tag = load_policy(
            opp_dir, args.opponent_checkpoint, args.seed
        )
        if opp_dir == args.run_dir and opp_tag == agent_tag:
            names[1] = f"agent {opp_tag} (mirror)"
        else:
            names[1] = f"agent {opp_tag}"
        opp_memory = opp_net.batched_initial_memory(())
    else:
        opp_net = opp_params = opp_memory = None

    recorder = None
    if args.save_replay or args.video:
        recorder = ReplayRecorder(
            env_cfg,
            players=[(names[0], "agent"), (names[1], args.opponent if args.opponent != "agent" else "agent")],
            seed=args.seed,
            meta={"run_dir": args.run_dir, "checkpoint": agent_tag},
        )
        recorder.add(state)

    view = None if args.show_all else 0
    if not args.dry_run and every:
        print(ascii_state(state, env_cfg, player=view))

    info = {"done": jnp.asarray(False), "winner": jnp.asarray(-1), "turn": jnp.asarray(0)}
    t0 = time.perf_counter()
    for _half_turn in range(2 * env_cfg.max_turns):
        obs = env.observe(state, 0)
        mask = env.action_mask(state)[0]
        key, action_key = jax.random.split(key)
        out = net.step(params, obs.grid, obs.scalars, mask, memory, key=action_key, sample=args.sample)
        memory = out.memory

        if args.opponent == "greedy":
            opp = greedy_action(state, 1, env_cfg, env.tables)
        elif args.opponent == "random":
            key, sub = jax.random.split(key)
            opp = env.sample_actions(sub, state)[1]
        else:
            opp_obs = env.observe(state, 1)
            opp_mask = env.action_mask(state)[1]
            key, opp_key = jax.random.split(key)
            opp_out = opp_net.step(
                opp_params, opp_obs.grid, opp_obs.scalars, opp_mask, opp_memory,
                key=opp_key, sample=args.sample,
            )
            opp_memory = opp_out.memory
            opp = opp_out.action

        actions = jnp.stack([out.action, opp])
        state, rewards, info = env.step(state, actions, auto_reset=False)
        if recorder is not None:
            frame = recorder.add(state, actions=actions, rewards=rewards)
            frame["value"] = float(out.value)
            frame["entropy"] = float(out.entropy)

        if every and not args.dry_run:
            display_turn = int(info["turn"])
            should_print = bool(info["done"]) or (
                int(state.half_turn) == 0 and display_turn % every == 0
            )
            if should_print:
                src, direction = engine.decode_action(int(out.action), env_cfg)
                print(f"--- turn {display_turn:3d} | agent {src // env_cfg.width},"
                      f"{src % env_cfg.width} {['pass', 'up', 'down', 'left', 'right', 'half up', 'half down', 'half left', 'half right'][direction]}"
                      f" | value {float(out.value):+.2f} | entropy {float(out.entropy):.2f}")
                print(ascii_state(state, env_cfg, player=view))

        if bool(info["done"]):
            break
    elapsed = time.perf_counter() - t0

    if recorder is not None:
        recorder.result()  # refresh the summary from the final frame
        replay_path = Path(args.save_replay or "replays/last_game.json")
        recorder.save(replay_path)
        print(f"replay saved -> {replay_path}", flush=True)
        if args.video:
            from .video import VideoOptions, render_replay

            out = Path(args.video)
            fmt = "gif" if args.gif else None
            if fmt == "gif" and out.suffix.lower() != ".gif":
                out = out.with_suffix(".gif")
            render_replay(
                Replay.from_dict(recorder.to_dict()),
                out,
                VideoOptions(view=args.video_view),
                fmt=fmt,
            )
            print(f"video saved  -> {out}", flush=True)

    winner = int(info["winner"])
    print("=" * 60)
    if winner == 0:
        print(f"{names[0]} wins in {int(info['turn'])} turns ({elapsed:.1f}s)")
    elif winner == 1:
        print(f"{names[1]} wins in {int(info['turn'])} turns ({elapsed:.1f}s)")
    else:
        print(f"draw after {int(info['turn'])} turns ({elapsed:.1f}s)")


if __name__ == "__main__":
    sys.exit(main())
