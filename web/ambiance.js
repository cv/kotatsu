// "Ambiance" layer for the 3-D view: a wooden floor, tea things, a laptop and a book on the table,
// and someone napping on the shikibuton, legs under the table. All built from primitives and canvas textures.
import * as THREE from "three";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import { rng, canvas, texture, wrapped } from "./textures.js";

const shadowed = (o) => { o.traverse((m) => { if (m.isMesh) m.castShadow = m.receiveShadow = true; }); return o; };
const mat = (o) => new THREE.MeshStandardMaterial(o);

/** Medium-dark oak strip floor. One tile = tileMm square, planks ~180 mm wide. */
function floorTexture(tileMm = 1800, seed = 21) {
  const S = 1024, r = rng(seed), [c, g] = canvas(S, S), rows = 10, ph = S / rows;
  const tones = ["#6e4a2e", "#7a5434", "#63412a", "#80593a", "#5c3c26", "#74502f"];
  for (let k = 0; k < rows; k++) {
    const y0 = k * ph;
    let x = r() * S;                                   // stagger the seams per row
    const x0 = x;
    while (x < x0 + S) {
      const L = S * (0.35 + r() * 0.65), tone = tones[Math.floor(r() * tones.length)];
      wrapped(S, 0, (dx) => {
        g.fillStyle = tone; g.fillRect(x + dx, y0, L, ph);
        for (let i = 0; i < 26; i++) {                 // grain along the plank
          const yy = y0 + 3 + r() * (ph - 6), a = 0.05 + r() * 0.12, w = 0.6 + r() * 2.2;
          g.strokeStyle = r() < 0.6 ? `rgba(40,22,10,${a})` : `rgba(190,140,90,${a * 0.7})`; g.lineWidth = w;
          g.beginPath();
          for (let t = 0; t <= L; t += 12) {
            const yv = yy + 2.5 * Math.sin((t / L) * 6.28 * (1 + (i % 3)) + i);
            t ? g.lineTo(x + dx + t, yv) : g.moveTo(x + dx + t, yv);
          }
          g.stroke();
        }
        g.fillStyle = "rgba(20,10,4,0.55)"; g.fillRect(x + dx, y0, 2, ph);   // butt joint
      });
      x += L;
    }
    g.fillStyle = "rgba(20,10,4,0.6)"; g.fillRect(0, y0, S, 2);             // long seam
  }
  return texture(c, [1 / tileMm, 1 / tileMm]);
}

function screenTexture() {
  const W = 512, H = 330, r = rng(9), [c, g] = canvas(W, H);
  g.fillStyle = "#1d1f24"; g.fillRect(0, 0, W, H);
  g.fillStyle = "#2a2d34"; g.fillRect(0, 0, W, 18);
  ["#ff5f57", "#febc2e", "#28c840"].forEach((col, i) => { g.fillStyle = col; g.beginPath(); g.arc(12 + i * 14, 9, 4, 0, 6.3); g.fill(); });
  const cols = ["#c792ea", "#82aaff", "#c3e88d", "#f78c6c", "#89ddff", "#a6accd"];
  for (let y = 30, n = 0; y < H - 8; y += 13, n++) {
    let x = 14 + (n % 5 === 0 ? 0 : 16 * (1 + Math.floor(r() * 2)));
    const words = 1 + Math.floor(r() * 5);
    for (let w = 0; w < words && x < W - 40; w++) {
      const L = 12 + r() * 60; g.fillStyle = cols[Math.floor(r() * cols.length)];
      g.globalAlpha = 0.85; g.fillRect(x, y, L, 6); x += L + 7;
    }
  }
  g.globalAlpha = 1;
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

// Fur textures. Soft, broken stripes (blurred), a darker back and a cream belly.
function band(g, horizontal, p, w, len, wob, seed) {   // one wavy stripe across the canvas
  g.beginPath();
  for (let t = 0; t <= len; t += 6) {
    const o = p + wob * Math.sin(t / 37 + seed) + 0.5 * wob * Math.sin(t / 11 + 2 * seed);
    const [x, y] = horizontal ? [t, o] : [o, t];
    t ? g.lineTo(x, y) : g.moveTo(x, y);
  }
  for (let t = len; t >= 0; t -= 6) {
    const ww = w * (0.55 + 0.45 * Math.sin(t / 23 + seed * 3) ** 2);
    const o = p + ww + wob * Math.sin(t / 37 + seed) + 0.5 * wob * Math.sin(t / 11 + 2 * seed);
    const [x, y] = horizontal ? [t, o] : [o, t];
    g.lineTo(x, y);
  }
  g.closePath(); g.fill();
}

function softPatch(g, W, H, x, y, rx, ry, rgb, a) { // elliptical soft patch, wrapped in x
  for (const dx of [-W, 0, W]) {
    g.save(); g.translate(x + dx, y); g.scale(rx, ry);
    const gr = g.createRadialGradient(0, 0, 0, 0, 0, 1);
    gr.addColorStop(0, `rgba(${rgb},${a})`); gr.addColorStop(0.6, `rgba(${rgb},${a * 0.7})`); gr.addColorStop(1, `rgba(${rgb},0)`);
    g.fillStyle = gr; g.fillRect(-1, -1, 2, 2); g.restore();
  }
}

function flecks(g, W, H, r, n = 7000) {
  for (let i = 0; i < n; i++) {
    g.fillStyle = r() < 0.55 ? `rgba(255,232,195,${r() * 0.22})` : `rgba(120,64,26,${r() * 0.14})`;
    g.fillRect(r() * W, r() * H, 1, 2 + r() * 2);
  }
}

const FUR = "#e2a061", STRIPE = "rgba(176,98,44,0.40)", BACK = "196,128,66", CREAM = "247,226,196";

/** Body: u wraps around the spine (back at u = 0.25, belly at 0.75), v runs nose to tail. */
function bodyFur(seed = 33) {
  const W = 512, H = 256, r = rng(seed), [c, g] = canvas(W, H);
  g.fillStyle = FUR; g.fillRect(0, 0, W, H);
  softPatch(g, W, H, 0.25 * W, H / 2, 0.22 * W, H, BACK, 0.55);
  g.filter = "blur(1.6px)"; g.fillStyle = STRIPE;
  for (let i = 0; i < 15; i++) band(g, true, ((i + 0.3 + r() * 0.4) / 15) * H, 4 + r() * 4, W, 3 + r() * 3, r() * 9);
  g.filter = "none";
  softPatch(g, W, H, 0.75 * W, H / 2, 0.2 * W, H, CREAM, 1);
  flecks(g, W, H, r);
  return texture(c);
}

/** Tail: u runs along the tail, so stripes are rings (vertical in the canvas). */
function tailFur(seed = 34) {
  const W = 512, H = 128, r = rng(seed), [c, g] = canvas(W, H);
  g.fillStyle = FUR; g.fillRect(0, 0, W, H);
  g.filter = "blur(1.4px)"; g.fillStyle = "rgba(176,98,44,0.5)";
  for (let i = 0; i < 11; i++) band(g, false, ((i + 0.5) / 11) * W * 0.92, 7 + r() * 5, H, 2, r() * 9);
  g.filter = "none";
  flecks(g, W, H, r, 2500);
  return texture(c);
}

/** Head (poles along z, face at u = 0.25): a few forehead stripes, cream chin. */
function headFur(seed = 35) {
  const W = 512, H = 256, r = rng(seed), [c, g] = canvas(W, H);
  g.fillStyle = FUR; g.fillRect(0, 0, W, H);
  g.filter = "blur(1.6px)"; g.fillStyle = "rgba(176,98,44,0.45)";
  for (const [x, w] of [[0.25, 7], [0.215, 5], [0.285, 5], [0.1, 6], [0.4, 6], [0.6, 7], [0.75, 7], [0.9, 7]])
    band(g, false, x * W - w / 2, w, H * 0.42, 2.5, r() * 9);
  g.filter = "none";
  softPatch(g, W, H, 0.25 * W, 0.78 * H, 0.16 * W, 0.3 * H, CREAM, 1);
  flecks(g, W, H, r, 4000);
  return texture(c);
}

function kyusu() { // Japanese side-handled teapot (kyusu), tokoname clay: spout and handle at 90°
  const clay = mat({ color: 0x8c4a2c, roughness: 0.6, side: THREE.DoubleSide });
  const g = new THREE.Group();
  const lathe = (pts) => { // profile (radius, height), smoothed with a spline, revolved around z
    const prof = new THREE.SplineCurve(pts.map(([x, y]) => new THREE.Vector2(x, y))).getPoints(48);
    const geo = new THREE.LatheGeometry(prof, 64);
    geo.rotateX(Math.PI / 2);
    return new THREE.Mesh(geo, clay);
  };
  g.add(lathe([[0, 0], [30, 0], [50, 3], [62, 12], [68, 30], [66, 48], [57, 63], [40, 73]]));   // body
  g.add(lathe([[40, 73], [41, 76], [31, 83], [12, 88], [0, 89]]));                       // lid
  const knob = new THREE.Mesh(new THREE.SphereGeometry(8, 16, 12), clay); knob.position.z = 94; g.add(knob);
  // a tapered tube from `base` along `dir`: CylinderGeometry runs along +y, so turn +y onto dir
  const tube = (rBase, rEnd, len, base, dir, open = false) => {
    const geo = new THREE.CylinderGeometry(rEnd, rBase, len, 20, 1, open);
    geo.translate(0, len / 2, 0);
    const m = new THREE.Mesh(geo, clay);
    m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().normalize());
    m.position.copy(base);
    return m;
  };
  const up = (deg) => Math.tan((deg * Math.PI) / 180);
  // both start well inside the body so their base ends never show
  g.add(tube(14, 5, 100, new THREE.Vector3(36, 0, 18), new THREE.Vector3(1, 0, up(38))));        // spout, +x, rising 38°
  g.add(tube(12, 9.5, 112, new THREE.Vector3(0, -40, 36), new THREE.Vector3(0, -1, up(12))));    // handle, -y, rising 12°
  return g;
}

function yunomi() { // handle-less teacup, pale glaze, green tea inside
  const glaze = mat({ color: 0xe8e2d4, roughness: 0.3 });
  const g = new THREE.Group();
  const prof = [[0, 0], [28, 0], [31, 3], [35, 66], [36, 70], [33, 70], [30, 9], [0, 9]].map(([x, y]) => new THREE.Vector2(x, y));
  const cup = new THREE.LatheGeometry(prof, 40); cup.rotateX(Math.PI / 2); g.add(new THREE.Mesh(cup, glaze));
  const tea = new THREE.Mesh(new THREE.CircleGeometry(33, 32), mat({ color: 0x9c8f3c, roughness: 0.08 }));
  tea.position.z = 55; g.add(tea);
  return g;
}

function laptop() {
  const alu = mat({ color: 0xb9bcc1, metalness: 0.55, roughness: 0.35 });
  const g = new THREE.Group(), W = 304, D = 212;
  const base = new THREE.Mesh(new RoundedBoxGeometry(W, D, 14, 3, 5), alu); base.position.z = 7; g.add(base);
  const keys = new THREE.Mesh(new THREE.BoxGeometry(272, 108, 1), mat({ color: 0x2c2e33, roughness: 0.7 }));
  keys.position.set(0, 30, 14.2); g.add(keys);
  const pad = new THREE.Mesh(new THREE.BoxGeometry(120, 72, 0.6), mat({ color: 0xa9adb3, metalness: 0.4, roughness: 0.25 }));
  pad.position.set(0, -58, 14.1); g.add(pad);
  const lid = new THREE.Group(); lid.position.set(0, D / 2, 14);   // pivots on the hinge at the back edge
  const shell = new THREE.Mesh(new RoundedBoxGeometry(W, D, 5, 3, 2), alu); shell.position.set(0, -D / 2, 2.5);
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(W - 22, D - 26), mat({ color: 0x000000, emissive: 0xffffff, emissiveMap: screenTexture(), emissiveIntensity: 0.9, roughness: 0.2 }));
  screen.position.set(0, -D / 2 - 2, -0.2); screen.rotation.x = Math.PI;  // faces the user when open
  lid.add(shell, screen); lid.rotation.x = -1.92;  // opened ~110°, screen facing the user (-y)
  g.add(lid);
  return g;
}

function book() {
  const cover = mat({ color: 0x334766, roughness: 0.75 });
  const [c, ctx] = canvas(64, 64); ctx.fillStyle = "#f1e9d6"; ctx.fillRect(0, 0, 64, 64);
  for (let y = 0; y < 64; y += 2) { ctx.fillStyle = "rgba(120,100,70,0.18)"; ctx.fillRect(0, y, 64, 1); }
  const pages = mat({ map: texture(c), roughness: 0.9 });
  // BoxGeometry faces: +x, -x, +y, -y, +z, -z  (spine on -x)
  const m = new THREE.Mesh(new THREE.BoxGeometry(152, 229, 28), [pages, cover, pages, pages, cover, cover]);
  m.position.z = 14;
  const g = new THREE.Group(); g.add(m);
  const band = new THREE.Mesh(new THREE.BoxGeometry(153, 18, 28.4), mat({ color: 0xc9a24a, roughness: 0.4, metalness: 0.3 }));
  band.position.set(0, 70, 14); g.add(band);
  return g;
}

function catHead() { // the tabby's head, facing -y: big and round (that's most of the cute), ears, sleepy smile
  const g = new THREE.Group();
  const add = (geo, m, [x, y, z], [sx, sy, sz] = [1, 1, 1]) => { const o = new THREE.Mesh(geo, m); o.position.set(x, y, z); o.scale.set(sx, sy, sz); g.add(o); return o; };
  const cream = mat({ color: 0xf7e6cc, roughness: 0.95 });
  const headGeo = new THREE.SphereGeometry(1, 48, 32); headGeo.rotateX(Math.PI / 2);
  add(headGeo, mat({ map: headFur(), roughness: 0.95 }), [0, 0, 0], [84, 78, 70]);
  const ear = mat({ color: 0xd8915a, roughness: 0.95 }), inner = mat({ color: 0xf0aaa4, roughness: 0.9 });
  for (const s of [-1, 1]) {
    const e = new THREE.Group(); e.position.set(s * 44, 6, 52); e.rotation.set(-0.2, s * 0.5, 0);
    const cone = (rad, h) => { const geo = new THREE.ConeGeometry(rad, h, 24); geo.rotateX(Math.PI / 2); return geo; }; // axis up (+z)
    const outer = new THREE.Mesh(cone(25, 40), ear); outer.scale.set(1, 0.55, 1);      // flattened front to back
    const pink = new THREE.Mesh(cone(15, 28), inner); pink.scale.set(1, 0.4, 1); pink.position.set(0, -7, -4);
    e.add(outer, pink); g.add(e);
  }
  const fy = 0 - 74;                                   // front of the face
  for (const s of [-1, 1]) add(new THREE.SphereGeometry(1, 20, 14), cream, [0 + s * 13, fy - 6, 0 - 12], [17, 12, 13]); // whisker pads
  add(new THREE.SphereGeometry(1, 16, 10), mat({ color: 0xe48f93, roughness: 0.4 }), [0, fy - 14, 0 - 1], [8, 5, 5]);    // nose
  const lash = mat({ color: 0x3a2414, roughness: 0.6 });
  for (const s of [-1, 1]) {                               // sleepy closed eyes: little smiles ◡
    const eye = add(new THREE.TorusGeometry(11, 2.4, 8, 24, Math.PI), lash, [0 + s * 31, fy + 1.5, 0 + 16]);
    eye.rotation.set(-Math.PI / 2, 0, s * 0.42, "ZYX");    // bottom half of the ring, turned to follow the cheek
  }
  const blush = mat({ color: 0xf29b96, roughness: 0.9, transparent: true, opacity: 0.55 });
  for (const s of [-1, 1]) add(new THREE.SphereGeometry(1, 16, 10), blush, [0 + s * 46, fy + 10, 0 - 4], [13, 4, 8]);
  const wpts = [];
  for (const s of [-1, 1]) for (const k of [-1, 0, 1]) {
    const x0 = 0 + s * 20, z0 = 0 - 10 + k * 5;
    wpts.push(x0, fy - 10, z0, x0 + s * 75, fy - 4 - 6 * Math.abs(k), z0 + k * 14 + 4);
  }
  const wg = new THREE.BufferGeometry(); wg.setAttribute("position", new THREE.Float32BufferAttribute(wpts, 3));
  g.add(new THREE.LineSegments(wg, new THREE.LineBasicMaterial({ color: 0xfff8ee, transparent: true, opacity: 0.8 })));
  return g;
}

function cat() { // a curled-up orange tabby (~7 kg) asleep in the warm: chin on paws, tail round the front
  const g = new THREE.Group();
  const add = (geo, m, [x, y, z], [sx, sy, sz] = [1, 1, 1]) => { const o = new THREE.Mesh(geo, m); o.position.set(x, y, z); o.scale.set(sx, sy, sz); g.add(o); return o; };
  const cream = mat({ color: 0xf7e6cc, roughness: 0.95 });
  // body: a soft loaf, poles along the spine so the stripes ring it
  const body = new THREE.SphereGeometry(1, 64, 40); body.rotateZ(-Math.PI / 2);
  add(body, mat({ map: bodyFur(), roughness: 0.95 }), [0, 0, 86], [205, 160, 92]);
  // head: big and round, resting low at the front right
  const H = [140, -108, 66];
  const head = catHead(); head.position.set(...H); g.add(head);
  for (const s of [-1, 1]) add(new THREE.SphereGeometry(1, 24, 16), cream, [H[0] + s * 30, H[1] - 66, 16], [24, 36, 16]); // front paws
  // tail: tapered tube from the rump round the front, tip by the paws
  const path = new THREE.CatmullRomCurve3([[-195, 40, 36], [-222, -50, 28], [-170, -140, 22], [-60, -192, 19],
    [40, -196, 18], [90, -184, 17]].map(([x, y, z]) => new THREE.Vector3(x, y, z)));
  const T = 96, R = 16, tg = new THREE.TubeGeometry(path, T, 1, R), pos = tg.attributes.position, v = new THREE.Vector3();
  for (let i = 0; i <= T; i++) {
    const t = i / T, c = path.getPointAt(t), rad = 25 - 11 * t * t;
    for (let j = 0; j <= R; j++) { const k = i * (R + 1) + j; v.fromBufferAttribute(pos, k).sub(c).multiplyScalar(rad).add(c); pos.setXYZ(k, v.x, v.y, v.z); }
  }
  tg.computeVertexNormals();
  const tailTex = tailFur(); tailTex.repeat.set(1, 1);
  g.add(new THREE.Mesh(tg, mat({ map: tailTex, roughness: 0.95 })));
  add(new THREE.SphereGeometry(14, 16, 12), mat({ color: 0xe2a061, roughness: 0.95 }), path.getPointAt(1).toArray());
  return shadowed(g);
}

function catReach(pose) { // the same ~7 kg tabby up on its hind legs, front paws on the table's edge
  // pose (kotatsu/scenes.py cat_reach_pose): hips, shoulders, paws and head in its own (forward, up) frame from
  // its hind feet; Python places it clear of the quilt and the tabletop, and this only draws it.
  const g = new THREE.Group();
  const fur = mat({ map: bodyFur(), roughness: 0.95 }), cream = mat({ color: 0xf7e6cc, roughness: 0.95 });
  const V2 = ([x, z]) => new THREE.Vector2(x, z), LT = 330;
  const hip = V2(pose.hip), sh = V2(pose.sh), paw = V2(pose.paw);
  const v3 = (p, y = 0) => new THREE.Vector3(p.x, y, p.y);
  const seg = (a3, b3, r, m) => {                    // a capsule between two points
    const c = new THREE.Mesh(new THREE.CapsuleGeometry(r, Math.max(1, a3.distanceTo(b3)), 8, 16), m);
    c.position.copy(a3.clone().add(b3).multiplyScalar(0.5)); c.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b3.clone().sub(a3).normalize());
    return c;
  };
  const body = new THREE.Mesh(new THREE.SphereGeometry(1, 48, 32), fur);  // the torso, hips to shoulders
  body.scale.set(LT / 2 + 40, 92, 92); body.position.copy(v3(hip.clone().add(sh).multiplyScalar(0.5)));   // as long as the curled cat's loaf, as round
  body.rotation.y = -Math.atan2(sh.y - hip.y, sh.x - hip.x); g.add(body);
  const hc = v3(V2(pose.head));
  const head = catHead(); head.position.copy(hc); head.rotation.z = Math.PI / 2; g.add(head);   // the curled cat's head, facing forward (+x)
  for (const s of [-1, 1]) {
    const shY = s * 34;
    g.add(seg(v3(sh, shY), v3(paw, shY), 19, fur));                                   // a foreleg
    const toe = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 16), cream); toe.scale.set(36, 24, 16); toe.position.copy(v3(paw, shY)).add(new THREE.Vector3(10, 0, 4)); g.add(toe);
    const haunch = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 16), fur); haunch.scale.set(70, 38, 72); haunch.position.set(-15, s * 48, 95); g.add(haunch);
    g.add(seg(new THREE.Vector3(-20, s * 48, 70), new THREE.Vector3(10, s * 46, 18), 17, fur));   // a hind leg
    const foot = new THREE.Mesh(new THREE.SphereGeometry(1, 16, 12), cream); foot.scale.set(46, 20, 13); foot.position.set(32, s * 46, 12); g.add(foot);
  }
  const path = new THREE.CatmullRomCurve3([[-40, 0, 110], [-140, 30, 60], [-230, 70, 70], [-270, 110, 150]].map(([x, y, z]) => new THREE.Vector3(x, y, z)));
  g.add(new THREE.Mesh(new THREE.TubeGeometry(path, 40, 19, 12), mat({ map: tailFur(), roughness: 0.95 })));
  return shadowed(g);
}

function card(face = false, seed = 0) { // a playing card, 63 x 88 mm
  const r = rng(seed + 7);
  const m = new THREE.Mesh(new RoundedBoxGeometry(63, 88, 0.6, 2, 3),
    mat({ color: face ? 0xfbfaf6 : (r() < 0.5 ? 0xa8323a : 0x2f4e8c), roughness: 0.6 }));
  return m;
}

function cardPile(spread = false) {
  const g = new THREE.Group(), r = rng(spread ? 11 : 5);
  if (!spread) {
    const deck = new THREE.Mesh(new RoundedBoxGeometry(63, 88, 14, 2, 3), mat({ color: 0xa8323a, roughness: 0.6 }));
    deck.position.z = 7; g.add(deck);
  } else {
    for (let k = 0; k < 7; k++) { const c = card(true, k); c.position.set((r() - 0.5) * 90, (r() - 0.5) * 70, 0.7 * k + 0.3); c.rotation.z = (r() - 0.5) * 1.6; g.add(c); }
  }
  return shadowed(g);
}

function cardFan() { // five cards fanned in two hands: faces towards the player (the group's -x), tops leaning away
  const g = new THREE.Group();
  for (let k = 0; k < 5; k++) {
    const c = card(true, k + 20), piv = new THREE.Group();
    c.geometry = c.geometry.clone().rotateX(Math.PI / 2).rotateZ(Math.PI / 2);   // stood up in the y-z plane, face along x
    c.position.set(0, 0, 32); piv.add(c); piv.rotation.x = (k - 2) * 0.22; piv.position.x = k * 0.8;
    g.add(piv);
  }
  g.rotation.y = 0.45;            // tops tilted away, so the faces look up at the player
  const holder = new THREE.Group(); holder.add(g);
  return shadowed(holder);
}

function sushi() { // a geta board of nigiri and maki
  const g = new THREE.Group();
  const wood = mat({ color: 0xd8b98a, roughness: 0.7 });
  const board = new THREE.Mesh(new RoundedBoxGeometry(380, 190, 18, 2, 4), wood); board.position.z = 30; g.add(board);
  for (const x of [-140, 140]) { const f = new THREE.Mesh(new THREE.BoxGeometry(24, 170, 22), wood); f.position.set(x, 0, 11); g.add(f); }
  const rice = mat({ color: 0xf6f2e8, roughness: 0.9 });
  const tops = [0xf08a5d, 0xc0303a, 0xf3c94c, 0xf08a5d, 0xe9e2d0, 0xc0303a];
  tops.forEach((c, k) => {
    const x = -150 + k * 58, y = 40;
    const ri = new THREE.Mesh(new RoundedBoxGeometry(44, 24, 20, 2, 8), rice); ri.position.set(x, y, 49); g.add(ri);
    const fish = new THREE.Mesh(new RoundedBoxGeometry(52, 28, 7, 2, 3), mat({ color: c, roughness: 0.5 })); fish.position.set(x, y, 61); g.add(fish);
  });
  for (let k = 0; k < 6; k++) {
    const m = new THREE.Mesh(new THREE.CylinderGeometry(19, 19, 30, 24), [mat({ color: 0x1f2a1e, roughness: 0.8 }), rice, rice]);
    m.rotation.x = Math.PI / 2; m.rotation.set(0, 0, 0); m.position.set(-150 + k * 58, -45, 54); g.add(m);
    const fill = new THREE.Mesh(new THREE.CylinderGeometry(7, 7, 31, 12), mat({ color: 0xf08a5d })); fill.position.copy(m.position); g.add(fill);
  }
  const wasabi = new THREE.Mesh(new THREE.SphereGeometry(14, 12, 8), mat({ color: 0x8fbf5a })); wasabi.position.set(165, -60, 44); wasabi.scale.z = 0.6; g.add(wasabi);
  return shadowed(g);
}

function plate() {
  const g = new THREE.Group();
  const p = new THREE.Mesh(new THREE.CylinderGeometry(85, 70, 14, 40), mat({ color: 0xf2efe8, roughness: 0.35 })); p.rotation.x = Math.PI / 2; p.position.z = 7; g.add(p);
  const soy = new THREE.Mesh(new THREE.CylinderGeometry(38, 32, 12, 28), mat({ color: 0x2c3e5c, roughness: 0.3 })); soy.rotation.x = Math.PI / 2; soy.position.set(110, 40, 6); g.add(soy);
  const s = new THREE.Mesh(new THREE.CylinderGeometry(30, 30, 1, 24), mat({ color: 0x3a1e10, roughness: 0.2 })); s.rotation.x = Math.PI / 2; s.position.set(110, 40, 12.5); g.add(s);
  return shadowed(g);
}

function chopsticks() {
  const g = new THREE.Group(), m = mat({ color: 0x5a3a24, roughness: 0.5 });
  for (const y of [-9, 9]) { const c = new THREE.Mesh(new THREE.CylinderGeometry(3, 5, 230, 10), m); c.rotation.z = Math.PI / 2; c.position.set(0, y, 8); g.add(c); }
  const rest = new THREE.Mesh(new RoundedBoxGeometry(18, 46, 12, 2, 5), mat({ color: 0xe9e4da })); rest.position.set(-90, 0, 6); g.add(rest);
  return shadowed(g);
}

function bowl() {
  const g = new THREE.Group();
  const pts = [[0, 0], [38, 0], [52, 18], [58, 60], [54, 62], [48, 22], [0, 18]].map(([r, z]) => new THREE.Vector2(r, z));
  const b = new THREE.Mesh(new THREE.LatheGeometry(pts, 40), mat({ color: 0x6b1f1f, roughness: 0.3, side: THREE.DoubleSide })); b.rotation.x = Math.PI / 2; g.add(b);
  const soup = new THREE.Mesh(new THREE.CircleGeometry(51, 32), mat({ color: 0xa5763d, roughness: 0.4 })); soup.position.z = 48; g.add(soup);
  return shadowed(g);
}

function laptopStand() { // an aluminium stand lifting the laptop's screen ~15 cm, the laptop on it
  const g = new THREE.Group(), al = mat({ color: 0xbfc3c8, roughness: 0.35, metalness: 0.6 });
  // two flat-footed side plates, sloped on top (118 mm at the front, -y, to 177 at the back), carrying the deck
  const T = Math.tan(0.25), side = new THREE.Shape([[-115, 0], [115, 0], [115, 147 + 115 * T], [-115, 147 - 115 * T]].map(([y, z]) => new THREE.Vector2(y, z)));
  for (const x of [-127, 113]) {
    const geo = new THREE.ExtrudeGeometry(side, { depth: 14, bevelEnabled: false });   // the shape in (y, z), extruded along x
    geo.applyMatrix4(new THREE.Matrix4().set(0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1));   // shape x -> y, shape y -> z, depth -> x
    const m = new THREE.Mesh(geo, al); m.position.x = x; g.add(m);
  }
  const deck = new THREE.Mesh(new THREE.BoxGeometry(280, 250, 6), al); deck.position.set(0, 0, 150); deck.rotation.x = 0.25; g.add(deck);   // the back (+y, the hinge) higher
  const lap = laptop(); lap.position.set(0, -10, 156); lap.rotation.x = 0.25; g.add(lap);
  return shadowed(g);
}

function keyboard() {
  const g = new THREE.Group();
  const k = new THREE.Mesh(new RoundedBoxGeometry(440, 130, 18, 2, 5), mat({ color: 0x3b3f45, roughness: 0.6 })); k.position.z = 9; g.add(k);
  const keys = new THREE.Mesh(new THREE.BoxGeometry(410, 100, 4), mat({ color: 0xd7d9dc, roughness: 0.7 })); keys.position.z = 19; g.add(keys);
  return shadowed(g);
}

function mouse() {
  const m = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 16), mat({ color: 0xe8e8e8, roughness: 0.4 }));
  m.scale.set(32, 56, 18); m.position.z = 14;
  const g = new THREE.Group(); g.add(m); return shadowed(g);
}

function bookOpen() { // an open paperback held up to read: pages facing the reader (the group's -x)
  const g = new THREE.Group(), paper = mat({ color: 0xf6f0e2, roughness: 0.9 }), cover = mat({ color: 0x7a2e2a, roughness: 0.7 });
  for (const s of [-1, 1]) {
    const leaf = new THREE.Group();
    const pg = new THREE.Mesh(new THREE.BoxGeometry(6, 110, 175), paper); pg.position.set(0, s * 55, 0); leaf.add(pg);
    const cv = new THREE.Mesh(new THREE.BoxGeometry(2, 112, 178), cover); cv.position.set(4, s * 56, 0); leaf.add(cv);
    leaf.rotation.z = s * 0.35; g.add(leaf);
  }
  g.rotation.y = 0.6;   // tilted back towards the reader's eyes
  const h = new THREE.Group(); h.add(g); return shadowed(h);
}

function zaisu(seatH) { // a legless chair: a cushioned seat seatH high (sat on) and a reclined back, facing +x
  const g = new THREE.Group(), fabric = mat({ color: 0x3a3d42, roughness: 0.9 }), base = mat({ color: 0x23252a, roughness: 0.8 });
  const b = new THREE.Mesh(new RoundedBoxGeometry(440, 440, seatH - 60, 2, 10), base); b.position.z = (seatH - 60) / 2; g.add(b);
  const c = new THREE.Mesh(new RoundedBoxGeometry(430, 430, 90, 3, 30), fabric); c.position.z = seatH - 15; g.add(c);
  const back = new THREE.Mesh(new RoundedBoxGeometry(70, 430, 480, 3, 25), fabric);
  back.position.set(-210, 0, seatH + 200); back.rotation.y = -0.28; g.add(back);   // kotatsu/scenes.py ZAISU must match
  return shadowed(g);
}

const PROPS = { cat_curled: () => cat(), card_pile: (q) => cardPile(!!q.spread), card_fan: () => cardFan(), sushi, plate, chopsticks, bowl,
  kyusu: () => kyusu(), yunomi: () => yunomi(), laptop_stand: laptopStand, keyboard, mouse, book_open: bookOpen };

/** One scene's things (kotatsu/scenes.py places them all): people, props on the floor and the top, things held. */
export function sceneLayer(S, { topZ, edgeX }) {
  const out = { people: (S.people || []).map((P) => person({ parts: P })), floor: [], top: [], held: [] };
  for (const q of S.props || []) {
    let o;
    if (q.kind === "zaisu") o = zaisu(q.seat_h);
    else if (q.kind === "cat_reach") o = catReach(q.pose);
    else o = PROPS[q.kind]?.(q);
    if (!o) continue;
    o.position.set(...q.pos); o.rotation.z = q.yaw || 0; out.floor.push(o);
  }
  for (const q of S.top || []) {
    const o = PROPS[q.kind]?.(q); if (!o) continue;
    o.position.set(q.pos[0], q.pos[1], topZ); o.rotation.z = q.yaw || 0; out.top.push(shadowed(o));
  }
  for (const q of S.held || []) {
    const o = PROPS[q.kind]?.(q); if (!o) continue;
    o.position.set(...q.pos); o.rotation.z = q.yaw || 0; out.held.push(o);   // its -x face turned back towards the holder
  }
  return out;
}

function person(P) { // someone napping, posed and sized in Python (kotatsu/sleeper.py): the page only draws it
  const g = new THREE.Group();
  const M = { top: mat({ color: 0xd9cbb4, roughness: 0.95 }), pants: mat({ color: 0x4a4a52, roughness: 0.9 }),
    skin: mat({ color: 0xd9a988, roughness: 0.7 }), hair: mat({ color: 0x2e241c, roughness: 0.8 }),
    socks: mat({ color: 0xece6dc, roughness: 0.95 }) };
  const up = new THREE.Vector3(0, 1, 0);
  for (const q of P.parts) {
    let o;
    if (q.kind === "capsule") {
      const a = new THREE.Vector3(...q.a), b = new THREE.Vector3(...q.b), d = b.clone().sub(a);
      o = new THREE.Mesh(new THREE.CapsuleGeometry(q.r, Math.max(1, d.length()), 8, 20), M[q.mat]);
      o.position.copy(a.clone().add(b).multiplyScalar(0.5));
      o.quaternion.setFromUnitVectors(up, d.normalize());
    } else {
      o = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 20), M[q.mat]);
      o.scale.set(...q.r); o.position.set(...q.c); o.rotation.set(0, -(q.pitch || 0), q.yaw, "ZYX");   // yaw, then the long axis tilted up
    }
    g.add(o);
  }
  return shadowed(g);
}

/** Everything in the ambiance layer, placed around a table centred at (cx, cy) with its top surface at topZ. */
export function ambiance({ cx, cy, topZ, floorZ, half, sleeper }) {
  const size = 5200, tile = 1800, ftex = floorTexture(tile);
  ftex.repeat.set(size / tile, size / tile);            // plane UVs run 0..1, so repeat = tiles across
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(size, size), mat({ map: ftex, roughness: 0.55 }));
  floor.position.set(cx, cy, floorZ); floor.receiveShadow = true;
  const onTop = [];
  const put = (o, x, y, rot = 0) => { o.position.set(cx + x, cy + y, topZ); o.rotation.z = rot; onTop.push(shadowed(o)); };
  const k = half / 430;  // positions scaled to the top's size
  // the default view looks in from the front-right, so the tea things sit back-right, clear of the screen
  put(laptop(), -110 * k, -140 * k, 0.06);
  put(book(), 270 * k, -200 * k, -0.35);
  put(kyusu(), 235 * k, 200 * k, 2.6);
  put(yunomi(), 70 * k, 270 * k);
  return { floor, onTop, under: sleeper ? [person(sleeper)] : [] };
}
