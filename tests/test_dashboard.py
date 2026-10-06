"""Tests for the dashboard's static site generator (docs + gallery)."""

import sys
from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dashboard import plot_gallery
from dashboard.markdown_lite import markdown_to_html
from dashboard.plot_gallery import GALLERY_EXAMPLES
from dashboard.site import build_site
from mudplot.capabilities import LAYER_TYPES


@pytest.fixture(scope="module")
def built_site(tmp_path_factory):
    return build_site(str(tmp_path_factory.mktemp("dashboard") / "site"))


def test_markdown_headers_and_inline():
    html = markdown_to_html("# Title\n\nSome **bold** and `code`.\n")
    assert "<h1>Title</h1>" in html
    assert "<strong>bold</strong>" in html
    assert "<code>code</code>" in html


def test_markdown_list():
    html = markdown_to_html("- one\n- two\n")
    assert "<ul>" in html
    assert "<li>one</li>" in html
    assert "<li>two</li>" in html


def test_markdown_table():
    md = "| a | b |\n|---|---|\n| 1 | 2 |\n"
    html = markdown_to_html(md)
    assert "<table>" in html
    assert "<th>a</th>" in html
    assert "<td>1</td>" in html


def test_markdown_table_with_pipe_in_type_name_is_safe():
    # regression: capabilities() must not leak a bare "|" into table cells
    from mudplot.capabilities import capabilities

    for fields in capabilities()["actions"].values():
        for field in fields:
            assert "|" not in field["type"]


def test_build_site_produces_index_and_gallery(built_site):
    index = built_site / "index.html"
    assert index.exists()
    html = index.read_text(encoding="utf-8")
    assert "<h1>mudplot</h1>" in html
    assert "Engine reference" in html

    design_gallery = built_site / "gallery"
    for name in [
        "palette_safety.png",
        "redundant_encoding.png",
        "tex_preview.png",
        "heatmap.png",
    ]:
        assert (design_gallery / name).exists()

    expected = set(LAYER_TYPES)
    assert len(GALLERY_EXAMPLES) == len(expected)
    assert {example.name for example in GALLERY_EXAMPLES} == expected
    assert {path.stem for path in (built_site / "plots").glob("*.png")} == expected
    assert {
        path.name.removesuffix(".mplot.json")
        for path in (built_site / "plots").glob("*.mplot.json")
    } == expected
    assert not plt.get_fignums()


def test_gallery_preserves_existing_files(tmp_path, monkeypatch):
    # The generator may replace its own artifacts, never delete unrelated files.
    example = GALLERY_EXAMPLES[0]
    monkeypatch.setattr(plot_gallery, "GALLERY_EXAMPLES", (example,))
    unrelated = {"notes.json": b"keep notes", "other.png": b"keep image"}
    for name, contents in unrelated.items():
        (tmp_path / name).write_bytes(contents)

    plot_gallery.render_plot_gallery(tmp_path, write_specs=True)
    for name, contents in unrelated.items():
        assert (tmp_path / name).read_bytes() == contents

    # Rendering must succeed before the matching editable spec is replaced.
    (tmp_path / f"{example.name}.mplot.json").write_bytes(b"keep previous spec")
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}

    def fail_save(*args, **kwargs):
        raise ValueError("simulated render failure")

    monkeypatch.setattr("mudplot.api.Plot.save", fail_save)
    with pytest.raises(ValueError, match="simulated render failure"):
        plot_gallery.render_plot_gallery(tmp_path, write_specs=True)
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before
    assert not plt.get_fignums()


def test_build_site_references_gallery_images_in_html(built_site):
    html = (built_site / "index.html").read_text(encoding="utf-8")
    assert "gallery/palette_safety.png" in html
    for name in LAYER_TYPES:
        assert f"plots/{name}.png" in html
        assert f'href="plots/{name}.mplot.json"' in html
        assert f'id="plot-{name}"' in html
