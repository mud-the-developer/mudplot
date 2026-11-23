"""External grid contracts: original rows, native cells and ordinary edits."""

import json
from datetime import date

import mudplot as mp
import pytest
from mudplot._facet import panel_rows
from mudplot.actions import AddLayer, SetData, SetLimits
from mudplot.spec import LayerSpec, SemanticSpec, TemporalSpec


def _rows(plot):
    spec = plot.spec
    return [panel_rows(spec.data.columns, panel) for panel in spec.panels]


def test_corner_keeps_asymmetric_raw_membership_and_reserved_empty():
    columns = {
        "date": [
            "2024-01-01T12:00:00Z",
            "2024-01-01T07:00:00-05:00",
            None,
            "2024-01-03T12:00:00Z",
            "not a date",
        ],
        "x": [1, None, 3, 5, 7],
        "y": [None, 2, 4, 6, 8],
        "w": [1, 3, 4, 8, 0],
        "g": [True, 1, True, 1, True],
    }
    plot = (
        mp.Plot(columns)
        .size(13, 10)
        .pair(
            ["date", "x", "y"],
            corner=True,
            weights="w",
            diag_kind="ecdf",
            diag_stat="probability",
            complementary=True,
            temporal={"date": TemporalSpec()},
            semantics=SemanticSpec(hue="g", hue_order=[True, 1, "reserved"]),
        )
    )
    assert _rows(plot) == [[0, 1, 3], [0, 3], [0, 2, 3], [1, 3], [2, 3], [1, 2, 3]]
    assert plot.spec.data.columns == columns
    assert len(plot.spec.panels) == 6
    fig = plot.render()
    assert len(fig.axes) == 6
    assert [tuple(line.get_ydata()) for line in fig.axes[2].lines] == [
        (1.0, 0.8, 0.0),
        (1.0, 0.0),
    ]
    old = json.loads(plot.to_json())
    with pytest.raises(ValueError, match="exactly one scientific owner"):
        plot.dispatch(AddLayer(LayerSpec(type="scatter", x="date", y="x"), panel=1))
    poisoned = {name: values.copy() for name, values in columns.items()}
    poisoned["w"][0] = -1
    with pytest.raises(ValueError, match="finite nonnegative"):
        plot.dispatch(SetData(columns=poisoned))
    assert json.loads(plot.to_json()) == old
    ids = [panel.panel_id for panel in plot.spec.panels]
    plot.nest(1, 1).reorder_panels(ids[::-1])
    assert _rows(plot)[-1] == [0, 1, 3]
    assert len(mp.Plot.from_json(plot.to_json()).render().axes) == 6
    plot.dispatch(
        SetData(columns={name: [values[4]] for name, values in columns.items()})
    )
    assert _rows(plot) == [[] for _ in range(6)]
    assert len(plot.render().axes) == 6


def test_joint_clock_twin_scalar_and_strict_weighted_complement():
    dates = [
        "2024-01-01T12:00:00Z",
        "2024-01-01T07:00:00-05:00",
        "2024-01-02T12:00:00Z",
        "malformed",
        "2024-01-03T12:00:00Z",
    ]
    data = {
        "x": [1, 2, 4, 8, 16],
        "clock": dates,
        "c": [10, 20, 30, 40, None],
        "w": [1, 3, 4, 0, 8],
    }
    plot = (
        mp.Plot(data)
        .size(10, 6)
        .secondary_yaxis("Observed date")
        .date_axis("y2")
        .scatter(
            "x",
            "clock",
            c="c",
            axis="y2",
            colorbar=True,
        )
        .joint(
            marginal_kind="ecdf",
            marginal_stat="probability",
            complementary=True,
            weights="w",
        )
    )
    assert _rows(plot) == [[0, 1, 2]] * 3
    plot.secondary_yaxis("Edited UTC date")
    epoch = date(1970, 1, 1)
    limits = [(date(2024, 1, day) - epoch).days for day in (1, 3)]
    plot.dispatch(SetLimits("y2", *limits))
    assert json.loads(mp.Plot.from_json(plot.to_json()).to_json()) == json.loads(
        plot.to_json()
    )
    assert mp.apply(plot.action_log) == plot.spec
    fig = plot.render()
    center, right = fig.axes[:2]
    twin = center._mudplot_secondary_axis
    assert right.get_shared_y_axes().joined(right, twin)
    assert not right.get_shared_y_axes().joined(right, center)
    assert tuple(twin.collections[0].get_array()) == (10.0, 20.0, 30.0)
    assert tuple(right.lines[0].get_xdata()) == (1.0, 0.5, 0.0)
    assert right.get_ylim() == twin.get_ylim() == (19723.0, 19725.0)
    assert twin.get_ylabel() == "Edited UTC date"
    assert center.get_ylim() != right.get_ylim()


def test_joint_grouped_hexbin_uses_physical_occupancy_on_common_lattice():
    data = {
        "x": [0, 0, 1, 0, 0, 1, 1, 100],
        "y": [0, 0, 1, 0, 0, 1, 1, 100],
        "g": [True, True, True, 1, 1, 1, 1, 1],
        "w": [2, 3, 99, 4, 6, 7, 8, 0],
    }
    plot = (
        mp.Plot(data)
        .size(10, 7)
        .hexbin("x", "y", gridsize=5, mincnt=2)
        .joint(group="g", weights="w")
    )
    assert _rows(plot) == [list(range(7))] * 3
    fig = plot.render()
    artists = [a for a in fig.axes[0].collections if hasattr(a, "_mudplot_hex_field")]
    assert [list(a.get_array()) for a in artists] == [[5.0], [10.0, 15.0]]
    assert [type(a._mudplot_hex_field["group"]) for a in artists] == [bool, int]
    assert artists[0].norm is artists[1].norm
    assert artists[0].get_clim() == (0, 15)
    assert tuple(artists[0].get_offsets()[0]) == tuple(artists[1].get_offsets()[0])
    assert all(a._mudplot_hex_field["extent"] == (0, 1, 0, 1) for a in artists)
    # Independent native lattice: match offsets without rounding bins.
    from matplotlib import pyplot as plt

    f, ax = plt.subplots()
    try:
        direct = ax.hexbin(
            data["x"][:7], data["y"][:7], gridsize=5, extent=(0, 1, 0, 1), mincnt=1
        )
        assert {tuple(v) for v in artists[1].get_offsets()} == {
            tuple(v) for v in direct.get_offsets()
        }
    finally:
        plt.close(f)


def test_joint_weighted_histogram_and_kde_use_same_rows_before_bins():
    data = {
        "x": [0, 0, 1, 3, 0, 1, 1, 4, None, 2],
        "y": [0, 1, 0, 2, 0, 0, 1, 3, 0, 2],
        "g": [True] * 4 + [1] * 6,
        "w": [1, 2, 3, 4, 5, 6, 7, 8, 300, 0],
    }
    plot = (
        mp.Plot(data)
        .size(12, 8)
        .hist2d(
            "x",
            "y",
            bins=mp.BivariateBinsSpec(x=[-0.5, 0.5, 1.5], y=[-0.5, 0.5, 1.5]),
            stat="count",
            semantics=SemanticSpec(hue="g", hue_order=[True, 1]),
            kde=mp.KDE2DSpec(levels=[0.5], gridsize=24, cut=1),
            colorbar=False,
        )
        .joint(bins=4, marginal_stat="count", weights="w")
    )
    assert _rows(plot) == [list(range(8))] * 3
    fig = plot.render()
    meshes = [a for a in fig.axes[0].collections if hasattr(a, "_mudplot_field")]
    assert [a._mudplot_field["source_row_indices"] for a in meshes] == [
        (0, 1, 2, 3),
        (4, 5, 6, 7),
    ]
    assert [float(a.get_array().sum()) for a in meshes] == [6.0, 18.0]
    assert len(fig.axes[0].collections) > len(meshes)
    for marginal in fig.axes[1:3]:
        if marginal is fig.axes[1]:
            masses = [patch.get_width() for patch in marginal.patches]
        else:
            masses = [patch.get_height() for patch in marginal.patches]
        assert sum(masses) == 36.0


def test_weighted_pair_kde_diagonal_matches_its_own_univariate_view():
    data = {
        "x": [0.0, 1.0, 2.0, 4.0, 10.0],
        "y": [0.0, None, 3.0, 4.0, 10.0],
        "w": [1.0, 2.0, 3.0, 4.0, 0.0],
    }
    settings = mp.KDESpec(bw_method=0.8, gridsize=16, cut=0)
    pair = (
        mp.plot(data)
        .size(8, 8)
        .pair(["x", "y"], corner=True, weights="w", diag_kind="kde", kde=settings)
    )
    assert _rows(pair) == [[0, 1, 2, 3], [0, 2, 3], [0, 2, 3]]
    original = mp.plot({k: v[:4] for k, v in data.items()}).kde(
        "x", kde=mp.KDESpec(bw_method=0.8, gridsize=16, cut=0, weights="w")
    )
    observed = pair.render().axes[0].lines[0]
    expected = original.render().axes[0].lines[0]
    assert tuple(observed.get_xdata()) == tuple(expected.get_xdata())
    assert tuple(observed.get_ydata()) == pytest.approx(tuple(expected.get_ydata()))


@pytest.mark.parametrize("mapped", [False, True], ids=["plain", "semantic"])
def test_joint_raw_scatter_twin_owns_visible_right_y_after_reverse_edit(mapped):
    raw = {
        "x": [1, 2, 4, 8],
        "date": [
            "2024-01-01T12:00:00Z",
            "2024-01-01T07:00:00-05:00",
            "2024-01-02T12:00:00Z",
            "invalid zero-weight clock",
        ],
        "w": [1, 3, 4, 0],
        "arm": ["A", "B", "A", "B"],
    }
    roles = SemanticSpec(hue="arm") if mapped else None
    plot = (
        mp.plot(raw)
        .size(10, 7)
        .secondary_yaxis("Original time")
        .date_axis("y2")
        .scatter("x", "date", axis="y2", semantics=roles)
        .joint(weights="w", marginal_kind="ecdf", marginal_stat="probability")
        .secondary_yaxis("Observed UTC date")
    )
    epoch = date(1970, 1, 1)
    lo, hi = ((date(2024, 1, day) - epoch).days for day in (1, 3))
    plot.dispatch(SetLimits("y", lo, hi, panel=1))
    assert _rows(plot) == [[0, 1, 2]] * 3
    fig = plot.render()
    center, right = fig.axes[:2]
    twin = center._mudplot_secondary_axis
    assert right.get_shared_y_axes().joined(right, twin)
    assert twin.get_ylim() == right.get_ylim() == (lo, hi)
    assert center.get_ylim() != (lo, hi)
    assert twin.get_ylabel() == "Observed UTC date"
    assert any(
        label.get_visible() and label.get_text() for label in twin.get_yticklabels()
    )
    coordinates = sorted(
        tuple(point) for mark in twin.collections for point in mark.get_offsets()
    )
    assert coordinates == [(1, lo + 0.5), (2, lo + 0.5), (4, lo + 1.5)]
    assert plot.spec.data.columns == raw


def test_joint_mixed_y_axes_install_one_fixed_calendar_ticker():
    days = [19723, 19724, 19725]
    labels = ["Jan 1", "Jan 2", "Jan 3"]
    plot = (
        mp.plot({"x": [1, 2], "when": ["2024-01-01T00:00Z", "2024-01-03T00:00Z"]})
        .size(10, 7)
        .secondary_yaxis("UTC day")
        .date_axis("y2")
        .ticks(
            "y2",
            mp.TickSpec(
                locator=mp.LocatorSpec(kind="fixed", values=days),
                formatter=mp.FormatterSpec(kind="fixed", labels=labels),
                rotation=18,
            ),
        )
        .scatter("x", "when", axis="y2")
        .joint(weights=None, marginal_kind="ecdf", marginal_stat="count")
    )
    plot.dispatch(SetLimits("y", days[0], days[-1], panel=1))
    figure = plot.render()
    center, right = figure.axes[:2]
    twin = center._mudplot_secondary_axis
    locator = twin.yaxis.get_major_locator()
    assert right.yaxis.get_major_locator() is locator
    assert center.yaxis.get_major_locator() is not locator
    for ax in (twin, right):
        assert list(ax.get_yticks()) == days
        assert [label.get_text() for label in ax.get_yticklabels()] == labels
        assert [label.get_rotation() for label in ax.get_yticklabels()] == [18] * 3
