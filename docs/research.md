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
(and laminating thin sheets would need glue). So everything is **CNC-routed Baltic birch** (18 mm in v1, 15 mm in
v2), ordered the same way.

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
Baltic birch weighs about 680–720 kg/m³, so 18 mm sheet is about **12.6 kg/m²** (15 mm: about 10.5). In v1 the
86 cm top weighed about 9.3 kg and the whole order about 16 kg; in v2, about 7.6 and 10.5 kg.

## Heaters
Japanese kotatsu heaters run on 100 V. In Canada you want a **120 V replacement-style unit**, ideally with a
cUL, cETL or CSA mark, rather than a transformer. The one I chose, and why, is in `docs/heater.md`.

## Other shops
Found in October 2026 (searched in English, French, German, Dutch, Japanese, Spanish and Portuguese) and checked only against
their public pages. I haven't ordered from any of them. Everything here is **TODO-verify** before you rely
on it: thickness range, largest part, bit size, and whether the price really comes back instantly.
What v1 needed: CNC routing of 18 mm (3/4") birch plywood from a DXF, and a part 860 mm across. (v2 needs 15 mm:
see the next table.)

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

### More shops, for v2's 15 mm (2026-11)
Searched in English, Japanese, Korean, Chinese, German, Spanish, Italian, Polish, Dutch and Swedish; checked against
each shop's own pages, nothing ordered, everything **TODO-verify** (thickness, largest part, bit size, shipping).

| Region | Shop | What its pages say | Source |
|---|---|---|---|
| Japan | EMARF (VUILD) | Upload DXF (or Rhino/Fusion plugins) → see the quote → order; parts cut at workshops across Japan, delivered or picked up. Price = material + machining + finish + system fee + shipping + packing. シナ合板 (white, knot-free; r3.5 advised on sharp corners), thickness ±0.5 mm | <https://emarf.co/>, <https://docs.emarf.co/1525709244d2801b9a79f28ad4edec9b> |
| Japan (Yokohama) | Fabnode | ShopBot router 2440 × 1220 × 120 mm; DXF upload gives an automatic rough estimate (Web見積もり); end mills φ3–12 mm; plywood, MDF, laminated wood supplied by them | <https://fabnode.jp/> |
| Japan | Acoroom 合板部 | Plywood sold and cut; NC router for shapes, but the automatic price covers only rectangles, circles and ovals (up to 1800 × 900) | <https://www.plywood-ac.shop/page/automatic-quote> |
| South Korea | 차츰우드 (Chachum Wood) | Russian B/BB birch plywood 4–30T from one sheet; cutting, CNC, oil, UV coating in its own factory; drawings by KakaoTalk; free delivery from 80 sheets (15T) | <https://ccwood.kkb.kr/> |
| South Korea | 미르조각 (Mir CNC), Namyangju | Birch plywood CNC work from customers' drawings (18T examples) | <https://mircnc.co.kr/> |
| Taiwan (Taichung) | 雲手木工 (YunShou) | Cutting up to 4 × 8 ft (122 × 244 cm); stocks 樺木夾板 3B (birch plywood); DXF or AI by LINE for a quote; from NT$1,000 a sheet plus simple work; pickup or delivery | <https://yunshou.com/cnc-service/> |
| Taiwan (Taichung) | WoodCNC | 4 × 8 ft sheets, one-offs accepted, quotes by LINE | <https://woodcnc.com.tw/> |
| China | Pizhou Tianfu Wood | Plywood maker (birch among others) that also CNC-cuts parts for "global furniture factories, designers, contractors": likely bulk | <https://www.tianfuplywood.com/en/product/CNC-cutting-plywood.html> |
| China | JLCCNC, RapidDirect | Online CNC services with instant quotes, but for metals and plastics; no plywood found | <https://jlccnc.com/>, <https://www.rapiddirect.com/services/cnc-routing/> |
| India (Mumbai) | HyperFabs | Search listing: "Online CNC Routing Service – up to 18 mm plywood, MDF, HDMR, 2–3 days, instant quote" (the page itself returned 404 on 2026-11-08) | <https://hyperfabs.com/services/cnc-routing> |
| Malaysia | Ledanim | Online DXF quote for laser cutting and CNC routing: upload, choose material, thickness and sheet size, review, order (wood stock not checked) | <https://ledanim.com/OCQ_Main.html> |
| Singapore | Plony Industries | Heavy timber CNC for construction ("unlike carpentry CNC services that focus on thin plywood"); enquiry only | <https://www.plonyindustries.com/wood-timber-cnc-cutting-construction-singapore> |
| Sweden | ScandCut | BB/BB birch plywood 4–30 mm (and form plywood), **waterjet**-cut from a CAD file, "pris direkt online", ready in 5 days, ISO 9001/14001 | <https://www.scandcut.se/tra> |
| Switzerland | Zunder Atelier | Online configurator: poplar, pine or birch plywood in 4, 10 or 16 mm; price estimate shown at once, then reviewed by a person; free shipping from CHF 55 | <https://zunderatelier.ch/cncofferte/> |
| Spain (Madrid) | Manoj Sawlani Studio | Upload a DXF (mm), choose fiber laser, CO₂ laser or CNC, a material and thickness: instant estimate, then they confirm feasibility and the final price | <https://manojsawlani.com/es/presupuesto-instantaneo/> |
| Italy | Godea | Online laser service; CNC milling for wood, marble, acrylic over 1 cm thick | <https://www.godea.it/> |
| Poland | LaserTrade | Platform: one request goes to many CNC milling shops, which reply with free quotes; plywood 1–40 mm, birch among the species | <https://lasertrade.pl/frezowanie-sklejki> |
| Netherlands | Vormig, Ritmeester CNC, De Firma CNC | Birch multiplex CNC milling to a drawing; quotes | <https://vormig.nl/multiplex-cnc-frezen/>, <https://defirmacnc.nl/services/cnc-utrecht/multiplex-laten-frezen/> |
| Ireland | Woodworkers.ie (Dublin) | Stocked sheet goods custom- and CNC-cut to your specifications | <https://www.woodworkers.ie/pages/cnc-cutting> |
| Ireland | Fineline | Online DXF shape cutting with nesting and an instant calculator, but MDF, MR-MDF, MFC and HDF only: not plywood | <https://fineline.ie/> |
| US | Xometry | CNC routing lists Baltic birch plywood (with MDF, HDPE, acrylic, ACM…); instant quote; free standard US shipping | <https://www.xometry.com/capabilities/cnc-machining-service/cnc-routing/> |
| Canada (Vancouver) | Fab Lab Vancouver | CNC router 72 × 96 × 6"; $2.50/min machining, $80 minimum per setup | <https://www.fablabvan.ca/service> |
| Canada (Vancouver) | CNC Cutting Services; Mosswood Millwork; Westcoast CNC | Local CNC routing for furniture parts, signs, panels; quotes | <https://cnccuttingservices.ca/>, <https://www.mosswoodmillwork.com/cnc-cutting-routing-vancouver> |
| Mexico | Arteknia | Wood (MDF, triplay, melamine), acrylic, PVC, aluminium; quote within 24 working hours; ships anywhere in Mexico | <https://arteknia.com.mx/> |
| Mexico | Triplay Carpisur | Plywood retailer with a CNC cutting service | <https://carpisur.com.mx/servicios/corte-cnc/> |
| — | Cut Ready CNC | Search listing promised instant plywood/MDF prices; the site returned 404 on 2026-11-08 | (dropped) |

Also seen: Laser Studio (Japan) quotes a DXF in 30 s, but for laser cutting (thickness not checked; lasers seldom
cut 15 mm plywood cleanly); Laseo (Québec) stocks Baltic birch only in 9–12 mm.


## Local route: plywood from Windsor Plywood (Vernon) and a makerspace router (2026-11)
Windsor Plywood's Vernon store answered my price request by email (2026-11; prices before tax, all in stock):

| Sheet | Price | Notes |
|---|---|---|
| Baltic birch, 15 mm (5/8"), B/B, 5 × 5 ft | $115.99 | **measured 15 mm ± 0.1 mm** (our joints take 14.1–15.7) |
| Baltic birch, 18 mm, B/B, 5 × 5 ft | $123.99 | |
| Maple cabinet plywood, ¾", 4 × 8 ft | $189.99 | veneer core, "likely poplar core and import plywood, not the nicest lay-up"; far more plies than Baltic birch, the count varies |
| ... a 4 × 4 ft piece of it | $96.49 | they sell 4 × 4 pieces |
| Maple plywood, 5/8" | none | only with a particleboard core |

What it means for this table (`kotatsu/nest.py`, the diagonal legs): the frame fits one 5 × 5 ft sheet (or a 4 × 4 ft
piece), but the top and the deck can't share a 5 × 5, so the whole table takes **two 5 × 5 sheets of 15 mm Baltic
birch: $231.98 + 12 % tax = $259.82**, with a lot left over. The maple's poplar core would show at the rounded edge;
Baltic birch's even stripes are the look I want. Cutting it means a CNC router: the Shuswap Makerspace has a
medium-to-large one (<https://shuswapmakerspace.ca/equipment-2/>) and a CNC 101 course; membership and router time
are not counted above (TODO-verify).

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

### Hinoki, walnut or white oak from Japan or China (2026-11)
No shop found that cuts hinoki from a DXF with an instant price *and* ships abroad. The closest:

- **Marutoku** (木材通販のマルトク, <https://shop.woodworks-marutoku.com/>, Japan): solid panels, edge-glued
  (幅はぎ), "free cut" up to 1300 × 3800 mm, 10–50 mm thick, rectangle or circle, with corner radius (each
  corner), edge profiles and finish. Online **automatic estimate** (自動見積もり); shipping and special machining
  are added in a confirmation email after ordering (its guide). Ships within Japan only (Hokkaido/Okinawa quoted
  separately), so Canada needs a forwarder (Buyee, Tenso). Lead time 7–17 working days.
  Prices from its configurator for **860 × 860 × 20 mm, corners R150, edges 上下R面 5R + 磨き, natural oil both
  faces** (自然塗料クリアー 両面), incl. Japanese consumption tax:
  - **Hinoki, Japanese, knot-free (【国産材】桧（無節）): ¥39,610**
  - White oak (ホワイトオーク): ¥54,200
  - Walnut (ウォールナット): ¥57,170
- **Getting it here** (estimates, TODO-verify): about 6 kg (hinoki) to 10 kg (walnut) plus packing; EMS takes
  it (max 1.5 m long, length + girth 3 m: this is about 2.6 m). Japan-side shipping to the forwarder, the
  forwarder's fee, EMS to Canada (very roughly $150–250 for 8–12 kg), then GST/PST and any duty and handling.
- **Taobao / AliExpress / Alibaba** (China): hinoki (often Taiwanese 桧木) boards and "custom Japanese hinoki"
  panels, CNC-cut to a drawing (来图来样加工), but priced by chat with the seller.
- **Wood notes for a solid top:** solid wood moves across the grain with the seasons (an 86 cm panel a few mm),
  and the heater warms one face, so finish both faces the same and keep it loose (it already is). Hinoki is soft
  and dents easily; it's prized for its scent and pale, fine grain. A corner radius stands in for the squircle,
  unless the corners are cut by hand from a printed template.

### A solid hinoki top from Marutoku, delivered to Canada (2026-11, JPY 112 = CAD 1, TODO-verify at order time)
Only the top would come from Japan; the frame stays uMake birch (it's under the futon).
- **Strength (FEA, `fea.top_case` with rough solid-hinoki values: E 8.8 GPa along / 0.45 across, splits across
  the grain at ~3 MPa; TODO-verify):** 20 mm: 41 % of strength, 9.5 mm sag; **25 mm: 26 %, 5.0 mm**; 30 mm: 19 %.
  The limit is the stress across the grain (solid wood splits along it), not along it. 25 mm is the pick.
- **Marutoku configurator** (hinoki knot-free, 860 × 860, R150 corners, 5R edges top and bottom, natural clear
  oil both faces, tax in): 20 mm ¥39,610, **25 mm ¥40,390 (CAD ~361)**, 30 mm ¥44,270. Walnut and white oak at
  20 mm: ¥57,170 / ¥54,200. Marutoku sells to Japanese addresses only and confirms the final total (with its
  shipping) by email, in Japanese, so order through a proxy-buying service (e.g. Buyee) that handles that.
- **Shipping:** Marutoku to the proxy's warehouse: not quoted (a large panel; TODO-verify, guess ¥2,000–5,000).
  Proxy fees: guess ~¥1,500 (TODO-verify). **EMS to Canada** (Japan Post, the Oceania/Canada/Mexico/Middle
  East/Europe column): up to 9 kg ¥21,400, 10 kg ¥23,500, about +¥2,100 a kg after. The top weighs ~7.8 kg,
  ~10 kg packed. A 92 × 92 × 6 cm box is 2.88 m in length + girth, just under EMS's usual 3 m limit (TODO-verify
  Canada's limits; a padded box over 95 cm wouldn't go).
- **Into Canada:** CPTPP should make Japanese wood duty-free (TODO-verify the HS code and origin statement);
  GST 5 %, BC PST 7 % if collected at the border, and Canada Post's handling fee (~$10).
- **Total, the hinoki top delivered:** about ¥69,000 before import, **about CAD 660–705 landed**. The uMake order
  without its top: about $271 (model), so the whole table ≈ CAD 965–1,010 against $368 all-birch.

### Show-top materials on the corner posts (FEA, 2026-11; rough handbook strengths, TODO-verify)
`fea.top_case`, worst everyday case vs the "adult sits hard on an edge" case, Tsai-Hill share of strength:

| Top | kg | Everyday worst | Adult on the edge |
|---|---|---|---|
| White oak 20 mm (E 12.3 / 0.8 GPa, splits across at ~5.5 MPa) | 10.9 | 23 %, 5.8 mm sag | 25 % |
| Hard maple 20 mm (~7 MPa across) | 10.2 | 18 % | 20 % |
| Ash 20 mm | 9.7 | 21 % | 23 % |
| Hinoki 20 / 25 mm (~3 MPa across) | 6.2 / 7.8 | 40 % / 26 % | 43 % / 28 % |
| Sintered stone 6 / 9 / 12 mm (~45 MPa) | 10.6 / 16 / 21 | 59 / 27 / 16 % | 121 / 54 / 31 % |
| Quartzite 20 mm (~20 MPa) | 38 | 14 % | 26 % |
| Marble 20 mm (~9 MPa) | 39 | 30 % | 58 % |
| Limestone / travertine 20 mm (~7 MPa) | 35 | 38 % | 74 % |

For wood the everyday loads govern, about as much as edge-sitting. Stone is brittle and natural stone has hidden
flaws, so it wants everyday use under about a third of its strength. Owner's choice (2026-11): **pale wood**, used
carefully (no sitting, coasters): white oak or hard maple at 20 mm, hinoki at 25. Ash is held back until Canada's
ash import rules (emerald ash borer, CFIA) are checked. Hinoki dents about three times as easily as oak.
