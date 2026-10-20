"""Loads on the loose top: a grillage (beam-grid) plate model, no FEA library needed.

The top is a free square plate resting on the frame's full-height pads (tenon tops and ear fingers at the
four corners; comfort.top_supports). Supports are compression-only: if a pad would have to pull the top
down, it lets go (the top lifts there). Loads are patches (forearms, a curled cat, paws, a laptop).

Grillage: a grid of beams at spacing a in x and y, each node with (w, dw/dx, dw/dy). Beam bending
stiffness E I with I = b t^3/12 (b = strip width) and torsion G J with J = b t^3/6, which reproduces a
plate's bending and twisting rigidity (nu = 0). Curvatures come from central differences of the nodal
slopes; stresses are sigma = E t kappa / 2 and tau = G t kappa_xy (outer ply).

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


def solve(p, patches: list[Patch], n: int = 35, supports=None, compression_only: bool = True) -> Result:
    """Deflection and stresses of the top under the patches. Coordinates are centred on the top (mm)."""
    M, Ld = p.material, p.loads
    t = M.t_nominal
    Ex, Ey, G = M.E_par, Ld.E_cross, Ld.G_plate
    half = p.top.length / 2
    xs = np.linspace(-half, half, n)
    ys = np.linspace(-half, half, n)
    a = xs[1] - xs[0]
    idx = lambda i, j: 3 * (j * n + i)                       # node (i along x, j along y): w, rx=dw/dy, ry=dw/dx
    N = 3 * n * n
    K = np.zeros((N, N))
    for j in range(n):
        for i in range(n):
            for di, dj in ((1, 0), (0, 1)):
                i2, j2 = i + di, j + dj
                if i2 >= n or j2 >= n:
                    continue
                along_x = di == 1
                edge = (j in (0, n - 1)) if along_x else (i in (0, n - 1))
                b = a / 2 if edge else a
                E = Ex if along_x else Ey
                kb = _beam(E * b * t ** 3 / 12, a)
                kt = G * b * t ** 3 / 6 / a * np.array([[1, -1], [-1, 1]])
                n1, n2 = idx(i, j), idx(i2, j2)
                bend = [n1, n1 + (2 if along_x else 1), n2, n2 + (2 if along_x else 1)]
                tors = [n1 + (1 if along_x else 2), n2 + (1 if along_x else 2)]
                K[np.ix_(bend, bend)] += kb
                K[np.ix_(tors, tors)] += kt
    F = np.zeros(N)
    for pa in patches:
        sel = [(i, j) for j in range(n) for i in range(n)
               if pa.x0 - 1e-6 <= xs[i] <= pa.x1 + 1e-6 and pa.y0 - 1e-6 <= ys[j] <= pa.y1 + 1e-6]
        if not sel:                                           # patch smaller than the grid: nearest node
            cx, cy = (pa.x0 + pa.x1) / 2, (pa.y0 + pa.y1) / 2
            sel = [(int(np.argmin(abs(xs - cx))), int(np.argmin(abs(ys - cy))))]
        for i, j in sel:
            F[idx(i, j)] += pa.force_n / len(sel)
    sup = comfort.top_supports(p) if supports is None else supports
    sup = sup.buffer(a / 2)
    snodes = [(i, j) for j in range(n) for i in range(n) if sup.contains(Point(xs[i], ys[j]))]
    active = set(snodes)
    for _ in range(30):                                       # compression-only supports
        fixed = sorted(idx(i, j) for i, j in active)
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
    kx = np.gradient(ry, a, axis=1)
    ky = np.gradient(rx, a, axis=0)
    kxy = np.gradient(rx, a, axis=1)
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


def self_weight(p) -> Patch:
    h = p.top.length / 2
    W = (2 * h) ** 2 / 1e6 * p.material.t_nominal / 1000 * p.material.density_kg_m3 * 9.81
    return Patch("top's own weight", W, -h, -h, h, h)


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
