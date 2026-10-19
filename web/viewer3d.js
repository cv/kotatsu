// 3-D assembly preview (three.js). Frame is a draft until phase 2.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import GUI from "lil-gui";

const COL = { a: 0xead3a8, b: 0xd9b47c, key: 0x9c6232, panel: 0xe2c595, deck: 0xd6b88a, heater: 0x2b2b2b };

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
    grid.position.set(600, 400, 0); this.scene.add(grid);
    this.root = new THREE.Group(); this.scene.add(this.root);
    this.state = { option: null, explode: 0, showTop: true, showFrame: true, showHeater: true };
    new ResizeObserver(() => this.resize()).observe(container);
  }

  setData(data, onOption) {
    this.data = data;
    const names = data.top.options.map((o) => o.name);
    if (!names.includes(this.state.option)) this.state.option = data.top.selected;
    if (!this.gui) {
      this.gui = new GUI({ container: this.c, title: "View" });
      this.gui.domElement.style.position = "absolute"; this.gui.domElement.style.right = "8px"; this.gui.domElement.style.top = "8px";
      this.optCtl = this.gui.add(this.state, "option", names).name("top seam").onChange((v) => { this.build(); onOption && onOption(v); });
      this.gui.add(this.state, "explode", 0, 400, 1).onChange(() => this.place());
      this.gui.add(this.state, "showTop").name("top").onChange(() => this.place());
      this.gui.add(this.state, "showFrame").name("frame (draft)").onChange(() => this.place());
      this.gui.add(this.state, "showHeater").name("heater").onChange(() => this.place());
    } else {
      this.optCtl.options(names).setValue(this.state.option);
    }
    this.build();
  }

  setOption(name) { if (this.state.option !== name) { this.state.option = name; this.optCtl?.setValue(name); } }

  build() {
    const d = this.data; if (!d) return;
    this.root.clear();
    const F = d.frame, t = d.top.thickness, opt = d.top.options.find((o) => o.name === this.state.option);
    this.items = [];
    const ztop = F.height + F.futon_gap;
    const nb = opt.boards.length;
    opt.boards.forEach((h, i) => {
      const m = slab(h, t, i % 2 ? COL.b : COL.a); m.position.z = ztop;
      const sx = nb > 1 ? (2 * i / (nb - 1) - 1) : 0; // -1 .. +1, left -> right
      this.items.push({ obj: m, kind: "top", dir: new THREE.Vector3(sx, 0, sx === 0 ? 0.4 : 0), base: m.position.clone() });
    });
    opt.keys.forEach((k) => {
      const m = slab(k, t, COL.key); m.position.z = ztop;
      this.items.push({ obj: m, kind: "key", dir: new THREE.Vector3(0, 0, 1.6), base: m.position.clone() });
    });
    const cx = d.top.length / 2, cy = d.top.width / 2;
    for (const p of F.panels) {
      const m = slab(p.shape, t, COL.panel);
      m.applyMatrix4(BASIS[p.axis]); m.position.set(...p.origin);
      const c = new THREE.Vector3(p.origin[0] - cx, p.origin[1] - cy, 0);
      const dir = p.axis === "x" ? new THREE.Vector3(0, Math.sign(c.y), 0) : new THREE.Vector3(Math.sign(c.x), 0, 0);
      this.items.push({ obj: m, kind: "frame", dir, base: m.position.clone() });
    }
    const deck = slab(F.deck.shape, t, COL.deck); deck.position.set(...F.deck.origin);
    this.items.push({ obj: deck, kind: "frame", dir: new THREE.Vector3(0, 0, 0.3), base: deck.position.clone() });
    const hz = F.heater;
    const heater = new THREE.Mesh(new THREE.BoxGeometry(...hz.size), new THREE.MeshStandardMaterial({ color: COL.heater, roughness: 0.5 }));
    heater.position.set(...hz.center);
    this.items.push({ obj: heater, kind: "heater", dir: new THREE.Vector3(0, 0, -0.6), base: heater.position.clone() });
    for (const it of this.items) this.root.add(it.obj);
    if (!this.framed) { this.framed = true; this.frame(); }
    this.place();
  }

  place() {
    const e = this.state.explode, S = this.state;
    for (const it of this.items || []) {
      const vis = { top: S.showTop, key: S.showTop, frame: S.showFrame, heater: S.showHeater }[it.kind];
      it.obj.visible = vis;
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
