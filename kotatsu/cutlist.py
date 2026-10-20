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
ANY = (0, 90, 180, 270)


def cut_list(p, copies: int = 1, frame_grain: str | None = None) -> list[CutPart]:
    """All parts for `copies` complete tables (names stay per-part; quantities multiply).

    frame_grain: "horizontal" = side panels' length along the grain; "free" = any rotation
    (default from params [layout])."""
    frame_grain = frame_grain or getattr(getattr(p, "layout", None), "frame_grain", "horizontal")
    tp = top.build(p)
    out: list[CutPart] = [CutPart("top", _norm(tp.outline), 1, ANY if tp.name == "round" else GRAIN_ALONG_U,
                                  "top", "one piece")]
    for pt in frame.parts(p):
        rot = GRAIN_ALONG_U if (pt.kind == "frame" and frame_grain == "horizontal") else ANY
        grp = "wedge" if pt.kind == "wedge" else "frame"
        out.append(CutPart(pt.name, _norm(pt.shape), pt.qty, rot, grp,
                           f"{pt.spares} spare" if pt.spares else ""))
    for c in out:
        c.qty *= copies
    return out


def cut_list_all(p, copies: int = 1, **kw) -> list[CutPart]:
    """Every part of every [[tables]] entry, names prefixed "<table>: ", for one shared nest."""
    out = []
    tabs = params.tables(p) or [p]
    for tp in tabs:
        prefix = f"{getattr(tp, 'table_name', 'table')}: " if len(tabs) > 1 else ""
        for c in cut_list(tp, copies=copies, **kw):
            c.name = prefix + c.name
            out.append(c)
    return out
