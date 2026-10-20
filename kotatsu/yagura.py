"""Yagura frame: four "+" corner legs, each two crossed plates, carry a deck; no aprons. The heater
hangs under the deck from two cheeks (kotatsu/frame.py).

Legs are straight (plumb edges), 120 mm plates: a 40 mm ear arm outside the corner cross-lap, the slot,
a 10 mm shoulder, then a tenon out to the inner edge.

Joints
  * legs: cross-lap at each corner ("A" plates slotted from the shoulder down, "B" plates from the floor up)
  * leg -> deck: every plate's top edge is a shoulder under the deck, with one tenon through it.
    A small wedge through the tenon, lying on the deck, clamps the deck between shoulder and wedge.
Assembly: cross the 4 pairs of plates into "+" legs, stand them up, lower the deck over the 8 tenons,
tap in the 8 leg wedges, then hang the cheeks + heater.
"""
from __future__ import annotations

from shapely.geometry import Point, Polygon, box

from . import frame as fr
from .frame import Part, Placement


def _tenon_u(p) -> tuple[float, float]:
    """u-range of a plate's tenon, from the plate's outer end: just past the cross-lap slot."""
    F, Y = p.frame, p.yagura
    a = F.ear + fr.slot_w(p) / 2 + Y.tenon_gap
    return a, min(a + Y.tenon_w, F.leg_width)          # any leg width left over is an inner shoulder


def leg_hole_z(p) -> tuple[float, float]:
    L, Y = fr.layout(p), p.yagura
    z0 = L.z_deck_bot + L.t_min - Y.hole_drop
    return z0, z0 + Y.hole_h


def leg_plate(p, slotted_from_top: bool) -> Polygon:
    """One leg plate in its own (u from the frame edge inward, v = z) plane."""
    F, L, r = p.frame, fr.layout(p), fr._rd(p)
    zs, H = L.z_deck_bot, L.H
    wt = F.leg_width
    g = box(0, 0, wt, zs)
    nc = narrow_cut(p)
    if nc is not None:                                   # haunched leg: narrow below, full width under the deck
        g = g.difference(nc)
    g = fr._round_outer(g, F.foot_r)
    ta, tb = _tenon_u(p)
    g = g.union(fr._round_outer(box(ta, zs - 10, tb, H), 3.0))
    pu = post_u(p)
    if pu > 0:                                           # corner post: the ear arm rises to the top too
        g = g.union(fr._round_outer(box(0, zs - 10, pu, H), 3.0).intersection(box(0, 0, pu, H)))
        if not slotted_from_top:                         # B: shoulder runs on from the post -> root relief
            g = g.difference(fr.dogbone((pu, zs), (1, 1), r))
    g = g.difference(fr.dogbone((ta, zs), (-1, 1), r))   # root reliefs: the shoulders seat flat on the deck
    if tb < wt - 0.01:
        g = g.difference(fr.dogbone((tb, zs), (1, 1), r))
    lw = leg_window(p)
    if lw is not None:
        g = g.difference(lw)
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


def post_u(p) -> float:
    """Width of the corner post (each plate's ear arm, outside the cross-lap) that rises past the deck to
    the top's underside, so the top is carried right at the frame corners. 0 = no posts."""
    if not getattr(p.yagura, "corner_posts", False):
        return 0.0
    return p.frame.ear - fr.slot_w(p) / 2


def corner_cut(p) -> float:
    """Distance from the frame centre at which the deck is cut away for the posts (post inner end -
    clearance). The deck still covers the cross-laps, so it keeps bearing on the shoulders there."""
    return fr.layout(p).Lf / 2 - post_u(p) - p.fit.tight


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
    if post_u(p) > 0:                                   # L-shaped corner cut-outs around the two posts
        k = corner_cut(p)
        j = L.Lf / 2 - p.frame.ear - fr.thick_slot(p) / 2  # plates' inner faces (+ clearance)
        far = 500.0

        def quad(sx, sy, ax, ay):                        # box from (ax, ay) outwards, in corner (sx, sy)
            x0, y0 = L.cx + sx * ax, L.cy + sy * ay
            return box(min(x0, x0 + sx * far), min(y0, y0 + sy * far), max(x0, x0 + sx * far), max(y0, y0 + sy * far))

        for sx in (-1, 1):
            for sy in (-1, 1):
                g = g.difference(quad(sx, sy, k, j)).difference(quad(sx, sy, j, k))
                for ax, ay in ((k, j), (j, k)):          # the cut-out's two inside corners
                    g = g.difference(fr.dogbone((L.cx + sx * ax, L.cy + sy * ay), (sx, sy), r))
    for x0, y0, x1, y1 in mortises(p):
        g = g.difference(fr.hole(x0, y0, x1, y1, r))
    for w in windows(p):                                # weight-saving windows away from the heater
        g = g.difference(w)
    for xi, sgn in zip(fr.cheek_xs(p), (-1, 1)):        # cheek tab slots, as in the slab deck
        xa, xb = sorted((xi, xi + sgn * fr.thick_slot(p)))
        for ya, yb in fr.tab_ys(p):
            g = g.difference(fr.hole(xa, ya - p.fit.tight, xb, yb + p.fit.tight, r))
    return g


def window_rects(p) -> list[tuple[float, float, float, float]]:
    """Deck lightening windows as centre-relative (x0, y0, x1, y1), sized from the features around them:
    two "side" windows beside the cheeks (x) and two "end" windows past the cheek ends (y), each
    window_margin clear of the heater, cheeks, cheek wedges, mortises and leg wedges, window_bar from the
    deck edge and from each other. [deck] windows = "auto" | [] | explicit list.
    window_style = "notch" opens them through the deck edge (same wood out, ~1 m less cutting); then
    `neck` is the width of wood joining each corner pad (mortises, posts) to the middle."""
    D, L = p.deck, fr.layout(p)
    w = getattr(D, "windows", [])
    if w != "auto":
        return [tuple(v) for v in (w or [])]
    m, bar, t = D.window_margin, D.window_bar, p.material.t_max
    h = L.Lf / 2
    ta, tb = _tenon_u(p)
    m_in = h - tb - p.fit.tight                                  # mortises' inner ends (from the centre)
    ci = abs(fr.cheek_xs(p)[0] - L.cx)                           # cheek inner face
    cw_x = ci + t / 2 + p.cheek_wedge.length / 2                 # cheek wedges' outer ends
    notch = getattr(D, "window_style", "hole") == "notch"        # notches run out through the deck edge
    edge = h + 20 if notch else h - bar
    sx0, sx1, sy = cw_x + m, edge, m_in - m                      # side windows
    ey0 = p.cheek.length / 2 + m                                 # end windows: past the cheek ends ...
    gap = getattr(D, "neck", bar) if notch else bar              # wood joining each corner pad to the middle
    ey1, ex = edge, min(sx0 - gap, m_in - m)                     # ... and clear of the side windows / mortises
    out = []
    if sx1 - sx0 > 40 and sy > 40:
        out += [(sx0, -sy, sx1, sy), (-sx1, -sy, -sx0, sy)]
    if ey1 - ey0 > 40 and ex > 40:
        out += [(-ex, ey0, ex, ey1), (-ex, -ey1, ex, -ey0)]
    return out


def windows(p) -> list[Polygon]:
    """Lightening windows in the deck (world coords), rounded by window_r. They keep the order under
    uMake's free-shipping weight (box <= 91 cm and under ~20 kg)."""
    D, L = p.deck, fr.layout(p)
    return [fr._round_outer(box(L.cx + x0, L.cy + y0, L.cx + x1, L.cy + y1), D.window_r)
            for x0, y0, x1, y1 in window_rects(p)]


def narrow_cut(p) -> Polygon | None:
    """Owner's haunched leg (2026-10-20): below the deck the plate keeps only leg_narrow of its width
    (from the frame edge); a sloped haunch (leg_haunch_top at the inner edge, leg_haunch_drop lower at
    the narrow line) widens it back to the full leg_width under the shoulders. Returns the region to cut
    away, its inside corner rounded by leg_haunch_r. None if disabled."""
    Y, F = p.yagura, p.frame
    wn = getattr(Y, "leg_narrow", 0.0)
    if not wn or wn >= F.leg_width:
        return None
    wt, zt = F.leg_width, Y.leg_haunch_top
    zl = zt - Y.leg_haunch_drop
    cut = Polygon([(wn, -50), (wn, zl), (wt, zt), (wt + 50, zt), (wt + 50, -50)])
    rr = Y.leg_haunch_r
    return cut.buffer(-rr, quad_segs=16, join_style="round").buffer(rr, quad_segs=16, join_style="round")


def leg_window(p) -> Polygon | None:
    """Slot-shaped window in each leg plate's inner arm (plate coords), leg_window_bar of wood each side
    and leg_window_end above the floor / below the shoulders. None if disabled or too narrow."""
    Y, F, L = p.yagura, p.frame, fr.layout(p)
    if not getattr(Y, "leg_windows", False):
        return None
    b = Y.leg_window_bar
    u0, u1 = F.ear + fr.slot_w(p) / 2 + b, F.leg_width - b
    z0, z1 = Y.leg_window_end, L.z_deck_bot - Y.leg_window_end
    if u1 - u0 < 12 or z1 - z0 < 60:
        return None
    rr = (u1 - u0) / 2 - 0.01
    return fr._round_outer(box(u0, z0, u1, z1), rr)


def wedge_dims(p, which: str = "cheek") -> tuple[float, float]:
    """(length, head) of the cheek wedges, or of the (shorter) leg wedges."""
    CW, Y = p.cheek_wedge, p.yagura
    if which == "leg":
        return getattr(Y, "wedge_len", CW.length), getattr(Y, "wedge_head", CW.head)
    return CW.length, CW.head


def wedge_shape(p, which: str = "cheek") -> Polygon:
    n, h = wedge_dims(p, which)
    taper = p.fit.wedge_taper
    w = Polygon([(0, 0), (n, 0), (n, h), (0, h - n * taper)])
    return fr._round_outer(w, 3.0)


def parts(p) -> list[Part]:
    L, t = fr.layout(p), fr.layout(p).t
    out: list[Part] = []
    xp = [Placement("x", (L.O, y - t / 2, 0)) for y in L.yL] + \
         [Placement("x", (L.O + L.Lf, y - t / 2, 0), mirror_u=True) for y in L.yL]
    yp = [Placement("y", (x - t / 2, L.O, 0)) for x in L.xS] + \
         [Placement("y", (x - t / 2, L.O + L.Wf, 0), mirror_u=True) for x in L.xS]
    out.append(Part("leg plate A", leg_plate(p, True), xp, grain="v"))   # slotted from the shoulder down
    out.append(Part("leg plate B", leg_plate(p, False), yp, grain="v"))  # slotted from the floor up; grain up the leg
    out.append(Part("deck", deck(p), [Placement("z", (0, 0, L.z_deck_bot))], kind="deck"))
    cs, y0 = fr.cheek(p)
    zb = L.z_deck_bot - p.cheek.height
    out.append(Part("heater cheek", cs, [Placement("y", (xi - (t if s < 0 else 0), y0, zb))
                                         for xi, s in zip(fr.cheek_xs(p), (-1, 1))], kind="cheek"))
    CW = p.cheek_wedge
    w = wedge_shape(p)
    # leg wedges lie on the deck and pass through each tenon, normal to its plate
    wl, _ = wedge_dims(p, "leg")
    lw = []
    for x0, y0, x1, y1 in mortises(p):
        xc, yc = (x0 + x1) / 2, (y0 + y1) / 2
        if x1 - x0 > y1 - y0:          # x plate tenon: wedge runs along y (plate in the y-z plane)
            lw.append(Placement("y", (xc - t / 2, yc - wl / 2, L.z_deck_top)))
        else:
            lw.append(Placement("x", (xc - wl / 2, yc - t / 2, L.z_deck_top)))
    out.append(Part("leg wedge", wedge_shape(p, "leg"), lw, spares=1, kind="wedge"))
    cw_pl = []
    for xi, s in zip(fr.cheek_xs(p), (-1, 1)):
        xmid = xi + s * t / 2
        for ya, yb in fr.tab_ys(p):
            yc = (ya + yb) / 2
            cw_pl.append(Placement("x", (xmid - CW.length / 2, yc - t / 2, L.z_deck_top)))
    if getattr(p.yagura, "one_wedge", False):          # owner: one wedge part for legs and cheeks
        if wedge_dims(p, "cheek") != wedge_dims(p, "leg"):
            raise ValueError("one_wedge needs [cheek_wedge] length/head = [yagura] wedge_len/wedge_head")
        lw_part = out.pop()
        out.append(Part("wedge", lw_part.shape, lw_part.placements + cw_pl, spares=2, kind="wedge"))
    else:
        out.append(Part("cheek wedge", w, cw_pl, spares=1, kind="wedge"))
    return out
