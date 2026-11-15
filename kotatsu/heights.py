"""The table at other heights, for the 3-D view's height slider.

variant(p, dz) is the design with the frame dz mm taller (or shorter): the frame's height and every leg height
that's measured from the floor (the haunch, the taper, the curve) move with it, so the leg keeps its shape above
the floor-level kick. export(p, dz) is what the 3-D view needs to redraw the table at that height: the frame
and top, the room's scenes with everyone re-posed for it (kotatsu/scenes.py), the v1 room map
(kotatsu/compare.py), and the clearances that matter (knees, thighs, feet, elbows). Python computes it all; the
page only draws. Heights the generator can't build come back with the reason.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out" / "heights"

STEP = 25          # the slider's step (mm)
SPAN = 300         # +- this much


def variant(p, dz: float):
    q = NS(**vars(p))
    q.frame = NS(**{**vars(p.frame), "height": p.frame.height + dz})
    Y = vars(p.yagura)
    q.yagura = NS(**{**Y, **{k: Y[k] + dz for k in ("leg_haunch_top", "leg_taper_top", "leg_curve_top") if k in Y}})
    return q


def clearances(q) -> dict:
    """The numbers to read next to the picture (mm): what's overhead, and how the body fits."""
    from . import comfort, frame
    L = frame.layout(q)
    (sx, sy, sz), (_, _, hz) = frame.heater_box(q)
    surf = L.H + q.room.futon_gap + q.material.t_nominal
    C = q.comfort
    H = q.sleeper.height
    squash = getattr(q.room, "seat_squash", 30.0)
    cushion = q.room.cushion_h - squash + q.room.rug_t
    elbow = 0.141 * H                                       # seated elbow height above the seat (Pheasant)
    lf = comfort.legs_forward(q, C.chair_seat_h)
    out = {"table surface": round(surf), "top underside": round(L.H + q.room.futon_gap), "deck underside": round(L.z_deck_bot),
           "heater underside": round(hz - sz / 2), "room between the legs": round(comfort.legroom(q)),
           "cross-legged knees under the deck": round(comfort.side_clear(q) - C.knee_h, 1),
           "legs out on the zaisu, thighs": lf["thigh_room"], "legs out, feet under the heater": lf["feet_room"],
           "elbows to surface, on a cushion": round(surf - (cushion + elbow)),
           "elbows to surface, on the zaisu": round(surf - (C.chair_seat_h + elbow))}
    return out


def clips(q) -> dict:
    """Per scene, where bodies pass into the table or each other at this height (kotatsu/clipping.py), worst first."""
    from . import clipping
    try:
        res = clipping.overlaps(q)
    except Exception as e:                                  # a scene that can't be posed at this height
        return {"*": [[0, f"the scenes can't be posed ({type(e).__name__})", ""]]}
    return {name: [[d, a, b] for d, a, b in v if d > 3.0][:4] for name, v in res.items()}


def export(p, dz: float) -> dict:
    from . import compare, room, site, top
    q = variant(p, dz)
    try:
        fd = site.frame_data(q)
        data = {"dz": dz, "frame": fd, "top": {"length": q.top.length, "width": q.top.width,
                                                "boards": [site.rings(b) for b in top.build(q).boards]},
                "room3d": room.room3d(q, n=41), "clear": clearances(q), "clips": clips(q)}
        cmp = compare.data(q)
        if cmp:
            data["compare"] = {k: v for k, v in cmp.items() if k != "v1"}
        return data
    except Exception as e:                                  # too short (or too tall) for the generator
        why = "too low: the heater, deck and leg joints no longer fit above the floor" if dz < 0 else "too tall for the generator"
        return {"dz": dz, "error": f"{why} ({type(e).__name__}: {e})"[:300]}


def offsets() -> list[int]:
    return list(range(-SPAN, SPAN + 1, STEP))


def key() -> str:
    """Hash of everything the variants depend on: params.toml and the generator's code."""
    h = hashlib.sha1((ROOT / "params.toml").read_bytes())
    for f in sorted((ROOT / "kotatsu").glob("*.py")):
        h.update(f.read_bytes())
    return h.hexdigest()[:12]


def _one(dz):
    from . import params
    P = params.tables(params.load())[0]
    return dz, export(P, dz)


def build_all(if_stale: bool = False) -> dict:
    """Every height (offsets()), computed in parallel, written to out/heights/<dz>.json with an index."""
    import datetime as dt
    from concurrent.futures import ProcessPoolExecutor
    k = key()
    idx = OUT / "index.json"
    if if_stale and idx.exists() and json.loads(idx.read_text()).get("key") == k:
        print("[heights] up to date")
        return json.loads(idx.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    ok, bad = [], {}
    with ProcessPoolExecutor() as ex:
        for dz, d in ex.map(_one, offsets()):
            (OUT / f"{dz}.json").write_text(json.dumps(d, separators=(",", ":")))
            (bad.__setitem__(dz, d["error"]) if "error" in d else ok.append(dz))
    index = {"key": k, "built": dt.datetime.now().isoformat(timespec="seconds"), "step": STEP, "span": SPAN,
             "ok": ok, "errors": {str(k_): v for k_, v in bad.items()}}
    idx.write_text(json.dumps(index))
    print(f"[heights] {len(ok)} heights built, {len(bad)} the generator can't make")
    return index


def load_index() -> dict | None:
    idx = OUT / "index.json"
    if not idx.exists():
        return None
    d = json.loads(idx.read_text())
    d["stale"] = d.get("key") != key()
    return d


if __name__ == "__main__":
    build_all(if_stale="--if-stale" in sys.argv)
