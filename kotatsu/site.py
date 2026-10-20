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

from shapely.geometry import Polygon

from . import build as cutbuild, comfort, cutlist, frame, nest, params, room, stiffness, top
from .params import ROOT

WEB = ROOT / "web"
OUT = ROOT / "out" / "site"
DOCS = ["PLAN.md", "docs/quote.md", "docs/heater.md", "docs/futon.md", "docs/research.md", "AGENTS.md"]
WATCH = ["params.toml", "kotatsu", "web", "docs", "PLAN.md", "AGENTS.md", "README.md"]


def rings(poly: Polygon, nd: int = 2) -> dict:
    r = lambda cs: [[round(x, nd), round(y, nd)] for x, y in list(cs)[:-1]]
    return {"ext": r(poly.exterior.coords), "holes": [r(h.coords) for h in poly.interiors]}


def _cut_len(polys) -> float:
    return sum(p.exterior.length + sum(h.length for h in p.interiors) for p in polys)


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
            sm = -1 if pl.mirror_u else 1
            if pl.axis == "x":
                c = (ox + sm * (x0 + x1) / 2, oy + t / 2, oz + (y0 + y1) / 2)
            elif pl.axis == "y":
                c = (ox + t / 2, oy + sm * (x0 + x1) / 2, oz + (y0 + y1) / 2)
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


def table_summary(tp, fd: dict, plan) -> dict:
    """Side-by-side numbers for the Overview comparison."""
    t, rho = tp.material.t_nominal, tp.material.density_kg_m3
    tb = top.build(tp)
    top_kg = tb.outline.area / 1e6 * t / 1000 * rho
    parts = frame.parts(tp)
    cut = _cut_len([tb.outline]) + sum(_cut_len([pt.shape]) * pt.qty for pt in parts)
    (sx, sy, sz), (_, _, hz) = frame.heater_box(tp)
    k = comfort.summary(tp)
    return {
        "pieces": 1 + sum(pt.qty for pt in parts),
        "wedges": sum(pt.qty for pt in parts if pt.kind == "wedge"),
        "frame_kg": fd["total_kg"], "total_kg": round(fd["total_kg"] + top_kg, 1),
        "cut_m": round(cut / 1000, 1),
        "side_clear": k["apron_clear"], "knee_reach": k["reach"], "shin_w": k["shin_w"],
        "heater_clear": round(hz - sz / 2), "tip_n": k["tip_n"], "tip_edge_n": k["tip_edge_n"],
        "top_lift_n": k["top_lift_n"], "top_lift_edge_n": k["top_lift_edge_n"],
        "tip_inset": k["tip_inset"],
        "wobble": stiffness.summary(tp),
        "min": {**({"tip_n": k["tip_min_n"]} if k["tip_min_n"] > 0 else {}),
                "knee_reach": k["reach_min"], "side_clear": tp.comfort.knee_h + 5},
        "sheets": [nest.sheet_name((s.w, s.h)) for s in plan.sheets] if plan else [],
        "plywood_m2": round(nest.material_m2(plan), 2) if plan else None,
        "util": round(nest.utilisation(plan), 3) if plan else None,
    }


def tables_data(p) -> list[dict]:
    out = []
    best = cutbuild.cached_layouts(p).get(1, {}).get("best mix")
    for tp in params.tables(p):
        tb = top.build(tp)
        fd = frame_data(tp)
        out.append({"name": tp.table_name, "label": tp.table_label, "shape": getattr(tp.top, "shape", "rect"),
                    "top": {"length": tp.top.length, "width": tp.top.width, "boards": [rings(b) for b in tb.boards]},
                    "frame": fd, "summary": table_summary(tp, fd, best), "room3d": room.room3d(tp)})
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


def story() -> str:
    """The README's story (between the <!-- story --> markers), with image paths for the site."""
    text = (ROOT / "README.md").read_text()
    a, b = text.find("<!-- story -->"), text.find("<!-- /story -->")
    if a < 0 or b < 0:
        return ""
    return text[a + len("<!-- story -->"):b].replace("](docs/img/", "](img/")


def build(with_tests: bool = True) -> None:
    p = params.load()
    with open(ROOT / "params.toml", "rb") as f:
        raw = tomllib.load(f)
    data = {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "git": git_rev(),
        "story": story(),
        "params": raw,
        "thickness": p.material.t_nominal,
        "tables": tables_data(p),
        "room": room.room_data(p),
        "sheets": sheets_data(p),
        "tests": run_tests() if with_tests else None,
        "docs": {d: (ROOT / d).read_text() for d in DOCS if (ROOT / d).exists()},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for f in WEB.iterdir():
        if f.is_file():
            shutil.copy2(f, OUT / f.name)
    (OUT / "img").mkdir(exist_ok=True)
    for f in (ROOT / "docs" / "img").glob("*.png"):
        shutil.copy2(f, OUT / "img" / f.name)
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


def _lan_ip() -> str:
    """This machine's LAN address (for printing a URL a phone can open)."""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as so:
            so.connect(("192.0.2.1", 9))      # TEST-NET address: no packet is sent for UDP connect
            return so.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def dev(port: int, host: str = "0.0.0.0") -> None:
    build()
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):  # no access log spam
            pass

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

    handler = functools.partial(Quiet, directory=str(OUT))
    srv = http.server.ThreadingHTTPServer((host, port), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    shown = _lan_ip() if host in ("0.0.0.0", "") else host
    print(f"[site] http://{shown}:{port}/  (listening on {host}; watching for changes, Ctrl-C to stop)")
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
    ap.add_argument("--host", default="0.0.0.0", help="bind address (0.0.0.0 = reachable from the LAN, e.g. a phone)")
    ap.add_argument("--no-tests", action="store_true")
    a = ap.parse_args()
    dev(a.port, a.host) if a.dev else build(with_tests=not a.no_tests)
