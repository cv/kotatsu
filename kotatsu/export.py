"""DXF / SVG / PNG export of shapely polygons (mm)."""
from __future__ import annotations

from pathlib import Path

import ezdxf
from shapely.geometry import Polygon

LAYERS = {"CUT": 7, "ENGRAVE": 1, "POCKET": 5}  # ACI colours: white/black, red, blue


def _rings(poly: Polygon):
    yield poly.exterior.coords
    for r in poly.interiors:
        yield r.coords


def write_dxf(path: Path | str, parts: list[tuple[str, Polygon]]) -> Path:
    """parts: list of (layer, polygon). Every ring becomes one closed LWPOLYLINE."""
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    doc.header["$INSUNITS"] = 4
    for name, color in LAYERS.items():
        doc.layers.add(name, color=color)
    msp = doc.modelspace()
    for layer, poly in parts:
        for ring in _rings(poly):
            pts = list(ring)[:-1]
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(path)
    return path


def write_png(path: Path | str, parts: list[tuple[str, Polygon]], title: str = "") -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"CUT": "k", "ENGRAVE": "r", "POCKET": "b"}
    fig, ax = plt.subplots(figsize=(10, 7))
    for layer, poly in parts:
        for ring in _rings(poly):
            xs, ys = zip(*ring)
            ax.plot(xs, ys, color=colors.get(layer, "g"), lw=0.8)
    ax.set_aspect("equal")
    ax.set_title(title)
    ax.grid(True, lw=0.2)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path
