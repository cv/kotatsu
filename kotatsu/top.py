"""Table top (tenban): 1200 x 800, split into two halves so every box stays <= 48".

Split styles (params.top.split):
  ari      - ari-tsugi: dovetail seam, tails alternate direction. No loose parts.
  puzzle   - jigsaw-tab seam, tabs alternate direction. No loose parts.
  chigiri  - straight butt seam locked by through bow-tie keys (loose parts).
  none     - single slab (box > 48" -> oversize parcel).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from .geom import female_cut, largest, male, rounded_rect


@dataclass
class TopParts:
    halves: list[Polygon]
    keys: list[Polygon] = field(default_factory=list)
    outline: Polygon | None = None


def _seam_ys(p) -> list[float]:
    n = p.top.seam_count
    return [p.top.width * (i + 0.5) / n for i in range(n)]


def _dovetail(x: float, y: float, d: float, w0: float, w1: float, sign: int) -> Polygon:
    """Tail rooted at seam x, pointing +x (sign=1) or -x (sign=-1)."""
    e = 2.0 * sign  # overlap into the root so the union is clean
    return Polygon([
        (x - e, y - w0 / 2), (x + sign * d, y - w1 / 2),
        (x + sign * d, y + w1 / 2), (x - e, y + w0 / 2),
    ])


def _puzzle_tab(x: float, y: float, R: float, neck: float, sign: int):
    cx = x + sign * (R * 0.9)
    head = Point(cx, y).buffer(R, quad_segs=24)
    neck_box = box(min(x - 2 * sign, cx), y - neck / 2, max(x - 2 * sign, cx), y + neck / 2)
    return unary_union([head, neck_box])


def _bowtie(x: float, y: float, L: float, W: float, w: float) -> Polygon:
    return Polygon([
        (x - L / 2, y - W / 2), (x, y - w / 2), (x + L / 2, y - W / 2),
        (x + L / 2, y + W / 2), (x, y + w / 2), (x - L / 2, y + W / 2),
    ])


def build(p) -> TopParts:
    T, cnc, fit = p.top, p.cnc, p.fit
    r, c = cnc.bit_d / 2, fit.inplane_c
    Lx, Wy = T.length, T.width
    outline = rounded_rect(0, 0, Lx, Wy, T.corner_r)
    xs = Lx / 2
    style = T.split

    if style == "none":
        return TopParts([outline], outline=outline)

    if style == "chigiri":
        k = T.chigiri
        keys = [male(_bowtie(xs, y, k.length, k.width, k.waist), r, c) for y in _seam_ys(p)]
        holes = unary_union([female_cut(kk, c) for kk in keys])
        a = largest(outline.intersection(box(-1, -1, xs, Wy + 1)).difference(holes))
        b = largest(outline.intersection(box(xs, -1, Lx + 1, Wy + 1)).difference(holes))
        return TopParts([a, b], keys=keys, outline=outline)

    # interlocking seams: build half A over an extended region, round it, then clip
    pad = 60.0
    a0 = box(-pad, -pad, xs, Wy + pad)
    for i, y in enumerate(_seam_ys(p)):
        sign = 1 if i % 2 == 0 else -1
        if style == "ari":
            d = T.ari
            tail = _dovetail(xs, y, d.depth, d.root, d.tip, sign)
        elif style == "puzzle":
            z = T.puzzle
            tail = _puzzle_tab(xs, y, z.head_r, z.neck, sign)
        else:
            raise ValueError(f"unknown top.split {style!r}")
        a0 = a0.union(tail) if sign > 0 else a0.difference(tail)
    a_m = male(a0, r, c)
    a = largest(a_m.intersection(outline))
    b = largest(outline.difference(female_cut(a_m, c)))
    return TopParts([a, b], outline=outline)
