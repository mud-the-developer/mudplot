"""C05 relative mass, stable band ownership, actual native effects and admission."""

from __future__ import annotations

import io
import math
import xml.etree.ElementTree as ET
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
from statistics import NormalDist

import matplotlib

matplotlib.use("Agg")

import itertools
from datetime import UTC

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import PathCollection
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon, Rectangle
from mudplot._letter_value import letter_value_summary
from mudplot.spec import LayerSpec


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def reference(values, weights, depth, *, full=False):
    """Definition-level Fraction oracle; no product selectors/stat helpers."""
    pairs = [(x, Fraction(w)) for x, w in zip(values, weights, strict=True) if w > 0]
    total = sum((w for _, w in pairs), Fraction())
    ordered = sorted(pairs)

    def q(p):
        mass = Fraction()
        for x, w in ordered:
            mass += w
            if mass >= p * total:
                return x
        raise AssertionError("CDF never reached probability")

    lower = [Fraction(1, 2**exponent) for exponent in range(depth + 1, 1, -1)]
    probabilities = lower + [1 - p for p in lower[::-1]]
    if full:
        probabilities[0], probabilities[-1] = Fraction(0), Fraction(1)
    edges = [q(p) for p in probabilities]
    masses = [
        sum(
            (
                w
                for x, w in pairs
                if low <= x and (x <= high if i == len(edges) - 2 else x < high)
            ),
            Fraction(),
        )
        / total
        for i, (low, high) in enumerate(itertools.pairwise(edges))
    ]
    tails = tuple(x for x, _ in pairs if x < edges[0] or x > edges[-1])
    tail_mass = (
        sum((w for x, w in pairs if x < edges[0] or x > edges[-1]), Fraction()) / total
    )
    effective = total**2 / sum((w * w for _, w in pairs), Fraction())
    densities = [
        m / (Fraction(hi) - Fraction(lo)) if hi > lo else Fraction()
        for m, lo, hi in zip(masses, edges[:-1], edges[1:], strict=True)
    ]
    widths = [float(d / max(densities)) for d in densities] if any(densities) else None
    return edges, masses, tails, tail_mass, effective, q(Fraction(1, 2)), widths


def trunc_binary_exponent(value):
    """Independent rational interval search rather than floating logarithms."""
    if value >= 1:
        exponent = 0
        while 2 ** (exponent + 1) <= value:
            exponent += 1
        return exponent
    exponent = 0
    while Fraction(1, 2 ** (1 - exponent)) >= value:
        exponent -= 1
    return exponent


def test_left_quantiles_and_half_open_atom_ownership_conserve_actual_mass():
    s = letter_value_summary([0, 10, 20], weights=[1, 2, 1], k_depth=1)
    assert (s.values, s.median, s.fliers) == ((0, 10), 10, (20,))
    assert s.masses == (Fraction(3, 4),)
    assert s.tail_mass == Fraction(1, 4) and s.effective_size == Fraction(8, 3)
    full = letter_value_summary(
        [0, 10, 20], weights=[1, 2, 1], k_depth="full", width_method="area"
    )
    assert full.values == (0, 0, 10, 20)
    assert full.masses == (0, Fraction(1, 4), Fraction(3, 4))
    assert full.widths == (0, 1 / 3, 1) and full.tail_mass == 0
    assert sum(full.masses) + full.tail_mass == 1


@pytest.mark.parametrize("depth", [1, 2, 5, 32])
@pytest.mark.parametrize(
    "values,weights",
    [
        ([20, 0, 10, 20, 30], [1, 1, 2, 1, 1]),
        ([0, 1, 2, 3], [math.ulp(0), 1, 2, float.fromhex("0x1.fffffffffffffp+1023")]),
        ([2, 2, 2, 2], [1, math.ulp(0), 2, 0]),
        ([-1e308, 0, 1e308, 1e308], [1, 2, 1, 3]),
    ],
)
def test_exact_weighted_cdf_mass_and_physical_tails_match_independent_reference(
    depth, values, weights
):
    expected = reference(values, weights, depth)
    s = letter_value_summary(values, weights=weights, k_depth=depth)
    assert s.values == tuple(expected[0]) and s.masses == tuple(expected[1])
    assert s.fliers == expected[2] and s.tail_mass == expected[3]
    assert s.effective_size == expected[4] and s.median == expected[5]
    assert sum(s.masses) + s.tail_mass == 1
    if expected[6] is not None and all(
        width > 0 or mass == 0 or hi == lo
        for width, mass, lo, hi in zip(
            expected[6], expected[1], expected[0][:-1], expected[0][1:], strict=True
        )
    ):
        area = letter_value_summary(
            values, weights=weights, k_depth=depth, width_method="area"
        )
        assert area.widths == tuple(expected[6])


@pytest.mark.parametrize("method", ["full", "tukey", "proportion", "trustworthy"])
@pytest.mark.parametrize(
    "weights",
    [[1] * 64, [1, 2, 1], [1, 1, 1, 1.0000000000000002], [math.ulp(0), 1, 1e308]],
)
def test_named_depth_uses_physical_kish_and_exact_exponent_boundaries(method, weights):
    masses = list(map(Fraction, weights))
    effective = sum(masses) ** 2 / sum(w * w for w in masses)
    n = trunc_binary_exponent(effective)
    if method == "full":
        expected = n + 1
    elif method == "tukey":
        expected = n - 3
    elif method == "proportion":
        expected = n - trunc_binary_exponent(effective * Fraction(0.007)) + 1
    else:
        threshold = Fraction(2 * NormalDist().inv_cdf(0.05 / 2) ** 2)
        expected = trunc_binary_exponent(effective / threshold) + 1
    s = letter_value_summary(range(len(weights)), weights=weights, k_depth=method)
    assert s.depth == min(32, max(1, expected))
    split = letter_value_summary([0, 10, 10, 20], weights=[1, 1, 1, 1], k_depth="full")
    if weights == [1, 2, 1] and method == "full":
        assert s.depth == 2 and split.depth == 3


def patches(ax):
    return [patch for patch in ax.patches if isinstance(patch, Polygon)]


@pytest.mark.parametrize("orient", ["v", "h"])
def test_weighted_native_band_area_and_observed_tail_order(orient):
    p = mp.plot({"cat": ["A"] * 3, "v": [0, 10, 20], "w": [1, 2, 1]}).boxenplot(
        "cat",
        "v",
        weights="w",
        orient=orient,
        k_depth="full",
        width_method="area",
        width=0.6,
    )
    ax = p.render().axes[0]
    category_dim, value_dim = int(orient == "h"), int(orient == "v")
    bands = patches(ax)
    assert len(bands) == 3
    for band, lo, hi, relative in zip(
        bands, [0, 0, 10], [0, 10, 20], [0, 1 / 3, 1], strict=True
    ):
        points = band.get_xy()
        np.testing.assert_array_equal(
            [points[:, value_dim].min(), points[:, value_dim].max()], [lo, hi]
        )
        assert points[:, category_dim].max() - points[
            :, category_dim
        ].min() == pytest.approx(0.6 * relative)
    tail_data = {"v": [40, -1, 0, 40, 1, 99], "w": [1, 1, 20, 1, 20, 0]}
    tails = (
        mp.plot(tail_data)
        .boxenplot("v", weights="w", k_depth=1, orient=orient)
        .render()
        .axes[0]
        .lines[1]
    )
    np.testing.assert_array_equal(
        tails.get_xdata() if orient == "h" else tails.get_ydata(), [40, -1, 40]
    )
    assert p.spec.data.columns["w"] == [1, 2, 1]


def test_stable_rank_and_fieldwise_raw_hue_band_precedence_are_actual_native_traits():
    data = {"cat": ["A"] * 8, "v": [0, 1, 2, 3] * 2, "h": [True] * 4 + [1] * 4}
    options = {
        "band_components": [
            {"rank": 0, "side": "central", "body": {"color": "#112233", "hatch": "/"}}
        ],
        "hue_components": [
            {
                "level": True,
                "components": {"body": {"edge_color": "#aa0000", "alpha": 0.9}},
                "band_components": [
                    {"rank": 0, "side": "central", "body": {"color": "#00aa00"}}
                ],
            }
        ],
    }
    for depth in (2, 3):
        p = mp.plot(data).boxenplot(
            "cat", "v", group="h", k_depth=depth, boxen=options, alpha=0.75
        )
        bands = patches(p.render().axes[0])
        central_true, central_one = bands[depth - 1], bands[(2 * depth - 1) + depth - 1]
        assert central_true.get_facecolor() == to_rgba("#00aa00", 0.9)
        assert central_one.get_facecolor() == to_rgba("#112233", 0.75)
        assert central_true.get_edgecolor() == to_rgba("#aa0000", 0.9)
        assert central_true.get_hatch() == central_one.get_hatch() == "/"


def test_numeric_hue_all_bands_match_actual_colourbar_without_tail_retint():
    data = {"v": [0, 1, 2, 3] * 2, "h": [0] * 4 + [10] * 4}
    p = mp.plot(data).boxenplot(
        "v",
        hue="h",
        semantics={"hue_kind": "numeric"},
        boxen={},
        k_depth=3,
        colorbar=True,
        alpha=0.8,
    )
    fig = p.render()
    bar = fig.axes[1].collections[-1]
    bands = patches(fig.axes[0])
    assert len(bands) == 10
    for group, value in enumerate((0, 10)):
        expected = np.asarray(bar.cmap(bar.norm(np.array([value], dtype=float))))[0]
        expected[3] = 0.8
        for band in bands[group * 5 : (group + 1) * 5]:
            np.testing.assert_allclose(np.asarray(band.get_facecolor()), expected)


def test_body_size_and_dash_glyph_roles_have_distinct_real_native_owners():
    data = {
        "v": [0, 0, 1, 30] * 2,
        "w": [20, 20, 20, 1] * 2,
        "s": ["a"] * 4 + ["b"] * 4,
        "z": [0] * 4 + [1] * 4,
    }
    p = mp.plot(data).boxenplot(
        "v",
        weights="w",
        style="s",
        size="z",
        semantics={"sizes": [0, 3], "markers": ["P", "X"], "dashes": ["--", ":"]},
        components={"median": {"line_width": 1.7}, "flier": {"marker_size": 4.2}},
        k_depth=1,
    )
    ax = p.render().axes[0]
    bands = patches(ax)
    assert [band.get_linewidth() for band in bands] == [0, 3]
    assert all(np.asarray(band.get_facecolor(), dtype=float)[-1] > 0 for band in bands)
    observed = [line for line in ax.lines if line.get_marker() in ("P", "X")]
    assert [line.get_marker() for line in observed] == ["P", "X"]
    assert all(line.get_markersize() == 4.2 for line in observed)
    medians = [line for line in ax.lines if len(np.asarray(line.get_ydata())) == 2]
    assert all(line.get_linewidth() == 1.7 for line in medians)
    no_tails = (
        mp.plot({"v": [0, 1, 2, 3], "s": ["a", "a", "b", "b"]})
        .boxenplot(
            "v",
            style="s",
            semantics={"markers": ["o"], "dashes": ["--", ":"]},
            k_depth="full",
        )
        .render()
        .axes[0]
    )
    legend = no_tails.get_legend()
    assert legend is not None
    legend_marks = [artist.get_marker() for artist in legend.findobj(Line2D)]
    assert not set(legend_marks) & {"o", "P", "X"}


def test_selected_zero_missing_and_invalid_weights_have_one_paired_cohort():
    data = {
        "c": ["A", "A", "A", "A", "B", "A"],
        "v": [0, 10, 999, None, 500, 20],
        "w": [1, 2, 0, -5, -99, 1],
    }
    p = mp.plot(data).boxenplot("c", "v", weights="w", order=["A", "empty"], k_depth=1)
    ax = p.render().axes[0]
    np.testing.assert_array_equal(ax.lines[0].get_ydata(), [10, 10])
    np.testing.assert_array_equal(ax.lines[1].get_ydata(), [20])
    assert [t.get_text() for t in ax.get_xticklabels()] == ["A", "empty"]
    invalid = p.spec
    invalid.data.columns["w"][0] = -1
    with pytest.raises(ValueError):
        mp.assert_valid(invalid)
    empty = mp.plot({"c": ["A"], "v": [2], "w": [0]}).boxenplot(
        "c", "v", weights="w", order=["A", "empty"]
    )
    empty_ax = empty.render().axes[0]
    assert not patches(empty_ax) and not empty_ax.lines
    assert [t.get_text() for t in empty_ax.get_xticklabels()] == ["A", "empty"]


@pytest.mark.parametrize(
    "options",
    [
        {"band_components": [{"rank": 0, "side": "lower", "body": {"color": "red"}}]},
        {"band_components": [{"rank": 2, "side": "upper", "body": {"hatch": "/"}}]},
        {"band_components": [{"rank": 0, "side": "central", "body": {"marker": "o"}}]},
        {
            "hue_components": [
                {"level": "absent", "components": {"body": {"color": "red"}}}
            ]
        },
    ],
)
def test_impossible_rank_owned_trait_and_unknown_raw_hue_reject(options):
    p = mp.plot({"c": ["A"] * 4, "v": [0, 1, 2, 3], "h": ["present"] * 4}).boxenplot(
        "c", "v", group="h", k_depth=2, boxen=options
    )
    existing = set(plt.get_fignums())
    with pytest.raises(ValueError):
        p.render()
    assert set(plt.get_fignums()) == existing


def test_advanced_positive_row_and_raw_tuple_cell_limits_do_not_count_zero_rows():
    p = mp.plot({"v": list(range(10001)), "w": [1] * 10000 + [0]}).boxenplot(
        "v", weights="w", k_depth=1, showfliers=False
    )
    np.testing.assert_array_equal(p.render().axes[0].lines[0].get_ydata(), [4999, 4999])
    invalid = p.spec
    invalid.data.columns["w"][-1] = 1
    with pytest.raises(ValueError):
        mp.assert_valid(invalid)
    tuples = mp.plot({"v": list(range(256)), "h": list(range(256))}).boxenplot(
        "v", semantics={"hue": "h", "hue_kind": "numeric"}
    )
    actual = [
        float(np.asarray(line.get_ydata())[0]) for line in tuples.render().axes[0].lines
    ]
    assert actual == list(range(256))
    invalid = tuples.spec
    invalid.data.columns["v"].append(256)
    invalid.data.columns["h"].append(256)
    with pytest.raises(ValueError):
        mp.assert_valid(invalid)


def test_actual_figure_band_work_counts_repeated_layers_without_deduplication():
    data = {"c": [], "h": [], "v": []}
    for category in range(64):
        for hue in range(4):
            for value in (0, 1):
                data["c"].append(category)
                data["h"].append(hue)
                data["v"].append(value)
    p = mp.plot(data)
    for _ in range(2):
        p.boxenplot("c", "v", group="h", boxen={}, k_depth=32, showfliers=False)
    p.boxenplot(
        "c", "v", group="h", boxen={}, k_depth=32, order=[0, 1], showfliers=False
    )
    valid = p.spec
    mp.assert_valid(valid)  # 520 cells *63 =32760; physical uses, not deduplicated
    admitted = mp.Plot.from_json(mp.to_json(valid)).render().axes[0]
    actual_bands = patches(admitted)
    assert len(actual_bands) == 520 * 63
    np.testing.assert_array_equal(
        [actual_bands[0].get_xy()[:, 1].min(), actual_bands[0].get_xy()[:, 1].max()],
        [2**-33, 2**-32],
    )
    invalid = deepcopy(valid)
    invalid.panels[0].layers[-1].order = [0, 1, 2]
    invalid.panels[0].layers[-1].hue_order = [0, 1, 2]
    # Valid SOURCE; the actual aggregate effect budget rejects before allocation.
    mp.assert_valid(invalid)
    existing = set(plt.get_fignums())
    with pytest.raises(ValueError):
        mp.Plot.from_json(mp.to_json(invalid)).render()
    assert set(plt.get_fignums()) == existing


@pytest.mark.parametrize(
    "panel,index",
    [
        (True, 0),
        (False, 0),
        (-1, 0),
        (1, 0),
        (0.0, 0),
        (0, True),
        (0, False),
        (0, -1),
        (0, 1),
        (0, 0.0),
    ],
)
def test_replace_layer_requires_existing_nonbool_integer_indices(panel, index):
    p = mp.plot({"v": [0, 10, 20], "w": [1, 2, 1]}).boxenplot("v", k_depth=1)
    before, history = p.to_json(), p.action_log
    replacement = LayerSpec(type="boxenplot", x="v", weights="w", k_depth=1)
    with pytest.raises(ValueError):
        p.dispatch(mp.actions.ReplaceLayer(index, replacement, panel=panel))
    assert p.to_json() == before and p.action_log == history
    np.testing.assert_array_equal(p.render().axes[0].lines[0].get_ydata(), [10, 10])


def test_replace_layer_preserves_native_content_order_and_history():
    data = {"x": [0, 1, 2], "v": [0, 10, 20], "w": [1, 2, 1]}
    p = mp.plot(data).line("x", "v").boxenplot("v", k_depth=1)
    p.mosaic([["main"]]).inset("main", [0.55, 0.55, 0.35, 0.35], panel_id="detail")
    p.boxenplot("v", k_depth=1, panel=1)
    before = p.to_json()
    supplied_bands = [
        mp.BoxenBandComponentsSpec(0, "central", mp.ComponentStyleSpec(color="#aa0000"))
    ]
    replacement = LayerSpec(
        type="boxenplot",
        x="v",
        weights="w",
        k_depth=1,
        alpha=0.7,
        boxen=mp.BoxenSpec(band_components=supplied_bands),
    )
    p.dispatch(mp.actions.ReplaceLayer(1, replacement))
    after = p.to_json()
    # Caller mutation cannot leak into stored content or later redo snapshots.
    replacement.x = "missing"
    supplied_bands[0].body.color = "#00aa00"
    ax = p.render().axes[0]
    assert len(ax.lines) == 3  # original line, replacement median, actual flier
    np.testing.assert_array_equal(ax.lines[0].get_ydata(), data["v"])
    np.testing.assert_array_equal(ax.lines[1].get_ydata(), [10, 10])
    np.testing.assert_array_equal(ax.lines[2].get_ydata(), [20])
    assert patches(ax)[0].get_facecolor() == to_rgba("#aa0000", 0.7)
    assert len(ax.child_axes) == 1
    np.testing.assert_array_equal(ax.child_axes[0].lines[0].get_ydata(), [10, 10])
    np.testing.assert_allclose(
        (ax.child_axes[0].get_position().x0 - ax.get_position().x0)
        / ax.get_position().width,
        0.55,
    )
    p.store.undo()
    assert p.to_json() == before
    assert len(p.render().axes[0].collections) == 1
    p.store.redo()
    assert p.to_json() == after
    reopened = mp.Plot.from_json(after)
    layer = reopened.spec.panels[0].layers[1]
    layer.boxen = mp.BoxenSpec(
        band_components=[
            mp.BoxenBandComponentsSpec(
                0, "central", mp.ComponentStyleSpec(color="#0000aa")
            )
        ]
    )
    reopened.dispatch(mp.actions.ReplaceLayer(1, layer))
    assert patches(reopened.render().axes[0])[0].get_facecolor() == to_rgba(
        "#0000aa", 0.7
    )
    assert reopened.spec.data.columns == data
    assert [panel.panel_id for panel in reopened.spec.panels] == ["main", "detail"]


def test_replace_live_cell_keeps_recipe_and_template_update_supersedes_local_override():
    data = {
        "facet": ["left"] * 3 + ["right"] * 3,
        "v": [0, 10, 20, 100, 110, 120],
        "w": [1, 2, 1] * 2,
    }
    p = mp.plot(data).boxenplot("v", k_depth=1).facet(col="facet", live=True)
    p.rename_panel("panel1", "left-cell")
    panel_ids = [panel.panel_id for panel in p.spec.panels]
    recipe = p.spec.facet_template
    assert recipe is not None
    template = deepcopy(recipe.template)
    local = p.spec.panels[0].layers[0]
    local.weights = "w"
    p.dispatch(mp.actions.ReplaceLayer(0, local))
    assert p.spec.facet_template is not None
    left, right = p.render().axes
    np.testing.assert_array_equal(left.lines[1].get_ydata(), [20])
    np.testing.assert_array_equal(right.lines[1].get_ydata(), [100, 120])
    reopened = mp.Plot.from_json(p.to_json())
    template.layers[0] = replace(template.layers[0], weights="w", boxen=mp.BoxenSpec())
    reopened.facet_template(template)
    assert reopened.spec.facet_template is not None
    assert [panel.panel_id for panel in reopened.spec.panels] == panel_ids
    left, right = reopened.render().axes
    np.testing.assert_array_equal(left.lines[1].get_ydata(), [20])
    np.testing.assert_array_equal(right.lines[1].get_ydata(), [120])


@pytest.mark.parametrize("orient", ["v", "h"])
def test_log_native_y2_geometry_and_fliers_retain_actual_source_observations(orient):
    values = [0.3, 1, 10, 30, 100]
    data = {"c": [10] * 5, "v": values, "w": [1, 20, 20, 1, 1]}
    p = mp.plot(data).secondary_yaxis("independent")
    p.boxenplot(
        "c",
        "v",
        weights="w",
        native_scale=True,
        orient=orient,
        axis="y2",
        stat_scale="axis",
        k_depth=1,
    )
    value_axis, category_axis = ("x", "y2") if orient == "h" else ("y2", "x")
    p.axis_scale(value_axis, "log").axis_scale(category_axis, "log")
    fig = p.render()
    ax = fig.axes[1]
    band = patches(ax)[0].get_xy()
    value_dim = int(orient == "v")
    np.testing.assert_allclose(
        [band[:, value_dim].min(), band[:, value_dim].max()], [1, 10]
    )
    flier = ax.lines[1]
    np.testing.assert_array_equal(
        flier.get_xdata() if orient == "h" else flier.get_ydata(), [0.3, 30, 100]
    )
    assert p.spec.data.columns == data


def test_declared_clocks_preserve_source_and_weights_cannot_be_time_coordinates():
    data = {
        "when": [
            "2025-01-01T00:00:00Z",
            "2025-01-03T00:00:00Z",
            "2025-01-05T00:00:00Z",
        ],
        "w": [1, 2, 1],
    }
    p = mp.plot(data).date_axis("y").boxenplot("when", weights="w", k_depth=1)
    ax = p.render().axes[0]
    from datetime import datetime

    expected = datetime(2025, 1, 3, tzinfo=UTC).timestamp() / 86400
    np.testing.assert_array_equal(ax.lines[0].get_ydata(), [expected, expected])
    assert p.spec.data.columns == data
    invalid = mp.plot(data).date_axis("y").boxenplot("when", weights="when", k_depth=1)
    with pytest.raises(ValueError):
        mp.assert_valid(invalid.spec)


def test_four_style_legend_strokes_match_actual_band_svg_strokes():
    data = {
        "v": [0, 1, 2, 10] * 4,
        "protocol": [name for name in ("A", "B", "C", "D") for _ in range(4)],
    }
    p = (
        mp.plot(data)
        .boxenplot(
            "v",
            style="protocol",
            k_depth=1,
            line_width=1.5,
            color="#336699",
            semantics={"markers": ["o", "s", "^", "D"]},
        )
        .legend(title="Protocol", location="outside right")
        .size(9, 5)
    )
    figure = p.render()
    axis = figure.axes[0]
    legend = axis.get_legend()
    assert legend is not None
    bands, guides = patches(axis), legend.get_patches()
    assert len(bands) == len(guides) == 4
    for i, (band, guide) in enumerate(zip(bands, guides, strict=True)):
        # GIDs identify real provider-rendered paths; no style/geometry override.
        band.set_gid(f"c05-band-{i}")
        guide.set_gid(f"c05-guide-{i}")
    vector = io.StringIO()
    figure.savefig(vector, format="svg")
    root = ET.fromstring(vector.getvalue())

    def rendered_dash(gid):
        group = next(node for node in root.iter() if node.get("id") == gid)
        path = next(node for node in group.iter() if node.tag.endswith("path"))
        style = dict(
            part.strip().split(":", 1)
            for part in path.get("style", "").split(";")
            if ":" in part
        )
        return style.get("stroke-dasharray", "solid").strip()

    actual = [rendered_dash(f"c05-band-{i}") for i in range(4)]
    shown = [rendered_dash(f"c05-guide-{i}") for i in range(4)]
    assert actual == shown
    assert len(set(actual)) == 4  # all requested styles have distinct real strokes


def test_old_supported_component_none_does_not_opt_into_new_row_admission():
    p = mp.plot({"v": list(range(10001))}).boxenplot(
        "v",
        k_depth=1,
        components={"flier": {"marker": "none"}},
    )
    axis = p.render().axes[0]
    np.testing.assert_array_equal(axis.lines[0].get_ydata(), [5000, 5000])
    observed = np.asarray(axis.lines[1].get_ydata())
    np.testing.assert_array_equal(
        observed,
        [
            *range(2500),
            *range(7501, 10001),
        ],
    )


def test_independent_style_partition_does_not_consume_the_unmapped_hue_palette_twice():
    data = {
        "v": [0, 1, 2, 10] * 4,
        "protocol": [name for name in ("A", "B", "C", "D") for _ in range(4)],
    }
    control = (
        mp.plot(data)
        .palette(
            hue_start=120,
            lightness=55,
            chroma=45,
        )
        .boxenplot("v", boxen={}, k_depth=1, alpha=0.8)
    )
    expected = patches(control.render().axes[0])[0].get_facecolor()
    styled = (
        mp.plot(data)
        .palette(
            hue_start=120,
            lightness=55,
            chroma=45,
        )
        .boxenplot("v", style="protocol", k_depth=1, alpha=0.8)
    )
    actual = patches(styled.render().axes[0])
    assert len(actual) == 4
    for band in actual:
        np.testing.assert_allclose(
            np.asarray(band.get_facecolor()), np.asarray(expected)
        )


@pytest.mark.parametrize(
    "values",
    [
        [math.ulp(0), 2 * math.ulp(0)],
        [math.ulp(0), 4 * math.ulp(0)],
        [-math.ulp(0), 2 * math.ulp(0)],
        [2**53 + 1, 2**53 + 2],
        [2**53 + 1, 2**53 + 10],
        [2**53 + 1, float(2**53 + 4), 2**53 + 11],
        [-1e308, 1e308],
        [2**53 + 1] * 5,
    ],
)
def test_canonical_type7_interpolation_rounds_only_the_final_result(values):
    ordered = sorted(Fraction(value) for value in values)
    summary = letter_value_summary(values, k_depth=3)
    expected = []
    for probability in summary.percentiles:
        h = Fraction(probability) * (len(ordered) - 1)
        index = h.numerator // h.denominator
        remainder = h - index
        result = (
            ordered[index]
            if remainder == 0
            else (ordered[index] + remainder * (ordered[index + 1] - ordered[index]))
        )
        expected.append(float(result))
    h = Fraction(len(ordered) - 1, 2)
    index = h.numerator // h.denominator
    exact_median = (
        ordered[index]
        if h.denominator == 1
        else (ordered[index] + (h - index) * (ordered[index + 1] - ordered[index]))
    )
    assert summary.values == tuple(expected)
    assert summary.median == float(exact_median)
    assert summary.fliers == tuple(
        value for value in values if value < expected[0] or value > expected[-1]
    )  # chosen FINAL numeric type7 bounds, not a second rational-tail estimator


def test_canonical_left_boundaries_true_atoms_and_actual_native_precision_admission():
    low, high = 2**53, 2**53 + 1
    summary = letter_value_summary(
        [low, high], weights=[1, 1], k_depth=1, width_method="area"
    )
    assert summary.values == (low, high) and summary.median == low
    assert summary.masses == (1,) and summary.fliers == ()
    collapsed = mp.plot({"v": [low, high], "w": [1, 1]}).boxenplot(
        "v",
        weights="w",
        k_depth=1,
        width_method="area",
    )
    before = collapsed.to_json()
    mp.assert_valid(collapsed.spec)
    existing = set(plt.get_fignums())
    with pytest.raises(ValueError):
        collapsed.render()
    assert set(plt.get_fignums()) == existing and collapsed.to_json() == before
    atom = letter_value_summary([low, high], weights=[100, 1], k_depth=1)
    assert atom.values == (low, low) and atom.fliers == (high,)
    assert atom.masses == (Fraction(100, 101),) and atom.tail_mass == Fraction(1, 101)
    requested = mp.plot({"v": [low, high], "w": [100, 1]}).boxenplot(
        "v",
        weights="w",
        k_depth=1,
        showfliers=True,
    )
    with pytest.raises(ValueError):
        requested.render()  # actual requested strict-tail ordering cannot be shown
    hidden = (
        mp.plot({"v": [low, high], "w": [100, 1]})
        .boxenplot(
            "v",
            weights="w",
            k_depth=1,
            showfliers=False,
            showmedians=True,
            width=0.6,
        )
        .render()
        .axes[0]
    )
    assert len(hidden.lines) == 1
    np.testing.assert_array_equal(hidden.lines[0].get_ydata(), [low, low])
    points = patches(hidden)[0].get_xy()
    assert points[:, 1].min() == points[:, 1].max() == low
    assert np.ptp(points[:, 0]) == pytest.approx(0.6)


def test_native_rounding_and_atomic_precision_admission(
    tmp_path,
):
    from dashboard.editor_server import EditorSession

    tiny = math.ulp(0)
    p = mp.plot({"v": [tiny, 2 * tiny]}).boxenplot("v", k_depth=1)
    axis = p.render().axes[0]
    np.testing.assert_array_equal(axis.lines[0].get_ydata(), [2 * tiny, 2 * tiny])
    assert len(axis.lines) == 1  # final numeric bounds do not invent strict tails
    wide = mp.plot({"v": [2**53 + 1, 2**53 + 10]}).boxenplot("v", k_depth=1)
    axis = wide.render().axes[0]
    np.testing.assert_array_equal(axis.lines[0].get_ydata(), [2**53 + 6] * 2)
    session = EditorSession()
    session.load_spec(mp.plot({"v": [0, 10]}).boxenplot("v", k_depth=1).to_json())
    old_spec, old_png, old_history = (
        mp.to_json(session.store.state),
        session.png,
        session.action_log(),
    )
    session.dispatch_safe(mp.actions.SetData({"v": [2**53 + 1, 2**53 + 2]}))
    assert session.error is not None
    assert mp.to_json(session.store.state) == old_spec
    assert session.png == old_png and session.action_log() == old_history
    bad = mp.plot({"v": [2**53 + 1, 2**53 + 2]}).boxenplot("v", k_depth=1)
    kept = tmp_path / "owned.png"
    kept.write_bytes(b"previous owned output")
    original = bad.to_json()
    with pytest.raises(ValueError):
        bad.save(str(kept))
    assert kept.read_bytes() == b"previous owned output" and bad.to_json() == original


def test_shared_raw_size_domain_keeps_mark_specific_native_units_and_guides():
    # 14000 physical member-row uses share only4000 original normalization rows.
    x = np.tile(np.linspace(1, 2, 1000), 4)
    size = np.repeat([0, 1, 2, 6], 1000)
    data = {
        "c": [1] * 4000,
        "x": x.tolist(),
        "v": (x + 2 * size).tolist(),
        "s": size.tolist(),
        "w": [1] * 3000 + [0] * 1000,
        "row_id": [f"row{i}" for i in range(4000)],
    }
    semantics = {"scale_id": "shared_raw", "size": "s", "sizes": [0.5, 3]}
    p = (
        mp.plot(data)
        .boxenplot(
            "c",
            "v",
            weights="w",
            native_scale=True,
            semantics=semantics,
            k_depth=1,
            showfliers=False,
        )
        .scatter("x", "v", semantics=semantics)
        .lineplot(
            "x",
            "v",
            semantics=semantics,
            errorbar=None,
        )
        .boxenplot(
            "c",
            "v",
            weights="w",
            native_scale=True,
            semantics=semantics,
            k_depth=1,
            showfliers=False,
        )
        .size(11, 6)
    )
    axis = p.render().axes[0]
    bands = patches(axis)
    assert len(bands) == 6  # two actual three-cell Boxen views, not deduplicated work
    expected_body = [0.5, 0.5 + 2.5 / 6, 0.5 + 5 / 6]
    np.testing.assert_allclose(
        [band.get_linewidth() for band in bands], expected_body * 2
    )
    scatter = [item for item in axis.collections if isinstance(item, PathCollection)]
    assert len(scatter) == 1
    np.testing.assert_allclose(np.sqrt(scatter[0].get_sizes()), 0.5 + 2.5 * size / 6)
    curves = [line for line in axis.lines if len(np.asarray(line.get_xdata())) == 1000]
    np.testing.assert_allclose(
        [line.get_linewidth() for line in curves], [*expected_body, 3]
    )
    legend = axis.get_legend()
    assert legend is not None
    handles = legend.legend_handles
    body = [handle for handle in handles if isinstance(handle, Rectangle)]
    point = [
        handle
        for handle in handles
        if isinstance(handle, Line2D) and handle.get_marker() == "o"
    ]
    stroke = [
        handle
        for handle in handles
        if isinstance(handle, Line2D)
        and handle.get_marker() in (None, "None", "none", "")
    ]
    np.testing.assert_allclose(
        [handle.get_linewidth() for handle in body], [0.5, 1.75, 3]
    )
    np.testing.assert_allclose(
        [handle.get_markersize() for handle in point], [0.5, 1.75, 3]
    )
    np.testing.assert_allclose(
        [handle.get_linewidth() for handle in stroke], [0.5, 1.75, 3]
    )
    assert len({text.get_text() for text in legend.get_texts()}) == 9
    assert p.spec.data.columns == data


def _rendered_flier_glyph(figure, line):
    line.set_gid("actual-flier-glyph")
    vector = io.StringIO()
    figure.savefig(vector, format="svg")
    root = ET.fromstring(vector.getvalue())
    group = next(node for node in root.iter() if node.get("id") == "actual-flier-glyph")
    uses = [node for node in group.iter() if node.tag.endswith("use")]
    assert len(uses) == 2
    reference = uses[0].get("{http://www.w3.org/1999/xlink}href")
    assert reference is not None
    path = next(node for node in root.iter() if node.get("id") == reference[1:])
    return path.get("d")


@pytest.mark.parametrize("marker", ["+", "x", ".", "P", "X", "p", "h", "8"])
def test_scalar_and_component_flier_glyphs_match_actual_native_reference(marker):
    reference, axis = plt.subplots()
    (native,) = axis.plot(
        [1, 1],
        [0, 9],
        linestyle="none",
        marker=marker,
        markersize=5,
        markerfacecolor="none",
        markeredgewidth=0.8,
    )
    expected = _rendered_flier_glyph(reference, native)
    data = {"v": [0, 1, 2, 9], "w": [1, 2, 2, 1]}
    scalar = (
        mp.plot(data)
        .boxenplot(
            "v",
            weights="w",
            k_depth=1,
            marker=marker,
            marker_size=5,
        )
        .render()
    )
    scalar_flier = scalar.axes[0].lines[1]
    np.testing.assert_array_equal(scalar_flier.get_ydata(), [0, 9])
    assert _rendered_flier_glyph(scalar, scalar_flier) == expected
    component = (
        mp.plot(data)
        .boxenplot(
            "v",
            weights="w",
            k_depth=1,
            components={"flier": {"marker": marker, "marker_size": 5}},
        )
        .render()
    )
    component_flier = component.axes[0].lines[1]
    np.testing.assert_array_equal(component_flier.get_ydata(), [0, 9])
    assert _rendered_flier_glyph(component, component_flier) == expected


@pytest.mark.parametrize("marker", ["+", "x", "."])
def test_unfilled_scalar_flier_choices_do_not_broaden_semantic_style_cycle(marker):
    data = {"v": [0, 1, 2, 9], "w": [1, 2, 2, 1], "style": ["A"] * 4}
    p = mp.plot(data).boxenplot(
        "v",
        weights="w",
        semantics={"style": "style", "markers": [marker]},
    )
    with pytest.raises(ValueError):
        p.render()


@pytest.mark.parametrize(
    "mode", ["vertical-log", "horizontal-log", "value-clock", "category-clock"]
)
def test_secondary_letter_values_survive_filtered_live_cells_and_template_history(mode):
    from datetime import datetime

    from mudplot._layout_render import panel_axes

    data = {
        "facet": ["L"] * 3 + ["R"] * 3,
        "c": [10] * 6,
        "v": [0.3, 1, 10, 3, 10, 100],
        "when": [f"2025-01-{day:02d}T00:00:00Z" for day in (1, 3, 5, 7, 9, 11)],
        "category_date": ["2025-01-01T00:00:00Z"] * 3 + ["2025-02-01T00:00:00Z"] * 3,
        "w": [1, 2, 1] * 2,
        "local_w": [4, 1, 1] * 2,
        "stroke": [1] * 3 + [2] * 3,
        "row_id": ["r5", "r2", "r0", "r8", "r7", "r4"],
    }
    orient = "h" if mode in {"horizontal-log", "category-clock"} else "v"
    value = "when" if mode == "value-clock" else "v"
    category = "category_date" if mode == "category-clock" else "c"
    plot = mp.plot(data).secondary_yaxis("Declared observed response")
    value_axis, category_axis = ("x", "y2") if orient == "h" else ("y2", "x")
    if mode == "value-clock":
        plot.date_axis(value_axis)
    else:
        plot.axis_scale(value_axis, "log")
    if mode == "category-clock":
        plot.date_axis(category_axis)
    else:
        plot.axis_scale(category_axis, "log")
    plot.boxenplot(
        category,
        value,
        orient=orient,
        axis="y2",
        weights="w",
        native_scale=True,
        k_depth=1,
        stat_scale="data" if mode == "value-clock" else "axis",
        semantics={"size": "stroke", "sizes": [0.5, 2], "scale_id": "precision"},
    )
    plot.facet(col="facet", col_order=["L", "empty", "R"], col_wrap=2, live=True)
    plot.rename_panel("panel1", "left-cell")
    identities = [panel.panel_id for panel in plot.spec.panels]
    selectors = [panel.filters for panel in plot.spec.panels]
    plot.layout(2, 2, width_ratios=[2, 1])
    assert len(plot.spec.panels) == 3 and plot.spec.facet_template is not None

    def date_number(value):
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() / 86400

    def native_check(candidate, *, local=False, marker=None):
        figure = candidate.render()
        try:
            parents = panel_axes(figure)
            assert len(parents) == 3
            for index, rows in ((0, slice(0, 3)), (2, slice(3, 6))):
                target = parents[index]._mudplot_secondary_axis
                values = data[value][rows]
                if mode == "value-clock":
                    values = [date_number(item) for item in values]
                weights = data["local_w" if local and index == 0 else "w"][rows]
                expected = reference(values, weights, 1)
                median = target.lines[0]
                observed = median.get_xdata() if orient == "h" else median.get_ydata()
                np.testing.assert_array_equal(observed, [expected[5], expected[5]])
                tail = target.lines[1]
                np.testing.assert_array_equal(
                    tail.get_xdata() if orient == "h" else tail.get_ydata(),
                    expected[2],
                )
                band = patches(target)[0]
                assert band.get_linewidth() == (0.5 if index == 0 else 2)
                category_points = (
                    median.get_ydata() if orient == "h" else median.get_xdata()
                )
                center = (
                    sum(category_points) / 2
                    if mode == "category-clock"
                    else math.sqrt(math.prod(category_points))
                )
                expected_center = (
                    date_number(data[category][rows][0])
                    if mode == "category-clock"
                    else 10
                )
                assert center == pytest.approx(expected_center)
                if marker is not None:
                    assert tail.get_marker() == marker
            empty = parents[1]._mudplot_secondary_axis
            assert not empty.patches and not empty.lines
        finally:
            plt.close(figure)

    native_check(plot)
    before = plot.to_json()
    local = plot.spec.panels[0].layers[0]
    local.weights = "local_w"
    plot.dispatch(mp.actions.ReplaceLayer(0, local))
    edited = plot.to_json()
    assert plot.spec.facet_template is not None
    native_check(plot, local=True)
    plot.store.undo()
    assert plot.to_json() == before
    plot.store.redo()
    assert plot.to_json() == edited
    reopened = mp.Plot.from_json(edited)
    template = deepcopy(reopened.spec.facet_template.template)
    template.layers[0].marker = "P"
    reopened.facet_template(template)
    native_check(reopened, marker="P")
    assert [panel.panel_id for panel in reopened.spec.panels] == identities
    assert [panel.filters for panel in reopened.spec.panels] == selectors
    assert reopened.spec.data.columns == data
    final = mp.Plot.from_json(reopened.to_json())
    native_check(final, marker="P")
