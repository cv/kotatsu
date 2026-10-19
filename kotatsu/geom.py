"""Router-aware 2-D geometry helpers (shapely, mm).

A CNC router cannot cut an *inside* (concave) corner sharper than the bit radius r.
For two parts that mate in-plane (seams, keys), we round the male shape so that:
  * its concave corners have radius >= r   (closing by r)
  * its convex corners have radius >= r + c  (opening by r + c)
and cut the female as the male grown by the clearance c. The female's concave
corners then have radius >= r + 2c, so both parts are cuttable without dogbones.
"""
from __future__ import annotations

from shapely.geometry import Polygon, box
from shapely.geometry.base import BaseGeometry

Q = 16  # quad segments for arcs


def closing(g: BaseGeometry, r: float) -> BaseGeometry:
    return g.buffer(r, quad_segs=Q, join_style="round").buffer(-r, quad_segs=Q, join_style="round")


def opening(g: BaseGeometry, r: float) -> BaseGeometry:
    return g.buffer(-r, quad_segs=Q, join_style="round").buffer(r, quad_segs=Q, join_style="round")


def router_cuttable(g: BaseGeometry, r: float, tol: float = 0.5) -> bool:
    """True if every concave corner already has radius >= r (closing adds no real material).

    Checked per corner: a square inside corner with a 1/4" bit leaves (1 - pi/4) r^2 ~ 2.2 mm^2,
    while arc-segmentation noise is < 0.15 mm^2 per corner, so the per-piece test scales to any
    number of corners.
    """
    d = closing(g, r).symmetric_difference(g)
    return all(piece.area < tol for piece in getattr(d, "geoms", [d]))


def male(shape: BaseGeometry, r: float, c: float) -> BaseGeometry:
    return opening(closing(shape, r), r + c)


def female_cut(male_shape: BaseGeometry, c: float) -> BaseGeometry:
    """Region to remove from the mating part."""
    return male_shape.buffer(c, quad_segs=Q, join_style="round")


def rounded_rect(x0: float, y0: float, x1: float, y1: float, r: float) -> Polygon:
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=Q)


def largest(g: BaseGeometry) -> Polygon:
    if g.geom_type == "Polygon":
        return g
    return max(g.geoms, key=lambda p: p.area)
