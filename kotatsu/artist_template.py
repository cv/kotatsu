"""Printable seam-design template for a commissioned artist (docs/artist/).

Page 1: plan of the top at 1:10 with the two seam bands, plus the cutting rules in plain words.
Page 2: one seam band at 1:4 with a 50 mm grid, to sketch on directly.
Run: uv run python -m kotatsu.artist_template
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle

from . import params, top
from .params import ROOT

OUT = ROOT / "docs" / "artist"
MM = 1 / 25.4
BIRCH, BIRCH2, INK, BAND = "#ecd9b4", "#dcc195", "#2b2118", "#b5523b"


def _ax_mm(fig, x, y, w, h, xlim, ylim):
    """Axes placed in page millimetres with data units = real mm (true scale)."""
    W, H = fig.get_size_inches() / MM
    ax = fig.add_axes([x / W, y / H, w / W, h / H])
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect("equal"); ax.axis("off")
    return ax


def page_plan(p, band: float):
    fig = plt.figure(figsize=(279.4 * MM, 215.9 * MM))  # US letter landscape
    fig.text(0.04, 0.93, "Kotatsu table top: seam design template", fontsize=16, weight="bold", color=INK)
    fig.text(0.04, 0.895, "Top 1200 x 800 mm, birch plywood 18 mm, made of 3 boards. Scale 1:10.", fontsize=9.5, color=INK)
    L, Wd = p.top.length, p.top.width
    ax = _ax_mm(fig, 10, 58, 160, 115, (-100, L + 400), (-150, Wd + 200))  # true 1:10: 1 mm on paper = 10 mm real
    xs = top.seam_xs(p)
    edges = [0, *xs, L]
    for i, (a, b) in enumerate(zip(edges, edges[1:])):
        ax.add_patch(Rectangle((a, 0), b - a, Wd, fc=BIRCH2 if i == 1 else BIRCH, ec="none"))
    ax.add_patch(FancyBboxPatch((0, 0), L, Wd, boxstyle="round,pad=0,rounding_size=20", fc="none", ec=INK, lw=1.2))
    for k, x in enumerate(xs):
        ax.add_patch(Rectangle((x - band, 0), 2 * band, Wd, fc=BAND, alpha=0.18, ec=BAND, lw=0.8, ls="--"))
        ax.plot([x, x], [0, Wd], color=INK, lw=0.8)
        ax.text(x, Wd + 40, f"seam {k + 1}", ha="center", fontsize=8, color=BAND, weight="bold")
    for i, (a, b) in enumerate(zip(edges, edges[1:])):
        ax.text((a + b) / 2, Wd / 2, ["left board", "middle board", "right board"][i] if len(edges) == 4 else f"board {i + 1}",
                ha="center", va="center", fontsize=7.5, color=INK, rotation=90)
    ax.annotate("", (0, -70), (L, -70), arrowprops=dict(arrowstyle="<->", lw=0.7))
    ax.text(L / 2, -120, "1200 mm", ha="center", fontsize=7.5)
    ax.annotate("", (L + 70, 0), (L + 70, Wd), arrowprops=dict(arrowstyle="<->", lw=0.7))
    ax.text(L + 110, Wd / 2, "800 mm", va="center", fontsize=7.5, rotation=90)
    ax.text(0, Wd + 120, f"Shaded = where the seam line may wander: up to {band:.0f} mm either side of the straight line.",
            fontsize=7, color=BAND)

    rules = [
        ("It must lock.", "Picture pulling two boards straight apart. Somewhere the shape\nhas to catch: wider further in than at its opening, like a\ndovetail or a keyhole. A plain wave or zig-zag slides apart."),
        ("No sharp inside corners.", "The cutter is a round bit 6.35 mm (1/4\") wide, so every inside\ncorner comes out rounded at least that much. Outside points\nare fine, but they get softened slightly."),
        ("Nothing thinner than about 25 mm.", "A neck or finger narrower than ~25 mm (1 inch) may crack.\nBig, confident shapes cut best."),
        ("It reads as a line only.", "Both boards are the same pale birch. The design shows as a\nfine dark hairline (a 0.4 mm gap). No colour, no carving\n(unless we agree to add shallow engraving)."),
        ("Two seams, each ~800 mm long.", "They can be one design and its mirror image, two related\ndesigns, or a single design that spans both."),
        ("Any medium is fine.", "A pencil sketch on page 2 photographed straight on works.\nSo does any vector file (SVG, AI, PDF). I convert it and send\nback a proof to approve before anything is cut."),
    ]
    y = 0.84
    for head, body in rules:
        fig.text(0.63, y, head, fontsize=10, weight="bold", color=INK)
        fig.text(0.63, y - 0.022, body, fontsize=7.8, color=INK, va="top", linespacing=1.35)
        y -= 0.125

    # mini examples: locks vs slides apart (real mm, shown at 1:4)
    for j, (title, ok) in enumerate([("locks", True), ("slides apart", False)]):
        a = _ax_mm(fig, 14 + j * 56, 12, 50, 34, (-100, 100), (-60, 75))
        if ok:
            shape = [(-100, -60), (0, -60), (0, -25), (55, -45), (55, 45), (0, 25), (0, 60), (-100, 60)]
        else:
            shape = [(-100, -60), (0, -60), (0, -30), (50, -10), (50, 10), (0, 30), (0, 60), (-100, 60)]
        a.add_patch(Rectangle((-100, -60), 200, 120, fc=BIRCH2, ec="none"))
        a.add_patch(Polygon(shape, fc=BIRCH, ec=INK, lw=0.9))
        a.annotate("", (95, 0), (60, 0), arrowprops=dict(arrowstyle="->", lw=1, color=BAND))
        a.text(0, 66, ("OK: " if ok else "No: ") + title, ha="center", fontsize=7.5, color=INK, weight="bold")
    a = _ax_mm(fig, 130, 10, 40, 42, (-20, 20), (-20, 22))  # actual size
    a.add_patch(Rectangle((-20, -20), 40, 40, fc=BIRCH2, ec="none"))
    a.add_patch(Polygon([(-20, -20), (8, -20), (8, 20), (-20, 20)], fc=BIRCH, ec=INK, lw=0.9))
    a.add_patch(Circle((8 - 3.175, 20 - 3.175), 3.175, fc="none", ec=BAND, lw=1))
    a.text(0, 21, "router bit, 1:1", ha="center", fontsize=7, color=INK, weight="bold")
    fig.text(0.04, 0.02, "Examples at 1:4 except the bit (actual size). Questions welcome; nothing is final until you approve the proof.",
             fontsize=7, color="#6b5b4b")
    return fig


def page_band(p, band: float):
    fig = plt.figure(figsize=(215.9 * MM, 279.4 * MM))  # US letter portrait
    Wd, s = p.top.width, 4.0
    fig.text(0.06, 0.955, "Seam sketch sheet, scale 1:4 (1 grid square = 50 mm real)", fontsize=12, weight="bold", color=INK)
    fig.text(0.06, 0.935, "Draw the line where two boards meet. Stay inside the shaded band. Rules on page 1.",
             fontsize=8.5, color=INK)
    w_page = 2 * band / s + 40
    ax = _ax_mm(fig, (215.9 - w_page) / 2, 30, w_page, Wd / s + 10, (-band - 80, band + 80), (-20, Wd + 20))
    ax.add_patch(Rectangle((-band - 80, 0), band + 80, Wd, fc=BIRCH, ec="none"))
    ax.add_patch(Rectangle((0, 0), band + 80, Wd, fc=BIRCH2, ec="none"))
    ax.add_patch(Rectangle((-band, 0), 2 * band, Wd, fc=BAND, alpha=0.10, ec=BAND, lw=0.8, ls="--"))
    for gx in range(-int(band) - 50, int(band) + 51, 50):
        ax.plot([gx, gx], [0, Wd], color=INK, lw=0.25, alpha=0.35)
    for gy in range(0, int(Wd) + 1, 50):
        ax.plot([-band - 80, band + 80], [gy, gy], color=INK, lw=0.25, alpha=0.35)
    ax.plot([0, 0], [0, Wd], color=INK, lw=0.6, ls=":")
    ax.plot([-band - 80, band + 80], [0, 0], color=INK, lw=1.2)
    ax.plot([-band - 80, band + 80], [Wd, Wd], color=INK, lw=1.2)
    ax.text(-band - 40, Wd / 2, "board A", rotation=90, ha="center", va="center", fontsize=9, color=INK)
    ax.text(band + 40, Wd / 2, "board B", rotation=90, ha="center", va="center", fontsize=9, color=INK)
    ax.text(0, Wd + 8, "table edge", ha="center", fontsize=7, color=INK)
    ax.text(0, -16, "table edge (800 mm from the other edge)", ha="center", fontsize=7, color=INK)
    return fig


def main():
    p = params.load()
    band = 120.0
    OUT.mkdir(parents=True, exist_ok=True)
    f1, f2 = page_plan(p, band), page_band(p, band)
    with PdfPages(OUT / "seam-template.pdf") as pdf:
        pdf.savefig(f1); pdf.savefig(f2)
    f1.savefig(OUT / "seam-template-p1.png", dpi=110)
    f2.savefig(OUT / "seam-template-p2.png", dpi=110)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
