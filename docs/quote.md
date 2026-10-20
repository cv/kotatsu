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
