"""Explicit live-template transactions versus authoritative local saved views."""

import copy
import json
from dataclasses import replace

import mudplot as mp
import numpy as np
import pytest
from dashboard.editor_server import EditorSession

from test_swarm_workflow import assert_paths


def source():
    return {
        "c": ["a", "a", "b", "b"],
        "v": [1, 1.01, 2, 2.01],
        "other": [1.02, 1.03, 2.02, 2.03],
        "cohort": ["left", "left", "right", "right"],
        "old": ["A", "B", "A", "B"],
        "new": ["U", "V", "U", "V"],
        "id": ["l2", "l1", "r2", "r1"],
    }


def live_plot(**options):
    p = mp.plot(source()).size(10, 6)
    for value in ["v", "other"]:
        p.swarmplot("c", value, pack_scope="members", marker_size=5, **options)
    return p.facet(
        col="cohort", col_order=["left", "empty", "right"], col_wrap=2, live=True
    )


def test_local_edit_saved_truth_and_explicit_template_replacement_native_history(
    tmp_path,
):
    p = live_plot()
    initial = p.to_json()
    local = replace(p.spec.panels[0].layers[0], marker="D")
    p.dispatch(mp.actions.RemoveLayer(0, panel=0)).dispatch(
        mp.actions.AddLayer(local, panel=0)
    )
    p.dispatch(mp.actions.SetTitle("Only local", panel=0))
    local_json = p.to_json()
    mp.save_spec(p.spec, tmp_path / "local.json")
    reopened = mp.Plot.from_json((tmp_path / "local.json").read_text())
    fig = reopened.render()
    assert_paths(fig.axes[0].collections[-1], ["D"] * 2)
    assert_paths(fig.axes[2].collections[0], ["o"] * 2)
    assert reopened.spec.panels[0].title == "Only local"
    assert p.spec.facet_template.template.layers[0].marker is None
    template = copy.deepcopy(reopened.spec.facet_template.template)
    for layer in template.layers:
        layer.marker = "s"
        layer.marker_size = 8
    reopened.facet_template(template)
    edited = reopened.to_json()
    fig = reopened.render()
    for panel, expected in [(0, [1, 1.01]), (2, [2, 2.01])]:
        collection = fig.axes[panel].collections[0]
        assert_paths(collection, ["s"] * 2)
        np.testing.assert_array_equal(collection.get_sizes(), [64])
        np.testing.assert_array_equal(
            np.asarray(collection.get_offsets())[:, 1], expected
        )
    assert len(fig.axes[1].collections) == 0
    assert all(layer.marker == "s" for layer in reopened.spec.panels[1].layers)
    assert reopened.spec.panels[0].title != "Only local"
    reopened.store.undo()
    assert reopened.to_json() == local_json
    undone = reopened.render()
    assert_paths(undone.axes[0].collections[-1], ["D"] * 2)
    reopened.store.redo()
    assert reopened.to_json() == edited
    assert reopened.spec.data.columns == source()
    assert mp.apply(p.action_log) == p.spec
    assert initial != local_json


def test_wrapped_partial_grid_ratio_edit_preserves_fixed_cells_and_native_frames():
    p = live_plot()
    selectors = copy.deepcopy(p.spec.facet_template.selectors)
    p.layout(2, 2, width_ratios=[2, 1], height_ratios=[1, 2])
    p.layout(2, 2, width_ratios=[3, 1])
    template = copy.deepcopy(p.spec.facet_template.template)
    for layer in template.layers:
        layer.marker = "^"
    p.facet_template(template)
    fig = p.render()
    assert len(p.spec.panels) == len(fig.axes) == 3
    assert p.spec.facet_template.selectors == selectors
    assert p.spec.width_ratios == [3, 1] and p.spec.height_ratios == [1, 2]
    assert fig.axes[0].bbox.width / fig.axes[1].bbox.width == pytest.approx(3)
    assert fig.axes[2].bbox.height / fig.axes[0].bbox.height == pytest.approx(2)
    assert_paths(fig.axes[0].collections[0], ["^"] * 2)
    p.layout(1, 3)
    assert p.spec.facet_template is None
    ordinary = (
        mp.plot(source())
        .swarmplot("c", "v")
        .facet(col="cohort", col_order=["left", "empty", "right"], col_wrap=2)
    )
    ordinary.layout(2, 2)
    assert len(ordinary.spec.panels) == 4  # Existing non-live SetLayout expansion.


def test_new_data_and_explicit_order_reset_keep_fixed_cells():
    p = live_plot()
    selectors = copy.deepcopy(p.spec.facet_template.selectors)
    data = {
        "c": ["a", "c", "a"],
        "v": [1, 2, 3],
        "other": [1.01, 2.01, 3.01],
        "cohort": ["empty", "left", "excluded"],
        "old": ["A"] * 3,
        "new": ["U"] * 3,
        "id": ["fill-reserved", "new-category", "new-facet"],
    }
    p.dispatch(mp.actions.SetData(data))
    fig = p.render()
    assert len(fig.axes) == 3 and [q.filters for q in p.spec.panels] == selectors
    assert len(fig.axes[0].collections) == len(fig.axes[2].collections) == 0
    np.testing.assert_array_equal(
        np.asarray(fig.axes[1].collections[0].get_offsets())[:, 1], [1]
    )
    template = copy.deepcopy(p.spec.facet_template.template)
    for layer in template.layers:
        layer.marker = "s"
    p.facet_template(template)
    assert p.spec.panels[0].layers[0].order == ["a", "b"]
    for layer in template.layers:
        layer.order = None
    p.facet_template(template, reset_orders=True)
    fig = p.render()
    np.testing.assert_array_equal(
        np.asarray(fig.axes[0].collections[0].get_offsets())[:, 1], [2]
    )
    assert p.spec.panels[0].layers[0].order == ["a", "c"]
    assert len(fig.axes) == 3 and p.spec.data.columns == data


@pytest.mark.parametrize("semantic", [False, True])
def test_role_channel_change_resolves_its_own_hue_slots_without_erasing_rows(semantic):
    options = {"semantics": {"hue": "old"}} if semantic else {"group": "old"}
    p = live_plot(**options)
    template = copy.deepcopy(p.spec.facet_template.template)
    for layer in template.layers:
        if semantic:
            layer.semantics.hue = "new"
            layer.semantics.hue_order = None
        else:
            layer.group = "new"
            layer.hue_order = None
    p.facet_template(template)
    fig = p.render()
    for panel in [0, 2]:
        assert [len(c.get_offsets()) for c in fig.axes[panel].collections] == [2, 2]
        np.testing.assert_array_equal(
            np.asarray(fig.axes[panel].collections[0].get_offsets())[:, 1],
            [1, 1.01] if panel == 0 else [2, 2.01],
        )
    orders = [
        layer.semantics.hue_order if semantic else layer.hue_order
        for layer in p.spec.facet_template.template.layers
    ]
    assert orders == [["U", "V"], ["U", "V"]]


def test_future_recipe_validates_frozen_views_not_undrawn_global_template():
    p = mp.plot(source()).size(12, 6).swarmplot("c", "v", marker_size=1, line_width=0)
    p.facet(col="cohort", col_order=["left", "right", "empty"], live=True)
    n = 1500
    data = {
        "c": ["a"] * (2 * n + 1),
        "v": list(range(n)) * 2 + ["not a numeric observation"],
        "cohort": ["left"] * n + ["right"] * n + ["excluded"],
        "id": list(range(2 * n + 1)),
    }
    p.dispatch(mp.actions.SetData(data))
    fig = p.render()
    assert [sum(len(c.get_offsets()) for c in ax.collections) for ax in fig.axes] == [
        n,
        n,
        0,
    ]
    template = copy.deepcopy(p.spec.facet_template.template)
    template.layers[0].marker = "s"
    p.facet_template(template)
    fig = p.render()
    assert_paths(fig.axes[0].collections[0], ["s"] * n)
    np.testing.assert_array_equal(
        np.asarray(fig.axes[1].collections[0].get_offsets())[:, 1], list(range(n))
    )
    assert p.spec.data.columns["v"][-1] == "not a numeric observation"
    data["v"][0] = "invalid inside a selected cell"
    p.dispatch(mp.actions.SetData(data))
    with pytest.raises(ValueError):
        p.render()


@pytest.mark.parametrize("corruption", ["selectors", "count", "layout", "recipe"])
def test_inconsistent_saved_live_recipe_rejects_without_silently_detaching(corruption):
    raw = json.loads(live_plot().to_json())
    if corruption == "selectors":
        raw["facet_template"]["selectors"][0] = {"cohort": "other"}
    elif corruption == "count":
        raw["panels"].pop()
    elif corruption == "layout":
        raw["layout"] = [1, 3]
    else:
        raw["facet_template"]["col_order"] = ["left", "right"]
    p = mp.Plot.from_json(json.dumps(raw))
    with pytest.raises(ValueError):
        p.render()
    assert p.spec.facet_template is not None


def test_invalid_template_safe_edit_keeps_accepted_native_png_spec_and_history():
    p = live_plot()
    session = EditorSession()
    session.load_spec(p.to_json())
    before = session.store.state.to_dict()
    png = session.png
    history = session.store.history
    template = copy.deepcopy(p.spec.facet_template.template)
    template.layers[0].width = 2
    session.dispatch_safe(mp.actions.SetFacetTemplate(template))
    assert session.error is not None
    assert session.store.state.to_dict() == before and session.png == png
    assert session.store.history == history


def test_live_secondary_date_swarm_cells_keep_clocks_rows_and_reserved_slots():
    data = {
        "c": ["a"] * 4,
        "when": ["2026-01-01", "2026-01-01", "2026-01-03", "2026-01-03"],
        "cohort": ["left", "left", "right", "right"],
        "id": ["l1", "l2", "r1", "r2"],
    }
    p = mp.plot(data).size(12, 5).secondary_yaxis("Observed date")
    p.date_axis("y2", timezone="UTC")
    for _ in range(2):
        p.swarmplot("c", "when", axis="y2", pack_scope="s")
    p.facet(col="cohort", col_order=["left", "empty", "right"], live=True)
    template = copy.deepcopy(p.spec.facet_template.template)
    for layer in template.layers:
        layer.marker = "s"
    p.facet_template(template)
    figure = p.render()
    axes = [ax for ax in figure.axes if ax.get_ylabel() == "Observed date"]
    assert [len(ax.collections) for ax in axes] == [2, 0, 2]
    for index, day in [(0, 20454), (2, 20456)]:
        for collection in axes[index].collections:
            np.testing.assert_array_equal(
                np.asarray(collection.get_offsets())[:, 1], [day, day]
            )
            assert_paths(collection, ["s", "s"])
    assert p.spec.panels[0].y2.temporal.timezone == "UTC"
    assert p.spec.data.columns == data
