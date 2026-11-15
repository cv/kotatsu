"""The 3-D view's v1 comparison (kotatsu/compare.py): v1 rebuilt from its own tag, and the clear-height map."""
import numpy as np
import pytest

from kotatsu import compare, frame, params

P = params.tables(params.load())[0]
D = compare.data(P)
pytestmark = pytest.mark.skipif(D is None, reason="no v1-ordered tag in this checkout")


def test_v1_is_v1():
    """The ghost is the ordered v1: '+' legs (plates A and B), an H deck, 18 mm stock, the frame 385 mm tall."""
    F1 = D["v1"]["frame"]
    names = {p["name"] for p in F1["parts"]}
    assert {"leg plate A", "leg plate B", "deck"} <= names
    assert F1["height"] == 385.0 and F1["thickness"] == 18.0


def test_the_map_reads_the_heights():
    """Under the top, away from legs, deck and heater, the difference is just the two tops' undersides."""
    L = frame.layout(P)
    n, c = D["n"], D["cell"]
    M = np.array(D["diff"]).reshape(n, n)
    F1 = D["v1"]["frame"]
    expect = (L.H + P.room.futon_gap) - (F1["height"] + F1.get("futon_gap", 0.0))
    # a point 40 mm in from the middle of a side: under both tops, outside both frames
    x, y = L.cx, L.cy - P.top.width / 2 + 40.0
    i, j = int(round((y - D["y0"]) / c)), int(round((x - D["x0"]) / c))
    assert abs(M[i, j] - expect) <= 1
    assert D["more"] > 0 and D["less"] > 0, "v2 gains room somewhere and loses it somewhere"
