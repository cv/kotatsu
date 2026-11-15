"""The 3-D view's height slider (kotatsu/heights.py)."""
from kotatsu import frame, heights, params

P = params.tables(params.load())[0]


def test_a_taller_frame_moves_everything_overhead_up():
    base, up = heights.clearances(P), heights.clearances(heights.variant(P, 50))
    for k in ("table surface", "top underside", "deck underside", "heater underside"):
        assert up[k] - base[k] == 50, k
    assert frame.layout(heights.variant(P, 50)).H == frame.layout(P).H + 50


def test_the_slider_covers_its_span_and_reports_what_it_cant_build():
    assert heights.offsets()[0] == -heights.SPAN and heights.offsets()[-1] == heights.SPAN and 0 in heights.offsets()
    low = heights.export(P, -heights.SPAN)
    assert "error" in low and low["error"].startswith("too low")
