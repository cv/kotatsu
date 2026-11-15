"""Room fit: a square futon + 8 ft round rug around the square table (Futon & rug page)."""
from __future__ import annotations

import math
import tomllib

from . import comfort
from .params import ROOT

FUTONS = ROOT / "docs" / "futons.toml"
PLAN_SIZES = (1900.0, 2050.0, 2250.0, 2290.0)     # futon sizes (mm) the room plan offers as buttons, with spread_d


def footprint_d(p, futon_d: float) -> float:
    """Approximate floor footprint size (diameter, or side for a square futon) of a futon draped over the table.

    The futon covers the frame and is clamped by the top; from the top's edge it falls
    (frame height + top thickness) to the floor and the rest lies flat. Real futons are stiff and
    slope outward, so only part of the drop is "used" (drape_k)."""
    h = p.frame.height + p.material.t_nominal
    return max(p.top.length, futon_d - 2 * p.room.drape_k * h)


def spread_d(p) -> float:
    """How big the futon drapes: room.futon_spread_d if set (owner 2026-11: the quilt is folded and tucked in),
    else its real size."""
    return p.room.futon_spread_d or p.room.futon_d


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


def seat_offset(p, size: tuple[float, float] | None = None) -> float:
    """Distance from the table's centre to a floor pillow's centre (one pillow per side), for a pillow
    `size` (w along the table's side, d outwards; default the zabuton).

    Each pillow tucks at least zabuton_tuck under the futon's floor edge, and further in if needed so that
    all of it, corners included, stays rug_margin inside the round rug."""
    R = p.room
    w, d = size or R.zabuton
    rho_out = footprint_d(p, spread_d(p)) / 2
    c = rho_out - R.zabuton_tuck + d / 2
    lim = (R.rug_d / 2 - R.rug_margin) ** 2 - (w / 2) ** 2
    if lim > 0:
        c = min(c, math.sqrt(lim) - d / 2)
    return c


def seats(p) -> list[dict]:
    """The floor seating, centred on the table, as boxes: [{kind, center [x, y, z], size [along x, along y, h]}].
    room.seats = "zabuton": a square pillow on each side. "set": one long shikibuton through the legs along x, and
    a square cushion on each of the other two sides (y)."""
    R = p.room
    if getattr(R, "seats", "zabuton") == "set":
        (sw, sl), sh = R.shikibuton, R.shikibuton_h
        (cw, cd), ch = R.cushion, R.cushion_h
        c = seat_offset(p, (cw, cd))
        return ([{"kind": "shikibuton", "center": [0.0, 0.0, sh / 2], "size": [sl, sw, sh]}] +
                [{"kind": "cushion", "center": [0.0, s * c, ch / 2], "size": [cw, cd, ch]} for s in (1, -1)])
    w, d = R.zabuton
    h, c = R.zabuton_h, seat_offset(p)
    return [{"kind": "zabuton", "center": [ux * c, uy * c, h / 2], "size": [w if uy else d, d if uy else w, h]}
            for ux, uy in ((1, 0), (-1, 0), (0, 1), (0, -1))]


def top_outline(p, tol: float = 0.5) -> list[list[float]]:
    """The top's outline, centred, as [x, y] points (to within tol mm) for the site's plan views."""
    from . import top
    g = top.build(p).outline.simplify(tol)
    return [[round(x - p.top.length / 2, 1), round(y - p.top.width / 2, 1)] for x, y in g.exterior.coords[:-1]]



def frame_plan(p) -> list[list[list[float]]]:
    """The frame in plan, centred, for the room plan: the deck's outline and the legs' footprints, as rings of [x, y]."""
    from shapely.affinity import translate
    from . import frame, yagura
    deck = translate(yagura.deck(p), -p.top.length / 2, -p.top.width / 2)
    legs = comfort.low_footprint(p, frame.layout(p).H + 1)
    return [[[round(x, 1), round(y, 1)] for x, y in g.simplify(0.5).exterior.coords[:-1]]
            for g in [deck, *getattr(legs, "geoms", [legs])]]


def room_data(p) -> dict:
    sizes = sorted({*PLAN_SIZES, spread_d(p)})
    return {"rug_d": p.room.rug_d, "futon_d": p.room.futon_d, "top_d": p.top.length,
            "top_outline": top_outline(p), "frame_plan": frame_plan(p),
            "frame": p.top.length - 2 * p.frame.overhang, "ear": p.frame.ear,
            "height": p.frame.height + p.material.t_nominal, "zabuton": list(p.room.zabuton),
            "seat_c": round(seat_offset(p), 1),
            "seats_plan": [{"kind": s["kind"], "center": s["center"][:2], "size": s["size"][:2]} for s in seats(p)],
            "spread_d": spread_d(p), "footprint_d": round(footprint_d(p, spread_d(p))), "futons": futons(p),
            "plan_sizes": [[s, round(footprint_d(p, s))] for s in sizes],
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


def _boxes(parts: list[dict], cx: float, cy: float) -> list[dict]:
    """Each body part's box, in world coordinates, for the drape to clear."""
    out = []
    for q in parts:
        if q["kind"] == "capsule":
            (ax, ay, az), (bx, by, bz), r = q["a"], q["b"], q["r"]
            lo, hi = (min(ax, bx) - r, min(ay, by) - r), (max(ax, bx) + r, max(ay, by) + r, max(az, bz) + r)
        else:
            (qx, qy, qz), (rx, ry, rz) = q["c"], q["r"]
            rr = max(rx, ry)
            lo, hi = (qx - rr, qy - rr), (qx + rr, qy + rr, qz + rz)
        out.append({"center": [cx + (lo[0] + hi[0]) / 2, cy + (lo[1] + hi[1]) / 2, hi[2] / 2],
                    "size": [hi[0] - lo[0], hi[1] - lo[1], hi[2]]})
    return out


def drape(p, clear_of: list[dict], n: int = 61) -> dict:
    """The futon draped over the table (a grid of n x n points, square cloth), riding up over every box in clear_of
    (world coordinates) and easing back down over zabuton_ramp mm (a picture, not a cloth simulation: the drape
    itself is drape_profile's)."""
    from . import frame
    L = frame.layout(p)
    cx, cy = L.cx, L.cy
    fd = spread_d(p)                                           # folded and tucked: how far it really spreads
    at, _, rho_out = drape_profile(p, fd)
    half, ramp = fd / 2, p.room.zabuton_ramp

    def over(x: float, y: float) -> float:
        top = 0.0
        for st in clear_of:
            (sx, sy, sz), (sw, sd, sh) = st["center"], st["size"]
            dx, dy = max(0.0, abs(x - sx) - sw / 2), max(0.0, abs(y - sy) - sd / 2)
            top = max(top, (sz + sh / 2) * _smooth(1 - math.hypot(dx, dy) / ramp))
        return top

    pts = []
    for j in range(n):
        for i in range(n):
            a, b = -half + fd * i / (n - 1), -half + fd * j / (n - 1)
            r = max(abs(a), abs(b))                           # square cloth: rings are squares
            rho, z = at(r)
            k = rho / r if r > 1e-9 else 1.0
            x, y = cx + a * k, cy + b * k
            z = max(z, over(x, y) + 4.0)                       # lies on the rug, the seats and the people, not in them
            pts += [round(x, 1), round(y, 1), round(z, 1)]
    return {"n": n, "pts": pts, "size": fd}


def _cloth_z(f: dict, x: float, y: float, r: float = 80.0) -> float:
    """The draped cloth's height near (x, y), world coordinates (the highest point within r)."""
    pts = f["pts"]
    zs = [pts[k + 2] for k in range(0, len(pts), 3) if math.hypot(pts[k] - x, pts[k + 1] - y) <= r]
    return max(zs) if zs else 0.0


def scene_cloth(p, S: dict, n: int = 61):
    """One scene's quilt (room.drape over its seats and the people's legs) and its height as a function of centred
    (x, y): the highest cloth point within 60 mm."""
    import numpy as np
    from . import frame
    L = frame.layout(p)
    cx, cy = L.cx, L.cy
    seats_ = [{**s, "center": [cx + s["center"][0], cy + s["center"][1], s["center"][2]]} for s in seats(p)]
    clear_of = [st for k, st in enumerate(seats_) if k not in S["hide_seats"]]
    clear_of = [{**st, "center": [st["center"][0] + (S["seat_slide"] if st["kind"] == "shikibuton" else 0.0), *st["center"][1:]]}
                for st in clear_of]
    clear_of += _boxes(S["drape_over"], cx, cy)
    f = drape(p, clear_of, n)
    P = np.array(f["pts"]).reshape(-1, 3)

    def cloth(x: float, y: float, r: float = 60.0) -> float:
        d = np.hypot(P[:, 0] - (x + cx), P[:, 1] - (y + cy))
        m = d <= r
        return float(P[m, 2].max()) if m.any() else 0.0
    return f, cloth


def room3d(p, n: int = 61) -> dict:
    """World-space geometry for the 3-D view's room layers: the rug, the seats, and for every scene (kotatsu/scenes.py)
    its people, props and the futon draped over the table, the seats and the people's legs."""
    from . import frame
    L = frame.layout(p)
    cx, cy = L.cx, L.cy
    R = p.room
    seats_ = [{**s, "center": [cx + s["center"][0], cy + s["center"][1], s["center"][2]]} for s in seats(p)]
    out = {"rug": {"center": [cx, cy], "d": R.rug_d, "t": R.rug_t}, "seats": seats_}
    if getattr(R, "seats", "zabuton") != "set" or not hasattr(p, "sleeper"):
        out["futon"] = drape(p, seats_, n)
        return out
    from . import scenes as sc
    W = lambda v: [round(v[0] + cx, 1), round(v[1] + cy, 1), *([round(v[2], 1)] if len(v) > 2 else [])]
    out["scenes"], out["scene_order"], out["scene_default"] = {}, sc.ORDER, sc.DEFAULT
    for name, S in sc.scenes(p).items():
        f, cloth = scene_cloth(p, S, n)
        props = []
        for q in S["props"]:
            if q["kind"] == "cat_reach":                       # stands on the quilt, clear of it and of the top
                q = sc.place_cat(p, q, cloth)
                q = {k: v for k, v in q.items() if k != "parts"}
            q = {**q, "pos": W(q["pos"])}
            if q.pop("on_cloth", False):                       # stands on the quilt
                q["pos"][2] = max(q["pos"][2], _cloth_z(f, q["pos"][0], q["pos"][1]) - 2.0)
            props.append(q)
        out["scenes"][name] = {"futon": f, "seat_slide": S["seat_slide"], "hide_seats": S["hide_seats"],
                               "people": [[_shift(q, cx, cy) for q in ps] for ps in S["people"]],
                               "props": props, "held": [{**q, "pos": W(q["pos"])} for q in S["held"]],
                               "top": [{**q, "pos": W(q["pos"])} for q in S["top"]]}
    out["futon"] = drape(p, seats_, n)                         # nobody there (the ambiance layer off): over the seats only
    out["sleeper"] = {"slide": out["scenes"]["napping"]["seat_slide"], "parts": out["scenes"]["napping"]["people"][0]}
    return out


def _shift(q: dict, dx: float, dy: float) -> dict:
    """A sleeper part moved from centred to world coordinates, rounded for the page."""
    r = lambda v: [round(v[0] + dx, 1), round(v[1] + dy, 1), round(v[2], 1)]
    if q["kind"] == "capsule":
        return {**q, "a": r(q["a"]), "b": r(q["b"]), "r": round(q["r"], 1)}
    return {**q, "c": r(q["c"]), "r": [round(v, 1) for v in q["r"]], "yaw": round(q["yaw"], 4)}
