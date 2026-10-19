import ezdxf

from kotatsu import build, export, params


def test_params_load():
    p = params.load()
    assert p.top.length == 1200 and p.top.width == 800
    assert p.material.t_min < p.material.t_nominal < p.material.t_max


def test_top_dxf_roundtrip(tmp_path):
    p = params.load()
    poly = build.top(p)
    assert poly.is_valid
    minx, miny, maxx, maxy = poly.bounds
    assert abs((maxx - minx) - 1200) < 0.01 and abs((maxy - miny) - 800) < 0.01
    f = export.write_dxf(tmp_path / "top.dxf", [("CUT", poly)])
    doc = ezdxf.readfile(f)
    assert doc.header["$INSUNITS"] == 4
    plines = list(doc.modelspace().query("LWPOLYLINE"))
    assert len(plines) == 1 and plines[0].closed
