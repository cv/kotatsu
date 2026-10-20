import { marked } from "marked";
import { el, PanZoom, niceLength, polyD } from "./viewer2d.js";

const $ = (s) => document.querySelector(s);
const state = { data: null, tab: "overview", futon: null, fsize: null, fpz: null, doc: "PLAN.md", v3d: null, part: null, ppz: null, sheet: null, spz: null, tables: null, ptable: null };

// ---------- tabs ----------
function showTab(tab) {
  state.tab = tab;
  document.querySelectorAll(".tab").forEach((s) => s.classList.toggle("active", s.id === "tab-" + tab));
  document.querySelectorAll("nav a").forEach((a) => a.classList.toggle("active", a.dataset.tab === tab));
  if (tab === "3d") ensure3d();
  if (tab === "sheets" && state.spz && !state.spzFitted) { state.spzFitted = true; requestAnimationFrame(() => state.spz.fit(state.spz.home)); }
  if (tab === "futon" && state.fpz && !state.fpzFitted) { state.fpzFitted = true; requestAnimationFrame(() => state.fpz.fit(state.fpz.home)); }
  if (tab === "frame" && state.ppz && !state.ppzFitted) { state.ppzFitted = true; requestAnimationFrame(() => state.ppz.fit(state.ppz.home)); }
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
}

// ---------- futon & rug ----------
const FIT = { ideal: ["fits Ø90", "ok"], generous: ["roomy", ""], small: ["small for Ø90", "warn"] };
const cad = (n) => "$" + n.toLocaleString("en-CA");

function renderFutonList(d) {
  const R = d.room, F = R.futons;
  const list = $("#futon-list"); list.replaceChildren();
  const head = document.createElement("div"); head.className = "stats";
  head.innerHTML = `${F.items.length} round futons · checked ${F.checked} · ¥→CAD at ${F.jpy_cad} · totals exclude duty/GST/PST`;
  list.appendChild(head);
  const items = [...F.items].sort((x, y) => (x.fit === "ideal" ? 0 : x.fit === "generous" ? 1 : 2) - (y.fit === "ideal" ? 0 : y.fit === "generous" ? 1 : 2) || /SOLD/.test(x.status) - /SOLD/.test(y.status) || x.total_cad - y.total_cad);
  for (const f of items) {
    const div = document.createElement("div");
    div.className = "opt futon" + (f.url === state.futon ? " active" : "");
    const [fitTxt, fitCls] = FIT[f.fit] || [f.fit, ""];
    const sold = /SOLD/.test(f.status);
    const price = f.currency === "JPY" ? `¥${f.price.toLocaleString()}${f.ship ? ` + ¥${f.ship.toLocaleString()} ship` : ""} ≈ <b>${cad(f.total_cad)}</b>` : `<b>${cad(f.price)}</b> CAD${f.ship ? ` + ${cad(f.ship)}` : " + shipping"}`;
    div.innerHTML = `<img class="fimg" src="${f.img}" alt="" loading="lazy" referrerpolicy="no-referrer">
      <div class="name">${f.size_cm} cm <span class="badge ${fitCls}">${fitTxt}</span>${sold ? '<span class="badge warn">sold out</span>' : ""}</div>
      <div class="label">${f.name}</div>
      <div class="stats">${price}<br>${f.store}${f.rating ? " · " + f.rating : ""}<br>${f.status}<br><i>${f.notes}</i><br>
      floor footprint ≈ Ø ${(f.footprint_d / 1000).toFixed(2)} m · rug ring ≈ ${Math.round(f.rug_ring / 10)} cm · <a href="${f.url}" target="_blank" rel="noopener">open store ↗</a></div>`;
    div.onclick = (e) => { if (e.target.tagName === "A") return; state.futon = f.url; state.fsize = f.size_cm * 10; renderFutonList(d); renderFutonPlan(d); };
    list.appendChild(div);
  }
}

function footprint(R, fd) { return Math.max(R.top_d, fd - 2 * 0.7 * R.height); }

function renderFutonPlan(d, refit = false) {
  const R = d.room, fd = state.fsize || R.futon_d, fp = footprint(R, fd);
  $("#futon-btns").replaceChildren(btnGroup([1850, 1900, 2050, 2250, 2450].map((x) => [x, `${x / 10} cm`]), fd, (x) => { state.fsize = x; state.futon = null; renderFutonList(d); renderFutonPlan(d); }));
  $("#futon-summary").textContent = `futon Ø ${fd / 10} cm → floor ≈ Ø ${(fp / 1000).toFixed(2)} m · rug ring ≈ ${Math.round((R.rug_d - fp) / 20)} cm · top Ø ${R.top_d / 10} cm · ratios ${(R.rug_d / fp).toFixed(2)} : ${(fp / R.top_d).toFixed(2)}`;
  const host = $("#fviewer");
  let svg = host.querySelector("svg");
  const r0 = R.rug_d / 2 + 80, home = { x: -r0, y: -r0, w: 2 * r0, h: 2 * r0 };
  if (!svg) {
    svg = el("svg", { preserveAspectRatio: "xMidYMid meet" }, host);
    const bar = document.createElement("div"); bar.className = "scalebar"; host.appendChild(bar);
    state.fpz = new PanZoom(svg, home, (pz) => { const k = pz.scale(), L = niceLength(120 / k); bar.innerHTML = `<div style="width:${L * k}px"></div>${L} mm`; });
    refit = true;
  }
  state.fpz.home = home;
  svg.replaceChildren();
  el("circle", { r: R.rug_d / 2, class: "rug" }, svg);
  el("circle", { r: R.rug_d / 2 - 60, class: "rug-border" }, svg);
  el("circle", { r: fp / 2, class: "futon-floor" }, svg);
  el("circle", { r: fd / 2, class: "futon-flat" }, svg);
  if ($("#chk-fzab").checked) {
    const [zw, zd] = R.zabuton, rc = R.top_d / 2 + 30 + zd / 2;   // cushion's front edge just past the top
    for (const ang of [0, 90, 180, 270]) {
      const g = el("g", { transform: `rotate(${ang}) translate(0 ${rc})` }, svg);
      el("rect", { x: -zw / 2, y: -zd / 2, width: zw, height: zd, rx: 40, class: "zabuton" }, g);
    }
  }
  const h = R.frame / 2, c = h - R.ear;     // "#" plan: panels cross `ear` in from their ends
  for (const q of [-c, c]) {
    el("line", { x1: -h, y1: q, x2: h, y2: q, class: "frame-ghost" }, svg);
    el("line", { x1: q, y1: -h, x2: q, y2: h, class: "frame-ghost" }, svg);
  }
  el("circle", { r: R.top_d / 2, class: "top-disc" }, svg);
  if (R.knees) {                              // owner's cross-legged knee zone at each side
    const K = R.knees, y0 = R.top_d / 2 - K.reach;
    for (const ang of [0, 90, 180, 270]) {
      const g = el("g", { transform: `rotate(${ang})` }, svg);
      el("rect", { x: -K.knee_w / 2, y: y0, width: K.knee_w, height: K.reach + 260, class: "knee-zone" }, g);
    }
    const t = el("text", { x: 0, y: y0 + 60, class: "plan-label knee-label" }, svg);
    t.textContent = `knees 30″ × 12.5″: up to ${Math.round(K.reach)} mm under the edge`;
  }
  const lab = (txt, y) => { const t = el("text", { x: 0, y, class: "plan-label" }, svg); t.textContent = txt; };
  lab(`rug Ø ${R.rug_d / 10} cm`, -R.rug_d / 2 + 40);
  lab(`futon on the floor ≈ Ø ${Math.round(fp / 10)} cm`, -fp / 2 + 45);
  lab(`top Ø ${R.top_d / 10} cm`, 15);
  if (refit || !state.fpzFitted) requestAnimationFrame(() => requestAnimationFrame(() => state.fpz.fit(home)));
}

// ---------- frame parts ----------
const partFlip = (p) => p.bounds[3];            // svg y = top - v
function partSvg(p, pad = 8) {
  const [x0, y0, x1, y1] = p.bounds;
  const svg = el("svg", { viewBox: `${x0 - pad} ${-pad} ${x1 - x0 + 2 * pad} ${y1 - y0 + 2 * pad}` });
  el("path", { d: polyD(p.shape, partFlip(p)), class: "part board0" }, svg);
  return svg;
}

function curTable(d) {
  if (!d.tables.some((t) => t.name === state.ptable)) state.ptable = d.tables[0].name;
  return d.tables.find((t) => t.name === state.ptable);
}

function renderPartList(d) {
  const T = curTable(d), F = T.frame;
  if (!F.parts.some((p) => p.name === state.part)) state.part = F.parts[0].name;
  const list = $("#part-list"); list.replaceChildren();
  if (d.tables.length > 1) list.appendChild(btnGroup(d.tables.map((t) => [t.name, t.label]), state.ptable, (n) => { state.ptable = n; state.part = null; renderPartList(d); renderPartViewer(d, true); }));
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
  const p = curTable(d).frame.parts.find((x) => x.name === state.part);
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
      const q = state.ppz.toSvg(e.clientX, e.clientY), cur = curTable(state.data).frame.parts.find((x) => x.name === state.part);
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

// ---------- cut sheets ----------
function btnGroup(items, current, onPick) {
  const span = document.createElement("span"); span.className = "btn-group";
  for (const [key, label] of items) {
    const b = document.createElement("button"); b.textContent = label;
    b.className = key === current ? "on" : ""; b.onclick = () => onPick(key);
    span.appendChild(b);
  }
  return span;
}

function renderSheets(d, refit = false) {
  const S = d.sheets, tablesKeys = Object.keys(S);
  if (!tablesKeys.includes(state.tables)) state.tables = tablesKeys[0];
  const opts = S[state.tables], names = Object.keys(opts);   // sorted by plywood, least first
  if (!names.includes(state.sheet)) state.sheet = names[0];
  $("#sheet-btns").replaceChildren(
    btnGroup(tablesKeys.map((k) => [k, k === "1" ? "1 set" : `${k} sets`]), state.tables, (k) => { state.tables = k; state.sheet = null; renderSheets(d, true); }),
    btnGroup(names.map((n) => [n, `${n} · ${opts[n].material_m2} m²`]), state.sheet, (n) => { state.sheet = n; renderSheets(d, true); }));
  const N = opts[state.sheet], k = +state.tables;
  $("#sheet-summary").textContent = `${N.sizes.join(" + ")} · ${N.material_m2} m²${k > 1 ? ` (${(N.material_m2 / k).toFixed(2)} m² per set)` : ""} · parts use ${Math.round(N.util * 100)}% · gap ${N.gap} mm`;
  const host = $("#sviewer");
  let svg = host.querySelector("svg");
  const offs = []; let y = 0;
  for (const sh of N.sheets) { offs.push(y); y += sh.h + 160; }
  const maxW = Math.max(...N.sheets.map((sh) => sh.w));
  const home = { x: -60, y: -120, w: maxW + 120, h: y + 60 };
  if (!svg) {
    svg = el("svg", { preserveAspectRatio: "xMidYMid meet" }, host);
    const bar = document.createElement("div"); bar.className = "scalebar"; host.appendChild(bar);
    state.spz = new PanZoom(svg, home, (pz) => {
      const kk = pz.scale(), L = niceLength(120 / kk);
      bar.innerHTML = `<div style="width:${L * kk}px"></div>${L} mm`;
    });
    svg.addEventListener("pointermove", (e) => {
      const q = state.spz.toSvg(e.clientX, e.clientY);
      $("#sreadout").textContent = `x ${q.x.toFixed(0)} mm`;
    });
    refit = true;
  }
  state.spz.home = home;
  svg.replaceChildren();
  N.sheets.forEach((sh, i) => {
    const g = el("g", { transform: `translate(0 ${offs[i]})` }, svg);
    el("rect", { x: 0, y: 0, width: sh.w, height: sh.h, class: "sheet" }, g);
    el("rect", { x: N.margin, y: N.margin, width: sh.w - 2 * N.margin, height: sh.h - 2 * N.margin, class: "sheet-margin" }, g);
    const lab = el("text", { x: 0, y: -24, class: "sheet-label" }, g);
    lab.textContent = `sheet ${i + 1} of ${N.count} · ${N.sizes[i].replace("in", '"').replace("x", "×")}`;
    for (const p of sh.parts) {
      const path = el("path", { d: polyD(p.shape, sh.h), class: `part grp-${p.group}` }, g);
      const t = el("title", {}, path); t.textContent = `${p.name} (rotated ${p.angle}°)`;
      const xs = p.shape.ext.map((q) => q[0]), ys = p.shape.ext.map((q) => q[1]);
      const w = Math.max(...xs) - Math.min(...xs), h = Math.max(...ys) - Math.min(...ys);
      if (w > 200 && h > 100) {
        const tx = el("text", { x: Math.min(...xs) + 14, y: sh.h - Math.max(...ys) + 30, class: "part-label" }, g);
        tx.textContent = p.name;
      }
    }
  });
  if (refit) requestAnimationFrame(() => state.spz.fit(home));
}

// ---------- 3-D (lazy: only load three.js when the tab is opened) ----------
async function ensure3d() {
  if (state.v3d || !state.data) return;
  const { Viewer3D } = await import("./viewer3d.js");
  state.v3d = new Viewer3D($("#viewer3d"));
  state.v3d.setData(state.data);
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
  $("#meta").innerHTML = `<span class="dot"></span>built ${d.generated} · ${d.git}`;
  renderOverview(d); renderDocs(d); renderFutonList(d); renderFutonPlan(d);
  renderPartList(d); renderPartViewer(d); renderSheets(d);
  state.v3d?.setData(d);
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
for (const id of ["#chk-pgrid", "#chk-pbit"]) $(id).onchange = () => renderPartViewer(state.data);
$("#btn-pfit").onclick = () => state.ppz.fit(state.ppz.home);
$("#btn-ffit").onclick = () => state.fpz.fit(state.fpz.home);
$("#chk-fzab").onchange = () => renderFutonPlan(state.data);
$("#btn-sfit").onclick = () => state.spz.fit(state.spz.home);
addEventListener("keydown", (e) => {
  if (state.tab === "frame" && (e.key === "f" || e.key === "F")) state.ppz.fit(state.ppz.home);
});

window.kotatsu = state; // debug handle (console / screenshots)
renderAll(await load());
showTab(location.hash.slice(1) || "overview");
poll();
