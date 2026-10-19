"""Table top (tenban): 1200 x 800, split into `top.boards` boards across the length.

Splitting keeps every box <= 48" and gives the top a board-and-seam look. Seams sit at equal
spacing; with `top.mirror` each seam's pattern is mirrored, so inner boards are symmetric.
Seam variants live in params.toml [[top.options]]; params.top.split picks one.
kinds:
  ari      dovetail tails (ari-tsugi)            - no loose parts
  kama     gooseneck: neck + flared head          - no loose parts
  hishi    neck + diamond (or kikko hexagon) head  - no loose parts
  bract    Douglas-fir cone bract: forked 3-lobed tip - no loose parts
  yajiri   barbed arrowhead on a stem              - no loose parts
  combo    a different spec per seam (o.seam list)
  puzzle   jigsaw: neck + round head              - no loose parts
  lobes    seigaiha wave of necked round lobes    - no loose parts
  chigiri  straight seam + through bow-tie keys   - loose keys
"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace

from shapely.affinity import rotate
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from .geom import female_cut, largest, male, rounded_rect


@dataclass
class TopParts:
    name: str
    kind: str
    boards: list[Polygon]  # left -> right
    keys: list[Polygon] = field(default_factory=list)
    outline: Polygon | None = None
    joints: list[tuple[float, float]] = field(default_factory=list)  # joint centres (zoom targets)
    seams: list[float] = field(default_factory=list)  # seam x positions


def option(p, name: str | None = None):
    name = name or p.top.split
    for o in p.top.options:
        if o.name == name:
            return o
    raise KeyError(f"no [[top.options]] named {name!r}")


def _ys(width: float, o) -> list[float]:
    tails = getattr(o, "tails", None)
    if tails:  # fully per-tail spec: each entry has y (fraction) + any overrides
        return [width * t.y for t in tails]
    fr = getattr(o, "ys", None)  # optional explicit positions, as fractions of the width
    if fr:
        return [width * f for f in fr]
    return [width * (i + 0.5) / o.count for i in range(o.count)]


def _xbox(x0: float, x1: float, y: float, w: float) -> Polygon:
    a, b = sorted((x0, x1))
    return box(a, y - w / 2, b, y + w / 2)


def _dovetail(x, y, o, s):
    e = 40.0  # long root extension: absorbed by the own side, keeps skewed roots clean
    tail = Polygon([(x - s * e, y - o.root / 2), (x, y - o.root / 2), (x + s * o.depth, y - o.tip / 2),
                    (x + s * o.depth, y + o.tip / 2), (x, y + o.root / 2), (x - s * e, y + o.root / 2)])
    cd = getattr(o, "counter_depth", 0.0)
    if cd:  # nested counter-tail: a small reverse dovetail cut into this tail's tip
        xt, e2 = x + s * o.depth, 2.0
        counter = Polygon([(xt + s * e2, y - o.counter_root / 2), (xt - s * cd, y - o.counter_tip / 2),
                           (xt - s * cd, y + o.counter_tip / 2), (xt + s * e2, y + o.counter_root / 2)])
        tail = tail.difference(counter)
    fd = getattr(o, "fork_depth", 0.0)
    if fd:  # forked tip (salmon tail): a V notch cut back from the tip
        xt, fw = x + s * o.depth, o.fork_width
        tail = tail.difference(Polygon([(xt + s * 2, y - fw / 2), (xt - s * fd, y), (xt + s * 2, y + fw / 2)]))
    return tail


def _kama(x, y, o, s):
    h0 = x + s * o.neck_len
    h1 = h0 + s * o.head_len
    neck = _xbox(x - 2 * s, h0 + s, y, o.neck)
    head = Polygon([(h0, y - o.head_root / 2), (h1, y - o.head_tip / 2),
                    (h1, y + o.head_tip / 2), (h0, y + o.head_root / 2)])
    return unary_union([neck, head])


def _hishi(x, y, o, s):
    """Neck + diamond head (hishi). With flat > 0 the head becomes a long hexagon (kikko)."""
    h0 = x + s * o.neck_len
    hl, hw, f = o.head_len, o.head_w, getattr(o, "flat", 0.0)
    q = (hl - f) / 2  # length of each pointed end
    head = Polygon([(h0, y), (h0 + s * q, y - hw / 2), (h0 + s * (q + f), y - hw / 2),
                    (h0 + s * hl, y), (h0 + s * (q + f), y + hw / 2), (h0 + s * q, y + hw / 2)])
    neck = _xbox(x - 2 * s, h0 + s * q, y, o.neck)
    return unary_union([neck, head])


def _bract(x, y, o, s):
    """Douglas-fir cone bract: a dovetail whose tip splits into two short side lobes and a long,
    narrow middle lobe (the 'mouse tail' poking out between the cone scales)."""
    d, t, r_ = o.depth, o.tip, o.root
    a, b, c, m, L = o.side_len, o.side_inset, o.notch, o.mid_w, o.mid_len
    e = 40.0
    pts = [(-e, -r_ / 2), (0, -r_ / 2), (d, -t / 2), (d + a, -t / 2 + b), (d + c, -m / 2), (d + L, 0),
           (d + c, m / 2), (d + a, t / 2 - b), (d, t / 2), (0, r_ / 2), (-e, r_ / 2)]
    return Polygon([(x + s * u, y + v) for u, v in pts])


def _yajiri(x, y, o, s):
    """Barbed arrowhead (yajiri) on a stem: the swept-back barbs are the lock."""
    n, nl, hl, hw, bb = o.neck, o.neck_len, o.head_len, o.head_w, o.barb
    if nl - bb < 15:  # the mating board must reach in behind the barbs, or the notch is a sealed void
        raise ValueError(f"yajiri: neck_len - barb = {nl - bb:.0f} mm; keep >= 15 (better ~30)")
    e = 40.0
    stem = Polygon([(-e, -n / 2), (nl + 2, -n / 2), (nl + 2, n / 2), (-e, n / 2)])
    head = Polygon([(nl, -n / 2), (nl - bb, -hw / 2), (nl + hl, 0), (nl - bb, hw / 2), (nl, n / 2)])
    g = unary_union([stem, head])
    return Polygon([(x + s * u, y + v) for u, v in g.exterior.coords])


def _puzzle(x, y, o, s):
    cx = x + s * o.head_r * 0.9
    return unary_union([Point(cx, y).buffer(o.head_r, quad_segs=24), _xbox(x - 2 * s, cx, y, o.neck)])


def _lobe(x, y, o, s):
    return Point(x + s * o.offset * o.r, y).buffer(o.r, quad_segs=24)


def _bowtie(x, y, o):
    L, W, w = o.length, o.width, o.waist
    return Polygon([(x - L / 2, y - W / 2), (x, y - w / 2), (x + L / 2, y - W / 2),
                    (x + L / 2, y + W / 2), (x, y + w / 2), (x - L / 2, y + W / 2)])


TAILS = {"ari": _dovetail, "bract": _bract, "yajiri": _yajiri, "kama": _kama, "hishi": _hishi, "puzzle": _puzzle, "lobes": _lobe}
KINDS = (*TAILS, "chigiri", "combo")
_SIZED = ("depth", "root", "tip", "counter_depth", "counter_root", "counter_tip", "fork_depth", "fork_width", "neck", "neck_len",
          "head_len", "head_w", "head_root", "head_tip", "flat", "head_r", "r",
          "side_len", "side_inset", "notch", "mid_w", "mid_len", "barb")


def _per_tail(o, i: int):
    """Option values for tail i: optional per-tail lists scale=[..], skew=[deg..], dirs=[+1/-1..]."""
    sc = getattr(o, "scale", None)
    k = sc[i % len(sc)] if sc else 1.0
    v = SimpleNamespace(**{n: getattr(o, n) * (k if n in _SIZED else 1) for n in vars(o)})
    sk = getattr(o, "skew", None)
    v.skew_deg = sk[i % len(sk)] if sk else 0.0
    tails = getattr(o, "tails", None)
    if tails:  # per-tail overrides (already in mm; 'scale' still applies on top)
        for n, val in vars(tails[i]).items():
            if n == "skew":
                v.skew_deg = val
            elif n not in ("y", "dir"):
                setattr(v, n, val * (k if n in _SIZED else 1))
    return v


def seam_xs(p) -> list[float]:
    n = int(getattr(p.top, "boards", 2))
    return [p.top.length * k / n for k in range(1, n)]


def _left_region(xs: float, ys, o, flip: bool, Wy: float, pad: float = 60.0) -> Polygon:
    """Everything left of seam xs, with tails added (pointing +x) or cut (pointing -x).

    flip mirrors the pattern (used on every other seam), so directions and skews reverse.
    """
    alternate = getattr(o, "alternate", True)
    dirs = getattr(o, "dirs", None)
    reg = box(-pad, -pad, xs, Wy + pad)
    for i, y in enumerate(ys):
        tails = getattr(o, "tails", None)
        if tails and hasattr(tails[i], "dir"):
            s = tails[i].dir
        else:
            s = dirs[i % len(dirs)] if dirs else (-1 if (alternate and i % 2) else 1)
        v = _per_tail(o, i)
        if flip:
            s, v.skew_deg = -s, -v.skew_deg
        tail = TAILS[o.kind](xs, y, v, s)
        if v.skew_deg:
            tail = rotate(tail, v.skew_deg, origin=(xs, y))
        reg = reg.union(tail) if s > 0 else reg.difference(tail)
    return reg


def build(p, name: str | None = None) -> TopParts:
    T, r, c = p.top, p.cnc.bit_d / 2, p.fit.inplane_c
    Lx, Wy = T.length, T.width
    outline = rounded_rect(0, 0, Lx, Wy, T.corner_r)
    name = name or T.split
    if name == "none":
        return TopParts("none", "none", [outline], outline=outline)

    o = option(p, name)
    xs_list = seam_xs(p)
    ys = _ys(Wy, o) if o.kind != "combo" else []
    joints = [(xs, y) for xs in xs_list for y in ys]
    pad = 60.0

    if o.kind == "chigiri":
        keys = [male(_bowtie(xs, y, o), r, c) for xs, y in joints]
        holes = unary_union([female_cut(k, c) for k in keys])
        edges = [-pad, *xs_list, Lx + pad]
        boards = [largest(outline.intersection(box(x0, -pad, x1, Wy + pad)).difference(holes))
                  for x0, x1 in zip(edges, edges[1:])]
        return TopParts(o.name, o.kind, boards, keys=keys, outline=outline, joints=joints, seams=xs_list)

    if o.kind == "combo":  # a different seam spec per seam: o.seam = [{kind=..}, {kind=..}], used as-is
        subs = list(o.seam)
        if len(subs) != len(xs_list):
            raise ValueError(f"{o.name}: {len(subs)} seam specs for {len(xs_list)} seams")
        joints = [(xs, y) for xs, sub in zip(xs_list, subs) for y in _ys(Wy, sub)]
        lefts = [male(_left_region(xs, _ys(Wy, sub), sub, False, Wy, pad), r, c)
                 for xs, sub in zip(xs_list, subs)]
    else:
        if o.kind not in TAILS:
            raise ValueError(f"unknown seam kind {o.kind!r}")
        mirror = getattr(o, "mirror", getattr(T, "mirror", True))  # per-option override
        # male-rounded "left of seam k" regions; board k = left(k) - female(left(k-1))
        lefts = [male(_left_region(xs, ys, o, mirror and k % 2 == 1, Wy, pad), r, c)
                 for k, xs in enumerate(xs_list)]
    boards, prev = [], None
    for reg in [*lefts, None]:
        b = outline if reg is None else outline.intersection(reg)
        if prev is not None:
            b = b.difference(female_cut(prev, c))
        boards.append(largest(b))
        prev = reg
    return TopParts(o.name, o.kind, boards, outline=outline, joints=joints, seams=xs_list)
