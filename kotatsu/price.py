"""uMake price estimate, fitted from test uploads (docs/quote.md, 2026-10-20). TODO: refit when prices drift.

Per part (Baltic birch "19mm", CNC router):
    raw = A_RATE * area_m2 + L_RATE * cut_length_m + H_RATE * holes        (no per-file fee seen)
The order total then follows a volume curve fitted over orders from $72 to $580 raw:
    total ~= K * raw_total ** B         (so the marginal $ per raw $ falls as the order grows)
Cutting is ~3/4 of the raw cost for this table, so shorter cut paths pay more than less wood.
"""
from __future__ import annotations

from . import frame, top

A_RATE, L_RATE, H_RATE = 101.03, 15.25, 0.18     # $/m2, $/m of cut, $/hole (raw, before the volume curve)
K, B = 11.25, 0.551                              # total = K * raw ** B  (fit: 6 probe states + the real order)


def features(g) -> tuple[float, float, int]:
    L = g.exterior.length + sum(i.length for i in g.interiors)
    return g.area / 1e6, L / 1000, len(g.interiors)


def raw(g) -> float:
    a, l, h = features(g)
    return A_RATE * a + L_RATE * l + H_RATE * h


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
