# Research notes

Retrieved 2026 from uMake.ca public pages and the help text built into app.umake.ca.

## uMake.ca: ordering
- Instant quote at <https://app.umake.ca>. You upload a file, choose the process, material,
  thickness, quantity and delivery, then pay. An account/login is needed to see the materials and
  thicknesses (the materials API returns 401 without one).
- Accepted files: DXF, DWG, AI, SVG, PDF (STEP for some processes).
- The app shows a "Tolerance Guide" confirmation before you order. Some parts get flagged
  `needs_manual_quote`. **We must avoid that flag, because it means staff contact.**
- Source: <https://www.umake.ca/>, app bundle `main.318c06b4.js`.

## Processes
| Process | Plywood thickness | Bed / max part | Cut tolerance (ply) |
|---|---|---|---|
| CO₂ laser | ≤ 1/4" (≈6 mm) for plywood ("up to 1/4"" on the service page) | 48×36" or 60×60" (the pages disagree) | ±0.30–0.45 mm |
| CNC router | up to 3/4"+ (Baltic birch) | max part 61×140"; birch sheets 48×96", 60×60", 60×120" | ±0.30–0.45 mm |

**Conclusion:** laser-cut 6 mm plywood is too thin and floppy for a 1200 × 800 top, and too weak for
a glue-free frame (and lamination would need glue). We use **CNC-routed 18 mm Baltic birch**,
which is ordered through the same online flow. The laser stays an option for thin accessory parts
or engraving.

Sources: <https://www.umake.ca/co2-laser-cutting-engraving>, <https://www.umake.ca/canada-custom-cnc-parts>

## CNC router file rules (uMake checklist)
- Check scale and units.
- Leave **≥ 5 mm between parts** and a **20 mm margin** around the sheet.
- **No cut part smaller than the material thickness.**
- No overlapping or double lines. Use outlines only (closed).
- One file for all sheets, or one file per thickness. Mark engravings/pockets with different colours.
- Inside corners get a radius of half the bit: 1/8" bit → ~1.6 mm, 1/4" bit → ~3.2 mm. **Use dogbones.**
  The shop says a minimal dogbone leaves only ~0.5 mm of visible overcut.
- **Holding tabs** ≈ 0.1875" (4.8 mm) wide and half the thickness deep. Sand them off.
  Keep ≥ 0.4" between nodes.

## Stock thickness (sanded plywood, mill tolerance)
| Nominal | Tolerance |
|---|---|
| 6.5 mm (1/4") | +0.45 / −0.55 |
| 9 mm (3/8") | +0.45 / −0.65 |
| 12 mm (1/2") | +0.55 / −0.75 |
| 18 mm (3/4") | **+0.85 / −1.05** |

North American "3/4"" often measures ~23/32" (18.3 mm). → Joints must tolerate **~17.0–18.9 mm**
stock, or use the actual thickness if the app shows it.

## Shipping (policy updated 2025-12-02)
| Class | Limits | Cost | Human contact? |
|---|---|---|---|
| Standard parcel | ≤ 48" longest side, ≤ 50 lb/box, L+girth ≤ 108" | free on orders ≥ $250 CAD | no |
| Oversize parcel | 48–60" longest side **or** 51–150 lb | calculated at checkout | no |
| Freight / LTL | > 60" **or** > 150 lb **or** needs a pallet | "quoted separately by a uMake team member" | **yes, avoid** |

- The 1200 mm top is 47.2". Packed, the box will probably be just over 48", so it becomes an
  **oversize parcel**. That is still priced automatically at checkout.
- The frame parts (≤ ~1150 mm) can go in a standard box. Keep each box ≤ 50 lb.
- Source: <https://www.umake.ca/canada-shipping-terms>

## Weight estimate basis
Baltic birch is ~680–720 kg/m³, so 18 mm ≈ **12.6 kg/m²**. The top (0.96 m²) is ≈ 12 kg / 27 lb.

## Kotatsu heater (TODO-verify)
- Japanese units are 100 V. In Canada we need a **120 V, cUL/CSA/ETL-listed** replacement-style
  kotatsu heater unit, or a properly rated transformer (not recommended).
- Typical units: a square or rectangular mounting plate of about 250–330 mm, fixed with 4 wood
  screws (included) to the underside of the frame or a centre board. They hang about 80–120 mm
  below it and draw about 300–600 W.
- Once a heater is chosen, record: mounting-hole pattern, plate size, hang depth, required
  clearances, where the cord exits, and where the controller goes.

## Alternatives (fallbacks, not yet verified for 18 mm birch + Canadian shipping)
- SendCutSend (US): ships to Canada; check its wood thicknesses and size limits.
- Ponoko: laser only and small beds, so not suitable for the top.
