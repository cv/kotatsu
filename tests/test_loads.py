"""The grillage plate model against textbook plate solutions, and the everyday load cases."""
import pytest
from shapely.geometry import box

from kotatsu import comfort, loads, params


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
    r = loads.solve(P, [loads.Patch("pt", 1000.0, -1, -1, 1, 1)], supports=ring, compression_only=False,
                    outline=box(-h, -h, h, h))
    D = P.material.E_par * P.material.t_nominal ** 3 / 12
    assert r.w_max == pytest.approx(0.0116 * 1000 * (2 * h) ** 2 / D, rel=0.03)


def test_grillage_matches_plate_theory_uniform_load(P):
    """Uniform load, nu = 0: w = 0.00406 q a^4 / D, M = 0.0368 q a^2."""
    h, ring = _iso_ss(P)
    q, a, t = 0.001, 2 * h, P.material.t_nominal
    r = loads.solve(P, [loads.Patch("q", q * a * a, -h, -h, h, h)], supports=ring, compression_only=False,
                    outline=box(-h, -h, h, h))
    D = P.material.E_par * t ** 3 / 12
    assert r.w_max == pytest.approx(0.00406 * q * a ** 4 / D, rel=0.08)
    assert r.sigma_x == pytest.approx(6 * 0.0368 * q * a * a / t ** 2, rel=0.08)


def test_everyday_loads_have_a_big_margin(P):
    """Napping + cat + laptop, slumping, cat jumps: under 20 % of the (rough) strength, top sags < 5 mm,
    every corner stays down. Sitting on the table: still under half, sag < 10 mm (v2's 15 mm top: 6.7;
    the futon and the 26 mm gap to the deck take far more)."""
    rep = loads.report(P, lift=False)
    for name, r in rep.items():
        beyond = name.startswith("beyond")
        assert r["use_of_strength_%"] < (50.0 if beyond else 20.0), name
        assert r["sag_mm"] < (10.0 if beyond else 5.0), name
        assert len(r["corner_reactions_N"]) == 4 and min(r["corner_reactions_N"].values()) > 0, name


def test_grillage_is_the_real_top(P):
    """The grillage models the squircle, not its bounding square: its own weight from the real area, grid nodes off
    the top carry nothing, and a patch hanging off the corner puts its whole force on the part that's on the top."""
    from shapely.geometry import Point
    top = comfort._top_centred(P)
    sw = loads.self_weight(P)
    assert sw.force_n == pytest.approx(top.area / 1e6 * P.material.t_nominal / 1000 * P.material.density_kg_m3 * 9.81)
    h = P.top.length / 2
    paw = loads.Patch("paw off the corner", 200.0, h - 60, h - 60, h + 20, h + 20)
    r = loads.solve(P, [sw, paw])
    assert sum(r.reactions.values()) == pytest.approx(sw.force_n + paw.force_n, abs=0.5)   # (rounded to 0.1 N a corner)
    off = [(j, i) for j, y in enumerate(r.ys) for i, x in enumerate(r.xs) if not top.buffer(1e-6).contains(Point(x, y))]
    assert off and all(r.w[j, i] == 0.0 for j, i in off)
