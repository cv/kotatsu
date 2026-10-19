"""Load params.toml into a plain nested dict with attribute access."""
from __future__ import annotations

import tomllib
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent


def _ns(d):
    if isinstance(d, list):
        return [_ns(v) for v in d]
    if isinstance(d, dict):
        return SimpleNamespace(**{k: _ns(v) for k, v in d.items()})
    return d


def load(path: Path | str = ROOT / "params.toml") -> SimpleNamespace:
    with open(path, "rb") as f:
        return _ns(tomllib.load(f))
