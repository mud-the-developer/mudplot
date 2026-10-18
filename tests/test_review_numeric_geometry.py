"""P0 numeric/artist contracts, checked against independently constructed inputs."""

from __future__ import annotations

import copy
from statistics import NormalDist

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.axes import Axes
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d import Axes3D
from mudplot._render import _regression_fit


@pytest.mark.parametrize("degree", [1, 2, 3])
@pytest.mark.parametrize("confidence", [50, 95, 99])
def test_regression_matches_independent_normal_equations_and_mean_not_prediction_ci(
    degree, confidence
):
    x = np.array([-3, -1, -1, 0, 2, 4], dtype=float)
    y = np.array([11, 2, 3, 1, 6, 18], dtype=float)
    at = np.array([-3, -0.5, 1, 4])
    design = np.column_stack([x**power for power in range(degree + 1)])
    target = np.column_stack([at**power for power in range(degree + 1)])
    gram_inverse = np.linalg.inv(design.T @ design)
    coefficients = gram_inverse @ design.T @ y
    expected = target @ coefficients
    residual = y - design @ coefficients
    variance = float(residual @ residual) / (len(x) - degree - 1)
    leverage = np.sum((target @ gram_inverse) * target, axis=1)
    critical = NormalDist().inv_cdf(0.5 + confidence / 200)
    width = critical * np.sqrt(variance * leverage)
    grid, fitted, interval = _regression_fit(x, y, degree, confidence, at=at)
    np.testing.assert_array_equal(grid, at)
    np.testing.assert_allclose(fitted, expected, rtol=1e-10, atol=1e-10)
    assert interval is not None
    np.testing.assert_allclose(interval[0], expected - width, rtol=1e-10, atol=1e-10)
    np.testing.assert_allclose(interval[1], expected + width, rtol=1e-10, atol=1e-10)
    prediction_width = critical * np.sqrt(variance * (1 + leverage))
    assert np.all(width < prediction_width)
    order = [4, 1, 5, 0, 3, 2]
    _, reordered, reordered_interval = _regression_fit(
        x[order], y[order], degree, confidence, at=at
    )
    np.testing.assert_allclose(reordered, fitted, atol=1e-10)
    assert reordered_interval is not None
    np.testing.assert_allclose(reordered_interval, interval, atol=1e-10)


def test_legacy_regression_default_has_no_confidence_band():
    plot = mp.plot({"x": [3, 1, 2, 1, 0], "y": [7, 3, 5, 3, 1]}).regplot("x", "y")
    assert plot.spec.panels[0].layers[0].confidence is None
    axes = plot.render().axes[0]
    line = axes.lines[0]
    np.testing.assert_allclose(
        np.asarray(line.get_ydata()), 1 + 2 * np.asarray(line.get_xdata()), atol=1e-12
    )
    assert len(axes.collections) == 1  # observations only, not a hidden band


@pytest.mark.parametrize(
    "order", [("line", "scatter", "bar"), ("bar", "line", "scatter")]
)
def test_categorical_positions_align_across_native_layer_permutations(order):
    data = {"a": ["A", "B"], "b": ["B", "C"], "c": ["C", "A"], "y": [10, 20]}
    plot = mp.plot(data)
    columns = {"line": "a", "scatter": "b", "bar": "c"}
    for kind in order:
        getattr(plot, kind)(columns[kind], "y", label=kind)
    axes = plot.render().axes[0]
    labels = [text.get_text() for text in axes.get_xticklabels()]
    slots = {label: index for index, label in enumerate(labels)}
    np.testing.assert_array_equal(axes.lines[0].get_xdata(), [slots["A"], slots["B"]])
    np.testing.assert_allclose(
        np.asarray(axes.collections[0].get_offsets())[:, 0], [slots["B"], slots["C"]]
    )
    assert all(isinstance(bar, Rectangle) for bar in axes.patches)
    np.testing.assert_allclose(
        [
            bar.get_x() + bar.get_width() / 2
            for bar in axes.patches
            if isinstance(bar, Rectangle)
        ],
        [slots["C"], slots["A"]],
    )
    assert plot.spec.data.columns == data


def test_ordered_group_styles_are_reserved_across_panel_permutations():
    data = {
        "x": [0, 1, 0, 1],
        "y": [1, 2, 2, 3],
        "first": ["A", "A", "B", "B"],
        "second": ["B", "B", "C", "C"],
    }
    styles = []
    for columns in (("first", "second"), ("second", "first")):
        plot = mp.plot(data).layout(1, 2).encoding(redundant_encoding=True)
        for index, group in enumerate(columns):
            plot.line("x", "y", group=group, hue_order=["A", "B", "C"], panel=index)
        figure = plot.render()
        observed = {}
        for axes in figure.axes:
            for line in axes.lines:
                value = (line.get_color(), line.get_marker(), line.get_linestyle())
                if line.get_label() in observed:
                    assert observed[line.get_label()] == value
                observed[line.get_label()] = value
        styles.append(observed)
        plt.close(figure)
    assert styles[0] == styles[1]


def test_secondary_log_axis_keeps_its_artists_labels_limits_and_annotations():
    data = {"x": [1, 2, 3], "left": [1, 2, 3], "right": [10, 100, 1000]}
    plot = mp.plot(data).secondary_yaxis("right units", scale="log", limits=[1, 10000])
    plot.line("x", "left", label="left").line("x", "right", axis="y2", label="right")
    plot.hline(100, axis="y2").text("right annotation", at=[2, 100], axis="y2").legend()
    primary, secondary = plot.render().axes
    assert primary.lines[0].axes is primary
    assert all(line.axes is secondary for line in secondary.lines)
    assert not primary.texts and secondary.texts[0].axes is secondary
    assert primary.get_yscale() == "linear" and secondary.get_yscale() == "log"
    assert (
        secondary.get_ylim() == (1, 10000) and secondary.get_ylabel() == "right units"
    )
    np.testing.assert_array_equal(secondary.lines[0].get_ydata(), data["right"])
    legend = primary.get_legend()
    assert legend is not None and [text.get_text() for text in legend.get_texts()] == [
        "left",
        "right",
    ]


def test_asymmetric_heatmap_cell_annotation_and_origin_contract():
    matrix = [[11, 12, 13], [21, 22, 23]]
    before = copy.deepcopy(matrix)
    plot = (
        mp.plot()
        .matrix("m", matrix)
        .heatmap("m", heatmap={"annot": True, "fmt": ".0f"}, colorbar=False)
    )
    axes = plot.render().axes[0]
    np.testing.assert_array_equal(axes.images[0].get_array(), matrix)
    assert axes.images[0].origin == "upper"
    assert tuple(axes.images[0].get_extent()) == (-0.5, 2.5, 1.5, -0.5)
    assert {(text.get_position(), text.get_text()) for text in axes.texts} == {
        ((column, row), str(value))
        for row, values in enumerate(matrix)
        for column, value in enumerate(values)
    }
    assert plot.spec.data.matrices["m"] == before == matrix


@pytest.mark.parametrize("kind", ["surface", "wireframe"])
def test_asymmetric_3d_matrix_receives_column_x_row_y_grid(kind, monkeypatch):
    matrix = [[11, 12, 13], [21, 22, 23]]
    original = getattr(Axes3D, "plot_" + kind)
    captured = []

    def record(axes, x, y, z, *args, **kwargs):
        captured.append((np.array(x), np.array(y), np.array(z)))
        return original(axes, x, y, z, *args, **kwargs)

    monkeypatch.setattr(Axes3D, "plot_" + kind, record)
    plot = mp.plot().matrix("m", matrix).projection3d()
    getattr(plot, kind)("m", colorbar=False)
    assert plot.render().axes[0].name == "3d"
    assert len(captured) == 1
    np.testing.assert_array_equal(captured[0][0], [[0, 1, 2], [0, 1, 2]])
    np.testing.assert_array_equal(captured[0][1], [[0, 0, 0], [1, 1, 1]])
    np.testing.assert_array_equal(captured[0][2], matrix)


@pytest.mark.parametrize("kind", ["contour", "contourf"])
def test_contours_on_asymmetric_plane_match_native_xy_level_geometry(kind, monkeypatch):
    original = getattr(Axes, kind)
    captured = []

    def record(axes, *args, **kwargs):
        result = original(axes, *args, **kwargs)
        captured.append(result)
        return result

    monkeypatch.setattr(Axes, kind, record)
    plot = mp.plot().matrix("m", [[11, 12, 13], [21, 22, 23]])
    getattr(plot, kind)("m", colorbar=False)
    plot.render()
    contour = captured[0]
    for index, path in enumerate(contour.get_paths()):
        points = path.vertices
        if not len(points):
            continue
        value = 11 + points[:, 0] + 10 * points[:, 1]
        if kind == "contour":
            np.testing.assert_allclose(value, contour.levels[index], atol=1e-12)
        else:
            assert np.min(value) >= contour.levels[index] - 1e-12
            assert np.max(value) <= contour.levels[index + 1] + 1e-12
