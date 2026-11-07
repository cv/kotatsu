"""The zaisu (floor chairs): cuttable parts, hook joints that go in and lock across the plywood thickness
range, seat-board tabs that hold the side frames down, no tipping under a hard lean, and an order (table +
chairs) that still ships free."""
import math

import pytest
from shapely.affinity import rotate, translate
from shapely.geometry import Point, box

from kotatsu import comfort, frame as fr, geom, optimize, params, price, zaisu

P = params.tables(params.load())[0]
Z = P.zaisu
R = P.cnc.bit_d / 2
T_RANGE = (P.material.t_min, P.material.t_nominal, P.material.t_max)
SIDE = zaisu.side(P)
HALF = Z.seat_w / 2


def _hole_at(g, x, y):
    for h in g.interiors:
        from shapely.geometry import Polygon
        hp = Polygon(h)
        if hp.contains(Point(x, y)):
            return hp
    raise AssertionError(f"no hole at {(x, y)}")


def test_parts_cuttable():
    names = [pt.name for pt in zaisu.parts(P)]
    assert names == ["zaisu side", "zaisu seat board", "zaisu stretcher", "zaisu back"]
    for pt in zaisu.parts(P):
        g = pt.shape
        assert g.geom_type == "Polygon" and g.is_valid, pt.name
        assert geom.router_cuttable(g, R), pt.name
        assert max(g.bounds[2] - g.bounds[0], g.bounds[3] - g.bounds[1]) + 50 <= P.shipping.box_max, pt.name
    q = {pt.name: pt.qty for pt in zaisu.parts(P)}
    n = int(Z.count)
    assert q == {"zaisu side": 2 * n, "zaisu seat board": n, "zaisu stretcher": n, "zaisu back": n}


def _span(hole):
    """The slot's own rectangle (x0, y0, x1, y1), measured through its middle (the bounds include dogbones)."""
    from shapely.geometry import LineString
    cx, cy = hole.centroid.x, hole.centroid.y
    a, _, b, _ = hole.intersection(LineString([(cx - 1e3, cy), (cx + 1e3, cy)])).bounds
    _, c, _, d = hole.intersection(LineString([(cx, cy - 1e3), (cx, cy + 1e3)])).bounds
    return a, c, b, d


def _check_hook(part, hole, v_off, t):
    """part in (u = X, v); hole in (n across the side frame's plane, s along the slot), the slot's s measured
    on the part's v axis + v_off. Installed: the part's section through the side frame (X in [HALF, HALF+t])
    sits in the hole; raised by hook_drop it still does (it went in that way); its finger, past the thickest
    side frame, hangs below the hole's bottom (locked)."""
    _, s0, _, s1 = _span(hole)
    sec = part.intersection(box(HALF, -1e4, HALF + t, 1e4))
    lo, hi = sec.bounds[1] + v_off, sec.bounds[3] + v_off
    assert lo >= s0 - 1e-6 and hi + Z.hook_drop <= s1 + 1e-6, (lo, hi, s0, s1)
    fin = part.intersection(box(HALF + P.material.t_max + 0.5, -1e4, 1e4, 1e4))
    assert fin.bounds[1] + v_off <= s0 - Z.hook_drop + 0.5        # the finger reaches hook_drop below the slot
    assert fin.bounds[0] >= HALF + P.material.t_max                # ... and clears the thickest side frame


@pytest.mark.parametrize("t", T_RANGE)
def test_stretcher_hooks(t):
    ys, zt = zaisu.stretcher_y(P), zaisu.stretcher_tab_z(P)
    hole = _hole_at(SIDE, ys + t / 2, zt + 1)
    x0, _, x1, _ = _span(hole)
    assert x0 <= ys + 1e-6 and ys + t <= x1 - 1e-6                 # the stretcher's thickness fits
    _check_hook(zaisu.stretcher(P), hole, 0.0, t)


@pytest.mark.parametrize("t", T_RANGE)
def test_back_hooks(t):
    y0 = zaisu.post_origin(P)
    upright = rotate(translate(SIDE, -y0, 0), Z.recline, origin=(0, 0))   # the post (and its slots) vertical
    s0, _ = zaisu.back_s(P)
    for v0 in zaisu.back_tabs(P):
        hole = _hole_at(upright, 0, s0 + v0 + 1)
        n0, _, n1, _ = _span(hole)
        assert n0 <= -t / 2 + 1e-6 and t / 2 <= n1 - 1e-6        # the panel is centred on the post's slots
        tab = zaisu.back(P).intersection(box(-1e4, v0 - Z.hook_drop - 1, 1e4, v0 + Z.tab_w + 1))
        _check_hook(tab, hole, s0, t)


def test_board_tabs_hold_the_runners_down():
    ys = zaisu.board_tab_ys(P)
    for yb in ys:
        hole = _hole_at(SIDE, yb, Z.board_lift + 1)
        y0, z0, y1, z1 = _span(hole)
        assert hole.bounds[1] >= P.material.t_nominal - 1e-6        # wood under the hole (dogbones too): >= the sheet
        assert z1 - z0 >= P.material.t_max                          # the thickest board fits
        assert y0 <= yb - Z.board_tab_w / 2 and yb + Z.board_tab_w / 2 <= y1
    b = zaisu.board(P)                                              # the tabs reach through the thickest side frame
    assert b.bounds[2] >= HALF + P.material.t_max + Z.board_tab_out
    assert ys[0] < Z.front_gap + Z.seat_d / 2 < ys[1]               # one tab pair in front of the sitter, one behind


def test_no_tipping_back():
    assert zaisu.tipping_n(P) >= 1.5 * Z.lean_n


F = P.loads.f_m_cross          # the weaker way round: the nester may turn a part either way


def test_post_strength():
    assert zaisu.post_stress(P) <= 0.4 * F                  # a flop back, root and through the lower slot


def test_back_panel_strength():
    stress, sag = zaisu.back_stress(P)
    assert stress <= 0.5 * F and sag <= 6.0


def test_seat_board_strength():
    stress, sag = zaisu.board_stress(P)
    assert stress <= 0.5 * F
    assert sag < Z.board_lift - 5                           # it stays off the floor


def test_wood_beside_the_post_slots():
    """Shop rule: no wood narrower than the sheet. The post's edges vs each back slot (dogbones too)."""
    from shapely.geometry import Polygon
    y0 = zaisu.post_origin(P)
    upright = rotate(translate(SIDE, -y0, 0), Z.recline, origin=(0, 0))
    s0, _ = zaisu.back_s(P)
    edges = [box(-Z.post_w / 2 - 50, 0, -Z.post_w / 2, 2000), box(Z.post_w / 2, 0, Z.post_w / 2 + 50, 2000)]
    for v0 in zaisu.back_tabs(P):
        hole = _hole_at(upright, 0, s0 + v0 + 1)
        assert min(hole.distance(e) for e in edges) >= P.material.t_nominal - 1e-6
        assert zaisu.post_end(P) - hole.bounds[3] >= P.material.t_nominal      # and above the top slot


def test_chairs_beside_the_table():
    L = fr.layout(P)
    for pt in zaisu.parts(P):
        for pl in pt.placements:
            M = pl.matrix
            for (u, v) in list(pt.shape.exterior.coords)[::5]:
                x, y = M[0] * u + M[1] * v + M[3], M[4] * u + M[5] * v + M[7]
                assert max(abs(x - L.cx), abs(y - L.cy)) > L.Lf / 2 + 50      # clear of the frame
            assert M[11] >= -1e-6 and (M[8] * 0 + M[9] * 0 + M[11]) < 1000


def test_order_ships_free():
    rho = P.material.density_kg_m3 * P.material.t_nominal / 1e9
    kg = sum(g.area * rho * q for _, g, q in price.parts(P))        # the table and the chairs, one box
    assert kg * optimize.UMAKE_KG <= P.shipping.free_kg - 0.3       # a little margin for the real sheet


def test_legs_forward_fit():
    """On a zaisu the owner sits legs forward (2026-11): thighs under the deck, feet under the heater."""
    room = comfort.legs_forward(P, zaisu.seat_top(P) + Z.cushion_squashed)
    assert room["thigh_room"] >= 0 and room["feet_room"] >= 0
    assert Z.cushion_squashed <= zaisu.cushion_max(P)


def test_cross_legged_knees_need_room_under_the_top():
    """Knees higher than the frame's top can't come in under the top's edge (the futon is squeezed there)."""
    L = fr.layout(P)
    assert comfort.knee_reach(P, height=L.H + 1) == 0.0
    assert comfort.knee_reach(P) >= P.comfort.knee_reach_min          # the bare-floor posture still fits


@pytest.mark.parametrize("name", ["zaisu side", "zaisu seat board", "zaisu stretcher", "zaisu back"])
def test_wood_round_every_hole(name):
    """Shop rule: no feature thinner than the sheet. Every slot and cut-out keeps that much wood to the
    part's edge (dogbones and squircle corners included)."""
    from shapely.geometry import Polygon
    g = {pt.name: pt.shape for pt in zaisu.parts(P)}[name]
    for h in g.interiors:
        assert Polygon(g.exterior).exterior.distance(Polygon(h)) >= P.material.t_nominal - 1e-6, (name, Polygon(h).bounds)
