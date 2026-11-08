"""FEA checks (kotatsu/fea.py): textbook cases first, then the table's parts."""
import numpy as np
import pytest
from shapely.geometry import Point, box

from kotatsu import fea, params


@pytest.fixture(scope="module")
def p():
    return params.tables(params.load())[0]


def test_mesh_area_and_embedded_patch():
    g = box(0, 0, 100, 50).difference(Point(50, 25).buffer(10))
    m = fea.mesh(g, 5, extra=[box(10, 10, 20, 20)])
    x, y = m.p[:, m.t]
    area = 0.5 * np.abs((x[1] - x[0]) * (y[2] - y[0]) - (x[2] - x[0]) * (y[1] - y[0]))
    assert area.sum() == pytest.approx(g.area, rel=2e-3)
    assert area[fea.in_any(m, [box(10, 10, 20, 20)])].sum() == pytest.approx(100.0, rel=1e-6)


def _navier(a, q, D, n=99):
    """Simply supported square plate, uniform load, nu = 0: centre deflection and moment (series)."""
    w = mo = 0.0
    for i in range(1, n, 2):
        for j in range(1, n, 2):
            s = (-1) ** ((i + j) // 2 - 1)
            den = i * j * ((i / a) ** 2 + (j / a) ** 2) ** 2
            w += s / den
            mo += s * (i / a) ** 2 / den
    c = 16 * q / np.pi ** 6
    return c * w / D, c * mo * np.pi ** 2


def test_plate_simply_supported_square_matches_navier():
    a, t, E, q = 1000.0, 10.0, 1e4, 1e-3
    w0, m0 = _navier(a, q, E * t ** 3 / 12)
    assert w0 == pytest.approx(0.00406 * q * a ** 4 / (E * t ** 3 / 12), rel=1e-3)   # Timoshenko's table
    m = fea.mesh(box(0, 0, a, a), 50)
    edge = np.where((m.p[0] < 1e-6) | (m.p[0] > a - 1e-6) | (m.p[1] < 1e-6) | (m.p[1] > a - 1e-6))[0]
    r = fea.plate(m, t, E, E, E / 2, np.full(m.t.shape[1], q), edge, hold=edge)    # held both ways
    assert r.w.max() == pytest.approx(w0, rel=0.01)
    assert np.abs(r.sx).max() == pytest.approx(6 * m0 / t ** 2, rel=0.01)
    assert r.reaction.sum() == pytest.approx(q * a * a, rel=1e-6)


def test_top_sitter_balances_and_holds(p):
    """The worst case (an adult sitting on an edge), coarse mesh: forces balance, the grillage agrees,
    and the thinnest top keeps a margin of 2 or more one thickness clear of the pads."""
    from kotatsu import loads
    pats = loads.cases(p)["beyond normal: an 80 kg adult sits on the middle of an edge (x1.5)"]
    r = fea.top_case(p, pats, h=28)
    assert sum(r["pad_N"]) == pytest.approx(r["load_N"], rel=1e-6)
    assert r["away"]["util"] < 0.5
    assert r["sag_mm"] < 12
    near_edge = r["corner_N"]["+-"] + r["corner_N"]["--"]
    assert near_edge > 0.9 * r["load_N"]                      # the far corners nearly lift
    q = params.load()                                          # the grillage at the same (thinnest) stock
    q = params.tables(q)[0]
    q.material.t_nominal = q.material.t_min
    g = loads.solve(q, [loads.self_weight(q)] + pats)
    assert r["sag_mm"] == pytest.approx(g.w_max, rel=0.2)
    assert r["away"]["sx"] == pytest.approx(g.sigma_x, rel=0.2)


def test_deck_hand_on_ring(p):
    """A hand beside a cheek, coarse mesh: forces balance; with the wedges tight the deck holds (Tsai-Hill
    under 1 at the fillets) and sags under 15 mm; with them slack it sags much more (keep them tapped in)."""
    case = fea.deck_cases(p)["hand on the ring beside a cheek (mid-side)"]
    tight = fea.deck_case(p, case, h=16)
    assert tight["support_N"] == pytest.approx(tight["load_N"], rel=1e-6)
    assert tight["fillets"]["tsai_hill"] < 1.0
    assert tight["sag_mm"] < 15
    assert tight["fillets"]["sx"] > tight["arms"]["sx"]                 # the fillets carry the peak
    slack = fea.deck_case(p, case, h=16, wedges=False)
    assert slack["sag_mm"] > 2 * tight["sag_mm"]


def test_plane_stress_cantilever_matches_timoshenko():
    L, h, t, E, P = 200.0, 20.0, 10.0, 1e4, 10.0
    I = t * h ** 3 / 12
    tip = P * L ** 3 / (3 * E * I) + P * L / (5 / 6 * E / 2 * t * h)       # bending + shear (nu = 0)
    m = fea.mesh(box(0, 0, L, h), 5)
    end = box(-0.1, -1, 0.1, h + 1)
    cs = [fea.Contact("x", end, 0, 1, 1e7, bilateral=True), fea.Contact("y", end, 1, 1, 1e7, bilateral=True)]
    r = fea.plane(m, t, E, E, E / 2, cs, [(box(L - 0.1, -1, L + 0.1, h + 1), (0.0, -P))])
    assert -r.u.min() == pytest.approx(tip, rel=0.01)
    c = m.p[:, m.t].mean(axis=1)
    mid = np.abs(c[0] - L / 2) < 5
    assert np.abs(r.su[mid]).max() == pytest.approx(P * L / 2 * (h / 2) / I, rel=0.03)
    assert r.forces["y"] == pytest.approx(P, rel=1e-3)



@pytest.fixture(scope="module")
def leg_push(p):
    return fea.leg_case(p, "A", p.fea.push_n, None, h=4)   # converged (6 mm overstates the wedge hole with the taper)


def test_leg_pair_takes_the_push_and_the_wedge_its_preload(p, leg_push):
    a, b = leg_push["forces"]                                   # the plate, and its mirror image
    assert a["floor (grip)"] - b["floor (grip)"] == pytest.approx(p.fea.push_n, abs=1.0)
    rest = fea.leg_case(p, "A", 0.0, {"A tenon": 600.0}, h=6)
    assert rest["forces"][0]["wedge"] == pytest.approx(p.stiffness.wedge_preload, abs=2.0)
    assert max(z["tsai_hill"] for z in rest["zones"].values()) < 0.5   # a sitter's load alone is fine


def test_leg_fingers_bend_alone(p, leg_push):
    """The lumped model bends the slotted part of A as one section; FE finds the fingers either side of the
    open slot bending each on its own, the peak at a finger's root (the haunch fillet, or the slot's root since
    the haunch became an S-curve), many times stiffness.stresses' value."""
    from kotatsu import stiffness
    z = leg_push["zones"]
    finger = max(z["haunch fillet"]["sx"], z["slot root"]["sx"])        # at 70 mm the wedge hole can be worse still
    assert finger > 5 * float(stiffness.stresses(p, p.fea.push_n)["leg_MPa"])


def test_leg_plates_hold_the_push(leg_push):
    """A 200 N shove at table height, 14.1 mm stock: no zone of plate A past its strength (Tsai-Hill; the
    wedge's bearing peaks are local crushing, kept apart). Failed at leg_narrow 60; holds at 70 (owner 2026-11)."""
    assert max(v["tsai_hill"] for k, v in leg_push["zones"].items() if k != "contact edges") < 1.0
