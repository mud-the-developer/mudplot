"""Finite facet constructors, saved views and actual shared guide ownership."""

from dataclasses import replace

import mudplot as mp
import numpy as np
import pytest
from matplotlib import pyplot as plt


def _scalar_facets():
    source = {
        "clock": [0, 86400, 172800, 604800, 345600],
        "v": [2, 4, 7, 90, None],
        "cell": [True, 1, 1, "omitted", True],
    }
    p = (
        mp.plot(source)
        .size(11, 5)
        .secondary_yaxis("Measured response")
        .date_axis("x", unit="s", origin="1970-01-02T00:00:00Z")
        .relplot(
            "clock",
            "v",
            c="clock",
            axis="y2",
            colorbar=True,
            clabel="Elapsed seconds",
            col="cell",
            col_order=[True, 1, "Reserved"],
        )
        .nest(1, 1)
    )
    return p, source


def test_legacy_scatter_uses_original_clock_values_and_one_native_calibration():
    p, source = _scalar_facets()
    before = p.to_json()
    assert mp.apply(p.action_log) == p.spec == mp.Plot.from_json(before).spec
    fig = p.render()
    try:
        panels = [a for a in fig.axes if hasattr(a, "_mudplot_panel")]
        a, b, blank = [ax._mudplot_secondary_axis for ax in panels]
        first, second = a.collections[0], b.collections[0]
        np.testing.assert_array_equal(first.get_offsets().compressed(), [1, 2])
        assert np.ma.getmaskarray(first.get_offsets())[1].all()
        np.testing.assert_array_equal(second.get_offsets(), [[2, 4], [3, 7]])
        assert float(first.get_array()[0]) == 0
        np.testing.assert_array_equal(second.get_array(), [86400, 172800])
        assert first.norm is second.norm and first.cmap is second.cmap
        assert first.get_clim() == (0, 172800) and not blank.collections
        (guide,) = fig._mudplot_shared_guide_artists
        assert guide.get_xlabel() == "Elapsed seconds"
        assert [float(t.get_text()) for t in guide.get_xticklabels()] == [
            0,
            86400,
            172800,
        ]
        assert not hasattr(guide, "_mudplot_panel")
        assert before == p.to_json() and p.spec.data.columns == source
    finally:
        plt.close(fig)
    old = [(a.panel_id, a.placement, a.filters) for a in p.spec.panels]
    p.labels(title="Local override", panel=0)
    assert p.spec.facet_template.template.title != "Local override"
    recipe = p.spec.facet_template.template
    layers = [replace(recipe.layers[0], marker_size=9)]
    p.facet_template(replace(recipe, title="New template", layers=layers))
    assert [(a.panel_id, a.placement, a.filters) for a in p.spec.panels] == old
    assert all(a.layers[0].marker_size == 9 for a in p.spec.panels)
    assert p.spec.data.columns == source and mp.apply(p.action_log) == p.spec


def test_raw_consolidation_keeps_real_order_and_unrelated_same_text():
    p = (
        mp.relplot(
            {
                "x": [1, 2, 1, 2],
                "y": [1, 2, 4, 5],
                "g": [True, True, 1, 1],
                "cell": ["a", "a", "b", "b"],
            },
            "x",
            "y",
            kind="line",
            group="g",
            hue_order=[1, "Reserved", True],
            col="cell",
            col_order=["a", "b", "empty"],
        )
        .size(8, 4)
        .line("x", "y", label="1", panel=0)
    )
    fig = p.render()
    try:
        (shared,) = fig._mudplot_shared_guide_artists
        assert [t.get_text() for t in shared.get_texts()] == ["1", "True"]
        local = fig.axes[0].get_legend()
        assert [t.get_text() for t in local.get_texts()] == ["1"]
        assert shared.legend_handles[0].get_color() == fig.axes[1].lines[0].get_color()
        assert fig.axes[0].lines[0].get_color() != fig.axes[1].lines[0].get_color()
        assert not fig.axes[2].lines
    finally:
        plt.close(fig)


def test_cell_local_distribution_estimation_and_regression_dispatch():
    raw = {
        "x": [1, 2, 3, 1, 2, 3],
        "y": [2, 4, 6, 5, 10, 15],
        "w": [1, 2, 1, 2, 1, 2],
        "cell": ["a"] * 3 + ["b"] * 3,
    }
    named = mp.displot(raw, "x", bins=[0, 2, 4], weights="w", col="cell").size(7, 3)
    estimated = mp.catplot(
        raw,
        "x",
        "y",
        kind="point",
        errorbar=None,
        col="cell",
        transforms=[mp.TransformSpec("y", "log")],
    ).size(7, 3)
    model = mp.lmplot(
        raw,
        "x",
        "y",
        weights="w",
        col="cell",
        regression={"components": {"show_fit": True}},
    ).size(7, 3)
    for i, p in enumerate((named, estimated, model)):
        assert not mp.validate(p.spec)
        assert mp.apply(p.action_log) == mp.Plot.from_json(p.to_json()).spec
        fig = p.render()
        try:
            for j, ax in enumerate(fig.axes):
                if i == 0:
                    heights = [bar.get_height() for bar in ax.patches]
                    np.testing.assert_allclose(heights, [[1, 3], [2, 3]][j])
                if i == 1:
                    want = np.log10(raw["y"][3 * j : 3 * j + 3])
                    np.testing.assert_allclose(ax.lines[0].get_ydata(), want)
                if i == 2:
                    (line,) = [
                        a
                        for a in ax.lines
                        if getattr(a, "_mudplot_regression_role", None) == "mean_fit"
                    ]
                    want = np.asarray(line.get_xdata()) * [2, 5][j]
                    np.testing.assert_allclose(line.get_ydata(), want)
        finally:
            plt.close(fig)


def test_default_histogram_edges_and_failed_builder_transaction():
    raw = {"x": [1, 3, 5, 999], "w": [1, 2, 3, 1], "cell": ["a", "b", "b", "outside"]}
    p = mp.plot(raw)
    original, history = p.to_json(), p.action_log
    with pytest.raises(ValueError, match="must name existing columns"):
        p.displot("x", col="absent")
    assert p.to_json() == original and p.action_log == history
    with pytest.raises(ValueError, match="edges"):
        p.displot("x", col="cell", bins=[2, 1])
    assert p.to_json() == original and p.action_log == history
    p.displot("x", col="cell", col_order=["a", "b", "reserved"], weights="w").size(9, 4)
    all_edges = [a.layers[0].bins for a in p.spec.panels]
    assert all(edges == all_edges[0] for edges in all_edges)
    assert len(all_edges[0]) == 21 and all_edges[0][0] == 1 and all_edges[0][-1] == 5
    assert mp.apply(p.action_log) == mp.Plot.from_json(p.to_json()).spec
    fig = p.render()
    try:
        assert [sum(b.get_height() for b in ax.patches) for ax in fig.axes] == [1, 5, 0]
    finally:
        plt.close(fig)
