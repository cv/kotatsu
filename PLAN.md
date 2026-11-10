# Design notes: v2 (in progress)

This is the reference for **v2**, the design on `main` (designed and quoted, not ordered yet). v1 was ordered (git tag `v1-ordered`), assembled
and is in use. The story of how it got here is in the README. Every number below comes from `params.toml`,
and anything I haven't confirmed yet is marked **TODO-verify**.

## What v2 changes
| | v1 (as ordered) | v2 |
|---|---|---|
| Plywood | 18 mm (uMake's "19mm") | **15 mm throughout** |
| Heater | hangs under the deck from 2 cheeks, 4 cheek wedges | **sits in a well in the deck**, in a cradle that hangs by gravity |
| Clear height under the heater | 286 mm | **304 mm** |
| Deck | H-shaped (four notches) | **X-shaped**: corner pads, a ring round the heater, 45° arms |
| Legs | 8 plates in four "+" legs, 8 tenons, a wedge in each | **four diagonal legs**: one plate a corner on its diagonal, a crosspiece in its head, one tenon and wedge each |
| Wedges | 12 + 2 spares | **4 + 2 spares** |
| Top | square, R20 corners (re-rounded by hand) | **squircle** (n = 8), cut in the file; feet and deck rounder to match |
| Parts, weight, cutting | 26, 15.9 kg, 25.5 m | **18, 10.4 kg, 16.8 m** |
| Chairs | none | a bought zaisu (owner, 2026-11). Two plywood ones were designed, checked and quoted (+$173), then archived (tag `zaisu-archive`) |

## Decisions

| Topic | Decision |
|---|---|
| Table | One **86 × 86 cm squircle** kotatsu. The top is one piece and sits loose on the frame, with the futon in between |
| Show top | Researched and dropped (owner 2026-11): solid pale wood, stone, a copper skin and a ¼" low-iron glass sheet over the birch (previewed in 3-D: too glossy) were all priced or checked with the FEA (`docs/research.md`; the quote pack is at git tag `show-top-archive`). The pale birch look of v1 is what I want: the top stays uMake birch, finished by hand with a satin hardwax oil (owner: "the simple and honest look of the waxed satin birch still wins at the price point") |
| Frame | A **yagura**: four diagonal legs (one plate a corner, on the diagonal, owner 2026-11; the "+" legs are tag `plus-legs-archive`) under an X-shaped deck. No aprons, so knees get the room |
| Material | **15 mm Baltic birch for everything**, wedges included (v1: 18 mm). Joints accept 14.1–15.7 mm (TODO-verify the real tolerance, and which uMake menu entry, "15mm" or "16mm", it is) |
| Heater | **PaletteLife 120 V 400 W**, 29 × 29 × 5 cm, the same unit as v1, screwed in at the sides (`docs/heater.md`). I drill its screw holes during assembly, so the files have none. Its control panel (power inlet, switch, knob) is on one end, near the grille: the heater sits low enough that the panel clears the deck's underside by 5 mm, so the knob and the plug stick out under the deck's ring (owner 2026-11; the panel's height read off a photo, TODO-verify). Its screws are 10-15 mm from its top, so the cheeks are short |
| Height | About 41 cm: 385 mm frame + 15 mm top + the futon |
| Futon & seats | An oversized king quilt, 120 × 120 in (305 cm), over the frame (owner 2026-11: it works really well; I'd planned an 80 × 80 in futon). I fold and tuck it in so it doesn't spread so much: it covers about half of each floor pillow (the 3-D view draws it so). On an 8 ft round rug (`docs/futon.md`), four 25 × 25 in floor pillows, and a bought, adjustable zaisu (about $70). On a zaisu I sit **legs forward**: cross-legged on a chair, my knees wouldn't fit under the top with any cushion worth having. The 3-D view shows the futon, rug and pillows |
| Budget | Under CAD $1200 all in |

## The parts

- **Leg plates (4, 169 × 385 mm), one on each corner's diagonal**, its outer end at the frame corner (owner 2026-11).
  - Under the deck each plate is 140 mm wide along the diagonal: the post, the 16 mm head slot centred 60 mm
    in from the corner, a 10 mm shoulder, the 50 mm tenon and a 12 mm inner shoulder. Below the haunch (full width
    down to 305 mm, then one S-curve 50 mm long) it narrows to 56 mm, and from 220 mm down tapers softly to 46 mm at the
    floor. **The kick** (owner 2026-11, "more japanese-ish"): below 290 mm the whole lower leg sweeps outwards, both
    edges together, reaching 30 mm past the frame corner at the floor (`yagura.leg_kick`). The feet stand about 24 mm
    past the top's edge, and tipping the table at an edge takes about 4.5 kN. Slimmer than this fails: 56 mm with the
    old 30 mm haunch puts the slot root at 106 % (the longer haunch moves its bend away from the slot); feet under
    46 mm can't be cut.
  - **The crosspiece (4, 90 × 25.5 mm, its underside arched up to 14 mm at the ends: each half is a little
    cantilever)** drops into the plate's head slot, across the plate. The slot is only
    25 mm deep and round-bottomed: the crosspiece's square edges sit on the arc, and its top comes out flush
    with the plate's shoulders. The deck bears on both, which gives the joint a 90 mm base against twisting
    (one plate alone would rock open at about 32 N). The crosspiece is cut 0.5 mm proud: sand its top edge at
    the fit-up until the deck sits on it and on the shoulders together.
  - The tenon rises through a mortise on the diagonal and takes the corner's one wedge, lying on the deck
    across the arm. Above the deck the post rises to the top. Its outer edge sweeps in in one long, gentle curve (owner 2026-11), leaving
    from the foot, one curve the whole height of the leg (11 mm in at the deck's underside), reaching 14 mm in at the top, so the flat end the top rests on stays 18+ mm inside the squircle top's
    edge (on the diagonal the edge comes closest).
  - Each head-slot wall has one small bump ("crush ribs"), 0.95 mm proud: the slot is 16.0 mm (the thickest
    sheet + 0.3) and 14.1 mm at the bumps, the thinnest sheet, so the crosspiece is snug on any stock (v2 recs; was
    0.5 mm, 15.0 at the bumps, with 0.9 mm of play at 14.1). On thicker stock sand the bumps, or the crosspiece's
    faces, at the fit-up: (t − 14.1) / 2 a side, 0.8 mm at 15.7 (owner: up to about 1 mm is fine, `fit.fit_sand`). The foot has a 1.5 mm arc cut under it, so the plate stands on its two ends and doesn't rock.
  - How I shaped the head, with the leg FEA under a 200 N shove: a 60 mm crosspiece needed the haunch at
    270 mm and cost ~90 mm of room at thigh height; at 36 mm the slot's bottom landed in the haunch (183 %);
    25 mm with the haunch from 305 mm gave 84-95 % with dogbones in the slot, and **74-75 %** with the round
    bottom.
- **Deck (1, 769 × 769 mm, X-shaped, on the 780 mm frame).** It sits on the plates' shoulders and the crosspieces, its top
  26 mm below the tenon tops. Each corner's pad holds only what needs wood: 20 mm round the mortise (tenon +
  0.2 mm each side), 5 mm past the lying wedge, the plate's top edge and the crosspiece's (owner, 2026-11), so the
  pads are small crosses at the ends of the arms; the deck stops square across the diagonal beside each post. A ring round the **heater well** (326 × 300 mm: the heater plus
  both cheeks) is 40 mm wide beside the cheeks and runs 15 mm past their ears. Four 36 mm arms along the
  diagonals join them, with R150 fillets at the ring (owner 2026-11: smoother, and stronger) and R12 corners outside. Each corner pad is
  one convex outline round what needs wood, flaring out of its arm on an R300 fillet (only there), and its far
  corners, beside the post, are rounded R10 (owner 2026-11: nothing left to fight with sandpaper). 1.27 kg,
  against 2.1 kg for the H.
  - The deck holds the futon up across the middle. Its openings are as big as the H's were (188 mm deep
    at mid-side, where the knees go); the extra open area is near the corners.
  - The arms: a 300 N hand pressing on the ring, plus the heater, as cantilevers at 45° to the grain on
    the thinnest stock (116 mm free): 8 MPa, 27 % of the rough strength, 1.1 mm of give. In the FEA it's more
    (below): 60 %.
- **Wedges (6: 4 plus 2 spares, 60 × 18 mm, 1:8 taper).** They lie on the deck across the arm and tap
  through each tenon, clamping the deck between the shoulders (and the crosspiece) and the wedge. This works at any sheet thickness from 14.1
  to 15.7 mm. Gravity can't replace all of them: with the weight alone (about 20 N a plate) there's
  about 9 mm of sway at a 25 N push in the wobble model, because the tenon rocks in its mortise.
- **Heater cradle: 2 cheeks (380 × 46 mm).** The heater screws between their inner faces, 294 mm apart (a
  290 mm heater gets 4 mm of play). The pair drops into the deck's well, and a 40 mm ear at each cheek end
  rests on the deck top: gravity holds it up, and it lifts out for summer. The cheeks cover the heater's
  screw line and 12.5 mm of wood below it, and rise 16 mm above the deck (the ears stay a sheet thick),
  under the futon: 46 mm tall (owner 2026-11: the screws sit 10-15 mm from the heater's top; the cheeks were 60). The
  heater hangs with its top 5 mm under the deck top, low enough that its control panel, on one end, clears the
  deck's underside by 5 mm: the knob and the plug stick out under the deck's ring, and the cord runs out under it.
  21 mm of air above the heater, under the cheek tops.
- **Top (1, 860 × 860 mm), a squircle**: |x/a|⁸ + |y/a|⁸ = 1, a curve that fades into the edges instead of
  a radius that starts abruptly. The corner posts stay 20 mm inside its edge (v1: 40). The futon lies
  over the heater as in a traditional open frame (v1 had the deck in between).

That's **18 parts, about 10.4 kg, 16.8 m of cutting**. They fit on one 48 × 96" sheet. uMake lays out
the sheets itself and prices per part, so this only matters for my estimate.

## Assembly (a mallet, plus a screwdriver for the heater)
1. Sand the holding tabs off. Fit-up: measure the sheet. The crush ribs leave 14.1 mm, the thinnest sheet, so on
   anything thicker sand the bumps (or the crosspiece's faces) about (t − 14.1) / 2 a side, up to 0.8 mm at 15.7,
   until each crosspiece slides into its plate's head slot without play.
2. Drop a crosspiece into the head of each leg plate.
3. Stand the four legs up on the diagonals and lower the deck over the 4 tenons. Sand the crosspieces' top
   edges until the deck sits on them and on the shoulders together (first fit-up only).
4. Tap a wedge firmly through each tenon. Keep the wedges tapped in, and check them each season: with them
   slack, a hard press on a corner of the deck's ring uses nearly all of the wood's rough strength
   (`docs/fea.md`: 97 %, against 60 % with them tight).
5. On the floor or a bench, screw the heater between the two cheeks (drill 2–2.5 mm pilot holes).
6. Lower the heater and cheeks into the deck's well: the ears rest on the deck.
7. Drape the futon over the frame and lay the top on it.

## How it measures up

| Measure | Value |
|---|---|
| Clear height at the middle of each side (deck underside) | 344 mm |
| Clear height under the heater | 304 mm (v1: 286) |
| My 76 × 32 cm cross-legged knee zone (on the bare floor): how far it reaches under the top's edge | 38 mm |
| On a zaisu, legs forward: room above my thighs under the deck / my feet under the heater (seat 100 mm high when sat on, TODO-verify) | 69 mm / 69 mm (a typical 160 mm thigh, TODO-verify) |
| My knee room on the floor pillows, against v1 (where it's fine, owner 2026-11) | about the same: frame top 385 / 385 mm, deck underside 344 / 341, heater 304 / 286, reach 38 / 40, between the legs 571 / 568 |
| Cross-legged on a zaisu: knee room under the top's edge (385 mm, the futon squeezed over the knees) | none to spare once the seat's height is added, so I sit legs forward |
| Room between the legs at knee height / legs forward (to 275 mm) | 571 / 642 mm ("+" legs: 570 / 637) |
| Sway under a sideways push (spring model; FEA at 200 N: 6.1 mm, "+" legs 7.1) | 0.8 mm at 50 N, 1.6 at 100 N, 3.8 at 200 N |
| Twist: 115 N pushed along an edge at a top corner (best case: the joints rigid until they open, each crosspiece held down by the whole wedge clamp through the deck; the feet where the kick puts them) | 1.5 mm at the corner; the crosspiece joints open at about 203 N at most |
| Play in each tenon, and extra wobble per 0.1 mm a wedge works loose | 0.4 mm, about 1 mm |
| Push 50 mm in from the edge that tips the table / lifts the loose top's far side | never, in the model (the feet and corner posts sit almost under the edge) |
| Push right at the edge that tips the table / lifts the loose top's far side | about 4500 N / 640 N (v1: 1700 / 770): the loose top lifts long before the table tips |

- **Tipping**: I work it out the way EN 12521 and EN 1730 test it: a vertical push in the middle of a side,
  50 mm in from the edge. I assume the feet don't slide, and the weight includes a guessed 3 kg heater and
  2 kg futon. There's no pass/fail limit, only the report.
- **Wobble** comes from a spring model of each leg-to-deck joint (`kotatsu/stiffness.py`), not FEA. It
  includes the shoulders pressing on the deck, a wedge tapped in to about 300 N, the tenon faces bearing in
  the mortises, and each plate bending. One early discovery: when the tenon ran right to the leg's inner
  edge, every shoulder sat on one side of the wedge, so tapping the wedge in twisted the leg about 9 mm at
  the foot. I added the inner shoulder (12 mm in v2) to fix that. Re-tap the wedges after the first heating season.
  A push along x reaches each diagonal plate at 45°: all four take part in their own planes, and their
  stiffness across the plate is counted as nothing. Twisting is the one load that bends them across their
  faces, and the crosspieces resist it (`stiffness.twist`).
- **Strength**: I check it two ways. In the spring model, a 200 N sideways push stresses the legs to about
  2.1 MPa (all four plates share it; 14.1 mm stock, as everywhere); in the FEA it's more (below). For the top, I
  put it on its corner posts, which can only push up, in a plate model (`kotatsu/loads.py`). I checked the model
  against textbook plate results, and it matches within 3–5 %. The top rests on the 4 posts and the 4
  tenons (v1: 8 tenons; the "+" legs: 8 posts and 4 tenons).

| Load on the top | Peak load | Peak stress | Share of strength | Sag |
|---|---|---|---|---|
| Napping hunched over, a 7 kg cat curled up, a laptop | 39 kg | 3.3–3.5 MPa | 9–10 % | 1.6–1.7 mm |
| Flopping down while the cat jumps up mid-table | 75 kg | 5.1 MPa | 15 % | 2.7 mm |
| The cat lands on a corner | 28 kg | 0.8 MPa | 2 % | 0.1 mm |
| Everything piled at one edge | 54 kg | 4.5 MPa | 13 % | 2.2 mm |
| *Beyond normal:* an 80 kg adult sits hard on an edge | 120 kg | 13.1 MPa | 37 % | 6.7 mm |

No corner of the top lifts in any of these cases. The strength figures are rough textbook values
(TODO-verify), and a typical sheet breaks at about 1.5× them. The legs carry at most about 60 kg per
corner, and the wedges and deck don't carry any of the weight from above.

**Finite-element check ([docs/fea.md](docs/fea.md)).** I re-check the three parts with
`kotatsu/fea.py`, with their real outlines on 14.1 mm stock:
- **Top.** In the FE, everyday loads use at most 15 % and an adult on an edge 37 %, so I trust the grillage above
  (on the real squircle, the loads clipped to it): it's 9–15 % on the safe side.
- **X deck.** Under a 300 N hand the deck uses up to about 60 % of its strength at the arm fillets with the
  wedges tight, not the cantilever estimate's 27 % (the 45° arms are softer and weaker than assumed). With
  slack wedges 97 % (127 % before the bigger fillets, 155 % under the "+" legs). Keep them tight.
- **Legs.** A 200 N sideways shove at table height, 14.1 mm stock: the worst spot is the head slot's root at
  63 % (slim kicked legs; 74-75 % before), the wedge hole about 43 %; the sway is 6.1 mm along x, unchanged. With the
  top's worst corner load as well (an adult on an edge) 54 %, at the haunch fillet; that load alone uses 42 % (was
  31-32 %: the slimmer leg carries it harder at the haunch). (The "+" legs' plate A: 80 %, sway 7.1 mm, after it
  first failed at a 60 mm leg width; tag `plus-legs-archive`.) TODO-verify the strengths.

## Budget (CAD)

| Item | Cost |
|---|---|
| Heater (PaletteLife, amazon.ca, delivered) | $258 |
| uMake: 18 parts at 15mm, **quoted $306.84 + about $36.82 tax** (slim kicked legs; $303.98 before) (saved as quote 2926, not ordered, `docs/quote.md`), free shipping expected. If finalization adds what it did for v1 (~15 %): about $395 | $344–395 |
| Futon: an oversized king quilt, 120 × 120 in (owner 2026-11; planned as a 205 cm square from Etsy, or a queen duvet + cover) | about $200 |
| Sandpaper and finishing oil | $30–50 |
| A zaisu (bought, adjustable: about $70, free shipping) + tax | $78 |
| **Total** | **about $910–980** |

## Off-season storage
Everything packs flat inside the top's footprint, in two layers (the top, then the deck with the other 16 parts round it), a stack about 32 mm tall (I pack it with
`kotatsu/storage.py`, flipping parts over where that helps).

## The design space (`make optimize`, 2026-11, for the "+" legs: TODO rerun for the diagonal legs)
With `kotatsu/optimize.py` I sampled 384 designs over 8 knobs (`[optimize.knobs]`: the deck's arm width, fillets and
ring, the legs' lower width, haunch, taper and foot), kept the ones that cut, box and ship free with the knees
reaching under the top, then ran the FEA on the 48 most promising (plate A under the 200 N shove, plate B, the
deck's hard hand cases). What I found:
- **Price is flat:** every design costs $326.9–328.0. uMake prices each part's bounding box, and none of these
  knobs moves a box. Weight barely moves either (11.1–11.7 kg).
- **The real trade is leg room against stiffness and strength,** and the lower-leg width drives it: from 60 to 90 mm
  it takes sway down 4.4 mm and the worst share of strength down 85 points, for 47 mm less room between the legs
  where shins and thighs pass (`comfort.legroom`, new: measured at knee height, `shin_w` left it out).
- **The current design is on the front:** it has the most leg room (637 mm) of any design that passes the FEA.
- Near-free gains: a wider foot (less taper) buys strength for almost no room; a higher haunch top buys room.
  For the same money, about 595 mm of room gives 5.7 mm of sway and 72 % (now 7.1 mm, 80 %).
- **With economics and looks as the goals** (owner: equally important once the functional limits hold; looks
  measured as the legs' average visible width below the deck, `looks.leg_width`): the current legs are 63.4 mm.
  The slimmest that passes is 61.9 mm (−2 %), at 88 % of strength and $0.05 more; the cheapest saves $0.59 with legs
  19 % wider. So on these knobs the design is already at the edge for looks, and economics can't be traded at all.

## Tried and rejected: the heater turned 45° (2026-11, prototype)
Turning the heater, cradle and ring 45° (a diamond well, the arms meeting the ring mid-side) was tried in memory
against today's deck, with the same loads turned with it (deck FEA at h = 10, wedges tight):
- the ring's corners point at the sitters with nothing under them: a hand there uses **146–233 %** of the ring's
  strength (today 51–64 %); fillets 62–95 % (today 49–67 %); sag 10.7–10.9 mm (today 7.3–9.9);
- the deck-free opening in front of each sitter shrinks from 187 to 107 mm; the deck gets 0.24 kg heavier and the
  order $1.37 dearer; the cheeks' ends overhang the rounded diamond.
Today's orientation is the natural one for an X deck: each arm lands on a ring corner, so every ring side spans
between two supported corners.

## Price: what's left to save
Little: the design is at uMake's price floor (`docs/quote.md`, "What can still be saved"). About 40 % of the bill
doesn't depend on the design, the remaining cut is all required, and wood inside a part's box is free. A solid
deck would save about $4 but costs 3.8 kg and the knee room in the X's openings, so I'm keeping the X. The bigger
unknown is uMake's finalization: v1's receipt was **$405.83 + tax = $454.53**, $52.50 more than the cart's
$353.33 (TODO-verify what was added; if it repeats, v2's $306.84 becomes about $353 + tax, about $395).

## Still open
1. **The 15 mm sheet.** Order uMake's "15mm" Baltic birch (its "16mm" is probably 5/8", too thick). Its
   real thickness range is assumed at 14.1–15.7 mm: TODO-verify. Windsor Plywood's 15 mm B/B measures 15.0 ± 0.1 mm
   (`docs/research.md`), well inside it. uMake requoted for the diagonal legs: $303.98, and $306.84 with the slim kicked legs (`docs/quote.md`).
2. **Heater details.** The screws' length (the tips must stay inside the 15 mm cheek), and the control panel's
   real height (read off a photo: the knob and plug must clear the deck's underside, and stick out under the ring). With the futon now over the heater, check
   its top stays cool to the touch on high (owner, 2026-11: 40 °C on v1, the same heater: fine). Look for a cUL, cETL or CSA mark on the rating label.
3. **The crosspieces.** At the first fit-up, sand each crosspiece's top edge until the deck sits on it and on the
   plate's shoulders together, then twist the frame by hand: the joints should feel solid. The twist figure (1.5 mm
   at 115 N) comes from a spring model, not the FEA, and is a best case: in it I take each joint as rigid until it
   opens, and give each crosspiece the wedge's whole clamp. What holds the crosspiece down is the deck, lying on
   its top edge (sanded flush with the shoulders) and clamped onto the shoulders by the wedge beside the tenon.
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
- **Legs: ease the exposed vertical edges to about 3 mm, no more.** v2's legs work hard (in the FEA the
  root of the head slot uses 63 % of its strength under a hard 200 N shove), so the full half-rounds once
  planned for v1 would cost real strength. Keep sharp and flat: the top edges that carry the top and deck,
  the tenons and shoulders, the head slots' walls and the crosspieces' edges in them, and the wedge holes. Ease
  the floor edge about 2 mm.
- **Sand** to 180, wipe with a damp cloth to raise the grain, let it dry, then 220 (320 on the top).
- **Oil:** Osmo Polyx-Oil 3043 Clear Satin, which I already have and used on v1 (owner 2026-11). It's a hardwax oil, so it warms birch only
  a little (normal linseed, tung or Danish oils turn it honey-coloured). Try it on the 2 spare wedges first;
  if it looks too warm, Osmo Polyx-Oil Raw (3044) keeps it paler. Two thin coats, wiping off the excess,
  overnight between them, on **both faces and the edges equally**, so the top can't cup over the heater.
- No essential oils (hinoki scent): the cat sleeps in the warm kotatsu, and many are toxic to cats.

## Earlier designs
- **v1**, as ordered and built: 18 mm birch, the heater hung under the deck from wedged cheeks, R20
  corners. Git tag `v1-ordered` (and `main` until v2 merges).
- **v2's "+" legs** (two crossed plates a corner, one wedged, the other held by gravity; as quoted at $328.02):
  tag `plus-legs-archive`. I replaced them with the diagonal legs (owner 2026-11). At the time: $24 less in uMake's quotes ($36 by the price model),
  5.8 m less cutting, 0.8 kg lighter, 22 mm more room between the legs, and a little stronger and stiffer in the FEA.
  Slimmed and kicked, they're now $21.18 less ($306.84 against $328.02), 5.7 m less cutting, 1.0 kg lighter and 5 mm
  more room between the legs (642 against 637 mm).
- **v2's H deck** (four notches round the heater well, a wedge in all 8 tenons): commit ced3313 on the v2 branch.
- The 120 × 80 top in three boards with decorative seams (dovetails, arrowheads, maple leaves and more),
  and the 120 × 90 and Ø 90 tables: git tag `seams-archive`.
- The solid-sided frame (tapered legs, flared feet) and a splayed-leg yagura: git tag `frame-variants-archive`.
- Options I built and then didn't use, all at git tag `options-archive`:
  - **Deck windows** (closed holes): the notches took the same wood out with about 1 m less cutting, ~$20.
  - **X deck** (v1's): diagonal arms through the middle, optionally with a square "shield" over the heater.
    About $4 cheaper and 0.6 kg lighter, with the same joints. But the deck is what holds the futon up
    across the middle, and the X's openings are 22–26 cm wide against 18 cm in the H, each right where
    the knees go. Not worth it then. v2's X has a ring round the heater, which holds the futon up there.
  - **Leg windows**: replaced by the slim haunched legs.
  - **Lighter-look cuts**: R70 top corners, a curved haunch, feet tapering 10 mm. About $1.50 cheaper and a
    little less tipping margin (1698 → 1476 N at the edge), but hard to see. The hand finishing does more.
  - **Linking modules**: a tongue (or lugs) at each deck notch and a drop-in key, so tables push together
    into a row. About +$17 a module. I didn't like how it looked.
  - **Round top** (Ø 90): $199 shipping and round futons that wouldn't ship here.
