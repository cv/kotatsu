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

import math

from shapely.ops import unary_union
from shapely.geometry import LineString, Point, Polygon, box

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
    if slotted_from_top:
        ft = foot_taper_cut(p)
        if ft is not None:                               # plate A only: its feet narrow toward the floor
            g = g.difference(ft)
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
        g = g.union(crush_ribs(p, u - w / 2, u + w / 2, zs - d, zs))
        g = g.difference(foot_relief(p))
    else:
        g = g.difference(fr.notch(u - w / 2, u + w / 2, 0, d, r))
        g = g.union(crush_ribs(p, u - w / 2, u + w / 2, 0, d))
    return g


def crush_ribs(p, u0: float, u1: float, z0: float, z1: float) -> Polygon:
    """Small rounded bumps on both walls of a cross-lap slot (fit.crush_rib proud per side, radius
    fit.crush_rib_r), at fit.crush_rib_at fractions of the slot's length. They make the joint snug on
    real stock that's thinner than the slot is cut for. Too tight: sand the bumps down (easy)."""
    F = p.fit
    h, R = getattr(F, "crush_rib", 0.0), getattr(F, "crush_rib_r", 10.0)
    if h <= 0:
        return Polygon()
    bumps = []
    for f in getattr(F, "crush_rib_at", [0.3, 0.75]):
        z = z0 + f * (z1 - z0)
        bumps.append(Point(u0 + h - R, z).buffer(R, quad_segs=32).intersection(box(u0 - 1, z - R, u0 + h, z + R)))
        bumps.append(Point(u1 - h + R, z).buffer(R, quad_segs=32).intersection(box(u1 - h, z - R, u1 + 1, z + R)))
    return unary_union(bumps)


def foot_relief(p) -> Polygon:
    """Shallow arc (yagura.foot_relief deep) under the middle of a full-width foot, so each plate stands
    on its two ends: no rocking on a slightly uneven floor. Only plate A needs it (B's slot splits its foot)."""
    Y = p.yagura
    sag = getattr(Y, "foot_relief", 0.0)
    if sag <= 0:
        return Polygon()
    wn = getattr(Y, "leg_narrow", 0.0) or p.frame.leg_width
    ft = getattr(Y, "foot_taper", 0.0)                   # plate A's foot is narrower by this much each side
    a, b = ft + Y.foot_relief_margin, wn - ft - Y.foot_relief_margin
    c = (b - a) / 2
    R = (c * c + sag * sag) / (2 * sag)
    return Point((a + b) / 2, sag - R).buffer(R, quad_segs=64).intersection(box(a - 1, -1, b + 1, sag))


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
    xstyle = getattr(p.deck, "window_style", "hole") == "x"
    if xstyle:                                          # study: an X of diagonal arms instead of an H
        g = g.intersection(x_outline(p))
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
    for w in ([] if xstyle else windows(p)):            # weight-saving windows away from the heater
        g = g.difference(w)
    g = _round_mouths(p, g)
    g = _add_link_tongues(p, g)
    for x0, y0, x1, y1 in link_slots(p):                # key slots, cut after the tongues exist
        g = g.difference(fr.hole(x0, y0, x1, y1, r))
    for xi, sgn in zip(fr.cheek_xs(p), (-1, 1)):        # cheek tab slots, as in the slab deck
        xa, xb = sorted((xi, xi + sgn * fr.thick_slot(p)))
        for ya, yb in fr.tab_ys(p):
            g = g.difference(fr.hole(xa, ya - p.fit.tight, xb, yb + p.fit.tight, r))
    return g


def x_outline(p) -> Polygon:
    """Study (owner 2026-10-20): the deck as an X. Four corner pads carry the leg mortises and wedges;
    diagonal arms join them through the middle, where the cheek tabs already sit (on the diagonals).
    deck.x_hub = "shield" adds a square over the heater, so the futon can't sag onto it.
    Inside corners are filleted (deck.x_fillet) before any joint is cut, so the joints stay exact."""
    D, L = p.deck, fr.layout(p)
    h, cx, cy = L.Lf / 2, L.cx, L.cy
    pad, w = D.x_pad, D.x_arm
    parts = [box(cx + sx * h - (pad if sx > 0 else 0), cy + sy * h - (pad if sy > 0 else 0),
                 cx + sx * h + (0 if sx > 0 else pad), cy + sy * h + (0 if sy > 0 else pad))
             for sx in (-1, 1) for sy in (-1, 1)]
    far = 2 * h
    for d in (1, -1):                                   # the two diagonals
        arm = LineString([(cx - far, cy - d * far), (cx + far, cy + d * far)]).buffer(w / 2, cap_style=2)
        parts.append(arm)
    if getattr(D, "x_hub", "none") == "shield":
        sx, sy, _ = fr.heater_box(p)[0]
        m = D.x_hub_margin
        parts.append(box(cx - sx / 2 - m, cy - sy / 2 - m, cx + sx / 2 + m, cy + sy / 2 + m))
    g = unary_union(parts).intersection(box(cx - h, cy - h, cx + h, cy + h))
    f = D.x_fillet
    return g.buffer(f, join_style=1).buffer(-f, join_style=1)   # round the inside corners


# ----------------------------------------------------------------------------- linking (owner 2026-10-20)
# Modules sit side by side with their tops touching, so neighbouring frames are 2 x overhang apart.
# Each notch in the deck gets a tongue at its middle, reaching the edge, with a slot near its end.
# A link key (an on-edge strip, like a short cheek) lies on the two facing tongues with a tab down
# through each slot. It stops the modules drifting apart or sliding past each other. Gravity and the
# futon keep it in. One key per module covers a row (n-1 seams) and a 2 x 2 square (4 seams).
def linking(p) -> bool:
    return bool(getattr(getattr(p, "link", None), "enabled", False))


def _tongue_sides(p):
    """(side, centre-relative notch rect) for every notch that opens through a deck edge."""
    h = fr.layout(p).Lf / 2
    out = []
    for x0, y0, x1, y1 in window_rects(p):
        side = "+x" if x1 > h else "-x" if x0 < -h else "+y" if y1 > h else "-y" if y0 < -h else None
        if side:
            out.append((side, (x0, y0, x1, y1)))
    return out


def link_tongues(p) -> list[Polygon]:
    """World-space tongues, one per edge notch, from the notch bottom to the deck edge."""
    if not linking(p):
        return []
    K, L = p.link, fr.layout(p)
    h, cx, cy, w = L.Lf / 2, L.cx, L.cy, K.tongue_w / 2
    out = []
    for side, (x0, y0, x1, y1) in _tongue_sides(p):
        if side == "+x":
            out.append(box(cx + x0 - 1, cy - w, cx + h, cy + w))
        elif side == "-x":
            out.append(box(cx - h, cy - w, cx + x1 + 1, cy + w))
        elif side == "+y":
            out.append(box(cx - w, cy + y0 - 1, cx + w, cy + h))
        else:
            out.append(box(cx - w, cy - h, cx + w, cy + y1 + 1))
    return out


def link_slots(p) -> list[tuple[float, float, float, float]]:
    """World (x0, y0, x1, y1) of the key slots: tab_len long, `edge` mm of wood between slot and deck edge."""
    if not linking(p):
        return []
    K, L, c = p.link, fr.layout(p), p.fit.tight
    h, cx, cy, ts = L.Lf / 2, L.cx, L.cy, fr.thick_slot(p) / 2
    a, b = h - K.edge - K.tab_len, h - K.edge
    out = []
    for side, _ in _tongue_sides(p):
        if side == "+x":
            out.append((cx + a - c, cy - ts, cx + b + c, cy + ts))
        elif side == "-x":
            out.append((cx - b - c, cy - ts, cx - a + c, cy + ts))
        elif side == "+y":
            out.append((cx - ts, cy + a - c, cx + ts, cy + b + c))
        else:
            out.append((cx - ts, cy - b - c, cx + ts, cy - a + c))
    return out


def _add_link_tongues(p, g):
    if not linking(p):
        return g
    K, L = p.link, fr.layout(p)
    h, cx, cy, w, R, rt = L.Lf / 2, L.cx, L.cy, p.link.tongue_w / 2, K.root_r, K.tip_r
    for tg, (side, (x0, y0, x1, y1)) in zip(link_tongues(p), _tongue_sides(p)):
        g = g.union(tg)
        # (root corner, direction along the tongue away from the root, direction away from the tongue)
        if side in ("+x", "-x"):
            sx = 1 if side == "+x" else -1
            xr = cx + (x0 if sx > 0 else x1)
            roots = [((xr, cy + sy * w), (sx, 0), (0, sy)) for sy in (-1, 1)]
            tips = [((cx + sx * h, cy + sy * w), (-sx, 0), (0, -sy)) for sy in (-1, 1)]
        else:
            sy = 1 if side == "+y" else -1
            yr = cy + (y0 if sy > 0 else y1)
            roots = [((cx + sx * w, yr), (0, sy), (sx, 0)) for sx in (-1, 1)]
            tips = [((cx + sx * w, cy + sy * h), (0, -sy), (-sx, 0)) for sx in (-1, 1)]
        for (px, py), (ax, ay), (bx, by) in roots:      # fillet where the tongue meets the notch bottom
            qx, qy = px + R * (ax + bx), py + R * (ay + by)
            sq = box(min(px, qx), min(py, qy), max(px, qx), max(py, qy))
            g = g.union(sq.difference(Point(qx, qy).buffer(R, quad_segs=24)))
        for (px, py), (ax, ay), (bx, by) in tips:       # round the tongue's two corners at the edge
            qx, qy = px + rt * (ax + bx), py + rt * (ay + by)
            sq = box(min(px, qx), min(py, qy), max(px, qx), max(py, qy))
            g = g.difference(sq.difference(Point(qx, qy).buffer(rt, quad_segs=16)))
    return g


def link_key(p) -> Polygon:
    """The key in its own plane (u along the link, v up from the tab bottoms): a strip lying on the two
    tongues, with a tab at each end dropping through the slots. Root reliefs let it sit flat."""
    K, L, r = p.link, fr.layout(p), fr._rd(p)
    tl, e, t = K.tab_len, K.edge, L.t
    n = key_length(p)
    g = unary_union([box(0, t, n, t + K.above), box(0, 0, tl, t + 1), box(n - tl, 0, n, t + 1)])
    g = fr._round_outer(g, 4.0)
    g = g.difference(fr.dogbone((tl, t), (1, -1), r)).difference(fr.dogbone((n - tl, t), (-1, -1), r))
    return g


def key_length(p) -> float:
    K = p.link
    return 2 * p.frame.overhang + K.top_gap + 2 * (K.edge + K.tab_len)


def link_pitch(p) -> float:
    """Centre-to-centre spacing of linked modules (tops touching, plus top_gap)."""
    return p.top.length + p.link.top_gap


def mouth_corners(p) -> list[tuple[float, float, int, int]]:
    """The notched deck's convex corners where the notches meet the edge (away from the legs), as world
    (x, y, dx, dy) with (dx, dy) pointing into the wood."""
    D, L = p.deck, fr.layout(p)
    if getattr(D, "window_style", "hole") != "notch":
        return []
    h, out = L.Lf / 2, []
    for x0, y0, x1, y1 in window_rects(p):
        if x1 > h:                                      # side notch, open at x = +h
            out += [(h, y0, -1, -1), (h, y1, -1, 1)]
        elif x0 < -h:
            out += [(-h, y0, 1, -1), (-h, y1, 1, 1)]
        elif y1 > h:                                    # end notch, open at y = +h
            out += [(x0, h, -1, -1), (x1, h, 1, -1)]
        elif y0 < -h:
            out += [(x0, -h, -1, 1), (x1, -h, 1, 1)]
    return [(L.cx + x, L.cy + y, dx, dy) for x, y, dx, dy in out]


def mouth_cutters(p) -> list[Polygon]:
    """Fillet cutters for the notch mouths: the r x r corner square minus its quarter circle."""
    rr = getattr(p.deck, "mouth_r", 0.0)
    out = []
    if rr <= 0:
        return out
    for x, y, dx, dy in mouth_corners(p):
        cx, cy = x + dx * rr, y + dy * rr
        sq = box(min(x, cx), min(y, cy), max(x, cx), max(y, cy))
        out.append(sq.difference(Point(cx, cy).buffer(rr, quad_segs=32)))
    return out


def _round_mouths(p, g):
    """Round the notch-mouth corners (owner 2026-10-20) with radius deck.mouth_r; leg-side corners stay square."""
    for c in mouth_cutters(p):
        g = g.difference(c)
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
    if getattr(Y, "leg_haunch_style", "straight") == "curve":
        # a long cove, like a bracket: leaves the narrow leg's inner edge going straight up (vertical
        # tangent) and meets the full width under the deck level (horizontal tangent): a quarter ellipse
        zl = zt - Y.leg_haunch_curve_drop
        a, b, n = wt - wn, zt - zl, 48
        curve = [(wt - a * math.cos(math.pi / 2 * k / n), zl + b * math.sin(math.pi / 2 * k / n)) for k in range(n + 1)]
        return Polygon([(wn, -50), *curve, (wt + 50, zt), (wt + 50, -50)])
    zl = zt - Y.leg_haunch_drop
    cut = Polygon([(wn, -50), (wn, zl), (wt, zt), (wt + 50, zt), (wt + 50, -50)])
    rr = Y.leg_haunch_r
    return cut.buffer(-rr, quad_segs=16, join_style="round").buffer(rr, quad_segs=16, join_style="round")


def foot_taper_cut(p) -> Polygon | None:
    """Plate A's feet taper (2026-10-20 option): both edges of the narrow leg slope in by foot_taper over the
    bottom foot_taper_from mm, so the foot is leg_narrow - 2 x foot_taper wide. Only plate A can: plate B's
    floor slot needs its two fingers at full width. Returns the two slivers to cut away. None if disabled."""
    Y, F = p.yagura, p.frame
    ft = getattr(Y, "foot_taper", 0.0)
    if ft <= 0:
        return None
    wn = getattr(Y, "leg_narrow", 0.0) or F.leg_width
    z0 = Y.foot_taper_from
    left = Polygon([(-1, z0), (0, z0), (ft, 0), (ft, -1), (-1, -1)])
    right = Polygon([(wn + 1, z0), (wn, z0), (wn - ft, 0), (wn - ft, -1), (wn + 1, -1)])
    return unary_union([left, right])


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
    if linking(p):  # not placed in a single module; one per module, used between neighbours
        out.append(Part("link key", link_key(p), [], spares=p.link.keys_per_module, kind="link"))
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
