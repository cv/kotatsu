.PHONY: all dxf preview test fea heights site dev clean sync optimize
UV ?= uv
PORT ?= 8765

all: test dxf fea heights site

sync:
	$(UV) sync

dxf preview:
	$(UV) run python -m kotatsu.build

test:
	$(UV) run pytest -q

fea:             ## FEA heat maps for the 3-D view (out/fea.json; a minute or so; skipped when up to date)
	$(UV) run python -m kotatsu.fea_view --if-stale

heights:         ## the 3-D view's height slider: the table every mm, -50 to +50 (out/heights; a few minutes; skipped when up to date)
	$(UV) run python -m kotatsu.heights --if-stale

optimize:        ## the design-space search (out/optimize/: results.json and map.png; a few minutes)
	$(UV) run python -m kotatsu.optimize

site:            ## build out/site (static; serve it over http)
	$(UV) run python -m kotatsu.site

dev:             ## build + serve on :$(PORT) + rebuild on change (page live-reloads)
	$(UV) run python -m kotatsu.site --dev --port $(PORT)

clean:
	rm -rf out .pytest_cache
