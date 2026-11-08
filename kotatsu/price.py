"""uMake price estimate, fitted from real quotes (docs/quote.md). TODO: refit when prices drift.

Per part (Baltic birch, CNC router):
    raw = A_RATE * bounding_box_m2 + L_RATE * cut_length_m        (no per-file or per-hole fee)
Material is charged by each part's **bounding box**, not the wood in it (v2 full quote, 2026-11: this fits
all 10 lines within 2 %, true area only within 38 %). So cut-outs and windows save weight, not money: they
only add cutting. The order total then follows a volume curve:
    total ~= K * raw_total ** B
fitted on two 15mm quotes ($328.70 for the table alone, $501.66 with two plywood zaisu, since archived). uMake's own share
of the total between the parts is proportional to raw. v1's 19mm order comes out 3 % low (thicker stock).
Cutting is about half the raw cost of this design; one more metre of cutting costs about as much as
0.09 m2 more bounding box.
"""
from __future__ import annotations

from . import frame, top

A_RATE, L_RATE = 64.17, 5.84     # per m2 of bounding box, per m of cut (raw units, before the volume curve)
K, B = 12.45, 0.595              # total = K * raw ** B  (two 15mm quotes, 2026-11)


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
    out += [(pt.name, pt.shape, pt.qty) for pt in frame.parts(p)]
    return out


def estimate(p) -> dict:
    rows = [(n, raw(g) * q, q) for n, g, q in parts(p)]
    R = sum(r for _, r, _ in rows)
    T = K * R ** B
    cut = sum(features(g)[1] * q for _, g, q in parts(p))
    return {"subtotal": round(T, 2), "raw": round(R, 2), "cut_m": round(cut, 1),
            "marginal_per_raw": round(B * T / R, 3),
            "by_part": {n: round(r * T / R, 2) for n, r, _ in rows}}
