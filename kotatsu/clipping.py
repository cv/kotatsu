"""Clipping checks for the 3-D scenes (kotatsu/scenes.py): where a body part passes into a prop on the table, into
the tabletop itself, or into another person. Props are boxes and cylinders sized like the page draws them
(web/ambiance.js); people are the capsules and ellipsoids scenes.py hands the page.

overlaps(p) -> {scene: [(mm, what, with), ...]}, worst first; a few mm of contact (a hand resting on the table, a
foot on the cushion) is normal, so callers pick their own threshold.
"""
from __future__ import annotations

import math

import numpy as np
from shapely.affinity import rotate, translate
from shapely.geometry import Point, box

from . import frame, scenes, top as T

# footprints (half-sizes or radius, mm) and heights above the tabletop, as web/ambiance.js draws them
PROP = {"sushi": ("box", 190, 95, 68), "plate": ("circle", 85, 0, 14), "bowl": ("circle", 58, 0, 62),
        "chopsticks": ("box", 120, 15, 10), "kyusu": ("circle", 75, 0, 95), "yunomi": ("circle", 36, 0, 70),
        "keyboard": ("box", 220, 65, 20), "mouse": ("circle", 35, 0, 30), "card_pile": ("circle", 70, 0, 14),
        "laptop_stand": ("box", 140, 125, 330)}


def prop_shape(q):
    kind, a, b, h = PROP[q["kind"]]
    g = Point(0, 0).buffer(a) if kind == "circle" else box(-a, -b, a, b)
    g = rotate(g, q.get("yaw", 0.0), origin=(0, 0), use_radians=True)
    return translate(g, q["pos"][0], q["pos"][1]), h


def samples(part):
    """Points (x, y, z) and the radius each carries, along a capsule's axis or over an ellipsoid's surface."""
    if part["kind"] == "capsule":
        a, b = np.array(part["a"]), np.array(part["b"])
        return [(a + (b - a) * t, part["r"]) for t in np.linspace(0, 1, 11)]
    c, (rx, ry, rz), yaw = np.array(part["c"]), part["r"], part.get("yaw", 0.0)
    out = []
    for th in np.linspace(0, math.pi, 7):
        for ph in np.linspace(0, 2 * math.pi, 13)[:-1]:
            x, y, z = rx * math.sin(th) * math.cos(ph), ry * math.sin(th) * math.sin(ph), rz * math.cos(th)
            out.append((c + np.array([x * math.cos(yaw) - y * math.sin(yaw), x * math.sin(yaw) + y * math.cos(yaw), z]), 0.0))
    return out


def _name(part, i):
    return f"{part['mat']} {part['kind']} #{i}"


def overlaps(p) -> dict:
    L = frame.layout(p)
    surf = L.H + p.material.t_nominal
    outline = translate(T.build(p).outline, -p.top.length / 2, -p.top.width / 2)
    res = {}
    for name, sc in scenes.scenes(p).items():
        hits = []
        props = [(q["kind"], *prop_shape(q)) for q in sc["top"] if q["kind"] in PROP]
        for pi, person in enumerate(sc["people"]):
            for i, part in enumerate(person):
                for pt, r in samples(part):
                    xy = Point(pt[0], pt[1])
                    for kind, g, h in props:                      # into a thing on the table
                        if pt[2] - r < surf + h and pt[2] + r > surf:
                            d = r - g.exterior.distance(xy) if not g.contains(xy) else r + g.exterior.distance(xy)
                            if d > 0:
                                hits.append((round(min(d, h, pt[2] + r - surf), 1), f"person {pi} {_name(part, i)}", kind))
                    if outline.contains(xy) and pt[2] - r < surf and pt[2] + r > L.H:   # into the tabletop
                        hits.append((round(min(pt[2] + r - L.H, surf - (pt[2] - r)), 1), f"person {pi} {_name(part, i)}", "tabletop"))
        for pi in range(len(sc["people"])):                       # people into each other
            for pj in range(pi + 1, len(sc["people"])):
                A = [s for q in sc["people"][pi] for s in samples(q)]
                B = [s for q in sc["people"][pj] for s in samples(q)]
                worst = max((ra + rb - float(np.linalg.norm(a - b)) for a, ra in A for b, rb in B), default=-1)
                if worst > 0:
                    hits.append((round(worst, 1), f"person {pi}", f"person {pj}"))
        best = {}
        for d, a, b in hits:
            k = (a, b)
            best[k] = max(best.get(k, 0), d)
        res[name] = sorted(((d, a, b) for (a, b), d in best.items()), reverse=True)
    return res
