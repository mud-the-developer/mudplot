"""C03 consumer contracts: supplied summaries, median CI, caps and real styles."""

from __future__ import annotations

import copy
import inspect
import statistics
from typing import Any, cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.cbook import boxplot_stats
from matplotlib.colors import to_rgba
from matplotlib.patches import Rectangle


def bodies(ax) -> list[Any]:
    return [patch for patch in ax.patches if len(patch.get_path().vertices)]


def native_bxp(ax, stats, *, orient="v", **kwargs: Any) -> dict[str, list[Any]]:
    if "orientation" in inspect.signature(ax.bxp).parameters:
        kwargs["orientation"] = "horizontal" if orient == "h" else "vertical"
    else:
        kwargs["vert"] = orient != "h"
    return ax.bxp(stats, patch_artist=True, manage_ticks=False, **kwargs)


def supplied_columns(samples, categories, hues=None) -> dict[str, list[Any]]:
    stats = [boxplot_stats(sample, bootstrap=None)[0] for sample in samples]
    result: dict[str, list[Any]] = {
        "category": list(categories),
        "median": [item["med"] for item in stats],
    }
    if hues is not None:
        result["hue"] = list(hues)
    for role in ("q1", "q3", "whislo", "whishi", "mean", "cilo", "cihi", "fliers"):
        result[role] = [
            item[role].tolist() if role == "fliers" else float(item[role])
            for item in stats
        ]
    return result


def bxp(plot, *, category=True, **options: Any):
    args = ("category", "median") if category else ("median",)
    return plot.bxp(
        *args,
        q1="q1",
        q3="q3",
        whislo="whislo",
        whishi="whishi",
        mean="mean",
        cilo="cilo",
        cihi="cihi",
        fliers="fliers",
        **options,
    )


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("category_log", [False, True])
@pytest.mark.parametrize("stat_scale", ["data", "axis"])
@pytest.mark.parametrize("axis", ["y", "y2"])
@pytest.mark.parametrize("log_base", [2, 10])
def test_raw_and_supplied_match_native_dodge_gap_inverse(
    orient, category_log, stat_scale, axis, log_base
):
    category_order = [10, 100, 1000]
    hue_order = ["u", "empty", "v"]
    samples = [
        [1, 2, 3, 4, 5, 30],
        [2, 4, 6, 8, 10, 60],
        [3, 6, 9, 12, 15, 90],
        [4, 8, 12, 16, 20, 120],
    ]
    cats, hues = [10, 100, 10, 100], ["u", "u", "v", "v"]
    raw_data: dict[str, list[Any]] = {"category": [], "value": [], "hue": [], "id": []}
    for index, (sample, category, hue) in enumerate(
        zip(samples, cats, hues, strict=True)
    ):
        raw_data["category"].extend([category] * len(sample))
        raw_data["value"].extend(sample)
        raw_data["hue"].extend([hue] * len(sample))
        raw_data["id"].extend([f"original-{index}-{row}" for row in range(len(sample))])
    options: dict[str, Any] = {
        "group": "hue",
        "native_scale": True,
        "stat_scale": stat_scale,
        "order": category_order,
        "hue_order": hue_order,
        "width": 0.8,
        "dodge": 0.6,
        "gap": 0.25,
        "cap_fraction": 0.7,
        "showmeans": True,
        "notch": True,
        "orient": orient,
        "axis": axis,
    }
    raw = mp.plot(raw_data).box("category", "value", **options)
    working = [
        np.log(sample) / np.log(log_base)
        if stat_scale == "axis"
        else np.asarray(sample)
        for sample in samples
    ]
    summaries = supplied_columns(working, cats, hues)
    if stat_scale == "axis":
        for role in ("median", "q1", "q3", "whislo", "whishi", "mean", "cilo", "cihi"):
            summaries[role] = [float(log_base**value) for value in summaries[role]]
        summaries["fliers"] = [
            [float(log_base**value) for value in values]
            for values in summaries["fliers"]
        ]
    supplied = bxp(mp.plot(summaries), **options)
    category_axis = axis if orient == "h" else "x"
    value_axis = "x" if orient == "h" else axis
    for plot in (raw, supplied):
        if axis == "y2":
            plot.secondary_yaxis("Declared target")
        plot.axis_scale(value_axis, "log", options={"base": log_base, "subs": [1.5]})
        if category_log:
            plot.axis_scale(
                category_axis, "log", options={"base": log_base, "subs": [1.5]}
            )
    axes = [plot.render().axes[1 if axis == "y2" else 0] for plot in (raw, supplied)]
    reference = plt.figure().subplots()
    positions = (
        np.log(category_order) / np.log(log_base)
        if category_log
        else np.asarray(category_order)
    )
    spacing = float(np.min(np.diff(positions)))
    width = 0.8 * spacing / 3 * 0.75
    centers = [
        positions[0] - 0.6 * spacing / 3,
        positions[1] - 0.6 * spacing / 3,
        positions[0] + 0.6 * spacing / 3,
        positions[1] + 0.6 * spacing / 3,
    ]
    stats = [boxplot_stats(values, bootstrap=None)[0] for values in working]
    native_bxp(
        reference,
        stats,
        orient=orient,
        positions=centers,
        widths=width,
        capwidths=width * 0.7,
        showmeans=True,
        shownotches=True,
    )
    cd, vd = (1, 0) if orient == "h" else (0, 1)
    for patch in bodies(reference):
        vertices = np.asarray(patch.get_path().vertices)
        if category_log:
            vertices[:, cd] = log_base ** vertices[:, cd]
        if stat_scale == "axis":
            vertices[:, vd] = log_base ** vertices[:, vd]
    for line in reference.lines:
        xy = np.asarray(line.get_xydata()).copy()
        if category_log:
            xy[:, cd] = log_base ** xy[:, cd]
        if stat_scale == "axis":
            xy[:, vd] = log_base ** xy[:, vd]
        line.set_data(xy[:, 0], xy[:, 1])
    for actual in axes:
        target_value_axis = actual.xaxis if orient == "h" else actual.yaxis
        assert target_value_axis.get_transform().base == log_base
        if category_log:
            target_category_axis = actual.yaxis if orient == "h" else actual.xaxis
            assert target_category_axis.get_transform().base == log_base
        assert len(bodies(actual)) == 4
        for got, expected in zip(bodies(actual), bodies(reference), strict=True):
            np.testing.assert_allclose(
                np.asarray(got.get_path().vertices),
                np.asarray(expected.get_path().vertices),
                rtol=1e-12,
                atol=1e-12,
            )
        for got, expected in zip(actual.lines, reference.lines, strict=True):
            np.testing.assert_allclose(
                np.asarray(got.get_xydata()),
                np.asarray(expected.get_xydata()),
                rtol=1e-12,
                atol=1e-12,
            )
    assert raw.spec.data.columns == raw_data
    assert supplied.spec.data.columns == summaries


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("stat_scale", ["data", "axis"])
def test_seeded_median_notches_match_independent_resampled_medians_and_keep_rng(
    orient, stat_scale
):
    values = [1, 2, 5, 9, 40]
    seed, count, level = 17, 257, 80
    work = np.log10(values) if stat_scale == "axis" else np.asarray(values)
    indices = np.random.default_rng(seed).integers(
        0, len(work), size=(count, len(work))
    )
    independent = [statistics.median(work[row].tolist()) for row in indices]
    low, high = np.quantile(independent, [0.1, 0.9], method="linear")
    stats = boxplot_stats(work, bootstrap=None)[0]
    stats["cilo"], stats["cihi"] = low, high
    plot = mp.plot(
        {
            "category": ["A"] * len(values),
            "value": values,
            "id": ["z", "a", "q", "b", "x"],
        }
    ).box(
        "category",
        "value",
        orient=orient,
        stat_scale=stat_scale,
        median_ci={"level": level, "n_boot": count, "seed": seed},
    )
    if stat_scale == "axis":
        getattr(plot, "xscale" if orient == "h" else "yscale")("log")
    before = np.random.get_state()
    first = plot.render().axes[0]
    second = mp.Plot.from_json(plot.to_json()).render().axes[0]
    after = np.random.get_state()
    assert (
        before[0] == after[0]
        and np.array_equal(before[1], after[1])
        and before[2:] == after[2:]
    )
    reference = plt.figure().subplots()
    parts = native_bxp(
        reference, [stats], orient=orient, positions=[0], widths=0.8, shownotches=True
    )
    expected = parts["boxes"][0].get_path().vertices.copy()
    if stat_scale == "axis":
        expected[:, 0 if orient == "h" else 1] = (
            10 ** expected[:, 0 if orient == "h" else 1]
        )
    np.testing.assert_allclose(
        bodies(first)[0].get_path().vertices, expected, rtol=1e-12, atol=1e-12
    )
    np.testing.assert_array_equal(
        bodies(first)[0].get_path().vertices, bodies(second)[0].get_path().vertices
    )
    assert mp.apply(plot.action_log) == plot.spec
    assert plot.spec.data.columns["id"] == ["z", "a", "q", "b", "x"]


def test_singleton_bootstrap_request_keeps_real_box_without_gaussian_notch():
    plot = mp.plot({"value": [7], "id": ["only"]}).box(
        "value", median_ci={"n_boot": 31, "seed": 3}
    )
    with pytest.warns(UserWarning) as warnings:
        actual = plot.render().axes[0]
    assert len(warnings) == 1
    reference = plt.figure().subplots()
    parts = native_bxp(
        reference, boxplot_stats([7]), positions=[1], widths=0.15, shownotches=False
    )
    np.testing.assert_array_equal(
        bodies(actual)[0].get_path().vertices, parts["boxes"][0].get_path().vertices
    )
    assert plot.spec.data.columns == {"value": [7], "id": ["only"]}


def test_same_cell_bootstrap_schedule_survives_facet_and_category_order():
    data = {
        "category": ["A"] * 5 + ["B"] * 5,
        "value": [1, 2, 3, 8, 30, 3, 4, 5, 12, 50],
        "cohort": ["left"] * 5 + ["right"] * 5,
    }
    plot = mp.plot(data).box(
        "category", "value", median_ci={"n_boot": 257, "seed": 19}, order=["B", "A"]
    )
    original = {
        tuple(p.get_path().vertices[:, 1]): p for p in bodies(plot.render().axes[0])
    }
    plot.facet(col="cohort", col_order=["left", "empty", "right"], live=True)
    native = plot.render()
    selected = [ax for ax in native.axes if bodies(ax)]
    assert len(selected) == 2
    assert {
        tuple(p.get_path().vertices[:, 1]) for ax in selected for p in bodies(ax)
    } == set(original)


@pytest.mark.parametrize("fraction", [0, 0.25, 1])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_cap_length_uses_final_gap_dodge_body_width_and_keeps_measurement_limits(
    fraction, orient
):
    data = {"c": [10] * 6, "v": [1, 2, 3, 4, 5, 30], "h": ["A"] * 3 + ["B"] * 3}
    plot = mp.plot(data).box(
        "c",
        "v",
        group="h",
        width=0.8,
        dodge=0.6,
        gap=0.5,
        cap_fraction=fraction,
        native_scale=True,
        orient=orient,
    )
    native = plot.render().axes[0]
    dimension = int(orient == "h")
    width = 0.8 / 2 * 0.5
    for index in range(2):
        for line in native.lines[index * 6 + 2 : index * 6 + 4]:
            coordinates = np.asarray(line.get_xydata())[:, dimension]
            assert float(np.ptp(coordinates)) == pytest.approx(width * fraction)
    assert len(native.lines) == 12
    assert (
        list(native.dataLim.intervaly) == [1, 30]
        if orient == "v"
        else list(native.dataLim.intervalx) == [1, 30]
    )


def test_optional_missing_marks_never_drop_an_otherwise_valid_supplied_box():
    columns = supplied_columns([[1, 2, 3], [3, 4, 5]], ["A", "B"])
    columns["mean"] = [None, None]
    columns["cilo"] = columns["cihi"] = [None, None]
    columns["fliers"] = [None, []]
    plot = bxp(mp.plot(columns))
    native = plot.render().axes[0]
    assert len(bodies(native)) == 2
    np.testing.assert_allclose(
        [patch.get_path().vertices[:, 1].min() for patch in bodies(native)], [1.5, 3.5]
    )
    assert plot.spec.data.columns == columns
    for request in ({"showmeans": True}, {"notch": True}, {"showfliers": True}):
        invalid = bxp(mp.plot(columns), **request)
        with pytest.raises(ValueError):
            invalid.render()


def test_per_hue_overrides_use_typed_keys_and_merge_only_supplied_properties():
    data = {"c": ["A"] * 6, "v": [1, 2, 8, 3, 4, 10], "h": [True] * 3 + [1] * 3}
    plot = mp.plot(data).box(
        "c",
        "v",
        group="h",
        components={
            "body": {"alpha": 0.8, "line_width": 0.7},
            "cap": {"line_width": 2},
        },
        hue_components=[
            {
                "level": True,
                "components": {"body": {"color": "#228833", "hatch": "//"}},
            },
            {
                "level": 1,
                "components": {
                    "body": {"color": "#aa3377", "line_width": 1.5},
                    "cap": {"color": "#1122aa"},
                },
            },
        ],
    )
    native = mp.Plot.from_json(plot.to_json()).render().axes[0]
    patches = bodies(native)
    np.testing.assert_allclose(
        [patch.get_facecolor() for patch in patches],
        [to_rgba("#228833", 0.8), to_rgba("#aa3377", 0.8)],
    )
    assert [patch.get_linewidth() for patch in patches] == [0.7, 1.5]
    assert patches[0].get_hatch() == "//"
    assert native.lines[2].get_linewidth() == native.lines[8].get_linewidth() == 2
    assert native.lines[8].get_color() == "#1122aa"
    legend = native.get_legend()
    assert legend is not None
    legend_colors = [
        artist.get_facecolor()
        for artist in legend.findobj()
        if type(artist) is Rectangle
    ]
    for expected in [to_rgba("#228833", 0.8), to_rgba("#aa3377", 0.8)]:
        assert any(np.allclose(color, expected) for color in legend_colors)
    assert mp.apply(plot.action_log) == plot.spec


def test_advanced_category_order_does_not_select_numeric_one_for_boolean_true():
    plot = mp.plot({"c": [True, 1, True, 1], "v": [1, 100, 3, 200]}).box(
        "c", "v", order=[True], cap_fraction=0.5
    )
    native = plot.render().axes[0]
    assert len(bodies(native)) == 1
    np.testing.assert_allclose(np.asarray(native.lines[4].get_ydata()), [2, 2])


@pytest.mark.parametrize("role", ["body", "whisker", "cap", "median", "mean", "flier"])
def test_zero_width_dash_keeps_native_component_coordinates_and_independent_markers(
    role,
):
    data = {"c": ["A"] * 6, "v": [1, 2, 3, 4, 5, 30]}
    plot = mp.plot(data).box(
        "c",
        "v",
        showmeans=True,
        cap_fraction=0.5,
        components={role: {"line_width": 0, "line_style": "--"}},
    )
    native = plot.render().axes[0]
    reference = plt.figure().subplots()
    parts = native_bxp(
        reference, boxplot_stats(data["v"]), positions=[0], widths=0.8, showmeans=True
    )
    for actual, expected in zip(native.lines, reference.lines, strict=True):
        np.testing.assert_array_equal(
            np.asarray(actual.get_xydata()), np.asarray(expected.get_xydata())
        )
        assert actual.get_visible()
    assert native.lines[-2].get_marker() == parts["means"][0].get_marker()
    assert native.lines[-1].get_marker() == parts["fliers"][0].get_marker()
    assert len(np.asarray(native.lines[-1].get_xdata())) == 1
    if role == "body":
        assert bodies(native)[0].get_facecolor()[3] > 0
        assert bodies(native)[0].get_linewidth() == 0


def semantic_data():
    return {
        "c": ["A"] * 12 + ["B"] * 12,
        "v": [1, 2, 3, 4, 5, 30, 3, 4, 5, 6, 7, 50] * 2,
        "h": ([-10] * 6 + [10] * 6) * 2,
        "m": ([1] * 6 + [3] * 6) * 2,
        "s": (["left"] * 6 + ["right"] * 6) * 2,
    }


def semantic_config():
    return mp.SemanticSpec(
        scale_id="box-study",
        hue="h",
        hue_kind="numeric",
        hue_norm=[-20, 20],
        size="m",
        size_norm=[1, 3],
        sizes=[0.5, 2],
        style="s",
        dashes=["--", ":"],
    )


@pytest.mark.parametrize("low_stroke", [0, 0.5])
def test_box_roles_own_body_properties_and_actual_flier_glyphs_not_other_components(
    low_stroke,
):
    config = semantic_config()
    config.sizes = [low_stroke, 2]
    plot = mp.plot(semantic_data()).box(
        "c",
        "v",
        semantics=config,
        components={
            "whisker": {"line_width": 3, "line_style": "-."},
            "cap": {"line_width": 4, "color": "#aa3311"},
            "median": {"line_width": 5},
            "flier": {"marker_size": 7, "edge_color": "#112233"},
        },
        colorbar=True,
    )
    figure = plot.render()
    native = figure.axes[0]
    assert [patch.get_linewidth() for patch in bodies(native)] == [
        low_stroke,
        low_stroke,
        2,
        2,
    ]
    for patch, dash in zip(bodies(native), ["--", "--", ":", ":"], strict=True):
        if patch.get_linewidth():
            assert patch.get_linestyle() == dash
        else:
            assert patch.get_facecolor()[3] > 0 and patch.get_visible()
    for start in range(0, len(native.lines), 6):
        assert native.lines[start].get_linewidth() == 3
        assert native.lines[start].get_linestyle() == "-."
        assert native.lines[start + 2].get_linewidth() == 4
        assert native.lines[start + 4].get_linewidth() == 5
        assert native.lines[start + 5].get_markersize() == 7
        assert len(np.asarray(native.lines[start + 5].get_xdata())) == 1
    assert [native.lines[index].get_marker() for index in (5, 11, 17, 23)] == [
        semantic_config().markers[0]
    ] * 2 + [semantic_config().markers[1]] * 2
    assert len(figure.axes) == 2


def test_typed_dict_and_reopened_default_marker_cycles_encode_identical_real_fliers():
    config = mp.SemanticSpec(scale_id="box-style", style="s", dashes=["--", ":"])
    plots = [
        mp.plot(semantic_data()).box("c", "v", semantics=value)
        for value in (config, config.to_dict())
    ]
    plots.append(mp.Plot.from_json(plots[0].to_json()))
    actual = []
    for plot in plots:
        native = plot.render().axes[0]
        actual.append(
            [
                (
                    line.get_marker(),
                    line.get_markersize(),
                    np.asarray(line.get_xydata()).tolist(),
                )
                for line in native.lines
                if line.get_marker() not in ("", "None", "none")
            ]
        )
    assert actual[0] == actual[1] == actual[2]
    assert {marker for marker, _, _ in actual[0]} == set(config.markers[:2])


@pytest.mark.parametrize("component", ["body", "flier"])
def test_actual_mapped_component_overrides_reject_atomically(component):
    from dashboard.editor_server import EditorSession

    plot = mp.plot(semantic_data()).box("c", "v", semantics=semantic_config())
    session = EditorSession()
    session.load_spec(plot.to_json())
    accepted, png, history = (
        session.store.state.to_dict(),
        session.png,
        session.store.history,
    )
    layer = copy.deepcopy(plot.spec.panels[0].layers[0])
    layer.components = (
        mp.DistributionComponentsSpec(body=mp.ComponentStyleSpec(line_width=2))
        if component == "body"
        else mp.DistributionComponentsSpec(flier=mp.ComponentStyleSpec(marker="s"))
    )
    session.dispatch_safe(mp.actions.AddLayer(layer))
    assert session.error is not None
    assert session.store.state.to_dict() == accepted and session.png == png
    assert session.store.history == history


def test_one_column_group_is_category_and_semantic_hue_is_independent():
    data = {
        "v": [1, 2, 3, 4, 5, 6],
        "category": ["A"] * 3 + ["B"] * 3,
        "hue": ["u", "u", "v"] * 2,
    }
    plot = mp.plot(data).box("v", group="category", semantics={"hue": "hue"})
    native = plot.render().axes[0]
    assert len(bodies(native)) == 4
    assert [tick.get_text() for tick in native.get_xticklabels()] == ["A", "B"]
    assert {
        tuple(np.asarray(line.get_ydata()))
        for line in native.lines
        if line.get_marker() == "" and len(np.asarray(line.get_ydata())) == 2
    } >= {(1.5, 1.5), (4.5, 4.5), (3, 3), (6, 6)}
    invalid = mp.plot(data).box(
        "v",
        group="category",
        hue_components=[{"level": "A", "components": {"cap": {"color": "red"}}}],
    )
    with pytest.raises(ValueError):
        invalid.render()


def test_advanced_box_work_bounds_allow_exactly_256_native_cells_and_reject_next():
    count = 256
    columns = {
        "category": list(range(count)),
        "median": [2] * count,
        "q1": [1] * count,
        "q3": [3] * count,
        "whislo": [0] * count,
        "whishi": [4] * count,
        "mean": [2.1] * count,
        "cilo": [1.5] * count,
        "cihi": [2.5] * count,
        "fliers": [[5]] * count,
    }
    plot = bxp(mp.plot(columns), showmeans=True, notch=True)
    native = plot.render().axes[0]
    assert len(bodies(native)) == 256
    assert (
        sum(
            len(np.asarray(line.get_xdata()))
            for line in native.lines
            if line.get_marker() not in ("", "None", "none")
        )
        == 512
    )
    overflow = {
        key: [*values, 257 if key == "category" else values[-1]]
        for key, values in columns.items()
    }
    with pytest.raises(ValueError):
        bxp(mp.plot(overflow)).render()


def test_source_row_and_total_declared_flier_budgets_are_separate_native_boundaries():
    raw = mp.plot({"v": [2] * 10_000}).box("v", cap_fraction=0.5)
    assert len(bodies(raw.render().axes[0])) == 1
    columns = supplied_columns([[1, 2, 3]], ["A"])
    columns["fliers"] = [[4] * 10_000]
    supplied = bxp(mp.plot(columns))
    native = supplied.render().axes[0]
    assert len(np.asarray(native.lines[-1].get_xdata())) == 10_000
    columns["fliers"][0].append(4)
    with pytest.raises(ValueError):
        bxp(mp.plot(columns)).render()
    with pytest.raises(ValueError):
        mp.plot({"v": [2] * 10_001}).box("v", cap_fraction=0.5).render()


def test_supplied_summary_edit_history_reopen_keeps_scientific_geometry(tmp_path):
    plot = bxp(mp.plot(supplied_columns([[1, 2, 3, 30]], ["A"])), cap_fraction=0.25)
    before = plot.to_json()
    replacement = copy.deepcopy(plot.spec.panels[0].layers[0])
    cast(mp.BoxSpec, replacement.box).cap_fraction = 1
    plot.dispatch(mp.actions.RemoveLayer(0))
    plot.dispatch(mp.actions.AddLayer(replacement))
    edited = plot.to_json()
    plot.store.undo()
    plot.store.undo()
    assert plot.to_json() == before
    plot.store.redo()
    plot.store.redo()
    assert plot.to_json() == edited
    target = tmp_path / "summary.mplot.json"
    mp.save_spec(plot.spec, target)
    reopened = mp.Plot.from_json(target.read_text())
    native = reopened.render().axes[0]
    assert np.ptp(np.asarray(native.lines[2].get_xdata())) == pytest.approx(0.8)
    assert reopened.spec == mp.apply(plot.action_log) == plot.spec


@pytest.mark.parametrize("showbox", [False, True])
def test_raw_cap_request_preserves_explicit_native_rc_statistics_and_other_marks(
    showbox,
):
    rc: dict[Any, Any] = {
        "boxplot.whiskers": 2,
        "boxplot.notch": True,
        "boxplot.showmeans": True,
        "boxplot.showfliers": False,
        "boxplot.showbox": showbox,
        "boxplot.showcaps": False,
    }
    values = [1, 2, 3, 4, 5, 9]
    with matplotlib.rc_context(rc):
        plot = mp.plot({"c": ["A"] * 6, "v": values}).box("c", "v", cap_fraction=0.3)
        actual = plot.render().axes[0]
        reference = plt.figure().subplots()
        reference.boxplot(
            values,
            positions=[0],
            widths=0.8,
            capwidths=0.8 * 0.3,
            patch_artist=True,
            showcaps=True,
        )
        assert len(bodies(actual)) == len(bodies(reference)) == int(showbox)
        for got, expected in zip(bodies(actual), bodies(reference), strict=True):
            np.testing.assert_array_equal(
                got.get_path().vertices, expected.get_path().vertices
            )
        for got, expected in zip(actual.lines, reference.lines, strict=True):
            np.testing.assert_array_equal(
                np.asarray(got.get_xydata()), np.asarray(expected.get_xydata())
            )
            assert got.get_marker() == expected.get_marker()
        assert len(np.asarray(actual.lines[-1].get_xdata())) == 1
        assert np.asarray(actual.lines[-1].get_ydata())[0] == statistics.mean(values)
        assert np.asarray(actual.lines[1].get_ydata())[-1] == 9
        assert np.ptp(np.asarray(actual.lines[2].get_xdata())) == pytest.approx(
            0.8 * 0.3
        )


def test_native_hidden_box_retains_whiskers_median_and_requested_mean():
    with matplotlib.rc_context(
        {
            "boxplot.showbox": False,
            "boxplot.showcaps": False,
            "boxplot.showmeans": True,
            "boxplot.showfliers": False,
        }
    ):
        actual = (
            mp.plot({"c": ["A"] * 3, "v": [1, 3, 8]}).box("c", "v").render().axes[0]
        )
        assert not bodies(actual)
        assert len(actual.lines) == 4
        np.testing.assert_allclose(np.asarray(actual.lines[0].get_ydata()), [2, 1])
        np.testing.assert_allclose(np.asarray(actual.lines[1].get_ydata()), [5.5, 8])
        np.testing.assert_allclose(np.asarray(actual.lines[2].get_ydata()), [3, 3])
        assert np.asarray(actual.lines[3].get_ydata())[0] == 4


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("target_axis", ["y", "y2"])
@pytest.mark.parametrize("calendar_roles", ["category", "measurement", "both"])
def test_supplied_absolute_calendar_roles_and_target_axes_match_native_days(
    orient, target_axis, calendar_roles
):
    import datetime as dt

    import matplotlib.dates as mdates

    temporal_category = calendar_roles in ("category", "both")
    temporal_value = calendar_roles in ("measurement", "both")
    dates = ["2026-01-01", "2026-07-01"]
    columns: dict[str, list[Any]] = {
        "category": dates if temporal_category else [10, 100],
        "median": ["2026-02-03", "2026-08-03"] if temporal_value else [2, 4],
        "q1": ["2026-02-02", "2026-08-02"] if temporal_value else [1, 3],
        "q3": ["2026-02-04", "2026-08-04"] if temporal_value else [3, 5],
        "whislo": ["2026-02-01", "2026-08-01"] if temporal_value else [0.5, 2],
        "whishi": ["2026-02-05", "2026-08-05"] if temporal_value else [4, 6],
        "fliers": [["2026-02-08"], ["2026-08-08"]] if temporal_value else [[5], [7]],
        "id": ["original-late-order-z", "original-a"],
    }
    plot = mp.plot(columns)
    if target_axis == "y2":
        plot.secondary_yaxis("Category" if orient == "h" else "Measured value")
    category_axis = target_axis if orient == "h" else "x"
    value_axis = "x" if orient == "h" else target_axis
    if temporal_category:
        plot.date_axis(category_axis, timezone="UTC")
    if temporal_value:
        plot.date_axis(value_axis, timezone="UTC")
    plot.bxp(
        "category",
        "median",
        q1="q1",
        q3="q3",
        whislo="whislo",
        whishi="whishi",
        fliers="fliers",
        axis=target_axis,
        orient=orient,
        native_scale=True,
        cap_fraction=0.25,
        showfliers=True,
    )
    fig = mp.Plot.from_json(plot.to_json()).render()
    actual = fig.axes[1] if target_axis == "y2" else fig.axes[0]

    def days(value):
        return float(
            mdates.date2num(dt.datetime.fromisoformat(value).replace(tzinfo=dt.UTC))
        )

    positions = np.asarray(
        [days(value) for value in dates] if temporal_category else [10, 100]
    )
    expected = []
    for row in range(2):
        summary = {"med": columns["median"][row]}
        summary.update(
            {
                role: columns[role][row]
                for role in ("q1", "q3", "whislo", "whishi", "fliers")
            }
        )
        if temporal_value:
            summary = {
                role: [days(v) for v in value] if role == "fliers" else days(value)
                for role, value in summary.items()
            }
        expected.append(summary)
    reference = plt.figure().subplots()
    width = 0.8 * float(np.diff(positions)[0])
    native_bxp(
        reference,
        expected,
        orient=orient,
        positions=positions,
        widths=width,
        capwidths=width * 0.25,
    )
    for got, want in zip(bodies(actual), bodies(reference), strict=True):
        np.testing.assert_allclose(
            got.get_path().vertices, want.get_path().vertices, rtol=0, atol=1e-10
        )
    for got, want in zip(actual.lines, reference.lines, strict=True):
        np.testing.assert_allclose(
            np.asarray(got.get_xydata()),
            np.asarray(want.get_xydata()),
            rtol=0,
            atol=1e-10,
        )
    assert plot.spec.data.columns == columns
    assert mp.apply(plot.action_log) == plot.spec


@pytest.mark.parametrize("orient", ["v", "h"])
def test_numeric_clock_units_origin_inversion_and_summary_fliers_are_absolute(orient):
    import datetime as dt

    import matplotlib.dates as mdates

    columns = {
        "category": [0, 181],
        "median": [2, 183],
        "q1": [1, 182],
        "q3": [3, 184],
        "whislo": [0, 181],
        "whishi": [4, 185],
        "fliers": [[6], [187]],
    }
    plot = mp.plot(columns).secondary_yaxis("Original calendar values")
    category_axis, value_axis = ("y2", "x") if orient == "h" else ("x", "y2")
    for axis in (category_axis, value_axis):
        plot.date_axis(axis, unit="day", origin="2026-01-01", timezone="UTC")
    plot.bxp(
        "category",
        "median",
        q1="q1",
        q3="q3",
        whislo="whislo",
        whishi="whishi",
        fliers="fliers",
        orient=orient,
        axis="y2",
        cap_fraction=0.5,
    )
    plot.dispatch(mp.actions.SetLimits(category_axis, 220, -40))
    actual = plot.render().axes[1]
    origin = float(mdates.date2num(dt.datetime(2026, 1, 1, tzinfo=dt.UTC)))
    assert actual.yaxis_inverted() if orient == "h" else actual.xaxis_inverted()
    dimension = 0 if orient == "h" else 1
    np.testing.assert_allclose(
        np.asarray(actual.lines[5].get_xydata())[:, dimension],
        [origin + 6],
        rtol=0,
        atol=1e-10,
    )
    np.testing.assert_allclose(
        np.asarray(actual.lines[11].get_xydata())[:, dimension],
        [origin + 187],
        rtol=0,
        atol=1e-10,
    )
    assert plot.spec.data.columns == columns


def test_box_and_point_families_share_original_domains_not_duplicate_source_counts():
    count = 6000
    data = {
        "c": [10] * count,
        "v": np.linspace(1, 6, count).tolist(),
        "x": [10] * count,  # Same declared numeric-native category coordinate.
        "h": [42] * count,
        "m": [2] * count,
        "id": [f"source-{index}" for index in range(count)],
    }
    config = mp.SemanticSpec(
        scale_id="same-source", hue="h", hue_kind="numeric", size="m", sizes=[0.5, 2]
    )
    plot = mp.plot(data).secondary_yaxis("Second statistical view")
    plot.box("c", "v", semantics=config, native_scale=True)
    plot.scatter("x", "v", semantics=config)
    plot.box(
        "c",
        "v",
        semantics=config,
        native_scale=True,
        axis="y2",
        colorbar=True,
        clabel="Raw calibration",
    )
    native = plot.render()
    assert len(native.axes) == 3
    assert len(bodies(native.axes[0])) == len(bodies(native.axes[1])) == 1
    collection = cast(Any, native.axes[0].collections[0])
    assert len(np.asarray(collection.get_offsets())) == count
    assert (
        bodies(native.axes[0])[0].get_linewidth()
        == bodies(native.axes[1])[0].get_linewidth()
        == 1.25
    )
    np.testing.assert_allclose(collection.get_sizes(), 1.25**2)
    assert native.axes[2].get_ylim() == (0, 1)
    assert [float(tick.get_text()) for tick in native.axes[2].get_yticklabels()] == [42]
    assert native.axes[0].get_position().bounds == native.axes[1].get_position().bounds
    assert plot.spec.data.columns == data


def test_live_per_hue_components_reserve_known_levels_before_empty_cell_validation():
    data = {
        "c": ["A"] * 6,
        "v": [1, 2, 3, 4, 5, 6],
        "h": ["u"] * 3 + ["v"] * 3,
        "cell": ["left"] * 3 + ["right"] * 3,
        "id": ["z", "a", "q", "b", "y", "x"],
    }
    plot = (
        mp.plot(data)
        .box(
            "c",
            "v",
            semantics={"hue": "h"},
            hue_components=[
                {"level": "u", "components": {"cap": {"color": "red"}}},
                {"level": "v", "components": {"cap": {"color": "blue"}}},
            ],
        )
        .facet(col="cell", col_order=["left", "empty", "right"], live=True)
    )
    before = plot.to_json()
    template = copy.deepcopy(
        cast(mp.FacetTemplateSpec, plot.spec.facet_template).template
    )
    cast(mp.BoxSpec, template.layers[0].box).cap_fraction = 1
    plot.facet_template(template)
    edited = plot.to_json()
    native = mp.Plot.from_json(edited).render()
    assert [len(bodies(ax)) for ax in native.axes] == [1, 0, 1]
    assert native.axes[0].lines[2].get_color() == "red"
    assert native.axes[2].lines[2].get_color() == "blue"
    assert np.ptp(np.asarray(native.axes[0].lines[2].get_xdata())) == pytest.approx(0.4)
    plot.store.undo()
    assert plot.to_json() == before
    plot.store.redo()
    assert plot.to_json() == edited
    assert plot.spec.data.columns == data


def test_one_column_live_category_identity_is_not_the_measurement_column():
    data = {
        "v": [1, 2, 3, 4, 5, 6],
        "other_value": [2, 4, 6, 8, 10, 12],
        "first": ["A"] * 3 + ["B"] * 3,
        "second": ["X"] * 3 + ["Y"] * 3,
        "cell": ["left"] * 3 + ["right"] * 3,
        "id": ["z", "a", "q", "b", "y", "x"],
    }
    plot = (
        mp.plot(data)
        .box("v", group="first", order=["B", "reserved", "A"], cap_fraction=0.5)
        .facet(col="cell", col_order=["left", "empty", "right"], live=True)
    )
    reopened = mp.Plot.from_json(plot.to_json())
    previous = reopened.to_json()
    literal = mp.Plot.from_json(previous)
    literal_template = copy.deepcopy(
        cast(mp.FacetTemplateSpec, literal.spec.facet_template).template
    )
    literal_template.layers[0].group = "second"
    literal.facet_template(literal_template)
    literal_native = literal.render()
    assert [len(bodies(ax)) for ax in literal_native.axes] == [0, 0, 0]
    assert [tick.get_text() for tick in literal_native.axes[0].get_xticklabels()] == [
        "B",
        "reserved",
        "A",
    ]
    assert literal.spec.data.columns == data
    template = copy.deepcopy(
        cast(mp.FacetTemplateSpec, reopened.spec.facet_template).template
    )
    template.layers[0].group = "second"
    template.layers[0].order = None  # Explicit request to infer, not literal A/B.
    reopened.facet_template(template)
    changed = reopened.to_json()
    native = reopened.render()
    assert [len(bodies(ax)) for ax in native.axes] == [1, 0, 1]
    assert [tick.get_text() for tick in native.axes[0].get_xticklabels()] == ["X", "Y"]
    np.testing.assert_allclose(np.asarray(native.axes[0].lines[4].get_ydata()), [2, 2])
    np.testing.assert_allclose(np.asarray(native.axes[2].lines[4].get_ydata()), [5, 5])
    reopened.store.undo()
    assert reopened.to_json() == previous
    reopened.store.redo()
    assert reopened.to_json() == changed
    template = copy.deepcopy(
        cast(mp.FacetTemplateSpec, reopened.spec.facet_template).template
    )
    template.layers[0].x = "other_value"
    template.layers[0].order = None
    reopened.facet_template(template)
    native = reopened.render()
    assert [tick.get_text() for tick in native.axes[0].get_xticklabels()] == ["X", "Y"]
    np.testing.assert_allclose(np.asarray(native.axes[0].lines[4].get_ydata()), [4, 4])
    assert reopened.spec.data.columns == data


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("axis", ["y", "y2"])
def test_raw_date_median_bootstrap_uses_observation_clock_and_independent_day_oracle(
    orient, axis
):
    import datetime as dt

    import matplotlib.dates as mdates

    values = [f"2026-02-{day:02d}" for day in (1, 2, 3, 5, 9, 28)]
    days = np.asarray(
        [
            mdates.date2num(dt.datetime.fromisoformat(value).replace(tzinfo=dt.UTC))
            for value in values
        ]
    )
    samples = np.random.default_rng(17).integers(
        0, len(values), size=(257, len(values))
    )
    low, high = np.quantile(
        np.median(days[samples], axis=1), [0.1, 0.9], method="linear"
    )
    stats = boxplot_stats(days, bootstrap=None)[0]
    stats["cilo"], stats["cihi"] = low, high
    data = {"c": [10] * len(values), "v": values, "id": ["f", "e", "d", "c", "b", "a"]}
    plot = mp.plot(data)
    if axis == "y2":
        plot.secondary_yaxis("Original date")
    plot.date_axis("x" if orient == "h" else axis, timezone="UTC")
    plot.box(
        "c",
        "v",
        axis=axis,
        orient=orient,
        native_scale=True,
        median_ci={"level": 80, "n_boot": 257, "seed": 17},
        cap_fraction=0.5,
    )
    native = plot.render().axes[1 if axis == "y2" else 0]
    reference = plt.figure().subplots()
    native_bxp(
        reference, [stats], orient=orient, positions=[10], widths=0.8, shownotches=True
    )
    np.testing.assert_allclose(
        bodies(native)[0].get_path().vertices,
        bodies(reference)[0].get_path().vertices,
        rtol=0,
        atol=1e-10,
    )
    for got, expected in zip(native.lines, reference.lines, strict=True):
        np.testing.assert_allclose(
            np.asarray(got.get_xydata()),
            np.asarray(expected.get_xydata()),
            rtol=0,
            atol=1e-10,
        )
    assert plot.spec.data.columns == data


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("fraction", [0, 1])
def test_cap_geometry_preserves_unrelated_measurement_autolimits(orient, fraction):
    rx, ry = ([100] * 6, [8] * 6) if orient == "h" else ([8] * 6, [100] * 6)
    data = {"c": [10] * 6, "v": [1, 2, 3, 4, 5, 30], "rx": rx, "ry": ry}
    plot = mp.plot(data).line("rx", "ry")
    plot.box("c", "v", native_scale=True, orient=orient, cap_fraction=fraction)
    native = plot.render().axes[0]
    reference = plt.figure().subplots()
    reference.plot(rx, ry)
    native_bxp(
        reference,
        boxplot_stats(data["v"]),
        orient=orient,
        positions=[10],
        widths=0.8,
        capwidths=0.8 * fraction,
    )
    dimension = 0 if orient == "h" else 1
    np.testing.assert_array_equal(
        native.dataLim.get_points()[:, dimension],
        reference.dataLim.get_points()[:, dimension],
    )
    limits = native.get_xlim() if orient == "h" else native.get_ylim()
    expected_limits = reference.get_xlim() if orient == "h" else reference.get_ylim()
    np.testing.assert_allclose(limits, expected_limits, rtol=0, atol=1e-12)


@pytest.mark.parametrize(
    "changes",
    [
        {"q1": [4]},
        {"q3": [0]},
        {"whislo": [2]},
        {"whishi": [2]},
        {"cilo": [3], "cihi": [1]},
        {"cilo": [None], "cihi": [2]},
        {"fliers": [[1]]},
        {"fliers": [[float("inf")]]},
    ],
)
def test_supplied_scientific_inconsistencies_reject_without_reinterpreting_source(
    changes,
):
    columns = supplied_columns([[1, 2, 3]], ["A"])
    columns.update(changes)
    with pytest.raises(ValueError):
        bxp(mp.plot(columns)).render()


@pytest.mark.parametrize(
    "options",
    [
        {"cap_fraction": True},
        {"cap_fraction": -1},
        {"cap_fraction": 1.01},
        {"median_ci": {"n_boot": True}},
        {"median_ci": {"n_boot": 100001}},
        {"median_ci": {"seed": True}},
        {"median_ci": {"seed": -1}},
        {"median_ci": {"level": 0}},
        {"median_ci": {"level": 100}},
        {"median_ci": {"seed": 1}, "notch": False},
        {
            "hue_components": [
                {"level": "unknown", "components": {"cap": {"color": "red"}}}
            ]
        },
        {
            "hue_components": [
                {"level": "u", "components": {}},
                {"level": "u", "components": {}},
            ]
        },
    ],
)
def test_new_box_options_reject_invalid_requests_through_public_boundary(options):
    with pytest.raises((TypeError, ValueError)):
        mp.plot({"c": ["A"] * 3, "v": [1, 2, 3], "h": ["u"] * 3}).box(
            "c", "v", group="h", **options
        ).render()


def test_box_pgf_legend_retains_citation_hyperlink_and_declared_units(tmp_path):
    import shutil

    if shutil.which(matplotlib.rcParams["pgf.texsystem"]) is None:
        pytest.skip("native PGF export requires the declared TeX engine")
    plot = (
        mp.plot({"c": ["A"] * 6, "v": [1, 2, 3, 4, 5, 30]})
        .box(
            "c",
            "v",
            median_ci={"n_boot": 31, "seed": 7},
            cap_fraction=0.8,
            label="Observed median",
            citation="box2026",
            href="https://example.org/box",
        )
        .labels(y="Response (μm)")
    )
    target = tmp_path / "box.pgf"
    figure = plot.save(str(target))
    plt.close(figure)
    native = target.read_text()
    assert r"\figcite{box2026}" in native
    assert r"\href{https://example.org/box}" in native
    assert "Response (μm)" in native
