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


def _clone(ns):
    if isinstance(ns, SimpleNamespace):
        return SimpleNamespace(**{k: _clone(v) for k, v in vars(ns).items()})
    if isinstance(ns, list):
        return [_clone(v) for v in ns]
    return ns


def table(p: SimpleNamespace, name: str) -> SimpleNamespace:
    """Params for one table: the defaults with that [[tables]] entry's sections merged on top."""
    for t in getattr(p, "tables", []):
        if t.name == name:
            break
    else:
        raise KeyError(f"no [[tables]] named {name!r}")
    q = _clone(p)
    for key, val in vars(t).items():
        if isinstance(val, SimpleNamespace):
            sec = getattr(q, key, None)
            if sec is None:
                setattr(q, key, _clone(val))
            else:
                for k, v in vars(val).items():
                    setattr(sec, k, _clone(v))
    q.table_name, q.table_label = t.name, getattr(t, "label", t.name)
    return q


def tables(p: SimpleNamespace) -> list[SimpleNamespace]:
    return [table(p, t.name) for t in getattr(p, "tables", [])]
