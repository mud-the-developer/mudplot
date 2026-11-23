"""M01/M02: original identities, native guides and prospective rejection."""

from dataclasses import replace
from pathlib import Path

import mudplot as mp
import pytest
from mudplot import actions as A
from mudplot.spec import DataSpec, FigureSpec, LayerSpec, PanelSpec


def panel(fig, index=0):
    return next(ax for ax in fig.axes if getattr(ax, "_mudplot_panel", None) == index)


def track(name, values, first, second, *, ratio=0.04, legend=True):
    return {
        "id": name,
        "title": name,
        "values": values,
        "ratio": ratio,
        "legend": legend,
        "levels": [
            {"key": "a", "label": "Group A", "color": first},
            {"key": "b", "label": "Group B", "color": second},
        ],
    }


def cut_figure():
    return (
        mp.plot()
        .size(10, 7)
        .matrix("m", [[1, 7, None], [3, 5, 8], [2, 9, 6]])
        .clustermap(
            "m",
            clabel="Response",
            heatmap={
                "square": True,
                "norm": "symlog",
                "linthresh": 1,
                "xrotation": 25,
                "yrotation": -20,
                "xlabels": ["Third", "First", "Second"],
                "ylabels": ["Zulu", "Echo", "Alpha"],
                "annot": True,
                "annot_data": [[f"{i}:{j}" for j in range(3)] for i in range(3)],
                "mask": [[True, False, False], [False] * 3, [False] * 3],
                "colorbar_options": {"location": "bottom", "ticks": [2, 5, 9]},
            },
            cluster={
                "missing": "complete_features",
                "row_linkage": [[2, 0, 2, 2], [3, 1, 1.8, 3]],
                "col_linkage": [[1, 2, 1, 2], [3, 0, 4, 3]],
                "row_cut": {"height": 1.8, "anchor": 2},
                "col_cut": {"height": 1, "anchor": 1},
                "row_dendrogram_ratio": 0.19,
                "col_dendrogram_ratio": 0.22,
                "row_tracks": [
                    track("Site", ["a", "b", "a"], "#4060a0", "#934728", ratio=0.035),
                    track("Dose", ["b", "a", "a"], "#247b61", "#66558a", ratio=0.065),
                ],
                "col_tracks": [
                    track("Batch", ["a", "a", "b"], "#4060a0", "#247b61", legend=False)
                ],
            },
        )
    )


def test_pure_nullable_geometry_shape_and_action_round_trip():
    action = A.action_from_dict(
        {
            "type": "SetMatrix",
            "name": "m",
            "values": [[0, None, 4], [2, 5, 7], [3, 8, 6]],
        }
    )
    start = mp.reduce(FigureSpec(), action)
    mp.assert_valid(start)
    spec = (
        mp.Plot.from_json(mp.to_json(start)).clustermap(
            "m",
            cluster={
                "missing": "complete_features",
                "row_distances": {"label": "External", "values": [4, 1, 3]},
                "row_cut": {"height": 1, "anchor": 0},
            },
        )
    ).spec
    mp.assert_valid(spec)
    assert mp.from_json(mp.to_json(spec)) == spec
    later = mp.reduce(spec, A.SetMatrix("m", [[0, 1, 4], [2, 5, 7], [3, None, 6]]))
    mp.assert_valid(later)
    assert later.panels[0].layers[0].cluster.row_distances.values == [4, 1, 3]
    bad = mp.reduce(later, A.SetMatrix("m", [[0, 1, 4], [2, None, 7]]))
    with pytest.raises(ValueError):
        mp.assert_valid(bad)
    for builder in ("heatmap", "contour"):
        with pytest.raises(ValueError):
            mp.assert_valid(
                getattr(mp.Plot.from_json(mp.to_json(start)), builder)("m").spec
            )
    with pytest.raises(TypeError):
        A.action_from_dict({"type": "SetMatrix", "name": "m", "values": [[True, None]]})
    with pytest.raises(ValueError):
        mp.HeatmapSpec.from_dict({"colorbar_options": {"formatter": "g"}})


@pytest.mark.parametrize(
    "norm,opts,visible,raw,expected,locations",
    [
        (
            "symlog",
            {"linthresh": 1},
            [-100, -1, 0, 1, 100],
            [-100, -1, 0, 1, 100],
            [0, 9 / 28, 0.5, 19 / 28, 1],
            "left",
        ),
        (
            "power",
            {"gamma": 2, "vmin": 0, "vmax": 4},
            [-1, 0, 1, 2, 4, 5],
            [0, 1, 2, 4],
            [0, 1 / 16, 1 / 4, 1],
            "top",
        ),
        (
            "boundary",
            {"boundaries": [-2, 0, 3, 10]},
            [-3, -2, 0, 2, 3, 10],
            [-2, 0, 3, 10],
            [0, 1 / 3, 2 / 3, 1],
            "bottom",
        ),
    ],
)
def test_native_colorbar_ticks_and_real_colours(
    norm, opts, visible, raw, expected, locations
):
    np = pytest.importorskip("numpy")
    plt = pytest.importorskip("matplotlib.pyplot")
    p = (
        mp.plot()
        .size(8, 5)
        .matrix("m", [visible, visible])
        .heatmap(
            "m",
            clabel="Outcome",
            heatmap={
                "norm": norm,
                **opts,
                "colorbar_options": {
                    "location": locations,
                    "ticks": raw,
                    "tick_format": "g",
                    "fraction": 0.08,
                    "pad": 0.12,
                },
            },
        )
    )
    fig = p.render()
    try:
        ax = panel(fig)
        artist = ax.images[0]
        guide_ax = next(a for a in fig.axes if a is not ax)
        guide = guide_ax._colorbar
        np.testing.assert_allclose(guide.get_ticks(), expected, rtol=0, atol=2e-15)
        assert [
            t.get_text()
            for t in (
                guide_ax.get_yticklabels()
                if locations == "left"
                else guide_ax.get_xticklabels()
            )
        ] == [format(v, "g") for v in raw]
        if norm == "boundary":
            assert artist.norm(visible).tolist() == [-1, 0, 1, 1, 2, 3]
            np.testing.assert_allclose(
                guide.solids.get_facecolors(), artist.cmap([0, 1, 2]), rtol=0, atol=0
            )
        else:
            np.testing.assert_allclose(artist.norm(raw), expected, rtol=0, atol=2e-15)
        body, bar = ax.bbox, guide_ax.bbox
        if locations == "left":
            assert bar.x1 < body.x0 and bar.width / body.width == pytest.approx(0.08)
        elif locations == "top":
            assert bar.y0 > body.y1 and bar.height / body.height == pytest.approx(0.08)
        else:
            assert bar.y1 < body.y0 and bar.height / body.height == pytest.approx(0.08)
    finally:
        plt.close(fig)


def test_complete_features_is_not_pairwise_and_mask_not_input_missingness():
    np = pytest.importorskip("numpy")
    plt = pytest.importorskip("matplotlib.pyplot")
    pytest.importorskip("scipy")
    values = [[0, 2, None, 4], [0, None, 9, 7], [None, 6, 9, 4]]
    p = (
        mp.plot()
        .matrix("m", values)
        .size(8, 5)
        .clustermap(
            "m",
            colorbar=False,
            cluster={"missing": "complete_features", "col_cluster": False},
            heatmap={"mask": [[False] * 4, [False, False, False, True], [False] * 4]},
        )
    )
    fig = p.render()
    try:
        body = panel(fig)
        assert body._mudplot_cluster_order["cols"] == (0, 1, 2, 3)
        tree = next(a for a in fig.axes if a.get_ylim() == (30, 0))
        segments = tree.collections[0].get_segments()
        np.testing.assert_allclose(
            sorted(max(s[:, 0]) for s in segments), [0, 3], rtol=0, atol=0
        )
        assert body.images[0].get_clim() == (0, 9)
        np.testing.assert_equal(p.spec.data.matrices["m"], values)
    finally:
        plt.close(fig)
    both = mp.Plot.from_json(p.to_json())
    layer = both.spec.panels[0].layers[0]
    both.dispatch(
        A.ReplaceLayer(
            0, replace(layer, cluster=replace(layer.cluster, col_cluster=True))
        )
    )
    with pytest.raises(ValueError):
        both.render()
    corr = mp.Plot.from_json(p.to_json())
    corr.dispatch(
        A.ReplaceLayer(
            0, replace(layer, cluster=replace(layer.cluster, metric="correlation"))
        )
    )
    with pytest.raises(ValueError):
        corr.render()


def test_native_selected_bands_tracks_and_original_preview_ids():
    np = pytest.importorskip("numpy")
    plt = pytest.importorskip("matplotlib.pyplot")
    pytest.importorskip("scipy")
    from matplotlib.collections import LineCollection
    from matplotlib.colors import to_hex
    from matplotlib.legend import Legend
    from matplotlib.lines import Line2D
    from mudplot._editor import extract_layout

    spec = mp.from_json(cut_figure().to_json())
    fig = mp.render(spec)
    try:
        ax = panel(fig)
        assert ax._mudplot_cluster_order == {"rows": (2, 0, 1), "cols": (1, 2, 0)}
        assert [t.get_text() for t in ax.texts] == [
            "2:1",
            "2:2",
            "2:0",
            "0:1",
            "1:1",
            "1:2",
            "1:0",
        ]
        metadata = extract_layout(spec, fig, 0)["matrix_cuts"]
        assert metadata["row"]["partition"]["inverted"]
        assert metadata["row"]["partition"]["selected"] == [2]
        assert metadata["col"]["partition"]["selected"] == [1, 2]
        assert [item["label"] for item in metadata["row"]["items"]] == [
            "Zulu",
            "Echo",
            "Alpha",
        ]
        for name, coord, expected in (("row", 1, [2]), ("col", 0, [1, 2])):
            tree = next(
                a
                for a in fig.axes
                if (a.get_ylim() == (30, 0) if coord else a.get_xlim() == (0, 30))
            )
            artist = max(tree.collections, key=lambda c: c.get_linewidths()[0])
            limits = sorted(
                artist.get_transform().transform(artist.get_segments()[0])[:, coord]
            )
            centers = ax.transData.transform([(i, i) for i in range(3)])[:, coord]
            ids = ax._mudplot_cluster_order["rows" if name == "row" else "cols"]
            assert [
                ids[i] for i, v in enumerate(centers) if limits[0] < v < limits[1]
            ] == expected
        lane = next(a for a in fig.axes if len(a.images) == 2)
        assert lane.bbox.width / ax.bbox.width == pytest.approx(0.1)
        assert [to_hex(v / 255) for v in lane.images[0].get_array()[:, 0]] == [
            "#4060a0",
            "#4060a0",
            "#934728",
        ]
        legends = [
            c for a in fig.axes for c in a.get_children() if isinstance(c, Legend)
        ]
        assert [l.get_title().get_text() for l in legends] == ["Site", "Dose", ""]
        assert isinstance(legends[-1].legend_handles[0], Line2D)
        missing_marks = [c for c in ax.collections if isinstance(c, LineCollection)]
        assert len(missing_marks) == 1
        segments = missing_marks[0].get_segments()
        assert len(segments) == 1
        np.testing.assert_equal(segments[0].mean(axis=0), [1, 1])
        assert (
            segments[0][1, 0] > segments[0][0, 0]
            and segments[0][1, 1] < segments[0][0, 1]
        )
    finally:
        plt.close(fig)


def test_work_and_managed_admission_before_effects(monkeypatch):
    plt = pytest.importorskip("matplotlib.pyplot")
    scipy = pytest.importorskip("scipy.cluster.hierarchy")

    def unexpected(*_a, **_kw):
        pytest.fail("over-budget request entered effects")

    monkeypatch.setattr(plt, "figure", unexpected)
    monkeypatch.setattr(scipy, "linkage", unexpected)
    matrix = [[0.0] * 512] * 512
    layer = LayerSpec(
        type="clustermap",
        matrix="m",
        cluster=mp.ClusterSpec(
            missing="complete_features",
            optimal_ordering=True,
        ),
    )
    one = FigureSpec(
        data=DataSpec(matrices={"m": matrix}), panels=[PanelSpec(layers=[layer])]
    )
    with pytest.raises(ValueError, match="work credits"):
        mp.render(replace(one, panels=one.panels * 3))
    palettes = [track(str(i), ["a"] * 512, "#4060a0", "#934728") for i in range(300)]
    many = replace(
        layer,
        cluster=mp.ClusterSpec.from_dict(
            {"row_tracks": palettes, "row_cluster": False, "col_cluster": False}
        ),
    )
    with pytest.raises(ValueError, match="managed reservation"):
        mp.render(replace(one, panels=[PanelSpec(layers=[many])] * 4))


def test_legacy_01_document_reopens_with_native_text_and_raw_data():
    plt = pytest.importorskip("matplotlib.pyplot")
    path = (
        Path(__file__).resolve().parents[1] / "docs/images/heatmap_controls.mplot.json"
    )
    spec = mp.from_json(path.read_text(encoding="utf-8"))
    reopened = mp.from_json(mp.to_json(spec))
    fig = mp.render(reopened)
    try:
        ax = panel(fig)
        assert [t.get_text() for t in ax.get_xticklabels()] == list(
            spec.panels[0].layers[0].heatmap.xlabels
        )
        assert (
            reopened.version == "0.1" and reopened.data.matrices == spec.data.matrices
        )
        assert ax.images[0].get_array().mask.any()
        assert len(ax.texts) == ax.images[0].get_array().count()
    finally:
        plt.close(fig)


def test_unrepresentable_positive_linkage_height_rejects_editor_transaction():
    from math import ulp

    pytest.importorskip("matplotlib.pyplot")
    pytest.importorskip("scipy")
    from dashboard.editor_server import EditorSession

    plot = (
        mp.plot()
        .size(8, 6)
        .matrix("m", [[1, 2], [3, 4], [5, 6]])
        .clustermap(
            "m",
            colorbar=False,
            cluster={
                "col_cluster": False,
                "row_distances": {"label": "Provided", "values": [0, 1, 1]},
                "row_cut": {"height": 0, "anchor": 0},
            },
        )
    )
    session = EditorSession()
    session.load_spec(plot.to_json())
    old = session.store.state
    preview = session.png
    history = session.store.history
    cut = session.layout["matrix_cuts"]["row"]["partition"]
    assert cut["selected"] == [0, 1]
    # First linkage is exactly zero, second equals half the least positive float.
    layer = old.panels[0].layers[0]
    candidate = A.ReplaceLayer(
        0,
        replace(
            layer,
            cluster=replace(
                layer.cluster,
                row_distances=mp.CondensedDistanceSpec("Provided", [0, ulp(0.0), 0]),
            ),
        ),
    )
    prospective = mp.reduce(old, candidate)
    mp.assert_valid(prospective)
    session.dispatch_safe(candidate)
    assert session.error
    assert (
        session.store.state == old
        and session.png == preview
        and session.store.history == history
    )
    assert session.layout["matrix_cuts"]["row"]["partition"] == cut


def test_nested_named_matrix_colorbars_and_bottom_legends_clear_real_labels():
    plt = pytest.importorskip("matplotlib.pyplot")
    pytest.importorskip("scipy")
    from examples.matrix_workflow import build_plot
    from matplotlib.legend import Legend

    plot = (
        build_plot()
        .mosaic([["heat", "cluster"]], width_ratios=[1, 1.8])
        .nest(1, 1)
        .size(13, 7)
    )
    layer = plot.spec.panels[1].layers[0]
    plot.dispatch(
        A.ReplaceLayer(
            0,
            replace(layer, cluster=replace(layer.cluster, track_legend_side="bottom")),
            1,
        )
    )
    fig = plot.render()
    try:
        a, b = panel(fig, 0), panel(fig, 1)
        assert [a._mudplot_panel_id, b._mudplot_panel_id] == ["heat", "cluster"]
        assert {t.get_rotation() for t in a.get_xticklabels()} == {28}
        assert [t.get_text() for t in b.get_xticklabels()] == ["Q1", "Q3", "Q2", "Q4"]
        assert [t.get_text() for t in b.get_yticklabels()] == [
            "Zulu",
            "Echo",
            "Alpha",
            "Beta",
        ]
        assert b._mudplot_matrix_cuts["row"]["selected"] == [0, 1]
        renderer = fig.canvas.get_renderer()
        bars = [ax for ax in fig.axes if getattr(ax, "_colorbar", None) is not None]
        assert len(bars) == 2
        for body, guide in zip((a, b), bars, strict=True):
            assert (
                guide.get_tightbbox(renderer).y1 < body.xaxis.get_tightbbox(renderer).y0
            )
        legends = [
            artist
            for ax in fig.axes
            for artist in ax.get_children()
            if isinstance(artist, Legend)
        ]
        assert len(legends) == 3 and {l.get_title().get_text() for l in legends} >= {
            "Site",
            "Design",
        }
        assert all(
            0
            < l.get_window_extent(renderer).y0
            < l.get_window_extent(renderer).y1
            < bars[1].get_tightbbox(renderer).y0
            for l in legends
        )
    finally:
        plt.close(fig)


def test_nested_matrix_and_adjacent_root_guide_keep_distinct_owners():
    np = pytest.importorskip("numpy")
    plt = pytest.importorskip("matplotlib.pyplot")
    from matplotlib.axes import Axes

    source = {"x": [1, 2, 3], "y": [8, 3, 6], "score": [1, 4, 9]}
    plot = (
        mp.plot(source)
        .size(12, 7)
        .mosaic([["matrix", "observations"]])
        .nest(1, 1)
        .matrix("m", [[1, 3, 6], [2, 4, 9]])
        .heatmap(
            "m",
            clabel="Matrix response",
            heatmap={
                "norm": "power",
                "gamma": 2,
                "xrotation": 25,
                "xlabels": ["Before treatment", "Recovery", "Follow-up"],
                "colorbar_options": {
                    "location": "bottom",
                    "ticks": [1, 4, 9],
                    "tick_format": "g",
                },
            },
        )
        .labels(title="Measured matrix", panel=0)
        .scatter(
            "x",
            "y",
            panel=1,
            clabel="Continuous score",
            colorbar=True,
            semantics=mp.SemanticSpec(
                hue="score", hue_kind="numeric", scale_id="root-score"
            ),
        )
        .labels(title="Original observations", panel=1)
        .shared_guides(
            [mp.SharedGuideSpec(scale_id="root-score", location="outside top")]
        )
    )
    fig = plot.render()
    try:
        r = fig.canvas.get_renderer()
        a, b = panel(fig, 0), panel(fig, 1)
        assert [a._mudplot_panel_id, b._mudplot_panel_id] == ["matrix", "observations"]
        np.testing.assert_array_equal(
            b.collections[0].get_offsets(), [[1, 8], [2, 3], [3, 6]]
        )
        bars = [ax for ax in fig.findobj(Axes) if hasattr(ax, "_colorbar")]
        local = next(
            ax for ax in bars if getattr(ax, "_mudplot_matrix_panel", None) is a
        )
        root = next(
            ax
            for ax in bars
            if getattr(ax, "_mudplot_shared_guide_scale_id", None) == "root-score"
        )
        assert len(bars) == 2 and root.xaxis.label.get_text() == "Continuous score"
        assert local.get_tightbbox(r).y1 < a.xaxis.get_tightbbox(r).y0
        assert all(
            root.get_tightbbox(r).y0 > max(ax.bbox.y1, ax.title.get_window_extent(r).y1)
            for ax in (a, b)
        )
        assert (
            local.get_tightbbox(r).x1 < b.bbox.x0 and plot.spec.data.columns == source
        )
    finally:
        plt.close(fig)
