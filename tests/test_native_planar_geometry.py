import math

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import LineCollection


def test_finite_segments_and_spans_use_their_real_axes():
    p = (
        mp.plot()
        .size(8, 4)
        .secondary_yaxis("B")
        .hlines(
            mp.SegmentSpec([3, 5], [1, 2], [4, 7]),
            axis="y2",
            native_style=mp.ComponentStyleSpec(line_width=2.2, line_style="--"),
        )
        .vlines(mp.SegmentSpec([2], [4], [9]))
        .vspan(
            mp.SpanSpec(4, 6, [0.2, 0.8]),
            native_style=mp.ComponentStyleSpec(color="teal", alpha=0.25),
        )
    )
    fig = p.render()
    try:
        ax = fig.axes[0]
        twin = ax._mudplot_secondary_axis
        lines = next(a for a in twin.collections if isinstance(a, LineCollection))
        np.testing.assert_array_equal(
            lines.get_segments(), [[[1, 3], [4, 3]], [[2, 5], [7, 5]]]
        )
        assert list(lines.get_linewidths()) == [2.2]
        np.testing.assert_array_equal(
            ax.collections[0].get_segments(), [[[2, 4], [2, 9]]]
        )
        patch = ax.patches[0]
        predicted = ax.get_xaxis_transform().transform([[4, 0.2], [6, 0.8]])
        np.testing.assert_allclose(patch.get_window_extent().get_points(), predicted)
        assert mp.Plot.from_json(p.to_json()).spec == mp.apply(p.action_log) == p.spec
    finally:
        plt.close(fig)


def test_native_asymmetric_clock_errors_keep_duration_and_endpoint_precision():
    seconds = 1_000_000_000
    raw = {
        "time": [2 * seconds, 5 * seconds],
        "value": [3, 5],
        "lo": [seconds, 2 * seconds],
        "hi": [2 * seconds, seconds],
        "down": [0.5, 1],
        "up": [2, 0.5],
    }
    p = (
        mp.plot(raw)
        .date_axis("x", unit="ns", origin="1970-01-02T00:00:00Z")
        .errorbar(
            "time",
            "value",
            magnitudes=mp.ErrorMagnitudesSpec(x=["lo", "hi"], y=["down", "up"]),
        )
    )
    fig = p.render()
    try:
        xerr, yerr = fig.axes[0].containers[0].lines[2]

        def day(t):
            return 1 + t / 86400

        np.testing.assert_allclose(
            xerr.get_segments(),
            [[[day(1), 3], [day(4), 3]], [[day(3), 5], [day(6), 5]]],
            rtol=0,
            atol=5e-16,
        )
        np.testing.assert_array_equal(
            yerr.get_segments(),
            [[[day(2), 2.5], [day(2), 5]], [[day(5), 4], [day(5), 5.5]]],
        )
        assert p.spec.data.columns == raw
    finally:
        plt.close(fig)
    before, history = p.to_json(), p.action_log
    # The float of this integer is a valid multiple of 1000; the original is not.
    low_bits = 9_007_199_254_742_001
    assert int(float(low_bits)) == low_bits - 1
    from mudplot.actions import SetData

    with pytest.raises(ValueError, match="finer than microseconds"):
        p.dispatch(SetData({**raw, "lo": [low_bits, 2 * seconds]}))
    assert p.to_json() == before and p.action_log == history


def test_fill_native_masks_keep_two_polygons_and_real_horizontal_step():
    raw = {
        "a": [0, 1, 2, 3, 4],
        "lower": [1.0, 2.0, None, 5.0, 6.0],
        "upper": [3.0, 4.0, None, 6.0, 8.0],
        "show": [True, True, False, True, True],
    }
    p = (
        mp.plot(raw)
        .layout(1, 2)
        .size(9, 5)
        .band(
            "a", "lower", "upper", fill=mp.FillSpec(where="show", step="post"), panel=0
        )
        .band(
            "a",
            "lower",
            "upper",
            orient="h",
            fill=mp.FillSpec(where="show", step="post"),
            panel=1,
        )
    )
    fig = p.render()
    try:
        v, h = [a.collections[0].get_paths() for a in fig.axes]
        assert len(v) == len(h) == 2
        assert max(v[0].vertices[:, 0]) == 1 and min(v[1].vertices[:, 0]) == 3
        for first, second in zip(v, h, strict=True):
            assert {tuple(x) for x in first.vertices} == {
                tuple(x[::-1]) for x in second.vertices
            }
        assert [1.0, 1.0] in v[0].vertices.tolist()
    finally:
        plt.close(fig)
    q = mp.plot({"x": [1, 2], "y": [1, 2], "lo": [2, 0], "hi": [1, 1]}).axis_scale(
        "y", "log"
    )
    before = q.to_json()
    with pytest.raises(ValueError, match="positive on log"):
        q.errorbar("x", "y", magnitudes={"y": ["lo", "hi"]})
    assert q.to_json() == before


def test_named_native_line_and_scatter_styles_reach_native_traits():
    p = (
        mp.plot({"x": [0, 1], "y": [1, 3]})
        .line(
            "x",
            "y",
            native_style=mp.ComponentStyleSpec(
                marker="s", marker_edge_width=1.6, line_style="--"
            ),
        )
        .scatter(
            "x",
            "y",
            native_style=mp.ComponentStyleSpec(
                marker="d",
                marker_size=7,
                edge_color="black",
                face_color="orange",
                line_width=1.3,
            ),
        )
    )
    fig = p.render()
    try:
        line = fig.axes[0].lines[0]
        mark = fig.axes[0].collections[0]
        assert (
            line.get_marker() == "s"
            and line.get_markeredgewidth() == 1.6
            and line.get_linestyle() == "--"
        )
        assert float(mark.get_sizes()[0]) == 49 and math.isclose(
            mark.get_linewidths()[0], 1.3
        )
        assert np.all(mark.get_edgecolors()[0, :3] == 0)
        assert mark.get_facecolors()[0][0] == 1
    finally:
        plt.close(fig)


def test_native_interpolation_locates_the_actual_mask_boundary_crossings():
    p = mp.plot(
        {
            "x": [0, 1, 2, 3],
            "baseline": [0, 0, 0, 0],
            "curve": [-1, 1, 1, -1],
            "positive": [False, True, True, False],
        }
    ).band(
        "x", "baseline", "curve", fill=mp.FillSpec(where="positive", interpolate=True)
    )
    figure = p.render()
    try:
        (path,) = figure.axes[0].collections[0].get_paths()
        assert min(path.vertices[:, 0]) == 0.5
        assert max(path.vertices[:, 0]) == 2.5
    finally:
        plt.close(figure)
