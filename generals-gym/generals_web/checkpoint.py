"""Server-side trained opponent with one recurrent memory per game."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import jax

from src.play import load_policy


class CheckpointPolicy:
    """Immutable, shared policy weights; mutable memory belongs to each game."""

    def __init__(self, run_dir: str, tag: str = "latest") -> None:
        # Avoid Checkpoint's mkdir-on-load behavior for an invalid path.
        directory = Path(run_dir) / "checkpoints"
        if not directory.is_dir():
            raise ValueError(f"checkpoint directory not found: {directory}")
        try:
            self.cfg, self.net, self.params, self.tag = load_policy(run_dir, tag)
        except (OSError, KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"could not load checkpoint {tag!r} from {directory}: {exc}") from exc
        template = self.net.init(jax.random.PRNGKey(0))
        expected = jax.tree_util.tree_leaves(template)
        actual = jax.tree_util.tree_leaves(self.params)
        if len(actual) != len(expected) or any(a.shape != e.shape for a, e in zip(actual, expected)):
            raise ValueError(f"checkpoint {tag!r} parameters do not match its configuration")
        if self.cfg.height != self.cfg.width or not 5 <= self.cfg.height <= 31:
            raise ValueError("web checkpoint games require a square board between 5 and 31")
        self.env_config = replace(self.cfg.env_config(), half_moves=True)
        self.infer = jax.jit(lambda params, grid, scalars, mask, memory:
                             self.net.step(params, grid, scalars, mask, memory, sample=False))

    def initial_memory(self):
        return self.net.batched_initial_memory(())

    def action(self, env, state, memory):
        obs = env.observe(state, 1)
        # Training uses five direction codes; the web engine uses nine to let
        # humans split. Preserve the policy's action space and translate back.
        mask = env.action_mask(state)[1].reshape(-1, env.config.dir_actions)
        mask = mask[:, :self.net.config.dir_actions].reshape(-1)
        out = self.infer(self.params, obs.grid, obs.scalars, mask, memory)
        tile, direction = divmod(int(out.action), self.net.config.dir_actions)
        return tile * env.config.dir_actions + direction, out.memory
