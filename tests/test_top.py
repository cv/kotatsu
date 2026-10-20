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


def test_boards_have_no_holes_or_islands(built):
    """A hole in a board means some feature broke off (pinched below the bit width) and was dropped."""
    for b in built.boards:
        assert len(b.interiors) == 0, f"{built.name}: board has {len(b.interiors)} hole(s)"


def test_no_overlap_and_full_coverage(built):
    parts = built.boards + built.keys
    for i, a in enumerate(parts):
        for b in parts[i + 1:]:
            assert a.intersection(b).area < 1e-6
    gap = built.outline.area - sum(x.area for x in parts)
    # only clearance slivers: ~2c wide along every seam (seam length from the part perimeters)
    seam_len = (sum(x.exterior.length + sum(h.length for h in x.interiors) for x in parts) - built.outline.exterior.length) / 2
    assert 0 <= gap < 2 * P.fit.inplane_c * seam_len * 1.5 + 50


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
        if not getattr(o, "mirror", P.top.mirror):
            continue  # option opts out of mirroring (e.g. salmon all swimming one way)
        t = top.build(P, o.name)
        mid = t.boards[1]
        flipped = scale(mid, -1, 1, origin=(P.top.length / 2, 0))
        # equal up to the seam clearance (each seam's gap is taken from its right-hand board)
        assert mid.hausdorff_distance(flipped) < 2 * P.fit.inplane_c + 0.75, o.name  # + male/female rounding


def test_chigiri_keys_lock_boards():
    for o in P.top.options:
        if o.kind != "chigiri":
            continue
        t = top.build(P, o.name)
        for k in t.keys:
            assert all(k.intersection(b).area < 1e-6 for b in t.boards)
            assert any(k.bounds[0] < xs < k.bounds[2] for xs in t.seams)  # straddles a seam


def test_round_top_is_one_piece_and_ships():
    R = params.table(P, "round")
    t = top.build(R)
    assert len(t.boards) == 1 and not t.keys
    b = t.boards[0]
    assert b.is_valid and len(b.interiors) == 0
    d = R.top.length
    assert abs(b.area - 3.14159265 * (d / 2) ** 2) / b.area < 0.002
    assert d + 50 <= P.shipping.std_max_side_in * INCH


@pytest.mark.parametrize("name", ["maple-3-updown", "maple-5-updown"])
def test_maple_updown_is_rotationally_symmetric(name):
    """One row tips up, the other tips down: the middle board reads the same turned 180°,
    and the two outer boards are the same shape (only the fit clearance differs)."""
    from shapely.affinity import rotate
    p = params.table(params.load(), "rect")
    b = top.build(p, name).boards
    c = (p.top.length / 2, p.top.width / 2)
    per = b[1].length
    assert rotate(b[1], 180, origin=c).symmetric_difference(b[1]).area < 0.5 * per
    assert rotate(b[0], 180, origin=c).symmetric_difference(b[2]).area < 0.5 * b[0].length
