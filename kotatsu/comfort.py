"""Sitting comfort: clearance for the owner's cross-legged posture (params [comfort]).

The knees (knee_w wide, up to knee_h high) sit at the table edge. Anything of the frame lower than
knee_h must stay out of a knee_w-wide strip running in from the top's edge at mid-side; the heater
too, if it hangs lower than knee_h. Coordinates here are centred on the table (plan view, mm).
"""
from __future__ import annotations

import math

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from . import frame


def low_footprint(p, z: float, z_lo: float = -10.0):
    """Plan footprint (centred) of leg material between heights z_lo and z: the legs, mostly."""
    L, t = frame.layout(p), p.material.t_max
    c = L.cx
    h = (L.t - t) / 2                                   # thickest stock, centred on the plate's plane
    out = []
    for pt in frame.parts(p):
        if pt.kind != "frame":
            continue
        for pl in pt.placements:
            z0 = pl.matrix[11] if pl.axis == "m" else 0.0  # matrix-placed parts can start above the floor
            low = pt.shape.intersection(box(-1e3, z_lo - z0, 1e4, z - z0))
            for g in getattr(low, "geoms", [low]):
                if g.is_empty:
                    continue
                u0, _, u1, _ = g.bounds
                ox, oy, _ = pl.origin
                a, b = (-u1, -u0) if pl.mirror_u else (u0, u1)
                if pl.axis == "m":                      # a vertical plate placed by matrix (diagonal legs)
                    M = pl.matrix
                    pts = [(M[0] * uu + M[2] * ww + M[3] - L.cx, M[4] * uu + M[6] * ww + M[7] - L.cy)
                           for uu, ww in ((u0, h), (u1, h), (u1, L.t - h), (u0, L.t - h))]
                    out.append(Polygon(pts))
                elif pl.axis == "x":
                    out.append(box(ox + a - c, oy + h - c, ox + b - c, oy + L.t - h - c))
                elif pl.axis == "y":
                    out.append(box(ox + h - c, oy + a - c, ox + L.t - h - c, oy + b - c))
    return unary_union(out)


def knee_reach(p, width: float | None = None, height: float | None = None) -> float:
    """How far (mm) a width x height knee zone, centred on one side, can come in under the top's edge
    before it touches the frame (or the heater, if the heater hangs lower than the knees). Knees higher than
    the frame's top can't come in at all: the top, with the futon squeezed under it, is right above."""
    C = p.comfort
    width = C.knee_w if width is None else width
    height = C.knee_h if height is None else height
    if height > frame.layout(p).H:
        return 0.0
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


def _top_centred(p):
    from shapely.affinity import translate
    from . import top
    return translate(top.build(p).outline, -p.top.length / 2, -p.top.width / 2)


def _lever_min(W: float, support, top_outline, inset: float, steps: int = 144) -> tuple[float, float]:
    """Smallest push W * h / (r - h) over all directions: h = support hull's reach, r = how far out the
    push point can be (the top's edge, `inset` in). Returns (N, direction in degrees)."""
    pts = list(support.convex_hull.exterior.coords)
    edge = top_outline.buffer(-inset) if inset > 0 else top_outline
    tpts = list(edge.exterior.coords)
    best = (float("inf"), 0.0)
    for i in range(steps):
        a = 2 * math.pi * i / steps
        dx, dy = math.cos(a), math.sin(a)
        h = max(x * dx + y * dy for x, y in pts)
        rr = max(x * dx + y * dy for x, y in tpts)
        F = W * h / (rr - h) if rr > h else float("inf")
        best = min(best, (F, math.degrees(a)))
    return best


def tip_load(p, inset: float | None = None) -> float:
    """Smallest downward push (N) on the top that tips the whole table, applied `inset` in from the
    top's edge (default comfort.tip_inset = 50 mm, the EN 12521 / EN 1730 loading point), in the worst
    direction. It pivots on the outermost feet. Assumes the feet don't slide; the weight includes a
    guessed heater + futon."""
    inset = getattr(p.comfort, "tip_inset", 0.0) if inset is None else inset
    return _lever_min(weight_n(p), low_footprint(p, 1.0), _top_centred(p), inset)[0]


def top_supports(p):
    """Plan footprint (centred) of what the top (over the futon) rests on: frame material at full height."""
    H = frame.layout(p).H
    return low_footprint(p, H + 1, H - 0.6)


def top_lift(p, inset: float | None = None) -> tuple[float, float]:
    """Smallest downward push (N), `inset` in from the top's edge, that lifts the loose top's far side off
    its supports, and the direction (deg) it happens in. The top pivots on the outermost support line."""
    inset = getattr(p.comfort, "tip_inset", 0.0) if inset is None else inset
    top_o = _top_centred(p)
    W = top_o.area / 1e6 * p.material.t_nominal / 1000 * p.material.density_kg_m3 * 9.81
    return _lever_min(W, top_supports(p), top_o, inset)


def _n(x: float):
    """Round a force for reports; None when it never happens (infinite)."""
    return round(x) if math.isfinite(x) else None


def summary(p) -> dict:
    C = p.comfort
    return {"knee_w": C.knee_w, "knee_h": C.knee_h, "reach": round(knee_reach(p), 1),
            "tip_n": _n(tip_load(p)), "tip_edge_n": _n(tip_load(p, 0.0)),
            "top_lift_n": _n(top_lift(p)[0]), "top_lift_edge_n": _n(top_lift(p, 0.0)[0]),
            "tip_inset": getattr(C, "tip_inset", 0.0), "tip_min_n": C.tip_min_n,
            "reach_min": C.knee_reach_min,
            "side_clear": side_clear(p),
            "shin_w": round(p.top.length - 2 * p.frame.overhang - 2 * low_footprint_leg_u(p, C.knee_h), 1),
            "legroom": round(legroom(p), 1)}


def legs_forward(p, seat: float) -> dict:
    """Sitting with the legs out under the table (on a zaisu: comfort.chair_seat_h), the sitting surface `seat` mm off the floor:
    room (mm, after leg_margin) above the thighs, which pass under the deck at mid-side, and above the feet,
    under the heater. Heels stay on the floor, so the seat raises the thighs but not the feet."""
    C = p.comfort
    (_, _, sz), (_, _, hz) = frame.heater_box(p)
    return {"thigh_room": round(side_clear(p) - C.leg_margin - (seat + C.thigh_h), 1),
            "feet_room": round(hz - sz / 2 - C.leg_margin - C.foot_h, 1)}


def side_clear(p) -> float:
    """Clear height at the middle of each side: the deck's underside (no aprons)."""
    return frame.layout(p).z_deck_bot


def legroom(p, step: float = 10.0) -> float:
    """Narrowest room between two legs on a side (mm), from 20 mm off the floor up to the thighs' top when
    sitting legs forward on the zaisu (seat + thigh + margin): where shins and thighs pass between the legs."""
    C = p.comfort
    z1 = C.chair_seat_h + C.thigh_h + C.leg_margin
    zs = [20.0 + i * step for i in range(int((z1 - 20.0) // step) + 1)] + [z1]
    return min(p.top.length - 2 * p.frame.overhang - 2 * low_footprint_leg_u(p, z) for z in zs)


def low_footprint_leg_u(p, z: float) -> float:
    """How far (mm) the legs at a corner reach along a side from the frame's corner at height z: the frame
    material between z - 0.5 and z at the (-, -) corner, measured along x (any leg style)."""
    half = frame.layout(p).Lf / 2
    fp = low_footprint(p, z, z - 0.5)
    near = [g for g in getattr(fp, "geoms", [fp]) if not g.is_empty and g.centroid.x < 0 and g.centroid.y < 0]
    return max(g.bounds[2] for g in near) + half
