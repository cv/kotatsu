// Procedural textures for the 3-D view, drawn once on canvases (no image files to download).
// Birch plywood faces (pale, rotary-cut figure, fine fibres), plywood edges (13 plies with glue lines),
// cotton for the futon and pillows, and a braided round rug. All tile seamlessly; seeded, so every
// page load looks the same.
import * as THREE from "three";

function rng(seed) { // mulberry32
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function canvas(w, h) {
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  return [c, c.getContext("2d")];
}

function texture(c, repeat = [1, 1]) {
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.colorSpace = THREE.SRGBColorSpace;
  t.repeat.set(...repeat);
  t.anisotropy = 8;
  return t;
}

// draw fn(dx, dy) at the 9 tile offsets so anything crossing an edge wraps around
function wrapped(W, H, fn) { for (const dx of [-W, 0, W]) for (const dy of [-H, 0, H]) fn(dx, dy); }

/** Birch face veneer, grain along the canvas x axis. One tile = `tileMm` mm. */
export function birchFace(seed = 1, tileMm = 700) {
  const W = 1024, H = 1024, r = rng(seed), [c, g] = canvas(W, H);
  g.fillStyle = "#efe2c9"; g.fillRect(0, 0, W, H);
  for (let i = 0; i < 14; i++) { // broad, soft colour drift (warm, never grey)
    const x = r() * W, y = r() * H, rad = 160 + r() * 300, warm = r() < 0.5;
    wrapped(W, H, (dx, dy) => {
      const gr = g.createRadialGradient(x + dx, y + dy, 0, x + dx, y + dy, rad);
      const rgb = warm ? "232,200,150" : "252,247,236";      // fade to the same colour, not to black
      gr.addColorStop(0, `rgba(${rgb},${warm ? 0.12 : 0.14})`);
      gr.addColorStop(1, `rgba(${rgb},0)`);
      g.fillStyle = gr; g.fillRect(x + dx - rad, y + dy - rad, 2 * rad, 2 * rad);
    });
  }
  // rotary-cut figure: long, gently wandering bands (periodic in x so the tile wraps).
  // Wide soft bands first (blurred), then a few crisper growth lines.
  for (let i = 0; i < 130; i++) {
    const soft = i < 70;
    g.filter = soft ? "blur(4px)" : "none";
    const y0 = r() * H, k1 = 1 + Math.floor(r() * 2), k2 = 3 + Math.floor(r() * 4);
    const a1 = 6 + r() * 22, a2 = 1 + r() * 4, p1 = r() * 6.28, p2 = r() * 6.28;
    const lw = soft ? 8 + r() * 26 : 0.8 + r() * 1.6, al = soft ? 0.04 + r() * 0.06 : 0.04 + r() * 0.07;
    g.strokeStyle = `rgba(${175 + r() * 25 | 0},${130 + r() * 25 | 0},${75 + r() * 20 | 0},${al})`;
    g.lineWidth = lw;
    wrapped(0, H, (_, dy) => {
      g.beginPath();
      for (let x = 0; x <= W; x += 8) {
        const y = y0 + dy + a1 * Math.sin((2 * Math.PI * k1 * x) / W + p1) + a2 * Math.sin((2 * Math.PI * k2 * x) / W + p2);
        x ? g.lineTo(x, y) : g.moveTo(x, y);
      }
      g.stroke();
    });
  }
  g.filter = "none";
  for (let i = 0; i < 5000; i++) { // fine fibres
    const x = r() * W, y = r() * H, L = 8 + r() * 50, dark = r() < 0.5;
    g.strokeStyle = dark ? `rgba(170,125,70,${0.02 + r() * 0.035})` : `rgba(255,250,240,${0.04 + r() * 0.05})`;
    g.lineWidth = r() < 0.8 ? 0.7 : 1.3;
    wrapped(W, H, (dx, dy) => { g.beginPath(); g.moveTo(x + dx, y + dy); g.lineTo(x + dx + L, y + dy + (r() - 0.5) * 1.2); g.stroke(); });
  }
  for (let i = 0; i < 5; i++) { // a few pin knots
    const x = r() * W, y = r() * H, rx = 2 + r() * 4, ry = 1.5 + r() * 2.5;
    g.fillStyle = `rgba(120,80,40,${0.25 + r() * 0.25})`;
    g.beginPath(); g.ellipse(x, y, rx, ry, 0, 0, 6.29); g.fill();
  }
  return texture(c, [1 / tileMm, 1 / tileMm]);
}

/** Plywood edge: `plies` plies across the canvas height (= one sheet thickness), along-edge tile `tileMm`. */
export function plyEdge(t, plies = 13, seed = 7, tileMm = 240) {
  const W = 512, H = 520, r = rng(seed), [c, g] = canvas(W, H), b = H / plies;
  for (let k = 0; k < plies; k++) {
    const y0 = k * b, cross = k % 2 === 1;           // odd plies run across: end grain on this edge
    g.fillStyle = cross ? "#dcc49a" : "#ebd9b6"; g.fillRect(0, y0, W, b);
    if (cross) {
      for (let i = 0; i < 900; i++) {                // end grain: fine pores
        g.fillStyle = `rgba(120,85,45,${0.12 + r() * 0.2})`;
        g.fillRect(r() * W, y0 + 2 + r() * (b - 4), 1 + r() * 1.5, 1 + r() * 1.5);
      }
    } else {
      for (let i = 0; i < 70; i++) {                 // long grain: streaks along the edge
        const y = y0 + 2 + r() * (b - 4), x = r() * W, L = 30 + r() * 160;
        g.strokeStyle = `rgba(150,110,62,${0.06 + r() * 0.1})`; g.lineWidth = 0.8;
        wrapped(W, 0, (dx) => { g.beginPath(); g.moveTo(x + dx, y); g.lineTo(x + dx + L, y); g.stroke(); });
      }
    }
    if (k) { g.fillStyle = "rgba(92,62,32,0.55)"; g.fillRect(0, y0 - 1, W, 2); } // glue line
  }
  const tex = texture(c, [1 / tileMm, 1 / t]);
  tex.offset.y = (t - 1) / t;   // ExtrudeGeometry side walls use v = 1 - z, z in [0, t]: map that onto one tile
  return tex;
}

/** Plain-weave cotton, white (tint it with the material colour). `quilt` adds stitched lines. */
export function cotton(seed = 3, quilt = false) {
  const W = 512, H = 512, r = rng(seed), [c, g] = canvas(W, H);
  g.fillStyle = "#f3f3f3"; g.fillRect(0, 0, W, H);
  for (let y = 0; y < H; y += 3) { g.fillStyle = `rgba(0,0,0,${0.03 + r() * 0.04})`; g.fillRect(0, y, W, 1); }
  for (let x = 0; x < W; x += 3) { g.fillStyle = `rgba(255,255,255,${0.05 + r() * 0.06})`; g.fillRect(x, 0, 1, H); }
  for (let i = 0; i < 6000; i++) { g.fillStyle = `rgba(0,0,0,${r() * 0.05})`; g.fillRect(r() * W, r() * H, 2, 2); }
  if (quilt) {
    for (const [x0, y0, x1, y1] of [[0, H / 2, W, H / 2], [W / 2, 0, W / 2, H]]) {
      const gr = x0 === x1 ? g.createLinearGradient(x0 - 22, 0, x0 + 22, 0) : g.createLinearGradient(0, y0 - 22, 0, y0 + 22);
      gr.addColorStop(0, "rgba(0,0,0,0)"); gr.addColorStop(0.5, "rgba(0,0,0,0.16)"); gr.addColorStop(1, "rgba(0,0,0,0)");
      g.fillStyle = gr;
      x0 === x1 ? g.fillRect(x0 - 22, 0, 44, H) : g.fillRect(0, y0 - 22, W, 44);
      g.strokeStyle = "rgba(255,255,255,0.55)"; g.lineWidth = 2; g.setLineDash([9, 7]);
      g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke(); g.setLineDash([]);
    }
  }
  return texture(c);
}

/** Braided round rug, for a CylinderGeometry cap (circular UVs centred on 0.5, 0.5). */
export function braidedRug(seed = 5, rings = 46) {
  const S = 1024, R = S / 2, r = rng(seed), [c, g] = canvas(S, S);
  const tones = ["#d9ccb4", "#cbbb9f", "#e3d8c4", "#bfae92", "#d3c4aa"];
  const w = R / rings;
  g.fillStyle = tones[0]; g.fillRect(0, 0, S, S);
  for (let k = 0; k < rings; k++) {
    const rad = (k + 0.5) * w;
    g.strokeStyle = tones[Math.floor(r() * tones.length)]; g.lineWidth = w;
    g.beginPath(); g.arc(R, R, rad, 0, 6.2832); g.stroke();
    const n = Math.max(6, Math.floor((2 * Math.PI * rad) / (w * 0.7))), s = k % 2 ? 1 : -1;
    g.strokeStyle = "rgba(70,50,30,0.16)"; g.lineWidth = 1.2;
    for (let i = 0; i < n; i++) {   // braid: short slanted strands
      const a = (2 * Math.PI * i) / n, ca = Math.cos(a), sa = Math.sin(a);
      const r0 = rad - w * 0.42, r1 = rad + w * 0.42, da = (s * w * 0.5) / rad;
      g.beginPath();
      g.moveTo(R + r0 * ca, R + r0 * sa);
      g.lineTo(R + r1 * Math.cos(a + da), R + r1 * Math.sin(a + da));
      g.stroke();
    }
    g.strokeStyle = "rgba(60,40,20,0.25)"; g.lineWidth = 1;
    g.beginPath(); g.arc(R, R, (k + 1) * w, 0, 6.2832); g.stroke();
  }
  for (let i = 0; i < 20000; i++) { g.fillStyle = `rgba(0,0,0,${r() * 0.05})`; g.fillRect(r() * S, r() * S, 1.5, 1.5); }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  return t;
}
