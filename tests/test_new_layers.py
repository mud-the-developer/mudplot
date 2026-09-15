"""Tests for the expanded layer coverage: 3-D (scatter3d/line3d/surface/
wireframe), violin, kde, rug, regplot, stripplot, stackplot, hist2d, hexbin,
pie, contour/contourf.
"""

from typing import Any, cast

import matplotlib

matplotlib.use("Agg")

import mudplot as mp
import numpy as np
from mudplot._render import _regression_fit, render


def _matrix_data(rows=8, cols=10):
    rng = np.random.default_rng(0)
    return (rng.normal(size=(rows, cols))).tolist()


# --------------------------------------------------------------------------
# 3-D
# --------------------------------------------------------------------------
def test_scatter3d_renders():
    data = {"x": [0, 1, 2], "y": [0, 1, 2], "z": [0, 1, 2]}
    p = mp.plot(data).projection3d().scatter3d("x", "y", "z")
    fig = render(p.spec)
    ax = fig.axes[0]
    assert ax.name == "3d"


def test_line3d_renders():
    data = {"x": [0, 1, 2], "y": [0, 1, 2], "z": [0, 1, 2]}
    p = mp.plot(data).projection3d().line3d("x", "y", "z")
    fig = render(p.spec)
    assert fig.axes[0].name == "3d"


def test_scatter3d_with_colorbar():
    data = {"x": [0, 1, 2], "y": [0, 1, 2], "z": [0, 1, 2], "v": [1, 2, 3]}
    p = mp.plot(data).projection3d().scatter3d("x", "y", "z", c="v", colorbar=True)
    fig = render(p.spec)
    assert len(fig.axes) >= 2  # 3d axes + colorbar axes


def test_surface_renders():
    p = mp.plot({}).matrix("z", _matrix_data()).projection3d().surface("z")
    fig = render(p.spec)
    assert fig.axes[0].name == "3d"


def test_wireframe_renders():
    p = mp.plot({}).matrix("z", _matrix_data()).projection3d().wireframe("z")
    fig = render(p.spec)
    assert fig.axes[0].name == "3d"


def test_3d_layer_in_2d_panel_rejected_by_validate():
    data = {"x": [0, 1], "y": [0, 1], "z": [0, 1]}
    p = mp.plot(data).scatter3d("x", "y", "z")  # no .projection3d()
    issues = mp.validate(p.spec)
    assert any("projection" in i for i in issues)


def test_2d_layer_in_3d_panel_rejected_by_validate():
    data = {"x": [0, 1], "y": [0, 1]}
    p = mp.plot(data).projection3d().line("x", "y")
    issues = mp.validate(p.spec)
    assert any("not a 3-D layer type" in i for i in issues)


def test_invalid_projection_rejected():
    spec = mp.apply(
        [
            {"type": "SetData", "columns": {"x": [1], "y": [1]}},
            {"type": "SetProjection", "projection": "4d"},
            {"type": "AddLayer", "layer": {"type": "line", "x": "x", "y": "y"}},
        ]
    )
    issues = mp.validate(spec)
    assert any("invalid projection" in i for i in issues)


def test_zaxis_set_via_zlabel_builder():
    p = (
        mp.plot({"x": [0, 1], "y": [0, 1], "z": [0, 1]})
        .projection3d()
        .scatter3d("x", "y", "z")
        .zlabel("Depth", limits=[0, 5])
    )
    assert mp.validate(p.spec) == []
    fig = render(p.spec)
    assert cast(Any, fig.axes[0]).get_zlabel() == "Depth"


def test_z_axis_without_3d_projection_flagged():
    p = mp.plot({"x": [1], "y": [2]}).line("x", "y").zlabel("Depth")
    issues = mp.validate(p.spec)
    assert any("z-axis is configured" in i for i in issues)


def test_mixed_2d_3d_panels_in_one_figure():
    data = {"x": [1, 2, 3], "y": [4, 5, 6], "z": [7, 8, 9]}
    p = (
        mp.plot(data)
        .layout(1, 2)
        .line("x", "y", panel=0)
        .projection3d(panel=1)
        .scatter3d("x", "y", "z", panel=1)
    )
    assert mp.validate(p.spec) == []
    fig = render(p.spec)
    assert len(fig.axes) == 2
    assert fig.axes[0].name != "3d"
    assert fig.axes[1].name == "3d"


# --------------------------------------------------------------------------
# violin / kde
# --------------------------------------------------------------------------
def test_violin_renders_and_ticks_labelled():
    data = {"v": [1, 2, 3, 4, 5, 6], "g": ["A", "A", "A", "B", "B", "B"]}
    p = mp.plot(data).violin("v", group="g")
    fig = render(p.spec)
    ax = fig.axes[0]
    assert [t.get_text() for t in ax.get_xticklabels()] == ["A", "B"]


def test_kde_renders_a_smooth_density_curve():
    rng = np.random.default_rng(0)
    data = {"v": list(rng.normal(size=200))}
    p = mp.plot(data).kde("v")
    fig = render(p.spec)
    assert len(fig.axes[0].lines) == 1
    ydata = np.asarray(fig.axes[0].lines[0].get_ydata(), dtype=float)
    assert np.all(ydata >= 0)  # density is non-negative
    assert ydata.max() > 0


def test_kde_grouped_gives_two_redundantly_styled_curves():
    rng = np.random.default_rng(0)
    data = {
        "v": list(rng.normal(0, 1, 100)) + list(rng.normal(3, 1, 100)),
        "g": ["A"] * 100 + ["B"] * 100,
    }
    p = mp.plot(data).kde("v", group="g").legend()
    fig = render(p.spec)
    lines = fig.axes[0].lines
    assert len(lines) == 2
    assert lines[0].get_linestyle() != lines[1].get_linestyle()


def test_stackplot_renders_long_form_groups_with_redundant_hatches():
    data = {
        "x": [0, 1, 2, 0, 1, 2],
        "y": [1, 2, 3, 2, 1, 2],
        "g": ["base"] * 3 + ["top"] * 3,
    }
    p = mp.plot(data).stackplot("x", "y", group="g").legend()
    assert mp.validate(p.spec) == []
    fig = render(p.spec)
    collections = fig.axes[0].collections
    assert len(collections) == 2
    assert collections[0].get_hatch() != collections[1].get_hatch()
    assert fig.axes[0].get_legend_handles_labels()[1] == ["base", "top"]


def test_stackplot_rejects_misaligned_groups_and_nonfinite_values():
    misaligned = mp.plot(
        {
            "x": [0, 1, 0, 2],
            "y": [1, 2, 3, 4],
            "g": ["A", "A", "B", "B"],
        }
    ).stackplot("x", "y", group="g")
    nonfinite = mp.plot(
        {
            "x": [0, 1, 0, 1],
            "y": [1, 2, 3, float("nan")],
            "g": ["A", "A", "B", "B"],
        }
    ).stackplot("x", "y", group="g")
    assert any("same x sequence" in issue for issue in mp.validate(misaligned.spec))
    assert any("finite numbers" in issue for issue in mp.validate(nonfinite.spec))


def test_stripplot_jitter_is_bounded_and_reproducible():
    data = {"category": ["A", "A", "A", "B", "B"], "value": [1, 2, 3, 4, 5]}
    p = mp.plot(data).stripplot("category", "value", jitter=0.1)
    assert mp.validate(p.spec) == []

    first_collection = cast(Any, render(p.spec).axes[0].collections[0])
    second_collection = cast(Any, render(p.spec).axes[0].collections[0])
    first = np.asarray(first_collection.get_offsets())[:, 0]
    second = np.asarray(second_collection.get_offsets())[:, 0]
    centers = np.array([0, 0, 0, 1, 1])
    assert np.array_equal(first, second)
    assert np.all(np.abs(first - centers) <= 0.1)
    assert np.any(first != centers)


def test_stripplot_rejects_bad_or_misplaced_jitter():
    data = {"x": [0, 1], "y": [1, 2]}
    too_wide = mp.plot(data).stripplot("x", "y", jitter=0.6)
    wrong_layer = mp.plot(data).line("x", "y", jitter=0.1)
    assert any("jitter must be" in issue for issue in mp.validate(too_wide.spec))
    assert any("only applies" in issue for issue in mp.validate(wrong_layer.spec))


def test_regplot_renders_polynomial_fit_and_opt_in_confidence_band():
    data = {"x": [-2, -1, 0, 1, 2], "y": [4.2, 1.0, 0.1, 1.1, 3.9]}
    p = mp.plot(data).regplot("x", "y", degree=2, confidence=95)
    assert mp.validate(p.spec) == []
    rebuilt = mp.Plot.from_json(p.to_json())
    layer = rebuilt.spec.panels[0].layers[0]
    assert (layer.degree, layer.confidence) == (2, 95)

    fig = render(rebuilt.spec)
    assert len(fig.axes[0].lines) == 1
    assert np.asarray(fig.axes[0].lines[0].get_xdata()).size == 200
    assert len(fig.axes[0].collections) == 2  # confidence band + observations

    _grid, fitted, interval = _regression_fit(data["x"], data["y"], 2, 95)
    assert interval is not None
    lower, upper = interval
    assert np.all(lower <= fitted)
    assert np.all(fitted <= upper)
    assert np.any(upper > lower)


def test_regplot_rejects_unsafe_fit_settings_and_data():
    data = {"x": [0, 1, 2], "y": [0, 1, 4]}
    bad_degree = mp.plot(data).regplot("x", "y", degree=0)
    bad_confidence = mp.plot(data).regplot("x", "y", confidence=100)
    too_small = mp.plot(data).regplot("x", "y", degree=2, confidence=95)
    nonnumeric = mp.plot({"x": ["a", "b"], "y": [1, 2]}).regplot("x", "y")
    empty = mp.plot({"x": [], "y": []}).regplot("x", "y")
    mismatched = mp.plot({"x": [0, 1], "y": [0]}).regplot("x", "y")
    grouped = mp.plot({"x": [0, 1, 2], "y": [0, 1, 4], "g": ["A", "A", "B"]}).regplot(
        "x", "y", group="g"
    )

    assert any("degree must be" in issue for issue in mp.validate(bad_degree.spec))
    assert any(
        "confidence must be" in issue for issue in mp.validate(bad_confidence.spec)
    )
    assert any(
        "at least 4 observations" in issue for issue in mp.validate(too_small.spec)
    )
    assert any("finite numbers" in issue for issue in mp.validate(nonnumeric.spec))
    assert any("at least 2 observations" in issue for issue in mp.validate(empty.spec))
    assert any("mismatched lengths" in issue for issue in mp.validate(mismatched.spec))
    assert any("group 'B'" in issue for issue in mp.validate(grouped.spec))


def test_rug_marks_each_observation_inside_the_x_axis():
    p = mp.plot({"v": [1, 2, 3]}).rug("v")
    assert mp.validate(p.spec) == []
    fig = render(p.spec)
    segments = cast(Any, fig.axes[0].collections[0]).get_segments()
    assert [segment[0, 0] for segment in segments] == [1, 2, 3]
    assert all((segment[:, 1] == [0, 0.04]).all() for segment in segments)

    issues = mp.validate(mp.plot({"v": [1]}).rug("missing").spec)
    assert any("column 'missing' not found" in issue for issue in issues)


# --------------------------------------------------------------------------
# pie
# --------------------------------------------------------------------------
def test_pie_renders_correct_wedge_count():
    p = mp.plot({"cat": ["A", "B", "C"], "val": [1, 2, 3]}).pie("cat", "val")
    fig = render(p.spec)
    assert len(fig.axes[0].patches) == 3


def test_pie_does_not_duplicate_labels_via_legend():
    # regression guard for the wedge-label/legend overlap bug found while
    # implementing this
    p = mp.plot({"cat": ["A", "B"], "val": [1, 2]}).pie("cat", "val")
    fig = render(p.spec)
    ax = fig.axes[0]
    handles, _labels = ax.get_legend_handles_labels()
    assert handles == []  # wedges must not register as legend handles
    assert ax.get_legend() is None


def test_pie_missing_columns_caught_by_validate():
    p = mp.plot({"cat": ["A"], "val": [1]}).pie("nope", "also_nope")
    issues = mp.validate(p.spec)
    assert len(issues) == 2


# --------------------------------------------------------------------------
# contour / contourf
# --------------------------------------------------------------------------
def test_hist2d_renders_counts_with_lch_colorbar():
    rng = np.random.default_rng(0)
    data = {"x": rng.normal(size=100).tolist(), "y": rng.normal(size=100).tolist()}
    p = mp.plot(data).hist2d("x", "y", bins=8, clabel="count")
    assert mp.validate(p.spec) == []
    fig = render(p.spec)
    counts = np.asarray(cast(Any, fig.axes[0].collections[0]).get_array())
    assert len(fig.axes) == 2
    assert fig.axes[1].get_ylabel() == "count"
    assert counts.sum() == 100


def test_hexbin_renders_counts_with_lch_colorbar():
    rng = np.random.default_rng(1)
    data = {"x": rng.normal(size=80).tolist(), "y": rng.normal(size=80).tolist()}
    p = mp.plot(data).hexbin("x", "y", gridsize=7, mincnt=1)
    assert mp.validate(p.spec) == []
    fig = render(p.spec)
    counts = np.asarray(cast(Any, fig.axes[0].collections[0]).get_array())
    assert len(fig.axes) == 2
    assert counts.sum() == 80


def test_bivariate_density_settings_and_data_are_validated():
    data = {"x": [0, 1, 2], "y": [1, 2, 3], "g": ["A", "A", "B"]}
    bad_bins = mp.plot(data).hist2d("x", "y", bins=[0, 2, 1])
    bad_density = mp.plot(data).hist2d("x", "y", density=cast(Any, "yes"))
    bad_grid = mp.plot(data).hexbin("x", "y", gridsize=0, mincnt=-1)
    grouped = mp.plot(data).hexbin("x", "y", group="g")
    nonnumeric = mp.plot({"x": ["a"], "y": [1]}).hist2d("x", "y")

    assert any("bins must be" in issue for issue in mp.validate(bad_bins.spec))
    assert any("density must be" in issue for issue in mp.validate(bad_density.spec))
    grid_issues = mp.validate(bad_grid.spec)
    assert any("gridsize" in issue for issue in grid_issues)
    assert any("mincnt" in issue for issue in grid_issues)
    assert any("group is not supported" in issue for issue in mp.validate(grouped.spec))
    assert any("finite numbers" in issue for issue in mp.validate(nonnumeric.spec))


def test_contour_renders():
    p = mp.plot({}).matrix("z", _matrix_data()).contour("z")
    fig = render(p.spec)
    assert len(fig.axes) >= 1


def test_contourf_renders_with_colorbar():
    p = mp.plot({}).matrix("z", _matrix_data()).contourf("z", colorbar=True)
    fig = render(p.spec)
    assert len(fig.axes) >= 2


def test_contour_with_explicit_levels():
    p = mp.plot({}).matrix("z", _matrix_data()).contour("z", levels=5)
    fig = render(p.spec)  # should not raise
    assert fig is not None


def test_contour_missing_matrix_caught_by_validate():
    p = mp.plot({}).contour("nope")
    issues = mp.validate(p.spec)
    assert any("nope" in i for i in issues)


# --------------------------------------------------------------------------
# capabilities / schema sanity for the new types
# --------------------------------------------------------------------------
def test_new_types_appear_in_capabilities():
    caps = mp.capabilities()
    for t in (
        "regplot",
        "stripplot",
        "stackplot",
        "hist2d",
        "hexbin",
        "scatter3d",
        "line3d",
        "surface",
        "wireframe",
        "violin",
        "kde",
        "rug",
        "pie",
        "contour",
        "contourf",
    ):
        assert t in caps["layers"], t


def test_new_types_all_pass_validate_when_built_correctly():
    data = {"x": [0, 1, 2], "y": [0, 1, 2], "z": [0, 1, 2], "cat": ["a", "b", "c"]}
    specs = [
        mp.plot(data).regplot("x", "y").spec,
        mp.plot(data).stripplot("cat", "y").spec,
        mp.plot(
            {
                "x": [0, 1, 2, 0, 1, 2],
                "y": [1, 2, 3, 3, 2, 1],
                "g": ["A", "A", "A", "B", "B", "B"],
            }
        )
        .stackplot("x", "y", group="g")
        .spec,
        mp.plot(data).hist2d("x", "y").spec,
        mp.plot(data).hexbin("x", "y").spec,
        mp.plot(data).projection3d().scatter3d("x", "y", "z").spec,
        mp.plot(data).projection3d().line3d("x", "y", "z").spec,
        mp.plot({}).matrix("m", _matrix_data()).projection3d().surface("m").spec,
        mp.plot({}).matrix("m", _matrix_data()).projection3d().wireframe("m").spec,
        mp.plot(data).violin("x").spec,
        mp.plot(data).kde("x").spec,
        mp.plot(data).rug("x").spec,
        mp.plot(data).pie("cat", "x").spec,
        mp.plot({}).matrix("m", _matrix_data()).contour("m").spec,
        mp.plot({}).matrix("m", _matrix_data()).contourf("m").spec,
    ]
    for spec in specs:
        assert mp.validate(spec) == [], spec.panels[0].layers
