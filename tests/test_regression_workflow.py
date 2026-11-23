"""Independent regression equations, source-role geometry and atomic transitions."""

from __future__ import annotations

import copy
import math
from fractions import Fraction
from typing import Any, cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest


def rational_line(x, y, w, at):
    x, y, w = ([Fraction(v) for v in values] for values in (x, y, w))
    total = sum(w)
    first = sum(a * b for a, b in zip(w, x, strict=True))
    second = sum(a * b * b for a, b in zip(w, x, strict=True))
    response = sum(a * b for a, b in zip(w, y, strict=True))
    cross = sum(a * b * c for a, b, c in zip(w, x, y, strict=True))
    denominator = total * second - first * first
    slope = (total * cross - first * response) / denominator
    intercept = (response - slope * first) / total
    return [intercept + slope * Fraction(v) for v in at]


def type7(values, probability):
    values = sorted(Fraction(float(value)) for value in values)
    position = (len(values) - 1) * probability
    low = math.floor(position)
    fraction = position - low
    return (
        values[low]
        if not fraction
        else values[low] * (1 - fraction) + values[low + 1] * fraction
    )


def native_role(fig, role) -> list[Any]:
    return [
        artist
        for ax in fig.axes
        for artist in (*ax.lines, *ax.collections)
        if getattr(artist, "_mudplot_regression_role", None) == role
    ]


def source(n=64, query=0):
    x = np.linspace(-2, 2, n + query)
    return {
        "x": x.tolist(),
        "y": (1 + 2 * x + 0.13 * np.sin(np.arange(n + query) * 0.73)).tolist(),
        "w": (1 + np.arange(n + query) % 3).tolist(),
        "split": ["train"] * n + ["query"] * query,
        "id": [True, 1, "duplicate", "duplicate", *range(4, n + query)],
    }


def test_strict_appended_controls_copy_and_roundtrip():
    raw = source()
    config = {
        "bootstrap": {"n_boot": 7, "seed": 13},
        "components": {"scatter": {"marker_size": 4}, "fit": {"line_width": 2}},
    }
    plot = mp.plot(raw).regplot("x", "y", weights="w", confidence=95, regression=config)
    config["bootstrap"]["n_boot"] = 99
    restored = mp.Plot.from_json(plot.to_json())
    assert restored.spec.panels[0].layers[0].regression.bootstrap.n_boot == 7
    assert restored.spec.data.columns == raw
    assert type(restored.spec.data.columns["id"][0]) is bool
    assert type(restored.spec.data.columns["id"][1]) is int
    assert isinstance(
        restored.spec.panels[0].layers[0].regression.components.fit,
        mp.ComponentStyleSpec,
    )
    for invalid in (
        {"bootstrap": {"n_boot": True}},
        {"bootstrap": {"seed": True}},
        {"bootstrap": {"method": "percentile"}},
        {"confidence": 95},
        {"partial": {"columns": ["z"], "reference": {"other": 0}}},
    ):
        before = plot.to_json(), plot.action_log
        with pytest.raises((ValueError, TypeError)):
            plot.regplot("x", "y", confidence=95, regression=invalid)
        assert (plot.to_json(), plot.action_log) == before


@pytest.mark.parametrize(
    "orient,axis", [("v", "y"), ("h", "y"), ("v", "y2"), ("h", "y2")]
)
def test_paired_case_percentiles_match_independent_rational_native_query(orient, axis):
    raw = source(32, 16)
    plot = mp.plot(raw)
    if axis == "y2":
        plot = plot.secondary_yaxis("Response or predictor")
    plot = plot.regplot(
        "x",
        "y",
        weights="w",
        confidence=80,
        orient=orient,
        axis=axis,
        regression={
            "sampling": {"train": {"split": "train"}, "query": {"split": "query"}},
            "bootstrap": {"n_boot": 7, "seed": 13},
        },
    )
    before = plot.to_json()
    rng = np.random.Generator(np.random.PCG64(13))
    predictions = []
    for _ in range(7):
        train = rng.integers(0, 32, size=32, dtype=np.int64)
        rng.integers(0, 16, size=16, dtype=np.int64)
        predictions.append(
            rational_line(
                [raw["x"][int(i)] for i in train],
                [raw["y"][int(i)] for i in train],
                [raw["w"][int(i)] for i in train],
                raw["x"][32:],
            )
        )
    expected = np.asarray(
        [
            [
                float(type7([row[j] for row in predictions], p))
                for p in (Fraction(1, 10), Fraction(9, 10))
            ]
            for j in range(16)
        ]
    )
    fig = plot.render()
    try:
        query = native_role(fig, "query_mean_prediction")[0]
        predictor = query.get_ydata() if orient == "h" else query.get_xdata()
        np.testing.assert_array_equal(predictor, raw["x"][32:])
        assert query._mudplot_source_rows == tuple(range(32, 48))
        intervals = [
            collection
            for ax in fig.axes
            for collection in ax.collections
            if getattr(collection, "_mudplot_source_rows", None) == tuple(range(32, 48))
        ]
        segments = next(
            item.get_segments() for item in intervals if hasattr(item, "get_segments")
        )
        observed = np.asarray(
            [
                [
                    segment[0, 0 if orient == "h" else 1],
                    segment[1, 0 if orient == "h" else 1],
                ]
                for segment in segments
            ]
        )
        np.testing.assert_allclose(observed, expected, rtol=2e-12, atol=2e-12)
        assert plot.to_json() == before
    finally:
        plt.close(fig)


def test_explicit_query_response_missing_is_role_specific_and_source_retained():
    raw = source(32, 8)
    raw["y"][32:] = [None] * 8
    settings = {"sampling": {"train": {"split": "train"}, "query": {"split": "query"}}}
    plot = mp.plot(raw).regplot("x", "y", weights="w", regression=settings)
    fig = plot.render()
    try:
        assert len(native_role(fig, "query_mean_prediction")[0].get_xdata()) == 8
        assert plot.spec.data.columns == raw
    finally:
        plt.close(fig)
    invalid = mp.plot(raw).residplot("x", "y", weights="w", regression=settings)
    assert mp.validate(invalid.spec)


def test_empty_explicit_query_has_no_diagnostic_fit_or_random_work():
    raw = source()
    plot = mp.plot(raw).residplot(
        "x",
        "y",
        weights="w",
        confidence=95,
        regression={
            "sampling": {"train": {"split": "train"}, "query": {"split": "absent"}},
            "bootstrap": {"n_boot": 11, "seed": 7},
            "diagnostics": {"trend": {"model": "poly"}},
        },
    )
    fig = plot.render()
    try:
        assert not native_role(fig, "diagnostic")
        assert not native_role(fig, "mean_fit")
        assert not native_role(fig, "independent_residual_trend")
        assert cast(Any, fig)._mudplot_regression_work["logical_work_upper"] == 0
    finally:
        plt.close(fig)


def test_partial_conditional_and_adjusted_observations_match_complete_design():
    raw = source(64, 16)
    raw["z"] = np.cos(np.arange(80) * 0.73).tolist()
    raw["y"] = (
        1
        + 0.7 * np.asarray(raw["z"])
        + 2 * np.asarray(raw["x"])
        + 0.2 * np.asarray(raw["x"]) ** 2
    ).tolist()
    settings = {
        "partial": {"columns": ["z"], "reference": {"z": 0.3}},
        "sampling": {"train": {"split": "train"}, "query": {"split": "query"}},
    }
    plot = mp.plot(raw).regplot("x", "y", degree=2, weights="w", regression=settings)
    fig = plot.render()
    try:
        points = native_role(fig, "adjusted_observation")[0]
        expected = (
            1
            + 0.7 * 0.3
            + 2 * np.asarray(raw["x"][:64])
            + 0.2 * np.asarray(raw["x"][:64]) ** 2
        )
        np.testing.assert_allclose(
            np.asarray(points.get_offsets())[:, 1], expected, atol=1e-12
        )
        query = native_role(fig, "query_mean_prediction")[0]
        np.testing.assert_allclose(query.get_ydata(), raw["y"][64:], atol=1e-12)
        assert query._mudplot_source_rows == tuple(range(64, 80))
    finally:
        plt.close(fig)
    changed = copy.deepcopy(raw)
    changed["y"][64:] = [v + 100 for v in changed["y"][64:]]
    second = (
        mp.plot(changed)
        .regplot("x", "y", degree=2, weights="w", regression=settings)
        .render()
    )
    try:
        np.testing.assert_allclose(
            native_role(second, "query_mean_prediction")[0].get_ydata(),
            raw["y"][64:],
            atol=1e-12,
        )
    finally:
        plt.close(second)


@pytest.mark.parametrize("model", ["poly", "logx", "robust", "logistic", "lowess"])
def test_weighted_all_named_model_point_factory_is_independent_of_ci(model):
    pytest.importorskip("statsmodels")
    if model == "robust":
        x = np.linspace(-2, 2, 129)
        y = 1 + 2 * x + 0.12 * np.sin(np.arange(129) * 0.83)
        y[5] += 1
        y[101] -= 1
    elif model == "logistic":
        x = np.repeat(np.arange(-3, 4, dtype=float), 16)
        y = np.concatenate(
            [np.array([1.0] * n + [0.0] * (16 - n)) for n in [3, 4, 6, 8, 10, 12, 13]]
        )
    elif model == "lowess":
        x = np.linspace(-2, 2, 97)
        y = np.sin(x) + 0.05 * np.cos(np.arange(97) * 0.71)
        y[5] += 0.4
        y[81] -= 0.4
    else:
        x = np.linspace(-2, 2, 64)
        y = 1 + 2 * x + 0.1 * np.sin(np.arange(64))
        if model == "logx":
            x = np.exp(x)
    raw = {"x": x.tolist(), "y": y.tolist(), "w": (1 + np.arange(len(x)) % 3).tolist()}
    point = mp.plot(raw).regplot(
        "x",
        "y",
        weights="w",
        regression={"model": model, "components": {"scatter": {"marker_size": 3}}},
    )
    confidence = mp.plot(raw).regplot(
        "x",
        "y",
        weights="w",
        confidence=95,
        regression={"model": model, "bootstrap": {"n_boot": 19, "seed": 43}},
    )
    left, right = point.render(), confidence.render()
    try:
        np.testing.assert_array_equal(
            native_role(left, "mean_fit")[0].get_ydata(),
            native_role(right, "mean_fit")[0].get_ydata(),
        )
    finally:
        plt.close(left)
        plt.close(right)


def test_true_zero_and_near_atom_weighted_huber_are_not_epsilon_scale():
    from mudplot._regression_model import _huber

    x = np.linspace(-2, 2, 49)
    design = np.column_stack((np.ones(49), x))
    masses = (1 + np.arange(49) % 3).tolist()
    np.testing.assert_array_equal(
        _huber(design, np.zeros(49), masses, design), np.zeros(49)
    )
    response = (1 + 2 * x + 0.1 * np.sin(3 * x)) * 1e-100
    prediction = _huber(design, response, masses, design)
    assert np.isfinite(prediction).all() and np.max(np.abs(response - prediction)) > 0
    with pytest.raises(ValueError):
        _huber(
            np.column_stack((np.ones(3), [0.0, 1.0, 2.0])),
            np.array([0.0, 0.0, 3.0]),
            [10, 10, 1],
            np.array([[1.0, 0.5]]),
        )


def test_local_mass_erasure_and_rank_are_not_repaired():
    from mudplot._regression_model import weighted_solve

    design = np.column_stack((np.ones(3), [-1.0, 0.0, 1.0]))
    for masses in ([2.0, np.nextafter(0.0, 1.0), 2.0], [1.0, float("inf"), 1.0]):
        with pytest.raises(ValueError):
            weighted_solve(design, np.array([1.0, 2.0, 3.0]), masses)
    with pytest.raises(ValueError):
        weighted_solve(np.ones((3, 2)), np.array([1.0, 2.0, 3.0]), [1.0, 2.0, 1.0])


def test_full_residual_trend_does_not_replace_primary_or_change_source():
    raw = source(64, 24)
    base = {"sampling": {"train": {"split": "train"}, "query": {"split": "query"}}}
    plot = mp.plot(raw).residplot(
        "x",
        "y",
        weights="w",
        confidence=80,
        regression={
            **base,
            "bootstrap": {"n_boot": 7, "seed": 13},
            "diagnostics": {"kind": "raw", "trend": {"model": "poly"}},
        },
    )
    before = plot.to_json()
    fig = plot.render()
    try:
        points = native_role(fig, "diagnostic")[0]
        expected = np.asarray(raw["y"][64:]) - np.asarray(
            [
                float(v)
                for v in rational_line(
                    raw["x"][:64], raw["y"][:64], raw["w"][:64], raw["x"][64:]
                )
            ]
        )
        np.testing.assert_allclose(
            np.asarray(points.get_offsets())[:, 1], expected, atol=2e-12
        )
        assert points._mudplot_source_rows == tuple(range(64, 88))
        assert len(native_role(fig, "zero_reference")) == 1
        assert len(native_role(fig, "independent_residual_trend")) == 1
        assert not native_role(fig, "mean_fit")
        assert plot.to_json() == before
    finally:
        plt.close(fig)


def test_mathematical_deviance_endpoints_and_mapped_interval_noncommutation():
    from mudplot._regression_model import diagnostic

    np.testing.assert_array_equal(
        diagnostic([0, 1], [0, 1], "deviance", [3, 7]), [0, 0]
    )
    for y, p in ((0, 1), (1, 0)):
        with pytest.raises(ValueError) as error:
            diagnostic([y], [p], "deviance", [119])
        assert "119" in str(error.value)
    probability = [0.1, 0.4, 0.8]
    lo, hi = type7(probability, Fraction(1, 40)), type7(probability, Fraction(39, 40))
    mapped = [math.sqrt(-2 * math.log(float(hi))), math.sqrt(-2 * math.log(float(lo)))]
    transformed = [
        float(type7([math.sqrt(-2 * math.log(p)) for p in probability], q))
        for q in (Fraction(1, 40), Fraction(39, 40))
    ]
    assert not np.allclose(mapped, transformed, rtol=1e-5)


@pytest.mark.parametrize("orient,axis", [("v", "y"), ("h", "y2")])
def test_calendar_prediction_uses_actual_logical_predictor_axis(orient, axis):
    raw = source(32, 8)
    raw["date"] = [f"2026-01-{1 + i % 10:02d}" for i in range(40)]
    plot = mp.plot(raw)
    if axis == "y2":
        plot = plot.secondary_yaxis("UTC predictor")
    plot = plot.date_axis("y2" if orient == "h" else "x", timezone="UTC")
    plot = plot.regplot(
        "date",
        "y",
        weights="w",
        axis=axis,
        orient=orient,
        regression={
            "sampling": {"train": {"split": "train"}, "query": {"split": "query"}}
        },
    )
    before = plot.to_json()
    fig = plot.render()
    try:
        query = native_role(fig, "query_mean_prediction")[0]
        predictor = np.asarray(
            query.get_ydata() if orient == "h" else query.get_xdata()
        )
        assert np.min(predictor) > 20000 and np.ptp(predictor) == 7
        assert (
            plot.to_json() == before and plot.spec.data.columns["date"] == raw["date"]
        )
    finally:
        plt.close(fig)


def test_live_regression_cells_keep_ids_and_local_template_ownership():
    raw = source(64)
    raw["site"] = ["north"] * 32 + ["south"] * 32
    plot = (
        mp.plot(raw)
        .size(12, 8)
        .regplot(
            "x",
            "y",
            weights="w",
            confidence=80,
            regression={"bootstrap": {"n_boot": 7, "seed": 13}},
        )
        .facet(col="site", col_order=["north", "south", "empty"], live=True)
        .nest(2, 1, row=0, grid_id="outer")
    )
    ids = [panel.panel_id for panel in plot.spec.panels]
    plot.rename_panel(ids[1], "south-view").reorder_panels(
        ["south-view", ids[2], ids[0]]
    )
    geometry = {
        panel.filters["site"]: (panel.panel_id, panel.placement.to_dict())
        for panel in plot.spec.panels
    }
    north = next(
        i
        for i, panel in enumerate(plot.spec.panels)
        if panel.filters["site"] == "north"
    )
    plot.labels(title="Local title", panel=north)
    recipe = copy.deepcopy(plot.spec.facet_template)
    changed = copy.deepcopy(raw)
    changed["y"][0] += 0.3
    plot.dispatch(mp.actions.SetData(changed))
    assert plot.spec.facet_template == recipe
    assert plot.spec.panels[north].title == "Local title"
    template = copy.deepcopy(recipe.template)
    template.title = "Whole experiment"
    template.layers[0].regression.bootstrap.n_boot = 9
    plot.facet_template(template)
    committed = plot.to_json()
    plot.store.undo()
    assert plot.spec.facet_template == recipe
    assert plot.spec.panels[north].title == "Local title"
    plot.store.redo()
    assert plot.to_json() == committed
    assert {
        panel.filters["site"]: (panel.panel_id, panel.placement.to_dict())
        for panel in plot.spec.panels
    } == geometry
    restored = mp.Plot.from_json(committed)
    fig = restored.render()
    try:
        assert len(native_role(fig, "mean_fit")) == 2
        assert (
            cast(Any, fig)._mudplot_regression_work["components"]["case_choices"]
            == 9 * 64
        )
        assert restored.spec.data.columns == changed
    finally:
        plt.close(fig)


def test_invalid_full_layer_controls_are_atomic_through_existing_reducer():
    plot = mp.plot(source()).regplot(
        "x",
        "y",
        weights="w",
        confidence=80,
        regression={"bootstrap": {"n_boot": 7, "seed": 13}},
    )
    before = plot.to_json(), plot.action_log
    replacement = copy.deepcopy(plot.spec.panels[0].layers[0])
    replacement.regression.bootstrap.n_boot = 0
    with pytest.raises(ValueError):
        plot.dispatch(mp.actions.ReplaceLayer(0, replacement))
    assert (plot.to_json(), plot.action_log) == before
    replacement.regression.bootstrap.n_boot = 9
    plot.dispatch(mp.actions.ReplaceLayer(0, replacement))
    assert plot.spec.panels[0].layers[0].regression.bootstrap.n_boot == 9
    plot.store.undo()
    assert plot.to_json() == before[0]


def test_independent_native_component_effects_keep_source_and_experiment():
    raw = source()
    plot = mp.plot(raw).regplot(
        "x",
        "y",
        weights="w",
        confidence=80,
        label="Original observations",
        regression={
            "bootstrap": {"n_boot": 7, "seed": 13},
            "components": {
                "fit": {
                    "color": "#075985",
                    "line_width": 0,
                    "marker": "s",
                    "marker_size": 5,
                },
                "scatter": {
                    "face_color": "#fbbf24",
                    "edge_color": "#7c2d12",
                    "marker_size": 4,
                    "marker_edge_width": 2,
                },
            },
        },
    )
    before = plot.to_json()
    fig = plot.render()
    try:
        fit = native_role(fig, "mean_fit")[0]
        observations = native_role(fig, "observation")[0]
        assert fit.get_linewidth() == 0
        assert fit.get_marker() == "s" and fit.get_markersize() == 5
        np.testing.assert_array_equal(observations.get_sizes(), [16])
        np.testing.assert_array_equal(observations.get_linewidths(), [2])
        np.testing.assert_allclose(
            observations.get_facecolors()[0, :3],
            matplotlib.colors.to_rgb("#fbbf24"),
        )
        assert plot.to_json() == before
        assert observations._mudplot_source_rows == tuple(range(64))
    finally:
        plt.close(fig)


def test_real_infinite_query_deviance_retains_previous_native_file(tmp_path):
    pytest.importorskip("statsmodels")
    n = 119
    raw = {
        "x": [float(i % 3 - 1) for i in range(n)] + [0.0],
        "y": [int(i % 7 < (2 if i % 3 == 0 else 5)) for i in range(n)] + [0],
        "split": ["train"] * n + ["query"],
    }
    config = {
        "model": "logistic",
        "sampling": {"train": {"split": "train"}, "query": {"split": "query"}},
        "diagnostics": {"kind": "deviance"},
    }
    plot = mp.plot(raw).residplot("x", "y", regression=config)
    output = tmp_path / "diagnostic.png"
    plot.save(output)
    previous = output.read_bytes()
    changed = copy.deepcopy(raw)
    changed["x"][-1] = 1e6
    invalid = mp.plot(changed).residplot("x", "y", regression=config)
    with pytest.raises(ValueError) as error:
        invalid.save(output)
    assert "119" in str(error.value)
    assert output.read_bytes() == previous


def test_actual_integer_response_is_not_rounded_to_a_fake_zero_residual():
    from mudplot._regression_model import affine_response, diagnostic

    observed = 2**60 + 1
    mean = float(2**60)
    np.testing.assert_array_equal(diagnostic([observed], [mean], "raw", [119]), [1.0])
    np.testing.assert_array_equal(
        affine_response([observed], np.array([mean]), [119], reference=np.array([3.0])),
        [4.0],
    )


def test_borrowed_source_values_do_not_change_numerical_admission():
    from matplotlib.collections import PolyCollection

    raw = source(128)
    shared = "borrowed" + "s" * (2 * 1024 * 1024)
    geometry = []
    for extra in (False, True):
        columns = {**raw}
        if extra:
            columns["unused"] = [shared] * 128
        plot = mp.plot(columns).regplot(
            "x",
            "y",
            weights="w",
            confidence=80,
            regression={"bootstrap": {"n_boot": 1, "seed": 13}},
        )
        fig = plot.render()
        try:
            fit = native_role(fig, "mean_fit")[0]
            bands = [
                artist
                for artist in fig.axes[0].collections
                if isinstance(artist, PolyCollection)
            ]
            geometry.append(
                (
                    np.asarray(fit.get_xdata()).copy(),
                    np.asarray(fit.get_ydata()).copy(),
                    [
                        path.vertices.copy()
                        for band in bands
                        for path in band.get_paths()
                    ],
                    np.asarray(native_role(fig, "observation")[0].get_offsets()).copy(),
                )
            )
            assert plot.spec.data.columns == columns
            assert type(plot.spec.data.columns["id"][0]) is bool
            assert type(plot.spec.data.columns["id"][1]) is int
        finally:
            plt.close(fig)
    for index in (0, 1, 3):
        np.testing.assert_array_equal(geometry[0][index], geometry[1][index])
    assert geometry[0][2] and len(geometry[0][2]) == len(geometry[1][2])
    for before, after in zip(geometry[0][2], geometry[1][2], strict=True):
        np.testing.assert_array_equal(before, after)


@pytest.mark.parametrize("display_order", [["A", "B"], ["B", "A"]])
def test_bootstrap_group_order_uses_first_positive_original_role(display_order):
    from matplotlib.collections import LineCollection, PolyCollection

    rows = [("A", "train", 99, 999, 0), ("B", "query", 11.5, None, 1)]
    for index in range(5):
        rows.extend(
            [
                ("A", "train", index, 1 + 2 * index + 0.2 * math.sin(index), 1),
                ("B", "train", 10 + index, 3 + 0.5 * index + 0.25 * math.cos(index), 1),
            ]
        )
    rows.extend(
        [
            ("B", "train", 15, 5.5 + 0.25 * math.cos(5), 1),
            ("B", "train", 16, 6 + 0.25 * math.cos(6), 1),
            ("A", "query", 0.5, None, 1),
            ("B", "query", 12.5, None, 1),
            ("A", "query", 3.5, None, 1),
            ("B", "query", 14.5, None, 1),
        ]
    )
    raw = {
        name: [row[index] for row in rows]
        for index, name in enumerate(("group", "split", "x", "y", "w"))
    }
    plot = mp.plot(raw).regplot(
        "x",
        "y",
        group="group",
        weights="w",
        hue_order=display_order,
        confidence=80,
        regression={
            "bootstrap": {"n_boot": 3, "seed": 13},
            "sampling": {"train": {"split": "train"}, "query": {"split": "query"}},
        },
    )
    fig = plot.render()
    try:
        fits = {
            "A" if np.min(artist.get_xdata()) < 10 else "B": artist
            for artist in native_role(fig, "mean_fit")
        }
        queries = {
            "A" if np.min(artist.get_xdata()) < 10 else "B": artist
            for artist in native_role(fig, "query_mean_prediction")
        }
        training = {
            group: [
                row
                for row in rows
                if row[0] == group and row[1] == "train" and row[4] > 0
            ]
            for group in ("A", "B")
        }
        query_rows = {
            group: [
                index
                for index, row in enumerate(rows)
                if row[0] == group and row[1] == "query" and row[4] > 0
            ]
            for group in ("A", "B")
        }
        targets = {
            group: [*fits[group].get_xdata(), *queries[group].get_xdata()]
            for group in ("A", "B")
        }
        sampled = {"A": [], "B": []}
        rng = np.random.Generator(np.random.PCG64(13))
        for _replicate in range(3):
            for group in ("B", "A"):
                cases = training[group]
                indices = rng.integers(0, len(cases), size=len(cases), dtype=np.int64)
                selected = [cases[int(index)] for index in indices]
                sampled[group].append(
                    rational_line(
                        [row[2] for row in selected],
                        [row[3] for row in selected],
                        [row[4] for row in selected],
                        targets[group],
                    )
                )
                count = len(query_rows[group])
                rng.integers(0, count, size=count, dtype=np.int64)
        for group in ("A", "B"):
            cases = training[group]
            center = rational_line(
                [row[2] for row in cases],
                [row[3] for row in cases],
                [row[4] for row in cases],
                targets[group],
            )
            fit_count = len(fits[group].get_xdata())
            np.testing.assert_allclose(
                fits[group].get_ydata(), [float(value) for value in center[:fit_count]]
            )
            np.testing.assert_allclose(
                queries[group].get_ydata(),
                [float(value) for value in center[fit_count:]],
            )
            lower = [
                float(type7(values, Fraction(1, 10)))
                for values in zip(*sampled[group], strict=True)
            ]
            upper = [
                float(type7(values, Fraction(9, 10)))
                for values in zip(*sampled[group], strict=True)
            ]
            band = next(
                artist
                for artist in fig.axes[0].collections
                if isinstance(artist, PolyCollection)
                and (
                    (np.min(artist.get_paths()[0].vertices[:, 0]) < 10)
                    == (group == "A")
                )
            )
            vertices = np.concatenate([path.vertices for path in band.get_paths()])
            for index, predictor in enumerate(fits[group].get_xdata()):
                response = vertices[vertices[:, 0] == predictor, 1]
                np.testing.assert_allclose(
                    [response.min(), response.max()],
                    [lower[index], upper[index]],
                    rtol=1e-10,
                    atol=1e-10,
                )
            bars = next(
                artist
                for artist in fig.axes[0].collections
                if isinstance(artist, LineCollection)
                and getattr(artist, "_mudplot_source_rows", ())
                == tuple(query_rows[group])
            )
            for index, segment in enumerate(bars.get_segments(), start=fit_count):
                np.testing.assert_allclose(
                    segment[:, 1], [lower[index], upper[index]], rtol=1e-10, atol=1e-10
                )
        assert plot.spec.data.columns == raw
    finally:
        plt.close(fig)


@pytest.mark.parametrize("untrained", [True, False])
def test_sparse_panel_strict_errors_use_original_physical_row(untrained):
    import re

    import mudplot._regression_inference as engine
    from mudplot._render import _regression_fit

    raw = {
        "x": list(range(14)),
        "y": [1 + 2 * index for index in range(14)],
        "group": ["excluded"] * 14,
        "split": ["ignore"] * 14,
        "keep": [False] * 14,
        "w": [1] * 14,
    }
    for row in (3, 7, 11):
        raw["keep"][row] = True
        raw["group"][row] = "trained"
        raw["split"][row] = "train" if row != 11 else "query"
    if untrained:
        raw["group"][11] = "untrained"
    else:
        raw["x"][11] = float("inf")
        raw["w"][11] = 0
    plot = mp.plot(raw).regplot(
        "x",
        "y",
        group="group",
        weights="w",
        regression={
            "sampling": {"train": {"split": "train"}, "query": {"split": "query"}}
        },
    )
    spec = plot.spec
    spec.panels[0].filters = {"keep": True}
    assert any(
        11 in map(int, re.findall(r"\d+", problem)) for problem in mp.validate(spec)
    )
    with pytest.raises(ValueError) as error:
        engine.prepare_regressions(spec, _regression_fit)
    assert 11 in map(int, re.findall(r"\d+", str(error.value)))


def test_later_known_byte_rejection_precedes_rng_and_native(monkeypatch):
    import mudplot._regression_inference as engine

    plot = mp.plot(source(32))
    for count, level in ((1, 95), (100000, 50)):
        plot.regplot(
            "x",
            "y",
            weights="w",
            confidence=level,
            regression={"bootstrap": {"n_boot": count, "seed": 43}},
        )

    def unexpected(*args, **kwargs):
        pytest.fail("known byte rejection must precede RNG/native")

    class NoRandom:
        def __init__(self, original):
            self.__basicsize__ = original.__basicsize__

        def __call__(self, *args, **kwargs):
            unexpected()

    for name in ("Generator", "PCG64"):
        monkeypatch.setattr(
            engine.np.random, name, NoRandom(getattr(engine.np.random, name))
        )
    monkeypatch.setattr(plt, "figure", unexpected)
    with pytest.raises(ValueError):
        plot.render()
