"""LAY-03: registry TeX geometry reaches actual files, not only preview."""

import json
import re
import struct
from xml.etree import ElementTree as ET

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import pytest
from mudplot.tex import PT_PER_INCH
from mudplot.theme import AVAILABLE_JOURNALS, JOURNAL_SIZES, journal_overrides


@pytest.mark.parametrize("preset", sorted(mp.TEX_PRESETS))
@pytest.mark.parametrize("columns", [1, 2])
@pytest.mark.parametrize("fraction", [0.75, 1.0])
def test_preset_columns_reach_preview_render_and_file_boxes(
    preset, columns, fraction, tmp_path, request
):
    ctx = mp.TEX_PRESETS[preset]
    width = (
        (ctx.textwidth_pt if columns == 2 else ctx.columnwidth_pt)
        * fraction
        / PT_PER_INCH
    )
    expected = [width, width * 0.5]
    plot = mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y")
    original = plot.to_json()
    preview = plot.preview(
        tex=preset,
        full_width=columns == 2,
        fraction=fraction,
        aspect=0.5,
        show_context=False,
    )
    try:
        assert preview.get_size_inches() == pytest.approx(expected)
    finally:
        plt.close(preview)
    mock = plot.preview(
        tex=preset, full_width=columns == 2, fraction=fraction, aspect=0.5
    )
    try:
        extent = mock.axes[0].images[0].get_extent()
        assert extent[1] - extent[0] == pytest.approx(width)
    finally:
        plt.close(mock)
    assert plot.to_json() == original
    plot.tex_size(preset, columns=columns, fraction=fraction, aspect=0.5)
    plot.dispatch(mp.actions.SetDpi(100))
    assert plot.spec.size == pytest.approx(expected)
    before = plot.to_json()
    file_boxes = {}
    for extension in ("png", "pdf", "svg"):
        path = tmp_path / f"figure.{extension}"
        fig = plot.save(str(path))
        try:
            assert fig.get_size_inches() == pytest.approx(expected)
        finally:
            plt.close(fig)
        raw = path.read_bytes()
        if extension == "png":
            pixels = struct.unpack(">II", raw[16:24])
            file_boxes["png_pixels"] = list(pixels)
            assert all(
                abs(actual - requested * 100) <= 1
                for actual, requested in zip(pixels, expected, strict=True)
            )
        elif extension == "pdf":
            box = re.search(
                rb"/MediaBox\s*\[\s*0\s+0\s+([0-9.]+)\s+([0-9.]+)\s*\]", raw
            )
            assert box is not None
            file_boxes["pdf_points"] = [float(box[1]), float(box[2])]
            assert [float(box[1]), float(box[2])] == pytest.approx(
                [value * 72 for value in expected], abs=1e-4
            )
        else:
            root = ET.fromstring(raw)
            file_boxes["svg_points"] = [
                float(root.attrib[k].removesuffix("pt")) for k in ("width", "height")
            ]
            assert [
                float(root.attrib[k].removesuffix("pt")) for k in ("width", "height")
            ] == pytest.approx([value * 72 for value in expected], abs=1e-4)
    assert plot.to_json() == before
    assert not plt.get_fignums()
    request.node.user_properties.append(
        (
            "preset_geometry",
            json.dumps(
                {
                    "preset": preset,
                    "columns": columns,
                    "fraction": fraction,
                    "requested_inches": expected,
                    "dpi": 100,
                    "file_boxes": file_boxes,
                    "mock_image_width_inches": float(extent[1] - extent[0]),
                }
            ),
        )
    )


@pytest.mark.parametrize("name", AVAILABLE_JOURNALS)
def test_last_size_action_wins_but_journal_font_style_has_registry_priority(name):
    plot = mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y").journal(name)
    assert plot.spec.size == JOURNAL_SIZES[name]
    plot.tex_size(name, columns=2).size(4, 2).font(size=15, label_size=15)
    assert plot.spec.size == [4, 2]
    assert plot.spec.theme.font.size == 15
    fig = plot.render()
    try:
        assert (
            fig.axes[0].xaxis.label.get_fontsize()
            == journal_overrides(name)["axes.labelsize"]
        )
    finally:
        plt.close(fig)
    plot.journal(None)
    assert plot.spec.size == [4, 2]
    fig = plot.render()
    try:
        assert fig.axes[0].xaxis.label.get_fontsize() == 15
    finally:
        plt.close(fig)
