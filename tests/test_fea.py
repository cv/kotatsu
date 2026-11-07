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
