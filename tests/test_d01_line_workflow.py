"""D01 consumer equations, topology, typed ownership and atomic transitions."""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from fractions import Fraction

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import LineCollection


def _type7_observed(values, probability):
    ordered = sorted(Fraction(value) for value in values)
    position = (len(ordered) - 1) * Fraction(probability)
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


@pytest.mark.parametrize(
    "declaration",
    [
        {"resampling": "cell"},
        {"calibration": "percentile"},
        {"resampling": "cell", "calibration": "percentile"},
    ],
)
def test_explicit_cell_units_have_typed_identity_through_actions_json_and_native_ci(
    declaration,
):
    data = {
        "id": ["r0", "r1", "r2", "r3", "r4", "r5"],
        "x": [2] * 6,
        "y": [0, 10, 20, 30, 40, 50],
        "w": [1, 2, 3, 4, 5, 6],
        "u": [True, 1, 1.0, False, 0, ""],
    }
    # Independent declared clusters: bools differ from numbers; numeric1/1.0
    # are the same unit, and an opaque empty string is a valid fifth unit.
    units = [[0], [1, 2], [3], [4], [5]]
    rng = np.random.Generator(np.random.PCG64(11))
    boot, sampled_cases = [], 0
    for _ in range(31):
        chosen = rng.integers(0, len(units), size=len(units))
        selected = []
        for unit in chosen:
            rows = units[int(unit)]
            if len(rows) == 1:
                selected.extend(rows)  # Singleton ranges consume no entropy.
            else:
                selected.extend(
                    rows[int(index)]
                    for index in rng.integers(0, len(rows), size=len(rows))
                )
        sampled_cases += len(selected)
        numerator = sum(
            (Fraction(data["y"][i]) * data["w"][i] for i in selected), Fraction()
        )
        denominator = sum((Fraction(data["w"][i]) for i in selected), Fraction())
        boot.append(float(numerator / denominator))
    tail = (1.0 - 95.5 / 100.0) / 2.0
    expected = [
        float(_type7_observed(boot, probability)) for probability in (tail, 1.0 - tail)
    ]
    p = mp.plot(data).lineplot(
        "x",
        "y",
        weights="w",
        units="u",
        n_boot=31,
        seed=11,
        errorbar=("ci", 95.5),
        error_style="bars",
        line=declaration,
    )
    before = p.to_json()
    reopened = mp.Plot.from_json(before)
    assert reopened.spec.data.columns == data
    assert [type(value) for value in reopened.spec.data.columns["u"]] == [
        bool,
        int,
        float,
        bool,
        int,
        str,
    ]
    assert mp.apply(p.action_log) == reopened.spec
    replacement = mp.actions.action_from_dict(
        {
            "type": "ReplaceLayer",
            "layer_index": 0,
            "layer": reopened.spec.panels[0].layers[0].to_dict(),
        }
    )
    reopened.dispatch(replacement)
    fig = reopened.render()
    try:
        segments = next(
            c for c in fig.axes[0].collections if isinstance(c, LineCollection)
        ).get_segments()
        np.testing.assert_array_equal(np.asarray(segments)[0, :, 1], expected)
        work = fig._mudplot_line_inference_work
        assert work["whole_unit"] == 0
        assert work["cell_unit_case"] == 31 * len(units) + sampled_cases
        assert work["cell_reductions"] == 31
        assert reopened.spec.data.columns == data
        assert json.loads(reopened.to_json())["data"] == json.loads(before)["data"]
    finally:
        plt.close(fig)


def _statistic(data, rows, method, weighted):
    values = [
        (
            Fraction(data["y"][row]),
            Fraction(data["w"][row]) if weighted else Fraction(1),
        )
        for row in rows
    ]
    if method == "mean":
        return sum((value * mass for value, mass in values), Fraction()) / sum(
            (mass for value, mass in values), Fraction()
        )
    if method == "sum":
        return sum((value * mass for value, mass in values), Fraction())
    if method in {"min", "max"}:
        return (min if method == "min" else max)(value for value, mass in values)
    ordered = sorted(values)
    if not weighted:
        length = len(ordered)
        return (ordered[(length - 1) // 2][0] + ordered[length // 2][0]) / 2
    target = sum((mass for value, mass in values), Fraction()) / 2
    cumulative = Fraction()
    for value, mass in ordered:
        cumulative += mass
        if cumulative >= target:
            return value
    raise AssertionError("positive reference mass was not conserved")


@pytest.mark.parametrize("method", ["mean", "median", "sum", "min", "max"])
@pytest.mark.parametrize("weighted", [False, True])
@pytest.mark.parametrize(
    "calibration,family",
    [("percentile", None), ("max_deviation", "curve"), ("max_deviation", "layer")],
)
def test_complete_original_units_match_independent_paired_equations(
    method, weighted, calibration, family
):
    data = {name: [] for name in ("id", "x", "y", "w", "u", "g")}
    for unit in range(3):
        for group in ("A", "B"):
            for predictor in (0, 2):
                value = (
                    (unit + 1) * (predictor + 1)
                    if group == "A"
                    else (4 - unit) * (predictor + 2)
                )
                for name, item in zip(
                    data,
                    (f"r{len(data['id'])}", predictor, value, unit + 1, unit, group),
                    strict=True,
                ):
                    data[name].append(item)
    for name, value in zip(
        data, ("duplicate-physical-row", 0, 7, 5, 0, "A"), strict=True
    ):
        data[name].append(value)
    targets = [(group, predictor) for group in ("A", "B") for predictor in (0, 2)]
    original = {
        (group, x): [
            i
            for i in range(len(data["id"]))
            if data["g"][i] == group and data["x"][i] == x
        ]
        for group, x in targets
    }
    centers = {
        target: _statistic(data, rows, method, weighted)
        for target, rows in original.items()
    }
    units = [
        [i for i, value in enumerate(data["u"]) if value == unit] for unit in range(3)
    ]
    rng = np.random.Generator(np.random.PCG64(19))
    bootstrap = []
    for _ in range(31):
        chosen = rng.integers(0, len(units), size=len(units), dtype=np.int64)
        rows = [row for unit in chosen for row in units[int(unit)]]
        bootstrap.append(
            {
                target: _statistic(
                    data,
                    [row for row in rows if (data["g"][row], data["x"][row]) == target],
                    method,
                    weighted,
                )
                for target in targets
            }
        )
    expected = {}
    if calibration == "percentile":
        probabilities = ((1 - Fraction(95.5) / 100) / 2, (1 + Fraction(95.5) / 100) / 2)
        for target in targets:
            expected[target] = tuple(
                float(
                    _type7_observed([value[target] for value in bootstrap], probability)
                )
                for probability in probabilities
            )
    else:
        for target in targets:
            selected = (
                targets
                if family == "layer"
                else [key for key in targets if key[0] == target[0]]
            )
            maxima = sorted(
                max(abs(value[key] - centers[key]) for key in selected)
                for value in bootstrap
            )
            q = maxima[math.ceil(Fraction(95.5) * len(maxima) / 100) - 1]
            expected[target] = (float(centers[target] - q), float(centers[target] + q))
    declaration = {"resampling": "unit", "calibration": calibration}
    if family is not None:
        declaration["family"] = family
    p = mp.plot(data).lineplot(
        "x",
        "y",
        group="g",
        weights="w" if weighted else None,
        units="u",
        estimator=method,
        errorbar=("ci", 95.5),
        error_style="bars",
        n_boot=31,
        seed=19,
        line=declaration,
    )
    before = p.to_json()
    if method in {"min", "max"}:
        with pytest.warns(UserWarning):
            fig = p.render()
    else:
        fig = p.render()
    try:
        ax = fig.axes[0]
        for group in ("A", "B"):
            points = np.asarray(
                next(
                    line for line in ax.lines if line.get_label() == group
                ).get_xydata()
            )
            np.testing.assert_array_equal(
                points[:, 1], [float(centers[(group, x)]) for x in (0, 2)]
            )
        segments = np.concatenate(
            [
                np.asarray(c.get_segments())
                for c in ax.collections
                if isinstance(c, LineCollection)
            ]
        )
        np.testing.assert_array_equal(
            segments[:, :, 1], [expected[target] for target in targets]
        )
        assert fig._mudplot_line_inference_work["whole_unit"] == 31 * (3 + 13 + 4)
        assert p.to_json() == before
        assert mp.Plot.from_json(before).spec.data.columns == data
    finally:
        plt.close(fig)


def test_native_missing_grid_is_per_curve_not_unrelated_union():
    data = {
        "x": [0, 1, 4, 2, 6],
        "y": [2, None, 6, 3, 9],
        "g": ["A", "A", "A", "B", "B"],
    }
    p = mp.plot(data).lineplot("x", "y", group="g", errorbar=None)
    fig = p.render()
    try:
        a = next(line for line in fig.axes[0].lines if line.get_label() == "A")
        b = next(line for line in fig.axes[0].lines if line.get_label() == "B")
        np.testing.assert_array_equal(a.get_xdata(), [0, 1, 4])
        assert np.isnan(a.get_ydata()[1])
        np.testing.assert_array_equal(b.get_xydata(), [[2, 3], [6, 9]])
        assert p.spec.data.columns == data
    finally:
        plt.close(fig)


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("axis", ["y", "y2"])
@pytest.mark.parametrize("predictor", ["numeric", "date", "categorical"])
def test_complete_unit_predictors_use_actual_axes_and_reserved_slots(
    predictor, axis, orient
):
    x = [1, 2, 9]
    declaration = {"resampling": "unit", "calibration": "max_deviation"}
    order = None
    if predictor == "date":
        x = ["2026-01-01", "2026-01-02", "2026-01-09"]
    elif predictor == "categorical":
        x = ["low", "empty", "high"]
        declaration["predictor"] = "categorical"
        order = x
    data = {"x": x * 2, "y": [1, None, 4, 3, None, 8], "u": ["a"] * 3 + ["b"] * 3}
    p = mp.plot(data)
    if axis == "y2":
        p.secondary_yaxis("Independent target")
    if predictor == "date":
        p.date_axis(
            ("y2" if axis == "y2" else "y") if orient == "h" else "x", timezone="UTC"
        )
    p.lineplot(
        "x",
        "y",
        units="u",
        n_boot=31,
        seed=5,
        line=declaration,
        orient=orient,
        axis=axis,
        order=order,
        error_style="bars",
        marker="o",
    )
    before = p.to_json()
    fig = p.render()
    try:
        target = fig.axes[1] if axis == "y2" else fig.axes[0]
        coordinates = np.asarray(target.lines[0].get_xydata())
        if orient == "h":
            coordinates = coordinates[:, ::-1]
        expected_x = (
            matplotlib.dates.date2num(
                [datetime.fromisoformat(value).replace(tzinfo=UTC) for value in x]
            )
            if predictor == "date"
            else [0, 1, 2]
            if predictor == "categorical"
            else x
        )
        np.testing.assert_array_equal(coordinates[:, 0], expected_x)
        np.testing.assert_array_equal(coordinates[[0, 2], 1], [2, 6])
        assert np.isnan(coordinates[1, 1])
        assert p.to_json() == before
    finally:
        plt.close(fig)


def test_raw_line_roles_preserve_duplicates_order_coordinate_and_semantic_barriers():
    data = {
        "id": list(range(8)),
        "x": [2, 1, 1, 3, 4, 5, 6, 7],
        "y": [8, 4, 5, None, 3, 6, 9, 10],
        "h": ["A", "A", "A", "A", "A", None, "B", "A"],
        "s": [1, 1, 1, 1, 1, 1, 2, 1],
        "m": ["first"] * 8,
    }
    p = mp.plot(data).line(
        "x",
        "y",
        semantics=mp.SemanticSpec(hue="h", size="s", style="m"),
    )
    before = p.to_json()
    fig = p.render()
    try:
        observed = [line for line in fig.axes[0].lines if len(line.get_xdata())]
        assert len(observed) == 2
        a = next(line for line in observed if len(line.get_xdata()) > 2)
        np.testing.assert_array_equal(a.get_xdata(), [2, 1, 1, 3, 4, 5, 7])
        assert np.isnan(a.get_ydata()[3]) and np.isnan(a.get_ydata()[5])
        np.testing.assert_array_equal(a.get_ydata()[[0, 1, 2, 4, 6]], [8, 4, 5, 3, 10])
        assert tuple(a._mudplot_source_rows) == (0, 1, 2, 3, 4, 5, 7)
        assert p.to_json() == before
    finally:
        plt.close(fig)


def test_shared_guide_has_one_scope_owner_and_truthful_mark_specific_units():
    data = {
        "x": [0, 1, 0, 1],
        "y": [1, 2, 4, 5],
        "h": ["a", "a", "b", "b"],
        "s": [0, 1, 0, 1],
        "m": ["same"] * 4,
    }
    mapping = mp.SemanticSpec(
        hue="h",
        size="s",
        style="m",
        sizes=[0, 6],
        markers=["s"],
        scale_id="scope",
    )
    p = (
        mp.plot(data)
        .scatter(
            "x",
            "y",
            semantics=mapping,
            edge_color="#222222",
            line_width=1.8,
            label="points",
        )
        .line("x", "y", semantics=mapping, label="supplied")
        .shared_guides([mp.SharedGuideSpec("scope", title="Shared raw domain")])
        .size(9, 5)
    )
    before = p.to_json()
    fig = p.render()
    try:
        assert len(fig.legends) == 1
        assert {text.get_text() for text in fig.axes[0].get_legend().get_texts()} == {
            "points",
            "supplied",
        }
        handles = fig.legends[0].legend_handles
        native_edges = fig.axes[0].collections[0].get_edgecolors()
        assert np.array_equal(
            np.sqrt(fig.axes[0].collections[0].get_sizes()), [0, 6, 0, 6]
        )
        supplied = [line for line in fig.axes[0].lines if len(line.get_xdata())]
        assert {line.get_linewidth() for line in supplied} == {0, 6}
        assert any(
            line.get_linewidth() == 0 and line.get_markersize() > 0 for line in supplied
        )
        point_handle = next(
            handle
            for handle in handles
            if handle.get_linestyle() in ("None", "", " ")
            and np.isclose(handle.get_markeredgewidth(), 1.8)
            and np.allclose(
                matplotlib.colors.to_rgba(handle.get_markeredgecolor()), native_edges[0]
            )
        )
        assert point_handle.get_marker() == "s"
        assert p.to_json() == before
        assert mp.Plot.from_json(before).spec.shared_guides == p.spec.shared_guides
    finally:
        plt.close(fig)


@pytest.mark.parametrize("hue", [[-5, 0, 5], [0, 0, 0]])
def test_shared_numeric_hue_has_one_truthful_original_domain_colourbar(hue):
    data = {"x": [0, 1, 2], "y": [2, 5, 4], "h": hue}
    mapping = mp.SemanticSpec(hue="h", hue_kind="numeric", scale_id="scope")
    p = (
        mp.plot(data)
        .scatter("x", "y", semantics=mapping, colorbar=True, clabel="Raw h")
        .line("x", "y", semantics=mapping, colorbar=True, clabel="Raw h")
        .shared_guides([{"scale_id": "scope"}])
        .size(8, 5)
    )
    fig = p.render()
    try:
        bars = [
            ax for ax in fig.findobj(matplotlib.axes.Axes) if hasattr(ax, "_colorbar")
        ]
        assert len(bars) == 1
        assert bars[0].get_xlabel() == "Raw h"
        numeric_labels = [
            float(label.get_text()) for label in bars[0].get_xticklabels()
        ]
        assert (min(numeric_labels), max(numeric_labels)) == (min(hue), max(hue))
        mappable = bars[0]._colorbar.mappable
        fractions = (
            [0.5] * len(hue)
            if len(set(hue)) == 1
            else [(value - min(hue)) / (max(hue) - min(hue)) for value in hue]
        )
        native_faces = fig.axes[0].collections[0].get_facecolors()
        assert np.allclose(mappable.to_rgba(fractions), native_faces)
        if len(set(hue)) == 1:
            assert np.allclose(mappable.to_rgba([0, 0.5, 1]), native_faces)
    finally:
        plt.close(fig)


def test_shared_guide_invalid_membership_is_atomic_and_empty_scope_draws_nothing():
    p = (
        mp.plot({"x": [], "y": [], "h": []})
        .line("x", "y", semantics=mp.SemanticSpec(hue="h", scale_id="scope"))
        .shared_guides([{"scale_id": "scope"}])
    )
    before, history = p.to_json(), p.action_log
    with pytest.raises(ValueError):
        p.shared_guides([{"scale_id": "unknown"}])
    assert p.to_json() == before and p.action_log == history
    with pytest.raises(ValueError):
        p.dispatch(mp.actions.RemoveLayer(0))
    assert p.to_json() == before and p.action_log == history
    fig = p.render()
    try:
        assert not fig.legends
        assert not fig.axes[0].lines and not fig.axes[0].collections
    finally:
        plt.close(fig)
    p.shared_guides(None).dispatch(mp.actions.RemoveLayer(0))
    assert not p.spec.panels[0].layers


def test_live_line_facets_keep_typed_cells_and_guides_through_nested_history():
    import copy

    data = {
        "x": ["left", "right"] * 6,
        "y": [1, 4, 2, 6, 3, 8, 4, 9, 5, 11, 6, 13],
        "u": ["a", "a", "b", "b", "c", "c"] * 2,
        "f": ["north"] * 6 + ["south"] * 6,
        "h": ["original trajectories"] * 12,
    }
    p = (
        mp.plot(data)
        .size(13, 9)
        .lineplot(
            "x",
            "y",
            units="u",
            n_boot=11,
            seed=9,
            line=mp.LineSpec(
                predictor="categorical", resampling="unit", calibration="max_deviation"
            ),
            order=["left", "reserved", "right"],
            semantics=mp.SemanticSpec(hue="h", scale_id="trajectories"),
        )
        .facet(col="f", col_order=["north", "south", "empty"], live=True)
        .shared_guides([{"scale_id": "trajectories"}])
        .nest(2, 1, row=0, grid_id="outer")
    )
    ids = [panel.panel_id for panel in p.spec.panels]
    p.rename_panel(ids[1], "south-cell").reorder_panels(["south-cell", ids[2], ids[0]])
    assert p.spec.facet_template is not None
    geometry = {
        panel.filters["f"]: (panel.panel_id, panel.placement.to_dict())
        for panel in p.spec.panels
    }
    north = next(
        i for i, panel in enumerate(p.spec.panels) if panel.filters["f"] == "north"
    )
    p.labels(title="Local title", panel=north)
    original_recipe = copy.deepcopy(p.spec.facet_template)
    changed = copy.deepcopy(data)
    changed["y"][0] = 10
    p.dispatch(mp.actions.SetData(changed))
    assert p.spec.panels[north].title == "Local title"
    assert p.spec.facet_template == original_recipe
    replacement = copy.deepcopy(original_recipe.template)
    replacement.title = "Whole template"
    replacement.layers[0].stat.n_boot = 13
    p.facet_template(replacement)
    committed = p.to_json()
    p.store.undo()
    assert p.spec.panels[north].title == "Local title"
    assert p.spec.facet_template == original_recipe
    p.store.redo()
    assert p.to_json() == committed
    assert {
        panel.filters["f"]: (panel.panel_id, panel.placement.to_dict())
        for panel in p.spec.panels
    } == geometry
    assert all("Whole template" in panel.title for panel in p.spec.panels)
    p = mp.Plot.from_json(p.to_json())
    fig = p.render()
    try:
        assert len(fig.legends) == 1
        assert fig._mudplot_line_inference_work["whole_unit"] == 2 * 13 * (3 + 6 + 2)
        for panel, ax in zip(p.spec.panels, fig.axes, strict=True):
            if panel.filters["f"] == "empty":
                assert not ax.lines and not ax.collections
            else:
                line = next(
                    artist for artist in ax.lines if len(artist.get_xdata()) == 3
                )
                assert np.isnan(line.get_ydata()[1])
                assert "Whole template" in ax.get_title()
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "calibration,level",
    [("max_deviation", 50), ("max_deviation", 100), ("percentile", 50)],
)
def test_missing_trajectories_remain_in_uniform_unit_population_and_extended_ranks(
    calibration, level
):
    data = {
        "x": [0, 1] * 4,
        "y": [0, 4, 2, 6, None, None, None, None],
        "u": ["a", "a", "b", "b", "missing-c", "missing-c", "", ""],
    }
    choices = np.random.Generator(np.random.PCG64(13)).integers(
        0, 4, size=(31, 4), dtype=np.int64
    )
    scores = []
    for replicate in choices:
        a, b = (
            int(np.count_nonzero(replicate == 0)),
            int(np.count_nonzero(replicate == 1)),
        )
        scores.append(math.inf if a + b == 0 else abs(Fraction(2 * b, a + b) - 1))
    undefined = sum(score == math.inf for score in scores)
    assert undefined > 0
    p = (
        mp.plot(data)
        .size(9, 5)
        .lineplot(
            "x",
            "y",
            units="u",
            n_boot=31,
            seed=13,
            errorbar=("ci", level),
            error_style="bars",
            line={"resampling": "unit", "calibration": calibration},
        )
    )
    if calibration == "percentile" or level == 100:
        figures = plt.get_fignums()
        with pytest.raises(ValueError):
            p.render()
        assert plt.get_fignums() == figures
        assert p.spec.data.columns == data
        return
    q = sorted(scores)[math.ceil(Fraction(level) * 31 / 100) - 1]
    fig = p.render()
    try:
        segments = next(
            collection
            for collection in fig.axes[0].collections
            if isinstance(collection, LineCollection)
        ).get_segments()
        assert np.allclose(segments[0][:, 1], [float(1 - q), float(1 + q)])
        assert np.allclose(segments[1][:, 1], [float(5 - q), float(5 + q)])
        assert fig._mudplot_line_inference_work["whole_unit"] == 31 * (4 + 8 + 2)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("interval", [None, "sd", "se", "pi"])
@pytest.mark.parametrize(
    "controls",
    [
        {"resampling": "cell"},
        {"calibration": "percentile"},
        {"resampling": "unit", "calibration": "max_deviation"},
    ],
)
def test_explicit_inference_controls_are_ci_only_and_invalid_actions_are_atomic(
    interval, controls
):
    p = mp.plot({"x": [0, 0], "y": [1, 3], "u": ["a", "b"]})
    before, history = p.to_json(), p.action_log
    with pytest.raises(ValueError):
        p.lineplot(
            "x",
            "y",
            errorbar=interval,
            units="u" if controls.get("resampling") == "unit" else None,
            line=controls,
        )
    assert p.to_json() == before and p.action_log == history


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("axis", ["y", "y2"])
def test_whole_unit_working_log10_is_independent_of_display_base_and_target(
    orient, axis
):
    p = mp.plot(
        {"x": [0, 1, 0, 1], "y": [1, 100, 100, 10000], "u": ["a", "a", "b", "b"]}
    ).size(9, 5)
    if axis == "y2":
        p.secondary_yaxis("Actual target")
    value_axis = "x" if orient == "h" else axis
    p.axis_scale(value_axis, "log", options=mp.ScaleOptionsSpec(base=2))
    p.lineplot(
        "x",
        "y",
        units="u",
        stat_scale="axis",
        n_boot=31,
        seed=5,
        line={"resampling": "unit", "calibration": "max_deviation"},
        error_style="bars",
        orient=orient,
        axis=axis,
    )
    fig = p.render()
    try:
        target = fig.axes[1] if axis == "y2" else fig.axes[0]
        points = target.lines[0].get_xydata()
        if orient == "h":
            points = points[:, ::-1]
        assert np.allclose(points, [[0, 10], [1, 1000]])
        segments = next(
            item for item in target.collections if isinstance(item, LineCollection)
        ).get_segments()
        dimension = 0 if orient == "h" else 1
        assert np.allclose(segments[0][:, dimension], [1, 100])
        assert np.allclose(segments[1][:, dimension], [100, 10000])
    finally:
        plt.close(fig)


@pytest.mark.parametrize("interval", [("sd", 1), ("pi", 50)])
def test_predictor_only_retains_unweighted_sum_observation_intervals(interval):
    p = mp.plot({"x": [0, 0, 0], "y": [1, 3, 7]}).lineplot(
        "x",
        "y",
        estimator="sum",
        errorbar=interval,
        error_style="bars",
        line={"predictor": "native"},
    )
    fig = p.render()
    try:
        assert fig.axes[0].lines[0].get_ydata()[0] == 11
        expected = (
            [11 - math.sqrt(28 / 3), 11 + math.sqrt(28 / 3)]
            if interval[0] == "sd"
            else [2, 5]
        )
        segments = next(
            item for item in fig.axes[0].collections if isinstance(item, LineCollection)
        ).get_segments()
        assert np.allclose(segments[0][:, 1], expected)
        assert fig._mudplot_line_inference_work["total"] == 0
    finally:
        plt.close(fig)


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("axis", ["y", "y2"])
def test_complete_unit_calendar_response_uses_native_day_deviations(orient, axis):
    data = {
        "x": [0, 1, 0, 1],
        "y": ["2026-01-01", "2026-01-05", "2026-01-03", "2026-01-09"],
        "u": ["a", "a", "b", "b"],
    }
    p = mp.plot(data).size(10, 6)
    if axis == "y2":
        p.secondary_yaxis("Calendar target")
    p.date_axis("x" if orient == "h" else axis, timezone="UTC")
    p.lineplot(
        "x",
        "y",
        units="u",
        n_boot=31,
        seed=5,
        orient=orient,
        axis=axis,
        line={"resampling": "unit", "calibration": "max_deviation"},
        error_style="bars",
    )
    expected = matplotlib.dates.date2num(
        [
            datetime(2026, 1, 2, tzinfo=UTC),
            datetime(2026, 1, 7, tzinfo=UTC),
        ]
    )
    fig = p.render()
    try:
        target = fig.axes[1] if axis == "y2" else fig.axes[0]
        points = target.lines[0].get_xydata()
        dimension = 0 if orient == "h" else 1
        assert np.allclose(points[:, dimension], expected)
        segments = next(
            item for item in target.collections if isinstance(item, LineCollection)
        ).get_segments()
        assert np.allclose(segments[0][:, dimension], expected[0] + np.asarray([-2, 2]))
        assert np.allclose(segments[1][:, dimension], expected[1] + np.asarray([-2, 2]))
        assert p.spec.data.columns == data
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "failure",
    [
        "singleton-target",
        "native-collapse",
        "native-overflow",
        "log-inverse-overflow",
        "data-band-negative-on-log",
    ],
)
def test_complete_unit_undrawable_or_inadequate_support_rejects_before_native_figure(
    failure,
):
    if failure == "singleton-target":
        data = {"x": [0, 1, 0, 1], "y": [1, 2, None, 4], "u": ["a", "a", "b", "b"]}
    elif failure == "native-collapse":
        data = {"x": [0, 0], "y": [2**53, 2**53 + 1], "u": ["a", "b"]}
    elif failure == "native-overflow":
        data = {
            "x": [0, 1, 0, 1],
            "y": [-1.7e308, 1.7e308, 1.7e308, 1.7e308],
            "u": ["a", "a", "b", "b"],
        }
    elif failure == "log-inverse-overflow":
        data = {
            "x": [0, 1, 0, 1],
            "y": [1e-300, 1e300, 1e300, 1e300],
            "u": ["a", "a", "b", "b"],
        }
    else:
        data = {"x": [0, 1, 0, 1], "y": [1, 1, 3, 100], "u": ["a", "a", "b", "b"]}
    p = mp.plot(data)
    if failure in {"log-inverse-overflow", "data-band-negative-on-log"}:
        p.yscale("log")
    p.lineplot(
        "x",
        "y",
        units="u",
        n_boot=31,
        seed=5,
        stat_scale="axis" if failure == "log-inverse-overflow" else "data",
        line={"resampling": "unit", "calibration": "max_deviation"},
    )
    before = plt.get_fignums()
    with pytest.raises(ValueError):
        p.render()
    assert plt.get_fignums() == before
    assert p.spec.data.columns == data


@pytest.mark.parametrize("calibration", ["percentile", "max_deviation"])
def test_real_empirical_atom_retains_zero_width_without_invented_uncertainty(
    calibration,
):
    p = mp.plot(
        {"x": [0, 1, 0, 1], "y": [4, 7, 4, 7], "u": ["a", "a", "b", "b"]}
    ).lineplot(
        "x",
        "y",
        units="u",
        n_boot=31,
        seed=5,
        error_style="bars",
        line={"resampling": "unit", "calibration": calibration},
    )
    fig = p.render()
    try:
        segments = next(
            item for item in fig.axes[0].collections if isinstance(item, LineCollection)
        ).get_segments()
        assert np.array_equal(segments[0][:, 1], [4, 4])
        assert np.array_equal(segments[1][:, 1], [7, 7])
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "declaration,error",
    [
        ({"band": "simultaneous"}, ValueError),
        ({"predictor": True}, TypeError),
        ({"predictor": "ordinal"}, ValueError),
        ({"resampling": "trajectory"}, ValueError),
        ({"calibration": "simultaneous"}, ValueError),
        ({"calibration": "band"}, ValueError),
        ({"family": "figure"}, ValueError),
        ({"family": ["curve"]}, TypeError),
    ],
)
def test_line_declaration_has_one_strict_persisted_vocabulary(declaration, error):
    p = mp.plot({"x": [0, 0], "y": [1, 3]})
    before, history = p.to_json(), p.action_log
    with pytest.raises(error):
        p.lineplot("x", "y", line=declaration)
    assert p.to_json() == before and p.action_log == history


def test_typed_categorical_predictors_do_not_merge_boolean_numeric_slots():
    data = {"x": [True, 1, True, 1], "y": [1, 10, 3, 14], "u": ["a", "a", "b", "b"]}
    p = mp.plot(data).lineplot(
        "x",
        "y",
        order=[True, "reserved", 1],
        units="u",
        n_boot=31,
        seed=5,
        line={
            "predictor": "categorical",
            "resampling": "unit",
            "calibration": "max_deviation",
        },
    )
    fig = p.render()
    try:
        points = fig.axes[0].lines[0].get_xydata()
        assert np.array_equal(points[:, 0], [0, 1, 2])
        assert np.array_equal(points[[0, 2], 1], [2, 12])
        assert np.isnan(points[1, 1])
        restored = mp.Plot.from_json(p.to_json()).spec.data.columns["x"]
        assert type(restored[0]) is bool and type(restored[1]) is int
    finally:
        plt.close(fig)


def test_live_line_family_survives_mosaic_inset_template_and_leaf_removal():
    import copy

    data = {
        "x": [0, 1, 0, 1] * 2,
        "y": [1, 4, 3, 8, 2, 6, 4, 10],
        "u": ["a", "a", "b", "b"] * 2,
        "f": ["A"] * 4 + ["B"] * 4,
        "h": ["same raw scope"] * 8,
    }
    p = (
        mp.plot(data)
        .lineplot(
            "x",
            "y",
            units="u",
            n_boot=7,
            line={"resampling": "unit", "calibration": "max_deviation"},
            semantics=mp.SemanticSpec(hue="h", scale_id="scope"),
        )
        .facet(col="f", col_order=["A", "B", "empty"], live=True)
        .shared_guides([{"scale_id": "scope"}])
        .nest(2, 1)
    )
    ids = [panel.panel_id for panel in p.spec.panels]
    p.mosaic([ids]).inset(ids[0], [0.6, 0.6, 0.3, 0.3], panel_id="detail")
    assert p.spec.facet_template is not None
    before = {panel.panel_id: panel.placement for panel in p.spec.panels}
    replacement = copy.deepcopy(p.spec.facet_template.template)
    replacement.layers[0].line.calibration = "percentile"
    p.facet_template(replacement)
    assert {panel.panel_id: panel.placement for panel in p.spec.panels} == before
    assert not p.spec.panels[-1].layers
    assert p.spec.shared_guides[0].scale_id == "scope"
    p.remove_panel("detail")
    assert p.spec.facet_template is not None
    p.remove_panel(ids[-1])
    assert p.spec.facet_template is None
    assert {panel.filters["f"] for panel in p.spec.panels} == {"A", "B"}
    assert p.spec.shared_guides[0].scale_id == "scope"


@pytest.mark.parametrize("clock", ["same-instant-aliases", "numeric-origin"])
def test_complete_unit_clock_boundary_preserves_original_aliases_and_native_spacing(
    clock,
):
    if clock == "same-instant-aliases":
        predictors = [
            "2026-01-01T00:00:00Z",
            "2026-01-10T00:00:00",
            "2025-12-31T19:00:00-05:00",
            "2026-01-09T19:00:00-05:00",
        ]
        options = {"timezone": "UTC"}
    else:
        predictors = [0, 9 * 86400, 0, 9 * 86400]
        options = {"unit": "s", "origin": "2026-01-01T00:00:00Z", "timezone": "UTC"}
    data = {"x": predictors, "y": [1, 4, 3, 8], "u": ["a", "a", "b", "b"]}
    p = (
        mp.plot(data)
        .date_axis("x", **options)
        .lineplot(
            "x",
            "y",
            units="u",
            n_boot=31,
            seed=5,
            line={"resampling": "unit", "calibration": "max_deviation"},
        )
    )
    fig = p.render()
    try:
        points = fig.axes[0].lines[0].get_xydata()
        expected_x = matplotlib.dates.date2num(
            [
                datetime(2026, 1, 1, tzinfo=UTC),
                datetime(2026, 1, 10, tzinfo=UTC),
            ]
        )
        assert np.array_equal(points[:, 0], expected_x)
        assert np.array_equal(points[:, 1], [2, 6])
        assert points[1, 0] - points[0, 0] == 9
        assert mp.Plot.from_json(p.to_json()).spec.data.columns == data
    finally:
        plt.close(fig)


def test_mapped_supplied_horizontal_y2_clock_keeps_raw_rows_and_actual_coordinates():
    dates = ["2026-01-09", "2026-01-01", "2026-01-01", "2026-01-02", "2026-01-10"]
    data = {
        "date": dates,
        "response": [9, 1, 3, None, 10],
        "h": ["A"] * 5,
        "s": [2] * 5,
        "m": ["square"] * 5,
        "id": list(range(5)),
    }
    p = (
        mp.plot(data)
        .secondary_yaxis("UTC predictor")
        .date_axis("y2", timezone="UTC")
        .xscale("log")
        .line(
            "date",
            "response",
            orient="h",
            axis="y2",
            semantics=mp.SemanticSpec(hue="h", size="s", style="m", markers=["s"]),
        )
    )
    fig = p.render()
    try:
        artist = next(line for line in fig.axes[1].lines if len(line.get_xdata()) == 5)
        points = artist.get_xydata()
        expected_dates = matplotlib.dates.date2num(
            [datetime.fromisoformat(value).replace(tzinfo=UTC) for value in dates]
        )
        assert np.array_equal(points[:, 1], expected_dates)
        assert np.array_equal(points[[0, 1, 2, 4], 0], [9, 1, 3, 10])
        assert np.isnan(points[3, 0])
        assert tuple(artist._mudplot_source_rows) == (0, 1, 2, 3, 4)
        assert p.spec.data.columns == data
        assert fig._mudplot_line_inference_work["total"] == 0
    finally:
        plt.close(fig)


def test_simultaneous_calibration_is_independent_of_sort_and_interval_geometry():
    data = {"x": [2, 0, 1] * 2, "y": [4, 0, 2, 8, 2, 6], "u": ["a"] * 3 + ["b"] * 3}
    for sorted_predictor, style in ((False, "bars"), (True, "bars"), (True, "band")):
        p = mp.plot(data).lineplot(
            "x",
            "y",
            units="u",
            n_boot=31,
            seed=5,
            sort=sorted_predictor,
            error_style=style,
            line={"resampling": "unit", "calibration": "max_deviation"},
        )
        fig = p.render()
        try:
            points = fig.axes[0].lines[0].get_xydata()
            order = [0, 1, 2] if sorted_predictor else [2, 0, 1]
            assert np.array_equal(points[:, 0], order)
            assert np.array_equal(points[:, 1], [{0: 1, 1: 4, 2: 6}[x] for x in order])
            if style == "bars":
                segments = next(
                    item
                    for item in fig.axes[0].collections
                    if isinstance(item, LineCollection)
                ).get_segments()
                assert np.array_equal(
                    np.asarray(segments)[:, :, 1],
                    [
                        [{0: 1, 1: 4, 2: 6}[x] - 2, {0: 1, 1: 4, 2: 6}[x] + 2]
                        for x in order
                    ],
                )
            else:
                vertices = fig.axes[0].collections[0].get_paths()[0].vertices
                for x in order:
                    native = vertices[vertices[:, 0] == x, 1]
                    assert native.min() == {0: 1, 1: 4, 2: 6}[x] - 2
                    assert native.max() == {0: 1, 1: 4, 2: 6}[x] + 2
        finally:
            plt.close(fig)
    invalid = mp.plot(data).lineplot(
        "x",
        "y",
        units="u",
        n_boot=31,
        seed=5,
        sort=False,
        error_style="band",
        line={"resampling": "unit", "calibration": "max_deviation"},
    )
    figures = plt.get_fignums()
    with pytest.raises(ValueError):
        invalid.render()
    for number in set(plt.get_fignums()) - set(figures):
        plt.close(number)


@pytest.mark.parametrize("calibration", ["percentile", "max_deviation"])
def test_weighted_total_small_mass_tail_rejects_before_random_or_native(
    calibration, monkeypatch
):
    # Continuous numeric hue permits256 distinct curves, not categorical64.
    # Tiny positive masses retain their native denominator in totals, unlike
    # means. Bounded exact tails must account for that denominator on both routes.
    data = {"x": [], "y": [], "unit": [], "hue": [], "weight": []}
    for unit in range(2):
        for curve in range(256):
            row = (1, unit + 1, unit, curve, math.ulp(0.0))
            for name, value in zip(data, row, strict=True):
                data[name].append(value)
    p = mp.plot(data).lineplot(
        "x",
        "y",
        semantics={"hue": "hue", "hue_kind": "numeric"},
        units="unit",
        weights="weight",
        estimator="sum",
        errorbar="ci",
        n_boot=100000,
        seed=29,
        line={"resampling": "unit", "calibration": calibration},
    )
    assert mp.validate(p.spec) == []
    before = p.to_json()
    calls = {"random": 0, "native": 0}

    def no_random(*args, **kwargs):
        calls["random"] += 1
        raise AssertionError("working-state rejection must precede random draws")

    def no_native(*args, **kwargs):
        calls["native"] += 1
        raise AssertionError("working-state rejection must precede native output")

    monkeypatch.setattr(np.random, "Generator", no_random)
    monkeypatch.setattr(plt, "figure", no_native)
    with pytest.raises(ValueError):
        p.render()
    assert calls == {"random": 0, "native": 0}
    assert p.to_json() == before


@pytest.mark.parametrize(
    "kind,controls",
    [("lineplot", {"resampling": "cell"}), ("lineplot", None), ("pointplot", None)],
)
def test_positive_working_ci_inverse_collapse_rejects_and_retains_output(
    kind, controls, tmp_path
):
    data = {
        "id": list(range(100)),
        "x": [0] * 100,
        "y": [1.0] * 99 + [math.nextafter(1.0, math.inf)],
        "w": [1000.0] * 99 + [1.0],
    }
    # Independent paired-row enumeration preserves the inherited binary64
    # replicate/probability boundary without a production quantile helper.
    value = Fraction(float(np.log10(data["y"][-1])))
    rng = np.random.Generator(np.random.PCG64(7))
    replicates = []
    for _ in range(31):
        selected = rng.integers(0, 100, size=100)
        count = sum(int(index) == 99 for index in selected)
        replicates.append(float(count * value / ((100 - count) * 1000 + count)))
    tail = (1.0 - 95.0 / 100.0) / 2.0
    lower = _type7_observed(replicates, tail)
    upper = _type7_observed(replicates, 1.0 - tail)
    assert lower == 0 < upper
    assert 10.0 ** float(lower) == 10.0 ** float(upper) == 1.0

    options = {
        "weights": "w",
        "errorbar": ("ci", 95),
        "n_boot": 31,
        "seed": 7,
        "stat_scale": "axis",
    }
    if kind == "lineplot":
        options.update(line=controls, error_style="bars")
    p = getattr(mp.plot(data), kind)("x", "y", **options).yscale("log")
    before, history = p.to_json(), p.action_log
    output = tmp_path / "accepted.png"
    figure = mp.plot({"x": [0, 1], "y": [1, 2]}).line("x", "y").save(output)
    plt.close(figure)
    retained = output.read_bytes()
    figures = plt.get_fignums()
    with pytest.raises(ValueError):
        p.save(output)
    assert output.read_bytes() == retained
    assert plt.get_fignums() == figures
    assert p.to_json() == before and p.action_log == history
    assert p.spec.data.columns == data


@pytest.mark.parametrize("kind", ["line", "lineplot"])
@pytest.mark.parametrize("shared", [False, True])
@pytest.mark.parametrize(
    "orient,axis", [("v", "y"), ("h", "y"), ("v", "y2"), ("h", "y2")]
)
def test_line_order_selects_actual_mapping_domains_and_empty_scope_history(
    kind, shared, orient, axis
):
    import copy

    from matplotlib.axes import Axes

    data = {
        "id": ["excluded-row", "kept-row"],
        "x": ["excluded", "keep"],
        "y": [7, 1],
        "h": [999, 0],
        "s": [999, 2],
        "d": ["excluded-style", "kept-style"],
    }
    mapping = mp.SemanticSpec(
        hue="h",
        hue_kind="numeric",
        size="s",
        style="d",
        sizes=[2, 8],
        markers=["s", "^"],
        scale_id="selected" if shared else None,
    )
    options = {
        "semantics": mapping,
        "line": {"predictor": "categorical"},
        "order": ["keep"],
        "colorbar": True,
        "orient": orient,
        "axis": axis,
    }
    if kind == "lineplot":
        options["errorbar"] = None
    p = mp.plot(data).size(9, 5)
    if axis == "y2":
        p.secondary_yaxis("Declared target")
    p = getattr(p, kind)("x", "y", **options)
    if shared:
        p.shared_guides([{"scale_id": "selected"}])
    selected = p.to_json()
    fig = p.render()
    try:
        target = fig.axes[1] if axis == "y2" else fig.axes[0]
        line = next(artist for artist in target.lines if len(artist.get_xdata()))
        assert np.array_equal(
            line.get_xydata(), [[0, 1]] if orient == "v" else [[1, 0]]
        )
        assert line.get_linewidth() == 5
        assert line.get_marker() == "s"
        colourbars = [
            axis._colorbar
            for axis in fig.findobj(Axes)
            if getattr(axis, "_colorbar", None) is not None
        ]
        assert len(colourbars) == 1
        assert np.allclose(
            matplotlib.colors.to_rgba(line.get_color()), colourbars[0].cmap(0.5)
        )
    finally:
        plt.close(fig)
    replacement = copy.deepcopy(p.spec.panels[0].layers[0])
    replacement.order = ["reserved"]
    p.dispatch(mp.actions.ReplaceLayer(0, replacement))
    empty = p.to_json()
    p.store.undo()
    assert p.to_json() == selected
    p.store.redo()
    assert p.to_json() == empty
    reopened = mp.Plot.from_json(empty)
    assert reopened.spec.data.columns == data
    fig = reopened.render()
    try:
        assert not any(
            len(line.get_xdata()) for target in fig.axes for line in target.lines
        )
        assert not fig.legends and fig.axes[0].get_legend() is None
        assert not any(
            getattr(axis, "_colorbar", None) is not None for axis in fig.findobj(Axes)
        )
        target = fig.axes[1] if axis == "y2" else fig.axes[0]
        predictor = fig.axes[0].xaxis if orient == "v" else target.yaxis
        assert any(
            location == 0 and label.get_text() == "reserved"
            for location, label in zip(
                predictor.get_majorticklocs(), predictor.get_ticklabels(), strict=True
            )
        )
    finally:
        plt.close(fig)


@pytest.mark.parametrize("dpi", [72, 300])
def test_nested_shared_guides_keep_automatic_titles_and_twin_decorations_separate(dpi):
    from itertools import pairwise

    from matplotlib.axes import Axes
    from matplotlib.transforms import Bbox
    from mudplot._layout_render import native_axes, panel_axes

    data = {name: [] for name in ("id", "t", "v", "u", "site", "h", "s")}
    for site_index, site in enumerate(("north", "south")):
        for hue, style in ((10, "circle"), (20, "square")):
            for unit in range(3):
                for point, date in enumerate(("2026-01-01", "2026-01-09")):
                    data["id"].append(len(data["id"]))
                    data["t"].append(date)
                    data["v"].append(2 ** (4 + 2 * point + unit + site_index))
                    data["u"].append(unit)
                    data["site"].append(site)
                    data["h"].append(hue)
                    data["s"].append(style)
    p = (
        mp.plot(data)
        .size(15, 10)
        .dispatch(mp.actions.SetDpi(dpi))
        .secondary_yaxis("UTC predictor")
        .date_axis("y2", timezone="UTC")
        .axis_scale("x", "log", options=mp.ScaleOptionsSpec(base=2))
        .lineplot(
            "t",
            "v",
            axis="y2",
            orient="h",
            units="u",
            n_boot=11,
            seed=7,
            stat_scale="axis",
            errorbar=("ci", 80),
            line={"resampling": "unit", "calibration": "max_deviation"},
            semantics=mp.SemanticSpec(
                hue="h",
                hue_kind="numeric",
                style="s",
                scale_id="original",
                markers=["o", "s"],
            ),
            colorbar=True,
        )
        .facet(col="site", col_order=["north", "south", "empty"], live=True)
        .nest(2, 1, grid_id="outer")
        .shared_guides([{"scale_id": "original", "location": "outside top"}])
    )
    ids = [panel.panel_id for panel in p.spec.panels]
    p.reorder_panels([ids[1], ids[2], ids[0]])
    before = p.to_json()
    figure = p.render()
    try:
        figure.canvas.draw()
        renderer = figure.canvas.get_renderer()
        panels = panel_axes(figure)
        bars = [axis for axis in figure.findobj(Axes) if hasattr(axis, "_colorbar")]
        guides = [artist.get_tightbbox(renderer) for artist in [*figure.legends, *bars]]
        assert guides
        for axis in panels:
            title = axis.title.get_window_extent(renderer)
            assert all(not title.overlaps(guide) for guide in guides)
        decorations = {}
        for axis in native_axes(figure):
            owner = getattr(axis, "_mudplot_semantic_guide_axis", axis)
            if owner not in panels:
                continue
            bounds = axis.yaxis.get_tightbbox(renderer)
            if bounds is not None:
                decorations.setdefault(owner, []).append(bounds)
        ordered = sorted(panels, key=lambda axis: axis.bbox.x0)
        for left, right in pairwise(ordered):
            left_bounds = Bbox.union(decorations[left])
            right_bounds = Bbox.union(decorations[right])
            assert left_bounds.x1 < right_bounds.x0
        assert p.to_json() == before and p.spec.data.columns == data
    finally:
        plt.close(figure)
