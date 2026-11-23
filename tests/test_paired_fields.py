"""Paired scientific/statistic fields: hand mass, native cells and atomic edits."""

from __future__ import annotations

import copy
from fractions import Fraction
from typing import Any, cast

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.axes import Axes
from matplotlib.collections import QuadMesh


def _meshes(figure):
    return [
        artist
        for axes in figure.axes
        for artist in axes.collections
        if isinstance(artist, QuadMesh) and not hasattr(axes, "_colorbar")
    ]


@pytest.mark.parametrize(
    "stat", ["count", "frequency", "probability", "proportion", "percent", "density"]
)
@pytest.mark.parametrize("reopen", [False, True])
def test_weighted_nonsquare_nonuniform_histogram_uses_paired_in_bin_mass(stat, reopen):
    x_edges, y_edges = [0, 1, 3, 6], [0, 2, 5]
    source = {
        "id": ["a", "b", "c", "d", "out-x", "out-y", "missing", "zero"],
        "x": [0.25, 1, 3, 6, -1, 2, None, 2],
        "y": [0.5, 2, 5, 5, 1, 8, 1, 1],
        "w": [1, 2, 3, 4, 100, 200, 300, 0],
    }
    p = mp.plot(source).hist2d(
        "x",
        "y",
        bins=mp.BivariateBinsSpec.from_dict({"x": x_edges, "y": y_edges}),
        stat=stat,
        weights="w",
        colorbar=True,
    )
    serialized = p.to_json()
    assert mp.apply(p.action_log) == p.spec
    if reopen:
        p = mp.Plot.from_json(serialized)
    mass = [[1, 0], [0, 2], [0, 7]]
    expected = np.zeros((3, 2))
    for ix in range(3):
        for iy in range(2):
            value = Fraction(mass[ix][iy])
            area = Fraction(x_edges[ix + 1] - x_edges[ix]) * (
                y_edges[iy + 1] - y_edges[iy]
            )
            if stat in {"frequency", "density"}:
                value /= area
            if stat in {"probability", "proportion", "percent", "density"}:
                value /= 10
            if stat == "percent":
                value *= 100
            expected[ix, iy] = float(value)
    figure = p.render()
    try:
        (mesh,) = _meshes(figure)
        np.testing.assert_array_equal(
            np.asarray(mesh.get_array()).reshape(2, 3), expected.T
        )
        gx, gy = np.meshgrid(x_edges, y_edges)
        np.testing.assert_array_equal(
            mesh.get_coordinates(), np.stack((gx, gy), axis=-1)
        )
        bars = [
            cast(Any, axis)._colorbar
            for axis in figure.findobj(Axes)
            if hasattr(axis, "_colorbar")
        ]
        assert len(bars) == 1 and bars[0].mappable is mesh
        assert mesh.get_clim() == (0, float(expected.max()))
        assert p.to_json() == serialized and p.spec.data.columns == source
    finally:
        plt.close(figure)


@pytest.mark.parametrize("common_norm", [False, True])
def test_histogram_role_tuples_share_effective_typed_hue_normalization(common_norm):
    source = {
        "id": ["bool-small", "bool-large", "number-small", "number-large"],
        "x": [0.5] * 4,
        "y": [0.5] * 4,
        "w": [1, 3, 2, 4],
        "h": [True, True, 1, 1],
        "q": [1, 2, 1, 2],
        "s": ["first", "second", "first", "second"],
    }
    p = mp.plot(source).hist2d(
        "x",
        "y",
        bins=mp.BivariateBinsSpec(x=[0, 1], y=[0, 1]),
        stat="probability",
        weights="w",
        common_norm=common_norm,
        semantics=mp.SemanticSpec(
            hue="h",
            size="q",
            style="s",
            sizes=[0, 3],
            markers=["o"],
            dashes=["--", ":"],
        ),
        colorbar=False,
    )
    figure = p.render()
    try:
        meshes = _meshes(figure)
        assert len(meshes) == 4
        expected = [
            Fraction(weight, 10 if common_norm else total)
            for weight, total in zip(source["w"], [4, 4, 6, 6], strict=True)
        ]
        for index, (mesh, value) in enumerate(zip(meshes, expected, strict=True)):
            np.testing.assert_array_equal(
                np.asarray(mesh.get_array()).ravel(), [float(value)]
            )
            assert float(np.asarray(mesh.get_linewidth())[0]) == (
                0 if index % 2 == 0 else 3
            )
        assert p.spec.data.columns == source
    finally:
        plt.close(figure)


def test_tiny_positive_statistic_colourbar_keeps_the_actual_raw_mappable_domain():
    unit = float.fromhex("0x0.0000000000001p-1022")
    p = mp.plot({"x": [0.25, 0.75], "y": [0.25, 0.75], "w": [unit, unit]}).hist2d(
        "x",
        "y",
        bins={"x": [0, 0.5, 1], "y": [0, 0.5, 1]},
        stat="count",
        weights="w",
        colorbar=True,
        alpha=1,
    )
    figure = p.render()
    try:
        (mesh,) = _meshes(figure)
        bar = next(
            cast(Any, axis)._colorbar
            for axis in figure.findobj(Axes)
            if hasattr(axis, "_colorbar")
        )
        np.testing.assert_array_equal(
            np.asarray(mesh.get_array()).ravel(), [unit, 0, 0, unit]
        )
        assert mesh.get_clim() == (0, unit) and bar.mappable is mesh
        np.testing.assert_array_equal(mesh.norm(np.asarray([0, unit])), [0, 1])
        assert [float(text.get_text()) for text in bar.ax.get_yticklabels()] == [
            0,
            unit,
        ]
        np.testing.assert_array_equal(
            np.asarray(mesh.get_facecolor())[[0, 1]], np.asarray(mesh.cmap([1.0, 0.0]))
        )
    finally:
        plt.close(figure)


@pytest.mark.parametrize("stat", ["proportion", "percent", "count"])
@pytest.mark.parametrize("complementary", [False, True])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_joint_empirical_cells_keep_all_knots_and_strict_or_complement(
    stat, complementary, orient
):
    source = {
        "id": ["a", "b", "c", "d", "zero", "missing"],
        "x": [0, 1, 2, 3, 2, None],
        "y": [3, 1, 0, 2, 1, 1],
        "w": [1, 2, 3, 4, 0, 100],
    }
    p = mp.plot(source).ecdf2d(
        "x",
        "y",
        bounds=[[-1, 4], [-1, 4]],
        weights="w",
        stat=stat,
        complementary=complementary,
        query_x=[0.5, 1.5],
        query_y=[0.5, 1.5],
        orient=orient,
        colorbar=True,
    )
    serialized = p.to_json()
    p = mp.Plot.from_json(serialized)
    figure = p.render()
    try:
        (mesh,) = _meshes(figure)
        coordinates = np.asarray(mesh.get_coordinates())
        x = coordinates[0, :, 0] if orient == "v" else coordinates[:, 0, 1]
        y = coordinates[:, 0, 1] if orient == "v" else coordinates[0, :, 0]
        assert {-1, 0, 1, 2, 3, 0.5, 1.5, 4} == set(x)
        assert {-1, 0, 1, 2, 3, 0.5, 1.5, 4} == set(y)
        expected = np.empty((len(x) - 1, len(y) - 1))
        for ix, a in enumerate(x[:-1]):
            for iy, b in enumerate(y[:-1]):
                prefix = sum(
                    weight
                    for xx, yy, weight in zip(
                        source["x"][:4], source["y"][:4], source["w"][:4], strict=True
                    )
                    if xx <= a and yy <= b
                )
                numerator = 10 - prefix if complementary else prefix
                value = (
                    Fraction(numerator) if stat == "count" else Fraction(numerator, 10)
                )
                if stat == "percent":
                    value *= 100
                expected[ix, iy] = float(value)
        displayed = expected.T if orient == "v" else expected
        np.testing.assert_array_equal(
            np.asarray(mesh.get_array()).reshape(displayed.shape), displayed
        )
        # At(1.5,1.5), OR mass is8; strict AND survival has only4.
        ix, iy = list(x).index(1.5), list(y).index(1.5)
        or_mass = 8 if stat == "count" else 80 if stat == "percent" else 0.8
        if complementary:
            assert expected[ix, iy] == or_mass
        assert p.to_json() == serialized and p.spec.data.columns == source
    finally:
        plt.close(figure)


@pytest.mark.parametrize(
    "case", ["negative_weight", "unknown_kernel", "cdf_mass_levels", "cdf_full_hdr"]
)
def test_invalid_paired_field_edit_keeps_accepted_native_png_spec_and_history(case):
    from dashboard.editor_server import EditorSession
    from mudplot.spec import LayerSpec

    p = mp.plot(
        {
            "x": [0.0, 0.5, 1.0, 2.0],
            "y": [0.0, 1.0, 0.25, 2.0],
            "w": [1, 2, 3, 4],
            "negative": [1, -1, 2, 1],
        }
    ).line("x", "y")
    session = EditorSession()
    session.load_spec(p.to_json())
    accepted = copy.deepcopy(session.store.state.to_dict())
    png, history = session.png, copy.deepcopy(session.store.history)
    if case == "negative_weight":
        layer = LayerSpec(
            type="hist2d",
            x="x",
            y="y",
            bins=mp.BivariateBinsSpec(x=[0, 1], y=[0, 1]),
            histogram2d=mp.Histogram2DSpec(stat="probability", weights="negative"),
        )
    else:
        options = {
            "unknown_kernel": {"kernel": "epanechnikov"},
            "cdf_mass_levels": {"cumulative": True, "level_kind": "mass"},
            "cdf_full_hdr": {
                "cumulative": True,
                "level_kind": "cdf",
                "hdr": mp.HDRSpec(),
            },
        }[case]
        layer = LayerSpec(
            type="kde2d",
            x="x",
            y="y",
            kde2d=mp.KDE2DSpec(weights="w", **options),
        )
    session.dispatch_safe(mp.actions.AddLayer(layer))
    assert session.error is not None
    assert session.store.state.to_dict() == accepted
    assert session.png == png and session.store.history == history


def test_shared_field_roles_keep_real_cell_and_contour_guide_geometries():
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    source = {
        "x": [-1.0, -1.0, 1.0, 1.0] * 2,
        "y": [-1.0, 1.0, -1.0, 1.0] * 2,
        "kind": ["first"] * 4 + ["second"] * 4,
    }
    roles = mp.SemanticSpec(
        style="kind", markers=["o"], dashes=["--", ":"], scale_id="shared"
    )
    p = (
        mp.plot(source)
        .hist2d(
            "x",
            "y",
            bins=mp.BivariateBinsSpec(x=2, y=2),
            stat="count",
            semantics=roles,
            color="#234a70",
            line_width=0,
            colorbar=False,
        )
        .kde2d(
            "x",
            "y",
            gridsize=17,
            bw_method=0.5,
            level_kind="density",
            levels=[0.01, 0.02],
            semantics=roles,
            color="#234a70",
            line_width=3,
            colorbar=False,
        )
    )
    figure = p.render()
    try:
        legend = figure.axes[0].get_legend()
        assert legend is not None
        handles = legend.legend_handles
        cells = [handle for handle in handles if isinstance(handle, Patch)]
        contours = [handle for handle in handles if isinstance(handle, Line2D)]
        assert len(cells) == 2 and len(contours) == 2
        assert all(handle.get_linewidth() == 0 for handle in cells)
        assert all(
            handle.get_linewidth() == 3 and handle.get_marker() in ("None", "")
            for handle in contours
        )
        assert {handle.get_linestyle() for handle in contours} == {"--", ":"}
        assert p.spec.data.columns == source
    finally:
        plt.close(figure)


def test_explicit_paired_row_bound_keeps_old_raw_histogram_and_complete_output(
    tmp_path,
):
    source = {
        "x": list(range(10001)),
        "y": [index % 7 for index in range(10001)],
        "id": [f"row-{index}" for index in range(10001)],
    }
    legacy = mp.plot(source).hist2d("x", "y", bins=2, colorbar=False)
    output = tmp_path / "accepted.png"
    figure = legacy.save(output)
    try:
        assert float(np.asarray(_meshes(figure)[0].get_array()).sum()) == 10001
    finally:
        plt.close(figure)
    accepted = output.read_bytes()
    requested = mp.plot(source).hist2d(
        "x",
        "y",
        bins=2,
        stat="probability",
        colorbar=False,
    )
    before, history = requested.to_json(), copy.deepcopy(requested.action_log)
    figures = plt.get_fignums()
    with pytest.raises(ValueError):
        requested.save(output)
    assert output.read_bytes() == accepted
    assert requested.to_json() == before and requested.action_log == history
    assert requested.spec.data.columns == source and plt.get_fignums() == figures


def test_native_field_vertex_bound_counts_invisible_second_field_and_keeps_png(
    tmp_path,
):
    source = {
        "x": [0.25, 0.75, 1.25, 1.75],
        "y": [0.25, 1.25, 0.75, 1.75],
        "id": ["a", "b", "c", "d"],
    }
    plot = mp.plot(source).hist2d(
        "x",
        "y",
        bins=512,
        stat="count",
        colorbar=False,
        line_width=0,
    )
    output = tmp_path / "accepted.png"
    figure = plot.save(output)
    try:
        mesh = _meshes(figure)[0]
        assert np.asarray(mesh.get_coordinates()).shape == (513, 513, 2)
        assert float(np.asarray(mesh.get_array()).sum()) == 4
    finally:
        plt.close(figure)
    accepted = output.read_bytes()
    plot.hist2d(
        "x",
        "y",
        bins=512,
        stat="count",
        colorbar=False,
        line_width=0,
        line_style="--",
        alpha=0,
    )
    before, history = plot.to_json(), copy.deepcopy(plot.action_log)
    figures = plt.get_fignums()
    with pytest.raises(ValueError):
        plot.save(output)
    assert output.read_bytes() == accepted
    assert plot.to_json() == before and plot.action_log == history
    assert plot.spec.data.columns == source and plt.get_fignums() == figures


def test_grouped_joint_ecdf_guides_keep_raw_ticks_and_fit_native_backends(tmp_path):
    source = {
        "x": [0, 1, 3, 0.5, 1.5, 3],
        "y": [0, 1, 3, 0.5, 1.5, 3],
        "w": [1, 1, 1, 1, 2, 3],
        "g": ["A"] * 3 + ["B"] * 3,
    }
    plot = (
        mp.plot(source)
        .size(3.5, 2.625)
        .ecdf2d(
            "x",
            "y",
            group="g",
            weights="w",
            bounds=[[-1, 2.5], [-1, 2.5]],
            query_x=[0.75, 1.75],
            query_y=[0.75, 1.75],
            colorbar=True,
        )
    )
    before = plot.to_json()
    figure = plot.render()
    try:
        bars = [
            axis._colorbar
            for axis in figure.findobj(Axes)
            if hasattr(axis, "_colorbar")
        ]
        meshes = _meshes(figure)
        assert len(bars) == len(meshes) == 2
        assert {id(bar.mappable) for bar in bars} == {id(mesh) for mesh in meshes}
        texts = {text.get_text() for bar in bars for text in bar.ax.get_yticklabels()}
        assert "0.3333333333333333" in texts and "0.6666666666666666" in texts
        for extension in ("png", "svg"):
            figure.savefig(tmp_path / f"grouped.{extension}")
        figure.canvas.draw()
        renderer = figure.canvas.get_renderer()
        boxes = [bar.ax.get_tightbbox(renderer) for bar in bars]
        assert not boxes[0].overlaps(boxes[1])
        for box in boxes:
            assert figure.bbox.contains(box.x0, box.y0)
            assert figure.bbox.contains(box.x1, box.y1)
        assert all(
            bar.ax.yaxis.label.get_text()
            .replace("\n", " ")
            .endswith("joint CDF proportion")
            for bar in bars
        )
        assert plot.to_json() == before and plot.spec.data.columns == source
    finally:
        plt.close(figure)


def test_unfit_authored_statistic_label_rejects_without_replacing_output(tmp_path):
    source = {"x": [0, 1, 2, 3], "y": [0, 1, 2, 3], "g": ["A", "A", "B", "B"]}
    accepted = mp.plot(source).scatter("x", "y")
    output = tmp_path / "accepted.png"
    figure = accepted.save(output)
    plt.close(figure)
    original = output.read_bytes()
    label = "authored  whitespace   and " + "indivisible-label-" * 40
    candidate = (
        mp.plot(source)
        .size(3.5, 2.625)
        .hist2d(
            "x",
            "y",
            group="g",
            bins=2,
            stat="probability",
            colorbar=True,
            clabel=label,
        )
    )
    before = candidate.to_json()
    with pytest.raises(ValueError, match="statistic guide"):
        candidate.save(output)
    assert output.read_bytes() == original
    assert candidate.to_json() == before and candidate.spec.data.columns == source


def test_histogram_pdf_overlay_guides_clear_the_actual_native_title(tmp_path):
    source = {
        "x": [-2, -1, 0, 0.5, 1, 2, 3, 1.5],
        "y": [-1, 1, -0.5, 1.5, 0.25, 2, -0.5, -1],
        "w": [1, 2, 4, 1, 3, 2, 1, 2],
    }
    plot = (
        mp.plot(source)
        .layout(2, 3)
        .size(15, 9)
        .hist2d(
            "x",
            "y",
            panel=0,
            bins=mp.BivariateBinsSpec(x=[-3, 0, 1, 4], y=[-2, 0, 3]),
            stat="density",
            weights="w",
            colorbar=True,
            kde=mp.KDE2DSpec(weights="w", levels=[0.5, 0.8], gridsize=32),
        )
        .labels(title="In-bin density + full-cohort KDE", panel=0)
    )
    before = plot.to_json()
    figure = plot.render()
    try:
        owner = next(
            ax for ax in figure.axes if getattr(ax, "_mudplot_panel", None) == 0
        )
        bars = [ax._colorbar for ax in figure.findobj(Axes) if hasattr(ax, "_colorbar")]
        assert len(bars) == 2 and len({id(bar.mappable) for bar in bars}) == 2
        for extension in ("png", "svg", "pdf"):
            figure.savefig(tmp_path / f"overlay.{extension}")
        figure.canvas.draw()
        renderer = figure.canvas.get_renderer()
        title = getattr(owner, "_mudplot_title_artist", owner.title)
        with title._cm_set(text=title._get_wrapped_text()):
            title_box = title.get_window_extent(renderer)
        frames = [bar.ax.get_window_extent(renderer) for bar in bars]
        assert frames[0].x0 == pytest.approx(frames[1].x0, abs=1e-8)
        assert all(frame.y1 <= owner.get_window_extent(renderer).y1 for frame in frames)
        assert all(not frame.overlaps(title_box) for frame in frames)
        assert title.get_text() == "In-bin density + full-cohort KDE"
        assert plot.to_json() == before and plot.spec.data.columns == source
    finally:
        plt.close(figure)
