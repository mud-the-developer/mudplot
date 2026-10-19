"""Vertical numeric stems preserve supplied rows and explicit raw baseline."""

import copy

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.container import StemContainer


def data():
    return {"x": [2.0, 1.0, 2.0], "y": [3.0, -1.0, 4.0]}


def test_stems_preserve_row_order_duplicates_style_baseline_and_source():
    p = mp.plot(data()).stem(
        "x",
        "y",
        baseline=0.5,
        label="observed",
        color="#225577",
        line_width=2.0,
        line_style="--",
        marker="s",
        marker_size=0,
        alpha=0.4,
    )
    original = copy.deepcopy(p.spec)
    assert (
        mp.validate(p.spec) == []
        and mp.from_json(p.to_json()) == p.spec
        and mp.apply(p.action_log) == p.spec
    )
    figure = p.render()
    try:
        axes = figure.axes[0]
        container = axes.containers[0]
        assert isinstance(container, StemContainer)
        np.testing.assert_array_equal(container.markerline.get_xdata(), [2, 1, 2])
        np.testing.assert_array_equal(container.markerline.get_ydata(), [3, -1, 4])
        np.testing.assert_array_equal(
            container.stemlines.get_segments(),
            [[[2, 0.5], [2, 3]], [[1, 0.5], [1, -1]], [[2, 0.5], [2, 4]]],
        )
        np.testing.assert_array_equal(container.baseline.get_ydata(), [0.5, 0.5])
        assert (
            container.markerline.get_markersize() == 0
            and container.markerline.get_marker() == "s"
        )
        assert (
            container.stemlines.get_alpha()
            == container.markerline.get_alpha()
            == container.baseline.get_alpha()
            == 0.4
        )
        np.testing.assert_allclose(container.stemlines.get_linewidth(), 2)
        assert container.baseline.get_linewidth() == 2
        assert (
            container.get_label() == "observed"
            and container.markerline.get_color() == "#225577"
        )
        assert p.spec == original and p.spec.data.columns == data()
    finally:
        plt.close(figure)


def test_default_zero_baseline_and_secondary_axis_routing():
    p = mp.plot(data()).secondary_yaxis().stem("x", "y", axis="y2")
    figure = p.render()
    try:
        assert not figure.axes[0].containers
        container = figure.axes[1].containers[0]
        assert isinstance(container, StemContainer)
        np.testing.assert_array_equal(container.baseline.get_ydata(), [0, 0])
    finally:
        plt.close(figure)


def test_positive_log_axes_require_actual_positive_baseline():
    p = (
        mp.plot({"x": [1, 2], "y": [2, 4]})
        .stem("x", "y", baseline=1)
        .xscale("log")
        .yscale("log")
    )
    figure = p.render()
    try:
        assert figure.axes[0].get_xscale() == figure.axes[0].get_yscale() == "log"
        container = figure.axes[0].containers[0]
        assert isinstance(container, StemContainer)
        np.testing.assert_array_equal(
            container.stemlines.get_segments(), [[[1, 1], [1, 2]], [[2, 1], [2, 4]]]
        )
    finally:
        plt.close(figure)
    bad = mp.plot({"x": [1, 2], "y": [2, 4]}).stem("x", "y").yscale("log")
    with pytest.raises(ValueError, match="baseline"):
        bad.render()


@pytest.mark.parametrize(
    "source",
    [
        {"x": [], "y": []},
        {"x": [True], "y": [1]},
        {"x": [1], "y": [None]},
        {"x": ["A"], "y": [1]},
        {"x": [1], "y": [float("inf")]},
    ],
)
def test_invalid_data_fails_before_owned_figures(source):
    p = mp.plot(source).stem("x", "y")
    before = plt.get_fignums()
    with pytest.raises(ValueError):
        p.render()
    assert plt.get_fignums() == before


@pytest.mark.parametrize("baseline", [True, float("nan"), float("inf"), "zero"])
def test_invalid_baseline_fails_without_overwriting_output(tmp_path, baseline):
    p = mp.plot(data()).stem("x", "y", baseline=baseline)
    target = tmp_path / "old.png"
    target.write_bytes(b"previous")
    before = plt.get_fignums()
    with pytest.raises((ValueError, TypeError)):
        p.save(target)
    assert target.read_bytes() == b"previous" and plt.get_fignums() == before


@pytest.mark.parametrize(
    "style",
    [
        {"group": "x"},
        {"orient": "h"},
        {"semantics": {"hue": "x"}},
        {"weights": "x"},
        {"density": True},
        {"colorbar": True},
        {"matrix": "unused"},
        {"bins": 12},
        {"value": 1},
        {"quiver_scale": 3},
        {"marker_size": -1},
        {"line_width": float("inf")},
        {"marker_size": True},
        {"line_width": 1001},
    ],
)
def test_unsupported_mappings_and_horizontal_geometry_are_not_ignored(style):
    p = mp.plot(data()).stem("x", "y", **style)
    with pytest.raises(ValueError):
        p.render()


@pytest.mark.parametrize("projection", ["polar", "3d"])
def test_stem_does_not_silently_route_to_another_projection(projection):
    p = mp.plot(data()).stem("x", "y")
    if projection == "polar":
        p.projection_polar()
    else:
        p.projection3d()
    with pytest.raises(ValueError):
        p.render()


def test_setdata_changes_segments_without_mutating_source_or_stale_artists():
    p = mp.plot(data()).stem("x", "y", baseline=-1)
    updated = {"x": [3, 2], "y": [4, 5]}
    p.dispatch(mp.actions.SetData(updated))
    figure = p.render()
    try:
        container = figure.axes[0].containers[0]
        assert isinstance(container, StemContainer)
        np.testing.assert_array_equal(
            container.stemlines.get_segments(), [[[3, -1], [3, 4]], [[2, -1], [2, 5]]]
        )
        assert p.spec.data.columns == updated and mp.apply(p.action_log) == p.spec
    finally:
        plt.close(figure)


def test_single_observation_is_preserved_without_invented_series():
    p = mp.plot({"x": [3], "y": [-2]}).stem("x", "y")
    figure = p.render()
    try:
        container = figure.axes[0].containers[0]
        assert isinstance(container, StemContainer)
        np.testing.assert_array_equal(
            container.stemlines.get_segments(), [[[3, 0], [3, -2]]]
        )
    finally:
        plt.close(figure)


@pytest.mark.parametrize(
    "axis,source",
    [("x", {"x": [0, 1], "y": [2, 3]}), ("y", {"x": [1, 2], "y": [0, 3]})],
)
def test_log_axis_does_not_clip_nonpositive_observations(axis, source):
    p = mp.plot(source).stem("x", "y", baseline=1)
    if axis == "x":
        p.xscale("log")
    else:
        p.yscale("log")
    with pytest.raises(ValueError, match="positive"):
        p.render()


def test_stem_does_not_enable_unsupported_facet_or_dropna_selection():
    p = mp.plot({"x": [1, 2], "y": [2, 3], "g": ["A", "B"]}).stem("x", "y")
    before, history = p.spec, p.action_log
    with pytest.raises(ValueError):
        p.facet(col="g")
    assert p.spec == before and p.action_log == history
    spec = p.spec
    spec.panels[0].dropna = ["x"]
    assert any("does not support panel filters" in issue for issue in mp.validate(spec))


def test_stem_row_budget_and_capability_are_explicit():
    p = mp.plot({"x": list(range(10001)), "y": [1] * 10001}).stem("x", "y")
    assert any("10000" in issue for issue in mp.validate(p.spec))
    assert mp.capabilities()["layers"]["stem"]["required"] == ["x", "y"]
