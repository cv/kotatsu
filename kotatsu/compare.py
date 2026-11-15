"""v1 next to v2, for the 3-D view's comparison mode.

v1 is built from its own code at the git tag v1-ordered (extracted to out/v1/src and run there, so its params.toml
and generator are v1's, not today's), and exported in the 3-D view's own schema (site.frame_data, the top's
boards). From both versions' exports this module works out the clear height under the table at every point of a
plan grid (floor to the first thing overhead: a leg, the deck, the heater, the top), and the difference, v2 minus
v1: positive where v2 gives more room, negative where it gives less. The page draws v1 as a ghost and the
difference as a red/green map on the floor; it computes nothing itself.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from shapely import contains_xy
from shapely.affinity import translate
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
TAG = "v1-ordered"
CELL = 20.0        # the map's grid (mm)
CAP = 700.0        # clear heights above this don't matter for knees and legs

_EXPORT = r'''
import json, sys
sys.path.insert(0, ".")
from kotatsu import params, site, top, frame
tp = params.tables(params.load())[0]
fd = site.frame_data(tp)
L = frame.layout(tp)
print(json.dumps({"frame": fd, "top": {"length": tp.top.length, "width": tp.top.width,
                  "boards": [site.rings(b) for b in top.build(tp).boards]}, "cx": L.cx, "cy": L.cy}))
'''


def v1_export() -> dict:
    """v1's 3-D export, built from its own code (cached in out/v1, rebuilt when the tag moves)."""
    out = ROOT / "out" / "v1"
    rev = subprocess.run(["git", "rev-parse", TAG], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    cache = out / f"export-{rev[:12]}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    src = out / "src"
    subprocess.run(["rm", "-rf", str(src)], check=True)
    src.mkdir(parents=True)
    arc = subprocess.run(["git", "archive", TAG], cwd=ROOT, capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(src)], input=arc, check=True)
    r = subprocess.run([sys.executable, "-c", _EXPORT], cwd=src, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("v1 export failed: " + r.stderr[-800:])
    data = json.loads(r.stdout.strip().splitlines()[-1])
    cache.write_text(json.dumps(data))
    return data


def _poly(r) -> Polygon:
    return Polygon(r["ext"], r["holes"])


def clear_height(export: dict, cx: float, cy: float, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    """Clear height (mm, capped at CAP) above the floor at each grid point (centred coordinates, xs by ys)."""
    F, T = export["frame"], export["top"]
    t = F["thickness"]
    X, Y = np.meshgrid(xs + cx, ys + cy)                       # world coordinates
    H = np.full(X.shape, CAP)
    top = unary_union([_poly(b) for b in T["boards"]])
    ztop = F["height"] + F.get("futon_gap", 0.0)
    H = np.where(contains_xy(top, X, Y), np.minimum(H, ztop), H)
    hz = F["heater"]
    (sx, sy, sz), (hx, hy, hzc) = hz["size"], hz["center"]
    inside = (np.abs(X - hx) <= sx / 2) & (np.abs(Y - hy) <= sy / 2)
    H = np.where(inside, np.minimum(H, hzc - sz / 2), H)
    shapes = {pt["name"]: _poly(pt["shape"]) for pt in F["parts"]}
    for pl in F["placed"]:
        if pl["kind"] == "wedge":
            continue
        g = shapes[pl["part"]]
        ox, oy, oz = pl["origin"]
        if pl["axis"] == "z":                                  # a flat part: its underside is overhead
            gw = translate(g, ox, oy)
            H = np.where(contains_xy(gw, X, Y), np.minimum(H, oz), H)
            continue
        sm = -1.0 if pl.get("mirror") else 1.0                 # a standing plate: (u along it, w through it)
        if pl.get("matrix"):
            M = pl["matrix"]
            A = np.array([[M[0], M[2]], [M[4], M[6]]])
            uw = np.linalg.solve(A, np.stack([(X - M[3]).ravel(), (Y - M[7]).ravel()]))
            u, w = uw[0].reshape(X.shape), uw[1].reshape(X.shape)
            zv = lambda v: M[9] * v + M[11]
        elif pl["axis"] == "x":
            u, w = (X - ox) * sm, Y - oy
            zv = lambda v: oz + v
        else:
            u, w = (Y - oy) * sm, X - ox
            zv = lambda v: oz + v
        band = (w >= 0) & (w <= t)
        if not band.any():
            continue
        x0, y0, x1, y1 = g.bounds
        us = np.arange(x0, x1 + 5.0, 5.0)                     # the plate's lowest material at each u
        low = []
        for uu in us:
            cut = g.intersection(LineString([(uu, y0 - 1), (uu, y1 + 1)]))
            low.append(cut.bounds[1] if not cut.is_empty else np.inf)
        low = np.array(low)
        k = np.clip(np.round((u - x0) / 5.0).astype(int), 0, len(us) - 1)
        on = band & (u >= x0) & (u <= x1)
        zlow = np.where(on, zv(low[k]), np.inf)
        H = np.minimum(H, np.where(np.isfinite(zlow), np.maximum(zlow, 0.0), np.inf))
    return H


def data(p) -> dict | None:
    """The comparison for the page: v1's export (moved onto v2's centre) and the clear-height difference map; None
    if the v1 tag isn't in this checkout (a shallow clone)."""
    from . import frame, site, top
    try:
        v1 = v1_export()
    except subprocess.CalledProcessError:
        print(f"[compare] no {TAG} tag here: the 3-D view's v1 comparison is skipped")
        return None
    L = frame.layout(p)
    v2 = {"frame": site.frame_data(p), "top": {"boards": [site.rings(b) for b in top.build(p).boards]}}
    half = max(p.top.length, v1["top"]["length"]) / 2 + 80.0
    xs = np.arange(-half, half + 0.1, CELL)
    ys = xs.copy()
    h2 = clear_height(v2, L.cx, L.cy, xs, ys)
    h1 = clear_height(v1, v1["cx"], v1["cy"], xs, ys)
    diff = np.round(h2 - h1).astype(int)
    dx, dy = L.cx - v1["cx"], L.cy - v1["cy"]
    shift = lambda r: {"ext": [[x + dx, y + dy] for x, y in r["ext"]], "holes": [[[x + dx, y + dy] for x, y in h] for h in r["holes"]]}
    F1 = v1["frame"]
    placed = []
    for pl in F1["placed"]:
        o = pl["origin"]
        placed.append({**pl, "origin": [o[0] + dx, o[1] + dy, o[2]], "moves": []})
    return {"cell": CELL, "x0": float(xs[0]) + L.cx, "y0": float(ys[0]) + L.cy, "n": len(xs), "diff": diff.ravel().tolist(),
            "more": int((diff > 5).sum()), "less": int((diff < -5).sum()),
            "v1": {"frame": {**F1, "placed": placed}, "boards": [shift(b) for b in v1["top"]["boards"]],
                   "heater": {**F1["heater"], "center": [F1["heater"]["center"][0] + dx, F1["heater"]["center"][1] + dy, F1["heater"]["center"][2]]}}}
