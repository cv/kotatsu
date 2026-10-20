"""Cut list: every flat part to be cut, with quantity and allowed rotations on the sheet."""
from __future__ import annotations

from dataclasses import dataclass

from shapely.affinity import translate
from shapely.geometry import Polygon

from . import frame, params, top


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


def cut_list(p, seam: str | None = None, copies: int = 1,
             top_grain: str | None = None, frame_grain: str | None = None) -> list[CutPart]:
    """All parts for `copies` complete tables (names stay per-part; quantities multiply).

    top_grain:   "across" = grain along each board's 800 mm length (runs across the table)
                 "along"  = grain along the table's 1200 mm length, continuous across the 3 boards
    frame_grain: "horizontal" = side panels' length along the grain; "free" = any rotation
    (defaults from params [layout])."""
    L = getattr(p, "layout", None)
    top_grain = top_grain or getattr(L, "top_grain", "across")
    frame_grain = frame_grain or getattr(L, "frame_grain", "horizontal")
    tp = top.build(p, seam or p.top.split)
    trot = GRAIN_ALONG_V if top_grain == "across" else GRAIN_ALONG_U
    out: list[CutPart] = []
    for i, b in enumerate(tp.boards):
        # top boards: grain across the table (along the 800 mm board length) on every board
        nm = "top" if len(tp.boards) == 1 else f"top board {i + 1}"
        out.append(CutPart(nm, _norm(b), 1, trot, "top", f"seam {tp.name}, grain {top_grain}" if len(tp.boards) > 1 else "one piece"))
    for i, k in enumerate(tp.keys):
        out.append(CutPart(f"top key {i + 1}", _norm(k), 1, (0, 90, 180, 270), "top"))
    for pt in frame.parts(p):
        rot = GRAIN_ALONG_U if (pt.kind == "frame" and frame_grain == "horizontal") else (0, 90, 180, 270)
        grp = "wedge" if pt.kind == "wedge" else "frame"
        out.append(CutPart(pt.name, _norm(pt.shape), pt.qty, rot, grp,
                           f"{pt.spares} spare" if pt.spares else ""))
    for c in out:
        c.qty *= copies
    return out


def cut_list_all(p, copies: int = 1, **kw) -> list[CutPart]:
    """Every part of every [[tables]] entry, names prefixed "<table>: ", for one shared nest."""
    out = []
    for tp in params.tables(p) or [p]:
        prefix = f"{getattr(tp, 'table_name', 'table')}: "
        for c in cut_list(tp, copies=copies, **kw):
            c.name = prefix + c.name
            out.append(c)
    return out
