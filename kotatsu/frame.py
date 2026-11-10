"""Frame (yagura) shared pieces: coordinates, placements, router-aware joint helpers, the layout,
and the heater cheeks. The legs and deck themselves are in kotatsu/yagura.py.

World coordinates (mm): x and y across the top (origin at the top's bounding-box corner), z up, floor z = 0.
Every part is a flat 2-D shape in its own (u, v) plane, plus a placement:
  axis "x": plate in the x-z plane (u -> x, v -> z, thickness along y)
  axis "y": plate in the y-z plane (u -> y, v -> z, thickness along x)
  axis "z": plate in the x-y plane (u -> x, v -> y, thickness along z)
origin = world position of local (0, 0, 0); the plate occupies [0, t] along its thickness axis.

Heater cradle (v2): 2 on-edge cheeks the heater screws in between. The pair drops into a well in the deck's
middle and an ear at each cheek end rests on the deck top, so gravity holds it up: no tabs, no wedges.
Every square-cornered opening (and every male root corner) gets a dogbone for the round bit.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union



@dataclass
class Placement:
    axis: str                       # "x" | "y" | "z"
    origin: tuple[float, float, float]
    mirror_u: bool = False          # informational: shape already mirrored for this placement
    matrix: tuple[float, ...] | None = None   # axis "m": row-major 4x4, part (u, v, w = thickness) -> world


@dataclass
class Part:
    name: str
    shape: Polygon
    placements: list[Placement] = field(default_factory=list)
    spares: int = 0                 # extra copies to cut (not placed)
    kind: str = "frame"             # frame | deck | cheek | wedge
    ordered: bool = True            # cut by the shop (False: the owner has them already, e.g. v1's wedges)
    grain: str = "u"                # face grain along the part's u, or "v" (legs: grain running up the leg)

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
    z_deck_bot: float; z_deck_top: float
    cx: float; cy: float


def layout(p) -> Layout:
    F, M = p.frame, p.material
    O = F.overhang
    Lf, Wf = p.top.length - 2 * O, p.top.width - 2 * O
    zt = F.height - p.deck.drop
    return Layout(t=M.t_nominal, t_min=M.t_min, t_max=M.t_max, H=F.height, O=O, Lf=Lf, Wf=Wf,
                  z_deck_bot=zt - M.t_nominal, z_deck_top=zt, cx=p.top.length / 2, cy=p.top.width / 2)


def slot_w(p) -> float:
    return p.material.t_max + p.fit.slot_clearance


def wedge_t(p) -> tuple[float, float]:
    """The leg wedges' thickness range (mm): yagura.wedge_stock if set (v1's wedges, from its thicker sheet), else
    the sheet's."""
    s = getattr(p.yagura, "wedge_stock", None)
    return (float(s[0]), float(s[1])) if s else (p.material.t_min, p.material.t_max)


def wedge_slot(p) -> float:
    """Width of the wedge hole through each leg's tenon: the thickest wedge, + mortise_height_extra."""
    return wedge_t(p)[1] + p.fit.mortise_height_extra


def rib_proud(p) -> float:
    """How far each crush rib stands proud of its slot wall: the gap between a pair is the thinnest sheet, so the
    crosspiece is snug on any stock (thicker stock: sand the bumps or the crosspiece's faces at the fit-up)."""
    return (slot_w(p) - p.material.t_min) / 2


def thick_slot(p) -> float:
    """Width of any through-opening that a plate's thickness passes through (mortise height, wedge holes)."""
    return p.material.t_max + p.fit.mortise_height_extra


def cheek_xs(p) -> list[float]:
    """Inner-face x of the two cheeks (left cheek's inner face is its +x face)."""
    L, h = layout(p), p.heater
    half = (h.body_x + h.cheek_clearance) / 2
    return [L.cx - half, L.cx + half]


def well(p) -> tuple[float, float, float, float]:
    """World (x0, y0, x1, y1) of the deck's heater well: the heater between the cheeks, plus both cheeks (for
    the thickest stock + slot clearance) across x; the heater body + end_clearance along y."""
    L, h = layout(p), p.heater
    wx = (h.body_x + h.cheek_clearance) / 2 + slot_w(p)
    wy = (h.body_y + h.end_clearance) / 2
    return L.cx - wx, L.cy - wy, L.cx + wx, L.cy + wy


def cheek_z(p) -> tuple[float, float]:
    """(bottom, top) z of the cheeks: from below_screw under the heater's screw line (screw_from_top below its top;
    owner 2026-11: the screws are near the top, so the cheeks needn't cover the whole side), or the heater's
    underside if that's higher, to ear_h above the nominal deck top. The bottom stays under the deck's underside,
    so the cheeks locate in the well's whole depth."""
    L, C, h = layout(p), p.cheek, p.heater
    (_, _, sz), (_, _, hz) = heater_box(p)
    zb = hz - sz / 2
    zb = max(zb, hz + sz / 2 - h.screw_from_top - C.below_screw)
    zb = min(zb, L.z_deck_bot - 2.0)
    zt = L.z_deck_top + C.ear_h
    if zt < hz + sz / 2:
        raise ValueError("[cheek] ear_h must reach the heater top ([heater] top_rise)")
    return zb, zt


def cheek_ys(p) -> tuple[float, float]:
    """World (y0, y1) of each cheek: the well's length plus an ear of ear_len at each end."""
    _, y0, _, y1 = well(p)
    return y0 - p.cheek.ear_len, y1 + p.cheek.ear_len


# ----------------------------------------------------------------------------- parts
def cheek(p) -> tuple[Polygon, float]:
    """Cheek in its own (u = y - y_start, v = z - z_bottom) plane. Returns (shape, y_start).
    The body (below the deck top) fits the well's length with p.fit.tight a side; above the deck top the
    cheek runs on as an ear at each end, whose underside rests on the deck. Root reliefs at the two
    inside corners let the ears seat flat on the well's edge."""
    L, C, r = layout(p), p.cheek, _rd(p)
    (_, w0, _, w1), (y0, y1) = well(p), cheek_ys(p)
    zb, zt = cheek_z(p)
    n, v_deck, top = y1 - y0, L.z_deck_top - zb, zt - zb
    b0, b1 = w0 - y0 + p.fit.tight, w1 - y0 - p.fit.tight
    g = box(b0, 0, b1, top).union(box(0, v_deck, n, top))
    from . import geom
    rb, rt, re = C.bottom_r, C.top_r, C.ear_r   # v2 (owner 2026-11): squircle corners, each sized for its job

    def size(c, convex):
        if not convex:
            return 0.0                      # the ears' roots: dogbones go there
        if c[1] < 1:
            return rb                       # the bottom, hanging in the well
        if c[1] > top - 1:
            return rt                       # the top, under the futon
        return re                           # the ears' undersides rest on the deck: keep most of the bearing
    g = geom.squircle_corners(g, size, p.frame.corner_n)
    g = g.difference(dogbone((b0, v_deck), (-1, -1), r)).difference(dogbone((b1, v_deck), (1, -1), r))
    return g, y0


# ----------------------------------------------------------------------------- assembly
def parts(p) -> list[Part]:
    """Every frame part with its placements (the yagura legs + deck are in kotatsu/yagura.py)."""
    from . import yagura
    return yagura.parts(p)


def heater_box(p) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """(size, centre) of the heater body, screwed between the cheeks; its top is top_rise above the deck top."""
    L, h = layout(p), p.heater
    ztop = L.z_deck_top + h.top_rise
    ztop = min(ztop, L.z_deck_bot - h.panel_clear - h.panel_h + h.body_h)   # owner 2026-11: the control panel on
                                                                            # one end must clear the deck
    return (h.body_x, h.body_y, h.body_h), (L.cx, L.cy, ztop - h.body_h / 2)
