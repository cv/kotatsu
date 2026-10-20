# uMake instant quote

**2026-10-19.** Saved project: in the owner's uMake account. **Not ordered.**

All 7 part DXFs from `out/dxf/parts/` were uploaded. Every file was set up the same way:

- file units: millimetres; preferred units: millimetres;
- material: Engineered Wood > Baltic Birch, **19mm**. The thickness choices are 3/6/9/12/15/16/19/25 mm, with no 18;
- process: CNC Router, no additional processes.

| Part (file) | Size shown by uMake | Qty | Per item | Line |
|---|---|---|---|---|
| top.dxf | 900 × 900 mm | 1 | $97.03 | $97.03 |
| deck.dxf | 660 × 660 mm | 1 | $75.00 | $75.00 |
| leg-plate-a.dxf | 130 × 385 mm | 4 | $16.10 | $64.40 |
| leg-plate-b.dxf | 130 × 385 mm | 4 | $16.10 | $64.40 |
| heater-cheek.dxf | 372 × 94 mm | 2 | $12.51 | $25.02 |
| leg-wedge.dxf | 60 × 17.6 mm | 9 | $1.35 | $12.15 |
| cheek-wedge.dxf | 80 × 17.6 mm | 5 | $1.68 | $8.40 |
| **Total** (before tax and shipping) | | **26** | | **$346.40** |

Notes
- The sizes and quantities match `out/BOM.md`. No part was flagged for a manual quote.
- uMake prices each part and gives quantity discounts. A leg plate cost $24.03 at qty 1 and $16.10 once all 8 were in the order.
  Uploading the laid-out sheet instead isn't needed: they nest the parts themselves.
- The order is over the $250 free-standard-shipping threshold. The top's box (about 37 × 37 × 2.7") is over the 108" length + girth limit,
  so expect an oversize charge at checkout (the next page, after "Confirm Order"). **TODO:** read the shipping cost to rural BC.
- **TODO-verify the thickness:** "19mm" is uMake's 3/4" Baltic birch. The joints accept 17.0–18.9 mm (`[material]`). If the
  stock really measures 19.0 mm or more, the cross-laps (19.2 mm slots) would be too tight. Choices: ask or measure before the
  order, or widen `t_max` to about 19.3 (looser fit on thinner stock; the wedges take up the slack at the deck).

## Shipping probe (2026-10-20)
uMake's cart prices shipping itself. It packs everything into **one box** about 5 cm bigger than the top and 18 cm
deep, and charges by that box. Tested by swapping only the top file (frame files unchanged), to rural BC:

| Top | Box | Weight | Shipping | Parts | Tax | Total |
|---|---|---|---|---|---|---|
| Ø 900 | 95×95×18 cm | 15.5 kg | **$199.07** | $346.40 | $65.46 | $610.93 |
| Ø 870 | 92×92×18 cm | 15.0 kg | **$195.38** | $342.55 | $64.55 | $602.48 |
| Ø 860 | 91×91×18 cm | 14.8 kg | **FREE** | $341.10 | $40.93 | $382.03 |
| Ø 800 | 85×85×18 cm | 13.8 kg | **FREE** | $333.56 | $40.03 | $373.59 |

- Free shipping stops between a 91 and a 92 cm box. That's about 36" (91.4 cm), so the top can be at most about **Ø 860**.
  The published "L + girth ≤ 108"" rule isn't what the cart uses: the free 85 cm box is about 115".
- The project is left with **top-860-test.dxf** in place of top.dxf. The deck and leg-plate files there are the
  pre-corner-post versions. **Re-upload deck.dxf, leg-plate-a.dxf and leg-plate-b.dxf (and the real top) before ordering.**

### Correction + square top (2026-10-20, later)
- The weights in the probe table above were low: the cart had counted the leg plates once. The free tier is
  **box ≤ 91 cm AND weight below about 20 kg**. Ø 860 with the full order came to 18.3 kg, free. An 860 square came to 20.4 kg, **$195.38**.
- **Square 860 + deck with lightening windows** (−1.5 kg): **91×91×18 cm, 18.9 kg, FREE**.
  Parts $356.66 + tax $42.80 = **$399.46** (deck $94.95: the windows add routing).
- The project now holds the current files: top.dxf (860 square), deck.dxf (windows + corner cut-outs),
  leg-plate-a/b.dxf (corner posts) ×4 each, heater-cheek ×2, leg-wedge ×9, cheek-wedge ×5.

### Frame 780 (2026-10-20, latest)
Owner asked for the legs further apart: frame 780 × 780 under the 860 top (40 mm overhang), with bigger
auto-sized deck windows and a slot window in each leg plate. Cart: **91×91×18 cm, 18.5 kg, FREE**.
| Part | Qty | Line |
|---|---|---|
| top.dxf 860 × 860 | 1 | $91.31 |
| deck.dxf 780 × 780 (4 windows) | 1 | $121.95 |
| leg-plate-a.dxf (corner post + window) | 4 | $75.92 |
| leg-plate-b.dxf | 4 | $75.96 |
| heater-cheek.dxf | 2 | $22.86 |
| leg-wedge.dxf | 9 | $10.80 |
| cheek-wedge.dxf | 5 | $7.55 |
| **Subtotal** | | **$406.35** + tax $48.76 = **$455.11** |

The windows cost routing time. The 660 frame order was $399.46. The leg windows add about $25 and save
about 0.4 kg; without them the order is about 18.9 kg, the same weight that shipped free before (thin margin).

### Haunched legs (2026-10-20, latest)
The owner's sketch: leg plates 80 mm wide below a sloped haunch, full 130 mm under the deck; no leg windows.
Cart: **91×91×18 cm, 17.7 kg, FREE**. Leg plates $61.64 + $61.68 (×4 each, down from about $76 each with windows),
deck $123.40, top $91.83, cheeks $23.22, wedges $10.98 + $7.70. **Subtotal $380.45 + tax $45.65 = $426.10.**

### Slim legs (2026-10-20, latest)
The owner's second sketch: the outer finger is as wide as the inner one (20.4 mm). Ear 30, plates 110 mm under the deck and
60 mm below the haunch. Cart: **91×91×18 cm, 16.8 kg, FREE**. Leg plates 110 × 385: $57.84 + $57.88 (×4 each),
deck $124.88, top $92.20, cheeks $23.26, wedges $10.98 + $7.70. **Subtotal $374.74 + tax $44.97 = $419.71.**

## How uMake prices (probe, 2026-10-20) → kotatsu/price.py
Test shapes went into a separate, unsaved quote (Baltic birch 19mm, CNC). On its own, one 300 × 300 square
costs $83.18: there's a large fixed share per order. Shapes added one after another (totals $119 → $232),
fitted at a fixed order size:

    part raw $ ≈ 101 $/m² × area + 15.25 $/m × cut length + ~0.2 $/hole      (residuals < $1)
    order total ≈ 11.25 × (Σ raw)^0.551

This reproduces the real order ($374.78 predicted vs $374.74 quoted).
- **Cutting is ~77 % of the raw cost** (29 m of cut). Marginal at our order size: about **$5.4 per metre of cut** and
  **$36 per m² of wood**. A window costs more in cutting than it saves in wood. Opening it through the edge (a notch)
  saves money.
- **No per-file fee**, so merging identical parts (one wedge file) is tidier but saves about $0.
- **Pockets aren't offered.** A shape on a POCKET layer was cut through as a hole. "Additional processes" are only
  custom instructions, bending, brushed finish and paint. So summer pockets would need a manual quote (not done).

## Re-quote after optimizing (2026-10-20, saved project)
Notched H deck, one wedge part (x14 = 12 + 2 spares), crush ribs, foot relief. All Baltic birch 19mm, CNC router, mm.

| File | Size | Qty | Line |
|---|---|---|---|
| heater-cheek.dxf | 372 × 94 | 2 | $23.62 |
| top.dxf | 860 × 860 | 1 | $92.77 |
| deck.dxf | 780 × 780 | 1 | $102.38 |
| leg-plate-a.dxf | 110 × 385 | 4 | $58.80 |
| leg-plate-b.dxf | 110 × 385 | 4 | $58.84 |
| wedge.dxf | 60 × 17.6 | 14 | $17.50 |

Subtotal **$353.91** (price model predicted $354.03), shipping **FREE** (91 × 91 × 16 cm, 16.6 kg), tax $42.47,
**total $396.38**. That's $23.33 less than the slim-leg quote ($419.71).
