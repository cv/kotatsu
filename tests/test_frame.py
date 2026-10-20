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
    P, L, PARTS = C.P, C.L, C.PARTS
    q = {n: pt.qty for n, pt in PARTS.items()}
    assert q["long side"] == 2 and q["short side"] == 2 and q["deck"] == 1 and q["heater cheek"] == 2
    assert q["deck wedge"] >= 2 * P.deck.tenons_per_side
    assert q["cheek wedge"] >= 4


# ------------------------------------------------------------------ cross-laps
def test_cross_lap_depths_and_widths(C):
    P, L, PARTS = C.P, C.L, C.PARTS
    d = frame.lap_depth(P)
    assert 2 * d >= L.H and 2 * d - L.H <= 2.0          # never bottoms out, never sloppy in height
    assert frame.slot_w(P) >= P.material.t_max + 0.2


@pytest.mark.parametrize("t", T_RANGE)
def test_short_panel_passes_through_long_slot(C, t):
    P, L, PARTS = C.P, C.L, C.PARTS
    """In the long panel's plane, the short panel's cross-section at the crossing must be empty space."""
    lp = PARTS["long side"].shape
    d = frame.lap_depth(P)
    for x in L.xS:
        u = x - L.O
        assert clear(lp, box(u - t / 2, d + 0.01, u + t / 2, L.H))


@pytest.mark.parametrize("t", T_RANGE)
def test_long_panel_passes_through_short_slot(C, t):
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


# ------------------------------------------------------------------ deck tusk tenons
@pytest.mark.parametrize("t", T_RANGE)
def test_deck_tenons_fit_mortises(C, t):
    P, L, PARTS = C.P, C.L, C.PARTS
    lp = PARTS["long side"].shape
    for x0, x1 in frame.tenon_xs(P):
        sec = box(x0 - L.O, L.z_deck_bot, x1 - L.O, L.z_deck_bot + t)    # tenon cross-section
        assert clear(lp, sec)
        # in-plane fit is tight: mortise is at most 2 * fit.tight + 0.1 longer than the tenon
        assert not clear(lp, box(x0 - L.O - P.fit.tight - 0.2, L.z_deck_bot, x0 - L.O, L.z_deck_bot + t))


def test_deck_body_fits_between_aprons(C):
    P, L, PARTS = C.P, C.L, C.PARTS
    dk = PARTS["deck"].shape
    for t in T_RANGE:
        inner0, inner1 = L.yL[0] + t / 2, L.yL[1] - t / 2
        # the deck body (not tenons) lies between the inner faces even for the thickest stock
        body = dk.intersection(box(0, inner0 - 50, 2000, inner1 + 50)).difference(
            box(0, inner0 - 50, 2000, inner0)).difference(box(0, inner1, 2000, inner1 + 50))
        assert body.area > 0
    gap = (L.yL[1] - L.yL[0] - P.material.t_min) - (L.yL[1] - L.yL[0] - P.material.t_max - 2 * P.fit.tight)
    assert gap <= 2.5     # worst-case play along y, taken up by the wedges


@pytest.mark.parametrize("t", T_RANGE)
def test_deck_wedge_hole_starts_inside_apron(C, t):
    P, L, PARTS = C.P, C.L, C.PARTS
    for side in (-1, 1):
        yc = L.yL[0] if side < 0 else L.yL[1]
        outer_face = yc + side * t / 2
        ya, yb = frame.deck_wedge_hole(P, side)
        inner = yb if side < 0 else ya
        assert (outer_face - inner) * side > 0.5, "wedge must bear on the apron, not the hole wall"


@pytest.mark.parametrize("t", T_RANGE)
def test_deck_wedge_engages_below_futon_plane(C, t):
    P, L, PARTS = C.P, C.L, C.PARTS
    """For every stock thickness the wedge tightens with its head still below the apron top."""
    W, taper = P.deck_wedge, P.fit.wedge_taper
    foot = W.head - W.length * taper
    for side in (-1, 1):
        yc = L.yL[0] if side < 0 else L.yL[1]
        face = yc + side * t / 2
        ya, yb = frame.deck_wedge_hole(P, side)
        far = ya if side < 0 else yb
        need = abs(face - far)
        assert foot < need < W.head
        v_at = (need - foot) / taper
        head_z = L.z_deck_top - v_at + W.length
        assert head_z <= L.H - 3, f"wedge head at {head_z:.0f} pokes above the apron top"
        foot_z = L.z_deck_top - v_at
        assert foot_z >= P.frame.height - P.frame.apron_depth + 3, \
            f"wedge foot at {foot_z:.0f} hangs below the apron into knee space"


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
    P, L, PARTS = C.P, C.L, C.PARTS
    F = P.frame
    assert F.height - F.apron_depth >= 280, "thighs under the apron"
    (sx, sy, sz), (cx, cy, cz) = frame.heater_box(P)
    assert cz - sz / 2 >= 250, "knees under the heater"
    n_long, n_short = P.comfort.sitters
    assert L.Lf - 2 * F.leg_width >= n_long * P.comfort.leg_gap, "legs through a long side"
    assert L.Wf - 2 * F.leg_width >= n_short * P.comfort.leg_gap, "legs through a short side"


def test_total_height_in_owner_range(C):
    P, L, PARTS = C.P, C.L, C.PARTS
    total = P.frame.height + P.material.t_nominal + 10      # ~10 mm compressed futon
    assert 390 <= total <= 410


def test_ear_fingers_are_sturdy(C):
    P, L, PARTS = C.P, C.L, C.PARTS
    """Half-height ear fingers outside the cross-lap slots."""
    assert P.frame.ear - frame.slot_w(P) / 2 >= 50
    assert P.frame.leg_width - P.frame.ear - frame.slot_w(P) / 2 >= 80


def test_deck_clears_short_panels(C):
    P, L = C.P, C.L
    x0, x1 = L.cx - P.deck.length_x / 2, L.cx + P.deck.length_x / 2
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
