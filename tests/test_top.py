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
    for part in built.boards + built.keys:
        assert part.is_valid and part.geom_type == "Polygon"
        assert geom.router_cuttable(part, r), f"{built.name}: inside corner tighter than bit radius"


def test_no_overlap_and_full_coverage(built):
    parts = built.boards + built.keys
    for i, a in enumerate(parts):
        for b in parts[i + 1:]:
            assert a.intersection(b).area < 1e-6
    gap = built.outline.area - sum(x.area for x in parts)
    assert 0 <= gap < P.top.width * 1.0  # only clearance slivers


def test_boards_fit_standard_parcel(built):
    if built.name == "none":
        pytest.skip("single slab is an oversize parcel by design")
    for h in built.boards:
        x0, y0, x1, y1 = h.bounds
        assert max(x1 - x0, y1 - y0) + 50 <= P.shipping.std_max_side_in * INCH


def test_seam_resists_pulling_apart(built):
    """Sliding a board away from its left neighbour along x must collide (each seam locks)."""
    if built.kind in ("none", "chigiri"):
        pytest.skip("no interlocking seam")
    for k, (a, b) in enumerate(zip(built.boards, built.boards[1:])):
        for dx in (1.0, 5.0, 20.0):
            assert translate(b, dx).intersection(a).area > 1.0, f"{built.name} seam {k} pulls apart at {dx} mm"
            assert translate(a, -dx).intersection(b).area > 1.0


def test_board_count_and_seams(built):
    if built.name == "none":
        pytest.skip("single slab")
    assert len(built.boards) == P.top.boards
    assert len(built.seams) == P.top.boards - 1


def test_mirrored_middle_board_is_symmetric():
    if P.top.boards != 3 or not P.top.mirror:
        pytest.skip("only for 3 mirrored boards")
    from shapely.affinity import scale
    for o in P.top.options:
        t = top.build(P, o.name)
        mid = t.boards[1]
        flipped = scale(mid, -1, 1, origin=(P.top.length / 2, 0))
        # equal up to the seam clearance (each seam's gap is taken from its right-hand board)
        assert mid.hausdorff_distance(flipped) < 2 * P.fit.inplane_c + 0.5, o.name


def test_chigiri_keys_lock_boards():
    for o in P.top.options:
        if o.kind != "chigiri":
            continue
        t = top.build(P, o.name)
        for k in t.keys:
            assert all(k.intersection(b).area < 1e-6 for b in t.boards)
            assert any(k.bounds[0] < xs < k.bounds[2] for xs in t.seams)  # straddles a seam
