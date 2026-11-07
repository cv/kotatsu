"""Zaisu: legless floor chairs for the kotatsu (v2, owner 2026-11), cut from the same sheet as the table.

Chair coordinates (mm): X across the seat (0 in the middle), Y from the chair's front edge backwards, Z up
from the floor. Each chair is
  * 2 side frames (in the Y-Z plane): a floor runner and a back post leaning back by `recline`;
  * a seat board, its 2 tabs a side through holes in the runners, board_lift off the floor. The wood under
    each hole carries the board, and the sitter on the board holds the runners down (no tipping back);
  * a front stretcher and a back panel (with a cut-out), each hooking into slots in the side frames: the
    part goes in raised by hook_drop and drops, so a finger on each tab hangs behind the side frame. They
    stop the sides spreading; gravity keeps them down.
No wedges, no glue, no hardware.
Assembly: lay the board down; push one side frame onto its tabs; put the stretcher's and the back's tabs into
that side's slots (raised); push the other side frame on; let the stretcher and the back drop.
"""
from __future__ import annotations

import math

from shapely.affinity import rotate, translate
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from . import frame as fr
from .frame import Part, Placement


def _z(p):
    return p.zaisu


def _tan(p) -> float:
    return math.tan(math.radians(_z(p).recline))


def post_origin(p) -> float:
    """Y where the back post's centre line meets the floor."""
    Z = _z(p)
    return Z.front_gap + Z.seat_d + Z.post_w / 2


def post_point(p, s: float) -> tuple[float, float]:
    """(Y, Z) on the post's centre line, s mm along it from the floor."""
    a = math.radians(_z(p).recline)
    return post_origin(p) + s * math.sin(a), s * math.cos(a)


def back_s(p) -> tuple[float, float]:
    """(start, end) of the back panel along the post, from the floor."""
    Z = _z(p)
    s0 = Z.back_z0 / math.cos(math.radians(Z.recline))
    return s0, s0 + Z.back_h


def post_end(p) -> float:
    """The post stops post_cap past the back panel's top edge (measured along it): nothing to carry above."""
    return back_s(p)[1] + _z(p).post_cap


def back_tabs(p) -> list[float]:
    """Each back tab's lower edge, measured up the panel from its lower edge (installed, dropped)."""
    Z = _z(p)
    e = Z.back_frame / 2 - Z.tab_w / 2
    return [e, Z.back_h - e - Z.tab_w]


def board_tab_ys(p) -> list[float]:
    Z = _z(p)
    return [Z.front_gap + f * Z.seat_d for f in (0.2, 0.8)]


def stretcher_y(p) -> float:
    """Y of the stretcher's front face: centred in the gap in front of the board."""
    Z = _z(p)
    return (Z.front_gap - p.material.t_max) / 2


def stretcher_tab_z(p) -> float:
    """The stretcher tab's lower edge above the floor (installed): centred on the runner."""
    Z = _z(p)
    return (Z.runner_h - Z.tab_w - Z.hook_drop) / 2


def _hook_tabs(p, half: float, v0s: list[float], body: Polygon) -> Polygon:
    """Tabs at u = +-half (the side frames' inner faces) for each lower edge v0 in v0s, each with a finger
    hanging hook_drop below it outside the side frame; root reliefs so the part seats flat."""
    Z, r, tmax = _z(p), fr._rd(p), p.material.t_max
    out_face = half + tmax + 1.0                       # finger starts 1 mm past the thickest side frame
    g = body
    for s in (-1, 1):
        for v0 in v0s:
            a, b = sorted((s * (half - 1.0), s * (out_face + Z.tab_out)))
            g = g.union(box(a, v0, b, v0 + Z.tab_w))
            fa, fb = sorted((s * out_face, s * (out_face + Z.tab_out)))
            g = g.union(box(fa, v0 - Z.hook_drop, fb, v0))
    g = fr._round_outer(g, 3.0)
    for s in (-1, 1):
        for v0 in v0s:
            edge = s * (half - 0.5)
            if g.contains(box(edge - 0.1 * s, v0 - 2, edge, v0 - 1).centroid):
                g = g.difference(fr.dogbone((edge, v0), (s, -1), r))
            if g.contains(box(edge - 0.1 * s, v0 + Z.tab_w + 1, edge, v0 + Z.tab_w + 2).centroid):
                g = g.difference(fr.dogbone((edge, v0 + Z.tab_w), (s, 1), r))
            g = g.difference(fr.dogbone((s * out_face, v0), (-s, -1), r))   # finger root
    return g


def side(p) -> Polygon:
    """Side frame in (u = Y, v = Z)."""
    Z, r = _z(p), fr._rd(p)
    tan = _tan(p)
    run = box(0, 0, Z.runner_len, Z.runner_h)
    y0 = post_origin(p)
    s_end = post_end(p)
    post = LineString([(y0 - 60 * tan, -60), (y0 + s_end * math.sin(math.radians(Z.recline)),
                                              s_end * math.cos(math.radians(Z.recline)))]).buffer(Z.post_w / 2, cap_style="flat")
    g = unary_union([run, post]).intersection(box(-1, 0, 5000, 5000))
    g = g.buffer(Z.fillet_r).buffer(-Z.fillet_r).intersection(box(-1, 0, 5000, 5000))   # inside fillet
    g = fr._round_outer(g, Z.edge_r)
    sw = fr.slot_w(p)
    ys, zt = stretcher_y(p) - p.fit.slot_clearance / 2, stretcher_tab_z(p)
    g = g.difference(fr.hole(ys, zt, ys + sw, zt + Z.tab_w + Z.hook_drop + p.fit.tight, r))
    for yb in board_tab_ys(p):                          # the seat board's tabs
        h = Z.board_tab_w / 2 + p.fit.tight
        g = g.difference(fr.hole(yb - h, Z.board_lift, yb + h, Z.board_lift + fr.thick_slot(p), r))
    s0, _ = back_s(p)
    for v0 in back_tabs(p):                             # the back panel's tabs, along the post
        sl = fr.hole(-sw / 2, s0 + v0, sw / 2, s0 + v0 + Z.tab_w + Z.hook_drop + p.fit.tight, r)
        sl = rotate(sl, -Z.recline, origin=(0, 0))      # lean back like the post
        g = g.difference(translate(sl, y0, 0))
    return g


def board(p) -> Polygon:
    """Seat board in (u = X, v = Y), with a cut-out under the thighs (weight)."""
    Z, r, tmax = _z(p), fr._rd(p), p.material.t_max
    half = Z.seat_w / 2
    g = box(-half + 0.5, Z.front_gap, half - 0.5, Z.front_gap + Z.seat_d)
    for s in (-1, 1):
        for yb in board_tab_ys(p):
            a, b = sorted((s * (half - 1.0), s * (half + tmax + 1.0 + Z.board_tab_out)))
            g = g.union(box(a, yb - Z.board_tab_w / 2, b, yb + Z.board_tab_w / 2))
    g = fr._round_outer(g, 3.0)
    for s in (-1, 1):
        for yb in board_tab_ys(p):
            for dv, sv in ((-Z.board_tab_w / 2, -1), (Z.board_tab_w / 2, 1)):
                g = g.difference(fr.dogbone((s * (half - 0.5), yb + dv), (s, sv), r))
    m = Z.board_frame
    cut = box(-half + m, Z.front_gap + m, half - m, Z.front_gap + Z.seat_d * Z.board_cut_depth)
    return g.difference(fr._round_outer(cut, 40.0))


def stretcher(p) -> Polygon:
    """Front stretcher in (u = X, v = Z), installed (dropped) position."""
    Z = _z(p)
    half, zt = Z.seat_w / 2, stretcher_tab_z(p)
    body = box(-half + 0.5, max(zt - Z.hook_drop, 2.0), half - 0.5, zt + Z.tab_w + Z.hook_drop)
    return _hook_tabs(p, half, [zt], body)


def back(p) -> Polygon:
    """Back panel in (u = X, v = up the panel from its lower edge), with a cut-out (weight, and a handle)."""
    Z = _z(p)
    half, m, st = Z.seat_w / 2, Z.back_frame, Z.back_stile
    body = box(-half + 0.5, 0, half - 0.5, Z.back_h)
    g = _hook_tabs(p, half, back_tabs(p), body)
    return g.difference(fr._round_outer(box(-half + st, m, half - st, Z.back_h - m), 40.0))


# ----------------------------------------------------------------------------- placement
def _mat(ucol, vcol, wcol, origin) -> tuple[float, ...]:
    """Row-major 4x4: part (u, v, w) -> chair (X, Y, Z)."""
    return (ucol[0], vcol[0], wcol[0], origin[0],
            ucol[1], vcol[1], wcol[1], origin[1],
            ucol[2], vcol[2], wcol[2], origin[2],
            0.0, 0.0, 0.0, 1.0)


def _mul(A, B) -> tuple[float, ...]:
    return tuple(sum(A[4 * i + k] * B[4 * k + j] for k in range(4)) for i in range(4) for j in range(4))


def local_matrices(p) -> dict[str, list[tuple[float, ...]]]:
    """Each part's placements in chair coordinates."""
    Z, t = _z(p), p.material.t_nominal
    half = Z.seat_w / 2
    a = math.radians(Z.recline)
    d = (0.0, math.sin(a), math.cos(a))                   # up the post
    w = (0.0, -math.cos(a), math.sin(a))                  # through the back panel (u x d)
    s0, _ = back_s(p)
    py, pz = post_point(p, s0)
    return {
        "zaisu side": [_mat((0, 1, 0), (0, 0, 1), (1, 0, 0), (x0, 0, 0)) for x0 in (-half - t, half)],
        "zaisu seat board": [_mat((1, 0, 0), (0, 1, 0), (0, 0, 1), (0, 0, Z.board_lift))],
        "zaisu stretcher": [_mat((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, stretcher_y(p) + t, 0))],
        "zaisu back": [_mat((1, 0, 0), d, w, (0, py - w[1] * t / 2, pz - w[2] * t / 2))],
    }


def chair_frames(p) -> list[tuple[float, ...]]:
    """World matrices for each chair: on the table's -y and +y sides (then -x, +x), facing it, its front
    at the floor pillows' inner edge (kotatsu/room.py)."""
    from . import room
    L, Z = fr.layout(p), _z(p)
    front = room.seat_offset(p) - p.room.zabuton[1] / 2
    out = []
    for k in range(int(Z.count)):
        ang = [180.0, 0.0, 90.0, 270.0][k % 4]            # chair Y points away from the table
        c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        # chair (X, Y) -> world: rotate, then move the chair's front to `front` from the table centre
        oy = (0.0, 1.0)
        dx, dy = c * oy[0] - s * oy[1], s * oy[0] + c * oy[1]
        out.append((c, -s, 0.0, L.cx + dx * front,
                    s, c, 0.0, L.cy + dy * front,
                    0.0, 0.0, 1.0, 0.0,
                    0.0, 0.0, 0.0, 1.0))
    return out


def parts(p) -> list[Part]:
    """The chairs' parts (all chairs), with world placements as matrices."""
    if int(getattr(_z(p), "count", 0)) <= 0:
        return []
    shapes = {"zaisu side": side(p), "zaisu seat board": board(p), "zaisu stretcher": stretcher(p), "zaisu back": back(p)}
    loc = local_matrices(p)
    frames = chair_frames(p)
    out = []
    for name, g in shapes.items():
        pls = [Placement("m", (W[3], W[7], W[11]), matrix=_mul(W, M)) for W in frames for M in loc[name]]
        out.append(Part(name, g, pls, kind="chair"))
    return out


# ----------------------------------------------------------------------------- checks
def tipping_n(p) -> float:
    """Push back on the back, at lean_z, that tips a chair over its runners' back ends with a sitter_n
    sitter on it (centre of weight seat_d / 2 into the seat). The board holds the runners down."""
    Z = _z(p)
    xs = Z.front_gap + Z.seat_d / 2
    return Z.sitter_n * (Z.runner_len - xs) / Z.lean_z


def post_stress(p, n: float | None = None) -> float:
    """Worst in-plane bending stress (MPa) in a post: at its root (the runner's top) and through the lower back
    slot (net of the slot), under a lean of n (default back_check_n) at lean_z, shared by the two posts.
    Thinnest stock."""
    Z, t = _z(p), p.material.t_min
    n = Z.back_check_n if n is None else n
    a = math.radians(Z.recline)
    w, sw = Z.post_w, fr.slot_w(p)
    out = (n / 2) * (Z.lean_z - Z.runner_h) / (t * w ** 2 / 6)
    s0, _ = back_s(p)
    for v0 in back_tabs(p):
        z = (s0 + v0 + (Z.tab_w + Z.hook_drop) / 2) * math.cos(a)
        if z < Z.lean_z:
            S = 2 * t * (w ** 3 - sw ** 3) / 12 / w
            out = max(out, (n / 2) * (Z.lean_z - z) / S)
    return out


def back_stress(p, n: float | None = None) -> tuple[float, float]:
    """The back panel face-on under a lean of n (default back_check_n) at mid-span, simply supported in the
    posts' slots: (stress MPa, sag mm) in its two rails, thinnest stock, across the face grain (worst)."""
    Z, t = _z(p), p.material.t_min
    n = Z.back_check_n if n is None else n
    E = p.loads.E_cross
    L, b = Z.seat_w, 2 * Z.back_frame
    return n * L / 4 / (b * t * t / 6), n * L ** 3 / (48 * E * b * t ** 3 / 12)


def board_stress(p, n: float | None = None) -> tuple[float, float]:
    """The seat board face-on under a sitter of n (default seat_check_n) at mid-span, simply supported on its
    tabs: (stress MPa, sag mm) through the section beside the cut-out, thinnest stock, across the grain."""
    Z, t = _z(p), p.material.t_min
    n = Z.seat_check_n if n is None else n
    E = p.loads.E_cross
    L = Z.seat_w
    b = Z.seat_d - (Z.seat_d * Z.board_cut_depth - Z.board_frame)
    return n * L / 4 / (b * t * t / 6), n * L ** 3 / (48 * E * b * t ** 3 / 12)


def kg_per_chair(p) -> float:
    Z = _z(p)
    rho = p.material.density_kg_m3 * p.material.t_nominal / 1e9
    a = 2 * side(p).area + board(p).area + stretcher(p).area + back(p).area
    return a * rho
