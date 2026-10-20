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
INCH = 25.4


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
    assert long_side + 50 <= P.shipping.std_max_side_in * INCH   # boxed, still a standard parcel
    w, h = sorted((x1 - x0, y1 - y0))
    assert any(w <= min(s) - 2 * P.cnc.sheet_margin and h <= max(s) - 2 * P.cnc.sheet_margin
               for s in P.cnc.sheets)


# ------------------------------------------------------------------ cross-laps
def test_crossings_agree(C):
    P, L, PARTS = C.P, C.L, C.PARTS
    """Slot positions in each panel coincide with the other panel's centre plane."""
    assert L.xS[0] - L.O == pytest.approx(P.frame.ear) and L.Lf - (L.xS[1] - L.O) == pytest.approx(P.frame.ear)
    assert L.yL[0] - L.O == pytest.approx(P.frame.ear) and L.Wf - (L.yL[1] - L.O) == pytest.approx(P.frame.ear)


# ------------------------------------------------------------------ cheeks
@pytest.mark.parametrize("t", T_RANGE)
def test_cheek_tabs_fit_deck_slots(C, t):
    P, L, PARTS = C.P, C.L, C.PARTS
    dk = PARTS["deck"].shape
    for xi, s in zip(frame.cheek_xs(P), (-1, 1)):
        xa, xb = sorted((xi, xi + s * t))
        for ya, yb in frame.tab_ys(P):
            assert clear(dk, box(xa, ya, xb, yb))


@pytest.mark.parametrize("t_deck", T_RANGE)
@pytest.mark.parametrize("t_wedge", T_RANGE)
def test_cheek_wedge_through_tab(C, t_deck, t_wedge):
    P, L, PARTS = C.P, C.L, C.PARTS
    ck, _ = frame.cheek(P)
    y_start = L.cy - P.cheek.length / 2
    zb = L.z_deck_bot - P.cheek.height
    z_top = L.z_deck_bot + t_deck
    z0, z1 = frame.cheek_hole_z(P)
    assert z0 < z_top, "hole must start below the deck top, so the wedge bears on the deck"
    need = z1 - z_top                                  # wedge height that pulls the cheek up tight
    CW = P.cheek_wedge
    assert CW.head - CW.length * P.fit.wedge_taper < need < CW.head
    for ya, yb in frame.tab_ys(P):
        uc = (ya + yb) / 2 - y_start
        sec = box(uc - t_wedge / 2, z_top - zb, uc + t_wedge / 2, z_top - zb + need - 0.01)
        assert clear(ck, sec)


def test_tabs_and_wedges_stay_below_futon_plane(C):
    P, L, PARTS = C.P, C.L, C.PARTS
    ck, _ = frame.cheek(P)
    zb = L.z_deck_bot - P.cheek.height
    assert ck.bounds[3] + zb <= L.H - 5
    assert L.z_deck_top + P.cheek_wedge.head <= L.H - 3


def test_cheeks_hug_the_heater(C):
    P, L, PARTS = C.P, C.L, C.PARTS
    a, b = frame.cheek_xs(P)
    assert b - a == pytest.approx(P.heater.body_x + P.heater.cheek_clearance)
    assert P.cheek.length >= P.heater.body_y + 40
    assert P.cheek.height >= P.heater.body_h + P.heater.top_gap


# ------------------------------------------------------------------ comfort & safety
def test_total_height_in_owner_range(C):
    P, L, PARTS = C.P, C.L, C.PARTS
    total = P.frame.height + P.material.t_nominal + 10      # ~10 mm compressed futon
    assert 390 <= total <= 415                               # owner OK'd ~41 cm for the leg room


def test_ear_fingers_are_sturdy(C):
    P, L, PARTS = C.P, C.L, C.PARTS
    """Ear fingers outside the cross-lap slots: at least the stock thickness (uMake's minimum feature).
    In the yagura they're braced by the crossing plate in the slot (owner chose 20.4 mm, = inner finger)."""
    assert P.frame.ear - frame.slot_w(P) / 2 >= P.material.t_max


def test_frame_hidden_under_round_top(C):
    """Round top: every frame corner (ear tips) stays inside the circle, with some overhang."""
    P, L = C.P, C.L
    if getattr(P.top, "shape", "rect") != "round":
        pytest.skip("rectangular top")
    r = P.top.length / 2
    t = P.material.t_max
    pts = []
    for y in L.yL:      # long panels' ends
        for x in (L.O, L.O + L.Lf):
            pts += [(x, y - t / 2), (x, y + t / 2)]
    for x in L.xS:      # short panels' ends
        for y in (L.O, L.O + L.Wf):
            pts += [(x - t / 2, y), (x + t / 2, y)]
    worst = max(((x - L.cx) ** 2 + (y - L.cy) ** 2) ** 0.5 for x, y in pts)
    assert worst <= r - 10, f"frame corner {worst:.0f} mm from centre vs top radius {r:.0f}"


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
    assert cz - sz / 2 >= 280, "shins under the heater"
    assert L.z_deck_bot - P.cheek.height >= cz - sz / 2 - 0.01, "cheeks must not hang below the heater"
