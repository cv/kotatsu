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
    assert long_side + P.shipping.packing <= P.shipping.box_max  # boxed, still ships free
    w, h = sorted((x1 - x0, y1 - y0))
    assert any(w <= min(s) - 2 * P.cnc.sheet_margin and h <= max(s) - 2 * P.cnc.sheet_margin
               for s in P.cnc.sheets)


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
    assert zb + ck.bounds[3] == pytest.approx(zt)
    assert zt + (P.material.t_max - P.material.t_nominal) <= L.H - 1, "a thick deck lifts the cheeks: never proud of the tenons"
    assert L.z_deck_top + P.yagura.wedge_head <= L.H - 3


def test_cheeks_hold_the_heater_by_its_screws(C):
    """The cheeks hug the heater's sides (cheek_clearance), reach below_screw under its screw line (screw_from_top
    below its top) and rise above its top; their bottom stays under the deck's underside (they locate in the well).
    The heater's control panel, on one end, stays panel_clear under the deck's underside, so the knob and the plug
    stick out under the deck's ring, not into the well's end wall (owner 2026-11)."""
    P, L = C.P, C.L
    h, ch = P.heater, P.cheek
    (sx, sy, sz), (_, _, hz) = frame.heater_box(P)
    zb, zt = frame.cheek_z(P)
    top, bottom = hz + sz / 2, hz - sz / 2
    x0, x1 = frame.cheek_xs(P)
    assert x1 - x0 - sx == pytest.approx(h.cheek_clearance)
    assert zb <= top - h.screw_from_top - ch.below_screw + 1e-6 and zt > top
    assert zb < L.z_deck_bot
    assert bottom + h.panel_h <= L.z_deck_bot - h.panel_clear + 1e-6

def test_total_height_in_owner_range(C):
    P = C.P
    total = P.frame.height + P.material.t_nominal + 10      # ~10 mm compressed futon
    assert 390 <= total <= 415                               # owner OK'd ~41 cm for the leg room


def test_posts_are_sturdy(C):
    """Each corner post (outside the head slot, post_inset in from the plate's end) is at least the stock
    thickness wide: uMake's minimum feature, and it carries a corner of the top."""
    from kotatsu import yagura
    P = C.P
    assert yagura.post_u(P) - P.frame.post_inset >= P.material.t_max


def test_cross_legged_clearance(C):
    """Owner's cross-legged knees (30" x 12.5"): the deck's ring clears them at the sides, and the knee zone can
    come knee_reach_min in under the top's edge at every side without touching a leg or the heater."""
    from kotatsu import comfort
    P = C.P
    K = P.comfort
    assert comfort.summary(P)["side_clear"] >= K.knee_h + K.knee_margin
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
    assert cz - sz / 2 >= 300, f"shins under the heater (v2: it rides in the deck, {cz - sz / 2:.0f} mm up)"
    assert frame.cheek_z(P)[0] >= cz - sz / 2 - 0.01, "cheeks must not hang below the heater"


def test_legs_forward_on_a_zaisu():
    """On a zaisu the owner sits legs forward (2026-11; a bought one, comfort.chair_seat_h): thighs under the
    deck, feet under the heater."""
    from kotatsu import comfort
    for P in TABLES:
        room = comfort.legs_forward(P, P.comfort.chair_seat_h)
        assert room["thigh_room"] >= 0 and room["feet_room"] >= 0


def test_cross_legged_knees_need_room_under_the_top():
    """Knees higher than the frame's top can't come in under the top's edge (the futon is squeezed there)."""
    from kotatsu import comfort
    for P in TABLES:
        assert comfort.knee_reach(P, height=frame.layout(P).H + 1) == 0.0
        assert comfort.knee_reach(P) >= P.comfort.knee_reach_min          # on the floor pillows it fits
