"""Room fit: round futon + round rug around the round table (Futon & rug page)."""
from __future__ import annotations

import tomllib

from .params import ROOT

FUTONS = ROOT / "docs" / "futons.toml"


def footprint_d(p, futon_d: float) -> float:
    """Approximate floor footprint diameter of a round futon draped over the table.

    The futon covers the frame and is clamped by the top; from the top's edge it falls
    (frame height + top thickness) to the floor and the rest lies flat. Real futons are stiff and
    slope outward, so only part of the drop is "used" (drape_k)."""
    h = p.frame.height + p.material.t_nominal
    return max(p.top.length, futon_d - 2 * p.room.drape_k * h)


def futons(p) -> dict:
    d = tomllib.loads(FUTONS.read_text())
    rate = d["jpy_cad"]
    out = []
    for f in d["futon"]:
        k = rate if f["currency"] == "JPY" else 1.0
        fd = f["size_cm"] * 10.0
        out.append({**f,
                    "price_cad": round(f["price"] * k), "ship_cad": round(f["ship"] * k),
                    "total_cad": round((f["price"] + f["ship"]) * k),
                    "footprint_d": round(footprint_d(p, fd)),
                    "rug_ring": round((p.room.rug_d - footprint_d(p, fd)) / 2)})
    return {"checked": d["checked"], "jpy_cad": rate, "items": out}


def room_data(p) -> dict:
    return {"rug_d": p.room.rug_d, "futon_d": p.room.futon_d, "top_d": p.top.length,
            "frame": p.top.length - 2 * p.frame.overhang, "ear": p.frame.ear,
            "height": p.frame.height + p.material.t_nominal, "zabuton": list(p.room.zabuton),
            "footprint_d": round(footprint_d(p, p.room.futon_d)), "futons": futons(p)}
