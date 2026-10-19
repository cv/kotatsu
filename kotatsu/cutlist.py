"""Cut list: every flat part to be cut, with quantity and allowed rotations on the sheet."""
from __future__ import annotations

from dataclasses import dataclass

from shapely.affinity import translate
from shapely.geometry import Polygon

from . import frame, top


@dataclass
class CutPart:
    name: str
    shape: Polygon          # normalised: bounds start at (0, 0)
    qty: int
    rotations: tuple[int, ...] = (0, 90, 180, 270)   # degrees allowed on the sheet
    group: str = "frame"    # top | frame | wedge
    note: str = ""


def _norm(g: Polygon) -> Polygon:
    x0, y0, _, _ = g.bounds
    return translate(g, -x0, -y0)


GRAIN_ALONG_U = (0, 180)        # keep the part's u axis along the sheet's long (grain) axis
GRAIN_ALONG_V = (90, 270)


def cut_list(p, seam: str | None = None) -> list[CutPart]:
    tp = top.build(p, seam or p.top.split)
    out: list[CutPart] = []
    for i, b in enumerate(tp.boards):
        # top boards: grain across the table (along the 800 mm board length) on every board
        out.append(CutPart(f"top board {i + 1}", _norm(b), 1, GRAIN_ALONG_V, "top", f"seam {tp.name}"))
    for i, k in enumerate(tp.keys):
        out.append(CutPart(f"top key {i + 1}", _norm(k), 1, (0, 90, 180, 270), "top"))
    for pt in frame.parts(p):
        rot = GRAIN_ALONG_U if pt.kind == "frame" else (0, 90, 180, 270)
        grp = "wedge" if pt.kind == "wedge" else "frame"
        out.append(CutPart(pt.name, _norm(pt.shape), pt.qty, rot, grp,
                           f"{pt.spares} spare" if pt.spares else ""))
    return out
