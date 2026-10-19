"""Table top (tenban): 1200 x 800, split into two halves so every box stays <= 48".

Seam variants live in params.toml [[top.options]]; params.top.split picks one.
kinds:
  ari      dovetail tails (ari-tsugi)            - no loose parts
  kama     gooseneck: neck + flared head          - no loose parts
  puzzle   jigsaw: neck + round head              - no loose parts
  lobes    seigaiha wave of necked round lobes    - no loose parts
  chigiri  straight seam + through bow-tie keys   - loose keys
"""
from __future__ import annotations

from dataclasses import dataclass, field

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from .geom import female_cut, largest, male, rounded_rect


@dataclass
class TopParts:
    name: str
    kind: str
    halves: list[Polygon]
    keys: list[Polygon] = field(default_factory=list)
    outline: Polygon | None = None
    joints: list[tuple[float, float]] = field(default_factory=list)  # joint centres (zoom targets)


def option(p, name: str | None = None):
    name = name or p.top.split
    for o in p.top.options:
        if o.name == name:
            return o
    raise KeyError(f"no [[top.options]] named {name!r}")


def _ys(width: float, n: int) -> list[float]:
    return [width * (i + 0.5) / n for i in range(n)]


def _xbox(x0: float, x1: float, y: float, w: float) -> Polygon:
    a, b = sorted((x0, x1))
    return box(a, y - w / 2, b, y + w / 2)


def _dovetail(x, y, o, s):
    e = 2.0 * s  # root overlap so unions are clean
    return Polygon([(x - e, y - o.root / 2), (x + s * o.depth, y - o.tip / 2),
                    (x + s * o.depth, y + o.tip / 2), (x - e, y + o.root / 2)])


def _kama(x, y, o, s):
    h0 = x + s * o.neck_len
    h1 = h0 + s * o.head_len
    neck = _xbox(x - 2 * s, h0 + s, y, o.neck)
    head = Polygon([(h0, y - o.head_root / 2), (h1, y - o.head_tip / 2),
                    (h1, y + o.head_tip / 2), (h0, y + o.head_root / 2)])
    return unary_union([neck, head])


def _puzzle(x, y, o, s):
    cx = x + s * o.head_r * 0.9
    return unary_union([Point(cx, y).buffer(o.head_r, quad_segs=24), _xbox(x - 2 * s, cx, y, o.neck)])


def _lobe(x, y, o, s):
    return Point(x + s * o.offset * o.r, y).buffer(o.r, quad_segs=24)


def _bowtie(x, y, o):
    L, W, w = o.length, o.width, o.waist
    return Polygon([(x - L / 2, y - W / 2), (x, y - w / 2), (x + L / 2, y - W / 2),
                    (x + L / 2, y + W / 2), (x, y + w / 2), (x - L / 2, y + W / 2)])


TAILS = {"ari": _dovetail, "kama": _kama, "puzzle": _puzzle, "lobes": _lobe}
KINDS = (*TAILS, "chigiri")


def build(p, name: str | None = None) -> TopParts:
    T, r, c = p.top, p.cnc.bit_d / 2, p.fit.inplane_c
    Lx, Wy = T.length, T.width
    outline = rounded_rect(0, 0, Lx, Wy, T.corner_r)
    xs = Lx / 2
    name = name or T.split

    if name == "none":
        return TopParts("none", "none", [outline], outline=outline)

    o = option(p, name)
    ys = _ys(Wy, o.count)
    joints = [(xs, y) for y in ys]

    if o.kind == "chigiri":
        keys = [male(_bowtie(xs, y, o), r, c) for y in ys]
        holes = unary_union([female_cut(k, c) for k in keys])
        a = largest(outline.intersection(box(-1, -1, xs, Wy + 1)).difference(holes))
        b = largest(outline.intersection(box(xs, -1, Lx + 1, Wy + 1)).difference(holes))
        return TopParts(o.name, o.kind, [a, b], keys=keys, outline=outline, joints=joints)

    if o.kind not in TAILS:
        raise ValueError(f"unknown seam kind {o.kind!r}")
    alternate = getattr(o, "alternate", True)
    pad = 60.0
    a0 = box(-pad, -pad, xs, Wy + pad)
    for i, y in enumerate(ys):
        s = -1 if (alternate and i % 2) else 1
        tail = TAILS[o.kind](xs, y, o, s)
        a0 = a0.union(tail) if s > 0 else a0.difference(tail)
    a_m = male(a0, r, c)
    a = largest(a_m.intersection(outline))
    b = largest(outline.difference(female_cut(a_m, c)))
    return TopParts(o.name, o.kind, [a, b], outline=outline, joints=joints)
