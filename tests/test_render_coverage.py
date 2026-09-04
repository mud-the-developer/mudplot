"""Tests for the render-coverage pass: secondary axis, shared axes,
colour-mapped scatter + colorbar, heatmap, despine, outside legend, and
redundant marker/line-style encoding.
"""

import matplotlib

matplotlib.use("Agg")

import mudplot as mp
import numpy as np
from mudplot._render import render


def _xy(n=20):
    x = np.linspace(0, 1, n)
    return {"x": list(x), "y": list(x**2), "z": list(x), "g": ["a", "b"] * (n // 2)}


def test_secondary_axis_creates_twin():
    p = mp.plot(_xy()).secondary_yaxis("Y2").line("x", "y").line("x", "z", axis="y2")
    fig = render(p.spec)
    assert len(fig.axes[0].figure.axes) == 2  # ax + twin


def test_secondary_axis_labels_applied():
    p = mp.plot(_xy()).secondary_yaxis("right label").line("x", "y", axis="y2")
    fig = render(p.spec)
    labels = [ax.get_ylabel() for ax in fig.axes]
    assert "right label" in labels


def test_layer_without_secondary_axis_configured_is_invalid():
    p = mp.plot(_xy()).line("x", "y", axis="y2")  # no .secondary_yaxis() call
    issues = mp.validate(p.spec)
    assert any("secondary" in i for i in issues)


def test_shared_axes_configured():
    p = mp.plot(_xy()).layout(1, 2).share(x="all", y="all")
    p = p.line("x", "y", panel=0).line("x", "z", panel=1)
    assert p.spec.share_x == "all"
    assert p.spec.share_y == "all"
    fig = render(p.spec)
    assert len(fig.axes) == 2


def test_invalid_share_mode_caught_by_validate():
    spec = mp.apply(
        [
            {"type": "SetData", "columns": {"x": [1], "y": [1]}},
            {"type": "AddLayer", "layer": {"type": "line", "x": "x", "y": "y"}},
            {"type": "SetShare", "x": "sideways"},
        ]
    )
    issues = mp.validate(spec)
    assert any("share_x" in i for i in issues)


def test_colormap_scatter_draws_and_colorbar():
    p = mp.plot(_xy()).scatter("x", "y", c="z", colorbar=True, clabel="z-value")
    fig = render(p.spec)
    ax = fig.axes[0]
    assert len(ax.collections) >= 1
    # a colorbar adds a second axes to the figure
    assert len(fig.axes) >= 2


def test_colormap_scatter_diverging_kind():
    p = mp.plot(_xy()).scatter("x", "y", c="z", cmap_kind="diverging")
    fig = render(p.spec)
    assert len(fig.axes[0].collections) >= 1


def test_invalid_cmap_kind_caught():
    p = mp.plot(_xy()).scatter("x", "y", c="z", cmap_kind="rainbow")
    issues = mp.validate(p.spec)
    assert any("cmap_kind" in i for i in issues)


def test_heatmap_renders_with_colorbar():
    p = mp.plot({}).matrix("m", [[1, 2, 3], [4, 5, 6]]).heatmap("m")
    fig = render(p.spec)
    assert len(fig.axes) >= 2  # image axes + colorbar axes


def test_heatmap_missing_matrix_caught_by_validate():
    p = mp.plot({}).heatmap("nope")
    issues = mp.validate(p.spec)
    assert any("nope" in i for i in issues)


def test_despine_offsets_visible_spines():
    p = mp.plot(_xy()).line("x", "y").axes_style(spine_offset=10)
    fig = render(p.spec)
    ax = fig.axes[0]
    left_pos = ax.spines["left"].get_position()
    assert left_pos == ("outward", 10)


def test_outside_right_legend_does_not_error():
    p = mp.plot(_xy()).line("x", "y", label="s1").legend(location="outside right")
    fig = render(p.spec)
    assert fig is not None


def test_invalid_legend_location_caught():
    p = mp.plot(_xy()).line("x", "y").legend(location="north-east")
    issues = mp.validate(p.spec)
    assert any("legend location" in i for i in issues)


def test_redundant_encoding_cycles_marker_and_style():
    data = {
        "x": [0, 1, 2] * 3,
        "y": [0, 1, 2, 1, 2, 3, 2, 3, 4],
        "g": ["a"] * 3 + ["b"] * 3 + ["c"] * 3,
    }
    p = mp.plot(data).line("x", "y", group="g").encoding(redundant_encoding=True)
    fig = render(p.spec)
    lines = fig.axes[0].lines
    markers = {ln.get_marker() for ln in lines}
    styles = {ln.get_linestyle() for ln in lines}
    assert len(markers) >= 2  # distinct markers assigned
    assert len(styles) >= 2  # distinct dash patterns assigned


def test_redundant_encoding_disabled_leaves_lines_plain():
    data = {"x": [0, 1, 2] * 2, "y": [0, 1, 2, 1, 2, 3], "g": ["a"] * 3 + ["b"] * 3}
    p = mp.plot(data).line("x", "y", group="g").encoding(redundant_encoding=False)
    fig = render(p.spec)
    markers = {ln.get_marker() for ln in fig.axes[0].lines}
    assert markers == {"None"}  # matplotlib reports no-marker as the string "None"


def test_ungrouped_line_unaffected_by_redundant_encoding():
    # a single, ungrouped series should never get an unwanted marker
    p = mp.plot(_xy()).line("x", "y")
    fig = render(p.spec)
    assert fig.axes[0].lines[0].get_marker() == "None"


def test_explicit_marker_overrides_cycle():
    data = {"x": [0, 1] * 2, "y": [0, 1, 1, 2], "g": ["a", "a", "b", "b"]}
    p = mp.plot(data).line("x", "y", group="g", marker="x")
    fig = render(p.spec)
    assert all(ln.get_marker() == "x" for ln in fig.axes[0].lines)


def test_theme_markers_and_linestyles_customisable():
    theme = mp.FigureSpec().theme
    assert len(theme.markers) >= 4
    assert len(theme.line_styles) >= 2


def test_full_pipeline_validates_clean(tmp_path):
    rng = np.random.default_rng(0)
    x = np.linspace(0, 5, 30)
    data = {
        "x": list(x),
        "y1": list(np.sin(x)),
        "y2": list(np.cos(x) * 10),
        "z": list(rng.normal(size=30)),
    }
    p = (
        mp.plot(data)
        .secondary_yaxis("y2")
        .line("x", "y1", label="y1")
        .line("x", "y2", axis="y2", label="y2")
        .scatter("x", "z", c="z", colorbar=True)
        .axes_style(spine_offset=4)
        .legend(location="outside right")
    )
    assert mp.validate(p.spec) == []
    out = tmp_path / "fig.png"
    p.save(str(out))
    assert out.exists()
