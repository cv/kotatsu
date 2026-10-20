"""One-off: the before/after strips in docs/img/evolution-*.png, for the README story.

They're made from preview images saved along the way in out/preview (not in git: the earlier designs
live in the seams-archive and frame-variants-archive tags), plus the current deck and the top drawn to
scale. Kept to show how the pictures were made; rerunning it needs those previews.
Run from the repo root: uv run python tools/story_figs.py
"""
import textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
from PIL import Image, ImageDraw, ImageFont

FONT = matplotlib.get_data_path() + "/fonts/ttf/DejaVuSans.ttf"
BOLD = matplotlib.get_data_path() + "/fonts/ttf/DejaVuSans-Bold.ttf"
INK, MUTED, ACC = (43, 33, 24), (110, 98, 86), (176, 112, 58)
P = "out/preview/"


def load(path, box=None):
    im = Image.open(path).convert("RGB")
    if box:
        im = im.crop(box)
    bg = Image.new("RGB", im.size, (255, 255, 255))
    diff = Image.eval(Image.composite(im, bg, Image.new("L", im.size, 255)), lambda v: v)
    bbox = Image.eval(im.convert("L"), lambda v: 255 if v < 245 else 0).getbbox()
    return im.crop(bbox) if bbox else im


def strip(panels, title, out, H=300, W=360):
    f, fb, ft = ImageFont.truetype(FONT, 17), ImageFont.truetype(BOLD, 17), ImageFont.truetype(BOLD, 22)
    gap, arrow, pad = 26, 50, 24
    n = len(panels)
    width = pad * 2 + n * W + (n - 1) * arrow
    cap_lines = [textwrap.wrap(c, 34) for _, _, c in panels]
    cap_h = 24 * max(len(c) for c in cap_lines) + 30
    height = pad + 40 + H + gap + cap_h + pad
    can = Image.new("RGB", (width, height), (250, 248, 244))
    d = ImageDraw.Draw(can)
    d.text((pad, pad), title, font=ft, fill=INK)
    y0 = pad + 44
    for i, (im, label, cap) in enumerate(panels):
        x0 = pad + i * (W + arrow)
        d.rounded_rectangle((x0, y0, x0 + W, y0 + H), 10, fill=(255, 255, 255), outline=(225, 218, 206))
        s = min((W - 24) / im.width, (H - 24) / im.height)
        im2 = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
        can.paste(im2, (x0 + (W - im2.width) // 2, y0 + (H - im2.height) // 2))
        d.text((x0 + 4, y0 + H + 12), label, font=fb, fill=ACC if i == n - 1 else INK)
        for k, line in enumerate(cap_lines[i]):
            d.text((x0 + 4, y0 + H + 38 + 24 * k), line, font=f, fill=MUTED)
        if i < n - 1:
            ax, ay = x0 + W + 10, y0 + H // 2
            d.line((ax, ay, ax + arrow - 20, ay), fill=ACC, width=4)
            d.polygon([(ax + arrow - 20, ay - 9), (ax + arrow - 8, ay), (ax + arrow - 20, ay + 9)], fill=ACC)
    can.save(out, optimize=True)
    print(out, can.size)


def top_shapes():
    """The top at true scale: 120 x 80 in 3 boards, Ø90 round, 86 square in the 91 cm free box."""
    outs = []
    for k in range(3):
        fig, ax = plt.subplots(figsize=(4, 3.2), dpi=110)
        ax.set_xlim(-660, 660); ax.set_ylim(-540, 500); ax.set_aspect("equal"); ax.axis("off")
        birch = dict(fc="#ecd9b4", ec="#2b2118", lw=1.0)
        ax.add_patch(Rectangle((-455, -455), 910, 910, fc="none", ec="#b0703a", lw=1.2, ls="--"))
        if k == 0:
            ax.add_patch(FancyBboxPatch((-600, -400), 1200, 800, boxstyle="round,pad=0,rounding_size=15", **birch))
            for x in (-200, 200):
                ax.plot([x, x], [-400, 400], color="#2b2118", lw=0.9)
                for y in (-250, 0, 250):
                    ax.add_patch(Rectangle((x - 25, y - 35), 50, 70, fc="#dcc195", ec="#2b2118", lw=0.6))
        elif k == 1:
            ax.add_patch(Circle((0, 0), 450, **birch))
        else:
            ax.add_patch(FancyBboxPatch((-430, -430), 860, 860, boxstyle="round,pad=0,rounding_size=20", **birch))
        ax.text(0, -520, "dashed: the 91 cm box that ships free", ha="center", fontsize=8, color="#b0703a")
        fig.savefig(f"/tmp/top-{k}.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
        outs.append(load(f"/tmp/top-{k}.png"))
    return outs


def deck_now():
    import sys; sys.path.insert(0, ".")
    from kotatsu import params, frame
    p = params.tables(params.load())[0]
    d = [pt for pt in frame.parts(p) if pt.name == "deck"][0].shape
    L = frame.layout(p)
    fig, ax = plt.subplots(figsize=(5, 5), dpi=110)
    x, y = d.exterior.xy; ax.fill(x, y, fc="#ecd9b4", ec="#2b2118", lw=0.8)
    for ring in d.interiors:
        x, y = ring.xy; ax.fill(x, y, fc="white", ec="#2b2118", lw=0.8)
    c, h = L.cx, p.top.length / 2
    ax.add_patch(FancyBboxPatch((c - h, c - h), 2 * h, 2 * h, boxstyle="round,pad=0,rounding_size=20", fc="none", ec="#b0703a", lw=0.8, ls="--"))
    ax.set_aspect("equal"); ax.axis("off")
    fig.savefig("/tmp/deck-now.png", bbox_inches="tight", facecolor="white"); plt.close(fig)


deck_now()
t = top_shapes()
strip([(t[0], "120 × 80, three boards", "Too big for a parcel, so I split it and joined the boards with decorative seams."),
       (t[1], "Ø 90 round, one piece", "After re-measuring the room. But round futons were hard to find at a fair price, and the box cost $200 to ship."),
       (t[2], "86 × 86, one piece", "Square futons are easy to get, and the box fits the free shipping tier.")],
      "The top: from big and fancy to small enough to ship free", "docs/img/evolution-top.png")

strip([(load(P + "leg-taper-1.png", (30, 75, 385, 280)), "Solid side panels", "Strong and simple, but the aprons along each side ate the room my knees need."),
       (load(P + "foot-flare-1.png", (500, 55, 1010, 300)), "Tapered, flared legs", "More room at the floor and steadier feet. Still an apron in the way."),
       (load(P + "yagura-splay-1.png", (10, 70, 745, 390)), "Yagura: legs + a deck", "No aprons at all. Four corner legs hold a deck, and the heater hangs under it.")],
      "The frame: getting the side panels out of the way of my knees", "docs/img/evolution-frame.png")

strip([(load(P + "frame780-1.png", (60, 40, 460, 504)), "Plates with windows", "Windows cut the weight under the 20 kg free-shipping limit, but every window is more cutting."),
       (load(P + "haunch-legs-1.png", (0, 45, 600, 600)), "My first sketch", "A wide shoulder up top and a narrow leg below. Lighter without any windows."),
       (load(P + "slim-legs-1.png", (50, 40, 380, 504)), "My second sketch", "Slimmer still, with equal fingers on both sides of each slot.")],
      "The legs: two of my sketches made them lighter", "docs/img/evolution-legs.png")

strip([(load(P + "deck-windows-1.png", (0, 38, 540, 540)), "Windows", "Holes to save weight. Then I found that cutting is about 3/4 of the price."),
       (load(P + "deck-notch-1.png", (495, 25, 935, 467)), "Notches", "Open the holes to the edge: the same wood out, a metre less cutting, about $20 cheaper."),
       (load("/tmp/deck-now.png"), "Rounded notches", "I asked for round corners away from the legs. The corners at the legs stay square.")],
      "The deck: how a price experiment changed its shape", "docs/img/evolution-deck.png")
