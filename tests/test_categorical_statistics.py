"""Categorical layouts preserve raw statistics, level order and real endpoints."""

import matplotlib

matplotlib.use("Agg")

import mudplot as mp
import numpy as np
import pytest
from matplotlib.container import BarContainer, ErrorbarContainer
from matplotlib.text import Annotation
from mudplot._estimate import summarize
from mudplot._render import _count_colors


def _data():
    return {
        "x": ["B", "B", "A", "A"] * 2,
        "y": [1, 3, 2, 4, 3, 5, 4, 6],
        "g": ["u"] * 4 + ["v"] * 4,
    }


def _bars(ax):
    return [c for c in ax.containers if isinstance(c, BarContainer)]


@pytest.mark.parametrize("kind", ["barplot", "pointplot", "countplot"])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_orientation_and_explicit_orders_work_through_public_builders(kind, orient):
    p = mp.plot(_data())
    kwargs = {
        "group": "g",
        "order": ["A", "B", "empty"],
        "hue_order": ["v", "u", "absent"],
        "orient": orient,
    }
    if kind == "countplot":
        p.countplot("x", **kwargs)
    else:
        getattr(p, kind)("x", "y", errorbar=None, **kwargs)
    assert mp.validate(p.spec) == []
    assert _count_colors(p.spec) == 3
    ax = p.render().axes[0]
    ticks = ax.get_yticklabels() if orient == "h" else ax.get_xticklabels()
    assert [t.get_text() for t in ticks] == ["A", "B", "empty"]
    assert ax.get_legend_handles_labels()[1] == ["v", "u"]
    assert mp.Plot.from_json(p.to_json()).spec == p.spec
    assert mp.apply(p.action_log) == p.spec


@pytest.mark.parametrize("kind", ["barplot", "pointplot"])
def test_horizontal_ranges_can_exclude_estimate_without_becoming_negative_errors(kind):
    p = getattr(mp.plot({"x": ["A"] * 4, "y": [1, 2, 3, 100]}), kind)(
        "x", "y", estimator="min", errorbar=("pi", 50), orient="h"
    )
    ax = p.render().axes[0]
    ranges = [c for c in ax.containers if isinstance(c, ErrorbarContainer)]
    assert ranges[0].has_xerr and not ranges[0].has_yerr
    np.testing.assert_allclose(
        ranges[0].lines[2][0].get_segments(), [[[1.75, 0], [27.25, 0]]]
    )
    assert ax.get_xlim()[1] > 27.25


@pytest.mark.parametrize("orient", ["v", "h"])
def test_missing_selected_category_slots_break_point_lines(orient):
    p = mp.plot({"x": ["A", "A", "B", "B"], "y": [1, 3, 4, 6]}).pointplot(
        "x", "y", order=["A", "empty", "B"], orient=orient, errorbar=None
    )
    line = p.render().axes[0].lines[0]
    categories = line.get_ydata() if orient == "h" else line.get_xdata()
    values = line.get_xdata() if orient == "h" else line.get_ydata()
    np.testing.assert_allclose(np.asarray(categories), [0, np.nan, 2])
    np.testing.assert_allclose(np.asarray(values), [2, np.nan, 5])


@pytest.mark.parametrize("gap,expected", [(None, 0.368), (0, 0.4), (0.5, 0.2)])
def test_gap_is_a_fraction_of_the_allocated_group_span(gap, expected):
    ax = (
        mp.plot(_data())
        .barplot("x", "y", group="g", errorbar=None, gap=gap)
        .render()
        .axes[0]
    )
    assert all(b.get_width() == pytest.approx(expected) for c in _bars(ax) for b in c)


@pytest.mark.parametrize("orient", ["v", "h"])
def test_countplot_stacks_actual_percentages_and_labels_segment_values(orient):
    p = mp.plot({"x": ["A", "A", "A", "B", "B"], "g": ["u", "u", "v", "v", "v"]})
    p.countplot(
        "x",
        group="g",
        stat="percent",
        stack=True,
        value_labels=True,
        label_format=".0f",
        orient=orient,
    )
    ax = p.render().axes[0]
    bars = _bars(ax)
    assert [text.get_text() for text in ax.texts] == ["40", "20", "40"]
    first = bars[0][0]
    second = bars[1][0]
    assert (first.get_width() if orient == "h" else first.get_height()) == 40
    assert (second.get_x() if orient == "h" else second.get_y()) == 40
    assert (second.get_width() if orient == "h" else second.get_height()) == 20


def test_order_and_hue_order_filter_normalized_count_denominator_explicitly():
    p = mp.plot(_data()).countplot(
        "x", group="g", stat="percent", order=["A"], hue_order=["v"]
    )
    result = summarize(p.spec.data.columns, p.spec.panels[0].layers[0])
    assert len(result.estimates) == 1 and result.estimates[0].value == 100


@pytest.mark.parametrize(
    "options,message",
    [
        ({"orient": "horizontal"}, "orient"),
        ({"gap": 1}, "gap"),
        ({"gap": True}, "gap"),
        ({"order": []}, "nonempty"),
        ({"order": ["A", "A"]}, "unique"),
        ({"order": [1, "1"]}, "collisions"),
        ({"order": [None]}, "finite scalars"),
        ({"order": ["missing"]}, "no usable"),
        ({"hue_order": ["u"]}, "requires group"),
        ({"stack": True}, "stack is not supported"),
        ({"value_labels": 1}, "value_labels must be boolean"),
        ({"label_format": "{value:9999999999}"}, "label_format must be"),
    ],
)
def test_bad_or_unsupported_layout_settings_fail_without_silent_ignoring(
    options, message
):
    p = mp.plot(_data()).barplot("x", "y", **options)
    assert any(message in issue for issue in mp.validate(p.spec))


def test_conflicting_orders_on_a_shared_axis_fail_instead_of_ignoring_order():
    p = mp.plot(_data()).barplot("x", "y", order=["B", "A"], errorbar=None)
    p.pointplot("x", "y", order=["A", "B"], errorbar=None)
    with pytest.raises(ValueError, match="conflicting category order"):
        p.render()


def test_horizontal_secondary_y_route_is_explicitly_unsupported():
    p = (
        mp.plot(_data())
        .secondary_yaxis("Estimate")
        .barplot("x", "y", orient="h", axis="y2")
    )
    assert any("do not route to y2" in issue for issue in mp.validate(p.spec))


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("sign", [1, -1])
def test_labels_clear_real_intervals_without_misaligning_singleton_bars(orient, sign):
    data = {"x": ["A", "B", "B", "B"], "y": [sign * y for y in [1, 1, 2, 3]]}
    p = mp.plot(data).barplot(
        "x",
        "y",
        errorbar="sd",
        orient=orient,
        value_labels=True,
    )
    with pytest.warns(UserWarning, match="fewer than 2"):
        ax = p.render().axes[0]
    assert [t.get_text() for t in ax.texts] == [str(sign), str(2 * sign)]
    expected = (
        [(sign, 0), (3 * sign, 1)] if orient == "h" else [(0, sign), (1, 3 * sign)]
    )
    for text, coordinates in zip(ax.texts, expected, strict=True):
        assert isinstance(text, Annotation)
        assert text.xy == coordinates
        assert text.get_position() == (
            (2 * sign, 0) if orient == "h" else (0, 2 * sign)
        )
