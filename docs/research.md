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

## Other shops
Found in October 2026 (searched in English, French, German, Dutch, Japanese, Spanish and Portuguese) and checked only against
their public pages. I haven't ordered from any of them. Everything here is **TODO-verify** before you rely
on it: thickness range, largest part, bit size, and whether the price really comes back instantly.
What this design needs: CNC routing of 18 mm (3/4") birch plywood from a DXF, and a part 860 mm across.

| Region | Shop | What its pages say | Source |
|---|---|---|---|
| Canada | EZCNC | Upload a DXF, choose a sheet material, configure the routing; a guided quote confirms size, material, thickness and quantity | <https://ezcnc.ca/services/plywood-mdf-cutting> |
| Canada (Quebec) | Laseo | "Prix instantané" for CNC routing; lists Baltic birch plywood; free delivery from $49. Thicknesses not checked | <https://www.laseo.ca/services/cncrouting/> |
| US? | ConceptCut | Instant quotes from a DXF, Baltic birch 18 mm on 48 × 96" sheets, ±0.5 mm; priced per sheet used after nesting + per inch of cut; ships in 3–5 days. No address or shipping area on the site | <https://conceptcut.net/> |
| US | SendCutSend | Baltic birch .125–.472" (3.18–12 mm), CNC-routed from .354"; instant pricing up to 44 × 44", custom quote to 46 × 46". Too thin for this design as drawn | <https://sendcutsend.com/materials/baltic-birch-plywood/> |
| US | Ponoko | Laser only, small beds: can't cut the top | (earlier note) |
| US | Xometry | Has a CNC routing service (Big Blue Saw's address now redirects to Xometry). Not checked for plywood | <https://www.xometry.com/capabilities/cnc-machining-service/cnc-routing/> |
| UK | Chop Shop CNC | "Upload your files and receive an instant quote" (DXF; material, thickness, quantity); delivery anywhere in the UK. Materials not checked | <https://chopshopcnc.com/cnccutting> |
| UK | Cut Online | Fill in a form for an instant quote, then they review the drawing and confirm; 1220 × 2440 bed, up to 50 mm | <https://www.cut-online.co.uk/> |
| France | Vectorealism | Online CNC routing: birch plywood 15 and 18 mm, sheets 60 × 60, 120 × 120 and 180 × 120 cm; upload a 2-D drawing, quote by email (usually same day); 7 working days | <https://www.vectorealism.com/fr/fraisage-cnc/> |
| Netherlands | Moderne Ambacht | Public price calculator: €90/h routing (about half an hour a sheet), €60 setup, 18 mm birch €105.71 a sheet, excl. 21 % VAT | <https://www.moderneambacht.com/prijzen/> |
| Australia | Laser Cutting Experts | CNC router cut plywood; instant pricing for cut-ready CAD; pickup in Botany NSW or freight anywhere in Australia | <https://lasercuttingexperts.com.au/cnc-router-cut-plywood> |
| Australia | GV CNC (Shepparton VIC) | "Drop DXF files for routing": MDF, plywood, acrylic; DXF priced instantly; inside corners get about a 3 mm radius | <https://www.gvcnc.com.au/quote.html> |
| New Zealand | CNC Cutting Direct (Christchurch) | Upload a DXF for a quote (not instant); NZ-wide delivery | <https://www.cnccutting.co.nz/cnc-services> |
| India | HyperFabs (Mumbai) | Instant quotes; search listing says CNC-routed plywood up to 18 mm (the service page was missing) | <https://hyperfabs.com/> |
| Brazil | ZiOLAB | Router-cut plywood (compensado) on 1600 × 2200 or 1600 × 2500 mm sheets, 4/6/10/15/18/20/25 mm; "envie seu orçamento" (quote on request). City not checked | <https://www.ziolab.com.br/corte-compensado/> |
| Argentina | Trebol CNC | Router with a 2 × 3 m bed plus a laser; cuts multilaminado de guatambú 3–18 mm and multilaminado fenólico 6/15/18/25 mm (whole sheets); free quote on request. Guatambú and phenolic ply aren't birch: set your own strength and thickness values | <https://trebolcnc.com.ar/servicios> |
| Chile (Santiago) | CNC Studio | Two CNC routers, 2000 × 3000 mm; takes DXF, AI, SVG, PDF, DWG; quote form answered within 24 working hours | <https://cncstudio.cl/> |
| Chile | Andes Maker | Router cutting from a DXF; its quoting guide uses "terciado de 18 mm aportado por el cliente" as the example (you can supply the plywood) | <https://andesmaker.cl/comocotizar/> |
| Colombia (Medellín) | Makers Medellín | "Cotizador CNC instantáneo": upload SVG, DXF, PDF or AI, pick the material and thickness (1–100 mm), get an estimated price at once | <https://makersmedellin.com/cotizacion/> |
| Peru (Lima) | Laser Cut Peru | Router CNC for wood, MDF, plywood and more; cutting area 1.30 × 2.50 m, up to 60 mm thick; free quote by email | <https://lasercutperu.com/servicio/corte-router-cnc-lima-peru/> |

Not useful here: the German "Zuschnitt" shops (auprotec, plattenzuschnitt24, expresszuschnitt) cut straight
panels to size, not shapes from a DXF. Laser shops (Snijlab, formulor) can't cut 18 mm plywood. The
Japanese results were machine sellers and international CNC networks, not plywood routing. In South America,
the instant DXF quotes I found are for laser cutting (Makers Manufatura in Rio de Janeiro, CNCero in Argentina),
which can't cut 18 mm plywood. Makers Medellín was the only instant router quote.

## Nicer woods: who cuts them online (owner question, 2026-11)
Looking for walnut, white oak, "real" birch or hinoki, CNC-routed from a DXF with an instant online price and
shipping to BC. Checked 2026-11; nothing ordered.

| Shop | Where | Sheets that matter | Online price? | Notes / source |
|---|---|---|---|---|
| uMake | Montreal | Baltic birch 3–25 mm (15mm, 16mm, 19mm, 25mm…). Engineered Wood also: aircraft ply, construction ply, hardboard, MDF, melamine particle board, OSB. Composites: ACM, G-10. **No hardwood-veneer plywood** | Instant | Its material menu, 2026-11. The top alone at 19 mm: +$37.37 on the order; at 25 mm: +$97.60 |
| EZCNC | Canada (ships Canada-wide) | **Bamboo plywood 3/4"** (Natural, Caramel), **All-Birch plywood** 1/4, 1/2, 3/4" (birch faces and core), standard plywood 1/2, 3/4", all 48 × 96" | "Calculated pricing" for supported work; unusual work or shipments go to a person | <https://ezcnc.ca/materials/plywood>, <https://ezcnc.ca/services>. Not yet quoted (TODO-verify: price, and whether an 86 cm part ships as a standard package) |
| Laseo | Québec | Baltic birch 9–12 mm only | Instant | <https://www.laseo.ca/materials/merisier-baltique/>. Too thin |
| SendCutSend | US | Baltic birch to 12 mm (.472"), birch plywood, hardboard, MDF | Instant | <https://sendcutsend.com/materials/>. Too thin, 44" parts |
| Xometry | US | Baltic birch (and MDF, plastics) for routing | Instant | <https://www.xometry.com/capabilities/cnc-machining-service/cnc-routing/> |
| ConceptCut | US? | Baltic birch 18 mm only | Instant | <https://conceptcut.net/> |
| CNC Cut to Size | Toronto / Arizona | Baltic birch, "hardwood plywood"; maple, oak, walnut *tabletops* | No: "confirmed per project" by quote brief | <https://cnccuttosize.com/llms-full.txt>. Commercial millwork; breaks the no-email rule |

- **Walnut, white oak and hinoki:** no shop found that cuts them from a DXF with an instant price and ships to BC.
  Veneered hardwood plywood shows up only behind manual quotes. Hinoki plywood is essentially not stocked in North
  America (solid hinoki boards come from specialty lumber dealers).
- **Bamboo** (EZCNC, 3/4") is the only premium-looking sheet on an online quote found so far. It would mean a 19 mm
  version of the design (v1's thickness), or a bamboo top only, with the frame still from uMake.
