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


def spec_lines(p) -> list[str]:
    Q = p.top_quote
    return [Q.grade,
            f"edge-glued from full-length boards {Q.staves[0]:g}-{Q.staves[1]:g} mm wide, no finger joints; colour and grain matched so it reads as one board",
            f"kiln-dried to {Q.moisture[0]:g}-{Q.moisture[1]:g} % moisture",
            f"sanded to {Q.grit} grit, edges routed as drawn",
            Q.finish,
            "packed flat and wrapped in plastic film (it keeps its moisture), with edge and corner protectors, foam, double-wall box"]


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
    lines += ["", "Wood quality and finish:"]
    for item in spec_lines(p):
        lines += textwrap.wrap(f"- {item}", 58, subsequent_indent="  ")
    lines += ["", "Before shipping, please send photos of both faces, the edges", "and a moisture-meter reading."]
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
        f"I'd like a quote for one table top, {L:.0f} x {W:.0f} mm ({L / 25.4:.2f} x {W / 25.4:.2f} in), cut to a squircle outline (a square with very",
        "rounded corners), in solid pale wood. The DXF and a one-page drawing are attached. Please quote any of",
        "these you offer:", ""]
        + [f"- {o['name']}, {o['t']:g} mm ({o['t'] / 25.4:.2f} in) thick, or the nearest you make" for o in opts] + ["", "Quality and finish:"]
        + [f"- {x}" for x in spec_lines(p)] + [
        f"- eased edges (about {p.top_quote.edge_r:g} mm) on both faces; please also price an optional bevel under the edge",
        "", "Before shipping, please send photos of both faces, the edges and a moisture-meter reading.",
        "No holes. Quantity 1. Please include shipping to Canada (courier), the lead time and the packing. Thank you!"])
    zh = "\n".join([
        "您好，", "",
        f"我想询价一块桌面：{L:.0f} x {W:.0f} mm，按附件 DXF 的方圆形（超椭圆）轮廓切割，附一页图纸。",
        "材料（请报价您能提供的）：白橡木实木 20 mm（径切/半径切，美国白橡 Quercus alba 或欧洲橡木，不要柞木），",
        "硬枫木实木 20 mm（Acer saccharum），或日本扁柏（桧木）无节 25 mm。",
        f"要求：FAS/精选级，无节、无边材、无裂、无补腻子；整根长木条直拼（宽 {p.top_quote.staves[0]:g}-{p.top_quote.staves[1]:g} mm），不要指接板，颜色和纹理匹配；",
        f"窑干，含水率 {p.top_quote.moisture[0]:g}-{p.top_quote.moisture[1]:g}%；砂光至 {p.top_quote.grit} 目；边缘倒圆约 {p.top_quote.edge_r:g} mm（另请报价底面斜边）；",
        "不上油、不涂装（我自己上油），砂光后用保鲜膜包好以保持含水率。",
        "发货前请发两面、边缘和含水率读数的照片。包装：护角、泡沫、双层瓦楞纸箱。数量 1 件，无孔。",
        "请包含运到加拿大的快递运费（DHL/FedEx）、交期。谢谢！"])
    ja = "\n".join([
        "お世話になります。", "",
        f"天板 1 枚の見積もりをお願いします：{L:.0f} x {W:.0f} mm、添付の DXF の形（スーパー楕円、角の大きく丸い正方形）に",
        "切り抜き。材料：ヒノキ無節 25 mm、または ホワイトオーク（柾目・追柾）・ハードメープル 20 mm。",
        f"幅はぎ（通し材、幅 {p.top_quote.staves[0]:g}〜{p.top_quote.staves[1]:g} mm、フィンガージョイント無し、色・木目を揃えて）、含水率 {p.top_quote.moisture[0]:g}〜{p.top_quote.moisture[1]:g}%、",
        f"#{p.top_quote.grit} 仕上げ、上下の角は {p.top_quote.edge_r:g}R 程度（裏面の面取りも別途お見積もりください）。",
        "塗装なし（こちらでオイル仕上げします）。ラップで包んで発送してください。穴なし、数量 1。送料と納期も教えてください。よろしくお願いします。"])
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
