"""Finite-element checks of the zaisu (kotatsu/zaisu.py), with kotatsu/fea.py's tools, next to zaisu.py's
lumped checks (post_stress, back_stress, board_stress). Thinnest stock; each part's grain the weaker way
round (the nester may turn chair parts any way).

  * seat_case: the seat board, a plate on its four tabs (they rest on the bottoms of the side frames'
    holes: push up only), under a sitter spread over a cushion-sized patch.
  * back_case: the back panel, a plate held at its hook tabs in the posts' slots (they push forward only),
    leaned on along its top rail (where a back touches: the middle is cut out).
  * side_case: a side frame in plane stress, standing on the floor (push only; gripping it sideways),
    loaded through the board's tab holes (its share of the sitter) and through the back's slots (its share
    of the lean, split between the two slots by lever).
"""
from __future__ import annotations

import math

import numpy as np
from shapely import contains_xy
from shapely.affinity import rotate, translate
from shapely.geometry import LineString, box
from shapely.ops import unary_union

from . import fea, zaisu
from . import frame as fr


def _away(m, sup, t):
    return ~fea.near(m, sup, t)


def seat_case(p, n: float | None = None, h: float = 8.0) -> dict:
    Z, M, Ld = p.zaisu, p.material, p.loads
    n = Z.seat_check_n if n is None else n
    t = M.t_min
    g = zaisu.board(p)
    half, tm = Z.seat_w / 2, M.t_max
    pads = [box(s * half if s > 0 else -half - tm, yb - Z.board_tab_w / 2, half + tm if s > 0 else -half, yb + Z.board_tab_w / 2)
            .intersection(g) for s in (-1, 1) for yb in zaisu.board_tab_ys(p)]
    pads = [x for x in pads if x.area > 0]
    cw, cd = Z.cushion
    yc = Z.front_gap + 0.6 * Z.seat_d                                   # a sitter sits towards the back
    patch = box(-cw / 3, yc - cd / 3, cw / 3, yc + cd / 3).intersection(g)
    m = fea.mesh(g, h, extra=pads)
    q = np.full(m.t.shape[1], M.density_kg_m3 * 1e-9 * t * 9.81) + fea.pressure(m, patch, n)
    sv = np.where(fea.in_any(m, pads, at="vertices"))[0]
    r = fea.plate(m, t, Ld.E_cross, M.E_par, Ld.G_plate, q, sv)        # spans x across the grain (worst)
    away = _away(m, unary_union(pads), t)
    pk = fea.peaks(fea_swap(r), away, M.f_m, Ld.f_m_cross, Ld.f_v_plate)
    return {"part": "zaisu seat board", "n": n, "result": r, "local": ~away, "sag_mm": float(r.w.max()),
            "peak": pk, "loads": [patch], "support_N": float(r.reaction.sum())}


def back_case(p, n: float | None = None, h: float = 6.0) -> dict:
    Z, M, Ld = p.zaisu, p.material, p.loads
    n = Z.back_check_n if n is None else n
    t = M.t_min
    g = zaisu.back(p)
    half, tm = Z.seat_w / 2, M.t_max
    pads = [box(half, v0, half + tm, v0 + Z.tab_w).intersection(g) if s > 0 else box(-half - tm, v0, -half, v0 + Z.tab_w).intersection(g)
            for s in (-1, 1) for v0 in zaisu.back_tabs(p)]
    pads = [x for x in pads if x.area > 0]
    rail = box(-Z.seat_w / 3, Z.back_h - Z.back_frame, Z.seat_w / 3, Z.back_h).intersection(g)
    m = fea.mesh(g, h, extra=pads)
    q = np.full(m.t.shape[1], 0.0) + fea.pressure(m, rail, n)           # the lean, face-on (weight is in-plane)
    sv = np.where(fea.in_any(m, pads, at="vertices"))[0]
    r = fea.plate(m, t, Ld.E_cross, M.E_par, Ld.G_plate, q, sv)        # spans x across the grain (worst)
    away = _away(m, unary_union(pads), t)
    pk = fea.peaks(fea_swap(r), away, M.f_m, Ld.f_m_cross, Ld.f_v_plate)
    return {"part": "zaisu back", "n": n, "result": r, "local": ~away, "sag_mm": float(r.w.max()),
            "peak": pk, "loads": [rail], "support_N": float(r.reaction.sum())}


def fea_swap(r):
    """A plate result with its stresses relabelled so sx is along the grain (the plates above run their
    grain along y: x spans across it)."""
    from types import SimpleNamespace
    return SimpleNamespace(m=r.m, sx=r.sy, sy=r.sx, txy=r.txy)


def side_zones(p) -> dict:
    """Load and contact edges on a side frame, in its (u = Y, v = Z) plane."""
    Z, M = p.zaisu, p.material
    a = Z.recline
    y0 = zaisu.post_origin(p)
    s0, _ = zaisu.back_s(p)
    sw = fr.slot_w(p)
    slots = []
    for v0 in zaisu.back_tabs(p):                                     # the slot's rear wall, where the back's tab bears
        wall = LineString([(sw / 2, s0 + v0), (sw / 2, s0 + v0 + Z.tab_w)]).buffer(0.6)
        slots.append(translate(rotate(wall, -a, origin=(0, 0)), y0, 0))
    holes = [box(yb - Z.board_tab_w / 2, Z.board_lift - 0.6, yb + Z.board_tab_w / 2, Z.board_lift + 0.6)
             for yb in zaisu.board_tab_ys(p)]
    floor = box(-1, -0.6, Z.runner_len + 1, 0.6)
    return {"slots": slots, "holes": holes, "floor": floor}


def side_case(p, lean: float, seat: float, h: float = 4.0) -> dict:
    """One side frame: half the lean (backwards, at lean_z) through the back's two slots, half the sitter
    through the board's two tab holes; on the floor."""
    Z, M, Ld = p.zaisu, p.material, p.loads
    t = M.t_min
    g = zaisu.side(p)
    zs = side_zones(p)
    a = math.radians(Z.recline)
    s0, _ = zaisu.back_s(p)
    zt = [(s0 + v0 + Z.tab_w / 2) * math.cos(a) for v0 in zaisu.back_tabs(p)]  # the two slots' heights
    F = lean / 2
    lo = F * (zt[1] - Z.lean_z) / (zt[1] - zt[0])                        # lever: share between the slots
    shares = [lo, F - lo]
    trac = [(w, (f, 0.0)) for w, f in zip(zs["slots"], shares) if abs(f) > 1e-9]
    trac += [(hz, (0.0, -seat / 4)) for hz in zs["holes"]]               # 2 tabs a side, 2 sides
    kf = M.E_par * M.t_nominal / p.stiffness.bearing_len
    cs = [fea.Contact("floor", zs["floor"], 1, -1, kf), fea.Contact("floor (grip)", zs["floor"], 0, 1, kf, bilateral=True)]
    m = fea.mesh(g, h, h_edge=h / 2)
    r = fea.plane(m, t, M.E_par, Ld.E_cross, Ld.G_plate, cs, trac)      # grain along the runner: the post is across it
    c = m.p[:, m.t].mean(axis=1)
    loaded = unary_union(zs["slots"] + zs["holes"] + [zs["floor"]]).buffer(3.0)
    local = contains_xy(loaded, c[0], c[1])
    from types import SimpleNamespace
    pk = fea.peaks(SimpleNamespace(sx=r.su, sy=r.sv, txy=r.tuv, m=m), ~local, M.f_m, Ld.f_m_cross, Ld.f_v_plate)
    return {"part": "zaisu side", "lean": lean, "seat": seat, "result": r, "local": local, "peak": pk,
            "forces": {k: round(v, 1) for k, v in r.forces.items() if k != "body"}}


def report(p) -> dict:
    """Every chair case next to zaisu.py's lumped figures (Tsai-Hill use of strength)."""
    Z = p.zaisu
    s, b = seat_case(p), back_case(p)
    f1, f2 = side_case(p, Z.back_check_n, Z.sitter_n), side_case(p, 0.0, Z.seat_check_n)
    pct = lambda x: round(100 * x["peak"]["tsai_hill"])
    return {"seat board, sitter": {"use_%": pct(s), "sag_mm": round(s["sag_mm"], 1),
                                    "lumped_%": round(100 * zaisu.board_stress(p)[0] / p.loads.f_m_cross)},
            "back, lean on the top rail": {"use_%": pct(b), "sag_mm": round(b["sag_mm"], 1),
                                            "lumped_%": round(100 * zaisu.back_stress(p)[0] / p.loads.f_m_cross)},
            "side, flop back with a sitter": {"use_%": pct(f1), "at": f1["peak"]["at"],
                                               "lumped_post_%": round(100 * zaisu.post_stress(p) / p.loads.f_m_cross)},
            "side, heavy sitter": {"use_%": pct(f2), "at": f2["peak"]["at"]}}
