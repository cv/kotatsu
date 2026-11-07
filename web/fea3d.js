// FEA heat maps for the 3-D view. kotatsu/fea_view.py computes everything (meshes in each part's own
// coordinates, every element's use of strength, the deflections); this only turns them into geometry:
// a slab with the part's two faces and its cut edges, coloured, bent by the deflections times k.
import * as THREE from "three";

// share of strength (Tsai-Hill) -> colour: blue (idle) .. yellow (half) .. red (all of it) .. purple (past it)
const STOPS = [[0, [44, 123, 182]], [0.25, [120, 190, 220]], [0.5, [250, 240, 160]], [0.75, [253, 160, 80]],
  [1.0, [215, 25, 28]], [1.5, [110, 10, 120]]];
const LOCAL = [150, 150, 150]; // right at a pad or contact: bearing peaks, not bending (see the legend)

export function heat(u) {
  if (!(u > 0)) u = 0;
  for (let i = 1; i < STOPS.length; i++) {
    const [b, cb] = STOPS[i], [a, ca] = STOPS[i - 1];
    if (u <= b) { const f = (u - a) / (b - a); return ca.map((c, j) => (c + (cb[j] - c) * f) / 255); }
  }
  return STOPS[STOPS.length - 1][1].map((c) => c / 255);
}

export const GRADIENT = `linear-gradient(to right, ${STOPS.map(([u, c]) => `rgb(${c}) ${(u / 1.5) * 100}%`).join(", ")})`;

// The largest deflection in a case (mm): plates [w], plane plates [du, dv] per vertex.
export function maxDisp(c) {
  let m = 0;
  if (c.kind === "plate") for (const w of c.disp) m = Math.max(m, Math.abs(w));
  else for (let i = 0; i < c.disp.length; i += 2) m = Math.max(m, Math.hypot(c.disp[i], c.disp[i + 1]));
  return m;
}

// A coloured slab for case c on mesh me, t thick, in the part's own (u, v, w) frame (as web/viewer3d.js's
// slab()); mirror flips u like a mirrored placement. bend(m, k) then draws it with the deflections × k.
export function heatSlab(me, c, t, mirror) {
  const m0 = slabAt(me, c, t, 0, mirror), p1 = slabAt(me, c, t, 1, mirror).geometry.attributes.position.array;
  const base = m0.geometry.attributes.position.array.slice();
  m0.userData.base = base;
  m0.userData.dir = p1.map((x, i) => x - base[i]);
  return m0;
}

export function bend(m, k) {
  const { base, dir } = m.userData, pos = m.geometry.attributes.position;
  for (let i = 0; i < base.length; i++) pos.array[i] = base[i] + dir[i] * k;
  pos.needsUpdate = true;
  m.geometry.computeBoundingSphere();
}

function slabAt(me, c, t, k, mirror) {
  const xy = me.xy, tri = me.tri, nv = xy.length / 2, s = mirror ? -1 : 1;
  const P = new Float32Array(nv * 3), lift = 0.4;
  for (let i = 0; i < nv; i++) {
    let u = xy[2 * i], v = xy[2 * i + 1], w = 0;
    if (c.kind === "plate") w = -c.disp[i] * k;                      // plates deflect down (+)
    else { u += c.disp[2 * i] * k; v += c.disp[2 * i + 1] * k; }     // in their own plane
    P[3 * i] = s * u; P[3 * i + 1] = v; P[3 * i + 2] = w;
  }
  const col = (i) => (c.local[i] ? LOCAL.map((x) => x / 255) : heat(c.util[i]));   // per vertex: smooth
  const pos = [], cols = [];
  const put = (i, z, shade = 1) => { pos.push(P[3 * i], P[3 * i + 1], P[3 * i + 2] + z); cols.push(...col(i).map((x) => x * shade)); };
  const edges = new Map();
  const ne = tri.length / 3;
  for (let e = 0; e < ne; e++) {
    const a = tri[3 * e], b = tri[3 * e + 1], d = tri[3 * e + 2];
    put(a, -lift, 0.85); put(d, -lift, 0.85); put(b, -lift, 0.85);            // underside
    put(a, t + lift); put(b, t + lift); put(d, t + lift);                      // top face
    for (const [x, y] of [[a, b], [b, d], [d, a]]) {
      const key = x < y ? x + "," + y : y + "," + x;
      edges.set(key, edges.has(key) ? null : [x, y]);                         // seen once: an outline edge
    }
  }
  for (const v of edges.values()) {                                           // the cut edges, a shade darker
    if (!v) continue;
    const [x, y] = v;
    put(x, -lift, 0.7); put(y, -lift, 0.7); put(y, t + lift, 0.7);
    put(x, -lift, 0.7); put(y, t + lift, 0.7); put(x, t + lift, 0.7);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute("color", new THREE.Float32BufferAttribute(cols, 3));
  g.computeVertexNormals();
  // unlit and not tone-mapped, so the colours read exactly as the legend's; darker edges show the shape
  const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.DoubleSide, toneMapped: false }));
  m.castShadow = m.receiveShadow = true;
  return m;
}

// The case's loads, drawn as translucent pads just above the part (polygons in the part's own frame, mm).
export function loadMarks(c, t) {
  const g = new THREE.Group();
  g.userData.sink = c.loads_w || [];                 // each patch's mean deflection: the markers ride on the bend
  for (const ring of c.loads || []) {
    const sh = new THREE.Shape(ring.map(([x, y]) => new THREE.Vector2(x, y)));
    const geo = new THREE.ExtrudeGeometry(sh, { depth: 6, bevelEnabled: false });
    const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: 0x222222, transparent: true, opacity: 0.35, toneMapped: false }));
    m.position.z = t + 2; m.userData.z0 = t + 2; g.add(m);
  }
  return g;
}

export function sinkMarks(g, k) {
  g.children.forEach((m, i) => { m.position.z = m.userData.z0 - (g.userData.sink[i] || 0) * k; });
}
