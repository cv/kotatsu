"""One-off: docs/img/v2-parts.png, v1's cut parts (git tag v1-ordered) beside v2's (the working tree), for
the README's v2 chapter. Same scale throughout.
Run from the repo root: uv run python tools/v2_figs.py
"""
import json
import subprocess
import sys
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely import wkt
from shapely.affinity import translate

DUMP = """
import json, sys
sys.path.insert(0, sys.argv[1])
from kotatsu import params, frame, top
P = params.tables(params.load())[0]
parts = {pt.name: (pt.shape.wkt, pt.qty) for pt in frame.parts(P)}
parts["top"] = (top.build(P).outline.wkt, 1)
rho = P.material.density_kg_m3 * P.material.t_nominal / 1e9
kg = (sum(pt.shape.area * pt.qty for pt in frame.parts(P)) + top.build(P).outline.area) * rho
print(json.dumps({"parts": parts, "t": P.material.t_nominal, "kg": round(kg, 1)}))
"""


def dump(ref):
    with tempfile.TemporaryDirectory() as d:
        if ref:
            subprocess.run(f"git archive {ref} | tar -x -C {d}", shell=True, check=True)
            root = d
        else:
            root = "."
        out = subprocess.run([sys.executable, "-c", DUMP, root], capture_output=True, text=True, check=True, cwd=root)
        return json.loads(out.stdout)


def draw(ax, g, x, y, fc="#efe2c8", ec="#7a5a2a"):
    g = translate(g, x - g.bounds[0], y - g.bounds[1])
    for pg in getattr(g, "geoms", [g]):
        ax.fill(*pg.exterior.xy, color=fc, ec=ec, lw=0.8)
        for h in pg.interiors:
            ax.fill(*h.xy, color="white", ec=ec, lw=0.8)
    return g.bounds


def main():
    rows = [("v1, as built", dump("v1-ordered")), ("v2", dump(None))]
    fig, axs = plt.subplots(2, 1, figsize=(14, 7.6))
    for ax, (label, D) in zip(axs, rows):
        P = {k: (wkt.loads(s), q) for k, (s, q) in D["parts"].items()}
        x = 0
        for name in ("top", "deck", "leg plate A", "leg plate B", "heater cheek", "wedge", "cheek wedge", "leg wedge"):
            if name not in P:
                continue
            g, q = P[name]
            b = draw(ax, g, x, 0)
            tag = name.replace("leg plate ", "leg plate\n").replace("heater cheek", "heater\ncheek")
            ax.text((b[0] + b[2]) / 2, -30, tag + (f" ×{q}" if q > 1 else ""), ha="center", va="top", fontsize=9,
                    color="#6e6256", linespacing=1.1)
            x = b[2] + 70
        n = sum(q for _, q in P.values())
        ax.set_title(f"{label}: {D['t']:.0f} mm birch, {n} parts, about {D['kg']} kg", loc="left", fontsize=12, color="#2b2118")
        ax.set_aspect("equal"); ax.axis("off"); ax.set_ylim(-150, 900)
    x1 = max(ax.get_xlim()[1] for ax in axs)
    for ax in axs:
        ax.set_xlim(-20, x1)
    plt.tight_layout()
    plt.savefig("docs/img/v2-parts.png", dpi=110, facecolor="white")


if __name__ == "__main__":
    main()
