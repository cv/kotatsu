"""The assembly, step by step, for the 3-D tab's animation (PLAN.md "Assembly", and how it really went).

Each part gets a list of moves: during step k, between fractions a and b of that step, it travels from
its assembled position + `from` (mm, world axes) back to its assembled position. Before the step it waits
at the offset; after it, it's home. So at the slider's end (= the number of steps) everything sits exactly
where the cut files put it, and the JS only interpolates what's computed here. The distances come from
the layout, so each part starts clear of whatever it slides into.
"""
from __future__ import annotations

import math

from . import frame as fr
from . import yagura

STEPS = [
    "Cross each pair of plates into a \"+\" leg",
    "Stand the four legs up",
    "Lower the deck over the 8 tenons",
    "Push a wedge through each tenon",
    "Hang the two heater cheeks, tabs up through the deck",
    "Push a wedge through each cheek tab",
    "Screw the heater in between the cheeks",
    "Drape the futon over the frame",
    "Lay the top on the futon",
    "Tea time",
]
LEGS, STAND, DECK, LEG_WEDGES, CHEEKS, CHEEK_WEDGES, HEATER, FUTON, TOP, TEA = range(len(STEPS))
CLEAR = 40.0     # mm of daylight between a waiting part and whatever it goes into


def stagger(i: int, n: int, width: float = 0.5) -> tuple[float, float]:
    """Window [a, b] inside a step for the i-th of n parts that go one after another (overlapping)."""
    a = (1 - width) * i / (n - 1) if n > 1 else 0.0
    return round(a, 3), round(a + (width if n > 1 else 1.0), 3)


def move(step: int, frm, window=(0.0, 1.0)) -> dict:
    return {"step": step, "a": window[0], "b": window[1], "from": [round(v, 1) for v in frm]}


def corner(L, c) -> tuple[int, int, int]:
    """(sx, sy, index) of the corner a part at centre c belongs to; index runs round the table."""
    sx, sy = (1 if c[0] > L.cx else -1), (1 if c[1] > L.cy else -1)
    return sx, sy, {(-1, -1): 0, (1, -1): 1, (1, 1): 2, (-1, 1): 3}[(sx, sy)]


def part_moves(p, pt, pl, c, k: int) -> list[dict]:
    """Moves for the k-th placement of part pt, whose centre (world, mm) is c."""
    L, t = fr.layout(p), p.material.t_nominal
    if pt.kind == "frame":                       # leg plates
        sx, sy, i = corner(L, c)
        spread = L.Lf * 0.3                      # the legs wait out beyond their corners
        out = [move(STAND, (sx * spread / math.sqrt(2), sy * spread / math.sqrt(2), 0), stagger(i, 4))]
        if pt.name == "leg plate B":             # slotted from the floor up: drops onto plate A
            out.insert(0, move(LEGS, (0, 0, yagura.lap_depth(p) + CLEAR), stagger(i, 4)))
        return out
    if pt.kind == "deck":                        # comes down over the tenons
        return [move(DECK, (0, 0, L.H - L.z_deck_bot + CLEAR))]
    if pt.kind == "cheek":                       # comes up from below until its tabs poke through
        rise = L.z_deck_top + p.cheek.tab_above_deck - L.z_deck_bot + CLEAR
        return [move(CHEEKS, (0, 0, -rise), stagger(k, 2, 0.7))]
    if pt.kind == "wedge":                       # slides in tip first (tip at u = 0, head at u = length)
        n_leg = len(yagura.mortises(p))
        leg = pt.name == "leg wedge" or (pt.name == "wedge" and k < n_leg)
        n, head = yagura.wedge_dims(p, "leg" if leg else "cheek")
        ux, uy = (1, 0) if pl.axis == "x" else (0, 1)
        d = n * 0.6 + t                          # starts mostly out of its hole, beside the tenon or tab
        i, m = (k, n_leg) if leg else (k - n_leg if pt.name == "wedge" else k, 4)
        return [move(LEG_WEDGES if leg else CHEEK_WEDGES, (ux * d, uy * d, 0), stagger(i, m))]
    raise ValueError(f"no assembly moves for part kind {pt.kind!r}")


def extras(p) -> dict:
    """Moves for the things the 3-D view adds itself: the heater, the futon, the top and the tea things."""
    L = fr.layout(p)
    (_, _, sz), (_, _, hz) = fr.heater_box(p)
    return {
        "steps": STEPS,
        "heater": [move(HEATER, (0, 0, -min(hz - sz / 2 - CLEAR, 220.0)))],    # up from the floor
        "futon": [move(FUTON, (0, 0, 120.0))],                                 # settles and fades in
        "top": [move(TOP, (0, 0, L.H + CLEAR * 4))],
        "tea": [move(TEA, (0, 0, 160.0))],
    }
