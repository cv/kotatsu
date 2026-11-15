"""Clipping checks for the 3-D scenes (kotatsu/scenes.py).

Every body part (the capsules and ellipsoids scenes.py hands the page) is filled with points on a grid, and each
point is tested against the solids it mustn't enter: the tabletop, the deck, the heater, the table's legs, the
things on the table (sized as web/ambiance.js draws them), the zaisu's backrest, and the other people. A seated
person's hips sinking into a cushion is normal and isn't checked.

overlaps(p) -> {scene: [(depth mm, what, into), ...]}, deepest first.
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
from shapely import contains_xy
from shapely.affinity import rotate, translate
from shapely.geometry import Point, box

from . import frame, scenes, top as T

# footprints (half-sizes or radius, mm) and heights above the tabletop, as web/ambiance.js draws them
PROP = {"sushi": ("box", 190, 95, 68), "plate": ("circle", 85, 0, 14), "chopsticks": ("box", 120, 15, 10),
        "kyusu": ("circle", 75, 0, 95), "yunomi": ("circle", 36, 0, 70), "keyboard": ("box", 220, 65, 20),
        "mouse": ("circle", 35, 0, 30), "card_pile": ("circle", 70, 0, 14), "laptop_stand": ("box", 140, 125, 330)}
STEP = 6.0       # grid spacing for the points inside each body part (mm)
SINK = 25.0      # how far a body may sink into a squashed seat (hips, a heel) before it counts as clipping


def prop_shape(q):
    kind, a, b, h = PROP[q["kind"]]
    g = Point(0, 0).buffer(a) if kind == "circle" else box(-a, -b, a, b)
    g = rotate(g, q.get("yaw", 0.0), origin=(0, 0), use_radians=True)
    return translate(g, q["pos"][0], q["pos"][1]), h


def inside(part, P: np.ndarray) -> np.ndarray:
    """Which of the points P lie inside a body part."""
    if part["kind"] == "capsule":
        a, b, r = np.array(part["a"]), np.array(part["b"]), part["r"]
        ab = b - a
        t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-9), 0, 1)
        return np.linalg.norm(P - (a + t[:, None] * ab), axis=1) <= r
    c, rr, yaw, pitch = np.array(part["c"]), np.array(part["r"]), part.get("yaw", 0.0), part.get("pitch", 0.0)
    d = P - c
    x = d[:, 0] * math.cos(yaw) + d[:, 1] * math.sin(yaw)
    y = -d[:, 0] * math.sin(yaw) + d[:, 1] * math.cos(yaw)
    x, z = x * math.cos(pitch) + d[:, 2] * math.sin(pitch), -x * math.sin(pitch) + d[:, 2] * math.cos(pitch)
    return (x / rr[0]) ** 2 + (y / rr[1]) ** 2 + (z / rr[2]) ** 2 <= 1.0


def fill(part) -> np.ndarray:
    """Grid points inside one body part (N x 3)."""
    if part["kind"] == "capsule":
        a, b, r = np.array(part["a"]), np.array(part["b"]), part["r"]
        lo, hi = np.minimum(a, b) - r, np.maximum(a, b) + r
    else:
        c, m = np.array(part["c"]), max(part["r"])
        lo, hi = c - m, c + m
    ax = [np.arange(lo[i], hi[i] + STEP, STEP) for i in range(3)]
    P = np.stack(np.meshgrid(*ax, indexing="ij"), -1).reshape(-1, 3)
    return P[inside(part, P)]


def _prism(poly, z0, z1, P):
    """Depth (mm) of each point inside a vertical prism (poly x [z0, z1]); 0 outside."""
    out = np.zeros(len(P))
    hit = (P[:, 2] > z0) & (P[:, 2] < z1)
    if hit.any():
        hit[hit] = contains_xy(poly, P[hit, 0], P[hit, 1])
    if hit.any():
        b = poly.boundary
        dxy = np.array([b.distance(Point(x, y)) for x, y in P[hit, :2]])
        out[hit] = np.minimum(dxy, np.minimum(P[hit, 2] - z0, z1 - P[hit, 2]))
    return out


_P = {}


@lru_cache(maxsize=None)
def _legs_at(key, k):
    from . import comfort
    return comfort.low_footprint(_P[key], k * 10.0 + 5.0, 0.0)


def solids(p, sc) -> list:
    """(name, kind, data) for everything a body mustn't enter in one scene."""
    from . import yagura
    L = frame.layout(p)
    surf = L.H + p.material.t_nominal
    out = [("tabletop", "prism", (translate(T.build(p).outline, -p.top.length / 2, -p.top.width / 2), L.H, surf)),
           ("deck", "prism", (translate(yagura.deck(p), -L.cx, -L.cy), L.z_deck_bot, L.z_deck_bot + p.material.t_nominal))]
    (hx, hy, hz), (cx, cy, cz) = frame.heater_box(p)
    out.append(("heater", "prism", (box(cx - L.cx - hx / 2, cy - L.cy - hy / 2, cx - L.cx + hx / 2, cy - L.cy + hy / 2), cz - hz / 2, cz + hz / 2)))
    out.append(("a table leg", "legs", None))
    for q in sc["top"]:
        if q["kind"] in PROP:
            g, h = prop_shape(q)
            out.append((q["kind"], "prism", (g, surf, surf + h)))
    from . import room
    squash = getattr(p.room, "seat_squash", 30.0)
    for i, st in enumerate(room.seats(p)):                 # the seats, below where a body sinks into them
        if i in sc.get("hide_seats", []):
            continue
        (x, y, _), (l, w, h) = st["center"], st["size"]
        if st["kind"] == "shikibuton":
            x += sc.get("seat_slide", 0.0)
        out.append((st["kind"], "prism", (box(x - l / 2, y - w / 2, x + l / 2, y + w / 2), -1.0, h - squash - SINK)))
    for q in sc["props"]:
        if q["kind"] == "zaisu":
            out.append(("the zaisu's back", "zaisu", q))
    return out


def zaisu_back_local(q, P):
    """Points in the reclined backrest's own frame (x through its thickness, forward +; y across; z up its face)."""
    Z = scenes.ZAISU
    yaw = q["yaw"]
    d = P - np.array([q["pos"][0], q["pos"][1], 0.0])
    x = d[:, 0] * math.cos(yaw) + d[:, 1] * math.sin(yaw) - Z["back_x"]
    y = -d[:, 0] * math.sin(yaw) + d[:, 1] * math.cos(yaw)
    z = d[:, 2] - (q["seat_h"] + Z["back_zc"])
    a = Z["recline"]                                       # the page turns it by rotation.y = -recline
    return x * math.cos(a) + z * math.sin(a), y, -x * math.sin(a) + z * math.cos(a)


def _depths(p, kind, data, P):
    if kind == "prism":
        return _prism(*data, P)
    out = np.zeros(len(P))
    if kind == "legs":
        key = id(p)
        _P[key] = p
        top = frame.layout(p).H
        ks = np.floor(P[:, 2] / 10.0).astype(int)
        for k in np.unique(ks):
            if k < 0 or k * 10.0 > top:
                continue
            m = ks == k
            fp = _legs_at(key, int(k))
            if fp.is_empty:
                continue
            hit = contains_xy(fp, P[m, 0], P[m, 1])
            if hit.any():
                idx = np.where(m)[0][hit]
                out[idx] = [fp.boundary.distance(Point(x, y)) for x, y in P[idx, :2]]
        return out
    if kind == "zaisu":
        Z = scenes.ZAISU
        xs, y, zs = zaisu_back_local(data, P)
        m = (np.abs(xs) < Z["back_t"] / 2) & (np.abs(y) < Z["back_w"] / 2) & (np.abs(zs) < Z["back_h"] / 2)
        out[m] = np.minimum(Z["back_t"] / 2 - np.abs(xs[m]), np.minimum(Z["back_w"] / 2 - np.abs(y[m]), Z["back_h"] / 2 - np.abs(zs[m])))
        return out
    raise ValueError(kind)


def into_tabletop(p, parts) -> float:
    """How far (mm) any of one person's parts pass into the tabletop."""
    L = frame.layout(p)
    poly = translate(T.build(p).outline, -p.top.length / 2, -p.top.width / 2)
    worst = 0.0
    for q in parts:
        P = fill(q)
        if len(P):
            worst = max(worst, float(_prism(poly, L.H, L.H + p.material.t_nominal, P).max()))
    return worst


def part_name(q) -> str:
    """A body part's plain name, from what scenes.py and sleeper.py make it of."""
    m, k = q["mat"], q["kind"]
    if m == "fur":
        return "body"
    if m == "socks":
        return "foot"
    if m == "pants":
        return "hips" if k == "ellipsoid" else "leg"
    if m == "top":
        return "torso" if k == "ellipsoid" else "arm"
    if m == "skin" and k == "ellipsoid":
        return "hand" if q["r"][2] < q["r"][1] * 0.6 else "head"
    return "head" if m == "hair" else m


def cats(p, sc) -> tuple[list[list[dict]], object]:
    """The scene's cats as bodies (lists of parts), and the quilt's height function if a cat stands on it."""
    out, cloth = [], None
    for q in sc["props"]:
        if q["kind"] == "cat_reach":
            from . import room
            _, cloth = room.scene_cloth(p, sc)
            out.append(scenes.place_cat(p, q, cloth)["parts"])
        elif q["kind"] == "cat_curled":                      # web/ambiance.js cat(): the loaf and the head
            x, y, z = q["pos"]
            yaw = q.get("yaw", 0.0)
            R = lambda u, v: (x + u * math.cos(yaw) - v * math.sin(yaw), y + u * math.sin(yaw) + v * math.cos(yaw))
            out.append([{"kind": "ellipsoid", "c": [x, y, z + 86.0], "r": [205.0, 160.0, 92.0], "yaw": yaw, "mat": "fur"},
                        {"kind": "ellipsoid", "c": [*R(140.0, -108.0), z + 66.0], "r": [84.0, 78.0, 70.0], "yaw": yaw, "mat": "fur"}])
    return out, cloth


def overlaps(p) -> dict:
    res = {}
    for name, sc in scenes.scenes(p).items():
        best = {}
        sol = solids(p, sc)
        felines, cloth = cats(p, sc)
        people = sc["people"] + felines                      # the cats count as bodies too (labelled after the people)
        who = [f"person {i + 1}" for i in range(len(sc["people"]))] + ["the cat"] * len(felines)
        for ci, cat in enumerate(felines):
            for i, part in enumerate(cat):
                P = fill(part)
                if cloth is not None and len(P):             # a cat on the quilt rides above it (a soft quilt gives 10 mm)
                    d = max(cloth(x, y) - z for x, y, z in P[:: max(1, len(P) // 300)])
                    if d > 10.0:
                        k = (f"the cat's {part_name(part)}", "the quilt")
                        best[k] = max(best.get(k, 0.0), round(d - 10.0, 1))
        for pi, person in enumerate(people):
            for i, part in enumerate(person):
                P = fill(part)
                if not len(P):
                    continue
                what = f"{who[pi]}'s {part_name(part)}"
                for sname, kind, data in sol:
                    d = _depths(p, kind, data, P)
                    if d.max() > 0:
                        k = (what, sname)
                        best[k] = max(best.get(k, 0.0), round(float(d.max()), 1))
                for pj in range(pi + 1, len(people)):
                    hit = np.zeros(len(P), bool)
                    for q in people[pj]:
                        hit |= inside(q, P)
                    if hit.any():                          # depth ~ the size of the shared blob
                        k = (what, who[pj])
                        best[k] = max(best.get(k, 0.0), round(STEP * float(hit.sum()) ** (1 / 3), 1))
        res[name] = sorted(((d, a, b) for (a, b), d in best.items()), reverse=True)
    return res


def _axis(part):
    """Points along a capsule's axis (with its radius), or an ellipsoid's centre and rim (radius 0)."""
    if part["kind"] == "capsule":
        a, b = np.array(part["a"]), np.array(part["b"])
        return [(a + (b - a) * t, part["r"]) for t in np.linspace(0, 1, 11)]
    c, (rx, ry, rz), yaw, pitch = np.array(part["c"]), part["r"], part.get("yaw", 0.0), part.get("pitch", 0.0)
    pts = [(c, 0.0)]
    for t in np.linspace(0, 2 * math.pi, 25)[:-1]:
        u, v = rx * math.cos(t), ry * math.sin(t)              # the rim through the long axis, tilted with it
        h, w = u * math.cos(pitch), u * math.sin(pitch)
        pts.append((c + np.array([h * math.cos(yaw) - v * math.sin(yaw), h * math.sin(yaw) + v * math.cos(yaw), w]), 0.0))
    return pts


def leg_problems(p, parts, leg_gap: float = 5.0) -> list[str]:
    """Where a person's legs and feet don't fit under the table: into a table leg (by less than leg_gap mm), within
    40 mm of the heater's underside, 10 mm of the deck's or 10 mm of the top's (the same limits as the scene tests)."""
    from . import comfort, yagura
    L = frame.layout(p)
    (hx, hy, hz), (cx, cy, cz) = frame.heater_box(p)
    heater = box(cx - L.cx - hx / 2, cy - L.cy - hy / 2, cx - L.cx + hx / 2, cy - L.cy + hy / 2)
    deck = translate(yagura.deck(p), -L.cx, -L.cy)
    out, cache = [], {}

    def legs_at(z):
        k = round(z / 5.0)
        if k not in cache:
            cache[k] = comfort.low_footprint(p, k * 5.0, 0.0)
        return cache[k]

    for q in scenes.legs_of(parts):
        for pt, r in _axis(q):
            rz = r if q["kind"] == "capsule" else (q["r"][2] if abs(pt[2] - q["c"][2]) < 1e-6 else 0.0)
            topz, at = pt[2] + rz, Point(pt[0], pt[1])
            if legs_at(topz + 2.5).distance(at) - r < leg_gap:
                out.append("a table leg")
            if heater.distance(at) < r and cz - hz / 2 - topz < 40:
                out.append("the heater")
            if deck.distance(at) < r and L.z_deck_bot - topz < 10:
                out.append("the deck")
            if abs(pt[0]) < p.top.length / 2 and abs(pt[1]) < p.top.width / 2 and L.H - topz < 10:
                out.append("the top")
    return sorted(set(out))
