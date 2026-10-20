"""The grillage plate model against textbook plate solutions, and the everyday load cases."""
import pytest
from shapely.geometry import box

from kotatsu import loads, params


@pytest.fixture
def P():
    return params.tables(params.load())[0]


def _iso_ss(P):
    P.loads.E_cross = P.material.E_par
    P.loads.G_plate = P.material.E_par / 2              # nu = 0
    h = P.top.length / 2
    return h, box(-h - 1, -h - 1, h + 1, h + 1).difference(box(-h + 5, -h + 5, h - 5, h - 5))


def test_grillage_matches_navier_point_load(P):
    """Simply supported square plate, central point load: w = 0.0116 P a^2 / D (Timoshenko)."""
    h, ring = _iso_ss(P)
    r = loads.solve(P, [loads.Patch("pt", 1000.0, -1, -1, 1, 1)], supports=ring, compression_only=False)
    D = P.material.E_par * P.material.t_nominal ** 3 / 12
    assert r.w_max == pytest.approx(0.0116 * 1000 * (2 * h) ** 2 / D, rel=0.03)


def test_grillage_matches_plate_theory_uniform_load(P):
    """Uniform load, nu = 0: w = 0.00406 q a^4 / D, M = 0.0368 q a^2."""
    h, ring = _iso_ss(P)
    q, a, t = 0.001, 2 * h, P.material.t_nominal
    r = loads.solve(P, [loads.Patch("q", q * a * a, -h, -h, h, h)], supports=ring, compression_only=False)
    D = P.material.E_par * t ** 3 / 12
    assert r.w_max == pytest.approx(0.00406 * q * a ** 4 / D, rel=0.08)
    assert r.sigma_x == pytest.approx(6 * 0.0368 * q * a * a / t ** 2, rel=0.08)


def test_everyday_loads_have_a_big_margin(P):
    """Napping + cat + laptop, slumping, cat jumps: under 20 % of the (rough) strength, top sags < 5 mm,
    every corner stays down. Sitting on the table: still under half."""
    rep = loads.report(P, lift=False)
    for name, r in rep.items():
        limit = 50.0 if name.startswith("beyond") else 20.0
        assert r["use_of_strength_%"] < limit, name
        assert r["sag_mm"] < 5.0, name
        assert len(r["corner_reactions_N"]) == 4 and min(r["corner_reactions_N"].values()) > 0, name
