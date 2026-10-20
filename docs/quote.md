# The uMake quote

The final order came to **CAD $395.73: $353.33 for 26 parts plus $42.40 tax, with free shipping**. Getting
there took eight quotes over two days, and the cart taught me more about pricing than the published rules
did.

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
**The thickness.** The joints accept 17.0–18.9 mm. If the sheet really measures 19.0 mm or more, the
19.2 mm cross-lap slots will be tight. The crush ribs and wedges absorb some of that, and sanding does the rest.
