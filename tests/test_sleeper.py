"""The napper in the 3-D view (kotatsu/sleeper.py): an 80 kg, 180 cm adult on the shikibuton, legs under the table,
clear of the heater, the deck, the top and the table's legs."""
import math

import pytest
from shapely.affinity import translate
from shapely.geometry import Point, box

from kotatsu import comfort, frame, params, room, sleeper, yagura

P = params.tables(params.load())[0]
pytestmark = pytest.mark.skipif(P.room.seats != "set", reason="the napper lies on the seating set's shikibuton")
R = sleeper.pose(P)


def samples(q, n=12):
    if q["kind"] == "capsule":
        (ax, ay, az), (bx, by, bz) = q["a"], q["b"]
        for k in range(n + 1):
            t = k / n
            yield ax + t * (bx - ax), ay + t * (by - ay), az + t * (bz - az), q["r"], q["r"]
    else:                                                    # the ellipsoid's plan outline (and its centre)
        (x, y, z), (rx, ry, rz), yaw = q["c"], q["r"], q.get("yaw", 0.0)
        yield x, y, z, 0.0, rz
        for k in range(24):
            t = 2 * math.pi * k / 24
            u, v = rx * math.cos(t), ry * math.sin(t)
            yield x + u * math.cos(yaw) - v * math.sin(yaw), y + u * math.sin(yaw) + v * math.cos(yaw), z, 0.0, rz


def test_the_body_weighs_what_it_should():
    assert R["volume_l"] * 1.01 == pytest.approx(P.sleeper.mass, rel=0.03)
    xs = [v for q in R["parts"] for x, _, _, rp, _ in samples(q) for v in (x - rp, x + rp)]
    assert 1.0 * P.sleeper.height < max(xs) - min(xs) < 1.15 * P.sleeper.height   # head to pointed toes


def test_air_above_the_body_and_clear_of_the_legs():
    L = frame.layout(P)
    (hx, hy, hz), (cx, cy, cz) = frame.heater_box(P)
    heater = box(cx - L.cx - hx / 2, cy - L.cy - hy / 2, cx - L.cx + hx / 2, cy - L.cy + hy / 2)
    deck = translate(yagura.deck(P), -L.cx, -L.cy)
    for q in R["parts"]:
        for x, y, z, rp, rz in samples(q):
            top, at = z + rz, Point(x, y)
            if heater.distance(at) < rp:
                assert cz - hz / 2 - top >= 60, "the heater"
            if deck.distance(at) < rp:
                assert L.z_deck_bot - top >= 40, "the deck"
            if abs(x) < P.top.length / 2 and abs(y) < P.top.width / 2:
                assert L.H - top >= 40, "the top"
            assert comfort.low_footprint(P, top, 0.0).distance(at) - rp >= 30, "a table leg"


def test_the_hips_stay_out_from_under_the_heater_and_the_head_lies_on_the_mattress():
    (hx, _, _), _ = frame.heater_box(P)
    pelvis = R["parts"][0]
    assert pelvis["c"][0] + pelvis["r"][0] < -hx / 2                    # the hips are outside the heater
    (sh,) = [s for s in room.seats(P) if s["kind"] == "shikibuton"]
    end = sh["center"][0] + R["slide"] - sh["size"][0] / 2
    heads = [q for q in R["parts"] if q["mat"] in ("skin", "head") and q["kind"] == "ellipsoid"]
    assert all(q["c"][0] - max(q["r"]) > end for q in heads), "the head and hands lie on the slid mattress"
