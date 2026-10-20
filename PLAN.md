# Kotatsu plan

Status: **designing**. Every number lives in `params.toml`. Items marked **TODO-verify** need
data from the uMake app, or from the heater once it's in hand.

## 0. Owner decisions (2026-10)
| Question | Answer |
|---|---|
| Table | **One round kotatsu, top Ø 900 cut as one piece**, on a 660 × 660 square slab frame. The 1200 × 900 rectangle and all the decorative seam options were dropped (they're archived at git tag `seams-archive`) |
| Heater | **PaletteLife 120 V 400 W** ordered (see docs/heater.md); the backup is Zuomeng PTC |
| Height | ≈ 41 cm total: frame 385 + top 18 + futon (owner accepted the top of the 39–41 range for leg room) |
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
- **Side panels (×4), 660 × 385.** Each panel is one slab that forms the apron and both legs.
  - Corners: cross-laps 50 mm in from the panel ends (the "ears"). Long panels are slotted from the top, short panels from the bottom.
  - Slots: width = t_max + 0.3; depth = H/2 + 0.5, so the floor sets the height.
  - Legs: 140 wide where they meet the apron, **tapering to 100 at the floor**. The inner edge slants and the outer edge stays plumb.
    That leaves a **380 mm** opening on every side, widening to 460 at the floor. Each short-panel foot is two equal 40 mm fingers either side of the slot.
  - Aprons: only **55 deep**, leaving **330 mm** of clear height under them. No joint is cut into the apron.
- **Deck (×1), 500 × 582.** A horizontal shear plate, top at z = 359.
  - It has 4 plain through-tenons (40 wide, standing 2 mm proud), one in each **leg zone**: the 80 mm of solid leg between the cross-lap slot and the opening.
  - No wedges: the cross-laps fix the panel spacing, so the tenons can't pull out.
  - It makes the frame rack-proof.
- **Heater cheeks (×2).** Plates hung under the deck by tabs. The tabs come up through deck slots and are locked by small flat wedges
  (80 × 18, 1:8) lying on the deck.
  - The cheeks end level with the heater bottom, at z = 285.
  - The heater screws into the cheeks through its side flanges (the only hardware).
  - The deck is solid over the heater, so it doubles as the heat shield.
- **Top**: Ø 900 in one piece. It sits on the futon, which is draped over the frame.
- Total height ≈ 385 + 18 + futon ≈ **41 cm**.
- Tests (`tests/test_frame.py`) check every joint fit at t = 17.0 / 18.0 / 18.9 mm, plus:
  - nothing pokes above the futon plane;
  - the frame corners stay ≥ 10 mm inside the round top (currently 11 mm);
  - leg-room minimums.
- **Parts:** 13 pieces, about 18 kg, on one 48×96" sheet (47 % used).
  - The nester pairs each long side with a short side turned upside down, one leg inside the other's opening. Each pair needs a 27 % smaller rectangle,
    so everything fits with room to spare (about 0.45 × 1.2 m free for fit coupons).

### Assembly (mallet + the heater's screwdriver)
1. Hang the cheeks: push the tabs up through the deck and tap in the 4 cheek wedges.
2. Screw the heater between the cheeks.
3. Stand two opposite panels up and slide the deck's corner tenons through them.
4. Lower the other 2 panels onto the cross-laps from above.
5. Lay on the futon, then the top.

## 3. Leg room (decided 2026-10-19: owner chose A, B, D, E, F)
| | Before | Now |
|---|---|---|
| Clear height under the aprons (thighs/knees) | 285 | **330** |
| Opening width, each of the 4 sides | 360 | **380** |
| Interior between the panels | 522 | **542** |
| Clear height under the heater/cheeks (shins) | 261 / 253 | **285** |
| Parts sticking into the openings | 4 tusk tenons + wedges | none |

- A: the deck tenons moved into the legs.
- B: no deck wedges.
- D: deck drop 40 → 26, using smaller cheek wedges; the cheeks now end level with the heater.
- E: ear 60 → 50.
- F: frame height 375 → 385.
- Not chosen: C (arched apron, which would give ~345 mid-span).

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
3. ✅ **Leg room** (section 3): A, B, D, E, F applied.
4. ◐ **Heater**: measure it when it arrives and freeze `[heater]` (body, screw-hole positions, screw size, cord exit).
5. **Quote** on app.umake.ca: read the actual stock thickness and price; make sure there's no "manual quote" flag.
6. Optional fit coupons (a cross-lap pair, a tenon + wedge).
7. Order, assemble, finish (sand off the holding tabs, ease the edges, oil).

## 6. Open questions
1. Heater measurements, and the clearances required by its manual.
2. Futon choice. The traditional shijira cotton (Wataman) is sold out; Amazon.co.jp has 205 cm options in stock.
