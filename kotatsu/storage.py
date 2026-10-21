"""Off-season storage (owner idea 8): everything packs flat inside the top's footprint.

Layer 1: the top. Layer 2: the deck, with whatever fits in its notches. Layer 3: the rest.
Packed greedily on a 3 mm grid (largest part first), then checked exactly.
Stack about 3 x 19 mm thick, 860 x 860. Centred plan coordinates (mm).
Run: uv run python -m kotatsu.storage  (writes out/preview/storage.png)
"""
from __future__ import annotations

from shapely.affinity import rotate, translate
from shapely.geometry import box

from . import frame, top
from .params import ROOT

GAP = 3.0


def _centred(g):
    x0, y0, x1, y1 = g.bounds
    return translate(g, -(x0 + x1) / 2, -(y0 + y1) / 2)


def _pack(items, layers, side, res=3.0):
    """Greedy raster packing (largest first, lowest-then-leftmost spot) into the given layers.
    layers: {name: [obstacle polygons]}; returns {name: [placed polygons]} (obstacles included)."""
    import numpy as np
    from .nest import _fft_free, _mask
    n = int(side * 2 // res)
    grow = GAP / 2 + 0.75 * res
    occ, out = {}, {}
    for name, obs in layers.items():
        o = np.zeros((n, n), bool)
        for g in obs:
            m = _mask(g, res, grow)
            x0, y0 = g.buffer(grow, quad_segs=8).bounds[:2]
            i0, j0 = int(round((y0 + side) / res)), int(round((x0 + side) / res))
            o[max(i0, 0):i0 + m.shape[0], max(j0, 0):j0 + m.shape[1]] |= m[max(-i0, 0):n - i0, max(-j0, 0):n - j0]
        occ[name], out[name] = o, list(obs)
    for label, g in sorted(items, key=lambda it: -it[1].area):
        done = False
        for name in layers:
            best = None
            for ang in (0, 90, 180, 270):
                gr = rotate(g, ang, origin=(0, 0))
                gr = translate(gr, -gr.bounds[0], -gr.bounds[1])
                m = _mask(gr, res, grow)
                free = _fft_free(occ[name], m)
                if free.size == 0 or not free.any():
                    continue
                ii, jj = np.nonzero(free)
                k = np.lexsort((jj, ii))[0]
                cand = (ii[k], jj[k], ang, gr, m)
                if best is None or (cand[0], cand[1]) < (best[0], best[1]):
                    best = cand
            if best is None:
                continue
            i, j, ang, gr, m = best
            gx = gr.buffer(grow, quad_segs=8).bounds
            placed = translate(gr, -side + j * res - gx[0], -side + i * res - gx[1])
            occ[name][i:i + m.shape[0], j:j + m.shape[1]] |= m
            out[name].append(placed)
            done = True
            break
        if not done:
            raise ValueError(f"{label} doesn't fit in storage")
    return out


def layout(p) -> dict[str, list]:
    parts = {pt.name: pt for pt in frame.parts(p)}
    deck = _centred(parts["deck"].shape)
    side = p.top.length / 2
    items = []
    for name, pt in parts.items():
        if name == "deck":
            continue
        g = translate(pt.shape, -pt.shape.bounds[0], -pt.shape.bounds[1])
        items += [(name, g)] * pt.qty
    packed = _pack(items, {"deck layer": [deck], "loose layer": []}, side)
    return {"top": [_centred(top.build(p).outline)], **packed}


def check(p) -> list[str]:
    """Problems with the layout: overlaps, or anything outside the top's footprint."""
    L = layout(p)
    out = []
    lim = box(-p.top.length / 2, -p.top.width / 2, p.top.length / 2, p.top.width / 2)
    for name, gs in L.items():
        for i, a in enumerate(gs):
            if not a.within(lim.buffer(0.5)):
                out.append(f"{name} #{i} outside the footprint")
            for j in range(i + 1, len(gs)):
                if a.distance(gs[j]) < GAP - 0.1:
                    out.append(f"{name} #{i} touches #{j}")
    return out


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from . import params
    p = params.tables(params.load())[0]
    L = layout(p)
    fig, axs = plt.subplots(1, 3, figsize=(15, 5.4))
    for ax, (name, gs) in zip(axs, L.items()):
        s = p.top.length / 2
        ax.add_patch(plt.Rectangle((-s, -s), 2 * s, 2 * s, fill=False, ls="--", ec="#b5793f"))
        for g in gs:
            x, y = g.exterior.xy; ax.fill(x, y, fc="#ecd9b4", ec="#2b2118", lw=0.6)
            for h in g.interiors:
                x, y = h.xy; ax.fill(x, y, fc="white", ec="#2b2118", lw=0.5)
        ax.set_xlim(-s - 10, s + 10); ax.set_ylim(-s - 10, s + 10); ax.set_aspect("equal"); ax.axis("off"); ax.set_title(name)
    fig.suptitle("Off-season storage: three flat layers inside the top's 860 × 860 footprint")
    fig.tight_layout()
    out = ROOT / "out" / "preview" / "storage.png"
    fig.savefig(out, dpi=85)
    print(out, check(p))


if __name__ == "__main__":
    main()
