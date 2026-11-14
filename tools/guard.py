"""Geometry guard: snapshot every cut part's shape and the key numbers, then report what a change moved.

    uv run python tools/guard.py snapshot   # before a change (writes out/guard.json)
    uv run python tools/guard.py check      # after it: prints GUARD OK, or each part and number that changed

Use it to prove a tidy-up changed nothing, or that a design change changed only what it meant to (AGENTS.md: the
design is ordered; tidy-ups must not move the geometry by accident).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kotatsu import comfort, optimize, params, price, stiffness  # noqa: E402

SNAP = ROOT / "out" / "guard.json"


def state() -> dict:
    p = params.tables(params.load())[0]
    parts = {}
    for name, g, qty in price.parts(p):
        parts[name] = {"qty": qty, "area": round(g.area, 3), "bounds": [round(v, 3) for v in g.bounds],
                       "holes": len(g.interiors), "length": round(g.exterior.length, 3)}
    e = price.estimate(p)
    return {"parts": parts,
            "numbers": {"price": e["subtotal"], "cut_m": e["cut_m"], "kg": round(optimize.weight_kg(p), 4),
                        "legroom": round(comfort.legroom(p), 2),
                        "sway200": stiffness.summary(p)["x"]["sway_mm"]["200"],
                        "twist": stiffness.twist(p)["corner_mm"]}}


def main(cmd: str) -> int:
    now = state()
    if cmd == "snapshot":
        SNAP.parent.mkdir(exist_ok=True)
        SNAP.write_text(json.dumps(now, indent=1))
        print("snapshot written")
        return 0
    old = json.loads(SNAP.read_text())
    bad = []
    for name in sorted(set(old["parts"]) | set(now["parts"])):
        a, b = old["parts"].get(name), now["parts"].get(name)
        if a != b:
            if a is None or b is None:
                bad.append(f"{name}: {'added' if a is None else 'removed'}")
            else:
                diff = ", ".join(f"{k} {a[k]} -> {b[k]}" for k in a if a[k] != b[k])
                bad.append(f"{name}: {diff}")
    for k, v in now["numbers"].items():
        if old["numbers"].get(k) != v:
            bad.append(f"{k}: {old['numbers'].get(k)} -> {v}")
    print("GUARD OK: geometry and numbers unchanged" if not bad else "GUARD FAILED:\n" + "\n".join(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "check"))
