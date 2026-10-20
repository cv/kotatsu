// 3-D assembly preview (three.js): top boards + every frame part at its real placement, plus the room
// layers (rug, draped futon, floor pillows).
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import GUI from "lil-gui";
import { birchFace, plyEdge, cotton, braidedRug } from "./textures.js";

const COL = { heater: 0x2b2b2b, futon: 0x56637f, seat: 0xb4643f, rugSide: 0xb9a888 };
// all parts are the same pale birch; a faint tint per kind keeps them apart in the exploded view
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
    container.appendChild(this.renderer.domElement);
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0xfdfbf8);
    this.camera = new THREE.PerspectiveCamera(35, 1, 10, 20000);
    this.camera.up.set(0, 0, 1);
    this.camera.position.set(2100, -1500, 1400);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.target.set(600, 400, 220);
    this.controls.addEventListener("change", () => this.render());
    this.scene.add(new THREE.HemisphereLight(0xffffff, 0x8a7a66, 1.9));
    const sun = new THREE.DirectionalLight(0xfff6ea, 2.1);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    Object.assign(sun.shadow.camera, { left: -1700, right: 1700, top: 1700, bottom: -1700, near: 100, far: 6000 });
    sun.shadow.bias = -0.0004; sun.shadow.normalBias = 1.5; sun.shadow.radius = 4;
    this.scene.add(sun, sun.target);
    this.sun = sun;
    const grid = new THREE.GridHelper(3000, 30, 0xcfc6b8, 0xe7e0d6); grid.rotation.x = Math.PI / 2;
    grid.position.set(600, 400, -12); this.scene.add(grid); // just under the rug
    this.grid = grid;
    this.root = new THREE.Group(); this.scene.add(this.root);
    this.state = { table: null, linked: false, explode: 0, showTop: true, showFrame: true, showHeater: true,
      showFuton: true, showRug: true, showSeats: true };
    new ResizeObserver(() => this.resize()).observe(container);
  }

  setData(data) {
    this.data = data;
    const tnames = data.tables.length > 1 ? [...data.tables.map((t) => t.name), "all"] : data.tables.map((t) => t.name);
    if (!tnames.includes(this.state.table)) this.state.table = tnames[0];
    if (!this.gui) {
      this.gui = new GUI({ container: this.c, title: "View" });
      this.gui.domElement.style.position = "absolute"; this.gui.domElement.style.right = "8px"; this.gui.domElement.style.top = "8px";
      if (tnames.length > 1) this.gui.add(this.state, "table", tnames).name("table").onChange(() => { this.framed = false; this.build(); });
      if (data.tables.some((t) => t.link)) this.gui.add(this.state, "linked").name("linked pair").onChange(() => { this.framed = false; this.build(); });
      this.gui.add(this.state, "explode", 0, 400, 1).onChange(() => this.place());
      this.gui.add(this.state, "showTop").name("top").onChange(() => this.place());
      this.gui.add(this.state, "showFrame").name("frame").onChange(() => this.place());
      this.gui.add(this.state, "showHeater").name("heater").onChange(() => this.place());
      this.gui.add(this.state, "showFuton").name("futon").onChange(() => this.place());
      this.gui.add(this.state, "showSeats").name("seats").onChange(() => this.place());
      this.gui.add(this.state, "showRug").name("rug").onChange(() => this.place());
    }
    this.build();
  }

  build() {
    const d = this.data; if (!d) return;
    this.root.clear();
    this.items = [];
    const t = d.thickness;
    const which = this.state.table === "all" ? d.tables : d.tables.filter((x) => x.name === this.state.table);
    let dx = 0;
    for (const T of which) {
      if (this.state.linked && T.link) { // two modules side by side, tops touching, one key between them
        this.addTable(T, dx, t, false);
        this.addTable(T, dx + T.link.pitch, t, false);
        this.addKey(T, dx, t);
        dx += T.link.pitch + T.top.length + 400;
        continue;
      }
      this.addTable(T, dx, t);
      dx += T.top.length + 400;
    }
    for (const it of this.items) this.root.add(it.obj);
    const c = new THREE.Box3().setFromObject(this.root).getCenter(new THREE.Vector3()); // aim the sun at the table
    this.sun.target.position.set(c.x, c.y, 0);
    this.sun.position.set(c.x + 800, c.y - 1200, 2600);
    if (!this.framed) { this.framed = true; this.frame(); }
    this.place();
  }

  addKey(T, dx, t) {
    const part = T.frame.parts.find((p) => p.name === T.link.key);
    for (const pl of T.link.placed) {
      const m = slab(part.shape, t, "wedge", "u");
      m.applyMatrix4(BASIS[pl.axis]);
      m.position.set(pl.origin[0] + dx, pl.origin[1], pl.origin[2]);
      this.items.push({ obj: m, kind: "wedge", dir: new THREE.Vector3(0, 0, 1.2), base: m.position.clone() });
    }
  }

  addTable(T, dx, t, room = true) {
    const F = T.frame;
    const off = new THREE.Vector3(dx, 0, 0);
    const opt = { boards: T.top.boards, keys: [] };
    const ztop = F.height + F.futon_gap;
    const nb = opt.boards.length;
    const push = (obj, kind, dir) => { obj.position.add(off); this.items.push({ obj, kind, dir, base: obj.position.clone() }); };
    opt.boards.forEach((h, i) => {
      const m = slab(h, t, "top", "u"); m.position.z = ztop;
      const sx = nb > 1 ? (2 * i / (nb - 1) - 1) : 0; // -1 .. +1, left -> right
      push(m, "top", new THREE.Vector3(sx, 0, sx === 0 ? 0.4 : 0));
    });
    opt.keys.forEach((k) => { const m = slab(k, t, "wedge"); m.position.z = ztop; push(m, "key", new THREE.Vector3(0, 0, 1.6)); });
    const byName = Object.fromEntries(F.parts.map((p) => [p.name, p]));
    for (const pl of F.placed) {
      const part = byName[pl.part];
      let shape = part.shape;
      if (pl.mirror) shape = { ext: shape.ext.map(([u, v]) => [-u, v]).reverse(), holes: shape.holes.map((h) => h.map(([u, v]) => [-u, v]).reverse()) };
      const m = slab(shape, t, pl.kind, part.grain || "u");
      if (pl.axis !== "z") m.applyMatrix4(BASIS[pl.axis]);
      m.position.set(...pl.origin);
      push(m, pl.kind === "wedge" ? "wedge" : "frame", new THREE.Vector3(...pl.explode));
    }
    const hz = F.heater;
    const heater = new THREE.Mesh(new THREE.BoxGeometry(...hz.size), new THREE.MeshStandardMaterial({ color: COL.heater, roughness: 0.5 }));
    heater.castShadow = true;
    heater.position.set(...hz.center);
    push(heater, "heater", new THREE.Vector3(0, 0, -0.6));
    if (T.room3d && room) this.addRoom(T.room3d, push);
  }

  addRoom(R, push) { // rug, draped futon and floor pillows; geometry comes from Python (room.room3d)
    const still = new THREE.Vector3();
    TEX.rug ??= braidedRug();
    TEX.cotton ??= cotton(3, false);
    TEX.quilt ??= cotton(4, true);
    const rugCap = new THREE.MeshStandardMaterial({ map: TEX.rug, roughness: 1 });
    const rug = new THREE.Mesh(new THREE.CylinderGeometry(R.rug.d / 2, R.rug.d / 2, R.rug.t, 128),
      [new THREE.MeshStandardMaterial({ color: COL.rugSide, roughness: 1 }), rugCap, rugCap]); // side, top, bottom
    rug.receiveShadow = true;
    rug.rotation.x = Math.PI / 2; rug.position.set(R.rug.center[0], R.rug.center[1], -R.rug.t / 2);
    push(rug, "rug", still);
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
    push(futon, "futon", still);
    const seatTex = TEX.cotton.clone(); seatTex.repeat.set(2, 2); seatTex.needsUpdate = true;
    const seatMat = new THREE.MeshStandardMaterial({ map: seatTex, color: COL.seat, roughness: 0.9 });
    for (const st of R.seats) {
      const [w, d, h] = st.size;
      const m = new THREE.Mesh(new RoundedBoxGeometry(w, d, h, 4, Math.min(35, h / 2.2)), seatMat);
      m.position.set(...st.center);
      m.castShadow = m.receiveShadow = true;
      push(m, "seat", still);
    }
  }

  place() {
    const e = this.state.explode, S = this.state;
    for (const it of this.items || []) {
      const vis = { top: S.showTop, key: S.showTop, frame: S.showFrame, wedge: S.showFrame, heater: S.showHeater,
        futon: S.showFuton, rug: S.showRug, seat: S.showSeats }[it.kind];
      it.obj.visible = vis;
      if (it.kind === "futon") { // fades out as the parts explode, so you can see them through it
        const m = it.obj.material, o = 1 - 0.9 * Math.min(1, e / 400);
        const fade = o < 0.999;
        if (m.transparent !== fade) { m.transparent = fade; m.depthWrite = !fade; m.needsUpdate = true; }
        m.opacity = o;
        it.obj.castShadow = o > 0.6; // a see-through futon shouldn't darken the frame inside it
      }
      const lift = it.kind === "top" ? new THREE.Vector3(0, 0, e * 0.8) : new THREE.Vector3();
      it.obj.position.copy(it.base).addScaledVector(it.dir, e * 0.5).add(lift);
    }
    this.render();
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
