"""The website's story pages: the README, split at its <!-- page: ... --> markers by kotatsu/site.py."""
import re

from kotatsu import site
from kotatsu.params import ROOT

README = (ROOT / "README.md").read_text()


def test_story_pages():
    pages = site.story()
    assert [p["id"] for p in pages] == ["overview", "design", "build", "v2", "make"]
    assert all(p["title"] and p["md"].strip() for p in pages)
    home = pages[0]["md"]
    assert "## The rules" in home and "## Where it stands" in home      # home collects two stretches
    assert home.index("## The rules") < home.index("## Where it stands")
    for p in pages:
        assert "<!--" not in p["md"], f"a marker leaked into page {p['id']}"
        assert "](docs/img/" not in p["md"]


def test_github_only_blocks_stay_off_the_site():
    make = next(p for p in site.story() if p["id"] == "make")["md"]
    assert "The website has" in README and "The website has" not in make
    assert "lixo.org/kotatsu/dxf/" in make


def test_story_images_exist_and_have_alt_text():
    images = re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", README)
    assert images
    for alt, path in images:
        assert alt.strip(), f"{path} has no alt text"
        assert (ROOT / path).is_file(), f"{path} is missing"


def test_pages_without_markers():
    pages = site.story("<!-- story -->\nhello ![a](docs/img/x.png)\n<!-- /story -->")
    assert pages == [{"id": "overview", "title": "Overview", "md": "\nhello ![a](img/x.png)\n"}]
