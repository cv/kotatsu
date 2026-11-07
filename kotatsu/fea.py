"""Finite-element checks of the top, the X deck and the leg plates (v2), to confirm or correct the lumped
models in kotatsu/loads.py and kotatsu/stiffness.py. Results and method: docs/fea.md.

  * mesh(): a quality triangle mesh (Shewchuk's Triangle) of a shapely outline, with the edges of the
    support pads and load patches built into it, so each element is wholly in or out of them.
  * plate(): Kirchhoff plate bending, Morley triangles (scikit-fem), orthotropic with nu = 0 as in
    loads.py, on compression-only supports (an active-set loop: a support that would have to pull lets go).
  * plane(): plane stress, quadratic (P2) triangles, orthotropic, with contact springs that only push
    (the leg's shoulders on the deck, the wedge on its hole, the tenon's faces on the mortise ends).

Plywood is treated as a homogeneous orthotropic plate: the face grain's modulus and strength for bending
along it, the cross values across it ([material], [loads], [fea] in params.toml; all rough, TODO-verify).
Stresses are at the faces (bending) or in-plane (legs). Kirchhoff's peak right over a small rigid pad is
mesh-dependent (the reaction concentrates on the pad's rim), so peaks are also given away from the pads,
one plate thickness clear of them; that is the number to hold against the strength.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import triangle
from scipy.sparse.linalg import spsolve
from shapely import contains_xy, segmentize
from shapely.geometry import Polygon
from shapely.ops import unary_union
from skfem import Basis, BilinearForm, ElementTriMorley, LinearForm, MeshTri
from skfem.helpers import dd


# ----------------------------------------------------------------------------- mesh
def _parts(g):
    return [x for x in getattr(g, "geoms", [g]) if not x.is_empty]


def mesh(poly, h: float, extra=(), h_edge: float | None = None, min_angle: float = 30.0) -> MeshTri:
    """Triangle mesh of `poly` (shapely, holes allowed), elements about h across, boundary pieces
    h_edge (default h / 2), with the outlines of the `extra` polygons (clipped to poly) built in."""
    h_edge = h / 2 if h_edge is None else h_edge
    lines = [poly.boundary] + [e.intersection(poly).boundary for e in extra if not e.intersection(poly).is_empty]
    net = segmentize(unary_union(lines), h_edge)
    vid, verts, segs = {}, [], []
    for ln in _parts(net):
        if ln.geom_type != "LineString":
            continue
        ids = []
        for x, y in ln.coords:
            k = (round(x, 6), round(y, 6))
            if k not in vid:
                vid[k] = len(verts)
                verts.append(k)
            ids.append(vid[k])
        segs += [(a, b) for a, b in zip(ids[:-1], ids[1:]) if a != b]
    data = {"vertices": np.array(verts, float), "segments": np.array(sorted({tuple(sorted(s)) for s in segs}))}
    holes = [Polygon(r).representative_point().coords[0] for g in _parts(poly) for r in g.interiors]
    if holes:
        data["holes"] = np.array(holes)
    area = h * h * np.sqrt(3) / 4
    out = triangle.triangulate(data, f"pq{min_angle:g}a{area:.6g}")
    P, T = out["vertices"], out["triangles"]
    c = P[T].mean(axis=1)
    T = T[contains_xy(poly.buffer(1e-6), c[:, 0], c[:, 1])]
    used = np.unique(T)
    remap = -np.ones(len(P), int)
    remap[used] = np.arange(len(used))
    return MeshTri(P[used].T.copy(), remap[T].T.copy())


def in_any(m: MeshTri, polys, tol: float = 1e-6, at: str = "elements") -> np.ndarray:
    """Mask of the mesh's element centroids (or vertices) inside any of `polys`."""
    pts = m.p.T if at == "vertices" else m.p[:, m.t].mean(axis=1).T
    mask = np.zeros(len(pts), bool)
    for g in polys:
        mask |= contains_xy(g.buffer(tol), pts[:, 0], pts[:, 1])
    return mask


# ----------------------------------------------------------------------------- Kirchhoff plate (Morley)
@dataclass
class PlateResult:
    m: MeshTri
    w: np.ndarray            # vertex deflections, mm (down positive)
    sx: np.ndarray           # per element: face bending stress along x, across, twisting shear (MPa, signed)
    sy: np.ndarray
    txy: np.ndarray
    reaction: np.ndarray     # per vertex: what the supports push on the plate (N, + = up); 0 where free
    lifted: np.ndarray       # support vertices that let go
    sup: np.ndarray          # support vertices (all, active or not)


def plate(m: MeshTri, t: float, Ex: float, Ey: float, G: float, q: np.ndarray, sup: np.ndarray,
          hold: np.ndarray | None = None, it: int = 60) -> PlateResult:
    """Orthotropic Kirchhoff plate (nu = 0), thickness t, under element pressures q (N/mm^2, down +).
    sup: vertices resting on pads below (push up only); hold: vertices under something above them that
    only pushes down (the deck's wedges). Rigid, compression-only: an active-set loop."""
    D11, D22, D66 = Ex * t ** 3 / 12, Ey * t ** 3 / 12, G * t ** 3 / 12
    b = Basis(m, ElementTriMorley())

    @BilinearForm
    def bend(u, v, w):
        U, V = dd(u), dd(v)
        return D11 * U[0, 0] * V[0, 0] + D22 * U[1, 1] * V[1, 1] + 4 * D66 * U[0, 1] * V[0, 1]

    @LinearForm
    def load(v, w):
        return w.q * v

    K = bend.assemble(b).tocsr()
    f = load.assemble(b, q=np.repeat(np.asarray(q, float)[:, None], b.X.shape[1], axis=1))
    hold = np.zeros(0, int) if hold is None else np.asarray(hold, int)
    verts = np.concatenate([np.asarray(sup, int), hold])
    sgn = np.concatenate([np.ones(len(sup)), -np.ones(len(hold))])   # +1: pad below, -1: stop above
    dofs = b.nodal_dofs[0][verts]
    active = np.ones(len(verts), bool)
    for _ in range(it):
        fixed = dofs[active]
        free = np.setdiff1d(np.arange(b.N), fixed)
        u = np.zeros(b.N)
        u[free] = spsolve(K[free][:, free].tocsc(), f[free])
        R = K @ u - f                                    # support force on the plate, + = down
        push_up = -R[dofs] * sgn                         # > 0: the support pushes, as it can
        into = u[dofs] * sgn > 1e-9                      # a let-go vertex moving into its support
        new = (active & (push_up > -1e-9)) | (~active & into)
        if np.array_equal(new, active):
            break
        active = new
    H = b.interpolate(u).hess                           # (2, 2, nel, nqp): constant per Morley element
    kx, ky, kxy = H[0, 0][:, 0], H[1, 1][:, 0], H[0, 1][:, 0]
    reac = np.zeros(m.p.shape[1])
    np.add.at(reac, verts[active], -R[dofs[active]])
    w = u[b.nodal_dofs[0]]
    return PlateResult(m, w, Ex * t / 2 * kx, Ey * t / 2 * ky, G * t * kxy, reac,
                       np.asarray(sup, int)[~active[:len(sup)]], np.asarray(sup, int))
