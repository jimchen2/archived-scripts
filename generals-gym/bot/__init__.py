"""The agent side of generals-gym: network, PPO, checkpoints and baselines.

Layout
------
``bot.network``
    :class:`PolicyValueNet` – SE-ResNet + global context + ConvGRU with a
    fully convolutional policy head and a pooled value head.
``bot.ppo``
    GAE, clipped PPO loss, AdamW and the scan-based update rule.
``bot.checkpoint``
    ``.npz`` parameter checkpoints with a JSON config sidecar.
``bot.baselines``
    The fog-honest greedy and random-legal reference policies.
"""

from .baselines import greedy_action, greedy_actions, random_legal_actions
from .checkpoint import Checkpoint, load_params, save_params
from .network import (
    Memory,
    NetConfig,
    PolicyValueNet,
    StepOutput,
    param_count,
    reset_memory,
)
from .ppo import (
    LR_SCHEDULES,
    PPOBatch,
    PPOConfig,
    TrainState,
    Trajectory,
    adamw_init,
    compute_gae,
    init_train_state,
    make_batch,
    ppo_loss,
    ppo_update,
    scheduled_lr,
)

__all__ = [
    # checkpointing
    "Checkpoint",
    # network
    "Memory",
    "NetConfig",
    # ppo
    "LR_SCHEDULES",
    "PPOBatch",
    "PPOConfig",
    "PolicyValueNet",
    "StepOutput",
    "TrainState",
    "Trajectory",
    "adamw_init",
    "compute_gae",
    # baselines
    "greedy_action",
    "greedy_actions",
    "init_train_state",
    "load_params",
    "make_batch",
    "param_count",
    "ppo_loss",
    "ppo_update",
    "random_legal_actions",
    "reset_memory",
    "save_params",
    "scheduled_lr",
]
