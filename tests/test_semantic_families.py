"""Raw row roles share domains across point/category/curve/empirical marks."""

import io
import xml.etree.ElementTree as ET
from datetime import datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def source():
    return {
        "x": [0, 1, 2, 0, 1, 2],
        "value": [1, 1, 2, 1, 4, 4],
        "category": ["a", "b", "a", "a", "b", "a"],
        "hue": [-10] * 3 + [10] * 3,
        "size": [1] * 3 + [3] * 3,
        "shape": ["left"] * 3 + ["right"] * 3,
        "weight": [1, 2, 1, 2, 1, 1],
    }


def config(**overrides):
    return {
        "scale_id": "shared",
        "hue": "hue",
        "hue_kind": "numeric",
        "size": "size",
        "sizes": [2, 8],
        "style": "shape",
        **overrides,
    }


def data_lines(ax):
    return [line for line in ax.lines if len(line.get_xdata())]


def test_four_families_share_raw_domains_colours_and_physical_units():
    data = source()
    p = mp.plot(data).layout(2, 2).size(10, 7)
    mapping = config()
    p.scatter("x", "value", semantics=mapping, panel=0)
    p.lineplot("x", "value", semantics=mapping, errorbar=None, panel=1)
    p.stripplot(
        "category", "value", semantics=mapping, strip={"jitter_policy": "none"}, panel=2
    )
    p.ecdf("value", weights="weight", semantics=mapping, panel=3)
    assert mp.validate(p.spec) == []
    fig = p.render()
    scatter, line, strip, ecdf = fig.axes
    for index in range(2):
        point = scatter.collections[index]
        category = strip.collections[index]
        curve = data_lines(line)[index]
        empirical = data_lines(ecdf)[index]
        diameter = 2 if index == 0 else 8
        np.testing.assert_array_equal(point.get_sizes(), [diameter**2] * 3)
        np.testing.assert_array_equal(category.get_sizes(), [diameter**2] * 3)
        assert curve.get_linewidth() == empirical.get_linewidth() == diameter
        np.testing.assert_allclose(
            point.get_facecolors()[0], category.get_facecolors()[0]
        )
        np.testing.assert_allclose(point.get_facecolors()[0], curve.get_color())
        np.testing.assert_allclose(point.get_facecolors()[0], empirical.get_color())
    np.testing.assert_array_equal(
        strip.collections[0].get_offsets(), [[0, 1], [1, 1], [0, 2]]
    )
    np.testing.assert_array_equal(
        strip.collections[1].get_offsets(), [[0, 1], [1, 4], [0, 4]]
    )
    np.testing.assert_allclose(data_lines(ecdf)[0].get_ydata(), [0, 0.75, 1])
    np.testing.assert_allclose(data_lines(ecdf)[1].get_ydata(), [0, 0.5, 1])
    assert p.spec.data.columns == data
    assert mp.apply(p.action_log) == mp.Plot.from_json(p.to_json()).spec == p.spec


@pytest.mark.parametrize("orient", ["v", "h"])
def test_strip_reserved_hue_slots_and_seed_keep_category_and_role_selection(orient):
    data = {
        "c": [10, 10, 40, 40, 10],
        "v": [1, 2, 3, 4, -9],
        "h": ["A", "B", "A", "B", None],
        "s": [1, 3, 1, 3, 9],
    }
    mapping = {
        "hue": "h",
        "hue_order": ["A", "empty", "B"],
        "size": "s",
        "sizes": [2, 8],
    }
    p = mp.plot(data).stripplot(
        "c",
        "v",
        semantics=mapping,
        native_scale=True,
        order=[40, 100, 10],
        dodge=0.9,
        jitter=0.2,
        strip={"seed": 17},
        orient=orient,
    )
    (p.xscale if orient == "h" else p.yscale)("log")
    assert mp.validate(p.spec) == []  # Negative measurement has missing required hue.
    ax = p.render().axes[0]
    offsets = np.asarray(ax.collections[0].get_offsets())
    dim = int(orient == "h")
    jitter = np.random.default_rng(17).uniform(-1.8, 1.8, 4)
    np.testing.assert_allclose(
        offsets[:, 1] if dim else offsets[:, 0],
        np.array([10, 10, 40, 40]) + np.array([-9, 9, -9, 9]) + jitter,
    )
    np.testing.assert_array_equal(offsets[:, 0] if dim else offsets[:, 1], [1, 2, 3, 4])
    assert p.spec.data.columns == data


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("complementary", [False, True])
def test_ecdf_markers_are_actual_right_continuous_knots_not_boundary_sentinel(
    orient, complementary
):
    data = {"v": [1, 1, 2], "w": [1, 2, 1], "shape": ["A"] * 3}
    p = (
        mp.plot(data)
        .ecdf(
            "v",
            weights="w",
            orient=orient,
            complementary=complementary,
            semantics={"style": "shape"},
            marker_size=5,
        )
        .size(6, 4)
    )
    fig = p.render()
    ax = fig.axes[0]
    line = data_lines(ax)[0]
    line.set_gid("empirical-observations")
    buffer = io.StringIO()
    fig.savefig(buffer, format="svg")
    document = ET.fromstring(buffer.getvalue())
    group = next(
        node
        for node in document.iter()
        if node.attrib.get("id") == "empirical-observations"
    )
    marks = [node for node in group.iter() if node.tag.endswith("}use")]
    assert len(marks) == 2
    mass = [0.25, 0] if complementary else [0.75, 1]
    points = (
        np.column_stack((mass, [1, 2]))
        if orient == "h"
        else np.column_stack(([1, 2], mass))
    )
    expected = ax.transData.transform(points) * (72 / fig.dpi)
    expected[:, 1] = fig.get_size_inches()[1] * 72 - expected[:, 1]
    np.testing.assert_allclose(
        [[float(mark.attrib["x"]), float(mark.attrib["y"])] for mark in marks],
        expected,
        rtol=0,
        atol=1e-4,
    )
    assert p.spec.data.columns == data


def test_raw_tuple_partition_does_not_merge_clipped_hues_or_zero_weight_rows():
    data = {"v": [1, 2, 4, 8, -1], "h": [1, 1, 2, 2, None], "w": [1, 1, 1, 1, 0]}
    p = (
        mp.plot(data)
        .ecdf(
            "v",
            weights="w",
            semantics={"hue": "h", "hue_kind": "numeric", "hue_norm": [0, 0.5]},
            colorbar=True,
        )
        .xscale("log")
    )
    assert mp.validate(p.spec) == []
    lines = data_lines(p.render().axes[0])
    assert len(lines) == 2
    np.testing.assert_array_equal(lines[0].get_xdata(), [1, 1, 2])
    np.testing.assert_array_equal(lines[1].get_xdata(), [4, 4, 8])
    np.testing.assert_allclose(lines[0].get_color(), lines[1].get_color())


@pytest.mark.parametrize("kind", ["stripplot", "ecdf"])
def test_date_secondary_geometry_matches_elapsed_days_and_empirical_values(kind):
    dates = ["2026-01-01", "2026-01-11", "2026-01-11"]
    data = {"date": dates, "v": [1, 2, 3], "h": [-1, 1, 1]}
    p = mp.plot(data)
    mapping = {"hue": "h", "hue_kind": "numeric"}
    if kind == "stripplot":
        p.stripplot(
            "date", "v", semantics=mapping, strip={"jitter_policy": "none"}, axis="y2"
        )
    else:
        p.ecdf("date", semantics=mapping, axis="y2")
    p.date_axis("x", timezone="UTC").secondary_yaxis()
    assert mp.validate(p.spec) == []
    fig = p.render()
    assert not fig.axes[0].collections and not data_lines(fig.axes[0])
    days = [
        (datetime.fromisoformat(value) - datetime(1970, 1, 1)).days for value in dates
    ]
    secondary = fig.axes[1]
    if kind == "stripplot":
        np.testing.assert_array_equal(
            secondary.collections[0].get_offsets(), np.column_stack([days, [1, 2, 3]])
        )
    else:
        curves = data_lines(secondary)
        assert len(curves) == 2
        np.testing.assert_array_equal(curves[0].get_xdata(), [days[0], days[0]])
        np.testing.assert_array_equal(curves[1].get_xdata(), [days[1], days[1]])
        np.testing.assert_array_equal(curves[0].get_ydata(), [0, 1])
        np.testing.assert_array_equal(curves[1].get_ydata(), [0, 1])
        assert curves[1].get_xdata()[0] - curves[0].get_xdata()[0] == 10
    assert p.spec.data.columns == data
    assert mp.apply(p.action_log) == mp.Plot.from_json(p.to_json()).spec


def test_boolean_false_weight_is_invalid_not_silently_a_zero_mass_row():
    p = mp.plot({"v": [1, 2], "h": ["A", "A"], "w": [False, 1]}).ecdf(
        "v", weights="w", semantics={"hue": "h"}
    )
    assert any("finite nonnegative" in issue for issue in mp.validate(p.spec))
    with pytest.raises(ValueError, match="finite nonnegative"):
        p.render()


def test_horizontal_strip_secondary_clock_uses_y2_elapsed_days_not_ordinal_dates():
    dates = ["2026-01-01", "2026-01-11", "2026-01-11"]
    data = {"date": dates, "value": [1, 2, 3], "hue": [-1, 1, 1]}
    p = (
        mp.plot(data)
        .stripplot(
            "date",
            "value",
            semantics={"hue": "hue", "hue_kind": "numeric"},
            orient="h",
            axis="y2",
            strip={"jitter_policy": "none"},
        )
        .secondary_yaxis()
        .date_axis("y2", timezone="UTC")
    )
    assert mp.validate(p.spec) == []
    secondary = p.render().axes[1]
    days = [
        (datetime.fromisoformat(value) - datetime(1970, 1, 1)).days for value in dates
    ]
    np.testing.assert_array_equal(
        secondary.collections[0].get_offsets(), np.column_stack([[1, 2, 3], days])
    )
    assert p.spec.data.columns == data
