"""Pre-binned heights are supplied values, never re-estimated observations."""

import copy

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.patches import StepPatch


def test_stairs_preserve_heights_edges_raw_baseline_style_and_source():
    source = {"height": [2.0, -1.0, 3.0]}
    edges = [0.0, 1.0, 3.0, 4.0]
    p = mp.plot(source).stairs(
        "height",
        edges,
        baseline=0.5,
        color="#225577",
        line_width=2.0,
        line_style="--",
        alpha=0.4,
        label="given",
    )
    before = copy.deepcopy(p.spec)
    edges[1] = 99
    assert (
        mp.validate(p.spec) == []
        and mp.from_json(p.to_json()) == p.spec
        and mp.apply(p.action_log) == p.spec
    )
    figure = p.render()
    try:
        patch = figure.axes[0].patches[0]
        assert isinstance(patch, StepPatch)
        values, edges, baseline = patch.get_data()
        np.testing.assert_array_equal(values, [2, -1, 3])
        np.testing.assert_array_equal(edges, [0, 1, 3, 4])
        np.testing.assert_array_equal(baseline, 0.5)
        np.testing.assert_array_equal(
            patch.get_path().vertices,
            [[0, 0.5], [0, 2], [1, 2], [1, -1], [3, -1], [3, 3], [4, 3], [4, 0.5]],
        )
        assert (
            not patch.get_fill()
            and patch.get_linewidth() == 2
            and patch.get_alpha() == 0.4
            and patch.get_label() == "given"
        )
        assert p.spec == before and p.spec.data.columns == source
    finally:
        plt.close(figure)


def test_default_zero_baseline_single_bin_and_secondary_axis():
    p = (
        mp.plot({"height": [-2.0]})
        .secondary_yaxis()
        .stairs("height", [1.0, 2.0], axis="y2")
    )
    figure = p.render()
    try:
        assert not figure.axes[0].patches
        patch = figure.axes[1].patches[0]
        assert isinstance(patch, StepPatch)
        values, _edges, baseline = patch.get_data()
        np.testing.assert_array_equal(values, [-2])
        np.testing.assert_array_equal(baseline, 0)
    finally:
        plt.close(figure)


@pytest.mark.parametrize(
    "edges",
    [
        [],
        [0, 1],
        [0, 1, 2, 3, 4],
        [0, 1, 1, 2],
        [3, 2, 1, 0],
        [0, True, 2, 3],
        [0, 1, None, 3],
        [0, 1, float("inf"), 3],
        [-1e308, 1e308, 1.1e308, 1.2e308],
        20,
    ],
)
def test_bad_edge_shapes_values_or_collapsed_ranges_reject(edges):
    p = mp.plot({"height": [1, 2, 3]}).stairs("height", edges)
    before = plt.get_fignums()
    with pytest.raises((ValueError, TypeError)):
        p.render()
    assert plt.get_fignums() == before


@pytest.mark.parametrize("values", [[], [True], [None], [float("nan")], ["2"]])
def test_invalid_heights_reject_without_rebinning(values):
    p = mp.plot({"height": values}).stairs("height", list(range(len(values) + 1)))
    with pytest.raises(ValueError):
        p.render()


@pytest.mark.parametrize(
    "style",
    [
        {"orient": "h"},
        {"group": "height"},
        {"colorbar": True},
        {"density": True},
        {"weights": "height"},
        {"marker": "s"},
        {"line_width": -1},
        {"line_width": True},
    ],
)
def test_unused_mappings_and_options_are_not_ignored(style):
    p = mp.plot({"height": [1, 2]}).stairs("height", [0, 1, 2], **style)
    with pytest.raises(ValueError):
        p.render()


@pytest.mark.parametrize("axis", ["x", "y"])
def test_first_stairs_subset_does_not_silently_support_log_axes(axis):
    p = mp.plot({"height": [1, 2]}).stairs("height", [1, 2, 3], baseline=1)
    if axis == "x":
        p.xscale("log")
    else:
        p.yscale("log")
    with pytest.raises(ValueError, match="linear"):
        p.render()


def test_setdata_updates_heights_but_never_invents_new_edges(tmp_path):
    p = mp.plot({"height": [1, 2, 3]}).stairs("height", [0, 1, 3, 4])
    p.dispatch(mp.actions.SetData({"height": [2, 4, 6]}))
    figure = p.render()
    try:
        patch = figure.axes[0].patches[0]
        assert isinstance(patch, StepPatch)
        values, edges, _baseline = patch.get_data()
        np.testing.assert_array_equal(values, [2, 4, 6])
        np.testing.assert_array_equal(edges, [0, 1, 3, 4])
    finally:
        plt.close(figure)
    p.dispatch(mp.actions.SetData({"height": [1, 2]}))
    target = tmp_path / "old.png"
    target.write_bytes(b"previous")
    with pytest.raises(ValueError):
        p.save(target)
    assert target.read_bytes() == b"previous"


def test_stairs_budget_capability_and_no_facet_dropna():
    p = mp.plot({"height": list(range(10001))}).stairs("height", list(range(10002)))
    assert any("10000" in issue for issue in mp.validate(p.spec))
    p = mp.plot({"height": [1, 2], "g": ["A", "B"]}).stairs("height", [0, 1, 2])
    before, history = p.spec, p.action_log
    with pytest.raises(ValueError):
        p.facet(col="g")
    assert p.spec == before and p.action_log == history
    assert mp.capabilities()["layers"]["stairs"]["required"] == ["x", "bins"]
