"""The 3-D view's scenes (kotatsu/scenes.py): the table in use. Every person's legs stay clear of the table's legs,
under the heater and the deck with air to spare; the cat fits under the heater; the zaisu sitter's knees stop
short of the heater ring."""
import math

import pytest
from shapely.affinity import translate
from shapely.geometry import Point, box

from kotatsu import comfort, frame, params, scenes, yagura

P = params.tables(params.load())[0]
pytestmark = pytest.mark.skipif(P.room.seats != "set", reason="the scenes use the seating set")
SC = scenes.scenes(P)
L = frame.layout(P)
(HX, HY, HZ), (HCX, HCY, HCZ) = frame.heater_box(P)
HEATER = box(HCX - L.cx - HX / 2, HCY - L.cy - HY / 2, HCX - L.cx + HX / 2, HCY - L.cy + HY / 2)
DECK = translate(yagura.deck(P), -L.cx, -L.cy)


def samples(q, n=12):
    if q["kind"] == "capsule":
        (ax, ay, az), (bx, by, bz) = q["a"], q["b"]
        for k in range(n + 1):
            t = k / n
            yield ax + t * (bx - ax), ay + t * (by - ay), az + t * (bz - az), q["r"], q["r"]
    else:
        (x, y, z), (rx, ry, rz), yaw = q["c"], q["r"], q.get("yaw", 0.0)
        yield x, y, z, 0.0, rz
        for k in range(24):
            t = 2 * math.pi * k / 24
            u, v = rx * math.cos(t), ry * math.sin(t)
            yield x + u * math.cos(yaw) - v * math.sin(yaw), y + u * math.sin(yaw) + v * math.cos(yaw), z, 0.0, rz


def test_every_scene_is_there():
    assert set(scenes.ORDER) == set(SC) and scenes.DEFAULT in SC
    assert len(SC["napping"]["people"]) == 2 and all(len(s["people"]) == 2 for s in SC.values())


@pytest.mark.parametrize("name", scenes.ORDER)
def test_legs_clear_the_table(name):
    for ps in SC[name]["people"]:
        for q in scenes.legs_of(ps):
            for x, y, z, rp, rz in samples(q):
                top, at = z + rz, Point(x, y)
                # crossed feet point sideways, about 12 mm from a corner leg's kicked foot: they mustn't touch
                assert comfort.low_footprint(P, top, 0.0).distance(at) - rp >= 5, f"{name}: a table leg"
                if HEATER.distance(at) < rp:
                    assert HCZ - HZ / 2 - top >= 40, f"{name}: under the heater"
                if DECK.distance(at) < rp:
                    assert L.z_deck_bot - top >= 10, f"{name}: under the deck"
                if abs(x) < P.top.length / 2 and abs(y) < P.top.width / 2:
                    assert L.H - top >= 10, f"{name}: under the top"


def test_the_cat_fits_under_the_heater():
    (cat,) = [q for q in SC["cards"]["props"] if q["kind"] == "cat_curled"]
    assert HEATER.distance(Point(cat["pos"][:2])) == 0, "it's under the heater, where it's warm"
    assert cat["pos"][2] + 185 <= HCZ - HZ / 2, "the curled cat (~185 mm high) fits under it"


def test_the_zaisu_sitter_stops_short_of_the_heater_ring():
    """Legs out on the zaisu: the knees stay out of the ring's reach (comfort.mid_side_opening from the edge)."""
    w = SC["working, legs out"]["people"][0]
    legs = [q for q in w if q["kind"] == "capsule" and q["mat"] == "pants"]
    knees = [legs[0]["b"], legs[2]["b"]]                     # hip -> knee, knee -> ankle, for each leg
    edge = P.top.length / 2
    for k in knees:
        assert abs(k[1]) >= edge - comfort.mid_side_opening(P), "the knees reach the heater ring"


def test_held_things_sit_in_the_hands():
    """Cards and books are between their holder's hands, a miso bowl on one; each a little above the hands."""
    import numpy as np
    from kotatsu import scenes
    S = scenes.scenes(P)
    for name, sc in S.items():
        for h in sc["held"]:
            near = []
            for ps in sc["people"]:
                try:
                    c = scenes.hands_of(ps)
                except ValueError:
                    continue                                 # the napper has no seated hands
                hs = [np.array(q["c"]) for q in ps if q["kind"] == "ellipsoid" and q["mat"] == "skin" and q["r"][2] < q["r"][1] * 0.6]
                for at in (c, *hs):                          # between both hands, or resting on one
                    near.append(float(np.linalg.norm(np.array(h["pos"][:2]) - at[:2])))
            assert near and min(near) < 1.0, f"{name}: the {h['kind']} isn't in anyone's hands"


def test_the_laptop_faces_the_zaisu():
    """The laptop's screen faces -y in the page's model, where the zaisu sits."""
    from kotatsu import scenes
    for name in ("working", "working, legs out"):
        sc = scenes.scenes(P)[name]
        (st,) = [q for q in sc["top"] if q["kind"] == "laptop_stand"]
        (z,) = [q for q in sc["props"] if q["kind"] == "zaisu"]
        assert st["yaw"] == 0.0 and z["pos"][1] < 0


def test_nothing_clips():
    """No hand or arm passes into a thing on the table or into the tabletop, and nobody into anybody else, by more
    than a touch (kotatsu/clipping.py samples every body part against props sized like the page draws them)."""
    from kotatsu import clipping
    bad = {k: [x for x in v if x[0] > 3.0] for k, v in clipping.overlaps(P).items()}
    assert not any(bad.values()), bad


def test_the_zaisu_sitter_leans_on_its_back():
    """In the working scenes the reclined backrest's face touches the sitter's back (within 4 mm, not into it), and
    the seat is under the hips."""
    import numpy as np
    from kotatsu import clipping
    for name in [n for n in scenes.ORDER if n.startswith("working")]:
        sc = SC[name]
        (z,) = [q for q in sc["props"] if q["kind"] == "zaisu"]
        w = sc["people"][0]
        pts = np.vstack([clipping.fill(q) for q in w if q["kind"] == "ellipsoid" and q["mat"] in ("top", "pants")])
        xs, y, zs = clipping.zaisu_back_local(z, pts)
        Z = scenes.ZAISU
        band = (np.abs(y) < Z["back_w"] / 2) & (np.abs(zs) < Z["back_h"] / 2)
        gap = float((xs[band] - Z["back_t"] / 2).min())
        assert -4.0 <= gap <= 4.0, f"{name}: the back is {gap:.0f} mm from the backrest"
        (pelvis,) = [q for q in w if q["kind"] == "ellipsoid" and q["mat"] == "pants"]
        assert abs(pelvis["c"][1] - z["pos"][1]) < 220.0, f"{name}: the hips are off the seat"
