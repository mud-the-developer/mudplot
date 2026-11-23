"""C07 raw estimators: independent arithmetic, intervals, native units and replay."""

from __future__ import annotations

import copy
import math
from decimal import Decimal, localcontext
from fractions import Fraction

import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import LineCollection


def figure_for(kind, values, *, weights=None, **options):
    columns = {
        "x": [0] * len(values),
        "v": list(values),
        "id": list(range(len(values))),
    }
    if weights is not None:
        columns["w"] = list(weights)
        options["weights"] = "w"
    if kind == "lineplot" and options.get("errorbar", "ci") is not None:
        options["error_style"] = "bars"
    plot = getattr(mp.plot(columns), kind)("x", "v", **options)
    return plot, plot.render()


def center(axis, kind):
    return (
        axis.patches[0].get_height()
        if kind == "barplot"
        else axis.lines[0].get_ydata()[0]
    )


def endpoints(axis):
    return [
        segment[:, 1]
        for artist in axis.collections
        if isinstance(artist, LineCollection)
        for segment in artist.get_segments()
    ]


def reference(values, weights, estimator):
    pairs = list(zip(values, weights, strict=True))
    if estimator == "count":
        return float(sum(map(Fraction, weights), Fraction()))
    if estimator in ("min", "max"):
        return (min if estimator == "min" else max)(values)
    if estimator == "median":
        target = sum(map(Fraction, weights), Fraction()) / 2
        mass = Fraction()
        for value, weight in sorted(pairs):
            mass += Fraction(weight)
            if mass >= target:
                return value
        raise AssertionError("positive mass was not conserved")
    total = sum((Fraction(v) * Fraction(w) for v, w in pairs), Fraction())
    return (
        float(total / sum(map(Fraction, weights), Fraction()))
        if estimator == "mean"
        else float(total)
    )


@pytest.mark.parametrize("kind", ["barplot", "pointplot", "lineplot"])
@pytest.mark.parametrize("estimator", ["sum", "mean"])
@pytest.mark.parametrize("values", [[1e300, -1e300, 1e-300], [2**80, 3, -(2**80)]])
def test_source_unit_cancellation_retains_representable_residual(
    kind, estimator, values
):
    plot, figure = figure_for(kind, values, estimator=estimator, errorbar=None)
    expected = float(
        sum(map(Fraction, values), Fraction())
        / (len(values) if estimator == "mean" else 1)
    )
    assert expected > 0
    assert center(figure.axes[0], kind) == expected
    assert plot.spec.data.columns["v"] == values
    assert mp.apply(plot.action_log) == plot.spec
    assert mp.Plot.from_json(plot.to_json()).spec == plot.spec


@pytest.mark.parametrize("kind", ["barplot", "pointplot", "lineplot"])
@pytest.mark.parametrize("estimator", ["mean", "median", "sum", "min", "max", "count"])
def test_named_weighted_estimates_are_native_quantities(kind, estimator):
    values, weights = [0, 10, 20], [1, 38, 1]
    _, figure = figure_for(
        kind, values, weights=weights, estimator=estimator, errorbar=None
    )
    assert center(figure.axes[0], kind) == reference(values, weights, estimator)


@pytest.mark.parametrize("kind", ["barplot", "pointplot", "lineplot"])
@pytest.mark.parametrize("estimator", ["mean", "median", "min", "max"])
def test_exact_declared_percent_LEFT_PI_keeps_observed_CDF_knots(kind, estimator):
    _, figure = figure_for(
        kind, [0, 10, 20], weights=[1, 38, 1], estimator=estimator, errorbar=("pi", 95)
    )
    np.testing.assert_array_equal(endpoints(figure.axes[0]), [[0, 10]])
    assert center(figure.axes[0], kind) == reference([0, 10, 20], [1, 38, 1], estimator)


@pytest.mark.parametrize("kind", ["barplot", "pointplot", "lineplot"])
def test_LEFT_endpoints_keep_minsubnormal_mass_next_to_maxfinite(kind):
    _, figure = figure_for(
        kind,
        [0, 1],
        weights=[math.ulp(0), 1e308],
        estimator="median",
        errorbar=("pi", 100),
    )
    np.testing.assert_array_equal(endpoints(figure.axes[0]), [[0, 1]])
    assert center(figure.axes[0], kind) == 1


@pytest.mark.parametrize("method", ["sd", "se"])
@pytest.mark.parametrize("distance", [2.0, 2e-300])
def test_weighted_spread_uses_full_exponent_reliability_and_effective_size(
    method, distance
):
    values, weights = [0, distance], [1e308, math.ulp(0)]
    _, figure = figure_for("pointplot", values, weights=weights, errorbar=(method, 1))
    masses = list(map(Fraction, weights))
    total = sum(masses, Fraction())
    mu = (
        sum((Fraction(v) * w for v, w in zip(values, masses, strict=True)), Fraction())
        / total
    )
    variance = (
        sum(
            (w * (Fraction(v) - mu) ** 2 for v, w in zip(values, masses, strict=True)),
            Fraction(),
        )
        * total
        / (total * total - sum((w * w for w in masses), Fraction()))
    )
    effective = total * total / sum((w * w for w in masses), Fraction())
    if method == "se":
        variance /= effective
    with localcontext() as context:
        context.prec = 1200
        expected = float(
            (Decimal(variance.numerator) / Decimal(variance.denominator)).sqrt()
        )
    actual = endpoints(figure.axes[0])[0]
    assert expected > 0
    np.testing.assert_allclose(
        actual, [float(mu) - expected, float(mu) + expected], rtol=3e-15, atol=0
    )


@pytest.mark.parametrize("estimator", ["mean", "median", "sum", "min", "max"])
@pytest.mark.parametrize("kind", ["barplot", "pointplot", "lineplot"])
def test_percentile_CI_uniformly_resamples_original_value_weight_pairs(kind, estimator):
    values = [1, 4, 9, 12]
    weights = [1, 3, 2, 1]
    generator = np.random.default_rng(19)
    indices = generator.integers(0, 4, size=(41, 4))
    replicates = [
        reference([values[i] for i in row], [weights[i] for i in row], estimator)
        for row in indices
    ]
    expected = np.quantile(replicates, [0.1, 0.9], method="linear")
    _, figure = figure_for(
        kind,
        values,
        weights=weights,
        estimator=estimator,
        errorbar=("ci", 80),
        n_boot=41,
        seed=19,
    )
    np.testing.assert_allclose(
        endpoints(figure.axes[0]), [expected], rtol=2e-15, atol=0
    )


def test_hierarchical_new_inference_keeps_typed_units_and_uniform_case_pairs():
    values, weights = [1, 3, 5, 8, 13], [1, 2, 1, 3, 1]
    units = [True, True, 1, "True", "1"]
    groups = [[0, 1], [2], [3], [4]]
    rng = np.random.default_rng(31)
    expected = []
    for _ in range(37):
        chosen = rng.integers(0, len(groups), size=len(groups))
        rows = [
            index
            for group in chosen
            for index in np.asarray(groups[group])[
                rng.integers(0, len(groups[group]), size=len(groups[group]))
            ]
        ]
        expected.append(
            reference(
                [values[index] for index in rows],
                [weights[index] for index in rows],
                "median",
            )
        )
    data = {"c": ["A"] * 5, "v": values, "w": weights, "u": units}
    plot = mp.plot(data).pointplot(
        "c",
        "v",
        weights="w",
        units="u",
        estimator="median",
        errorbar=("ci", 80),
        n_boot=37,
        seed=31,
    )
    before = np.random.get_state()
    figure = plot.render()
    after = np.random.get_state()
    assert before[0] == after[0] and before[2:] == after[2:]
    np.testing.assert_array_equal(before[1], after[1])
    np.testing.assert_allclose(
        endpoints(figure.axes[0]),
        [np.quantile(expected, [0.1, 0.9], method="linear")],
        rtol=2e-15,
        atol=0,
    )
    assert plot.spec.data.columns == data


@pytest.mark.parametrize("kind", ["barplot", "pointplot"])
def test_roles_keep_raw_tuples_physical_main_units_and_no_guide_data_limits(kind):
    columns = {
        "c": ["A", "A", "B", "B"] * 3,
        "v": [1, 2, 3, 4, 2, 3, 4, 5, 3, 4, 5, 6],
        "h": [True, 1, True, 1] * 3,
        "s": [1, 2, 1, 2] * 3,
        "style": ["First", "Second", "First", "Second"] * 3,
    }
    semantics = {
        "hue": "h",
        "hue_order": [True, 1],
        "size": "s",
        "size_norm": [1, 2],
        "sizes": [2, 4],
        "style": "style",
        "markers": ["D", "^"],
    }
    plot = getattr(mp.plot(columns), kind)("c", "v", semantics=semantics, errorbar=None)
    axis = plot.render().axes[0]
    if kind == "barplot":
        marks = [
            patch
            for patch in axis.patches
            if patch.get_data_transform().contains_branch(axis.transData)
        ]
        assert len(marks) == 4
        assert sorted(mark.get_linewidth() for mark in marks) == [2, 2, 4, 4]
        actual = sorted(mark.get_height() for mark in marks)
        assert actual == [2, 3, 4, 5]
    else:
        marks = [line for line in axis.lines if len(line.get_xdata())]
        assert len(marks) == 2
        assert sorted(mark.get_markersize() for mark in marks) == [2, 4]
        assert all(mark.get_linewidth() == 1.25 for mark in marks)
        assert {mark.get_marker() for mark in marks} == {"D", "^"}
        np.testing.assert_array_equal(axis.dataLim.extents, [0, 2, 1, 5])
    assert plot.spec.data.columns == columns
    labels = axis.get_legend_handles_labels()[1]
    assert "hue: h=True" in labels and "hue: h=1" in labels
    assert all("__mudplot" not in label for label in labels)


@pytest.mark.parametrize("kind", ["barplot", "pointplot"])
def test_axis_only_NEW_horizontal_y2_uses_typed_category_selection(kind):
    plot = mp.plot({"c": [True, 1, True, 1], "v": [1, 2, 3, 4]}).secondary_yaxis(
        "Categories"
    )
    getattr(plot, kind)("c", "v", orient="h", axis="y2", order=[True], errorbar=None)
    axes = [axis for axis in plot.render().axes if axis.get_ylabel() == "Categories"]
    assert len(axes) == 1
    if kind == "barplot":
        assert len(axes[0].patches) == 1 and axes[0].patches[0].get_width() == 2
    else:
        np.testing.assert_array_equal(axes[0].lines[0].get_xdata(), [2])


@pytest.mark.parametrize("new", ["weighted_median", "axis_only", "roles"])
def test_NEW_selected_row_bound_does_not_drop_source_observations(new):
    columns = {
        "c": ["A"] * 10001,
        "v": [1] * 10001,
        "w": [1] * 10001,
        "h": ["A"] * 10001,
    }
    plot = mp.plot(columns)
    if new == "axis_only":
        plot.secondary_yaxis("Categories").barplot(
            "c", "v", axis="y2", orient="h", errorbar=None
        )
    elif new == "roles":
        plot.barplot("c", "v", hue="h", errorbar=None)
    else:
        plot.barplot("c", "v", weights="w", estimator="median", errorbar=None)
    before = plot.to_json()
    with pytest.raises(ValueError):
        plot.render()
    assert plot.to_json() == before


def test_NEW_pointwise_cell_bound_is_not_an_old_dense_line_bound():
    columns = {"x": list(range(257)), "v": [1] * 257, "w": [1] * 257}
    new = mp.plot(columns).lineplot(
        "x", "v", weights="w", estimator="median", errorbar=None
    )
    with pytest.raises(ValueError):
        new.render()
    old = mp.plot(columns).lineplot("x", "v", weights="w", errorbar=None)
    np.testing.assert_array_equal(
        old.render().axes[0].lines[0].get_xdata(), columns["x"]
    )
    semantic = mp.plot({**columns, "h": ["A"] * 257}).lineplot(
        "x", "v", hue="h", errorbar=None
    )
    lines = [line for line in semantic.render().axes[0].lines if len(line.get_xdata())]
    assert len(lines) == 1 and len(lines[0].get_xdata()) == 257


@pytest.mark.parametrize("method", [None, "ci"])
def test_old_weighted_mean_admits_more_than_NEW_row_budget(method):
    columns = {
        "c": ["A"] * 10001,
        "v": [1] * 10001,
        "w": [1] * 10001,
        "u": ["one"] * 10001,
    }
    plot = mp.plot(columns).barplot(
        "c", "v", weights="w", errorbar=method, units="u" if method else None, n_boot=1
    )
    if method:
        with pytest.warns(UserWarning):
            figure = plot.render()
    else:
        figure = plot.render()
    assert figure.axes[0].patches[0].get_height() == 1


@pytest.mark.parametrize("hierarchical", [False, True])
def test_NEW_actual_work_failure_is_whole_editor_transaction(monkeypatch, hierarchical):
    from dashboard.editor_server import EditorSession
    from mudplot import _estimate

    monkeypatch.setattr(_estimate, "MAX_RESAMPLING_WORK", 45)
    columns = {
        "c": ["A"] * 4,
        "v": [1, 3, 5, 9],
        "w": [1, 2, 1, 3],
        "u": ["a", "a", "a", "b"],
    }
    plot = mp.plot(columns).pointplot(
        "c",
        "v",
        weights="w",
        estimator="median",
        errorbar="ci",
        units="u" if hierarchical else None,
        n_boot=2,
        seed=7,
    )
    session = EditorSession()
    session.load_spec(plot.to_json())
    accepted = (mp.to_json(session.store.state), session.png, session.action_log())
    layer = copy.deepcopy(plot.spec.panels[0].layers[0])
    layer.stat.n_boot = 20
    session.dispatch_safe(mp.actions.ReplaceLayer(0, layer))
    assert session.error is not None
    assert (
        mp.to_json(session.store.state),
        session.png,
        session.action_log(),
    ) == accepted
    session.undo()
    session.redo()
    assert mp.to_json(session.store.state) == accepted[0] and session.png == accepted[1]


@pytest.mark.parametrize(
    "options",
    [
        {"estimator": "median", "errorbar": "se", "weights": "w"},
        {"estimator": "sum", "errorbar": "sd", "weights": "w"},
        {"estimator": "count", "errorbar": "ci", "weights": "w"},
        {"errorbar": "se", "units": "u", "weights": "w"},
    ],
)
def test_named_unsupported_inference_is_rejected_without_mean_SE_fallback(options):
    plot = mp.plot(
        {"c": ["A"] * 3, "v": [1, 2, 3], "w": [1, 2, 1], "u": ["a", "b", "c"]}
    ).pointplot("c", "v", **options)
    with pytest.raises(ValueError):
        plot.render()


@pytest.mark.parametrize("kind", ["barplot", "pointplot", "lineplot"])
@pytest.mark.parametrize("method,level", [("sd", 1), ("se", 1), ("pi", 50)])
def test_unweighted_canonical_interval_does_not_round_endpoints_before_statistics(
    kind, method, level
):
    base = 2**53
    values = [base + 1, base + 10]
    _, figure = figure_for(kind, values, errorbar=(method, level))
    if method == "pi":
        expected = [
            float(
                Fraction(values[0]) * Fraction(3, 4)
                + Fraction(values[1]) * Fraction(1, 4)
            ),
            float(
                Fraction(values[0]) * Fraction(1, 4)
                + Fraction(values[1]) * Fraction(3, 4)
            ),
        ]
    else:
        with localcontext() as context:
            context.prec = 100
            mu = (Decimal(values[0]) + Decimal(values[1])) / 2
            variance = Decimal(81) / 2
            spread = (variance / (2 if method == "se" else 1)).sqrt()
            expected = [float(mu - spread), float(mu + spread)]
    np.testing.assert_array_equal(endpoints(figure.axes[0]), [expected])


@pytest.mark.parametrize("weighted", [False, True])
def test_legacy_mixed_unit_sizes_stream_with_seeded_CI_and_no_new_work_cap(
    monkeypatch, weighted
):
    from mudplot import _estimate

    values = [1, 3, 4, 7, 9, 11, 15, 2, 8, 13, 17, 6, 10, 14, 18, 21]
    weights = [1 + i % 3 for i in range(len(values))]
    units = ["a"] * 7 + ["b"] * 3 + ["c"] + ["d"] * 5
    groups = [
        np.array(range(7)),
        np.array(range(7, 10)),
        np.array([10]),
        np.array(range(11, 16)),
    ]
    rng = np.random.default_rng(43)
    replicates = []
    for _ in range(31):
        chosen = rng.integers(0, 4, size=4)
        rows = np.concatenate(
            [
                groups[index][
                    rng.integers(0, len(groups[index]), size=len(groups[index]))
                ]
                for index in chosen
            ]
        )
        replicates.append(
            reference(
                [values[i] for i in rows],
                [weights[i] if weighted else 1 for i in rows],
                "mean",
            )
        )
    expected = np.quantile(replicates, [0.1, 0.9], method="linear")
    plot = mp.plot({"c": ["A"] * 16, "v": values, "w": weights, "u": units}).pointplot(
        "c",
        "v",
        weights="w" if weighted else None,
        units="u",
        errorbar=("ci", 80),
        n_boot=31,
        seed=43,
    )
    before = np.random.get_state()
    normal = endpoints(plot.render().axes[0])
    monkeypatch.setattr(_estimate, "MAX_ACTIVE_SAMPLE_ELEMENTS", 5)
    monkeypatch.setattr(_estimate, "MAX_RESAMPLING_WORK", 0)
    streamed = endpoints(plot.render().axes[0])
    after = np.random.get_state()
    np.testing.assert_allclose(normal, [expected], rtol=2e-15, atol=0)
    np.testing.assert_array_equal(streamed, normal)
    assert before[0] == after[0] and before[2:] == after[2:]
    np.testing.assert_array_equal(before[1], after[1])


def test_strict_PI_precision_rejects_but_true_atom_retains_center():
    base = 2**53
    impossible = mp.plot({"c": ["A"] * 2, "v": [base + 1, base + 2]}).pointplot(
        "c", "v", errorbar=("pi", 50)
    )
    with pytest.raises(ValueError):
        impossible.render()
    atom = mp.plot({"c": ["A"] * 2, "v": [base + 2, base + 2]}).pointplot(
        "c", "v", errorbar=("pi", 50)
    )
    axis = atom.render().axes[0]
    np.testing.assert_array_equal(endpoints(axis), [[base + 2, base + 2]])
    np.testing.assert_array_equal(axis.lines[0].get_ydata(), [base + 2])


@pytest.mark.parametrize("kind", ["barplot", "pointplot"])
@pytest.mark.parametrize(
    "orient,axis", [("v", "y"), ("v", "y2"), ("h", "y"), ("h", "y2")]
)
@pytest.mark.parametrize("stat_scale", ["data", "axis"])
def test_declared_calendar_category_and_log_measurement_use_actual_targets(
    kind, orient, axis, stat_scale
):
    from datetime import UTC, datetime

    dates = ["2026-01-01"] * 3 + ["2026-01-04"] * 3
    plot = mp.plot({"c": dates, "v": [1, 4, 9] * 2, "w": [1, 3, 2] * 2})
    if axis == "y2":
        plot.secondary_yaxis("Target")
    category_axis = "x" if orient == "v" else axis
    measurement_axis = axis if orient == "v" else "x"
    plot.date_axis(category_axis, timezone="UTC")
    plot.axis_scale(measurement_axis, "log", options={"base": 2})
    options = {
        "weights": "w",
        "estimator": "median",
        "errorbar": None,
        "orient": orient,
        "axis": axis,
        "stat_scale": stat_scale,
    }
    if kind == "barplot":
        options["baseline"] = 0.5
    getattr(plot, kind)("c", "v", **options)
    before = plot.to_json()
    figure = plot.render()
    target = (
        figure.axes[0]
        if axis == "y"
        else next(a for a in figure.axes if a.get_ylabel() == "Target")
    )
    days = [
        (
            datetime(2026, 1, day, tzinfo=UTC) - datetime(1970, 1, 1, tzinfo=UTC)
        ).total_seconds()
        / 86400
        for day in (1, 4)
    ]
    if kind == "barplot":
        bodies = target.patches
        categories = [
            b.get_y() + b.get_height() / 2
            if orient == "h"
            else b.get_x() + b.get_width() / 2
            for b in bodies
        ]
        values = [
            b.get_x() + b.get_width() if orient == "h" else b.get_y() + b.get_height()
            for b in bodies
        ]
    else:
        line = target.lines[0]
        categories = line.get_ydata() if orient == "h" else line.get_xdata()
        values = line.get_xdata() if orient == "h" else line.get_ydata()
    np.testing.assert_allclose(categories, days, rtol=0, atol=1e-10)
    np.testing.assert_allclose(values, [4, 4], rtol=2e-15, atol=0)
    assert (target.get_xscale() if orient == "h" else target.get_yscale()) == "log"
    limits = target.dataLim.intervaly if orient == "h" else target.dataLim.intervalx
    np.testing.assert_allclose(
        limits, [days[0] - 1.5, days[1] + 1.5], rtol=0, atol=1e-10
    )
    assert plot.to_json() == before


def test_shared_raw_domains_keep_bar_outline_point_diameter_and_curve_stroke_distinct():
    data = {
        "c": [10, 20] * 1000,
        "v": [1, 3, 2, 4] * 500,
        "h": [0, 0, 1, 1] * 500,
        "s": [0, 0, 2, 2] * 500,
        "method": ["A", "A", "B", "B"] * 500,
        "id": list(range(2000)),
    }
    semantics = {
        "scale_id": "same-original-rows",
        "hue": "h",
        "hue_kind": "numeric",
        "hue_norm": [-1, 2],
        "size": "s",
        "size_norm": [0, 2],
        "sizes": [2, 4],
        "style": "method",
        "markers": ["D", "^"],
    }
    plot = (
        mp.plot(data)
        .secondary_yaxis("Other response")
        .barplot(
            "c", "v", semantics=semantics, native_scale=True, errorbar=None, alpha=0.3
        )
    )
    plot.pointplot(
        "c",
        "v",
        semantics=semantics,
        native_scale=True,
        errorbar=None,
        axis="y2",
        colorbar=True,
    )
    plot.lineplot("c", "v", semantics=semantics, errorbar=None)
    figure = plot.render()
    primary = figure.axes[0]
    secondary = next(a for a in figure.axes if a.get_ylabel() == "Other response")
    assert len(figure.axes) == 3
    body = [
        p
        for p in primary.patches
        if p.get_data_transform().contains_branch(primary.transData)
    ]
    assert len(body) == 4 and sorted(p.get_linewidth() for p in body) == [2, 2, 4, 4]
    points = [line for line in secondary.lines if len(line.get_xdata())]
    curves = [line for line in primary.lines if len(line.get_xdata())]
    assert sorted(line.get_markersize() for line in points) == [2, 4]
    assert sorted(line.get_linewidth() for line in curves) == [2, 4]
    np.testing.assert_allclose(
        primary.get_position().bounds, secondary.get_position().bounds, atol=1e-12
    )
    assert plot.spec.data.columns == data


def live_heights(plot):
    figure = plot.render()
    return [
        [
            patch.get_height()
            for patch in axis.patches
            if patch.get_data_transform().contains_branch(axis.transData)
        ]
        for axis in figure.axes
    ]


def test_live_statistical_template_is_explicit_preserves_typed_slots_and_overrides():
    data = {
        "c": [True, True, 1, 1] * 2,
        "v": [1, 3, 4, 8, 2, 6, 8, 16],
        "w": [1, 2, 1, 2] * 2,
        "s": [1] * 8,
        "cell": ["left"] * 4 + ["right"] * 4,
        "id": list(range(8)),
    }
    plot = mp.plot(data).barplot(
        "c",
        "v",
        weights="w",
        estimator="median",
        semantics={"size": "s", "size_norm": [0, 2], "sizes": [1, 3]},
        errorbar=None,
    )
    plot.facet(
        col="cell", col_order=["left", "empty", "right"], col_wrap=2, live=True
    ).layout(2, 2, width_ratios=[2, 1])
    initial = plot.to_json()
    assert live_heights(plot) == [[3, 8], [], [6, 16]]
    layer = copy.deepcopy(plot.spec.panels[0].layers[0])
    layer.stat.estimator = "min"
    plot.dispatch(mp.actions.ReplaceLayer(0, layer, panel=0))
    local = plot.to_json()
    assert live_heights(plot) == [[1, 4], [], [6, 16]]
    recipe = copy.deepcopy(plot.spec.facet_template.template)
    recipe.layers[0].stat.estimator = "mean"
    plot.facet_template(recipe)
    replaced = plot.to_json()
    np.testing.assert_allclose(live_heights(plot)[0], [7 / 3, 20 / 3], rtol=2e-15)
    np.testing.assert_allclose(live_heights(plot)[2], [14 / 3, 40 / 3], rtol=2e-15)
    assert live_heights(plot)[1] == []
    assert len(plot.spec.panels) == 3 and plot.spec.width_ratios == [2, 1]
    assert plot.spec.facet_template.template.layers[0].order == [True, 1]
    plot.store.undo()
    assert plot.to_json() == local and live_heights(plot) == [[1, 4], [], [6, 16]]
    plot.store.redo()
    assert plot.to_json() == replaced
    reopened = mp.Plot.from_json(replaced)
    assert reopened.to_json() == replaced
    recipe = copy.deepcopy(reopened.spec.facet_template.template)
    recipe.layers[0].stat.estimator = "max"
    reopened.facet_template(recipe)
    assert live_heights(reopened) == [[3, 8], [], [6, 16]]
    assert reopened.spec.data.columns == data
    plot.store.undo()
    plot.store.undo()
    assert plot.to_json() == initial


def test_new_facet_views_do_not_count_undrawn_macro_or_excluded_invalid_rows():
    count = 10000
    data = {
        "c": ["A"] * (2 * count + 1),
        "v": [1] * count + [2] * count + ["not a selected observation"],
        "w": [1] * (2 * count + 1),
        "cell": ["left"] * count + ["right"] * count + ["excluded"],
        "id": list(range(2 * count + 1)),
    }
    plot = mp.plot(data).pointplot(
        "c", "v", weights="w", estimator="median", errorbar=None
    )
    plot.facet(col="cell", col_order=["left", "right", "empty"], live=True)
    figure = plot.render()
    actual = [
        [
            float(v)
            for line in axis.lines
            for v in line.get_ydata()
            if len(line.get_ydata())
        ]
        for axis in figure.axes
    ]
    assert actual == [[1], [2], []]
    assert plot.spec.data.columns == data
    assert len(plot.spec.panels) == 3 and plot.spec.facet_template.col_order == [
        "left",
        "right",
        "empty",
    ]


def test_boxen_secondary_fixed_views_local_and_whole_recipe_keep_real_native_rows():
    import matplotlib.pyplot as plt

    data = {
        "c": ["A"] * 6 + ["B"] * 6,
        "v": [1, 2, 4, 2, 4, 8, 2, 4, 8, 4, 8, 16],
        "w": [1, 2, 1] * 4,
        "cell": ["left"] * 3 + ["right"] * 3 + ["left"] * 3 + ["right"] * 3,
        "id": list(range(12)),
    }
    plot = (
        mp.plot(data)
        .secondary_yaxis("Boxen response")
        .boxenplot("c", "v", weights="w", axis="y2", k_depth=1)
    )
    plot.facet(col="cell", col_order=["left", "empty", "right"], col_wrap=2, live=True)

    def medians(view):
        figure = view.render()
        try:
            axes = [a for a in figure.axes if a.get_ylabel() == "Boxen response"]
            assert len(axes) == 3
            return [
                [
                    float(np.asarray(line.get_ydata())[0])
                    for line in a.lines
                    if line.get_marker() == "None"
                ]
                for a in axes
            ]
        finally:
            plt.close(figure)

    initial = plot.to_json()
    assert medians(plot) == [[2, 4], [], [4, 8]]
    selectors = [dict(panel.filters) for panel in plot.spec.panels]
    local = copy.deepcopy(plot.spec.panels[0].layers[0])
    local.showmedians = False
    plot.dispatch(mp.actions.ReplaceLayer(0, local, panel=0))
    local_json = plot.to_json()
    assert medians(plot) == [[], [], [4, 8]]
    recipe = copy.deepcopy(plot.spec.facet_template.template)
    recipe.layers[0].showmedians = True
    plot.facet_template(recipe)
    whole = plot.to_json()
    assert medians(plot) == [[2, 4], [], [4, 8]]
    plot.store.undo()
    assert plot.to_json() == local_json and medians(plot) == [[], [], [4, 8]]
    plot.store.redo()
    assert plot.to_json() == whole
    reopened = mp.Plot.from_json(whole)
    assert medians(reopened) == [[2, 4], [], [4, 8]]
    assert [dict(panel.filters) for panel in reopened.spec.panels] == selectors
    assert reopened.spec.data.columns == data
    plot.store.undo()
    plot.store.undo()
    assert plot.to_json() == initial


@pytest.mark.parametrize("kind", ["barplot", "pointplot"])
def test_legacy_typed_hues_keep_reserved_slots_with_independent_size_and_style(kind):
    data = {
        "c": ["A"] * 6 + ["B"] * 6,
        "h": ([True] * 3 + [1] * 3) * 2,
        "v": [1, 2, 4, 3, 6, 12, 2, 4, 8, 6, 12, 24],
        "w": [1, 38, 1] * 4,
        "s": ([1] * 3 + [3] * 3) * 2,
        "d": (["First"] * 3 + ["Second"] * 3) * 2,
        "id": list(range(12)),
    }
    plot = mp.plot(data)
    getattr(plot, kind)(
        "c",
        "v",
        group="h",
        hue_order=["reserved", True, 1],
        weights="w",
        estimator="median",
        errorbar=("pi", 95),
        semantics={
            "size": "s",
            "sizes": [2, 4],
            "style": "d",
            "markers": ["D", "^"],
            "dashes": ["--", ":"],
        },
    )
    figure = plot.render()
    axis = figure.axes[0]
    if kind == "barplot":
        marks = [
            patch
            for patch in axis.patches
            if patch.get_data_transform().contains_branch(axis.transData)
        ]
        np.testing.assert_array_equal(
            [patch.get_height() for patch in marks], [2, 4, 6, 12]
        )
        np.testing.assert_allclose(
            [patch.get_x() + patch.get_width() / 2 for patch in marks],
            [0, 1, 0.8 / 3, 1 + 0.8 / 3],
        )
        assert [patch.get_linewidth() for patch in marks] == [2, 2, 4, 4]
    else:
        marks = [
            line
            for line in axis.lines
            if len(line.get_ydata()) and line.get_marker() in ["D", "^"]
        ]
        np.testing.assert_array_equal(
            [line.get_ydata() for line in marks], [[2, 4], [6, 12]]
        )
        assert [line.get_markersize() for line in marks] == [2, 4]
        assert [line.get_linewidth() for line in marks] == [1.25, 1.25]
    intervals = [
        segment[:, 1]
        for collection in axis.collections
        if isinstance(collection, LineCollection)
        for segment in collection.get_segments()
    ]
    np.testing.assert_array_equal(intervals, [[1, 2], [2, 4], [3, 6], [6, 12]])
    assert mp.Plot.from_json(plot.to_json()).spec.data.columns == data


@pytest.mark.parametrize(
    "kind,attribute,value",
    [
        ("barplot", "color", "#ff0000"),
        ("barplot", "line_width", 3),
        ("barplot", "line_style", "--"),
        ("pointplot", "color", "#ff0000"),
        ("pointplot", "marker_size", 3),
        ("pointplot", "line_style", "--"),
        ("pointplot", "marker", "x"),
    ],
)
def test_owned_statistical_roles_reject_real_live_cell_edits_atomically(
    kind, attribute, value
):
    from dashboard.editor_server import EditorSession

    data = {
        "c": ["A"] * 4,
        "v": [1, 3, 5, 9],
        "w": [1, 2, 1, 3],
        "h": [True, True, 1, 1],
        "s": [1, 1, 3, 3],
        "d": ["First", "First", "Second", "Second"],
        "cell": ["left", "left", "right", "right"],
        "id": list(range(4)),
    }
    plot = mp.plot(data).size(15, 5)
    getattr(plot, kind)(
        "c",
        "v",
        weights="w",
        estimator="median",
        errorbar=None,
        semantics={"hue": "h", "size": "s", "style": "d"},
    )
    plot.facet(col="cell", col_order=["left", "empty", "right"], live=True)
    session = EditorSession()
    session.load_spec(plot.to_json())
    accepted = (
        mp.to_json(session.store.state),
        session.png,
        session.action_log(),
        copy.deepcopy(session.store.history),
    )
    layer = copy.deepcopy(plot.spec.panels[0].layers[0])
    setattr(layer, attribute, value)
    candidate = copy.deepcopy(plot.spec)
    candidate.panels[0].layers[0] = layer
    reopened = mp.from_json(mp.to_json(candidate))
    with pytest.raises(ValueError):
        mp.render(reopened)
    session.dispatch_safe(mp.actions.ReplaceLayer(0, layer, panel=0))
    assert session.error is not None
    assert (
        mp.to_json(session.store.state),
        session.png,
        session.action_log(),
        session.store.history,
    ) == accepted
    session.undo()
    session.redo()
    assert mp.to_json(session.store.state) == accepted[0] and session.png == accepted[1]


@pytest.mark.parametrize("stroke", [0, 3])
def test_point_diameter_mapping_keeps_independently_requested_connecting_stroke(stroke):
    plot = mp.plot(
        {
            "c": ["A"] * 4,
            "v": [1, 3, 5, 9],
            "w": [1, 2, 1, 3],
            "s": [1, 1, 3, 3],
            "d": ["First", "First", "Second", "Second"],
        }
    ).pointplot(
        "c",
        "v",
        weights="w",
        estimator="median",
        errorbar=("pi", 95),
        line_width=stroke,
        error_line_width=0.75,
        semantics={
            "size": "s",
            "sizes": [2, 4],
            "style": "d",
            "markers": ["D", "^"],
            "dashes": ["--", ":"],
        },
    )
    reopened = mp.Plot.from_json(plot.to_json())
    figure = reopened.render()
    axis = figure.axes[0]
    marks = [
        line
        for line in axis.lines
        if len(line.get_ydata()) and line.get_marker() in ["D", "^"]
    ]
    np.testing.assert_array_equal([line.get_ydata() for line in marks], [[3], [9]])
    assert [line.get_markersize() for line in marks] == [2, 4]
    assert all(line.get_linewidth() == stroke and line.get_visible() for line in marks)
    intervals = [item for item in axis.collections if isinstance(item, LineCollection)]
    np.testing.assert_array_equal(
        [segment[:, 1] for item in intervals for segment in item.get_segments()],
        [[1, 3], [5, 9]],
    )
    assert all(np.array_equal(item.get_linewidths(), [0.75]) for item in intervals)


@pytest.mark.parametrize("kind", ["barplot", "pointplot"])
@pytest.mark.parametrize("stroke", [0, 3, None])
def test_style_legend_handlers_inherit_actual_native_main_traits(kind, stroke):
    import matplotlib as mpl

    data = {
        "c": ["A"] * 4,
        "v": [1, 2, 3, 4],
        "d": ["First", "First", "Second", "Second"],
    }
    with mpl.rc_context({"patch.linewidth": 2.75}):
        plot = getattr(mp.plot(data), kind)(
            "c",
            "v",
            errorbar=None,
            line_width=stroke,
            semantics={"style": "d", "markers": ["D", "^"], "dashes": ["--", ":"]},
        )
        axis = plot.render().axes[0]
    marks = (
        [
            patch
            for patch in axis.patches
            if patch.get_data_transform().contains_branch(axis.transData)
        ]
        if kind == "barplot"
        else [line for line in axis.lines if len(line.get_ydata())]
    )
    handles = axis.get_legend().legend_handles
    assert len(marks) == len(handles) == 2
    for mark, guide in zip(marks, handles, strict=True):
        assert guide.get_linewidth() == mark.get_linewidth()
        assert guide.get_linestyle() == mark.get_linestyle()
        assert guide.get_visible() and mark.get_visible()
        if kind == "barplot":
            np.testing.assert_array_equal(guide.get_facecolor(), mark.get_facecolor())
            np.testing.assert_array_equal(guide.get_edgecolor(), mark.get_edgecolor())
            assert guide.get_facecolor()[3] > 0
        else:
            assert guide.get_marker() == mark.get_marker()
            assert guide.get_markersize() == mark.get_markersize()


@pytest.mark.parametrize("stroke", [0, 3])
def test_point_hue_and_diameter_guides_retain_independent_stroke_and_native_glyph(
    stroke,
):
    plot = mp.plot(
        {"c": ["A"] * 4, "v": [1, 2, 3, 4], "h": [True, True, 1, 1], "s": [1, 1, 3, 3]}
    ).pointplot(
        "c",
        "v",
        errorbar=None,
        line_width=stroke,
        line_style=":",
        marker="D",
        semantics={"hue": "h", "hue_order": [True, 1], "size": "s", "sizes": [2, 4]},
    )
    axis = plot.render().axes[0]
    marks = [line for line in axis.lines if len(line.get_ydata())]
    guides = axis.get_legend().legend_handles
    assert [mark.get_markersize() for mark in marks] == [2, 4]
    assert len(guides) == 5
    assert all(
        guide.get_linewidth() == mark.get_linewidth() == stroke
        for guide in guides
        for mark in marks
    )
    assert all(
        guide.get_marker() == mark.get_marker() == "D"
        for guide in guides
        for mark in marks
    )
    assert all(
        guide.get_linestyle() == mark.get_linestyle()
        for guide in guides
        for mark in marks
    )
    assert {guide.get_markersize() for guide in guides} == {2, 3, 4}


@pytest.mark.parametrize(
    "estimator,weighted,semantic",
    [("mean", False, False), ("median", True, False), ("mean", False, True)],
)
def test_opaque_unit_relabelling_retains_independent_hierarchical_ci_and_editor_replay(
    estimator, weighted, semantic
):
    from dashboard.editor_server import EditorSession

    values = [1, 3, 5, 9]
    weights = [1, 2, 1, 3] if weighted else [1] * 4
    data = {
        "c": ["A"] * 6,
        "v": [*values, 1e9, 2e9],
        "w": [1, 2, 1, 3, 7, 9],
        "empty_ids": ["", "", "A", "A", None, float("nan")],
        "other_ids": ["renamed", "renamed", "A", "A", None, float("nan")],
        "h": ["cohort"] * 6,
        "id": list(range(6)),
    }
    random = np.random.default_rng(7)
    replicas = []
    for _ in range(47):
        chosen = []
        for unit in random.integers(0, 2, size=2):
            rows = [[0, 1], [2, 3]][int(unit)]
            chosen.extend(rows[int(index)] for index in random.integers(0, 2, size=2))
        replicas.append(
            reference(
                [values[i] for i in chosen], [weights[i] for i in chosen], estimator
            )
        )
    tail = (1 - 0.95) / 2
    interval = np.quantile(replicas, [tail, 1 - tail])
    plots = []
    for units in ("other_ids", "empty_ids"):
        plot = mp.plot(data).pointplot(
            "c",
            "v",
            estimator=estimator,
            errorbar="ci",
            n_boot=47,
            seed=7,
            weights="w" if weighted else None,
            units=units,
            semantics={"hue": "h"} if semantic else None,
        )
        before = plot.to_json()
        axis = plot.render().axes[0]
        assert axis.lines[0].get_ydata()[0] == reference(values, weights, estimator)
        np.testing.assert_allclose(endpoints(axis), [interval], rtol=2e-15, atol=0)
        assert plot.to_json() == before
        plots.append(plot)
    session = EditorSession()
    session.load_spec(plots[0].to_json())
    before = mp.to_json(session.store.state), session.png
    layer = copy.deepcopy(plots[0].spec.panels[0].layers[0])
    assert layer.stat is not None
    layer.stat.units = "empty_ids"
    session.dispatch_safe(mp.actions.ReplaceLayer(0, layer))
    assert session.error is None and session.png == before[1]
    after = mp.to_json(session.store.state)
    reopened = mp.Plot.from_json(after)
    np.testing.assert_allclose(
        endpoints(reopened.render().axes[0]), [interval], rtol=2e-15, atol=0
    )
    session.undo()
    assert mp.to_json(session.store.state) == before[0] and session.png == before[1]
    session.redo()
    assert mp.to_json(session.store.state) == after and session.png == before[1]


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("other", ["weighted-mean", "raw-value", "weighted-total"])
def test_weighted_total_response_sharing_keeps_declared_units_and_legacy_gate(
    orient, other
):
    from dashboard.editor_server import EditorSession

    data = {"c": [1, 1, 2, 2], "v": [1, 3, 3, 5], "w": [1, 2, 1, 2]}
    plot = mp.plot(data).layout(1, 2).size(12, 5)
    plot.barplot(
        "c",
        "v",
        weights="w",
        estimator="sum",
        errorbar=None,
        native_scale=True,
        orient=orient,
    )
    if other == "raw-value":
        plot.scatter(
            "c" if orient == "v" else "v", "v" if orient == "v" else "c", panel=1
        )
    else:
        plot.pointplot(
            "c",
            "v",
            weights="w",
            errorbar=None,
            native_scale=True,
            estimator="sum" if other == "weighted-total" else "mean",
            orient=orient,
            panel=1,
        )
    response = "y" if orient == "v" else "x"
    unshared = plot.to_json()
    plot.share(**{response: "all"})
    legacy = plot.render().axes
    shared = (
        legacy[0].get_shared_y_axes()
        if orient == "v"
        else legacy[0].get_shared_x_axes()
    )
    assert shared.joined(legacy[0], legacy[1])
    explicit = mp.Plot.from_json(unshared).mosaic([["total", "other"]])
    session = EditorSession()
    session.load_spec(explicit.to_json())
    accepted = mp.to_json(session.store.state), session.png, session.action_log()
    action = mp.actions.SetShare(**{response: "all"})
    session.dispatch_safe(action)
    if other != "weighted-total":
        assert session.error is not None
        assert (
            mp.to_json(session.store.state),
            session.png,
            session.action_log(),
        ) == accepted
        with pytest.raises(ValueError):
            candidate = mp.Plot.from_json(explicit.to_json()).share(**{response: "all"})
            mp.Plot.from_json(candidate.to_json()).render()
    else:
        assert session.error is None
        reopened = mp.Plot.from_json(mp.to_json(session.store.state))
        axes = reopened.render().axes
        shared = (
            axes[0].get_shared_y_axes()
            if orient == "v"
            else axes[0].get_shared_x_axes()
        )
        assert shared.joined(axes[0], axes[1])
        values = (
            axes[0].patches[0].get_height()
            if orient == "v"
            else axes[0].patches[0].get_width()
        )
        assert values == 7


@pytest.mark.parametrize("kind", ["barplot", "pointplot"])
def test_editor_stroke_edit_reopen_and_history_keep_guides_equal_to_real_marks(kind):
    from dashboard.editor_server import EditorSession

    plot = mp.plot(
        {"c": ["A"] * 4, "v": [1, 2, 3, 4], "d": ["First", "First", "Second", "Second"]}
    ).size(8, 5)
    getattr(plot, kind)(
        "c",
        "v",
        errorbar=None,
        line_width=0,
        semantics={"style": "d", "markers": ["D", "^"], "dashes": ["--", ":"]},
    )
    session = EditorSession()
    session.load_spec(plot.to_json())
    before = mp.to_json(session.store.state), session.png
    layer = copy.deepcopy(plot.spec.panels[0].layers[0])
    layer.line_width = 3
    session.dispatch_safe(mp.actions.ReplaceLayer(0, layer))
    assert session.error is None and session.png != before[1]
    after = mp.to_json(session.store.state), session.png
    reopened = mp.Plot.from_json(after[0])
    axis = reopened.render().axes[0]
    marks = (
        [
            patch
            for patch in axis.patches
            if patch.get_data_transform().contains_branch(axis.transData)
        ]
        if kind == "barplot"
        else [line for line in axis.lines if len(line.get_ydata())]
    )
    handles = axis.get_legend().legend_handles
    for mark, guide in zip(marks, handles, strict=True):
        assert mark.get_linewidth() == guide.get_linewidth() == 3
        assert mark.get_linestyle() == guide.get_linestyle()
        if kind == "pointplot":
            assert mark.get_marker() == guide.get_marker()
        else:
            np.testing.assert_array_equal(mark.get_facecolor(), guide.get_facecolor())
    session.undo()
    assert (mp.to_json(session.store.state), session.png) == before
    session.redo()
    assert (mp.to_json(session.store.state), session.png) == after


def test_unweighted_sum_shares_explicit_value_axes_with_mean_and_raw_values():
    plot = mp.plot({"c": [1, 1, 2, 2], "v": [1, 3, 3, 5]}).layout(1, 3)
    plot.mosaic([["sum", "mean", "raw"]]).barplot(
        "c", "v", estimator="sum", errorbar=None, native_scale=True
    )
    plot.pointplot("c", "v", errorbar=None, native_scale=True, panel=1)
    plot.scatter("c", "v", panel=2).share(y="all")
    axes = plot.render().axes
    assert all(axes[0].get_shared_y_axes().joined(axes[0], axis) for axis in axes[1:])
    np.testing.assert_array_equal(
        [patch.get_height() for patch in axes[0].patches], [4, 8]
    )
    np.testing.assert_array_equal(axes[1].lines[0].get_ydata(), [2, 4])
