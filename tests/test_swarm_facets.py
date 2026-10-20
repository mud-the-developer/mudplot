"""Facet Swarms share selected size domains; empty cells are frames, not data."""

import copy

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from mudplot._semantics import shared_scale_domains
from mudplot._swarm import SwarmCollection

from test_swarm_sizes import _pixel_clearance


def _collections(ax):
    return [c for c in ax.collections if isinstance(c, SwarmCollection)]


def _guides(ax):
    return [
        line
        for line in ax.lines
        if isinstance(label := line.get_label(), str) and label.startswith("size:")
    ]


@pytest.mark.parametrize("orient", ["v", "h"])
def test_scalar_reserved_cells_have_category_frames_without_observations(orient):
    source = {
        "cat": ["A", "B", "A", "B"],
        "value": [1, 2, 3, 4],
        "cell": ["left", "left", "right", "right"],
        "g": ["u", "v", "u", "v"],
    }
    p = (
        mp.plot(source)
        .swarmplot("cat", "value", group="g", orient=orient)
        .facet(col="cell", col_order=["empty", "left", "right"], col_wrap=2)
        .size(7, 5)
    )
    assert mp.validate(p.spec) == [] and len(p.spec.panels) == 3
    fig = p.render()
    try:
        empty = fig.axes[0]
        assert not empty.collections and not empty.lines
        ticks = empty.get_yticklabels() if orient == "h" else empty.get_xticklabels()
        assert [t.get_text() for t in ticks] == ["A", "B"]
        assert "empty" in empty.get_title() and len(fig.axes) == 3
        for ax in fig.axes[1:]:
            _pixel_clearance(ax)
        assert (
            p.spec.data.columns == source
            and mp.from_json(p.to_json()) == p.spec
            and mp.apply(p.action_log) == p.spec
        )
    finally:
        plt.close(fig)


@pytest.mark.parametrize("kind", ["numeric", "categorical"])
def test_size_facets_pool_original_selected_rows_and_skip_empty_guides(kind):
    source = {
        "cat": ["A"] * 4,
        "value": [1, 1.01, 2, 2.01],
        "mass": [0, 5, 10, None],
        "grade": ["large", "small", "middle", None],
        "cell": ["left", "left", "right", "right"],
        "g": ["u", "v", "u", "v"],
    }
    config = {"size": "mass" if kind == "numeric" else "grade", "size_kind": kind}
    p = (
        mp.plot(source)
        .swarmplot("cat", "value", group="g", dodge=0, semantics=config)
        .facet(col="cell", col_order=["left", "empty", "right"])
        .size(9, 4)
    )
    assert mp.validate(p.spec) == []
    domains = shared_scale_domains(p.spec)
    assert len(domains) == 1 and next(iter(domains.values()))["rows"] == [0, 1, 2]
    before = copy.deepcopy(p.spec)
    fig = p.render()
    try:
        left, empty, right = fig.axes
        assert not empty.collections and not empty.lines
        _pixel_clearance(left)
        _pixel_clearance(right)
        np.testing.assert_allclose(_collections(left)[0].get_sizes(), [9, 36])
        np.testing.assert_allclose(_collections(right)[0].get_sizes(), [81])
        assert len(_guides(left)) == len(_guides(right)) == 3 and not _guides(empty)
        assert "v" not in right.get_legend_handles_labels()[1]
        np.testing.assert_array_equal(
            np.asarray(_collections(left)[0].get_offsets())[:, 1], [1, 1.01]
        )
        np.testing.assert_array_equal(
            np.asarray(_collections(right)[0].get_offsets())[:, 1], [2]
        )
        assert p.spec == before and p.spec.data.columns == source
    finally:
        plt.close(fig)


@pytest.mark.parametrize("kind", [None, "numeric", "categorical"])
def test_all_reserved_swarm_grid_never_normalizes_an_empty_domain(kind):
    source = {
        "cat": ["A", "A"],
        "value": [1, 2],
        "mass": [0, 10],
        "grade": ["small", "large"],
        "cell": ["left", "right"],
    }
    config = (
        None
        if kind is None
        else {"size": "mass" if kind == "numeric" else "grade", "size_kind": kind}
    )
    p = (
        mp.plot(source)
        .swarmplot("cat", "value", semantics=config)
        .facet(col="cell", col_order=["absent"])
        .size(4, 3)
    )
    assert mp.validate(p.spec) == []
    state = np.random.get_state()
    fig = p.render()
    try:
        assert (
            len(fig.axes) == 1 and not fig.axes[0].collections and not fig.axes[0].lines
        )
        assert "absent" in fig.axes[0].get_title() and p.spec.data.columns == source
        now = np.random.get_state()
        assert state[0] == now[0] and state[2:] == now[2:]
        np.testing.assert_array_equal(state[1], now[1])
    finally:
        plt.close(fig)


def test_missing_size_can_empty_a_nonempty_facet_cell_without_imputing_points():
    p = (
        mp.plot(
            {
                "cat": ["A", "B"],
                "value": [1, 2],
                "mass": [1, None],
                "cell": ["left", "right"],
            }
        )
        .swarmplot("cat", "value", semantics={"size": "mass"})
        .facet(col="cell")
        .size(6, 3)
    )
    fig = p.render()
    try:
        assert (
            len(_collections(fig.axes[0])) == 1
            and not fig.axes[1].collections
            and not fig.axes[1].lines
        )
        assert (
            np.asarray(_collections(fig.axes[0])[0].get_offsets(), dtype=float).shape[0]
            == 1
        )
    finally:
        plt.close(fig)


def test_empty_first_shared_layer_does_not_suppress_later_enabled_size_guide():
    source = {
        "cat": ["A", "A"],
        "left": [1, None],
        "right": [None, 2],
        "mass": [0, 10],
        "cell": ["other", "target"],
    }
    p = (
        mp.plot(source)
        .swarmplot("cat", "left", semantics={"size": "mass", "scale_id": "same"})
        .swarmplot("cat", "right", semantics={"size": "mass", "scale_id": "same"})
    )
    spec = p.spec
    spec.panels[0].filters = {"cell": "target"}
    assert mp.validate(spec) == []
    fig = mp.render(spec)
    try:
        assert len(_collections(fig.axes[0])) == 1 and len(_guides(fig.axes[0])) == 1
        assert _guides(fig.axes[0])[0].get_markersize() == 6
        np.testing.assert_allclose(_collections(fig.axes[0])[0].get_sizes(), [36])
    finally:
        plt.close(fig)


@pytest.mark.parametrize("kind", [None, "numeric"])
def test_plain_empty_swarm_still_fails_without_an_explicit_selection(kind):
    p = mp.plot({"cat": ["A"], "value": [None], "mass": [1]}).swarmplot(
        "cat", "value", semantics=None if kind is None else {"size": "mass"}
    )
    before = plt.get_fignums()
    with pytest.raises(ValueError):
        p.render()
    assert plt.get_fignums() == before


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("width", 0, "width"),
        ("marker", "s", "circular"),
        ("marker_size", 0, "positive"),
        ("line_width", True, "line_width"),
        ("x", "missing", "missing"),
    ],
)
def test_empty_filtered_cell_does_not_skip_invalid_layer_options(field, value, message):
    p = mp.plot({"cat": ["A"], "value": [1], "cell": ["known"]}).swarmplot(
        "cat", "value"
    )
    spec = p.spec
    spec.panels[0].filters = {"cell": "absent"}
    setattr(spec.panels[0].layers[0], field, value)
    with pytest.raises(ValueError, match=message):
        mp.render(spec)


def test_empty_filtered_cell_does_not_hide_unrepresentable_declared_sizes():
    p = mp.plot({"cat": ["A"], "value": [1], "mass": [0], "cell": ["known"]}).swarmplot(
        "cat", "value", semantics={"size": "mass"}
    )
    spec = p.spec
    spec.panels[0].filters = {"cell": "absent"}
    config = spec.panels[0].layers[0].semantics
    assert isinstance(config, mp.SemanticSpec)
    config.sizes = [0, 1e-200]
    assert any("representable" in issue for issue in mp.validate(spec))


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("kind", [None, "numeric"])
@pytest.mark.parametrize("all_reserved", [False, True])
def test_native_log_category_cells_keep_valid_frames(orient, kind, all_reserved):
    p = (
        mp.plot(
            {
                "cat": [1, 10, 1, 10],
                "value": [1, 2, 3, 4],
                "mass": [0, 5, 10, 2],
                "cell": ["left", "left", "right", "right"],
            }
        )
        .swarmplot(
            "cat",
            "value",
            orient=orient,
            native_scale=True,
            semantics=None if kind is None else {"size": "mass"},
        )
        .xscale("log")
        .yscale("log")
        .facet(
            col="cell",
            col_order=["absent"] if all_reserved else ["empty", "left", "right"],
        )
        .size(9, 4)
    )
    fig = p.render()
    try:
        assert not fig.axes[0].collections and not fig.axes[0].lines
        for ax in fig.axes[1:]:
            _pixel_clearance(ax)
        fig.set_dpi(120)
        fig.canvas.draw()
        for ax in fig.axes[1:]:
            _pixel_clearance(ax)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("sized", [False, True])
def test_explicit_dropna_can_select_a_frame_without_rewriting_source(sized):
    p = mp.plot(
        {"cat": ["A", "A"], "value": [1, 2], "mass": [0, 10], "meta": [None, None]}
    ).swarmplot("cat", "value", semantics={"size": "mass"} if sized else None)
    spec = p.spec
    before = copy.deepcopy(spec)
    spec.panels[0].dropna = ["meta"]
    assert mp.validate(spec) == []
    fig = mp.render(spec)
    try:
        assert not fig.axes[0].collections and not fig.axes[0].lines
        assert spec.data == before.data
    finally:
        plt.close(fig)


def test_materialized_empty_cell_can_fill_and_empty_again_through_setdata():
    p = (
        mp.plot(
            {
                "cat": ["A", "A"],
                "value": [1, 2],
                "mass": [0, 10],
                "cell": ["left", "right"],
            }
        )
        .swarmplot("cat", "value", semantics={"size": "mass"})
        .facet(col="cell", col_order=["empty", "left", "right"])
        .size(9, 3)
    )
    filters = [copy.deepcopy(panel.filters) for panel in p.spec.panels]
    p.dispatch(
        mp.actions.SetData(
            {
                "cat": ["A"] * 3,
                "value": [1, 2, 1.5],
                "mass": [0, 10, 5],
                "cell": ["left", "right", "empty"],
            }
        )
    )
    fig = p.render()
    try:
        assert len(_collections(fig.axes[0])) == 1
        np.testing.assert_array_equal(_collections(fig.axes[0])[0].get_sizes(), [36])
        assert len(_guides(fig.axes[0])) == 3
    finally:
        plt.close(fig)
    p.dispatch(mp.actions.SetData({"cat": [], "value": [], "mass": [], "cell": []}))
    assert (
        mp.validate(p.spec) == []
        and [panel.filters for panel in p.spec.panels] == filters
    )
    fig = p.render()
    try:
        assert len(fig.axes) == 3 and all(
            not ax.collections and not ax.lines for ax in fig.axes
        )
        assert mp.apply(p.action_log) == p.spec
    finally:
        plt.close(fig)


def test_invalid_facet_expansion_is_still_atomic():
    p = mp.plot({"cat": ["A"], "value": [1], "mass": [2], "cell": ["known"]}).swarmplot(
        "cat", "value", semantics={"size": "mass"}
    )
    before, history = p.spec, p.action_log
    with pytest.raises(ValueError):
        p.facet(col="cell", col_order=[str(i) for i in range(65)])
    assert p.spec == before and p.action_log == history
