"""Quote pack for a show top (v2, owner 2026-11: the top may be bought by quote, stone or solid wood).

Writes to out/quote/:
  kotatsu-top.dxf          the squircle outline, mm ($INSUNITS = 4), one closed polyline on layer CUT
  kotatsu-top-drawing.pdf  one page: plan with sizes, the corner curve, the edge profile, materials, notes
  request.md               the request text, in English, Chinese and Japanese
Everything comes from params.toml ([top], [top_quote]).
"""
from __future__ import annotations

import math
import textwrap
from pathlib import Path

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

from . import params, top

OUT = Path("out/quote")


def options(p) -> list[dict]:
    out = []
    area = top.build(p).outline.area / 1e6
    for o in p.top_quote.options:
        o = dict(vars(o)) if not isinstance(o, dict) else dict(o)
        o["kg"] = round(area * o["t"] / 1000 * o["density"], 1)
        out.append(o)
    return out


def write_dxf(p, path: Path) -> Path:
    g = top.build(p).outline
    x0, y0, _, _ = g.bounds
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4
    doc.layers.add("CUT", color=7)
    pts = [(x - x0, y - y0) for x, y in list(g.exterior.coords)[:-1]]
    doc.modelspace().add_lwpolyline(pts, close=True, dxfattribs={"layer": "CUT"})
    doc.saveas(path)
    return path


def write_pdf(p, path: Path) -> Path:
    T, Q = p.top, p.top_quote
    g = top.build(p).outline
    x0, y0, x1, y1 = g.bounds
    fig = plt.figure(figsize=(11.69, 8.27))                      # A4 landscape
    fig.suptitle("Kotatsu top: one piece, squircle outline (all sizes in mm)", fontsize=14, x=0.02, ha="left")
    ax = fig.add_axes([0.03, 0.08, 0.5, 0.82])
    ax.add_patch(MplPolygon([(x - x0, y - y0) for x, y in g.exterior.coords], closed=True, fc="#f3ead8", ec="k", lw=1.2))
    L, W = x1 - x0, y1 - y0
    for a, b, lab, off in (((0, -40), (L, -40), f"{L:.0f}", (L / 2, -70)), ((-40, 0), (-40, W), f"{W:.0f}", (-75, W / 2))):
        ax.annotate("", a, b, arrowprops=dict(arrowstyle="<->", lw=0.8))
        ax.text(*off, lab, ha="center", va="center", rotation=0 if a[1] == b[1] else 90, fontsize=11)
    ax.plot([L / 2, L / 2], [-15, W + 15], "k-.", lw=0.5); ax.plot([-15, L + 15], [W / 2, W / 2], "k-.", lw=0.5)
    n, a = T.squircle_n, L / 2
    ax.text(L / 2, W / 2 + 40, f"|x/{a:.0f}|^{n:g} + |y/{W/2:.0f}|^{n:g} = 1\n(origin at the centre)", ha="center", fontsize=10)
    ax.text(L / 2, W / 2 - 60, "The DXF (kotatsu-top.dxf) is the exact outline.\nPlease cut from the DXF.", ha="center", fontsize=9, style="italic")
    ax.set_xlim(-110, L + 30); ax.set_ylim(-110, W + 30); ax.set_aspect("equal"); ax.axis("off")
    # corner points table
    rows = []
    for deg in (0, 15, 30, 45):
        th = math.radians(deg)
        r = (abs(math.cos(th)) ** n / a ** n + abs(math.sin(th)) ** n / (W / 2) ** n) ** (-1 / n)
        rows.append((deg, r * math.cos(th), r * math.sin(th)))
    tx = fig.add_axes([0.56, 0.08, 0.42, 0.82]); tx.axis("off")
    lines = ["Corner check points (from the centre):"] + [f"   {d:>2} deg:  x = {x:6.1f}   y = {y:6.1f}" for d, x, y in rows]
    lines += ["", "Edge profile:",
              f"   eased edges, radius about {Q.edge_r:g} mm on both faces",
              f"   optional (please price both): a bevel under the edge,",
              f"   leaving {Q.undercut:g} mm of visible edge, so it reads thinner",
              "", f"Tolerance: outline +/- {Q.tolerance:g} mm; flat within {Q.flatness:g} mm.",
              "Quantity: 1. No holes, no fixings: it rests loose on a frame.",
              "Both faces finished (it can be seen from below).", "", "Materials (any one; please quote the ones you offer):"]
    for o in options(p):
        lines += textwrap.wrap(f"- {o['name']}", 58, subsequent_indent="  ")
        lines += textwrap.wrap(f"{o['t']:g} mm thick, about {o['kg']} kg; {o['note']}", 58,
                               initial_indent="    ", subsequent_indent="    ")
    lines += ["", "Not suitable: marble, limestone, travertine, 6 mm slabs", "(too weak where it rests on small supports)."]
    tx.text(0, 1, "\n".join(lines), va="top", family="monospace", fontsize=8.6)
    fig.savefig(path)
    plt.close(fig)
    return path


def request_text(p) -> str:
    T = p.top
    L, W = T.length, T.width
    opts = options(p)
    en = "\n".join([
        "Hello,", "",
        f"I'd like a quote for one table top, {L:.0f} x {W:.0f} mm, cut to a squircle outline (a square with very",
        "rounded corners). The DXF and a one-page drawing are attached. Please quote any of these you offer:", ""]
        + [f"- {o['name']}, {o['t']:g} mm ({o['note']})" for o in opts] + ["",
        f"Eased edges (about {p.top_quote.edge_r:g} mm) on both faces; please also price an optional bevel under the edge.",
        "Both faces finished. No holes. Quantity 1.",
        "Please include delivery (or pickup), the lead time, and how it will be packed. Thank you!"])
    zh = "\n".join([
        "您好，", "",
        f"我想询价一块桌面：{L:.0f} x {W:.0f} mm，按附件 DXF 的方圆形（超椭圆）轮廓切割，附一页图纸。",
        "请报价您能提供的材料：实木（胡桃木、白橡木或白蜡木，整根木条拼板，不要指接板），厚 25 mm；",
        "或岩板（烧结石），厚 12 mm。两面都要处理（木材两面上油），边缘倒圆约 2 mm。数量 1 件，无孔。",
        "请包含运到加拿大的运费（DHL/FedEx 等快递）、交期和包装方式。谢谢！"])
    ja = "\n".join([
        "お世話になります。", "",
        f"天板 1 枚の見積もりをお願いします：{L:.0f} x {W:.0f} mm、添付の DXF の形（スーパー楕円、角の大きく丸い正方形）に",
        "切り抜き。材料：ヒノキ無節、または ウォールナット・ホワイトオーク（幅はぎ、フィンガージョイント無し）、厚み 25 mm。",
        "両面 自然塗料クリアー、上下の角は 2R 程度。穴なし、数量 1。送料と納期も教えてください。よろしくお願いします。"])
    return f"# Request for quote: kotatsu top\n\n## English\n\n{en}\n\n## 中文 (Alibaba)\n\n{zh}\n\n## 日本語 (Marutoku)\n\n{ja}\n"


def main() -> None:
    p = params.tables(params.load())[0]
    OUT.mkdir(parents=True, exist_ok=True)
    write_dxf(p, OUT / "kotatsu-top.dxf")
    write_pdf(p, OUT / "kotatsu-top-drawing.pdf")
    (OUT / "request.md").write_text(request_text(p))
    print(f"[quote] wrote {OUT}/kotatsu-top.dxf, kotatsu-top-drawing.pdf, request.md")


if __name__ == "__main__":
    main()
