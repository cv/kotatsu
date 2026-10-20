"""Yagura frame: "+" corner legs under a deck, no aprons. Every joint must fit across the
stock-thickness range."""
import pytest
from shapely.affinity import translate
from shapely.geometry import Point, Polygon, box
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
        pu = yagura.post_u(P)
        assert empty(g, box(pu + 5, zs + 0.5, ta - 5, L.H + 5)) and empty(g, box(tb + 5, zs + 0.5, 400, L.H + 5))
        if pu:
            assert g.intersection(box(1, L.H - 2, pu - 1, L.H)).area > 0.9 * (pu - 2) * 2, "corner post reaches the top"
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


def test_quantities(Y):
    P, L, parts = Y
    q = {n: pt.qty for n, pt in parts.items()}
    assert q["leg plate A"] == 4 and q["leg plate B"] == 4 and q["deck"] == 1 and q["heater cheek"] == 2
    assert q["leg wedge"] >= 8 and q["cheek wedge"] >= 4


def test_legs_are_straight(Y):
    """Plumb plates: as wide at the floor as under the deck."""
    P, L, parts = Y
    for name in ("leg plate A", "leg plate B"):
        g = parts[name].shape
        lo = g.intersection(box(-50, 10, 400, 11)).bounds       # above the corner rounding
        hi = g.intersection(box(-50, L.z_deck_bot - 20, 400, L.z_deck_bot - 19)).bounds
        assert lo[0] == pytest.approx(hi[0], abs=0.5) and lo[2] == pytest.approx(hi[2], abs=0.5)


def test_corner_posts_clear_the_deck(Y):
    """The posts (ear arms) rise past the deck: the deck's corner cut-outs must clear them for any stock."""
    from kotatsu import comfort
    P, L, parts = Y
    if not yagura.post_u(P):
        pytest.skip("no corner posts")
    above = comfort.low_footprint(P, L.H, L.z_deck_bot + 0.5)          # frame material beside the deck
    d = translate(parts["deck"].shape, -L.cx, -L.cy)
    tenons = unary_union([translate(box(*m), -L.cx, -L.cy) for m in yagura.mortises(P)])
    assert d.intersection(above.difference(tenons.buffer(0.01))).area < 1e-6
    assert d.is_valid and d.geom_type == "Polygon"


def test_posts_carry_the_top_further_out(Y):
    from kotatsu import comfort
    P = Y[0]
    with_posts = comfort.top_lift(P)[0]
    P2 = params.tables(params.load())[0]
    P2.yagura.corner_posts = False
    assert with_posts > 1.5 * comfort.top_lift(P2)[0]


def test_deck_windows_clear_everything(Y):
    """Lightening windows: window_margin from every hole, slot, wedge, cheek and the heater; window_bar
    from the deck's outer edge; the deck stays one piece."""
    P, L, parts = Y
    wins = yagura.windows(P)
    if not wins:
        pytest.skip("no deck windows")
    d = parts["deck"].shape
    assert d.geom_type == "Polygon"
    t = P.material.t_max
    keep = [box(*m) for m in yagura.mortises(P)]
    for xi, s in zip(frame.cheek_xs(P), (-1, 1)):                       # cheeks (plan) + their tab slots
        xa, xb = sorted((xi, xi + s * t))
        keep.append(box(xa, L.cy - P.cheek.length / 2, xb, L.cy + P.cheek.length / 2))
    (sx, sy, _), (hx, hy, _) = frame.heater_box(P)
    keep.append(box(hx - sx / 2, hy - sy / 2, hx + sx / 2, hy + sy / 2))
    for pt in frame.parts(P):                                           # wedges lying on the deck
        if pt.kind != "wedge":
            continue
        w0, _, w1, _ = pt.shape.bounds
        for pl in pt.placements:
            ox, oy, _ = pl.origin
            keep.append(box(ox, oy, ox + w1 - w0, oy + t) if pl.axis == "x" else box(ox, oy, ox + t, oy + w1 - w0))
    keep = unary_union(keep)
    outer = Polygon(d.exterior)
    for w in wins:
        assert w.distance(keep) >= P.deck.window_margin - 1e-6
        assert outer.exterior.distance(w) >= P.deck.window_bar - 1e-6
    for a in wins:
        for b in wins:
            if a is not b:
                assert a.distance(b) >= P.deck.window_bar - 1e-6
        assert d.intersection(w).area < 1e-6


def test_leg_windows_leave_enough_wood(Y):
    """Leg windows keep >= stock thickness of wood around them and never touch the slot, tenon or hole."""
    P, L, parts = Y
    lw = yagura.leg_window(P)
    if lw is None:
        pytest.skip("no leg windows")
    t = P.material.t_max
    for name in ("leg plate A", "leg plate B"):
        g = parts[name].shape
        assert g.geom_type == "Polygon" and len(g.interiors) == 2          # wedge hole + window
        x0, z0, x1, z1 = lw.bounds
        assert x0 - (P.frame.ear + frame.slot_w(P) / 2) >= t - 0.5          # wood beside the cross-lap slot
        assert P.frame.leg_width - x1 >= t - 0.5                            # wood at the inner edge
        assert z0 >= 40 and L.z_deck_bot - z1 >= 40
