import pytest
from shapely.affinity import scale, translate
from shapely.geometry import box

from kotatsu import geom

R = 3.175  # 1/4" bit


def test_square_inside_corner_is_not_cuttable():
    L = box(0, 0, 100, 100).difference(box(50, 50, 101, 101))
    assert not geom.router_cuttable(L, R)


def test_rounded_inside_corner_is_cuttable():
    L = box(0, 0, 100, 100).difference(box(50, 50, 101, 101))
    assert geom.router_cuttable(geom.closing(L, R), R)



def test_squircle():
    """Closed, symmetric, between the inscribed circle and the box, squarer as n grows; no inside corners."""
    a = [geom.squircle(0, 0, 860, 860, n) for n in (4, 10)]
    for s in a:
        assert s.is_valid and s.geom_type == "Polygon"
        assert s.bounds == pytest.approx((0, 0, 860, 860), abs=0.05)
        assert 0.785 * 860 ** 2 < s.area < 860 ** 2
        assert s.convex_hull.area - s.area < 1.0                    # convex: nothing for the bit to miss
        flip = translate(scale(s, -1, 1, origin=(430, 430)), 0, 0)
        assert s.hausdorff_distance(flip) < 0.1                     # mirror image within 0.1 mm
    assert a[0].area < a[1].area