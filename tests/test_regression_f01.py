"""The glyph lens must never change R4's scientific observations."""

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import to_rgba
from matplotlib.markers import MarkerStyle


def _glyphs(ax, role):
    return [
        a
        for a in ax.collections
        if getattr(a, "_mudplot_regression_role", None) == role
    ]


def _marker(name):
    style = MarkerStyle(name)
    return style.get_path().transformed(style.get_transform()).vertices


def test_shared_wls_role_colours_do_not_change_fit_or_heldout_diagnostics():
    source = {
        "x": [1, 2, 3, 4, 5, 6],
        "y": [2, 4, 13, 8, 16, 100],
        "mass": [1, 1, 4, 1, 1, 0],
        "role": ["train"] * 4 + ["query", "query"],
        "temperature": [10, 20, None, 40, 50, 900],
        "sample_y": [None, None, None, None, 16, None],
    }
    semantic = {
        "hue": "temperature",
        "hue_kind": "numeric",
        "scale_id": "temperature",
        "legend": False,
    }
    sampling = {"train": {"role": "train"}, "query": {"role": "query"}}
    model = {
        "sampling": sampling,
        "components": {
            "fit": {"color": "#333333", "line_style": "--"},
            "scatter": {"edge_color": "#182b39", "marker_edge_width": 1.25},
        },
    }
    p = (
        mp.plot(source)
        .layout(1, 2)
        .size(10.5, 4.2)
        .secondary_yaxis("Expected response")
    )
    p.scatter("x", "sample_y", semantics=semantic)
    p.regplot(
        "x",
        "y",
        regression=model,
        weights="mass",
        semantics=semantic,
        axis="y2",
        colorbar=True,
        clabel="Temperature (°C)",
    )
    p.residplot(
        "x",
        "y",
        regression={"sampling": sampling},
        weights="mass",
        semantics=semantic,
        panel=1,
    )
    p.shared_guides([{"scale_id": "temperature", "location": "outside bottom"}])
    opened = mp.Plot.from_json(p.to_json())
    fig = opened.render()
    control = (
        mp.plot(source)
        .size(6, 4)
        .secondary_yaxis("Expected response")
        .scatter("x", "sample_y")
        .regplot("x", "y", regression=model, weights="mass", axis="y2")
        .render()
    )
    try:
        first, diag, twin = fig.axes
        assert twin.get_ylabel() == "Expected response"
        (fit,) = [
            l
            for l in twin.lines
            if getattr(l, "_mudplot_regression_role", "") == "mean_fit"
        ]
        np.testing.assert_allclose(
            fit.get_ydata(), fit.get_xdata() * 66 / 19, rtol=0, atol=2e-14
        )
        assert (fit.get_color(), fit.get_linestyle()) == ("#333333", "--")
        control_twin = control.axes[0]._mudplot_secondary_axis
        (control_fit,) = [
            line
            for line in control_twin.lines
            if getattr(line, "_mudplot_regression_role", "") == "mean_fit"
        ]
        (control_query,) = [
            line
            for line in control_twin.lines
            if getattr(line, "_mudplot_regression_role", "") == "query_mean_prediction"
        ]
        np.testing.assert_array_equal(fit.get_xdata(), control_fit.get_xdata())
        np.testing.assert_array_equal(fit.get_ydata(), control_fit.get_ydata())
        np.testing.assert_allclose(control_query.get_ydata(), [330 / 19], atol=2e-14)
        (obs,) = _glyphs(twin, "observation")
        (query,) = _glyphs(twin, "query_mean_prediction")
        (residual,) = _glyphs(diag, "diagnostic")
        assert obs._mudplot_source_rows == (0, 1, 3)
        assert query._mudplot_source_rows == residual._mudplot_source_rows == (4,)
        np.testing.assert_allclose(query.get_offsets(), [[5, 330 / 19]], atol=2e-14)
        np.testing.assert_allclose(residual.get_offsets(), [[5, -26 / 19]], atol=2e-14)
        np.testing.assert_allclose(obs.get_edgecolors(), [to_rgba("#182b39")])
        assert obs.get_linewidths()[0] == 1.25
        np.testing.assert_array_equal(
            query.get_facecolors(), first.collections[0].get_facecolors()
        )
        np.testing.assert_array_equal(residual.get_facecolors(), query.get_facecolors())
        figures_bars = [
            ax for ax in fig.findobj(Axes) if ax.get_xlabel() == "Temperature (°C)"
        ]
        (bar,) = figures_bars
        labels = [float(text.get_text()) for text in bar.get_xticklabels()]
        assert min(labels) == 10 and max(labels) == 50
        assert opened.spec.data.columns == source and opened.to_json() == p.to_json()
    finally:
        plt.close(control)
        plt.close(fig)


def test_typed_observed_markers_and_zero_size_use_native_point_area():
    raw = {
        "x": [1, 2, 3, 1, 2, 3],
        "response": [2, 4, 6, 5, 10, 15],
        "fit": [True, True, True, 1, 1, 1],
        "hue": [True, 1, True, 1, True, 1],
        "size": [0, 1, 2, 2, 1, 0],
        "mark": [True, 1, True, 1, True, 1],
    }
    semantics = {
        "hue": "hue",
        "hue_order": [True, "Reserved", 1],
        "size": "size",
        "sizes": [0, 8],
        "style": "mark",
        "style_order": [True, 1],
        "markers": ["o", "s"],
    }
    p = (
        mp.plot(raw)
        .size(8, 5)
        .regplot(
            "x",
            "response",
            group="fit",
            hue_order=[True, 1],
            semantics=semantics,
            edge_color="#243644",
        )
    )
    fig = p.render()
    try:
        (ax,) = fig.axes
        fits = [
            l
            for l in ax.lines
            if getattr(l, "_mudplot_regression_role", "") == "mean_fit"
        ]
        assert len(fits) == 2
        for fit, slope in zip(fits, [2, 5], strict=True):
            np.testing.assert_allclose(
                fit.get_ydata(), slope * fit.get_xdata(), atol=1e-14
            )
        points = {}
        for artist in _glyphs(ax, "observation"):
            for i, row in enumerate(artist._mudplot_source_rows):
                points[row] = (
                    artist.get_facecolors()[i],
                    artist.get_sizes()[i],
                    artist.get_paths()[0].vertices,
                )
        assert set(points) == set(range(len(raw["x"])))
        assert [points[i][1] for i in range(6)] == [0, 16, 64, 64, 16, 0]
        np.testing.assert_array_equal(points[0][0], points[4][0])
        assert not np.array_equal(points[0][0], points[1][0])
        np.testing.assert_array_equal(points[2][2], _marker("o"))
        np.testing.assert_array_equal(points[3][2], _marker("s"))
        labels = ax.get_legend_handles_labels()[1]
        assert any("hue=True" in label for label in labels)
        assert any("hue=1" in label for label in labels)
        assert not any("Reserved" in label or "size=0" in label for label in labels)
    finally:
        plt.close(fig)


def test_adjusted_observation_and_hidden_alpha_keep_model_and_domain_separate():
    raw = {
        "x": [1, 2, 3, 4, 5, 6],
        "z": [1, 0, 1, 0, 1, 0],
        "heat": [5, 7, 9, 11, 13, 15],
    }
    raw["y"] = [2 * x + 3 * z for x, z in zip(raw["x"], raw["z"], strict=True)]
    cfg = {"partial": {"columns": ["z"], "reference": {"z": 0}, "method": "joint"}}
    p = mp.plot(raw).layout(1, 2).size(8, 4)
    p.regplot(
        "x",
        "y",
        regression=cfg,
        semantics={"hue": "heat", "hue_kind": "numeric", "legend": False},
    )
    p.regplot(
        "x",
        "y",
        regression={**cfg, "components": {"scatter": {"alpha": 0, "color": "red"}}},
        semantics={"hue": "heat", "hue_kind": "numeric", "legend": False},
        colorbar=True,
        panel=1,
    )
    fig = p.render()
    try:
        a, b = fig.axes
        (points,) = _glyphs(a, "adjusted_observation")
        np.testing.assert_allclose(
            points.get_offsets(),
            np.column_stack((raw["x"], np.asarray(raw["x"]) * 2)),
            atol=2e-14,
        )
        assert points._mudplot_source_rows == tuple(range(6))
        assert not _glyphs(b, "adjusted_observation")
        (fit,) = [
            l
            for l in b.lines
            if getattr(l, "_mudplot_regression_role", "") == "conditional_fit"
        ]
        np.testing.assert_allclose(fit.get_ydata(), fit.get_xdata() * 2, atol=2e-14)
    finally:
        plt.close(fig)


def test_filtered_y2_date_regression_reads_raw_hue_by_original_row():
    sec = 86400
    source = {
        "clock": [0, 1, sec, 2 * sec, 2 * sec, 3 * sec],
        "value": [2, 10, 4, 20, 6, None],
        "cell": ["A", "B", "A", "B", "A", "A"],
        "use": ["train", "train", "train", "train", "train", "query"],
    }
    p = (
        mp.plot(source)
        .secondary_yaxis("Response")
        .date_axis("x", unit="s", origin="1970-01-02T00:00:00Z")
        .regplot(
            "clock",
            "value",
            axis="y2",
            regression={
                "sampling": {"train": {"use": "train"}, "query": {"use": "query"}}
            },
            semantics={
                "hue": "clock",
                "hue_kind": "numeric",
                "hue_norm": [0, 3 * sec],
                "legend": False,
            },
            colorbar=True,
        )
        .facet(col="cell", col_order=["A", "B", "Reserved"])
        .size(11, 4.2)
    )
    opened = mp.Plot.from_json(p.to_json())
    fig = opened.render()
    try:
        primary = [a for a in fig.axes if hasattr(a, "_mudplot_secondary_axis")]
        assert [panel.filters for panel in opened.spec.panels] == [
            {"cell": "A"},
            {"cell": "B"},
            {"cell": "Reserved"},
        ]
        a, b, empty = [axis._mudplot_secondary_axis for axis in primary]
        (obs,) = _glyphs(a, "observation")
        (other,) = _glyphs(b, "observation")
        (query,) = _glyphs(a, "query_mean_prediction")
        assert obs._mudplot_source_rows == (0, 2, 4)
        assert other._mudplot_source_rows == (1, 3)
        assert query._mudplot_source_rows == (5,)
        assert not empty.collections and not empty.lines
        np.testing.assert_allclose(obs.get_offsets(), [[1, 2], [2, 4], [3, 6]])
        np.testing.assert_allclose(query.get_offsets(), [[4, 8]])
        assert len(np.unique(obs.get_facecolors(), axis=0)) == 3
        cbar = next(axis for axis in fig.axes if axis.get_ylabel() == "clock")
        ticks = [float(t.get_text()) for t in cbar.get_yticklabels()]
        assert min(ticks) == 0 and max(ticks) == 3 * sec
        assert opened.spec.data.columns == source
    finally:
        plt.close(fig)


def test_deviance_glyph_maps_the_heldout_raw_row_not_fitted_probability():
    raw = {
        "x": [1, 1, 2, 2, 3],
        "y": [0, 1, 0, 1, 1],
        "use": ["train"] * 4 + ["query"],
        "style": ["training"] * 4 + [True],
    }
    p = mp.plot(raw).residplot(
        "x",
        "y",
        regression={
            "model": "logistic",
            "diagnostics": {"kind": "deviance"},
            "sampling": {"train": {"use": "train"}, "query": {"use": "query"}},
        },
        semantics={"style": "style", "style_order": [True], "markers": ["D"]},
    )
    fig = p.render()
    try:
        (point,) = _glyphs(fig.axes[0], "diagnostic")
        assert point._mudplot_source_rows == (4,)
        np.testing.assert_allclose(point.get_offsets(), [[3, np.sqrt(2 * np.log(2))]])
        np.testing.assert_array_equal(point.get_paths()[0].vertices, _marker("D"))
    finally:
        plt.close(fig)
