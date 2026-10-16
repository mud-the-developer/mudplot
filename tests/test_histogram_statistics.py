"""Weighted/shared-bin histogram equations, geometry and opt-in compatibility."""

from __future__ import annotations

import json
import math
from typing import Any, cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.axes import Axes
from matplotlib.colors import to_rgba
from matplotlib.container import BarContainer
from matplotlib.patches import Rectangle, StepPatch
from mudplot import actions as A
from mudplot._histogram import histogram_summary
from mudplot.spec import HistogramSpec, LayerSpec


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def data():
    return {
        "x": [0, 1, 2, 3, 4, 0.5, 2.5, 3, 7],
        "w": [1, 2, 3, 4, 99, 2, 4, 5, 99],
        "g": ["A"] * 5 + ["B"] * 4,
    }


def rects(ax):
    return [cast(Rectangle, patch) for patch in ax.patches]


@pytest.mark.parametrize("multiple", ["layer", "stack"])
@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize(
    "stat,cumulative", [("count", False), ("density", False), ("density", True)]
)
def test_step_weighted_heights_and_paths_match_independent_native_stairs(
    multiple, orient, stat, cumulative
):
    p = mp.plot(data()).hist(
        "x",
        bins=[0, 1, 3],
        weights="w",
        group="g",
        stat=stat,
        cumulative=cumulative,
        multiple=multiple,
        element="step",
        orient=orient,
    )
    assert mp.validate(p.spec) == []
    assert mp.Plot.from_json(p.to_json()).spec == mp.apply(p.action_log) == p.spec
    ax = p.render().axes[0]
    assert len(ax.patches) == 2
    assert ax.get_legend_handles_labels()[1] == ["A", "B"]
    _, native_ax = plt.subplots()
    baseline = np.zeros(2)
    for patch, counts in zip(ax.patches, ([1, 9], [2, 9]), strict=True):
        assert isinstance(patch, StepPatch) and not patch.get_fill()
        heights = np.array(counts, dtype=float)
        if cumulative:
            heights = np.cumsum(heights) / 21
        elif stat == "density":
            heights /= np.array([1, 2]) * 21
        base = baseline if multiple == "stack" else 0
        top = base + heights
        native = native_ax.stairs(
            top,
            [0, 1, 3],
            baseline=base,
            fill=False,
            orientation="vertical" if orient == "v" else "horizontal",
        )
        values, edges, bottom = patch.get_data()
        np.testing.assert_allclose(values, top)
        np.testing.assert_array_equal(edges, [0, 1, 3])
        np.testing.assert_allclose(bottom, base)
        np.testing.assert_allclose(
            np.asarray(patch.get_path().vertices),
            np.asarray(native.get_path().vertices),
        )
        baseline = top


@pytest.mark.parametrize("multiple", ["layer", "stack"])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_step_edges_stay_raw_on_inverted_log_observation_axes(multiple, orient):
    p = mp.plot({"x": [1, 3, 2, 10], "g": ["A", "A", "B", "B"]}).hist(
        "x",
        bins=[1, 3, 10],
        group="g",
        element="step",
        multiple=multiple,
        orient=orient,
    )
    (p.xscale if orient == "v" else p.yscale)("log")
    (p.xlim if orient == "v" else p.ylim)(12, 0.8)
    ax = p.render().axes[0]
    for patch in ax.patches:
        assert isinstance(patch, StepPatch)
        np.testing.assert_array_equal(patch.get_data()[1], [1, 3, 10])
    assert ax.xaxis_inverted() if orient == "v" else ax.yaxis_inverted()


@pytest.mark.parametrize("multiple", ["layer", "stack"])
def test_step_empty_hues_reserve_dashes_and_exact_stroke_style(multiple):
    raw = {"x": [0.5, 2.5, 20], "g": ["A", "B", "outside"]}
    full = (
        mp.plot(raw)
        .hist("x", bins=[0, 1, 3], element="step", group="g", hue_order=["A", "B"])
        .render()
        .axes[0]
    )
    partial = (
        mp.plot(raw)
        .hist(
            "x",
            bins=[0, 1, 3],
            element="step",
            group="g",
            multiple=multiple,
            hue_order=["empty", "B", "outside"],
            edge_color="#123456",
            line_width=0.7,
            alpha=0.4,
        )
        .render()
        .axes[0]
    )
    assert len(partial.patches) == 1
    patch = partial.patches[0]
    assert isinstance(patch, StepPatch) and not patch.get_fill()
    assert patch.get_linestyle() == full.patches[1].get_linestyle() == "--"
    assert to_rgba(patch.get_edgecolor()) == to_rgba("#123456", 0.4)
    assert patch.get_linewidth() == 0.7 and patch.get_alpha() == 0.4
    assert partial.get_legend_handles_labels()[1] == ["B"]


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("width,alpha", [(0, 1), (1.4, 0)])
def test_step_zero_width_or_alpha_never_fills_and_keeps_legend(orient, width, alpha):
    p = mp.plot(data()).hist(
        "x",
        bins=[0, 1, 3],
        element="step",
        group="g",
        label="sample",
        orient=orient,
        line_width=width,
        alpha=alpha,
        color="#123456",
    )
    ax = p.render().axes[0]
    assert ax.get_legend_handles_labels()[1] == ["A", "B"]
    for patch in ax.patches:
        assert isinstance(patch, StepPatch) and not patch.get_fill()
        assert patch.get_linewidth() == width and patch.get_alpha() == alpha
        assert to_rgba(patch.get_edgecolor()) == to_rgba("#123456", alpha)


@pytest.mark.parametrize("multiple", ["stack", "dodge"])
@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize(
    "stat,common,cumulative",
    [
        ("count", True, False),
        ("frequency", True, False),
        ("density", True, False),
        ("density", False, False),
        ("percent", False, True),
    ],
)
def test_grouped_geometry_preserves_weighted_heights_and_normalization(
    multiple, orient, stat, common, cumulative
):
    p = mp.plot(data()).hist(
        "x",
        bins=[0, 1, 3],
        stat=stat,
        weights="w",
        group="g",
        common_norm=common,
        cumulative=cumulative,
        multiple=multiple,
        orient=orient,
    )
    assert mp.validate(p.spec) == []
    result = histogram_summary(p.spec.data.columns, p.spec.panels[0].layers[0])
    patches = rects(p.render().axes[0])
    geometry = np.array(
        [
            [q.get_x(), q.get_width(), q.get_y(), q.get_height()]
            if orient == "v"
            else [q.get_y(), q.get_height(), q.get_x(), q.get_width()]
            for q in patches
        ]
    )
    assert len(patches) == 4
    np.testing.assert_allclose(
        geometry[:, 0], [0, 1, 0, 1] if multiple == "stack" else [0, 1, 0.5, 2]
    )
    np.testing.assert_allclose(
        geometry[:, 1], [1, 2, 1, 2] if multiple == "stack" else [0.5, 1, 0.5, 1]
    )
    np.testing.assert_allclose(
        geometry[:, 2],
        [0, 0, *result.curves[0].heights] if multiple == "stack" else [0] * 4,
    )
    np.testing.assert_allclose(
        geometry[:, 3], [h for curve in result.curves for h in curve.heights]
    )
    if stat == "density":
        # Dodge narrows bars; density still uses the ORIGINAL raw bin widths.
        expected_area = (1 if common else 2) / (2 if multiple == "dodge" else 1)
        assert sum(geometry[:, 1] * geometry[:, 3]) == pytest.approx(expected_area)


@pytest.mark.parametrize("multiple", ["stack", "dodge"])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_grouped_bins_keep_raw_spacing_on_inverted_log_observation_axes(
    multiple, orient
):
    p = mp.plot({"x": [1, 3, 2, 10], "g": ["A", "A", "B", "B"]}).hist(
        "x", bins=[1, 3, 10], group="g", multiple=multiple, orient=orient
    )
    (p.xscale if orient == "v" else p.yscale)("log")
    (p.xlim if orient == "v" else p.ylim)(12, 0.8)
    ax = p.render().axes[0]
    patches = rects(ax)
    np.testing.assert_allclose(
        [q.get_x() if orient == "v" else q.get_y() for q in patches],
        [1, 3, 1, 3] if multiple == "stack" else [1, 3, 2, 6.5],
    )
    np.testing.assert_allclose(
        [q.get_width() if orient == "v" else q.get_height() for q in patches],
        [2, 7, 2, 7] if multiple == "stack" else [1, 3.5, 1, 3.5],
    )
    assert ax.xaxis_inverted() if orient == "v" else ax.yaxis_inverted()


@pytest.mark.parametrize("multiple", ["stack", "dodge"])
def test_empty_and_outside_hues_reserve_geometry_color_and_hatch_slots(multiple):
    raw = {"x": [0.5, 2.5, 20], "g": ["A", "B", "outside"]}
    options: dict[str, Any] = {
        "bins": [0, 1, 3],
        "group": "g",
        "hue_order": ["empty", "B", "A", "outside"],
        "alpha": 0.4,
        "edge_color": "#123456",
        "line_width": 0.7,
    }
    full = mp.plot(raw).hist("x", **options, multiple="layer").render().axes[0]
    ax = mp.plot(raw).hist("x", **options, multiple=multiple).render().axes[0]
    patches = rects(ax)
    assert ax.get_legend_handles_labels()[1] == ["B", "A"]
    assert len(patches) == 4
    np.testing.assert_allclose(
        [q.get_x() for q in patches],
        [0, 1, 0, 1] if multiple == "stack" else [0.25, 1.5, 0.5, 2],
    )
    np.testing.assert_allclose(
        [q.get_width() for q in patches],
        [1, 2, 1, 2] if multiple == "stack" else [0.25, 0.5, 0.25, 0.5],
    )
    for original, q in zip(rects(full), patches, strict=True):
        assert q.get_facecolor() == original.get_facecolor()
        assert q.get_hatch() == original.get_hatch()
        assert q.get_alpha() == 0.4 and q.get_linewidth() == 0.7
        assert to_rgba(q.get_edgecolor()) == to_rgba("#123456", 0.4)


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize(
    "element,multiple,weights,bins",
    [
        ("bars", "stack", [1e308, 1e308], [0, 1]),
        ("bars", "stack", [1e308, 1], [0, 1]),
        ("bars", "dodge", [1, 1], [0.5, np.nextafter(0.5, 1)]),
        ("step", "stack", [1e308, 1e308], [0, 1]),
        ("step", "stack", [1e308, 1], [0, 1]),
    ],
)
def test_nonfinite_or_collapsed_group_geometry_fails_before_any_bar(
    monkeypatch, orient, element, multiple, weights, bins
):
    def unexpected_artist(*args, **kwargs):
        pytest.fail("all group geometry must be checked before adding bars")

    monkeypatch.setattr(Axes, "bar", unexpected_artist)
    monkeypatch.setattr(Axes, "barh", unexpected_artist)
    monkeypatch.setattr(Axes, "stairs", unexpected_artist)
    p = mp.plot({"x": [0.5, 0.5], "g": ["A", "B"], "w": weights}).hist(
        "x",
        bins=bins,
        weights="w",
        group="g",
        multiple=multiple,
        orient=orient,
        element=element,
    )
    assert mp.validate(p.spec) == []
    with pytest.raises(
        ValueError, match=r"derived histogram (stacked tops|dodge bins)"
    ):
        p.render()


@pytest.mark.parametrize("multiple", ["layer", "stack", "dodge"])
def test_multiple_round_trips_actions_and_generated_contracts(multiple):
    import jsonschema

    p = mp.plot(data()).hist("x", group="g", multiple=multiple)
    assert mp.validate(p.spec) == []
    assert mp.Plot.from_json(p.to_json()).spec == mp.apply(p.action_log) == p.spec
    assert p.spec.panels[0].layers[0].histogram == HistogramSpec(multiple=multiple)
    jsonschema.validate(p.spec.to_dict(), mp.json_schema())
    assert mp.capabilities()["histogram"]["multiple"] == ["layer", "stack", "dodge"]
    assert mp.capabilities()["histogram"]["elements"] == ["bars", "step"]
    assert mp.json_schema()["$defs"]["HistogramSpec"]["properties"]["element"] == {
        "type": "string",
        "default": "bars",
    }
    old = p.spec.to_dict()
    del old["panels"][0]["layers"][0]["histogram"]["element"]
    assert mp.FigureSpec.from_dict(old) == p.spec
    assert mp.json_schema()["$defs"]["HistogramSpec"]["properties"]["multiple"] == {
        "type": "string",
        "default": "layer",
    }


@pytest.mark.parametrize(
    "stat,common",
    [
        ("count", True),
        ("frequency", True),
        *[
            (stat, common)
            for stat in ("probability", "proportion", "percent", "density")
            for common in (False, True)
        ],
    ],
)
def test_unequal_width_weighted_bin_equations_and_in_range_normalization(stat, common):
    raw = data()
    p = mp.plot(raw).hist(
        "x", bins=[0, 1, 3], stat=stat, weights="w", group="g", common_norm=common
    )
    assert mp.validate(p.spec) == []
    result = histogram_summary(p.spec.data.columns, p.spec.panels[0].layers[0])
    assert result.edges == (0, 1, 3)
    expected_counts = []
    for group in ("A", "B"):
        expected_counts.append(
            [
                math.fsum(
                    w
                    for x, w, g in zip(raw["x"], raw["w"], raw["g"], strict=True)
                    if g == group and (left <= x < right or (right == 3 and x == 3))
                )
                for left, right in ((0, 1), (1, 3))
            ]
        )
    assert expected_counts == [[1, 9], [2, 9]]
    pooled = math.fsum(sum(counts) for counts in expected_counts)
    for curve, counts in zip(result.curves, expected_counts, strict=True):
        heights = np.array(counts)
        if stat not in ("count", "frequency"):
            heights = heights / (pooled if common else sum(counts))
        if stat in ("density", "frequency"):
            heights = heights / [1, 2]
        elif stat == "percent":
            heights *= 100
        np.testing.assert_allclose(curve.heights, heights, rtol=2e-15)
    patches = rects(p.render().axes[0])
    assert len(patches) == 4
    np.testing.assert_array_equal([q.get_x() for q in patches], [0, 1, 0, 1])
    np.testing.assert_array_equal([q.get_width() for q in patches], [1, 2, 1, 2])
    np.testing.assert_allclose(
        [q.get_height() for q in patches], [v for c in result.curves for v in c.heights]
    )


@pytest.mark.parametrize(
    "stat,common",
    [
        ("count", True),
        *[
            (stat, common)
            for stat in ("probability", "proportion", "percent", "density")
            for common in (False, True)
        ],
    ],
)
def test_cumulative_is_mass_integration_not_sum_of_density_heights(stat, common):
    p = mp.plot(data()).hist(
        "x",
        bins=[0, 1, 3],
        stat=stat,
        weights="w",
        group="g",
        common_norm=common,
        cumulative=True,
    )
    result = histogram_summary(p.spec.data.columns, p.spec.panels[0].layers[0])
    for curve, first, total in zip(result.curves, [1, 2], [10, 11], strict=True):
        expected = np.array([first, total], dtype=float)
        if stat != "count":
            expected /= 21 if common else total
        if stat == "percent":
            expected *= 100
        np.testing.assert_allclose(curve.heights, expected, rtol=2e-15)
    if stat == "density" and common:
        assert result.curves[0].heights[-1] == pytest.approx(10 / 21)


def test_weighted_small_bin_mass_is_not_lost_to_prefix_subtraction():
    p = mp.plot({"x": [0.5, 1.5], "w": [1e308, 1]}).hist(
        "x",
        bins=[0, 1, 2],
        weights="w",
        stat="count",
    )
    result = histogram_summary(p.spec.data.columns, p.spec.panels[0].layers[0])
    assert result.curves[0].heights == (1e308, 1)


def test_numeric_histogram_refuses_shared_ordinal_but_allows_native_overlays():
    p = mp.plot({"x": [1, 2], "c": [1, 2]}).hist("x", stat="count").barplot("c", "x")
    assert any("cannot mix ordinal" in i for i in mp.validate(p.spec))
    q = (
        mp.plot({"x": [1, 2], "c": [1, 2]})
        .hist("x", stat="count")
        .barplot(
            "c",
            "x",
            native_scale=True,
            errorbar=None,
        )
    )
    assert mp.validate(q.spec) == []


def test_density_area_not_density_height_sum_and_per_curve_vs_global_scope():
    for common in (False, True):
        p = mp.plot(data()).hist(
            "x",
            bins=[0, 1, 3],
            stat="density",
            weights="w",
            group="g",
            common_norm=common,
        )
        result = histogram_summary(p.spec.data.columns, p.spec.panels[0].layers[0])
        areas = [sum(np.asarray(c.heights) * [1, 2]) for c in result.curves]
        np.testing.assert_allclose(areas, [10 / 21, 11 / 21] if common else [1, 1])
        assert not np.isclose(sum(result.curves[0].heights), areas[0])


def test_selected_hues_pool_automatic_bins_and_missing_zero_weight_pairs():
    raw = {
        "x": [1, 2, 10, 20, None, -3, 500, 4],
        "w": [1, 2, 3, 4, 99, 0, -1, None],
        "g": ["A", "A", "B", "B", "A", "A", "omit", "A"],
    }
    p = mp.plot(raw).hist(
        "x", bins=2, stat="count", weights="w", group="g", hue_order=["empty", "A", "B"]
    )
    assert mp.validate(p.spec) == []
    result = histogram_summary(p.spec.data.columns, p.spec.panels[0].layers[0])
    np.testing.assert_allclose(
        result.edges, np.histogram_bin_edges([1, 2, 10, 20], bins=2)
    )
    assert result.curves[0].heights == ()
    assert [sum(c.heights) for c in result.curves[1:]] == [3, 7]
    assert p.render().axes[0].get_legend_handles_labels()[1] == ["A", "B"]


@pytest.mark.parametrize("stat", ["count", "frequency", "density", "proportion"])
def test_independent_numpy_reference_on_unweighted_unequal_bins(stat):
    values = [0, 0.2, 1, 1.5, 2, 3, 4]
    p = mp.plot({"x": values}).hist("x", bins=[0, 1, 3], stat=stat)
    result = histogram_summary(p.spec.data.columns, p.spec.panels[0].layers[0])
    counts, edges = np.histogram(values, bins=[0, 1, 3])
    expected = counts.astype(float)
    if stat == "density":
        expected = np.histogram(values, bins=edges, density=True)[0]
    elif stat == "frequency":
        expected /= np.diff(edges)
    elif stat == "proportion":
        expected /= expected.sum()
    np.testing.assert_allclose(result.curves[0].heights, expected)


@pytest.mark.parametrize("orient", ["v", "h"])
def test_histogram_bar_geometry_log_observations_raw_density_widths_and_limits(orient):
    p = mp.plot({"x": [1, 2, 3, 10]}).hist(
        "x", bins=[1, 3, 10], stat="density", orient=orient
    )
    (p.xscale if orient == "v" else p.yscale)("log")
    (p.xlim if orient == "v" else p.ylim)(12, 0.8)
    ax = p.render().axes[0]
    patches = rects(ax)
    widths = [q.get_width() if orient == "v" else q.get_height() for q in patches]
    heights = [q.get_height() if orient == "v" else q.get_width() for q in patches]
    np.testing.assert_allclose(widths, [2, 7])
    np.testing.assert_allclose(heights, [0.5 / 2, 0.5 / 7])
    assert ax.xaxis_inverted() if orient == "v" else ax.yaxis_inverted()


def test_reserved_hue_color_hatch_slots_and_explicit_alpha_edge_width():
    full = mp.plot(data()).hist(
        "x", bins=[0, 1, 3], stat="count", group="g", hue_order=["A", "B"]
    )
    partial = mp.plot(data()).hist(
        "x",
        bins=[0, 1, 3],
        stat="count",
        group="g",
        hue_order=["absent", "B"],
        alpha=1,
        edge_color="#123456",
        line_width=0,
    )
    a = rects(full.render().axes[0])[2]
    b = rects(partial.render().axes[0])[0]
    np.testing.assert_allclose(to_rgba(a.get_facecolor()), to_rgba(b.get_facecolor()))
    assert a.get_hatch() == b.get_hatch()
    assert b.get_alpha() == 1 and b.get_linewidth() == 0
    np.testing.assert_allclose(to_rgba(b.get_edgecolor()), to_rgba("#123456"))


@pytest.mark.parametrize(
    "raw", [{"x": []}, {"x": [None]}, {"x": [1, 2], "w": [0, 0]}, {"x": [-9, 99]}]
)
@pytest.mark.parametrize("element", ["bars", "step"])
def test_empty_or_outside_support_curves_have_no_fake_bars_or_legend(raw, element):
    p = mp.plot(raw).hist(
        "x",
        bins=[0, 1, 3],
        stat="density",
        weights="w" if "w" in raw else None,
        label="empty",
        element=element,
    )
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    assert not ax.patches and ax.get_legend_handles_labels() == ([], [])


@pytest.mark.parametrize("values", [[1], [1, 1, 1], [0, 0], [-5, -5]])
def test_singleton_or_constant_automatic_bins_are_shared_finite_and_conserve_mass(
    values,
):
    p = mp.plot({"x": values}).hist("x", bins=2, stat="count")
    result = histogram_summary(p.spec.data.columns, p.spec.panels[0].layers[0])
    assert len(result.edges) == 3 and np.all(np.diff(result.edges) > 0)
    assert sum(result.curves[0].heights) == len(values)


@pytest.mark.parametrize("stat", ["proportion", "percent", "density"])
def test_large_weights_normalize_without_overflow_and_raw_mass_overflow_fails(stat):
    raw = {"x": [0.2, 1.5, 2.5], "w": [1e308] * 3}
    p = mp.plot(raw).hist("x", bins=[0, 1, 3], weights="w", stat=stat)
    result = histogram_summary(p.spec.data.columns, p.spec.panels[0].layers[0])
    expected = np.array([1 / 3, 2 / 3])
    if stat == "density":
        expected /= [1, 2]
    if stat == "percent":
        expected *= 100
    np.testing.assert_allclose(result.curves[0].heights, expected)
    q = mp.plot(raw).hist("x", bins=[0, 1, 3], weights="w", stat="count")
    with pytest.raises(ValueError, match="raw mass exceeds finite range"):
        q.render()


@pytest.mark.parametrize("cumulative", [False, True])
def test_wide_weight_mass_prefixes_are_monotone_and_stay_in_normalized_range(
    cumulative,
):
    rng = np.random.default_rng(51)
    for _ in range(30):
        values = rng.integers(0, 10, 100).tolist()
        weights = (10.0 ** rng.uniform(-300, 300, 100)).tolist()
        p = mp.plot({"x": values, "w": weights}).hist(
            "x",
            bins=list(range(11)),
            weights="w",
            stat="proportion",
            cumulative=cumulative,
        )
        heights = np.array(
            histogram_summary(p.spec.data.columns, p.spec.panels[0].layers[0])
            .curves[0]
            .heights
        )
        assert heights.min() >= 0 and heights.max() <= 1
        if cumulative:
            assert np.all(np.diff(heights) >= 0) and heights[-1] == 1


@pytest.mark.parametrize(
    "options,match",
    [
        ({"stat": "median"}, "invalid histogram stat"),
        ({"stat": []}, "invalid histogram stat"),
        ({"multiple": "fill"}, "invalid histogram multiple"),
        ({"multiple": []}, "invalid histogram multiple"),
        ({"multiple": False}, "invalid histogram multiple"),
        ({"multiple": "stack"}, "requires group"),
        ({"multiple": "dodge"}, "requires group"),
        ({"element": "poly"}, "invalid histogram element"),
        ({"element": []}, "invalid histogram element"),
        ({"element": False}, "invalid histogram element"),
        ({"element": "step", "multiple": "dodge", "group": "g"}, "not dodge"),
        ({"common_norm": 1}, "common_norm must be boolean"),
        ({"common_norm": False}, "only applies to normalized"),
        ({"cumulative": 1}, "cumulative must be boolean"),
        ({"stat": "frequency", "cumulative": True}, "cumulative frequency"),
        ({"stat": "count", "density": True}, "density=True conflicts"),
        ({"density": 1, "stat": "density"}, "density alias must be boolean"),
        ({"weights": "missing"}, "column 'missing'"),
        ({"weights": []}, "weights must be a nonempty"),
        ({"bins": True}, "histogram bins require"),
        ({"bins": 0}, "histogram bins require"),
        ({"bins": 10001}, "histogram bins require"),
        ({"bins": [1]}, "histogram bins require"),
        ({"bins": [0, 1, 1]}, "histogram bins require"),
        ({"bins": [0, float("inf")]}, "histogram bins require"),
        ({"bins": "auto"}, "histogram bins require"),
        ({"orient": "horizontal"}, "orient must be"),
        ({"hue_order": ["A"]}, "hue_order requires group"),
        ({"group": "g", "hue_order": ["A", "A"]}, "levels must be unique"),
        ({"line_width": -1}, "line_width must be"),
        ({"edge_color": "bad"}, "edge_color must be"),
    ],
)
def test_invalid_options_fail_with_clear_pure_validation(options, match):
    options = {"stat": "count", **options}
    p = mp.plot({"x": [1, 2], "g": ["A", "A"]}).hist("x", **options)
    assert any(match in issue for issue in mp.validate(p.spec))


@pytest.mark.parametrize("value", [True, "1", float("inf"), 10**400])
def test_invalid_observations_rejected_not_silently_converted(value):
    p = mp.plot({"x": [1, value]}).hist("x", stat="count")
    assert any("observations must be finite numeric" in i for i in mp.validate(p.spec))


@pytest.mark.parametrize("weight", [True, False, -1, "2", float("inf"), 10**400])
def test_invalid_selected_weights_rejected_including_false_not_excluded_as_zero(weight):
    p = mp.plot({"x": [1, 2], "w": [1, weight]}).hist("x", stat="count", weights="w")
    assert any("weights must be finite nonnegative" in i for i in mp.validate(p.spec))


@pytest.mark.parametrize(
    "style",
    [
        {"stack": True},
        {"dodge": 0.5},
        {"stat_scale": "axis"},
        {"native_scale": True},
        {"order": [1, 2]},
        {"line_style": ":"},
        {"element": "step", "line_style": ":"},
        {"ecdf": mp.ECDFSpec()},
        {"marker": "o"},
        {"baseline": 1},
        {"value_labels": True},
    ],
)
def test_ignored_geometry_inference_and_other_configurations_are_not_accepted(style):
    p = mp.plot({"x": [1, 2]}).hist("x", stat="count", **style)
    assert any("not supported" in i for i in mp.validate(p.spec))


@pytest.mark.parametrize("orient", ["v", "h"])
def test_unsupported_mass_log_and_nonpositive_observation_log_edges(orient):
    p = mp.plot({"x": [1, 2]}).hist(
        "x", bins=[0.5, 1.5, 3], stat="count", orient=orient
    )
    (p.yscale if orient == "v" else p.xscale)("log")
    assert any("height axis must be linear" in i for i in mp.validate(p.spec))
    q = mp.plot({"x": [1, 2]}).hist("x", bins=[0, 1, 3], stat="count", orient=orient)
    (q.xscale if orient == "v" else q.yscale)("log")
    assert any("bin edges must be positive" in i for i in mp.validate(q.spec))


def test_generated_edge_collapse_and_density_overflow_fail_before_artists():
    p = mp.plot({"x": [1]}).hist(
        "x", bins=[0, 1e-320, 2], stat="frequency", weights=None
    )
    # Use an actual nonzero tiny-bin observation for frequency overflow.
    q = mp.plot({"x": [1e-321]}).hist("x", bins=[0, 1e-320, 2], stat="frequency")
    with pytest.raises(ValueError, match="derived histogram heights"):
        q.render()
    assert mp.validate(p.spec) == []
    r = mp.plot({"x": [1e308]}).hist("x", bins=2, stat="count")
    with pytest.raises(ValueError):
        r.render()


def test_legacy_specs_render_match_native_hist_and_opt_in_is_explicit():
    raw = {"x": [1, 2, 20, 25], "g": ["A", "A", "B", "B"]}
    p = mp.plot(raw).hist("x", bins=2, density=True, group="g")
    assert p.spec.panels[0].layers[0].histogram is None
    patches = rects(p.render().axes[0])
    _, ax = plt.subplots()
    native = []
    for values in ([1, 2], [20, 25]):
        native.extend(
            cast(BarContainer, ax.hist(values, bins=2, density=True)[2]).patches
        )
    np.testing.assert_allclose(
        [[r.get_x(), r.get_width(), r.get_height()] for r in patches],
        [[r.get_x(), r.get_width(), r.get_height()] for r in native],
    )
    assert patches[0].get_alpha() == 0.6
    old = p.spec.to_dict()
    del old["panels"][0]["layers"][0]["histogram"]
    assert mp.FigureSpec.from_dict(old).panels[0].layers[0].histogram is None
    q = mp.plot(raw).hist("x", bins=2, stat="density", group="g")
    assert isinstance(q.spec.panels[0].layers[0].histogram, HistogramSpec)
    assert rects(q.render().axes[0])[0].get_alpha() == 1
    explicit = mp.plot(raw).hist("x", bins=2, group="g", multiple="layer")
    assert explicit.spec.panels[0].layers[0].histogram == HistogramSpec()
    explicit = mp.plot(raw).hist("x", bins=2, group="g", element="bars")
    assert explicit.spec.panels[0].layers[0].histogram == HistogramSpec()
    old_typed = q.spec.to_dict()
    del old_typed["panels"][0]["layers"][0]["histogram"]["multiple"]
    del old_typed["panels"][0]["layers"][0]["histogram"]["element"]
    assert mp.FigureSpec.from_dict(old_typed) == q.spec


def test_typed_json_actions_schema_strict_config_alias_and_wrong_layer_guard():
    import jsonschema

    p = mp.plot(data()).hist(
        "x",
        bins=[0, 1, 3],
        stat="density",
        density=True,
        weights="w",
        common_norm=False,
        cumulative=True,
        orient="h",
    )
    assert p.spec.panels[0].layers[0].histogram == HistogramSpec(
        "density", "w", False, True
    )
    assert (
        mp.Plot.from_json(p.to_json()).spec == p.spec
        and mp.apply(p.action_log) == p.spec
    )
    jsonschema.validate(p.spec.to_dict(), mp.json_schema())
    assert mp.json_schema()["$defs"]["HistogramSpec"]["additionalProperties"] is False
    raw = p.spec.to_dict()
    raw["panels"][0]["layers"][0]["histogram"]["fill"] = True
    with pytest.raises(ValueError, match="unknown HistogramSpec"):
        mp.FigureSpec.from_dict(raw)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(raw, mp.json_schema())
    q = mp.plot(data()).ecdf("x", histogram=HistogramSpec())
    assert any("histogram is not supported" in i for i in mp.validate(q.spec))
    invalid = p.spec
    invalid.panels[0].layers[0].histogram = cast(Any, {"stat": "count"})
    assert any("histogram must be HistogramSpec" in i for i in mp.validate(invalid))


def test_projection_and_y2_rejected_and_direct_legacy_style_options_not_ignored():
    p = (
        mp.plot(data())
        .hist("x", stat="count", axis="y2")
        .secondary_yaxis(label="second")
    )
    assert any("axis='y2' is not supported" in i for i in mp.validate(p.spec))
    p = mp.plot(data()).hist("x", stat="count").projection_polar()
    assert any("polar" in i for i in mp.validate(p.spec))
    q = mp.plot(data()).dispatch(A.AddLayer(LayerSpec(type="hist", x="x", orient="h")))
    assert any("options require HistogramSpec" in i for i in mp.validate(q.spec))


@pytest.mark.parametrize(
    "element,multiple",
    [
        ("bars", "layer"),
        ("bars", "stack"),
        ("bars", "dodge"),
        ("step", "layer"),
        ("step", "stack"),
    ],
)
def test_editor_json_weighted_histogram_path_and_unknown_nested_keys(element, multiple):
    from dashboard.editor_server import EditorSession, _build_action

    session = EditorSession()
    session.dispatch_safe(A.SetData(data()))
    session.dispatch_safe(
        _build_action(
            "add_layer_json",
            {
                "layer_type": "hist",
                "layer_json": json.dumps(
                    {
                        "x": "x",
                        "bins": [0, 1, 3],
                        "group": "g",
                        "histogram": {
                            "stat": "density",
                            "weights": "w",
                            "multiple": multiple,
                            "element": element,
                        },
                    }
                ),
            },
            session.store.state,
        )
    )
    assert session.error is None and session.png.startswith(b"\x89PNG")
    assert b"<svg" in session.export("svg")
    with pytest.raises(ValueError, match="unknown HistogramSpec"):
        _build_action(
            "add_layer_json",
            {"layer_type": "hist", "layer_json": '{"x":"x","histogram":{"kde":true}}'},
            session.store.state,
        )


@pytest.mark.parametrize("extension", ["png", "pdf", "svg"])
@pytest.mark.parametrize(
    "element,multiple",
    [
        ("bars", "layer"),
        ("bars", "stack"),
        ("bars", "dodge"),
        ("step", "layer"),
        ("step", "stack"),
    ],
)
def test_same_environment_exports_reproducible_and_do_not_use_global_rng(
    tmp_path, extension, element, multiple
):
    p = (
        mp.plot(data())
        .hist(
            "x",
            bins=[0, 1, 3],
            stat="percent",
            weights="w",
            group="g",
            alpha=0.65,
            multiple=multiple,
            element=element,
        )
        .size(4, 3)
    )
    before = np.random.get_state()
    a, b = tmp_path / f"a.{extension}", tmp_path / f"b.{extension}"
    plt.close(p.save(a))
    plt.close(mp.Plot.from_json(p.to_json()).save(b))
    assert a.read_bytes() == b.read_bytes()
    after = np.random.get_state()
    assert before[0] == after[0] and before[2:] == after[2:]
    np.testing.assert_array_equal(before[1], after[1])
