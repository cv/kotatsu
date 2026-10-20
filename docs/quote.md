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
