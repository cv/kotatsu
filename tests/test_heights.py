"""The 3-D view's height slider (kotatsu/heights.py)."""
from kotatsu import frame, heights, params

P = params.tables(params.load())[0]


def test_a_taller_frame_moves_everything_overhead_up():
    base, up = heights.clearances(P), heights.clearances(heights.variant(P, 50))
    for k in ("table surface", "top underside", "deck underside", "heater underside"):
        assert up[k] - base[k] == 50, k
    assert frame.layout(heights.variant(P, 50)).H == frame.layout(P).H + 50


def test_the_slider_covers_its_span_in_millimetres():
    o = heights.offsets()
    assert o[0] == -heights.SPAN and o[-1] == heights.SPAN and 0 in o and heights.STEP == 1


def test_both_ends_of_the_slider_build_and_far_beyond_is_reported():
    for dz in (-heights.SPAN, heights.SPAN):
        d = heights.export(P, dz)
        assert "error" not in d, (dz, d.get("error"))
        assert not d["frame"]["parts_delta"] or d["frame"]["parts"], "a height file carries the parts that changed"
    low = heights.export(P, -300)
    assert "error" in low and low["error"].startswith("too low")


def test_the_cache_key_skips_only_modules_the_variants_never_use():
    """Editing the page or the FEA mustn't flag the slider stale, but anything the variants use must."""
    import inspect, re
    from pathlib import Path
    from kotatsu import site
    root = Path(heights.__file__).parent
    used = {"heights", "compare", "scenes", "room", "clipping", "sleeper", "comfort", "frame", "yagura", "top",
            "geom", "params", "assembly"}
    for m in sorted(used):
        src = (root / f"{m}.py").read_text()
        for dep in re.findall(r"from \. import ([\w, ]+)|from \.(\w+) import", src):
            for name in ",".join(dep).replace(" ", "").split(","):
                if name == "site":                      # only frame_data and rings, hashed by source
                    assert set(re.findall(r"\bsite\.(\w+)\(", src)) <= {"frame_data", "rings"}, f"{m}.py uses more of site.py"
                    continue
                assert not name or f"{name}.py" not in heights.SKIP, f"{m}.py uses {name}.py, which the key skips"
    src = inspect.getsource(site.frame_data) + inspect.getsource(site.rings)
    for name in re.findall(r"\b([a-z_]+)\.[a-z_]+\(", src):
        assert f"{name}.py" not in heights.SKIP, f"site.frame_data uses {name}.py, which the key skips"
