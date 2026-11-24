"""Tests for training configuration and presets."""

from __future__ import annotations

import pytest

from src.config import PRESETS, TrainConfig


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_presets_build_valid_configs(name):
    cfg = TrainConfig.from_preset(name)
    assert cfg.preset == name
    assert cfg.out_dir == f"runs/{name}"
    assert cfg.height == cfg.width
    assert cfg.num_envs > 0 and cfg.rollout_len > 0
    assert cfg.epochs > 0 and cfg.num_minibatches > 0

    net = cfg.net_config()
    env = cfg.env_config()
    assert net.dir_actions == env.dir_actions
    assert net.channels > 0 and net.num_blocks >= 0
    assert net.memory in ("none", "gru", "stack")


def test_preset_overrides_and_unknown_field():
    cfg = TrainConfig.from_preset("smoke", channels=99, total_updates=7)
    assert cfg.channels == 99
    assert cfg.total_updates == 7

    with pytest.raises(ValueError):
        TrainConfig.from_preset("smoke", not_a_field=1)
    with pytest.raises(ValueError):
        TrainConfig.from_preset("nope")


def test_replace_keeps_other_fields():
    cfg = TrainConfig.from_preset("small")
    other = cfg.replace(lr=1e-3)
    assert other.lr == 1e-3
    assert other.height == cfg.height
    assert other.preset == cfg.preset


def test_to_dict_roundtrip():
    cfg = TrainConfig.from_preset("smoke")
    clone = TrainConfig(**cfg.to_dict())
    assert clone == cfg


def test_lr_schedule_config_and_cli_overrides():
    from src.train import build_parser, config_from_args

    args = build_parser().parse_args([
        "--preset", "smoke",
        "--lr", "5e-4",
        "--lr-end", "1e-5",
        "--lr-schedule", "cosine",
        "--lr-warmup-updates", "5",
        "--weight-decay", "1e-4",
    ])
    cfg = config_from_args(args)
    assert cfg.lr == pytest.approx(5e-4)
    assert cfg.lr_end == pytest.approx(1e-5)
    assert cfg.lr_schedule == "cosine"
    assert cfg.lr_warmup_updates == 5
    assert cfg.weight_decay == pytest.approx(1e-4)

    ppo = cfg.ppo_config()
    assert ppo.lr == pytest.approx(5e-4)
    assert ppo.lr_end == pytest.approx(1e-5)
    assert ppo.lr_schedule == "cosine"
    assert ppo.lr_warmup_updates == 5
    assert ppo.weight_decay == pytest.approx(1e-4)

    # Backwards compatibility: older checkpoint configs without new LR fields.
    legacy = cfg.to_dict()
    for key in ("lr_end", "lr_schedule", "lr_warmup_updates"):
        legacy.pop(key)
    restored = TrainConfig(**legacy)
    assert restored.lr_schedule == "linear"
    assert restored.lr_end == 0.0
    assert restored.lr_warmup_updates == 0

    with pytest.raises(ValueError):
        TrainConfig.from_preset("smoke", lr_schedule="invalid")
    with pytest.raises(ValueError):
        TrainConfig.from_preset("smoke", lr=-1.0)
    with pytest.raises(ValueError):
        TrainConfig.from_preset("smoke", lr_warmup_updates=-1)
