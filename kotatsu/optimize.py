"""Small design search: cheapest estimated uMake order (kotatsu/price.py) that still meets the limits.

Knobs are the things the owner left open (frame size, slim-leg concept and top are fixed):
deck notch neck / margin, haunch height and slope. Limits: shipping weight (uMake-calibrated), sway,
leg stress, knee reach and leg room, and every part still router-cuttable.
Run: uv run python -m kotatsu.optimize
"""
from __future__ import annotations

import itertools

from . import comfort, frame, geom, params, price, stiffness, top

WEIGHT_MAX = 18.9       # kg, the heaviest order uMake has shipped free for us (20.4 was not)
SWAY_MAX = 1.0          # mm at 100 N sideways, either direction
LEG_MPA_MAX = 3.0
UMAKE_KG = 20.4 / 20.85  # our weight model -> uMake's cart weight (calibrated)

GRID = {
    ("deck", "neck"): [50.0, 70.0, 90.0],
    ("deck", "window_margin"): [15.0, 20.0],
    ("yagura", "leg_haunch_top"): [300.0, 320.0],
    ("yagura", "leg_haunch_drop"): [20.0, 30.0, 45.0],
}


def weight_kg(p) -> float:
    t, rho = p.material.t_nominal / 1000, p.material.density_kg_m3
    a = top.build(p).outline.area + sum(pt.shape.area * pt.qty for pt in frame.parts(p))
    return a / 1e6 * 0.019 * 700 * UMAKE_KG if t else 0.0


def evaluate(p) -> dict:
    parts = frame.parts(p)
    ok = all(pt.shape.geom_type == "Polygon" and geom.router_cuttable(pt.shape, p.cnc.bit_d / 2) for pt in parts)
    e = price.estimate(p)
    c = comfort.summary(p)
    s = stiffness.summary(p)
    sway = max(s["x"]["sway_mm"]["100"], s["y"]["sway_mm"]["100"])
    r = {"price": e["subtotal"], "cut_m": e["cut_m"], "kg": round(weight_kg(p), 2), "sway": sway,
         "leg_MPa": float(s["stress"]["leg_MPa"]), "reach": c["reach"], "shin": c["shin_w"], "cuttable": ok}
    r["feasible"] = (ok and r["kg"] <= WEIGHT_MAX and sway <= SWAY_MAX and r["leg_MPa"] <= LEG_MPA_MAX
                     and c["reach"] >= p.comfort.knee_reach_min)
    return r


def search(grid=GRID) -> list[dict]:
    keys = list(grid)
    out = []
    for vals in itertools.product(*grid.values()):
        p = params.tables(params.load())[0]
        for (sec, k), v in zip(keys, vals):
            setattr(getattr(p, sec), k, v)
        try:
            r = evaluate(p)
        except Exception as ex:          # a knob combination that breaks the geometry
            r = {"feasible": False, "error": str(ex)[:80]}
        r["knobs"] = {f"{s}.{k}": v for (s, k), v in zip(keys, vals)}
        out.append(r)
    return sorted(out, key=lambda r: (not r["feasible"], r.get("price", 1e9)))


def main():
    base = evaluate(params.tables(params.load())[0])
    print("current:", base)
    res = search()
    for r in res[:8]:
        print(r)
    print("infeasible:", sum(not r["feasible"] for r in res), "of", len(res))


if __name__ == "__main__":
    main()
