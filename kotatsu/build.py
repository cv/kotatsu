"""Entry point: generate all outputs into out/. (Parts are added in phase 2.)"""
from __future__ import annotations

from shapely.geometry import box

from . import export, params
from .params import ROOT

OUT = ROOT / "out"


def top(p):
    t = p.top
    r = t.corner_r
    return box(r, r, t.length - r, t.width - r).buffer(r, quad_segs=16)


def main() -> None:
    p = params.load()
    parts = {"top": [("CUT", top(p))]}
    for name, geo in parts.items():
        export.write_dxf(OUT / "dxf" / f"{name}.dxf", geo)
        export.write_png(OUT / "preview" / f"{name}.png", geo, title=name)
    print(f"wrote {len(parts)} part(s) to {OUT}")


if __name__ == "__main__":
    main()
