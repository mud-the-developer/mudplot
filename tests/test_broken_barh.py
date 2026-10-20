"""Explicit numeric start/duration intervals in one raw-coordinate band."""

import copy

import matplotlib.colors as colors
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import PolyCollection
from matplotlib.path import Path


def _bounds(path: Path):
    xy = np.asarray(path.vertices, dtype=float)
    return xy[:, 0].min(), xy[:, 0].max(), xy[:, 1].min(), xy[:, 1].max()


@pytest.mark.parametrize("line_width", [0, 2])
def test_interval_paths_preserve_overlaps_source_geometry_and_style(line_width):
    source = {"start": [3.0, 1.0, 3.0], "duration": [1.0, 2.0, 0.5]}
    p = mp.plot(source).broken_barh(
        "start",
        "duration",
        bottom=1,
        height=1,
        color="#225577",
        edge_color="#aa3344",
        line_width=line_width,
        line_style="--",
        alpha=0.4,
        label="given",
    )
    before = copy.deepcopy(p.spec)
    assert (
        mp.validate(p.spec) == []
        and mp.from_json(p.to_json()) == p.spec
        and mp.apply(p.action_log) == p.spec
    )
    figure = p.render()
    try:
        band = figure.axes[0].collections[0]
        assert isinstance(band, PolyCollection)
        paths = band.get_paths()
        assert len(paths) == 3
        bounds = sorted(_bounds(path) for path in paths)
        np.testing.assert_array_equal(
            bounds, [[1, 3, 1, 2], [3, 3.5, 1, 2], [3, 4, 1, 2]]
        )
        np.testing.assert_allclose(
            colors.to_rgba_array(band.get_facecolor()),
            [colors.to_rgba("#225577", alpha=0.4)],
        )
        np.testing.assert_allclose(
            colors.to_rgba_array(band.get_edgecolor()),
            [colors.to_rgba("#aa3344", alpha=0.4)],
        )
        np.testing.assert_allclose(band.get_linewidth(), line_width)
        styles = band.get_linestyle()
        assert isinstance(styles, list)
        assert (styles[0][1] is None) == (line_width == 0)
        assert band.get_label() == "given" and figure.axes[0].get_legend() is not None
        assert p.spec == before and p.spec.data.columns == source
    finally:
        plt.close(figure)


def test_one_interval_and_default_band_can_route_secondary_axis():
    p = (
        mp.plot({"start": [-2.0], "duration": [0.5]})
        .secondary_yaxis()
        .broken_barh("start", "duration", axis="y2")
    )
    figure = p.render()
    try:
        assert not figure.axes[0].collections
        band = figure.axes[1].collections[0]
        assert isinstance(band, PolyCollection)
        np.testing.assert_array_equal(_bounds(band.get_paths()[0]), [-2, -1.5, 0, 1])
    finally:
        plt.close(figure)


@pytest.mark.parametrize(
    "starts,durations",
    [
        ([], []),
        ([True], [1]),
        ([None], [1]),
        (["1"], [1]),
        ([float("inf")], [1]),
        ([1], [0]),
        ([1], [-1]),
        ([1], [True]),
        ([1], [None]),
        ([1], [float("nan")]),
        ([1], [float("inf")]),
        ([1e308], [1e308]),
        ([1e300], [1]),
        ([2**53], [1]),
    ],
)
def test_invalid_or_collapsed_intervals_fail_before_artists(starts, durations):
    p = mp.plot({"start": starts, "duration": durations}).broken_barh(
        "start", "duration"
    )
    before = plt.get_fignums()
    with pytest.raises(ValueError):
        p.render()
    assert plt.get_fignums() == before


@pytest.mark.parametrize(
    "bottom,height",
    [
        (True, 1),
        (float("inf"), 1),
        (0, 0),
        (0, -1),
        (0, True),
        (0, float("inf")),
        (2**53, 1),
        (1.7e308, 1e308),
    ],
)
def test_invalid_or_collapsed_band_preserves_existing_output(tmp_path, bottom, height):
    p = mp.plot({"start": [1], "duration": [2]}).broken_barh(
        "start", "duration", bottom=bottom, height=height
    )
    target = tmp_path / "old.png"
    target.write_bytes(b"previous")
    before = plt.get_fignums()
    with pytest.raises(ValueError):
        p.save(target)
    assert target.read_bytes() == b"previous" and plt.get_fignums() == before


@pytest.mark.parametrize(
    "style",
    [
        {"orient": "h"},
        {"group": "start"},
        {"weights": "duration"},
        {"semantics": {"hue": "start"}},
        {"density": True},
        {"marker": "s"},
        {"colorbar": True},
    ],
)
def test_unimplemented_mappings_are_not_ignored(style):
    p = mp.plot({"start": [1], "duration": [2]}).broken_barh(
        "start", "duration", **style
    )
    with pytest.raises(ValueError):
        p.render()


@pytest.mark.parametrize("axis", ["x", "y"])
def test_initial_band_subset_requires_linear_axes(axis):
    p = mp.plot({"start": [1], "duration": [2]}).broken_barh(
        "start", "duration", bottom=1
    )
    if axis == "x":
        p.xscale("log")
    else:
        p.yscale("log")
    with pytest.raises(ValueError, match="linear"):
        p.render()


def test_setdata_rebuilds_intervals_and_rejects_unsupported_cohort_selection():
    p = mp.plot({"start": [1, 2], "duration": [2, 3], "g": ["A", "B"]}).broken_barh(
        "start", "duration"
    )
    updated = {"start": [4, 2], "duration": [1, 0.5], "g": ["A", "B"]}
    p.dispatch(mp.actions.SetData(updated))
    figure = p.render()
    try:
        band = figure.axes[0].collections[0]
        assert isinstance(band, PolyCollection)
        np.testing.assert_array_equal(
            sorted(_bounds(path)[:2] for path in band.get_paths()),
            [[2, 2.5], [4, 5]],
        )
        assert p.spec.data.columns == updated and mp.apply(p.action_log) == p.spec
    finally:
        plt.close(figure)
    before, history = p.spec, p.action_log
    with pytest.raises(ValueError):
        p.facet(col="g")
    assert p.spec == before and p.action_log == history
    spec = p.spec
    spec.panels[0].dropna = ["start"]
    assert any("does not support panel filters" in issue for issue in mp.validate(spec))


@pytest.mark.parametrize("projection", ["polar", "3d"])
def test_intervals_do_not_silently_switch_projection(projection):
    p = mp.plot({"start": [1], "duration": [2]}).broken_barh("start", "duration")
    if projection == "polar":
        p.projection_polar()
    else:
        p.projection3d()
    with pytest.raises(ValueError):
        p.render()


def test_interval_columns_must_remain_row_aligned():
    with pytest.raises(ValueError):
        mp.plot({"start": [1, 2], "duration": [3]}).broken_barh(
            "start", "duration"
        ).render()


def test_interval_budget_and_capability_are_explicit():
    p = mp.plot({"start": list(range(10001)), "duration": [1] * 10001}).broken_barh(
        "start", "duration"
    )
    assert any("10000" in issue for issue in mp.validate(p.spec))
    assert mp.capabilities()["layers"]["broken_barh"]["required"] == ["x", "y"]
