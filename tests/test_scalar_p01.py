"""Native scalar geometry, calibration and guide comparisons for P01."""

import matplotlib as mpl
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
from matplotlib.colors import (
    BoundaryNorm,
    LinearSegmentedColormap,
    ListedColormap,
    LogNorm,
    Normalize,
    TwoSlopeNorm,
    to_rgba,
)


def test_shared_scalar_artists_keep_raw_bad_under_over_and_local_bar_positions():
    raw = {"x": [1, 2, 3, 4, None], "y": [1, 2, 1, 2, 3], "c": [-1, 2, 12, None, 200]}
    base = {
        "colors": ["#16425b", "#f2d897"],
        "under": "#7a263a",
        "over": "#124a42",
        "bad": "#aeb7c0",
        "vmin": 0,
        "vmax": 10,
        "scale_id": "signal",
    }
    p = (
        mp.plot(raw)
        .layout(1, 2)
        .size(9, 4.4)
        .matrix("data", [[-1, 2, 12], [None, 7, 9]])
    )
    p.scatter(
        "x",
        "y",
        c="c",
        scalar_display={
            **base,
            "colorbar_options": {
                "location": "bottom",
                "ticks": [0, 2, 10],
                "extend": "both",
            },
        },
        colorbar=True,
        clabel="Row signal (mV)",
    )
    p.heatmap(
        "data",
        heatmap={"mask": [[False, False, False], [False, True, False]]},
        scalar_display={
            **base,
            "colorbar_options": {"location": "right", "ticks": [0, 7, 10]},
        },
        clabel="Cell signal (mV)",
        panel=1,
    )
    fig = mp.Plot.from_json(p.to_json()).render()
    try:
        scatter, matrix = fig.axes[:2]
        (dots,) = scatter.collections
        (img,) = matrix.images
        assert dots.norm is img.norm and dots.cmap is img.cmap
        assert dots.get_clim() == (0, 10)
        cols = LinearSegmentedColormap.from_list(
            "control", base["colors"]
        ).with_extremes(under=base["under"], over=base["over"], bad=base["bad"])
        expected = cols(
            Normalize(0, 10)(np.ma.array([-1, 2, 12, 0], mask=[0, 0, 0, 1]))
        )
        np.testing.assert_allclose(dots.get_facecolors()[:4], expected)
        np.testing.assert_allclose(img.to_rgba(img.get_array())[0], expected[:3])
        np.testing.assert_allclose(
            img.to_rgba(img.get_array())[1, :2], [to_rgba(base["bad"])] * 2
        )
        assert np.ma.getmaskarray(dots.get_offsets())[4].all()
        low = next(a for a in fig.axes if a.get_xlabel() == "Row signal (mV)")
        side = next(a for a in fig.axes if a.get_ylabel() == "Cell signal (mV)")
        assert [float(t.get_text()) for t in low.get_xticklabels()] == [0, 2, 10]
        assert [float(t.get_text()) for t in side.get_yticklabels()] == [0, 7, 10]
        assert low.get_position().y1 < scatter.get_position().y0
        assert side.get_position().x0 > matrix.get_position().x1
        patches = low._colorbar._extend_patches
        assert len(patches) == 2
        np.testing.assert_allclose(
            [a.get_facecolor() for a in patches],
            [to_rgba(base["under"]), to_rgba(base["over"])],
        )
        assert p.spec.data.columns == raw
    finally:
        plt.close(fig)


def test_log_centered_and_boundary_norm_on_actual_scalar_images_and_mesh():
    p = (
        mp.plot()
        .layout(1, 3)
        .size(11, 4)
        .matrix("log", [[0.1, 1, 10]])
        .matrix("center", [[-3, 0, 2]])
        .matrix("boundary", [[-2, 0, 3, 5]])
    )
    p.imshow(
        "log",
        grid={},
        scalar_display={"cmap": "plasma", "norm": "log", "vmin": 0.1, "vmax": 10},
    )
    p.imshow(
        "center",
        grid={},
        scalar_display={"cmap": "coolwarm", "norm": "centered", "center": 0},
        panel=1,
    )
    p.pcolormesh(
        "boundary",
        grid={
            "x": [0, 1, 2, 4, 7],
            "y": [0, 2],
            "position": "edges",
            "shading": "flat",
        },
        scalar_display={
            "colors": ["#053a50", "#d3aa67"],
            "norm": "boundary",
            "boundaries": [-1, 0, 4],
            "under": "black",
            "over": "red",
            "colorbar_options": {
                "location": "bottom",
                "ticks": [-1, 0, 4],
                "extend": "both",
            },
        },
        colorbar=True,
        clabel="Band (mV)",
        panel=2,
    )
    fig = p.render()
    try:
        log, center, mesh = fig.axes[:3]
        ln = log.images[0].norm
        cn = center.images[0].norm
        (item,) = mesh.collections
        np.testing.assert_array_equal(ln([0.1, 1, 10]), LogNorm(0.1, 10)([0.1, 1, 10]))
        np.testing.assert_array_equal(
            cn([-3, 0, 2]), TwoSlopeNorm(0, -3, 3)([-3, 0, 2])
        )
        assert (cn.vmin, cn.vmax) == (-3, 3)
        values = [-2, 0, 3, 5]
        original = ListedColormap(["#053a50", "#d3aa67"]).with_extremes(
            under="black", over="red"
        )
        np.testing.assert_allclose(
            item.get_facecolors(), original(BoundaryNorm([-1, 0, 4], 2)(values))
        )
        bar = next(a for a in fig.axes if a.get_xlabel() == "Band (mV)")
        np.testing.assert_allclose(
            [q.get_facecolor() for q in bar._colorbar._extend_patches],
            [to_rgba("black"), to_rgba("red")],
        )
        assert [float(t.get_text()) for t in bar.get_xticklabels()] == [-1, 0, 4]
        assert item.get_clim() == (-1, 4)
    finally:
        plt.close(fig)


def test_short_authored_palette_shared_semantic_offsets_and_real_legend_handlers():
    raw = {"x": [0, 1, 2, 3], "y": [2, 3, 2, 3], "g": ["a", "b", "c", "d"]}
    original = mpl.rcParams["font.size"], mpl.rcParams["axes.prop_cycle"]
    fig = (
        mp.plot(raw)
        .size(8, 4.6)
        .context("talk")
        .palette(colors=["#064c61", "#b0464d"])
        .scatter(
            "x",
            "y",
            semantics={
                "hue": "g",
                "scale_id": "swatches",
                "legend": False,
                "size": "y",
                "sizes": [4, 8],
            },
        )
        .line("x", "y", label="Measured", marker="o")
        .line("x", "y", label="Reference", marker="s", color="black")
        .legend(ncols=2, handler="line-pair")
        .labels(title="Authored swatches")
        .render()
    )
    try:
        (ax,) = fig.axes
        colours = ax.collections[0].get_facecolors()
        np.testing.assert_allclose(
            colours, [to_rgba(c) for c in ["#064c61", "#b0464d"] * 2]
        )
        np.testing.assert_array_equal(ax.collections[0].get_sizes(), [16, 64, 16, 64])
        legend = ax.get_legend()
        assert all(len(handle.get_xdata()) == 2 for handle in legend.legend_handles)
        assert ax.title.get_fontsize() > original[0]
        assert original == (mpl.rcParams["font.size"], mpl.rcParams["axes.prop_cycle"])
    finally:
        plt.close(fig)


def test_named_automatic_range_uses_actual_filtered_scatter_and_large_heatmap():
    raw = {
        "x": [1, 2, 3, 4],
        "y": [2, 3, None, 4],
        "c": [4, 8, 999, 1500],
        "cell": ["A", "A", "A", "B"],
    }
    p = (
        mp.plot(raw)
        .size(8, 4)
        .scatter("x", "y", c="c", scalar_display={"scale_id": "pooled"})
        .facet(col="cell", col_order=["A"], share_x="none", share_y="none")
    )
    p.layout(1, 2).matrix("wide", [[5] * 512 for _ in range(511)] + [[6] * 511 + [17]])
    p.heatmap("wide", scalar_display={"scale_id": "pooled"}, colorbar=False, panel=1)
    fig = p.render()
    try:
        a, b = fig.axes
        (scatter,) = a.collections
        (matrix,) = b.images
        assert scatter.norm is matrix.norm and matrix.get_array().shape == (512, 512)
        assert matrix.get_clim() == (4, 17)
    finally:
        plt.close(fig)


def test_two_slope_raw_asymmetry_and_native_scatter_pair_guide():
    p = (
        mp.plot({"x": [1, 2, 3], "y": [3, 2, 1], "c": [-2, 0, 8]})
        .size(6, 4)
        .scatter(
            "x",
            "y",
            c="c",
            label="Native samples",
            scalar_display={"norm": "two_slope", "center": 0, "vmin": -2, "vmax": 8},
        )
        .line("x", "y", label="Reference", color="black")
        .legend(ncols=2, handler="scatter-pair")
    )
    fig = p.render()
    try:
        (axis,) = fig.axes
        (points,) = axis.collections
        native = TwoSlopeNorm(0, -2, 8)
        np.testing.assert_array_equal(points.norm([-1, 0, 2]), native([-1, 0, 2]))
        np.testing.assert_allclose(
            points.get_facecolors(), mpl.colormaps["viridis"]([0.0, 0.5, 1.0])
        )
        legend = axis.get_legend()
        renderer = fig.canvas.get_renderer()
        first, second = [
            text.get_window_extent(renderer) for text in legend.get_texts()
        ]
        assert first.x1 < second.x0
        np.testing.assert_allclose(first.y0, second.y0, atol=1)
        assert len(legend.legend_handles[0].get_offsets()) == 2
    finally:
        plt.close(fig)
