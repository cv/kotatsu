from shapely.geometry import box

from kotatsu import geom

R = 3.175  # 1/4" bit


def test_square_inside_corner_is_not_cuttable():
    L = box(0, 0, 100, 100).difference(box(50, 50, 101, 101))
    assert not geom.router_cuttable(L, R)


def test_rounded_inside_corner_is_cuttable():
    L = box(0, 0, 100, 100).difference(box(50, 50, 101, 101))
    assert geom.router_cuttable(geom.closing(L, R), R)
