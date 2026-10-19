// 2-D drawing helpers + a tiny viewBox pan/zoom (crisp vector at any zoom).
const NS = "http://www.w3.org/2000/svg";

export function el(tag, attrs = {}, parent) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (parent) parent.appendChild(e);
  return e;
}

// data y-up (mm) -> svg y-down
export const ringD = (ring, W) => "M" + ring.map(([x, y]) => `${x},${(W - y).toFixed(2)}`).join("L") + "Z";
export const polyD = (p, W) => [p.ext, ...p.holes].map((r) => ringD(r, W)).join("");

export function drawOption(g, opt, top) {
  const W = top.width;
  opt.halves.forEach((h, i) => el("path", { d: polyD(h, W), class: `part half${i}` }, g));
  opt.keys.forEach((k) => el("path", { d: polyD(k, W), class: "part key" }, g));
  return g;
}

export function drawFootprint(g, top) {
  const o = top.overhang;
  el("rect", { x: o, y: o, width: top.length - 2 * o, height: top.width - 2 * o, class: "footprint" }, g);
}

export function drawGrid(g, top, step = 100) {
  const grid = el("g", { class: "grid" }, g);
  for (let x = 0; x <= top.length; x += step) el("line", { x1: x, y1: -20, x2: x, y2: top.width + 20 }, grid);
  for (let y = 0; y <= top.width; y += step) el("line", { x1: -20, y1: y, x2: top.length + 20, y2: y }, grid);
  return grid;
}

export function staticSvg(opt, top, viewBox) {
  const svg = el("svg", { viewBox: viewBox || `-10 -10 ${top.length + 20} ${top.width + 20}` });
  drawOption(el("g", {}, svg), opt, top);
  return svg;
}

export const jointBox = (top, [x, y], hw = 140, hh = 90) => ({ x: x - hw, y: top.width - y - hh, w: 2 * hw, h: 2 * hh });

export class PanZoom {
  constructor(svg, home, onChange) {
    this.svg = svg; this.home = home; this.onChange = onChange || (() => {});
    this.vb = { ...home };
    this.apply();
    svg.addEventListener("wheel", (e) => {
      e.preventDefault();
      const p = this.toSvg(e.clientX, e.clientY);
      this.zoomAt(Math.exp(e.deltaY * (e.ctrlKey ? 0.01 : 0.0015)), p);
    }, { passive: false });
    let drag = null;
    svg.addEventListener("pointerdown", (e) => {
      drag = { x: e.clientX, y: e.clientY, vb: { ...this.vb }, k: this.vb.w / svg.getBoundingClientRect().width };
      svg.setPointerCapture(e.pointerId); svg.classList.add("dragging");
    });
    svg.addEventListener("pointermove", (e) => {
      if (!drag) return;
      const k = this.scale();
      this.vb.x = drag.vb.x - (e.clientX - drag.x) / k;
      this.vb.y = drag.vb.y - (e.clientY - drag.y) / k;
      this.apply();
    });
    const end = () => { drag = null; svg.classList.remove("dragging"); };
    svg.addEventListener("pointerup", end); svg.addEventListener("pointercancel", end);
    svg.addEventListener("dblclick", () => this.fit(this.home));
    new ResizeObserver(() => this.apply()).observe(svg);
  }
  scale() { // px per mm (preserveAspectRatio = meet)
    const r = this.svg.getBoundingClientRect();
    return Math.min(r.width / this.vb.w, r.height / this.vb.h) || 1;
  }
  toSvg(cx, cy) {
    const pt = this.svg.createSVGPoint(); pt.x = cx; pt.y = cy;
    const m = this.svg.getScreenCTM(); return m ? pt.matrixTransform(m.inverse()) : { x: 0, y: 0 };
  }
  zoomAt(f, p) {
    const vb = this.vb, nw = Math.min(Math.max(vb.w * f, 5), this.home.w * 4);
    const k = nw / vb.w;
    this.vb = { x: p.x - (p.x - vb.x) * k, y: p.y - (p.y - vb.y) * k, w: nw, h: vb.h * k };
    this.apply();
  }
  fit(b) {
    const r = this.svg.getBoundingClientRect(), ar = r.width / r.height || 1.5;
    let w = b.w, h = b.h;
    if (w / h < ar) w = h * ar; else h = w / ar;
    this.vb = { x: b.x + b.w / 2 - w / 2, y: b.y + b.h / 2 - h / 2, w, h };
    this.apply();
  }
  apply() {
    const { x, y, w, h } = this.vb;
    this.svg.setAttribute("viewBox", `${x} ${y} ${w} ${h}`);
    this.onChange(this);
  }
}

export function niceLength(mm) {
  const p = Math.pow(10, Math.floor(Math.log10(mm)));
  for (const m of [5, 2, 1]) if (m * p <= mm) return m * p;
  return p;
}
