# AGENTS.md — Kotatsu project

## Goal
Design a **120 × 80 cm kotatsu** (low Japanese heated table) built only from **flat-cut birch plywood**
ordered online from **uMake.ca** (or a similar upload-a-file service). The parts must ship to the
owner's door, and ordering must not involve a phone call or an email.

Deliverables:
1. Parametric source (Python) that generates every part from one parameter file.
2. Upload-ready cut files (DXF in mm, plus SVG) for the top, frame/aprons, legs, heater mount, and
   any joinery pieces (wedges, keys).
3. Previews (PNG), a cut list/BOM, an estimated weight and shipping-box check, and assembly instructions.

## Hard constraints (never violate)
- **No glue, nails, screws, bolts, dowels, inserts or other hardware.** All joints are plywood-only:
  cross-laps (half-laps), through-tenons with wedges or keys (tusk tenons), tabs and slots.
  - *Only exception:* the kotatsu heater unit, plus the screws that come with it, to mount it.
- **Online-only ordering.** Every part must be quotable in the uMake instant-quote app
  (app.umake.ca). Do not design anything that needs a manual quote, freight/LTL shipping or a pallet:
  - **each part ≤ 1219 mm (48")** on its longest side, so every box is a standard parcel (the top is split into 3 boards); never > 1500 mm (60");
  - each box ≤ 50 lb (22.7 kg) if possible, and never > 150 lb;
  - no secondary operations (bending, finishing, assembly) ordered from the vendor.
- **Overall size:** top is 1200 × 800 mm.
- **Electrical safety:** the heater must be rated for the local mains (Canada: 120 V / 60 Hz, cUL/CSA/ETL).
  Do not plan around a 100 V Japanese heater with no transformer. Follow the heater maker's
  clearances and mounting instructions; they override this design.

## Process facts (see docs/research.md for sources)
- uMake's CO₂ laser cuts plywood **≤ 6 mm** only. Structural 18 mm birch must be **CNC-routed**
  (same app, same ordering flow). The laser is fine for thin parts or engraving.
- CNC router: inside corners get a radius of half the bit diameter (1/8" or 1/4" bits), so every
  slot/mortise that takes a square edge **needs dogbones**. Allow ≥ 5 mm between parts and a 20 mm
  sheet margin. No feature smaller than the material thickness. Use closed outlines only, with no
  duplicate or overlapping lines.
- The vendor leaves holding tabs (~4.8 mm wide, half thickness deep); sand them off.
- Baltic birch thickness varies (18 mm nominal: +0.85 / −1.05 mm). Joints must **tolerate the
  thickness range**: use wedges, keys, or crush ribs, not exact-thickness press fits.
- Birch sheets in stock: 48×96", 60×60", 60×120".

## Dos
- Keep **one source of truth**: every dimension lives in `params.toml`, and nothing is hard-coded
  in geometry code.
- Work in **millimetres**. Set DXF `$INSUNITS = 4` (mm). Put cut lines and engrave/pocket lines on
  separate layers and colours.
- Re-generate outputs with one command (`make all`) and check them with tests (`make test`):
  closed polygons, no self-intersection, part fits the sheet, slot width ≥ max stock thickness
  + clearance, dogbones present, weight and box limits met.
- Look at the PNG previews (viewImage) after geometry changes.
- **Make small, focused git commits** with clear messages (one logical change each).
- Record decisions and open questions in `PLAN.md`, and vendor facts with source URLs in
  `docs/research.md`.
- Mark anything unverified (heater dimensions, live prices, actual stock thickness) as **TODO-verify**.

## Don'ts
- Don't add hardware, glue or fasteners to "fix" a joint. Redesign the joint instead.
- Don't assume the laser can cut 18 mm plywood.
- Don't design parts > 60" or orders that need freight. That would force contact with staff.
- Don't commit generated junk such as caches or virtualenvs. Commit `out/` cut files only when
  they are a release candidate (tagged).
- Don't hand-edit DXF/SVG outputs. Change the parameters or the generator.
- Don't guess the heater's mounting geometry. The chosen unit is in docs/heater.md; freeze `[heater]` only after measuring the real unit, and never send plywood for cutting before that.
- Don't imitate Indigenous designs (Northwest Coast formline, crests, Salish basketry patterns). Use them
  only if they come from, or are licensed by, an Indigenous artist (see docs/motifs.md). Nature motifs are fine.

## Tooling
- **Python ≥ 3.11 via `uv`** (the system python is 3.9; don't use it).
- `ezdxf`: writes DXF files (R2010, mm).
- `shapely`: 2-D geometry (booleans, dogbones, overlap/clearance checks, areas for weights).
- `matplotlib`: PNG/SVG previews of parts, sheet layouts and a simple assembly view.
- `pytest`: geometric and constraint checks.
- `tomllib` (stdlib) reads `params.toml`.
- Optional later: `build123d` for a 3-D assembly/interference check and STEP export.
- `make` targets: `all`, `dxf`, `test`, `site`, `dev`, `clean`.
- **Project site** (`make dev` → http://127.0.0.1:8765, rebuilds on change and the page live-reloads):
  - `kotatsu/site.py` exports `out/site/data.json` (geometry, stats, params, test results, docs). The page
    in `web/` is hand-written static HTML/JS, with no build step and no npm.
  - The JS libraries are pinned versions on jsdelivr, loaded via an importmap: `three` (3-D +
    OrbitControls), `lil-gui` (controls) and `marked` (docs).
  - 2-D pan/zoom is a small custom viewBox controller in `web/viewer2d.js`. It stays crisp vector at
    any zoom and reads cursor positions in mm.
  - Add new visualisations by extending `data.json` in Python. Never compute geometry in JS; JS only draws it.

## Layout
```
params.toml          # all dimensions & tolerances
kotatsu/             # generator package (parts, joints, export, checks)
tests/               # pytest constraint checks
out/                 # generated DXF/SVG/PNG (gitignored except tagged releases)
docs/research.md     # vendor + heater research, with sources
PLAN.md              # design plan, decisions, open questions, phases
```
