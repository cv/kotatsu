"""The 3-D view's scenes (owner 2026-11): the table in use, so its heights and clearances can be seen.

    cards    two people cross-legged on the cushions, across from each other; the cat curled under the heater
    eating   two people at a meal; the cat reaching up from the shikibuton for the sushi
    napping  one napping (kotatsu/sleeper.py), the other cross-legged on a cushion, reading
    working  one on the zaisu at the laptop (stand, keyboard, mouse), cross-legged; the other reading by the side
    working, legs out   the same, with the zaisu sitter's legs out under the table

Every figure is the napper's body (sleeper.py: 180 cm, 80 kg, Winter's proportions, the same girths), posed here
from joint positions: arms and legs are two-bone chains (shoulder-elbow-wrist, hip-knee-ankle) reaching their
targets. Positions are in the table's centred coordinates, z up from the floor. The page only draws: capsules and
ellipsoids for people, and each prop by its kind at the position and yaw given here.
"""
from __future__ import annotations

import math

import numpy as np

from . import comfort, frame, room, sleeper

ORDER = ["napping", "cards", "eating", "working", "working, legs out"]
DEFAULT = "napping"


def _v(*a) -> np.ndarray:
    return np.array(a, dtype=float)


def _ik(a: np.ndarray, t: np.ndarray, la: float, lb: float, pole: np.ndarray) -> np.ndarray:
    """The middle joint of a two-bone chain from a towards t (bones la, lb), bent towards pole."""
    d = t - a
    L = float(np.linalg.norm(d))
    L = min(max(L, abs(la - lb) + 1.0), la + lb - 1.0)
    u = d / np.linalg.norm(d)
    x = (la ** 2 - lb ** 2 + L ** 2) / (2 * L)
    h = math.sqrt(max(0.0, la ** 2 - x ** 2))
    w = pole - u * float(pole @ u)
    w = w / (np.linalg.norm(w) or 1.0)
    return a + u * x + w * h


def _reach(a: np.ndarray, t: np.ndarray, la: float, lb: float, pole: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(middle joint, end) of a chain reaching for t; the end stops short if t is out of reach."""
    d = t - a
    L = float(np.linalg.norm(d))
    end = t if L <= la + lb - 1.0 else a + d / L * (la + lb - 1.0)
    return _ik(a, end, la, lb, pole), end


class Body:
    """Collects one figure's parts (the sleeper's schema), with the sleeper's proportions and girths."""

    def __init__(self, p):
        self.H = p.sleeper.height
        self.g = sleeper.pose(p)["girth"]
        self.parts: list[dict] = []

    def cap(self, a, b, r, mat):
        self.parts.append({"kind": "capsule", "a": [float(v) for v in a], "b": [float(v) for v in b], "r": float(r), "mat": mat})

    def ell(self, c, r, mat, yaw=0.0):
        self.parts.append({"kind": "ellipsoid", "c": [float(v) for v in c], "r": [float(v) for v in r], "yaw": float(yaw), "mat": mat})


def seated(p, seat, seat_z: float, facing: float, legs: str, hands: tuple, lean: float = 0.0) -> list[dict]:
    """A person sitting at (seat x, y), seat_z up, facing `facing` (radians, towards the table), legs "cross"
    (cross-legged) or "forward" (out under the table, heels on the floor), hands = (left, right) wrist targets in the
    person's own frame, (forward, to their right, height above the floor), lean = how far the shoulders sit back of the
    hips (mm, a zaisu's backrest)."""
    B = Body(p)
    H, g = B.H, B.g
    f = _v(math.cos(facing), math.sin(facing), 0.0)              # forward, towards the table
    r = _v(math.sin(facing), -math.cos(facing), 0.0)             # the person's right
    z = _v(0, 0, 1)
    s = _v(seat[0], seat[1], seat_z)
    yaw = facing
    pelvis = s + z * 0.06 * H
    B.ell(pelvis, (0.061 * H * g, 0.097 * H * g, 0.085 * H), "pants", yaw)
    chest = s + z * 0.25 * H - f * lean * 0.6
    B.ell(chest, (0.069 * H * g, 0.105 * H * g, 0.13 * H), "top", yaw)
    head = s + z * 0.46 * H - f * lean + f * 0.015 * H
    B.cap(s + z * 0.36 * H - f * lean * 0.8, head - z * 0.03 * H, 0.03 * H * g, "skin")
    B.ell(head, (0.055 * H, 0.044 * H, 0.064 * H), "skin", yaw)
    B.ell(head - f * 0.012 * H + z * 0.01 * H, (0.05 * H, 0.046 * H, 0.056 * H), "hair", yaw)
    upper, fore, hand = 0.186 * H, 0.146 * H, 0.108 * H
    for side, tgt in ((-1, hands[0]), (1, hands[1])):          # left (-r), right (+r)
        sh = s + z * 0.33 * H - f * lean + r * side * 0.11 * H
        t3 = s + f * tgt[0] + r * tgt[1]
        t3[2] = tgt[2]
        el, wr = _reach(sh, t3, upper, fore, -z + r * side * 0.8 - f * 0.4)
        B.cap(sh, el, 0.026 * H * g, "top")
        B.cap(el, wr, 0.020 * H * g, "top")
        d = (wr - el) / np.linalg.norm(wr - el)
        B.ell(wr + d * 0.45 * hand, (0.5 * hand, 0.026 * H, 0.012 * H), "skin", math.atan2(d[1], d[0]))
    thigh, shank, foot = 0.245 * H, 0.246 * H, 0.152 * H
    for side in (-1, 1):
        hip = s + z * 0.045 * H + r * side * 0.05 * H
        if legs == "cross":                                     # the ankle tucks under the other thigh
            ank_t = s + f * 0.10 * H - r * side * 0.06 * H + z * (0.025 * H + (0.02 * H if side > 0 else 0.0))
            kn, ank = _reach(hip, ank_t, thigh, shank, r * side + f * 0.6 + z * 0.4)
            toe = -r * side
        else:                                                   # out under the table, heels on the floor
            ank_t = _v(*(hip[:2] + f[:2] * 0.47 * H), 0.03 * H)   # nearly straight, so the thighs stay low (the rug's top is z = 0)
            kn, ank = _reach(hip, ank_t, thigh, shank, z + f * 0.2)
            toe = f * 0.4 + z
            toe = toe / np.linalg.norm(toe)
        B.cap(hip, kn, 0.040 * H * g, "pants")
        B.cap(kn, ank, 0.026 * H * g, "pants")
        B.ell(ank + toe * 0.35 * foot, (0.5 * foot, 0.027 * H, 0.02 * H), "socks", math.atan2(toe[1], toe[0]))
    return B.parts


def legs_of(parts: list[dict]) -> list[dict]:
    """The parts the quilt lies over: legs and feet (the torso comes up through the quilt, as at a real kotatsu)."""
    return [q for q in parts if q["mat"] in ("pants", "socks") and not (q["kind"] == "ellipsoid" and q["mat"] == "pants")]


def scenes(p) -> dict:
    """Every scene: people (lists of parts), props on the floor and on the top, the cat, the shikibuton's slide,
    the seats hidden (the zaisu stands where a cushion was), and the parts the quilt drapes over."""
    L = frame.layout(p)
    S, R = p.sleeper, p.room
    H = S.height
    surf = L.H + p.material.t_nominal                          # the top's surface
    edge = p.top.length / 2
    squash = getattr(R, "seat_squash", 30.0)
    seat_on = R.cushion_h - squash                             # sitting on a cushion or the shikibuton (the rug's top is z = 0)
    cush = [s for s in room.seats(p) if s["kind"] == "cushion"]
    back = edge + 0.22 * H                                     # hips this far from the centre: crossed knees just under the
                                                               #   top's edge, clear of the corner legs
    nap = sleeper.pose(p)

    def at_side(sy: int, legs="cross", hands="read", seat_z=None, dist=None, lean=0.0):
        """Sitting on the cushion at the +y (sy = 1) or -y side, facing the table."""
        d = dist or back
        sz = seat_on if seat_z is None else seat_z
        to_edge = d - edge                                      # from the hips to the table's edge
        hh = {"cards": ((to_edge + 0.07 * H, -0.05 * H, surf + 0.09 * H), (to_edge + 0.07 * H, 0.05 * H, surf + 0.09 * H)),
              "eat": ((to_edge + 0.05 * H, -0.09 * H, surf + 0.03 * H), (to_edge + 0.12 * H, 0.06 * H, surf + 0.06 * H)),
              "type": ((to_edge + 50.0, -0.07 * H, surf + 0.025 * H), (to_edge + 50.0, 0.07 * H, surf + 0.025 * H)),
              "read": ((0.16 * H, -0.07 * H, sz + 0.26 * H), (0.16 * H, 0.07 * H, sz + 0.26 * H))}[hands]
        return seated(p, (0.0, sy * d), sz, math.atan2(-sy, 0.0), legs, hh, lean)

    def reader_end(sx: int):
        """Cross-legged on the shikibuton's end at +x (sx = 1) or -x, reading; returns the parts, the book's place, yaw."""
        x0 = sx * back
        fac = math.atan2(0.0, -sx)
        hh = ((0.16 * H, -0.07 * H, seat_on + 0.26 * H), (0.16 * H, 0.07 * H, seat_on + 0.26 * H))
        return seated(p, (x0, 0.0), seat_on, fac, "cross", hh), (x0 - sx * 0.16 * H, 0.0, seat_on + 0.27 * H), fac

    out = {}
    # cards: across each other on the two cushions; the cat curled under the heater, on the shikibuton
    a, b = at_side(1, hands="cards"), at_side(-1, hands="cards")
    held_y = edge - 0.07 * H                                   # the fan between the hands, over the table's edge
    out["cards"] = {"people": [a, b], "seat_slide": 0.0, "hide_seats": [],
                    "props": [{"kind": "cat_curled", "pos": [0.0, 60.0, R.shikibuton_h - squash - 8.0], "yaw": 0.5}],
                    "top": [{"kind": "card_pile", "pos": [0.0, 0.0], "yaw": 0.2}, {"kind": "card_pile", "pos": [70.0, -15.0], "yaw": 1.1, "spread": True},
                            {"kind": "yunomi", "pos": [-300.0, 250.0]}, {"kind": "yunomi", "pos": [300.0, -250.0]}],
                    "held": [{"kind": "card_fan", "pos": [0.0, sy * held_y, surf + 0.11 * H], "yaw": math.atan2(-sy, 0.0)}
                             for sy in (1, -1)]}
    # eating: two at a meal; the cat on the shikibuton's end, reaching up for the sushi
    a, b = at_side(1, hands="eat"), at_side(-1, hands="eat")
    out["eating"] = {"people": [a, b], "seat_slide": 0.0, "hide_seats": [],
                     "props": [{"kind": "cat_reach", "pos": [edge + 120.0, 40.0, R.shikibuton_h - squash], "yaw": math.pi, "on_cloth": True}],
                     "top": [{"kind": "sushi", "pos": [60.0, 0.0], "yaw": 0.0},
                             {"kind": "plate", "pos": [-40.0, 230.0]}, {"kind": "plate", "pos": [-40.0, -230.0]},
                             {"kind": "chopsticks", "pos": [60.0, 260.0], "yaw": 0.0}, {"kind": "chopsticks", "pos": [60.0, -260.0], "yaw": 0.0},
                             {"kind": "bowl", "pos": [-200.0, 300.0]}, {"kind": "bowl", "pos": [-200.0, -300.0]},
                             {"kind": "kyusu", "pos": [-280.0, 0.0], "yaw": 2.6}, {"kind": "yunomi", "pos": [200.0, 300.0]}, {"kind": "yunomi", "pos": [200.0, -300.0]}],
                     "held": []}
    # napping: the napper (sleeper.py) and a reader on the far cushion
    rd = at_side(-1, hands="read")
    out["napping"] = {"people": [nap["parts"], rd], "seat_slide": nap["slide"], "hide_seats": [],
                      "props": [], "top": [{"kind": "kyusu", "pos": [235.0, 200.0], "yaw": 2.6}, {"kind": "yunomi", "pos": [70.0, 270.0]}],
                      "held": [{"kind": "book_open", "pos": [0.0, -(back - 0.16 * H), seat_on + 0.27 * H], "yaw": math.atan2(1.0, 0.0)}]}
    # working: on the zaisu (where the -y cushion was), the laptop on a stand; a reader on the shikibuton's end
    zs = p.comfort.chair_seat_h
    zy = edge + (0.245 * H - min(200.0, comfort.mid_side_opening(p) - 25.0))   # knees ~200 mm in, short of the heater ring
    def clears_top(ps):                                         # every leg part under the top stays 10 mm below it
        for q in legs_of(ps):
            pts = [q["a"], q["b"]] if q["kind"] == "capsule" else [q["c"]]
            rz = q["r"] if q["kind"] == "capsule" else q["r"][2]
            if any(abs(v[0]) < edge + 30 and abs(v[1]) < edge + 30 and v[2] + rz > L.H - 10 for v in pts):
                return False
        return True

    for name, legs in (("working", "cross"), ("working, legs out", "forward")):
        d = zy
        w = at_side(-1, legs=legs, hands="type", seat_z=zs, dist=d, lean=0.05 * H)
        while not clears_top(w) and d < edge + 0.4 * H:         # cross-legged on the zaisu the knees ride ~400 mm up,
            d += 20.0                                            #   above the top: sit back until they clear its edge
            w = at_side(-1, legs=legs, hands="type", seat_z=zs, dist=d, lean=0.05 * H)
        rdr, book_at, fac = reader_end(1)
        out[name] = {"people": [w, rdr], "seat_slide": 0.0, "hide_seats": [i for i, s in enumerate(room.seats(p)) if s["kind"] == "cushion" and s["center"][1] < 0],
                     "props": [{"kind": "zaisu", "pos": [0.0, -d, 0.0], "yaw": math.pi / 2, "seat_h": zs}],
                     "sit_back": round(d - zy),
                     "top": [{"kind": "laptop_stand", "pos": [0.0, -edge + 330.0], "yaw": math.pi},   # the screen faces the sitter (-y)
                             {"kind": "keyboard", "pos": [0.0, -edge + 0.06 * H], "yaw": 0.0},
                             {"kind": "mouse", "pos": [260.0, -edge + 0.06 * H], "yaw": 0.0},
                             {"kind": "yunomi", "pos": [-300.0, -edge + 140.0]}],
                     "held": [{"kind": "book_open", "pos": list(book_at), "yaw": fac}]}
    for sc in out.values():                                     # what the quilt lies over: legs (and the napper whole)
        drape = []
        for ps in sc["people"]:
            drape += ps if ps is nap["parts"] else legs_of(ps)
        sc["drape_over"] = drape
    return out
