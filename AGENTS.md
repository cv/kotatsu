# AGENTS.md: working on this kotatsu

## The goal
A **kotatsu** (a low Japanese heated table) built only from **flat CNC-cut birch plywood**, ordered online
from **uMake.ca**, shipped to the owner's door, with no phone calls and no back-and-forth emails. The design
being built is an **86 × 86 cm square top** on a **yagura frame**: four "+" corner legs under an H-shaped
deck, with the heater hanging under the deck. `PLAN.md` has the details and the README tells the story.
That design has been **ordered** (git tag `v1-ordered`). Changes to the cut parts from here are a v2:
say so in the commit, and don't let tidy-ups change the geometry by accident.

What this repo produces:
1. Parametric Python that builds every part from one parameter file, `params.toml`.
2. Upload-ready cut files (DXF, millimetres), one per part and one per sheet.
3. Previews, a bill of materials (`out/BOM.md`), weight and price estimates, and assembly notes.
4. A static website (`out/site`, published from `main` to GitHub Pages).

## Hard rules
- **No glue, nails, screws, bolts, dowels, inserts or other hardware.** Joints are plywood only: cross-laps,
  wedged through-tenons, tabs and slots. The one exception is the heater and the screws that come with it.
- **Online ordering only.** Every part must quote instantly in app.umake.ca. Nothing that needs a manual
  quote, freight or a pallet. In practice:
  - free shipping needs the whole order to pack into **one box of 91 cm or less** and weigh **under about
    20 kg** (that's what the cart does; see `docs/quote.md`);
  - bigger boxes ship as oversize parcels, priced automatically at checkout. That's allowed, but costs about $200;
  - never design a part over 60" (1524 mm) or an order over 150 lb, because that means freight and staff;
  - don't order extra processes (bending, finishing, assembly) from the shop.
- **Electrical safety.** The heater must be rated for Canadian mains (120 V, 60 Hz), ideally cUL, cETL or
  CSA listed. Never plan around a 100 V Japanese heater without a transformer. The heater maker's clearances
  and instructions override this design.
- **Focus.** Keep only the design being built in the code. Archive alternatives with a git tag first, then
  delete them. (So far: `seams-archive`, `frame-variants-archive` and `options-archive`.)
- **Indigenous designs.** Don't imitate them. Use them only if they come from, or are licensed by, an
  Indigenous artist.

## Shop facts (sources in `docs/research.md`)
- uMake's laser only cuts plywood up to about 6 mm. The 18 mm birch must be **CNC-routed**, ordered the same way.
- The router bit can't cut a sharp inside corner: it leaves a radius of half its width (1/8" or 1/4" bits).
  Every slot or mortise that takes a square edge **needs dogbones**.
- Leave at least 5 mm between parts and a 20 mm sheet margin. No feature smaller than the sheet's thickness.
  Closed outlines only, with no duplicate or overlapping lines.
- The shop leaves small holding tabs (about 4.8 mm wide, half the thickness deep); they get sanded off.
- **"18 mm" birch can be anywhere from 17.0 to 18.9 mm**, and uMake sells it as "19mm". Every joint must work
  across that range. Use wedges or crush ribs, never exact press fits.
- Birch sheets come in 48 × 96", 60 × 60" and 60 × 120".
- About three-quarters of the price is cutting (`kotatsu/price.py`). Fewer metres of cut beats less wood.

## Do
- Keep **one source of truth**: every dimension lives in `params.toml`. Never hard-code one in geometry code.
- Work in **millimetres**. DXF files use `$INSUNITS = 4`. Keep cut lines on their own layer.
- Rebuild with one command (`make all`) and check with `make test`: closed shapes, cuttable corners, parts
  that fit the sheet, slots wide enough for the thickest sheet, joints that hold at the thinnest, weight
  and box limits.
- Look at the previews after changing geometry. (Image viewers can cache by file name, so use a new name.)
- **Make small, focused git commits**, one logical change each, with clear messages.
- Record decisions and open questions in `PLAN.md`, and shop facts with their sources in `docs/research.md`.
- Mark anything unconfirmed (heater sizes, live prices, real sheet thickness, material strengths) **TODO-verify**.
- Keep personal data (addresses, account or order numbers, local paths) out of the repo. It's public.

## Don't
- Don't add hardware, glue or fasteners to fix a joint. Redesign the joint.
- Don't assume the laser can cut 18 mm plywood.
- Don't commit generated files, caches or virtual environments. `out/` is rebuilt by CI.
- Don't hand-edit DXF files. Change the parameters or the generator.
- Don't guess the heater's mounting geometry. Use the measured values in `[heater]` (`docs/heater.md`).
- Don't compute geometry in the website's JavaScript. Python computes it, and JS only draws it.

## Tools
- **Python 3.12 or newer via `uv`.** Don't use the system Python.
- `ezdxf` writes the DXFs. `shapely` does the 2-D geometry (booleans, dogbones, clearances, areas).
  `matplotlib` draws previews. `numpy` runs the sheet layout and the load models. `pytest` runs the checks.
- Analysis modules: `comfort.py` (knee room, tipping), `stiffness.py` (wobble), `loads.py` (the top under
  everyday loads), `price.py` (uMake's price), `optimize.py` (a small search over the deck and leg knobs),
  `storage.py` (flat packing for summer).
- `make` targets: `all`, `test`, `dxf`, `site`, `dev`, `clean`.
- **The website.** `make dev` serves it at http://127.0.0.1:8765, rebuilds on every change, and the page
  reloads by itself.
  - `kotatsu/site.py` writes `out/site/data.json`: geometry, stats, parameters, test results, docs, and the
    README's story (between the `<!-- story -->` markers). The page in `web/` is plain HTML and JavaScript,
    with no build step and no npm.
  - The JS libraries are pinned versions on jsdelivr, loaded through an import map: `three` (3-D),
    `lil-gui` (controls) and `marked` (Markdown).
  - 2-D pan and zoom is a small custom controller in `web/viewer2d.js`. It stays sharp at any zoom and reads
    positions in millimetres.
  - The 3-D view's textures (birch, plywood edges, fabric, rug, floor) are drawn on canvases at load
    (`web/textures.js`); the "ambiance" props (tea things, laptop, book, the cat) are in `web/ambiance.js`.
  - `.github/workflows/pages.yml` builds the DXFs and the site (running the tests) on every push to `main`,
    and publishes them to GitHub Pages, with the DXFs under `/dxf/`.
  - The public site sits behind a CDN that keeps scripts for hours, so the build tags every local .js/.css
    address with `?v=<hash>`. Add new scripts as plain relative imports; the tagging is automatic.

## Layout
```
params.toml          every dimension and tolerance
kotatsu/             the generator: parts, joints, layout, export, checks, site
tests/               pytest checks
web/                 the website's static files
docs/                shop, heater, futon and quote research; docs/img has the README's pictures
tools/               one-off scripts (the README's before/after strips)
out/                 generated DXFs, previews and site (not in git)
PLAN.md              the design as ordered: decisions, numbers, open questions
```
