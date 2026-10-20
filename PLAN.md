# Kotatsu plan

Status: **designing**. Every number lives in `params.toml`. Items marked **TODO-verify** need
data from the uMake app, or from the heater once it's in hand.

## 0. Owner decisions (2026-10)
| Question | Answer |
|---|---|
| Table | **One round kotatsu, top Ø 900 cut as one piece**, on a 660 × 660 square slab frame. The 1200 × 900 rectangle and all the decorative seam options were dropped (they're archived at git tag `seams-archive`) |
| Heater | **PaletteLife 120 V 400 W** ordered (see docs/heater.md); the backup is Zuomeng PTC |
| Height | 39–41 cm total: frame 375 + top 18 + futon ≈ 400–410 |
| Corners | the default visible cross-lap "ears"; no engraving |
| Futon & rug | a **205 cm round** futon on an 8 ft round rug (docs/futon.md, docs/futons.toml, site tab "Futon & rug") |
| Ship to | rural BC |
| Budget | **< $1200 CAD all-in** |

## 1. Process & material
- **18 mm Baltic birch, CNC-routed** on uMake (app.umake.ca → CNC router → Birch plywood 18 mm / 3/4").
  The laser only cuts plywood ≤ 6 mm (docs/research.md).
- **Everything fits on one 48 × 96" sheet** (2.97 m², 52 % used; `out/BOM.md`).
- **Shipping:** the Ø 900 top packs to about 37 × 37 × 2.7". Length + girth is about 118", which is over the 108" standard-parcel
  limit, so it ships **oversize** (priced automatically at checkout, no staff contact). The frame parts are standard parcels.
  TODO: add a length + girth check to the build.

## 2. Design: "four slab sides + deck" (`kotatsu/frame.py`)
- **Side panels (×4), 660 × 375.** Each panel is one slab that forms the apron and both legs. The corners are cross-laps 60 mm in
  from the panel ends (the "ears"). Long panels are slotted from the top and short panels from the bottom. Slot width = t_max + 0.3, and slot depth =
  H/2 + 0.5, so the floor sets the height. The legs are 150 wide, which leaves a **360 mm** opening on every side (4 sitters). The apron is 90 deep,
  which leaves **285 mm** of clear height under it.
- **Deck (×1)**: a horizontal shear plate with its top at z = 335. It has 2 tusk tenons per side, through dogboned mortises in two opposite
  panels, locked by 1:8 vertical wedges. It makes the frame rack-proof.
- **Heater cheeks (×2)**: plates hung under the deck by tabs. The tabs come up through deck slots and are locked by flat wedges lying on the
  deck. The heater screws into the cheeks through its side flanges (the only hardware). The deck is solid over the heater, so it doubles as the
  heat shield between the heater and the futon.
- **Top**: Ø 900 in one piece. It sits on the futon, which is draped over the frame.
- Tests (`tests/test_frame.py`) check every joint fit at t = 17.0 / 18.0 / 18.9 mm. They also check that nothing pokes above the futon
  plane, and that the frame corners stay ≥ 10 mm inside the round top.

### Assembly (mallet + the heater's screwdriver)
1. Hang the cheeks: push the tabs up through the deck and tap in the 4 cheek wedges. 2. Screw the heater between the cheeks.
3. Stand two opposite panels up and slide the deck tenons through them. 4. Fit the deck wedges.
5. Lower the other 2 panels onto the cross-laps from above. 6. Tap the wedges home. 7. Lay on the futon, then the top.

## 3. Leg room: proposal (2026-10-19, waiting for the owner's choice)
On a Ø 90 table, 4 sitters' knees end up ~20–25 cm from the centre, just outside the heater. Their thighs pass under the
aprons. So the clear height **under the aprons** matters most, then the opening width, then the clearance under the heater
(only shins and feet go there).

What limits it today:
- the apron has to be 90 deep only because the deck mortises sit in it (the tenons are at x = 240–360, inside the 270–630 opening);
- the tusk tenons and their wedges stick out into the openings, right where thighs come in;
- the deck sits 40 mm down to make room for the cheek wedges, and the cheeks hang 8 mm below the heater.

| Change | Effect | Cost / risk |
|---|---|---|
| A. Move the deck tenons into the legs (40 wide at x 210–250, between the opening edge and the cross-lap slot, ~20 mm of wood each side) | apron 90 → **55**: clear height **285 → 320** | narrow tenons |
| B. Drop the deck wedges: plain through-tenons (the cross-laps already fix the panel spacing) | nothing sticks out into the openings; −6 parts | loses the visible tusk detail (or keep small wedges on A's tenons) |
| C. Arch the apron (55 at the legs, ~40 at mid-span) | **335** at the centre of each opening | looks different; still stiff (span 360) |
| D. Smaller cheek wedges, deck drop 40 → ~28; cheeks no lower than the heater | under the heater **261 → ~273** | TODO-verify the wedge geometry |
| E. Ear 60 → 50 (panels move out; the ear tips stay 10 mm inside the top) | openings **360 → ~380**, interior 522 → 542 | ear fingers 40 wide instead of 50 |
| F. Frame height 375 → 385 | everything +10 | total ≈ 41 cm with futon (top of the 39–41 range) |

Recommended: **A + B + D**; C and E are a matter of taste; F only if 41 cm is fine.

## 4. Budget (CAD, estimates; TODO-verify)
| Item | Estimate |
|---|---|
| Heater (PaletteLife, amazon.ca, delivered) | $258 |
| uMake CNC order: one 48×96" sheet of 18 mm Baltic birch + routing; oversize shipping for the top | **$300–550** |
| Round futon 205 cm (Amazon.co.jp delivered, before duty/tax) | $160–280 |
| Finish oil + sandpaper | $30–50 |
| **Total** | **~$750–1150** |

## 5. Phases
0. ✅ Repo, AGENTS.md, vendor research, tooling (uv, ezdxf, shapely, matplotlib, pytest, Makefile).
1. ✅ Project site (`make dev`, http://127.0.0.1:8765): futon & rug plan, frame parts, cut sheets, 3-D, docs, test status.
2. ✅ Frame geometry and joint tests; cut list, nesting, DXF per part and per sheet, `out/BOM.md`.
3. ◐ **Leg room** (section 3): waiting for the owner's choice.
4. ◐ **Heater**: measure it when it arrives and freeze `[heater]` (body, screw-hole positions, screw size, cord exit).
5. **Quote** on app.umake.ca: read the actual stock thickness and price; make sure there's no "manual quote" flag.
6. Optional fit coupons (a cross-lap pair, a tenon + wedge).
7. Order, assemble, finish (sand off the holding tabs, ease the edges, oil).

## 6. Open questions
1. Leg-room changes A–F (section 3).
2. Heater measurements, and the clearances required by its manual.
3. Futon choice. The traditional shijira cotton (Wataman) is sold out; Amazon.co.jp has 205 cm options in stock.
