"""Yagura frame (v2, owner 2026-11): four diagonal legs under an X-shaped deck, no aprons. The heater sits in a
well in the deck, in a cradle of two cheeks that hangs from the deck by gravity (kotatsu/frame.py).

Each corner is one plate standing on the corner's diagonal, its outer end at the frame corner: frame.leg_width
wide under the deck (the post, the crosspiece's head slot, a shoulder, the tenon, an inner shoulder), a slim
strip below a haunch. Above the deck the post rises to the top (frame.post_inset in from the plate's end, so it
stays inside the squircle top), and the tenon through the deck takes the corner's one wedge.
(The earlier "+" legs, two crossed plates a corner, are tag plus-legs-archive.)

Joints
  * crosspiece: a plain board (cross_w x head_slot, cut cross_proud taller and sanded to fit) drops into a short
    round-bottomed slot in the plate's head, across it. The deck bears on its top edge with the plate's shoulders,
    which gives the joint a cross_w-wide base against twisting: one plate alone rocks open at about 32 N.
  * leg -> deck: the plate's tenon goes up through a mortise on the diagonal; a wedge, lying on the deck across
    the arm, clamps the deck between the shoulders (and the crosspiece) and itself.
  * heater cradle -> deck: the cheeks' ears rest on the deck top (gravity), the bodies locate in the well.
Plan geometry is drawn per corner in its own frame (corners(): u along the diagonal inwards, v across it).
Assembly: drop each crosspiece into its plate, stand the four legs up, lower the deck over the 4 tenons, tap in
the 4 wedges; screw the heater between the cheeks and lower the cradle into the well.
"""
from __future__ import annotations

import math

from shapely.affinity import affine_transform
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from . import geom
from . import frame as fr
from .frame import Part, Placement


# ----------------------------------------------------------------------------- the leg plate (its own u, v = z plane)
def _tenon_u(p) -> tuple[float, float]:
    """u-range of the plate's tenon, from its outer end: just past the head slot."""
    F, Y = p.frame, p.yagura
    a = F.ear + fr.slot_w(p) / 2 + Y.tenon_gap
    return a, min(a + Y.tenon_w, F.leg_width)          # any leg width left over is an inner shoulder


def leg_hole_z(p) -> tuple[float, float]:
    L, Y = fr.layout(p), p.yagura
    z0 = L.z_deck_bot + L.t_min - Y.hole_drop
    return z0, z0 + Y.hole_h


def post_u(p) -> float:
    """Where the corner post (outside the head slot) ends, from the plate's outer end; it rises past the deck to
    the top's underside, so the top is carried near the frame's corners. 0 = no posts."""
    if not getattr(p.yagura, "corner_posts", False):
        return 0.0
    return p.frame.ear - fr.slot_w(p) / 2


def corner_cut(p) -> float:
    """Kept for the joint model: the deck starts at post_u + fit.tight along the plate (Lf / 2 minus this)."""
    return fr.layout(p).Lf / 2 - post_u(p) - p.fit.tight


def lap_depth(p) -> float:
    """The head slot's depth: the crosspiece's height."""
    return p.yagura.head_slot


def head_slot(p) -> Polygon:
    """The round-bottomed slot in the plate's head (no dogbones: the crosspiece's square edges sit on the arc, a
    gentle root), cut deeper by that seat so the crosspiece's top comes out flush with the shoulders."""
    L, u, w = fr.layout(p), p.frame.ear, fr.slot_w(p)
    R = w / 2
    seat = R - math.sqrt(R * R - (p.material.t_nominal / 2) ** 2)
    zb = L.z_deck_bot - lap_depth(p) - seat
    return box(u - R, zb + R, u + R, L.z_deck_bot + 1).union(Point(u, zb + R).buffer(R, quad_segs=32))


def leg_plate(p) -> Polygon:
    """The leg plate in its own (u from the frame corner inward along the diagonal, v = z) plane: the outline, the
    post and the tenon above the deck, the wedge hole, the head slot with its crush ribs, the foot relief."""
    F, L, r = p.frame, fr.layout(p), fr._rd(p)
    zs, H = L.z_deck_bot, L.H
    wt, tr = F.leg_width, getattr(F, "top_r", 3.0)
    g = leg_outline(p)
    ta, tb = _tenon_u(p)
    g = g.union(fr._round_outer(box(ta, zs - 10, tb, H), tr))
    pu = post_u(p)
    if pu > 0:                                           # the post rises to the top, post_inset in from the end
        g = g.union(post(p))
    g = g.difference(fr.dogbone((ta, zs), (-1, 1), r))   # the tenon's root reliefs (the shoulders seat flat)
    if tb < wt - 0.01:
        g = g.difference(fr.dogbone((tb, zs), (1, 1), r))
    hz0, hz1 = leg_hole_z(p)
    uc, ts = (ta + tb) / 2, fr.thick_slot(p)
    g = g.difference(fr.hole(uc - ts / 2, hz0, uc + ts / 2, hz1, r))
    w, u = fr.slot_w(p), F.ear
    g = g.difference(head_slot(p))
    g = g.union(crush_ribs(p, u - w / 2, u + w / 2, zs - lap_depth(p), zs))
    return g.difference(foot_relief(p))


def post(p) -> Polygon:
    """The corner post above the deck, in the plate's (u, v = z) plane: its inner edge straight up at post_u, its
    outer edge one smooth sweep (owner 2026-11) from the plate's outer edge at the deck's underside, carrying straight
    on from it, to post_inset in at the top: u = post_inset * s^2, s from 0 at the underside to 1 at the top. The top
    rests on the flat end, post_inset to post_u."""
    F, L = p.frame, fr.layout(p)
    zs, H, pu = L.z_deck_bot, L.H, post_u(p)
    pi = getattr(F, "post_inset", 0.0)
    n = 48
    sweep = [(pi * (k / n) ** 2, zs + (H - zs) * k / n) for k in range(n + 1)]
    g = Polygon([(0, zs - 10)] + sweep + [(pu, H), (pu, zs - 10)])
    return fr._round_outer(g, getattr(F, "top_r", 3.0)).union(box(0, zs - 10, pu, zs))


def crosspiece(p) -> Polygon:
    """In its own (u across the plate, v = z from the head slot's bottom) plane: cross_w long, the slot's depth +
    cross_proud tall (sanded to fit). Its top edge bears on the deck."""
    Y = p.yagura
    g = box(0, 0, Y.cross_w, Y.head_slot + Y.cross_proud)
    return geom.squircle_corners(g, lambda c, cv: Y.cross_r if c[1] < 1 else 3.0, p.frame.corner_n)


def crush_ribs(p, u0: float, u1: float, z0: float, z1: float) -> Polygon:
    """Small rounded bumps on both walls of a slot (fit.crush_rib proud per side, radius fit.crush_rib_r), at
    fit.crush_rib_at fractions of the slot's length. They make the joint snug on real stock that's thinner than
    the slot is cut for. Too tight: sand the bumps down (easy)."""
    F = p.fit
    h, R = getattr(F, "crush_rib", 0.0), getattr(F, "crush_rib_r", 10.0)
    if h <= 0:
        return Polygon()
    bumps = []
    for f in getattr(F, "crush_rib_at", [0.6]):
        z = z0 + f * (z1 - z0)
        bumps.append(Point(u0 + h - R, z).buffer(R, quad_segs=32).intersection(box(u0 - 1, z - R, u0 + h, z + R)))
        bumps.append(Point(u1 - h + R, z).buffer(R, quad_segs=32).intersection(box(u1 - h, z - R, u1 + 1, z + R)))
    return unary_union(bumps)


def foot_relief(p) -> Polygon:
    """Shallow arc (yagura.foot_relief deep) under the middle of the foot, so each plate stands on its two ends:
    no rocking on a slightly uneven floor."""
    Y = p.yagura
    sag = getattr(Y, "foot_relief", 0.0)
    if sag <= 0:
        return Polygon()
    wn = foot_w(p)
    a, b = Y.foot_relief_margin, wn - Y.foot_relief_margin
    c = (b - a) / 2
    R = (c * c + sag * sag) / (2 * sag)
    return Point((a + b) / 2, sag - R).buffer(R, quad_segs=64).intersection(box(a - 1, -1, b + 1, sag))


# ----------------------------------------------------------------------------- the outline
def foot_w(p) -> float:
    """The leg's width at the floor: leg_foot_w if set (v2, owner 2026-11: a soft taper, the inner edge
    bending in from leg_narrow at leg_taper_top down to this), else straight at leg_narrow."""
    Y = p.yagura
    wn = getattr(Y, "leg_narrow", 0.0) or p.frame.leg_width
    return getattr(Y, "leg_foot_w", None) or wn


def leg_outline(p) -> Polygon:
    """A leg plate's outline before its joints, in (u from the frame edge inward, v = z), with squircle
    corners (geom.squircle_corners). Owner's haunched leg (2026-10-20): below the deck it keeps only
    leg_narrow of its width; a haunch (leg_haunch_top at the inner edge, leg_haunch_drop lower at the narrow
    line) widens it back to the full leg_width under the shoulders. v2 (owner 2026-11): the haunch is one
    S-curve (each bend takes up to leg_haunch_r along its edges, half the slope at most), the feet foot_r
    (they still stand on their ends), the top corners shoulder_r (the inner shoulder bears on the deck)."""
    Y, F, L = p.yagura, p.frame, fr.layout(p)
    wt, zs = F.leg_width, L.z_deck_bot
    wn = getattr(Y, "leg_narrow", 0.0)
    if wn and wn < wt:
        zt = Y.leg_haunch_top
        wf, ztp = foot_w(p), getattr(Y, "leg_taper_top", 0.0)
        if wf < wn and ztp > 0:      # full width down to leg_taper_top, then a soft taper to the foot
            g = Polygon([(0, 0), (wf, 0), (wn, ztp), (wn, zt - Y.leg_haunch_drop), (wt, zt), (wt, zs), (0, zs)])
        else:
            g = Polygon([(0, 0), (wf, 0), (wn, zt - Y.leg_haunch_drop), (wt, zt), (wt, zs), (0, zs)])
    else:
        g = box(0, 0, wt, zs)

    ztp = getattr(Y, "leg_taper_top", 0.0)

    def size(c, convex):
        if c[1] < 1:
            return F.foot_r
        if c[1] > zs - 1:
            return F.shoulder_r
        if ztp and abs(c[1] - ztp) < 1:
            return getattr(Y, "leg_taper_r", 60.0)        # where the taper starts: a long, soft bend
        return Y.leg_haunch_r
    return geom.squircle_corners(g, size, F.corner_n)


# ----------------------------------------------------------------------------- the corners, in plan
def corners(p) -> list[tuple[int, int, tuple[float, float], tuple[float, float], tuple[float, float]]]:
    """(sx, sy, C, d, n) for each corner, round the table: C the frame corner (world x, y), d the unit vector
    along its diagonal inwards, n = d turned +90 degrees (across the plate)."""
    L = fr.layout(p)
    if abs(L.Lf - L.Wf) > 1e-6:
        raise ValueError("diagonal legs need a square frame")
    k = 1 / math.sqrt(2)
    out = []
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        d = (-sx * k, -sy * k)
        out.append((sx, sy, (L.cx + sx * L.Lf / 2, L.cy + sy * L.Wf / 2), d, (-d[1], d[0])))
    return out


def _plan(g, C, d, n):
    """Plan-local (u along d from the corner, v along n) -> world x-y."""
    return affine_transform(g, [d[0], n[0], d[1], n[1], C[0], C[1]])


def mortise_boxes(p) -> list[Polygon]:
    """Each deck mortise's rectangle (world), without its dogbones: the tenon + fit.tight, thickest stock."""
    ta, tb = _tenon_u(p)
    c, h = p.fit.tight, fr.thick_slot(p) / 2
    return [_plan(box(ta - c, -h, tb + c, h), C, d, n) for *_, C, d, n in corners(p)]


def mortises(p) -> list[Polygon]:
    """The 4 deck mortises (world outlines with their dogbones), each with a wedge through its tenon."""
    ta, tb = _tenon_u(p)
    c, h, r = p.fit.tight, fr.thick_slot(p) / 2, fr._rd(p)
    return [_plan(fr.hole(ta - c, -h, tb + c, h, r), C, d, n) for *_, C, d, n in corners(p)]


def tenon_mid(p) -> float:
    ta, tb = _tenon_u(p)
    return (ta + tb) / 2


def wedge_footprints(p) -> list[Polygon]:
    """Plan (world) of each wedge lying on the deck across its tenon (thickest stock)."""
    wl, _ = wedge_dims(p)
    uc, t = tenon_mid(p), p.material.t_max
    return [_plan(box(uc - t / 2, -wl / 2, uc + t / 2, wl / 2), C, d, n) for *_, C, d, n in corners(p)]


def plate_tops(p) -> list[Polygon]:
    """Each plate's top edge under the deck (both shoulders, the tenon between them), past the post's relief."""
    t = p.material.t_max
    u0 = post_u(p) + 2 * fr._rd(p)
    return [_plan(box(u0, -t / 2, p.frame.leg_width, t / 2), C, d, n) for *_, C, d, n in corners(p)]


def cross_tops(p) -> list[Polygon]:
    """Each crosspiece's top edge (world), where the deck bears on it."""
    Y, t, e = p.yagura, p.material.t_max, p.frame.ear
    return [_plan(box(e - t / 2, -Y.cross_w / 2, e + t / 2, Y.cross_w / 2), C, d, n) for *_, C, d, n in corners(p)]


def corner_trim(p) -> Polygon:
    """The deck stops square across each diagonal just inside the post (fit.tight past it): the posts rise outside
    it, and no thin wood is left beside them."""
    u = post_u(p) + p.fit.tight
    g = box(-1e4, -1e4, 1e4, 1e4)
    for *_, C, d, n in corners(p):
        g = g.difference(_plan(box(-1e3, -1e3, u, 1e3), C, d, n))
    return g


# ----------------------------------------------------------------------------- the deck
def deck_blank(p) -> Polygon:
    """The deck's full square (rounded corners): the X is cut out of it."""
    L = fr.layout(p)
    return fr._round_outer(box(L.O, L.O, L.O + L.Lf, L.O + L.Wf), 8.0)


def pads(p) -> list[Polygon]:
    """The wood the corners need, and no more (owner 2026-11): pad_margin round each mortise (a hole),
    bearing_margin past each lying wedge, each plate's top edge and each crosspiece's."""
    D = p.deck
    keep = [m.buffer(D.pad_margin, join_style="mitre") for m in mortise_boxes(p)]
    return keep + [k.buffer(D.bearing_margin, join_style="mitre")
                   for k in wedge_footprints(p) + plate_tops(p) + cross_tops(p)]


def ring(p) -> Polygon:
    """The wood round the heater well: ring_w beside the cheeks, ear_margin past the cheek ears."""
    D = p.deck
    wx0, _, wx1, _ = fr.well(p)
    c0, c1 = fr.cheek_ys(p)
    return box(wx0 - D.ring_w, c0 - D.ear_margin, wx1 + D.ring_w, c1 + D.ear_margin)


def arms(p) -> list[Polygon]:
    """The four arms, arm_w wide, along the diagonals from the middle to the corners."""
    L, h = fr.layout(p), fr.layout(p).Lf / 2
    return [LineString([(L.cx, L.cy), (L.cx + sx * h, L.cy + sy * h)]).buffer(p.deck.arm_w / 2, cap_style="flat")
            for sx in (-1, 1) for sy in (-1, 1)]


def deck(p) -> Polygon:
    """Deck in world x-y: X-shaped. A ring round the heater well and four diagonal arms (inside corners filleted
    fillet_r), joined to the corner pads (pad_fillet_r); outside corners rounded edge_r; stopped square beside
    the posts, with the 4 mortises and the well."""
    D, r = p.deck, fr._rd(p)
    if D.edge_r >= D.arm_w / 2:
        raise ValueError("[deck] edge_r must stay under arm_w / 2, or the rounding eats the arms")
    core = geom.closing(unary_union([ring(p)] + arms(p)), D.fillet_r)
    g = geom.closing(unary_union(pads(p) + [core]), D.pad_fillet_r)
    g = g.buffer(-D.edge_r, quad_segs=geom.Q).buffer(D.edge_r, quad_segs=geom.Q)
    g = g.intersection(deck_blank(p)).intersection(corner_trim(p))
    for m in mortises(p):
        g = g.difference(m)
    return g.difference(fr.hole(*fr.well(p), r))       # the heater well: the cradle drops in


# ----------------------------------------------------------------------------- wedges, parts
def wedge_dims(p, which: str = "leg") -> tuple[float, float]:
    """(length, head) of the wedges (v2: only the leg wedges; `which` is kept for older callers)."""
    Y = p.yagura
    return Y.wedge_len, Y.wedge_head


def wedge_shape(p, which: str = "leg") -> Polygon:
    """The tapered wedge: its two long faces stay straight (they clamp); v2 (owner 2026-11) squircles its
    struck head (wedge_head_r) and softens the tip."""
    n, h = wedge_dims(p)
    taper = p.fit.wedge_taper
    w = Polygon([(0, 0), (n, 0), (n, h), (0, h - n * taper)])
    hr = getattr(p.yagura, "wedge_head_r", 0.0)
    if hr > 0:
        w = geom.squircle_corners(w, lambda c, cv: hr if c[0] > n - 1 else 3.0, p.frame.corner_n)
        return w
    return fr._round_outer(w, 3.0)


def _vmat(udir, origin) -> tuple[float, ...]:
    """Row-major 4x4 for a vertical plate: u along udir (horizontal), v up, w = u x z (its thickness)."""
    wx, wy = udir[1], -udir[0]
    return (udir[0], 0.0, wx, origin[0],
            udir[1], 0.0, wy, origin[1],
            0.0, 1.0, 0.0, origin[2],
            0.0, 0.0, 0.0, 1.0)


def parts(p) -> list[Part]:
    L, t, Y, F = fr.layout(p), fr.layout(p).t, p.yagura, p.frame
    wl, _ = wedge_dims(p)
    uc = tenon_mid(p)
    plates, crosses, wedges = [], [], []
    for *_, C, d, n in corners(p):
        w = (d[1], -d[0])                                  # the plate's thickness direction (d x z)
        plates.append(Placement("m", (C[0], C[1], 0.0), matrix=_vmat(d, (C[0] - w[0] * t / 2, C[1] - w[1] * t / 2, 0.0))))
        o = (C[0] + d[0] * (F.ear - t / 2) - n[0] * Y.cross_w / 2, C[1] + d[1] * (F.ear - t / 2) - n[1] * Y.cross_w / 2)
        crosses.append(Placement("m", (o[0], o[1], 0.0), matrix=_vmat(n, (o[0], o[1], L.z_deck_bot - Y.head_slot))))
        o = (C[0] + d[0] * (uc - t / 2) - n[0] * wl / 2, C[1] + d[1] * (uc - t / 2) - n[1] * wl / 2)
        wedges.append(Placement("m", (o[0], o[1], 0.0), matrix=_vmat(n, (o[0], o[1], L.z_deck_top))))
    out = [Part("leg plate", leg_plate(p), plates, grain="v"),
           Part("leg crosspiece", crosspiece(p), crosses, grain="u"),
           Part("deck", deck(p), [Placement("z", (0, 0, L.z_deck_bot))], kind="deck")]
    cs, y0 = fr.cheek(p)
    zb, _ = fr.cheek_z(p)
    out.append(Part("heater cheek", cs, [Placement("y", (xi - (t if s < 0 else 0), y0, zb))
                                         for xi, s in zip(fr.cheek_xs(p), (-1, 1))], kind="cheek"))
    out.append(Part("wedge", wedge_shape(p), wedges, spares=2, kind="wedge"))
    return out
