"""Wobble model (kotatsu/stiffness.py): sanity and safety-margin checks. The material values are rough
(params [material], [stiffness]), so these guard the model's behaviour and big margins, not certification."""
import numpy as np
import pytest

from kotatsu import params, stiffness

P = params.tables(params.load())[0]


@pytest.fixture(scope="module")
def S():
    return stiffness.summary(P)


def test_sway_is_finite_and_grows_with_load(S):
    for d in ("x", "y"):
        v = [S[d]["sway_mm"][k] for k in ("50", "100", "200")]
        assert all(np.isfinite(v)) and 0 < v[0] < v[1] < v[2]


def test_sway_small_with_tight_wedges(S):
    """Rough target (mine, not a standard): under 1 mm of sway for a 100 N sideways push."""
    assert S["x"]["sway_mm"]["100"] < 1.0 and S["y"]["sway_mm"]["100"] < 1.0


def test_stress_margins(S):
    """At least 3x margin to the (rough) bending strength in every checked spot."""
    st = S["stress"]
    for k in ("leg_MPa", "top_MPa_at_1000N", "wedge_bridge_shear_MPa"):
        assert st[k] * 3 <= st["f_m"], k


def test_joint_softer_material_means_more_sway():
    import copy
    soft = copy.deepcopy(P)
    soft.stiffness.E_perp = P.stiffness.E_perp / 3
    soft.material.E_par = P.material.E_par / 3
    assert stiffness.frame_sway(soft, 100.0)["sway_mm"] > stiffness.frame_sway(P, 100.0)["sway_mm"]
