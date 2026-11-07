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


def peaks(r: PlateResult, keep: np.ndarray, f_x: float, f_y: float, f_v: float) -> dict:
    """Peak |stresses| over the elements in `keep` and the worst use of strength among them."""
    sx, sy, tv = (float(np.abs(a[keep]).max()) if keep.any() else 0.0 for a in (r.sx, r.sy, r.txy))
    return {"sx": sx, "sy": sy, "tau": tv, "util": max(sx / f_x, sy / f_y, tv / f_v)}


def near(m: MeshTri, geom, d: float) -> np.ndarray:
    """Elements whose centroid lies within d of geom."""
    c = m.p[:, m.t].mean(axis=1)
    return contains_xy(geom.buffer(d), c[0], c[1])


# ----------------------------------------------------------------------------- the top
def top_model(p):
    """(outline, support pads) of the top, centred on the top (mm): what loads.py and comfort.py use."""
    from . import comfort
    return comfort._top_centred(p), comfort.top_supports(p)


def top_case(p, patches, h: float | None = None, t: float | None = None) -> dict:
    """The top (squircle, t thick: default the thinnest stock) on the post and tenon tops, under its own
    weight and `patches` (loads.Patch, centred mm). Each patch's force spreads evenly over its part on the top."""
    from shapely.geometry import box
    M, Ld, F = p.material, p.loads, p.fea
    h = F.top_h if h is None else h
    t = M.t_min if t is None else t
    top, sup = top_model(p)
    boxes = [box(x.x0, x.y0, x.x1, x.y1).intersection(top) for x in patches]
    pads = _parts(sup)
    m = mesh(top, h, extra=pads)
    q = np.full(m.t.shape[1], M.density_kg_m3 * 1e-9 * t * 9.81)         # own weight, N/mm^2
    for x, b in zip(patches, boxes):
        q += pressure(m, b, x.force_n)
    sv = np.where(in_any(m, pads, at="vertices"))[0]
    r = plate(m, t, M.E_par, Ld.E_cross, Ld.G_plate, q, sv)
    away = ~near(m, sup, t)
    pk, pa = peaks(r, np.ones(m.t.shape[1], bool), M.f_m, Ld.f_m_cross, Ld.f_v_plate), \
        peaks(r, away, M.f_m, Ld.f_m_cross, Ld.f_v_plate)
    per_pad = [float(r.reaction[np.where(in_any(m, [g], at="vertices"))[0]].sum()) for g in pads]
    corners = {}
    for g, R in zip(pads, per_pad):
        c = g.centroid
        k = ("+" if c.x > 0 else "-") + ("+" if c.y > 0 else "-")
        corners[k] = corners.get(k, 0.0) + R
    idle = [i for i, R in enumerate(per_pad) if R < 0.5]                  # pads carrying (next to) nothing
    return {"t": t, "h": h, "elements": m.t.shape[1], "sag_mm": float(r.w.max()), "rise_mm": float(-r.w.min()),
            "peak": pk, "away": pa, "corner_N": {k: round(v, 1) for k, v in sorted(corners.items())},
            "pads": pads, "pad_N": per_pad, "idle_pads": idle, "load_N": float((q * _areas(m)).sum()), "result": r}


def pressure(m: MeshTri, patch, force: float) -> np.ndarray:
    """Element pressures (N/mm^2) spreading `force` evenly over `patch`: each element gets its overlap's
    share, so the patch's edges needn't be in the mesh (they often run right along the top's edge)."""
    from shapely import area, intersection, polygons
    if patch.area <= 0:
        return np.zeros(m.t.shape[1])
    tris = polygons(np.transpose(m.p[:, m.t], (2, 1, 0)))
    return force / patch.area * area(intersection(tris, patch)) / _areas(m)


def _areas(m: MeshTri) -> np.ndarray:
    x, y = m.p[:, m.t]
    return 0.5 * np.abs((x[1] - x[0]) * (y[2] - y[0]) - (x[2] - x[0]) * (y[1] - y[0]))


def top_report(p, h: float | None = None, t: float | None = None) -> dict:
    """Every case in loads.cases(p): FE sag and stresses (one thickness clear of the pads), next to
    loads.solve's grillage at the same thickness. (loads.report itself is at the nominal thickness.)"""
    from types import SimpleNamespace
    from . import loads
    t = p.material.t_min if t is None else t
    q = SimpleNamespace(**vars(p))
    q.material = SimpleNamespace(**vars(p.material))
    q.material.t_nominal = t                                            # loads.solve reads t_nominal
    out = {}
    for name, pats in loads.cases(p).items():
        r = top_case(p, pats, h, t)
        g = loads.solve(q, [loads.self_weight(q)] + pats)
        out[name] = {"sag_mm": round(r["sag_mm"], 1), "stress_MPa": [round(r["away"][k], 1) for k in ("sx", "sy", "tau")],
                     "use_%": round(100 * r["away"]["util"], 1),
                     "peak_on_pads_MPa": round(max(r["peak"][k] for k in ("sx", "sy")), 1),
                     "corner_N": r["corner_N"], "pads_idle": len(r["idle_pads"]), "pads": len(r["pads"]),
                     "grillage": {"sag_mm": round(g.w_max, 1), "stress_MPa": [round(g.sigma_x, 1), round(g.sigma_y, 1),
                                  round(g.tau, 1)], "use_%": round(100 * g.util, 1), "corner_N": g.reactions}}
    return out
