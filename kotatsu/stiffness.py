"""Wobble (racking) check for the yagura frame: a lumped spring model, no FEA.

How the frame resists a sideways push H at the top
  The deck is a stiff plate; each "+" leg hangs from it and stands on the floor. A push in x is taken by
  the four "A" plates bending in their own plane (the "B" plates bend the weak way and are ignored),
  a push in y by the four "B" plates. Each plate deflects at the floor by
      delta = theta * L + H_i L^3 / (3 E I)          (joint rotation + plate bending; L = leg height)
  and the joint rotation theta comes from the leg <-> deck joint:
    * shoulders: the plate's top edge presses up on the deck's underside. Modelled as a row of
      compression-only springs (Winkler), k = E_perp * t_plate / t_deck per mm of shoulder, E_perp
      being plywood's (soft) modulus across its thickness;
    * wedge: lies on the deck top and pulls the tenon up; a compression-only spring, the wedge's
      bearing on the deck in series with the wood above the wedge hole;
    * preload: tapping the wedge in clamps the deck between shoulder and wedge with force P0.
  With the wedge tight every spring works and the joint is stiff. Past some moment one side of the
  joint unloads (a gap opens) and the stiffness drops: that's where wobble starts. Plates at the two
  ends of a side are mirror images, so for either push direction two legs work in their strong sense
  and two in their weak sense.

All material values are TODO-verify (params [material] / [stiffness]); results are estimates for
comparing options and spotting weak links, not certification.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from shapely.geometry import box

from . import frame as fr
from . import yagura


@dataclass
class Joint:
    u: np.ndarray        # vertical spring positions along the plate top (mm, plate-local u)
    k: np.ndarray        # their stiffnesses (N/mm): shoulders, then the wedge (last)
    c0: np.ndarray       # preload compressions (mm)
    is_wedge: np.ndarray # bool mask
    uw: float            # wedge position (moments are taken about (uw, deck underside))
    hz: np.ndarray       # horizontal springs (tenon faces against the mortise ends): height above the deck underside
    hside: np.ndarray    # -1 = tenon's outer face (bears when the plate moves -u), +1 = inner face
    hk: float            # stiffness of each horizontal spring (N/mm)
    gap: float           # in-plane clearance per side before a tenon face touches (mm)
    uf: float            # where the floor reaction acts (middle of the foot)


def _shoulders(p, shape) -> list[tuple[float, float]]:
    L = fr.layout(p)
    ta, tb = yagura._tenon_u(p)
    strip = shape.intersection(box(-1e3, L.z_deck_bot - 0.6, 1e4, L.z_deck_bot - 0.1))
    u_deck = L.Lf / 2 - yagura.corner_cut(p) if yagura.post_u(p) else -1e3   # deck starts here (corner cut-outs)
    segs = []
    for g in getattr(strip, "geoms", [strip]):
        a, _, b, _ = g.bounds
        a = max(a, u_deck)
        for lo, hi in ((a, min(b, ta)), (max(a, tb), b)):
            if hi - lo > 0.5:
                segs.append((lo, hi))
    return segs


def joint(p, shape) -> Joint:
    S, M, L = p.stiffness, p.material, fr.layout(p)
    t = M.t_nominal
    ks = S.E_perp * t / L.t                                     # N/mm per mm of shoulder
    us, kk = [], []
    for a, b in _shoulders(p, shape):
        n = max(2, int(round(b - a)))
        xs = np.linspace(a, b, n + 1)
        mid = (xs[:-1] + xs[1:]) / 2
        us += list(mid)
        kk += [ks * (b - a) / n] * n
    ta, tb = yagura._tenon_u(p)
    uw = (ta + tb) / 2
    wl, _ = yagura.wedge_dims(p, "leg")
    k_bear = S.E_perp * (wl - t) * t / L.t                     # wedge pressing on the deck top
    z0, z1 = yagura.leg_hole_z(p)
    bridge = L.H - z1                                           # wood above the wedge hole
    span = fr.thick_slot(p)
    I_b = t * bridge ** 3 / 12                                  # fixed-fixed bridge, central load
    k_bridge = 192 * M.E_par * I_b / span ** 3
    kw = 1 / (1 / k_bear + 1 / k_bridge)
    u = np.array(us + [uw])
    k = np.array(kk + [kw])
    is_w = np.zeros(len(u), bool)
    is_w[-1] = True
    c0 = np.zeros(len(u))       # shoulders: no interference; the wedge's is set by preload() below
    # tenon faces bearing on the mortise ends, near the deck's bottom and top faces
    hz = np.array([1.0, L.t - 1.0, 1.0, L.t - 1.0])
    hside = np.array([-1, -1, 1, 1])
    hk = M.E_par * t * (L.t / 2) / S.bearing_len                # in-plane bearing, half the deck thickness each
    foot = shape.intersection(box(-1e3, -1, 1e4, 1.0))
    uf = (foot.bounds[0] + foot.bounds[2]) / 2
    J = Joint(u, k, c0, is_w, uw, hz, hside, hk, p.fit.tight, uf)
    preload(J, S.wedge_preload)
    return J


def preload(J: Joint, P0: float, N: float = 0.0) -> None:
    """Tap the wedge in: raise its interference until it pulls with P0 at rest. (The plate settles,
    possibly rotating until the tenon jams in the mortise, which then carries the clamp's couple.)"""
    lo, hi = 0.0, 5.0
    for _ in range(50):
        m = (lo + hi) / 2
        J.c0[-1] = m
        x, c = solve_joint(J, N, 0.0, 341.0)
        fw = J.k[-1] * max(c[-1], 0.0) if x is not None else 0.0
        lo, hi = (m, hi) if fw < P0 else (lo, m)
    J.c0[-1] = (lo + hi) / 2


EPS = 0.002   # mm: contact smoothing (softplus) so Newton can cross contact changes


def _pos(c):
    return EPS * np.logaddexp(0.0, c / EPS)


def _forces(J: Joint, x: np.ndarray):
    """Joint spring forces on the plate for x = (s, w, th): plate shift along u, lift, CCW rotation about
    (uw, deck underside). Returns (vertical forces, horizontal forces, vertical compressions)."""
    s_, w, th = x
    d = w + th * (J.u - J.uw)
    c = np.where(J.is_wedge, J.c0 - d, J.c0 + d)
    f = J.k * _pos(c)
    Fv = np.where(J.is_wedge, f, -f)                            # wedge pulls up, shoulders push down
    dx = s_ - th * J.hz                                         # sideways movement of the tenon faces
    ch = np.where(J.hside < 0, -dx, dx) - J.gap
    Fh = -J.hside * J.hk * _pos(ch)
    return Fv, Fh, c


def solve_joint(J: Joint, N: float, H: float, Lleg: float, guess=None):
    """Balance the plate at its joint: net upward push N (its share of deck + heater), a sideways force
    H at the foot (shear H and moment H*Lleg at the joint). Returns (x, vertical compressions) or (None, None)."""
    x = np.zeros(3) if guess is None else np.array(guess, float)

    def res(x):
        Fv, Fh, _ = _forces(J, x)
        return np.array([H + Fh.sum(), N + Fv.sum(),
                         H * Lleg + N * (J.uf - J.uw) + (Fv * (J.u - J.uw)).sum() - (Fh * J.hz).sum()])

    if H != 0 and abs(x[0]) < J.gap:                            # shear needs a tenon face in contact:
        x[0] = np.sign(H) * (J.gap + 0.005)                     # start there instead of in the clearance
    scale = np.array([1.0, 1.0, 1e-2])
    for _ in range(400):
        r = res(x)
        if np.all(np.abs(r * scale) < 1e-6):
            _, _, c = _forces(J, x)
            return x, c
        h = np.array([1e-6, 1e-6, 1e-8])
        Jm = np.column_stack([(res(x + np.eye(3)[i] * h[i]) - r) / h[i] for i in range(3)])
        try:
            dx = np.linalg.lstsq(Jm, -r, rcond=None)[0]
        except np.linalg.LinAlgError:
            return None, None
        step = 1.0
        while step > 1e-6 and np.abs(res(x + step * dx) * scale).sum() > np.abs(r * scale).sum():
            step /= 2
        x = x + step * dx
        if abs(x[2]) > 0.3 or abs(x[0]) > 20:
            return None, None
    return None, None


def section(shape, z: float, t: float) -> tuple[float, float]:
    """In-plane bending (I mm^4, W mm^3) of a plate's horizontal cross-section at height z: the solid
    u-intervals there (slots and windows leave gaps), t thick."""
    cut = shape.intersection(box(-1e4, z - 0.25, 1e4, z + 0.25))
    segs = [(g.bounds[0], g.bounds[2]) for g in getattr(cut, "geoms", [cut]) if not g.is_empty]
    if not segs:
        return 0.0, 0.0
    A = sum(b - a for a, b in segs)
    uc = sum((b - a) * (a + b) / 2 for a, b in segs) / A
    I = sum(t * ((b - a) ** 3 / 12 + (b - a) * ((a + b) / 2 - uc) ** 2) for a, b in segs)
    c = max(max(abs(a - uc), abs(b - uc)) for a, b in segs)
    return I, I / c


def bend_compliance(p, shape, n: int = 60) -> float:
    """Floor deflection per newton of a plate fixed at the deck, pushed sideways at the floor:
    integral of z^2 / (E I(z)) dz, from the plate's real cross-sections."""
    L, M = fr.layout(p), p.material
    zs = np.linspace(2.0, L.z_deck_bot - 2.0, n)
    vals = [z * z / (M.E_par * max(section(shape, z, M.t_nominal)[0], 1.0)) for z in zs]
    return float(np.trapezoid(vals, zs))


@dataclass
class PlateCurve:
    H: np.ndarray        # lateral force on this plate at the floor (N), negative..positive
    delta: np.ndarray    # floor displacement relative to the deck (mm)
    gap_H: tuple         # (negative, positive) force at which the plate starts to soften (2x compliance)
    rest_tilt: float     # how far the foot swings (mm) as the wedge is tapped in, if nothing stops it


def plate_curve(p, shape, N: float, Hmax: float = 300.0, n: int = 121) -> PlateCurve:
    L, M = fr.layout(p), p.material
    Lleg = L.z_deck_bot
    flex = bend_compliance(p, shape)                            # in-plane bending, real sections (slot, windows)
    J = joint(p, shape)
    x0, _ = solve_joint(J, N, 0.0, Lleg)                        # resting state, wedge tapped in
    if x0 is None:
        raise RuntimeError("joint model has no resting state")

    def foot(x):
        return x[0] + x[2] * Lleg                               # shift + rotation, relative to the deck

    Hs = np.linspace(-Hmax, Hmax, n)
    ds = []
    for side in (1, -1):                                        # walk out from H = 0 for good guesses
        guess, Hprev = x0, 0.0
        for H in (Hs[Hs >= 0] if side > 0 else Hs[Hs < 0][::-1]):
            x = None
            for Hs_ in np.linspace(Hprev, H, 6)[1:]:            # small load steps
                x, c = solve_joint(J, N, Hs_, Lleg, guess)
                if x is None:
                    break
                guess = x
            Hprev = H
            if x is None:
                ds.append((H, np.nan))
                guess = x0 if guess is None else guess
                continue
            ds.append((H, foot(x) - foot(x0) + H * flex))
    ds.sort()
    H_, D_ = np.array([h for h, _ in ds]), np.array([v for _, v in ds])
    ok = np.isfinite(D_)
    soft = [None, None]
    if ok.sum() > 4:
        h, dd = H_[ok], D_[ok]
        comp = np.gradient(dd, h)                                 # mm/N along the curve
        c0 = np.interp(0.0, h, comp)
        for i, sel in enumerate((h < 0, h > 0)):
            idx = np.where(sel & (comp > 2 * c0))[0]
            if len(idx):
                j = idx[np.argmin(abs(h[idx]))]
                soft[i] = float(h[j])
    J0 = joint(p, shape)
    J0.c0[-1] = 0.0
    xz, _ = solve_joint(J0, N, 0.0, Lleg)
    tilt = abs((x0[2] - (xz[2] if xz is not None else 0.0)) * Lleg) if x0 is not None else float("nan")
    return PlateCurve(H_, D_, tuple(soft), tilt)


def frame_sway(p, H_total: float, direction: str = "x") -> dict:
    """Sway of the deck relative to the floor under a sideways push H_total (N) in x or y."""
    parts = {pt.name: pt for pt in fr.parts(p)}
    plate = parts["leg plate A" if direction == "x" else "leg plate B"]
    deck_w = sum(pt.shape.area * pt.qty for pt in parts.values() if pt.kind in ("deck", "cheek", "wedge"))
    deck_n = (deck_w / 1e6 * p.material.t_nominal / 1000 * p.material.density_kg_m3 + p.comfort.heater_kg) * 9.81
    N = deck_n / 8                                              # each plate's share of deck + heater
    cur = plate_curve(p, plate.shape, N)
    ok = np.isfinite(cur.delta)
    if ok.sum() < 3:
        return {"sway_mm": float("inf"), "H": H_total, "gap_H_plate": cur.gap_H, "N_plate": N}
    H, d = cur.H[ok], cur.delta[ok]
    order = np.argsort(d)
    H, d = H[order], d[order]
    signs = [(-1 if pl.mirror_u else 1) for pl in plate.placements]

    def total(D):
        return sum(np.interp(s * D, d, H) * s for s in signs)

    hi = float(d.max()) if H_total > 0 else float(d.min())
    if abs(total(hi)) < abs(H_total):
        return {"sway_mm": float("inf"), "H": H_total}
    a, b = 0.0, hi
    for _ in range(60):
        m = (a + b) / 2
        a, b = (m, b) if abs(total(m)) < abs(H_total) else (a, m)
    D = (a + b) / 2
    return {"sway_mm": D, "H": H_total, "per_plate_N": [float(np.interp(s * D, d, H) * s) for s in signs],
            "gap_H_plate": cur.gap_H, "N_plate": N}


def wobble_onset(p, direction: str = "x") -> float:
    """Total sideways push at which the first leg joint starts to open (N)."""
    parts = {pt.name: pt for pt in fr.parts(p)}
    plate = parts["leg plate A" if direction == "x" else "leg plate B"]
    r = frame_sway(p, 1.0, direction)
    gaps = [g for g in r["gap_H_plate"] if g is not None]
    if not gaps:
        return float("inf")
    g = min(abs(x) for x in gaps)
    return g * len(plate.placements)                            # all plates share while every joint is tight


def wedge_slack_wobble(p, slack: float = 0.1) -> float:
    """Free floor movement (mm) of one leg if its wedge has worked loose by `slack` mm: the plate can
    rock about its shoulder until the tenon jams diagonally in the mortise (or the slack is taken up)."""
    L = fr.layout(p)
    J = joint(p, {pt.name: pt for pt in fr.parts(p)}["leg plate A"].shape)
    lever = J.uw - J.u[~J.is_wedge].min()                       # wedge to the far end of the shoulders
    rock = min(slack / lever, 2 * p.fit.tight / L.t)            # ... or the tenon's diagonal jam
    return rock * L.z_deck_bot


def stresses(p, H_total: float = 200.0, F_edge: float = 1000.0) -> dict:
    """Peak bending stresses (MPa) for a sideways push H_total and a downward push F_edge at mid-side,
    50 mm in from the edge, against the face-grain bending strength f_m (rough)."""
    L, M = fr.layout(p), p.material
    t = M.t_nominal
    r = frame_sway(p, H_total, "x")
    Hmax = max(abs(h) for h in r.get("per_plate_N", [H_total / 4])) if np.isfinite(r["sway_mm"]) else H_total
    leg = 0.0                                                   # moment H z at height z over the real section there
    for name in ("leg plate A", "leg plate B"):
        g = {pt.name: pt for pt in fr.parts(p)}[name].shape
        for z in np.linspace(5.0, L.z_deck_bot - 2.0, 80):
            W = section(g, z, t)[1]
            if W > 0:
                leg = max(leg, Hmax * z / W)
    R = p.top.length / 2
    ta, tb = yagura._tenon_u(p)
    support_y = L.yL[1] - L.cy                                  # the A-plate tenons along this side carry the top
    span = L.Lf - 2 * (ta + tb) / 2                             # between those two tenons
    a = R - p.comfort.tip_inset - support_y
    top = 6 * F_edge * a / (span * t * t)
    z0, z1 = yagura.leg_hole_z(p)
    bridge = L.H - z1
    J = joint(p, {pt.name: pt for pt in fr.parts(p)}["leg plate A"].shape)
    Fw = 0.0
    for h in (0.0, Hmax, -Hmax):                                # wedge pull at rest and under the push
        x, _ = solve_joint(J, r.get("N_plate", 10.0), h, L.z_deck_bot)
        if x is not None:
            Fv, _, _ = _forces(J, x)
            Fw = max(Fw, Fv[-1])
    tau = Fw / (2 * bridge * t)                                 # two shear planes above the wedge hole
    return {"H_N": H_total, "leg_MPa": round(leg, 1), "top_MPa_at_1000N": round(top, 1),
            "wedge_bridge_shear_MPa": round(tau, 1), "f_m": M.f_m}


def summary(p) -> dict:
    S = p.stiffness
    out = {}
    for dirn in ("x", "y"):
        rows = {}
        for H in S.report_loads:
            r = frame_sway(p, H, dirn)
            rows[str(int(H))] = round(r["sway_mm"], 2)
        parts = {pt.name: pt for pt in fr.parts(p)}
        cur = plate_curve(p, parts["leg plate A" if dirn == "x" else "leg plate B"].shape, 10.0)
        on = wobble_onset(p, dirn)
        out[dirn] = {"sway_mm": rows, "onset_N": round(on) if np.isfinite(on) else None,
                     "rest_tilt_mm": round(cur.rest_tilt, 1)}
    L = fr.layout(p)
    out["tenon_play_mm"] = round(2 * p.fit.tight, 2)
    out["loose_wedge_mm_per_0.1"] = round(wedge_slack_wobble(p, 0.1), 2)
    out["stress"] = stresses(p)
    out["assumptions"] = {"E_par": p.material.E_par, "E_perp": S.E_perp, "wedge_preload_N": S.wedge_preload,
                          "leg_L_mm": L.z_deck_bot}
    return out
