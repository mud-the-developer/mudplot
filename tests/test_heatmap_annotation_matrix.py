"""Custom display text and tick angles never replace scalar heatmap data."""

from __future__ import annotations

import copy

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def build(config):
    return mp.plot().matrix("m", [[1, 10], [100, 1000]]).heatmap("m", heatmap=config)


def test_text_coordinates_mask_norm_and_rotations_are_independent_of_values():
    config = {
        "annot": True,
        "annot_data": [["north", "hidden"], ["", "south"]],
        "mask": [[False, True], [False, False]],
        "norm": "log",
        "xlabels": ["A", "B"],
        "ylabels": ["C", "D"],
        "xrotation": -45,
        "yrotation": 90,
    }
    original = copy.deepcopy(config)
    p = build(config)
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    assert [(t.get_text(), t.get_position()) for t in ax.texts] == [
        ("north", (0, 0)),
        ("", (0, 1)),
        ("south", (1, 1)),
    ]
    assert all(t.get_rotation() == 315 for t in ax.get_xticklabels())
    assert all(t.get_rotation() == 90 for t in ax.get_yticklabels())
    image = ax.images[0]
    np.testing.assert_array_equal(image.get_array().data, [[1, 10], [100, 1000]])
    assert image.get_clim() == (1, 1000)
    assert p.spec.data.matrices["m"] == [[1, 10], [100, 1000]]
    assert config == original
    assert mp.apply(p.action_log) == mp.Plot.from_json(p.to_json()).spec == p.spec


@pytest.mark.parametrize("rotation", [-360, 0, 360])
def test_tick_angles_apply_without_explicit_labels(rotation):
    ax = build({"xrotation": rotation, "yrotation": rotation}).render().axes[0]
    assert all(t.get_rotation() == rotation % 360 for t in ax.get_xticklabels())
    assert all(t.get_rotation() == rotation % 360 for t in ax.get_yticklabels())


@pytest.mark.parametrize(
    "config",
    [
        {"annot_data": [["a", "b"], ["c", "d"]]},
        {"annot": True, "annot_data": [["a"]]},
        {"annot": True, "annot_data": [["a", "b"], ["c", 1]]},
        {"annot": True, "annot_data": [["a", "b"], ["c", None]]},
        {"annot": True, "annot_data": "abcd"},
        {"annot": True, "annot_data": [["a", "b"], "cd"]},
        {"xrotation": True},
        {"yrotation": float("nan")},
        {"xrotation": float("inf")},
        {"yrotation": -361},
        {"xrotation": 361},
    ],
)
def test_invalid_direct_options_are_reported_without_mutation(config):
    spec = build({}).spec
    spec.panels[0].layers[0].heatmap = mp.HeatmapSpec(**config)
    before = repr(spec)
    assert mp.validate(spec)
    assert repr(spec) == before


def test_cluster_reorders_custom_text_mask_and_labels_by_original_cell_identity():
    pytest.importorskip("scipy")
    matrix = [[1, 10, 100], [2, 20, 200], [3, 30, 300]]
    texts = [[f"r{i}c{j}" for j in range(3)] for i in range(3)]
    mask = [[False, False, False], [False, False, True], [False, False, False]]
    # Supplied trees independently fix the expected order to [2, 0, 1].
    linkage = [[0, 1, 1, 2], [2, 3, 2, 3]]
    p = (
        mp.plot()
        .matrix("m", matrix)
        .clustermap(
            "m",
            cluster={
                "row_linkage": linkage,
                "col_linkage": linkage,
            },
            heatmap={
                "annot": True,
                "annot_data": texts,
                "mask": mask,
                "xlabels": ["c0", "c1", "c2"],
                "ylabels": ["r0", "r1", "r2"],
                "xrotation": 30,
                "yrotation": -30,
            },
        )
    )
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    order = [2, 0, 1]
    expected = [
        (texts[i][j], (x, y))
        for y, i in enumerate(order)
        for x, j in enumerate(order)
        if not mask[i][j]
    ]
    assert [(t.get_text(), t.get_position()) for t in ax.texts] == expected
    np.testing.assert_array_equal(
        ax.images[0].get_array().data, np.array(matrix)[np.ix_(order, order)]
    )
    assert [t.get_text() for t in ax.get_xticklabels()] == ["c2", "c0", "c1"]
    assert [t.get_text() for t in ax.get_yticklabels()] == ["r2", "r0", "r1"]
    assert all(t.get_rotation() == 30 for t in ax.get_xticklabels())
    assert all(t.get_rotation() == 330 for t in ax.get_yticklabels())
    assert p.spec.data.matrices["m"] == matrix
    assert mp.Plot.from_json(p.to_json()).spec == mp.apply(p.action_log)


def test_editor_invalid_edit_isolation_and_history():
    from dashboard.editor_server import EditorSession

    base = mp.plot().matrix("m", [[1, 10], [100, 1000]])
    p = build({"annot": True, "annot_data": [["A", "B"], ["C", "D"]], "xrotation": 45})
    session = EditorSession()
    session.load_spec(base.to_json())
    session.dispatch_safe(mp.actions.AddLayer(p.spec.panels[0].layers[0]))
    assert session.error is None and session.store.state == p.spec
    before, png = session.store.state, session.png
    bad = copy.deepcopy(p.spec.panels[0].layers[0])
    bad.heatmap.annot_data = [["wrong shape"]]
    session.dispatch_safe(mp.actions.AddLayer(bad))
    assert session.error and session.store.state == before and session.png == png
    session.undo()
    assert session.store.state == base.spec
    session.redo()
    assert session.store.state == before and session.png == png
    session.load_spec(mp.to_json(session.store.state))


@pytest.mark.parametrize("masked", [False, True])
def test_annotation_text_length_boundary_including_masked_cells(masked):
    text = "A" * 512
    p = build(
        {
            "annot": True,
            "annot_data": [[text, ""], ["C", "D"]],
            "mask": [[masked, False], [False, False]],
        }
    )
    assert mp.validate(p.spec) == []
    before = copy.deepcopy(p.spec.data.matrices)
    ax = p.render().axes[0]
    assert (text in [t.get_text() for t in ax.texts]) is not masked
    spec = p.spec
    spec.panels[0].layers[0].heatmap.annot_data[0][0] += "A"
    assert any("512" in issue for issue in mp.validate(spec))
    assert spec.data.matrices == before
