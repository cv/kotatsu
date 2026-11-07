"""The FEA heat maps' data (kotatsu/fea_view.py): consistent arrays, smoothing that never overstates the
peak, and loads drawn where they press. Only the top's cases: they are quick."""
import numpy as np

from kotatsu import fea_view, params

P = params.tables(params.load())[0]


def test_top_cases_data():
    fea_view.MESHES.clear()
    cases = fea_view.top_cases(P)
    assert len(cases) >= 5
    for c in cases:
        me = fea_view.MESHES[c["mesh"]]
        nv = len(me["xy"]) // 2
        assert len(me["tri"]) % 3 == 0 and max(me["tri"]) < nv
        assert len(c["util"]) == nv and len(c["local"]) == nv and len(c["disp"]) == nv     # plates: w per vertex
        keep = ~np.array(c["local"], bool)
        assert max(np.array(c["util"])[keep]) <= c["worst"] + 1e-3      # vertex means can't exceed the element peak
        assert 0 < c["worst"] < 1.0 and c["sag_mm"] > 0
        xs, ys = np.array(me["xy"][0::2]), np.array(me["xy"][1::2])
        for ring in c["loads"]:                                          # in the top's own frame, on the top
            for x, y in ring:
                assert xs.min() - 1 <= x <= xs.max() + 1 and ys.min() - 1 <= y <= ys.max() + 1


def test_key_tracks_the_sources():
    assert len(fea_view.key()) == 12
    assert "zaisu" in fea_view.IGNORED            # changing the chairs doesn't make the table's results stale
    assert not any(s in fea_view.IGNORED for s in ("material", "loads", "fea", "frame", "yagura", "deck", "top"))
