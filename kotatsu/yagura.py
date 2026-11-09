"""Yagura frame: four "+" corner legs, each two crossed plates, carry a deck; no aprons. The heater
sits in a well in the deck, in a cradle of two cheeks that hangs from the deck by gravity (kotatsu/frame.py).

Leg plates are 110 mm wide under the deck (a 20 mm ear arm outside the corner cross-lap, the slot, a
10 mm shoulder, a 50 mm tenon, a 10 mm inner shoulder) and slim strips below a short haunch
(yagura.leg_narrow: a 20 mm finger each side of the slot). The ear arms rise past the deck as corner
posts that carry the top.

Joints
  * legs: cross-lap at each corner ("A" plates slotted from the shoulder down, "B" plates from the floor up)
  * leg -> deck: every plate's top edge is a shoulder under the deck, with one tenon through it.
    v2: one wedge per leg. Each corner wedges its "A" plate: a small wedge through the tenon, lying on
    the deck, clamps the deck between shoulder and wedge. The other plate is held by gravity, trapped
    between the floor and the wedged-down deck, and hangs on the A plate's cross-lap when the frame is
    lifted. A runs along x at two diagonal corners and along y at the other two, so a push either way meets
    two wedged plates. (Gravity alone everywhere can't work: the ~20 N on each plate is far too little to
    keep the shoulders down, and the tenon rocks in its mortise.)
  * heater cradle -> deck: the cheeks' ears rest on the deck top (gravity), the bodies locate in the well.
Assembly: cross the 4 pairs of plates into "+" legs, stand them up, lower the deck over the 4 tenons,
tap in the 4 wedges; screw the heater between the cheeks and lower the cradle into the well.
"""
from __future__ import annotations

import math

from shapely.affinity import affine_transform
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from . import geom
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
    """One leg plate in its own (u from the frame edge inward, v = z) plane. A (slotted from the top) has the
    tenon through the deck and its wedge hole; B (v2) has none: its top edge is all shoulder, under the deck."""
    F, L, r = p.frame, fr.layout(p), fr._rd(p)
    zs, H = L.z_deck_bot, L.H
    wt = F.leg_width
    g = leg_outline(p)
    ta, tb = _tenon_u(p)
    if slotted_from_top:
        g = g.union(fr._round_outer(box(ta, zs - 10, tb, H), getattr(F, "top_r", 3.0)))
    pu = post_u(p)
    if pu > 0:                                           # corner post: the ear arm rises to the top too
        g = g.union(fr._round_outer(box(0, zs - 10, pu, H), getattr(F, "top_r", 3.0)).intersection(box(0, 0, pu, H)))
        if not slotted_from_top:                         # B: shoulder runs on from the post -> root relief
            g = g.difference(fr.dogbone((pu, zs), (1, 1), r))
    if slotted_from_top:                                 # A's tenon: root reliefs (the shoulders seat flat), wedge hole
        g = g.difference(fr.dogbone((ta, zs), (-1, 1), r))
        if tb < wt - 0.01:
            g = g.difference(fr.dogbone((tb, zs), (1, 1), r))
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
    wn = foot_w(p)
    a, b = Y.foot_relief_margin, wn - Y.foot_relief_margin
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
    """Cross-laps share the leg height below the deck (+ lap_extra each, so the floor sets the height).
    Diagonal legs: the plate's head slot, the crosspiece's height."""
    if diagonal(p):
        return p.diagonal.head_slot
    return fr.layout(p).z_deck_bot / 2 + p.frame.lap_extra


def a_runs_along_x(sx: int, sy: int) -> bool:
    """Whether the corner (sx, sy) (each -1 or +1, from the centre) has its wedged A plate along x: at the
    (-,-) and (+,+) corners. At the other two it runs along y."""
    return sx * sy > 0


def mortise_info(p) -> list[tuple[tuple[float, float, float, float], str, int, int]]:
    """Every deck mortise as ((x0, y0, x1, y1) world, plate axis, sx, sy): tenon + in-plane clearance,
    thickest stock. v2: one per corner, for the A plate's tenon (B plates have none)."""
    L = fr.layout(p)
    ta, tb = _tenon_u(p)
    c, h = p.fit.tight, fr.thick_slot(p) / 2
    out = []
    for y, sy in zip(L.yL, (-1, 1)):                     # x plates (in the x-z plane at y)
        for (a, b), sx in zip(((L.O + ta, L.O + tb), (L.O + L.Lf - tb, L.O + L.Lf - ta)), (-1, 1)):
            if a_runs_along_x(sx, sy):
                out.append(((a - c, y - h, b + c, y + h), "x", sx, sy))
    for x, sx in zip(L.xS, (-1, 1)):                     # y plates (in the y-z plane at x)
        for (a, b), sy in zip(((L.O + ta, L.O + tb), (L.O + L.Wf - tb, L.O + L.Wf - ta)), (-1, 1)):
            if not a_runs_along_x(sx, sy):
                out.append(((x - h, a - c, x + h, b + c), "y", sx, sy))
    return out


def mortises(p) -> list:
    """World (x0, y0, x1, y1) of the 4 deck mortises, each with a wedge through its tenon (diagonal legs:
    the mortise outlines, turned 45 degrees, as polygons)."""
    if diagonal(p):
        return diag_mortises(p)
    return [m for m, *_ in mortise_info(p)]


def deck_blank(p) -> Polygon:
    """The deck's full square, cut around the two posts at each corner (L-shaped cut-outs)."""
    L, r = fr.layout(p), fr._rd(p)
    g = fr._round_outer(box(L.O, L.O, L.O + L.Lf, L.O + L.Wf), 8.0)
    if post_u(p) > 0:
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
    return g


def wedge_footprints(p) -> list[Polygon]:
    """Plan (world x-y) of each wedge lying on the deck, across its tenon (thickest stock)."""
    if diagonal(p):
        return diag_wedge_footprints(p)
    wl, _ = wedge_dims(p)
    t = p.material.t_max
    out = []
    for x0, y0, x1, y1 in mortises(p):
        xc, yc = (x0 + x1) / 2, (y0 + y1) / 2
        out.append(box(xc - t / 2, yc - wl / 2, xc + t / 2, yc + wl / 2) if x1 - x0 > y1 - y0
                   else box(xc - wl / 2, yc - t / 2, xc + wl / 2, yc + t / 2))
    return out


def plate_tops(p, which: str) -> list[Polygon]:
    """Plan (world x-y) of each `which` ("A" or "B") plate's top edge under the deck, from past its post's
    root relief to its inner end: it bears on the deck (A: the shoulders either side of the tenon; B: all
    of it, which keeps the plate trapped against the floor). Diagonal legs: "A" the plates, "B" the
    crosspieces' top edges."""
    if diagonal(p):
        return diag_plate_tops(p) if which == "A" else diag_cross_tops(p)
    L, t = fr.layout(p), p.material.t_max
    u0, u1 = post_u(p) + 2 * fr._rd(p), p.frame.leg_width          # along the plate, from the frame edge
    out = []
    for _, axis, sx, sy in mortise_info(p):              # one A and one B per corner
        if (axis == "x") == (which == "A"):              # this plate runs along x, at y = yL
            y = L.yL[0 if sy < 0 else 1]
            x0, x1 = (L.O + u0, L.O + u1) if sx < 0 else (L.O + L.Lf - u1, L.O + L.Lf - u0)
            out.append(box(x0, y - t / 2, x1, y + t / 2))
        else:                                            # along y, at x = xS
            x = L.xS[0 if sx < 0 else 1]
            y0, y1 = (L.O + u0, L.O + u1) if sy < 0 else (L.O + L.Wf - u1, L.O + L.Wf - u0)
            out.append(box(x - t / 2, y0, x + t / 2, y1))
    return out


def pads(p) -> list[Polygon]:
    """The wood the corners need, and no more (owner 2026-11): pad_margin round each mortise (a hole),
    bearing_margin past each lying wedge and each plate's top edge. Nothing outside the B plates."""
    D = p.deck
    if diagonal(p):
        keep = [m.buffer(D.pad_margin, join_style="mitre") for m in diag_mortise_boxes(p)]
        return keep + [k.buffer(D.bearing_margin, join_style="mitre")
                       for k in diag_wedge_footprints(p) + diag_plate_tops(p) + diag_cross_tops(p)]
    keep = [box(*m).buffer(D.pad_margin, join_style="mitre") for m in mortises(p)]
    keep += [k.buffer(D.bearing_margin, join_style="mitre")
             for k in wedge_footprints(p) + plate_tops(p, "A") + plate_tops(p, "B")]
    return keep


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
    """Deck in world x-y (v2): X-shaped. A ring round the heater well and four diagonal arms (inside corners
    filleted fillet_r), joined to the corner pads (pad_fillet_r); outside corners rounded edge_r; cut
    around the posts, with the 4 mortises and the well."""
    D, r = p.deck, fr._rd(p)
    if D.edge_r >= D.arm_w / 2:
        raise ValueError("[deck] edge_r must stay under arm_w / 2, or the rounding eats the arms")
    blank = deck_blank(p)
    core = geom.closing(unary_union([ring(p)] + arms(p)), D.fillet_r)
    g = geom.closing(unary_union(pads(p) + [core]), D.pad_fillet_r)
    g = g.buffer(-D.edge_r, quad_segs=geom.Q).buffer(D.edge_r, quad_segs=geom.Q)   # before the post cut-outs,
    g = g.intersection(blank)                                                      # which stay as in v1
    if diagonal(p):
        for m in diag_mortises(p):
            g = g.difference(m)
        g = g.intersection(diag_corner_trim(p))
        return g.difference(fr.hole(*fr.well(p), r))
    for x0, y0, x1, y1 in mortises(p):
        g = g.difference(fr.hole(x0, y0, x1, y1, r))
    g = g.difference(fr.hole(*fr.well(p), r))           # the heater well: the cradle drops in
    return g


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


# ----------------------------------------------------------------------------- diagonal legs
def diagonal(p) -> bool:
    return getattr(p.yagura, "leg_style", "plus") == "diagonal"


def _dp(p):
    """p as a diagonal plate sees it: [diagonal]'s ear, leg_width and haunch in place of the "+" legs'."""
    from types import SimpleNamespace as NS
    D = p.diagonal
    q = NS(**vars(p))
    q.frame = NS(**{**vars(p.frame), "ear": D.ear, "leg_width": D.leg_width})
    q.yagura = NS(**{**vars(p.yagura), "leg_haunch_top": D.leg_haunch_top})
    return q


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


def diag_plate(p) -> Polygon:
    """The diagonal plate: plate A's shape at [diagonal]'s sizes, its slot only head_slot deep."""
    return leg_plate(_dp(p), True)


def crosspiece(p) -> Polygon:
    """In its own (u across the plate, v = z from the head slot's bottom) plane: cross_w long, the slot's
    depth + cross_proud tall (sanded to fit). Its top edge bears on the deck."""
    D = p.diagonal
    g = box(0, 0, D.cross_w, D.head_slot + D.cross_proud)
    return geom.squircle_corners(g, lambda c, cv: D.cross_r if c[1] < 1 else 3.0, p.frame.corner_n)


def diag_mortise_boxes(p) -> list[Polygon]:
    """Each mortise's rectangle (world), without its dogbones: the tenon + clearance, thickest stock."""
    q = _dp(p)
    ta, tb = _tenon_u(q)
    c, h = p.fit.tight, fr.thick_slot(p) / 2
    return [_plan(box(ta - c, -h, tb + c, h), C, d, n) for *_, C, d, n in corners(p)]


def diag_mortises(p) -> list[Polygon]:
    q, r = _dp(p), fr._rd(p)
    ta, tb = _tenon_u(q)
    c, h = p.fit.tight, fr.thick_slot(p) / 2
    return [_plan(fr.hole(ta - c, -h, tb + c, h, r), C, d, n) for *_, C, d, n in corners(p)]


def diag_tenon_mid(p) -> float:
    ta, tb = _tenon_u(_dp(p))
    return (ta + tb) / 2


def diag_wedge_footprints(p) -> list[Polygon]:
    wl, _ = wedge_dims(p)
    uc, t = diag_tenon_mid(p), p.material.t_max
    return [_plan(box(uc - t / 2, -wl / 2, uc + t / 2, wl / 2), C, d, n) for *_, C, d, n in corners(p)]


def diag_plate_tops(p) -> list[Polygon]:
    """Each plate's top edge under the deck (both shoulders, the tenon between them), past the post's relief."""
    q, t = _dp(p), p.material.t_max
    u0 = post_u(q) + 2 * fr._rd(p)
    return [_plan(box(u0, -t / 2, p.diagonal.leg_width, t / 2), C, d, n) for *_, C, d, n in corners(p)]


def diag_cross_tops(p) -> list[Polygon]:
    D, t = p.diagonal, p.material.t_max
    return [_plan(box(D.ear - t / 2, -D.cross_w / 2, D.ear + t / 2, D.cross_w / 2), C, d, n)
            for *_, C, d, n in corners(p)]


def diag_corner_trim(p) -> Polygon:
    """The deck stops square across each diagonal just inside the post (fit.tight past it): the posts rise
    outside it, and no thin wood is left beside them."""
    q = _dp(p)
    u = post_u(q) + p.fit.tight
    g = box(-1e4, -1e4, 1e4, 1e4)
    for *_, C, d, n in corners(p):
        g = g.difference(_plan(box(-1e3, -1e3, u, 1e3), C, d, n))
    return g


def _vmat(udir, origin) -> tuple[float, ...]:
    """Row-major 4x4 for a vertical plate: u along udir (horizontal), v up, w = u x z (its thickness)."""
    wx, wy = udir[1], -udir[0]
    return (udir[0], 0.0, wx, origin[0],
            udir[1], 0.0, wy, origin[1],
            0.0, 1.0, 0.0, origin[2],
            0.0, 0.0, 0.0, 1.0)


def diag_parts(p) -> list[Part]:
    L, t, D = fr.layout(p), fr.layout(p).t, p.diagonal
    wl, _ = wedge_dims(p)
    uc = diag_tenon_mid(p)
    plates, crosses, wedges = [], [], []
    for *_, C, d, n in corners(p):
        w = (d[1], -d[0])                                  # the plate's thickness direction (d x z)
        plates.append(Placement("m", (C[0], C[1], 0.0), matrix=_vmat(d, (C[0] - w[0] * t / 2, C[1] - w[1] * t / 2, 0.0))))
        o = (C[0] + d[0] * (D.ear - t / 2) - n[0] * D.cross_w / 2, C[1] + d[1] * (D.ear - t / 2) - n[1] * D.cross_w / 2)
        crosses.append(Placement("m", (o[0], o[1], 0.0), matrix=_vmat(n, (o[0], o[1], L.z_deck_bot - D.head_slot))))
        o = (C[0] + d[0] * (uc - t / 2) - n[0] * wl / 2, C[1] + d[1] * (uc - t / 2) - n[1] * wl / 2)
        wedges.append(Placement("m", (o[0], o[1], 0.0), matrix=_vmat(n, (o[0], o[1], L.z_deck_top))))
    out = [Part("leg plate", diag_plate(p), plates, grain="v"),
           Part("leg crosspiece", crosspiece(p), crosses, grain="u"),
           Part("deck", deck(p), [Placement("z", (0, 0, L.z_deck_bot))], kind="deck")]
    cs, y0 = fr.cheek(p)
    zb, _ = fr.cheek_z(p)
    out.append(Part("heater cheek", cs, [Placement("y", (xi - (t if s < 0 else 0), y0, zb))
                                         for xi, s in zip(fr.cheek_xs(p), (-1, 1))], kind="cheek"))
    out.append(Part("wedge", wedge_shape(p), wedges, spares=2, kind="wedge"))
    return out


def parts(p) -> list[Part]:
    if diagonal(p):
        return diag_parts(p)
    L, t = fr.layout(p), fr.layout(p).t
    out: list[Part] = []
    xp = [(Placement("x", (L.O, y - t / 2, 0)), -1, sy) for y, sy in zip(L.yL, (-1, 1))] + \
         [(Placement("x", (L.O + L.Lf, y - t / 2, 0), mirror_u=True), 1, sy) for y, sy in zip(L.yL, (-1, 1))]
    yp = [(Placement("y", (x - t / 2, L.O, 0)), sx, -1) for x, sx in zip(L.xS, (-1, 1))] + \
         [(Placement("y", (x - t / 2, L.O + L.Wf, 0), mirror_u=True), sx, 1) for x, sx in zip(L.xS, (-1, 1))]
    pa = [pl for pl, sx, sy in xp if a_runs_along_x(sx, sy)] + [pl for pl, sx, sy in yp if not a_runs_along_x(sx, sy)]
    pb = [pl for pl, sx, sy in xp if not a_runs_along_x(sx, sy)] + [pl for pl, sx, sy in yp if a_runs_along_x(sx, sy)]
    out.append(Part("leg plate A", leg_plate(p, True), pa, grain="v"))   # slotted from the shoulder down; wedged
    out.append(Part("leg plate B", leg_plate(p, False), pb, grain="v"))  # slotted from the floor up; grain up the leg
    out.append(Part("deck", deck(p), [Placement("z", (0, 0, L.z_deck_bot))], kind="deck"))
    cs, y0 = fr.cheek(p)
    zb, _ = fr.cheek_z(p)
    out.append(Part("heater cheek", cs, [Placement("y", (xi - (t if s < 0 else 0), y0, zb))
                                         for xi, s in zip(fr.cheek_xs(p), (-1, 1))], kind="cheek"))
    # wedges lie on the deck and pass through each A plate's tenon, normal to its plate
    wl, _ = wedge_dims(p)
    lw = []
    for x0, y0, x1, y1 in mortises(p):
        xc, yc = (x0 + x1) / 2, (y0 + y1) / 2
        if x1 - x0 > y1 - y0:          # x plate tenon: wedge runs along y (plate in the y-z plane)
            lw.append(Placement("y", (xc - t / 2, yc - wl / 2, L.z_deck_top)))
        else:
            lw.append(Placement("x", (xc - wl / 2, yc - t / 2, L.z_deck_top)))
    out.append(Part("wedge", wedge_shape(p), lw, spares=2, kind="wedge"))
    return out
