"""One-off: extract the maple leaf outline from the Flag of Canada SVG (public domain) into
kotatsu/data/maple_leaf.json, normalised so the stem's foot is at (0, 0), the tip at (0, 1), and the
leaf axis is x = 0. The small fillet arcs at the notches are replaced by their chords; the router
rounds those corners anyway.
Run: uv run python -m kotatsu.maple_extract
"""
import json
import re
import urllib.request

from .params import ROOT

URL = "https://upload.wikimedia.org/wikipedia/commons/c/cf/Flag_of_Canada.svg"


def leaf_points(d: str):
    # the leaf is the second subpath of the white path: "...z m2490 4430 ... z"
    sub = d.split("z", 1)[1]
    tokens = re.findall(r"[a-zA-Z]|-?\d*\.?\d+(?:e-?\d+)?", sub)
    i, cmd = 0, None
    x = y = 0.0
    start = (2400.0, 0.0)          # current point after the first subpath's z
    x, y = start
    pts = []
    while i < len(tokens):
        t = tokens[i]
        if t.isalpha():
            cmd = t
            i += 1
            if cmd in "zZ":
                break
            continue
        if cmd == "m":
            x += float(tokens[i]); y += float(tokens[i + 1]); i += 2; pts.append((x, y)); cmd = "l"
        elif cmd == "l":
            x += float(tokens[i]); y += float(tokens[i + 1]); i += 2; pts.append((x, y))
        elif cmd == "a":
            # rx ry rot large sweep dx dy -> chord to the end point
            x += float(tokens[i + 5]); y += float(tokens[i + 6]); i += 7; pts.append((x, y))
        else:
            raise ValueError(f"unhandled path command {cmd!r}")
    return pts


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "kotatsu-project/0.1"})
    svg = urllib.request.urlopen(req, timeout=30).read().decode()
    d = re.findall(r'd="([^"]+)"', svg)[1]
    pts = leaf_points(d)
    xs = [p[0] for p in pts]
    cx = (min(xs) + max(xs)) / 2
    ybot, ytop = max(p[1] for p in pts), min(p[1] for p in pts)
    h = ybot - ytop
    norm = [((px - cx) / h, (ybot - py) / h) for px, py in pts]
    out = {"source": URL, "license": "public domain (Flag of Canada)", "note": __doc__.strip().splitlines()[0],
           "aspect_w_over_h": (max(xs) - min(xs)) / h, "points": [[round(a, 5), round(b, 5)] for a, b in norm]}
    path = ROOT / "kotatsu" / "data" / "maple_leaf.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(out, indent=1))
    print(f"{len(norm)} points -> {path}")


if __name__ == "__main__":
    main()
