"""Room fit: a square futon + 8 ft round rug around the square table (Futon & rug page)."""
from __future__ import annotations

import math
import tomllib

from . import comfort
from .params import ROOT

FUTONS = ROOT / "docs" / "futons.toml"


def footprint_d(p, futon_d: float) -> float:
    """Approximate floor footprint size (diameter, or side for a square futon) of a futon draped over the table.

    The futon covers the frame and is clamped by the top; from the top's edge it falls
    (frame height + top thickness) to the floor and the rest lies flat. Real futons are stiff and
    slope outward, so only part of the drop is "used" (drape_k)."""
    h = p.frame.height + p.material.t_nominal
    return max(p.top.length, futon_d - 2 * p.room.drape_k * h)


def futons(p) -> dict:
    d = tomllib.loads(FUTONS.read_text())
    rates = {"JPY": d.get("jpy_cad", 0.0), "USD": d.get("usd_cad", 1.0), "CAD": 1.0}
    out = []
    for f in d["futon"]:
        k = rates[f["currency"]]
        fd = f["size_cm"] * 10.0
        out.append({**f,
                    "price_cad": round(f["price"] * k), "ship_cad": round(f["ship"] * k),
                    "total_cad": round((f["price"] + f["ship"]) * k),
                    "footprint_d": round(footprint_d(p, fd)),
                    "rug_ring": round((p.room.rug_d - footprint_d(p, fd)) / 2)})
    return {"checked": d["checked"], "jpy_cad": rates["JPY"], "usd_cad": rates["USD"], "items": out}


def seat_offset(p) -> float:
    """Distance from the table's centre to each floor pillow's centre (one pillow per side).

    Each pillow tucks at least zabuton_tuck under the futon's floor edge, and further in if needed so that
    all of it, corners included, stays rug_margin inside the round rug."""
    R = p.room
    w, d = R.zabuton
    rho_out = footprint_d(p, R.futon_d) / 2
    c = rho_out - getattr(R, "zabuton_tuck", 50.0) + d / 2
    lim = (R.rug_d / 2 - getattr(R, "rug_margin", 0.0)) ** 2 - (w / 2) ** 2
    if lim > 0:
        c = min(c, math.sqrt(lim) - d / 2)
    return c


def room_data(p) -> dict:
    return {"rug_d": p.room.rug_d, "futon_d": p.room.futon_d, "top_d": p.top.length,
            "corner_r": getattr(p.top, "corner_r", 0.0),
            "frame": p.top.length - 2 * p.frame.overhang, "ear": p.frame.ear,
            "height": p.frame.height + p.material.t_nominal, "zabuton": list(p.room.zabuton),
            "seat_c": round(seat_offset(p), 1),
            "footprint_d": round(footprint_d(p, p.room.futon_d)), "futons": futons(p),
            "knees": comfort.summary(p)}


def _quarter_ellipse(a: float, b: float) -> float:
    """Length of a quarter ellipse with semi-axes a, b (Ramanujan)."""
    return math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b))) / 4


def drape_profile(p, futon_d: float):
    """The futon's cross-section from the table's centre outward, as a function of distance along the cloth.

    Flat on the frame under the top out to the top's edge, then a soft quarter-ellipse curve down to the
    floor (as wide as it needs to be for the cloth to reach footprint_d), then flat on the floor.
    Returns (map(s) -> (rho, z), rho_floor, rho_out)."""
    from . import frame
    H = frame.layout(p).H + 6.0                       # the cloth lies on the tenon tops, under the top
    r0 = p.top.length / 2
    half, rho_out = futon_d / 2, footprint_d(p, futon_d) / 2
    lo, hi = 1.0, 2000.0                              # find the curve's width: cloth used = what's left
    for _ in range(60):
        dw = (lo + hi) / 2
        used = r0 + _quarter_ellipse(dw, H) + (rho_out - r0 - dw)   # shrinks as the curve widens
        lo, hi = (lo, dw) if used < half else (dw, hi)
    dw = (lo + hi) / 2
    q = _quarter_ellipse(dw, H)

    def at(sv: float) -> tuple[float, float]:
        if sv <= r0:
            return sv, H
        if sv <= r0 + q:                              # arc length -> angle (fine-grained lookup)
            f = (sv - r0) / q
            th = f * math.pi / 2
            for _ in range(6):                        # refine: ellipse arc speed varies with angle
                n = 64
                ts = [th * k / n for k in range(n + 1)]
                ln = sum(math.hypot(dw * (math.sin(ts[k + 1]) - math.sin(ts[k])),
                                    H * (math.cos(ts[k + 1]) - math.cos(ts[k]))) for k in range(n))
                th *= (sv - r0) / ln if ln else 1
                th = min(th, math.pi / 2)
            return r0 + dw * math.sin(th), H * math.cos(th)
        return r0 + dw + (sv - r0 - q), 0.0
    return at, r0 + dw, rho_out


def _smooth(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def room3d(p, n: int = 81) -> dict:
    """World-space geometry for the 3-D view's room layers: the rug, the futon draped over the table
    (a grid of n x n points, square or round), and one floor pillow per side.

    Where the futon's floor edge meets a pillow it rides up over it, easing onto the pillow's top over
    zabuton_ramp mm (a picture, not a cloth simulation: the drape itself is drape_profile's)."""
    from . import frame
    L = frame.layout(p)
    cx, cy = L.cx, L.cy
    R = p.room
    fd = R.futon_d
    at, rho_floor, rho_out = drape_profile(p, fd)
    half = fd / 2
    w, d = R.zabuton
    h = getattr(R, "zabuton_h", 90.0)
    c = seat_offset(p)                                         # pillow centre distance from the table centre
    seats = [{"center": [cx + ux * c, cy + uy * c, h / 2], "size": [w if uy else d, d if uy else w, h]}
             for ux, uy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
    ramp = getattr(R, "zabuton_ramp", 80.0)

    def over_seats(x: float, y: float) -> float:
        """Height the cloth must clear at (x, y): each pillow's top, easing down to the floor around it."""
        top = 0.0
        for st in seats:
            (sx, sy, _), (sw, sd, sh) = st["center"], st["size"]
            dx, dy = max(0.0, abs(x - sx) - sw / 2), max(0.0, abs(y - sy) - sd / 2)
            top = max(top, sh * _smooth(1 - math.hypot(dx, dy) / ramp))
        return top

    pts = []
    for j in range(n):
        for i in range(n):
            a, b = -half + fd * i / (n - 1), -half + fd * j / (n - 1)
            r = max(abs(a), abs(b))                           # square cloth: rings are squares
            rho, z = at(r)
            k = rho / r if r > 1e-9 else 1.0
            x, y = cx + a * k, cy + b * k
            z = max(z, over_seats(x, y) + 4.0)                 # lies on the rug (and the pillows), not in them
            pts += [round(x, 1), round(y, 1), round(z, 1)]
    return {"rug": {"center": [cx, cy], "d": R.rug_d, "t": getattr(R, "rug_t", 10.0)},
            "futon": {"n": n, "pts": pts, "size": fd},
            "seats": seats}
