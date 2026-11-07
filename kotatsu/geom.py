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


def squircle_corners(poly: Polygon, size, n: float = 4.0, steps: int = 64) -> Polygon:
    """Replace a straight-edged polygon's corners with superellipse quarters (|x|^n + |y|^n = 1), convex and
    concave alike: the curvature fades into each edge instead of starting abruptly as a radius does.
    size(corner (x, y), convex: bool) -> mm along each edge from the corner (0 keeps it sharp). Each edge
    gives a corner at most half its length, so two corners can share a short edge (an S-curve)."""
    from shapely.geometry.polygon import orient
    poly = orient(poly.simplify(0.01), 1.0)
    pts = np.asarray(poly.exterior.coords)[:-1]
    m = len(pts)
    out = []
    t = np.linspace(np.pi / 2, 0, steps)
    x, y = np.cos(t) ** (2 / n), np.sin(t) ** (2 / n)
    for i in range(m):
        c, a_pt, b_pt = pts[i], pts[i - 1], pts[(i + 1) % m]
        la, lb = np.linalg.norm(a_pt - c), np.linalg.norm(b_pt - c)
        ua, ub = (a_pt - c) / la, (b_pt - c) / lb
        cross = (c - a_pt)[0] * (b_pt - c)[1] - (c - a_pt)[1] * (b_pt - c)[0]
        r = size((float(c[0]), float(c[1])), bool(cross > 0)) if abs(cross) > 1e-9 * la * lb else 0.0
        if r <= 0:
            out.append(c)
            continue
        ra, rb = min(r, la / 2), min(r, lb / 2)
        out.extend(c + np.outer(1 - x, ua * ra) + np.outer(1 - y, ub * rb))
    return Polygon(out).buffer(0)
