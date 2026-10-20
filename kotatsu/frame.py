"""Frame (yagura): 4 slab side panels + deck + 2 heater cheeks + wedges. Plywood-only joinery.

World coordinates (mm): x and y across the top (origin at the top's bounding-box corner), z up, floor z = 0.
Every part is a flat 2-D shape in its own (u, v) plane, plus a placement:
  axis "x": plate in the x-z plane (u -> x, v -> z, thickness along y)
  axis "y": plate in the y-z plane (u -> y, v -> z, thickness along x)
  axis "z": plate in the x-y plane (u -> x, v -> y, thickness along z)
origin = world position of local (0, 0, 0); the plate occupies [0, t] along its thickness axis.

Joints:
  * cross-laps at the 4 corners: long panels slotted from the top, short panels from the bottom
  * deck: 2 plain through-tenons per long side, one in each leg zone (outside the leg openings, so the
    aprons can stay shallow); no wedges - the cross-laps fix the panel spacing
  * cheeks: 2 tabs each, up through deck slots, locked by flat wedges lying on the deck (cheek_wedge)
Every square-cornered opening (and every male root corner) gets a dogbone for the round bit.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from .geom import rounded_rect


@dataclass
class Placement:
    axis: str                       # "x" | "y" | "z"
    origin: tuple[float, float, float]
    mirror_u: bool = False          # informational: shape already mirrored for this placement


@dataclass
class Part:
    name: str
    shape: Polygon
    placements: list[Placement] = field(default_factory=list)
    spares: int = 0                 # extra copies to cut (not placed)
    kind: str = "frame"             # frame | deck | cheek | wedge
    grain: str = "u"                # face grain along the part's u (slab panels: horizontal) or v (legs: vertical)

    @property
    def qty(self) -> int:
        return len(self.placements) + self.spares


# ----------------------------------------------------------------------------- helpers
def _rd(p) -> float:
    return p.cnc.bit_d / 2 + 0.05   # dogbone radius (a hair over the bit radius)


def dogbone(corner, toward, r) -> Polygon:
    """Circle of radius r through `corner`, centred along the unit bisector `toward`."""
    (x, y), (dx, dy) = corner, toward
    n = math.hypot(dx, dy)
    return Point(x + r * dx / n, y + r * dy / n).buffer(r, quad_segs=16)


def hole(x0, y0, x1, y1, r) -> Polygon:
    """Closed rectangular cut with dogbones in all 4 corners."""
    rect = box(x0, y0, x1, y1)
    bones = [dogbone((x0, y0), (1, 1), r), dogbone((x1, y0), (-1, 1), r),
             dogbone((x1, y1), (-1, -1), r), dogbone((x0, y1), (1, -1), r)]
    return unary_union([rect, *bones])


def notch(u0, u1, v_edge, v_in, r) -> Polygon:
    """Slot open at the edge v = v_edge, running to v = v_in, with dogbones at its two inner corners."""
    s = 1 if v_in > v_edge else -1
    rect = box(u0, min(v_edge - s * 5, v_in), u1, max(v_edge - s * 5, v_in))
    bones = [dogbone((u0, v_in), (1, -s), r), dogbone((u1, v_in), (-1, -s), r)]
    return unary_union([rect, *bones])


def _round_outer(poly: Polygon, r: float) -> Polygon:
    """Round convex corners only (the router does that anyway; looks intentional)."""
    return poly.buffer(-r, quad_segs=16, join_style="round").buffer(r, quad_segs=16, join_style="round")


# ----------------------------------------------------------------------------- layout
@dataclass
class Layout:
    t: float; t_min: float; t_max: float; H: float
    O: float; Lf: float; Wf: float
    yL: tuple[float, float]        # long panel centre planes
    xS: tuple[float, float]        # short panel centre planes
    z_deck_bot: float; z_deck_top: float
    cx: float; cy: float


def layout(p) -> Layout:
    F, M = p.frame, p.material
    O = F.overhang
    Lf, Wf = p.top.length - 2 * O, p.top.width - 2 * O
    zt = F.height - p.deck.drop
    return Layout(t=M.t_nominal, t_min=M.t_min, t_max=M.t_max, H=F.height, O=O, Lf=Lf, Wf=Wf,
                  yL=(O + F.ear, O + Wf - F.ear), xS=(O + F.ear, O + Lf - F.ear),
                  z_deck_bot=zt - M.t_nominal, z_deck_top=zt, cx=p.top.length / 2, cy=p.top.width / 2)


def slot_w(p) -> float:
    return p.material.t_max + p.fit.slot_clearance


def lap_depth(p) -> float:
    return p.frame.height / 2 + p.frame.lap_extra


def thick_slot(p) -> float:
    """Width of any through-opening that a plate's thickness passes through (mortise height, wedge holes)."""
    return p.material.t_max + p.fit.mortise_height_extra


def leg_zone(p) -> tuple[float, float]:
    """Panel-local u-range of solid leg between the cross-lap slot and the leg opening (near end)."""
    F = p.frame
    return F.ear + slot_w(p) / 2, F.leg_width


def tenon_xs(p) -> list[tuple[float, float]]:
    """World x-ranges of the deck tenons: centred in the long panels' two leg zones."""
    D, L = p.deck, layout(p)
    if D.tenons_per_side != 2:
        raise ValueError("deck tenons sit one per leg zone: tenons_per_side must be 2")
    a, b = leg_zone(p)
    c0 = L.O + (a + b) / 2
    c1 = L.O + L.Lf - (a + b) / 2
    return [(c - D.tenon_width / 2, c + D.tenon_width / 2) for c in (c0, c1)]


def cheek_xs(p) -> list[float]:
    """Inner-face x of the two cheeks (left cheek's inner face is its +x face)."""
    L, h = layout(p), p.heater
    half = (h.body_x + h.cheek_clearance) / 2
    return [L.cx - half, L.cx + half]


def tab_ys(p) -> list[tuple[float, float]]:
    C, L = p.cheek, layout(p)
    return [(L.cy + s * C.tab_spacing / 2 - C.tab_w / 2, L.cy + s * C.tab_spacing / 2 + C.tab_w / 2) for s in (-1, 1)]


def cheek_hole_z(p) -> tuple[float, float]:
    L, C = layout(p), p.cheek
    z0 = L.z_deck_bot + L.t_min - C.hole_drop
    return z0, z0 + C.hole_h


# ----------------------------------------------------------------------------- parts
def leg_inner_u(p, z: float) -> float:
    """u of a leg's inner (opening-side) edge at height z, near panel end. Legs are leg_width wide where
    they meet the apron and leg_width - leg_taper wide at the floor; the outer edge stays plumb."""
    F = p.frame
    Ha = F.height - F.apron_depth
    return F.leg_width - getattr(F, "leg_taper", 0.0) * (Ha - z) / Ha


def leg_opening(p, length: float) -> Polygon:
    """Leg opening: a trapezoid (wider at the floor when tapered) with r = opening_r fillets at the top.
    It runs below the floor far enough that the bottom corner rounding never reaches z = 0."""
    F = p.frame
    Ha, r = F.height - F.apron_depth, F.opening_r
    zb = -(r + 20)
    ub, ut = leg_inner_u(p, zb), F.leg_width
    trap = Polygon([(ub, zb), (length - ub, zb), (length - ut, Ha), (ut, Ha)])
    return trap.buffer(-r, quad_segs=16, join_style="round").buffer(r, quad_segs=16, join_style="round")


def foot_flares(p, length: float):
    """Bell-shaped feet: each panel end sweeps out by foot_flare at the floor along a cove (circular arc)
    that leaves the plumb end edge tangentially at flare_h. Moves the tipping edge outward."""
    F = p.frame
    f, fh = getattr(F, "foot_flare", 0.0), getattr(F, "flare_h", 120.0)
    if f <= 0:
        return None
    R = (f * f + fh * fh) / (2 * f)                    # circle tangent to the end edge at (0, fh), through (-f, 0)
    left = box(-f, 0, 0.01, fh).difference(Point(-R, fh).buffer(R, quad_segs=128))
    right = box(length - 0.01, 0, length + f, fh).difference(Point(length + R, fh).buffer(R, quad_segs=128))
    return unary_union([left, right])


def side_panel(p, length: float, slots_from_top: bool) -> Polygon:
    F, r = p.frame, _rd(p)
    H = F.height
    body = _round_outer(box(0, 0, length, H), F.ear_r)
    fl = foot_flares(p, length)
    if fl is not None:                                  # square bottom corners under the flares, then
        body = body.union(box(0, 0, length, H / 2)).union(fl)   # a small rounding keeps the tips crisp
        body = _round_outer(body, 3.0)
    opening = leg_opening(p, length)
    g = body.difference(opening)
    g = _round_outer(g, F.foot_r)                       # soften the inner foot corners too
    w, d = slot_w(p), lap_depth(p)
    for u in (F.ear, length - F.ear):
        if slots_from_top:
            g = g.difference(notch(u - w / 2, u + w / 2, H, H - d, r))
        else:
            g = g.difference(notch(u - w / 2, u + w / 2, 0, d, r))
    return g


def long_panel(p) -> Polygon:
    L, r = layout(p), _rd(p)
    g = side_panel(p, L.Lf, slots_from_top=True)
    for x0, x1 in tenon_xs(p):                          # deck mortises (tenon width + clearance)
        c = p.fit.tight
        g = g.difference(hole(x0 - c - L.O, L.z_deck_bot, x1 + c - L.O, L.z_deck_bot + thick_slot(p), r))
    return g


def short_panel(p) -> Polygon:
    return side_panel(p, layout(p).Wf, slots_from_top=False)


def deck(p) -> Polygon:
    """Deck in world x-y (axis z). Body between the long aprons' inner faces + through-tenons at its
    four corners (the body spans exactly from the first tenon's outer edge to the last one's)."""
    L, D, r = layout(p), p.deck, _rd(p)
    txs = tenon_xs(p)
    x0, x1 = txs[0][0], txs[-1][1]
    s0 = L.yL[0] + L.t_max / 2 + p.fit.tight           # shoulders clear the thickest apron
    s1 = L.yL[1] - L.t_max / 2 - p.fit.tight
    g = box(x0, s0, x1, s1)
    ends = (L.yL[0] - L.t / 2 - D.tenon_proud, L.yL[1] + L.t / 2 + D.tenon_proud)
    for tx0, tx1 in txs:
        g = g.union(box(tx0, ends[0], tx1, s0 + 1)).union(box(tx0, s1 - 1, tx1, ends[1]))
    g = _round_outer(g, 1.0)                           # just break the tenon-end corners (they show)
    for tx0, tx1 in txs:                               # root reliefs so the shoulders seat on the apron
        # dogbone centred in the empty quadrant beside the root, like a hole's corner bone, so the
        # bit can actually get in (its mouth is the open quadrant)
        for (sy, ty) in ((s0, -1), (s1, 1)):          # ty: direction the tenon sticks out
            # inner root only: the outer root is the deck's own corner (tenon flush with the body end)
            if tx0 > x0 + 0.01:
                g = g.difference(dogbone((tx0, sy), (-1, ty), r))
            if tx1 < x1 - 0.01:
                g = g.difference(dogbone((tx1, sy), (1, ty), r))
    for xi, sgn in zip(cheek_xs(p), (-1, 1)):          # cheek tab slots; inner edge = heater face
        xa, xb = sorted((xi, xi + sgn * thick_slot(p)))
        for ya, yb in tab_ys(p):
            g = g.difference(hole(xa, ya - p.fit.tight, xb, yb + p.fit.tight, r))
    return g


def cheek(p) -> tuple[Polygon, float]:
    """Cheek in its own (u = y - y_start, v = z - z_bottom) plane. Returns (shape, y_start)."""
    L, C, r = layout(p), p.cheek, _rd(p)
    y_start = L.cy - C.length / 2
    zb = L.z_deck_bot - C.height
    g = box(0, 0, C.length, C.height)
    g = _round_outer(g, 6.0)
    top_v = L.z_deck_top + C.tab_above_deck - zb
    hz0, hz1 = cheek_hole_z(p)
    for ya, yb in tab_ys(p):
        u0, u1 = ya - y_start, yb - y_start
        tab = _round_outer(box(u0, C.height - 15, u1, top_v), 5.0)  # rounding buried in the body
        g = g.union(tab)
        g = g.difference(dogbone((u0, C.height), (-1, 1), r)).difference(dogbone((u1, C.height), (1, 1), r))
        uc = (u0 + u1) / 2
        g = g.difference(hole(uc - thick_slot(p) / 2, hz0 - zb, uc + thick_slot(p) / 2, hz1 - zb, r))
    return g, y_start


def taper_wedge(length: float, head: float, taper: float, r: float = 3.0) -> Polygon:
    """Wedge: straight edge along v = 0 ... length at u = 0, tapered edge from `head` (v = length) down."""
    foot = head - length * taper
    return _round_outer(Polygon([(0, 0), (foot, 0), (head, length), (0, length)]), r)


# ----------------------------------------------------------------------------- assembly
def parts(p) -> list[Part]:
    if getattr(p.frame, "style", "slab") == "yagura":
        from . import yagura
        return yagura.parts(p)
    L = layout(p)
    t = L.t
    out: list[Part] = []
    lp = Part("long side", long_panel(p), [Placement("x", (L.O, y - t / 2, 0)) for y in L.yL])
    sp = Part("short side", short_panel(p), [Placement("y", (x - t / 2, L.O, 0)) for x in L.xS])
    dk = Part("deck", deck(p), [Placement("z", (0, 0, L.z_deck_bot))], kind="deck")
    cs, y0 = cheek(p)
    zb = L.z_deck_bot - p.cheek.height
    ck = Part("heater cheek", cs, [Placement("y", (xi - (t if s < 0 else 0), y0, zb))
                                   for xi, s in zip(cheek_xs(p), (-1, 1))], kind="cheek")
    out += [lp, sp, dk, ck]

    taper = p.fit.wedge_taper
    # cheek wedges: plate in x-z, lying on the deck top, passing through the tab holes in x
    CW = p.cheek_wedge
    cw = Polygon([(0, 0), (CW.length, 0), (CW.length, CW.head), (0, CW.head - CW.length * taper)])
    cw = _round_outer(cw, 3.0)
    cw_pl = []
    for xi, s in zip(cheek_xs(p), (-1, 1)):
        xmid = xi + s * t / 2                             # cheek centre plane
        for ya, yb in tab_ys(p):
            yc = (ya + yb) / 2
            cw_pl.append(Placement("x", (xmid - CW.length / 2, yc - t / 2, L.z_deck_top)))
    out.append(Part("cheek wedge", cw, cw_pl, spares=1, kind="wedge"))
    return out


def heater_box(p) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """(size, centre) of the heater body hanging between the cheeks."""
    L, h = layout(p), p.heater
    ztop = L.z_deck_bot - h.top_gap
    return (h.body_x, h.body_y, h.body_h), (L.cx, L.cy, ztop - h.body_h / 2)
