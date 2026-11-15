"""A person napping under the kotatsu, for the 3-D view's ambiance layer (owner 2026-11).

Lying on the stomach along the shikibuton (room.seats = "set"), feet towards the table, as in the owner's reference
photo: the head turned to one side; one arm up past the head with its hand under it, the other bent with its elbow
back towards the hips and its hand up by the face; one leg nearly straight, the other's knee drawn up and out to
the side with its shin back across, a "4", both feet turned to point the same way.

Proportions are Winter's segment fractions of stature (Biomechanics and Motor Control of Human Movement): the hip
joint 0.53 H above the floor standing (so 0.47 H from the top of the head), the shoulder 0.818 H, the thigh 0.245 H,
the shank 0.246 H, the foot 0.152 H, the upper arm 0.186 H, the forearm 0.146 H, the hand 0.108 H. Girths are
scaled so the body's volume is its mass at 1010 kg/m3. Python places every piece; the page only draws capsules
and ellipsoids.

The hips go as far in as they can, just clear of the heater (the thighs and legs pass under it with air to spare),
and the mattress slides along x for the nap (a real napper would pull it over) just far enough for the head
and hands to lie on it.
"""
from __future__ import annotations

import math

from . import frame, room


def _support(p, x: float, y: float, slide: float) -> float:
    """Height of whatever is under (x, y), centred coordinates: the (slid, slightly squashed) shikibuton, or the rug."""
    S = p.sleeper
    for s in room.seats(p):
        (cx, cy, _), (w, d, h) = s["center"], s["size"]
        if s["kind"] == "shikibuton":
            cx += slide
        if abs(x - cx) <= w / 2 and abs(y - cy) <= d / 2:
            return h - S.sink
    return p.room.rug_t


def _elbow(sh, wr, upper: float, fore: float, pick=min) -> tuple[float, float]:
    """In plan, where the upper arm (from the shoulder) and the forearm (to the wrist) meet: of the two places, the
    one pick (min or max) chooses along x (min: towards the head, max: back towards the hips)."""
    dx, dy = wr[0] - sh[0], wr[1] - sh[1]
    d = math.hypot(dx, dy)
    a = (upper ** 2 - fore ** 2 + d ** 2) / (2 * d)
    h = math.sqrt(max(0.0, upper ** 2 - a ** 2))
    mx, my = sh[0] + a * dx / d, sh[1] + a * dy / d
    return pick([(mx - h * dy / d, my + h * dx / d), (mx + h * dy / d, my - h * dx / d)], key=lambda e: e[0])


def pose(p) -> dict:
    """{"slide": mm the shikibuton moves along x, "parts": [capsule or ellipsoid dicts], "volume_l": litres}, in
    the table's centred coordinates (z up from the floor). Capsules: a, b, r; ellipsoids: c, r (along x, y, z
    before the yaw), yaw (radians about z). Every part has a material: top, pants, skin, hair or socks."""
    S, H = p.sleeper, p.sleeper.height
    L = frame.layout(p)
    (hx, _, _), _ = frame.heater_box(p)
    pelvis_half = 0.085 * H                                    # pelvis, along the body
    x_hip = -(hx / 2 + S.clear + pelvis_half)                  # as far in as the hips can go: just clear of the heater
    x_top = x_hip - 0.47 * H                                   # the top of the head
    (sh,) = [s for s in room.seats(p) if s["kind"] == "shikibuton"]
    length = sh["size"][0]
    slide = min(0.0, (x_top - S.margin) + length / 2)          # the mattress's head end just past the head
    sup = lambda x, y: _support(p, x, y, slide)

    def ang(a):                                                # unit vector at angle a (degrees) from +x
        return math.cos(math.radians(a)), math.sin(math.radians(a))

    parts: list[dict] = []

    def capsule(a2, b2, r, mat, lift=0.85):
        """A limb segment lying on whatever is under it: a2, b2 are plan points; each end rests on its support."""
        a = [a2[0], a2[1], sup(*a2) + lift * r]
        b = [b2[0], b2[1], sup(*b2) + lift * r]
        worst, at = 0.0, None                                  # over a mattress edge between the ends? bend there
        for k in range(1, 20):
            t = k / 20
            m = (a2[0] + t * (b2[0] - a2[0]), a2[1] + t * (b2[1] - a2[1]))
            need = sup(*m) + lift * r - (a[2] + t * (b[2] - a[2]))
            if need > worst:
                worst, at = need, m
        if at is not None and worst > 2.0:
            mz = [at[0], at[1], sup(*at) + lift * r]
            parts.append({"kind": "capsule", "a": a, "b": mz, "r": r, "mat": mat})
            parts.append({"kind": "capsule", "a": mz, "b": b, "r": r, "mat": mat})
        else:
            parts.append({"kind": "capsule", "a": a, "b": b, "r": r, "mat": mat})
        return b2

    def ellipsoid(c2, r, mat, yaw=0.0, z=None, lift=0.9):
        parts.append({"kind": "ellipsoid", "c": [c2[0], c2[1], z if z is not None else sup(*c2) + lift * r[2]],
                      "r": list(r), "yaw": yaw, "mat": mat})

    g = 1.0                                                    # girth scale, fixed below so the volume is the mass
    def build(g):
        parts.clear()
        thigh, shank, foot = 0.245 * H, 0.246 * H, 0.152 * H
        upper, fore, hand = 0.186 * H, 0.146 * H, 0.108 * H
        # torso: pelvis and chest, flattened ellipsoids lying on the mattress
        ellipsoid((x_hip, 0.0), (pelvis_half, 0.097 * H * g, 0.061 * H * g), "pants")
        x_sh = x_hip - (0.47 - 0.182) * H                      # shoulder line
        ellipsoid((x_sh + 0.11 * H, 0.0), (0.155 * H, 0.105 * H * g, 0.069 * H * g), "top")
        # legs (owner's reference photo): one nearly straight, the other's knee drawn up and out to the side with its
        # shin back across: a "4". Both feet turned to point the same way, towards the straight leg's side (-y).
        hs, hb = (x_hip, -0.05 * H), (x_hip, 0.05 * H)          # the straight leg's hip (-y), the bent leg's (+y)
        ks = capsule(hs, (hs[0] + thigh * ang(-3)[0], hs[1] + thigh * ang(-3)[1]), 0.040 * H * g, "pants")
        as_ = capsule(ks, (ks[0] + shank * ang(3)[0], ks[1] + shank * ang(3)[1]), 0.026 * H * g, "pants")
        kb = capsule(hb, (hb[0] + thigh * ang(S.knee_out)[0], hb[1] + thigh * ang(S.knee_out)[1]), 0.040 * H * g, "pants")
        ab = capsule(kb, (kb[0] + shank * ang(S.shin_back)[0], kb[1] + shank * ang(S.shin_back)[1]), 0.026 * H * g, "pants")
        for a2 in (as_, ab):                                    # feet turned out, toes towards -y, lying on their sides
            ellipsoid((a2[0] + 0.02 * H, a2[1] - 0.35 * foot), (0.5 * foot, 0.027 * H, 0.025 * H), "socks",
                      yaw=-math.pi / 2)
        # arms: the left (-y) up past the head, its hand under the head; the right (+y) bent with its elbow back
        # towards the hips and its hand up in front of the face (the head is turned that way, +y)
        head_c = (x_top + 0.064 * H, 0.0)
        for s in (-1, 1):
            shp = (x_sh, s * 0.11 * H)
            if s < 0:                                           # up past the head, the hand under it
                wrist = (head_c[0] + 0.02 * H, -0.03 * H)
                el2 = _elbow(shp, wrist, upper, fore, min)
            else:                                               # elbow out and back, the hand up in front of the face
                el2 = (shp[0] + upper * ang(S.elbow_back)[0], shp[1] + upper * ang(S.elbow_back)[1])
                face = (head_c[0] + 0.025 * H, 0.09 * H)
                k = fore / math.hypot(face[0] - el2[0], face[1] - el2[1])
                wrist = (el2[0] + (face[0] - el2[0]) * k, el2[1] + (face[1] - el2[1]) * k)
            capsule(shp, el2, 0.026 * H * g, "top")
            capsule(el2, wrist, 0.020 * H * g, "top")
            dx, dy = wrist[0] - el2[0], wrist[1] - el2[1]
            k = 0.5 * hand / math.hypot(dx, dy)
            ellipsoid((wrist[0] + dx * k, wrist[1] + dy * k), (0.5 * hand, 0.026 * H, 0.012 * H), "skin",
                      yaw=math.atan2(dy, dx))
        # head on the hands, a neck to the chest, hair on the crown
        zh = sup(*head_c) + 0.018 * H + 0.05 * H
        parts.append({"kind": "capsule", "a": [x_sh - 0.01 * H, 0.0, sup(x_sh, 0) + 0.06 * H],
                      "b": [head_c[0] + 0.03 * H, 0.0, zh], "r": 0.03 * H * g, "mat": "skin"})
        ellipsoid(head_c, (0.064 * H, 0.044 * H, 0.051 * H), "skin", z=zh)
        ellipsoid((head_c[0] - 0.016 * H, -0.012 * H), (0.05 * H, 0.044 * H, 0.05 * H), "hair", z=zh + 0.006 * H)  # face turned to +y
        return parts

    def volume(ps):
        v = 0.0
        for q in ps:
            if q["kind"] == "capsule":
                ln = math.dist(q["a"], q["b"])
                v += math.pi * q["r"] ** 2 * ln + 4 / 3 * math.pi * q["r"] ** 3
            else:
                v += 4 / 3 * math.pi * q["r"][0] * q["r"][1] * q["r"][2]
        return v

    want = S.mass / 1010 * 1e9                                 # mm3
    for _ in range(6):                                         # girths scale volume about as g^2
        g *= math.sqrt(want / volume(build(g)))
    ps = build(g)
    return {"slide": round(slide, 1), "parts": ps, "volume_l": round(volume(ps) / 1e6, 1), "girth": round(g, 3)}
