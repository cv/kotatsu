# Kotatsu plan

Status: **designing**. Every number lives in `params.toml`. Items marked **TODO-verify** need
data from the uMake app, or from the heater once it's in hand.

## 0. Owner decisions (2026-10)
| Question | Answer |
|---|---|
| Table | **One round kotatsu, top Ø 900 cut as one piece.** The 1200 × 900 rectangle and all the decorative seam options were dropped (they're archived at git tag `seams-archive`) |
| Frame | **Yagura, straight legs** (2026-10-19): 4 straight 120 mm "+" corner legs under a wedged deck, no aprons |
| Heater | **PaletteLife 120 V 400 W** ordered (see docs/heater.md); the backup is Zuomeng PTC |
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
- **Legs (4 "+" corner legs = 8 plates, 120 × 385).** They're straight, with plumb edges, and lie in the planes where the slab panels were.
  - Each corner crosses two plates in a cross-lap 50 mm in from the frame edge, which forms the "ears".
    "A" plates are slotted from the shoulder down, "B" plates from the floor up. Slots are t_max + 0.3 wide; their depths add up to the leg height + 1, so the floor sets the height.
  - Each plate's width, measured in from the frame edge: a 40 mm ear arm, the 19 mm slot, a 10 mm shoulder, then a 50 mm tenon out to the inner edge.
    That's the thinnest leg that still takes a wedge (≥ 15 mm of wood beside the wedge hole).
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
| Owner's 30" × 12.5" knee zone: reach under the top's edge / room between legs at knee height | 120 mm / 420 mm |
| Clear height under the heater | 285 mm |
| Push to tip it (mid-side, 50 mm in / at the very edge) | ≈ 1020 N / 600 N |

**Tipping** is computed the way EN 12521 / EN 1730 test it: a vertical push at the middle of a side, 50 mm in from the edge.
The figures assume no foot slip, and the weight includes a guessed heater (3 kg) and futon (2 kg). **There is no pass/fail limit yet.**
It needs a real figure: EN 12521:2023's force table, or a bathroom-scale test on the finished table (`comfort.tip_min_n`, 0 = report only).

### History
- 1200 × 900 rectangle with 3 boards and decorative seams (ari, yajiri, maple, …): dropped for the round one-piece top. Git tag `seams-archive`.
- Slab-side frame (apron + legs in one piece, tapered legs, bell feet; leg-room options A–F) and a splayed-leg yagura: built for comparison, then dropped in favour of the straight yagura. Git tag `frame-variants-archive`.

## 4. Budget (CAD, estimates; TODO-verify)
| Item | Estimate |
|---|---|
| Heater (PaletteLife, amazon.ca, delivered) | $258 |
| uMake CNC order: one 60×60" sheet of 18 mm Baltic birch + routing; oversize shipping for the top | **$300–550** |
| Round futon 205 cm (Amazon.co.jp delivered, before duty/tax) | $160–280 |
| Finish oil + sandpaper | $30–50 |
| **Total** | **~$750–1150** |

## 5. Phases
0. ✅ Repo, AGENTS.md, vendor research, tooling (uv, ezdxf, shapely, matplotlib, pytest, Makefile).
1. ✅ Project site (`make dev`, http://127.0.0.1:8765): futon & rug plan, frame parts, cut sheets, 3-D, docs, test status.
2. ✅ Frame geometry and joint tests; cut list, nesting, DXF per part and per sheet, `out/BOM.md`.
3. ✅ **Leg room** and ✅ **frame style**: yagura with straight legs (sections 2–3).
3b. **Stiffness / wobble check** for the yagura (2-D stress model + joint slack), and a real tipping limit.
4. ◐ **Heater**: measure it when it arrives and freeze `[heater]` (body, screw-hole positions, screw size, cord exit).
5. **Quote** on app.umake.ca: read the actual stock thickness and price; make sure there's no "manual quote" flag.
6. Optional fit coupons (a cross-lap pair, a tenon + wedge).
7. Order, assemble, finish (sand off the holding tabs, ease the edges, oil).

## 6. Open questions
1. Tipping limit: EN 12521:2023's force table, or a bathroom-scale test.
2. Heater measurements, and the clearances required by its manual.
3. Futon choice. The traditional shijira cotton (Wataman) is sold out; Amazon.co.jp has 205 cm options in stock.
