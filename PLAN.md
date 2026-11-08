# Design notes: v2 (in progress)

This is the reference for **v2**, on the `v2` branch. v1 was ordered (git tag `v1-ordered`), assembled
and is in use. The story of how it got here is in the README. Every number below comes from `params.toml`,
and anything I haven't confirmed yet is marked **TODO-verify**.

## What v2 changes
| | v1 (as ordered) | v2 |
|---|---|---|
| Plywood | 18 mm (uMake's "19mm") | **15 mm throughout** |
| Heater | hangs under the deck from 2 cheeks, 4 cheek wedges | **sits in a well in the deck**, in a cradle that hangs by gravity |
| Clear height under the heater | 286 mm | **313 mm** |
| Deck | H-shaped (four notches) | **X-shaped**: corner pads, a ring round the heater, 45° arms |
| Leg joints | 8 tenons, a wedge in each | **one wedge per leg**: 4 tenons, the other plate held by gravity |
| Wedges | 12 + 2 spares | **4 + 2 spares** |
| Top | square, R20 corners (re-rounded by hand) | **squircle** (n = 10), cut in the file; feet and deck rounder to match |
| Parts, weight, cutting | 26, 15.9 kg, 25.5 m | **18, 11.6 kg, 22.7 m** |
| Chairs | none | a bought zaisu (owner, 2026-11). Two plywood ones were designed, checked and quoted (+$173), then archived (tag `zaisu-archive`) |

## Decisions

| Topic | Decision |
|---|---|
| Table | One **86 × 86 cm squircle** kotatsu. The top is one piece and sits loose on the frame, with the futon in between |
| Show top | Researched and dropped (owner 2026-11): solid pale wood, stone, a copper skin and a ¼" low-iron glass sheet over the birch (previewed in 3-D: too glossy) were all priced or checked with the FEA (`docs/research.md`; the quote pack is at git tag `show-top-archive`). The pale birch look of v1 is what I want: the top stays uMake birch, finished by hand with a satin hardwax oil (owner: "the simple and honest look of the waxed satin birch still wins at the price point") |
| Frame | A **yagura**: four "+"-shaped corner legs (8 plates) under an X-shaped deck. No aprons, so knees get the room |
| Material | **15 mm Baltic birch for everything**, wedges included (v1: 18 mm). Joints accept 14.1–15.7 mm (TODO-verify the real tolerance, and which uMake menu entry, "15mm" or "16mm", it is) |
| Heater | **PaletteLife 120 V 400 W**, 29 × 29 × 5 cm, the same unit as v1, screwed in at the sides (`docs/heater.md`). I drill its screw holes during assembly, so the files have none. Its top sits 4 mm above the deck top, 22 mm under the tenon tops; the manual sets no clearance above the unit |
| Height | About 41 cm: 385 mm frame + 15 mm top + the futon |
| Futon & seats | An 80 × 80 in (203 cm) square futon on an 8 ft round rug (`docs/futon.md`), four 25 × 25 in floor pillows, and a bought, adjustable zaisu (about $70). On a zaisu I sit **legs forward**: cross-legged on a chair, my knees wouldn't fit under the top with any cushion worth having. The 3-D view shows the futon, rug and pillows |
| Budget | Under CAD $1200 all in |

## The parts

- **Leg plates (8, two shapes, 110 × 385 mm).** Each corner crosses an A plate and a B plate in a
  cross-lap 30 mm in from the frame edge. A plates are slotted from the top down, B plates from the floor
  up. The two slot depths add up to 1 mm more than needed, so the floor, not the slots, sets the height.
  - Under the deck, each plate is 110 mm wide: a 22 mm outer finger, the 16 mm slot, a 10 mm shoulder,
    a 50 mm tenon, and a 12 mm inner shoulder. Below a sloped haunch (my sketch), the leg narrows to
    70 mm (v2, owner 2026-11; was 60): a 22 mm outer finger and a 32 mm inner one either side of the slot.
    The haunch is one S-curve of squircle corners. Below the joints, from 150 mm down, the inner edge tapers
    softly to 56 mm at the floor (owner, 2026-11: for looks), on a long squircle bend that runs into the
    haunch's 60 mm S-curve: the inner edge is one continuous curve from the shoulder to the foot. FEA: plate A's
    worst is now the slot root at 80 % (the haunch 57 %; it was 81 % at the haunch with straight legs).
  - Only the A plate has a tenon (v2): it rises through the deck and takes the corner's one wedge. The B
    plate's top edge is all shoulder, under the deck. On both, the outer finger rises all the way to the
    top, so the top rests on the frame's four corners (the "corner posts").
  - A runs along x at two diagonal corners and along y at the other two, so a push either way meets two
    wedged plates. The B plate is held by gravity, trapped between the floor and the wedged-down deck, and
    hangs on A's cross-lap when the frame is lifted.
  - The feet are rounded R12; the top corners stay R6, because the 12 mm inner shoulder bears there.
  - Each slot wall has two small bumps that stand 0.5 mm proud ("crush ribs"). Sand them until the joint
    slides together.
  - Plate A has a 1.5 mm arc cut under its foot, so it stands on its two ends and doesn't rock.
- **Deck (1, 780 × 780 mm, X-shaped).** It sits on the plates' shoulders, its top 26 mm below the
  tenon tops. Each corner's pad holds only what needs wood: 20 mm round the mortise (tenon + 0.2 mm each
  side), 5 mm past the lying wedge and past both plates' top edges, which bear on the deck. Nothing
  outside the B plate (owner, 2026-11). A ring round the **heater well** (326 × 300 mm: the heater plus
  both cheeks) is 40 mm wide beside the cheeks and runs 15 mm past their ears. Four 36 mm arms along the
  diagonals join them, with R90 fillets at the ring, R40 at the pads and R12 corners outside. 1.33 kg,
  against 2.1 kg for the H.
  - The deck holds the futon up across the middle. Its openings are as big as the H's were (188 mm deep
    at mid-side, where the knees go); the extra open area is near the corners.
  - The arms: a 300 N hand pressing on the ring, plus the heater, as cantilevers at 45° to the grain on
    the thinnest stock (173 mm free): 12 MPa, 40 % of the rough strength, 3.7 mm of give
- **Wedges (6: 4 plus 2 spares, 60 × 18 mm, 1:8 taper).** They lie on the deck and tap sideways through
  each A tenon, clamping the deck between shoulder and wedge. This works at any sheet thickness from 14.1
  to 15.7 mm. Gravity can't replace all of them: with the weight alone (about 20 N a plate) the wobble
  model gives about 9 mm of sway at a 25 N push, because the tenon rocks in its mortise.
- **Heater cradle: 2 cheeks (380 × 70 mm).** The heater screws between their inner faces, 294 mm apart (a
  290 mm heater gets 4 mm of play). The pair drops into the deck's well, and a 40 mm ear at each cheek end
  rests on the deck top: gravity holds it up, and it lifts out for summer. The cheeks cover the heater's
  whole side and rise 24 mm above the deck, 2 mm under the tenon tops, so even on the thickest deck they never
  stand proud and carry the top. The heater's top sits 4 mm above the deck, with 20 mm of air above it (owner 2026-11:
  raised 4 mm, was flush).
- **Top (1, 860 × 860 mm), a squircle**: |x/a|¹⁰ + |y/a|¹⁰ = 1, a curve that fades into the edges instead of
  a radius that starts abruptly. The corner posts stay 28 mm inside its edge (v1: 40). The futon lies
  over the heater as in a traditional open frame (v1 had the deck in between).

That's **18 parts, about 11.6 kg, 22.7 m of cutting**. They fit on one 48 × 96" sheet. uMake lays out
the sheets itself and prices per part, so this only matters for my estimate.

## Assembly (a mallet, plus a screwdriver for the heater)
1. Sand the holding tabs off. Sand the crush ribs until each cross-lap slides together.
2. Cross each pair of plates into a "+" leg: drop the B plate (no tenon) onto the A plate's slot.
3. Stand the four legs up, the A plates along x at two diagonal corners and along y at the other two,
   and lower the deck over the 4 tenons.
4. Tap a wedge through each tenon.
5. On the floor or a bench, screw the heater between the two cheeks (drill 2–2.5 mm pilot holes).
6. Lower the heater and cheeks into the deck's well: the ears rest on the deck.
7. Drape the futon over the frame and lay the top on it.

## How it measures up

| Measure | Value |
|---|---|
| Clear height at the middle of each side (deck underside) | 344 mm |
| Clear height under the heater | 313 mm (v1: 286) |
| My 76 × 32 cm cross-legged knee zone (on the bare floor): how far it reaches under the top's edge | 40 mm |
| On a zaisu, legs forward: room above my thighs under the deck / my feet under the heater (seat 100 mm high when sat on, TODO-verify) | 69 mm / 74 mm (a typical 160 mm thigh, TODO-verify) |
| My knee room on the floor pillows, against v1 (where it's fine, owner 2026-11) | the same or more: frame top 385 / 385 mm, deck underside 344 / 341, heater 313 / 286, reach 40 / 40, between the legs 570 / 568 |
| Cross-legged on a zaisu: knee room under the top's edge (385 mm, the futon squeezed over the knees) | none to spare once the seat's height is added, so I sit legs forward |
| Room between the legs at knee height | 568 mm |
| Sway under a 100 N sideways push (wedges tight, gravity-held plates counted as nothing) | about 2.0 mm (0.8 at 50 N, 4.5 at 200 N; v1: 0.9) |
| Play in each tenon, and extra wobble per 0.1 mm a wedge works loose | 0.4 mm, about 1 mm |
| Push 50 mm in from the edge that tips the table / lifts the loose top's far side | never, in the model (the feet and corner posts sit almost under the edge) |
| Push right at the edge that tips the table / lifts the loose top's far side | about 1320 N / 710 N (v1: 1700 / 770; the table is lighter) |

- **Tipping** is worked out the way EN 12521 and EN 1730 test it: a vertical push in the middle of a side,
  50 mm in from the edge. It assumes the feet don't slide, and the weight includes a guessed 3 kg heater and
  2 kg futon. There's no pass/fail limit, only the report.
- **Wobble** comes from a spring model of each leg-to-deck joint (`kotatsu/stiffness.py`), not FEA. It
  includes the shoulders pressing on the deck, a wedge tapped in to about 300 N, the tenon faces bearing in
  the mortises, and each plate bending. One early discovery: when the tenon ran right to the leg's inner
  edge, every shoulder sat on one side of the wedge, so tapping the wedge in twisted the leg about 9 mm at
  the foot. The inner shoulder (12 mm in v2) fixed that. Re-tap the wedges after the first heating season.
  v2 wedges one plate per leg, and the model counts the other (held by gravity between the floor and the
  deck) as nothing, so the real table should be stiffer than the figures above.
- **Strength** is checked two ways. A 200 N sideways push stresses the legs to about 3.6 MPa (two wedged plates take it). For the top, a
  plate model (`kotatsu/loads.py`) puts it on its corner posts, which can only push up. I checked the model
  against textbook plate results, and it matches within 3–5 %. v2's top rests on 8 posts and the 4 A
  tenons (v1: 8 tenons).

| Load on the top | Peak load | Peak stress | Share of strength | Sag |
|---|---|---|---|---|
| Napping hunched over, a 7 kg cat curled up, a laptop | 39 kg | 3.4–3.6 MPa | 10 % | 1.9–2.0 mm |
| Flopping down while the cat jumps up mid-table | 75 kg | 5.7 MPa | 16 % | 3.6 mm |
| The cat lands on a corner | 28 kg | 1.0 MPa | 3 % | 0.2 mm |
| Everything piled at one edge | 54 kg | 4.9 MPa | 14 % | 2.9 mm |
| *Beyond normal:* an 80 kg adult sits hard on an edge | 120 kg | 14.4 MPa | 41 % | 8.7 mm |

No corner of the top lifts in any of these cases. The strength figures are rough textbook values
(TODO-verify), and a typical sheet breaks at about 1.5× them. The legs carry at most about 60 kg per
corner, and the wedges and deck don't carry any of the weight from above.

**Finite-element check ([docs/fea.md](docs/fea.md)).** `kotatsu/fea.py` re-checks the
three parts with real outlines on 14.1 mm stock:
- **Top.** The grillage above is confirmed within 10 %, slightly on the safe side.
- **X deck.** Under a 300 N hand the deck uses up to about 68 % of its strength at the arm fillets with the
  wedges tight, not the 40 % of the cantilever estimate (the 45° arms are softer and weaker than assumed). With
  slack wedges it is overstressed.
- **Legs (fixed: `leg_narrow` 70, owner 2026-11).** At 60 mm a 200 N sideways push overstressed plate A
  (Tsai-Hill 1.6): the lumped model bends A's slotted upper half as one section, but it is two separate
  fingers, and sway was about 12 mm, not 4.5. At 70 mm the worst zone is the wedge hole at 87 %, the
  haunch 81 %, the slot root 77 %, and sway 7.2 mm (the lumped model still says 3.7: trust the FE).
  It costs about 0.25 kg and 20 mm of room between the legs at shin height (knee height is unchanged).
  `tests/test_fea.py` now requires it. TODO-verify the strengths.


## Budget (CAD)

| Item | Cost |
|---|---|
| Heater (PaletteLife, amazon.ca, delivered) | $258 |
| uMake: 18 parts at 15mm, **quoted $328.40 + $39.41 tax, free shipping** (one 91 × 91 × 14 cm box; the final design, 2026-11, not ordered, `docs/quote.md`). If finalization adds what it did for v1 (~15 %): about $423 | $368–423 |
| Futon: 205 cm square from Etsy, or a queen duvet + cover from Douglas | $185–230 |
| Sandpaper and finishing oil | $30–50 |
| A zaisu (bought, adjustable: about $70, free shipping) + tax | $78 |
| **Total** | **about $920–1040** |

## Off-season storage
Everything packs flat inside the top's footprint, in three layers, a stack about 47 mm tall (kotatsu/storage.py
packs it by itself, flipping parts over where that helps).

## The design space (`make optimize`, 2026-11)
`kotatsu/optimize.py` samples 384 designs over 8 knobs (`[optimize.knobs]`: the deck's arm width, fillets and ring,
the legs' lower width, haunch, taper and foot), keeps the ones that cut, box and ship free with the knees
reaching under the top, then runs the FEA on the 48 most promising (plate A under the 200 N shove, plate B, the
deck's hard hand cases). What it found:
- **Price is flat:** every design costs $326.9–328.0. uMake prices each part's bounding box, and none of these
  knobs moves a box. Weight barely moves either (11.1–11.7 kg).
- **The real trade is leg room against stiffness and strength,** and the lower-leg width drives it: from 60 to 90 mm
  it takes sway down 4.4 mm and the worst share of strength down 85 points, for 47 mm less room between the legs
  where shins and thighs pass (`comfort.legroom`, new: the knee-height `shin_w` couldn't see it).
- **The current design is on the front:** it has the most leg room (637 mm) of any design that passes the FEA.
- Near-free gains: a wider foot (less taper) buys strength for almost no room; a higher haunch top buys room.
  For the same money, about 595 mm of room gives 5.7 mm of sway and 72 % (now 7.1 mm, 80 %).
- **With economics and looks as the goals** (owner: equally important once the functional limits hold; looks
  measured as the legs' average visible width below the deck, `looks.leg_width`): the current legs are 63.4 mm.
  The slimmest that passes is 61.9 mm (−2 %), at 88 % of strength and $0.05 more; the cheapest saves $0.59 with legs
  19 % wider. So on these knobs the design is already at the edge for looks, and economics can't be traded at all.

## Price: what's left to save
Little: the design is at uMake's price floor (`docs/quote.md`, "What can still be saved"). About 40 % of the bill
doesn't depend on the design, the remaining cut is all required, and wood inside a part's box is free. A solid
deck would save about $4 but costs 3.8 kg and the knee room in the X's openings, so the X stays. The bigger
unknown is uMake's finalization: v1's receipt was **$405.83 + tax = $454.53**, $52.50 more than the cart's
$353.33 (TODO-verify what was added; if it repeats, v2's $328.53 becomes about $378 + tax).

## Still open
1. **The 15 mm sheet.** Order uMake's "15mm" Baltic birch (its "16mm" is probably 5/8", too thick). Its
   real thickness range is assumed at 14.1–15.7 mm: TODO-verify. The price is settled (test quote, `docs/quote.md`).
2. **Heater details.** The screws' length (the tips must stay inside the 15 mm cheek), and nothing sticking
   out of the heater's ends past the 300 mm well (cord, knob). With the futon now over the heater, check
   its top stays cool to the touch on high (owner, 2026-11: 40 °C on v1, the same heater: fine). Look for a cUL, cETL or CSA mark on the rating label.
3. **The gravity-held plates.** Check the B plates don't rattle in the cross-laps once the table is up;
   the crush ribs should hold them snug.
4. **A tipping limit.** If I want one: EN 12521's force table, or a bathroom-scale test on the finished table.
5. **Fit-up.** v1's wedges went in by hand. Watch whether 15 mm tenons and wedges hold as well.
6. **Zaisu fit.** Measure the bought zaisu's seat (sat on, padding included: assumed 100 mm, `comfort.chair_seat_h`)
   and me sitting legs forward on the bare floor (top of a thigh just above the knee, top of the toes).

## Finishing (by hand, after the first fit-up)
The pale birch look of v1 is the goal (owner, 2026-11). All by hand, at no cost to the order:
- **Pick the cleaner face of the top** (fewest patches) and put it up, before anything else.
- **Undercut the top's edge:** a 15° bevel on the underside, about 35 mm wide, leaving a 9 mm rim, so from the
  side the 15 mm top reads thinner and its plies show as stripes. At the corners the posts sit 20 mm in from
  the edge, so narrow the bevel to about 15 mm there.
- **Round every visible edge a little** (2–3 mm, sandpaper on a block). Crisp, even edges and a good finish
  matter more than shape.
- **Legs: ease the exposed vertical edges to about 3 mm, no more.** v2's legs work hard (the FEA puts the
  bottom of plate A's slot at 80 % of its strength under a hard 200 N shove), so the full half-rounds once
  planned for v1 would cost real strength. Keep sharp and flat: the top edges that carry the top and deck,
  the tenons and shoulders, the slot walls and the faces inside the cross-laps, and the wedge holes. Ease
  the floor edge about 2 mm.
- **Sand** to 180, wipe with a damp cloth to raise the grain, let it dry, then 220 (320 on the top).
- **Oil:** Osmo Polyx-Oil Clear Satin (3032), which I already have. It's a hardwax oil, so it warms birch only
  a little (normal linseed, tung or Danish oils turn it honey-coloured). Try it on the 2 spare wedges first;
  if it looks too warm, Osmo Polyx-Oil Raw (3044) keeps it paler. Two thin coats, wiping off the excess,
  overnight between them, on **both faces and the edges equally**, so the top can't cup over the heater.
- No essential oils (hinoki scent): the cat sleeps in the warm kotatsu, and many are toxic to cats.

## Earlier designs
- **v1**, as ordered and built: 18 mm birch, the heater hung under the deck from wedged cheeks, R20
  corners. Git tag `v1-ordered` (and `main` until v2 merges).
- **v2's H deck** (four notches round the heater well, a wedge in all 8 tenons): commit ced3313 on the v2 branch.
- The 120 × 80 top in three boards with decorative seams (dovetails, arrowheads, maple leaves and more),
  and the 120 × 90 and Ø 90 tables: git tag `seams-archive`.
- The solid-sided frame (tapered legs, flared feet) and a splayed-leg yagura: git tag `frame-variants-archive`.
- Options I built and then didn't use, all at git tag `options-archive`:
  - **Deck windows** (closed holes): the notches took the same wood out with about 1 m less cutting, ~$20.
  - **X deck** (v1's): diagonal arms through the middle, optionally with a square "shield" over the heater.
    About $4 cheaper and 0.6 kg lighter, with the same joints. But the deck is what holds the futon up
    across the middle, and the X's openings are 22–26 cm wide against 18 cm in the H, each right where
    the knees go. Not worth it then. v2's X keeps a ring round the heater, which fixes that.
  - **Leg windows**: replaced by the slim haunched legs.
  - **Lighter-look cuts**: R70 top corners, a curved haunch, feet tapering 10 mm. About $1.50 cheaper and a
    little less tipping margin (1698 → 1476 N at the edge), but hard to see. The hand finishing does more.
  - **Linking modules**: a tongue (or lugs) at each deck notch and a drop-in key, so tables push together
    into a row. About +$17 a module. I didn't like how it looked.
  - **Round top** (Ø 90): $199 shipping and round futons that wouldn't ship here.
