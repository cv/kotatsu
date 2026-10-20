# Design notes

This is the reference for the table as ordered. The story of how it got here is in the README.
Every number below comes from `params.toml`, and anything I haven't confirmed yet is marked
**TODO-verify**.

## Decisions

| Topic | Decision |
|---|---|
| Table | One **86 × 86 cm square** kotatsu. The top is one piece and sits loose on the frame, with the futon in between |
| Frame | A **yagura**: four "+"-shaped corner legs (8 plates) under an H-shaped deck. No aprons, so knees get the room |
| Material | **18 mm Baltic birch for everything**, wedges included. uMake sells it as "19mm". If a wedge wears out, I'll cut a new one |
| Heater | **PaletteLife 120 V 400 W**, 29 × 29 × 5 cm, screwed in at the sides (`docs/heater.md`). I drill its screw holes during assembly, so the files have none |
| Height | About 41 cm: 385 mm frame + 18 mm top + the futon |
| Futon & seats | An 80 × 80 in (203 cm) square futon, four 25 × 25 in square floor pillows, on an 8 ft round rug (`docs/futon.md`). The 3-D view shows all three |
| Budget | Under CAD $1200 all in |

## The parts

- **Leg plates (8, two shapes, 110 × 385 mm).** Each corner crosses an A plate and a B plate in a
  cross-lap 30 mm in from the frame edge. A plates are slotted from the top down, B plates from the floor
  up. The two slot depths add up to 1 mm more than needed, so the floor, not the slots, sets the height.
  - Under the deck, each plate is 110 mm wide: a 20 mm outer finger, the 19.2 mm slot, a 10 mm shoulder,
    a 50 mm tenon, and a 10 mm inner shoulder. Below a sloped haunch (my sketch), the leg narrows to
    60 mm: two equal 20 mm fingers either side of the slot.
  - The tenon rises through the deck. The outer finger rises higher, all the way to the top, so the top
    rests on the frame's four corners (the "corner posts").
  - Each slot wall has two small bumps that stand 0.5 mm proud ("crush ribs"). Sand them until the joint
    slides together.
  - Plate A has a 1.5 mm arc cut under its foot, so it stands on its two ends and doesn't rock.
- **Deck (1, 780 × 780 mm, H-shaped).** It sits on the plates' shoulders, its top 26 mm below the
  tenon tops. It has 8 mortises (tenon + 0.2 mm each side), the cheek-tab slots, and four notches opened
  to the edge to save weight and cutting. The notch corners away from the legs are rounded (R30).
- **Wedges (14: 12 plus 2 spares, 60 × 18 mm, 1:8 taper).** One shape does both jobs. They lie on the deck
  and tap sideways through each tenon and cheek tab, clamping the deck between shoulder and wedge. This
  works at any sheet thickness from 17.0 to 18.9 mm.
- **Heater cheeks (2, 372 × 94 mm).** These hang from the deck by two tabs each, held by wedges. The heater
  screws into their inner faces. They sit 294 mm apart, which gives a 290 mm heater 4 mm of play.
- **Top (1, 860 × 860 mm).** Solid over the heater, so the deck and top shield the futon from it.

That's **26 parts, about 16 kg, 25.5 m of cutting**. They all fit on one 48 × 96" sheet (43 % used).
Leg plates are laid with the grain running up the leg.

## Assembly (a mallet, plus a screwdriver for the heater)
1. Sand the holding tabs off. Sand the crush ribs until each cross-lap slides together.
2. Cross each pair of plates into a "+" leg: drop the B plate onto the A plate's slot.
3. Stand the four legs up and lower the deck over the 8 tenons.
4. Tap a wedge through each tenon.
5. Hang the cheeks (tabs up through the deck, a wedge in each), then screw the heater between them.
   Drill 2–2.5 mm pilot holes.
6. Drape the futon over the frame and lay the top on it.

## How it measures up

| Measure | Value |
|---|---|
| Clear height at the middle of each side (deck underside) | 341 mm |
| Clear height under the heater | 286 mm |
| My 76 × 32 cm cross-legged knee zone: how far it reaches under the top's edge | 40 mm |
| Room between the legs at knee height | 568 mm |
| Sway under a 100 N sideways push (wedges tight) | about 0.9 mm (0.5 at 50 N, 2.2 at 200 N) |
| Play in each tenon, and extra wobble per 0.1 mm a wedge works loose | 0.4 mm, about 1 mm |
| Push 50 mm in from the edge that tips the table / lifts the loose top's far side | about 48 kN / 39 kN, so in practice never (the feet and corner posts sit almost under the edge) |
| Push right at the edge that tips the table / lifts the loose top's far side | about 1700 N / 770 N |

- **Tipping** is worked out the way EN 12521 and EN 1730 test it: a vertical push in the middle of a side,
  50 mm in from the edge. It assumes the feet don't slide, and the weight includes a guessed 3 kg heater and
  2 kg futon. There's no pass/fail limit, only the report.
- **Wobble** comes from a spring model of each leg-to-deck joint (`kotatsu/stiffness.py`), not FEA. It
  includes the shoulders pressing on the deck, a wedge tapped in to about 300 N, the tenon faces bearing in
  the mortises, and each plate bending. One early discovery: when the tenon ran right to the leg's inner
  edge, every shoulder sat on one side of the wedge, so tapping the wedge in twisted the leg about 9 mm at
  the foot. The 10 mm inner shoulder fixed that. Re-tap the wedges after the first heating season.
- **Strength** is checked two ways. A 200 N sideways push stresses the legs to about 1.7 MPa. For the top, a
  plate model (`kotatsu/loads.py`) puts it on its corner posts, which can only push up. I checked the model
  against textbook plate results, and it matches within 3–5 %.

| Load on the top | Peak load | Peak stress | Share of strength | Sag |
|---|---|---|---|---|
| Napping hunched over, a 7 kg cat curled up, a laptop | 39 kg | 2.2–2.4 MPa | 6–7 % | 1.0 mm |
| Flopping down while the cat jumps up mid-table | 75 kg | 3.7 MPa | 11 % | 2.0 mm |
| The cat lands on a corner | 28 kg | 0.7 MPa | 2 % | 0.1 mm |
| Everything piled at one edge | 54 kg | 3.1 MPa | 9 % | 1.2 mm |
| *Beyond normal:* an 80 kg adult sits hard on an edge | 120 kg | 9.4 MPa | 27 % | 3.9 mm |

No corner of the top lifts in any of these cases. The strength figures are rough textbook values
(TODO-verify), and a typical sheet breaks at about 1.5× them. The legs carry at most about 60 kg per
corner, and the wedges and deck don't carry any of the weight from above.

## Budget (CAD)

| Item | Cost |
|---|---|
| Heater (PaletteLife, amazon.ca, delivered) | $258 |
| uMake order: 26 parts $353.33 + tax $42.40, free shipping (`docs/quote.md`) | $396 |
| Futon: 205 cm square from Etsy, or a queen duvet + cover from Douglas | $185–230 |
| Sandpaper and finishing oil | $30–50 |
| **Total** | **about $870–930** |

## Still open
1. **Sheet thickness.** uMake's "19mm" could measure 19.0 mm or more, which would make the 19.2 mm slots
   tight. The crush ribs and wedges give some room, and a little sanding gives the rest.
2. **Heater details.** Measure the exact width across the screw tabs and the screw length (the tips must
   stay inside the 18 mm cheek). Also check the manual's clearances and the rating label for a
   cUL, cETL or CSA mark.
3. **A tipping limit.** If I want one: EN 12521's force table, or a bathroom-scale test on the finished table.
4. **Fit-up.** The first assembly will show how the tenons and wedges really fit. Then finish it: ease the
   edges and oil it. I'll make it look lighter by hand instead of in the cut files:
   - **Top corners: re-round to R50.** Bigger looks nicer, but R70 brings the edge within 29 mm of where
     the top rests on the legs, and that leaves no room for the bevel.
   - **Top edge: 15° underside bevel, 35 mm wide, leaving a 9 mm rim.** The top rests on the leg plates
     41 mm in from its edge, so the bevel has to stop short of that. The plies show as stripes about
     5 mm wide, like contour lines.
   - **Legs: round over every exposed vertical edge**, up to a full half-round (R9). Keep flat: the top
     edges that carry the top and deck, the tenons and shoulders, the slot walls and the plate faces
     inside the cross-laps, and the wedge holes. Only ease the floor edge (about 2 mm). The leg stress is
     1.7 MPa against roughly 35 MPa strength, so losing about 10% of the section costs nothing that
     matters.
   - **Finish: pale and matte, like hinoki (白木, "plain wood").** Birch is already close in colour.
     The aim is to keep it from yellowing and to keep it looking unfinished. Normal oils (linseed, tung,
     Danish) turn it honey-coloured, so I'm skipping them. Candidates:
     a water-based flat clear coat, a "raw" hardwax oil with a trace of white (e.g. Osmo Polyx-Oil Raw),
     or a Scandinavian soap finish. Try them on the 2 spare wedges first. No essential oils (hinoki
     scent): the cat will sleep in the warm kotatsu, and many essential oils are toxic to cats.
   - Before bevelling, pick the cleaner face of the top (fewest patches) and put it up.
   - Sand to 180, wipe with a damp cloth to raise the grain, let it dry, then sand 220 (320 on the top).
5. **Lighter-look cuts: mocked up, not used.** Bigger top corners (R70), a curved haunch on the legs,
   and feet tapering 10 mm on plate A. Together: about $1.50 cheaper, 0.1 kg lighter, lower leg stress,
   a little less tipping margin (1698 → 1476 N at the edge). The order had already gone in, and the
   difference was hard to see, so they stay as options in the code (off).

## Earlier designs
- The 120 × 80 top in three boards with decorative seams (dovetails, arrowheads, maple leaves and more),
  and the 120 × 90 and Ø 90 tables: git tag `seams-archive`.
- The solid-sided frame (tapered legs, flared feet) and a splayed-leg yagura: git tag `frame-variants-archive`.
