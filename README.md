# A kotatsu with no glue and no screws

<!-- story -->
<!-- page: overview Home -->
[![The finished kotatsu by a wood stove: a plaid blanket over the frame, a laptop on the top showing this design, and a white Persian cat peeking out from underneath](docs/img/home.jpg)](docs/img/home.jpg)

I designed a kotatsu, the low Japanese table with a heater underneath and a quilt draped over it. A CNC
shop cuts every part from birch plywood. It all ships to my door in **one box, for free**, and it goes
together with **no glue and no screws**: wooden wedges, tapped in with a mallet, hold it tight. The 26 parts came to
**CAD $396 with tax** in uMake's cart, and $455 once uMake had finalized the order. The only metal in it is the
heater.

Three things got me there:

1. **I set strict rules up front**, so every idea had to pass them.
2. **I let real limits shrink the design**: the shipping box, the futon I could find, and the price.
3. **I checked everything in code before spending a cent**: strength, wobble, knee room and price.

## The rules

I wanted a kotatsu for the winter. I also wanted to make it myself, and I don't own a workshop. So I made
three rules:

- **Plywood only.** Every joint is wood locking into wood. No glue, nails, screws or brackets. The heater
  and its own screws are the one exception.
- **Order it like a book.** Upload a file, pay, wait for the box. No phone calls, no back-and-forth emails.
  I used [uMake](https://umake.ca), a Canadian shop with an instant online quote.
- **It has to be comfortable.** I sit cross-legged, and my knees need about 76 × 32 cm of clear space
  under the edge.

<!-- page: design Design -->

## How the limits shaped it

This chapter is v1, the table I built and use every evening. Version 2 has its own chapter.

Most of this table was decided by things other than me: a cardboard box, my knees, a bathroom scale and
uMake's price list. Here are the four fights, and who won each one.

This is the very first full design, from the first afternoon: a 120 × 80 cm top in three boards joined
by dovetails, sitting on solid side panels.

![The very first full design: a 120 × 80 top in three boards joined by dovetails, on solid side panels](docs/img/first-design.png)

And this is where it ended up:

![The finished design: a square birch table on four slim legs](docs/img/table.png)

### The top: the box decides

I wanted a big table, 120 × 80 cm. uMake ships free in one box up to 91 cm, so a top that size had to
come in three boards, and joining boards without glue is where the fun was: dovetails, Japanese
arrowheads, salmon tails, fir-cone scales, half maple leaves. I'd drafted a request to commission a
local Secwépemc artist to design one.

![Some of the seam ideas: half maple leaves, tips up on one seam, tips down on the other](docs/img/seams.png)

Then I measured my room again, and it works much better with a square table. A round top looked lovely,
but it cost $200 more to ship, and round futons were hard to find at a fair price. The box won: 86 × 86 cm
in one piece, with no joinery at all. I cancelled the commission, and the seams went into a git tag.

![The top: 120 × 80 in three boards, then 90 cm round, then 86 cm square, drawn to scale against the 91 cm box](docs/img/evolution-top.png)

### The frame: my knees decide

Sitting cross-legged, my knees need a space 30" wide and 12.5" high. The first frame had solid side
panels that slot together at the corners. It was strong and simple, and the strip of wood along each
side (the apron) sat exactly where my knees wanted to be. Tapering the legs and flaring the feet bought a
little room. Dropping the aprons altogether bought all of it. That's a *yagura*: four "+"-shaped corner
legs hold up a flat deck, the heater hangs under the deck, and the middle of each side is open, with
34 cm of clearance under the deck.

![The frame: solid side panels, then tapered and flared legs, then the yagura with no aprons](docs/img/evolution-frame.png)

### The legs: the scale decides

The first yagura legs were plain strips, and the weight crept up. Free shipping stops at about 20 kg, and
the order came to 20.4 kg, which put shipping at $195. Cutting windows in the legs and the deck got it back
under. Then I sketched my own leg shape, twice: full width under the deck, where the joints are, then a
sloped shoulder (a *haunch*) down to a 60 mm leg. It needs no windows.

![The legs: plates with windows, then my first sketch, then my second, slimmer sketch](docs/img/evolution-legs.png)

### The deck: the price list decides

Cutting holes in the deck made the table more expensive. A few test uploads seemed to show why: most of
uMake's price was the router's path, not the wood, and a window is nothing but cutting. Opening each window
out to the edge took the same wood away with a metre less cutting, and about $20 off. Rounding the new
corners (the *fillets*) came last. The notches were the right call, but for a reason I only found in
Version 2.

![The deck: windows, then notches open to the edge, then rounded notches](docs/img/evolution-deck.png)

Here's the frame all together, without its top:

![The frame without its top: crossed leg plates, the H-shaped deck and its wedges](docs/img/frame.png)

## Checking it in code

I couldn't afford to learn things by cutting wood: every mistake would be a new order and another week
of waiting. So the design lives in code, and over a hundred tests try to break it every time something
changes. The tools are the same for both versions; the numbers in this chapter are v1's unless I say so.

Every dimension lives in one file, `params.toml`, including the things I'm not sure of yet:

```toml
[material]
t_nominal = 15.0      # v2: 15 mm throughout (v1 was 18 mm, uMake's "19mm")
t_min = 14.1          # mill tolerance about -0.9, TODO-verify
t_max = 15.7          # mill tolerance about +0.7, TODO-verify

[cnc]
bit_d = 6.35          # 1/4" router bit -> dogbone radius bit_d/2
part_gap = 5.0        # min spacing between parts (uMake)
sheet_margin = 20.0   # margin around sheet (uMake)
```

Python turns it into the outlines the shop cuts (with `shapely` for the 2-D shapes and `numpy` for the
maths), and the tests ask the same questions a woodworker would. The snippets below are from the repo,
lightly trimmed.

### Can a router cut it?

A router bit is round, so it can't cut a sharp inside corner. It leaves a little curve the size of the
bit, and a square edge won't seat in a slot like that. The fix is a *dogbone*: a small circle cut just
past each inside corner. To check that every corner has one, I borrowed a trick from image processing
called *closing*. Grow the shape by the bit's radius, then shrink it back. Anything the bit can't reach
gets filled in, so if the result isn't the same as the drawing, some corner is too sharp:

```python
def closing(g: BaseGeometry, r: float) -> BaseGeometry:
    return g.buffer(r, quad_segs=Q, join_style="round").buffer(-r, quad_segs=Q, join_style="round")


def router_cuttable(g: BaseGeometry, r: float, tol: float = 0.5) -> bool:
    """True if every concave corner already has radius >= r (closing adds no real material)."""
    d = closing(g, r).symmetric_difference(g)
    return all(piece.area < tol for piece in getattr(d, "geoms", [d]))
```

Every frame part goes through it. A square corner leaves about 2.2 mm² behind, which is easy to tell
apart from rounding noise.

### Will it fit together?

This was the scary one. v1's plywood, sold as 18 mm, could be anywhere from 17.0 to 18.9 mm thick, and I
wouldn't know which until the box arrived. So every slot was cut for the thickest sheet (19.2 mm), with two
small bumps on each wall (*crush ribs*), 0.5 mm proud, that narrow it to 18.2 mm. If a sheet turned out
thicker, I'd sand the bumps down. The wedges have a 1:8 taper, so they take up whatever is left. (v2's
15 mm sheet gets the same treatment, for anything from 14.1 to 15.7 mm.)

Each joint test runs three times: at the thinnest, the nominal and the thickest sheet. Here's the one
for the leg wedges. Whatever the deck's real thickness, the gap above it has to land somewhere along
the wedge, thicker than its tip and thinner than its head, and the wedge must stay below the futon:

```python
T_RANGE = (BASE.material.t_min, BASE.material.t_nominal, BASE.material.t_max)


@pytest.mark.parametrize("t_deck", T_RANGE)
def test_leg_wedges_clamp_the_deck(Y, t_deck):
    P, L, parts = Y
    z0, z1 = yagura.leg_hole_z(P)
    top = L.z_deck_bot + t_deck
    wl, wh = yagura.wedge_dims(P, "leg")
    need = z1 - top
    assert wh - wl * P.fit.wedge_taper < need < wh
    assert L.z_deck_top + wh <= L.H - 3, "wedges stay under the futon plane"
```

### Will it wobble?

For v1 there was no big engineering package, just small models I could read. Each leg-to-deck joint is a
handful of springs: the leg's shoulder pressing up under the deck, the wedge pulling up the *tenon* (the
tongue on top of the leg that pokes up through a hole in the deck, the *mortise*), and the tenon's faces
bearing on the sides of its hole. The catch is that wood in contact can push but
not pull: lean on the table and one side of a joint can lift off. The model handles that with
"compression-only" springs, smoothed just enough (a *softplus*) that Newton's method can step across
the moment a gap opens:

```python
EPS = 0.002   # mm: contact smoothing (softplus) so Newton can cross contact changes


def _pos(c):
    return EPS * np.logaddexp(0.0, c / EPS)
```

A firm 100 N sideways push (about 10 kg) swayed v1 about 0.9 mm (v2: 1.5 mm). The model also caught a
sneaky problem before I ordered: the first legs had wood on only one side of each joint, and tapping the
wedge in would have twisted each leg about 9 mm at the foot. A 10 mm shoulder on the other side fixed it.

### Will the top break?

The top is a loose board resting on the tops of the legs. The model treats it as a grid of little
beams that bend and twist like a plate. The legs can hold the top up but can't hold it down, so the
solver works it out in rounds: solve, find any leg that would have to pull, let it go, and solve
again.

```python
for _ in range(30):                                       # compression-only supports
    fixed = sorted(idx(i, j) for i, j in active)
    free = np.setdiff1d(np.arange(N), fixed)
    u = np.zeros(N)
    u[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
    R = F - K @ u                                         # what the pads must push on the top (+ = upward, compression)
    neg = [(i, j) for i, j in active if R[idx(i, j)] < -1e-6]   # pad would have to pull the top down
    if not neg:
        break
    active -= set(neg)
```

Before trusting it, a test checks it against the textbook answer for a square plate with a weight in
the middle (Timoshenko's), and it lands within 3 %. Then come the loads I actually care about:

```python
"nap: cat curled in the middle, laptop pushed back": arms(nap) + curled_cat(0, 120) + laptop,
"slump: flopping down (x1.5) + cat jumping up mid-table (x4)":
    arms(Ld.slump * nap) + paws(Ld.cat_impact * cat, 0, 0) + laptop,
"cat lands on the corner (x4), nobody else": paws(Ld.cat_impact * cat, h - 60, h - 60),
```

On v1's 18 mm top, napping hunched over the table with a 7 kg cat and a laptop used about 7 % of the
wood's strength and sagged it 1 mm. Even an 80 kg adult sitting hard on an edge used about a quarter. v2's
thinner top works harder: 9 % and 37 %.

### What will it cost?

uMake quotes instantly, so I uploaded a few test shapes and wrote down the prices. Each part costs a
rate per square metre plus a rate per metre the bit travels, and the order total follows a curve that
gives bigger orders a discount:

```python
A_RATE, L_RATE = 64.17, 5.84     # per m2 of bounding box, per m of cut (raw units, before the volume curve)
K, B = 12.45, 0.595              # total = K * raw ** B  (two 15mm quotes, 2026-11)


def raw(g) -> float:
    return A_RATE * bbox_m2(g) + L_RATE * features(g)[1]
```

That's the model today. v1's first version charged for the wood actually in each part, plus a little per
hole. It put the real order at $353.38 against the $353.33 I paid, and it said about three-quarters of the
price was cutting, which is why the deck's windows became notches open to the edge. It was right about the
total and wrong about the reason. Version 2's quote showed that uMake charges the wood by each part's
*bounding box*, the smallest rectangle round it. Cutting is about half the price, and a window never saves
money (see The quote, in Version 2).

### Will it fit on the sheet?

All of v1's 26 parts went on one 48 × 96" sheet, and v2's 18 do too. uMake lays out its own sheets, so
this is for anyone cutting it on their own router, and for summer. The packer draws each part on a grid
of 4 mm squares, then uses a Fourier transform to test every position on the sheet at once, the way image software finds a
pattern in a photo:

```python
F = np.fft.rfft2(occ.astype(np.float32), sh)
M = np.fft.rfft2(m[::-1, ::-1].astype(np.float32), sh)
corr = np.fft.irfft2(F * M, sh)[mh - 1:H, mw - 1:W]
return corr < 0.5
```

Big parts go first and the wedges fall into the gaps. A test then measures the real distances: no two
parts are closer than 7.35 mm (the shop asks for 5, and the bit needs room to pass between them), and
nothing crosses the 20 mm margin.

The same packer folds the parts flat into the top's footprint for summer.

![Off-season storage: three flat layers inside the top's footprint](docs/img/storage.png)

<!-- page: build Build -->

## Building it

The box arrived at the end of October: one flat parcel, with every part in a single shrink-wrapped stack.
The feline QA department was eager to begin inspections.

[![The opened box on the living-room floor: every part in one shrink-wrapped stack, and a ginger cat looking up](docs/img/build-1-box.jpg)](docs/img/build-1-box.jpg)

Unwrapped, it's the H-shaped deck, the two heater cheeks, eight leg plates crossed into four "+" legs, and
a small pile of wedges. The top waits at the side.

[![The parts laid out on the cardboard: the deck with its two heater cheeks, four crossed legs, the wedges, and the top leaning at the side](docs/img/build-2-parts.jpg)](docs/img/build-2-parts.jpg)

The legs stand up, the deck drops over their eight tenons, and the cheeks hang through it. A wedge goes
through every tenon and cheek tab. For now I pushed them in by hand, not with a mallet, so the table still
comes apart easily.

[![The frame standing on its four legs, with a wedge through every tenon and cheek tab](docs/img/build-3-frame.jpg)](docs/img/build-3-frame.jpg)

Flipped over, the heater screws in between the two cheeks, after drilling a pilot hole for each screw.
Right way up again, it hangs under the deck, grille down.

[![The frame upside down, with the heater sitting between the two cheeks](docs/img/build-4-heater.jpg)](docs/img/build-4-heater.jpg)
[![Looking up from the floor: the heater hanging under the deck between its cheeks, next to a leg](docs/img/build-5-under.jpg)](docs/img/build-5-under.jpg)

Putting the frame together took under a minute. The heater's holes took about five more, most of them
spent looking for the right drill bit.

## In use

At first a fleece blanket I had at hand went over the frame, with the top sitting on it. The futon I ended up
with is an oversized king quilt, 120 × 120 in, and it works really well. It's tea, crosswords, and the cats
keeping an eye on things. The heater is incredibly warm and comfortable. I cranked it for a couple of hours to get rid of
the factory smell, then lowered it to medium.

[![From above: a crossword and a phone on the birch top, with the plaid blanket draped all round](docs/img/use-crossword.jpg)](docs/img/use-crossword.jpg)
[![From above: a cast-iron teapot and a crossword on the top, and the ginger cat lying on its back by the blanket](docs/img/use-tea.jpg)](docs/img/use-tea.jpg)
[![The table under its plaid blanket, a white Persian cat sitting beside it and the ginger cat in a tunnel underneath](docs/img/use-blanket.jpg)](docs/img/use-blanket.jpg)
[![A crossword on the top, and both cats on the rug beyond it](docs/img/use-cats.jpg)](docs/img/use-cats.jpg)

<!-- page: v2 Version 2 -->

## Version 2

v1 works, and it gets used every evening. Living with it showed me four things I'd change:

- **The heater sat low.** It hung under the deck, right where shins go.
- **A lighter box.**
- **Fewer wedges.** Let gravity do some of the work.
- **Rounder corners.**

Version 2 is designed, checked and quoted, but not ordered yet. This chapter is how it got there, detours
included: two chairs I dropped, and a first set of legs I replaced.

### The heater moves into the deck

The deck now has a hole in the middle, and the two heater cheeks became a cradle. I screw the heater
between them on the floor, then lower the whole thing into the hole. An ear at each end of the cheeks
rests on the deck, so gravity holds it up, and in summer it lifts straight out. That's four fewer wedges,
and 304 mm of clear height under the heater instead of 286.

It started higher, at 323 mm, until I noticed that the heater's control panel (the plug, switch and knob)
sits on one end, where the deck would be. Now the heater hangs just low enough for the panel to clear the
deck. Its screws are near its top, so the cheeks only need to reach a little below them: they're 46 mm tall.

### Thinner plywood

Every part drops from 18 to 15 mm, and each joint is checked again across the range the shop's 15 mm sheet
might really measure (14.1 to 15.7 mm, TODO-verify). The top bends a little more: when an adult sits hard on
its edge, it sags about 7 mm instead of 4 (9 on the thinnest sheet). A test quote showed that 15 mm costs
about the same as 18 mm, so the saving is weight, not money.

### An X deck and a squircle top

The deck becomes an X: a pad at each corner, a ring round the heater, and four arms at 45° joining them,
with a big fillet in every inside corner. v1 had rejected an X deck, because its openings let the futon sag
right where the knees go. The ring round the heater fixes that. Each corner pad keeps only the wood that has
a job: round the mortise, under the wedge, and over the tops of the legs.

The top is a *squircle*: a curve that eases into its straight edges, where a radius starts suddenly. I liked
it so much that the legs got the same treatment. The haunch is now one smooth S-curve instead of a slope with
two small fillets, and the feet and shoulders are squircles too, as round as their jobs allow. (The feet stand
on just 8 mm at each end, so they can't get much rounder.)

### Fewer wedges: the first legs

v1's legs were two plates crossed into a "+" at each corner, each plate with a tenon and a wedge. Could
gravity hold them instead? Not on its own: the wobble model says the frame would sway about 9 mm under a
light push. But one wedge per leg is enough, if the wedges alternate. Each leg's other plate is trapped
between the floor and the wedged-down deck, and hangs on its partner when I lift the frame. That plate
doesn't even need a tenon, so the deck had 4 mortises instead of 8. The spring model counted the
gravity-held plates as doing nothing, and still got only 2 mm of sway under a hard shove (v1: under 1 mm).

These legs didn't last. The next check found them weaker than they looked.

### A second opinion

v1's checks are small models I can read. For v2 I wanted a heavier check, so a second AI agent wrote a
*finite-element* model (FEA: each part cut into small triangles that are solved together) of the three parts
that carry load: the top, the deck and the leg plates. It worked on its own branch and reported back:

- **The top:** the simple model was right, within 10 %.
- **The deck:** it works harder than I thought: up to about 68 % of its strength under a hard press on the
  ring round the heater, not 40 %. Arms at 45° to the grain are softer and weaker than the simple model
  assumed. That's fine as long as the wedges stay tight; with slack wedges it was overstressed, so I'll
  re-tap them every season. (The final deck, further on, does better.)
- **The legs:** a real problem. Above the slot where the two plates cross, the wedged plate is two separate
  22 mm fingers, and the wedge hangs the whole joint's bending on one of them. My spring model had quietly
  treated the slot as glued shut. A hard 200 N shove used 160 % of the leg's strength and swayed it 12 mm.

My first fix, a shallow slot in one plate and a deep one in the other, made it worse: the peak just moved to
the new slot's bottom. The plain fix worked: the narrow part of the legs went from 60 to 70 mm. The same shove
then used 87 % at worst and swayed the frame 7.2 mm, for 0.25 kg and 2 cm of room between the legs at shin
height (none at the knees).

### Seeing the stresses

Numbers in a table are easy to skim past, so the 3-D view can now paint them on the parts. Pick a load case
and the part turns blue where it's idle, yellow at half its strength and red at all of it. It bends,
exaggerated, as the load comes on and off.

![The FEA heat map in the 3-D view: the X deck under a hand pressing on the ring beside a cheek, mostly blue, warming to yellow in the arm's fillet near the hand](docs/img/v2-fea.jpg)

The first version taught me something about the model, too. In the "+" legs' case, one plate swung right
through the other. Nothing was wrong with the joint. Each part is analysed on its own, its neighbours standing
in as springs and supports, and the view had drawn one plate bending while the rest of the frame stood still.
At true scale, the slot round the other plate narrows by 0.2 mm at most, and that plate has 0.9 mm to spare.
Now the frame moves with the analysed part: the feet stay put, the deck sways, and the other plates lean along.

### Two chairs

There was room on the sheet and in the budget for two **zaisu**: legless floor chairs with a back. Each was
five parts and no wedges. The seat board's tabs went through the side frames, so sitting down held the chair
together and stopped it tipping back. The stretcher and the back hooked in, then dropped 6 mm to lock. They
were squircles all over: a big sweep where the post meets the runner, round post tops, and cut-outs in the
seat and the back shaped like the top.

![The 3-D view: two zaisu on the long sides of the kotatsu, each with its cushion, the futon draped over the frame and the top on it](docs/img/v2-zaisu.jpg)

The first draft had back posts working at 15 % of their strength, so I asked for less wood. That turned up
something more interesting: the posts were the wrong place to look. Leaning back pushes the back panel and
the seat board face-on, across their 15 mm, and nothing was checking those. They worked at about 40–46 %, so
they stayed as they were. The posts went from 60 to 50 mm (the least that leaves the shop's 15 mm of wood
beside their slots), and now stopped at the top of the back instead of standing 13 cm above it. The FEA then
found a hot spot nobody had looked at: the small inside corner behind each back post, where it meets the
runner's short tail. A hard flop back used 85 % of the wood's strength there. A bigger curve in that corner,
and a runner 4 cm longer to make room for it, brought it down to 68 % for 54 g a chair, and made the chair
harder to tip back. Each chair came to about 3.4 kg.

The chairs also taught me how I sit. The seat board sat as low as the shop's rules allow, 31 mm off the
floor, but my knee height (32 cm cross-legged) was measured on the bare floor, and a chair raises it by the
whole seat. With my knees under the table's edge, that left room for only a thin, firm cushion (4–5 cm). It
also showed a hole in the comfort model: it had never checked the top itself, so any knee height "fitted". On
a zaisu I'll sit with my legs out under the table instead: thighs under the deck, feet under the heater. My
cushions are 10 cm thick, and even if they didn't squash at all there'd be room to spare. On the
floor-pillow sides v2 has about the same knee room as v1: a little more height, and 2 mm less reach under
the top's edge.

### The quote

The whole thing, table and both chairs, quoted at **$501.66**: 28 parts, all instant, shipping free in one
91 × 91 × 20 cm box. That was 6 % more than my price model expected, and part by part it was further off: the
open X deck and the chairs' side frames were a quarter dearer than predicted, small solid parts cheaper. The
pattern gave it away. uMake charges the wood by each part's **bounding box**, the smallest rectangle round
it, not by the wood actually in it. Fitted that way, every line but the tiny wedge matches within 2 %. So
v1's lesson needs a correction: a window never saves money, only weight. It just adds cutting. (It still had
to happen in v1, where weight was what stood between me and free shipping.)

Then I took the chairs out of the quote. The table alone was **$328.53**, so the two zaisu were adding $173,
and I'd found an adjustable zaisu online for about $70, delivered. That settled it: the plywood chairs went
into the archive (the `zaisu-archive` tag has them, FEA and all), and I'm buying one. What they taught me
stays: on a chair I sit with my legs out, and the comfort model now knows a knee can't go higher than the top.

### Diagonal legs

With the design settled I kept poking at it, and asked what the legs could be if they didn't have to be two
crossed plates. The idea I liked best was the simplest: one plate per corner, standing on the diagonal. Half
the leg plates, less cutting, and from every side you'd see a single thin edge. The catch showed up in the
numbers straight away. Twist the frame, and a single plate has nothing to resist with but its own thin edge
on the deck: the joint rocks open at about 32 N.

The rescue is a **crosspiece**: a small board that drops into a slot in the plate's head, across it. The deck
bears on its top edge, so the joint now has a 90 mm base against twisting, and stays shut up to about 190 N
pushed at a corner. Then the FEA shaped the head. A tall crosspiece needed a deep slot, and the slot's bottom
landed in the leg's haunch, where it used 183 % of the plate's strength under a hard shove. A short one
(25 mm) and a higher haunch brought it to 84–95 %. A round-bottomed slot brought it to 75 %, with no dogbones
at all, since the crosspiece's square edges can sit on the curve.

On the diagonal, the squircle top's edge comes closest to the legs, so the posts had to end 14 mm in from the
corner. Each leg's outer edge sweeps in to there in one long curve, all the way from the foot, so it reads as part of the leg.

![The diagonal legs in the 3-D view, with the top, futon and rug hidden: one plate on each corner's diagonal, a crosspiece under each corner of the X deck, a wedge across each arm](docs/img/v2-diagonal.jpg)

### Smoothing every curve

Once I knew uMake charges by the bounding box, wood inside a part's outline was free, so I could go after
looks for nothing. The legs got a soft taper below the joints, so each leg's inner edge is one long curve from
the shoulder to the foot. (On the "+" legs the taper even made them a little stronger, 81 % instead of 87: the
lower leg gives a little, so the joint at the top takes less.) The heater cheeks and the wedges' heads got
rounder squircle corners, and the top got softer ones.

On the diagonal legs, a last pass shaved and smoothed every curve that didn't have a job. The legs taper in
one long line, the crosspieces arch underneath, and the deck's arms flare into the ring and the pads with much
bigger fillets. Each corner pad became one smooth outline, flaring out of its arm like a trumpet, with rounded
far corners: nothing left to fight with sandpaper. The bigger fillets made the deck stronger, too: a hard
press on the ring now uses 60 % of its strength, and with slack wedges it stays under it (97 %, was 127 %).

The rest is handwork: an undercut under the top's edge, so it reads thinner (a 9 mm rim on the 15 mm top),
and a small roundover and oil on every edge.

### Summer

In summer the table goes flat into a stack the size of its top, as v1 does: two layers, about 3 cm.

![Summer storage: the top, then the deck with the leg plates, crosspieces, cheeks and wedges laid round it, all inside the top's footprint](docs/img/v2-storage.png)

With the heater now in the deck, the futon lies right over it, so I measured it on v1: on high, the top of
the heater reaches about 40 °C, warm to the hand. That should be fine to cover, but the heater's manual has
the last word on clearances (TODO-verify).

### Where v2 stands

Against the "+" legs, the diagonal ones are better nearly everywhere. uMake quoted the table at **$303.98**,
$24 less than the "+" legs' $328.02. The cutting drops from 22.5 to 16.7 m, the table is 0.8 kg lighter, and
there's 22 mm more room between the legs. In the FEA they're a little stronger and stiffer too: under the hard
shove, 75 % of the legs' strength and 6.1 mm of sway, against 80 % and 7.1 mm. The one new job is at the
fit-up: each crosspiece is cut half a millimetre tall, and I sand its top edge until the deck sits on it and
on the plate's shoulders together. (The "+" legs are in the archive, tag `plus-legs-archive`.)

So, against my four wishes: the heater rides 18 mm higher and lifts out, the box is about 5 kg lighter, the
wedges go from 14 to 6, and every corner is rounder.

![v1's cut parts above v2's, to the same scale: the square top becomes a squircle, the H deck an X with the heater's hole in the middle, the eight leg plates become four diagonal ones with a small crosspiece each, the cheeks lose their tabs, and the wedges go from 14 to 6](docs/img/v2-parts.png)

| | v1 | v2 |
|---|---|---|
| Parts | 26 | 18 |
| Weight | 15.9 kg | 10.5 kg |
| Wedges | 14 | 6 (4 + 2 spares) |
| Clear height under the heater | 286 mm | 304 mm |
| A hard 200 N shove, finite elements | not checked | 75 % of the legs' strength, 6.1 mm of sway |
| uMake | $353.33 in the cart ($405.83 once uMake finalized it) | $303.98 (a quote, not an order; about $340 with tax; the "+" legs quoted $328.02) |

Before I order it, I want to measure how I really sit (no tape to hand yet), and I'd like to know how thick
uMake's "15mm" sheet really is (TODO-verify). A local yard, Windsor Plywood in Vernon, measures its 15 mm
Baltic birch at 15.0 ± 0.1 mm, right in the middle of what the joints take.

<!-- page: overview -->

## Where it stands

I placed the v1 order in October 2026. One surprise: uMake's checkout ends with "a representative will
reach out to confirm". So I still got one email, and the final invoice was $405.83 before tax, $52.50 more
than the cart (TODO-verify what was added). Next, the table comes apart again and goes to the garage for
sanding and oil.

Version 2 is designed, checked and quoted ($303.98, not ordered yet): lighter, with the heater up in the
deck, one diagonal leg at each corner, and a finite-element check that found (and fixed) weak legs. See
the Version 2 chapter.

I worked through v1 over about two days with an AI coding agent. I made the choices and drew
the sketches. It wrote the geometry code and tests, ran the numbers and filled in the quote forms.

<!-- page: make Make your own -->

## Make your own

<!-- github-only -->

The website has the drawings, a 3-D view, the cut sheets and all the numbers:
**https://lixo.org/kotatsu/**.

<!-- /github-only -->

The cut files (DXF, in millimetres) are at **https://lixo.org/kotatsu/dxf/**, and the code that makes
them is at **https://github.com/cv/kotatsu**.

| Part | Detail |
|---|---|
| Top | 860 × 860 × 15 mm squircle, one piece, sits loose on the frame with the futon in between |
| Frame | four diagonal legs (one plate a corner, a crosspiece in its head) under an X-shaped deck |
| Heater | 120 V 400 W replacement kotatsu heater, 29 × 29 × 5 cm, screwed between 2 cheeks that hang in a well in the deck |
| Joints | wedged through-tenons and slotted crosspieces; 6 wedges (2 spare) |
| Height | about 41 cm with a futon |
| Order | 18 parts, about 10.5 kg, one 91 cm box; quoted at CAD $303.98 + tax on uMake (Nov 2026, not ordered yet) |

These are v2's files. v1, the table in the Build chapter (26 parts in 18 mm, CAD $353 + tax in October
2026), is at the git tag `v1-ordered`.

```sh
uv sync
make test      # the checks
make dxf       # out/dxf/parts/*.dxf, sheet layouts and out/BOM.md
make site      # the website, in out/site
make dev       # serve it on :8765 and rebuild on every change
```

`PLAN.md` has the decisions and open questions. `docs/` has the research on the shop, heater, futon
and quote. `AGENTS.md` has the project's rules.

### Make it yours

Every size is a number in `params.toml`. Change one, run `make all` and `make test`, and the parts, cut
sheets, price, weight and 3-D view all follow. The tests tell you when a change breaks something. Here's
what a few changes do to v2, run through the same code (the prices are the price model's, which came in
4 % under uMake's last real quote):

| Change | What happens |
|---|---|
| A smaller top, 76 × 76 cm | $269 instead of $291, and 8.8 kg. But the frame shrinks with it: my knees reach only 34 mm under the edge (the test wants 35), and the room between the legs drops from 659 to 559 mm. The knee tests fail. |
| A bigger top, 100 × 100 cm | $324, and 13.4 kg, still under the free-shipping weight. But the top alone needs a 105 cm box, so uMake adds about $195 for shipping, and an adult sitting on its edge goes past the load test's limit. The parcel test fails. |
| A lower frame, 355 mm instead of 385 | It sways less (1.2 mm at 100 N, against 1.5), but the deck's underside drops to 314 mm, under the 317.5 mm my knees need sitting cross-legged, and shins get less room under the heater. The knee tests fail. Set your own in `[comfort]`. |
| A bigger heater, 33 × 33 cm | The cheeks and the well move apart by themselves. Every test passes, and the price goes up about $1.50. |

Measure your own heater and put its size in `[heater]`. Don't guess it from a listing.

Earlier versions and ideas I built and then dropped are kept as git tags, so you can check one out and
build it:

- **`v1-ordered`**: v1, as ordered and built.
- **`plus-legs-archive`**: v2's first legs, two crossed plates at each corner.
- **`zaisu-archive`**: the two plywood zaisu, with their FEA.
- **`show-top-archive`**: the quote pack for a "show" top in solid wood or stone, researched and dropped.

- **`seams-archive`**: the 120 × 80 cm top in three boards, joined by decorative seams (dovetails,
  arrowheads, maple leaves), and a 90 cm round top. Round looked lovely, but it cost $199 to ship, and
  round futons wouldn't ship here.
- **`frame-variants-archive`**: the solid-sided frame with tapered legs and flared feet, and a yagura
  with splayed legs.
- **`options-archive`**: windows in the deck and legs, an X-shaped deck, lighter-looking cuts, and
  modules that link several tables into a row.

### Ordering somewhere else

I've only ordered from uMake, in Canada. Elsewhere, look for a shop that **CNC-routes 15 mm (5/8") birch plywood**
from a DXF and can cut a part 86 cm across. Ideally it shows a price online, so there's no back-and-forth. If
its plywood is another thickness (16, 18 mm…), set its real range in `params.toml` (`[material]`) and rebuild:
the joints follow, and `make test` tells you if anything no longer fits.

These are the shops I found in October and November 2026, searching in each region's language. I haven't ordered
from any of them, so check before you rely on one (details and sources are in `docs/research.md`). **Online** means
the site shows a price for your file; **quote** means someone replies.

**North America**

| Where | Shop | Price | What I found |
|---|---|---|---|
| Canada | [uMake](https://www.umake.ca/) | Online | What I use. CNC-routed Baltic birch, "15mm" included; free shipping in one box up to 91 cm and about 20 kg |
| Canada | [EZCNC](https://ezcnc.ca/) | Online | Upload a DXF and configure the cut. All-birch and bamboo plywood, but in 3/4" (19 mm), not 5/8". Roughly $36 a part however small: a 19 mm version of this table (with the "+" legs) came to $787 before shipping, against uMake's $328 |
| Canada (Vancouver) | [Fab Lab Vancouver](https://www.fablabvan.ca/service) | Quote | A 72 × 96" router at $2.50 a minute, $80 minimum |
| Canada (Vancouver) | [CNC Cutting Services](https://cnccuttingservices.ca/), [Mosswood Millwork](https://www.mosswoodmillwork.com/cnc-cutting-routing-vancouver) | Quote | Local routing shops for furniture parts |
| US | [Xometry](https://www.xometry.com/capabilities/cnc-machining-service/cnc-routing/) | Online | CNC routing in Baltic birch plywood, free standard shipping in the US. Thicknesses not checked |
| US (I think) | [ConceptCut](https://conceptcut.net/) | Online | Baltic birch in 18 mm only, on 48 × 96" sheets: v1's thickness |
| US | [SendCutSend](https://sendcutsend.com/materials/baltic-birch-plywood/) | Online | Birch only up to 12 mm, and parts up to 44 × 44": too small for the top |
| Mexico | [Arteknia](https://arteknia.com.mx/) | Quote | Routes triplay (plywood) and MDF; prices within a working day; ships anywhere in Mexico |

**Europe**

| Where | Shop | Price | What I found |
|---|---|---|---|
| UK | [Chop Shop CNC](https://chopshopcnc.com/cnccutting), [Cut Online](https://www.cut-online.co.uk/) | Online | Both price a DXF online; Cut Online checks it before confirming (1220 × 2440 bed) |
| Ireland | [Woodworkers.ie](https://www.woodworkers.ie/pages/cnc-cutting) (Dublin) | Quote | Stocks sheet goods and CNC-cuts them to your drawing |
| France | [Vectorealism](https://www.vectorealism.com/fr/fraisage-cnc/) | Quote | Birch plywood in **15** and 18 mm, sheets up to 180 × 120 cm; quote by email, usually the same day |
| Netherlands | [Moderne Ambacht](https://www.moderneambacht.com/prijzen/) | Calculator | €90 an hour of routing; birch plywood by the sheet. [Vormig](https://vormig.nl/multiplex-cnc-frezen/) and [De Firma CNC](https://defirmacnc.nl/services/cnc-utrecht/multiplex-laten-frezen/) quote birch multiplex too |
| Sweden | [ScandCut](https://www.scandcut.se/tra) | Online | BB/BB birch plywood 4–30 mm, cut by **waterjet** from your CAD file; ready in 5 days |
| Switzerland | [Zunder Atelier](https://zunderatelier.ch/cncofferte/) | Online estimate | A configurator with birch plywood, but only 4, 10 or 16 mm; then a person checks it |
| Spain (Madrid) | [Manoj Sawlani Studio](https://manojsawlani.com/es/presupuesto-instantaneo/) | Online estimate | Upload a DXF, pick CNC and a material, see a price; they confirm. Materials not checked |
| Italy | [Godea](https://www.godea.it/) | Quote | CNC milling of wood over 1 cm thick, besides laser cutting |
| Poland | [LaserTrade](https://lasertrade.pl/frezowanie-sklejki) | Quotes | A platform: your request goes to several CNC shops, which send free quotes; birch plywood among them |

**Asia**

| Where | Shop | Price | What I found |
|---|---|---|---|
| Japan | [EMARF](https://emarf.co/) | Online | Upload a DXF (or use its CAD plugins), see the price, order; workshops across Japan cut it. White シナ (linden) plywood, ±0.5 mm |
| Japan (Yokohama) | [Fabnode](https://fabnode.jp/) | Online estimate | Upload a DXF for a rough price; a 2440 × 1220 mm router, bits 3–12 mm; they supply the plywood |
| South Korea | [차츰우드 (Chachum Wood)](https://ccwood.kkb.kr/) | Quote | Russian B/BB birch plywood 4–30 mm, CNC-cut in its own factory; send the drawing on KakaoTalk |
| Taiwan (Taichung) | [雲手木工 (YunShou)](https://yunshou.com/cnc-service/) | Quote | Cuts up to 4 × 8 ft; stocks birch plywood (樺木夾板); send a DXF on LINE; from NT$1,000 a sheet |
| China | Taobao / Alibaba sellers, [Tianfu Plywood](https://www.tianfuplywood.com/en/product/CNC-cutting-plywood.html) | Quote | Many sellers cut plywood to a drawing (来图加工), priced by chat. Tianfu makes birch plywood and CNC-cuts parts for furniture makers |
| India (Mumbai) | [HyperFabs](https://hyperfabs.com/) | Online | Instant quotes; its listing says CNC-routed plywood up to 18 mm |
| Malaysia | [Ledanim](https://ledanim.com/OCQ_Main.html) | Online | Upload a DXF, pick material, thickness and sheet size, get a quote for CNC routing. Wood stock not checked |

**Elsewhere**

| Where | Shop | Price | What I found |
|---|---|---|---|
| Australia | [Laser Cutting Experts](https://lasercuttingexperts.com.au/cnc-router-cut-plywood) (Sydney), [GV CNC](https://www.gvcnc.com.au/quote.html) (Victoria) | Online | Both price a DXF for plywood routing |
| New Zealand | [CNC Cutting Direct](https://www.cnccutting.co.nz/cnc-services) (Christchurch) | Quote | Upload a DXF; delivers NZ-wide |
| Brazil | [ZiOLAB](https://www.ziolab.com.br/corte-compensado/) | Quote | Router-cut compensado in 4–25 mm, **15** mm included |
| Argentina | [Trebol CNC](https://trebolcnc.com.ar/servicios) | Quote | A 2 × 3 m router; guatambú and phenolic multilaminado |
| Chile | [CNC Studio](https://cncstudio.cl/) (Santiago), [Andes Maker](https://andesmaker.cl/comocotizar/) | Quote | Both route terciado (plywood) from a DXF; Andes Maker can cut plywood you bring |
| Colombia (Medellín) | [Makers Medellín](https://makersmedellin.com/cotizacion/) | Online | Upload a DXF or SVG, pick material and thickness, see a price |
| Peru (Lima) | [Laser Cut Peru](https://lasercutperu.com/servicio/corte-router-cnc-lima-peru/) | Quote | Routes plywood up to 60 mm on a 1.3 × 2.5 m bed |

Whichever shop you pick, tell the code about it in `params.toml`: the bit size (`[cnc] bit_d`, for the dogbones),
its sheet sizes, the gap it wants between parts and round the sheet's edge, the real thickness range of its plywood
(`[material]`), and its shipping limits (`[shipping]`). The 91 cm box is uMake's rule, not a law of nature. A
makerspace with a CNC router works too: the DXFs are ordinary cut files.

**Caveats.** The plywood strength figures are rough textbook values, so read the load numbers as "lots of margin",
not as a certificate. uMake sells this sheet as "15mm", and the joints are designed for 14.1–15.7 mm. Follow your
heater's instructions and clearances, and make sure it's rated for your mains supply.

<!-- /story -->

## License

MIT, see `LICENSE`.
