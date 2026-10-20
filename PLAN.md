# Kotatsu plan

Status: **designing**. Every number lives in `params.toml`. Items marked **TODO-verify** need
data from the uMake app or from the heater once it's in hand.

## 0. Owner decisions (2026-10)
| Question | Answer |
|---|---|
| Heater | none yet. Pick: **PaletteLife 120 V 400 W** (see docs/heater.md); backup Zuomeng PTC |
| Height | 39–41 cm total → frame 375 + top 18 + futon ≈ 400–410 |
| Corners | default visible cross-lap "ears"; no engraving |
| Tables | **Two separate heated kotatsu** (2026-10): **rect 1200 × 900** (4×3 ft, rounded down) with a 3-board seamed top, and **round Ø 900** with a one-piece top on a 660 mm square frame. See `[[tables]]` in params.toml |
| Top seam | still open (placeholder ari-3); favourites: ya-*, bold-yabane, maple; an artist commission is being considered |
| Ship to | rural BC |
| Budget | **< $1200 CAD all-in** |

## 1. Process & material decision
- **18 mm Baltic birch, CNC-routed** on uMake (app.umake.ca → CNC router → Birch plywood 18 mm / 3/4").
  The laser is limited to plywood ≤ 6 mm, which is too thin for the top or for a frame with no glue
  (see docs/research.md).
- Fallback vendor: SendCutSend (TODO-verify its wood options and Canadian shipping).

## 2. Design concept: "four slab sides + deck"
```
         TOP (3 boards, 2 dovetail seams) ─ sits on futon, which is draped over the frame
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
**Side panels (×4)** (`kotatsu/frame.py`). Each side is one slab that forms the apron and both legs.
- Long sides are 1120 × 375 mm; short sides are 720 × 375 mm.
- Leg opening: legs 170 mm wide, apron 90 mm deep, 50 mm fillets.
  - Clear height under the aprons is **285 mm**, for thighs.
  - The short-side opening is 380 mm wide (one sitter). The long-side opening is 780 mm wide (two sitters).
- Corners are **cross-laps** 65 mm from the panel ends (the visible "ears"). Long panels are slotted from the top, short panels from the bottom.
  - Slots are 19.2 mm wide, to take the thickest stock (18.9 mm).
  - Each slot is H/2 + 0.5 deep, so the slot bottoms never touch and the floor sets the height.
  - Each leg is a stiff "+" section with four feet. The ear fingers are ≥ 55 mm wide.
- **Lift the table by the long sides.** The long panels' lower halves carry the short panels up with them. Lifting by a short side pulls it off.

**Deck (×1)**: 500 × 571 mm between the long aprons. It's a horizontal shear plate with its top at z = 335 (40 mm below the apron tops), resting in the mortises.
- **2 tusk tenons per long side** (120 wide, 300 apart), through dogboned mortises.
  - The in-plane fit is tight: +0.2 per side.
  - The mortise height takes the thickest stock (+0.5).
  - The tenons stick out 50 mm and are locked by **vertical wedges** (4 + 2 spare, 1:8).
- Each wedge hole starts 2 mm *inside* the apron face, so the wedge always bears on the apron and pulls the deck shoulders tight.
- The wedges are 66 mm long. At every stock thickness from 17.0 to 18.9 mm, they tighten with the head below the apron top (no futon bump) and the foot above the apron bottom edge (no knee bump).
- The deck makes the frame rack-proof. With the long panels locked parallel, the short panels can't rotate in plan.

**Heater cheeks (×2)**: 372 × 64 mm on-edge plates hung under the deck. Their inner faces are exactly heater width + 1 mm apart (293 mm for the PaletteLife).
- Each cheek has 2 tabs that rise through dogboned deck slots.
- The tabs are locked by **flat wedges** (4 + 1 spare) that lie on the deck top and are driven sideways. This pulls the cheek up tight under the deck.
- The heater screws through its side flanges into the cheek faces, the traditional yagura mount.
- The heater top sits 5 mm under the deck (TODO-verify against the manual), at z 261–312. That leaves **≥ 250 mm** of knee room under it.
- The deck is solid over the heater: it's the heat shield between the heater and the futon.

**Everything above the deck stays below the futon plane** (z ≤ 370). Tests check this, along with every joint fit, at t = 17.0 / 18.0 / 18.9 mm (`tests/test_frame.py`).

**Top.** 1200 × 800 × 18, split at x = 400 and 800 into **3 boards** (`top.boards`). The cut sizes are 470 / 540 / 470 ×
800 mm, about 4 kg each. Every board spans both long aprons, so each board carries its own load and the seams only
have to lock **in-plane**. With `top.mirror` the second seam mirrors the first, so the middle board is symmetric:
it takes tails from both sides at the outer joints and sends its own tails out at the centre.
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

### Assembly (mallet + the heater's screwdriver)
1. Hang the cheeks: push their tabs up through the deck slots, then tap the 4 flat cheek wedges through the tab holes.
2. Screw the heater between the cheeks (its own screws).
3. Stand both long panels up and slide the deck tenons through their mortises. Spread the panels a little to get the second side on.
4. Drop the 4 deck wedges into the tenon holes and press them in by hand.
5. Lower the 2 short panels from above onto the cross-lap slots.
6. Tap the deck wedges home.
7. Lay the futon over the frame. Lay the middle top board on it, then drop each outer board into its seam.

## 3. Parts list (draft)
| Part | Qty | Approx size (mm) | Notes |
|---|---|---|---|
| Top board | 3 | 470 / 540 / 470 × 800 | ari-3 dovetail seams |
| Long side | 2 | 1120 × 375 | top-open cross-laps, 2 deck mortises |
| Short side | 2 | 720 × 375 | bottom-open cross-laps |
| Deck | 1 | 500 × 708 incl. tenons | 4 tusk tenons with wedge holes, 4 cheek-tab slots |
| Heater cheek | 2 | 372 × 112 incl. tabs | 2 tabs with wedge holes |
| Deck wedge | 6 | 27 × 66 | 4 + 2 spares, 1:8 |
| Cheek wedge | 5 | 96 × 26 | 4 + 1 spare, 1:8 |

**Nesting.** No part is over 1219 mm, so 48 × 96" sheets work again. The generator will produce
layouts for 48×96, 60×60 and 60×120 so we can compare quotes.

**Weight and shipping.** Frame ≈ 13.5 kg + top ≈ 12 kg = 25.5 kg / 56 lb (two boxes). The longest part is 1120 mm (44"), so **every box
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
1b. ✅ **Project site** (`make dev`): seam gallery, zoomable 2-D viewer with mm readout and router-bit cursor, compare grid, 3-D preview (draft frame), docs, test status.
2. ◐ **Geometry.** Done: router-aware mating helpers and **7 top-seam variants** (ari-3, ari-5, ari-2-bold, kama-3, puzzle-3, seigaiha-8, chigiri-3) in `[[top.options]]`, with tests for cuttability, overlap and pull-apart locking.
   Done: frame (side panels with cross-laps, deck with wedged tusk tenons, hung heater cheeks, wedges, dogbones), with joint-fit tests across the stock-thickness range.
   Done: cut list, sheet nesting with mixed sheet sizes, per-part and per-sheet DXF, `out/BOM.md` (`make dxf`).
   **Both tables together: 60×120" + 60×60" = 6.97 m² (54 % used), ~47 kg of parts.** (Earlier one-table figures:) Least plywood: **1 table = 4.65 m²** (one 60×120" or two 60×60", 44 % used); **2 tables = 7.62 m²** (48×96" + 2 × 60×60", 53 % used, 3.81 m² per table, 18 % less each).
   Top grain now runs the table's length (`layout.top_grain = "along"`), continuous across the 3 boards; that's what lets 2 tables pack well.
   To do: freeze `[heater]` after measuring; check how uMake prices (per sheet or per part area + cut time); fit coupons in the spare sheet area.
3. **Checks (pytest):** mating dimensions agree (slot depths sum to H, tenon ↔ mortise, crossings
   line up, cheek spacing = heater + clearance); min feature ≥ t; parts fit the sheets; box and
   weight limits.
4. **Previews:** PNG per part, sheet layouts, and a 3-D assembly render.
5. **Export:** DXF R2010 in mm, layers `CUT`/`POCKET`; one file per part plus nested sheets;
   `out/BOM.md`.
6. ◐ **Heater ordered by owner** (arriving in a few days). Measure it and freeze `[heater]`.
7. **Quote:** upload to app.umake.ca and read the actual stock thickness and price. Make sure there
   is no "manual quote" flag.
8. **Optional fit coupons** (a cross-lap pair, a tenon + wedge, a seam sample), then tune the clearances.
9. **Order, assemble, finish:** sand off the holding tabs, ease the edges, apply oil.

## 6. Open questions
1. ~~Top seam style~~: **ari-3, 3 boards** (decided). Other variants stay on the site for reference.
2. Heater measurements when it arrives: body W×D×H, side screw-hole positions, screw size/length, cord exit.
