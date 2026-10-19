import { marked } from "marked";
import { el, drawOption, drawFootprint, drawGrid, staticSvg, jointBox, PanZoom, niceLength, polyD } from "./viewer2d.js";

const $ = (s) => document.querySelector(s);
const state = { data: null, option: null, tab: "overview", doc: "PLAN.md", compare: false, pz: null, v3d: null, joint: null, part: null, ppz: null };

// ---------- tabs ----------
function showTab(tab) {
  state.tab = tab;
  document.querySelectorAll(".tab").forEach((s) => s.classList.toggle("active", s.id === "tab-" + tab));
  document.querySelectorAll("nav a").forEach((a) => a.classList.toggle("active", a.dataset.tab === tab));
  if (tab === "3d") ensure3d();
  if (tab === "frame" && state.ppz && !state.ppzFitted) { state.ppzFitted = true; requestAnimationFrame(() => state.ppz.fit(state.ppz.home)); }
  if (tab === "seams" && state.pz && !state.pzFitted) { state.pzFitted = true; requestAnimationFrame(() => state.pz.fit(state.pz.home)); }
}
addEventListener("hashchange", () => showTab(location.hash.slice(1) || "overview"));

// ---------- overview ----------
function renderOverview(d) {
  $("#facts").replaceChildren(...d.project.facts.flatMap(([k, v]) => {
    const dt = document.createElement("dt"); dt.textContent = k;
    const dd = document.createElement("dd"); dd.textContent = v; return [dt, dd];
  }));
  const t = d.tests;
  $("#tests").innerHTML = t ? `<div class="${t.ok ? "ok" : "bad"}">${t.ok ? "✔" : "✘"} ${t.summary}</div>` +
    (t.failures.length ? "<pre>" + t.failures.join("\n") + "</pre>" : "") : "tests skipped";
  const sel = d.top.options.find((o) => o.selected);
  $("#sel-name").textContent = sel ? `${sel.name} — ${sel.label}` : "";
  $("#sel-thumb").replaceChildren(sel ? staticSvg(sel, d.top) : "");
}

// ---------- seam options ----------
function statLine(o) {
  const s = o.stats;
  return `${s.pieces} pcs${s.loose ? ` (${s.loose} loose)` : ""} · boards ${s.board_dims.map((x) => x.join("×")).join(", ")} mm · cut ${s.cut_m} m (+${s.extra_cut_m}) · ${s.weight_kg} kg`;
}

function renderOptionList(d) {
  const list = $("#option-list"); list.replaceChildren();
  for (const o of d.top.options) {
    const div = document.createElement("div");
    div.className = "opt" + (o.name === state.option ? " active" : "");
    div.innerHTML = `<div class="name">${o.name}${o.selected ? '<span class="badge">params</span>' : ""}${o.stats.loose ? '<span class="badge warn">loose keys</span>' : ""}${o.stats.cuttable ? "" : '<span class="badge warn">not cuttable</span>'}</div><div class="label">${o.label}</div>`;
    const th = document.createElement("div"); th.className = "thumb"; th.appendChild(staticSvg(o, d.top)); div.appendChild(th);
    const st = document.createElement("div"); st.className = "stats"; st.textContent = statLine(o); div.appendChild(st);
    div.onclick = () => selectOption(o.name);
    list.appendChild(div);
  }
}

function currentOpt() { return state.data.top.options.find((o) => o.name === state.option); }

function renderViewer(d) {
  const host = $("#viewer2d");
  let svg = host.querySelector("svg");
  const T = d.top;
  const home = { x: -40, y: -40, w: T.length + 80, h: T.width + 80 };
  if (!svg) {
    svg = el("svg", { preserveAspectRatio: "xMidYMid meet" }, host);
    const bar = document.createElement("div"); bar.className = "scalebar"; host.appendChild(bar);
    state.pz = new PanZoom(svg, home, (pz) => {
      const k = pz.scale(), L = niceLength(120 / k);
      bar.innerHTML = `<div style="width:${L * k}px"></div>${L} mm`;
    });
    requestAnimationFrame(() => state.pz.fit(home));
    const bit = () => svg.querySelector(".bit");
    svg.addEventListener("pointermove", (e) => {
      const p = state.pz.toSvg(e.clientX, e.clientY);
      $("#readout").textContent = `x ${p.x.toFixed(1)}  y ${(T.width - p.y).toFixed(1)} mm  ·  ${(state.pz.scale()).toFixed(2)} px/mm`;
      const b = bit(); if (b) { b.setAttribute("cx", p.x); b.setAttribute("cy", p.y); }
    });
  }
  state.pz.home = home;
  svg.replaceChildren();
  const o = currentOpt();
  drawOption(el("g", {}, svg), o, T);
  if ($("#chk-grid").checked) drawGrid(svg, T); // on top of parts, faint
  if ($("#chk-frame").checked) drawFootprint(svg, T);
  for (const j of o.joints) { const b = jointBox(T, j, 60, 45); el("rect", { ...b, width: b.w, height: b.h, class: "jointmark", rx: 6 }, svg); }
  if ($("#chk-bit").checked) el("circle", { r: d.params.cnc.bit_d / 2, cx: -100, cy: -100, class: "bit" }, svg);
  // joint buttons
  $("#joint-btns").replaceChildren(...o.joints.map((j, i) => {
    const b = document.createElement("button"); b.textContent = "J" + (i + 1); b.title = "zoom to joint " + (i + 1);
    b.onclick = () => zoomJoint(i); return b;
  }));
  renderCompare(d);
}

function zoomJoint(i) {
  const o = currentOpt(); if (!o.joints[i]) return;
  state.joint = i; state.pz.fit(jointBox(state.data.top, o.joints[i])); renderCompare(state.data);
}

function renderCompare(d) {
  const box = $("#compare");
  box.replaceChildren(...d.top.options.map((o) => {
    const cur = currentOpt(), refY = (state.joint != null && cur.joints[state.joint]) ? cur.joints[state.joint][1] : d.top.width / 2;
    const j = o.joints.reduce((best, q) => (Math.abs(q[1] - refY) < Math.abs(best[1] - refY) ? q : best), o.joints[0] || [d.top.length / 2, refY]);
    const b = state.compare === "whole" ? { x: -20, y: -20, w: d.top.length + 40, h: d.top.width + 40 } : jointBox(d.top, j, 150, 100);
    const cell = document.createElement("div"); cell.className = "cell";
    cell.innerHTML = `<div class="name">${o.name}</div>`;
    cell.title = o.label || o.name;
    cell.appendChild(staticSvg(o, d.top, `${b.x} ${b.y} ${b.w} ${b.h}`));
    cell.onclick = () => { selectOption(o.name); state.compare = false; toggleCompare(false); };
    return cell;
  }));
}

function toggleCompare(mode = "detail") {
  // mode: "detail" | "whole" | false; clicking the active mode again closes the grid
  state.compare = mode && state.compare === mode ? false : mode;
  $("#compare").classList.toggle("hidden", !state.compare);
  $("#viewer2d").classList.toggle("hidden", !!state.compare);
  $("#btn-compare").classList.toggle("on", state.compare === "detail");
  $("#btn-compare-whole").classList.toggle("on", state.compare === "whole");
  if (state.compare) renderCompare(state.data);
}

function selectOption(name) {
  state.option = name;
  sessionStorage.setItem("option", name);
  renderOptionList(state.data); renderViewer(state.data);
  state.v3d?.setOption(name);
}

// ---------- frame parts ----------
const partFlip = (p) => p.bounds[3];            // svg y = top - v
function partSvg(p, pad = 8) {
  const [x0, y0, x1, y1] = p.bounds;
  const svg = el("svg", { viewBox: `${x0 - pad} ${-pad} ${x1 - x0 + 2 * pad} ${y1 - y0 + 2 * pad}` });
  el("path", { d: polyD(p.shape, partFlip(p)), class: "part board0" }, svg);
  return svg;
}

function renderPartList(d) {
  const F = d.frame;
  if (!F.parts.some((p) => p.name === state.part)) state.part = F.parts[0].name;
  const list = $("#part-list"); list.replaceChildren();
  const head = document.createElement("div"); head.className = "stats";
  head.textContent = `${F.parts.reduce((n, p) => n + p.qty, 0)} pieces · frame ≈ ${F.total_kg} kg`;
  list.appendChild(head);
  for (const p of F.parts) {
    const div = document.createElement("div");
    div.className = "opt" + (p.name === state.part ? " active" : "");
    div.innerHTML = `<div class="name">${p.name} <span class="badge">×${p.qty}</span>${p.spares ? `<span class="badge warn">incl. ${p.spares} spare</span>` : ""}</div>`;
    const th = document.createElement("div"); th.className = "thumb"; th.appendChild(partSvg(p)); div.appendChild(th);
    const st = document.createElement("div"); st.className = "stats";
    st.textContent = `${p.size[0]} × ${p.size[1]} mm · ${p.kg} kg each · cut ${p.cut_m} m`;
    div.appendChild(st);
    div.onclick = () => { state.part = p.name; renderPartList(d); renderPartViewer(d, true); };
    list.appendChild(div);
  }
}

function renderPartViewer(d, refit = false) {
  const p = d.frame.parts.find((x) => x.name === state.part);
  const host = $("#pviewer");
  let svg = host.querySelector("svg");
  const [x0, y0, x1, y1] = p.bounds, top = partFlip(p);
  const home = { x: x0 - 30, y: -30, w: x1 - x0 + 60, h: y1 - y0 + 60 };
  if (!svg) {
    svg = el("svg", { preserveAspectRatio: "xMidYMid meet" }, host);
    const bar = document.createElement("div"); bar.className = "scalebar"; host.appendChild(bar);
    state.ppz = new PanZoom(svg, home, (pz) => {
      const k = pz.scale(), L = niceLength(120 / k);
      bar.innerHTML = `<div style="width:${L * k}px"></div>${L} mm`;
    });
    svg.addEventListener("pointermove", (e) => {
      const q = state.ppz.toSvg(e.clientX, e.clientY), cur = d.frame.parts.find((x) => x.name === state.part);
      $("#preadout").textContent = `u ${q.x.toFixed(1)}  v ${(partFlip(cur) - q.y).toFixed(1)} mm`;
      const b = svg.querySelector(".bit"); if (b) { b.setAttribute("cx", q.x); b.setAttribute("cy", q.y); }
    });
    refit = true;
  }
  state.ppz.home = home;
  svg.replaceChildren();
  if ($("#chk-pgrid").checked) {
    const g = el("g", { class: "grid" }, svg);
    for (let u = Math.floor(x0 / 50) * 50; u <= x1; u += 50) el("line", { x1: u, y1: -10, x2: u, y2: y1 - y0 + 10 }, g);
    for (let v = Math.floor(y0 / 50) * 50; v <= y1; v += 50) el("line", { x1: x0 - 10, y1: top - v, x2: x1 + 10, y2: top - v }, g);
  }
  el("path", { d: polyD(p.shape, top), class: "part board0" }, svg);
  if ($("#chk-pbit").checked) el("circle", { r: d.params.cnc.bit_d / 2, cx: -100, cy: -100, class: "bit" }, svg);
  if (refit) requestAnimationFrame(() => state.ppz.fit(home));
}

// ---------- 3-D (lazy: only load three.js when the tab is opened) ----------
async function ensure3d() {
  if (state.v3d || !state.data) return;
  const { Viewer3D } = await import("./viewer3d.js");
  state.v3d = new Viewer3D($("#viewer3d"));
  state.v3d.state.option = state.option;
  state.v3d.setData(state.data, (name) => selectOption(name));
}

// ---------- docs ----------
function renderDocs(d) {
  const names = Object.keys(d.docs);
  $("#doc-list").replaceChildren(...names.map((n) => {
    const a = document.createElement("a"); a.href = "#docs"; a.textContent = n;
    a.className = n === state.doc ? "active" : ""; a.onclick = () => { state.doc = n; renderDocs(d); };
    return a;
  }));
  $("#doc").innerHTML = marked.parse(d.docs[state.doc] || "");
}

// ---------- data + live reload ----------
function renderAll(d) {
  state.data = d;
  const names = d.top.options.map((o) => o.name);
  if (!names.includes(state.option)) state.option = sessionStorage.getItem("option");
  if (!names.includes(state.option)) state.option = d.top.selected;
  $("#meta").innerHTML = `<span class="dot"></span>built ${d.generated} · ${d.git}`;
  renderOverview(d); renderOptionList(d); renderViewer(d); renderDocs(d);
  renderPartList(d); renderPartViewer(d);
  state.v3d?.setData(d, (name) => selectOption(name));
}

async function load() {
  const r = await fetch("data.json", { cache: "no-store" });
  return r.json();
}

async function poll() {
  try {
    const d = await load();
    if (d.generated !== state.data?.generated) renderAll(d);
  } catch { /* server restarting */ }
  setTimeout(poll, 1500);
}

// ---------- wiring ----------
$("#btn-fit").onclick = () => state.pz.fit(state.pz.home);
$("#btn-compare").onclick = () => toggleCompare("detail");
$("#btn-compare-whole").onclick = () => toggleCompare("whole");
for (const id of ["#chk-frame", "#chk-grid", "#chk-bit"]) $(id).onchange = () => renderViewer(state.data);
for (const id of ["#chk-pgrid", "#chk-pbit"]) $(id).onchange = () => renderPartViewer(state.data);
$("#btn-pfit").onclick = () => state.ppz.fit(state.ppz.home);
addEventListener("keydown", (e) => {
  if (state.tab === "frame" && (e.key === "f" || e.key === "F")) state.ppz.fit(state.ppz.home);
  if (state.tab !== "seams" || e.target.tagName === "INPUT") return;
  const names = state.data.top.options.map((o) => o.name), i = names.indexOf(state.option);
  if (e.key === "ArrowRight" || e.key === "ArrowDown") { selectOption(names[(i + 1) % names.length]); e.preventDefault(); }
  if (e.key === "ArrowLeft" || e.key === "ArrowUp") { selectOption(names[(i - 1 + names.length) % names.length]); e.preventDefault(); }
  if (e.key === "f" || e.key === "F") state.pz.fit(state.pz.home);
  if (/^[1-9]$/.test(e.key)) zoomJoint(+e.key - 1);
});

window.kotatsu = state; // debug handle (console / screenshots)
renderAll(await load());
showTab(location.hash.slice(1) || "overview");
poll();
