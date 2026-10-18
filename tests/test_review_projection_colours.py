"""PLOT-07/08: independent coordinate expectations and scalar guide domains."""

import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import PathCollection
from matplotlib.projections.polar import PolarAxes
from matplotlib.quiver import Quiver
from mpl_toolkits.mplot3d.art3d import Line3D, Path3DCollection
from mpl_toolkits.mplot3d.axes3d import Axes3D


@pytest.mark.parametrize("u,v", [(2.0, 0.0), (0.0, 1.0), (2.0, 1.0)])
def test_quiver_tip_is_data_vector_under_unequal_axis_units(u, v):
    p = (
        mp.plot({"x": [1.0], "y": [0.5], "u": [u], "v": [v]})
        .quiver("x", "y", "u", "v", scale=1, width=0.005)
        .size(6, 3)
    )
    p.dispatch(mp.actions.SetLimits("x", 0, 4))
    p.dispatch(mp.actions.SetLimits("y", 0, 2))
    before = p.to_json()
    fig = p.render()
    try:
        ax = fig.axes[0]
        arrows = ax.collections[0]
        assert isinstance(arrows, Quiver)
        assert (
            arrows.angles == "xy" and arrows.scale_units == "xy" and arrows.scale == 1
        )
        origin = arrows.get_offset_transform().transform(arrows.get_offsets())[0]
        vertices = (
            arrows.get_transform().transform(np.asarray(arrows.get_paths()[0].vertices))
            + origin
        )
        end = ax.transData.transform([1 + u, 0.5 + v])
        start = ax.transData.transform([1, 0.5])
        direction = end - start
        tip = vertices[np.argmax((vertices - origin) @ direction)]
        np.testing.assert_allclose(tip, end, atol=1e-5)
        assert p.to_json() == before
    finally:
        plt.close(fig)


def test_3d_line_and_scatter_preserve_asymmetric_xyz():
    columns = {"x": [1, 7, 3], "y": [11, 5, 2], "z": [19, 23, 13]}
    p = mp.plot(columns).projection3d().line3d("x", "y", "z").scatter3d("x", "y", "z")
    fig = p.render()
    try:
        ax = fig.axes[0]
        assert isinstance(ax, Axes3D)
        line = ax.lines[0]
        assert isinstance(line, Line3D)
        for actual, key in zip(line.get_data_3d(), ("x", "y", "z"), strict=True):
            np.testing.assert_array_equal(actual, columns[key])
        points = ax.collections[0]
        assert isinstance(points, Path3DCollection)
        for actual, key in zip(points._offsets3d, ("x", "y", "z"), strict=True):
            np.testing.assert_array_equal(actual, columns[key])
    finally:
        plt.close(fig)


def test_polar_radians_have_expected_cardinal_positions_without_data_rewrite():
    p = (
        mp.plot({"theta": [0, math.pi / 2, math.pi], "r": [1, 1, 1]})
        .projection_polar()
        .line("theta", "r")
        .scatter("theta", "r")
        .size(4, 4)
    )
    before = p.to_json()
    fig = p.render()
    try:
        ax = fig.axes[0]
        assert isinstance(ax, PolarAxes)
        np.testing.assert_array_equal(
            ax.lines[0].get_xdata(), [0, math.pi / 2, math.pi]
        )
        center = ax.transData.transform([0, 0])
        east, north, west = ax.transData.transform(
            [[0, 1], [math.pi / 2, 1], [math.pi, 1]]
        )
        assert east[0] > center[0] and west[0] < center[0] and north[1] > center[1]
        assert east[1] == pytest.approx(center[1]) and west[1] == pytest.approx(
            center[1]
        )
        assert p.to_json() == before
    finally:
        plt.close(fig)


def test_incompatible_projection_is_rejected_without_silent_cartesian_fallback():
    p = mp.plot({"x": [1, 2], "y": [2, 3]}).projection_polar().hist("x")
    before = p.to_json()
    with pytest.raises(ValueError, match="polar"):
        p.render()
    assert p.to_json() == before


def test_heatmap_domains_map_outside_missing_without_panel_leak():
    p = mp.plot().matrix("m", [[-5, 0, 5], [10, 20, 999]]).layout(1, 2).size(7, 3)
    mask = [[False, False, False], [False, False, True]]
    p.heatmap(
        "m", heatmap={"vmin": 0, "vmax": 10, "mask": mask}, clabel="fixed", panel=0
    )
    p.heatmap(
        "m", heatmap={"vmin": -10, "vmax": 20, "mask": mask}, clabel="other", panel=1
    )
    before = p.to_json()
    fig = p.render()
    try:
        images = [ax.images[0] for ax in fig.axes if ax.images]
        assert (
            len(images) == 2
            and images[0].get_clim() == (0, 10)
            and images[1].get_clim() == (-10, 20)
        )
        for image in images:
            values = image.get_array()
            assert values is not None
            assert np.ma.getmaskarray(values)[1, 2]
            assert image.colorbar is not None and image.colorbar.mappable is image
            assert image.colorbar.ax.get_ylim() == pytest.approx(image.get_clim())
        np.testing.assert_allclose(
            images[0].to_rgba(np.array([-5, 0, 5, 10, 20])),
            images[0].cmap([0, 0, 0.5, 1, 1]),
        )
        assert p.to_json() == before
    finally:
        plt.close(fig)


def test_numeric_semantic_hue_bounds_are_mapping_not_row_selection():
    values = [-5.0, 0.0, 5.0, 10.0, 20.0]
    p = (
        mp.plot({"x": [1, 2, 3, 4, 5], "y": [2, 3, 1, 4, 2], "c": values})
        .scatter(
            "x", "y", semantics={"hue": "c", "hue_kind": "numeric", "hue_norm": [0, 10]}
        )
        .size(5, 3)
    )
    before = p.to_json()
    fig = p.render()
    try:
        artist = fig.axes[0].collections[0]
        assert isinstance(artist, PathCollection)
        assert len(np.asarray(artist.get_offsets())) == len(values)
        guide = fig.axes[0].get_legend()
        assert guide is not None
        assert [text.get_text() for text in guide.get_texts()] == [
            "hue: c=0.0",
            "hue: c=5.0",
            "hue: c=10.0",
        ]
        colors = np.asarray(artist.get_facecolor())
        np.testing.assert_allclose(colors[0], colors[1])
        np.testing.assert_allclose(colors[-1], colors[-2])
        assert not np.allclose(colors[2], colors[0])
        assert p.to_json() == before
    finally:
        plt.close(fig)


def test_typed_heatmap_null_is_explicitly_rejected_not_silently_imputed():
    p = mp.plot().matrix("m", [[1, None]]).heatmap("m", heatmap={"vmin": 0, "vmax": 10})
    before = p.to_json()
    with pytest.raises(ValueError, match="finite numeric"):
        p.render()
    assert p.to_json() == before


@pytest.mark.parametrize(
    "values", [[5.0, 5.0, 5.0], [None, None, None], [1.0, None, 3.0]]
)
def test_native_scatter_color_domain_missing_and_constants_are_finite(values):
    p = (
        mp.plot({"x": [1, 2, 3], "y": [2, 3, 1], "c": values})
        .scatter("x", "y", c="c", colorbar=True, clabel="scalar")
        .size(4, 3)
    )
    fig = p.render()
    try:
        artist = fig.axes[0].collections[0]
        assert isinstance(artist, PathCollection)
        mapped = artist.get_array()
        assert mapped is not None
        assert np.ma.getmaskarray(mapped).tolist() == [v is None for v in values]
        assert (
            artist.colorbar is not None and artist.colorbar.ax.get_ylabel() == "scalar"
        )
        assert all(np.isfinite(artist.colorbar.ax.get_ylim()))
    finally:
        plt.close(fig)
