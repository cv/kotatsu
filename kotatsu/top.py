"""Table top (tenban): one square-ish piece, a squircle (v2; v1 was a square with R20 corners).

Earlier tops are in git history: the decorative split/seam variants (tag seams-archive), a Ø 900 round
top (dropped for shipping and futon reasons, docs/quote.md) and v1's R20 square (tag v1-ordered).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from shapely.geometry import Polygon

from .geom import squircle


@dataclass
class TopParts:
    name: str
    boards: list[Polygon]          # one piece -> [outline]
    outline: Polygon | None = None
    keys: list[Polygon] = field(default_factory=list)


def build(p) -> TopParts:
    T = p.top
    outline = squircle(0, 0, T.length, T.width, T.squircle_n)
    return TopParts("rect", [outline], outline)
