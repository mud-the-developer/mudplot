"""Native N04 product checks from explicit measure and geometry oracles."""

import math
import sys

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.patches import StepPatch


def _rebinned(values, source, target, measure="mass", **options):
    return mp.plot({"height": values}).stairs(
        "height",
        source,
        stairs=mp.StairsSpec(rebin=mp.StairsRebinSpec(target, measure), **options),
    )


def test_exact_nonuniform_rebin_and_legacy_native_baseline():
    for measure, values, expect in (
        ("mass", [4, 9], [2, 5, 6]),
        ("density", [2, 3], [2, 2.5, 3]),
    ):
        p = _rebinned(values, [0, 2, 5], [0, 1, 3, 5], measure, fill=True)
        before = p.to_json()
        fig = mp.Plot.from_json(before).render()
        ref, ax = plt.subplots()
        try:
            (patch,) = fig.axes[0].patches
            control = ax.stairs(expect, [0, 1, 3, 5], baseline=0, fill=True)
            assert isinstance(patch, StepPatch) and patch.get_fill()
            np.testing.assert_array_equal(patch.get_data().values, expect)
            np.testing.assert_array_equal(
                patch.get_path().vertices, control.get_path().vertices
            )
            assert p.to_json() == before and p.spec.data.columns["height"] == values
        finally:
            plt.close(fig)
            plt.close(ref)
    p = mp.plot({"height": [-2, 3]}).stairs("height", [0, 1, 3], baseline=None)
    assert "stairs" not in p.spec.panels[0].layers[0].to_dict()
    fig = p.render()
    try:
        (patch,) = fig.axes[0].patches
        np.testing.assert_array_equal(
            patch.get_path().vertices,
            [[0, 0], [0, -2], [1, -2], [1, 3], [3, 3], [3, 0]],
        )
        assert not patch.get_fill()
    finally:
        plt.close(fig)


def test_grouped_original_grid_slots_holes_and_empty_live_cell():
    source = {
        "id": [0, 0, 2, 1, True],
        "height": [1, 4, 2, 5, "excluded"],
        "group": [True, 1, True, 1, "Excluded"],
        "facet": ["A"] * 5,
    }
    p = (
        mp.plot(source)
        .stairs(
            "height",
            [1, 2, 4, 7],
            group="group",
            hue_order=[True, "Reserved", 1],
            stairs=mp.StairsSpec(open=True, bin_index="id"),
        )
        .facet(col="facet", col_order=["Empty", "A"], live=True)
        .size(7, 3)
    )
    saved = p.to_json()
    p = mp.Plot.from_json(saved)
    fig = p.render()
    try:
        blank, ax = fig.axes
        assert not blank.patches and not blank.lines
        patches = list(ax.patches)
        assert len(patches) == 3
        assert [list(patch.get_data().edges) for patch in patches] == [
            [1, 2],
            [4, 7],
            [1, 2, 4],
        ]
        assert [list(patch.get_data().values) for patch in patches] == [
            [1],
            [2],
            [4, 5],
        ]
        assert [patch.get_label() for patch in patches] == ["True", "_nolegend_", "1"]
        assert all(patch.get_data().baseline is None for patch in patches)
        assert (
            patches[0].get_edgecolor()
            == patches[1].get_edgecolor()
            != patches[2].get_edgecolor()
        )
        assert p.spec.data.columns == source and p.to_json() == saved
    finally:
        plt.close(fig)
    p.apply([{"type": "SetData", "columns": {**source, "facet": ["New"] * 5}}])
    assert [panel.filters for panel in p.spec.panels] == [
        {"facet": "Empty"},
        {"facet": "A"},
    ]
    fig = p.render()
    try:
        assert all(not axis.patches for axis in fig.axes)
    finally:
        plt.close(fig)
    plain = mp.plot({"h": [2, 7, 3], "f": ["A", "B", "A"]}).stairs("h", [1, 2, 4, 8])
    plain.facet(col="f", col_order=["A"])
    fig = plain.render()
    try:
        assert [list(patch.get_data().edges) for patch in fig.axes[0].patches] == [
            [1, 2],
            [4, 8],
        ]
    finally:
        plt.close(fig)


def test_open_log_twin_keeps_prior_artists_and_scope_limits():
    p = (
        mp.plot({"h": [5, 10], "x": [10, 80], "old": [90, 100], "p": [4, 40]})
        .secondary_yaxis("Twin value", scale="log")
        .line("x", "p")
        .line("x", "old", axis="y2")
        .stairs("h", [20, 30, 45], axis="y2", stairs=mp.StairsSpec(open=True))
    )
    fig = p.render()
    try:
        primary, y2 = fig.axes
        (patch,) = y2.patches
        assert len(primary.lines) == len(y2.lines) == 1
        np.testing.assert_array_equal(y2.lines[0].get_ydata(), [90, 100])
        np.testing.assert_array_equal(primary.dataLim.get_points(), [[10, 4], [80, 40]])
        np.testing.assert_array_equal(y2.dataLim.get_points(), [[10, 5], [80, 100]])
        np.testing.assert_array_equal(y2.dataLim.minpos, [10, 5])
        assert y2.get_ylim()[0] > 0 and 0 not in patch.sticky_edges.y
        np.testing.assert_array_equal(
            patch.get_path().vertices,
            [[20, 5], [20, 5], [30, 5], [30, 10], [45, 10], [45, 10]],
        )
    finally:
        plt.close(fig)


def test_explicit_clocks_for_supplied_y2_and_rebinned_x():
    source_edges = [
        "1970-01-01T00:00:00Z",
        "1970-01-03T01:00:00+01:00",
        "1970-01-06T00:00:00Z",
    ]
    p = _rebinned([4, 9], source_edges, [0, 1, 3, 5]).date_axis(
        "x", unit="s", origin="1970-01-03T00:00:00Z"
    )
    fig = p.render()
    try:
        (patch,) = fig.axes[0].patches
        np.testing.assert_array_equal(patch.get_data().values, [2, 5, 6])
        np.testing.assert_array_equal(patch.get_data().edges, [0, 1, 3, 5])
        assert p.spec.panels[0].layers[0].bins == source_edges
    finally:
        plt.close(fig)
    source = {"height": ["1970-01-02T00:00:00Z", "1970-01-05T00:00:00Z"]}
    p = (
        mp.plot(source)
        .secondary_yaxis("Observed date")
        .date_axis("y2")
        .stairs("height", [1, 2, 3], axis="y2", stairs={"fill": True}, baseline=0.5)
    )
    fig = p.render()
    try:
        (patch,) = fig.axes[1].patches
        assert not fig.axes[0].patches
        np.testing.assert_array_equal(patch.get_data().values, [1, 4])
        assert patch.get_data().baseline == 0.5 and p.spec.data.columns == source
    finally:
        plt.close(fig)


def test_exact_extremes_and_public_negative_controls(tmp_path):
    maxf, tiny = sys.float_info.max, math.ulp(0.0)
    narrow = _rebinned([maxf], [0, maxf], [0, tiny, maxf])
    density = _rebinned([maxf, maxf], [0, 2, 4], [0, 4], "density")
    from mudplot._stairs import plan_stairs

    for plot, expected in ((narrow, [tiny, maxf]), (density, [maxf])):
        assert not mp.validate(plot.spec)
        panel = plot.spec.panels[0]
        cols = plot.spec.data.columns
        _, _, groups = plan_stairs(
            cols, panel.layers[0], panel, range(len(cols["height"]))
        )
        assert groups[0][1][0].heights == expected
    target = tmp_path / "preserved.svg"
    target.write_text("previous")
    with pytest.raises(ValueError, match="loses a positive height"):
        _rebinned([tiny], [0, 2], [0, 1, 2]).save(str(target))
    assert target.read_text() == "previous"
    source = {"h": [2, 3], "id": [0, 0], "g": [True, True]}
    for bad, message in (
        (_rebinned([maxf, maxf], [0, 2, 4], [0, 4]), "overflows"),
        (_rebinned([-1, 2], [0, 2, 4], [0, 4]), "nonnegative"),
        (_rebinned([1, 2], [0, 2, 4], [0, 3]), "outer endpoints"),
        (_rebinned([1, 2], [0, 2, 4], [0, 4]).date_axis("y"), "not date-valued"),
        (
            mp.plot(source).stairs(
                "h", [1, 2, 3], group="g", stairs={"bin_index": "id"}
            ),
            "duplicate",
        ),
        (
            mp.plot(source).stairs("h", [1, 2, 3], stairs={"open": True, "fill": True}),
            "cannot fill",
        ),
        (
            mp.plot(source).stairs("h", [1, 2, 3], stairs={"open": True}, baseline=1),
            "nonzero baseline",
        ),
        (
            mp.plot(source).stairs("h", [1, 2, 3]).yscale("log"),
            "baseline must be positive",
        ),
        (
            mp.plot(source).stairs("h", [0, 2, 3]).xscale("log"),
            "edges must be positive",
        ),
    ):
        with pytest.raises(ValueError, match=message):
            bad.render()
