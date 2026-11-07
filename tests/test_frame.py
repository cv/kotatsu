"""Frame-wide checks: every part cuttable and shippable, the cheeks fit across the plywood thickness
tolerance, and the kotatsu is comfortable (knee zone, heater clearance) and safe (futon plane, tipping).
Leg/deck joints: tests/test_yagura.py."""
import pytest
from shapely.geometry import box

from kotatsu import frame, geom, params

from types import SimpleNamespace

BASE = params.load()
TABLES = params.tables(BASE)
R = BASE.cnc.bit_d / 2
T_RANGE = (BASE.material.t_min, BASE.material.t_nominal, BASE.material.t_max)


@pytest.fixture(params=TABLES, ids=[t.table_name for t in TABLES])
def C(request):
    P = request.param
    return SimpleNamespace(P=P, L=frame.layout(P), PARTS={pt.name: pt for pt in frame.parts(P)})


def clear(part_shape, rect, tol=0.01):
    """rect (cross-section of a mating part) lies entirely in empty space of part_shape."""
    return part_shape.intersection(rect).area <= tol


def test_part_valid_cuttable(C):
    for name, pt in C.PARTS.items():
        g = pt.shape
        assert g.is_valid and g.geom_type == "Polygon"
        assert geom.router_cuttable(g, R), f"{name}: inside corner tighter than the bit"


def test_part_fits_sheet_and_parcel(C):
    P = C.P
    for name, pt in C.PARTS.items():
        _fits(P, pt.shape)


def _fits(P, shape):
    x0, y0, x1, y1 = shape.bounds
    long_side = max(x1 - x0, y1 - y0)
    assert long_side + 50 <= P.shipping.box_max                  # boxed, still ships free
    w, h = sorted((x1 - x0, y1 - y0))
    assert any(w <= min(s) - 2 * P.cnc.sheet_margin and h <= max(s) - 2 * P.cnc.sheet_margin
               for s in P.cnc.sheets)


# ------------------------------------------------------------------ cross-laps
def test_crossings_agree(C):
    """Slot positions in each panel coincide with the other panel's centre plane."""
    P, L = C.P, C.L
    assert L.xS[0] - L.O == pytest.approx(P.frame.ear) and L.Lf - (L.xS[1] - L.O) == pytest.approx(P.frame.ear)
    assert L.yL[0] - L.O == pytest.approx(P.frame.ear) and L.Wf - (L.yL[1] - L.O) == pytest.approx(P.frame.ear)


# ------------------------------------------------------------------ heater cradle (cheeks in the deck well)
@pytest.mark.parametrize("t", T_RANGE)
def test_cradle_drops_into_the_well(C, t):
    """Both cheek bodies pass the deck's well at any stock thickness, with the heater between them."""
    P, L, dk = C.P, C.L, C.PARTS["deck"].shape
    (_, w0, _, w1) = frame.well(P)
    for xi, s in zip(frame.cheek_xs(P), (-1, 1)):
        xa, xb = sorted((xi, xi + s * t))
        assert clear(dk, box(xa, w0 + P.fit.tight, xb, w1 - P.fit.tight)), "cheek body passes the well"
    (sx, sy, _), (hx, hy, _) = frame.heater_box(P)
    assert clear(dk, box(hx - sx / 2, hy - sy / 2, hx + sx / 2, hy + sy / 2)), "heater passes the well"


@pytest.mark.parametrize("t", T_RANGE)
def test_cradle_ears_rest_on_the_deck(C, t):
    """Gravity holds the cradle: each ear's flat underside sits on solid deck, ear_len long (any stock)."""
    P, L, dk = C.P, C.L, C.PARTS["deck"].shape
    ck, y0 = frame.cheek(P)
    zb, _ = frame.cheek_z(P)
    (_, w0, _, w1), (c0, c1) = frame.well(P), frame.cheek_ys(P)
    v = L.z_deck_top - zb
    for u0, u1 in ((c0 - y0 + 8, w0 - y0 - 6), (w1 - y0 + 6, c1 - y0 - 8)):    # ear, clear of the rounded ends
        assert ck.intersection(box(u0, v - 1.0, u1, v - 0.2)).area < 1e-6, "nothing below the ear"
        assert ck.intersection(box(u0, v + 0.2, u1, v + 1.0)).area > 0.99 * 0.8 * (u1 - u0), "ear underside"
    for xi, s in zip(frame.cheek_xs(P), (-1, 1)):
        xa, xb = sorted((xi, xi + s * t))
        for ya, yb in ((c0, w0), (w1, c1)):
            ear = box(xa, ya, xb, yb)
            assert dk.intersection(ear).area > 0.85 * ear.area, "deck under the ear"
    assert w0 - c0 >= P.cheek.ear_len and c1 - w1 >= P.cheek.ear_len


def test_cradle_stays_below_futon_plane(C):
    P, L = C.P, C.L
    zb, zt = frame.cheek_z(P)
    ck, _ = frame.cheek(P)
    assert zb + ck.bounds[3] == pytest.approx(zt) and zt <= L.H - 5
    assert L.z_deck_top + P.yagura.wedge_head <= L.H - 3


def test_cheeks_hug_the_heater(C):
    P = C.P
    a, b = frame.cheek_xs(P)
    assert b - a == pytest.approx(P.heater.body_x + P.heater.cheek_clearance)
    c0, c1 = frame.cheek_ys(P)
    assert c1 - c0 >= P.heater.body_y + 40
    (_, _, sz), (_, _, hz) = frame.heater_box(P)
    zb, zt = frame.cheek_z(P)
    assert zb <= hz - sz / 2 + 0.01 and zt >= hz + sz / 2, "the cheeks cover the heater's whole side"


# ------------------------------------------------------------------ comfort & safety
def test_total_height_in_owner_range(C):
    P = C.P
    total = P.frame.height + P.material.t_nominal + 10      # ~10 mm compressed futon
    assert 390 <= total <= 415                               # owner OK'd ~41 cm for the leg room


def test_ear_fingers_are_sturdy(C):
    """Ear fingers outside the cross-lap slots: at least the stock thickness (uMake's minimum feature).
    In the yagura they're braced by the crossing plate in the slot (owner chose 20.4 mm, = inner finger)."""
    P = C.P
    assert P.frame.ear - frame.slot_w(P) / 2 >= P.material.t_max


def test_cross_legged_clearance(C):
    """Owner's cross-legged knees (30" x 12.5"): the aprons clear them, and the knee zone can come
    knee_reach_min in under the top's edge at every side without touching a leg or the heater."""
    from kotatsu import comfort
    P = C.P
    K = P.comfort
    assert comfort.summary(P)["apron_clear"] >= K.knee_h + 5
    assert comfort.knee_reach(P) >= K.knee_reach_min


def test_does_not_tip_easily(C):
    """Tipping load at the EN 12521 / EN 1730 loading point (mid-side, tip_inset in from the edge).
    No pass/fail limit until tip_min_n comes from the standard's table or a real test (0 = report only)."""
    from kotatsu import comfort
    P = C.P
    edge, std = comfort.tip_load(P, 0.0), comfort.tip_load(P)
    assert 0 < edge < std, "pushing further in must take more force"
    if P.comfort.tip_min_n > 0:
        assert std >= P.comfort.tip_min_n


def test_heater_leaves_shin_room(C):
    P, L = C.P, C.L
    (sx, sy, sz), (cx, cy, cz) = frame.heater_box(P)
    assert cz - sz / 2 >= 300, "shins under the heater (v2: it rides in the deck, 309 mm up)"
    assert frame.cheek_z(P)[0] >= cz - sz / 2 - 0.01, "cheeks must not hang below the heater"
