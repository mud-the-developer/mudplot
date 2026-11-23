"""C04 scientific/native contracts; no product-helper or default-pixel oracles."""

from __future__ import annotations

import copy
import inspect
import io
import math
import shutil
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.markers import MarkerStyle


def bodies(axis) -> list[Any]:
    return [artist for artist in axis.collections if isinstance(artist, PolyCollection)]


def gaussian(values, weights=None, *, points=13, factor=None, adjust=1):
    """Direct ordinary-range Gaussian equations, independent of engine helpers."""
    x = np.asarray(values, dtype=float)
    w = np.ones(len(x)) if weights is None else np.asarray(weights, dtype=float)
    probability = w / w.sum()
    mean = float(np.dot(probability, x))
    effective_n = 1 / float(np.dot(probability, probability))
    variance = float(np.dot(probability, (x - mean) ** 2)) / (
        1 - float(np.dot(probability, probability))
    )
    scale = effective_n ** (-0.2) if factor is None else factor
    bandwidth = math.sqrt(variance) * scale * adjust
    support = np.linspace(float(x.min()), float(x.max()), points)
    density = np.asarray(
        [
            sum(
                float(p) * math.exp(-0.5 * ((float(t) - float(v)) / bandwidth) ** 2)
                for p, v in zip(probability, x, strict=True)
            )
            / (bandwidth * math.sqrt(2 * math.pi))
            for t in support
        ]
    )
    return support, density


def native_body(axis, support, profile, center, width, side, orient):
    half = width / 2 * np.asarray(profile)
    lower = center - half if side <= 0 else np.full(len(half), center)
    upper = center + half if side >= 0 else np.full(len(half), center)
    return (axis.fill_between if orient == "h" else axis.fill_betweenx)(
        support, lower, upper
    )


@pytest.mark.parametrize("count", [1, 3, 4, 5])
@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("target", ["y", "y2"])
@pytest.mark.parametrize("reserve", [False, True])
def test_paired_half_lanes_keep_odd_observations_and_reserved_slots(
    count, orient, target, reserve
):
    sample = [1, 2, 3, 5]
    columns = {
        "c": ["A"] * (count * 4),
        "v": sample * count,
        "h": [f"h{i}" for i in range(count) for _ in sample],
        "id": [f"row-{i}" for i in range(count * 4)],
    }
    reserved = [f"h{i}" for i in range(count + int(reserve))]
    plot = mp.plot(columns).violin(
        "c",
        "v",
        group="h",
        hue_order=reserved,
        orient=orient,
        axis=target,
        split=True,
        inner="point",
        marker_size=7,
        width=0.8,
        gap=0.25,
        points=13,
        violin={"split_policy": "paired"},
    )
    if target == "y2":
        plot.secondary_yaxis("Actual target")
    figure = plot.render()
    axis = figure.axes[1 if target == "y2" else 0]
    reference = plt.figure().subplots()
    support, density = gaussian(sample)
    pairs = (len(reserved) + 1) // 2
    for index, body in enumerate(bodies(axis)):
        center = (index // 2 - (pairs - 1) / 2) * 0.8 / pairs
        side = -1 if index % 2 == 0 else 1
        width = 0.8 / pairs * 0.75
        expected = native_body(
            reference, support, density / density.max(), center, width, side, orient
        )
        np.testing.assert_allclose(
            body.get_paths()[0].vertices,
            expected.get_paths()[0].vertices,
            rtol=1e-12,
            atol=1e-12,
        )
        mark = axis.lines[index]
        actual = np.asarray(mark.get_xdata() if orient == "h" else mark.get_ydata())
        np.testing.assert_array_equal(actual, sample)
        assert mark.get_markersize() == 7
    assert len(bodies(axis)) == count
    assert len(axis.lines) == count
    assert plot.spec.data.columns == columns


@pytest.mark.parametrize(
    "normalization,common",
    [
        ("width", False),
        ("area", False),
        ("area", True),
        ("count", False),
        ("count", True),
    ],
)
def test_weighted_raw_tuple_fits_normalize_by_effective_hue_not_style_or_size(
    normalization, common
):
    samples = [[1, 2, 3], [1, 4, 9], [2, 4, 6], [1, 3, 5]]
    masses = [1, 2, 10, 5]
    table: dict[str, list[Any]] = {
        name: [] for name in ["c", "v", "h", "s", "method", "w", "id"]
    }
    for index, (sample, mass) in enumerate(zip(samples, masses, strict=True)):
        for row, value in enumerate(sample):
            for name, item in {
                "c": "A",
                "v": value,
                "h": "a" if index < 2 else "b",
                "s": index % 2,
                "method": "first" if index % 2 == 0 else "second",
                "w": mass,
                "id": f"{index}-{row}",
            }.items():
                table[name].append(item)
    plot = mp.plot(table).violin(
        "c",
        "v",
        weights="w",
        split=True,
        inner="quart",
        points=13,
        density_norm=normalization,
        common_norm=common,
        violin={"split_policy": "paired"},
        semantics={
            "hue": "h",
            "size": "s",
            "style": "method",
            "sizes": [0.5, 2],
            "markers": ["o"],
        },
    )
    axis = plot.render().axes[0]
    fits = [
        gaussian(sample, [mass] * 3)
        for sample, mass in zip(samples, masses, strict=True)
    ]
    reference = plt.figure().subplots()
    for index, body in enumerate(bodies(axis)):
        support, density = fits[index]
        pool = list(range(4)) if common else ([0, 1] if index < 2 else [2, 3])
        profile = density / density.max()
        if normalization == "area":
            profile = density / max(fits[item][1].max() for item in pool)
        if normalization == "count":
            profile = profile * masses[index] / max(masses[item] for item in pool)
        expected = native_body(
            reference, support, profile, 0, 0.8, -1 if index < 2 else 1, "v"
        )
        np.testing.assert_allclose(
            body.get_paths()[0].vertices,
            expected.get_paths()[0].vertices,
            rtol=1e-12,
            atol=1e-12,
        )
        assert body.get_linewidths()[0] == pytest.approx(0.5 if index % 2 == 0 else 2)
    assert len(bodies(axis)) == 4
    assert not axis.lines  # Quart spans are real segments; no unused style glyph.
    assert (
        sum(
            len(item.get_segments())
            for item in axis.collections
            if isinstance(item, LineCollection)
        )
        == 12
    )
    assert plot.spec.data.columns == table


def test_typed_category_hue_selection_retains_only_the_requested_boolean_rows():
    table = {
        "c": [True, 1, False, 0] * 3,
        "v": [1, 2, 3, 4, 2, 3, 4, 5, 4, 5, 6, 7],
        "h": [True, 1, False, 0] * 3,
        "id": list(range(12)),
    }
    plot = mp.plot(table).violin(
        "c",
        "v",
        order=[True],
        inner="point",
        violin={},
        semantics={"hue": "h", "hue_order": [True]},
    )
    axis = plot.render().axes[0]
    assert len(bodies(axis)) == 1
    np.testing.assert_array_equal(axis.lines[0].get_ydata(), [1, 2, 4])
    assert [item.get_text() for item in axis.get_xticklabels()] == ["True"]
    assert plot.spec.data.columns == table


@pytest.mark.parametrize("inner,component", [("point", "point"), ("box", "median")])
def test_style_owns_actual_named_inner_glyph_but_size_only_owns_body_outline(
    inner, component
):
    table = {
        "c": ["A"] * 8,
        "v": [1, 2, 3, 5] * 2,
        "h": ["left"] * 4 + ["right"] * 4,
        "size": [0] * 4 + [1] * 4,
    }
    plot = mp.plot(table).violin(
        "c",
        "v",
        inner=inner,
        violin={},
        semantics={
            "hue": "h",
            "style": "h",
            "size": "size",
            "sizes": [0, 2],
            "markers": ["D", "^"],
        },
        components={
            component: {
                "marker_size": 7,
                "marker_edge_width": 0.75,
                "face_color": "white",
            }
        },
    )
    axis = plot.render().axes[0]
    assert len(axis.lines) == 2
    for index, (line, marker) in enumerate(zip(axis.lines, ["D", "^"], strict=True)):
        expected = MarkerStyle(marker)
        native_marker = line._marker
        np.testing.assert_allclose(
            np.asarray(
                native_marker.get_path()
                .transformed(native_marker.get_transform())
                .vertices
            ),
            np.asarray(
                expected.get_path().transformed(expected.get_transform()).vertices
            ),
            rtol=0,
            atol=0,
        )
        assert line.get_markersize() == 7
        assert line.get_markeredgewidth() == 0.75
        assert bodies(axis)[index].get_linewidths()[0] == [0, 2][index]
        assert len(line.get_ydata()) == (4 if inner == "point" else 1)


def test_numeric_hue_and_size_can_have_more_than64_distinct_drawn_tuples():
    count = 65
    data = {
        "c": ["A"] * count,
        "v": list(range(count)),
        "h": list(range(count)),
        "s": list(range(count)),
    }
    plot = mp.plot(data).violin(
        "c",
        "v",
        inner="point",
        points=2,
        semantics={"hue": "h", "hue_kind": "numeric", "size": "s", "sizes": [0, 2]},
        colorbar=True,
    )
    figure = plot.render()
    axis = figure.axes[0]
    assert len(bodies(axis)) == count
    assert [line.get_ydata()[0] for line in axis.lines] == list(range(count))
    np.testing.assert_allclose(
        [body.get_linewidths()[0] for body in bodies(axis)], np.linspace(0, 2, count)
    )
    assert len(figure.axes) == 2
    np.testing.assert_allclose(figure.axes[1].get_ylim(), [0, 1])
    assert plot.spec.data.columns == data


def test_same_original_rows_share_domains_but_each_drawn_layer_retains_its_points():
    data = {
        "c": ["A"] * 4,
        "v": [1, 2, 3, 5],
        "h": ["a", "a", "b", "b"],
        "s": [0, 0, 1, 1],
        "id": ["z", "a", "q", "b"],
    }
    semantics = mp.SemanticSpec(scale_id="rows", hue="h", size="s", sizes=[0.5, 2])
    plot = mp.plot(data).violin("c", "v", inner="point", semantics=semantics)
    plot.violin(
        "c", "v", inner="point", axis="y2", semantics=semantics
    ).secondary_yaxis("Second instance")
    figure = plot.render()
    assert [len(bodies(axis)) for axis in figure.axes] == [2, 2]
    for axis in figure.axes:
        np.testing.assert_array_equal(
            np.concatenate([line.get_ydata() for line in axis.lines]), data["v"]
        )
        np.testing.assert_allclose(
            [body.get_linewidths()[0] for body in bodies(axis)], [0.5, 2]
        )
    assert plot.spec.data.columns == data


@pytest.mark.parametrize(
    "inner,segments,points",
    [("quart", 3, 0), ("stick", 4, 0), ("box", 2, 1), ("point", 0, 4)],
)
def test_zero_dashed_components_keep_all_segments_fill_and_independent_actual_glyphs(
    inner, segments, points
):
    styles = {"body": {"line_width": 0, "line_style": "--", "color": "red"}}
    for role in {
        "quart": ["quartile"],
        "stick": ["stick"],
        "box": ["whisker", "box", "median"],
        "point": ["point"],
    }[inner]:
        styles[role] = {"line_width": 0, "line_style": "--"}
        if role in ["median", "point"]:
            styles[role].update(marker="D", marker_size=6, marker_edge_width=0.75)
    plot = mp.plot({"c": ["A"] * 4, "v": [1, 2, 3, 5]}).violin(
        "c", "v", inner=inner, components=styles
    )
    figure = plot.render()
    axis = figure.axes[0]
    assert (
        sum(
            len(item.get_segments())
            for item in axis.collections
            if isinstance(item, LineCollection)
        )
        == segments
    )
    np.testing.assert_allclose(bodies(axis)[0].get_facecolor()[0, :3], [1, 0, 0])
    assert sum(len(line.get_ydata()) for line in axis.lines) == points
    if points:
        line = axis.lines[0]
        assert line.get_marker() == "D" and line.get_markersize() == 6
        line.set_gid("actual-observed-inner-glyphs")
        buffer = io.BytesIO()
        figure.savefig(buffer, format="svg")
        root = ET.fromstring(buffer.getvalue())
        ns = {"svg": "http://www.w3.org/2000/svg"}
        group = next(
            item
            for item in root.iter()
            if item.attrib.get("id") == "actual-observed-inner-glyphs"
        )
        visible = [
            item
            for item in group.findall(".//svg:use", ns)
            if "x" in item.attrib and "y" in item.attrib
        ]
        assert len(visible) == points


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("target", ["y", "y2"])
def test_both_declared_calendar_roles_keep_absolute_native_days_on_actual_target(
    orient, target
):
    table = {
        "c": ["2026-01-01"] * 3 + ["2026-01-05"] * 3,
        "v": ["2026-02-01", "2026-02-02", "2026-02-04"] * 2,
        "h": ["a"] * 6,
        "id": list(range(6)),
    }
    plot = mp.plot(table).violin(
        "c", "v", orient=orient, axis=target, inner="point", violin={}
    )
    if target == "y2":
        plot.secondary_yaxis("Absolute date")
    category_axis = target if orient == "h" else "x"
    value_axis = "x" if orient == "h" else target
    plot.date_axis(category_axis, timezone="UTC").date_axis(value_axis, timezone="UTC")
    figure = plot.render()
    axis = figure.axes[1 if target == "y2" else 0]
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    expected = [
        (datetime.fromisoformat(value).replace(tzinfo=UTC) - epoch).total_seconds()
        / 86400
        for value in table["v"]
    ]
    actual = np.concatenate(
        [line.get_xdata() if orient == "h" else line.get_ydata() for line in axis.lines]
    )
    np.testing.assert_array_equal(actual, expected)
    assert len(bodies(axis)) == 2
    assert plot.spec.data.columns == table


@pytest.mark.parametrize("role", ["box", "quartile", "point", "stick", "extrema"])
@pytest.mark.parametrize("kind", ["box", "boxenplot"])
def test_new_violin_component_roles_do_not_become_ignored_box_fields(kind, role):
    plot = getattr(mp.plot({"c": ["A"] * 4, "v": [1, 2, 3, 5]}), kind)(
        "c", "v", components={role: {"color": "red"}}
    )
    with pytest.raises(ValueError):
        plot.render()


@pytest.mark.parametrize(
    "inner,role",
    [("quart", "point"), ("point", "whisker"), ("box", "quartile"), (None, "median")],
)
def test_unavailable_native_inner_traits_reject_without_fabricating_marks(inner, role):
    plot = mp.plot({"c": ["A"] * 4, "v": [1, 2, 3, 5]}).violin(
        "c", "v", inner=inner, components={role: {"color": "red"}}
    )
    with pytest.raises(ValueError):
        plot.render()


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("target", ["y", "y2"])
@pytest.mark.parametrize("stat_scale", ["data", "axis"])
def test_native_log_base2_category_and_value_geometry_match_independent_working_units(
    orient, target, stat_scale
):
    random_state = np.random.get_state()
    table = {"c": [], "v": [], "h": [], "otherc": [], "otherv": []}
    for category in [2, 8]:
        for hue in ["a", "b", "c"]:
            for value in [1, 2, 4, 8]:
                for name, item in {
                    "c": category,
                    "v": value,
                    "h": hue,
                    "otherc": 4,
                    "otherv": 64,
                }.items():
                    table[name].append(item)
    plot = mp.plot(table).line("otherc", "otherv", axis=target)
    plot.violin(
        "c",
        "v",
        group="h",
        native_scale=True,
        stat_scale=stat_scale,
        orient=orient,
        axis=target,
        split=True,
        inner="point",
        points=13,
        width=0.8,
        gap=0.25,
        violin={"split_policy": "paired"},
    )
    if target == "y2":
        plot.secondary_yaxis("Native target")
    category_axis = target if orient == "h" else "x"
    value_axis = "x" if orient == "h" else target
    plot.axis_scale(category_axis, "log", options={"base": 2, "subs": [1.5]})
    plot.axis_scale(value_axis, "log", options={"base": 2, "subs": [1.5]})
    figure = plot.render()
    axis = figure.axes[1 if target == "y2" else 0]
    reference = plt.figure().subplots()
    reference.set_xscale("log", base=2)
    reference.set_yscale("log", base=2)
    reference.plot(table["otherc"], table["otherv"])
    working = (
        np.log10([1, 2, 4, 8]) if stat_scale == "axis" else np.asarray([1, 2, 4, 8])
    )
    support, density = gaussian(working)
    category_dim, value_dim = (1, 0) if orient == "h" else (0, 1)
    spacing = math.log10(8) - math.log10(2)
    expected = []
    # Native control is constructed in working coordinates, inverse-mapped once.
    temp = plt.figure().subplots()
    for hue_index in range(3):
        for category in [2, 8]:
            center = math.log10(category) + (hue_index // 2 - 0.5) * (0.8 * spacing) / 2
            body = native_body(
                temp,
                support,
                density / density.max(),
                center,
                0.8 * spacing / 2 * 0.75,
                -1 if hue_index % 2 == 0 else 1,
                orient,
            )
            vertices = np.asarray(body.get_paths()[0].vertices).copy()
            vertices[:, category_dim] = 10 ** vertices[:, category_dim]
            if stat_scale == "axis":
                vertices[:, value_dim] = 10 ** vertices[:, value_dim]
            expected.append(vertices)
            reference.fill(vertices[:, 0], vertices[:, 1])
    for actual, vertices in zip(bodies(axis), expected, strict=True):
        np.testing.assert_allclose(
            actual.get_paths()[0].vertices, vertices, rtol=1e-12, atol=1e-12
        )
    reference.autoscale_view()
    np.testing.assert_allclose(
        axis.dataLim.intervalx, reference.dataLim.intervalx, rtol=1e-12
    )
    np.testing.assert_allclose(
        axis.dataLim.intervaly, reference.dataLim.intervaly, rtol=1e-12
    )
    getter = axis.get_xlim if orient == "h" else axis.get_ylim
    expected_getter = reference.get_xlim if orient == "h" else reference.get_ylim
    np.testing.assert_allclose(getter(), expected_getter(), rtol=1e-12)
    assert axis.xaxis.get_transform().base == 2 and axis.yaxis.get_transform().base == 2
    before = [np.asarray(body.get_paths()[0].vertices).copy() for body in bodies(axis)]
    for dpi in [72, 300, 72]:
        figure.set_dpi(dpi)
        axis.invert_xaxis()
        figure.canvas.draw()
        for actual, vertices in zip(bodies(axis), before, strict=True):
            np.testing.assert_array_equal(actual.get_paths()[0].vertices, vertices)
    assert plot.spec.data.columns == table
    after_random = np.random.get_state()
    assert random_state[0] == after_random[0]
    np.testing.assert_array_equal(random_state[1], after_random[1])
    assert random_state[2:] == after_random[2:]


def test_clipped_weighted_profile_keeps_fitted_rows_and_true_weighted_quartiles():
    table = {
        "c": ["A"] * 6,
        "v": [1, 4, 9, "invalid-zero", None, 12],
        "w": [1, 3, 2, 0, 4, None],
        "id": ["a", "b", "c", "zero", "missing-value", "missing-weight"],
    }
    plot = mp.plot(table).violin(
        "c", "v", weights="w", inner="quart", clip=[2, 6], points=13, violin={}
    )
    axis = plot.render().axes[0]
    support = np.linspace(2, 6, 13)
    values = np.asarray([1, 4, 9.0])
    prob = np.asarray([1, 3, 2.0]) / 6
    mean = float(prob @ values)
    variance = float(prob @ ((values - mean) ** 2)) / (1 - float(prob @ prob))
    bandwidth = math.sqrt(variance) * (1 / float(prob @ prob)) ** (-0.2)
    density = np.asarray(
        [
            sum(
                p * math.exp(-0.5 * ((t - v) / bandwidth) ** 2)
                for p, v in zip(prob, values, strict=True)
            )
            / (bandwidth * math.sqrt(2 * math.pi))
            for t in support
        ]
    )
    reference = plt.figure().subplots()
    expected = native_body(reference, support, density / density.max(), 0, 0.8, 0, "v")
    np.testing.assert_allclose(
        bodies(axis)[0].get_paths()[0].vertices,
        expected.get_paths()[0].vertices,
        rtol=1e-12,
        atol=1e-12,
    )
    segments = next(
        item.get_segments()
        for item in axis.collections
        if isinstance(item, LineCollection)
    )
    np.testing.assert_array_equal([item[0, 1] for item in segments], [4, 4, 9])
    assert axis.dataLim.ymax == 9
    assert plot.spec.data.columns == table


def test_advanced_profile_and_selected_row_boundaries_retain_every_native_instance():
    count = 256
    data = {
        "c": ["A"] * (count * 2),
        "v": [1, 2] * count,
        "s": [index for index in range(count) for _ in range(2)],
    }
    plot = mp.plot(data).violin(
        "c",
        "v",
        inner=None,
        points=2,
        semantics={"size": "s", "sizes": [0.5, 2], "legend": False},
    )
    axis = plot.render().axes[0]
    assert len(bodies(axis)) == count
    centers = [
        float(
            np.mean(
                [
                    body.get_paths()[0].vertices[:, 0].min(),
                    body.get_paths()[0].vertices[:, 0].max(),
                ]
            )
        )
        for body in bodies(axis)
    ]
    np.testing.assert_allclose(
        centers,
        (np.arange(count) - (count - 1) / 2) * 0.8 / count,
        rtol=1e-12,
        atol=1e-12,
    )
    bad = {"c": ["A"] * 257, "v": [1] * 257, "s": list(range(257))}
    with pytest.raises(ValueError):
        mp.plot(bad).violin("c", "v", semantics={"size": "s"}).render()
    rows = mp.plot({"c": ["A"] * 10000, "v": list(range(10000))}).violin(
        "c", "v", inner="point", points=2, violin={}
    )
    np.testing.assert_array_equal(
        rows.render().axes[0].lines[0].get_ydata(), np.arange(10000)
    )
    with pytest.raises(ValueError):
        mp.plot({"c": ["A"] * 10001, "v": list(range(10001))}).violin(
            "c", "v", inner="point", points=2, violin={}
        ).render()
    with pytest.raises(ValueError):
        mp.plot(
            {"c": ["A"] * 65, "v": list(range(65)), "h": [str(i) for i in range(65)]}
        ).violin("c", "v", semantics={"hue": "h"}).render()


def test_live_hue_components_whole_replacement_refill_and_reopen_keep_native_views():
    table = {
        "c": ["2026-01-01"] * 8,
        "v": [1, 2, 3, 5] * 2,
        "h": [True] * 4 + [1] * 4,
        "cell": ["left"] * 4 + ["right"] * 4,
        "id": list(range(8)),
    }
    plot = mp.plot(table).violin(
        "c",
        "v",
        axis="y2",
        inner="box",
        split=True,
        violin={
            "split_policy": "paired",
            "hue_components": [
                {"level": True, "components": {"whisker": {"color": "red"}}},
                {"level": 1, "components": {"whisker": {"color": "blue"}}},
            ],
        },
        components={"body": {"alpha": 0.8}},
        semantics={"hue": "h"},
    )
    plot.secondary_yaxis("Measured response").date_axis("x", timezone="UTC")
    plot.facet(
        col="cell", col_order=["left", "empty", "right"], col_wrap=2, live=True
    ).layout(2, 2, width_ratios=[2, 1])

    def targets(document):
        return [
            axis
            for axis in document.render().axes
            if axis.get_ylabel() == "Measured response"
        ]

    axes = targets(plot)
    assert [len(bodies(axis)) for axis in axes] == [1, 0, 1]
    assert axes[0].get_position().width / axes[1].get_position().width == pytest.approx(
        2
    )
    np.testing.assert_allclose(
        next(
            item for item in axes[0].collections if isinstance(item, LineCollection)
        ).get_colors()[0, :3],
        [1, 0, 0],
    )
    np.testing.assert_allclose(
        next(
            item for item in axes[2].collections if isinstance(item, LineCollection)
        ).get_colors()[0, :3],
        [0, 0, 1],
    )
    local = copy.deepcopy(plot.spec.panels[0].layers[0])
    local.components.body.alpha = 0.2
    plot.dispatch(mp.actions.RemoveLayer(0, panel=0)).dispatch(
        mp.actions.AddLayer(local, panel=0)
    )
    reopened = mp.Plot.from_json(plot.to_json())
    assert [
        bodies(axis)[0].get_alpha() for axis in targets(reopened) if bodies(axis)
    ] == [0.2, 0.8]
    template = copy.deepcopy(reopened.spec.facet_template.template)
    template.layers[0].components.body.alpha = 0.4
    before = reopened.to_json()
    reopened.facet_template(template)
    after = reopened.to_json()
    assert [
        bodies(axis)[0].get_alpha() for axis in targets(reopened) if bodies(axis)
    ] == [0.4, 0.4]
    reopened.store.undo()
    assert reopened.to_json() == before
    reopened.store.redo()
    assert reopened.to_json() == after
    updated = copy.deepcopy(table)
    for name, values in {
        "c": ["2026-01-01"] * 4 + ["bad-excluded"] * 4,
        "v": [2, 3, 4, 6] + ["bad-excluded"] * 4,
        "h": [True] * 4 + ["bad-excluded"] * 4,
        "cell": ["empty"] * 4 + ["excluded"] * 4,
        "id": list(range(8, 16)),
    }.items():
        updated[name].extend(values)
    reopened.dispatch(mp.actions.SetData(updated))
    axes = targets(mp.Plot.from_json(reopened.to_json()))
    assert [len(bodies(axis)) for axis in axes] == [1, 1, 1]
    assert [bodies(axis)[0].get_alpha() for axis in axes] == [0.4, 0.4, 0.4]
    assert len(reopened.spec.panels) == 3 and reopened.spec.layout == [2, 2]
    assert reopened.spec.width_ratios == [2, 1]
    assert axes[0].get_position().width / axes[1].get_position().width == pytest.approx(
        2
    )
    assert reopened.spec.data.columns == updated


@pytest.mark.parametrize(
    "components,semantics,inner",
    [
        ({"body": {"color": "red"}}, {"hue": "h"}, "box"),
        ({"body": {"line_width": 2}}, {"size": "s"}, "box"),
        ({"body": {"line_style": "--"}}, {"style": "h"}, "quart"),
        ({"point": {"marker": "D"}}, {"style": "h"}, "point"),
        ({"median": {"marker": "D"}}, {"style": "h"}, "box"),
    ],
)
def test_owned_property_rejection_preserves_real_editor_spec_png_and_history(
    components, semantics, inner
):
    from dashboard.editor_server import EditorSession

    data = {
        "c": ["A"] * 8,
        "v": [1, 2, 3, 5] * 2,
        "h": ["a"] * 4 + ["b"] * 4,
        "s": [0] * 4 + [1] * 4,
    }
    plot = mp.plot(data).violin("c", "v", inner=inner, semantics=semantics)
    session = EditorSession()
    session.load_spec(plot.to_json())
    accepted = session.store.state.to_dict()
    png = session.png
    history = session.store.history
    invalid = copy.deepcopy(plot.spec.panels[0].layers[0])
    invalid.components = mp.DistributionComponentsSpec.from_dict(components)
    session.dispatch_safe(mp.actions.AddLayer(invalid))
    assert session.error is not None
    assert session.store.state.to_dict() == accepted and session.png == png
    assert session.store.history == history


@pytest.mark.parametrize("marker", ["P", "X"])
def test_scalar_registered_inner_glyph_and_component_stroke_are_native(marker):
    plot = mp.plot({"c": ["A"] * 4, "v": [1, 2, 3, 5]}).violin(
        "c",
        "v",
        inner="point",
        marker=marker,
        marker_size=8,
        components={"point": {"color": "red", "face_color": "white"}},
    )
    line = plot.render().axes[0].lines[0]
    assert line.get_marker() == marker
    assert line.get_markersize() == 8
    assert line.get_markeredgecolor() == "red"
    assert line.get_markerfacecolor() == "white"
    np.testing.assert_array_equal(line.get_ydata(), [1, 2, 3, 5])


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize(
    "showmeans,showextrema", [(None, None), (True, False), (False, True)]
)
def test_only_body_alpha_preserves_actual_native_legacy_inner_styles_and_spans(
    orient, showmeans, showextrema
):
    from mudplot.theme import spec_to_rcparams

    samples = [[1, 2, 3, 5], [2, 3, 5, 8]]
    data = {"c": ["A"] * 4 + ["B"] * 4, "v": samples[0] + samples[1]}
    plot = mp.plot(data).violin(
        "c",
        "v",
        orient=orient,
        points=21,
        width=0.8,
        showmeans=showmeans,
        showextrema=showextrema,
        components={"body": {"alpha": 0.9}},
    )
    with mpl.rc_context({"lines.linewidth": 2.7, "patch.edgecolor": "red"}):
        actual = plot.render().axes[0]
        with mpl.rc_context(
            spec_to_rcparams(plot.spec.theme, plot.spec.journal, n_colors=3)
        ):
            reference = plt.figure().subplots()
            options = {
                "positions": [0, 1],
                "widths": 0.8,
                "points": 21,
                "showmedians": True,
            }
            if showmeans is not None:
                options["showmeans"] = showmeans
            if showextrema is not None:
                options["showextrema"] = showextrema
            if "orientation" in inspect.signature(reference.violinplot).parameters:
                options["orientation"] = "horizontal" if orient == "h" else "vertical"
            else:
                options["vert"] = orient != "h"
            native = reference.violinplot(samples, **options)
    for got, wanted in zip(bodies(actual), native["bodies"], strict=True):
        wanted.set_alpha(0.9)
        np.testing.assert_allclose(
            got.get_paths()[0].vertices,
            wanted.get_paths()[0].vertices,
            rtol=1e-12,
            atol=1e-12,
        )
        np.testing.assert_allclose(got.get_edgecolor(), wanted.get_edgecolor())
        np.testing.assert_array_equal(got.get_linewidths(), wanted.get_linewidths())
        assert got.get_alpha() == 0.9
    got_inner = [
        artist for artist in actual.collections if isinstance(artist, LineCollection)
    ]
    expected_inner = [
        artist for artist in reference.collections if isinstance(artist, LineCollection)
    ]
    assert len(got_inner) == len(expected_inner)
    for got, wanted in zip(got_inner, expected_inner, strict=True):
        np.testing.assert_allclose(
            got.get_segments(), wanted.get_segments(), rtol=1e-12, atol=1e-12
        )
        np.testing.assert_array_equal(got.get_colors(), wanted.get_colors())
        np.testing.assert_array_equal(got.get_linewidths(), wanted.get_linewidths())


def test_requested_native_legacy_mean_component_enables_only_that_actual_statistic():
    data = {"c": ["A"] * 4 + ["B"] * 4, "v": [1, 2, 3, 5, 2, 3, 5, 8]}
    plot = mp.plot(data).violin(
        "c",
        "v",
        width=0.8,
        components={"mean": {"color": "red", "line_width": 1.3}},
    )
    axis = plot.render().axes[0]
    mean = next(
        item
        for item in axis.collections
        if isinstance(item, LineCollection)
        and np.allclose(item.get_colors()[0, :3], [1, 0, 0])
    )
    np.testing.assert_allclose(
        mean.get_segments(),
        [[[-0.2, 2.75], [0.2, 2.75]], [[0.8, 4.5], [1.2, 4.5]]],
    )
    np.testing.assert_array_equal(mean.get_linewidths(), [1.3])
    with pytest.raises(ValueError):
        mp.plot(data).violin(
            "c", "v", showmeans=False, components={"mean": {"color": "red"}}
        ).render()


def test_observed_hue_guides_do_not_repeat_for_other_categories_or_reserved_halves():
    data = {
        "c": ["A"] * 6 + ["B"] * 6,
        "v": [1, 2, 3] * 4,
        "h": ["first"] * 3 + ["second"] * 3 + ["first"] * 3 + ["second"] * 3,
    }
    controls = {
        "split_policy": "paired",
        "hue_components": [
            {
                "level": "first",
                "components": {"body": {"color": "red", "line_width": 1.2}},
            },
            {
                "level": "second",
                "components": {"body": {"color": "blue", "line_width": 2}},
            },
        ],
    }
    plot = mp.plot(data).violin(
        "c",
        "v",
        group="h",
        hue_order=["first", "reserved", "second"],
        split=True,
        inner="quart",
        violin=controls,
        components={"body": {"alpha": 1}},
    )
    axis = plot.render().axes[0]
    assert [text.get_text() for text in axis.get_legend().get_texts()] == [
        "first",
        "second",
    ]
    guides = axis.get_legend().get_patches()
    np.testing.assert_allclose(
        [patch.get_facecolor() for patch in guides], [[1, 0, 0, 1], [0, 0, 1, 1]]
    )
    np.testing.assert_allclose([patch.get_linewidth() for patch in guides], [1.2, 2])
    assert len(bodies(axis)) == 4
    assert (
        sum(
            len(item.get_segments())
            for item in axis.collections
            if isinstance(item, LineCollection)
        )
        == 12
    )
    second = copy.deepcopy(controls)
    second["hue_components"][0]["components"]["body"]["color"] = "green"
    second["hue_components"][1]["components"]["body"]["color"] = "orange"
    plot.violin(
        "c",
        "v",
        group="h",
        hue_order=["first", "reserved", "second"],
        split=True,
        inner="quart",
        violin=second,
        components={"body": {"alpha": 1}},
    )
    both = plot.render().axes[0]
    assert [text.get_text() for text in both.get_legend().get_texts()] == [
        "first",
        "second",
        "first",
        "second",
    ]
    np.testing.assert_allclose(
        [patch.get_facecolor() for patch in both.get_legend().get_patches()],
        [
            [1, 0, 0, 1],
            [0, 0, 1, 1],
            [0, 0.5019607843137255, 0, 1],
            [1, 0.6470588235294118, 0, 1],
        ],
    )
    assert len(bodies(both)) == 8


@pytest.mark.parametrize("scalar", [False, True])
def test_explicit_absent_collection_stroke_keeps_paths_and_component_fill(scalar):
    components = {
        "body": {"color": "red", "line_width": 2},
        "quartile": {"line_width": 2},
    }
    if not scalar:
        for style in components.values():
            style["line_style"] = "none"
    plot = mp.plot({"c": ["A"] * 4, "v": [1, 2, 3, 5]}).violin(
        "c",
        "v",
        inner="quart",
        components=components,
        **({"line_style": "none"} if scalar else {}),
    )
    axis = plot.render().axes[0]
    body = bodies(axis)[0]
    np.testing.assert_array_equal(body.get_linewidths(), [0])
    np.testing.assert_allclose(body.get_facecolor()[0, :3], [1, 0, 0])
    segments = next(
        item for item in axis.collections if isinstance(item, LineCollection)
    )
    np.testing.assert_array_equal(segments.get_linewidths(), [0])
    np.testing.assert_allclose(
        [segment[0, 1] for segment in segments.get_segments()], [1.75, 2.5, 3.5]
    )
    assert plot.spec.panels[0].layers[0].line_style == ("none" if scalar else None)


@pytest.mark.skipif(
    shutil.which(mpl.rcParams["pgf.texsystem"]) is None,
    reason="native PGF export requires the declared TeX engine",
)
def test_native_violin_pgf_retains_real_zero_stroke_glyphs_units_and_references(
    tmp_path,
):
    plot = (
        mp.plot({"c": ["A"] * 4, "v": [1, 2, 3, 5]})
        .violin(
            "c",
            "v",
            inner="point",
            label="Observed rows",
            citation="violin2026",
            href="https://example.org/violin",
            components={
                "body": {"line_width": 0, "line_style": "--", "alpha": 1},
                "point": {
                    "line_width": 0,
                    "line_style": "--",
                    "marker": "D",
                    "marker_size": 6,
                    "marker_edge_width": 0.75,
                },
            },
        )
        .labels(y="Response (μm)")
    )
    before = plot.to_json()
    figure = plot.save(str(tmp_path / "native-violin.pgf"))
    try:
        np.testing.assert_array_equal(figure.axes[0].lines[0].get_ydata(), [1, 2, 3, 5])
        assert figure.axes[0].lines[0].get_marker() == "D"
        assert figure.axes[0].lines[0].get_markersize() == 6
    finally:
        plt.close(figure)
    pgf = (tmp_path / "native-violin.pgf").read_text()
    assert r"\figcite{violin2026}" in pgf
    assert "https://example.org/violin" in pgf
    assert "Response (μm)" in pgf
    assert plot.to_json() == before
