"""Evaluation: play a trained agent against the reference bots.

The agent always plays seat 0; the opponent (fog-honest ``"greedy"`` baseline or
``"random"`` legal policy) plays seat 1.  Games run in a batch inside one
``jax.lax.while_loop`` and stop as soon as ``games`` episodes have finished.

Command line
------------
    python -m src.evaluate --run-dir runs/default --games 128 --opponent greedy
"""

from __future__ import annotations

import argparse

import jax
import jax.numpy as jnp

from bot.baselines import greedy_actions
from bot.checkpoint import Checkpoint
from bot.network import PolicyValueNet, reset_memory
from game import NUM_GRID_CHANNELS, NUM_SCALARS, GeneralsEnv

from .config import TrainConfig


def evaluate_policy(
    env: GeneralsEnv,
    net: PolicyValueNet,
    params: dict,
    key: jax.Array,
    cfg: TrainConfig,
    opponent: str | None = None,
    games: int | None = None,
    deterministic: bool = False,
) -> dict:
    """Return win/loss/draw rates and mean episode length for seat 0.

    ``deterministic=False`` samples from the policy (the same stochastic
    policy PPO optimises); ``True`` takes the argmax action instead.
    """
    env_cfg = cfg.env_config()
    opponent = opponent or cfg.eval_opponent
    games = games or cfg.eval_games
    max_steps = 2 * env_cfg.max_turns  # two action half-turns per displayed turn

    def opponent_actions(step_key, states):
        if opponent == "greedy":
            acts = jax.vmap(lambda s: greedy_actions(s, env_cfg, env.tables))(states)
            return acts[:, 1]
        if opponent == "random":
            return env.sample_actions_batch(step_key, states)[:, 1]
        raise ValueError(f"unknown opponent {opponent!r}")

    def cond(carry):
        _, _, _, _, episodes, _, step = carry
        return (episodes < games) & (step < max_steps)

    def body(carry):
        states, memory, wins, losses, episodes, lengths, step = carry
        k_agent, k_opp = jax.random.split(jax.random.fold_in(key, step))

        obs = env.observations_batch(states)                  # (B, 2, ...)
        masks = jax.vmap(env.action_mask)(states)            # (B, 2, A)

        keys = jax.random.split(k_agent, games)
        out = jax.vmap(
            lambda g, s, m, mem, k: net.step(
                params, g, s, m, mem, key=k, sample=not deterministic
            )
        )(obs.grid[:, 0], obs.scalars[:, 0], masks[:, 0], memory, keys)

        opp = opponent_actions(k_opp, states)
        actions = jnp.stack([out.action, opp], axis=1)

        new_states, _, info = env.step_batch(
            states, actions, auto_reset=True
        )
        done = info["done"]
        wins = wins + jnp.sum(done & (info["winner"] == 0)).astype(jnp.int32)
        losses = losses + jnp.sum(done & (info["winner"] == 1)).astype(jnp.int32)
        episodes = episodes + jnp.sum(done).astype(jnp.int32)
        lengths = lengths + jnp.sum(jnp.where(done, info["turn"], 0))
        memory = reset_memory(out.memory, done)
        return new_states, memory, wins, losses, episodes, lengths, step + 1

    states = env.reset_batch(jax.random.split(key, games))
    memory = net.batched_initial_memory((games,))
    init = (
        states,
        memory,
        jnp.zeros((), dtype=jnp.int32),
        jnp.zeros((), dtype=jnp.int32),
        jnp.zeros((), dtype=jnp.int32),
        jnp.zeros((), dtype=jnp.int32),
        jnp.zeros((), dtype=jnp.int32),
    )
    _, _, wins, losses, episodes, lengths, _ = jax.lax.while_loop(cond, body, init)

    played = jnp.maximum(episodes, 1)
    return {
        "win_rate": wins / played,
        "loss_rate": losses / played,
        "draw_rate": 1.0 - (wins + losses) / played,
        "mean_length": lengths / played,
        "episodes": episodes,
    }


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run-dir", default="runs/default")
    ap.add_argument("--checkpoint", default="latest")
    ap.add_argument("--opponent", choices=["greedy", "random"], default=None)
    ap.add_argument("--games", type=int, default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--deterministic", action="store_true",
                    help="take the argmax action instead of sampling")
    args = ap.parse_args(argv)

    checkpoint = Checkpoint(args.run_dir)
    arrays, payload = checkpoint.load(args.checkpoint)
    cfg = TrainConfig(**payload["config"])
    overrides = {}
    if args.opponent:
        overrides["eval_opponent"] = args.opponent
    if args.games:
        overrides["eval_games"] = args.games
    cfg = cfg.replace(**overrides)

    env = GeneralsEnv(cfg.env_config(), map_pool_size=0, seed=args.seed)
    net = PolicyValueNet(
        cfg.net_config(),
        grid_channels=NUM_GRID_CHANNELS,
        num_scalars=NUM_SCALARS,
        height=cfg.height,
        width=cfg.width,
    )
    params = checkpoint.restore(arrays, net.init(jax.random.PRNGKey(0)))
    stats = jax.jit(
        lambda p, k: evaluate_policy(env, net, p, k, cfg,
                                     deterministic=args.deterministic)
    )(params, jax.random.PRNGKey(args.seed))
    print(f"checkpoint : {payload['tag']}")
    print(f"opponent   : {cfg.eval_opponent}")
    print(f"games      : {int(stats['episodes'])}")
    print(f"win rate   : {float(stats['win_rate']):.1%}")
    print(f"loss rate  : {float(stats['loss_rate']):.1%}")
    print(f"draw rate  : {float(stats['draw_rate']):.1%}")
    print(f"mean length: {float(stats['mean_length']):.1f} turns")


if __name__ == "__main__":
    main()
