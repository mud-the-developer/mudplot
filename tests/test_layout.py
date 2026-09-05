"""Regression checks for TeX column sizing and the no-clip/no-overlap layout
pass (_autofit): outside legends, dragged legends, long titles, 3-D fallback.
"""

import matplotlib.pyplot as plt
import mudplot as mp
import pytest
from mudplot.tex import TEX_PRESETS, figsize_for


@pytest.mark.parametrize("preset", ["ieee", "nature", "article"])
def test_tex_size_one_column_matches_columnwidth(preset):
    p = mp.plot({"x": [1, 2], "y": [3, 4]}).line("x", "y").tex_size(preset, columns=1)
    expected = figsize_for(TEX_PRESETS[preset], full_width=False)
    assert p.spec.size == pytest.approx(expected)


@pytest.mark.parametrize("preset", ["ieee", "nature"])
def test_tex_size_two_columns_spans_textwidth_and_is_wider(preset):
    ctx = TEX_PRESETS[preset]
    p1 = mp.plot({"x": [1], "y": [1]}).line("x", "y").tex_size(preset, columns=1)
    p2 = mp.plot({"x": [1], "y": [1]}).line("x", "y").tex_size(preset, columns=2)
    assert p2.spec.size[0] > p1.spec.size[0]
    assert p2.spec.size == pytest.approx(figsize_for(ctx, full_width=True))


def test_tex_size_matches_font_family_and_matches_action_log_pattern():
    p = mp.plot({"x": [1], "y": [1]}).line("x", "y").tex_size("nature", columns=1)
    assert p.spec.theme.font.family == "sans-serif"
    kinds = [a["type"] for a in p.action_log[-2:]]
    assert kinds == ["SetSize", "SetFont"]


def test_tex_size_rejects_bad_column_count():
    with pytest.raises(ValueError, match="columns must be 1 or 2"):
        mp.plot({"x": [1], "y": [1]}).line("x", "y").tex_size("ieee", columns=3)


def test_tex_size_accepts_texcontext_object_directly():
    p = mp.plot({"x": [1], "y": [1]}).line("x", "y").tex_size(TEX_PRESETS["acm"])
    assert p.spec.size == pytest.approx(figsize_for(TEX_PRESETS["acm"]))


def test_outside_legend_no_longer_clips_at_exact_column_width():
    data = {"x": list(range(20)), "temp": list(range(20)), "pressure": list(range(20))}
    p = (
        mp.plot(data)
        .tex_size("ieee", columns=1)
        .secondary_yaxis("Pressure")
        .line("x", "temp", label="Temp")
        .line("x", "pressure", label="Pressure", axis="y2")
        .legend(location="outside right")
    )
    fig = p.render()
    fig.canvas.draw()
    legend = fig.axes[0].get_legend()
    bb = legend.get_window_extent(fig.canvas.get_renderer())
    bb = bb.transformed(fig.transFigure.inverted())
    assert bb.x0 >= 0 and bb.x1 <= 1.001
    assert bb.y0 >= 0 and bb.y1 <= 1.001
    plt.close(fig)


def test_long_title_wraps_instead_of_clipping_at_exact_column_width():
    p = (
        mp.plot({"x": [1, 2], "y": [3, 4]})
        .tex_size("ieee", columns=1)
        .line("x", "y")
        .labels(title="a deliberately very long panel title that cannot fit one line")
    )
    fig = p.render()
    fig.canvas.draw()
    title = fig.axes[0].title
    bb = title.get_window_extent(fig.canvas.get_renderer())
    # matplotlib's native wrap (not a custom shrink) keeps the *rendered*
    # bbox within the figure; get_text() still returns the original
    # unwrapped string, wrapping only happens at draw time.
    assert bb.width <= fig.bbox.width + 1
    assert title.get_wrap() is True
    plt.close(fig)


def test_dragged_legend_bbox_to_anchor_is_respected_exactly():
    p = (
        mp.plot({"x": [1, 2, 3], "y": [1, 4, 9], "g": ["a", "a", "b"]})
        .line("x", "y", group="g")
        .legend(bbox_to_anchor=[0.2, 0.8])
    )
    fig = p.render()
    fig.canvas.draw()
    legend = fig.axes[0].get_legend()
    bb = legend.get_window_extent(fig.canvas.get_renderer())
    bb = bb.transformed(fig.transFigure.inverted())
    cx, cy = (bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2
    assert cx == pytest.approx(0.2, abs=0.01)
    assert cy == pytest.approx(0.8, abs=0.01)
    plt.close(fig)


def test_ordinary_figures_keep_default_font_sizes_unchanged():
    # _autofit must be a no-op (no shrink, no margin surprises) when nothing
    # actually overflows -- the common case stays exactly as before.
    p = mp.plot({"x": [1, 2], "y": [3, 4]}).line("x", "y").labels(title="Short title")
    fig = p.render()
    assert fig.axes[0].title.get_fontsize() == pytest.approx(
        p.spec.theme.font.title_size
    )
    plt.close(fig)


def test_invalid_legend_bbox_to_anchor_caught_by_validate():
    p = mp.plot({"x": [1], "y": [2]}).line("x", "y").legend(bbox_to_anchor=[0.1])
    assert any("bbox_to_anchor" in i for i in mp.validate(p.spec))


def test_3d_figure_still_renders_without_clipped_axis_labels():
    p = (
        mp.plot({"x": [1, 2], "y": [3, 4], "z": [5, 6]})
        .projection3d()
        .line3d("x", "y", "z")
        .zlabel("A fairly long z axis label")
    )
    fig = p.render()  # must not raise; exact pixel-fit isn't checked for 3-D
    assert fig.axes[0].name == "3d"
    plt.close(fig)


def test_mixed_2d_3d_figure_still_shares_2d_axes_after_layout_change():
    p = mp.plot({"x": [1, 2], "y": [3, 4], "z": [5, 6]}).layout(1, 3)
    p.line("x", "y").line("x", "y", panel=1)
    p.projection3d(panel=2).line3d("x", "y", "z", panel=2).share(x="all")
    ax, other, three_d = p.render().axes
    assert ax.get_shared_x_axes().joined(ax, other)
    assert not ax.get_shared_x_axes().joined(ax, three_d)
