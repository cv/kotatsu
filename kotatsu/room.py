"""Room fit: futon + 8 ft round rug around the table (Futon & rug page). Square or round futon/top."""
from __future__ import annotations

import tomllib

from . import comfort
from .params import ROOT

FUTONS = ROOT / "docs" / "futons.toml"


def footprint_d(p, futon_d: float) -> float:
    """Approximate floor footprint size (diameter, or side for a square futon) of a futon draped over the table.

    The futon covers the frame and is clamped by the top; from the top's edge it falls
    (frame height + top thickness) to the floor and the rest lies flat. Real futons are stiff and
    slope outward, so only part of the drop is "used" (drape_k)."""
    h = p.frame.height + p.material.t_nominal
    return max(p.top.length, futon_d - 2 * p.room.drape_k * h)


def futons(p) -> dict:
    d = tomllib.loads(FUTONS.read_text())
    rates = {"JPY": d.get("jpy_cad", 0.0), "USD": d.get("usd_cad", 1.0), "CAD": 1.0}
    out = []
    for f in d["futon"]:
        k = rates[f["currency"]]
        f.setdefault("shape", "round")
        fd = f["size_cm"] * 10.0
        out.append({**f,
                    "price_cad": round(f["price"] * k), "ship_cad": round(f["ship"] * k),
                    "total_cad": round((f["price"] + f["ship"]) * k),
                    "footprint_d": round(footprint_d(p, fd)),
                    "rug_ring": round((p.room.rug_d - footprint_d(p, fd)) / 2)})
    return {"checked": d["checked"], "jpy_cad": rates["JPY"], "usd_cad": rates["USD"], "items": out}


def room_data(p) -> dict:
    return {"rug_d": p.room.rug_d, "futon_d": p.room.futon_d, "top_d": p.top.length,
            "top_shape": getattr(p.top, "shape", "rect"), "corner_r": getattr(p.top, "corner_r", 0.0),
            "futon_shape": getattr(p.room, "futon_shape", "round"),
            "frame": p.top.length - 2 * p.frame.overhang, "ear": p.frame.ear,
            "height": p.frame.height + p.material.t_nominal, "zabuton": list(p.room.zabuton),
            "footprint_d": round(footprint_d(p, p.room.futon_d)), "futons": futons(p),
            "knees": comfort.summary(p)}
