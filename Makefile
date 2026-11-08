.PHONY: all dxf preview test fea site dev clean sync quote
UV ?= uv
PORT ?= 8765

all: test dxf fea site

sync:
	$(UV) sync

dxf preview:
	$(UV) run python -m kotatsu.build

test:
	$(UV) run pytest -q

fea:             ## FEA heat maps for the 3-D view (out/fea.json; a minute or so; skipped when up to date)
	$(UV) run python -m kotatsu.fea_view --if-stale

quote:           ## the show top's quote pack (out/quote: the DXF, a one-page drawing, the request text)
	$(UV) run python -m kotatsu.quote_pack

site:            ## build out/site (static; serve it over http)
	$(UV) run python -m kotatsu.site

dev:             ## build + serve on :$(PORT) + rebuild on change (page live-reloads)
	$(UV) run python -m kotatsu.site --dev --port $(PORT)

clean:
	rm -rf out .pytest_cache
