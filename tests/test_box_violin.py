"""Distribution summaries, categorical geometry and safe native controls."""

from __future__ import annotations

import json
from functools import wraps
from typing import Any

import matplotlib

matplotlib.use("Agg")

import mudplot as mp
import numpy as np
import pytest
from matplotlib.axes import Axes
from matplotlib.collections import PolyCollection
from mudplot._categorical import distribution_rows
from mudplot._render import _count_colors
from mudplot.spec import LayerSpec


def _data():
    return {
        "cat": ["B", "B", "A", "A"] * 2,
        "value": [1, 3, 2, 4, 3, 5, 4, 6],
        "hue": ["u"] * 4 + ["v"] * 4,
    }


def _bodies(ax, kind) -> list[Any]:
    return (
        list(ax.patches)
        if kind == "box"
        else [c for c in ax.collections if isinstance(c, PolyCollection)]
    )


def _vertices(body, kind):
    path = body.get_path() if kind == "box" else body.get_paths()[0]
    return np.asarray(path.vertices)


@pytest.mark.parametrize("kind", ["box", "violin"])
def test_legacy_one_column_coordinates_defaults_and_old_json_are_preserved(kind):
    p = getattr(mp.plot(_data()), kind)("value", group="hue")
    ax = p.render().axes[0]
    centers = [
        (_vertices(b, kind)[:, 0].min() + _vertices(b, kind)[:, 0].max()) / 2
        for b in _bodies(ax, kind)
    ]
    np.testing.assert_allclose(centers, [1, 2])
    assert [t.get_text() for t in ax.get_xticklabels()] == ["u", "v"]
    assert len({b.get_hatch() for b in _bodies(ax, kind)}) == 2
    layer = LayerSpec.from_dict({"type": kind, "x": "value", "group": "hue"})
    assert isinstance(layer, LayerSpec)
    assert layer.y == "" and layer.width is None and layer.showmeans is None
    assert mp.Plot.from_json(p.to_json()).spec == p.spec
    assert mp.apply(p.action_log) == p.spec


@pytest.mark.parametrize("kind", ["box", "violin"])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_nested_geometry_reserves_orders_and_reuses_hue_colors_and_hatches(
    kind, orient
):
    p = getattr(mp.plot(_data()), kind)(
        "cat",
        "value",
        group="hue",
        order=["A", "empty", "B"],
        hue_order=["v", "u", "absent"],
        orient=orient,
        gap=0.25,
    )
    assert mp.validate(p.spec) == []
    assert _count_colors(p.spec) == 3
    ax = p.render().axes[0]
    bodies = _bodies(ax, kind)
    assert len(bodies) == 4  # No fake distribution for an empty cell.
    coords = [_vertices(b, kind)[:, int(orient == "h")] for b in bodies]
    centers = [(c.max() + c.min()) / 2 for c in coords]
    np.testing.assert_allclose(centers, [-0.8 / 3, 2 - 0.8 / 3, 0, 2], atol=1e-15)
    if kind == "box":
        np.testing.assert_allclose([c.max() - c.min() for c in coords], [0.2] * 4)
    labels = ax.get_yticklabels() if orient == "h" else ax.get_xticklabels()
    assert [t.get_text() for t in labels] == ["A", "empty", "B"]
    assert ax.get_legend_handles_labels()[1] == ["v", "u"]
    np.testing.assert_allclose(bodies[0].get_facecolor(), bodies[1].get_facecolor())
    assert bodies[0].get_hatch() == bodies[1].get_hatch() != bodies[2].get_hatch()
    assert mp.Plot.from_json(p.to_json()).spec == p.spec
    assert mp.apply(p.action_log) == p.spec


@pytest.mark.parametrize("kind", ["box", "violin"])
def test_zero_dodge_overlays_hues_without_dividing_width(kind):
    ax = (
        getattr(mp.plot(_data()), kind)(
            "cat",
            "value",
            group="hue",
            dodge=0,
            width=0.6,
        )
        .render()
        .axes[0]
    )
    coords = [_vertices(b, kind)[:, 0] for b in _bodies(ax, kind)]
    np.testing.assert_allclose([(c.min() + c.max()) / 2 for c in coords], [0, 1, 0, 1])
    if kind == "box":
        np.testing.assert_allclose([c.max() - c.min() for c in coords], [0.6] * 4)


@pytest.mark.parametrize("orient", ["v", "h"])
def test_box_quartiles_whiskers_percentiles_notches_and_outliers_match_native(orient):
    data = {"cat": ["A"] * 6, "value": [0, 1, 2, 3, 4, 100]}
    p = mp.plot(data).box(
        "cat",
        "value",
        whis=(0, 100),
        orient=orient,
        showmeans=True,
        notch=True,
        edge_color="#112233",
        line_width=0.7,
    )
    assert p.spec.panels[0].layers[0].whis == [0, 100]
    ax = p.render().axes[0]
    value_axis = 0 if orient == "h" else 1
    median = ax.lines[4]
    np.testing.assert_allclose(
        np.asarray(median.get_xdata() if value_axis == 0 else median.get_ydata()),
        [2.5, 2.5],
    )
    whisker_values = [
        np.asarray(line.get_xdata() if value_axis == 0 else line.get_ydata())
        for line in ax.lines[:2]
    ]
    np.testing.assert_allclose(whisker_values, [[1.25, 0], [3.75, 100]])
    assert all(line.get_linewidth() == 0.7 for line in ax.lines[:5])
    assert len(np.asarray(ax.lines[5].get_xdata())) == 1  # requested mean marker
    assert (
        len(np.asarray(ax.lines[6].get_xdata())) == 0
    )  # full-range whiskers have no fliers
    assert (
        len(np.asarray(ax.patches[0].get_path().vertices)) == 12
    )  # native notched box
    default = mp.plot(data).box("cat", "value").render().axes[0]
    np.testing.assert_allclose(np.asarray(default.lines[-1].get_ydata()), [100])
    hidden = mp.plot(data).box("cat", "value", showfliers=False).render().axes[0]
    assert len(hidden.lines) == 5


@pytest.mark.parametrize("kind", ["box", "violin"])
def test_missing_rows_are_dropped_listwise_and_orders_filter_observations(kind):
    data = {
        "cat": ["A", "A", "A", "B", None, "A"],
        "value": [1, 3, None, 20, 50, 100],
        "hue": ["u", "u", "u", "v", "u", None],
    }
    p = getattr(mp.plot(data), kind)(
        "cat", "value", group="hue", order=["A"], hue_order=["u"]
    )
    assert mp.validate(p.spec) == []
    layer = p.spec.panels[0].layers[0]
    assert distribution_rows(p.spec.data.columns, layer) == [0, 1]
    ax = p.render().axes[0]
    assert len(_bodies(ax, kind)) == 1
    vertices = _vertices(_bodies(ax, kind)[0], kind)
    if kind == "box":
        assert vertices[:, 1].min() == 1.5 and vertices[:, 1].max() == 2.5
    else:
        assert vertices[:, 1].min() == 1 and vertices[:, 1].max() == 3


@pytest.mark.parametrize("kind", ["box", "violin"])
@pytest.mark.parametrize("values", [[4], [4, 4, 4]])
def test_constant_and_singleton_cells_are_real_degenerate_distributions(kind, values):
    ax = (
        getattr(mp.plot({"x": ["A"] * len(values), "y": values}), kind)("x", "y")
        .render()
        .axes[0]
    )
    vertices = _vertices(_bodies(ax, kind)[0], kind)
    assert np.isfinite(vertices).all()
    assert (vertices[:, 1] == 4).all()


def test_violin_named_numeric_bandwidth_grid_and_inner_flags_are_forwarded(monkeypatch):
    captured: list[dict[str, Any]] = []
    native = Axes.violinplot

    @wraps(native)
    def record(self, dataset, **kwargs):
        captured.append(kwargs)
        return native(self, dataset, **kwargs)

    monkeypatch.setattr(Axes, "violinplot", record)
    for bandwidth in ("silverman", 0.4):
        ax = (
            mp.plot(_data())
            .violin(
                "cat",
                "value",
                bw_method=bandwidth,
                points=51,
                showmeans=True,
                showmedians=False,
                showextrema=False,
                edge_color="#112233",
                line_width=0,
            )
            .render()
            .axes[0]
        )
        assert captured[-1]["bw_method"] == bandwidth
        assert captured[-1]["points"] == 51
        assert captured[-1]["showmeans"] is True
        assert captured[-1]["showmedians"] is False
        assert captured[-1]["showextrema"] is False
        assert len(ax.collections) == 3  # two bodies + mean bars only
        assert len(_bodies(ax, "violin")[0].get_paths()[0].vertices) == 105
        assert all(np.atleast_1d(c.get_linewidth())[0] == 0 for c in ax.collections)


@pytest.mark.parametrize("kind", ["box", "violin"])
@pytest.mark.parametrize(
    "options,message",
    [
        ({"orient": "horizontal"}, "orient"),
        ({"width": 0}, "width"),
        ({"width": True}, "width"),
        ({"gap": 1}, "gap"),
        ({"dodge": True}, "dodge"),
        ({"order": []}, "nonempty"),
        ({"order": ["A", "A"]}, "unique"),
        ({"hue_order": ["u"]}, "hue_order requires"),
        ({"showmeans": 1}, "boolean"),
        ({"stack": True}, "not supported"),
        ({"stat": mp.StatSpec()}, "not supported"),
    ],
)
def test_bad_common_options_fail_explicitly(kind, options, message):
    p = getattr(mp.plot(_data()), kind)("cat", "value", **options)
    assert any(message in issue for issue in mp.validate(p.spec))
    with pytest.raises(ValueError):
        p.render()


@pytest.mark.parametrize(
    "kind,options,message",
    [
        ("box", {"whis": -1}, "whis"),
        ("box", {"whis": [95, 5]}, "whis"),
        ("box", {"whis": [5, 101]}, "whis"),
        ("box", {"whis": True}, "whis"),
        ("box", {"notch": "yes"}, "boolean"),
        ("box", {"bw_method": "scott"}, "not supported"),
        ("violin", {"bw_method": 0}, "bw_method"),
        ("violin", {"bw_method": "auto"}, "bw_method"),
        ("violin", {"bw_method": True}, "bw_method"),
        ("violin", {"points": 1}, "points"),
        ("violin", {"points": 1001}, "points"),
        ("violin", {"points": True}, "points"),
        ("violin", {"whis": 1}, "not supported"),
        ("violin", {"showfliers": False}, "not supported"),
    ],
)
def test_native_controls_are_bounded_named_and_kind_specific(kind, options, message):
    p = getattr(mp.plot(_data()), kind)("cat", "value", **options)
    assert any(message in issue for issue in mp.validate(p.spec))


@pytest.mark.parametrize("kind", ["box", "violin"])
@pytest.mark.parametrize(
    "values,message",
    [
        ([1, float("inf")], "finite numbers"),
        ([1, True], "finite numbers"),
        ([1, "2"], "finite numbers"),
        ([None, float("nan")], "no usable"),
    ],
)
def test_invalid_or_all_missing_observations_fail_before_matplotlib(
    kind, values, message
):
    p = getattr(mp.plot({"x": ["A", "A"], "y": values}), kind)("x", "y")
    assert any(message in issue for issue in mp.validate(p.spec))


@pytest.mark.parametrize("kind", ["box", "violin"])
def test_nested_shared_categories_align_with_statistical_layers(kind):
    p = mp.plot(_data()).barplot("cat", "value", order=["A", "B"], errorbar=None)
    getattr(p, kind)("cat", "value", order=["A", "B"], width=0.5)
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    bodies = _bodies(ax, kind)[2:] if kind == "box" else _bodies(ax, kind)
    vertices = [_vertices(b, kind)[:, 0] for b in bodies]
    np.testing.assert_allclose([(v.min() + v.max()) / 2 for v in vertices], [0, 1])
    bad = mp.plot(_data()).barplot("cat", "value", order=["A", "B"], errorbar=None)
    getattr(bad, kind)("cat", "value", order=["B", "A"])
    with pytest.raises(ValueError, match="conflicting category order"):
        bad.render()


@pytest.mark.parametrize("kind", ["box", "violin"])
def test_legacy_order_selects_groups_and_nested_routes_scales_are_not_ignored(kind):
    p = getattr(mp.plot(_data()), kind)(
        "value", group="hue", order=["v", "empty", "u"], orient="h"
    )
    assert mp.validate(p.spec) == []
    assert [t.get_text() for t in p.render().axes[0].get_yticklabels()] == [
        "v",
        "empty",
        "u",
    ]
    for options in ({"axis": "y2"}, {"value_labels": True}):
        q = getattr(mp.plot(_data()), kind)("cat", "value", **options)
        assert any(
            "not supported" in i or "axis routing" in i for i in mp.validate(q.spec)
        )
    q = getattr(mp.plot(_data()), kind)("cat", "value").yscale("log")
    assert mp.validate(q.spec) == []
    assert q.render().axes[0].get_yscale() == "log"
    q = getattr(mp.plot(_data()), kind)("cat", "value").xscale("log")
    assert any("requires native_scale" in i for i in mp.validate(q.spec))


@pytest.mark.parametrize("kind", ["box", "violin"])
def test_distribution_controls_survive_schema_actions_and_editor_png(kind):
    import jsonschema
    from dashboard.editor_server import EditorSession, _build_action
    from mudplot import actions as A

    controls = (
        {"whis": [5, 95], "showfliers": False}
        if kind == "box"
        else {
            "bw_method": "silverman",
            "points": 51,
            "showextrema": False,
        }
    )
    session = EditorSession()
    session.dispatch_safe(A.SetData(_data()))
    action = _build_action(
        "add_layer_json",
        {
            "layer_type": kind,
            "layer_json": json.dumps(
                {
                    "x": "cat",
                    "y": "value",
                    "group": "hue",
                    "orient": "h",
                    "order": ["A", "B"],
                    **controls,
                }
            ),
        },
        session.store.state,
    )
    session.dispatch_safe(action)
    assert session.error is None and session.png.startswith(b"\x89PNG")
    jsonschema.Draft202012Validator(mp.json_schema()).validate(
        session.store.state.to_dict()
    )
    replay = mp.apply([A.action_to_dict(a) for a in session.store.history])
    assert replay == session.store.state
    assert mp.Plot.from_json(mp.to_json(replay)).spec == replay


def test_notched_boxes_ignore_ambient_bootstrap_without_consuming_global_rng():
    before = np.random.get_state()
    with matplotlib.rc_context({"boxplot.bootstrap": 101}):
        mp.plot(_data()).box("cat", "value", notch=True).render()
        assert matplotlib.rcParams["boxplot.bootstrap"] == 101
    after = np.random.get_state()
    assert before[0] == after[0] and before[2:] == after[2:]
    np.testing.assert_array_equal(before[1], after[1])


def test_nested_distribution_exports_are_repeatable_and_specs_editable(tmp_path):
    import matplotlib.pyplot as plt

    p = mp.plot(_data()).theme("publication").layout(1, 2)
    p.box("cat", "value", group="hue", whis=(5, 95), notch=True, panel=0)
    p.violin("cat", "value", group="hue", orient="h", bw_method="silverman", panel=1)
    for fmt in ("png", "svg"):
        first, second = tmp_path / f"a.{fmt}", tmp_path / f"b.{fmt}"
        plt.close(p.save(str(first)))
        plt.close(p.save(str(second)))
        assert first.read_bytes() == second.read_bytes()
    path = tmp_path / "editable.mplot.json"
    mp.save_spec(p.spec, path)
    assert mp.load_spec(path) == p.spec
