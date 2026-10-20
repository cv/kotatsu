"""Sitting comfort: clearance for the owner's cross-legged posture (params [comfort]).

The knees (knee_w wide, up to knee_h high) sit at the table edge. Anything of the frame lower than
knee_h must stay out of a knee_w-wide strip running in from the top's edge at mid-side; the heater
too, if it hangs lower than knee_h. Coordinates here are centred on the table (plan view, mm).
"""
from __future__ import annotations

from shapely.geometry import box
from shapely.ops import unary_union

from . import frame


def low_footprint(p, z: float):
    """Plan footprint of side-panel material below height z (the legs, mostly)."""
    L, t = frame.layout(p), p.material.t_max
    c = L.cx
    out = []
    for pt in frame.parts(p):
        if pt.kind != "frame":
            continue
        low = pt.shape.intersection(box(-1e3, -10, 1e4, z))
        for g in getattr(low, "geoms", [low]):
            if g.is_empty:
                continue
            u0, _, u1, _ = g.bounds
            for pl in pt.placements:
                ox, oy, _ = pl.origin
                a, b = (-u1, -u0) if pl.mirror_u else (u0, u1)
                if pl.axis == "x":
                    out.append(box(ox + a - c, oy - c, ox + b - c, oy + t - c))
                elif pl.axis == "y":
                    out.append(box(ox - c, oy + a - c, ox + t - c, oy + b - c))
    return unary_union(out)


def knee_reach(p, width: float | None = None, height: float | None = None) -> float:
    """How far (mm) a width x height knee zone, centred on one side, can come in under the top's edge
    before it touches the frame (or the heater, if the heater hangs lower than the knees)."""
    C = p.comfort
    width = C.knee_w if width is None else width
    height = C.knee_h if height is None else height
    R = p.top.length / 2
    fp = low_footprint(p, height)
    (sx, sy, sz), (_, _, hz) = frame.heater_box(p)
    obstacles = [fp]
    if hz - sz / 2 < height:
        obstacles.append(box(-sx / 2 - 20, -sy / 2 - 20, sx / 2 + 20, sy / 2 + 20))
    obs = unary_union(obstacles)
    lo, hi = 0.0, 2 * R
    if box(-width / 2, R, width / 2, R + 1).intersects(obs):
        return 0.0
    for _ in range(40):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if not box(-width / 2, R - m, width / 2, R + 1).intersects(obs) else (lo, m)
    return lo


def weight_n(p) -> float:
    """Table + heater + futon weight (N): what holds it down against tipping."""
    t, rho = p.material.t_nominal / 1000, p.material.density_kg_m3
    from . import top
    area = top.build(p).outline.area + sum(pt.shape.area * pt.qty for pt in frame.parts(p))
    kg = area / 1e6 * t * rho + p.comfort.heater_kg + p.comfort.futon_kg
    return kg * 9.81


def tip_load(p, inset: float | None = None) -> float:
    """Downward push (N) at mid-side (the worst direction) that tips the table, applied `inset` in from
    the top's edge (default comfort.tip_inset = 50 mm, the EN 12521 / EN 1730 loading point). It pivots
    on the outermost feet. Assumes the feet don't slide; the weight includes a guessed heater + futon."""
    x0, y0, x1, y1 = low_footprint(p, 1.0).bounds         # what actually touches the floor
    xf = min(-x0, -y0, x1, y1)                            # nearest tipping edge (frame is square)
    inset = getattr(p.comfort, "tip_inset", 0.0) if inset is None else inset
    R = p.top.length / 2 - inset
    return weight_n(p) * xf / (R - xf)


def summary(p) -> dict:
    C = p.comfort
    return {"knee_w": C.knee_w, "knee_h": C.knee_h, "reach": round(knee_reach(p), 1),
            "tip_n": round(tip_load(p)), "tip_edge_n": round(tip_load(p, 0.0)),
            "tip_inset": getattr(C, "tip_inset", 0.0), "tip_min_n": C.tip_min_n,
            "reach_min": C.knee_reach_min,
            "apron_clear": side_clear(p),
            "shin_w": round(p.top.length - 2 * p.frame.overhang - 2 * low_footprint_leg_u(p, C.knee_h), 1)}


def side_clear(p) -> float:
    """Clear height at the middle of each side: the deck's underside (no aprons)."""
    return frame.layout(p).z_deck_bot


def low_footprint_leg_u(p, z: float) -> float:
    """Leg width (from the panel end) at height z, including the opening's top fillet."""
    sp = next(pt.shape for pt in frame.parts(p) if pt.kind == "frame")
    low = sp.intersection(box(-1e3, z - 0.5, 1e4, z))
    half = frame.layout(p).Lf / 2                       # pieces at the near end: ear finger, inner leg
    return max(g.bounds[2] for g in getattr(low, "geoms", [low]) if g.bounds[2] < half)
