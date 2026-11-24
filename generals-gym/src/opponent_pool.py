"""Bounded FIFO of frozen policies used for historical self-play."""
from __future__ import annotations

from pathlib import Path

import jax
import jax.numpy as jnp
import numpy as np


class OpponentPool:
    """Keep the most recent snapshots; active games hold their own copies."""

    def __init__(self, capacity: int, initial_params):
        if capacity < 1:
            raise ValueError("opponent pool capacity must be positive")
        self.capacity = capacity
        self.snapshots = [initial_params]

    def add(self, params):
        self.snapshots.append(params)
        if len(self.snapshots) > self.capacity:
            self.snapshots.pop(0)

    def stacked(self):
        """Stack and pad to capacity so additions do not trigger recompilation."""
        padded = self.snapshots + [self.snapshots[-1]] * (self.capacity - len(self.snapshots))
        return jax.tree_util.tree_map(lambda *xs: jnp.stack(xs), *padded)

    def save(self, path):
        occupied = jax.tree_util.tree_map(lambda *xs: jnp.stack(xs), *self.snapshots)
        leaves = jax.tree_util.tree_leaves(occupied)
        np.savez(path, count=np.asarray(len(self.snapshots)),
                 **{f"arr_{i}": np.asarray(x) for i, x in enumerate(leaves)})

    @classmethod
    def load(cls, path, capacity, template):
        path = Path(path)
        leaves, treedef = jax.tree_util.tree_flatten(template)
        with np.load(path, allow_pickle=False) as data:
            count = int(data["count"])
            arrays = [data[f"arr_{i}"] for i in range(len(leaves))]
            if count < 1 or any(a.shape[0] < count or a.shape[1:] != leaf.shape
                                for a, leaf in zip(arrays, leaves)):
                raise ValueError(f"invalid or incompatible opponent pool: {path}")
            # Capacity can be reduced on resume; keep the newest snapshots.
            snapshots = [jax.tree_util.tree_unflatten(
                treedef, [jnp.asarray(a[i], dtype=leaf.dtype)
                          for a, leaf in zip(arrays, leaves)])
                for i in range(max(0, count - capacity), count)]
        pool = cls(capacity, snapshots[0])
        pool.snapshots = snapshots
        return pool


def sample_opponents(pool_params, count, key, num_envs):
    """Uniformly sample a frozen policy for each environment."""
    indices = jax.random.randint(key, (num_envs,), 0, count)
    return jax.tree_util.tree_map(lambda x: x[indices], pool_params)
