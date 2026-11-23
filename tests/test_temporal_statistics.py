"""F02 statistical integration references; original dates are never replaced."""

import copy
from dataclasses import replace

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.container import BarContainer
from mudplot._estimate import summarize
from mudplot._temporal_data import prepare_temporal_layer

DATES = [
    "2026-01-01",
    "2026-01-01",
    "2026-01-02",
    "2026-01-02",
    "2026-01-11",
    "2026-01-11",
]


@pytest.mark.parametrize("kind", ["barplot", "pointplot", "countplot"])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_date_categories_use_elapsed_spacing_and_reference_estimates(kind, orient):
    data = {"t": DATES, "v": [1, 3, 2, 6, 4, 8], "w": [1, 3, 2, 2, 4, 1]}
    original = copy.deepcopy(data)
    plot = mp.plot(data)
    if kind == "countplot":
        plot.countplot("t", weights="w", orient=orient)
    else:
        getattr(plot, kind)("t", "v", weights="w", errorbar=None, orient=orient)
    plot.date_axis("x" if orient == "v" else "y", timezone="UTC")
    before = plot.to_json()
    assert mp.validate(plot.spec) == []
    panel = plot.spec.panels[0]
    columns, layer, _mask = prepare_temporal_layer(
        plot.spec.data.columns, panel.layers[0], panel
    )
    summary = summarize(columns, layer)
    assert summary.categories == [20454, 20455, 20464]
    expected = [4, 4, 5] if kind == "countplot" else [2.5, 4, 4.8]
    assert [e.value for e in summary.estimates] == pytest.approx(expected)
    figure = plot.render()
    try:
        ax = figure.axes[0]
        if kind == "pointplot":
            line = ax.lines[0]
            category = np.asarray(
                line.get_xdata() if orient == "v" else line.get_ydata()
            )
            values = np.asarray(line.get_ydata() if orient == "v" else line.get_xdata())
        else:
            bars = [p for c in ax.containers if isinstance(c, BarContainer) for p in c]
            category = [
                (p.get_x() + p.get_width() / 2)
                if orient == "v"
                else (p.get_y() + p.get_height() / 2)
                for p in bars
            ]
            values = [p.get_height() if orient == "v" else p.get_width() for p in bars]
        assert list(category) == pytest.approx([20454, 20455, 20464])
        assert list(values) == pytest.approx(expected)
        assert plot.spec.data.columns == original and plot.to_json() == before
    finally:
        plt.close(figure)


def test_statistical_line_date_predictor_and_shared_hue_keep_source_keys():
    data = {"t": DATES, "v": [1, 3, 2, 6, 4, 8], "g": ["a", "b"] * 3}
    plot = (
        mp.plot(data)
        .lineplot("t", "v", hue="g", errorbar=None)
        .date_axis("x", timezone="UTC")
    )
    assert mp.validate(plot.spec) == []
    figure = plot.render()
    try:
        strokes = [
            line for line in figure.axes[0].lines if len(np.asarray(line.get_xdata()))
        ]
        assert len(strokes) == 2
        assert all(
            np.array_equal(line.get_xdata(), [20454, 20455, 20464]) for line in strokes
        )
        assert plot.spec.data.columns == data
    finally:
        plt.close(figure)


@pytest.mark.parametrize("estimator", ["mean", "median", "min", "max"])
def test_date_valued_response_statistics_have_calendar_meaning(estimator):
    plot = (
        mp.plot({"c": ["A", "A"], "t": ["2026-01-01", "2026-01-03"]})
        .pointplot("c", "t", estimator=estimator, errorbar=None)
        .date_axis("y", timezone="UTC")
    )
    panel = plot.spec.panels[0]
    columns, layer, _mask = prepare_temporal_layer(
        plot.spec.data.columns, panel.layers[0], panel
    )
    expected = {"mean": 20455, "median": 20455, "min": 20454, "max": 20456}[estimator]
    assert mp.validate(plot.spec) == []
    assert summarize(columns, layer).estimates[0].value == expected
    plt.close(plot.render())


@pytest.mark.parametrize("estimator", ["sum", "count"])
def test_absolute_date_response_sum_and_count_are_not_invented(estimator):
    plot = (
        mp.plot({"c": ["A", "A"], "t": ["2026-01-01", "2026-01-03"]})
        .pointplot("c", "t", estimator=estimator, errorbar=None)
        .date_axis("y", timezone="UTC")
    )
    assert any("temporal response" in issue for issue in mp.validate(plot.spec))


def test_count_value_axis_cannot_be_declared_calendar_time():
    plot = mp.plot({"c": ["A", "B"]}).countplot("c").date_axis("y", timezone="UTC")
    assert any("count" in i and "temporal" in i for i in mp.validate(plot.spec))


def test_explicit_date_order_and_zero_weight_selection_precede_parsing():
    source = {
        "t": ["2026-01-01", "2026-01-02", "bad", "excluded"],
        "v": [1, 3, 10, 20],
        "w": [1, 2, 0, 4],
    }
    plot = (
        mp.plot(source)
        .barplot(
            "t", "v", weights="w", errorbar=None, order=["2026-01-02", "2026-01-01"]
        )
        .date_axis("x", timezone="UTC")
    )
    assert mp.validate(plot.spec) == []
    panel = plot.spec.panels[0]
    columns, layer, _mask = prepare_temporal_layer(
        plot.spec.data.columns, panel.layers[0], panel
    )
    assert layer.order == [20455, 20454]
    result = summarize(columns, layer)
    assert [e.category for e in result.estimates] == [20455, 20454]
    assert [e.value for e in result.estimates] == [3, 1]
    assert plot.spec.data.columns == source


@pytest.mark.parametrize("kind", ["barplot", "pointplot", "countplot"])
def test_temporal_categories_on_secondary_value_axes_keep_elapsed_spacing(kind):
    plot = mp.plot({"t": DATES, "v": [1, 3, 2, 6, 4, 8]}).secondary_yaxis("Value")
    if kind == "countplot":
        plot.countplot("t", axis="y2")
    else:
        getattr(plot, kind)("t", "v", errorbar=None, axis="y2")
    plot.date_axis("x", timezone="UTC")
    assert mp.validate(plot.spec) == []
    figure = plot.render()
    try:
        ax = figure.axes[-1]
        if kind == "pointplot":
            positions = np.asarray(ax.lines[0].get_xdata())
        else:
            positions = np.asarray(
                [
                    p.get_x() + p.get_width() / 2
                    for c in ax.containers
                    if isinstance(c, BarContainer)
                    for p in c
                ]
            )
        np.testing.assert_allclose(positions, [20454, 20455, 20464])
    finally:
        plt.close(figure)


@pytest.mark.parametrize("kind", ["pointplot", "lineplot"])
def test_date_valued_secondary_response_is_not_misrouted(kind):
    plot = mp.plot(
        {"x": [1, 2, 3], "t": [DATES[0], DATES[2], DATES[4]]}
    ).secondary_yaxis("Event")
    getattr(plot, kind)("x", "t", errorbar=None, axis="y2")
    plot.date_axis("y2", timezone="UTC")
    assert mp.validate(plot.spec) == []
    figure = plot.render()
    try:
        np.testing.assert_allclose(
            np.asarray(figure.axes[-1].lines[0].get_ydata()), [20454, 20455, 20464]
        )
        assert not figure.axes[0].lines
    finally:
        plt.close(figure)


def test_semantic_statistical_line_uses_the_declared_secondary_temporal_axis():
    source = {
        "x": [1, 2, 3, 1, 2, 3],
        "t": ["2026-01-01", "2026-01-02", "2026-01-11"] * 2,
        "g": ["a"] * 3 + ["b"] * 3,
    }
    plot = (
        mp.plot(source)
        .secondary_yaxis("Date")
        .lineplot("x", "t", hue="g", errorbar=None, axis="y2")
        .date_axis("y2", timezone="UTC")
    )
    assert mp.validate(plot.spec) == []
    figure = plot.render()
    try:
        assert not figure.axes[0].lines
        strokes = [
            line for line in figure.axes[-1].lines if len(np.asarray(line.get_ydata()))
        ]
        assert len(strokes) == 2
        for line in strokes:
            np.testing.assert_allclose(
                np.asarray(line.get_ydata()), [20454, 20455, 20464]
            )
        assert plot.spec.data.columns == source
    finally:
        plt.close(figure)


@pytest.mark.parametrize("malformed", [{}, "count"])
def test_malformed_programmatic_stat_config_reports_an_issue(malformed):
    plot = (
        mp.plot({"t": ["2026-01-01"], "v": [1]})
        .barplot("t", "v", errorbar=None)
        .date_axis("x", timezone="UTC")
    )
    panel = plot.spec.panels[0]
    bad = replace(
        plot.spec,
        panels=[replace(panel, layers=[replace(panel.layers[0], stat=malformed)])],
    )
    assert any("StatSpec" in issue for issue in mp.validate(bad))


def test_offset_equivalent_categories_aggregate_only_in_requested_statistical_plot():
    source = {"t": ["2026-01-01T00:00:00Z", "2026-01-01T01:00:00+01:00"], "v": [1, 3]}
    plot = mp.plot(source).barplot("t", "v", errorbar=None).date_axis("x")
    panel = plot.spec.panels[0]
    columns, layer, _mask = prepare_temporal_layer(
        plot.spec.data.columns, panel.layers[0], panel
    )
    estimates = summarize(columns, layer).estimates
    assert len(estimates) == 1 and estimates[0].value == 2 and estimates[0].n == 2
    assert plot.spec.data.columns == source
