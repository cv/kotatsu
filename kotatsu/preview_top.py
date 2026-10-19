"""Render the top-split options side by side: out/preview/top_options.png"""
from __future__ import annotations

import copy

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly

from . import params, top
from .params import ROOT

COLORS = ["#e9cfa3", "#d9b47c", "#b5793f"]


def _draw(ax, poly, color, lw=0.6):
    ax.add_patch(MplPoly(list(poly.exterior.coords), closed=True, fc=color, ec="k", lw=lw))
    for hole in poly.interiors:
        ax.add_patch(MplPoly(list(hole.coords), closed=True, fc="white", ec="k", lw=lw))


def main(styles=("ari", "puzzle", "chigiri")) -> None:
    base = params.load()
    fig, axes = plt.subplots(2, len(styles), figsize=(6 * len(styles), 8.5),
                             gridspec_kw={"height_ratios": [2.2, 1]})
    for col, style in enumerate(styles):
        p = copy.deepcopy(base)
        p.top.split = style
        tp = top.build(p)
        for row, ax in enumerate(axes[:, col]):
            for i, h in enumerate(tp.halves):
                _draw(ax, h, COLORS[i])
            for k in tp.keys:
                _draw(ax, k, COLORS[2])
            ax.set_aspect("equal")
            ax.axis("off")
            if row == 0:
                f = p.frame.overhang
                ax.plot([f, p.top.length - f, p.top.length - f, f, f],
                        [f, f, p.top.width - f, p.top.width - f, f], "k--", lw=0.5)
                ax.set_xlim(-20, p.top.length + 20)
                ax.set_ylim(-20, p.top.width + 20)
                ax.set_title(f"{style}  ({len(tp.halves)} halves + {len(tp.keys)} keys)")
            else:
                y = p.top.width / (2 * p.top.seam_count)
                ax.set_xlim(p.top.length / 2 - 130, p.top.length / 2 + 130)
                ax.set_ylim(y - 75, y + 75)
                ax.set_title("joint detail (router-rounded corners)", fontsize=9)
    out = ROOT / "out" / "preview" / "top_options.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=110, bbox_inches="tight")
    print(out)


if __name__ == "__main__":
    main()
