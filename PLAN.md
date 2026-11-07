# Design notes: v2 (in progress)

This is the reference for **v2**, on the `v2` branch. v1 was ordered (git tag `v1-ordered`), assembled
and is in use. The story of how it got here is in the README. Every number below comes from `params.toml`,
and anything I haven't confirmed yet is marked **TODO-verify**.

## What v2 changes
| | v1 (as ordered) | v2 |
|---|---|---|
| Plywood | 18 mm (uMake's "19mm") | **15 mm throughout** |
| Heater | hangs under the deck from 2 cheeks, 4 cheek wedges | **sits in a well in the deck**, in a cradle that hangs by gravity |
| Clear height under the heater | 286 mm | **309 mm** |
| Wedges | 12 + 2 spares | **8 + 2 spares** (the legs still need theirs) |
| Parts, weight, cutting | 26, 15.9 kg, 25.5 m | **22, 12.3 kg, 25.0 m** |
| Top corners | R20 (re-rounded by hand) | rounder, cut in the file (choosing: R60 to R120, or a squircle) |

## Decisions

| Topic | Decision |
|---|---|
| Table | One **86 × 86 cm square** kotatsu. The top is one piece and sits loose on the frame, with the futon in between |
| Frame | A **yagura**: four "+"-shaped corner legs (8 plates) under an H-shaped deck. No aprons, so knees get the room |
| Material | **15 mm Baltic birch for everything**, wedges included (v1: 18 mm). Joints accept 14.1–15.7 mm (TODO-verify the real tolerance, and which uMake menu entry, "15mm" or "16mm", it is) |
| Heater | **PaletteLife 120 V 400 W**, 29 × 29 × 5 cm, the same unit as v1, screwed in at the sides (`docs/heater.md`). I drill its screw holes during assembly, so the files have none. Its top sits flush with the deck top; the manual sets no clearance above the unit |
| Height | About 41 cm: 385 mm frame + 15 mm top + the futon |
| Futon & seats | An 80 × 80 in (203 cm) square futon, four 25 × 25 in square floor pillows, on an 8 ft round rug (`docs/futon.md`). The 3-D view shows all three |
| Budget | Under CAD $1200 all in |

## The parts

- **Leg plates (8, two shapes, 110 × 385 mm).** Each corner crosses an A plate and a B plate in a
  cross-lap 30 mm in from the frame edge. A plates are slotted from the top down, B plates from the floor
  up. The two slot depths add up to 1 mm more than needed, so the floor, not the slots, sets the height.
  - Under the deck, each plate is 110 mm wide: a 22 mm outer finger, the 16 mm slot, a 10 mm shoulder,
    a 50 mm tenon, and a 12 mm inner shoulder. Below a sloped haunch (my sketch), the leg narrows to
    60 mm: two equal 22 mm fingers either side of the slot.
  - The tenon rises through the deck. The outer finger rises higher, all the way to the top, so the top
    rests on the frame's four corners (the "corner posts").
  - Each slot wall has two small bumps that stand 0.5 mm proud ("crush ribs"). Sand them until the joint
    slides together.
  - Plate A has a 1.5 mm arc cut under its foot, so it stands on its two ends and doesn't rock.
- **Deck (1, 780 × 780 mm, H-shaped).** It sits on the plates' shoulders, its top 26 mm below the
  tenon tops. It has 8 mortises (tenon + 0.2 mm each side), the **heater well** in the middle (326 × 300 mm:
  the heater plus both cheeks), and four notches opened to the edge to save weight and cutting, 40 mm of
  wood away from the well. The notch corners away from the legs are rounded (R30).
- **Wedges (10: 8 plus 2 spares, 60 × 18 mm, 1:8 taper).** They lie on the deck and tap sideways through
  each tenon, clamping the deck between shoulder and wedge. This works at any sheet thickness from 14.1 to
  15.7 mm. Gravity can't replace them: with the weight alone (about 20 N a plate) the wobble model gives
  about 9 mm of sway at a 25 N push, because the tenon rocks in its mortise.
- **Heater cradle: 2 cheeks (380 × 70 mm).** The heater screws between their inner faces, 294 mm apart (a
  290 mm heater gets 4 mm of play). The pair drops into the deck's well, and a 40 mm ear at each cheek end
  rests on the deck top: gravity holds it up, and it lifts out for summer. The cheeks cover the heater's
  whole side and rise 20 mm above the deck, under the futon.
- **Top (1, 860 × 860 mm).** The futon lies over the heater as in a traditional open frame (v1 had the
  deck in between).

That's **22 parts, about 12.3 kg, 25.0 m of cutting**. They all fit on one 48 × 96" sheet (39 % used).
Leg plates are laid with the grain running up the leg.

## Assembly (a mallet, plus a screwdriver for the heater)
1. Sand the holding tabs off. Sand the crush ribs until each cross-lap slides together.
2. Cross each pair of plates into a "+" leg: drop the B plate onto the A plate's slot.
3. Stand the four legs up and lower the deck over the 8 tenons.
4. Tap a wedge through each tenon.
5. On the floor or a bench, screw the heater between the two cheeks (drill 2–2.5 mm pilot holes).
6. Lower the heater and cheeks into the deck's well: the ears rest on the deck.
7. Drape the futon over the frame and lay the top on it.

## How it measures up

| Measure | Value |
|---|---|
| Clear height at the middle of each side (deck underside) | 344 mm |
| Clear height under the heater | 309 mm (v1: 286) |
| My 76 × 32 cm cross-legged knee zone: how far it reaches under the top's edge | 40 mm |
| Room between the legs at knee height | 568 mm |
| Sway under a 100 N sideways push (wedges tight) | about 0.8 mm (0.5 at 50 N, 2.0 at 200 N) |
| Play in each tenon, and extra wobble per 0.1 mm a wedge works loose | 0.4 mm, about 1 mm |
| Push 50 mm in from the edge that tips the table / lifts the loose top's far side | about 27 kN / 17 kN, so in practice never (the feet and corner posts sit almost under the edge) |
| Push right at the edge that tips the table / lifts the loose top's far side | about 1380 N / 630 N (v1: 1700 / 770; the table is lighter) |

- **Tipping** is worked out the way EN 12521 and EN 1730 test it: a vertical push in the middle of a side,
  50 mm in from the edge. It assumes the feet don't slide, and the weight includes a guessed 3 kg heater and
  2 kg futon. There's no pass/fail limit, only the report.
- **Wobble** comes from a spring model of each leg-to-deck joint (`kotatsu/stiffness.py`), not FEA. It
  includes the shoulders pressing on the deck, a wedge tapped in to about 300 N, the tenon faces bearing in
  the mortises, and each plate bending. One early discovery: when the tenon ran right to the leg's inner
  edge, every shoulder sat on one side of the wedge, so tapping the wedge in twisted the leg about 9 mm at
  the foot. The inner shoulder (12 mm in v2) fixed that. Re-tap the wedges after the first heating season.
- **Strength** is checked two ways. A 200 N sideways push stresses the legs to about 1.8 MPa. For the top, a
  plate model (`kotatsu/loads.py`) puts it on its corner posts, which can only push up. I checked the model
  against textbook plate results, and it matches within 3–5 %.

| Load on the top | Peak load | Peak stress | Share of strength | Sag |
|---|---|---|---|---|
| Napping hunched over, a 7 kg cat curled up, a laptop | 39 kg | 3.2–3.4 MPa | 9–10 % | 1.6–1.7 mm |
| Flopping down while the cat jumps up mid-table | 75 kg | 5.3 MPa | 15 % | 3.4 mm |
| The cat lands on a corner | 28 kg | 1.0 MPa | 3 % | 0.2 mm |
| Everything piled at one edge | 54 kg | 4.5 MPa | 13 % | 2.1 mm |
| *Beyond normal:* an 80 kg adult sits hard on an edge | 120 kg | 13.6 MPa | 39 % | 6.7 mm |

No corner of the top lifts in any of these cases. The strength figures are rough textbook values
(TODO-verify), and a typical sheet breaks at about 1.5× them. The legs carry at most about 60 kg per
corner, and the wedges and deck don't carry any of the weight from above.

## Budget (CAD)

| Item | Cost |
|---|---|
| Heater (PaletteLife, amazon.ca, delivered) | $258 |
| uMake order: 22 parts, about $346 + tax at the 19 mm rates (v1: $353.33 + tax, `docs/quote.md`). TODO-verify the 15 mm price with a test upload | about $390 |
| Futon: 205 cm square from Etsy, or a queen duvet + cover from Douglas | $185–230 |
| Sandpaper and finishing oil | $30–50 |
| **Total** | **about $870–930** |

## Off-season storage
Everything packs flat inside the top's footprint, in three layers (kotatsu/storage.py packs it by itself).

## Still open
1. **The 15 mm sheet.** Which uMake menu entry is 15 mm Baltic birch ("15mm" or "16mm"), its real
   thickness range (14.1–15.7 mm assumed), and its price per metre of cut. One test upload answers the
   price.
2. **Heater details.** The screws' length (the tips must stay inside the 15 mm cheek), and nothing sticking
   out of the heater's ends past the 300 mm well (cord, knob). With the futon now over the heater, check
   its top stays cool to the touch on high. Look for a cUL, cETL or CSA mark on the rating label.
3. **Top corners.** Choosing between R60, R90, R120 and a squircle (posts 40 to 21 mm in from the edge).
4. **A tipping limit.** If I want one: EN 12521's force table, or a bathroom-scale test on the finished table.
5. **Fit-up.** v1's wedges went in by hand. Watch whether 15 mm tenons and wedges hold as well.

## Finishing (by hand, after the first fit-up)
I'll make it look lighter by hand instead of in the cut files:
- **Top corners:** v2 cuts them round in the file (see Still open). R120 brings the edge within 21 mm of
  where the top rests on the posts, which leaves less room for the bevel below.
- **Top edge: 15° underside bevel, 35 mm wide, leaving a 9 mm rim.** The top rests on the leg plates 41 mm
  in from its edge, so the bevel has to stop short of that. The plies show as stripes about 5 mm wide,
  like contour lines.
- **Legs: round over every exposed vertical edge**, up to a full half-round (R7.5). Keep flat: the top edges
  that carry the top and deck, the tenons and shoulders, the slot walls and the plate faces inside the
  cross-laps, and the wedge holes. Only ease the floor edge (about 2 mm). The leg stress is 1.8 MPa against
  roughly 35 MPa strength, so losing about 10% of the section costs nothing that matters.
- **Pale and matte, like hinoki (白木, "plain wood").** Birch is already close in colour. The aim is to
  keep it from yellowing and looking unfinished. Normal oils (linseed, tung, Danish) turn it
  honey-coloured, so I'm skipping them. Candidates: a water-based flat clear coat, a "raw" hardwax oil
  with a trace of white (e.g. Osmo Polyx-Oil Raw), or a Scandinavian soap finish. Try them on the 2 spare
  wedges first. No essential oils (hinoki scent): the cat will sleep in the warm kotatsu, and many
  essential oils are toxic to cats.
- Before bevelling, pick the cleaner face of the top (fewest patches) and put it up.
- Sand to 180, wipe with a damp cloth to raise the grain, let it dry, then sand 220 (320 on the top).

## Earlier designs
- **v1**, as ordered and built: 18 mm birch, the heater hung under the deck from wedged cheeks, R20
  corners. Git tag `v1-ordered` (and `main` until v2 merges).
- The 120 × 80 top in three boards with decorative seams (dovetails, arrowheads, maple leaves and more),
  and the 120 × 90 and Ø 90 tables: git tag `seams-archive`.
- The solid-sided frame (tapered legs, flared feet) and a splayed-leg yagura: git tag `frame-variants-archive`.
- Options I built and then didn't use, all at git tag `options-archive`:
  - **Deck windows** (closed holes): the notches took the same wood out with about 1 m less cutting, ~$20.
  - **X deck**: diagonal arms through the middle, optionally with a square "shield" over the heater.
    About $4 cheaper and 0.6 kg lighter, with the same joints. But the deck is what holds the futon up
    across the middle, and the X's openings are 22–26 cm wide against 18 cm in the H, each right where
    the knees go. Not worth it.
  - **Leg windows**: replaced by the slim haunched legs.
  - **Lighter-look cuts**: R70 top corners, a curved haunch, feet tapering 10 mm. About $1.50 cheaper and a
    little less tipping margin (1698 → 1476 N at the edge), but hard to see. The hand finishing does more.
  - **Linking modules**: a tongue (or lugs) at each deck notch and a drop-in key, so tables push together
    into a row. About +$17 a module. I didn't like how it looked.
  - **Round top** (Ø 90): $199 shipping and round futons that wouldn't ship here.
