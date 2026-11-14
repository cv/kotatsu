"""Room layers for the 3-D view: the draped futon keeps its cloth length, and the pillows stay clear of the legs."""
import math

import pytest

from kotatsu import frame, params, room


def P():
    return params.tables(params.load())[0]


def test_drape_uses_the_whole_cloth_and_reaches_the_floor():
    p = P()
    at, rho_floor, rho_out = room.drape_profile(p, p.room.futon_d)
    half = p.room.futon_d / 2
    pts = [at(half * k / 400) for k in range(401)]
    length = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
    assert abs(length - half) < 0.02 * half                 # the cloth isn't stretched or shrunk
    assert pts[0][1] > frame.layout(p).H and pts[-1][1] == 0.0
    assert abs(pts[-1][0] - rho_out) < 5                     # its edge lands where the Futon & rug page says
    assert all(b[0] >= a[0] - 1e-6 for a, b in zip(pts, pts[1:]))   # it only ever moves outward


def test_room3d_layers():
    p = P()
    d = room.room3d(p)
    n = d["futon"]["n"]
    assert len(d["futon"]["pts"]) == 3 * n * n
    zs = d["futon"]["pts"][2::3]
    assert min(zs) >= 4.0 - 1e-9 and max(zs) <= frame.layout(p).H + 10
    L = frame.layout(p)
    R = p.room
    for s in d["seats"]:                                     # on the floor; pillows and cushions outside the frame
        (x, y, z), (w, dd, h) = s["center"], s["size"]
        assert abs(z - h / 2) < 1e-6
        if s["kind"] == "shikibuton":                        # runs under the table, along x
            assert (dd, w, h) == (*R.shikibuton, R.shikibuton_h) and abs(y - L.cy) < 1e-6
            continue
        assert max(abs(x - L.cx) - w / 2, abs(y - L.cy) - dd / 2) > L.Lf / 2
        want = tuple(R.cushion) if s["kind"] == "cushion" else tuple(R.zabuton)
        assert sorted((w, dd)) == sorted(want)


def test_pillows_fit_inside_the_rug_and_tuck_under_the_futon():
    p = P()
    d = room.room3d(p)
    L = frame.layout(p)
    rim = p.room.rug_d / 2 - p.room.rug_margin
    rho_out = room.footprint_d(p, p.room.futon_d) / 2
    for s in d["seats"]:
        (x, y, _), (w, dd, _) = s["center"], s["size"]
        for sx in (-1, 1):
            for sy in (-1, 1):
                assert math.hypot(x + sx * w / 2 - L.cx, y + sy * dd / 2 - L.cy) <= rim + 1e-6
        if s["kind"] == "shikibuton":
            continue
        inner = max(abs(x - L.cx) - w / 2, abs(y - L.cy) - dd / 2)
        assert rho_out - inner >= p.room.zabuton_tuck - 1e-6     # at least the minimum tuck under the futon


def test_room_plan_draws_the_current_frame():
    """The Futon & rug page draws the deck and the four (kicked) legs from Python and looks up every futon size it
    offers in room.footprint_d (the page computes nothing); the floor pillows stay clear of the legs' feet."""
    from shapely.geometry import Polygon, box
    from kotatsu import comfort, yagura
    p = P()
    d = room.room_data(p)
    rings = d["frame_plan"]
    assert len(rings) == 1 + len(yagura.corners(p))
    assert Polygon(rings[0]).area == pytest.approx(Polygon(yagura.deck(p).exterior).area, rel=0.01)
    sizes = dict(d["plan_sizes"])
    assert d["spread_d"] in sizes and all(f == round(room.footprint_d(p, s)) for s, f in sizes.items())
    L = frame.layout(p)
    legs = comfort.low_footprint(p, L.H + 1)
    for s in room.room3d(p)["seats"]:
        if s["kind"] == "shikibuton":                        # under the table by design: see the test below
            continue
        (x, y, _), (w, dd, _) = s["center"], s["size"]
        assert box(x - L.cx - w / 2, y - L.cy - dd / 2, x - L.cx + w / 2, y - L.cy + dd / 2).distance(legs) > 0


def test_the_shikibuton_slides_between_the_legs():
    """The set's long mattress (room.seats = "set") passes under the table between two legs on each side, with at
    least 20 mm to spare at every height up to its top (the kicked feet splay out, so the tightest is at the top)."""
    from shapely.geometry import box
    from kotatsu import comfort
    p = P()
    if p.room.seats != "set":
        pytest.skip("the four-pillow layout")
    (s,) = [x for x in room.seats(p) if x["kind"] == "shikibuton"]
    (_, _, z), (l, w, h) = s["center"], s["size"]
    for zz in (20.0, h / 2, h):
        legs = comfort.low_footprint(p, zz, 0.0)
        assert box(-l / 2, -w / 2, l / 2, w / 2).distance(legs) >= 20.0, f"at {zz:.0f} mm"
