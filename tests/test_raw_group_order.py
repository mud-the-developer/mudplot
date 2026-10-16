"""Ordered raw groups/facets preserve values and reserve visual slots."""

from __future__ import annotations

import copy
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import LineCollection, PathCollection
from matplotlib.container import BarContainer
from matplotlib.patches import Rectangle
from mudplot._facet import RAW_HUE_TYPES


def data():
    return {
        "x": [2, 1, 1, 1, 2, 1, 2],
        "y": [8, 4, 5, 2, 3, 4, 6],
        "lower": [7, 3, 4, 1, 2, 3, 5],
        "upper": [9, 5, 6, 3, 4, 5, 7],
        "err": [0.5] * 7,
        "h": ["B", "B", "B", "A", "A", "A", "A"],
        "site": ["North"] * 5 + ["South"] * 2,
    }


def build(kind, **style):
    p = mp.plot(data())
    if kind == "band":
        p.band("x", "upper", "lower", group="h", **style)
    elif kind == "rug":
        p.rug("x", group="h", **style)
    elif kind in ("bar", "errorbar"):
        getattr(p, kind)("x", "y", group="h", yerr="err", **style)
    else:
        getattr(p, kind)("x", "y", group="h", **style)
    return p


@pytest.mark.parametrize("kind", sorted(RAW_HUE_TYPES))
def test_raw_group_facets_render_reserved_and_sparse_hues_without_fake_legends(kind):
    p = build(kind).facet(col="site", col_order=["North", "empty", "South"]).size(10, 3)
    assert mp.validate(p.spec) == []
    assert all(panel.layers[0].hue_order == ["B", "A"] for panel in p.spec.panels)
    north, empty, south = p.render().axes
    assert north.get_legend_handles_labels()[1] == ["B", "A"]
    assert empty.get_legend_handles_labels()[1] == []
    assert south.get_legend_handles_labels()[1] == ["A"]
    assert not empty.lines and not empty.collections and not empty.patches
    assert mp.apply(p.action_log) == mp.Plot.from_json(p.to_json()).spec == p.spec


def test_raw_line_keeps_duplicate_x_original_path_order_and_same_styles_in_each_cell():
    p = build("line").facet(col="site").size(8, 3)
    north, south = p.render().axes
    np.testing.assert_array_equal(north.lines[0].get_xdata(), [2, 1, 1])
    np.testing.assert_array_equal(north.lines[0].get_ydata(), [8, 4, 5])
    assert p.spec.panels[0].layers[0].stat is None
    assert north.lines[1].get_color() == south.lines[0].get_color()
    assert north.lines[1].get_linestyle() == south.lines[0].get_linestyle()
    assert north.lines[1].get_marker() == south.lines[0].get_marker()


def test_ordered_raw_line_preserves_coordinate_gaps_instead_of_joining_across_them():
    raw = {"x": [1, 2, 3], "y": [2, None, 4], "h": ["A"] * 3}
    p = mp.plot(raw).line("x", "y", group="h", hue_order=["missing", "A"])
    ax = p.render().axes[0]
    assert len(ax.lines) == 1
    assert np.isnan(np.asarray(ax.lines[0].get_ydata(), dtype=float)[1])
    np.testing.assert_array_equal(ax.lines[0].get_xdata(), [1, 2, 3])


def test_raw_bar_preserves_supplied_values_errors_and_sparse_dodge_hatch_slots():
    p = build("bar", bar_width=0.8).facet(col="site").size(8, 3)
    north, south = p.render().axes
    bars_n = [
        container
        for container in north.containers
        if isinstance(container, BarContainer)
    ]
    bars_s = [
        container
        for container in south.containers
        if isinstance(container, BarContainer)
    ]
    np.testing.assert_array_equal([bar.get_height() for bar in bars_n[0]], [8, 4, 5])
    np.testing.assert_array_equal([bar.get_height() for bar in bars_s[0]], [4, 6])
    # Keep the raw bar primitive's existing 8% inter-bar gap.
    assert all(bar.get_width() == pytest.approx(0.4 * 0.92) for bar in bars_s[0])
    assert bars_n[1][0].get_facecolor() == bars_s[0][0].get_facecolor()
    assert bars_n[1][0].get_hatch() == bars_s[0][0].get_hatch()
    np.testing.assert_allclose(
        [bar.get_x() + bar.get_width() / 2 for bar in bars_s[0]], [1.2, 2.2]
    )
    segments = [
        np.asarray(segment)[:, 1]
        for collection in south.collections
        if isinstance(collection, LineCollection)
        for segment in collection.get_segments()
    ]
    np.testing.assert_allclose(segments, [[3.5, 4.5], [5.5, 6.5]])


@pytest.mark.parametrize("kind", ["bar", "errorbar"])
def test_absolute_raw_uncertainty_bounds_survive_facet_selection(kind):
    p = mp.plot(data())
    getattr(p, kind)("x", "y", group="h", y_lower="lower", y_upper="upper")
    p.facet(col="site").size(8, 3)
    south = p.render().axes[1]
    segments = [
        np.asarray(segment)[:, 1]
        for collection in south.collections
        if isinstance(collection, LineCollection)
        for segment in collection.get_segments()
    ]
    np.testing.assert_allclose(segments, [[3, 5], [5, 7]])


def test_explicit_raw_hue_order_selects_before_coordinates_and_keeps_source_table():
    raw = {"x": ["bad", 1, 2], "y": [99, 3, 4], "h": ["omit", "A", "A"]}
    p = (
        mp.plot(raw)
        .scatter("x", "y", group="h", hue_order=["empty", "A"])
        .xscale("log")
    )
    assert mp.validate(p.spec) == []
    assert p.spec.data.columns == raw
    ax = p.render().axes[0]
    collection = ax.collections[0]
    assert isinstance(collection, PathCollection)
    np.testing.assert_array_equal(collection.get_offsets(), [[1, 3], [2, 4]])


def test_raw_group_bool_and_numeric_identity_is_typed_when_ordered():
    p = mp.plot({"x": [1, 2], "y": [3, 4], "h": [True, 1]}).scatter(
        "x", "y", group="h", hue_order=[True, 1]
    )
    ax = p.render().axes[0]
    assert ax.get_legend_handles_labels()[1] == ["True", "1"]
    assert [np.asarray(c.get_offsets()).shape[0] for c in ax.collections] == [1, 1]


def test_empty_ordered_raw_groups_do_not_make_regression_fits_or_rug_collections():
    for kind in ("regplot", "rug", "scatter"):
        p = build(kind, hue_order=["missing"])
        assert mp.validate(p.spec) == []
        ax = p.render().axes[0]
        assert not ax.lines and not ax.collections and not ax.patches


def test_ordered_regression_validates_bool_and_numeric_groups_separately():
    p = mp.plot({"x": [1, 2], "y": [3, 5], "h": [True, 1]}).regplot(
        "x", "y", group="h", hue_order=[True, 1]
    )
    assert any("requires at least 2" in issue for issue in mp.validate(p.spec))


@pytest.mark.parametrize("order", [[], ["A", "A"], [1, "1"], [None], [float("inf")], 3])
def test_invalid_raw_orders_are_reported_without_mutating_inputs(order):
    p = build("line", hue_order=order)
    before = copy.deepcopy(p.spec)
    assert mp.validate(p.spec)
    assert p.spec == before


def test_raw_order_requires_group_and_rejects_legacy_numeric_colour_mapping():
    raw = data()
    assert mp.validate(mp.plot(raw).line("x", "y", hue_order=["A"]).spec)
    assert mp.validate(
        mp.plot(raw).scatter("x", "y", c="y", group="h", hue_order=["A"]).spec
    )


@pytest.mark.parametrize("extension", ["png", "pdf", "svg"])
def test_ordered_raw_facets_reproduce_exports_and_do_not_use_global_rng(
    tmp_path, extension
):
    state = np.random.get_state()
    p = build("line").facet(col="site").size(8, 3)
    paths = [tmp_path / f"{name}.{extension}" for name in ("a", "b")]
    plt.close(p.save(str(paths[0])))
    plt.close(mp.Plot.from_json(p.to_json()).save(str(paths[1])))
    assert paths[0].read_bytes() == paths[1].read_bytes()
    after = np.random.get_state()
    assert state[0] == after[0] and state[2:] == after[2:]
    np.testing.assert_array_equal(state[1], after[1])


def test_raw_categorical_bars_keep_shared_category_positions():
    raw = {
        "x": ["B", "A", "A", "C"],
        "y": [1, 2, 3, 4],
        "h": ["same"] * 4,
        "site": ["N", "N", "S", "S"],
    }
    p = mp.plot(raw).bar("x", "y", group="h").facet(col="site").size(8, 3)
    a, b = p.render().axes
    first = [patch for patch in a.patches if isinstance(patch, Rectangle)]
    second = [patch for patch in b.patches if isinstance(patch, Rectangle)]
    np.testing.assert_allclose(
        [patch.get_x() + patch.get_width() / 2 for patch in first], [0, 1]
    )
    np.testing.assert_allclose(
        [patch.get_x() + patch.get_width() / 2 for patch in second], [1, 2]
    )


def test_each_ordered_raw_layer_selects_from_the_original_panel_data():
    p = build("line", hue_order=["B"])
    p.scatter("x", "y", group="h", hue_order=["A"])
    p.facet(col="site").size(8, 3)
    a, b = p.render().axes
    assert a.get_legend_handles_labels()[1] == ["B", "A"]
    assert b.get_legend_handles_labels()[1] == ["A"]
    np.testing.assert_array_equal(a.lines[0].get_xdata(), [2, 1, 1])
    np.testing.assert_array_equal(b.collections[0].get_offsets(), [[1, 4], [2, 6]])


def test_default_unordered_groups_keep_their_existing_observed_only_style_cycle():
    raw = {"x": [1, 2], "y": [None, 3], "h": ["empty", "A"]}
    default = mp.plot(raw).line("x", "y", group="h").render().axes[0]
    ordered = (
        mp.plot(raw)
        .line("x", "y", group="h", hue_order=["empty", "A"])
        .render()
        .axes[0]
    )
    assert default.lines[0].get_linestyle() == "-"
    assert ordered.lines[0].get_linestyle() == "--"
    assert default.lines[0].get_color() != ordered.lines[0].get_color()


def test_ordered_raw_facet_core_needs_no_numeric_or_render_dependency():
    script = (
        "import sys; import mudplot as m; "
        "p=m.plot({'x':[2,1,1],'y':[3,4,5],'h':['A']*3,'f':['N','S','S']}); "
        "p.line('x','y',group='h').facet(col='f'); "
        "assert m.validate(p.spec)==[]; assert m.apply(p.action_log)==p.spec; "
        "assert 'numpy' not in sys.modules and 'matplotlib' not in sys.modules"
    )
    subprocess.run([sys.executable, "-S", "-c", script], check=True)
