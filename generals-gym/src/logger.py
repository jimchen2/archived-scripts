"""Tiny CSV/JSON run logger (no external dependencies)."""

from __future__ import annotations

import csv
import json
import time
from collections.abc import Iterable
from pathlib import Path


class RunLogger:
    """Append rows to ``metrics.csv`` and keep a ``config.json`` sidecar."""

    def __init__(self, run_dir: str | Path, filename: str = "metrics.csv",
                 append: bool = False):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.run_dir / filename
        self._fieldnames: list[str] | None = None
        if append and self.path.exists():
            with self.path.open(newline="") as fh:
                self._fieldnames = next(csv.reader(fh), None)
        self._start = time.perf_counter()

    def write_config(self, config: dict) -> None:
        (self.run_dir / "config.json").write_text(json.dumps(config, indent=2))

    def log(self, row: dict) -> None:
        """Append one row; the header is taken from the first row."""
        if self._fieldnames is None:
            self._fieldnames = list(row.keys())
            with self.path.open("w", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=self._fieldnames)
                writer.writeheader()
        with self.path.open("a", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=self._fieldnames, extrasaction="ignore")
            writer.writerow({k: _fmt(v) for k, v in row.items()})

    @property
    def elapsed(self) -> float:
        return time.perf_counter() - self._start


def _fmt(value):
    if isinstance(value, float):
        return f"{value:.6g}"
    return value


def print_row(row: dict, keys: Iterable[str]) -> None:
    """Print a compact one-line summary of the selected metrics."""
    parts = []
    for key in keys:
        if key not in row:
            continue
        value = row[key]
        if isinstance(value, float):
            parts.append(f"{key} {value:.4g}")
        else:
            parts.append(f"{key} {value}")
    print(" | ".join(parts), flush=True)
