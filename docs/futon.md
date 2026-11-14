# Futon and rug

A kotatsu needs a futon draped over the frame, with the top sitting on it. Round futons that ship to
Canada at a fair price turned out to be hard to find, so I made the top an 86 × 86 cm square
(October 2026). I went looking for square futons of 225 cm or more.

## What size?
Sellers go by **futon = top + 110–130 cm** (BarklotJapan, Etsy). For an 86 cm top that's 196–216 cm, so
205 × 205 is right. The 190 × 190 size is sold for 70–80 cm tops, and on this one it barely reaches the
floor. I planned an 80 × 80 in (203 cm) futon; in the end an **oversized king quilt, 120 × 120 in (305 cm)**, went
over v1 and works really well (owner 2026-11). With it go four 25 × 25 in square floor pillows, all on
the 8 ft round rug. That's what the site's 3-D view shows. Draped over the frame, the futon covers about
147 cm of floor, which leaves a ring of rug about 49 cm wide.

I found no 225 × 225 or larger square kotatsu futon that ships to Canada at a fair price:
- amazon.ca only stocks 185–190 cm squares;
- Futon Tokyo only lists 205 cm (from US$433);
- Wataman's 225 × 225 is sold out, and only ships within Japan.

## The best options (October 2026)
The full list is in `docs/futons.toml` and on the site's "Futon & rug" tab.

| Option | Size | Price (CAD, before duty and tax) | Notes |
|---|---|---|---|
| **Etsy · BarklotJapan premium cotton flannel, grey** | 205 × 205 | **$229.61, free delivery** | Made in Japan, quilted, with corner ties |
| Etsy · BarklotJapan cotton flannel, green (mat optional) | 205 × 205 | $250.22 (with the mat, $325) | Also brown, pink and blue |
| Etsy · BarklotJapan washable, green | 205 × 205 | $322.34 | Machine washable |
| Futon Tokyo GOTS organic cotton | 205 × 205 | about $598 + shipping | Handmade, and pricey |
| amazon.ca AZUMAYA / ROOM ESSENCE / KEN JAPAN | 190 × 190 | $157–258 | Small for this top |
| **DIY: Douglas down-alternative duvet (full/queen) + a queen cover** | about 229 × 229 | **$139 + $45–80** | See below |

## The duvet option
A queen duvet (about 88–90 × 90–92 in; TODO-verify Douglas's own size chart) in a 90 × 90 in cover comes
out at about 229 cm. That's bigger than a 205 cm kotatsu futon, and cheaper too, at about $185–220 all in,
with free shipping from Douglas. It works on a kotatsu, with a few things to know:
- **Loft.** A bed duvet is puffier than a quilted kotatsu futon. The top rests on the corner posts *through*
  the duvet, so it sits about 1–2 cm higher and may rock a little until the fill settles. A lightweight
  duvet works better than an all-season one.
- **Heat.** Polyester fill is fine. In v1 the heater hangs under the solid deck; in v2 the futon lies over the
  heater's top (about 40 °C on high, `docs/heater.md`), as on a traditional open frame.
- **Cover.** Pick a tightly woven cotton or linen cover with a zip, so it can go in the wash. Kotatsu futons
  meet feet, crumbs and tea. Some amazon.ca covers said "cannot ship to your location", so check at checkout.

## Safety
Keep the futon away from the heater's grille and fan, which face down. In v1 the heater hangs under the solid
deck, so they never touch; in v2 the futon lies just over the heater's top, the face away from the grille, which the
heater's manual allows (owner 2026-11, `docs/heater.md`). Either way, don't tuck the futon *inside* the frame, under the heater.

## A seating set: one long shikibuton and two square cushions (planned, owner 2026-11)
I'd like a matching set of cotton floor pieces, all of them seats: a long, narrow shikibuton that runs under the
table between the legs and out from under the quilt on two sides, and two square cushions on the other two sides.
The shikibuton also makes a nap mattress, with my legs under the heater.
- **Shikibuton: 25 × 75 in (635 × 1905 mm), about 3½ in (90 mm) thick.** The legs leave a clear gap of about
  710 mm between them at its height (the kicked feet splay out), so it clears them by about 40 mm on each side
  (`tests/test_room.py`). A twin shikibuton (38 in, 965 mm) won't fit.
- **Cushions: 24 × 24 in (610 mm), the same thickness and fabric.**
- I've asked a Canadian maker about custom sizes (TODO-verify sizes, thickness and price). The 3-D view and the room
  plan draw this set (`room.seats = "set"` in params.toml; `"zabuton"` draws the four square pillows instead).
- Lying down under the table, keep your chest out from under the heater: on a 90 mm mattress there's about 21 cm
  between it and the heater's underside. Legs and hips under, short naps, heater on low.
