"""Frame checks: every part cuttable and shippable, every joint actually fits across the plywood
thickness tolerance, and the kotatsu is comfortable (leg room, heater clearances)."""
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


def _slab(C):
    if getattr(C.P.frame, "style", "slab") != "slab":
        pytest.skip("slab-frame specific (yagura variant: tests/test_yagura.py)")


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


def test_quantities(C):
    _slab(C)
    P, L, PARTS = C.P, C.L, C.PARTS
    q = {n: pt.qty for n, pt in PARTS.items()}
    assert q["long side"] == 2 and q["short side"] == 2 and q["deck"] == 1 and q["heater cheek"] == 2
    assert "deck wedge" not in q, "deck tenons are plain through-tenons now"
    assert q["cheek wedge"] >= 4


# ------------------------------------------------------------------ cross-laps
def test_cross_lap_depths_and_widths(C):
    _slab(C)
    P, L, PARTS = C.P, C.L, C.PARTS
    d = frame.lap_depth(P)
    assert 2 * d >= L.H and 2 * d - L.H <= 2.0          # never bottoms out, never sloppy in height
    assert frame.slot_w(P) >= P.material.t_max + 0.2


@pytest.mark.parametrize("t", T_RANGE)
def test_short_panel_passes_through_long_slot(C, t):
    _slab(C)
    P, L, PARTS = C.P, C.L, C.PARTS
    """In the long panel's plane, the short panel's cross-section at the crossing must be empty space."""
    lp = PARTS["long side"].shape
    d = frame.lap_depth(P)
    for x in L.xS:
        u = x - L.O
        assert clear(lp, box(u - t / 2, d + 0.01, u + t / 2, L.H))


@pytest.mark.parametrize("t", T_RANGE)
def test_long_panel_passes_through_short_slot(C, t):
    _slab(C)
    P, L, PARTS = C.P, C.L, C.PARTS
    sp = PARTS["short side"].shape
    d = frame.lap_depth(P)
    for y in L.yL:
        u = y - L.O
        assert clear(sp, box(u - t / 2, 0, u + t / 2, L.H - d - 0.01))


def test_crossings_agree(C):
    P, L, PARTS = C.P, C.L, C.PARTS
    """Slot positions in each panel coincide with the other panel's centre plane."""
    assert L.xS[0] - L.O == pytest.approx(P.frame.ear) and L.Lf - (L.xS[1] - L.O) == pytest.approx(P.frame.ear)
    assert L.yL[0] - L.O == pytest.approx(P.frame.ear) and L.Wf - (L.yL[1] - L.O) == pytest.approx(P.frame.ear)


# ------------------------------------------------------------------ deck through-tenons
@pytest.mark.parametrize("t", T_RANGE)
def test_deck_tenons_fit_mortises(C, t):
    _slab(C)
    P, L, PARTS = C.P, C.L, C.PARTS
    lp = PARTS["long side"].shape
    for x0, x1 in frame.tenon_xs(P):
        sec = box(x0 - L.O, L.z_deck_bot, x1 - L.O, L.z_deck_bot + t)    # tenon cross-section
        assert clear(lp, sec)
        # in-plane fit is tight: mortise is at most 2 * fit.tight + 0.1 longer than the tenon
        assert not clear(lp, box(x0 - L.O - P.fit.tight - 0.2, L.z_deck_bot, x0 - L.O, L.z_deck_bot + t))


def test_deck_body_fits_between_aprons(C):
    _slab(C)
    P, L, PARTS = C.P, C.L, C.PARTS
    dk = PARTS["deck"].shape
    for t in T_RANGE:
        inner0, inner1 = L.yL[0] + t / 2, L.yL[1] - t / 2
        # the deck body (not tenons) lies between the inner faces even for the thickest stock
        body = dk.intersection(box(0, inner0 - 50, 2000, inner1 + 50)).difference(
            box(0, inner0 - 50, 2000, inner0)).difference(box(0, inner1, 2000, inner1 + 50))
        assert body.area > 0
    gap = (L.yL[1] - L.yL[0] - P.material.t_min) - (L.yL[1] - L.yL[0] - P.material.t_max - 2 * P.fit.tight)
    assert gap <= 2.5     # worst-case play along y (thin aprons): harmless, the tenons stay engaged


def test_deck_tenons_sit_in_the_legs(C):
    """Each tenon (and its mortise) lies in solid leg, clear of the cross-lap slot and the leg opening,
    so the apron above the opening carries no joint and can stay shallow."""
    _slab(C)
    P, L = C.P, C.L
    a, b = frame.leg_zone(P)
    for x0, x1 in frame.tenon_xs(P):
        u0, u1 = sorted((x0 - L.O, x1 - L.O))
        if u0 > L.Lf / 2:                                  # far end: mirror into the near end's terms
            u0, u1 = L.Lf - u1, L.Lf - u0
        assert u0 - P.fit.tight - a >= 15, "too close to the cross-lap slot"
        assert b - (u1 + P.fit.tight) >= 15, "too close to the leg opening"
    assert L.z_deck_top + P.material.t_max - P.material.t_nominal <= L.H - 20, "mortise too near the top edge"


@pytest.mark.parametrize("t", T_RANGE)
def test_deck_tenons_go_right_through(C, t):
    """Through-tenons end just proud of the apron's outer face for every stock thickness."""
    _slab(C)
    P, L, PARTS = C.P, C.L, C.PARTS
    _, y0, _, y1 = PARTS["deck"].shape.bounds
    for yc, end, side in ((L.yL[0], y0, -1), (L.yL[1], y1, 1)):
        proud = (end - (yc + side * t / 2)) * side
        assert 0.5 <= proud <= 3.0, f"tenon end {proud:.2f} mm past the outer face"


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
def test_leg_room(C):
    """Owner chose leg-room changes A, B, D, E, F (PLAN.md section 3)."""
    _slab(C)
    P, L, PARTS = C.P, C.L, C.PARTS
    F = P.frame
    assert F.height - F.apron_depth >= 325, "thighs/knees under the apron"
    (sx, sy, sz), (cx, cy, cz) = frame.heater_box(P)
    assert cz - sz / 2 >= 280, "shins under the heater"
    zb = L.z_deck_bot - P.cheek.height
    assert zb >= cz - sz / 2 - 0.01, "cheeks must not hang below the heater"
    n_long, n_short = P.comfort.sitters
    assert L.Lf - 2 * F.leg_width >= n_long * P.comfort.leg_gap, "legs through a long side"
    assert L.Wf - 2 * F.leg_width >= n_short * P.comfort.leg_gap, "legs through a short side"


def test_total_height_in_owner_range(C):
    P, L, PARTS = C.P, C.L, C.PARTS
    total = P.frame.height + P.material.t_nominal + 10      # ~10 mm compressed futon
    assert 390 <= total <= 415                               # owner OK'd ~41 cm for the leg room


def test_ear_fingers_are_sturdy(C):
    P, L, PARTS = C.P, C.L, C.PARTS
    """Half-height ear fingers outside the cross-lap slots."""
    assert P.frame.ear - frame.slot_w(P) / 2 >= 40
    if getattr(P.frame, "style", "slab") == "slab":      # slab legs carry the deck tenon in this zone
        assert P.frame.leg_width - P.frame.ear - frame.slot_w(P) / 2 >= 80


def test_deck_clears_short_panels(C):
    _slab(C)
    P, L = C.P, C.L
    x0, _, x1, _ = C.PARTS["deck"].shape.bounds
    assert x0 >= L.xS[0] + P.material.t_max / 2 + 5 and x1 <= L.xS[1] - P.material.t_max / 2 - 5


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


def test_tapered_feet_are_sturdy(C):
    """Tapered legs: at the floor, the foot beside the short panel's bottom-open slot is still >= 40 wide,
    and the taper never reaches up into the deck-tenon leg zone (it stops at the apron underside)."""
    _slab(C)
    P = C.P
    F = P.frame
    foot = frame.leg_inner_u(P, 0) - F.ear - frame.slot_w(P) / 2
    assert foot >= 40, f"inner foot finger only {foot:.1f} mm at the floor"
    assert frame.leg_inner_u(P, F.height - F.apron_depth) == pytest.approx(F.leg_width)
    sp = C.PARTS["short side"].shape
    u = frame.leg_inner_u(P, 1.0)
    assert sp.intersection(box(u + 0.5, 0, u + 30, 2)).area < 1, "opening must be wider at the floor"


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
    if P.comfort.tip_min_n > 0 and P.table_name in {t.table_name for t in params.build_tables(BASE)}:
        assert std >= P.comfort.tip_min_n
