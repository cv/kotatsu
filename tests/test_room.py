"""Room layers for the 3-D view: the draped futon keeps its cloth length, and the pillows stay clear of the legs."""
import math

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
    for s in d["seats"]:                                     # pillows sit outside the frame, on the floor
        (x, y, z), (w, dd, h) = s["center"], s["size"]
        assert abs(z - h / 2) < 1e-6
        assert max(abs(x - L.cx) - w / 2, abs(y - L.cy) - dd / 2) > L.Lf / 2
        assert (w, dd) == tuple(p.room.zabuton)


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
        inner = max(abs(x - L.cx) - w / 2, abs(y - L.cy) - dd / 2)
        assert rho_out - inner >= p.room.zabuton_tuck - 1e-6     # at least the minimum tuck under the futon
