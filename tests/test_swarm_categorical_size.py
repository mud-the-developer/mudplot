"""Categorical size ranks, selected source rows and observed-only guides."""

import copy

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from mudplot._categorical import distribution_rows
from mudplot._swarm import SwarmCollection

from test_swarm_sizes import _pixel_clearance


def _collection(ax) -> SwarmCollection:
    return next(c for c in ax.collections if isinstance(c, SwarmCollection))


def _guides(ax):
    return [
        line
        for line in ax.lines
        if isinstance(label := line.get_label(), str)
        and label.startswith("size: class=")
    ]


def test_explicit_order_selects_cohort_reserves_sizes_and_does_not_invent_guides():
    source = {
        "cat": ["A"] * 6,
        "value": [1] * 6,
        "class": ["middle", "small", "large", None, "outside", "small"],
        "g": ["u", "v", "u", "v", "u", "v"],
    }
    p = (
        mp.plot(source)
        .swarmplot(
            "cat",
            "value",
            group="g",
            dodge=0,
            semantics={
                "size": "class",
                "size_kind": "categorical",
                "size_order": ["small", "empty", "large", "middle"],
            },
        )
        .size(7, 4)
    )
    before = copy.deepcopy(p.spec)
    assert mp.validate(p.spec) == []
    assert distribution_rows(p.spec.data.columns, p.spec.panels[0].layers[0]) == [
        0,
        1,
        2,
        5,
    ]
    assert mp.from_json(p.to_json()) == p.spec and mp.apply(p.action_log) == p.spec
    fig = p.render()
    try:
        ax = fig.axes[0]
        c = _collection(ax)
        _pixel_clearance(ax)
        np.testing.assert_allclose(c.get_sizes(), [81, 9, 49, 9])
        guides = _guides(ax)
        assert [line.get_label() for line in guides] == [
            "size: class=small",
            "size: class=large",
            "size: class=middle",
        ]
        np.testing.assert_allclose(
            [line.get_markersize() for line in guides], [3, 7, 9]
        )
        assert all(
            np.asarray(line.get_xdata()).size == 0 and line.get_url() is None
            for line in guides
        )
        assert len(ax.collections) == 1 and p.spec == before
    finally:
        plt.close(fig)


def test_observed_order_is_stable_not_alphabetical():
    p = mp.plot(
        {"cat": ["A"] * 4, "value": [1] * 4, "class": ["big", "tiny", "mid", "tiny"]}
    ).swarmplot("cat", "value", semantics={"size": "class", "size_kind": "categorical"})
    fig = p.render()
    try:
        np.testing.assert_allclose(
            _collection(fig.axes[0]).get_sizes(), [9, 36, 81, 36]
        )
        assert [line.get_label() for line in _guides(fig.axes[0])] == [
            "size: class=big",
            "size: class=tiny",
            "size: class=mid",
        ]
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "order,diameter", [(None, 6), (["one"], 6), (["unused", "one"], 9)]
)
def test_singleton_and_reserved_level_slots_keep_honest_diameters(order, diameter):
    p = mp.plot({"cat": ["A"], "value": [1], "class": ["one"]}).swarmplot(
        "cat",
        "value",
        semantics={"size": "class", "size_kind": "categorical", "size_order": order},
    )
    fig = p.render()
    try:
        np.testing.assert_allclose(_collection(fig.axes[0]).get_sizes(), [diameter**2])
        guides = _guides(fig.axes[0])
        assert len(guides) == 1 and guides[0].get_markersize() == diameter
    finally:
        plt.close(fig)


def test_boolean_and_numeric_category_keys_do_not_select_each_other():
    p = mp.plot(
        {"cat": ["A"] * 4, "value": [1] * 4, "class": [True, 1, False, 0]}
    ).swarmplot(
        "cat",
        "value",
        semantics={"size": "class", "size_kind": "categorical", "size_order": [1]},
    )
    assert distribution_rows(p.spec.data.columns, p.spec.panels[0].layers[0]) == [1]
    fig = p.render()
    try:
        np.testing.assert_allclose(_collection(fig.axes[0]).get_sizes(), [36])
        assert [line.get_label() for line in _guides(fig.axes[0])] == ["size: class=1"]
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "value", ["", float("inf"), float("-inf"), [1], {"x": 1}, None, float("nan")]
)
@pytest.mark.parametrize("ordered", [False, True])
def test_invalid_categories_are_not_hidden_by_size_order(value, ordered):
    p = mp.plot({"cat": ["A"], "value": [1], "class": [value]}).swarmplot(
        "cat",
        "value",
        semantics={
            "size": "class",
            "size_kind": "categorical",
            "size_order": ["known"] if ordered else None,
        },
    )
    before = plt.get_fignums()
    with pytest.raises(ValueError):
        p.render()
    assert plt.get_fignums() == before


@pytest.mark.parametrize(
    "values,order",
    [
        ([1, "1"], None),
        (["a"], ["a", "a"]),
        (["a"], [1, "1"]),
        (["a"], []),
        ([str(i) for i in range(65)], None),
        (["a"], [str(i) for i in range(65)]),
    ],
)
def test_level_limits_and_ambiguous_labels_are_explicit(values, order):
    p = mp.plot(
        {"cat": ["A"] * len(values), "value": [1] * len(values), "class": values}
    ).swarmplot(
        "cat",
        "value",
        semantics={"size": "class", "size_kind": "categorical", "size_order": order},
    )
    with pytest.raises(ValueError):
        p.render()


def test_categorical_legend_false_and_numeric_norm_rejection_are_independent():
    source = {"cat": ["A", "A"], "value": [1, 1], "class": ["low", "high"]}
    p = mp.plot(source).swarmplot(
        "cat",
        "value",
        semantics={"size": "class", "size_kind": "categorical", "legend": False},
    )
    fig = p.render()
    try:
        np.testing.assert_allclose(_collection(fig.axes[0]).get_sizes(), [9, 81])
        assert not _guides(fig.axes[0])
    finally:
        plt.close(fig)
    p = mp.plot(source).swarmplot(
        "cat",
        "value",
        semantics={"size": "class", "size_kind": "categorical", "size_norm": [0, 1]},
    )
    with pytest.raises(ValueError):
        p.render()


def test_size_order_defines_usable_budget_and_source_stays_unchanged():
    source = {
        "cat": ["A"] * 2001,
        "value": [1] * 2001,
        "class": ["keep"] * 2000 + ["drop"],
    }
    p = mp.plot(source).swarmplot(
        "cat",
        "value",
        semantics={"size": "class", "size_kind": "categorical", "size_order": ["keep"]},
    )
    assert (
        mp.validate(p.spec) == []
        and len(distribution_rows(p.spec.data.columns, p.spec.panels[0].layers[0]))
        == 2000
    )
    assert p.spec.data.columns == source


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("dpi", [72, 200])
def test_categorical_sizes_keep_physical_clearance_on_native_log_categories(
    orient, dpi
):
    p = (
        mp.plot(
            {
                "cat": [1, 1, 10, 10],
                "value": [1, 1, 1.01, 1.01],
                "class": ["m", "s", "l", "m"],
                "g": ["u", "v", "u", "v"],
            }
        )
        .swarmplot(
            "cat",
            "value",
            orient=orient,
            native_scale=True,
            group="g",
            dodge=0,
            semantics={
                "size": "class",
                "size_kind": "categorical",
                "size_order": ["s", "m", "l"],
            },
        )
        .size(6, 4)
    )
    p.xscale("log").yscale("log").dispatch(mp.actions.SetDpi(dpi))
    before = copy.deepcopy(p.spec)
    fig = p.render()
    try:
        ax = fig.axes[0]
        c = _collection(ax)
        for size, render_dpi in (((6, 4), dpi), ((7, 5), dpi * 1.5)):
            fig.set_size_inches(*size)
            fig.set_dpi(render_dpi)
            fig.canvas.draw()
            _pixel_clearance(ax)
            np.testing.assert_allclose(c.get_sizes(), [36, 9, 81, 36])
        np.testing.assert_array_equal(
            np.asarray(c.get_offsets())[:, 0 if orient == "h" else 1],
            [1, 1, 1.01, 1.01],
        )
        assert p.spec == before
    finally:
        plt.close(fig)


def test_categorical_mapping_cannot_silently_gain_facet_shared_or_style_support():
    source = {
        "cat": ["A", "A"],
        "value": [1, 2],
        "class": ["low", "high"],
        "g": ["u", "v"],
    }
    for extra in ({"scale_id": "shared"}, {"style": "g"}, {"hue": "g"}):
        p = mp.plot(source).swarmplot(
            "cat",
            "value",
            semantics={"size": "class", "size_kind": "categorical", **extra},
        )
        with pytest.raises(ValueError):
            p.render()
    p = mp.plot(source).swarmplot(
        "cat", "value", semantics={"size": "class", "size_kind": "categorical"}
    )
    before, history = p.spec, p.action_log
    with pytest.raises(ValueError):
        p.facet(col="g")
    assert p.spec == before and p.action_log == history
