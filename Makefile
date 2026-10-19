.PHONY: all dxf preview test site dev clean sync
UV ?= uv
PORT ?= 8765

all: test dxf site

sync:
	$(UV) sync

dxf preview:
	$(UV) run python -m kotatsu.build

test:
	$(UV) run pytest -q

site:            ## build out/site (static; serve it over http)
	$(UV) run python -m kotatsu.site

dev:             ## build + serve on :$(PORT) + rebuild on change (page live-reloads)
	$(UV) run python -m kotatsu.site --dev --port $(PORT)

clean:
	rm -rf out .pytest_cache
