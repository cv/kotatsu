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
SRC = ["params.toml", "kotatsu/params.py", "kotatsu/build.py", "kotatsu/cutlist.py", "kotatsu/nest.py",
       "kotatsu/frame.py", "kotatsu/yagura.py", "kotatsu/top.py", "kotatsu/geom.py"]   # anything that can change a layout


def top(p):
    t = p.top
    r = t.corner_r
    return box(r, r, t.length - r, t.width - r).buffer(r, quad_segs=16)


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def layouts(p) -> dict[int, dict[str, nest.Nest]]:
    """{sets: {"best mix" | "<size> only": Nest}} for every count in [layout].sets (copies of all [[tables]])."""
    out = {}
    for k in getattr(p.layout, "sets", [1]):
        parts = cutlist.cut_list_all(p, copies=k)
        opts = {}
        best = nest.plan(p, parts)
        if best is not None:
            opts["best mix"] = best
        for name, n in nest.nest_all(p, parts).items():
            opts[f"{name} only"] = n
        out[k] = opts
    return out


def _src_hash() -> str:
    h = hashlib.sha256()
    for f in SRC:
        h.update((ROOT / f).read_bytes())
    return h.hexdigest()[:16]


_CODE_AT_IMPORT = _src_hash()   # the code this process actually runs


def cached_layouts(p) -> dict:
    """All layouts take ~1-2 min; cache them on the hash of everything that can change the result.
    If the sources changed since this process imported them (an edit during a dev-server rebuild),
    the result is not cached: it was computed by the old code and would be stored under the new hash."""
    key = _src_hash()
    path = CACHE / f"layouts-{key}.pkl"
    if path.exists():
        return pickle.loads(path.read_bytes())
    res = layouts(p)
    if key != _CODE_AT_IMPORT or _src_hash() != key:
        return res
    for opts in res.values():
        for n in opts.values():
            for s in n.sheets:
                s.occ = None                  # don't pickle the raster
    CACHE.mkdir(parents=True, exist_ok=True)
    for old in [*CACHE.glob("nest-*.pkl"), *CACHE.glob("layouts-*.pkl")]:
        old.unlink()
    path.write_bytes(pickle.dumps(res))
    return res


def bom_markdown(p, parts, lays) -> str:
    t, rho = p.material.t_nominal, p.material.density_kg_m3
    kg = lambda a: a / 1e6 * t / 1000 * rho
    rows, tot_q, tot_kg, tot_cut = [], 0, 0.0, 0.0
    for c in parts:
        x1, y1 = c.shape.bounds[2:]
        cut = (c.shape.exterior.length + sum(i.length for i in c.shape.interiors)) / 1000
        rows.append(f"| {c.name} | {c.qty} | {x1:.0f} × {y1:.0f} | {kg(c.shape.area):.2f} | {cut:.2f} | {c.note} |")
        tot_q += c.qty; tot_kg += c.qty * kg(c.shape.area); tot_cut += c.qty * cut
    sheet_rows = []
    for k, opts in lays.items():
        for name, n in sorted(opts.items(), key=lambda kv: nest.material_m2(kv[1])):
            sizes = " + ".join(nest.sheet_name((s.w, s.h)) for s in n.sheets)
            m2 = nest.material_m2(n)
            sheet_rows.append(f"| {k} | {name} | {sizes} | {m2:.2f} | {m2 / k:.2f} | {100 * nest.utilisation(n):.0f}% |")
    return f"""# Bill of materials (generated — do not edit)

Material: {p.material.name}, {t:.0f} mm nominal ({p.material.t_min}–{p.material.t_max} mm accepted by every joint).
Table: {", ".join(t.table_label for t in params.tables(p))}.
Top: one piece ({p.top.shape}, {p.top.length:.0f} mm).

| Part | Qty | Size (mm) | kg each | Cut length each (m) | Note |
|---|---|---|---|---|---|
{chr(10).join(rows)}
| **Total** | **{tot_q}** | | **{tot_kg:.1f} kg** | **{tot_cut:.1f} m** | |

## Sheet layouts

Gap between parts: {nest.effective_gap(p):.2f} mm (uMake asks for >= {p.cnc.part_gap:.0f} mm, and the {p.cnc.bit_d} mm bit
must fit between parts). Sheet margin: {p.cnc.sheet_margin:.0f} mm. Grain runs along each sheet's long side.
Leg plates are laid out with the grain running up the leg.
Frame grain: **{p.layout.frame_grain}**.

| Sets | Layout | Sheets | Plywood (m²) | Per set (m²) | Parts / plywood |
|---|---|---|---|---|---|
{chr(10).join(sheet_rows)}

"Set" = one of each table. The "best mix" row is the least plywood found. TODO-verify how uMake prices
(per sheet, or per part area + cut time) before choosing.

Files: `out/dxf/sheets/<N>-set/<layout>/sheet-K-<size>.dxf` (upload) and `out/dxf/parts/<table>-*.dxf`
(one per part; quantities above are for one set).
"""


def main() -> None:
    p = params.load()
    parts = cutlist.cut_list_all(p)
    import shutil
    shutil.rmtree(OUT / "dxf" / "parts", ignore_errors=True)
    for c in parts:
        export.write_dxf(OUT / "dxf" / "parts" / f"{slug(c.name)}.dxf", [("CUT", c.shape)])
    lays = cached_layouts(p)
    n_files = 0
    shutil.rmtree(OUT / "dxf" / "sheets", ignore_errors=True)
    shutil.rmtree(OUT / "preview" / "sheets", ignore_errors=True)
    for k, opts in lays.items():
        for name, n in opts.items():
            d = OUT / "dxf" / "sheets" / f"{k}-set" / slug(name)
            for i, s in enumerate(n.sheets, 1):
                size = nest.sheet_name((s.w, s.h))
                geo = [("CUT", pl.shape) for pl in s.placed]
                export.write_dxf(d / f"sheet-{i}-{size}.dxf", geo)
                export.write_png(OUT / "preview" / "sheets" / f"{k}-set-{slug(name)}-{i}.png",
                                 [("ENGRAVE", box(0, 0, s.w, s.h))] + geo, title=f"{k} set(s), {name}: sheet {i} ({size})")
                n_files += 1
    (OUT / "BOM.md").write_text(bom_markdown(p, parts, lays))
    print(f"wrote {len(parts)} part DXFs, {n_files} sheet DXFs, BOM.md to {OUT}")


if __name__ == "__main__":
    main()
