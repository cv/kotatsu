"""Off-season storage (owner idea 8): everything packs flat inside the top's footprint.

Layer 1: the top. Layer 2: the deck, with two leg plates (head to tail) in each side notch and the
wedges in the end notches. Layer 3: the other four plates and the two heater cheeks.
Stack about 3 x 19 mm thick, 860 x 860. Centred plan coordinates (mm).
Run: uv run python -m kotatsu.storage  (writes out/preview/storage.png)
"""
from __future__ import annotations

from shapely.affinity import rotate, translate
from shapely.geometry import box
from shapely.ops import unary_union

from . import frame, top, yagura
from .params import ROOT

GAP = 3.0


def _centred(g):
    x0, y0, x1, y1 = g.bounds
    return translate(g, -(x0 + x1) / 2, -(y0 + y1) / 2)


def _pair(plate):
    """Two plates head to tail, as tight as GAP allows (the narrow foot beside the wide head)."""
    a = translate(plate, -plate.bounds[0], -plate.bounds[1])
    b0 = rotate(a, 180, origin=(0, 0))
    b0 = translate(b0, -b0.bounds[0], -b0.bounds[1])
    lo, hi = 0.0, a.bounds[2] + GAP + 1
    for _ in range(40):
        m = (lo + hi) / 2
        lo, hi = (lo, m) if translate(b0, m, 0).distance(a) >= GAP else (m, hi)
    return [a, translate(b0, hi, 0)]


def layout(p) -> dict[str, list]:
    parts = {pt.name: pt for pt in frame.parts(p)}
    deck = _centred(parts["deck"].shape)
    side = p.top.length / 2
    pair = _pair(parts["leg plate A"].shape) + _pair(parts["leg plate B"].shape)
    rects = yagura.window_rects(p)
    deck_layer, loose = [deck], []
    # side notches (x > 0 and x < 0): one pair each, plates running along y
    for k, (x0, y0, x1, y1) in enumerate(rects[:2]):
        pr = pair[2 * k: 2 * k + 2]                     # plate length already runs along y
        u = unary_union(pr)
        cx = (max(x0, -side) + min(x1, side)) / 2
        deck_layer += [translate(g, cx - (u.bounds[0] + u.bounds[2]) / 2, -(u.bounds[1] + u.bounds[3]) / 2) for g in pr]
    # wedges in the end notches, in a row of columns
    w = parts["wedge"].shape if "wedge" in parts else parts["leg wedge"].shape
    w = translate(w, -w.bounds[0], -w.bounds[1])
    n = parts["wedge"].qty if "wedge" in parts else parts["leg wedge"].qty
    wl, wh = w.bounds[2], w.bounds[3]
    slots = []
    for x0, y0, x1, y1 in rects[2:]:
        ya, yb = (max(y0, -side) + GAP, min(y1, side) - GAP)
        xa, xb = x0 + GAP, x1 - GAP
        y = ya
        while y + wl <= yb:
            x = xa
            while x + wh <= xb:
                slots.append((x, y)); x += wh + GAP
            y += wl + GAP
    wr = rotate(w, 90, origin=(0, 0))
    placed = 0
    for x, y in slots:
        if placed == n:
            break
        g = translate(wr, x + wh, y)
        if g.distance(deck) >= GAP and all(g.distance(o) >= GAP for o in deck_layer[1:]):
            deck_layer.append(g); placed += 1
    if placed < n:
        raise ValueError(f"only {placed} of {n} wedges fit in the end notches")
    # layer 3: the other plates (as two pairs) + cheeks
    rest = _pair(parts["leg plate A"].shape) + _pair(parts["leg plate B"].shape)
    cheek = translate(parts["heater cheek"].shape, -parts["heater cheek"].shape.bounds[0], -parts["heater cheek"].shape.bounds[1])
    x = -side + 20
    for g in rest[:2]:
        loose.append(translate(g, x, -side + 20))
    x = unary_union(loose).bounds[2] + 20
    for g in rest[2:]:
        loose.append(translate(g, x - rest[2].bounds[0], -side + 20))
    y = unary_union(loose).bounds[3] + 20
    for k in range(parts["heater cheek"].qty):
        loose.append(translate(cheek, -side + 20, y + k * (cheek.bounds[3] + 20)))
    return {"top": [_centred(top.build(p).outline)], "deck layer": deck_layer, "loose layer": loose}


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
