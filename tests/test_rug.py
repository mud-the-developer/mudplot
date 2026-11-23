"""D07 native geometry, independent limits, raw-row roles and product replay."""

from dataclasses import replace

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import LineCollection


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def segments(collection):
    return np.asarray(collection.get_segments())


def assert_dashes(actual, expected):
    assert len(actual) == len(expected)
    for (offset, dash), (ref_offset, ref_dash) in zip(actual, expected, strict=True):
        assert offset == ref_offset
        np.testing.assert_array_equal(dash, ref_dash)


@pytest.mark.parametrize(
    "orient,axis", [("v", "y"), ("h", "y"), ("v", "y2"), ("h", "y2")]
)
@pytest.mark.parametrize("scale", ["linear", "log", "date"])
@pytest.mark.parametrize("height", [None, 0, 0.17, 1])
def test_observation_transform_matches_native_and_live_axes_extent(
    orient, axis, scale, height
):
    values = [1, 4, 2, 4]
    source = {"observed": values, "id": ["r3", "r1", "r4", "r2"]}
    p = mp.plot(source).size(6, 4)
    if axis == "y2":
        p.secondary_yaxis("Other observations")
    p.rug(
        "observed",
        orient=orient,
        axis=axis,
        height=height,
        color="#3a6391",
        line_width=2,
        line_style="--",
        alpha=0.6,
    )
    dimension = "x" if orient == "v" else axis
    if scale == "date":
        p.date_axis(dimension, unit="day", origin="2026-01-01T00:00:00Z")
        values = [20455, 20458, 20456, 20458]
    elif scale == "log":
        if dimension == "y2":
            p.secondary_yaxis("Other observations", scale="log")
        else:
            (p.xscale if dimension == "x" else p.yscale)("log")
    fig = p.render()
    ax = fig.axes[int(axis == "y2")]
    col = ax.collections[0]
    h = 0.04 if height is None else height
    _, ref = plt.subplots()
    ref.set_xscale(ax.get_xscale())
    ref.set_yscale(ax.get_yscale())
    ref.set_xlim(ax.get_xlim())
    ref.set_ylim(ax.get_ylim())
    start = 1 if orient == "h" and axis == "y2" else 0
    end = 1 - h if start else h
    native = (
        ref.vlines(
            values,
            start,
            end,
            transform=ref.get_xaxis_transform(),
            colors="#3a6391",
            linewidths=2,
            linestyles="--",
            alpha=0.6,
        )
        if orient == "v"
        else ref.hlines(
            values,
            start,
            end,
            transform=ref.get_yaxis_transform(),
            colors="#3a6391",
            linewidths=2,
            linestyles="--",
            alpha=0.6,
        )
    )
    np.testing.assert_array_equal(segments(col), segments(native))
    np.testing.assert_array_equal(col.get_colors(), native.get_colors())
    np.testing.assert_array_equal(col.get_linewidths(), native.get_linewidths())
    assert_dashes(col.get_linestyles(), native.get_linestyles())
    fig.set_layout_engine(None)
    for dpi in [72, 180]:
        fig.set_dpi(dpi)
        fig.subplots_adjust(left=0.2, bottom=0.2, right=0.8, top=0.85)
        fig.canvas.draw()
        actual = (
            col.get_transform()
            .transform(segments(col).reshape(-1, 2))
            .reshape(-1, 2, 2)
        )
        observation = 0 if orient == "v" else 1
        reference = ax.transData.transform(np.column_stack((values, values)))[
            :, observation
        ]
        np.testing.assert_allclose(actual[:, 0, observation], reference)
        extent = ax.bbox.height if orient == "v" else ax.bbox.width
        np.testing.assert_allclose(
            abs(actual[:, 1, 1 - observation] - actual[:, 0, 1 - observation]),
            h * extent,
            atol=1e-10,
        )
        boundary = ax.bbox.y0 if orient == "v" else ax.bbox.x1 if start else ax.bbox.x0
        np.testing.assert_allclose(actual[:, 0, 1 - observation], boundary)
    assert p.spec.data.columns == source


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("perpendicular", ["linear", "log", "date"])
@pytest.mark.parametrize("rug_first", [False, True])
def test_rug_never_changes_unrelated_data_limits_or_automatic_limits(
    orient, perpendicular, rug_first
):
    source = {"position": [1, 2, 4], "value": [100, 200, 400]}
    # Both plots have genuinely automatic limits, not fixed explicit bounds.
    baseline = mp.plot(source).line("position", "value")
    observation = "position" if orient == "v" else "value"
    actual = mp.plot(source)
    if rug_first:
        actual.rug(observation, orient=orient, height=0.9)
    actual.line("position", "value")
    if not rug_first:
        actual.rug(observation, orient=orient, height=0.9)
    dimension = "y" if orient == "v" else "x"
    if perpendicular == "log":
        for p in [baseline, actual]:
            (p.yscale if dimension == "y" else p.xscale)("log")
    elif perpendicular == "date":
        for p in [baseline, actual]:
            p.date_axis(dimension, unit="day", origin="2026-01-01T00:00:00Z")
    b, a = baseline.render().axes[0], actual.render().axes[0]
    index = 1 if orient == "v" else 0
    np.testing.assert_array_equal(
        a.dataLim.get_points()[:, index], b.dataLim.get_points()[:, index]
    )
    np.testing.assert_array_equal(a.dataLim.minpos[index], b.dataLim.minpos[index])
    assert (a.get_ylim() if orient == "v" else a.get_xlim()) == (
        b.get_ylim() if orient == "v" else b.get_xlim()
    )
    assert actual.spec.data.columns == source


@pytest.mark.parametrize("orient", ["v", "h"])
def test_rug_and_density_share_observations_without_changing_density_frame(orient):
    data = {"v": [1, 2, 3, 4, 7]}
    baseline = mp.plot(data).kde("v", orient=orient)
    p = mp.Plot.from_json(baseline.to_json()).rug("v", orient=orient, height=1)
    b, a = baseline.render().axes[0], p.render().axes[0]
    density = 1 if orient == "v" else 0
    np.testing.assert_array_equal(
        a.dataLim.get_points()[:, density], b.dataLim.get_points()[:, density]
    )
    assert (a.get_ylim() if orient == "v" else a.get_xlim()) == (
        b.get_ylim() if orient == "v" else b.get_xlim()
    )


def test_independent_roles_retain_rows_and_use_one_stroke_collection():
    data = {
        "v": [4, 2, 2, 8, -1],
        "hue": [0, 1, 0, 1, None],
        "size": [0, 1, 0.5, 1, 1],
        "style": ["B", "A", "B", "A", "B"],
        "id": ["d", "c", "a", "b", "excluded"],
    }
    p = (
        mp.plot(data)
        .rug(
            "v",
            semantics={
                "hue": "hue",
                "hue_kind": "numeric",
                "size": "size",
                "sizes": [0, 4],
                "style": "style",
                "style_order": ["A", "reserved", "B"],
                "dashes": ["--", ":", "-."],
            },
        )
        .xscale("log")
    )
    fig = p.render()
    ax = fig.axes[0]
    assert len(ax.collections) == 1 and isinstance(ax.collections[0], LineCollection)
    col = ax.collections[0]
    np.testing.assert_array_equal(segments(col)[:, 0, 0], [4, 2, 2, 8])
    np.testing.assert_array_equal(col.get_linewidths(), [0, 4, 2, 4])
    np.testing.assert_array_equal(segments(col)[:, 1, 1], [0.04] * 4)
    # Positive strokes have the corresponding named native dash geometry.
    _, ref = plt.subplots()
    native = ref.vlines(
        [1, 2, 3], 0, 1, linewidths=[4, 2, 4], linestyles=["--", "-.", "--"]
    )
    assert_dashes(col.get_linestyles()[1:], native.get_linestyles())
    for line in ax.lines:
        assert len(line.get_xdata()) == 0 and line.get_marker() == "None"
    assert "style: style=reserved" not in ax.get_legend_handles_labels()[1]
    assert p.spec.data.columns == data


@pytest.mark.parametrize("height", [0, 0.3])
def test_zero_height_and_zero_mapped_strokes_with_dashes_keep_all_segments(height):
    p = mp.plot({"v": [1, 2, 3], "s": [0, 1, 0], "d": ["a", "b", "a"]}).rug(
        "v",
        height=height,
        semantics={"size": "s", "sizes": [0, 3], "style": "d", "dashes": ["--", ":"]},
    )
    fig = p.render()
    col = fig.axes[0].collections[0]
    np.testing.assert_array_equal(segments(col)[:, 0, 0], [1, 2, 3])
    np.testing.assert_array_equal(col.get_linewidths(), [0, 3, 0])
    np.testing.assert_array_equal(segments(col)[:, 1, 1], [height] * 3)


def test_rug_shared_raw_domains_and_logical_panel_colorbar_with_y2():
    data = {"v": [1, 2, 3], "y": [10, 20, 30], "h": [-10, 0, 10], "s": [1, 2, 3]}
    mapping = {
        "scale_id": "scope",
        "hue": "h",
        "hue_kind": "numeric",
        "size": "s",
        "sizes": [1, 5],
    }
    p = (
        mp.plot(data)
        .scatter("v", "y", semantics=mapping)
        .secondary_yaxis("Observations")
    )
    p.rug("v", orient="h", axis="y2", semantics=mapping, colorbar=True)
    p.rug("v", semantics=mapping)
    fig = p.render()
    a, a2, bar = fig.axes
    assert a.get_position().bounds == a2.get_position().bounds
    assert [t.get_text() for t in bar.get_yticklabels()] == ["-10.0", "0.0", "10.0"]
    col = a2.collections[0]
    np.testing.assert_array_equal(col.get_linewidths(), [1, 3, 5])
    np.testing.assert_allclose(col.get_colors(), a.collections[0].get_facecolors())
    assert not any(
        label.startswith("hue:")
        for label in a.get_legend_handles_labels()[1]
        + a2.get_legend_handles_labels()[1]
    )


def test_rug_does_not_partition_or_cap_distinct_numeric_role_tuples():
    n = 301
    data = {"v": list(range(n)), "h": list(range(n)), "s": list(range(n))}
    p = mp.plot(data).rug(
        "v",
        semantics={"hue": "h", "hue_kind": "numeric", "hue_norm": [0, 1], "size": "s"},
    )
    col = p.render().axes[0].collections[0]
    np.testing.assert_array_equal(segments(col)[:, 0, 0], data["v"])
    assert len(col.get_colors()) == n
    np.testing.assert_array_equal(col.get_colors()[1], col.get_colors()[-1])
    assert p.spec.data.columns == data


@pytest.mark.parametrize("semantic", [False, True])
def test_empty_and_reserved_facets_keep_raw_ids_and_semantic_global_domain(semantic):
    data = {
        "v": [3, 1, 2, 4],
        "g": ["b", "a", "b", "a"],
        "id": ["r4", "r2", "r1", "r3"],
        "s": [0, 1, 2, 3],
    }
    p = (
        mp.plot(data)
        .size(12, 4)
        .rug(
            "v",
            **(
                {"semantics": {"size": "s", "sizes": [1, 4], "scale_id": "all"}}
                if semantic
                else {"group": "g", "hue_order": ["a", "empty", "b"]}
            ),
        )
        .facet(col="g", col_order=["a", "empty", "b"])
    )
    fig = p.render()
    assert [len(ax.collections) for ax in fig.axes] == (
        [1, 1, 1] if semantic else [1, 0, 1]
    )
    for ax, expected in zip(fig.axes, [[1, 4], [], [3, 2]], strict=True):
        observed = [
            segment[0, 0] for c in ax.collections for segment in c.get_segments()
        ]
        assert observed == expected
    if semantic:
        np.testing.assert_array_equal(
            fig.axes[0].collections[0].get_linewidths(), [2, 4]
        )
        np.testing.assert_array_equal(
            fig.axes[2].collections[0].get_linewidths(), [1, 3]
        )
    assert p.spec.data.columns == data
    empty = mp.plot({"v": []}).rug("v").render().axes[0]
    assert len(empty.collections[0].get_segments()) == 0
    np.testing.assert_array_equal(
        empty.dataLim.get_points(), [[np.inf, np.inf], [-np.inf, -np.inf]]
    )


@pytest.mark.parametrize(
    "options",
    [
        {"height": True},
        {"height": -0.1},
        {"height": 1.1},
        {"height": float("nan")},
        {"orient": "diagonal"},
        {"axis": "y2"},
        {"semantics": {"hue": "h"}, "group": "h"},
        {"semantics": {"hue": "h"}, "color": "red"},
        {"semantics": {"size": "s"}, "line_width": 1},
        {"semantics": {"style": "h"}, "line_style": ":"},
        {"semantics": {"style": "h", "dashes": ["-"]}},
        {"weights": "s"},
    ],
)
def test_invalid_rug_options_reject_at_render(options):
    p = mp.plot({"v": [1, 2], "h": ["a", "b"], "s": [1, 2]}).rug("v", **options)
    with pytest.raises(ValueError):
        p.render()


def test_builder_action_edit_history_save_reopen_geometry(tmp_path):
    p = mp.plot({"v": [4, 1, 4], "h": ["a", "b", "a"]}).rug(
        "v", height=0.2, semantics={"style": "h"}
    )
    initial = p.to_json()
    p.dispatch(mp.actions.RemoveLayer(0))
    p.dispatch(
        mp.actions.AddLayer(
            replace(
                mp.Plot.from_json(initial).spec.panels[0].layers[0],
                orient="h",
                width=0.35,
            )
        )
    )
    edited = p.to_json()
    p.store.undo()
    p.store.undo()
    assert p.to_json() == initial
    p.store.redo()
    p.store.redo()
    assert p.to_json() == edited
    target = tmp_path / "rug.mplot.json"
    mp.save_spec(p.spec, target)
    reopened = mp.Plot.from_json(mp.to_json(mp.load_spec(target)))
    assert reopened.spec == mp.apply(p.action_log) == p.spec
    col = reopened.render().axes[0].collections[0]
    np.testing.assert_array_equal(
        segments(col), [[[0, 4], [0.35, 4]], [[0, 1], [0.35, 1]], [[0, 4], [0.35, 4]]]
    )


@pytest.mark.parametrize("orient", ["v", "h"])
def test_observation_date_clock_does_not_parse_perpendicular_date_units(orient):
    data = {
        "when": ["2026-01-03T00:00:00+02:00", "2026-01-01T00:00:00Z", None],
        "value": [20, 10, None],
        "id": ["late", "early", "missing"],
    }
    p = mp.plot(data).rug("when", orient=orient, height=0.25)
    p.date_axis("x" if orient == "v" else "y", timezone="UTC")
    p.date_axis("y" if orient == "v" else "x", unit="s", origin="1980-01-01T00:00:00Z")
    col = p.render().axes[0].collections[0]
    observed = [
        segment[0, 0 if orient == "v" else 1]
        for segment in col.get_segments()
        if len(segment)
    ]
    np.testing.assert_allclose(observed, [20456 - 2 / 24, 20454], rtol=0, atol=1e-10)
    assert p.spec.data.columns == data


def test_semantic_row_bound_and_distinct_dash_bound_reject_without_sampling():
    p = mp.plot({"v": list(range(10001)), "s": [1] * 10001}).rug(
        "v", semantics={"size": "s"}
    )
    assert any("10000" in issue for issue in mp.validate(p.spec))
    with pytest.raises(ValueError):
        p.render()
    assert len(p.spec.data.columns["v"]) == 10001
    p = mp.plot({"v": [1, 2, 3, 4, 5], "style": ["a", "b", "c", "d", "e"]}).rug(
        "v", semantics={"style": "style"}
    )
    with pytest.raises(ValueError, match="distinct dashes"):
        p.render()
