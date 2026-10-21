"""Table top (tenban): one square piece with rounded corners.

Earlier tops are in git history: the decorative split/seam variants (tag seams-archive) and a Ø 900 round
top (dropped for shipping and futon reasons, docs/quote.md).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from shapely.geometry import Polygon

from .geom import rounded_rect


@dataclass
class TopParts:
    name: str
    boards: list[Polygon]          # one piece -> [outline]
    outline: Polygon | None = None
    keys: list[Polygon] = field(default_factory=list)


def build(p) -> TopParts:
    T = p.top
    outline = rounded_rect(0, 0, T.length, T.width, T.corner_r)
    return TopParts("rect", [outline], outline)
