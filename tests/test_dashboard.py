"""Tests for the dashboard's static site generator (docs + gallery)."""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dashboard.markdown_lite import markdown_to_html
from dashboard.site import build_site


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
        for f in fields:
            assert "|" not in f["type"]


def test_build_site_produces_index_and_gallery(tmp_path):
    out = build_site(str(tmp_path / "site"))
    index = out / "index.html"
    assert index.exists()
    html = index.read_text(encoding="utf-8")
    assert "<h1>mudplot</h1>" in html
    assert "Engine reference" in html
    gallery_dir = out / "gallery"
    pngs = list(gallery_dir.glob("*.png"))
    assert len(pngs) >= 4
    for name in [
        "palette_safety.png",
        "redundant_encoding.png",
        "tex_preview.png",
        "heatmap.png",
    ]:
        assert (gallery_dir / name).exists()


def test_build_site_references_gallery_images_in_html(tmp_path):
    out = build_site(str(tmp_path / "site"))
    html = (out / "index.html").read_text(encoding="utf-8")
    assert "gallery/palette_safety.png" in html
