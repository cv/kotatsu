"""uMake price estimate, fitted from real quotes (docs/quote.md). TODO: refit when prices drift.

Per part (Baltic birch, CNC router):
    raw = A_RATE * bounding_box_m2 + L_RATE * cut_length_m        (no per-file or per-hole fee)
Material is charged by each part's **bounding box**, not the wood in it (v2 full quote, 2026-11: this fits
all 10 lines within 2 %, true area only within 38 %). So cut-outs and windows save weight, not money: they
only add cutting. The order total is then a fixed amount per order plus a rate on the raw total:
    total ~= FIXED + PER_RAW * raw_total
fitted (least squares, owner 2026-11) on all five 15mm quotes, each re-priced with the parts of the commit it
quoted: $328.70, $328.53, $328.40 (tables with the "+" legs), $306.84 (quote 2926, the current design) and $501.66
(a table and two plywood zaisu, since archived); every one within 1.4 %. (The earlier curve, K * raw ** B fitted
on two of them, read the current design 4 % low; a three-parameter curve matched all five within 0.1 % but is an
overfit, with a $240 order of nothing.) The total is split between the parts in proportion to raw. Thicker stock
(v1's 19mm order) costs more than this predicts.
Cutting is about half the raw cost of this design; one more metre of cutting costs about as much as
0.09 m2 more bounding box.
"""
from __future__ import annotations

from . import frame, top

A_RATE, L_RATE = 64.17, 5.84     # per m2 of bounding box, per m of cut (raw units, before the volume curve)
FIXED, PER_RAW = 166.47, 0.6693  # total = FIXED + PER_RAW * raw  (five 15mm quotes, 2026-11)


def features(g) -> tuple[float, float, int]:
    """(area m2, cut length m, holes): what the part is, for reports."""
    L = g.exterior.length + sum(i.length for i in g.interiors)
    return g.area / 1e6, L / 1000, len(g.interiors)


def bbox_m2(g) -> float:
    x0, y0, x1, y1 = g.bounds
    return (x1 - x0) * (y1 - y0) / 1e6


def raw(g) -> float:
    return A_RATE * bbox_m2(g) + L_RATE * features(g)[1]


def parts(p) -> list[tuple[str, object, int]]:
    out = [("top", top.build(p).outline, 1)]
    out += [(pt.name, pt.shape, pt.qty) for pt in frame.parts(p) if pt.ordered]
    return out


def estimate(p) -> dict:
    rows = [(n, raw(g) * q, q) for n, g, q in parts(p)]
    R = sum(r for _, r, _ in rows)
    T = FIXED + PER_RAW * R
    cut = sum(features(g)[1] * q for _, g, q in parts(p))
    return {"subtotal": round(T, 2), "raw": round(R, 2), "cut_m": round(cut, 1),
            "marginal_per_raw": PER_RAW,
            "by_part": {n: round(r * T / R, 2) for n, r, _ in rows}}
