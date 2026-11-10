"""Loads on the loose top: a grillage (beam-grid) plate model, no FEA library needed.

The top is a free plate (the squircle, top.build) resting on the frame's full-height pads (the posts and tenon
tops at the four corners; comfort.top_supports). Supports are compression-only: if a pad would have to pull the
top down, it lets go (the top lifts there). Loads are patches (forearms, a curled cat, paws, a laptop), clipped to
the top's outline: each patch's whole force goes on its part that is on the table, as fea.top_case does.

Grillage: a square grid of beams at spacing a in x and y over the top's bounding box, each node with (w, dw/dx,
dw/dy). Only nodes on the top count; a beam joins two of them, its strip width b the top's width over the strip
(a, or less at the edge). Beam bending stiffness E I with I = b t^3/12 and torsion G J with J = b t^3/6, which
reproduces a plate's bending and twisting rigidity (nu = 0). Curvatures come from central differences of the nodal
slopes (one-sided at the edge); stresses are sigma = E t kappa / 2 and tau = G t kappa_xy (outer ply).

Plywood is orthotropic: stiffer and stronger along the face grain (x here) than across it. The material
values are rough (TODO-verify, params [material] / [loads]); the results are for "how much margin",
not certification.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from shapely.geometry import Point, box

from . import comfort


@dataclass
class Patch:
    name: str
    force_n: float
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass
class Result:
    w: np.ndarray            # (ny, nx) deflection, mm (down positive)
    sigma_x: float           # peak bending stress along the face grain, MPa
    sigma_y: float           # peak across it
    tau: float               # peak twisting shear on the face, MPa
    util: float              # worst stress / strength (max of the three ratios)
    w_max: float
    reactions: dict          # corner -> N
    lifted: list             # support nodes that let go
    xs: np.ndarray
    ys: np.ndarray


def _beam(EI: float, L: float) -> np.ndarray:
    return EI / L ** 3 * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L * L, -6 * L, 2 * L * L],
                                   [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L * L, -6 * L, 4 * L * L]])


def _diff(f: np.ndarray, on: np.ndarray, a: float, axis: int) -> np.ndarray:
    """d f / d(axis) at the nodes on the top: central differences where both neighbours are on it, else one-sided
    (as np.gradient does at the array's ends); 0 where a node has no neighbour on the top that way."""
    f, on = np.moveaxis(f, axis, 0), np.moveaxis(on, axis, 0)
    d = np.zeros_like(f)
    nxt, prv = np.zeros_like(on), np.zeros_like(on)
    nxt[:-1], prv[1:] = on[1:] & on[:-1], on[:-1] & on[1:]
    fwd, bwd = np.zeros_like(f), np.zeros_like(f)
    fwd[:-1], bwd[1:] = (f[1:] - f[:-1]) / a, (f[1:] - f[:-1]) / a
    both = nxt & prv
    d[both] = (fwd[both] + bwd[both]) / 2
    d[nxt & ~prv], d[prv & ~nxt] = fwd[nxt & ~prv], bwd[prv & ~nxt]
    return np.moveaxis(d, 0, axis)


def solve(p, patches: list[Patch], n: int = 35, supports=None, compression_only: bool = True,
          outline=None) -> Result:
    """Deflection and stresses of the top under the patches. Coordinates are centred on the top (mm). outline: the
    plate (default the real top, comfort._top_centred); grid nodes off it carry nothing and patches are clipped to it."""
    M, Ld = p.material, p.loads
    t = M.t_nominal
    Ex, Ey, G = M.E_par, Ld.E_cross, Ld.G_plate
    top = comfort._top_centred(p) if outline is None else outline
    x0, y0, x1, y1 = top.bounds
    xs = np.linspace(x0, x1, n)
    ys = np.linspace(y0, y1, n)
    a = xs[1] - xs[0]
    near = top.buffer(1e-6)
    on = np.array([[near.contains(Point(x, y)) for x in xs] for y in ys])   # (ny, nx): nodes on the top
    idx = lambda i, j: 3 * (j * n + i)                       # node (i along x, j along y): w, rx=dw/dy, ry=dw/dx
    N = 3 * n * n
    K = np.zeros((N, N))
    for j in range(n):
        for i in range(n):
            for di, dj in ((1, 0), (0, 1)):
                i2, j2 = i + di, j + dj
                if i2 >= n or j2 >= n or not (on[j, i] and on[j2, i2]):
                    continue
                along_x = di == 1
                strip = (box(xs[i], ys[j] - a / 2, xs[i2], ys[j] + a / 2) if along_x else
                         box(xs[i] - a / 2, ys[j], xs[i] + a / 2, ys[j2]))
                b = strip.intersection(top).area / a              # a inside, a / 2 along a straight edge
                E = Ex if along_x else Ey
                kb = _beam(E * b * t ** 3 / 12, a)
                kt = G * b * t ** 3 / 6 / a * np.array([[1, -1], [-1, 1]])
                n1, n2 = idx(i, j), idx(i2, j2)
                bend = [n1, n1 + (2 if along_x else 1), n2, n2 + (2 if along_x else 1)]
                tors = [n1 + (1 if along_x else 2), n2 + (1 if along_x else 2)]
                K[np.ix_(bend, bend)] += kb
                K[np.ix_(tors, tors)] += kt
    F = np.zeros(N)
    nodes = [(i, j) for j in range(n) for i in range(n) if on[j, i]]
    for pa in patches:
        part = box(pa.x0, pa.y0, pa.x1, pa.y1).intersection(top)        # the part of the patch on the table
        if part.is_empty:
            raise ValueError(f"{pa.name!r} is off the top")
        hit = part.buffer(1e-6)
        sel = [(i, j) for i, j in nodes if hit.contains(Point(xs[i], ys[j]))]
        if not sel:                                           # patch smaller than the grid: nearest node on the top
            c = part.centroid
            sel = [min(nodes, key=lambda ij: (xs[ij[0]] - c.x) ** 2 + (ys[ij[1]] - c.y) ** 2)]
        for i, j in sel:
            F[idx(i, j)] += pa.force_n / len(sel)
    sup = comfort.top_supports(p) if supports is None else supports
    sup = sup.buffer(a / 2)
    snodes = [(i, j) for i, j in nodes if sup.contains(Point(xs[i], ys[j]))]
    active = set(snodes)
    dead = np.where(np.diag(K) <= 0)[0]                         # off the top (or a rotation nothing resists): held at 0
    for _ in range(30):                                       # compression-only supports
        fixed = np.union1d(sorted(idx(i, j) for i, j in active), dead).astype(int)
        free = np.setdiff1d(np.arange(N), fixed)
        u = np.zeros(N)
        u[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
        R = F - K @ u                                         # what the pads must push on the top (+ = upward, compression)
        neg = [(i, j) for i, j in active if R[idx(i, j)] < -1e-6]   # pad would have to pull the top down
        if not neg or not compression_only:
            break
        active -= set(neg)
    w = u[0::3].reshape(n, n)
    rx = u[1::3].reshape(n, n)                                # dw/dy
    ry = u[2::3].reshape(n, n)                                # dw/dx
    kx = _diff(ry, on, a, axis=1)
    ky = _diff(rx, on, a, axis=0)
    kxy = _diff(rx, on, a, axis=1)
    sx = np.abs(Ex * t * kx / 2).max()
    sy = np.abs(Ey * t * ky / 2).max()
    tau = np.abs(G * t * kxy).max()
    util = max(sx / M.f_m, sy / Ld.f_m_cross, tau / Ld.f_v_plate)
    reac = {}
    for i, j in active:
        k = ("+" if xs[i] > 0 else "-") + ("+" if ys[j] > 0 else "-")
        reac[k] = reac.get(k, 0.0) + R[idx(i, j)]
    return Result(w, float(sx), float(sy), float(tau), float(util), float(w.max()),
                  {k: round(v, 1) for k, v in sorted(reac.items())},
                  sorted(set(snodes) - active), xs, ys)


def cases(p) -> dict[str, list[Patch]]:
    """Owner's question (2026-10-20): a 7 kg cat and a laptop on the table, and someone napping hunched
    over it. Loads in N (kg x 9.81), patches in mm, centred on the top; the napper sits at the -y side."""
    Ld, h = p.loads, p.top.length / 2
    g = 9.81
    edge = -h
    nap = Ld.nap_kg * g
    cat = Ld.cat_kg * g
    lap = Ld.laptop_kg * g
    arms = lambda f: [Patch("forearms + head", f, -220, edge + 40, 220, edge + 240)]
    curled_cat = lambda x, y: [Patch("cat, curled up", cat, x - 150, y - 120, x + 150, y + 120)]
    paws = lambda f, x, y: [Patch("cat landing (2 front paws)", f, x - 60, y - 15, x + 60, y + 15)]
    laptop = [Patch("laptop", lap, -165, edge + 260, 165, edge + 490)]
    return {
        "nap: cat curled in the middle, laptop pushed back": arms(nap) + curled_cat(0, 120) + laptop,
        "nap: cat curled right next to your head": arms(nap) + curled_cat(0, edge + 360) + laptop,
        "slump: flopping down (x1.5) + cat jumping up mid-table (x4)":
            arms(Ld.slump * nap) + paws(Ld.cat_impact * cat, 0, 0) + laptop,
        "cat lands on the corner (x4), nobody else": paws(Ld.cat_impact * cat, h - 60, h - 60),
        "everyone at the very edge: slump + cat curled beside you":
            arms(Ld.slump * nap) + [Patch("cat at the edge", cat, 230, edge + 10, 420, edge + 200)] + laptop,
        "beyond normal: an 80 kg adult sits on the middle of an edge (x1.5)":
            [Patch("sitting", Ld.slump * Ld.sitter_kg * g, -200, edge, 200, edge + 250)],
    }


def self_weight(p, outline=None) -> Patch:
    """The top's own weight, from its real area (default the squircle), spread over it."""
    top = comfort._top_centred(p) if outline is None else outline
    W = top.area / 1e6 * p.material.t_nominal / 1000 * p.material.density_kg_m3 * 9.81
    return Patch("top's own weight", W, *top.bounds)


def lift_factor(p, pats: list[Patch], hi: float = 50.0) -> float:
    """How many times the loads (not the top's own weight) could grow before a corner of the top lifts
    off its pads (one corner carrying nothing). Returns hi if it never does within that."""
    sw = self_weight(p)

    def lifted(k):
        r = solve(p, [sw] + [Patch(x.name, k * x.force_n, x.x0, x.y0, x.x1, x.y1) for x in pats])
        return len(r.reactions) < 4 or min(r.reactions.values()) < 1.0
    if not lifted(hi):
        return hi
    lo = 1e-3
    if lifted(lo):
        return 0.0
    for _ in range(18):
        m = (lo * hi) ** 0.5
        lo, hi = (m, hi) if not lifted(m) else (lo, m)
    return lo


def report(p, lift: bool = True) -> dict:
    out = {}
    for name, pats in cases(p).items():
        r = solve(p, [self_weight(p)] + pats)
        out[name] = {"total_kg": round(sum(x.force_n for x in pats) / 9.81, 1),
                     "stress_MPa": [round(r.sigma_x, 1), round(r.sigma_y, 1), round(r.tau, 1)],
                     "use_of_strength_%": round(100 * r.util, 1),
                     "margin_x": round(1 / r.util, 1) if r.util > 0 else None,
                     "sag_mm": round(r.w_max, 1), "corner_reactions_N": r.reactions,
                     "lift_factor": round(lift_factor(p, pats), 1) if lift else None}
    return out



def deck_arms(p) -> dict:
    """The X deck's arms under a hand pressing on the heater ring (deck.hand_n) plus the heater: each of
    the four takes a quarter, as a cantilever from its corner pad (conservative: the ring is let tilt).
    The arms run at 45 deg to the face grain, so the cross-grain strength and half the along-grain
    stiffness are used (both rough, TODO-verify), on the thinnest stock."""
    from shapely.geometry import LineString
    from shapely.ops import unary_union
    from . import frame as fr, yagura
    L, M, D = fr.layout(p), p.material, p.deck
    held = unary_union(yagura.pads(p) + [yagura.ring(p)])
    line = LineString([(L.cx, L.cy), (L.cx + L.Lf / 2, L.cy + L.Wf / 2)])
    free = line.difference(held)
    free_mm = max((g.length for g in getattr(free, "geoms", [free])), default=0.0)
    F = (D.hand_n + p.comfort.heater_kg * 9.81) / 4
    t, w = M.t_min, D.arm_w
    sigma = F * free_mm / (w * t * t / 6)
    E = M.E_par / 2
    sag = F * free_mm ** 3 / (3 * E * w * t ** 3 / 12)
    return {"free_mm": round(free_mm), "load_N": round(F), "stress_MPa": round(sigma, 1),
            "use_of_strength_%": round(100 * sigma / p.loads.f_m_cross, 1), "sag_mm": round(sag, 1)}
