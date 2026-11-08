"""The show top's quote pack: the DXF is the top's exact outline, in mm, one closed polyline."""
import ezdxf
from shapely.geometry import Polygon

from kotatsu import params, quote_pack, top

P = params.tables(params.load())[0]


def test_dxf_is_the_top(tmp_path):
    f = quote_pack.write_dxf(P, tmp_path / "t.dxf")
    doc = ezdxf.readfile(f)
    assert doc.header["$INSUNITS"] == 4
    ents = list(doc.modelspace())
    assert len(ents) == 1 and ents[0].dxftype() == "LWPOLYLINE" and ents[0].closed and ents[0].dxf.layer == "CUT"
    g = Polygon([(x, y) for x, y, *_ in ents[0].get_points()])
    t = top.build(P).outline
    assert abs(g.area - t.area) < 1e-6 * t.area
    x0, y0, x1, y1 = g.bounds
    assert abs(x0) < 1e-6 and abs(y0) < 1e-6                      # starts at the origin
    assert abs(x1 - x0 - P.top.length) < 0.05 and abs(y1 - y0 - P.top.width) < 0.05   # the squircle is sampled


def test_pack_writes_everything(tmp_path, monkeypatch):
    monkeypatch.setattr(quote_pack, "OUT", tmp_path)
    quote_pack.main()
    assert {f.name for f in tmp_path.iterdir()} == {"kotatsu-top.dxf", "kotatsu-top-drawing.pdf", "request.md"}
    text = (tmp_path / "request.md").read_text()
    assert f"{P.top.length:.0f} x {P.top.width:.0f} mm" in text
    for o in quote_pack.options(P):
        assert o["name"] in text and 5 <= o["kg"] <= 45         # the frame takes it (under 10 kg more a corner)
    assert "finger joints" in text and f"{P.top_quote.grit} grit" in text
