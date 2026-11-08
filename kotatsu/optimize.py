"""Design-space search: what each improvement costs, mapped as the best trade-offs (a Pareto front).

Knobs and their ranges are in params.toml [optimize.knobs]; everything else stays as designed.
  Stage 1 (cheap, every sample): the parts build as single router-cuttable outlines that fit the box; the
          order's price (kotatsu/price.py), its uMake cart weight and free shipping; knee reach and the room
          between the legs where shins and thighs pass (comfort.legroom). A scrambled Sobol sample of [optimize] samples designs.
  Stage 2 (FEA): plate A under fea.push_n (sway and worst share of strength), plate B's share with the top's
          corner load, and the deck's three hard hand cases (wedges tight). First on designs spread from slim to
          sturdy, then on small changes around the best so far ([optimize] refine_*), up to fea_budget in all.
Goals: price and the legs' visible width (looks.py), equally weighted; strength, sway, leg room, knee reach and
free shipping are limits. The result: every point, the front over (price, look), three picks next to the
current design, in out/optimize/results.json, map.png and legs.png (the picks' leg plates, to judge by eye).
Run: uv run python -m kotatsu.optimize  (or make optimize). Worker processes run the checks in parallel.
"""
from __future__ import annotations

import json
import math
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from . import comfort, frame, geom, looks, params, price

OUT = Path("out/optimize")
UMAKE_KG = 20.4 / 20.85          # our weight model -> uMake's cart weight (calibrated, docs/quote.md)
OBJECTIVES = ("price", "look")   # both minimised: the order's price and the legs' visible width (looks.py).
# Strength, sway, leg room, knee reach and free shipping are limits, not goals (owner 2026-11: "functional aspects
# taken care of, economics and looks are about as important"). The balanced pick weighs 1 % cheaper = 1 % slimmer.


def knob_ranges(p) -> dict[str, tuple[float, float]]:
    return {k: (float(v[0]), float(v[1])) for k, v in vars(p.optimize.knobs).items()}


def current_knobs(p) -> dict[str, float]:
    out = {}
    for k in knob_ranges(p):
        sec, name = k.split(".")
        out[k] = float(getattr(getattr(p, sec), name))
    return out


def design(knobs: dict[str, float]):
    """Fresh parameters with the knobs applied."""
    p = params.tables(params.load())[0]
    for k, v in knobs.items():
        sec, name = k.split(".")
        setattr(getattr(p, sec), name, float(v))
    return p


def weight_kg(p) -> float:
    """The order's weight as uMake's cart counts it (kg)."""
    rho = p.material.density_kg_m3 * p.material.t_nominal / 1e9
    return sum(g.area * rho * q for _, g, q in price.parts(p)) * UMAKE_KG


def cheap(knobs: dict[str, float]) -> dict:
    """Stage 1: the checks that take a fraction of a second."""
    r = {"knobs": knobs}
    try:
        p = design(knobs)
        if p.yagura.leg_foot_w > p.yagura.leg_narrow:
            return {**r, "ok": False, "why": "the foot is wider than the leg"}
        parts = frame.parts(p)
        R = p.cnc.bit_d / 2
        for pt in parts:
            g = pt.shape
            if g.geom_type != "Polygon" or not g.is_valid or not geom.router_cuttable(g, R):
                return {**r, "ok": False, "why": f"{pt.name}: not one cuttable outline"}
            x0, y0, x1, y1 = g.bounds
            if max(x1 - x0, y1 - y0) + 50 > p.shipping.box_max:
                return {**r, "ok": False, "why": f"{pt.name}: too big for the box"}
        c = comfort.summary(p)
        e = price.estimate(p)
        kg = weight_kg(p)
        r.update(price=e["subtotal"], cut_m=e["cut_m"], kg=round(kg, 3), reach=c["reach"], room=c["legroom"],
                 neg_room=-c["legroom"], look=round(looks.leg_width(p), 2))
        why = []
        if kg > p.shipping.free_kg:
            why.append("too heavy for free shipping")
        if c["reach"] < p.comfort.knee_reach_min:
            why.append("knees don't reach under the top")
        if c["legroom"] < p.comfort.legroom_min:
            why.append("too little room between the legs")
        r.update(ok=not why, why="; ".join(why))
    except Exception as ex:                    # a knob combination that breaks the geometry
        r.update(ok=False, why=f"geometry: {str(ex)[:90]}")
    return r


_TOP = None


def _init(top_load):
    global _TOP
    _TOP = top_load


def heavy(knobs: dict[str, float]) -> dict:
    """Stage 2: the FEA (about 20 s). Use of strength is Tsai-Hill, contact ends left out (local bearing)."""
    from . import fea
    p = design(knobs)
    O = p.optimize
    worst = lambda zones: max(v["tsai_hill"] for k, v in zones.items() if k != "contact edges")
    a = fea.leg_case(p, "A", p.fea.push_n, None, h=O.fea_leg_h)
    b = fea.leg_case(p, "B", p.fea.push_n, _TOP, h=O.fea_leg_h)
    deck = {}
    for name, ld in fea.deck_cases(p).items():
        if "whole ring" in name:               # the spread hand never governs
            continue
        d = fea.deck_case(p, ld, h=O.fea_deck_h, wedges=True)
        deck[name] = max(d[k]["tsai_hill"] for k in ("fillets", "arms", "ring", "pads"))
    use = {"leg A": worst(a["zones"]), "leg B": worst(b["zones"]), "deck": max(deck.values())}
    return {"sway": float(a["sway_mm"]), "use": max(use.values()), "use_by_part": {k: round(v, 3) for k, v in use.items()}}


def nondominated(rows: list[dict], keys=OBJECTIVES) -> list[int]:
    """Indices of rows no other row beats on every key (and strictly on one)."""
    X = np.array([[r[k] for k in keys] for r in rows], dtype=float)
    keep = []
    for i in range(len(X)):
        d = np.all(X <= X[i], axis=1) & np.any(X < X[i], axis=1)
        if not d.any():
            keep.append(i)
    return keep


def fronts(rows: list[dict], keys) -> list[list[int]]:
    """Non-dominated sorting: front 0, then the front of what's left, and so on."""
    left, out = list(range(len(rows))), []
    while left:
        f = [left[i] for i in nondominated([rows[i] for i in left], keys)]
        out.append(f)
        left = [i for i in left if i not in f]
    return out


def sample(p, n: int, seed: int) -> list[dict[str, float]]:
    from scipy.stats import qmc
    rng = knob_ranges(p)
    s = qmc.Sobol(len(rng), scramble=True, seed=seed).random(2 ** math.ceil(math.log2(max(n, 2))))[:n]
    lo = np.array([v[0] for v in rng.values()]); hi = np.array([v[1] for v in rng.values()])
    pts = lo + s * (hi - lo)
    return [{k: round(float(x), 1) for k, x in zip(rng, row)} for row in pts]


def score(r: dict, cur: dict) -> float:
    """Equal weight to economics and looks: the relative change in price plus the relative change in leg width."""
    return (r["price"] / cur["price"] - 1) + (r["look"] / cur["look"] - 1)


def picks(rows: list[dict], cur: dict) -> dict:
    """Readable choices among the designs that pass every limit."""
    if not rows:
        return {}
    return {"slimmest": min(rows, key=lambda r: (r["look"], r["price"])),
            "cheapest": min(rows, key=lambda r: (r["price"], r["look"])),
            "balanced (1 % cheaper = 1 % slimmer)": min(rows, key=lambda r: score(r, cur))}


def spread(rows: list[dict], n: int) -> list[dict]:
    """n designs spread evenly over the range of leg widths (cheaper first where they're close)."""
    if n <= 0 or not rows:
        return []
    srt = sorted(rows, key=lambda r: (r["look"], r["price"]))
    idx = sorted({round(i * (len(srt) - 1) / max(n - 1, 1)) for i in range(n)})
    return [srt[i] for i in idx]


def mutate(p, knobs: dict, k: int, step: float, rng) -> list[dict]:
    ranges = knob_ranges(p)
    out = []
    for _ in range(k):
        out.append({n: round(float(np.clip(knobs[n] + rng.normal(0, step * (hi - lo)), lo, hi)), 1)
                    for n, (lo, hi) in ranges.items()})
    return out


def _fea_all(rows: list[dict], workers: int, top_load, O) -> None:
    if not rows:
        return
    with ProcessPoolExecutor(workers, initializer=_init, initargs=(top_load,)) as ex:
        for r, h in zip(rows, ex.map(heavy, [r["knobs"] for r in rows])):
            r.update(h)
            r["feasible"] = r["use"] <= O.use_max and r["sway"] <= O.sway_max


def run(samples: int | None = None, fea_budget: int | None = None, workers: int | None = None) -> dict:
    p = params.tables(params.load())[0]
    O = p.optimize
    samples = O.samples if samples is None else samples
    fea_budget = O.fea_budget if fea_budget is None else fea_budget
    workers = workers or os.cpu_count() or 2
    cur_k = current_knobs(p)
    pts = [cur_k] + sample(p, samples, int(O.seed))
    with ProcessPoolExecutor(workers) as ex:
        stage1 = list(ex.map(cheap, pts, chunksize=8))
    ok = [r for r in stage1 if r.get("ok")]
    if not ok or ok[0]["knobs"] != cur_k:
        raise RuntimeError("the current design fails the cheap checks: " + stage1[0].get("why", "?"))
    from . import fea
    top_load = fea.top_on_legs(p)
    n_ref = int(round(fea_budget * O.refine_share))
    chosen = [ok[0]] + spread(ok[1:], fea_budget - 1 - n_ref)
    _fea_all(chosen, workers, top_load, O)                      # explore: slim to sturdy
    cur = chosen[0]
    rng = np.random.default_rng(int(O.seed))
    seen = {json.dumps(r["knobs"], sort_keys=True) for r in chosen}
    good = sorted([r for r in chosen if r.get("feasible")], key=lambda r: score(r, cur))
    seeds = (good[: int(O.refine_seeds)] + [min(good, key=lambda r: r["look"])]) if good else []
    if seeds and n_ref > 0:                                     # refine: around the best, and the slimmest that passes
        cands = [m for s in seeds for m in mutate(p, s["knobs"], max(1, 3 * n_ref // len(seeds)), O.refine_step, rng)]
        cands = [m for m in cands if json.dumps(m, sort_keys=True) not in seen]
        with ProcessPoolExecutor(workers) as ex:
            more = [r for r in ex.map(cheap, cands, chunksize=4) if r.get("ok")]
        more = sorted(more, key=lambda r: score(r, cur))[:n_ref]
        _fea_all(more, workers, top_load, O)
        chosen += more
    done = [r for r in chosen if r.get("feasible")]
    front = [done[i] for i in nondominated(done)] if done else []
    return {"knobs": knob_ranges(p), "current": cur, "stage1": {"tried": len(stage1), "ok": len(ok)},
            "fea": chosen, "front": front, "picks": picks(done, cur),
            "limits": {"use_max": O.use_max, "sway_max": O.sway_max, "free_kg": p.shipping.free_kg,
                       "legroom_min": p.comfort.legroom_min}}


def draw(res: dict, path: Path) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 3, figsize=(16, 5))
    pts = [r for r in res["fea"] if "use" in r]
    fr = {json.dumps(r["knobs"], sort_keys=True) for r in res["front"]}
    on = lambda r: json.dumps(r["knobs"], sort_keys=True) in fr
    cur = res["current"]
    for ax, (x, y, xl, yl) in zip(axs, (("look", "price", "legs' average visible width (mm): slimmer to the left", "order before tax ($)"),
                                        ("look", "use", "legs' average visible width (mm)", "worst share of strength"),
                                        ("look", "room", "legs' average visible width (mm)", "room between the legs (mm)"))):
        for r in pts:
            f = on(r)
            ax.scatter(r[x], r[y], s=28 if f else 12, c="#c0392b" if f else "#b9b9b9",
                       alpha=0.9 if r.get("feasible") else 0.35, marker="o" if r.get("feasible") else "x", zorder=3 if f else 2)
        ax.scatter(cur[x], cur[y], s=160, marker="*", c="#1f4e79", zorder=5, label="the current design")
        ax.set_xlabel(xl); ax.set_ylabel(yl); ax.grid(alpha=0.3)
    axs[0].legend(loc="upper right")
    fig.suptitle("Design space: red = best trade-offs (Pareto front), grey = beaten, x = fails a limit", x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(path, dpi=80)
    plt.close(fig)
    return path


def draw_legs(res: dict, path: Path) -> Path:
    """Plates A and B of the current design and of each pick, side by side at one scale, to judge the looks."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows = [("current", res["current"])] + list(res["picks"].items())
    fig, axs = plt.subplots(1, len(rows), figsize=(3.2 * len(rows), 5.2))
    for ax, (name, r) in zip(np.atleast_1d(axs), rows):
        p = design(r["knobs"])
        zs = frame.layout(p).z_deck_bot
        x = 0.0
        for pt in [q for q in frame.parts(p) if q.name in ("leg plate A", "leg plate B")]:
            g = pt.shape
            gx = g.bounds[0]
            for ring in [g.exterior, *g.interiors]:
                xs, ys = ring.xy
                ax.fill([a - gx + x for a in xs], ys, color="#e9dcc0" if ring is g.exterior else "white", ec="#6b4f2a", lw=0.8)
            x += (g.bounds[2] - g.bounds[0]) + 25
        ax.axhline(zs, color="#888", lw=0.6, ls="--")
        ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(f"{name}\n{r['look']:.1f} mm wide, ${r['price']:.2f}\nsway {r.get('sway', float('nan')):.1f} mm, "
                     f"{100 * r.get('use', float('nan')):.0f} % of strength", fontsize=9)
    fig.suptitle("Leg plates A and B (dashed: the deck's underside; the legs show below it)", x=0.01, ha="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=80)
    plt.close(fig)
    return path


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--samples", type=int); ap.add_argument("--fea", type=int); ap.add_argument("--workers", type=int)
    a = ap.parse_args()
    res = run(a.samples, a.fea, a.workers)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(res, indent=1))
    draw(res, OUT / "map.png")
    draw_legs(res, OUT / "legs.png")
    f = lambda r: (f"${r['price']:.2f}  legs {r['look']:.1f} mm wide  sway {r['sway']:.1f} mm  use {100 * r['use']:.0f} %  "
                   f"room {r['room']:.0f} mm  {r['kg']:.2f} kg  {r['knobs']}")
    print(f"[optimize] {res['stage1']['ok']} of {res['stage1']['tried']} designs pass the cheap checks; "
          f"{len(res['fea'])} through the FEA; {len(res['front'])} on the front")
    print("  current:", f(res["current"]))
    for k, r in res["picks"].items():
        print(f"  {k}:", f(r))


if __name__ == "__main__":
    main()
