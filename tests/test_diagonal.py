"""The legs (kotatsu/yagura.py): one plate per corner on its diagonal, a crosspiece in its head. Every joint must fit across the stock-thickness range; the deck bears on what it should."""
import math
from types import SimpleNamespace

import numpy as np
import pytest
from shapely.geometry import LineString, box
from shapely.ops import unary_union

from kotatsu import comfort, frame, params, stiffness, yagura

P = params.tables(params.load())[0]
L = frame.layout(P)
D = SimpleNamespace(**{**vars(P.frame), **vars(P.yagura)})   # ear, head_slot, cross_w ... in one place
PARTS = {pt.name: pt for pt in frame.parts(P)}
T_RANGE = (P.material.t_min, P.material.t_nominal, P.material.t_max)


def test_quantities():
    q = {pt.name: pt.qty for pt in frame.parts(P)}
    assert q == {"leg plate": 4, "leg crosspiece": 4, "deck": 1, "heater cheek": 2, "wedge": 6}


def _head_slot_gaps():
    """The head slot's width across the plate, every 0.5 mm from just above its round bottom to the shoulders."""
    g, w = PARTS["leg plate"].shape, frame.slot_w(P)
    zb = L.z_deck_bot - D.head_slot
    out = []
    for z in np.linspace(zb + 1.5, L.z_deck_bot - 1, 46):        # (below: the round bottom it sits on)
        cut = g.intersection(LineString([(D.ear - w, z), (D.ear + w, z)]))
        pieces = sorted((q.bounds[0], q.bounds[2]) for q in getattr(cut, "geoms", [cut]) if not q.is_empty)
        out.append(pieces[1][0] - pieces[0][1])
    return np.array(out)


@pytest.mark.parametrize("t", T_RANGE)
def test_crosspiece_fits_the_head_slot(t):
    """The head slot is the full slot width (it takes the thickest sheet) but at the crush ribs, where it narrows
    to the thinnest: the crosspiece is snug on any stock, and the thickest goes in after sanding the bumps (or its
    faces) by (t - t_min) / 2 a side, within fit.fit_sand. The crosspiece is head_slot deep + cross_proud (sanded
    to fit), and long enough to stand out cross_w / 2 each side."""
    gaps, w = _head_slot_gaps(), frame.slot_w(P)
    assert gaps.max() == pytest.approx(w, abs=1e-6) and w >= t, "clear of the bumps it takes any sheet"
    snug = gaps.min()
    assert snug == pytest.approx(P.material.t_min, abs=0.01), "the bumps leave the thinnest sheet between them"
    assert snug <= t + 1e-6, "snug: no play at the bumps"
    sand = max(0.0, (t - snug) / 2)
    assert sand <= P.fit.fit_sand, f"{t} mm stock needs {sand:.2f} mm off each side at the fit-up"
    assert frame.rib_proud(P) <= P.fit.fit_sand, "sanding a bump flat is within the fit-up's sanding"
    cp = PARTS["leg crosspiece"].shape
    assert cp.bounds[3] - cp.bounds[1] == pytest.approx(D.head_slot + D.cross_proud)
    assert cp.bounds[2] - cp.bounds[0] == pytest.approx(D.cross_w)


@pytest.mark.parametrize("t", T_RANGE)
def test_tenons_fit_the_mortises(t):
    """In each corner's own frame: the mortise takes the tenon + fit.tight each way, and any sheet across."""
    ta, tb = yagura._tenon_u(P)
    for (*_, C, d, n), m in zip(yagura.corners(P), yagura.mortise_boxes(P)):
        us = [(x - C[0]) * d[0] + (y - C[1]) * d[1] for x, y in m.exterior.coords]
        vs = [(x - C[0]) * n[0] + (y - C[1]) * n[1] for x, y in m.exterior.coords]
        assert min(us) <= ta - P.fit.tight + 1e-6 and max(us) >= tb + P.fit.tight - 1e-6
        assert max(vs) - min(vs) >= t


def test_deck_bears_on_the_plates_and_crosspieces():
    """The deck covers each plate's top edge (but for its tenon, which goes up through the mortise) and each
    crosspiece's whole top edge (but for a few mm2 at its rounded corners)."""
    d = PARTS["deck"].shape
    holes = unary_union(yagura.mortise_boxes(P))
    for s in yagura.plate_tops(P):
        assert s.difference(holes).difference(d).area < 15.0, "(the mortise's 4 dogbones nibble ~3 mm2 each)"
    for s in yagura.cross_tops(P):
        assert s.difference(d).area < 10.0, "(a sliver at the tips, under the pads' rounded far corners)"
    for w in yagura.wedge_footprints(P):
        assert w.difference(holes).difference(d).area < 1.0, "each wedge lies on wood"


def test_posts_rise_clear_of_the_deck():
    d = PARTS["deck"].shape
    pu, t = yagura.post_u(P), P.material.t_max
    for *_, C, dd, n in yagura.corners(P):
        post = yagura._plan(box(D.post_inset, -t / 2, pu, t / 2), C, dd, n)
        assert post.intersection(d).area == 0.0


def test_crosspieces_stay_inside_the_frame():
    sq = box(L.O, L.O, L.O + L.Lf, L.O + L.Wf).buffer(-3.0)
    for s in yagura.cross_tops(P):
        assert sq.contains(s)


def test_wood_beside_the_head_slot():
    """Below the shoulders the plate is wide enough that the slot never leaves wood thinner than the sheet."""
    g, w = PARTS["leg plate"].shape, frame.slot_w(P)
    zb = L.z_deck_bot - D.head_slot
    for z in np.linspace(zb - 8, L.z_deck_bot - 1, 30):
        cut = g.intersection(LineString([(D.ear + w / 2, z), (500, z)]))
        pieces = [q for q in getattr(cut, "geoms", [cut]) if not q.is_empty]
        assert pieces and min(q.length for q in pieces) >= P.material.t_nominal


def test_corners_are_the_same_rotated():
    from shapely.affinity import rotate
    q = box(L.O - 50, L.O - 50, L.cx, L.cy)
    for gs in (yagura.mortise_boxes(P), yagura.wedge_footprints(P), yagura.plate_tops(P),
               yagura.cross_tops(P), yagura.pads(P)):
        g = unary_union(gs)
        ref = g.intersection(q)
        for ang in (90, 180, 270):
            assert rotate(g, ang, origin=(L.cx, L.cy)).intersection(q).symmetric_difference(ref).area < 1.0


def test_twist_and_legroom():
    """The crosspieces give each joint cross_w to rock on: a stiff twist, and joints that stay shut well past
    the twist check's push; the legs, one thin plate a corner, leave more room than the "+" legs did (638 mm; the
    slim kicked legs: 642, the 50 mm haunch reaching into the legs-forward zone) and at least comfort.legroom_min."""
    tw = stiffness.twist(P)
    assert tw["corner_mm"] < 2.5 and tw["opens_at_corner_N"] > 1.5 * P.stiffness.twist_n
    assert comfort.legroom(P) > 638 and comfort.legroom(P) >= P.comfort.legroom_min


def test_the_kick_leaves_the_joints_alone():
    """yagura.leg_kick sweeps the lower leg out, both edges together, fading out at leg_curve_top: below the head
    slot's round bottom and the wedge hole, so above it the plate is exactly the unkicked one; at the floor the foot
    has moved out by leg_kick, its width kept."""
    import copy
    q = copy.deepcopy(P)
    q.yagura.leg_kick = 0.0
    g, g0 = yagura.leg_plate(P), yagura.leg_plate(q)
    zt, k = P.yagura.leg_curve_top, P.yagura.leg_kick
    assert k > 0 and zt < yagura.head_slot(P).bounds[1] and zt < yagura.leg_hole_z(P)[0]
    above = box(-1e3, zt, 1e3, 1e3)
    assert g.intersection(above).symmetric_difference(g0.intersection(above)).area < 1.0
    foot = box(-1e3, -1.0, 1e3, 0.5)
    (a, _, b, _), (a0, _, b0, _) = g.intersection(foot).bounds, g0.intersection(foot).bounds
    assert a == pytest.approx(a0 - k, abs=0.3) and b - a == pytest.approx(b0 - a0, abs=0.3)


def test_squircle_top_covers_the_posts():
    from shapely.affinity import translate
    from kotatsu import top
    posts = comfort.top_supports(P)                # what the top rests on: the posts' flat ends (and the tenons)
    tp = translate(top.build(P).outline, -P.top.length / 2, -P.top.width / 2)
    assert tp.contains(posts) and tp.exterior.distance(posts) >= 18.0
