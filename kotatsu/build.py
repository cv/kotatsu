"""Entry point: generate all cut files into out/.

out/dxf/parts/<part>.dxf             one file per distinct part (qty in BOM.md)
out/dxf/sheets/<size>/sheet-N.dxf    nested sheet layouts, ready to upload
out/preview/sheets/<size>-N.png      quick look at each layout
out/BOM.md                           parts list, weights, sheet comparison
"""
from __future__ import annotations

import hashlib
import pickle
import re

from shapely.geometry import box

from . import cutlist, export, nest, params
from .params import ROOT

OUT = ROOT / "out"
CACHE = OUT / ".cache"
SRC = ["params.toml", "kotatsu/cutlist.py", "kotatsu/nest.py", "kotatsu/frame.py", "kotatsu/top.py", "kotatsu/geom.py"]


def top(p):
    t = p.top
    r = t.corner_r
    return box(r, r, t.length - r, t.width - r).buffer(r, quad_segs=16)


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def cached_nests(p, parts) -> dict:
    """nest_all is ~10 s; cache it on the hash of everything that can change the result."""
    h = hashlib.sha256()
    for f in SRC:
        h.update((ROOT / f).read_bytes())
    path = CACHE / f"nest-{h.hexdigest()[:16]}.pkl"
    if path.exists():
        return pickle.loads(path.read_bytes())
    res = nest.nest_all(p, parts)
    for n in res.values():
        for s in n.sheets:
            s.occ = None                      # don't pickle the raster
    CACHE.mkdir(parents=True, exist_ok=True)
    for old in CACHE.glob("nest-*.pkl"):
        old.unlink()
    path.write_bytes(pickle.dumps(res))
    return res


def bom_markdown(p, parts, nests) -> str:
    t, rho = p.material.t_nominal, p.material.density_kg_m3
    kg = lambda a: a / 1e6 * t / 1000 * rho
    rows, tot_q, tot_kg, tot_cut = [], 0, 0.0, 0.0
    for c in parts:
        x1, y1 = c.shape.bounds[2:]
        cut = (c.shape.exterior.length + sum(i.length for i in c.shape.interiors)) / 1000
        rows.append(f"| {c.name} | {c.qty} | {x1:.0f} × {y1:.0f} | {kg(c.shape.area):.2f} | {cut:.2f} | {c.note} |")
        tot_q += c.qty; tot_kg += c.qty * kg(c.shape.area); tot_cut += c.qty * cut
    sheet_rows = []
    for name, n in nests.items():
        area = len(n.sheets) * n.sheet_w * n.sheet_h / 1e6
        sheet_rows.append(f"| {name} | {len(n.sheets)} | {area:.2f} | {100 * n.utilisation:.0f}% | {'/'.join(n.strategy)} |")
    best = min(nests.items(), key=lambda kv: (len(kv[1].sheets) * kv[1].sheet_w * kv[1].sheet_h, len(kv[1].sheets)))
    return f"""# Bill of materials (generated — do not edit)

Material: {p.material.name}, {t:.0f} mm nominal ({p.material.t_min}–{p.material.t_max} mm accepted by every joint).
Seam: `{p.top.split}`, {p.top.boards} top boards.

| Part | Qty | Size (mm) | kg each | Cut length each (m) | Note |
|---|---|---|---|---|---|
{chr(10).join(rows)}
| **Total** | **{tot_q}** | | **{tot_kg:.1f} kg** | **{tot_cut:.1f} m** | |

## Sheet layouts

Gap between parts: {nest.effective_gap(p):.2f} mm (uMake asks for >= {p.cnc.part_gap:.0f} mm, and the {p.cnc.bit_d} mm bit
must fit between parts). Sheet margin: {p.cnc.sheet_margin:.0f} mm. Grain runs along each sheet's long side:
the side panels keep their length along the grain, and the top boards keep their 800 mm length along it.

| Sheet | Sheets needed | Material (m²) | Parts / material | Packing |
|---|---|---|---|---|
{chr(10).join(sheet_rows)}

Least material: **{best[0]}**. TODO-verify how uMake prices, per sheet or per part area + cut time, before choosing.

Files: `out/dxf/sheets/<size>/sheet-N.dxf` (upload) and `out/dxf/parts/*.dxf` (one per part).
"""


def main() -> None:
    p = params.load()
    parts = cutlist.cut_list(p)
    for c in parts:
        export.write_dxf(OUT / "dxf" / "parts" / f"{slug(c.name)}.dxf", [("CUT", c.shape)])
    nests = cached_nests(p, parts)
    n_files = 0
    for name, n in nests.items():
        d = OUT / "dxf" / "sheets" / name
        if d.exists():
            for f in d.glob("*.dxf"):
                f.unlink()
        for i, s in enumerate(n.sheets, 1):
            geo = [("CUT", pl.shape) for pl in s.placed]
            export.write_dxf(d / f"sheet-{i}.dxf", geo)
            export.write_png(OUT / "preview" / "sheets" / f"{name}-{i}.png",
                             [("ENGRAVE", box(0, 0, s.w, s.h))] + geo, title=f"{name} sheet {i}")
            n_files += 1
    (OUT / "BOM.md").write_text(bom_markdown(p, parts, nests))
    print(f"wrote {len(parts)} part DXFs, {n_files} sheet DXFs, BOM.md to {OUT}")


if __name__ == "__main__":
    main()
