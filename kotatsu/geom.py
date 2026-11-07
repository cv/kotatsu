"""Router-aware 2-D geometry helpers (shapely, mm).

A CNC router cannot cut an *inside* (concave) corner sharper than the bit radius r: closing a shape by
r shows what the bit would leave behind, which is how router_cuttable checks every part.
"""
from __future__ import annotations

import numpy as np
from shapely.geometry import Polygon, box
from shapely.geometry.base import BaseGeometry

Q = 16  # quad segments for arcs


def closing(g: BaseGeometry, r: float) -> BaseGeometry:
    return g.buffer(r, quad_segs=Q, join_style="round").buffer(-r, quad_segs=Q, join_style="round")


def router_cuttable(g: BaseGeometry, r: float, tol: float = 0.5) -> bool:
    """True if every concave corner already has radius >= r (closing adds no real material).

    Checked per corner: a square inside corner with a 1/4" bit leaves (1 - pi/4) r^2 ~ 2.2 mm^2,
    while arc-segmentation noise is < 0.15 mm^2 per corner, so the per-piece test scales to any
    number of corners.
    """
    d = closing(g, r).symmetric_difference(g)
    return all(piece.area < tol for piece in getattr(d, "geoms", [d]))


def squircle(x0: float, y0: float, x1: float, y1: float, n: float, tol: float = 0.02) -> Polygon:
    """Superellipse |x/a|^n + |y/b|^n = 1 filling the box: n = 2 is an ellipse, larger n squarer. Its
    curvature fades smoothly into straight-looking edges, unlike a radius that starts abruptly. Sampled
    densely, then simplified to within tol mm."""
    a, b, cx, cy = (x1 - x0) / 2, (y1 - y0) / 2, (x0 + x1) / 2, (y0 + y1) / 2
    t = np.linspace(0, 2 * np.pi, 8192, endpoint=False)
    c, s = np.cos(t), np.sin(t)
    xy = np.c_[cx + a * np.sign(c) * np.abs(c) ** (2 / n), cy + b * np.sign(s) * np.abs(s) ** (2 / n)]
    return Polygon(xy).simplify(tol, preserve_topology=True)
