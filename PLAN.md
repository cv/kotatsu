# Kotatsu plan

Status: **designing**. Every number lives in `params.toml`. Items marked **TODO-verify** need
data from the uMake app, or from the heater once it's in hand.

## 0. Owner decisions (2026-10)
| Question | Answer |
|---|---|
| Table | **One round kotatsu, top Ø 900 cut as one piece.** The 1200 × 900 rectangle and all the decorative seam options were dropped (they're archived at git tag `seams-archive`) |
| Frame | **Yagura, straight legs** (2026-10-19): 4 straight 130 mm "+" corner legs under a wedged deck, no aprons |
| Material | **Everything in 18 mm birch plywood, wedges included** (2026-10-19). Hardwood wedges or other uMake materials were considered and dropped; the owner will make new wedges if any wear out |
| Heater | **PaletteLife 120 V 400 W** ordered (see docs/heater.md); the backup is Zuomeng PTC. **The owner drills the heater's screw holes on assembly**, so no holes are cut |
| Height | ≈ 41 cm total: frame 385 + top 18 + futon (owner accepted the top of the 39–41 range for leg room) |
| Corners | the default visible cross-lap "ears"; no engraving |
| Futon & rug | a **205 cm round** futon on an 8 ft round rug (docs/futon.md, docs/futons.toml, site tab "Futon & rug") |
| Ship to | rural BC |
| Budget | **< $1200 CAD all-in** |

## 1. Process & material
- **18 mm Baltic birch, CNC-routed** on uMake (app.umake.ca → CNC router → Birch plywood 18 mm / 3/4").
  The laser only cuts plywood ≤ 6 mm (docs/research.md).
- **Everything fits on one 60 × 60" sheet** (2.32 m², 62 % used; `out/BOM.md`). Leg plates are laid out with the grain running up the leg.
- **Shipping:** the Ø 900 top packs to about 37 × 37 × 2.7". Length + girth is about 118", which is over the 108" standard-parcel
  limit, so it ships **oversize** (priced automatically at checkout, no staff contact). The frame parts are standard parcels.
  TODO: add a length + girth check to the build.

## 2. Design: yagura frame with straight legs (`kotatsu/yagura.py`, `[[tables]] yagura`)
- **Legs (4 "+" corner legs = 8 plates, 130 × 385).** They're straight, with plumb edges, and lie in the planes where the slab panels were.
  - Each corner crosses two plates in a cross-lap 50 mm in from the frame edge, which forms the "ears".
    "A" plates are slotted from the shoulder down, "B" plates from the floor up. Slots are t_max + 0.3 wide; their depths add up to the leg height + 1, so the floor sets the height.
  - Each plate's width, measured in from the frame edge: a 40 mm ear arm, the 19 mm slot, a 10 mm shoulder, a 50 mm tenon, then a 10 mm inner shoulder.
    The tenon is the narrowest that still takes a wedge (≥ 15 mm of wood beside the hole). The inner shoulder puts the wedge between shoulders, so tapping it in doesn't twist the plate (owner chose this after the wobble check, 2026-10-19).
- **Deck (×1), 660 square** with its corners trimmed ≥ 10 mm inside the round top. Its top is at z = 359 (26 mm below the futon plane).
  - It has 8 mortises (tenon + 0.2 per side; thickness t_max + 0.5) and the cheek-tab slots.
  - Each leg plate's top edge is a **shoulder** under the deck. Its tenon rises through the deck to z = 385, so the 8 tenon tops carry the futon and top.
  - A **60 × 18 wedge** (1:8) lies on the deck and is driven through each tenon. It clamps the deck between the shoulder and the wedge, at every stock thickness from 17.0 to 18.9 mm.
- **Heater cheeks (×2)**: hung from the deck by tabs and flat 80 × 18 wedges. The heater screws into them through its side flanges (the only hardware).
  The deck is solid over the heater, so it doubles as the heat shield.
- **Top**: Ø 900 in one piece. It sits on the futon, which is draped over the frame. Total height ≈ 41 cm.
- **Parts:** 26 pieces (8 leg plates, deck, 2 cheeks, 9 + 5 wedges incl. spares, top), ≈ 18 kg, 22.9 m of cutting.
- Tests: `tests/test_yagura.py` (cross-laps, tenon fit, wedge clamp range, wedges don't collide, deck inside the top) and the
  shared checks in `tests/test_frame.py` (cuttable, fits a sheet and a parcel, cheeks, knee zone, nothing above the futon plane).
- **Not modelled yet: stiffness.** The legs rely on wedged tenons in an 18 mm deck. A wobble/stress check is the next engineering step.

### Assembly (mallet + the heater's screwdriver)
1. Cross each pair of leg plates into a "+" leg: drop the B plate onto the A plate's slot.
2. Stand the 4 legs up and lower the deck over the 8 tenons.
3. Tap a leg wedge through each tenon.
4. Hang the cheeks (tabs up through the deck, 4 cheek wedges), then screw the heater between them.
5. Lay on the futon, then the top.

## 3. Numbers (site Overview, "Design numbers")
| | |
|---|---|
| Pieces / of which wedges | 26 / 14 (incl. 2 spares) |
| Weight | ≈ 18 kg |
| Plywood | one 60×60" sheet, 2.32 m², 62 % used |
| Clear height at mid-side (deck underside) | 341 mm |
| Owner's 30" × 12.5" knee zone: reach under the top's edge / room between legs at knee height | 120 mm / 400 mm |
| Clear height under the heater | 285 mm |
| Push to tip it (mid-side, 50 mm in / at the very edge) | ≈ 1030 N / 610 N |
| Sway under a 100 N sideways push (wedges tight) | ≈ 0.3 mm |

**Tipping** is computed the way EN 12521 / EN 1730 test it: a vertical push at the middle of a side, 50 mm in from the edge.
The figures assume no foot slip, and the weight includes a guessed heater (3 kg) and futon (2 kg). **There is no pass/fail limit yet.**
It needs a real figure: EN 12521:2023's force table, or a bathroom-scale test on the finished table (`comfort.tip_min_n`, 0 = report only).

### Wobble and strength (`kotatsu/stiffness.py`, estimates)
This is a spring model of each leg-to-deck joint, not FEA. It includes:
- the shoulders pressing on the deck (plywood is soft through its thickness);
- the wedge pulling the tenon up, tapped in to about 300 N;
- the tenon faces bearing on the mortise ends, with 0.2 mm clearance per side;
- each plate bending.

Material values are rough (E along the grain 9 GPa, through the thickness 300–800 MPa, bending strength ~35 MPa) and need verifying.

| | Straight 120 mm legs (before) | With a 10 mm inner shoulder (130 mm legs, **chosen**) |
|---|---|---|
| Sway under a 100 N sideways push, wedges tight | ≈ 0.3 mm (0.24–0.42 across the material/preload range) | ≈ 0.3 mm (0.29–0.42) |
| Leg tilt as a wedge is tapped in, if nothing stops it | **≈ 9 mm at the foot** | ≈ 0.3 mm |
| Room between legs at knee height | 420 mm | 400 mm |

- **Frame stiffness is fine either way.** About 0.3 mm of sway per 100 N, plus up to 0.4 mm of play from the tenon clearance.
  A wedge that works 0.1 mm loose adds about 0.4 mm at that leg, so re-tap the wedges after the first heating season.
- **The current leg joint is one-sided.** The tenon runs to the leg's inner edge, so every shoulder sits outboard of the wedge.
  Tapping the wedge in twists the plate until its tenon jams diagonally in the mortise, about 1.5° (≈ 9 mm at the foot).
  The joint is stiff once jammed, but the legs end up out of plumb or fighting each other, by however much the real mortise clearance allows (uMake's in-plane tolerance is ±0.3–0.45 mm).
  A 10 mm shoulder on the inner side of each tenon (legs 130 mm wide) puts the wedge between shoulders and removes the twist.
- **Stresses are low.** Legs ≈ 1.3 MPa at a 200 N push. Top ≈ 4.7 MPa with 1000 N pressed 50 mm in from the edge.
  Wood above the wedge hole ≈ 1.4 MPa in shear. That's at least about 8× below the rough bending strength.

### History
- 1200 × 900 rectangle with 3 boards and decorative seams (ari, yajiri, maple, …): dropped for the round one-piece top. Git tag `seams-archive`.
- Slab-side frame (apron + legs in one piece, tapered legs, bell feet; leg-room options A–F) and a splayed-leg yagura: built for comparison, then dropped in favour of the straight yagura. Git tag `frame-variants-archive`.

## 4. Budget (CAD, estimates; TODO-verify)
| Item | Estimate |
|---|---|
| Heater (PaletteLife, amazon.ca, delivered) | $258 |
| uMake CNC order: **$353.91** for all 28 parts in Baltic birch "19mm" (notched deck, one wedge part ×14), shipping **free** (91×91×16 cm, 16.6 kg), tax $42.47 → **$396.38** (docs/quote.md) | **$396** |
| Round futon 205 cm (Amazon.co.jp delivered, before duty/tax) | $160–280 |
| Finish oil + sandpaper | $30–50 |
| **Total** | **~$850–1080** |

## 5. Phases
0. ✅ Repo, AGENTS.md, vendor research, tooling (uv, ezdxf, shapely, matplotlib, pytest, Makefile).
1. ✅ Project site (`make dev`, http://127.0.0.1:8765): futon & rug plan, frame parts, cut sheets, 3-D, docs, test status.
2. ✅ Frame geometry and joint tests; cut list, nesting, DXF per part and per sheet, `out/BOM.md`.
3. ✅ **Leg room** and ✅ **frame style**: yagura with straight legs (sections 2–3).
3b. ✅ **Wobble/strength estimate** (above): frame stiff, stresses low; one-sided leg joint found and fixed (130 mm legs). Still open: a real tipping limit; a test coupon to measure the tenon/mortise fit.
4. ◐ **Heater**: when it arrives, measure the body width/depth/height, its mounting flanges, the cord exit and the manual's clearances, then freeze `[heater]`. This **gates the order**, because the cheek spacing comes from the body width. Screw holes aren't cut: the owner drills them on assembly.
5. ✅ **Quote**: $396.38 incl. tax, free shipping, instant, no manual-quote flag (saved project; docs/quote.md). Still open: the real thickness of uMake's "19mm" (design takes 17.0–18.9).
6. Optional fit coupon (a cross-lap pair, a tenon + wedge). Decide after the quote: skip it if the wait or the cost isn't worth it.
7. Order, assemble, finish (sand off the holding tabs, ease the edges, oil).

## 6. Open questions
1. Tipping limit: EN 12521:2023's force table, or a bathroom-scale test.
2. Heater measurements (body, flanges, cord exit), and the clearances required by its manual.
3. Futon choice. The traditional shijira cotton (Wataman) is sold out; Amazon.co.jp has 205 cm options in stock.
