"""Frame (yagura) shared pieces: coordinates, placements, router-aware joint helpers, the layout,
and the heater cheeks. The legs and deck themselves are in kotatsu/yagura.py.

World coordinates (mm): x and y across the top (origin at the top's bounding-box corner), z up, floor z = 0.
Every part is a flat 2-D shape in its own (u, v) plane, plus a placement:
  axis "x": plate in the x-z plane (u -> x, v -> z, thickness along y)
  axis "y": plate in the y-z plane (u -> y, v -> z, thickness along x)
  axis "z": plate in the x-y plane (u -> x, v -> y, thickness along z)
origin = world position of local (0, 0, 0); the plate occupies [0, t] along its thickness axis.

Cheeks: 2 on-edge plates under the deck, 2 tabs each up through deck slots, locked by flat wedges lying
on the deck (cheek_wedge); the heater screws into their inner faces.
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


@dataclass
class Part:
    name: str
    shape: Polygon
    placements: list[Placement] = field(default_factory=list)
    spares: int = 0                 # extra copies to cut (not placed)
    kind: str = "frame"             # frame | deck | cheek | wedge
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


def thick_slot(p) -> float:
    """Width of any through-opening that a plate's thickness passes through (mortise height, wedge holes)."""
    return p.material.t_max + p.fit.mortise_height_extra


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


# ----------------------------------------------------------------------------- assembly
def parts(p) -> list[Part]:
    """Every frame part with its placements (the yagura legs + deck are in kotatsu/yagura.py)."""
    from . import yagura
    return yagura.parts(p)


def heater_box(p) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """(size, centre) of the heater body hanging between the cheeks."""
    L, h = layout(p), p.heater
    ztop = L.z_deck_bot - h.top_gap
    return (h.body_x, h.body_y, h.body_h), (L.cx, L.cy, ztop - h.body_h / 2)
