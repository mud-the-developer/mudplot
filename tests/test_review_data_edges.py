"""DATA-08/09: distinguish valid empty raw plots from undefined statistics."""

import copy

import matplotlib

matplotlib.use("Agg")
import mudplot as mp
import numpy as np
import pytest


@pytest.mark.parametrize("kind", ["line", "scatter"])
def test_named_empty_raw_data_is_a_valid_empty_figure(kind):
    plot = getattr(mp.plot({"x": [], "y": []}), kind)("x", "y")
    assert mp.validate(plot.spec) == []
    axes = plot.render().axes[0]
    assert not axes.lines and not axes.collections and not axes.patches
    assert mp.Plot.from_json(plot.to_json()).spec == plot.spec


@pytest.mark.parametrize("kind", ["barplot", "pointplot", "countplot", "lineplot"])
@pytest.mark.parametrize("missing", [False, True])
def test_statistical_layers_reject_no_usable_observations(kind, missing):
    raw = {"x": [None] if missing else [], "y": [None] if missing else []}
    before = copy.deepcopy(raw)
    plot = mp.plot(raw)
    if kind == "countplot":
        plot.countplot("x")
    else:
        getattr(plot, kind)("x", "y", errorbar=None)
    assert any("no usable observations" in issue for issue in mp.validate(plot.spec))
    with pytest.raises(ValueError, match="no usable observations"):
        plot.render()
    assert raw == before and plot.spec.data.columns == before


@pytest.mark.parametrize("kind", ["barplot", "pointplot"])
def test_singleton_estimate_stays_visible_without_a_fabricated_interval(kind):
    plot = getattr(mp.plot({"x": ["A"], "y": [3]}), kind)("x", "y")
    with pytest.warns(UserWarning, match="fewer than 2"):
        axes = plot.render().axes[0]
    if kind == "barplot":
        assert axes.patches[0].get_height() == 3
    else:
        np.testing.assert_array_equal(axes.lines[0].get_ydata(), [3])
    assert not axes.containers or all(
        not hasattr(container, "lines") for container in axes.containers
    )


@pytest.mark.parametrize(
    "sort,expected_x,expected_y",
    [(False, [2, 1, 0], [4.5, 1, 0]), (True, [0, 1, 2], [0, 1, 4.5])],
)
def test_raw_paths_keep_duplicates_but_lineplot_explicitly_aggregates(
    sort, expected_x, expected_y
):
    raw = {"x": [2, 1, 2, 0], "y": [4, 1, 5, 0]}
    plot = (
        mp.plot(raw)
        .layout(1, 2)
        .line("x", "y")
        .lineplot("x", "y", errorbar=None, sort=sort, panel=1)
    )
    first, second = plot.render().axes
    np.testing.assert_array_equal(first.lines[0].get_xdata(), raw["x"])
    np.testing.assert_array_equal(first.lines[0].get_ydata(), raw["y"])
    np.testing.assert_array_equal(second.lines[0].get_xdata(), expected_x)
    np.testing.assert_array_equal(second.lines[0].get_ydata(), expected_y)
    assert plot.spec.data.columns == raw
