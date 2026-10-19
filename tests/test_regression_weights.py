"""Relative weighted least squares: point fits only, not sampling inference."""

import copy
import math

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import PathCollection


def data(scale=1.0, outlier=False):
    values: dict[str, list[float | None]] = {
        "x": [0.0, 1.0, 2.0],
        "y": [0.0, 1.0, 4.0],
        "w": [scale, scale, 2 * scale],
    }
    if outlier:
        for name, value in (("x", 999.0), ("y", 99999.0), ("w", 0.0)):
            values[name].append(value)
    return values


@pytest.mark.parametrize("scale", [1.0, 1e-200, 1e200])
@pytest.mark.parametrize("outlier", [False, True])
def test_weighted_linear_fit_matches_independent_rational_coefficients(scale, outlier):
    source = data(scale, outlier)
    p = mp.plot(source).regplot("x", "y", weights="w", marker_size=0, alpha=0.4)
    original = copy.deepcopy(p.spec)
    assert mp.validate(p.spec) == [] and mp.from_json(p.to_json()) == p.spec
    assert mp.apply(p.action_log) == p.spec
    figure = p.render()
    try:
        axes = figure.axes[0]
        grid = np.asarray(axes.lines[0].get_xdata(), dtype=float)
        fit = np.asarray(axes.lines[0].get_ydata(), dtype=float)
        np.testing.assert_allclose(
            fit, -4 / 11 + 23 / 11 * grid, rtol=1e-12, atol=1e-12
        )
        scatter = axes.collections[0]
        assert isinstance(scatter, PathCollection)
        np.testing.assert_array_equal(scatter.get_offsets(), [[0, 0], [1, 1], [2, 4]])
        assert scatter.get_sizes()[0] == 0 and scatter.get_alpha() == 0.4
        assert grid[0] == 0 and grid[-1] == 2
        assert p.spec == original and p.spec.data.columns == source
    finally:
        plt.close(figure)


def test_weighted_quadratic_uses_positive_rows_only():
    p = mp.plot({"x": [0, 1, 2, 3], "y": [1, 4, 9, 99], "w": [1, 2, 3, 0]}).regplot(
        "x", "y", weights="w", degree=2
    )
    figure = p.render()
    try:
        line = figure.axes[0].lines[0]
        grid = np.asarray(line.get_xdata(), dtype=float)
        np.testing.assert_allclose(
            np.asarray(line.get_ydata(), dtype=float),
            (grid + 1) ** 2,
            rtol=1e-12,
            atol=1e-12,
        )
    finally:
        plt.close(figure)


def test_weighted_logx_fit_and_raw_residuals_use_the_same_rows():
    source = data(outlier=True)
    source["x"] = [1.0, math.e, math.e**2, 999.0]
    p = mp.plot(source).regplot("x", "y", weights="w", regression={"model": "logx"})
    q = mp.plot(source).residplot("x", "y", weights="w", regression={"model": "logx"})
    a, b = p.render(), q.render()
    try:
        line = a.axes[0].lines[0]
        np.testing.assert_allclose(
            np.asarray(line.get_ydata(), dtype=float),
            -4 / 11 + 23 / 11 * np.log(np.asarray(line.get_xdata(), dtype=float)),
            rtol=1e-12,
            atol=1e-12,
        )
        offsets = np.asarray(b.axes[0].collections[0].get_offsets(), dtype=float)
        np.testing.assert_allclose(
            offsets[:, 1], [4 / 11, -8 / 11, 2 / 11], rtol=1e-12, atol=1e-12
        )
        assert len(b.axes[0].lines) == 1
        np.testing.assert_array_equal(b.axes[0].lines[0].get_ydata(), [0, 0])
    finally:
        plt.close(a)
        plt.close(b)


@pytest.mark.parametrize(
    "weights",
    [
        [-1, 1, 1],
        [True, 1, 1],
        [None, 1, 1],
        [0, 0, 0],
        [1, 0, 0],
        [float("inf"), 1, 1],
        [float("nan"), 1, 1],
    ],
)
def test_invalid_or_insufficient_positive_weights_fail_before_artists(weights):
    source = data()
    source["w"] = weights
    p = mp.plot(source).regplot("x", "y", weights="w")
    before = plt.get_fignums()
    with pytest.raises(ValueError):
        p.render()
    assert plt.get_fignums() == before


@pytest.mark.parametrize(
    "options",
    [
        {"confidence": 95},
        {"regression": {"model": "robust"}},
        {"regression": {"model": "logistic"}},
        {"regression": {"model": "lowess"}},
    ],
)
def test_unsupported_weighted_inference_is_rejected_without_history_change(options):
    p = mp.plot(data())
    before, history = p.spec, p.action_log
    with pytest.raises(ValueError, match="weight"):
        p.regplot("x", "y", weights="w", **options)
    assert p.spec == before and p.action_log == history


@pytest.mark.parametrize("weight", ["", True, 7])
def test_weight_column_name_is_strict(weight):
    p = mp.plot(data())
    with pytest.raises((ValueError, TypeError), match="weight"):
        p.regplot("x", "y", weights=weight)


def test_weight_changes_in_setdata_do_not_use_a_stale_fit():
    source = data()
    p = mp.plot(source).regplot("x", "y", weights="w")
    source["w"] = [1, 1, 0]
    p.dispatch(mp.actions.SetData(source))
    figure = p.render()
    try:
        line = figure.axes[0].lines[0]
        np.testing.assert_allclose(
            np.asarray(line.get_ydata(), dtype=float),
            np.asarray(line.get_xdata(), dtype=float),
            atol=1e-12,
        )
        np.testing.assert_array_equal(
            figure.axes[0].collections[0].get_offsets(), [[0, 0], [1, 1]]
        )
        assert p.spec.data.columns == source and mp.apply(p.action_log) == p.spec
    finally:
        plt.close(figure)


def test_missing_weight_column_is_not_ignored():
    p = mp.plot(data()).regplot("x", "y", weights="absent")
    with pytest.raises(ValueError, match="absent"):
        p.render()


def test_relative_weight_underflow_fails_without_overwriting_output(tmp_path):
    source = data()
    source["w"] = [1e-300, 1.0, 1e300]
    p = mp.plot(source).regplot("x", "y", weights="w")
    path = tmp_path / "keep.png"
    path.write_bytes(b"previous")
    before = plt.get_fignums()
    with pytest.raises(ValueError, match="weight"):
        p.save(path)
    assert path.read_bytes() == b"previous" and plt.get_fignums() == before


def test_joint_does_not_make_unweighted_marginals_for_weighted_regression():
    p = mp.plot(data()).regplot("x", "y", weights="w")
    before, history = p.spec, p.action_log
    with pytest.raises(ValueError, match="weight"):
        p.joint()
    assert p.spec == before and p.action_log == history


@pytest.mark.parametrize("name", ["x", "y"])
def test_zero_weight_does_not_impute_missing_coordinates(name):
    source = data(outlier=True)
    source[name][-1] = None
    p = mp.plot(source).regplot("x", "y", weights="w")
    with pytest.raises(ValueError, match="finite"):
        p.render()


def test_explicit_existing_dropna_can_select_complete_weight_rows():
    source = data()
    source["w"] = [1, None, 2]
    spec = mp.plot(source).regplot("x", "y", weights="w").spec
    spec.panels[0].dropna = ["w"]
    p = mp.Plot.from_json(mp.to_json(spec))
    figure = p.render()
    try:
        np.testing.assert_array_equal(
            figure.axes[0].collections[0].get_offsets(), [[0, 0], [2, 4]]
        )
        assert p.spec.data.columns == source
    finally:
        plt.close(figure)


def test_raw_weighted_json_requires_explicit_typed_model():
    spec = mp.plot(data()).regplot("x", "y", weights="w").spec
    spec.panels[0].layers[0].regression = None
    assert any("weighted regression requires" in issue for issue in mp.validate(spec))


def test_zero_weight_logx_outlier_does_not_change_fit_domain():
    source = data(outlier=True)
    source["x"] = [1.0, math.e, math.e**2, -9.0]
    p = mp.plot(source).regplot("x", "y", weights="w", regression={"model": "logx"})
    figure = p.render()
    try:
        assert (
            np.asarray(figure.axes[0].collections[0].get_offsets(), dtype=float).shape[
                0
            ]
            == 3
        )
        assert np.asarray(figure.axes[0].lines[0].get_xdata(), dtype=float)[0] == 1
    finally:
        plt.close(figure)


def test_hue_deselection_precedes_weight_value_validation():
    source = {
        "x": [0, 1, 2, 0, 1, 2],
        "y": [0, 1, 4, 0, 1, 4],
        "w": [1, 1, 2, None, True, -1],
        "g": ["A"] * 3 + ["B"] * 3,
    }
    p = mp.plot(source).regplot("x", "y", weights="w", group="g", hue_order=["A"])
    figure = p.render()
    try:
        assert len(figure.axes[0].lines) == len(figure.axes[0].collections) == 1
    finally:
        plt.close(figure)


def test_weighted_model_keeps_existing_typed_row_budget():
    p = mp.plot({"x": list(range(10001)), "y": [1] * 10001, "w": [1] * 10001}).regplot(
        "x", "y", weights="w"
    )
    assert any("10000" in issue for issue in mp.validate(p.spec))


def test_private_fit_does_not_ignore_weights_when_ci_requested():
    from mudplot._render import _regression_fit

    with pytest.raises(ValueError, match="weighted"):
        _regression_fit([0, 1, 2], [0, 1, 4], 1, 95, weights=[1, 1, 2])


def test_groups_hue_selection_secondary_axis_and_facets_keep_weight_alignment():
    source = {
        "x": [0, 1, 2, 0, 1, 2],
        "y": [0, 1, 4, 10, 11, 14],
        "w": [1, 1, 2, 1, 1, 2],
        "g": ["A"] * 3 + ["B"] * 3,
    }
    p = (
        mp.plot(source)
        .secondary_yaxis()
        .regplot("x", "y", weights="w", group="g", hue_order=["B", "A"], axis="y2")
    )
    q = mp.plot(source).regplot("x", "y", weights="w").facet(col="g")
    a, b = p.render(), q.render()
    try:
        assert not a.axes[0].lines and len(a.axes[1].lines) == 2
        for line, offset in zip(a.axes[1].lines, [10, 0], strict=True):
            grid = np.asarray(line.get_xdata(), dtype=float)
            np.testing.assert_allclose(
                np.asarray(line.get_ydata(), dtype=float),
                offset - 4 / 11 + 23 / 11 * grid,
                atol=1e-12,
            )
        for axes, offset in zip(b.axes, [0, 10], strict=True):
            line = axes.lines[0]
            grid = np.asarray(line.get_xdata(), dtype=float)
            np.testing.assert_allclose(
                np.asarray(line.get_ydata(), dtype=float),
                offset - 4 / 11 + 23 / 11 * grid,
                atol=1e-12,
            )
    finally:
        plt.close(a)
        plt.close(b)
