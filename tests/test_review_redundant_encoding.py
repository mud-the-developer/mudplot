"""COLOR-06/07: finite patterns complement colour, not unlimited identification."""

import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import PathCollection, PolyCollection
from matplotlib.colors import to_rgba
from matplotlib.container import BarContainer
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from mudplot.color import palette as P


def data(groups):
    return {
        "cat": ["A", "B", "A", "B"] * groups,
        "value": [1, 2, 2, 3] * groups,
        "x": [1, 2, 3, 4] * groups,
        "g": [f"g{i}" for i in range(groups) for _ in range(4)],
    }


def handles(ax):
    leg = ax.get_legend()
    assert leg is not None
    return leg.legend_handles


@pytest.mark.parametrize("kind", ["bar", "box", "violin"])
def test_fill_hatches_repeat_finitely_and_match_legends_panels(kind):
    rows = data(7)
    if kind != "bar":
        rows["cat"] = ["A"] * len(rows["value"])
    p = mp.plot(rows).layout(1, 2).size(10, 4)
    for panel in (0, 1):
        if kind == "bar":
            p.bar("cat", "value", group="g", panel=panel)
        else:
            getattr(p, kind)("cat", "value", group="g", panel=panel)
    fig = p.render()
    expected = p.spec.theme.hatches
    try:
        observed = []
        for ax in fig.axes:
            if kind == "bar":
                patterns = [
                    container.patches[0].get_hatch()
                    for container in ax.containers
                    if isinstance(container, BarContainer)
                ]
            elif kind == "box":
                patterns = [patch.get_hatch() for patch in ax.patches]
            else:
                patterns = [
                    body.get_hatch()
                    for body in ax.collections
                    if isinstance(body, PolyCollection)
                    and np.asarray(body.get_facecolor()).size
                ]
            assert patterns == [expected[i % len(expected)] for i in range(7)]
            actual_handles = handles(ax)
            patch_handles = [h for h in actual_handles if isinstance(h, Patch)]
            assert len(patch_handles) == len(actual_handles)
            assert [h.get_hatch() for h in patch_handles] == patterns
            assert patterns[0] == patterns[len(expected)]
            observed.append(patterns)
        assert observed[0] == observed[1]
    finally:
        plt.close(fig)


@pytest.mark.parametrize("kind", ["line", "scatter"])
def test_grouped_point_line_cycles_and_guides_match_but_are_finite(kind):
    p = mp.plot(data(9)).layout(1, 2).size(10, 4)
    for panel in (0, 1):
        getattr(p, kind)("x", "value", group="g", panel=panel)
    fig = p.render()
    try:
        for ax in fig.axes:
            legends = handles(ax)
            if kind == "line":
                assert [a.get_marker() for a in ax.lines] == [
                    p.spec.theme.markers[i % len(p.spec.theme.markers)]
                    for i in range(9)
                ]
                assert [a.get_linestyle() for a in ax.lines] == [
                    p.spec.theme.line_styles[i % len(p.spec.theme.line_styles)]
                    for i in range(9)
                ]
                line_handles = [h for h in legends if isinstance(h, Line2D)]
                assert len(line_handles) == len(legends)
                assert [(h.get_marker(), h.get_linestyle()) for h in line_handles] == [
                    (a.get_marker(), a.get_linestyle()) for a in ax.lines
                ]
                period = math.lcm(
                    len(p.spec.theme.markers), len(p.spec.theme.line_styles)
                )
                assert period == 8
                assert line_handles[0].get_marker() == line_handles[period].get_marker()
            else:
                assert len(ax.collections) == len(legends) == 9
                scatter_handles = [h for h in legends if isinstance(h, PathCollection)]
                assert len(scatter_handles) == len(legends)
                for artist, handle in zip(ax.collections, scatter_handles, strict=True):
                    np.testing.assert_allclose(
                        np.asarray(artist.get_paths()[0].vertices),
                        np.asarray(handle.get_paths()[0].vertices),
                    )
                np.testing.assert_allclose(
                    np.asarray(scatter_handles[0].get_paths()[0].vertices),
                    np.asarray(scatter_handles[8].get_paths()[0].vertices),
                )
    finally:
        plt.close(fig)


def test_grayscale_is_linear_relative_luminance_not_ideal_equal_lightness():
    pal = P.qualitative(6, lightness_jitter=0)
    assert np.ptp(pal.lch[:, 0]) == 0
    rgb = pal.srgb
    linear = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    Y = linear @ np.array([0.2126, 0.7152, 0.0722])
    expected = np.where(Y <= 0.0031308, 12.92 * Y, 1.055 * Y ** (1 / 2.4) - 0.055)
    gray = pal.grayscale_srgb()
    np.testing.assert_allclose(
        gray, np.repeat(expected[:, None], 3, axis=1), atol=1e-12
    )
    assert np.ptp(gray[:, 0]) < 0.001 and pal.report()["grayscale_safe"] is False


def test_public_docs_describe_finite_patterns_and_measured_report_conditions():
    from pathlib import Path

    reference = mp.reference_markdown()
    assert "cycles are finite and repeat" in reference
    assert "not printing/accessibility certification" in reference
    root = Path(__file__).resolve().parents[1]
    assert "regardless of colour count" not in (root / "README.md").read_text(
        encoding="utf-8"
    )
    assert "색상 개수와 상관없이" not in (root / "README.ko.md").read_text(
        encoding="utf-8"
    )


def test_single_column_palette_quality_does_not_imply_pattern_distinction():
    p = (
        mp.plot(data(6))
        .line("x", "value", group="g", line_width=0.6, marker_size=2)
        .tex_size("ieee", columns=1)
        .labels(title="Six groups")
        .encoding(redundant_encoding=True)
    )
    fig = p.render()
    try:
        assert fig.get_size_inches()[0] == pytest.approx(
            mp.TEX_PRESETS["ieee"].columnwidth_pt / 72.27
        )
        assert (
            len({(a.get_marker(), a.get_linestyle()) for a in fig.axes[0].lines}) == 6
        )
        assert all(
            a.get_linewidth() == 0.6 and a.get_markersize() == 2
            for a in fig.axes[0].lines
        )
        assert all(to_rgba(a.get_color())[3] > 0 for a in fig.axes[0].lines)
    finally:
        plt.close(fig)
