"""Looks, as numbers the design search can weigh (kotatsu/optimize.py).

leg_width: the legs' visual weight, as the average visible width (mm) of the leg plate below the deck:
its area under the deck's underside divided by that height. The haunch,
the narrow part and the taper all show up in it; lower is slimmer. (In winter the futon hides the legs;
in summer, or with the futon up, they're what you see.)
"""
from __future__ import annotations

from shapely.geometry import box

from . import frame


def leg_plates(p) -> list:
    """The leg plates' shapes (one per corner, all the same; the crosspieces hide under the deck)."""
    return [pt.shape for pt in frame.parts(p) if pt.kind == "frame" and pt.name.startswith("leg plate")]


def leg_width(p) -> float:
    zs = frame.layout(p).z_deck_bot
    plates = leg_plates(p)
    if not plates:
        raise ValueError("no leg plates")
    under = box(-1e4, 0.0, 1e4, zs)
    return sum(g.intersection(under).area for g in plates) / (len(plates) * zs)
