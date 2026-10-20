"""Table top (tenban), cut as ONE piece: round (Ø = top.length) or a rounded rectangle.

The decorative split/seam variants were dropped when the owner chose the round table
(see git tag seams-archive).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from shapely.geometry import Point, Polygon

from .geom import rounded_rect


@dataclass
class TopParts:
    name: str
    boards: list[Polygon]          # one piece -> [outline]
    outline: Polygon | None = None
    keys: list[Polygon] = field(default_factory=list)


def build(p) -> TopParts:
    T = p.top
    if getattr(T, "shape", "rect") == "round":
        outline = Point(T.length / 2, T.width / 2).buffer(T.length / 2, quad_segs=64)
        return TopParts("round", [outline], outline)
    outline = rounded_rect(0, 0, T.length, T.width, T.corner_r)
    return TopParts("rect", [outline], outline)
