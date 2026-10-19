"""ECDF composition keeps paired joint and univariate pair-diagonal cohorts."""

import copy

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest


def data():
    return {
        "x": [1, 1, 3, None, 5],
        "y": [2, 4, None, 6, 8],
        "h": ["A", "A", "B", "B", "B"],
    }


def build(kind, stat="probability", **options):
    p = mp.plot(data())
    if kind == "joint":
        return p.scatter("x", "y").joint(
            marginal_kind="ecdf", marginal_stat=stat, **options
        )
    return p.pair(["x", "y"], diag_kind="ecdf", diag_stat=stat, **options)


@pytest.mark.parametrize("kind", ["joint", "pair"])
@pytest.mark.parametrize("stat", ["count", "probability", "percent"])
def test_grid_ecdf_uses_exact_cohorts_ties_and_mass(kind, stat):
    p = build(kind, stat)
    assert p.spec.data.columns == data() and mp.from_json(p.to_json()) == p.spec
    figure = p.render()
    try:
        if kind == "joint":
            right, bottom = figure.axes[1:]
            x, y = bottom.lines[0], right.lines[0]
            expected_x, mass_x = [1, 1, 5], [0, 2, 3]
            expected_y, mass_y = [2, 2, 4, 8], [0, 1, 2, 3]
            np.testing.assert_array_equal(y.get_ydata(), expected_y)
            y_mass = y.get_xdata()
            assert y.get_drawstyle() == "steps-pre"
            assert not figure.axes[0].get_shared_y_axes().joined(figure.axes[0], bottom)
        else:
            x, y = figure.axes[0].lines[0], figure.axes[3].lines[0]
            expected_x, mass_x = [1, 1, 3, 5], [0, 2, 3, 4]
            expected_y, mass_y = [2, 2, 4, 6, 8], [0, 1, 2, 3, 4]
            np.testing.assert_array_equal(y.get_xdata(), expected_y)
            y_mass = y.get_ydata()
            assert (
                not figure.axes[0]
                .get_shared_y_axes()
                .joined(figure.axes[0], figure.axes[1])
            )
        factor = (
            1 if stat == "count" else (100 if stat == "percent" else 1) / mass_x[-1]
        )
        np.testing.assert_array_equal(x.get_xdata(), expected_x)
        np.testing.assert_allclose(
            np.asarray(x.get_ydata(), dtype=float),
            np.asarray(mass_x) * factor,
            rtol=1e-14,
            atol=0,
        )
        np.testing.assert_allclose(
            np.asarray(y_mass, dtype=float),
            np.asarray(mass_y) * factor,
            rtol=1e-14,
            atol=0,
        )
        assert x.get_drawstyle() == "steps-post"
        for panel in p.spec.panels:
            for layer in panel.layers:
                if layer.type == "ecdf":
                    assert layer.histogram is None and layer.kde is None
                    assert layer.ecdf is not None and layer.ecdf.weights is None
    finally:
        plt.close(figure)


@pytest.mark.parametrize("kind", ["joint", "pair"])
@pytest.mark.parametrize(
    "options", [{"bins": 2}, {"kde": {}}, {"kde": {"weights": "h"}}]
)
def test_ecdf_does_not_ignore_histogram_bins_or_kde_options(kind, options):
    p = mp.plot(data())
    if kind == "joint":
        p.scatter("x", "y")
    before, history = p.to_json(), copy.deepcopy(p.action_log)
    with pytest.raises(ValueError):
        if kind == "joint":
            p.joint(marginal_kind="ecdf", marginal_stat="probability", **options)
        else:
            p.pair(["x", "y"], diag_kind="ecdf", diag_stat="probability", **options)
    assert p.to_json() == before and p.action_log == history


@pytest.mark.parametrize("kind", ["joint", "pair"])
@pytest.mark.parametrize("stat", ["density", None, True, {}, []])
def test_ecdf_requires_a_non_density_mass_stat(kind, stat):
    with pytest.raises(ValueError, match="ECDF"):
        build(kind, stat)


@pytest.mark.parametrize("kind", ["joint", "pair"])
def test_ecdf_grid_refreshes_after_setdata(kind):
    p = build(kind, "count")
    p.dispatch(
        mp.actions.SetData({"x": [1, 2, None], "y": [3, None, 4], "h": ["A"] * 3})
    )
    figure = p.render()
    try:
        indices = [1, 2] if kind == "joint" else [0, 3]
        for index in indices:
            line = figure.axes[index].lines[0]
            values = (
                line.get_xdata() if kind == "joint" and index == 1 else line.get_ydata()
            )
            assert np.asarray(values, dtype=float)[-1] == (1 if kind == "joint" else 2)
    finally:
        plt.close(figure)


def test_ecdf_joint_raw_hue_selection_and_log_value_axes():
    p = (
        mp.plot(data())
        .scatter("x", "y", group="h", hue_order=["A"])
        .xscale("log")
        .yscale("log")
        .joint(marginal_kind="ecdf", marginal_stat="count")
    )
    figure = p.render()
    try:
        main, right, bottom = figure.axes
        assert len(bottom.lines) == len(right.lines) == 1
        np.testing.assert_array_equal(bottom.lines[0].get_xdata(), [1, 1])
        np.testing.assert_array_equal(bottom.lines[0].get_ydata(), [0, 2])
        assert main.get_xscale() == bottom.get_xscale() == "log"
        assert (
            right.get_yscale() == "log"
            and right.get_xscale() == bottom.get_yscale() == "linear"
        )
    finally:
        plt.close(figure)


@pytest.mark.parametrize("center", ["hist2d", "hexbin"])
def test_ecdf_marginals_work_with_opt_in_binned_centers(center):
    p = mp.plot(data())
    getattr(p, center)("x", "y", colorbar=False)
    p.joint(marginal_kind="ecdf", marginal_stat="percent")
    figure = p.render()
    try:
        assert len(figure.axes) == 3
        assert np.asarray(figure.axes[2].lines[0].get_ydata(), dtype=float)[-1] == 100
    finally:
        plt.close(figure)
