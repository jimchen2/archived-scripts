"""Training configuration and presets.

Everything the trainer needs lives in :class:`TrainConfig`.  It is a plain
dataclass so it can be serialised to the JSON checkpoint sidecar and rebuilt
from the command line.  Presets are just dictionaries of overrides:

* ``smoke``   – tiny 9x9 board, 2 blocks, no memory; finishes an update in a
  few seconds on CPU.  Use it to check the plumbing.
* ``small``   – 11x11, 32 channels, 3 blocks, ConvGRU; a realistic CPU setup.
* ``default`` – the full architecture from the README: 21x21, 64 channels,
  6 residual blocks, SE + global context, ConvGRU.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any

from bot.network import NetConfig
from bot.ppo import LR_SCHEDULES, PPOConfig
from game import EnvConfig

PRESETS: dict[str, dict[str, Any]] = {
    "smoke": {
        "height": 9,
        "width": 9,
        "max_turns": 50,
        "map_pool_size": 128,
        "channels": 16,
        "num_blocks": 2,
        "memory": "none",
        "num_envs": 8,
        "rollout_len": 8,
        "epochs": 2,
        "num_minibatches": 2,
        "remat": False,
        "eval_games": 16,
        "eval_every": 5,
        "checkpoint_every": 10,
    },
    "small": {
        "height": 11,
        "width": 11,
        "max_turns": 150,
        "map_pool_size": 512,
        "channels": 32,
        "num_blocks": 3,
        "memory": "gru",
        "num_envs": 16,
        "rollout_len": 16,
        "epochs": 3,
        "num_minibatches": 4,
        "remat": False,
        "eval_games": 32,
        "eval_every": 10,
        "checkpoint_every": 20,
    },
    "default": {
        "height": 21,
        "width": 21,
        "max_turns": 1000,
        "map_pool_size": 1024,
        "channels": 64,
        "num_blocks": 6,
        "memory": "gru",
        "num_envs": 64,
        "rollout_len": 32,
        "epochs": 4,
        "num_minibatches": 4,
        "eval_games": 32,
        "eval_every": 25,
        "checkpoint_every": 50,
    },
}


@dataclass
class TrainConfig:
    """All hyper-parameters for one training run."""

    # --- environment -------------------------------------------------------
    height: int = 21
    width: int = 21
    fog: bool = True
    max_turns: int = 1000
    map_pool_size: int = 1024
    mountain_frac: float = 0.20
    city_count: int = 10

    # --- network -----------------------------------------------------------
    channels: int = 64
    num_blocks: int = 6
    use_se: bool = True
    se_ratio: int = 4
    global_context_every: int = 2
    memory: str = "gru"
    stack_frames: int = 4
    use_coords: bool = False

    # --- PPO ---------------------------------------------------------------
    num_envs: int = 64
    rollout_len: int = 32
    epochs: int = 4
    num_minibatches: int = 4
    lr: float = 3e-4
    lr_end: float = 0.0
    lr_schedule: str = "linear"  # "linear", "cosine", or "constant"
    lr_warmup_updates: int = 0
    weight_decay: float = 0.0
    gamma: float = 0.995
    gae_lambda: float = 0.95
    clip_eps: float = 0.2
    ent_coef: float = 0.001
    vf_coef: float = 0.5
    max_grad_norm: float = 0.5
    remat: bool = True
    # Potential-based reward shaping: coefficient on the change in
    # (normalised land + 0.5 * log army - distance term) advantage.
    # 0 disables shaping entirely.
    shaping_coef: float = 0.5
    # Weight of the "distance from my territory to the enemy general" term in
    # the shaping potential.  Privileged information, but legal in a reward.
    general_distance_coef: float = 0.25

    # --- run ---------------------------------------------------------------
    preset: str = "default"
    # "self" = shared-parameter self-play (both seats trained);
    # "random" / "greedy" = train seat 0 against a fixed opponent;
    # "pool" = train seat 0 against frozen historical snapshots.
    train_opponent: str = "self"
    opponent_pool_size: int = 8
    opponent_snapshot_every: int = 25
    seed: int = 0
    total_updates: int = 1000
    out_dir: str = "runs/default"
    eval_every: int = 25
    checkpoint_every: int = 50
    eval_games: int = 32
    eval_opponent: str = "greedy"  # "greedy" or "random"
    log_every: int = 1
    # Save a replay (and optionally a video) of one game every N updates.
    # 0 disables replay recording; see ``src.replay_tools``.
    save_replay_every: int = 0
    replay_video: bool = False
    replay_view: str = "all"  # "seat0", "seat1" or "all"

    # ------------------------------------------------------------------ api
    @classmethod
    def from_preset(cls, preset: str = "default", **overrides) -> TrainConfig:
        if preset not in PRESETS:
            raise ValueError(
                f"unknown preset {preset!r}; choose from {sorted(PRESETS)}"
            )
        values = dict(PRESETS[preset])
        values["preset"] = preset
        values["out_dir"] = f"runs/{preset}"
        unknown = set(overrides) - {f.name for f in fields(cls)}
        if unknown:
            raise ValueError(f"unknown config fields: {sorted(unknown)}")
        values.update(overrides)
        return cls(**values)

    def replace(self, **overrides) -> TrainConfig:
        values = asdict(self)
        values.update(overrides)
        return TrainConfig(**values)

    # ----------------------------------------------------------- components
    def env_config(self) -> EnvConfig:
        return EnvConfig(
            height=self.height,
            width=self.width,
            fog=self.fog,
            max_turns=self.max_turns,
            mountain_frac=self.mountain_frac,
            city_count=self.city_count,
        )

    def __post_init__(self) -> None:
        if self.train_opponent not in ("self", "random", "greedy", "pool"):
            raise ValueError("train_opponent must be self, random, greedy or pool")
        if self.opponent_pool_size < 1 or self.opponent_snapshot_every < 1:
            raise ValueError("opponent_pool_size and opponent_snapshot_every must be positive")
        if self.replay_view not in ("seat0", "seat1", "all"):
            raise ValueError("replay_view must be seat0, seat1 or all")
        if self.lr_schedule not in LR_SCHEDULES:
            raise ValueError(
                f"lr_schedule must be one of {LR_SCHEDULES}, got {self.lr_schedule!r}"
            )
        if self.lr < 0 or self.lr_end < 0:
            raise ValueError("lr and lr_end must be non-negative")
        if self.lr_warmup_updates < 0:
            raise ValueError("lr_warmup_updates must be non-negative")

    def net_config(self) -> NetConfig:
        return NetConfig(
            channels=self.channels,
            num_blocks=self.num_blocks,
            use_se=self.use_se,
            se_ratio=self.se_ratio,
            global_context_every=self.global_context_every,
            memory=self.memory,
            stack_frames=self.stack_frames,
            use_coords=self.use_coords,
            dir_actions=self.env_config().dir_actions,
        )

    def ppo_config(self) -> PPOConfig:
        return PPOConfig(
            num_envs=self.num_envs,
            rollout_len=self.rollout_len,
            epochs=self.epochs,
            num_minibatches=self.num_minibatches,
            lr=self.lr,
            lr_end=self.lr_end,
            lr_schedule=self.lr_schedule,
            lr_warmup_updates=self.lr_warmup_updates,
            weight_decay=self.weight_decay,
            gamma=self.gamma,
            gae_lambda=self.gae_lambda,
            clip_eps=self.clip_eps,
            ent_coef=self.ent_coef,
            vf_coef=self.vf_coef,
            max_grad_norm=self.max_grad_norm,
            remat=self.remat,
        )

    def to_dict(self) -> dict:
        return asdict(self)


def print_config(cfg: TrainConfig) -> None:
    """Small human-readable summary used at the start of a run."""
    net = cfg.net_config()
    ppo = cfg.ppo_config()
    lr_desc = f"lr={ppo.lr} ({ppo.lr_schedule}"
    if ppo.lr_schedule != "constant":
        lr_desc += f" -> {ppo.lr_end}"
    if ppo.lr_warmup_updates:
        lr_desc += f", warmup={ppo.lr_warmup_updates}"
    lr_desc += ")"
    print(f"preset        : {cfg.preset}")
    print(f"board         : {cfg.height}x{cfg.width}, fog={cfg.fog}, "
          f"max_turns={cfg.max_turns}")
    print(f"network       : {net.channels} ch x {net.num_blocks} blocks, "
          f"memory={net.memory}, SE={net.use_se}, "
          f"context every {net.global_context_every}")
    print(f"ppo           : {ppo.num_envs} envs x {ppo.rollout_len} steps, "
          f"{ppo.epochs} epochs x {ppo.num_minibatches} minibatches, "
          f"{lr_desc}")
    print(f"shaping       : coef={cfg.shaping_coef}, "
          f"distance={cfg.general_distance_coef}")
    print(f"opponents     : train={cfg.train_opponent}, "
          f"eval={cfg.eval_opponent}")
    if cfg.train_opponent == "pool":
        print(f"opponent pool : size={cfg.opponent_pool_size}, "
              f"snapshot every {cfg.opponent_snapshot_every} updates")
    print(f"run           : {cfg.total_updates} updates, seed={cfg.seed}, "
          f"out={cfg.out_dir}")
