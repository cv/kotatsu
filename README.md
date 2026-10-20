# Kotatsu: glue-free CNC birch plywood

A **kotatsu** (Japanese low heated table) whose parts are all cut from 18 mm Baltic birch plywood and
ordered online from a CNC shop ([uMake.ca](https://umake.ca)). There's **no glue, screws or other
hardware**: the joints are cross-laps and wedged through-tenons. The only metal is the heater, which
screws into two plywood cheeks.

**Website (drawings, 3-D view, cut sheets, numbers):** https://lixo.org/kotatsu/
**Cut files (DXF, mm):** https://lixo.org/kotatsu/dxf/

| | |
|---|---|
| Top | 860 × 860 mm, one piece, rests loose on the frame (with the futon in between) |
| Frame | "yagura" style: four "+" corner legs (8 plates) carry a notched deck; heater hangs under the deck |
| Height | 385 mm frame + 18 mm top, about 40–41 cm with a futon |
| Parts | top, deck, 8 leg plates (2 shapes), 2 heater cheeks, 14 wedges (2 spare), 26 pieces in all |
| Order | about 17 kg in one 91 × 91 × 16 cm box. Quoted at CAD $353 + tax on uMake (Oct 2026), free shipping |
| Heater | 120 V 400 W replacement kotatsu heater, 29 × 29 × 5 cm, side-screw mount (see `docs/heater.md`) |

## How it works

Everything comes from one parameter file, `params.toml`. A Python package (`kotatsu/`) turns it into
part shapes, then:

- **checks** them with pytest: router-cuttable inside corners (dogbones), fits that tolerate the
  17.0–18.9 mm thickness range, knee room, tipping, wobble, and strength under everyday loads (a plate
  model of the top, validated against textbook plate solutions);
- **lays out** the parts on stock sheets and exports DXF files, one per part and one per sheet;
- **estimates** the uMake price with a model fitted to test uploads (`kotatsu/price.py`);
- **builds** the static website in `out/site`.

```sh
uv sync
make test      # pytest
make dxf       # out/dxf/parts/*.dxf + sheet layouts + out/BOM.md
make site      # out/site (static)
make dev       # serve on :8765 and rebuild on change
```

`PLAN.md` records the design decisions and open questions. `docs/` has the vendor, heater, futon and
quote research. `AGENTS.md` lists the project's rules: no hardware, online-only ordering, and so on.

## Status and caveats

- The first set of parts has been ordered; the design hasn't been assembled yet. Expect changes after the
  first fit-up.
- The plywood strength and stiffness values are rough textbook figures (marked TODO-verify). The load and
  wobble numbers are for comparing options, not certification.
- uMake sells the sheet as "19mm". The joints are designed for 17.0–18.9 mm, and the crush ribs in the
  cross-lap slots are meant to be sanded to fit.
- Follow the heater maker's instructions and clearances. The heater must be rated for your mains supply.
- Earlier explorations are kept as git tags: `seams-archive` (split tops with decorative seams) and
  `frame-variants-archive` (slab-sided and splayed-leg frames).

## License

MIT, see `LICENSE`.
