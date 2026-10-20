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
        low = pt.shape.intersection(box(-10, -10, 1e4, z))
        for g in getattr(low, "geoms", [low]):
            if g.is_empty:
                continue
            u0, _, u1, _ = g.bounds
            for pl in pt.placements:
                ox, oy, _ = pl.origin
                if pl.axis == "x":
                    out.append(box(ox + u0 - c, oy - c, ox + u1 - c, oy + t - c))
                else:
                    out.append(box(ox - c, oy + u0 - c, ox + t - c, oy + u1 - c))
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


def tip_load(p) -> float:
    """Downward push (N) on the top's edge, at mid-side (the worst direction), that tips the table:
    it pivots on the feet at the panel ends, Lf/2 + foot_flare out from the centre."""
    L = frame.layout(p)
    lp = frame.long_panel(p)
    foot = lp.intersection(box(-1e3, -1, 1e4, 1.0))     # what actually touches the floor
    xf = L.Lf / 2 - foot.bounds[0]
    R = p.top.length / 2
    return weight_n(p) * xf / (R - xf)


def summary(p) -> dict:
    C = p.comfort
    return {"knee_w": C.knee_w, "knee_h": C.knee_h, "reach": round(knee_reach(p), 1),
            "tip_n": round(tip_load(p)), "tip_min_n": C.tip_min_n,
            "reach_min": C.knee_reach_min,
            "apron_clear": p.frame.height - p.frame.apron_depth,
            "shin_w": round(p.top.length - 2 * p.frame.overhang - 2 * low_footprint_leg_u(p, C.knee_h), 1)}


def low_footprint_leg_u(p, z: float) -> float:
    """Leg width (from the panel end) at height z, including the opening's top fillet."""
    sp = frame.short_panel(p)
    low = sp.intersection(box(-10, z - 0.5, 1e4, z))
    return min(g.bounds[2] for g in getattr(low, "geoms", [low]))
