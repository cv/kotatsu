"""Build the static project site into out/site/.

    uv run python -m kotatsu.site            # build once
    uv run python -m kotatsu.site --dev      # build, serve on :8765, rebuild on change

The page (web/) is hand-written HTML/JS; this module only exports data.json.
"""
from __future__ import annotations

import argparse
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

from . import geom, params, top
from .params import ROOT

WEB = ROOT / "web"
OUT = ROOT / "out" / "site"
DOCS = ["PLAN.md", "AGENTS.md", "docs/research.md", "docs/heater.md"]
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


def draft_frame(p) -> dict:
    """Rough frame for 3-D context only (no joinery yet - phase 2)."""
    F, t = p.frame, p.material.t_nominal
    L = p.top.length - 2 * F.overhang
    W = p.top.width - 2 * F.overhang
    H = F.height

    def side(length):
        outer = box(0, 0, length, H)
        hole = geom.rounded_rect(F.leg_width, -50, length - F.leg_width, H - F.apron_depth, F.opening_r)
        return rings(outer.difference(hole).buffer(0))

    x0, y0 = F.overhang, F.overhang
    panels = []
    for y in (y0 + F.ear, y0 + W - F.ear):
        panels.append({"name": "long side", "axis": "x", "shape": side(L), "origin": [x0, y - t / 2, 0]})
    for x in (x0 + F.ear, x0 + L - F.ear):
        panels.append({"name": "short side", "axis": "y", "shape": side(W), "origin": [x - t / 2, y0, 0]})
    D = p.deck
    dz = H - D.drop - t
    deck = {"name": "deck", "shape": rings(box(0, 0, D.length_x, W - 2 * F.ear)),
            "origin": [p.top.length / 2 - D.length_x / 2, y0 + F.ear, dz]}
    hz = p.heater
    heater = {"size": [hz.body_x, hz.body_y, hz.body_h],
              "center": [p.top.length / 2, p.top.width / 2, H - D.drop - hz.body_h / 2]}
    return {"thickness": t, "height": H, "futon_gap": 12.0, "panels": panels, "deck": deck,
            "heater": heater, "draft": True}


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
                ["Top", f"{p.top.length:.0f} × {p.top.width:.0f} × {p.material.t_nominal:.0f} mm, split in 2"],
                ["Height", f"{p.frame.height + p.material.t_nominal:.0f} mm + futon ≈ 40–41 cm"],
                ["Material", p.material.name],
                ["Heater", f"{p.heater.model} ({p.heater.mount} mount)"],
                ["Vendor", "uMake.ca (online instant quote)"],
                ["Ship to", "rural BC — standard parcels ≤ 48\""],
                ["Budget", "< $1200 CAD"],
            ],
        },
        "params": raw,
        "top": top_data(p),
        "frame": draft_frame(p),
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
            try:
                import importlib
                for mod in (geom, top, params):
                    importlib.reload(mod)
                build()
            except Exception as e:  # keep serving on errors
                print(f"[site] build failed: {e}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", action="store_true")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-tests", action="store_true")
    a = ap.parse_args()
    dev(a.port) if a.dev else build(with_tests=not a.no_tests)
