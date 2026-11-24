"""Replay helpers shared by the trainer, the player script and the API.

Everything that needs to *produce* a replay (not render it) lives here:

* :func:`play_episode` -- roll out one full game with a checkpoint and record
  every half-turn, including the agent's value estimate and entropy;
* :func:`record_game` -- the convenience wrapper the trainer calls: play,
  save, and optionally render a video next to the JSON.

The CLI equivalent is ``python -m src.play --save-replay ... --video ...``.
"""

from __future__ import annotations

import time
from pathlib import Path

import jax
import jax.numpy as jnp

from bot.baselines import greedy_action
from bot.network import PolicyValueNet
from game import EnvConfig, GeneralsEnv
from game.replay import Replay, ReplayRecorder

OPPONENTS = ("greedy", "random")


def play_episode(
    env: GeneralsEnv,
    net: PolicyValueNet,
    params: dict,
    env_cfg: EnvConfig,
    opponent: str = "greedy",
    seed: int = 0,
    sample: bool = False,
    seats: tuple[int, int] = (0, 1),
    names: tuple[str, str] | None = None,
    meta: dict | None = None,
    record: bool = True,
    on_turn=None,
) -> tuple[ReplayRecorder | None, dict]:
    """Play one game to the end and record it.

    ``opponent`` is ``"greedy"`` (the fog-honest baseline), ``"random"`` (uniform
    legal moves) or ``"self"`` (the same network in the other seat).  Returns
    ``(recorder, summary)``; ``recorder`` is ``None`` when ``record`` is off.
    """
    if opponent not in OPPONENTS + ("self",):
        raise ValueError(f"unknown opponent {opponent!r}")

    key = jax.random.PRNGKey(seed)
    state = env.reset(key)
    memory = net.batched_initial_memory(())
    opp_memory = net.batched_initial_memory(()) if opponent == "self" else None

    if names is None:
        names = (f"agent (seat {seats[0]})", opponent)
    recorder = None
    if record:
        recorder = ReplayRecorder(
            env_cfg,
            players=[
                (names[0], "agent"),
                (names[1], "agent" if opponent == "self" else opponent),
            ],
            seed=seed,
            meta=meta or {},
        )
        recorder.add(state)

    info = {"done": jnp.asarray(False), "winner": jnp.asarray(-1), "turn": jnp.asarray(0)}
    started = time.perf_counter()
    seat = seats[0]
    for _ in range(2 * env_cfg.max_turns):
        obs = env.observe(state, seat)
        mask = env.action_mask(state)[seat]
        key, action_key = jax.random.split(key)
        out = net.step(params, obs.grid, obs.scalars, mask, memory, key=action_key, sample=sample)
        memory = out.memory

        if opponent == "greedy":
            opp = greedy_action(state, seats[1], env_cfg, env.tables)
        elif opponent == "random":
            key, sub = jax.random.split(key)
            opp = env.sample_actions(sub, state)[seats[1]]
        else:
            opp_obs = env.observe(state, seats[1])
            opp_mask = env.action_mask(state)[seats[1]]
            key, opp_key = jax.random.split(key)
            opp_out = net.step(
                params, opp_obs.grid, opp_obs.scalars, opp_mask, opp_memory,
                key=opp_key, sample=sample,
            )
            opp_memory = opp_out.memory
            opp = opp_out.action

        actions = jnp.zeros((2,), dtype=jnp.int32)
        actions = actions.at[seats[0]].set(out.action).at[seats[1]].set(opp)
        state, rewards, info = env.step(state, actions, auto_reset=False)
        if recorder is not None:
            frame = recorder.add(state, actions=actions, rewards=rewards)
            frame["value"] = float(out.value)
            frame["entropy"] = float(out.entropy)
        if on_turn is not None:
            on_turn(state, out, info)

        if bool(info["done"]):
            break

    if recorder is not None:
        recorder.result()
    summary = {
        "winner": int(info["winner"]),
        "turns": int(info["turn"]),
        "elapsed": time.perf_counter() - started,
        "names": names,
        "opponent": opponent,
    }
    return recorder, summary


def record_game(
    cfg,
    net: PolicyValueNet,
    params: dict,
    name: str,
    key,
    *,
    tag: str | None = None,
    run_dir: str | Path | None = None,
    meta: dict | None = None,
    video: bool = False,
    view: str = "all",
    opponent: str | None = None,
    sample: bool = False,
    seed: int = 0,
) -> list[Path]:
    """Play one game, write ``<run_dir>/replays/<name>.json`` (+ optional video)."""
    run_dir = Path(run_dir or getattr(cfg, "out_dir", "runs/default"))
    out_dir = run_dir / "replays"
    out_dir.mkdir(parents=True, exist_ok=True)

    # The caller supplies a distinct key per update; derive the game seed from
    # it so periodic replays do not all use the same map and random sequence.
    seed = int(jax.random.bits(jax.random.fold_in(key, seed), (), dtype=jnp.uint32))
    env_cfg = cfg.env_config()
    env = GeneralsEnv(env_cfg, map_pool_size=0, seed=seed)
    opponent = opponent or getattr(cfg, "eval_opponent", "greedy")
    recorder, summary = play_episode(
        env,
        net,
        params,
        env_cfg,
        opponent=opponent,
        seed=seed,
        sample=sample,
        names=(f"{tag or name}", opponent),
        meta={
            "update": meta.get("update") if meta else None,
            "run_dir": str(run_dir),
            **(meta or {}),
        },
    )
    if recorder is None:  # pragma: no cover - record is always on here
        return []
    json_path = recorder.save(out_dir / f"{name}.json")
    written = [json_path]

    if video:
        from .video import VideoOptions, render_replay, find_ffmpeg

        replay = Replay.from_dict(recorder.to_dict())
        opts = VideoOptions(view=view)
        if find_ffmpeg():
            written.append(render_replay(replay, out_dir / f"{name}.mp4", opts))
        else:
            written.append(render_replay(replay, out_dir / f"{name}.gif", opts, fmt="gif"))

    summary["paths"] = written
    return written
