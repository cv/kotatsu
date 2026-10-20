"""Yagura-style frame (owner's comparison variant): no aprons. Four "+" corner legs, each two crossed
plates, carry a deck; the heater hangs under the deck as in the slab frame.

Same plan geometry as the slab frame: the plates lie in the slab panels' planes and cross `ear` in from
the frame's edge, so leg room, knee reach and tipping compare like for like.

Joints
  * legs: cross-lap at each corner ("x" plates slotted from the shoulder down, "y" plates from the floor up)
  * leg -> deck: every plate's top edge is a shoulder under the deck, with one tenon through it.
    A small wedge through the tenon, lying on the deck, clamps the deck between shoulder and wedge.
  * cheeks: as in the slab frame (tabs up through the deck, flat wedges)
Assembly: cross the 4 pairs of plates into "+" legs, stand them up, lower the deck over the 8 tenons,
tap in the 8 leg wedges, then hang the cheeks + heater.
"""
from __future__ import annotations

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from . import frame as fr
from .frame import Part, Placement


def _tenon_u(p) -> tuple[float, float]:
    """u-range of a plate's tenon, from the plate's outer end: just past the cross-lap slot."""
    F, Y = p.frame, p.yagura
    a = F.ear + fr.slot_w(p) / 2 + Y.tenon_gap
    return a, a + Y.tenon_w


def _flare_near(p):
    fl = fr.foot_flares(p, 10_000.0)
    return None if fl is None else fl.intersection(box(-1e3, -1, 5_000, 1e4))


def leg_hole_z(p) -> tuple[float, float]:
    L, Y = fr.layout(p), p.yagura
    z0 = L.z_deck_bot + L.t_min - Y.hole_drop
    return z0, z0 + Y.hole_h


def leg_plate(p, slotted_from_top: bool) -> Polygon:
    """One leg plate in its own (u from the frame edge inward, v = z) plane."""
    F, L, r = p.frame, fr.layout(p), fr._rd(p)
    zs, H = L.z_deck_bot, L.H
    wt = F.leg_width
    wb = wt - getattr(F, "leg_taper", 0.0)
    g = Polygon([(0, 0), (wb, 0), (wt, zs), (0, zs)])
    g = fr._round_outer(g, F.foot_r)
    fl = _flare_near(p)
    if fl is not None:
        g = fr._round_outer(g.union(box(0, 0, 20, zs / 2)).union(fl), 3.0)
    ta, tb = _tenon_u(p)
    g = g.union(fr._round_outer(box(ta, zs - 10, tb, H), 3.0))
    for u, s in ((ta, -1), (tb, 1)):                     # root reliefs: shoulders seat flat on the deck
        g = g.difference(fr.dogbone((u, zs), (s, 1), r))
    hz0, hz1 = leg_hole_z(p)
    uc, ts = (ta + tb) / 2, fr.thick_slot(p)
    g = g.difference(fr.hole(uc - ts / 2, hz0, uc + ts / 2, hz1, r))
    w, d = fr.slot_w(p), lap_depth(p)
    u = F.ear
    if slotted_from_top:
        g = g.difference(fr.notch(u - w / 2, u + w / 2, zs, zs - d, r))
    else:
        g = g.difference(fr.notch(u - w / 2, u + w / 2, 0, d, r))
    return g


def lap_depth(p) -> float:
    """Cross-laps share the leg height below the deck (+ lap_extra each, so the floor sets the height)."""
    return fr.layout(p).z_deck_bot / 2 + p.frame.lap_extra


def mortises(p) -> list[tuple[float, float, float, float]]:
    """World (x0, y0, x1, y1) of the 8 deck mortises (tenon + in-plane clearance, thickest stock)."""
    L = fr.layout(p)
    ta, tb = _tenon_u(p)
    c, h = p.fit.tight, fr.thick_slot(p) / 2
    out = []
    for y in L.yL:                                      # x plates (in the x-z plane at y)
        for a, b in ((L.O + ta, L.O + tb), (L.O + L.Lf - tb, L.O + L.Lf - ta)):
            out.append((a - c, y - h, b + c, y + h))
    for x in L.xS:                                      # y plates (in the y-z plane at x)
        for a, b in ((L.O + ta, L.O + tb), (L.O + L.Wf - tb, L.O + L.Wf - ta)):
            out.append((x - h, a - c, x + h, b + c))
    return out


def deck(p) -> Polygon:
    """Deck in world x-y: the frame square, corners trimmed to stay inside the round top."""
    L, Y, r = fr.layout(p), p.yagura, fr._rd(p)
    g = box(L.O, L.O, L.O + L.Lf, L.O + L.Wf)
    if getattr(p.top, "shape", "rect") == "round":
        g = g.intersection(Point(L.cx, L.cy).buffer(p.top.length / 2 - Y.deck_inset, quad_segs=64))
    g = fr._round_outer(g, 8.0)
    for x0, y0, x1, y1 in mortises(p):
        g = g.difference(fr.hole(x0, y0, x1, y1, r))
    for xi, sgn in zip(fr.cheek_xs(p), (-1, 1)):        # cheek tab slots, as in the slab deck
        xa, xb = sorted((xi, xi + sgn * fr.thick_slot(p)))
        for ya, yb in fr.tab_ys(p):
            g = g.difference(fr.hole(xa, ya - p.fit.tight, xb, yb + p.fit.tight, r))
    return g


def wedge_shape(p) -> Polygon:
    CW, taper = p.cheek_wedge, p.fit.wedge_taper
    w = Polygon([(0, 0), (CW.length, 0), (CW.length, CW.head), (0, CW.head - CW.length * taper)])
    return fr._round_outer(w, 3.0)


def parts(p) -> list[Part]:
    L, t = fr.layout(p), fr.layout(p).t
    out: list[Part] = []
    xp = [Placement("x", (L.O, y - t / 2, 0)) for y in L.yL] + \
         [Placement("x", (L.O + L.Lf, y - t / 2, 0), mirror_u=True) for y in L.yL]
    yp = [Placement("y", (x - t / 2, L.O, 0)) for x in L.xS] + \
         [Placement("y", (x - t / 2, L.O + L.Wf, 0), mirror_u=True) for x in L.xS]
    out.append(Part("leg plate A", leg_plate(p, True), xp))     # slotted from the shoulder down
    out.append(Part("leg plate B", leg_plate(p, False), yp))    # slotted from the floor up
    out.append(Part("deck", deck(p), [Placement("z", (0, 0, L.z_deck_bot))], kind="deck"))
    cs, y0 = fr.cheek(p)
    zb = L.z_deck_bot - p.cheek.height
    out.append(Part("heater cheek", cs, [Placement("y", (xi - (t if s < 0 else 0), y0, zb))
                                         for xi, s in zip(fr.cheek_xs(p), (-1, 1))], kind="cheek"))
    CW = p.cheek_wedge
    w = wedge_shape(p)
    # leg wedges lie on the deck and pass through each tenon, normal to its plate
    ta, tb = _tenon_u(p)
    lw = []
    for x0, y0, x1, y1 in mortises(p):
        xc, yc = (x0 + x1) / 2, (y0 + y1) / 2
        if x1 - x0 > y1 - y0:          # x plate tenon: wedge runs along y (plate in the y-z plane)
            lw.append(Placement("y", (xc - t / 2, yc - CW.length / 2, L.z_deck_top)))
        else:
            lw.append(Placement("x", (xc - CW.length / 2, yc - t / 2, L.z_deck_top)))
    out.append(Part("leg wedge", w, lw, spares=1, kind="wedge"))
    cw_pl = []
    for xi, s in zip(fr.cheek_xs(p), (-1, 1)):
        xmid = xi + s * t / 2
        for ya, yb in fr.tab_ys(p):
            yc = (ya + yb) / 2
            cw_pl.append(Placement("x", (xmid - CW.length / 2, yc - t / 2, L.z_deck_top)))
    out.append(Part("cheek wedge", w, cw_pl, spares=1, kind="wedge"))
    return out
