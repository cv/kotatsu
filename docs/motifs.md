# BC-inspired motifs for the top seams

## Two kinds of "BC native"

**1. BC's land, plants and animals.** These are free to use. The prototypes on the site are below.

**2. Indigenous art of the Pacific Northwest and the BC Interior.** This includes Northwest Coast
formline (ovoids, U-forms, split-U, crest figures) and Interior Salish coiled cedar-root basketry
patterns (imbrication, step and zig-zag designs). These are living cultural traditions, not public
motifs. Many crests and designs belong to particular nations, clans or families. Copying the
*look* (an "ovoid-ish" dovetail, a formline-style salmon) is appropriation, even for a personal
piece of furniture. **We won't generate imitations.**

The respectful route, if you want it:
- **Commission or license a design from an Indigenous artist**, ideally one from the Nation whose
  territory you live in (TODO-verify for your exact location).
- Ask the artist how the design may be used: a one-off piece, credit, whether it's fine for it to
  be CNC-cut into seams.
- **Technically this is easy:** the generator can take a seam drawn by the artist as an SVG path
  (a planned `kind = "path"`). We'd add only what the router needs: inside corners of at least
  3.2 mm radius, 0.2 mm clearance, and a check that the seam locks.

## Nature motifs (prototyped, in `params.toml`)

| Option | Inspiration | Notes |
|---|---|---|
| `bc-salmon` | Salmon running up the Columbia | Forked salmon-tail dovetails. Both seams point the same way (`mirror = false`), so the "fish" all swim upstream. |
| `bc-sword-fern` | Sword fern (*Polystichum munitum*) | The middle board is the stem. 7 angled leaflets on each side get smaller toward the "tip" of the frond. |
| `bc-fir-cone`, `bc-fir-cone-4` | Douglas-fir cone bracts | Dovetail heads ending in 3 lobes (2 short side lobes and a long "mouse tail"). Either 3 alternating, or 4 pointing into the middle board, small-big-big-small. |
| `bc-crevasse` | Glacier crevasses (Illecillewaet, Selkirks) | Ten leaning wedge "cracks" in an en-echelon pattern. 2 of them are real dovetails that do the locking. The spike tips are thin, so sand them gently and handle with care. |

## More nature ideas (not built yet)

- **Selkirk / Monashee skyline:** a seam traced from a real elevation profile (for example the view
  from a mountain lookout), with 2 hidden dovetails so it still locks. We can pull the profile from
  open DEM data.
- **Snowflake / hoarfrost:** hexagonal heads with small side spurs. The BC interior gets a lot of snow.
- **River braid:** long, shallow, staggered chevrons, like yabane but asymmetric.
- **Cedar bark:** long narrow interlocking strips. Keep these abstract; cedar bark weaving is
  itself an Indigenous practice.

## Arrows (Japanese *ya* motifs; in `params.toml`)

These are plain geometric barbed points. They're deliberately **not** styled after stone points or other
"Native" imagery. *Yajiri* (arrowhead) and *yabane* (arrow feather) are classic Japanese patterns, which
suits a kotatsu.

| Option | Notes |
|---|---|
| `yajiri-3` | 3 barbed arrowheads, alternating direction. The barbs are the lock. |
| `yajiri-yabane` | 2 large tilted arrowheads and a smaller one in the centre (the bold-yabane-rhythm layout, with arrowheads). |
| `ya-karimata` | 3 arrows with *karimata* (wild-goose fork) heads: a crescent between two prongs. Fletching in the style of a *kamon* (family crest): a wide trapezoid with a deep V cut at the back. |
| `ya-chigai` | A pair of arrows (*hitote*: *haya* + *otoya*) flying opposite ways, set off-centre (*fukinsei*, asymmetry). |
| `ya-togari` | 3 arrows with long willow-leaf (*yanagi-ba*) heads. |
| `ya-arrows` | The middle board becomes 3 arrows: forked fletching on the left seam and heads on the right seam (`kind = "combo"`, one spec per seam). |

Geometry rule: `neck_len - barb` must be at least 15 mm (about 30 is better). Otherwise the pocket behind
the barbs is sealed off, the other board can't fill it, and the seam doesn't lock. The generator raises
an error when this happens.

Karimata rule: each prong stays at least `prong_w` wide (24 mm) along its whole length. A bare crescent
circle bulges out and pinches the prongs below the bit width. Their tips then break off as islands,
which `test_boards_have_no_holes_or_islands` now catches.

## Maple leaves (`maple-3`, `maple-5`)

The outline is the official Flag of Canada leaf, extracted from the public-domain SVG on Wikimedia
Commons by `kotatsu/maple_extract.py` into `kotatsu/data/maple_leaf.json`. Each leaf is split along its
axis, and that axis lies exactly on the seam line. The visible joint is half a leaf, sticking out
alternately to one side and then the other, with the tip always pointing the same way.

There's no hidden dovetail. The lock comes from the leaf itself: its up-swept points overhang the notches
between the lobes, so the boards can't be pulled apart (checked by `test_seam_resists_pulling_apart`).
