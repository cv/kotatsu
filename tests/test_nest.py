"""Nesting must be exact: every part placed once per copy, inside the sheet margin, at least the
cutting gap from its neighbours, and only in the rotations its grain allows."""
import ezdxf
import pytest
from shapely.strtree import STRtree

from kotatsu import build, cutlist, export, nest, params

P = params.load()
LAYOUTS = build.cached_layouts(P)          # same cache the build uses (keyed on source hash)
CASES = [(k, name) for k, opts in LAYOUTS.items() for name in opts]
PARTS = {k: cutlist.cut_list_all(P, copies=k) for k in LAYOUTS}
PARTS1 = PARTS[min(PARTS)]


@pytest.fixture(params=CASES, ids=[f"{k}t-{nm}" for k, nm in CASES], scope="module")
def case(request):
    k, name = request.param
    return k, LAYOUTS[k][name]


@pytest.fixture
def n(case):
    return case[1]


def test_everything_placed(case):
    k, n = case
    assert not n.unplaced
    want = {c.name: c.qty for c in PARTS[k]}
    got = {}
    for s in n.sheets:
        for pl in s.placed:
            got[pl.name] = got.get(pl.name, 0) + 1
    assert got == want


def test_inside_margin(n):
    m = n.margin - 0.01
    for s in n.sheets:
        for pl in s.placed:
            x0, y0, x1, y1 = pl.shape.bounds
            assert x0 >= m and y0 >= m and x1 <= s.w - m and y1 <= s.h - m, pl.name


def test_gap_between_parts(n):
    for s in n.sheets:
        geoms = [pl.shape for pl in s.placed]
        tree = STRtree(geoms)
        for i, g in enumerate(geoms):
            for j in tree.query(g.buffer(n.gap)):
                if j > i:
                    assert g.distance(geoms[j]) >= n.gap - 0.01, (s.placed[i].name, s.placed[j].name)


def test_gap_fits_the_bit():
    assert nest.effective_gap(P) >= P.cnc.bit_d + 0.5 and nest.effective_gap(P) >= P.cnc.part_gap


def test_rotations_respect_grain(n):
    allowed = {c.name: c.rotations for c in PARTS1}
    for s in n.sheets:
        for pl in s.placed:
            assert pl.angle in allowed[pl.name]


def test_placed_shapes_are_the_parts(n):
    """Placement is a pure rotation + translation of the cut-list shape (same area, same holes)."""
    src = {c.name: c.shape for c in PARTS1}
    for s in n.sheets:
        for pl in s.placed:
            assert pl.shape.area == pytest.approx(src[pl.name].area, rel=1e-9)
            assert len(pl.shape.interiors) == len(src[pl.name].interiors)


def test_best_mix_is_least_material():
    for k, opts in LAYOUTS.items():
        assert "best mix" in opts
        best = nest.material_m2(opts["best mix"])
        assert all(best <= nest.material_m2(n) + 1e-6 for n in opts.values())


def test_both_tables_layout():
    """Regression guard for the current design (update when the design changes on purpose)."""
    one = LAYOUTS[1]["best mix"]
    assert nest.material_m2(one) <= 7.7
    assert nest.utilisation(one) >= 0.45


def test_sheet_dxf_roundtrip(n, tmp_path):
    """Every ring becomes one closed polyline, in mm, inside the sheet; ezdxf's audit finds nothing."""
    for i, s in enumerate(n.sheets):
        f = export.write_dxf(tmp_path / f"s{i}.dxf", [("CUT", pl.shape) for pl in s.placed])
        doc = ezdxf.readfile(f)
        assert doc.header["$INSUNITS"] == 4
        assert not doc.audit().has_errors
        pls = list(doc.modelspace().query("LWPOLYLINE"))
        assert len(pls) == sum(1 + len(pl.shape.interiors) for pl in s.placed)
        for e in pls:
            assert e.closed and e.dxf.layer == "CUT"
            xs, ys = zip(*[(x, y) for x, y, *_ in e.get_points()])
            assert min(xs) >= 0 and max(xs) <= s.w and min(ys) >= 0 and max(ys) <= s.h


def test_interlocked_pair_saves_sheet_area():
    """A long side + a short side, one upside down with a leg in the other's opening, need much less
    rectangle than the two side by side, and stay a full bit-gap apart."""
    parts = {c.name: c for c in cutlist.cut_list(params.tables(P)[0])}
    a, b = parts["long side"], parts["short side"]
    j = nest._pair_job(a, b, nest.effective_gap(P) + 0.5)
    x0, y0, x1, y1 = j.shape.bounds
    sep = (a.shape.bounds[2] * a.shape.bounds[3]) + (b.shape.bounds[2] * b.shape.bounds[3])
    assert (x1 - x0) * (y1 - y0) < 0.8 * sep
    (_, am, _), (_, bm, rot) = j.members
    assert am.distance(bm) >= nest.effective_gap(P) and rot == 180
    assert am.area == pytest.approx(a.shape.area) and bm.area == pytest.approx(b.shape.area)
