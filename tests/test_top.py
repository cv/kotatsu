import copy

import pytest

from kotatsu import geom, params, top

STYLES = ["ari", "puzzle", "chigiri", "none"]
INCH = 25.4


@pytest.fixture(scope="module")
def base():
    return params.load()


def build(base, style):
    p = copy.deepcopy(base)
    p.top.split = style
    return p, top.build(p)


@pytest.mark.parametrize("style", STYLES)
def test_parts_valid_and_cuttable(base, style):
    p, tp = build(base, style)
    r = p.cnc.bit_d / 2
    for part in tp.halves + tp.keys:
        assert part.is_valid and part.geom_type == "Polygon"
        assert geom.router_cuttable(part, r), "inside corner tighter than bit radius"


@pytest.mark.parametrize("style", STYLES)
def test_no_overlap_and_full_coverage(base, style):
    p, tp = build(base, style)
    parts = tp.halves + tp.keys
    for i, a in enumerate(parts):
        for b in parts[i + 1:]:
            assert a.intersection(b).area < 1e-6
    covered = sum(x.area for x in parts)
    gap_area = tp.outline.area - covered
    # only clearance slivers missing: < 1 mm average over the seam length
    assert 0 <= gap_area < p.top.width * 1.0


@pytest.mark.parametrize("style", ["ari", "puzzle", "chigiri"])
def test_halves_fit_standard_parcel(base, style):
    p, tp = build(base, style)
    for h in tp.halves:
        x0, y0, x1, y1 = h.bounds
        assert max(x1 - x0, y1 - y0) + 50 <= p.shipping.std_max_side_in * INCH


@pytest.mark.parametrize("style", ["ari", "puzzle"])
def test_seam_interlocks(base, style):
    """Each half must reach across the seam line somewhere (otherwise it would pull apart)."""
    p, tp = build(base, style)
    xs = p.top.length / 2
    a, b = tp.halves
    assert a.bounds[2] > xs + 10 and b.bounds[0] < xs - 10
