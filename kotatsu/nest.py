"""Sheet nesting: raster first-fit ("bottom-left") on an occupancy grid, verified exactly afterwards.

Each part (and each sheet's used area) is rasterised after growing it by half the part gap plus a
cell, so two parts whose grown masks don't overlap are at least `gap` apart. A 2-D FFT
cross-correlation finds every free position for a part at once; we take the one that keeps the
layout shortest along the sheet (then lowest). Big parts go first; small ones fall into the leg
openings and other gaps. The result is checked with exact shapely distances in tests.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import shapely
from shapely.affinity import rotate, translate
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

from .cutlist import CutPart


@dataclass
class Placed:
    name: str
    copy: int
    angle: int
    shape: Polygon          # in sheet coordinates (mm)


@dataclass
class Sheet:
    w: float                # along x (grain / long side)
    h: float
    placed: list[Placed] = field(default_factory=list)
    occ: np.ndarray | None = field(default=None, repr=False)

    @property
    def area_used(self) -> float:
        return sum(pl.shape.area for pl in self.placed)


@dataclass
class Nest:
    sheet_w: float
    sheet_h: float
    margin: float
    gap: float
    sheets: list[Sheet]
    unplaced: list[str]

    @property
    def utilisation(self) -> float:
        return sum(s.area_used for s in self.sheets) / (sum(s.w * s.h for s in self.sheets) or 1)


def effective_gap(p) -> float:
    """uMake asks for >= part_gap between parts; the bit must also fit between them."""
    return max(p.cnc.part_gap, p.cnc.bit_d + 1.0)


def _mask(g: Polygon, res: float, grow: float) -> np.ndarray:
    gg = g.buffer(grow, quad_segs=8)
    x0, y0, x1, y1 = gg.bounds
    nx, ny = int(math.ceil((x1 - x0) / res)), int(math.ceil((y1 - y0) / res))
    xs = x0 + (np.arange(nx) + 0.5) * res
    ys = y0 + (np.arange(ny) + 0.5) * res
    X, Y = np.meshgrid(xs, ys)
    return shapely.contains_xy(gg, X, Y)


def _fft_free(occ: np.ndarray, m: np.ndarray) -> np.ndarray:
    """free[i, j] == True where mask m placed with its corner at cell (i, j) hits no occupied cell."""
    H, W = occ.shape
    mh, mw = m.shape
    if mh > H or mw > W:
        return np.zeros((0, 0), bool)
    sh = (H + mh, W + mw)
    F = np.fft.rfft2(occ.astype(np.float32), sh)
    M = np.fft.rfft2(m[::-1, ::-1].astype(np.float32), sh)
    corr = np.fft.irfft2(F * M, sh)[mh - 1:H, mw - 1:W]
    return corr < 0.5


STRATEGIES = [("x", "area"), ("y", "area"), ("x", "long"), ("y", "long"), ("xy", "area"), ("xy", "long")]


# ----------------------------------------------------------------------------- interlocked pairs
@dataclass
class _Job:
    """A thing to place: one part, or an interlocked pair of parts placed as one rigid shape."""
    name: str
    shape: object                    # Polygon or MultiPolygon, bounds at (0, 0)
    rotations: tuple[int, ...]
    members: list[tuple[str, Polygon, int]]   # (part name, shape in job coords, extra rotation)


def _interlock(a: Polygon, b: Polygon, gap: float, step: float = 4.0):
    """Turn b upside down (180°) and slide it up into a's leg opening as far as the gap allows.
    Returns (dx, dy, bbox area) for the tightest bounding box, b's corner relative to a's corner."""
    from shapely.prepared import prep  # noqa: F401  (distance needs the real geometry)
    bx0, by0, bx1, by1 = b.bounds
    b180 = rotate(b, 180, origin=((bx0 + bx1) / 2, (by0 + by1) / 2))
    ax1, ay1 = a.bounds[2], a.bounds[3]
    bw, bh = bx1 - bx0, by1 - by0

    def lowest_ok(dx):
        lo, hi = -ay1 - bh, ay1 + 1.0          # dy: b's bottom relative to a's bottom; hi = clear above
        if translate(b180, dx, hi).distance(a) < gap:
            return None
        for _ in range(28):                     # smallest dy (b furthest down... i.e. most overlap from above)
            m = (lo + hi) / 2
            lo, hi = (lo, m) if translate(b180, dx, m).distance(a) >= gap else (m, hi)
        return hi

    def lowest_from_below(dx):                  # b placed under a, pushed up into a's opening
        lo, hi = -bh - 1.0, ay1
        if translate(b180, dx, lo).distance(a) < gap:
            return None
        for _ in range(28):
            m = (lo + hi) / 2
            lo, hi = (m, hi) if translate(b180, dx, m).distance(a) >= gap else (lo, m)
        return lo

    best = None
    for dx in np.arange(-bw, ax1 + step, step):
        for dy in (lowest_ok(dx), lowest_from_below(dx)):
            if dy is None:
                continue
            u = unary_union([a, translate(b180, dx, dy)])
            x0, y0, x1, y1 = u.bounds
            area = (x1 - x0) * (y1 - y0)
            if best is None or area < best[2] - 1e-6:
                best = (float(dx), float(dy), area)
    return best, b180


_PAIR_CACHE: dict = {}


def _pair_job(a: CutPart, b: CutPart, gap: float) -> _Job:
    key = (a.shape.wkb, b.shape.wkb, round(gap, 3))
    if key not in _PAIR_CACHE:
        (dx, dy, _), b180 = _interlock(a.shape, b.shape, gap)
        bm = translate(b180, dx, dy)
        u = unary_union([a.shape, bm])
        x0, y0, _, _ = u.bounds
        am, bm = translate(a.shape, -x0, -y0), translate(bm, -x0, -y0)
        _PAIR_CACHE[key] = (am, bm)
    am, bm = _PAIR_CACHE[key]
    rots = tuple(r for r in a.rotations if r in b.rotations)
    return _Job(f"{a.name} + {b.name}", MultiPolygon([am, bm]), rots, [(a.name, am, 0), (b.name, bm, 180)])


def _jobs(p, parts: list[CutPart], interlock: bool) -> list[tuple[_Job, int]]:
    """Expand quantities into placement jobs. With interlock, each "<x>long side" is paired with a
    "<x>short side" (one flipped, legs in the other's opening) wherever both are available."""
    qty = {c.name: c.qty for c in parts}
    jobs: list[tuple[_Job, int]] = []
    if interlock:
        gap = effective_gap(p) + 0.5
        for a in parts:
            if not a.name.endswith("long side"):
                continue
            b = next((c for c in parts if c.name == a.name[:-len("long side")] + "short side"), None)
            if b is None:
                continue
            n = min(qty[a.name], qty[b.name])
            if n == 0:
                continue
            j = _pair_job(a, b, gap)
            jobs += [(j, k) for k in range(n)]
            qty[a.name] -= n
            qty[b.name] -= n
    for c in parts:
        done = c.qty - qty[c.name]
        jobs += [(_Job(c.name, c.shape, c.rotations, [(c.name, c.shape, 0)]), done + k) for k in range(qty[c.name])]
    return jobs


def _interlock_modes(p) -> tuple[bool, ...]:
    return (False, True) if getattr(getattr(p, "layout", None), "interlock", True) else (False,)


def nest(p, parts: list[CutPart], sheet, res: float = 4.0,
         strategy: tuple[str, str] = ("x", "area"), limit: bool = False, interlock: bool = False) -> Nest:
    """sheet: one (w, h) size (open as many as needed), or a list of sizes opened in that order.
    With limit=True no sheets beyond the list are opened (parts that don't fit are unplaced).
    interlock=True places each long/short side pair as one shape, one panel upside down with its
    leg inside the other's leg opening (much less sheet per pair)."""
    sizes = [sheet] if isinstance(sheet[0], (int, float)) else list(sheet)
    sizes = [(max(a), min(a)) for a in sizes]
    W, H = sizes[0]
    margin, gap = p.cnc.sheet_margin, effective_gap(p)
    grow = gap / 2 + 0.75 * res

    def new_sheet() -> Sheet | None:
        k = len(sheets)
        if k >= len(sizes) and limit:
            return None
        Wk, Hk = sizes[min(k, len(sizes) - 1)]
        nx, ny = int(Wk // res), int(Hk // res)
        s = Sheet(Wk, Hk)
        occ = np.ones((ny, nx), bool)
        # usable cells: the part's grown mask may reach gap/2 beyond the margin line
        lo = int(math.ceil((margin - gap / 2) / res))
        occ[lo:ny - lo, lo:nx - lo] = False
        s.occ = occ
        return s

    jobs = _jobs(p, parts, interlock)
    if strategy[1] == "area":
        jobs.sort(key=lambda j: -(j[0].shape.bounds[2] * j[0].shape.bounds[3]))
    elif strategy[1].startswith("rand"):   # random order of the big parts, small ones last
        import random
        rnd = random.Random(int(strategy[1][4:] or 0))
        big = [j for j in jobs if j[0].shape.area > 0.05e6]
        small = [j for j in jobs if j[0].shape.area <= 0.05e6]
        rnd.shuffle(big)
        small.sort(key=lambda j: -j[0].shape.area)
        jobs = big + small
    else:  # longest side first
        jobs.sort(key=lambda j: (-max(j[0].shape.bounds[2:]), -min(j[0].shape.bounds[2:])))
    sheets: list[Sheet] = []
    unplaced: list[str] = []
    cache: dict[tuple[str, int], tuple[np.ndarray, Polygon, float, float]] = {}

    for cp, k in jobs:
        options = []
        for ang in cp.rotations:
            key = (cp.name, ang)
            if key not in cache:
                g = rotate(cp.shape, ang, origin=(0, 0))
                x0, y0, _, _ = g.bounds
                g = translate(g, -x0, -y0)
                m = _mask(g, res, grow)
                cache[key] = (m, g, -grow, -grow)       # mask cell (0,0) corner sits at (-grow, -grow)
            options.append((ang, *cache[key]))
        rot_off = {}
        for ang in cp.rotations:                            # where the rotated job's corner moved to
            x0, y0, _, _ = rotate(cp.shape, ang, origin=(0, 0)).bounds
            rot_off[ang] = (x0, y0)
        done = False
        for s in [*sheets, None]:
            if s is None:
                s = new_sheet()
                if s is None:
                    break
                fresh = True
            else:
                fresh = False
            best = None
            for ang, m, g, ox, oy in options:
                free = _fft_free(s.occ, m)
                if free.size == 0 or not free.any():
                    continue
                ii, jj = np.nonzero(free)
                if strategy[0] == "x":                         # shortest along x, then lowest
                    score = (jj + m.shape[1]) * 10_000 + ii
                elif strategy[0] == "y":                       # lowest, then leftmost
                    score = (ii + m.shape[0]) * 10_000 + jj
                else:                                          # smallest bounding corner
                    score = np.maximum((jj + m.shape[1]) * (s.h / s.w), ii + m.shape[0]) * 10_000 + jj + ii
                t = int(np.argmin(score))
                cand = (score[t], ang, ii[t], jj[t], m, g, ox, oy)
                if best is None or cand[0] < best[0]:
                    best = cand
            if best is None:
                if fresh:
                    unplaced += [mname for mname, _, _ in cp.members]       # doesn't fit even on an empty sheet
                    done = True
                    break
                continue
            _, ang, i, j, m, g, ox, oy = best
            X, Y = j * res - ox, i * res - oy        # translate so the grown mask corner hits cell (i, j)
            s.occ[i:i + m.shape[0], j:j + m.shape[1]] |= m
            rx, ry = rot_off[ang]
            for mi, (mname, mshape, mrot) in enumerate(cp.members):
                mg = translate(rotate(mshape, ang, origin=(0, 0)), X - rx, Y - ry)
                s.placed.append(Placed(mname, k, (ang + mrot) % 360, mg))
            if fresh:
                sheets.append(s)
            done = True
            break
        if not done:
            unplaced.append(cp.name)
    n = Nest(W, H, margin, gap, sheets, unplaced)
    n.strategy = strategy
    n.interlock = interlock and any(len(j.members) > 1 for j, _ in jobs)
    return n


def material_m2(n: Nest) -> float:
    return sum(s.w * s.h for s in n.sheets) / 1e6


def utilisation(n: Nest) -> float:
    return sum(s.area_used for s in n.sheets) / (material_m2(n) * 1e6 or 1)


def plan(p, parts: list[CutPart], max_sheets: int = 4) -> Nest | None:
    """Least-plywood mix of the available sheet sizes that holds every part.

    Candidate mixes are tried in order of total sheet area (smaller first); a mix is skipped
    without nesting if its usable area can't hold the parts' area. Within a mix, bigger sheets
    are opened first. The first mix any strategy can fill completely wins."""
    from itertools import combinations_with_replacement

    sizes = sorted({(max(s), min(s)) for s in p.cnc.sheets}, key=lambda s: -s[0] * s[1])
    m = p.cnc.sheet_margin
    need = sum(c.shape.area * c.qty for c in parts)
    biggest = max(max(c.shape.bounds[2:]) for c in parts)
    mixes = []
    for k in range(1, max_sheets + 1):
        for mix in combinations_with_replacement(sizes, k):
            usable = sum((w - 2 * m) * (h - 2 * m) for w, h in mix)
            if usable < need * 1.15 or max(w for w, _ in mix) - 2 * m < biggest:
                continue
            mixes.append((sum(w * h for w, h in mix), k, list(mix)))
    for _, _, mix in sorted(mixes):
        tries = [nest(p, parts, mix, strategy=st, limit=True, interlock=il)
                 for il in _interlock_modes(p) for st in STRATEGIES]
        ok = [n for n in tries if not n.unplaced]
        if ok:
            best = max(ok, key=utilisation)
            best.mix = [sheet_name(s) for s in mix]
            return best
    return None


def _last_sheet_fill(n: Nest) -> float:
    if not n.sheets:
        return 0.0
    s = n.sheets[-1]
    return max(pl.shape.bounds[2] for pl in s.placed) if s.placed else 0.0


def best_nest(p, parts: list[CutPart], sheet: tuple[float, float]) -> Nest:
    """Try every strategy; keep the fewest sheets, then the least-used last sheet."""
    results = [nest(p, parts, sheet, strategy=st, interlock=il) for il in _interlock_modes(p) for st in STRATEGIES]
    return min(results, key=lambda n: (len(n.unplaced), len(n.sheets), -n.utilisation, _last_sheet_fill(n)))


def sheet_name(s) -> str:
    w, h = max(s), min(s)
    return f"{round(h / 25.4)}x{round(w / 25.4)}in"


def nest_all(p, parts: list[CutPart]) -> dict[str, Nest]:
    return {sheet_name(s): best_nest(p, parts, (max(s), min(s))) for s in p.cnc.sheets}
