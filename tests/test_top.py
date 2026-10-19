import pytest
from shapely.affinity import translate

from kotatsu import geom, params, top

P = params.load()
NAMES = [o.name for o in P.top.options]
INCH = 25.4


@pytest.fixture(scope="module", params=NAMES + ["none"])
def built(request):
    return top.build(P, request.param)


def test_split_refers_to_an_option():
    assert P.top.split in NAMES + ["none"]
    assert len(set(NAMES)) == len(NAMES)


def test_parts_valid_and_cuttable(built):
    r = P.cnc.bit_d / 2
    for part in built.halves + built.keys:
        assert part.is_valid and part.geom_type == "Polygon"
        assert geom.router_cuttable(part, r), f"{built.name}: inside corner tighter than bit radius"


def test_no_overlap_and_full_coverage(built):
    parts = built.halves + built.keys
    for i, a in enumerate(parts):
        for b in parts[i + 1:]:
            assert a.intersection(b).area < 1e-6
    gap = built.outline.area - sum(x.area for x in parts)
    assert 0 <= gap < P.top.width * 1.0  # only clearance slivers


def test_halves_fit_standard_parcel(built):
    if built.name == "none":
        pytest.skip("single slab is an oversize parcel by design")
    for h in built.halves:
        x0, y0, x1, y1 = h.bounds
        assert max(x1 - x0, y1 - y0) + 50 <= P.shipping.std_max_side_in * INCH


def test_seam_resists_pulling_apart(built):
    """Sliding half B away from A along x must collide (the seam locks in-plane)."""
    if built.kind in ("none", "chigiri"):
        pytest.skip("no interlocking seam")
    a, b = built.halves
    for dx in (1.0, 5.0, 20.0):
        assert translate(b, dx).intersection(a).area > 1.0, f"{built.name} pulls apart at {dx} mm"


def test_chigiri_keys_lock_halves():
    for o in P.top.options:
        if o.kind != "chigiri":
            continue
        t = top.build(P, o.name)
        a, b = t.halves
        for k in t.keys:
            assert k.intersection(a).area < 1e-6 and k.intersection(b).area < 1e-6
            assert k.bounds[0] < P.top.length / 2 < k.bounds[2]  # straddles the seam
