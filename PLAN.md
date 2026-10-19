# Kotatsu plan

Status: **designing**. Every number lives in `params.toml`. Items marked **TODO-verify** need
data from the uMake app or from the heater once it's in hand.

## 0. Owner decisions (2026-10)
| Question | Answer |
|---|---|
| Heater | none yet. Pick: **PaletteLife 120 V 400 W** (see docs/heater.md); backup Zuomeng PTC |
| Height | 39–41 cm total → frame 375 + top 18 + futon ≈ 400–410 |
| Corners | default visible cross-lap "ears"; no engraving |
| Top | split into 2 halves (all boxes ≤ 48"). Joinery choice: see `out/preview/top_options.png` |
| Ship to | rural BC |
| Budget | **< $1200 CAD all-in** |

## 1. Process & material decision
- **18 mm Baltic birch, CNC-routed** on uMake (app.umake.ca → CNC router → Birch plywood 18 mm / 3/4").
  The laser is limited to plywood ≤ 6 mm, which is too thin for the top or for a frame with no glue
  (see docs/research.md).
- Fallback vendor: SendCutSend (TODO-verify its wood options and Canadian shipping).

## 2. Design concept: "four slab sides + deck"
```
        TOP (2 halves, interlocking seam) ─ sits on futon, which is draped over the frame
   ┌──────────────────────┬───────────────────────┐
   │  ear┃               ⟨seam⟩               ┃ear │   frame footprint ≈ 1120 × 720
   │ ━━━━╋━━━━━━━━━ long side panel ━━━━━━━━━━╋━━━ │   (40 mm top overhang all round)
   │     ┃      ┌────── DECK ───────┐         ┃    │
   │short┃  ▭═══╡ ║ [heater] ║      ╞═══▭     ┃short   ▭═ tusk tenon + wedge through
   │side ┃      │ ║  cheeks  ║      │         ┃side      the long aprons
   │     ┃      └───────────────────┘         ┃    │
   │ ━━━━╋━━━━━━━━━ long side panel ━━━━━━━━━━╋━━━ │
   └──────────────────────┴───────────────────────┘
```
**Side panels (×4).** Each side is one piece that forms the apron and both legs, with a large leg
opening with filleted corners.
- The corners are **cross-laps**: long panels slotted from the top, short panels from the bottom,
  each to half the height. The panels cross ~45 mm from their ends, so every leg is a stiff "+"
  section with four feet.

**Deck (×1).** About 500 × 650 plus tenons. It is a horizontal plate between the long aprons, with
its top 25 mm below the apron top edge.
- **2 tusk tenons per long side**, locked with **wedges** (×4, plus 2 spares). The deck is a shear
  diaphragm, so the frame can't rack.
- The tenon *width* ↔ mortise *length* fit is an in-plane, CNC-precise dimension (±0.4 mm). It does
  not depend on the ±1 mm sheet-thickness variation.
- **Heater bay:** a square opening of heater size + 2 mm. Two on-edge **heater cheeks** (~90 mm tall)
  pass through slots in the deck on either side of the bay. The PaletteLife screws through its side
  flanges into the cheek faces, the traditional yagura mount (`heater.mount = "side"`).
  - With `mount = "bracket"` (Zuomeng), the bay becomes a solid pad and its L-brackets screw into
    the deck underside.
  - Heater top ≈ deck top. Heater bottom ≈ 300 mm above the floor.

**Top.** 1200 × 800 × 18, split at x = 600 into two 600 × 800 halves. Each half rests on the frame
on three sides (both long aprons and one short apron), so the seam only has to lock **in-plane**.
The options are rendered in `out/preview/top_options.png`:
- **ari** (dovetail seam, alternating tails): Japanese *ari-tsugi*, no loose parts. Current default.
- **puzzle** (jigsaw tabs, alternating): playful, no loose parts.
- **chigiri** (3 through bow-tie keys on a straight seam): classic look. But the keys are only
  friction-held and can drop out when you lift a half.

All in-plane mating shapes are generated "router-aware": the male part's corners are rounded to
the bit radius, and the female is the male grown by `fit.inplane_c`. They need no dogbones and
look soft and intentional.

### Thickness-tolerance strategy
| Joint | Controlled by | Strategy |
|---|---|---|
| Cross-lap slot width | stock thickness (17.0–18.9) | slot = t_max + 0.3; optional crush ribs. Slop is harmless because the deck stops racking |
| Deck tenon ↔ mortise length | CNC in-plane | +0.2 per side |
| Mortise height ↔ deck thickness | stock thickness | t_max + 0.5; the wedges take up the play |
| Wedge hole in tenon | in-plane taper | 1:8, hole set 2 mm inside the apron face |
| Square-edged slots / mortises | 1/4" bit | dogbones |
| Top seam / keys | CNC in-plane | rounded male + `inplane_c` = 0.2 per side |

### Assembly (no tools beyond a mallet and a screwdriver for the heater)
1. Stand both long panels up and slide the deck tenons through their mortises.
2. Drop in the 4 wedges loosely.
3. Lower the short panels from above onto the cross-lap slots.
4. Tap the wedges home.
5. Fit the heater cheeks.
6. Flip the frame, drop the heater into the bay, and drive its 4 screws into the cheeks.
7. Flip it back, add the futon, then slide the two top halves together on top of it.

## 3. Parts list (draft)
| Part | Qty | Approx size (mm) | Notes |
|---|---|---|---|
| Top half | 2 | ~635 × 800 | interlocking seam |
| Long side | 2 | 1120 × 375 | top-open cross-lap slots, 2 mortises each |
| Short side | 2 | 720 × 375 | bottom-open cross-lap slots |
| Deck | 1 | ~500 × ~760 incl. tenons | heater bay + cheek slots |
| Heater cheek | 2 | ~400 × 90 | screw faces at heater width + 1 mm |
| Wedge | 6 | ~120 × 25 | 4 + 2 spares, nested in the offcuts |

**Nesting.** No part is over 1219 mm, so 48 × 96" sheets work again. The generator will produce
layouts for 48×96, 60×60 and 60×120 so we can compare quotes.

**Weight and shipping.** Total ≈ 25 kg / 55 lb. The longest part is 1120 mm (44"), so **every box
can be a standard parcel**: ≤ 48" and ≤ 50 lb each, with L+girth well under 108". Shipping is free
on orders ≥ $250. Nothing goes oversize or freight.

## 4. Budget (CAD, estimates; TODO-verify with real quotes)
| Item | Estimate |
|---|---|
| Heater (PaletteLife, amazon.ca, delivered) | $258 |
| uMake CNC order: ~2.7 m² of 18 mm Baltic birch + routing | **$400–700**. Get a quote early |
| Optional test-coupon order (< $250, so it pays for shipping) | $60–110 |
| Kotatsu futon/comforter for 120 × 80 (~205 × 245 cm) | $100–200 |
| Finish oil + sandpaper | $30–50 |
| **Total** | **~$850–1300** |

The budget is tight at the top end. If the uMake quote comes in high:
- skip the coupon order and rely on the wedges and tolerant slots;
- tune the nesting to one sheet size;
- or shrink the leg openings to save router time.

## 5. Phases
0. ✅ Repo, AGENTS.md, vendor research.
1. ✅ **Tooling skeleton** (uv, ezdxf, shapely, matplotlib, pytest, Makefile).
2. ◐ **Geometry.** Done: router-aware mating helpers and the top split variants (tests pass).
   To do: side panels, deck, cheeks, wedges, dogbones.
3. **Checks (pytest):** mating dimensions agree (slot depths sum to H, tenon ↔ mortise, crossings
   line up, cheek spacing = heater + clearance); min feature ≥ t; parts fit the sheets; box and
   weight limits.
4. **Previews:** PNG per part, sheet layouts, and a 3-D assembly render.
5. **Export:** DXF R2010 in mm, layers `CUT`/`POCKET`; one file per part plus nested sheets;
   `out/BOM.md`.
6. **Buy the heater now** (lead time ~1 week). Measure it and freeze `[heater]`.
7. **Quote:** upload to app.umake.ca and read the actual stock thickness and price. Make sure there
   is no "manual quote" flag.
8. **Optional fit coupons** (a cross-lap pair, a tenon + wedge, a seam sample), then tune the clearances.
9. **Order, assemble, finish:** sand off the holding tabs, ease the edges, apply oil.

## 6. Open questions
1. **Top seam style:** ari (default), puzzle or chigiri? Or something else: a wave, more or bigger
   tails?
2. OK to buy the PaletteLife heater now? Its listing shows "only 2 left".
