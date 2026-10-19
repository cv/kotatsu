# Heater selection

Researched 2026-10 on amazon.ca, delivering to rural BC. Prices are in CAD and
include import fees where stated.

## Requirements
- **120 V native** (Canada). No 100 V Japanese unit, and no step-up/down transformer.
- A kotatsu "replacement unit" form factor: a ~29 cm square box that mounts under the frame
  with screws. The only hardware in the build is the screws that come with it.
- Thermal cut-off or fuse, and adjustable heat.
- Ships to rural BC without anyone phoning or emailing anyone.

## Candidates
| | **PaletteLife** (B0CKBS16YY) | **Zuomeng** (B0HF7DW7YD) | Yamazen YHF-M506 / Metro 600 W |
|---|---|---|---|
| Voltage | 120 V ✅ | 120 V ✅ | 100 V ❌ (needs a transformer, rejected) |
| Element | quartz tube + fan, 400 W | PTC ceramic, 400 W, thermostat 104–149 °F | quartz/halogen 500–600 W |
| Size | 292 × 292 × 51 mm (11.5 × 11.5 × 2") | 290 × 290 × 50 mm (11.42 × 11.42 × 1.97") | — |
| Safety | power fuse, resin housing | over-current + over-heat cut-off with a reset button; PTC self-limits | — |
| Mounting | **4 screws through the side flanges** into crossbars spaced at the heater width (the traditional yagura way) | method 1: the same side-screw crossbars; method 2: **4 L-brackets** under a flat board (included) | — |
| Cord | detachable IEC cord, knob on the unit | detachable cord, 3 m (9.84 ft), knob on the unit | — |
| Reviews | **4.7★ / 58 ratings** (DIY kotatsu builders) | 3.9★, few ratings, new listing | — |
| Price / delivery | **$258.47** with import fees, free delivery (~1 week). Only 2 left in stock | $276.91 + $13.71 delivery, ships from Amazon | $226–232 |
| Listed cUL / cETL / CSA? | not stated ⚠️ | not stated ⚠️ | — |

Sources: amazon.ca/dp/B0CKBS16YY, amazon.ca/dp/B0HF7DW7YD,
forkinthe.net/kotatsu-heaters (this guide says 120 V kotatsu heaters are rare in North America)

## Recommendation
**PaletteLife 120 V 400 W** is the main pick. It has a proven track record with DIY builds, is the
cheapest of the 120 V units, ships free, and has a fan that spreads heat under a large 120 × 80 top.
The **Zuomeng PTC** is the backup, or the pick if you prefer PTC's self-limiting behaviour and
thermostat over a quartz tube.

The frame supports **both mounting methods** (`[heater] mount = "side" | "bracket"`):
- **side** (default): two on-edge plywood "heater cheeks" pass through the deck. Their inner faces
  sit at the heater width + 1 mm, and the heater's side screws go into the plywood face grain.
- **bracket**: a flat deck pad; the L-brackets screw into its underside.

### Caveats
- **400 W is modest for a 120 × 80 kotatsu.** Japanese units of this size are usually 600 W, but
  they run on 100 V, so they're not an option here. Use a thick kotatsu futon (and a
  shikifuton/mat under it) and expect a slower warm-up. Reviewers report it gets plenty warm.
- **Certification is not advertised on either listing.** When the heater arrives, look for a
  cUL/cETL/CSA mark on the rating label. If there isn't one, consider returning it (30-day
  returns), because it may matter for home insurance. You can also use Amazon's "Ask a question"
  feature before buying; that's still not a phone call or an email to a vendor.
- Don't block the fan or grille. Keep the futon and blankets off the unit, and follow the
  clearances in its manual.

## Workflow consequence
**Buy the heater first.** Measure it with calipers: body width/depth/height, the screw-hole
positions (height from the top face and distance from the corners), and the screw diameter and
length. Enter the numbers in `params.toml [heater]` before ordering the plywood. The CAD is not
frozen until this is done.
