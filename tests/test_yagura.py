"""Yagura variant (frame.style = "yagura"): "+" corner legs under a deck, no aprons.
Every joint must fit across the stock-thickness range, as for the slab frame."""
import pytest
from shapely.geometry import Point, box
from shapely.ops import unary_union

from kotatsu import frame, params, yagura

BASE = params.load()
YT = [t for t in params.tables(BASE) if getattr(t.frame, "style", "slab") == "yagura"]
T_RANGE = (BASE.material.t_min, BASE.material.t_nominal, BASE.material.t_max)
pytestmark = pytest.mark.skipif(not YT, reason="no yagura table in params.toml")


@pytest.fixture(params=YT, ids=[t.table_name for t in YT])
def Y(request):
    P = request.param
    parts = {pt.name: pt for pt in frame.parts(P)}
    return P, frame.layout(P), parts


def empty(shape, rect, tol=0.01):
    return shape.intersection(rect).area <= tol


@pytest.mark.parametrize("t", T_RANGE)
def test_corner_cross_laps(Y, t):
    P, L, parts = Y
    A, B = parts["leg plate A"].shape, parts["leg plate B"].shape
    d, u, zs = yagura.lap_depth(P), P.frame.ear, L.z_deck_bot
    assert zs <= 2 * d <= zs + 2
    assert empty(A, box(u - t / 2, zs - d + 0.01, u + t / 2, zs))     # B's upper half passes A
    assert empty(B, box(u - t / 2, 0, u + t / 2, d - 0.01))           # A's lower half passes B


@pytest.mark.parametrize("t", T_RANGE)
def test_tenons_fit_deck_mortises(Y, t):
    P, L, parts = Y
    dk = parts["deck"].shape
    ta, tb = yagura._tenon_u(P)
    for x0, y0, x1, y1 in yagura.mortises(P):
        xc, yc = (x0 + x1) / 2, (y0 + y1) / 2
        if x1 - x0 > y1 - y0:
            sec = box(xc - (tb - ta) / 2, yc - t / 2, xc + (tb - ta) / 2, yc + t / 2)
            snug = box(x0 - 0.3, yc - t / 2, x0, yc + t / 2)
        else:
            sec = box(xc - t / 2, yc - (tb - ta) / 2, xc + t / 2, yc + (tb - ta) / 2)
            snug = box(xc - t / 2, y0 - 0.3, xc + t / 2, y0)
        assert empty(dk, sec), "tenon must pass through the deck"
        assert not empty(dk, snug), "in-plane fit must be tight"


def test_plates_shoulder_under_the_deck_and_tenons_reach_the_top(Y):
    P, L, parts = Y
    ta, tb = yagura._tenon_u(P)
    zs = L.z_deck_bot
    for name in ("leg plate A", "leg plate B"):
        g = parts[name].shape
        assert g.bounds[3] == pytest.approx(L.H), "tenon tops carry the futon + top"
        assert empty(g, box(-50, zs + 0.5, ta - 5, L.H + 5)) and empty(g, box(tb + 5, zs + 0.5, 400, L.H + 5))
        assert g.intersection(box(ta + 1, zs - 1, tb - 1, L.H - 1)).area > 0.8 * (tb - ta - 2) * (L.H - zs) * 0.6


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
    for name in ("leg wedge", "cheek wedge"):
        pt = parts[name]
        x0, y0, x1, y1 = pt.shape.bounds
        for pl in pt.placements:
            ox, oy, _ = pl.origin
            rects.append(box(ox, oy, ox + t, oy + x1) if pl.axis == "y" else box(ox, oy, ox + x1, oy + t))
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            assert rects[i].distance(rects[j]) > 2, (i, j)


def test_deck_inside_round_top(Y):
    P, L, parts = Y
    if getattr(P.top, "shape", "rect") != "round":
        pytest.skip("rectangular top")
    dk = parts["deck"].shape
    far = max(Point(L.cx, L.cy).distance(Point(x, y)) for x, y in dk.exterior.coords)
    assert far <= P.top.length / 2 - P.yagura.deck_inset + 0.5
