# Research notes

What I learned about uMake and the materials before designing anything, plus what the cart taught me
later. Retrieved October 2026 from uMake.ca's public pages and the help text inside app.umake.ca.

## Ordering
- The instant quote lives at <https://app.umake.ca>. You upload a file, then pick the process, material,
  thickness, quantity and delivery. You need an account to see the materials and thicknesses.
- It accepts DXF, DWG, AI, SVG and PDF files (and STEP for some processes).
- Before you order, the app asks you to accept its tolerance guide. Some parts get flagged for a manual
  quote, which means talking to staff, so the design has to avoid that. None of ours were flagged.
- **One surprise at checkout:** every customer order ends with "One of our representatives will reach out
  to you to confirm and finalize your order." So an order is placed online, then confirmed by uMake.
- Source: <https://www.umake.ca/> and the app's own code.

## Laser or router?

| Process | Plywood thickness | Bed / max part | Cut tolerance |
|---|---|---|---|
| CO₂ laser | up to 1/4" (about 6 mm) | 48 × 36" or 60 × 60" (the pages disagree) | ±0.30–0.45 mm |
| CNC router | 3/4" and more (Baltic birch) | max part 61 × 140"; birch sheets 48 × 96", 60 × 60", 60 × 120" | ±0.30–0.45 mm |

The laser only cuts thin plywood. That's too floppy for a table top and too weak for a frame with no glue
(and laminating thin sheets would need glue). So everything is **CNC-routed 18 mm Baltic birch**, ordered the
same way.

Sources: <https://www.umake.ca/co2-laser-cutting-engraving>, <https://www.umake.ca/canada-custom-cnc-parts>

## Rules for router files
- Check the scale and units.
- Leave at least **5 mm between parts** and a **20 mm margin** round the sheet.
- **No part smaller than the sheet's thickness.**
- Outlines only, closed, with no overlapping or doubled lines.
- Mark engraving or pockets with different colours. (In practice uMake doesn't offer pockets: a test shape
  on a pocket layer came back priced as a hole cut right through.)
- The bit can't cut a sharp inside corner. It leaves a radius of half its width: about 1.6 mm for a 1/8"
  bit, 3.2 mm for a 1/4" bit. So every square slot gets small round **dogbones** in its corners. The shop
  says a small dogbone leaves only about 0.5 mm of visible overcut.
- The shop leaves **holding tabs**, about 4.8 mm wide and half the sheet thick, to keep parts in place. Sand
  them off.

## How thick is "18 mm"?

| Nominal | Mill tolerance |
|---|---|
| 6.5 mm (1/4") | +0.45 / −0.55 |
| 9 mm (3/8") | +0.45 / −0.65 |
| 12 mm (1/2") | +0.55 / −0.75 |
| 18 mm (3/4") | **+0.85 / −1.05** |

North American "3/4"" plywood often measures about 23/32" (18.3 mm). uMake lists it as "19mm". So every
joint has to work with anything from **17.0 to 18.9 mm**. That's why the design uses wedges and crush ribs
instead of exact press fits.

## Shipping

uMake publishes these rules (policy dated 2025-12-02):

| Class | Limits | Cost | Talk to someone? |
|---|---|---|---|
| Standard parcel | longest side ≤ 48", ≤ 50 lb a box, length + girth ≤ 108" | free on orders over $250 | no |
| Oversize parcel | longest side 48–60", or 51–150 lb | priced at checkout | no |
| Freight | over 60", over 150 lb, or needs a pallet | quoted by staff | **yes, so avoid** |

**The cart works differently.** It packs the whole order into one box about 5 cm bigger than the largest
part and charges by that box. Shipping is free while the box is **91 cm or less** and the order weighs
**under about 20 kg**. A 92 cm box cost about $195. The published length + girth rule doesn't apply: a free
85 cm box is already about 115". Details are in `docs/quote.md`.

Source: <https://www.umake.ca/canada-shipping-terms>

## Weight
Baltic birch weighs about 680–720 kg/m³, so 18 mm sheet is about **12.6 kg/m²**. The 86 cm top weighs
about 9.3 kg, and the whole order about 16 kg.

## Heaters
Japanese kotatsu heaters run on 100 V. In Canada you want a **120 V replacement-style unit**, ideally with a
cUL, cETL or CSA mark, rather than a transformer. The one I chose, and why, is in `docs/heater.md`.

## Other shops (not checked in detail)
- SendCutSend (US) ships to Canada. I didn't check its wood thicknesses and size limits.
- Ponoko is laser only, with small beds, so it can't cut the top.
