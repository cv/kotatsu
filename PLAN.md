# Kotatsu plan

Status: **planning**. Every number below is a default in `params.toml` (to be created). Items marked
**TODO-verify** need data from the uMake app or the chosen heater.

## 1. Process & material decision
- **18 mm Baltic birch, CNC-routed** on uMake (app.umake.ca → CNC router → Birch plywood 18 mm / 3/4").
  The laser is limited to plywood ≤ 6 mm, which is too thin for a 1200 × 800 top or a glue-free
  frame (see docs/research.md).
- The same online flow, the same vendor and no contact with staff.
- Fallback vendor: SendCutSend (TODO-verify its wood options and Canadian shipping).

## 2. Design concept: "four slab sides + deck"
```
        TOP (loose tenban, 1200×800×18) ─ sits on futon, which is draped over the frame
   ┌──────────────────────────────────────────────┐
   │  ear┃                                    ┃ear │   frame footprint ≈ 1120 × 720
   │ ━━━━╋━━━━━━━━━ long side panel ━━━━━━━━━━╋━━━ │   (40 mm top overhang all round)
   │     ┃      ┌────── DECK ───────┐         ┃    │
   │short┃  ▭═══╡  (heater screwed  ╞═══▭     ┃short   ▭═ tusk tenon + wedge through
   │side ┃      │   to underside)   │         ┃side      the long aprons
   │     ┃      └───────────────────┘         ┃    │
   │ ━━━━╋━━━━━━━━━ long side panel ━━━━━━━━━━╋━━━ │
   └──────────────────────────────────────────────┘
```
**Side panels (×4).** Each side is one piece of plywood that forms the apron and both legs, with a
large cut-out with filleted corners:
```
 long side (1120 × 370)          slots open at TOP on long panels, at BOTTOM on short panels
 ┌──┬┬───────────────────────┬┬──┐   ← apron band ~110 mm deep
 │  ││  ╭─────────────────╮  ││  │
 │  └┘  │    leg opening   │  └┘  │   legs ~130 mm wide, including a ~40–50 mm "ear"
 │      │   ~860 × 260     │      │      outside the crossing
 └──────┘                  └──────┘
```
- **Corners = cross-laps (half-laps).** The long panels are slotted from the top and the short panels
  from the bottom, each to half the height. The panels cross ~40–50 mm from their ends, so every leg
  is a stiff "+" section with four feet. The joint locks both ways when lifted, and the panels can't
  pull apart sideways.
- **Deck (×1)**, about 500 × 650 (x × y) plus tenons. It is a horizontal plate between the long
  aprons, with its top ~25 mm below the apron top edge.
  - It carries the **heater**, which is screwed to its underside with the heater's own screws.
    That is the only hardware allowed.
  - **2 tusk tenons per long side** pass through mortises in the long aprons and are locked with
    **wedges** (×4, plus 2 spares).
  - It acts as a **shear diaphragm**, so the frame can't rack. The tenon *width* fits the mortise
    *length*. That is an in-plane, CNC-precise dimension (±0.4 mm), so the fit does **not** depend
    on the sheet-thickness variation (±1 mm). The wedges pull the aprons tight against the deck
    shoulders whatever the stock thickness.
- **Top (×1).** 1200 × 800 × 18, corners rounded. It is loose, as on a traditional kotatsu tenban.
  Optional: four shallow router **pockets** on the underside where the panel ears land, so the top
  stays located in summer without the futon (TODO decide, since pockets may add cost).
- **Heights (defaults).** Frame 370 + top 18 + futon ≈ **390–400 mm** (standard floor kotatsu).
  With a ~100 mm heater hang, the heater bottom sits ≈ 225 mm above the floor (TODO-verify against
  the heater's clearance spec).

### Thickness-tolerance strategy
| Joint | Dimension controlled by | Strategy |
|---|---|---|
| Cross-lap slot width | stock thickness (17.0–18.9) | slot = t_max + 0.3 mm. Optional **crush ribs** (~0.4 mm bumps) for a snug fit. Slop here is harmless because the deck stops racking |
| Deck tenon width ↔ mortise length | CNC in-plane cut | tight, +0.2 mm |
| Mortise height ↔ deck thickness | stock thickness | t_max + 0.5 mm. The wedges take up the play |
| Wedge hole in tenon | in-plane (taper) + stock (wedge thickness) | 1:8 taper; hole set 2 mm inside the apron face so the wedge always bears on the apron |
| All inside corners | 1/4" bit | dogbones sized to the bit radius (parameter `bit_d`) |

If the app shows the *actual* stock thickness (it has `thickness_mm` / `detected_thickness` fields),
set `t_actual` and re-generate (TODO-verify after login).

### Assembly (no tools beyond a mallet)
1. Stand both long panels up and slide the deck tenons through their mortises.
2. Drop in the 4 wedges loosely.
3. Lower the short panels from above onto the cross-lap slots.
4. Tap the wedges home.
5. Flip the frame and screw the heater to the deck underside, following the heater manual.
6. Flip it back, add the futon, then the top.

## 3. Parts list (draft)
| Part | Qty | Approx size (mm) | Notes |
|---|---|---|---|
| Top | 1 | 1200 × 800 | optional underside pockets |
| Long side | 2 | 1120 × 370 | top-open cross-lap slots, 2 mortises each |
| Short side | 2 | 720 × 370 | bottom-open cross-lap slots |
| Deck / heater plate | 1 | ~500 × ~760 incl. tenons | heater pilot marks (engrave layer) once the heater is known |
| Wedge | 6 | ~120 × 25 | 4 + 2 spares, nested in the offcuts |
| Test coupon set | 1 | small | cross-lap + tenon/wedge sample (phase 6) |

**Nesting.** The top (1200) does **not** fit a 48" sheet with the 20 mm margins (1179 usable), so we
need 60"-wide stock. Everything fits on **one 60 × 120" sheet** (~2.7 m of 3.0 m used) or on two
60 × 60" sheets. The generator will produce both layouts so we can compare quotes.

**Weight and shipping.** Top ≈ 12 kg, sides ≈ 8.5 kg, deck ≈ 4.5 kg, total ≈ **25 kg / 55 lb**.
- The top box (~1250 × 850) is over 48", so it is an **oversize parcel**, priced at checkout with
  no contact. Put the deck and wedges in the same box.
- The side panels (≤ 1120 mm) fit a **standard parcel**.
- No part is over 60", so we never hit freight.
- Plan B, if the oversize cost is bad: split the top into two 600 × 800 halves joined with
  butterfly keys (bow-ties) cut from plywood. That keeps everything ≤ 48".

## 4. Phases
0. ✅ Repo, AGENTS.md, vendor research.
1. ✅ **Tooling skeleton:** uv project (Python 3.12, ezdxf, shapely, matplotlib, pytest), `params.toml`,
   Makefile, a smoke test that exports one rectangle DXF.
2. **Geometry:** a primitives module (rect, fillet, dogbone, slot, mortise, tenon, wedge) and
   one function per part, all driven by params.
3. **Checks (pytest):** closed and valid polygons; min feature ≥ t; slot ≥ t_max + clearance;
   mating dimensions agree (slot depths sum to H, tenon ↔ mortise, crossings line up); parts fit
   the sheets; box sizes and weights stay within the parcel limits.
4. **Previews:** PNG per part, sheet layouts, and a simple 3-D assembly render (matplotlib or
   build123d) to eyeball the joints.
5. **Export:** DXF R2010 in mm, layers `CUT` (outside and inside contours) and `ENGRAVE`/`POCKET`;
   one file per part plus nested sheets; a BOM/cut list in `out/BOM.md`.
6. **Fit validation:** order a cheap **test-coupon set** (a cross-lap pair, a tenon + mortise + wedge,
   and crush-rib variants) from the same stock. Measure, tune the clearances, re-generate.
7. **Quote and order:** upload to app.umake.ca. Confirm there is no "manual quote" flag, check the
   shipping class at checkout, then order.
8. **Assembly and finish:** sand off the holding tabs, ease the edges, and optionally oil-finish
   (no glue involved). Mount the heater.

## 5. Open questions (for the owner)
1. **Heater:** do you already have one? Model, voltage (must be 120 V listed), mounting-hole pattern,
   plate size, hang depth, screw length. A screw longer than 18 mm would poke through the deck.
2. **Height:** a floor kotatsu (~39 cm) or a "high" chair-height kotatsu (~60–65 cm)?
3. **Look:** visible cross-lap "ears" at the corners (the default) or flush corners? Any engraving on
   the top?
4. **Top:** single 1200 × 800 slab (an oversize parcel) or the 2-piece bow-tie version
   (standard parcels only)? Do you want the summer locating pockets?
5. **Province/postal code**, for shipping classes and cost (Canada assumed).
6. Budget ceiling? (A real price needs the app; the ≥ $250 free-shipping threshold is likely
   exceeded anyway.)
