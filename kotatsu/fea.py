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
from shapely import contains_xy, segmentize, set_precision
from shapely.geometry import Polygon
from shapely.ops import unary_union
from skfem import Basis, BilinearForm, ElementTriMorley, ElementTriP2, ElementVector, LinearForm, MeshTri
from skfem.helpers import dd, sym_grad


# ----------------------------------------------------------------------------- mesh
def _parts(g):
    return [x for x in getattr(g, "geoms", [g]) if not x.is_empty]


def mesh(poly, h: float, extra=(), h_edge: float | None = None, min_angle: float = 30.0,
         grid: float = 0.5) -> MeshTri:
    """Triangle mesh of `poly` (shapely, holes allowed), elements about h across, boundary pieces
    h_edge (default h / 2), with the outlines of the `extra` polygons (clipped to poly) built in, all snapped
    to a `grid` (mm) so lines a hair apart (a pad 0.2 mm inside an edge) merge instead of choking Triangle."""
    h_edge = h / 2 if h_edge is None else h_edge
    lines = [poly.boundary] + [e.intersection(poly).boundary for e in extra if not e.intersection(poly).is_empty]
    net = segmentize(set_precision(unary_union(lines), grid), h_edge)   # snap: no near-coincident lines
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
    """Peak |stresses| over the elements in `keep` and the worst use of strength among them: the largest
    of the three ratios (as loads.py), and Tsai-Hill's index, which also counts stresses that act together
    (off-axis bending, as in the deck's 45 deg arms: there it is the one to believe)."""
    sx, sy, tv = (float(np.abs(a[keep]).max()) if keep.any() else 0.0 for a in (r.sx, r.sy, r.txy))
    th = (r.sx / f_x) ** 2 - r.sx * r.sy / f_x ** 2 + (r.sy / f_y) ** 2 + (r.txy / f_v) ** 2
    th = np.where(keep, th, -1.0)
    i = int(th.argmax())
    at = tuple(round(float(x), 1) for x in r.m.p[:, r.m.t[:, i]].mean(axis=1)) if keep.any() else None
    return {"sx": sx, "sy": sy, "tau": tv, "util": max(sx / f_x, sy / f_y, tv / f_v),
            "tsai_hill": float(np.sqrt(max(th[i], 0.0))) if keep.any() else 0.0, "at": at}


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
            "pads": pads, "pad_N": per_pad, "idle_pads": idle, "load_N": float((q * _areas(m)).sum()), "result": r,
            "local": ~away}                              # elements over or next to a pad: local peaks


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


# ----------------------------------------------------------------------------- the X deck
def deck_cases(p) -> dict:
    """Hand loads (deck.hand_n over a fea.hand x fea.hand patch) on the heater ring, each with the heater on
    the cheek ears. World x-y polygons -> force (N)."""
    from shapely.geometry import box
    from . import frame as fr, yagura
    L, D, a = fr.layout(p), p.deck, p.fea.hand / 2
    rg = yagura.ring(p)
    x0, y0, x1, y1 = rg.bounds
    wx0, w0, wx1, w1 = fr.well(p)
    c0, c1 = fr.cheek_ys(p)
    xs0, xs1 = fr.cheek_xs(p)
    t = L.t
    ears = [box(xa, ya, xb, yb) for xa, xb in ((xs0 - t, xs0), (xs1, xs1 + t)) for ya, yb in ((c0, w0), (w1, c1))]
    heater = [(e, p.comfort.heater_kg * 9.81 / 4) for e in ears]
    ring_wood = rg.difference(box(wx0, w0, wx1, w1))
    hand = lambda x, y: [(box(x - a, y - a, x + a, y + a).intersection(ring_wood), D.hand_n)]
    return {"hand spread over the whole ring": heater + [(ring_wood, D.hand_n)],
            "hand on the ring beside a cheek (mid-side)": heater + hand((wx1 + x1) / 2, L.cy),
            "hand on a corner of the ring": heater + hand(x1 - a, y1 - a),
            "hand on the ring's end, over the cheek ears": heater + hand(L.cx, y1 - a)}


def deck_zones(p) -> dict:
    """The deck's regions (world x-y): the heater ring, the corner pads, the fillets (the wood the closing
    adds where arms meet ring and pads, plus a 3 mm skin) and what is left of the arms."""
    from . import yagura
    g = yagura.deck(p)
    rg, pd = yagura.ring(p).intersection(g), unary_union(yagura.pads(p)).intersection(g)
    fil = g.difference(unary_union([yagura.ring(p)] + yagura.arms(p) + yagura.pads(p))).buffer(3.0).intersection(g)
    arm = unary_union(yagura.arms(p)).intersection(g).difference(rg).difference(pd).difference(fil)
    return {"ring": rg.difference(fil), "fillets": fil, "arms": arm, "pads": pd.difference(fil)}


def deck_case(p, loads_, h: float | None = None, t: float | None = None, wedges: bool = True) -> dict:
    """The X deck (t thick, default the thinnest) on its plates' top edges (they push up only) and, if
    `wedges`, held down under its wedges (they push down only), under its own weight and `loads_`
    [(polygon, N)]. Both rigid: with wedges the corners are clamped (the stiffest the joints can be),
    without they only rest (the loosest). The real joint, a preloaded spring (stiffness.py), is between."""
    from . import yagura
    M, Ld, F = p.material, p.loads, p.fea
    h = F.deck_h if h is None else h
    t = M.t_min if t is None else t
    g = yagura.deck(p)
    below = [x.intersection(g) for x in yagura.plate_tops(p) + yagura.cross_tops(p)]
    above = [x.intersection(g) for x in yagura.wedge_footprints(p)]
    below, above = [x for x in below if x.area > 0], [x for x in above if x.area > 0]
    m = mesh(g, h, extra=below + above, h_edge=h / 3)
    q = np.full(m.t.shape[1], M.density_kg_m3 * 1e-9 * t * 9.81)
    for poly, f in loads_:
        q += pressure(m, poly, f)
    sv = np.where(in_any(m, below, at="vertices"))[0]
    hv = np.where(in_any(m, above, at="vertices"))[0] if wedges else np.zeros(0, int)
    r = plate(m, t, M.E_par, Ld.E_cross, Ld.G_plate, q, sv, hv)
    sup = unary_union(below + above)
    away = ~near(m, sup, t)
    args = (M.f_m, Ld.f_m_cross, Ld.f_v_plate)
    c = m.p[:, m.t].mean(axis=1)
    zone = lambda z: contains_xy(z, c[0], c[1]) & away
    return {"t": t, "h": h, "elements": m.t.shape[1], "sag_mm": float(r.w.max()),
            "load_N": float((q * _areas(m)).sum()), "held_N": float(-r.reaction[hv].sum()),
            "wedge_N": [float(-r.reaction[np.where(in_any(m, [x], at="vertices"))[0]].sum()) if wedges else 0.0
                        for x in above],
            "support_N": float(r.reaction.sum()),
            "plate_tops_N": [float(r.reaction[np.where(in_any(m, [x], at="vertices"))[0]].sum())   # (below: the plate
                             for x in below[:len(below) // 2]],                                    #  tops, then the crosspieces')
            "away": peaks(r, away, *args), "result": r, "local": ~away,
            **{k: peaks(r, zone(z), *args) for k, z in deck_zones(p).items()}}


def deck_report(p, h: float | None = None) -> dict:
    """Every deck_cases case, wedges tight (clamped corners) and slack (resting only), next to
    loads.deck_arms' cantilever. Use of strength is Tsai-Hill (the arms run at 45 deg to the grain)."""
    from . import loads
    f = lambda d: {"MPa": [round(d["sx"], 1), round(d["sy"], 1), round(d["tau"], 1)], "use_%": round(100 * d["tsai_hill"])}
    out = {"lumped (loads.deck_arms)": loads.deck_arms(p)}
    for name, ld in deck_cases(p).items():
        for w in (True, False):
            r = deck_case(p, ld, h, wedges=w)
            out[f"{name}, wedges {'tight' if w else 'slack'}"] = {
                "sag_mm": round(r["sag_mm"], 1), "max_wedge_N": round(max(r["wedge_N"], default=0.0)),
                **{k: f(r[k]) for k in ("fillets", "arms", "ring", "pads")}}
    return out


# ----------------------------------------------------------------------------- plane stress (P2)
@dataclass
class Contact:
    """Springs along the boundary facets whose midpoints lie in `zone`: they act on displacement component
    comp (0 = u, 1 = v), k N/mm per mm of edge. Closure = sign * displacement + c0; they push only while
    closure > 0 (unless bilateral). c0 < 0 is a gap, c0 > 0 an interference (a wedge tapped in)."""
    name: str
    zone: object
    comp: int
    sign: int
    k: float
    c0: float = 0.0
    bilateral: bool = False
    body: int = 0        # 0: to the ground (the deck); 1: to the floor, a rigid body; 2, 3...: other small
                         # rigid bodies (the crossing plate in a cross-lap slot, tying its two walls)


@dataclass
class PlaneResult:
    m: MeshTri
    u: np.ndarray
    su: np.ndarray       # per element, worst quadrature point: stress along u, along v, shear (MPa, signed)
    sv: np.ndarray
    tuv: np.ndarray
    forces: dict         # contact name -> total force it pushes on the plate (N, along its comp, + = +axis)
    open_: dict          # contact name -> share of its edge length not touching (0..1)


def _springs(m, b, c: Contact):
    """(dofs, spring constants) of a contact, lumped Simpson-wise onto the P2 edge nodes (1/6, 2/3, 1/6)."""
    f = m.boundary_facets()
    a, e = m.facets[:, f]
    mid = (m.p[:, a] + m.p[:, e]) / 2
    sel = contains_xy(c.zone, mid[0], mid[1])
    f, a, e = f[sel], a[sel], e[sel]
    L = np.linalg.norm(m.p[:, e] - m.p[:, a], axis=0)
    dofs = np.concatenate([b.nodal_dofs[c.comp][a], b.nodal_dofs[c.comp][e], b.facet_dofs[c.comp][f]])
    k = c.k * np.concatenate([L / 6, L / 6, 2 * L / 3])
    u, inv = np.unique(dofs, return_inverse=True)
    return u, np.bincount(inv, weights=k)


def plane(m: MeshTri, t: float, Eu: float, Ev: float, G: float, contacts: list[Contact], tractions=(),
          body_load=(0.0, 0.0), body_u: float | None = None, it: int = 60) -> PlaneResult:
    """Orthotropic plane stress (nu = 0), thickness t, P2 triangles. tractions: [(zone, (fu, fv))] total
    forces (N) spread evenly along the boundary facets in each zone. The contacts are the only supports:
    to the ground, or (Contact.body) to a rigid body that slides but doesn't turn (the floor under a leg,
    the deck being the ground), loaded by body_load (fu, fv), or moved to body_u along u (the frame's sway:
    the other legs hold the deck square over the floor). Its movement is in forces["body"]."""
    b = Basis(m, ElementVector(ElementTriP2()))

    @BilinearForm
    def stiff(u, v, w):
        e, d = sym_grad(u), sym_grad(v)
        return t * (Eu * e[0, 0] * d[0, 0] + Ev * e[1, 1] * d[1, 1] + 4 * G * e[0, 1] * d[0, 1])

    from scipy.sparse import bmat, coo_matrix, diags
    nb = max([1] + [int(c.body) for c in contacts])
    N = b.N + 2 * nb                                   # + each rigid body's (u, v)
    bd = lambda c: b.N + 2 * (int(c.body) - 1) + c.comp
    K = bmat([[stiff.assemble(b), None], [None, coo_matrix((2 * nb, 2 * nb))]]).tocsr()
    F = np.zeros(N)
    F[b.N:b.N + 2] = body_load
    for zone, force in tractions:
        fake = Contact("", zone, 0, 1, 1.0)
        for comp in (0, 1):
            fake.comp = comp
            d, w = _springs(m, b, fake)
            F[d] += force[comp] * w / w.sum()
    sp = [(c, *_springs(m, b, c)) for c in contacts]
    act = [np.ones(len(d), bool) for _, d, _ in sp]
    reg = diags(np.full(N, 1e-6))                      # a whisper of ground spring: no free rigid motion
    if body_u is not None:
        big = 1e9
        reg = reg + coo_matrix(([big], ([b.N], [b.N])), shape=(N, N))
        F[b.N] += big * body_u
    rel = lambda c, d, u: u[d] - (u[bd(c)] if c.body else 0.0)
    for _ in range(it):
        rows, cols, vals, rhs = [], [], [], F.copy()
        for (c, d, k), a in zip(sp, act):
            dd_, kk = d[a], k[a]
            rows += [dd_]; cols += [dd_]; vals += [kk]
            np.add.at(rhs, dd_, -c.sign * kk * c.c0)
            if c.body:                                  # k (u_node - u_body): couple the node to the body
                j = np.full(len(dd_), bd(c))
                rows += [dd_, j, j]; cols += [j, dd_, j]; vals += [-kk, -kk, kk]
                rhs[bd(c)] += (c.sign * kk * c.c0).sum()
        Ks = coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(N, N))
        u = spsolve((K + Ks + reg).tocsc(), rhs)
        new = [c.bilateral | (c.sign * rel(c, d, u) + c.c0 > 0) for (c, d, k) in sp]
        if all(np.array_equal(x, y) for x, y in zip(new, act)):
            break
        act = new
    forces, open_ = {}, {}
    for (c, d, k), a in zip(sp, act):
        forces[c.name] = forces.get(c.name, 0.0) - float((c.sign * k[a] * (c.sign * rel(c, d[a], u) + c.c0)).sum())
        open_[c.name] = float(k[~a].sum() / k.sum()) if k.sum() > 0 else 1.0
    forces["body"] = (float(u[b.N]), float(u[b.N + 1]))
    u = u[:b.N]
    e = b.interpolate(u)
    E = sym_grad(e)
    su, sv, tuv = Eu * E[0, 0], Ev * E[1, 1], 2 * G * E[0, 1]
    pick = lambda x: x[np.arange(x.shape[0]), np.abs(x).argmax(axis=1)]
    return PlaneResult(m, u, pick(su), pick(sv), pick(tuv), forces, open_)


# ----------------------------------------------------------------------------- the leg plates
def top_on_legs(p, case: str | None = None) -> dict:
    """What the top puts on the leg plate at its most loaded corner (N, from top_case): on its post and on its
    tenon ("A post", "A tenon": A as fea.leg_case names the plate). case: a loads.cases name; default the one
    loading a corner most."""
    from . import frame as fr, loads, yagura
    L, cs = fr.layout(p), loads.cases(p)
    best = None
    for name, pats in cs.items():
        if case is not None and name != case:
            continue
        r = top_case(p, pats)
        k, v = max(r["corner_N"].items(), key=lambda kv: kv[1])
        if best is None or v > best[2]:
            best = (name, r, v, k)
    name, r, _, k = best
    sx, sy = (1 if k[0] == "+" else -1), (1 if k[1] == "+" else -1)
    out = {"case": name, "corner": k, "A post": 0.0, "A tenon": 0.0}
    pu = yagura.post_u(p)
    cx, cy = sx * L.Lf / 2, sy * L.Wf / 2        # the corner, centred coords
    for g, R in zip(r["pads"], r["pad_N"]):
        c = g.centroid
        if (c.x > 0) != (sx > 0) or (c.y > 0) != (sy > 0):
            continue
        u = (abs(c.x - cx) + abs(c.y - cy)) / 2 ** 0.5             # along the diagonal from the corner
        out["A post" if u < pu + 5 else "A tenon"] += R
    return out


def leg_contacts(p, shape, rib_gap: float | None = None) -> list[Contact]:
    """The joint as springs (stiffness.joint's values, spread along the edges): the shoulders on the deck's
    underside, the wedge on its hole's top edge, the tenon's faces on the mortise ends and the post's inner face
    on the deck's cut-out.
    rib_gap: if given, the crosspiece sits in the head slot as a strut between its two walls at each crush rib,
    with this gap per side (mm; 0 = just touching): it ties the wood either side of the slot sideways (no shear).
    None: the slot is left empty (thin stock)."""
    from shapely.geometry import box
    from . import frame as fr, stiffness, yagura
    S, M, L = p.stiffness, p.material, fr.layout(p)
    t, zs, ks = M.t_nominal, L.z_deck_bot, S.E_perp * M.t_nominal / L.t
    band = lambda a, b: box(a, zs - 0.3, b, zs + 0.3)
    out = []
    for i, (a, b) in enumerate(stiffness._shoulders(p, shape)):
        out.append(Contact(f"shoulder {i}", band(a, b), 1, 1, ks))
    if rib_gap is not None:
        w, d, u0 = fr.slot_w(p), yagura.lap_depth(p), p.frame.ear
        za, zb = zs - d, zs
        for i, f in enumerate(p.fit.crush_rib_at):
            z = za + f * (zb - za)
            for uw, sg in ((u0 - w / 2, 1), (u0 + w / 2, -1)):
                out.append(Contact(f"rib {i} " + ("out" if sg > 0 else "in"), box(uw - 1.0, z - 6, uw + 1.0, z + 6), 0, sg, S.E_perp, -rib_gap, body=2 + i))
    ta, tb = yagura._tenon_u(p)
    uc, ts = (ta + tb) / 2, fr.thick_slot(p)
    _, z1 = yagura.leg_hole_z(p)
    wl, _ = yagura.wedge_dims(p)
    k_bear = S.E_perp * (wl - t) * t / L.t
    out.append(Contact("wedge", box(uc - ts / 2, z1 - 0.3, uc + ts / 2, z1 + 0.3), 1, -1, k_bear / ts))
    kh = M.E_par * t / S.bearing_len
    for u, sg in ((ta, -1), (tb, 1)):
        out.append(Contact("tenon face " + ("out" if sg < 0 else "in"), box(u - 0.3, zs + 0.5, u + 0.3, zs + L.t_min),
                           0, sg, kh, -p.fit.tight))
    pu = yagura.post_u(p)                                # the corner post meets the deck's cut-out after fit.tight
    if pu > 0:
        out.append(Contact("post on deck", box(pu - 0.3, zs + 0.5, pu + 0.3, zs + L.t_min), 0, 1, kh, -p.fit.tight))
    return out


def leg_zones(p) -> dict:
    """Plate-local regions to report: the haunch fillet, the head slot's root, the tenon's root reliefs, the
    wedge hole and the bridge of wood above it."""
    from shapely.geometry import Point, box
    from . import frame as fr, yagura
    F, Y, L = p.frame, p.yagura, fr.layout(p)
    zs, d, w = L.z_deck_bot, yagura.lap_depth(p), fr.slot_w(p)
    ta, tb = yagura._tenon_u(p)
    uc, ts = (ta + tb) / 2, fr.thick_slot(p)
    z0, z1 = yagura.leg_hole_z(p)
    z = {"haunch fillet": Point(Y.leg_narrow, Y.leg_haunch_top - Y.leg_haunch_drop).buffer(25),
         "slot root": Point(F.ear, zs - d).buffer(w / 2 + 10),
         "root reliefs": Point(ta, zs).buffer(10).union(Point(tb, zs).buffer(10)),
         "bridge": box(uc - ts / 2 - 2, z1, uc + ts / 2 + 2, L.H)}
    z["wedge hole"] = box(uc - ts / 2, z0, uc + ts / 2, z1).buffer(6).difference(z["bridge"])
    return z


def leg_case(p, which: str, H: float, top: dict | None = None, N_deck: float | None = None,
             h: float | None = None, t: float | None = None, ribs: bool = False) -> dict:
    """The leg plate in its own plane, t thick (default the thinnest), standing on a rigid floor (end grain on
    it, gripping it) and held at the deck by the joint springs; the top presses on its post and tenon with `top`
    (top_on_legs). Grain runs up the leg (v). which must be "A" (the name the wedged plate had when the "+" legs
    had two plates a corner; kept so the reports and the cached FEA keep their labels).
    Its wedge is first tapped in to stiffness.wedge_preload. Then the floor moves sideways by the sway that makes
    this plate and its mirror image (the plate at the opposite end of the push) take their share of H between
    them, as stiffness.frame_sway shares a push; both senses are reported (worst of each).
    ribs: the crosspiece, t thick, bears on the head slot's crush ribs (leg_contacts rib_gap); else the slot is empty."""
    from types import SimpleNamespace
    from shapely.geometry import box
    from . import frame as fr, stiffness, yagura
    M, Ld, F, L = p.material, p.loads, p.fea, fr.layout(p)
    h = F.leg_h if h is None else h
    t = M.t_min if t is None else t
    top = {} if top is None else top
    H_in = H
    if which != "A":                  # one plate a corner
        raise ValueError("the legs have one plate a corner: which = 'A'")
    c = stiffness._cosines(p, "x")    # each plate takes its cosine's share of the push in its own plane; the pair
    H = H * 2 * max(abs(x) for x in c) / sum(x * x for x in c)    # below (opposite senses) then totals this
    N_deck = stiffness.deck_weight_n(p) / 4 if N_deck is None else N_deck
    shape = yagura.leg_plate(p)
    pu, (ta, tb) = yagura.post_u(p), yagura._tenon_u(p)
    on_post, on_tenon = top.get("A post", 0.0), top.get("A tenon", 0.0)
    edge = lambda a, b, v: box(a, v - 0.3, b, v + 0.3)
    m = mesh(shape, h, h_edge=h / 2)
    trac = [(edge(0, pu, L.H), (0.0, -on_post))] + ([(edge(ta, tb, L.H), (0.0, -on_tenon))] if on_tenon else [])
    kf = M.E_par * M.t_nominal / p.stiffness.bearing_len               # end grain on the floor, as on the deck
    foot = edge(-1, p.frame.leg_width + 1, 0.0)
    gap = (fr.slot_w(p) - 2 * p.fit.crush_rib - t) / 2 if ribs else None
    cs = leg_contacts(p, shape, rib_gap=gap) + [
        Contact("floor", foot, 1, -1, kf, body=True), Contact("floor (grip)", foot, 0, -1, kf, bilateral=True, body=True)]
    Nv = N_deck + on_post + on_tenon
    run = lambda **kw: plane(m, t, Ld.E_cross, M.E_par, Ld.G_plate, cs, trac, **kw)
    wedge = next((c for c in cs if c.name == "wedge"), None)
    P0, xs, fs = p.stiffness.wedge_preload, [0.02, 0.08], []         # tap the wedge in: secant on interference
    for i in range(8):
        if i >= 2:
            xs.append(xs[-1] + (P0 - fs[-1]) * (xs[-1] - xs[-2]) / ((fs[-1] - fs[-2]) or 1e-9))
        wedge.c0 = xs[i]
        fs.append(run(body_load=(0.0, Nv), body_u=0.0).forces["wedge"])
        if i >= 2 and abs(fs[-1] - P0) < 1.0:
            break
    pair = lambda d: (run(body_load=(0.0, Nv), body_u=d), run(body_load=(0.0, Nv), body_u=-d))
    tot = lambda rr: rr[0].forces["floor (grip)"] - rr[1].forces["floor (grip)"]
    ds, rs = [1.0, 3.0], []                                              # sway: secant on the pair's total
    for i in range(8):
        if i >= 2:
            ds.append(ds[-1] + (H - tot(rs[-1])) * (ds[-1] - ds[-2]) / ((tot(rs[-1]) - tot(rs[-2])) or 1e-9))
        rs.append(pair(ds[i]))
        if i >= 2 and abs(tot(rs[-1]) - H) < 0.5:
            break
    res, delta = list(rs[-1]), ds[len(rs) - 1]
    zones = leg_zones(p)
    c = m.p[:, m.t].mean(axis=1)
    loaded = unary_union([z for z, _ in trac] + [x.zone for x in cs]).buffer(3.0)
    if wedge is not None:          # the wedge's bearing spreads further into the bridge: its peak 3-6 mm down is still
        loaded = loaded.union(wedge.zone.buffer(6.0))   # local crushing, and mesh-dependent (73-104 % at 2-4 mm)
    rest = ~contains_xy(unary_union(list(zones.values())).union(loaded), c[0], c[1])
    args = (M.f_m, Ld.f_m_cross, Ld.f_v_plate)
    clear = ~contains_xy(loaded, c[0], c[1])                          # contact ends: local bearing peaks
    sel = {**{k: contains_xy(z, c[0], c[1]) & clear for k, z in zones.items()}, "leg elsewhere": rest,
           "contact edges": ~clear}
    out = {}
    for k, msk in sel.items():                                        # worst of the two senses
        pk = [peaks(SimpleNamespace(sx=x.sv, sy=x.su, txy=x.tuv, m=m), msk, *args) for x in res]   # sx = along grain
        out[k] = max(pk, key=lambda d: d["tsai_hill"])
    for x in res:
        x.forces.pop("body")
    return {"which": which, "H": H_in, "H_plate_pair": H, "t": t, "h": h, "elements": m.t.shape[1], "zones": out, "sway_mm": delta,
            "local": ~clear,                                                   # contact ends: bearing peaks
            "forces": [{k: round(v, 1) for k, v in x.forces.items()} for x in res],
            "open": [{k: round(v, 2) for k, v in x.open_.items()} for x in res], "result": res}


def leg_report(p, h: float | None = None) -> dict:
    """The leg plate under fea.push_n (alone, and with the top's worst corner load on it), with that load alone,
    and on nominal stock with the crosspiece on the crush ribs; next to stiffness.stresses / frame_sway. Use of
    strength is Tsai-Hill."""
    from . import stiffness, yagura
    H = p.fea.push_n
    top = top_on_legs(p)
    lump = stiffness.stresses(p, H)
    out = {"lumped (stiffness.stresses)": {"leg_MPa": float(lump["leg_MPa"]),
                                           "wedge_bridge_shear_MPa": float(lump["wedge_bridge_shear_MPa"]),
                                           "sway_mm": round(stiffness.frame_sway(p, H, "x")["sway_mm"], 1)},
           "top load": {k: (round(v) if isinstance(v, float) else v) for k, v in top.items()}}
    runs = {f"A, {H:g} N push": ("A", H, None), f"A, {H:g} N push + top load": ("A", H, top),
            "A, top load only": ("A", 0.0, top),
            f"A, {H:g} N push, nominal stock, crosspiece on the crush ribs": ("A", H, None)}
    for name, (w, hh, tp) in runs.items():
        nom = "nominal" in name
        r = leg_case(p, w, hh, tp, h=h, t=p.material.t_nominal if nom else None, ribs=nom)
        out[name] = {"sway_mm": None if r["sway_mm"] is None else round(r["sway_mm"], 1),
                     "wedge_N": max((x.get("wedge", 0.0) for x in r["forces"]), default=0.0),
                     **{k: {"MPa": [round(v["sx"], 1), round(v["sy"], 1), round(v["tau"], 1)],
                            "use_%": round(100 * v["tsai_hill"]), "at": v["at"]} for k, v in r["zones"].items()}}
    return out
