"""Frame checks: every part cuttable and shippable, every joint actually fits across the plywood
thickness tolerance, and the kotatsu is comfortable (leg room, heater clearances)."""
import pytest
from shapely.geometry import box

from kotatsu import frame, geom, params

P = params.load()
L = frame.layout(P)
PARTS = {pt.name: pt for pt in frame.parts(P)}
R = P.cnc.bit_d / 2
T_RANGE = (P.material.t_min, P.material.t_nominal, P.material.t_max)
INCH = 25.4


def clear(part_shape, rect, tol=0.01):
    """rect (cross-section of a mating part) lies entirely in empty space of part_shape."""
    return part_shape.intersection(rect).area <= tol


@pytest.mark.parametrize("name", list(PARTS))
def test_part_valid_cuttable(name):
    g = PARTS[name].shape
    assert g.is_valid and g.geom_type == "Polygon"
    assert geom.router_cuttable(g, R), f"{name}: inside corner tighter than the bit"


@pytest.mark.parametrize("name", list(PARTS))
def test_part_fits_sheet_and_parcel(name):
    x0, y0, x1, y1 = PARTS[name].shape.bounds
    long_side = max(x1 - x0, y1 - y0)
    assert long_side + 50 <= P.shipping.std_max_side_in * INCH   # boxed, still a standard parcel
    w, h = sorted((x1 - x0, y1 - y0))
    assert any(w <= min(s) - 2 * P.cnc.sheet_margin and h <= max(s) - 2 * P.cnc.sheet_margin
               for s in P.cnc.sheets)


def test_quantities():
    q = {n: pt.qty for n, pt in PARTS.items()}
    assert q["long side"] == 2 and q["short side"] == 2 and q["deck"] == 1 and q["heater cheek"] == 2
    assert q["deck wedge"] >= 2 * P.deck.tenons_per_side
    assert q["cheek wedge"] >= 4


# ------------------------------------------------------------------ cross-laps
def test_cross_lap_depths_and_widths():
    d = frame.lap_depth(P)
    assert 2 * d >= L.H and 2 * d - L.H <= 2.0          # never bottoms out, never sloppy in height
    assert frame.slot_w(P) >= P.material.t_max + 0.2


@pytest.mark.parametrize("t", T_RANGE)
def test_short_panel_passes_through_long_slot(t):
    """In the long panel's plane, the short panel's cross-section at the crossing must be empty space."""
    lp = PARTS["long side"].shape
    d = frame.lap_depth(P)
    for x in L.xS:
        u = x - L.O
        assert clear(lp, box(u - t / 2, d + 0.01, u + t / 2, L.H))


@pytest.mark.parametrize("t", T_RANGE)
def test_long_panel_passes_through_short_slot(t):
    sp = PARTS["short side"].shape
    d = frame.lap_depth(P)
    for y in L.yL:
        u = y - L.O
        assert clear(sp, box(u - t / 2, 0, u + t / 2, L.H - d - 0.01))


def test_crossings_agree():
    """Slot positions in each panel coincide with the other panel's centre plane."""
    assert L.xS[0] - L.O == pytest.approx(P.frame.ear) and L.Lf - (L.xS[1] - L.O) == pytest.approx(P.frame.ear)
    assert L.yL[0] - L.O == pytest.approx(P.frame.ear) and L.Wf - (L.yL[1] - L.O) == pytest.approx(P.frame.ear)


# ------------------------------------------------------------------ deck tusk tenons
@pytest.mark.parametrize("t", T_RANGE)
def test_deck_tenons_fit_mortises(t):
    lp = PARTS["long side"].shape
    for x0, x1 in frame.tenon_xs(P):
        sec = box(x0 - L.O, L.z_deck_bot, x1 - L.O, L.z_deck_bot + t)    # tenon cross-section
        assert clear(lp, sec)
        # in-plane fit is tight: mortise is at most 2 * fit.tight + 0.1 longer than the tenon
        assert not clear(lp, box(x0 - L.O - P.fit.tight - 0.2, L.z_deck_bot, x0 - L.O, L.z_deck_bot + t))


def test_deck_body_fits_between_aprons():
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
def test_deck_wedge_hole_starts_inside_apron(t):
    for side in (-1, 1):
        yc = L.yL[0] if side < 0 else L.yL[1]
        outer_face = yc + side * t / 2
        ya, yb = frame.deck_wedge_hole(P, side)
        inner = yb if side < 0 else ya
        assert (outer_face - inner) * side > 0.5, "wedge must bear on the apron, not the hole wall"


@pytest.mark.parametrize("t", T_RANGE)
def test_deck_wedge_engages_below_futon_plane(t):
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
def test_cheek_tabs_fit_deck_slots(t):
    dk = PARTS["deck"].shape
    for xi, s in zip(frame.cheek_xs(P), (-1, 1)):
        xa, xb = sorted((xi, xi + s * t))
        for ya, yb in frame.tab_ys(P):
            assert clear(dk, box(xa, ya, xb, yb))


@pytest.mark.parametrize("t_deck", T_RANGE)
@pytest.mark.parametrize("t_wedge", T_RANGE)
def test_cheek_wedge_through_tab(t_deck, t_wedge):
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


def test_tabs_and_wedges_stay_below_futon_plane():
    ck, _ = frame.cheek(P)
    zb = L.z_deck_bot - P.cheek.height
    assert ck.bounds[3] + zb <= L.H - 5
    assert L.z_deck_top + P.cheek_wedge.head <= L.H - 3


def test_cheeks_hug_the_heater():
    a, b = frame.cheek_xs(P)
    assert b - a == pytest.approx(P.heater.body_x + P.heater.cheek_clearance)
    assert P.cheek.length >= P.heater.body_y + 40
    assert P.cheek.height >= P.heater.body_h + P.heater.top_gap


# ------------------------------------------------------------------ comfort & safety
def test_leg_room():
    F = P.frame
    assert F.height - F.apron_depth >= 280, "thighs under the apron"
    (sx, sy, sz), (cx, cy, cz) = frame.heater_box(P)
    assert cz - sz / 2 >= 250, "knees under the heater"
    assert L.Wf - 2 * F.leg_width >= 370, "one person's legs through a short side"
    assert L.Lf - 2 * F.leg_width >= 2 * 370, "two people per long side"


def test_total_height_in_owner_range():
    total = P.frame.height + P.material.t_nominal + 10      # ~10 mm compressed futon
    assert 390 <= total <= 410


def test_ear_fingers_are_sturdy():
    """Half-height ear fingers outside the cross-lap slots."""
    assert P.frame.ear - frame.slot_w(P) / 2 >= 50
    assert P.frame.leg_width - P.frame.ear - frame.slot_w(P) / 2 >= 80
