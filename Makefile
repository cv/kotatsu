.PHONY: all dxf preview test clean sync
UV ?= uv

all: test dxf

sync:
	$(UV) sync

dxf preview:
	$(UV) run python -m kotatsu.build

test:
	$(UV) run pytest -q

clean:
	rm -rf out .pytest_cache
