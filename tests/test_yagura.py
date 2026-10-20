"""Yagura frame: "+" corner legs under a deck, no aprons. Every joint must fit across the
stock-thickness range."""
import numpy as np
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
    w = frame.slot_w(P)
    ribs_A = yagura.crush_ribs(P, u - w / 2, u + w / 2, zs - d, zs)     # the bumps are meant to squeeze / be sanded
    ribs_B = yagura.crush_ribs(P, u - w / 2, u + w / 2, 0, d)
    assert empty(A.difference(ribs_A), box(u - t / 2, zs - d + 0.01, u + t / 2, zs))     # B's upper half passes A
    assert empty(B.difference(ribs_B), box(u - t / 2, 0, u + t / 2, d - 0.01))           # A's lower half passes B
    if t <= w - 2 * getattr(P.fit, "crush_rib", 0.0):                   # stock up to the rib gap: no squeeze at all
        assert empty(A, box(u - t / 2, zs - d + 0.01, u + t / 2, zs)) and empty(B, box(u - t / 2, 0, u + t / 2, d - 0.01))


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
    for name in [n for n in ("leg wedge", "cheek wedge", "wedge") if n in parts]:
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
    if "wedge" in q:
        assert q["wedge"] >= 12
    else:
        assert q["leg wedge"] >= 8 and q["cheek wedge"] >= 4


def _haunch_bottom(P):
    Y = P.yagura
    if getattr(Y, "leg_haunch_style", "straight") == "curve":
        return Y.leg_haunch_top - Y.leg_haunch_curve_drop
    return Y.leg_haunch_top - Y.leg_haunch_drop - Y.leg_haunch_r


def test_legs_are_straight(Y):
    """Plumb plates: the outer edge is straight; below the haunch the inner edge is too (leg_narrow wide),
    and the plate is full width just under the deck (shoulders + tenon). Plate A's feet may taper
    (yagura.foot_taper) over the bottom foot_taper_from mm; above that it's plumb too."""
    P, L, parts = Y
    wn = getattr(P.yagura, "leg_narrow", 0.0) or P.frame.leg_width
    ft = getattr(P.yagura, "foot_taper", 0.0)
    for name in ("leg plate A", "leg plate B"):
        g = parts[name].shape
        z_hi = _haunch_bottom(P) - 2 if getattr(P.yagura, "leg_narrow", 0) else L.z_deck_bot - 20
        zs = [z_hi] + [z for z in (10, 100) if not (name == "leg plate A" and ft and z < P.yagura.foot_taper_from)]
        if name == "leg plate A" and ft:
            zs.append(P.yagura.foot_taper_from + 2)
        for z in zs:
            b = g.intersection(box(-50, z, 400, z + 1)).bounds
            assert b[0] == pytest.approx(0, abs=0.5) and b[2] == pytest.approx(wn, abs=0.5), (name, z, b)
        hi = g.intersection(box(-50, L.z_deck_bot - 12, 400, L.z_deck_bot - 11)).bounds
        assert hi[2] == pytest.approx(P.frame.leg_width, abs=0.5)


def test_tapered_feet(Y):
    """Plate A's foot is leg_narrow - 2 x foot_taper wide at the floor, the taper stays clear of A's
    cross-lap slot (its fingers keep full width), and plate B never tapers (its floor slot needs both fingers)."""
    P, L, parts = Y
    ft = getattr(P.yagura, "foot_taper", 0.0)
    if not ft:
        pytest.skip("plumb feet")
    wn = getattr(P.yagura, "leg_narrow", 0.0) or P.frame.leg_width
    A, B = parts["leg plate A"].shape, parts["leg plate B"].shape
    b = A.intersection(box(-50, 8, 400, 9)).bounds
    assert b[2] - b[0] == pytest.approx(wn - 2 * ft * (1 - 8.5 / P.yagura.foot_taper_from), abs=1.0)
    assert P.yagura.foot_taper_from <= L.z_deck_bot - lap_depth_a(P) + 1e-6   # below A's slot bottom
    assert B.intersection(box(-50, 8, 400, 9)).bounds[2] == pytest.approx(wn, abs=0.5)


def lap_depth_a(P):
    from kotatsu import yagura
    return yagura.lap_depth(P)


def test_haunched_leg_fingers(Y):
    """Beside the cross-lap slot the narrow leg keeps at least the stock thickness of wood."""
    P = Y[0]
    wn = getattr(P.yagura, "leg_narrow", 0.0)
    if not wn:
        pytest.skip("straight full-width legs")
    assert wn - (P.frame.ear + frame.slot_w(P) / 2) >= P.material.t_max - 0.5
    assert P.yagura.leg_haunch_top < frame.layout(P).z_deck_bot - 10


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
    notch = getattr(P.deck, "window_style", "hole") == "notch"
    for w in wins:
        assert w.distance(keep) >= P.deck.window_margin - 1e-6
        if not notch:
            assert outer.exterior.distance(w) >= P.deck.window_bar - 1e-6
    tongues = unary_union(yagura.link_tongues(P)).buffer(getattr(getattr(P, "link", None), "root_r", 0) + 1)
    for a in wins:
        for b in wins:
            if a is not b:
                assert a.distance(b) >= (P.deck.neck if notch else P.deck.window_bar) - 1e-6
        assert d.intersection(a).difference(tongues).area < 1e-6     # open, except the link tongues


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


def test_crush_ribs_narrow_the_slots(Y):
    """Each cross-lap slot has bumps on both walls: the gap there is slot_w - 2 x crush_rib; elsewhere the
    full slot width (so a thick sheet still goes in after a little sanding)."""
    P, L, parts = Y
    h = getattr(P.fit, "crush_rib", 0.0)
    if not h:
        pytest.skip("no crush ribs")
    w, u = frame.slot_w(P), P.frame.ear
    d = yagura.lap_depth(P)
    for name, (z0, z1) in (("leg plate A", (L.z_deck_bot - d, L.z_deck_bot)), ("leg plate B", (0.0, d))):
        g = parts[name].shape
        gaps = []
        for f in np.linspace(0.05, 0.95, 181):
            z = z0 + f * (z1 - z0)
            cut = box(u - w, z - 0.05, u + w, z + 0.05).difference(g)
            seg = [c for c in getattr(cut, "geoms", [cut]) if c.bounds[0] < u < c.bounds[2]]
            gaps.append(seg[0].bounds[2] - seg[0].bounds[0])
        assert min(gaps) == pytest.approx(w - 2 * h, abs=0.05)
        assert max(gaps) == pytest.approx(w, abs=0.05)
        assert min(gaps) >= P.material.t_min, "even the thinnest sheet is gripped, never jammed shut"


def test_foot_relief(Y):
    """Plate A stands on its two ends; the middle of its foot is lifted by foot_relief."""
    P, L, parts = Y
    sag = getattr(P.yagura, "foot_relief", 0.0)
    if not sag:
        pytest.skip("no foot relief")
    g = parts["leg plate A"].shape
    touch = g.intersection(box(-1, -1, 500, 0.2))
    assert len(getattr(touch, "geoms", [touch])) == 2
    wn = P.yagura.leg_narrow
    mid = g.intersection(box(wn / 2 - 1, -1, wn / 2 + 1, sag + 2)).bounds
    assert mid[1] == pytest.approx(sag, abs=0.1)


def test_storage_layout_fits(Y):
    """Off-season: every part packs into three flat layers inside the top's footprint, nothing touching."""
    from kotatsu import storage
    assert storage.check(Y[0]) == []


def test_deck_notch_mouths_rounded_but_leg_side_square():
    """Owner 2026-10-20: the 8 notch-mouth corners are rounded; enough wood stays beside the mortises,
    and the corner pads around the legs keep their shape (wedge bearing unchanged)."""
    from shapely.geometry import Point, box
    P = params.tables(params.load())[0]
    rr = P.deck.mouth_r
    assert rr > 0
    deck = [pt for pt in frame.parts(P) if pt.name == "deck"][0].shape
    pts = yagura.mouth_corners(P)
    assert len(pts) == 8
    for x, y, dx, dy in pts:
        assert not deck.contains(Point(x + dx * 0.2 * rr, y + dy * 0.2 * rr))      # corner wood removed
        assert deck.contains(Point(x + dx * 0.4 * rr, y + dy * 0.4 * rr))          # just inside the arc: wood
    holes = [box(*m) for m in yagura.mortises(P)]
    assert min(c.distance(h) for c in yagura.mouth_cutters(P) for h in holes) >= 15.0
    P0 = params.tables(params.load())[0]
    P0.deck.mouth_r = 0.0
    sq = [pt for pt in frame.parts(P0) if pt.name == "deck"][0].shape
    lost = sq.difference(deck)
    for m in yagura.mortises(P):                                                  # nothing lost near the legs
        assert lost.distance(box(*m)) >= 15.0


def test_link_key_fits_two_modules_side_by_side():
    """Owner 2026-10-20 (linkable set): with two modules side by side, tops touching, the key's tabs drop
    into the facing slots with only the in-plane clearance; the key stays under the futon plane, keeps
    clear of everything else on the deck, and the slots keep their edge wood."""
    from shapely.affinity import translate
    P = params.tables(params.load())[0]
    if not yagura.linking(P):
        pytest.skip("linking off")
    K, L, c = P.link, frame.layout(P), P.fit.tight
    parts = {pt.name: pt for pt in frame.parts(P)}
    assert parts["link key"].qty >= 1
    slots = yagura.link_slots(P)
    assert len(slots) == 4
    pitch = yagura.link_pitch(P)
    assert abs(pitch - P.top.length) < 1e-6                              # the tops touch
    a = max(slots, key=lambda s: s[2])                                   # module A's +x slot
    b = min(slots, key=lambda s: s[0])                                   # module B's -x slot, shifted
    b = (b[0] + pitch, b[1], b[2] + pitch, b[3])
    x0 = a[0] + c                                                        # key placed with its first tab in A
    n = yagura.key_length(P)
    assert abs((x0 + n - K.tab_len) - (b[0] + c)) < 1e-6 and abs((x0 + n) - (b[2] - c)) < 1e-6
    key = parts["link key"].shape
    assert key.bounds[3] - L.t + L.z_deck_top <= L.H - 4                 # key top under the futon plane
    deck = parts["deck"].shape
    h = L.Lf / 2
    for s in slots:                                                      # edge wood outside each slot
        xs0, ys0, xs1, ys1 = s
        edge = min(L.cx + h - xs1, xs0 - (L.cx - h), L.cy + h - ys1, ys0 - (L.cy - h))
        assert edge >= K.edge - c - 1e-6
        r = box(*s).buffer(K.edge * 0.6)
        assert deck.buffer(0.01).contains(r.difference(box(*s).buffer(5)).intersection(box(L.cx - h, L.cy - h, L.cx + h, L.cy + h)))
    # nothing else lies on the deck where the key goes (wedges, cheek tabs, tenons)
    kx = box(x0, L.cy - L.t / 2, x0 + n, L.cy + L.t / 2)
    for pt in parts.values():
        if pt.kind == "wedge":
            w0, _, w1, _ = pt.shape.bounds
            for pl in pt.placements:
                ox, oy, _ = pl.origin
                f = box(ox, oy, ox + w1 - w0, oy + L.t) if pl.axis == "x" else box(ox, oy, ox + L.t, oy + w1 - w0)
                assert f.distance(kx) >= 10
    for m in yagura.mortises(P):
        assert box(*m).distance(kx) >= 10
