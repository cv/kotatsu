# Finite-element check of the v2 table (top, X deck, leg plates)

`kotatsu/fea.py` checks the three load-bearing parts of v2 with finite elements, to confirm or correct the lumped
models (`kotatsu/loads.py` for the top and the deck arms, `kotatsu/stiffness.py` for the legs). It reads the real
outlines (`top.build`, `yagura.deck`, `frame.parts`), so it follows `params.toml`. Nothing here changes a cut part.

## In short

**Update (v2, owner 2026-11): the legs are fixed.** `yagura.leg_narrow` went from 60 to 70 mm (and the haunch
became an S-curve of squircle corners). Under the 200 N push, plate A now peaks at the wedge hole (87 %), with
the haunch at 81 %, the slot root at 77 % and sway 7.2 mm. `tests/test_fea.py::test_leg_plates_hold_the_push`
is now a plain test, no longer an expected failure. The tables below are the 60 mm study that found it.


| Part | Lumped model says | FEA says | Verdict |
|---|---|---|---|
| Top, worst case (80 kg sitter × 1.5 on an edge), 14.1 mm | 16.3 MPa, 46 %, 10.4 mm sag (grillage at 14.1 mm) | 14.7 MPa, 42 %, 9.2 mm | **Confirmed.** The grillage is slightly conservative. |
| X deck, 300 N hand + heater | 11.9 MPa, 40 %, 3.7 mm (cantilever arm) | up to 68 % (Tsai-Hill) at the fillets, 7–10 mm sag, with the wedges tight | **Corrected.** About 1.7× the lumped figure, but it holds. With slack wedges it doesn't (up to 155 %). |
| Leg plate A, 200 N sideways push | 3.6 MPa in the legs, 4.5 mm sway | 41–56 MPa at the haunch fillet (Tsai-Hill 160 %), 12 mm sway | **Problem.** The lumped model misses that A's upper half is two separate fingers. |

The 200 N push is `stiffness.stresses`' check load, a hard shove at table height. On the thinnest stock the FE
model puts A's first failure at about 125 N (if you scale linearly; contact makes it only roughly linear). That is
a v2 design issue. See [Recommended changes](#recommended-changes-v2-not-made-here). The tests keep it visible as
a strict `xfail` (`tests/test_fea.py::test_leg_plates_hold_the_push`).

## Method

**Mesh.** A quality triangle mesh (Shewchuk's Triangle via `triangle`, minimum angle 30°) of the shapely outline,
holes included. The support pads' edges are built into the mesh, so each element is wholly on or off a pad. Lines
are snapped to a 0.5 mm grid first, so edges a hair apart merge (the deck's cut-outs sit 0.2 mm from the posts).
Load patches are *not* meshed in: each element takes its share of a patch's force by exact overlap area, because
patches often run right along the top's curved edge.

**Elements** (scikit-fem):
- top and deck: Kirchhoff plates on **Morley** triangles (constant curvature per element), orthotropic;
- leg plates: **plane stress** on quadratic (P2) triangles, orthotropic.

**Material.** Plywood is treated as a homogeneous orthotropic sheet with the values already in `params.toml`:
E = 9000 MPa along the face grain and 6500 across it, G = 620 MPa, ν = 0 (as in `loads.py`). Strengths are
f_m = 35 (along), 30 (across) and 9 MPa (shear). All are rough, **TODO-verify**. Stresses are at the faces
(plates) or in-plane (legs). Two measures of how much strength is used:
- the largest of σ_along/f_m, σ_across/f_m,cross and τ/f_v, as `loads.py` does;
- **Tsai-Hill**, √((σ1/X)² − σ1σ2/X² + (σ2/Y)² + (τ/S)²), which also counts stresses acting together. This is
  the one to believe for the deck's arms, which run at 45° to the grain.

The tables give Tsai-Hill unless they say otherwise. Every case uses the **thinnest stock, 14.1 mm**
(`material.t_min`).

Two consequences of orthotropy that the lumped deck model misses (hand calculation, same constants):
- At 45° the bending modulus is 1/E45 = (1/Ex + 1/Ey + 1/G)/4, so E45 ≈ 2130 MPa. `deck_arms` uses
  E_par/2 = 4500 MPa.
- At 45° Tsai-Hill gives a strength of about 2/√(1/Y² + 1/S²) ≈ 17 MPa. `deck_arms` holds the stress against
  f_m,cross = 30 MPa.

Both are TODO-verify against a birch-plywood handbook, which gives 45° bending values.

**Supports and contacts.**
- *Top*: rigid, compression-only pads at the post and tenon tops (`comfort.top_supports`, the thickest stock).
  An active-set loop lets go of any pad that would have to pull.
- *Deck*: rigid, compression-only on the plates' top edges (`yagura.plate_tops`, A and B). Under each lying
  wedge (`yagura.wedge_footprints`) a stop that can only push the deck down. Run both **tight** (shoulders and
  wedges both act: clamped corners) and **slack** (shoulders only). The real preloaded joint lies between. It is
  far nearer *tight*: `stiffness.joint`'s springs (wedge ≈ 22 kN/mm, shoulders ≈ 6 kN/mm per plate) are
  hundreds of times stiffer than the deck (≈ 30 N/mm under a hand), so rigid is a fair stand-in.
- *Legs*: the joint is `stiffness.joint`'s springs, spread along the real edges:
  - shoulders on the deck's underside (E_perp·t/t_deck per mm, push only);
  - the wedge on the hole's top edge (push only, tapped in to `stiffness.wedge_preload` = 300 N first). Only
    about 7 mm of that edge is straight: the dogbones take the rest;
  - the tenon's faces on the mortise ends, after `fit.tight`;
  - the corner post on the deck's cut-out, after `fit.tight`.

  The foot stands on a rigid **floor body** (end grain, push only, gripping sideways). The floor slides but
  doesn't turn. The deck stays put and the floor is moved sideways by the sway that makes this plate and its
  mirror image (the other wedged plate in that direction) take the push between them, as
  `stiffness.frame_sway` shares it. Both senses of push are run and the worst is reported. Plate B (no tenon) is
  bounded as `stiffness.stresses` does: its share of the push at the foot, its top edge clamped.
- Peaks right at the ends of a contact (the wedge's bearing, shoulder ends) are local bearing peaks of the
  stiff springs. They are listed separately ("contact edges") and kept out of the zone figures.

**Verification** (`tests/test_fea.py`):
- a simply supported square plate under uniform load against Navier's series: deflection within 0.2 % and
  moment within 0.1 % at 50 mm elements (Timoshenko's 0.00406 qa⁴/D);
- a plane-stress cantilever against Timoshenko beam theory (bending + shear): tip deflection within 0.03 %,
  stress within 1 %;
- force balance in every model.

## Mesh convergence

| Model | Element size (mm) | Result |
|---|---|---|
| Top, sitter case | 40 / 28 / **20** / 14 | sag 9.24 / 9.20 / 9.17 / 9.16 mm; σ_along 14.5 / 14.6 / 14.65 / 14.7 MPa |
| Deck, hand beside a cheek, wedges tight | 16 / **8** / 5.6 / 4 | sag 9.90 / 9.87 / 9.84 / 9.82 mm; fillet Tsai-Hill 0.67 / 0.67 / 0.68 / 0.70 |
| Deck, hand spread over the ring | 16 / **8** / 5.6 / 4 | sag 5.85 / 5.83 / 5.82 / 5.80 mm; fillet Tsai-Hill 0.33 / 0.36 / 0.35 / 0.34 |
| Leg A, 200 N push | **4** / 2.5 | sway 11.88 / 11.90 mm; haunch fillet Tsai-Hill 1.60 / 1.65; slot root 1.32 / 1.31; wedge 1250 / 1250 N |

The defaults (bold) are in `[fea]` in params.toml. The tests run coarser meshes (28, 16 and 6 mm) to stay quick.
The leg's peak *stress component* at the haunch moves more between meshes (41 → 56 MPa) than its Tsai-Hill index,
because the worst element shifts along the fillet. Read the leg peaks as ±15 %.

## Results

### The top (15 mm squircle on 8 posts and 4 tenons), 14.1 mm

FE stresses are along / across / twist, one plate thickness clear of the pads. The grillage
(`loads.solve`) is run at the same 14.1 mm (`loads.report` itself uses 15 mm).

| Case | FE sag | FE stress (MPa) | FE use | Grillage sag | Grillage stress | Grillage use |
|---|---|---|---|---|---|---|
| Nap, cat curled mid-table, laptop | 2.1 mm | 3.7 / 1.4 / 0.4 | 10 % | 2.3 mm | 3.9 / 1.4 / 0.2 | 11 % |
| Nap, cat curled by your head | 2.3 | 3.9 / 1.5 / 0.4 | 11 % | 2.5 | 4.1 / 1.4 / 0.2 | 12 % |
| Slump × 1.5 + cat landing mid-table × 4 | 4.1 | 6.1 / 2.7 / 0.6 | 17 % | 4.4 | 6.5 / 2.7 / 0.3 | 19 % |
| Cat lands on a corner × 4 | 0.2 | 0.3 / 0.3 / 0.1 (1.4 over the pad) | 1 % | 0.2 | 1.1 / 0.4 / 0.1 | 3 % |
| Everything at one edge | 3.2 | 5.2 / 2.2 / 0.6 | 15 % | 3.5 | 5.5 / 1.9 / 0.4 | 16 % |
| 80 kg adult sits on an edge × 1.5 | 9.2 | 14.7 / 4.2 / 1.6 | 42 % | 10.4 | 16.3 / 3.6 / 1.1 | 46 % |

Corner reactions agree within a few newtons (sitter: 617 / 550 / 58 / 23 N in FE against 618 / 563 / 50 / 17 N
in the grillage). No corner lifts off entirely. With rigid pads, though, only 4 or 5 of the 12 pads carry anything
in each case, and the rest carry nothing. On a real futon the load spreads
over the pads, so the rigid model is the harsh one. The peak is in the open span, not over a pad, so the
pad-edge singularity doesn't set the result.

### The X deck (hand_n = 300 N on an 80 mm patch on the ring + 3 kg heater on the cheek ears), 14.1 mm

Use is Tsai-Hill. The lumped `loads.deck_arms`: 82 N per arm, 11.9 MPa, **40 %** (against f_m,cross),
3.7 mm sag.

| Hand | Wedges | Sag | Fillets | Arms | Ring | Pads | Wedge force |
|---|---|---|---|---|---|---|---|
| spread over the ring | tight | 5.8 mm | 36 % | 26 % | 19 % | 25 % | 423 N |
| beside a cheek (mid-side) | tight | 9.9 | **67 %** | 53 % | 54 % | 35 % | 793 N |
| on a ring corner | tight | 7.3 | **68 %** (20.6 MPa along) | 48 % | 51 % | 50 % | 870 N |
| on the ring's end, over the cheek ears | tight | 8.6 | 53 % | 40 % | 63 % | 36 % | 686 N |
| spread over the ring | slack | 19.1 | 76 % | 54 % | 47 % | 5 % | none |
| beside a cheek | slack | 26.7 | 104 % | 77 % | 83 % | 8 % | none |
| on a ring corner | slack | 22.5 | **155 %** | 113 % | 97 % | 4 % | none |
| on the ring's end | slack | 24.1 | 103 % | 79 % | 93 % | 7 % | none |

The peaks sit in the fillets where the arms meet the ring (about 2× the arms' straight run), and in the 40 mm
ring strip beside the cheeks, which `deck_arms` doesn't look at. The tight joints clamp the corners. The deck
then pushes up on each wedge with up to about 0.8–0.9 kN (±15 % between meshes), well past the 300 N tap-in. The
leg's plate A balances this inside its own joint (A's shoulders take at least the wedge's pull, within 8 N),
so the joint doesn't need the floor to hold the plate down.

### The leg plates, 14.1 mm, grain up the leg

`stiffness.stresses` (200 N): legs **3.6 MPa**, wedge-bridge shear 3.0 MPa. `frame_sway`: 4.5 mm.

The worst case comes up first: the top's worst corner load is the sitter case, 616 N on A's tenon top at the
(−,−) corner.

| Case | Sway | Wedge | Haunch fillet | Slot root | Wedge hole | Bridge | Elsewhere | Contact edges |
|---|---|---|---|---|---|---|---|---|
| A, 200 N push | 11.9 mm | 1250 N | **160 %** (41 MPa along) | 132 % (45 MPa) | 80 % | 47 % | 79 % | 134 % |
| A, 200 N push + top load | 6.5 | 922 | 114 % | 49 % | 35 % | 27 % | 45 % | 91 % |
| A, top load only | 0 | 300 | 26 % | 37 % | 8 % | 7 % | 11 % | 21 % |
| B, its share (112 N), top clamped | n/a | n/a | 49 % | 109 % (37 MPa) | n/a | n/a | 27 % | 28 % |
| A, 200 N push, 15.0 mm stock, crossing plate on the crush ribs | 11.5 | 1250 | 151 % | 124 % | 75 % | 45 % | 64 % | 126 % |

Where the peaks are, in plate coordinates (u from the frame edge, z up):
- haunch fillet: (60, 286), the inside corner where the narrow leg widens under the deck;
- slot root: the outer dogbone at (21, 174), at the bottom of A's cross-lap slot;
- B's slot root: (21, 171), at the top of its slot from the floor.

The wedge hole and bridge figures are clear of the wedge's bearing. Right under the wedge the bearing peak
reaches about 47 MPa along the grain (that is the "contact edges" figure) over the 7 mm of straight edge. That is
local crushing of end grain, not a bending failure. TODO-verify the wedge seat after a season.

## Where they disagree, and why

1. **The legs: two fingers, not one section.** A's cross-lap slot runs from the shoulder down to z ≈ 172. Above
   that, the plate is two fingers: the corner post (0–22 mm) and the inner finger (38–60 mm, widening into the
   tenon at the haunch). They meet only below the slot root. `stiffness.section` adds the pieces of each
   horizontal section about one common centroid (the parallel-axis term), as if the slot were glued shut.
   - For the 22 + 22 mm fingers that gives about 10× the bending stiffness they really have, and 7× the
     section modulus of the inner finger, which carries the moment.
   - The tenon and wedge hang the whole joint moment on the inner finger. Just under the haunch that is about
     H·z ≈ 120 N × 286 mm on a 22 mm finger: 31 MPa nominal, × 1.3–1.8 for the fillet.
   - The same mistake makes the lumped sway about 2.6× too small (4.5 mm against 11.9 mm).
   - The crossing plate B in the slot doesn't fix it. It can push the slot walls apart but can't carry shear
     along the slot, and on thin stock it doesn't touch the ribs at all. The last row of the table runs it
     bearing on the crush ribs: no better.
2. **The deck: 45° and the ring.** The lumped arm uses half the along-grain modulus and the cross-grain
   strength. At 45° plywood is governed by its shear modulus and strength, so it is about half as stiff and
   about half as strong as assumed. The hand also bends the 40 mm ring strip, and the fillets concentrate the
   stress where arm meets ring. The lumped cantilever is unconservative: 40 % against 68 %.
3. **The top: agreement.** The grillage is within 10 %, a little on the safe side. Nothing to correct.
4. **Joint forces.** The lumped model's wedge force (and the 3.0 MPa bridge shear from it) assumes the wedge
   stays near its 300 N tap-in. FE has it rising to about 1.25 kN under a 200 N push, and to 0.8–0.9 kN under a
   hand on the deck. The two shoulders next to the tenon are only about 6 and 4 mm long after the root reliefs
   and rounding, so the lever is short. The bridge above the hole still copes: 45–47 % at 200 N.

## Recommended changes (v2, not made here)

These are what-ifs run with `fea.leg_case` / `fea.deck_case` on edited copies of the params. Check each
against comfort (knee room), weight and the cut list before adopting it.

| Change | Effect (200 N push, or the deck's worst hand) |
|---|---|
| `yagura.leg_narrow` 60 → 70 | sway 8.1 mm; haunch 89 %, slot root 69 %, wedge hole 81 % |
| `yagura.leg_narrow` 60 → 80 | sway 6.7 mm; haunch 58 %, slot root 54 %, wedge hole 79 % (costs 2 × 20 mm of room between the legs at knee height) |
| `yagura.leg_haunch_r` 15 → 30 | no help (haunch 151 %): the finger is too narrow, not the fillet too tight |
| `deck.ring_w` 40 → 50 | hand beside a cheek: fillets 64 %, ring 46 % (were 67 / 54 %) |
| `deck.arm_w` 36 → 44 | hand on a ring corner: fillets 57 %, arms 42 % (were 68 / 48 %) |

- **Legs (the one that matters).** Give the wedged plate a solid upper half. Either wedge the plate that's slotted
  *from the floor* (the moment H·z is largest near the deck, and smallest at the floor where that slot is), or
  widen the narrow leg to about 80 mm. Swapping A and B is a code change in `yagura.leg_plate` (the tenon,
  wedge hole and foot relief go on the floor-slotted plate) and should be re-run through this model.
  Until then: the table is fine for sitting at and leaning on (the top-load-only row is 37 %). Don't shove it
  sideways hard, and keep the wedges tapped tight.
- **Deck.** It holds as cut, with the wedges tight: 68 % worst, a margin of about 1.5 on rough strengths.
  Re-tap the wedges: slack wedges nearly triple the sag and overstress the fillets under a hard press. If more
  margin is wanted, the cheapest is a wider ring beside the cheeks or wider arms (table above).
- **Top.** No change.

## Limits of this model

- Homogeneous orthotropic plates. Real plies give the face grain a little more in bending than in-plane. The
  legs' in-plane values here are the bending values (TODO-verify).
- Rigid pads under the top and the deck. The futon under the top and the deck's soft E_perp bearing spread
  loads in reality, which lowers peaks over the pads.
- The leg model lets the floor slide but not turn, and holds the deck still. It leaves out the legs'
  out-of-plane bending, buckling and B's friction. It counts B as carrying none of the push, as
  `stiffness.py` does.
- Static, short-term strength. No creep (a warm heater under a loaded top), fatigue or moisture.
- The strengths (f_m 35, f_m,cross 30, f_v 9 MPa) are rough characteristic values (TODO-verify). A typical sheet
  breaks well above them, which is why 160 % is a warning and not a prediction that the leg snaps.

## The zaisu

`kotatsu/fea_chair.py` checks the chairs with the same tools, thinnest stock, each part's grain the weaker way
round (the nester may turn chair parts any way), next to `zaisu.py`'s lumped checks:

| Part, load | Model | FE (Tsai-Hill) | Lumped |
|---|---|---|---|
| Seat board, a 1000 N sitter on a cushion-sized patch towards the back | plate on its 4 tabs (push up only) | 38 %, 5.1 mm sag (16 mm to the floor) | 46 % (point load, mid-span) |
| Back panel, a 450 N lean along the top rail | plate on its 4 hook tabs (push forward only) | 49 %, 6.3 mm | 41 % (shared by both rails) |
| Side frame, a 450 N flop back with a 600 N sitter | plane stress on the floor (push only, gripping), the lean through the back's slots (split by lever), the sitter through the board's holes | 68 % (85 % before, see below) | 37 % (post root) |
| Side frame, a 1000 N sitter alone | as above | 2 % | n/a |

The lumped post check missed the side frame's peak. It isn't at the post's root but in the small inside corner
*behind* the post, where it meets the runner's short tail: 85 % with a 40 mm fillet on a 560 mm runner. A
bigger fillet there (80 mm) on a slightly longer runner (600 mm, which also makes the chair harder to tip back:
600 N instead of 531) brings it to 68 % for 54 g a chair. Adopted (`zaisu.fillet_back_r`, `zaisu.runner_len`).
`tests/test_fea_chair.py` checks forces balance and that every part holds.

## Seeing it

The site's **3-D view** has a "stress (FEA)" control. Pick a load case: the part is painted where it stands,
blue (idle) to yellow (half its strength) to red (all of it) and purple (past it), and drawn bent (exaggerated
"bend ×" times, pulsing load on and off). The load's patch is a dark pad; grey marks pads and contacts, whose
peaks are local bearing. Each part is analysed alone, its neighbours standing in as springs and supports, so
the view only *carries* the rest of the frame: for the leg cases (a push along x) it draws them as the floor
sees them, feet still and the deck swaying; the two plates along x bend in their plane, each the right way
round, while the deck and everything on it shift and the other plates lean with it. For the deck, the
cradle rides down with the ring. At true scale nothing collides: under the 200 N push A's cross-lap slot
narrows by 0.2 mm at most, against the 0.9 mm a thinnest B plate has between its crush ribs. `kotatsu/fea_view.py` computes it
on slightly coarser meshes (15 cases, about a minute): run `make fea` after changing the design. The site
says so when the results are stale. CI runs it on every push.

## Running it

```
uv run python -c "from kotatsu import params, fea; p = params.tables(params.load())[0]; print(fea.top_report(p))"
uv run python -c "from kotatsu import params, fea; p = params.tables(params.load())[0]; print(fea.deck_report(p))"
uv run python -c "from kotatsu import params, fea; p = params.tables(params.load())[0]; print(fea.leg_report(p))"
```

These take about 20 s, 45 s and 60 s. `uv run pytest tests/test_fea.py` takes about 25 s.
