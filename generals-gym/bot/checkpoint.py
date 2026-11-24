"""Checkpoint helpers: plain ``.npz`` files plus a JSON config sidecar.

Parameters are stored as a flat list of arrays in pytree order; loading
requires a template parameter tree (produced by ``net.init`` with the same
``NetConfig``), which keeps the format simple and framework-free.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path

import jax
import jax.numpy as jnp
import numpy as np


def _params_to_arrays(params: dict) -> list[np.ndarray]:
    return [np.asarray(x) for x in jax.tree_util.tree_leaves(params)]


def save_params(path: str | Path, params: dict) -> None:
    """Save a parameter pytree to ``path`` (``.npz``)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, *_params_to_arrays(params))


def load_params(path: str | Path, template: dict) -> dict:
    """Load parameters saved by :func:`save_params`, using ``template``'s tree."""
    path = Path(path)
    leaves, treedef = jax.tree_util.tree_flatten(template)
    with np.load(path) as data:
        arrays = [
            jnp.asarray(data[f"arr_{i}"], dtype=leaf.dtype)
            for i, leaf in enumerate(leaves)
        ]
    return jax.tree_util.tree_unflatten(treedef, arrays)


def _to_jsonable(value):
    if is_dataclass(value):
        return {k: _to_jsonable(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, (jnp.ndarray, np.ndarray)):
        return np.asarray(value).tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


class Checkpoint:
    """Read/write checkpoints under ``<run_dir>/checkpoints``."""

    def __init__(self, run_dir: str | Path):
        self.run_dir = Path(run_dir)
        self.dir = self.run_dir / "checkpoints"
        self.dir.mkdir(parents=True, exist_ok=True)

    def save(self, tag: str, params: dict, config: dict, metadata: dict | None = None):
        """Save ``tag.npz`` + ``tag.json`` and point ``latest.json`` at it."""
        npz = self.dir / f"{tag}.npz"
        save_params(npz, params)
        payload = {
            "tag": tag,
            "config": _to_jsonable(config),
            "metadata": _to_jsonable(metadata or {}),
        }
        (self.dir / f"{tag}.json").write_text(json.dumps(payload, indent=2))
        (self.dir / "latest.json").write_text(
            json.dumps({"tag": tag, **payload}, indent=2)
        )
        return npz

    def load(self, tag: str = "latest") -> tuple[dict, dict]:
        """Return ``(params, payload)`` for ``tag`` (or the latest checkpoint)."""
        if tag == "latest":
            latest = self.dir / "latest.json"
            if not latest.exists():
                raise FileNotFoundError(f"no checkpoints in {self.dir}")
            tag = json.loads(latest.read_text())["tag"]
        with np.load(self.dir / f"{tag}.npz") as data:
            arrays = {k: np.asarray(data[k]) for k in data.files}
        payload = json.loads((self.dir / f"{tag}.json").read_text())
        return arrays, payload

    @staticmethod
    def restore(arrays: dict, template: dict) -> dict:
        """Turn the ``{name: array}`` mapping back into a parameter pytree."""
        leaves, treedef = jax.tree_util.tree_flatten(template)
        return jax.tree_util.tree_unflatten(
            treedef,
            [jnp.asarray(arrays[f"arr_{i}"], dtype=leaf.dtype)
             for i, leaf in enumerate(leaves)],
        )
