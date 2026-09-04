"""Tests for the expanded layer coverage: 3-D (scatter3d/line3d/surface/
wireframe), violin, kde, pie, contour/contourf.
"""

import matplotlib

matplotlib.use("Agg")

import mudplot as mp
import numpy as np
from mudplot._render import render


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
    assert fig.axes[0].get_zlabel() == "Depth"


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
    ydata = fig.axes[0].lines[0].get_ydata()
    assert np.all(ydata >= 0)  # density is non-negative
    assert ydata.max() > 0


def test_kde_grouped_gives_two_curves():
    rng = np.random.default_rng(0)
    data = {
        "v": list(rng.normal(0, 1, 100)) + list(rng.normal(3, 1, 100)),
        "g": ["A"] * 100 + ["B"] * 100,
    }
    p = mp.plot(data).kde("v", group="g").legend()
    fig = render(p.spec)
    assert len(fig.axes[0].lines) == 2


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
        "scatter3d",
        "line3d",
        "surface",
        "wireframe",
        "violin",
        "kde",
        "pie",
        "contour",
        "contourf",
    ):
        assert t in caps["layers"], t


def test_new_types_all_pass_validate_when_built_correctly():
    data = {"x": [0, 1, 2], "y": [0, 1, 2], "z": [0, 1, 2], "cat": ["a", "b", "c"]}
    specs = [
        mp.plot(data).projection3d().scatter3d("x", "y", "z").spec,
        mp.plot(data).projection3d().line3d("x", "y", "z").spec,
        mp.plot({}).matrix("m", _matrix_data()).projection3d().surface("m").spec,
        mp.plot({}).matrix("m", _matrix_data()).projection3d().wireframe("m").spec,
        mp.plot(data).violin("x").spec,
        mp.plot(data).kde("x").spec,
        mp.plot(data).pie("cat", "x").spec,
        mp.plot({}).matrix("m", _matrix_data()).contour("m").spec,
        mp.plot({}).matrix("m", _matrix_data()).contourf("m").spec,
    ]
    for spec in specs:
        assert mp.validate(spec) == [], spec.panels[0].layers
