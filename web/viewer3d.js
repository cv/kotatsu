// 3-D assembly preview (three.js): top boards + every frame part at its real placement, plus the room
// layers (rug, draped futon, floor pillows).
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import GUI from "lil-gui";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { birchFace, plyEdge, cotton, braidedRug } from "./textures.js";
import { ambiance } from "./ambiance.js";
import { heatSlab, bend, loadMarks, maxDisp, GRADIENT } from "./fea3d.js";

// Lighting moods. Key = a window light from the front-left (casts the shadows); env = soft image-based
// fill from a generic room (gives the glaze and aluminium something to reflect); lamp = a warm pendant
// over the table; glow = the heater's orange light under the futon.
const LIGHT = {
  day:     { bg: 0xf4efe7, key: 3.0, keyCol: 0xffecd6, env: 0.55, hemi: 0.3, lamp: 0, glow: 0.8, exposure: 1.0 },
  evening: { bg: 0x17130f, key: 0.35, keyCol: 0x9fb2ff, env: 0.1, hemi: 0.06, lamp: 2.6, glow: 3.2, exposure: 1.15 },
};

const COL = { heater: 0x2b2b2b, futon: 0x56637f, seat: 0xb4643f, rugSide: 0xb9a888 };
// all parts are the same pale birch; a faint tint per kind keeps them apart while they come together
const TINT = { top: 0xffffff, frame: 0xfbf6ee, deck: 0xf4ebdd, cheek: 0xf4ebdd, wedge: 0xf1e2c8 };

const TEX = {}; // textures and materials, made once
function woodMats(kind, grain, t) {
  const key = kind + grain;
  if (TEX[key]) return TEX[key];
  if (!TEX.face) { TEX.face = birchFace(11); TEX.edge = plyEdge(t); }
  let face = TEX.face;
  if (grain === "v") { face = TEX.face.clone(); face.rotation = Math.PI / 2; face.needsUpdate = true; }
  const tint = TINT[kind] ?? TINT.frame;
  TEX[key] = [
    new THREE.MeshStandardMaterial({ map: face, color: tint, roughness: 0.78, side: THREE.DoubleSide }),
    new THREE.MeshStandardMaterial({ map: TEX.edge, color: tint, roughness: 0.9, side: THREE.DoubleSide }),
  ];
  return TEX[key];
}

function shapeFrom(p) {
  const s = new THREE.Shape(p.ext.map(([x, y]) => new THREE.Vector2(x, y)));
  for (const h of p.holes) s.holes.push(new THREE.Path(h.map(([x, y]) => new THREE.Vector2(x, y))));
  return s;
}

function slab(p, t, kind, grain = "u") {
  const geo = new THREE.ExtrudeGeometry(shapeFrom(p), { depth: t, bevelEnabled: false, curveSegments: 8 });
  const mesh = new THREE.Mesh(geo, woodMats(kind, grain, t)); // group 0 = faces, group 1 = cut edges
  mesh.castShadow = mesh.receiveShadow = true;
  const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geo, 25),
    new THREE.LineBasicMaterial({ color: 0x5a4632, transparent: true, opacity: 0.28 }));
  const g = new THREE.Group(); g.add(mesh, edges);
  return g;
}

// local (u, v, w=extrude) -> world, per panel axis
const BASIS = {
  x: new THREE.Matrix4().set(1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1),
  y: new THREE.Matrix4().set(0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1),
};

export class Viewer3D {
  constructor(container) {
    this.c = container;
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setPixelRatio(devicePixelRatio);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    container.appendChild(this.renderer.domElement);
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0xfdfbf8);
    this.camera = new THREE.PerspectiveCamera(35, 1, 10, 20000);
    this.camera.up.set(0, 0, 1);
    this.camera.position.set(2100, -1500, 1400);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.target.set(600, 400, 220);
    this.controls.addEventListener("change", () => this.render());
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this.scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    this.hemi = new THREE.HemisphereLight(0xfff4e6, 0x6b5440, 0.3); this.scene.add(this.hemi);
    const lamp = new THREE.PointLight(0xffc27a, 0, 4200, 0);  // decay 0 + range: soft falloff in mm units
    lamp.castShadow = true; lamp.shadow.mapSize.set(1024, 1024); lamp.shadow.bias = -0.002; lamp.shadow.radius = 6;
    this.scene.add(lamp); this.lamp = lamp;
    this.glows = [];
    const sun = new THREE.DirectionalLight(0xffecd6, 3.0);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    Object.assign(sun.shadow.camera, { left: -1700, right: 1700, top: 1700, bottom: -1700, near: 100, far: 6000 });
    sun.shadow.bias = -0.0004; sun.shadow.normalBias = 1.5; sun.shadow.radius = 6;
    this.scene.add(sun, sun.target);
    this.sun = sun;
    const grid = new THREE.GridHelper(3000, 30, 0xcfc6b8, 0xe7e0d6); grid.rotation.x = Math.PI / 2;
    grid.position.set(600, 400, -12); this.scene.add(grid); // just under the rug
    this.grid = grid;
    this.root = new THREE.Group(); this.scene.add(this.root);
    this.state = { table: null, assembly: null, showTop: true, showFrame: true, showHeater: true,
      showFuton: true, showRug: true, showChairs: true, showPillows: true, showAmbiance: true, light: "day",
      fea: "off", feaBend: 0, feaPulse: true };
    new ResizeObserver(() => this.resize()).observe(container);
    this.caption = document.createElement("div"); this.caption.className = "asm-caption"; container.appendChild(this.caption);
  }

  setData(data) {
    this.data = data;
    const tnames = data.tables.length > 1 ? [...data.tables.map((t) => t.name), "all"] : data.tables.map((t) => t.name);
    if (!tnames.includes(this.state.table)) this.state.table = tnames[0];
    if (!this.gui) {
      this.gui = new GUI({ container: this.c, title: "View" });
      this.gui.domElement.style.position = "absolute"; this.gui.domElement.style.right = "8px"; this.gui.domElement.style.top = "8px";
      if (tnames.length > 1) this.gui.add(this.state, "table", tnames).name("table").onChange(() => { this.framed = false; this.build(); });
      // the assembly, step by step (kotatsu/assembly.py): 0 = all apart, n = built
      this.steps = data.tables[0].frame.assembly?.steps || [];
      this.state.assembly ??= this.steps.length;
      this.asmCtl = this.gui.add(this.state, "assembly", 0, this.steps.length, 0.01)
        .decimals(1).onChange(() => { this.playing = false; this.place(); });
      this.gui.add(this, "play").name("▶ play the assembly");
      this.gui.add(this.state, "showTop").name("top").onChange(() => this.place());
      this.gui.add(this.state, "showFrame").name("frame").onChange(() => this.place());
      this.gui.add(this.state, "showHeater").name("heater").onChange(() => this.place());
      this.gui.add(this.state, "showFuton").name("futon").onChange(() => this.place());
      this.gui.add(this.state, "showChairs").name("chairs").onChange(() => this.place());
      this.gui.add(this.state, "showPillows").name("pillows").onChange(() => this.place()); // floor pillows and the chairs' cushions
      this.gui.add(this.state, "showRug").name("rug").onChange(() => this.place());
      this.gui.add(this.state, "showAmbiance").name("ambiance").onChange(() => this.place());
      this.gui.add(this.state, "light", Object.keys(LIGHT)).name("light").onChange(() => this.applyLight());
      if (data.fea) this.feaGui(data.fea);
    }
    this.build();
  }

  build() {
    const d = this.data; if (!d) return;
    this.root.clear();
    this.items = []; this.glows = []; this.slots = {}; this.itemPart = new Map(); // where each part sits (FEA)
    const t = d.thickness;
    const which = this.state.table === "all" ? d.tables : d.tables.filter((x) => x.name === this.state.table);
    let dx = 0;
    for (const T of which) {
      this.addTable(T, dx, t);
      dx += T.top.length + 400;
    }
    for (const it of this.items) this.root.add(it.obj);
    const c = new THREE.Box3().setFromObject(this.root).getCenter(new THREE.Vector3()); // aim the sun at the table
    this.sun.target.position.set(c.x, c.y, 0);
    this.sun.position.set(c.x - 1500, c.y - 1100, 1700);    // a low window light from the front-left
    this.lamp.position.set(c.x + 60, c.y + 40, 1650);       // pendant over the table
    this.applyLight();
    if (!this.framed) { this.framed = true; this.frame(); }
    this.place();
    if (this.feaCase) this.feaShow(false);   // the heat maps sit on the parts just rebuilt
  }

  addTable(T, dx, t) {
    const F = T.frame;
    const off = new THREE.Vector3(dx, 0, 0);
    const opt = { boards: T.top.boards, keys: [] };
    const ztop = F.height + F.futon_gap;
    const A = F.assembly || {};
    this.asm = A;
    // hideBefore: things that only turn up at their step (the top, heater, futon, tea), instead of waiting in view
    const push = (obj, kind, moves = [], hideBefore = false) => {
      obj.position.add(off); this.items.push({ obj, kind, moves, hideBefore, base: obj.position.clone() });
    };
    opt.boards.forEach((h) => {
      const m = slab(h, t, "top", "u"); m.position.z = ztop;
      push(m, "top", A.top, true);
      (this.slots.top ??= []).push({ M: new THREE.Matrix4().makeTranslation(off.x, off.y, ztop), mirror: false, it: this.items.at(-1) });
    });
    const byName = Object.fromEntries(F.parts.map((p) => [p.name, p]));
    for (const pl of F.placed) {
      const part = byName[pl.part];
      let shape = part.shape;
      if (pl.mirror) shape = { ext: shape.ext.map(([u, v]) => [-u, v]).reverse(), holes: shape.holes.map((h) => h.map(([u, v]) => [-u, v]).reverse()) };
      const m = slab(shape, t, pl.kind, part.grain || "u");
      if (pl.matrix) m.applyMatrix4(new THREE.Matrix4().set(...pl.matrix)); // Python's placement (the chairs)
      else {
        if (pl.axis !== "z") m.applyMatrix4(BASIS[pl.axis]);
        m.position.set(...pl.origin);
      }
      const kind = pl.kind === "wedge" ? "wedge" : pl.kind === "chair" ? "chair" : "frame";
      push(m, kind, pl.moves, pl.kind !== "frame"); // the legs are there from the start
      const M = pl.matrix ? new THREE.Matrix4().set(...pl.matrix)
        : (pl.axis !== "z" ? BASIS[pl.axis].clone() : new THREE.Matrix4()).premultiply(new THREE.Matrix4().makeTranslation(...pl.origin));
      (this.slots[pl.part] ??= []).push({ M: M.premultiply(new THREE.Matrix4().makeTranslation(off.x, off.y, off.z)), mirror: !!pl.mirror, it: this.items.at(-1) });
      this.itemPart.set(this.items.at(-1), pl.part);
    }
    const hz = F.heater;
    const heater = new THREE.Mesh(new THREE.BoxGeometry(...hz.size), new THREE.MeshStandardMaterial({ color: COL.heater, roughness: 0.5 }));
    heater.castShadow = true;
    const glow = new THREE.PointLight(0xff5a1f, 1, 750, 0); // the heater's orange glow, moves with it
    glow.position.set(0, 0, -hz.size[2] / 2 - 15); heater.add(glow); this.glows.push(glow);
    heater.position.set(...hz.center);
    push(heater, "heater", A.heater, true);
    if (T.room3d) this.addRoom(T.room3d, push);
    const amb = ambiance({ cx: hz.center[0], cy: hz.center[1], topZ: ztop + t, half: T.top.length / 2,
      floorZ: T.room3d ? -T.room3d.rug.t - 0.5 : -1 });   // table-local; push() adds the table offset
    push(amb.floor, "ambFloor");
    for (const o of amb.onTop) push(o, "ambTop", A.tea, true);
    for (const o of amb.under) push(o, "amb", (A.tea || []).map((m) => ({ ...m, from: [0, 0, 0] })), true); // the cat just turns up
  }

  applyLight() {
    const L = LIGHT[this.state.light] || LIGHT.day;
    this.scene.background = new THREE.Color(L.bg);
    this.sun.intensity = L.key; this.sun.color.setHex(L.keyCol);
    this.scene.environmentIntensity = L.env; this.hemi.intensity = L.hemi;
    this.lamp.intensity = L.lamp; this.lamp.visible = L.lamp > 0;
    for (const g of this.glows) g.intensity = L.glow;
    this.renderer.toneMappingExposure = L.exposure;
    this.render();
  }

  addRoom(R, push) { // rug, draped futon and floor pillows; geometry comes from Python (room.room3d)
    TEX.rug ??= braidedRug();
    TEX.cotton ??= cotton(3, false);
    TEX.quilt ??= cotton(4, true);
    const rugCap = new THREE.MeshStandardMaterial({ map: TEX.rug, roughness: 1 });
    const rug = new THREE.Mesh(new THREE.CylinderGeometry(R.rug.d / 2, R.rug.d / 2, R.rug.t, 128),
      [new THREE.MeshStandardMaterial({ color: COL.rugSide, roughness: 1 }), rugCap, rugCap]); // side, top, bottom
    rug.receiveShadow = true;
    rug.rotation.x = Math.PI / 2; rug.position.set(R.rug.center[0], R.rug.center[1], -R.rug.t / 2);
    push(rug, "rug");
    const n = R.futon.n, geo = new THREE.BufferGeometry(), idx = [];
    geo.setAttribute("position", new THREE.Float32BufferAttribute(R.futon.pts, 3));
    for (let j = 0; j < n - 1; j++) for (let i = 0; i < n - 1; i++) {
      const a = j * n + i, b = a + 1, c = a + n, d = c + 1;
      idx.push(a, b, d, a, d, c);
    }
    const uv = [], quilts = Math.max(2, Math.round(R.futon.size / 254)); // ~ 25 cm quilted squares
    for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) uv.push((i / (n - 1)) * quilts, (j / (n - 1)) * quilts);
    geo.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
    geo.setIndex(idx); geo.computeVertexNormals();
    const futon = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ map: TEX.quilt, color: COL.futon, roughness: 0.95, side: THREE.DoubleSide }));
    futon.castShadow = futon.receiveShadow = true;
    futon.renderOrder = 2; // drawn after the opaque parts, so it can fade over them
    push(futon, "futon", this.asm?.futon, true);
    const seatTex = TEX.cotton.clone(); seatTex.repeat.set(2, 2); seatTex.needsUpdate = true;
    const seatMat = new THREE.MeshStandardMaterial({ map: seatTex, color: COL.seat, roughness: 0.9 });
    for (const st of R.seats) {
      const [w, d, h] = st.size;
      const m = new THREE.Mesh(new RoundedBoxGeometry(w, d, h, 4, Math.min(35, h / 2.2)), seatMat);
      m.position.set(...st.center);
      m.castShadow = m.receiveShadow = true;
      push(m, "seat");
    }
  }

  place() {
    const S = this.state, fc = this.feaCase;
    const s = fc ? (this.steps?.length ?? 0) : (S.assembly ?? this.steps?.length ?? 0); // FEA: the table as built
    if (this.grid) this.grid.visible = !S.showAmbiance;
    const local = (m) => Math.min(1, Math.max(0, (s - m.step - m.a) / (m.b - m.a)));
    const ease = (x) => x * x * (3 - 2 * x);
    for (const it of this.items || []) {
      const vis = { top: S.showTop, frame: S.showFrame, wedge: S.showFrame, heater: S.showHeater,
        futon: S.showFuton, rug: S.showRug, seat: S.showPillows, chair: S.showChairs,
        ambTop: S.showAmbiance && S.showTop, amb: S.showAmbiance, ambFloor: S.showAmbiance }[it.kind];
      const started = !it.moves?.length || s > it.moves[0].step + it.moves[0].a;
      it.obj.visible = vis && (started || !it.hideBefore);
      if (fc) { // a heat map: just the frame (and the top, if it's the top's case); the analysed part is painted
        const keep = it.kind === "frame" || it.kind === "wedge" || (it.kind === "heater" && fc.part !== "deck") || (it.kind === "top" && fc.part === "top");
        it.obj.visible = keep && !this.feaHidden?.has(it);
      }
      it.obj.position.copy(it.base);
      for (const m of it.moves || []) {
        const k = 1 - ease(local(m));
        it.obj.position.x += m.from[0] * k; it.obj.position.y += m.from[1] * k; it.obj.position.z += m.from[2] * k;
      }
      if (it.kind === "futon") { // fades in as it settles over the frame
        const mat = it.obj.material, o = it.moves?.length ? ease(local(it.moves[0])) : 1;
        const fade = o < 0.999;
        if (mat.transparent !== fade) { mat.transparent = fade; mat.depthWrite = !fade; mat.needsUpdate = true; }
        mat.opacity = o;
        it.obj.castShadow = o > 0.6; // a see-through futon shouldn't darken the frame inside it
      }
    }
    const n = this.steps?.length || 0, k = Math.min(Math.floor(s), n - 1);
    this.caption.textContent = s < n && k >= 0 ? `Step ${k + 1} of ${n} · ${this.steps[k]}` : "";
    this.caption.hidden = !this.caption.textContent;
    if (fc) this.feaCarry(this.feaK ?? 0);
    this.render();
  }

  // ---------------------------------------------------------------- FEA heat maps (kotatsu/fea_view.py)
  feaGui(info) {
    const f = this.gui.addFolder("stress (FEA)");
    this.feaInfo = info;
    this.feaCtl = f.add(this.state, "fea", ["off"]).name("load case").onChange(() => this.feaShow());
    this.feaBendCtl = f.add(this.state, "feaBend", 0, 300, 1).name("bend ×").onChange(() => this.feaShow(false));
    f.add(this.state, "feaPulse").name("pulse").onChange(() => this.feaAnimate());
    f.close();
    f.onOpenClose((g) => { if (!g._closed) this.feaLoad(); });
    this.legend = document.createElement("div");
    Object.assign(this.legend.style, { position: "absolute", left: "12px", bottom: "40px", padding: "8px 10px", maxWidth: "430px",
      background: "rgba(255,255,255,0.92)", borderRadius: "6px", font: "12px/1.4 system-ui, sans-serif", color: "#333" });
    this.legend.hidden = true;
    this.c.appendChild(this.legend);
  }

  async feaLoad() {
    if (this.fea) return this.fea;
    const r = await fetch("fea.json", { cache: "no-store" });
    this.fea = await r.json();
    const labels = ["off", ...this.fea.cases.map((c) => c.label)];
    this.feaCtl = this.feaCtl.options(labels).onChange(() => this.feaShow());
    return this.fea;
  }

  feaShow(resetBend = true) {
    for (const o of this.feaObjs || []) { this.root.remove(o); o.geometry.dispose(); }
    if (this.feaMarks) { this.root.remove(this.feaMarks); this.feaMarks = null; }
    this.feaObjs = []; this.feaHidden = new Set();
    const c = this.fea?.cases.find((x) => x.label === this.state.fea);
    this.feaCase = c || null;
    if (!c) { for (const it of this.items || []) it.obj.matrixAutoUpdate = true; this.legend.hidden = true; this.place(); return; }
    const md = Math.max(...(c.senses || [c]).map((x) => maxDisp({ kind: c.kind, ...x })));
    if (resetBend) { this.state.feaBend = md > 0 ? Math.max(1, Math.min(300, Math.round(25 / md))) : 1; this.feaBendCtl.updateDisplay(); }
    const me = this.fea.meshes[c.mesh], t = this.fea.thickness, slots = this.slots[c.part] || [];
    // leg cases name the placements that bend in the push's plane, each with its sense; plates: every placement
    const on = c.on ? c.on.map((e) => [slots[e.i], { kind: c.kind, ...c.senses[e.sense] }]) : slots.map((sl) => [sl, c]);
    for (const [sl, data] of on) {
      if (!sl) continue;
      const m = heatSlab(me, data, t, sl.mirror);
      m.matrixAutoUpdate = false; m.matrix.copy(sl.M);
      this.root.add(m); this.feaObjs.push(m); this.feaHidden.add(sl.it);
    }
    const sl0 = (this.slots[c.part] || [])[0];
    if (sl0 && c.loads?.length) {                       // where the load presses (plates seen from above)
      const lm = loadMarks(c, t); lm.matrixAutoUpdate = false; lm.matrix.copy(sl0.M);
      this.root.add(lm); this.feaMarks = lm;
    }
    this.feaBendNow(1);
    const pct = (u) => `${Math.round(u * 100)} %`;
    const extra = c.sag_mm != null ? `sags ${c.sag_mm} mm` : c.sway_mm != null ? `sways ${c.sway_mm} mm` : "";
    this.legend.innerHTML = `<b>${c.label}</b><br>worst ${pct(c.worst)} of its strength${extra ? ", " + extra : ""}${c.on ? " (a push along x: the plates along x bend in their plane, the rest of the frame is carried along)" : ""}
      (deflection drawn × ${this.state.feaBend})
      <div style="height:10px;margin:6px 0 2px;border-radius:3px;background:${GRADIENT}"></div>
      <div style="display:flex;justify-content:space-between"><span>0</span><span>50 %</span><span>100 %</span><span>150 %</span></div>
      <span style="color:#777">Share of strength (Tsai-Hill), thinnest sheet (${this.fea.thickness} mm). Grey: right at a support or
      contact, where the peaks are local bearing, not bending. Each part is analysed alone, its neighbours as supports: the rest of the frame only follows (shifted, leaning or riding down), it isn't bent.
      ${this.feaInfo.stale ? "<br><b style='color:#b00'>Stale: the design changed since these were computed (make fea).</b>" : ""}</span>`;
    this.legend.hidden = false;
    this.place();
    this.feaAnimate();
  }

  feaBendNow(f) { // the slabs bent by bend × f (the pulse eases f between 0 and 1), the frame carried along
    if (!this.feaCase) return;
    this.feaK = this.state.feaBend * f;
    for (const m of this.feaObjs) bend(m, this.feaK);
    this.feaCarry(this.feaK);
    this.render();
  }

  feaCarry(k) { // the parts not analysed follow the analysed one (fea_view.py says how far, at true scale)
    const c = this.feaCase, sh = c?.frame_shift, carry = c?.carry || {};
    for (const it of this.items || []) {
      if (!it.obj.visible || this.feaHidden.has(it)) continue;
      const part = it.kind === "heater" ? "heater" : this.itemPart.get(it);
      it.obj.position.copy(it.base);
      it.obj.matrixAutoUpdate = true;
      if (carry[part] != null) it.obj.position.z += carry[part] * k;            // rides on the deck (deck cases)
      if (!sh) continue;
      const dx = sh.vec[0] * k, dy = sh.vec[1] * k;
      if (part?.startsWith("leg plate")) {                                       // feet fixed, tops with the deck
        it.obj.updateMatrix(); it.obj.matrixAutoUpdate = false;
        it.obj.matrix.premultiply(new THREE.Matrix4().set(1, 0, dx / sh.z_full, 0, 0, 1, dy / sh.z_full, 0, 0, 0, 1, 0, 0, 0, 0, 1));
      } else { it.obj.position.x += dx; it.obj.position.y += dy; }               // the deck and all on it
    }
  }

  feaAnimate() {
    cancelAnimationFrame(this.feaRaf);
    if (!this.feaCase) return;
    if (!this.state.feaPulse) { this.feaBendNow(1); return; }
    const t0 = performance.now();
    const tick = (now) => {
      if (!this.feaCase || !this.state.feaPulse) return;
      this.feaBendNow(0.5 - 0.5 * Math.cos(((now - t0) / 1600) * Math.PI));   // load on, load off: 3.2 s
      this.feaRaf = requestAnimationFrame(tick);
    };
    this.feaRaf = requestAnimationFrame(tick);
  }

  play() { // run the assembly from the start (or stop it), about 1.3 s a step
    if (this.playing) { this.playing = false; return; }
    const n = this.steps.length;
    if (this.state.assembly >= n) { this.state.assembly = 0; this.place(); this.frameClose(); }
    this.playing = true;
    let last = performance.now();
    const tick = (now) => {
      if (!this.playing) return;
      this.state.assembly = Math.min(n, this.state.assembly + (now - last) / 1300); last = now;
      this.asmCtl.updateDisplay(); this.place();
      if (this.state.assembly < n) requestAnimationFrame(tick); else this.playing = false;
    };
    requestAnimationFrame(tick);
  }

  frameClose() { // a closer look at the frame (legs, deck, cheeks, wedges) for the assembly
    const box = new THREE.Box3();
    for (const it of this.items || []) if (it.kind === "frame" || it.kind === "wedge") box.expandByObject(it.obj);
    if (box.isEmpty()) return;
    const c = box.getCenter(new THREE.Vector3()), r = box.getSize(new THREE.Vector3()).length() / 2;
    const dist = r / Math.sin((this.camera.fov * Math.PI) / 360) * 0.85;
    this.camera.position.copy(c).add(new THREE.Vector3(0.6, -0.8, 0.75).normalize().multiplyScalar(dist));
    this.controls.target.copy(c); this.controls.update(); this.render();
  }

  frame() { // aim the camera at the whole assembly
    const box = new THREE.Box3().setFromObject(this.root);
    const c = box.getCenter(new THREE.Vector3()), r = box.getSize(new THREE.Vector3()).length() / 2;
    const dist = r / Math.sin((this.camera.fov * Math.PI) / 360) * 0.9;
    this.camera.position.copy(c).add(new THREE.Vector3(0.75, -1, 0.65).normalize().multiplyScalar(dist));
    this.controls.target.copy(c); this.controls.update(); this.render();
  }

  resize() {
    const r = this.c.getBoundingClientRect(); if (!r.width) return;
    this.renderer.setSize(r.width, r.height); this.camera.aspect = r.width / r.height;
    this.camera.updateProjectionMatrix(); this.render();
  }

  render() { this.renderer.render(this.scene, this.camera); }
}
