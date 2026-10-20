import ezdxf

from kotatsu import build, export, params


def test_params_load():
    p = params.load()
    assert p.top.shape == "round" and p.top.length == p.top.width == 900
    assert [t.table_name for t in params.build_tables(p)] == ["yagura"]         # what gets cut
    assert {"slab", "yagura-splay"} <= {t.table_name for t in params.tables(p)}  # compare-only variants
    assert p.material.t_min < p.material.t_nominal < p.material.t_max


def test_top_dxf_roundtrip(tmp_path):
    p = params.load()
    poly = build.top(p)
    assert poly.is_valid
    minx, miny, maxx, maxy = poly.bounds
    assert abs((maxx - minx) - p.top.length) < 0.01 and abs((maxy - miny) - p.top.width) < 0.01
    f = export.write_dxf(tmp_path / "top.dxf", [("CUT", poly)])
    doc = ezdxf.readfile(f)
    assert doc.header["$INSUNITS"] == 4
    plines = list(doc.modelspace().query("LWPOLYLINE"))
    assert len(plines) == 1 and plines[0].closed
