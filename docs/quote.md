# The uMake quote

The final order came to **CAD $395.73: $353.33 for 26 parts plus $42.40 tax, with free shipping**. Getting
there took eight quotes over two days, and the cart taught me more about pricing than the published rules
did.

## The diagonal legs, quoted (2026-11, saved in my account as quote 2926, not ordered)
Baltic birch, 15mm, CNC router, millimetres; the old deck and leg plates A and B removed from the saved quote,
the new deck, leg plate and crosspiece uploaded (top, cheeks and wedges unchanged).

| Part | Size | Qty | Each | Line |
|---|---|---|---|---|
| top | 860 × 860 mm | 1 | $87.94 | $87.94 |
| deck (R150 ring fillets; convex pads flaring out of the arms on R300, R10 far corners; owner 2026-11) | 769 × 769 mm | 1 | $102.57 | $102.57 |
| leg plate (the posts' long sweep, one long taper) | 140 × 385 mm | 4 | $17.44 | $69.76 |
| leg crosspiece (arched underneath) | 90 × 25.5 mm | 4 | $2.54 | $10.16 |
| heater cheek | 380 × 60 mm | 2 | $11.59 | $23.18 |
| wedge | 60 × 17 mm | 6 | $1.86 | $11.16 |
| **Subtotal** | | **18** | | **$304.77** |

(First quoted at $306.47; the legs, crosspieces and deck were re-uploaded as their curves got smoother: $306.42,
$306.36, $305.80, $304.82, then $304.77.) With 12 % tax about **$341.34**; shipping should stay free (the same 91 cm box, 10.6 kg: not re-checked at the
cart). That's $23.25 less than the "+" legs' $328.02. My price model said $293.71, 4 % low this time: a smaller
order gets less of uMake's volume discount on every part (the top went from $80.36 to $87.59), which the model's
curve, fitted on bigger orders, underrates (TODO: refit with this quote). If uMake's finalization adds what it
did to v1 (+15 %), about $395 with tax.

## What I ordered (October 2026)
Every file: units in millimetres, Engineered Wood > Baltic Birch, **19mm**, CNC router, no extra processes.
The thickness menu offers 3, 6, 9, 12, 15, 16, 19 and 25 mm, with no 18. The "19mm" is uMake's 3/4" birch.

| File | Size | Qty | Line |
|---|---|---|---|
| top.dxf | 860 × 860 | 1 | $92.79 |
| deck.dxf | 780 × 780 | 1 | $101.68 |
| leg-plate-a.dxf | 110 × 385 | 4 | $58.84 |
| leg-plate-b.dxf | 110 × 385 | 4 | $58.88 |
| heater-cheek.dxf | 372 × 94 | 2 | $23.64 |
| wedge.dxf | 60 × 17.6 | 14 | $17.50 |
| **Subtotal** | | **26** | **$353.33** |

Shipping: one 91 × 91 × 16 cm box, 16.6 kg, **free**. No part was flagged for a manual quote.

## v2 test quote (November 2026, not ordered)
Every file: millimetres, Engineered Wood > Baltic Birch, **15mm**, CNC router, no extra processes. It
quoted instantly; nothing was flagged.

| File | Size | Qty | Each | Line |
|---|---|---|---|---|
| top.dxf (squircle) | 860 × 860 | 1 | $80.32 | $80.32 |
| deck.dxf (X) | 780 × 780 | 1 | $95.86 | $95.86 |
| leg-plate-a.dxf | 110 × 385 | 4 | $16.13 | $64.52 |
| leg-plate-b.dxf (no tenon) | 110 × 385 | 4 | $14.73 | $58.92 |
| heater-cheek.dxf | 380 × 70 | 2 | $10.01 | $20.02 |
| wedge.dxf | 60 × 17.6 | 6 | $1.51 | $9.06 |
| **Subtotal** | | **18** | | **$328.70** |

- `kotatsu/price.py` (fitted on 19mm quotes) predicted $330.36, so 15mm costs about the same per metre
  of cutting and per m² as 19mm. The saving is weight, not money.
- The thickness menu has both **15mm** and **16mm**. Since "19mm" is the 3/4" sheet, "16mm" is probably
  5/8" (15.9 mm), thicker than the 15.7 mm the joints accept. Order "15mm". TODO-verify its real
  thickness range (14.1–15.7 mm assumed).
- I didn't open the cart, so no shipping quote; the top is still 860 mm (a 91 cm box) and the parts
  weigh about 11.6 kg, well inside free shipping.
- With the top on its own, the top line was $137.78: the fixed share again.

## v2 as designed (November 2026, not ordered)
The final v2 table (tapered legs, rounder corners, squircle n = 8 top). Every file: millimetres, Engineered Wood >
Baltic Birch, **15mm**, CNC router, no extra processes. All quoted instantly; nothing flagged.

| File | Size | Qty | Each | Line |
|---|---|---|---|---|
| top.dxf | 860 × 860 | 1 | $80.28 | $80.28 |
| deck.dxf | 780 × 780 | 1 | $94.90 | $94.90 |
| leg-plate-a.dxf | 110 × 385 | 4 | $16.21 | $64.84 |
| leg-plate-b.dxf | 110 × 385 | 4 | $14.78 | $59.12 |
| heater-cheek.dxf | 380 × 70 | 2 | $10.07 | $20.14 |
| wedge.dxf | 60 × 17.4 | 6 | $1.52 | $9.12 |
| **Subtotal** | | **18** | | **$328.40** |

The cart: one 91 × 91 × 14 cm box, shipping **free**, tax (BC GST/PST) $39.41, **total $367.81**, lead time 2 days.
`kotatsu/price.py` predicted $327.64 (0.2 % low). If uMake's finalization adds what it added to v1 ($52.50 on
$353.33, about 15 %), expect about $378 + tax, about $423. TODO-verify when ordering.

## v2 full quote: table and both zaisu (November 2026, not ordered)
Every file: millimetres, Engineered Wood > Baltic Birch, **15mm**, CNC router, no extra processes. All 28 parts
quoted instantly; nothing was flagged.

| File | Size | Qty | Each | Line |
|---|---|---|---|---|
| top.dxf | 860 × 860 | 1 | $66.47 | $66.47 |
| deck.dxf | 780 × 780 | 1 | $72.79 | $72.79 |
| leg-plate-a.dxf | 110 × 385 | 4 | $11.25 | $45.00 |
| leg-plate-b.dxf | 110 × 385 | 4 | $10.34 | $41.36 |
| heater-cheek.dxf | 380 × 70 | 2 | $6.96 | $13.92 |
| wedge.dxf | 60 × 17.6 | 6 | $0.99 | $5.94 |
| zaisu-side.dxf | 615 × 447 | 4 | $32.86 | $131.44 |
| zaisu-seat-board.dxf | 493 × 400 | 2 | $28.49 | $56.98 |
| zaisu-stretcher.dxf | 513 × 32 | 2 | $7.62 | $15.24 |
| zaisu-back.dxf | 513 × 300 | 2 | $26.26 | $52.52 |
| **Subtotal** | | **28** | | **$501.66** |

The cart: one **91 × 91 × 20 cm** box, shipping **free**, tax (BC GST/PST) $60.20, **total $561.86**, lead time
2 days. The cart shows 12.6 kg, which is each file's weight counted once, ignoring quantities (v1's first probe
saw the same). The real parts weigh about 18.4 kg (about 18.0 kg on uMake's scale), still under free shipping.
I stopped at the cart: its Confirm Order button wasn't pressed.

**Material is priced by each part's bounding box.** The old model (below) put this order at $473.85, 5.5 % low,
and part by part it was far off: the deck and the zaisu sides (big outlines, little wood) 25 % too cheap, small
solid parts 15–29 % too dear. Charging material by the bounding box instead of the wood fits all 10 lines within
2 % (the tiny wedge within 9 %), and holes cost nothing extra. `kotatsu/price.py` now does that:

    each part (raw) ≈ 64.17 × bounding box (m²) + 5.84 × cutting (m)
    order total     ≈ 12.45 × (sum of the parts) ^ 0.595

fitted on the two 15mm quotes. It predicts this one at $502.24, and v1's 19mm order 3 % low (thicker stock).
What it means for the design: **a cut-out or window saves weight, never money.** It only adds cutting, which is
about half the raw cost. One more metre of cutting costs about as much as 0.09 m² more bounding box.

### Without the chairs
Removing the four zaisu files from the same quote: **$328.53 for the 18 table parts**, one 91 × 91 × 14 cm box,
shipping free, tax $39.42, **total $367.95** (not ordered). So the two zaisu added $173.13 to the order. The
owner chose a bought, adjustable zaisu (about $70, free shipping) instead, and the plywood chairs were archived
(tag `zaisu-archive`). The bounding-box model predicts the table alone at $328.40.

| File | Each | Qty |
|---|---|---|
| top.dxf | $80.47 | 1 |
| deck.dxf | $94.56 | 1 |
| leg-plate-a.dxf | $16.24 | 4 |
| leg-plate-b.dxf | $14.84 | 4 |
| heater-cheek.dxf | $10.06 | 2 |
| wedge.dxf | $1.51 | 6 |

### Ready to order (2026-11-08)
Rebuilt from fresh DXFs (`make dxf`) and **saved to the owner's uMake account** (the quote ID stays out of this
public repo): the same 6 files, 15mm Baltic birch, CNC router, quantities 1 / 1 / 4 / 4 / 2 / 6, **$328.40** before
tax, matching the 2026-11 quote. Not ordered: the owner will confirm it later.
**Updated 2026-11-08** for the raised heater: the old `heater-cheek.dxf` is off the invoice (its file tab stays,
unordered) and the new one is on it, quantity 2. Still **$328.40**; saved.
**Updated again 2026-11-08** for the heater 10 mm higher (owner: a 10 mm gap under the cheek tops): the cheeks are now
380 × 60 mm (were 70 tall). The previous cheek is off the invoice, the new one on it at 2: **$328.02** before tax
(about $39.36 tax at 12 %), saved and checked after a reload.

### EZCNC, for comparison (2026-11-09)
EZCNC (Canada) has no 5/8" sheet, so this quote is for a **19 mm variant** of the current design (the same 6 files
regenerated for its 3/4" All-Birch at 17.5–19.3 mm, not committed or tested; 14.4 kg). Saved as a project in the
owner's EZCNC account (created 2026-11-09, login in 1Password); not ordered.

| Part (3/4" All-Birch, Natural, through cut) | Qty | EZCNC | Each | uMake 15mm, each |
|---|---|---|---|---|
| top (860 × 860) | 1 | $90.84 | $90.84 | $80.28 |
| deck (780 × 780) | 1 | $106.66 | $106.66 | $94.90 |
| leg plate A (110 × 385) | 4 | $148.20 | $37.05 | $16.21 |
| leg plate B (110 × 385) | 4 | $148.20 | $37.05 | $14.78 |
| heater cheek (380 × 60) | 2 | $75.66 | $37.83 | ~$10 |
| wedge (60 × 17) | 6 | $217.62 | $36.27 | $1.52 |
| **Production subtotal** | **18** | **$787.18** | | **$328.02 in all** |

Plus a live shipping rate at checkout (oversized parcels go to a custom quote) and tax. **About 2.4× uMake.**
EZCNC seems to have a floor of roughly $36 a part, so small parts cost as much as large ones: the 6 wedges alone are
$217. In bamboo plywood (3/4", Natural) the top alone is $345.28, about 3.8× the birch.

### What can still be saved (tried 2026-11, not adopted)
With material priced by bounding box, a change only saves money if it shrinks a part's box or its cut. At this
order size 1 m of cutting is worth about $4.66 and 0.1 m² of bounding box about $5.12; about 40 % of the total
doesn't depend on the design at all. Tried on the price model and the deck FEA (`kotatsu.tryVariants`-style
runs, in memory):
- Rounder or bigger fillets and corners (deck, legs, top), no crush ribs, no foot relief: each under ±$0.25.
- **Squircle corners on the X deck instead of its round fillets: worse.** +$1.4–1.6, 0.3 m more cutting, the
  FEA peak up to 67–73 %, and the pads' short edges turn into curves the bit can't cut.
- Corner pads as smooth convex blobs: no change (they're nearly convex already).
- **A solid deck** (no X openings): −$4.26, deck FEA 60 % and a third of the sag, but +3.8 kg, and no knee room
  in the openings. Rejected by the owner: the X's openings give the knees a few more cm.
- The top at squircle n = 8: −$0.20 (the posts 20 mm inside the edge instead of 28). Not taken.
The cut that's left is required: outlines, cross-lap slots, wedge holes, mortises, the heater well.

## How each change moved the price

| Design | Box, weight | Shipping | Total with tax |
|---|---|---|---|
| Ø 90 round top, 66 cm frame, 130 mm legs | 95 × 95 cm | $199.07 | $610.93 |
| 86 cm square top, deck with windows | 91 × 91 cm, 18.9 kg | free | $399.46 |
| Frame widened to 78 cm, bigger deck windows, windows in the legs | 91 × 91 cm, 18.5 kg | free | $455.11 |
| My first leg sketch (haunched legs, no leg windows) | 91 × 91 cm, 17.7 kg | free | $426.10 |
| My second leg sketch (slim legs) | 91 × 91 cm, 16.8 kg | free | $419.71 |
| Notched H deck, one wedge shape, crush ribs, foot relief | 91 × 91 cm, 16.6 kg | free | $396.38 |
| Rounded notch corners (**ordered**) | 91 × 91 cm, 16.6 kg | free | **$395.73** |

The very first quote, before shipping, was $346.40 for the Ø 90 round design. The 78 cm frame jumped the
price because every window is extra cutting.

## What the cart taught me

**Shipping is set by one box.** The cart packs the whole order into one box about 5 cm bigger than the
largest part, and charges by that box. I tested it by swapping only the top file:

| Top | Box | Shipping |
|---|---|---|
| Ø 900 | 95 × 95 × 18 cm | $199.07 |
| Ø 870 | 92 × 92 × 18 cm | $195.38 |
| Ø 860 | 91 × 91 × 18 cm | **free** |
| Ø 800 | 85 × 85 × 18 cm | **free** |

- Free shipping stops between a 91 and a 92 cm box, about 36". So the top can be at most about 86 cm.
- The published "length + girth ≤ 108"" rule isn't what the cart uses: the free 85 cm box is already about 115".
- **Weight matters too.** Free shipping also needs the order under about 20 kg. A square 860 top with the
  first frame came to 20.4 kg and cost $195.38 to ship. Windows in the deck brought it to 18.9 kg, and it
  shipped free. (My first probe got the weights wrong, because the cart had counted the leg plates once.)

**The price is mostly cutting.** I put test shapes into a separate quote to see how the price is built. One
300 × 300 square on its own costs $83.18, so every order carries a big fixed share. Adding shapes one at a
time (totals from $119 to $232) fits this model, now in `kotatsu/price.py`:

    each part ≈ $101 per m² of wood + $15.25 per metre of cutting + about $0.20 per hole

(Superseded in November 2026: material goes by the bounding box, see the v2 full quote above. The
conclusions about windows below were right for the wrong reason.)
    order total ≈ 11.25 × (sum of the parts) ^ 0.551

It predicts the real orders to within 15 cents. What it showed:
- **Cutting is about 77 % of the cost.** At this order size, one more metre of cutting adds about $5.40, and
  one more m² of wood about $36. A window costs more in cutting than it saves in wood, but opening it out to
  the edge as a notch saves money.
- **There's no per-file fee.** Merging the two wedge shapes into one was tidier, but saved almost nothing.
- **Quantity helps.** A leg plate cost $24.03 on its own, and $16.10 each once all 8 were in the order.
- **You don't need to lay out the sheets.** uMake arranges the parts itself.
- **There are no pockets.** A shape on a pocket layer came back priced as a hole cut right through. The
  "additional processes" are only custom instructions, bending, brushed finish and paint.

## Checkout
Cart → **Confirm Order** → accept the tolerance guide (**Proceed**) → a message shown on *every* customer
order: "Please note that this is not the final price. One of our representatives will reach out to you to
confirm and finalize your order." → **Ok** places the order. You don't pay at that step: payment comes after
uMake confirms. So the order goes in online, but uMake gets in touch once.

## Still to check
**The thickness (v2).** The joints accept 14.1–15.7 mm of uMake's "15mm" Baltic birch (TODO-verify when it arrives;
Windsor Plywood's 15 mm measures 15.0 ± 0.1). Over 15.7 mm the 16 mm head slots and mortises get tight: the crush
ribs and wedges absorb some of that, and sanding does the rest. (v1, "19mm": 17.0–18.9 mm.)
