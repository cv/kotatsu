"""Yagura frame: diagonal legs under an X deck, no aprons (the leg joints themselves: tests/test_diagonal.py).
Every joint must fit across the stock-thickness range."""
import numpy as np
import pytest
from shapely.affinity import translate
from shapely.geometry import Point, box
from shapely.ops import unary_union

from kotatsu import frame, params, yagura

BASE = params.load()
YT = params.tables(BASE)
T_RANGE = (BASE.material.t_min, BASE.material.t_nominal, BASE.material.t_max)


@pytest.fixture(params=YT, ids=[t.table_name for t in YT])
def Y(request):
    P = request.param
    parts = {pt.name: pt for pt in frame.parts(P)}
    return P, frame.layout(P), parts


def empty(shape, rect, tol=0.01):
    return shape.intersection(rect).area <= tol


@pytest.mark.parametrize("t_deck", T_RANGE)
def test_leg_wedges_clamp_the_deck(Y, t_deck):
    P, L, parts = Y
    z0, z1 = yagura.leg_hole_z(P)
    top = L.z_deck_bot + t_deck
    assert z0 < top
    wl, wh = yagura.wedge_dims(P, "leg")
    need = z1 - top
    assert wh - wl * P.fit.wedge_taper < need < wh
    assert L.z_deck_top + wh <= L.H - 3, "wedges stay under the futon plane"
    ta, tb = yagura._tenon_u(P)
    assert (tb - ta) - frame.thick_slot(P) >= 2 * 15, "wood beside the wedge hole"
    assert L.H - z1 >= 10, "wood above the wedge hole"


def test_wedges_do_not_collide(Y):
    P, L, parts = Y
    t = P.material.t_max
    rects = []
    for name in [n for n in ("leg wedge", "cheek wedge", "wedge") if n in parts]:
        pt = parts[name]
        x0, y0, x1, y1 = pt.shape.bounds
        for pl in pt.placements:
            ox, oy, _ = pl.origin
            rects.append(box(ox, oy, ox + t, oy + x1) if pl.axis == "y" else box(ox, oy, ox + x1, oy + t))
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            assert rects[i].distance(rects[j]) > 2, (i, j)


def _haunch_bottom(P):
    Y = P.yagura
    return Y.leg_haunch_top - Y.leg_haunch_drop - Y.leg_haunch_r


def lap_depth_a(P):
    from kotatsu import yagura
    return yagura.lap_depth(P)


def test_posts_carry_the_top_further_out(Y):
    from kotatsu import comfort
    P = Y[0]
    with_posts = comfort.top_lift(P)[0]
    P2 = params.tables(params.load())[0]
    P2.yagura.corner_posts = False
    assert with_posts > 1.5 * comfort.top_lift(P2)[0]


def test_x_deck_arms_carry_a_hand(Y):
    """A hand pressing on the heater ring (deck.hand_n) plus the heater, on the four arms as cantilevers at
    45 deg to the grain, thinnest stock: under half the rough strength, a few mm of give."""
    from kotatsu import loads
    P, L, parts = Y
    a = loads.deck_arms(P)
    assert a["free_mm"] > 0 and a["use_of_strength_%"] < 50 and a["sag_mm"] < 5


def test_storage_layout_fits(Y):
    """Off-season: every part packs flat inside the top's footprint in 3 layers, nothing touching."""
    from kotatsu import storage
    assert storage.check(Y[0]) == []
    assert len(storage.layout(Y[0])) == 3 and storage.stack_mm(Y[0]) < 50



