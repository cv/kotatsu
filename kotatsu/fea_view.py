"""FEA results for the site's 3-D view (docs/fea.md): for each load case, its mesh in the part's own
coordinates, every element's use of strength (Tsai-Hill) and the deflections, so the page can paint the
part where it stands and bend it (exaggerated). Python computes everything; web/viewer3d.js only draws.

It takes a few minutes, so it is cached: `python -m kotatsu.fea_view` (make fea) writes out/fea.json,
stamped with a hash of the sources it came from. kotatsu/site.py copies it into the site and marks it
stale when the design has moved on since.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

from . import fea, params

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out" / "fea.json"
SRC = ["params.toml", "kotatsu/params.py", "kotatsu/fea.py", "kotatsu/fea_view.py", "kotatsu/yagura.py",
       "kotatsu/frame.py", "kotatsu/top.py", "kotatsu/geom.py", "kotatsu/comfort.py", "kotatsu/loads.py",
       "kotatsu/stiffness.py"]
VIEW_H = {"top": 28.0, "deck": 12.0, "leg": 4.0}     # element sizes for the view (coarser than the checks)


def key() -> str:
    h = hashlib.sha1()
    for f in SRC:
        h.update((ROOT / f).read_bytes())
    return h.hexdigest()[:12]


def tsai_hill(p, along, across, shear) -> np.ndarray:
    M, Ld = p.material, p.loads
    th = (along / M.f_m) ** 2 - along * across / M.f_m ** 2 + (across / Ld.f_m_cross) ** 2 + (shear / Ld.f_v_plate) ** 2
    return np.sqrt(np.maximum(th, 0.0))


MESHES: dict[str, dict] = {}


def _pack(m, util, local, disp) -> dict:
    """Flat lists for JSON. The mesh (xy in mm, tri as vertex indices) is stored once in MESHES and named
    by its hash: a part's cases share it. Per case, per vertex: util, local (0/1: only bearing peaks at a
    pad or contact round it), disp (per vertex: [w] for plates, down +; [du, dv] in a plate's own plane)."""
    xy, tri = np.round(m.p.T, 1).ravel(), m.t.T.ravel().astype(int)
    mid = hashlib.sha1(xy.tobytes() + tri.tobytes()).hexdigest()[:10]
    MESHES.setdefault(mid, {"xy": xy.tolist(), "tri": tri.tolist()})
    # smooth for the eye: each vertex takes the area-weighted mean of the elements round it that aren't local
    # peaks; a vertex with only local peaks round it is local. ("worst" stays the element peak.)
    loc = np.asarray(local, bool)
    a = fea._areas(m) * ~loc
    nv = m.p.shape[1]
    wsum = np.bincount(m.t.ravel(), weights=np.tile(a, 3), minlength=nv)
    usum = np.bincount(m.t.ravel(), weights=np.tile(a * util, 3), minlength=nv)
    vutil = np.where(wsum > 0, usum / np.maximum(wsum, 1e-12), 0.0)
    return {"mesh": mid, "util": np.round(vutil, 3).tolist(), "local": (wsum <= 0).astype(int).tolist(),
            "disp": np.round(np.asarray(disp, float).T, 3).ravel().tolist()}


def _rings(polys, dx: float = 0.0, dy: float = 0.0) -> list:
    """Load patches as rings of [x, y] (mm, rounded), for the view's markers."""
    out = []
    for g in polys:
        for q in getattr(g, "geoms", [g]):
            if not q.is_empty and q.area > 1:
                out.append([[round(x + dx, 1), round(y + dy, 1)] for x, y in q.exterior.coords[:-1]])
    return out


def _worst(util, local) -> float:
    keep = ~np.asarray(local, bool)
    return float(util[keep].max()) if keep.any() else 0.0


def top_cases(p) -> list[dict]:
    from . import loads
    out = []
    for name, pats in loads.cases(p).items():
        r = fea.top_case(p, pats, h=VIEW_H["top"])
        res = r["result"]
        m = res.m
        m = type(m)(m.p + np.array([[p.top.length / 2], [p.top.width / 2]]), m.t)   # centred -> the top's own
        util = tsai_hill(p, res.sx, res.sy, res.txy)
        from shapely.geometry import box
        pads = [box(x.x0, x.y0, x.x1, x.y1).intersection(fea.top_model(p)[0]) for x in pats]
        out.append({"part": "top", "label": f"top: {name}", "kind": "plate", "worst": _worst(util, r["local"]),
                    "sag_mm": round(r["sag_mm"], 1), "loads": _rings(pads, p.top.length / 2, p.top.width / 2),
                    **_pack(m, util, r["local"], [res.w])})
    return out


def deck_cases(p) -> list[dict]:
    out = []
    runs = [(n, l, True) for n, l in fea.deck_cases(p).items()]
    corner = next(n for n in fea.deck_cases(p) if "corner" in n)
    runs.append((corner, fea.deck_cases(p)[corner], False))
    for name, loads_, tight in runs:
        r = fea.deck_case(p, loads_, h=VIEW_H["deck"], wedges=tight)
        res = r["result"]
        util = tsai_hill(p, res.sx, res.sy, res.txy)
        label = f"deck: {name}" + ("" if tight else ", wedges slack")
        hand = [g for g, f in loads_ if f > p.comfort.heater_kg * 9.81]          # the hand, not the heater's ears
        out.append({"part": "deck", "label": label, "kind": "plate", "worst": _worst(util, r["local"]),
                    "sag_mm": round(r["sag_mm"], 1), "loads": _rings(hand),
                    **_pack(res.m, util, r["local"], [res.w])})
    return out


def leg_cases(p) -> list[dict]:
    from skfem import Basis, ElementTriP2, ElementVector
    H = p.fea.push_n
    top = fea.top_on_legs(p)
    runs = [(f"leg A: {H:g} N sideways push", "A", H, None), (f"leg A: {H:g} N push + the top's worst corner load", "A", H, top),
            ("leg A: the top's worst corner load only", "A", 0.0, top), (f"leg B: its share of {H:g} N, top clamped", "B", H, top)]
    out = []
    for label, which, hh, tp in runs:
        r = fea.leg_case(p, which, hh, tp, h=VIEW_H["leg"])
        local = r["local"]
        best = None
        for x in r["result"]:                              # the worse of the two senses of push
            util = tsai_hill(p, x.sv, x.su, x.tuv)         # grain runs up the leg (v)
            if best is None or _worst(util, local) > _worst(best[1], local):
                best = (x, util)
        x, util = best
        b = Basis(x.m, ElementVector(ElementTriP2()))
        disp = [x.u[b.nodal_dofs[0]], x.u[b.nodal_dofs[1]]]
        out.append({"part": f"leg plate {which}", "label": label, "kind": "plane", "worst": _worst(util, local),
                    "sway_mm": None if r["sway_mm"] is None else round(r["sway_mm"], 1),
                    **_pack(x.m, util, local, disp)})
    return out


def build(p=None) -> dict:
    p = p or params.tables(params.load())[0]
    t0 = time.time()
    MESHES.clear()
    cases = top_cases(p) + deck_cases(p) + leg_cases(p)
    return {"key": key(), "built": time.strftime("%Y-%m-%dT%H:%M:%S"), "seconds": round(time.time() - t0),
            "thickness": p.material.t_min, "meshes": dict(MESHES), "cases": cases}


def load_cached() -> dict | None:
    """out/fea.json if there is one, with stale = whether the sources changed since."""
    if not OUT.exists():
        return None
    d = json.loads(OUT.read_text())
    d["stale"] = d.get("key") != key()
    return d


def main() -> None:
    if "--if-stale" in sys.argv and (c := load_cached()) and not c["stale"]:
        print("[fea] up to date")
        return
    d = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, separators=(",", ":")))
    tmp.replace(OUT)
    print(f"[fea] {len(d['cases'])} cases in {d['seconds']} s -> {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
