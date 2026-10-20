"""Build the static project site into out/site/.

    uv run python -m kotatsu.site            # build once
    uv run python -m kotatsu.site --dev      # build, serve on :8765, rebuild on change

The page (web/) is hand-written HTML/JS; this module only exports data.json.
"""
from __future__ import annotations

import argparse
import sys
import datetime as dt
import functools
import http.server
import json
import shutil
import subprocess
import threading
import time
import tomllib

from shapely.geometry import Polygon, box

from . import build as cutbuild, cutlist, frame, geom, nest, params, top
from .params import ROOT

WEB = ROOT / "web"
OUT = ROOT / "out" / "site"
DOCS = ["PLAN.md", "AGENTS.md", "docs/research.md", "docs/heater.md", "docs/motifs.md", "docs/artist/request.md"]
WATCH = ["params.toml", "kotatsu", "web", "docs", "PLAN.md", "AGENTS.md"]


def rings(poly: Polygon, nd: int = 2) -> dict:
    r = lambda cs: [[round(x, nd), round(y, nd)] for x, y in list(cs)[:-1]]
    return {"ext": r(poly.exterior.coords), "holes": [r(h.coords) for h in poly.interiors]}


def _cut_len(polys) -> float:
    return sum(p.exterior.length + sum(h.length for h in p.interiors) for p in polys)


def top_data(p) -> dict:
    t_m = p.material.t_nominal / 1000
    kg_m2 = p.material.density_kg_m3 * t_m
    straight = top.build(p, "none")
    base_cut = _cut_len(straight.boards) + p.top.width * len(top.seam_xs(p))  # straight seam cuts
    out = []
    for o in p.top.options:
        tp = top.build(p, o.name)
        parts = tp.boards + tp.keys
        cut = _cut_len(parts)
        dims = [[round(h.bounds[2] - h.bounds[0]), round(h.bounds[3] - h.bounds[1])] for h in tp.boards]
        out.append({
            "name": o.name, "kind": o.kind, "label": getattr(o, "label", o.name),
            "selected": o.name == p.top.split,
            "boards": [rings(h) for h in tp.boards],
            "keys": [rings(k) for k in tp.keys],
            "joints": [[x, y] for x, y in tp.joints],
            "seams": tp.seams,
            "stats": {
                "pieces": len(parts), "loose": len(tp.keys),
                "board_dims": dims,
                "cut_m": round(cut / 1000, 2),
                "extra_cut_m": round((cut - base_cut) / 1000, 2),
                "weight_kg": round(sum(x.area for x in parts) / 1e6 * kg_m2, 1),
                "cuttable": all(geom.router_cuttable(x, p.cnc.bit_d / 2) for x in parts),
            },
        })
    return {"length": p.top.length, "width": p.top.width, "thickness": p.material.t_nominal,
            "overhang": p.frame.overhang, "selected": p.top.split, "boards": p.top.boards, "options": out}


def frame_data(p) -> dict:
    """Frame parts (flat shapes) + their 3-D placements, for the Frame and 3-D tabs."""
    L = frame.layout(p)
    t, kg_m3 = p.material.t_nominal, p.material.density_kg_m3
    plist, placed = [], []
    for pt in frame.parts(p):
        g = pt.shape
        x0, y0, x1, y1 = g.bounds
        plist.append({"name": pt.name, "kind": pt.kind, "qty": pt.qty, "spares": pt.spares,
                      "shape": rings(g), "bounds": [x0, y0, x1, y1],
                      "size": [round(x1 - x0, 1), round(y1 - y0, 1)],
                      "kg": round(g.area / 1e6 * t / 1000 * kg_m3, 2),
                      "cut_m": round((g.exterior.length + sum(h.length for h in g.interiors)) / 1000, 2)})
        for pl in pt.placements:
            ox, oy, oz = pl.origin
            if pl.axis == "x":
                c = (ox + (x0 + x1) / 2, oy + t / 2, oz + (y0 + y1) / 2)
            elif pl.axis == "y":
                c = (ox + t / 2, oy + (x0 + x1) / 2 * (-1 if pl.mirror_u else 1), oz + (y0 + y1) / 2)
            else:
                c = ((x0 + x1) / 2, (y0 + y1) / 2, oz)
            dx, dy = c[0] - L.cx, c[1] - L.cy
            ex = {"frame": [0.5 * (dx > 0) - 0.5 * (dx < 0) if pl.axis == "y" else 0,
                            0.5 * (dy > 0) - 0.5 * (dy < 0) if pl.axis == "x" else 0, 0],
                  "deck": [0, 0, 0.15], "cheek": [0, 0, -0.35],
                  "wedge": [0, 0, 0.9]}[pt.kind]
            placed.append({"part": pt.name, "kind": pt.kind, "axis": pl.axis, "origin": [ox, oy, oz],
                           "mirror": pl.mirror_u, "explode": ex})
    size, centre = frame.heater_box(p)
    total_kg = sum(x["kg"] * x["qty"] for x in plist)
    return {"thickness": t, "height": L.H, "futon_gap": 12.0, "parts": plist, "placed": placed,
            "heater": {"size": list(size), "center": list(centre)}, "total_kg": round(total_kg, 1),
            "draft": False}


def tables_data(p) -> list[dict]:
    out = []
    for tp in params.tables(p):
        tb = top.build(tp)
        out.append({"name": tp.table_name, "label": tp.table_label, "shape": getattr(tp.top, "shape", "rect"),
                    "top": {"length": tp.top.length, "width": tp.top.width, "boards": [rings(b) for b in tb.boards]},
                    "frame": frame_data(tp)})
    return out


def sheets_data(p) -> dict:
    group = {c.name: c.group for c in cutlist.cut_list_all(p)}
    out = {}
    for k, opts in cutbuild.cached_layouts(p).items():
        out[str(k)] = {}
        for name, n in sorted(opts.items(), key=lambda kv: nest.material_m2(kv[1])):
            out[str(k)][name] = {
                "margin": n.margin, "gap": round(n.gap, 2), "count": len(n.sheets),
                "util": round(nest.utilisation(n), 3), "material_m2": round(nest.material_m2(n), 2),
                "sizes": [nest.sheet_name((s.w, s.h)) for s in n.sheets],
                "sheets": [{"w": sh.w, "h": sh.h, "parts": [
                    {"name": pl.name, "group": group[pl.name], "angle": pl.angle, "shape": rings(pl.shape)}
                    for pl in sh.placed]} for sh in n.sheets],
            }
    return out


def git_rev() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True)
        d = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
        return r.stdout.strip() + ("+dirty" if d.stdout.strip() else "")
    except OSError:
        return "?"


def run_tests() -> dict:
    r = subprocess.run(["uv", "run", "pytest", "-q", "--tb=line", "-p", "no:cacheprovider"],
                       cwd=ROOT, capture_output=True, text=True)
    lines = [l for l in r.stdout.strip().splitlines() if l.strip()]
    return {"ok": r.returncode == 0, "summary": lines[-1] if lines else "", "failures":
            [l for l in lines if "Error" in l or "FAILED" in l][:20]}


def build(with_tests: bool = True) -> None:
    p = params.load()
    with open(ROOT / "params.toml", "rb") as f:
        raw = tomllib.load(f)
    data = {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "git": git_rev(),
        "project": {
            "title": "Kotatsu — glue-free CNC birch",
            "facts": [
                *[["Table", t.table_label] for t in params.tables(p)],
                ["Height", f"{p.frame.height + p.material.t_nominal:.0f} mm + futon ≈ 40–41 cm (both)"],
                ["Material", p.material.name],
                ["Heater", f"{p.heater.model} ({p.heater.mount} mount)"],
                ["Vendor", "uMake.ca (online instant quote)"],
                ["Ship to", "rural BC — standard parcels ≤ 48\""],
                ["Budget", "< $1200 CAD"],
            ],
        },
        "params": raw,
        "top": top_data(p),
        "tables": tables_data(p),
        "sheets": sheets_data(p),
        "tests": run_tests() if with_tests else None,
        "docs": {d: (ROOT / d).read_text() for d in DOCS if (ROOT / d).exists()},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for f in WEB.iterdir():
        if f.is_file():
            shutil.copy2(f, OUT / f.name)
    tmp = OUT / "data.json.tmp"
    tmp.write_text(json.dumps(data, separators=(",", ":")))
    tmp.replace(OUT / "data.json")
    print(f"[site] built {data['generated']} ({data['git']}) tests: "
          f"{(data['tests'] or {}).get('summary', 'skipped')}")


def _mtime() -> float:
    m = 0.0
    for w in WATCH:
        path = ROOT / w
        files = [path] if path.is_file() else [f for f in path.rglob("*") if f.is_file()]
        for f in files:
            if "__pycache__" not in f.parts:
                m = max(m, f.stat().st_mtime)
    return m


def dev(port: int) -> None:
    build()
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):  # no access log spam
            pass

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

    handler = functools.partial(Quiet, directory=str(OUT))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f"[site] http://127.0.0.1:{port}/  (watching for changes, Ctrl-C to stop)")
    last = _mtime()
    while True:
        time.sleep(1.0)
        m = _mtime()
        if m != last:
            last = m
            # fresh interpreter per build, so edits to any module (incl. this one) take effect
            res = subprocess.run([sys.executable, "-m", "kotatsu.site"], cwd=ROOT)
            if res.returncode:
                print(f"[site] build failed (exit {res.returncode}); still serving the last good build")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", action="store_true")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-tests", action="store_true")
    a = ap.parse_args()
    dev(a.port) if a.dev else build(with_tests=not a.no_tests)
