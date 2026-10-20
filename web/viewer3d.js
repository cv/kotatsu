// 3-D assembly preview (three.js): top boards + every frame part at its real placement, plus the room
// layers (rug, draped futon, floor pillows).
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import GUI from "lil-gui";

const COL = { a: 0xead3a8, b: 0xd9b47c, key: 0x9c6232, panel: 0xe2c595, deck: 0xd6b88a, heater: 0x2b2b2b,
  rug: 0xcdbfa8, futon: 0x56637f, seat: 0xb4643f };

function shapeFrom(p) {
  const s = new THREE.Shape(p.ext.map(([x, y]) => new THREE.Vector2(x, y)));
  for (const h of p.holes) s.holes.push(new THREE.Path(h.map(([x, y]) => new THREE.Vector2(x, y))));
  return s;
}

function slab(p, t, color) {
  const geo = new THREE.ExtrudeGeometry(shapeFrom(p), { depth: t, bevelEnabled: false, curveSegments: 4 });
  const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.85, side: THREE.DoubleSide });
  const mesh = new THREE.Mesh(geo, mat);
  const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geo, 25),
    new THREE.LineBasicMaterial({ color: 0x3b2f25, transparent: true, opacity: 0.55 }));
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
    container.appendChild(this.renderer.domElement);
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0xfdfbf8);
    this.camera = new THREE.PerspectiveCamera(35, 1, 10, 20000);
    this.camera.up.set(0, 0, 1);
    this.camera.position.set(2100, -1500, 1400);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.target.set(600, 400, 220);
    this.controls.addEventListener("change", () => this.render());
    this.scene.add(new THREE.HemisphereLight(0xffffff, 0x8a7a66, 2.2));
    const sun = new THREE.DirectionalLight(0xffffff, 1.6); sun.position.set(800, -1200, 2000); this.scene.add(sun);
    const grid = new THREE.GridHelper(3000, 30, 0xcfc6b8, 0xe7e0d6); grid.rotation.x = Math.PI / 2;
    grid.position.set(600, 400, -12); this.scene.add(grid); // just under the rug
    this.grid = grid;
    this.root = new THREE.Group(); this.scene.add(this.root);
    this.state = { table: null, explode: 0, showTop: true, showFrame: true, showHeater: true,
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
      this.addTable(T, dx, t);
      dx += T.top.length + 400;
    }
    for (const it of this.items) this.root.add(it.obj);
    if (!this.framed) { this.framed = true; this.frame(); }
    this.place();
  }

  addTable(T, dx, t) {
    const F = T.frame;
    const off = new THREE.Vector3(dx, 0, 0);
    const opt = { boards: T.top.boards, keys: [] };
    const ztop = F.height + F.futon_gap;
    const nb = opt.boards.length;
    const push = (obj, kind, dir) => { obj.position.add(off); this.items.push({ obj, kind, dir, base: obj.position.clone() }); };
    opt.boards.forEach((h, i) => {
      const m = slab(h, t, i % 2 ? COL.b : COL.a); m.position.z = ztop;
      const sx = nb > 1 ? (2 * i / (nb - 1) - 1) : 0; // -1 .. +1, left -> right
      push(m, "top", new THREE.Vector3(sx, 0, sx === 0 ? 0.4 : 0));
    });
    opt.keys.forEach((k) => { const m = slab(k, t, COL.key); m.position.z = ztop; push(m, "key", new THREE.Vector3(0, 0, 1.6)); });
    const byName = Object.fromEntries(F.parts.map((p) => [p.name, p]));
    const colour = { frame: COL.panel, deck: COL.deck, cheek: COL.deck, wedge: COL.key };
    for (const pl of F.placed) {
      let shape = byName[pl.part].shape;
      if (pl.mirror) shape = { ext: shape.ext.map(([u, v]) => [-u, v]).reverse(), holes: shape.holes.map((h) => h.map(([u, v]) => [-u, v]).reverse()) };
      const m = slab(shape, t, colour[pl.kind] ?? COL.panel);
      if (pl.axis !== "z") m.applyMatrix4(BASIS[pl.axis]);
      m.position.set(...pl.origin);
      push(m, pl.kind === "wedge" ? "wedge" : "frame", new THREE.Vector3(...pl.explode));
    }
    const hz = F.heater;
    const heater = new THREE.Mesh(new THREE.BoxGeometry(...hz.size), new THREE.MeshStandardMaterial({ color: COL.heater, roughness: 0.5 }));
    heater.position.set(...hz.center);
    push(heater, "heater", new THREE.Vector3(0, 0, -0.6));
    if (T.room3d) this.addRoom(T.room3d, push);
  }

  addRoom(R, push) { // rug, draped futon and floor pillows; geometry comes from Python (room.room3d)
    const still = new THREE.Vector3();
    const rug = new THREE.Mesh(new THREE.CylinderGeometry(R.rug.d / 2, R.rug.d / 2, R.rug.t, 96),
      new THREE.MeshStandardMaterial({ color: COL.rug, roughness: 1 }));
    rug.rotation.x = Math.PI / 2; rug.position.set(R.rug.center[0], R.rug.center[1], -R.rug.t / 2);
    push(rug, "rug", still);
    const n = R.futon.n, geo = new THREE.BufferGeometry(), idx = [];
    geo.setAttribute("position", new THREE.Float32BufferAttribute(R.futon.pts, 3));
    for (let j = 0; j < n - 1; j++) for (let i = 0; i < n - 1; i++) {
      const a = j * n + i, b = a + 1, c = a + n, d = c + 1;
      idx.push(a, b, d, a, d, c);
    }
    geo.setIndex(idx); geo.computeVertexNormals();
    const futon = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: COL.futon, roughness: 0.95, side: THREE.DoubleSide }));
    futon.renderOrder = 2; // drawn after the opaque parts, so it can fade over them
    push(futon, "futon", still);
    const seatMat = new THREE.MeshStandardMaterial({ color: COL.seat, roughness: 0.9 });
    for (const st of R.seats) {
      const [w, d, h] = st.size;
      const m = new THREE.Mesh(new RoundedBoxGeometry(w, d, h, 4, Math.min(35, h / 2.2)), seatMat);
      m.position.set(...st.center);
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
