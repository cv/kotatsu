"""Nesting must be exact: every part placed once per copy, inside the sheet margin, at least the
cutting gap from its neighbours, and only in the rotations its grain allows."""
import ezdxf
import pytest
from shapely.strtree import STRtree

from kotatsu import cutlist, export, nest, params

P = params.load()
PARTS = cutlist.cut_list(P)
NESTS = nest.nest_all(P, PARTS)


@pytest.fixture(params=list(NESTS), scope="module")
def n(request):
    return NESTS[request.param]


def test_everything_placed(n):
    assert not n.unplaced
    want = {c.name: c.qty for c in PARTS}
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
    allowed = {c.name: c.rotations for c in PARTS}
    for s in n.sheets:
        for pl in s.placed:
            assert pl.angle in allowed[pl.name]


def test_placed_shapes_are_the_parts(n):
    """Placement is a pure rotation + translation of the cut-list shape (same area, same holes)."""
    src = {c.name: c.shape for c in PARTS}
    for s in n.sheets:
        for pl in s.placed:
            assert pl.shape.area == pytest.approx(src[pl.name].area, rel=1e-9)
            assert len(pl.shape.interiors) == len(src[pl.name].interiors)


def test_best_layouts():
    """Regression guard for the current design (update when the design changes on purpose)."""
    counts = {k: len(v.sheets) for k, v in NESTS.items()}
    assert counts["60x120in"] == 1
    assert counts["48x96in"] <= 2
    assert counts["60x60in"] <= 2


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
