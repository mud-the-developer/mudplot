"""Declarative N13 geometry, identity, dimensions and transaction boundaries."""

import copy
import io
import math

import mudplot as mp
import numpy as np
import pytest
from matplotlib.gridspec import GridSpec
from mudplot import actions as A
from mudplot._editor import render_preview
from mudplot._layout_render import panel_axes, panel_legend

DATA = {"x": [1, 2, 4], "y": [3, 1, 5], "g": ["a", "a", "b"]}


def base():
    return mp.plot(DATA).line("x", "y").mosaic([["main", "blank"]])


def cell(grid, row, col, row_span=1, col_span=1):
    return mp.PanelPlacementSpec(
        cell=mp.GridCellSpec(grid, row, col, row_span, col_span)
    )


def test_mosaic_consumes_only_anonymous_and_preserves_content_and_source():
    p = mp.plot(DATA).line("x", "y").layout(1, 2).labels(title="reserved", panel=1)
    p.mosaic([["measurement", "empty", "new"], ["measurement", None, "new"]])
    assert [panel.panel_id for panel in p.spec.panels] == [
        "measurement",
        "empty",
        "new",
    ]
    assert p.spec.panels[0].layers[0].x == "x"
    assert p.spec.panels[1].title == "reserved"
    assert p.spec.panels[2].layers == []
    assert p.spec.data.columns == DATA
    before = p.to_json()
    with pytest.raises(ValueError, match="retain every existing"):
        p.mosaic([["different", "empty", "new"]])
    assert p.to_json() == before
    p.rename_panel("measurement", "different").mosaic(
        [["different", "empty", "new", "extra"]]
    )
    assert p.spec.panels[0].layers[0].x == "x"
    assert p.spec.panels[-1].layers == []


def test_identity_survives_nested_inset_reorder_reopen_undo_and_rename_refs():
    p = base().nest(2, 1).nest(1, 2)
    p.inset("main", [0.1, 0.2, 0.3, 0.4], panel_id="zoom")
    p.text("target", at=[2, 3], panel=2)
    p.inset("zoom", [0.1, 0.1, 0.4, 0.4], panel_id="detail")
    p.rename_panel("zoom", "magnified")
    assert p.spec.panels[3].placement.inset.parent == "magnified"
    old = p.to_json()
    p.reorder_panels(["detail", "blank", "magnified", "main"])
    assert p.spec.panels[2].layers[0].text == "target"
    p.store.undo()
    assert p.to_json() == old
    p.store.redo()
    reopened = mp.Plot.from_json(p.to_json())
    reopened.place(
        "magnified", {"inset": {"parent": "main", "bounds": [0.3, 0.1, 0.4, 0.5]}}
    )
    assert [panel.panel_id for panel in reopened.spec.panels] == [
        "detail",
        "blank",
        "magnified",
        "main",
    ]
    assert reopened.spec.panels[2].placement.inset.bounds == [0.3, 0.1, 0.4, 0.5]
    assert reopened.spec.data.columns == DATA


def test_complete_placement_ids_are_explicit_and_no_panel_is_dropped():
    p = base()
    layout = mp.PanelLayoutSpec([mp.LayoutGridSpec("root", 2, 2)])
    p.panel_layout(
        layout,
        {"value": cell("root", 0, 0, 2), "reserved": cell("root", 0, 1)},
        panel_ids=["value", "reserved"],
    )
    assert [x.panel_id for x in p.spec.panels] == ["value", "reserved"]
    before = p.to_json()
    with pytest.raises(ValueError, match="every existing"):
        p.panel_layout(layout, {"value": cell("root", 0, 0)})
    assert p.to_json() == before
    with pytest.raises(ValueError, match="expansion"):
        p.labels(title="unplaced", panel=2)
    assert p.to_json() == before
    p.layout(2, 2)
    assert len(p.spec.panels) == 4 and p.spec.panel_layout is None
    assert p.spec.panels[0].panel_id == "value"
    assert p.spec.panels[0].placement is None


@pytest.mark.parametrize(
    "rows",
    [
        [["main", "main"], ["main", None]],
        [["main"], ["main", "blank"]],
        [["bad id", "blank"]],
        [[True, "blank"]],
        [],
    ],
)
def test_invalid_mosaic_rejection_preserves_exact_spec(rows):
    p = base()
    before = p.to_json()
    with pytest.raises((ValueError, TypeError)):
        p.mosaic(rows)
    assert p.to_json() == before


@pytest.mark.parametrize(
    "bounds",
    [
        [-0.1, 0, 0.2, 0.2],
        [0, 0, 0, 0.2],
        [0.9, 0, 0.2, 0.2],
        [0, 0, math.inf, 0.2],
        [0, 0, math.nan, 0.2],
        [0, 0, True, 0.2],
        [0.5, 0.2, 1e-300, 0.1],
        [0, 0, 0.2],
    ],
)
def test_inset_invalid_bounds_are_atomic(bounds):
    p = base()
    before = p.to_json()
    with pytest.raises(ValueError, match="inset"):
        p.inset("main", bounds, panel_id="zoom")
    assert p.to_json() == before


def test_sibling_overlap_cycles_and_remove_references_reject_but_touching_is_valid():
    p = base().inset("main", [0.1, 0.1, 0.3, 0.3], panel_id="zoom")
    p.inset("main", [0.4, 0.1, 0.3, 0.3], panel_id="adjacent")
    before = p.to_json()
    for action in (
        A.AddInset("main", [0.2, 0.2, 0.2, 0.2], "overlap"),
        A.SetPanelPlacement(
            "main", mp.PanelPlacementSpec(inset=mp.InsetSpec("zoom", [0, 0, 1, 1]))
        ),
        A.RemovePanel("main"),
        A.RenamePanel("zoom", "main"),
        A.ReorderPanels(["main", "blank", "zoom", "zoom"]),
    ):
        with pytest.raises(ValueError):
            p.dispatch(action)
        assert p.to_json() == before
    p.remove_panel("zoom")
    assert [panel.panel_id for panel in p.spec.panels] == ["main", "blank", "adjacent"]
    assert p.spec.panels[2].placement.inset.parent == "main"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda spec: setattr(spec.panel_layout.grids[0], "rows", True),
        lambda spec: setattr(spec.panel_layout.grids[0], "width_ratios", [1, 0]),
        lambda spec: setattr(spec.panels[0].placement.cell, "grid", "missing"),
        lambda spec: setattr(spec.panels[0].placement.cell, "row_span", 3),
        lambda spec: setattr(spec.panels[1].placement.cell, "col", 0),
        lambda spec: setattr(spec.panels[1], "panel_id", "main"),
        lambda spec: setattr(spec, "layout", [1, 2]),
        lambda spec: setattr(spec.panels[0], "placement", mp.PanelPlacementSpec()),
    ],
)
def test_direct_invalid_graph_is_rejected_before_native_render(mutate):
    spec = base().spec
    mutate(spec)
    assert mp.validate(spec)
    with pytest.raises(ValueError, match="invalid FigureSpec"):
        mp.render(spec)


def test_grid_cycles_multiple_roots_and_missing_references_reject():
    p = base()
    for grids in (
        [mp.LayoutGridSpec("a", 1, 1), mp.LayoutGridSpec("b", 1, 1)],
        [
            mp.LayoutGridSpec("a", 1, 1, mp.GridCellSpec("b", 0, 0)),
            mp.LayoutGridSpec("b", 1, 1, mp.GridCellSpec("a", 0, 0)),
        ],
        [mp.LayoutGridSpec("a", 1, 1, mp.GridCellSpec("missing", 0, 0))],
        [mp.LayoutGridSpec("a", 1, 1), mp.LayoutGridSpec("a", 1, 1)],
    ):
        with pytest.raises(ValueError):
            p.panel_layout(
                mp.PanelLayoutSpec(grids),
                {"main": cell("a", 0, 0), "blank": cell("a", 0, 0)},
            )


def test_grid_spans_and_ratios_match_independent_native_subplotspec_geometry():
    p = (
        base()
        .panel_layout(
            mp.PanelLayoutSpec(
                [
                    mp.LayoutGridSpec(
                        "outer", 2, 3, width_ratios=[1, 3, 2], height_ratios=[2, 1]
                    ),
                    mp.LayoutGridSpec(
                        "inner",
                        1,
                        2,
                        mp.GridCellSpec("outer", 0, 0, 2, 2),
                        width_ratios=[4, 1],
                    ),
                ]
            ),
            {"main": cell("inner", 0, 0), "blank": cell("outer", 0, 2)},
        )
        .size(8, 4)
    )
    fig = p.render()
    reference = GridSpec(2, 3, figure=fig, width_ratios=[1, 3, 2], height_ratios=[2, 1])
    inner = reference[:, :2].subgridspec(1, 2, width_ratios=[4, 1])
    axes = panel_axes(fig)
    expected = [inner[0, 0], reference[0, 2]]
    for actual, native in zip(axes, expected, strict=True):
        assert actual.get_subplotspec().get_position(fig).bounds == pytest.approx(
            native.get_position(fig).bounds
        )
    assert axes[0].get_shared_x_axes().joined(axes[0], axes[1]) is False


@pytest.mark.parametrize("parent_projection", ["2d", "polar", "3d"])
@pytest.mark.parametrize("child_projection", ["2d", "polar", "3d"])
def test_actual_child_axes_projection_and_editor_metadata(
    parent_projection, child_projection
):
    p = mp.plot(DATA).mosaic([["main"]]).dispatch(A.SetProjection(parent_projection))
    p.inset("main", [0.15, 0.2, 0.35, 0.4], panel_id="zoom").dispatch(
        A.SetProjection(child_projection, panel=1)
    )
    p.labels(title="Child", panel=1)
    png, layouts = render_preview(p.spec)
    fig = p.render()
    axes = panel_axes(fig)
    assert axes[1] in axes[0].child_axes and axes[1] not in fig.axes
    assert (
        axes[1].name
        == {"2d": "rectilinear", "polar": "polar", "3d": "3d"}[child_projection]
    )
    assert layouts[1]["panel_id"] == "zoom"
    assert layouts[1]["panel_bbox"][2] > layouts[1]["panel_bbox"][0]
    from PIL import Image

    assert Image.open(io.BytesIO(png)).size == tuple(layouts[1]["image_size"])


def test_child_geometry_moves_with_parent_and_survives_auxiliary_axes_and_reorder():
    p = mp.plot({**DATA, "c": [0.2, 0.5, 0.8]}).scatter("x", "y", c="c", colorbar=True)
    p.mosaic([["main", "blank"]]).inset("main", [0.2, 0.3, 0.4, 0.25], panel_id="zoom")
    p.secondary_yaxis("Auxiliary", panel=2).line("x", "y", axis="y2", panel=2)
    p.text("inside", at=[2, 3], panel=2).labels(title="Inset", panel=2)
    p.reorder_panels(["zoom", "main", "blank"])
    fig = p.render()
    axes = panel_axes(fig)
    parent = axes[1]
    parent.set_position([0.15, 0.2, 0.5, 0.6])
    fig.canvas.draw()
    expected = parent.transAxes.transform([[0.2, 0.3], [0.6, 0.55]])
    assert axes[0].get_window_extent().extents == pytest.approx(
        [expected[0, 0], expected[0, 1], expected[1, 0], expected[1, 1]]
    )
    _, layouts = render_preview(p.spec)
    assert [entry["panel_id"] for entry in layouts] == ["zoom", "main", "blank"]
    assert any(
        h["kind"] == "layer-at" and h["panel"] == 0 for h in layouts[0]["handles"]
    )
    assert len(panel_axes(fig)) == 3


def test_hierarchy_sharing_uses_immediate_grid_exact_span_and_n12_ticks():
    p = (
        base()
        .panel_layout(
            mp.PanelLayoutSpec(
                [
                    mp.LayoutGridSpec("root", 2, 2),
                    mp.LayoutGridSpec(
                        "inner", 2, 1, mp.GridCellSpec("root", 0, 0, 2, 1)
                    ),
                ]
            ),
            {"main": cell("inner", 0, 0), "blank": cell("root", 0, 1)},
        )
        .share(x="row")
    )
    fig = p.render()
    a, b = panel_axes(fig)
    assert not a.get_shared_x_axes().joined(a, b)
    p.share(x="none").share_axis("x", "values", panel=0).share_axis(
        "x", "values", panel=1
    )
    p.ticks("x", {"locator": {"kind": "fixed", "values": [1, 2, 4]}})
    fig = p.render()
    a, b = panel_axes(fig)
    assert a.get_shared_x_axes().joined(a, b)
    assert list(b.get_xticks()) == [1, 2, 4]


def test_nested_pair_and_joint_keep_statistical_axes_independent_and_source_rows():
    data = {"x": [1, 2, None, 4], "y": [2, None, 5, 8]}
    for p in (mp.plot(data).pair(["x", "y"]), mp.plot(data).scatter("x", "y").joint()):
        p.nest(1, 2).nest(2, 1)
        p = mp.Plot.from_json(p.to_json())
        fig = p.render()
        axes = panel_axes(fig)
        assert p.spec.data.columns == data
        if len(axes) == 4:
            assert axes[0].get_shared_x_axes().joined(axes[0], axes[2])
            assert not axes[0].get_shared_y_axes().joined(axes[0], axes[1])
            assert axes[0].get_ylabel() == "Density"
        else:
            assert axes[0].get_shared_y_axes().joined(axes[0], axes[1])
            assert axes[0].get_shared_x_axes().joined(axes[0], axes[2])


@pytest.mark.parametrize(
    "stat", ["count", "density", "probability", "percent", "frequency"]
)
def test_observation_and_statistical_dimensions_cannot_be_shared(stat):
    p = (
        mp.plot(DATA)
        .layout(1, 2)
        .mosaic([["value", "statistic"]])
        .scatter("x", "y")
        .hist("x", stat=stat, panel=1)
        .share(y="all")
    )
    assert any("dimensions" in issue for issue in mp.validate(p.spec))


def test_mean_median_and_raw_value_axes_share_without_estimator_kind_guard():
    p = mp.plot(DATA).layout(1, 3).scatter("x", "y")
    p.pointplot("x", "y", estimator="mean", errorbar=None, native_scale=True, panel=1)
    p.pointplot("x", "y", estimator="median", errorbar=None, native_scale=True, panel=2)
    p.share(y="all").nest(1, 1)
    fig = p.render()
    axes = panel_axes(fig)
    assert all(axes[0].get_shared_y_axes().joined(axes[0], other) for other in axes[1:])


def test_extreme_finite_ratios_preserve_source_or_reject_unrepresentable_geometry():
    p = base().mosaic([["main", "blank"]], width_ratios=[1e308, 1e308])
    fig = p.render()
    assert all(ax.bbox.width > 0 for ax in panel_axes(fig))
    assert p.spec.panel_layout.grids[0].width_ratios == [1e308, 1e308]
    p.mosaic([["main", "blank"]], width_ratios=[1e-300, 1e300])
    before = p.to_json()
    with pytest.raises(ValueError, match="unrepresentable"):
        p.render()
    assert p.to_json() == before


def test_layout_resource_boundaries_and_atomic_overflow():
    p = mp.plot().mosaic([["main"]])
    for _ in range(14):
        p.nest(1, 1)
    assert mp.validate(p.spec) == []
    before = p.to_json()
    with pytest.raises(ValueError, match="depth"):
        p.nest(1, 1)
    assert p.to_json() == before
    with pytest.raises(ValueError, match="1024"):
        base().nest(1024, 1024)
    with pytest.raises(ValueError, match="256"):
        mp.FigureSpec.from_dict({"panel_layout": {"grids": [{}] * 257}})
    wide = mp.plot().mosaic([[f"p{i}" for i in range(256)]])
    assert len(wide.spec.panels) == 256
    before = wide.to_json()
    with pytest.raises(ValueError, match="256"):
        wide.inset("p0", [0, 0, 0.2, 0.2])
    assert wide.to_json() == before


def test_empty_selected_distribution_does_not_fabricate_a_mass_role():
    p = (
        mp.plot(DATA)
        .layout(1, 2)
        .mosaic([["value", "empty_statistic"]])
        .scatter("x", "y")
        .hist("x", stat="count", bins=[0, 1, 2, 3, 4, 5], panel=1)
        .share(y="all")
    )
    spec = p.spec
    spec.panels[1].filters = {"g": "reserved"}
    fig = mp.render(spec)
    axes = panel_axes(fig)
    assert axes[0].get_shared_y_axes().joined(axes[0], axes[1])
    assert len(axes[1].patches) == 0
    assert spec.data.columns == DATA


def test_named_sharing_and_figure_mode_still_reject_in_nested_layout():
    p = base().share_axis("x", "values").nest(1, 1).share(x="all")
    assert any("cannot mix figure sharing" in issue for issue in mp.validate(p.spec))
    with pytest.raises(ValueError, match="cannot mix figure sharing"):
        p.render()


def test_nested_clock_value_and_density_axes_keep_declared_units_and_rows():
    data = {"when": ["2026-10-01", "2026-10-02", "2026-10-04"], "value": [1, 3, 2]}
    p = mp.plot(data).scatter("when", "value").date_axis("x", timezone="UTC")
    p.joint().nest(1, 2).inset("panel1", [0.15, 0.2, 0.3, 0.4], panel_id="empty")
    p = mp.Plot.from_json(p.to_json())
    fig = p.render()
    axes = panel_axes(fig)
    assert axes[0].get_shared_x_axes().joined(axes[0], axes[2])
    assert not axes[1].get_shared_x_axes().joined(axes[1], axes[0])
    assert p.spec.panels[0].x.temporal == p.spec.panels[2].x.temporal
    assert p.spec.panels[1].x.temporal is None
    assert p.spec.panels[2].y.temporal is None
    assert p.spec.panels[3].layers == []
    assert p.spec.data.columns == data
    offsets = axes[0].collections[0].get_offsets()[:, 0]
    np.testing.assert_allclose(np.diff(offsets), [1, 2])


def test_complete_final_id_swap_keeps_inset_native_parent_content_undo_reopen():
    p = mp.plot(DATA).line("x", "y").mosaic([["A", "B"]])
    p.text("B content", at=[2, 2], panel=1)
    p.inset("A", [0.1, 0.2, 0.2, 0.3], panel_id="zoom")
    before = p.to_json()
    geometry = p.spec.panel_layout
    p.panel_layout(
        geometry,
        {
            "B": cell("grid1", 0, 0),
            "A": cell("grid1", 0, 1),
            "zoom": {"inset": {"parent": "A", "bounds": [0.2, 0.3, 0.25, 0.4]}},
        },
        panel_ids=["B", "A", "zoom"],
    )
    p = mp.Plot.from_json(p.to_json())
    fig = p.render()
    left, right, zoom = panel_axes(fig)
    assert len(left.lines) == 1
    assert right.texts[0].get_text() == "B content"
    assert zoom in right.child_axes and zoom not in left.child_axes
    expected = right.transAxes.transform([[0.2, 0.3], [0.45, 0.7]])
    np.testing.assert_allclose(zoom.bbox.extents, expected.ravel())
    reopened = p.to_json()
    invalid = copy.deepcopy(p.spec)
    invalid.panels[2].placement.inset.parent = "old-ID"
    with pytest.raises(ValueError, match="existing parent"):
        p.panel_layout(
            invalid.panel_layout, {v.panel_id: v.placement for v in invalid.panels}
        )
    assert p.to_json() == reopened
    history = mp.Plot.from_json(before)
    history.panel_layout(
        geometry,
        {
            "B": cell("grid1", 0, 0),
            "A": cell("grid1", 0, 1),
            "zoom": {"inset": {"parent": "A", "bounds": [0.2, 0.3, 0.25, 0.4]}},
        },
        panel_ids=["B", "A", "zoom"],
    )
    history.store.undo()
    restored = panel_axes(history.render())
    assert restored[2] in restored[0].child_axes
    assert restored[1].texts[0].get_text() == "B content"
    assert history.to_json() == before


@pytest.mark.parametrize("family", ["pair", "joint"])
def test_nested_grid_adds_real_outer_siblings_in_stable_sorted_id_order(family):
    data = {"x": [1, 2, None, 4], "y": [2, None, 5, 8]}
    initial = mp.plot(data)
    initial = (
        initial.pair(["x", "y"])
        if family == "pair"
        else initial.scatter("x", "y").joint()
    )
    initial.nest(2, 2, row_span=2, width_ratios=[3, 1])
    before = initial.to_json()
    spec = initial.spec
    root = next(g.grid_id for g in spec.panel_layout.grids if g.cell is None)
    places = {p.panel_id: p.placement.to_dict() for p in spec.panels}
    places["Zeta"] = cell(root, 1, 1).to_dict()
    places["Alpha"] = cell(root, 0, 1).to_dict()
    variants = []
    for payload in (places, dict(reversed(list(places.items())))):
        p = mp.Plot.from_json(before).panel_layout(spec.panel_layout, payload)
        n = len(spec.panels)
        p.hist("x", stat="density", panel=n)
        p.scatter("x", "y", panel=n + 1)
        f = p.render()
        axes = panel_axes(f)
        assert [panel.panel_id for panel in p.spec.panels][-2:] == ["Alpha", "Zeta"]
        assert len(axes) == n + 2 and p.spec.data.columns == data
        assert axes[n].bbox.x0 > axes[0].bbox.x0
        assert axes[n].bbox.y0 > axes[n + 1].bbox.y0
        if family == "pair":
            assert axes[0].get_shared_x_axes().joined(axes[0], axes[2])
            assert not axes[0].get_shared_y_axes().joined(axes[0], axes[1])
        else:
            assert axes[0].get_shared_x_axes().joined(axes[0], axes[2])
            assert axes[0].get_shared_y_axes().joined(axes[0], axes[1])
        assert not axes[n].get_shared_y_axes().joined(axes[n], axes[n + 1])
        variants.append((p.to_json(), [ax.get_position().bounds for ax in axes]))
        p.store.undo()
        p.store.undo()
        p.store.undo()
        assert p.to_json() == before
        p.store.redo()
        reopened = mp.Plot.from_json(p.to_json())
        assert [p.panel_id for p in reopened.spec.panels][-2:] == ["Alpha", "Zeta"]
    assert variants[0][0] == variants[1][0]
    np.testing.assert_allclose(variants[0][1], variants[1][1])


@pytest.mark.parametrize(
    "kind,axis",
    [
        ("spectrogram", "x"),
        ("spectrogram", "y"),
        ("psd", "x"),
        ("psd", "y"),
        ("magnitude", "x"),
        ("magnitude", "y"),
        ("coherence", "y"),
        ("angle", "y"),
    ],
)
def test_known_derived_spectral_units_do_not_share_unrelated_raw_value_axes(kind, axis):
    data = {"signal": [1, 2, 1, 3, 2, 4, 2, 3], "other": [2, 1, 3, 1, 4, 2, 3, 2]}
    p = mp.plot(data).mosaic([["spectral", "raw"]])
    p.spectrum(
        "signal",
        "other" if kind == "coherence" else None,
        fs=8,
        kind=kind,
        nfft=None if kind in ("magnitude", "angle") else 4,
        overlap=0,
    )
    p.scatter("signal", "other", panel=1).share(**{axis: "all"})
    assert any("dimensions" in issue for issue in mp.validate(p.spec))
    with pytest.raises(ValueError, match="dimensions"):
        p.render()


def test_compatible_phase_and_angle_radians_share_native_axis():
    data = {"signal": [1, 2, 1, 3, 2, 4, 2, 3]}
    p = mp.plot(data).layout(1, 2)
    p.spectrum("signal", fs=8, kind="angle")
    p.spectrum("signal", fs=8, kind="phase", panel=1).share(y="all").nest(1, 1)
    axes = panel_axes(p.render())
    assert axes[0].get_shared_y_axes().joined(axes[0], axes[1])


def test_inset_fractional_preview_preserves_per_target_handles_and_visible_reason():
    p = (
        mp.plot(DATA)
        .mosaic([["main"]])
        .inset("main", [0.2, 0.2, 0.6, 0.6], panel_id="zoom")
    )
    p.line("x", "y", label="primary", panel=1).text("primary", at=[2, -1], panel=1)
    p.secondary_yaxis("linear y2", panel=1).line(
        "x", "y", axis="y2", label="secondary", panel=1
    )
    p.text("secondary", at=[2, 3], axis="y2", panel=1)
    p.yscale("symlog", options={"linthresh": 1}, panel=1)
    p.labels(title="Still draggable", panel=1).size(6.013, 4.007).dispatch(
        A.SetDpi(153)
    )
    png, layouts = render_preview(p.spec)
    from PIL import Image

    assert Image.open(io.BytesIO(png)).size == (int(6.013 * 153), int(4.007 * 153))
    child = layouts[1]
    assert (
        "primary" in child["data_drag_reason"] and "symlog" in child["data_drag_reason"]
    )
    assert {h["kind"] for h in child["handles"]} >= {"title", "legend", "layer-at"}
    assert [h["layer_index"] for h in child["handles"] if h["kind"] == "layer-at"] == [
        3
    ]
    assert child["panel_id"] == "zoom"


def test_svg_stable_panel_groups_match_actual_native_inset_bounds(tmp_path):
    import re
    import xml.etree.ElementTree as ET

    p = base().inset("main", [0.2, 0.3, 0.4, 0.25], panel_id="zoom")
    p.reorder_panels(["zoom", "blank", "main"]).size(6.013, 4.007)
    path = tmp_path / "layout.svg"
    fig = p.save(str(path))
    document = ET.parse(path).getroot()
    view = [float(v) for v in document.attrib["viewBox"].split()]
    ns = {"s": "http://www.w3.org/2000/svg"}
    for axes in panel_axes(fig):
        group = document.find(
            f".//s:g[@id='mudplot-panel-{axes._mudplot_panel_id}']", ns
        )
        assert group is not None
        patch = group.find("./s:g/s:path", ns)
        assert patch is not None
        values = [
            float(v)
            for v in re.findall(
                r"[-+]?(?:\d*\.?\d+)(?:[eE][-+]?\d+)?", patch.attrib["d"]
            )
        ]
        points = np.asarray(values).reshape(-1, 2)
        extent = axes.get_window_extent().extents * 72 / fig.dpi
        expected = [extent[0], view[3] - extent[3], extent[2], view[3] - extent[1]]
        actual = [
            points[:, 0].min(),
            points[:, 1].min(),
            points[:, 0].max(),
            points[:, 1].max(),
        ]
        np.testing.assert_allclose(actual, expected, atol=2e-5, rtol=0)


@pytest.mark.parametrize("guide", ["outside bottom", "outside right", "manual left"])
def test_explicit_native_guides_insets_and_resize_keep_real_geometry(guide):
    p = (
        mp.plot(DATA)
        .line("x", "y", label="Measured response")
        .scatter("x", "y", c="y", colorbar=True, clabel="Value")
        .secondary_yaxis("Independent y2 units")
        .line("x", "y", axis="y2", label="Independent response")
        .mosaic([["main", "reserved"]])
        .size(10, 6)
        .inset("main", [0.5, 0.5, 0.3, 0.3], panel_id="zoom")
        .line("x", "y", panel=2)
        .legend(location="upper left" if guide == "manual left" else guide)
    )
    if guide == "manual left":
        p.legend(bbox_to_anchor=[0.02, 0.75])
    figure = p.render()
    axes = panel_axes(figure)
    legend = panel_legend(axes[0])
    assert legend is not None
    box = legend.get_window_extent().transformed(figure.transFigure.inverted())
    if guide == "manual left":
        assert (box.x0 + box.x1) / 2 == pytest.approx(0.02)
        assert box.x0 < axes[0].get_position().x0
    else:
        assert box.x0 >= -0.002 and box.y0 >= -0.002
        assert box.x1 <= 1.002 and box.y1 <= 1.002
    if guide == "outside bottom":
        assert axes[0].get_position().y1 > 0.9
        assert box.y1 <= axes[0].get_position().y0
    for size, dpi in [([11.013, 7.007], 100), ([9.013, 6.007], 200)]:
        figure.set_size_inches(size)
        figure.set_dpi(dpi)
        figure.canvas.draw()
        expected = axes[0].transAxes.transform([[0.5, 0.5], [0.8, 0.8]])
        np.testing.assert_allclose(axes[2].bbox.extents, expected.ravel(), atol=1e-7)
        assert all(a.bbox.width > 0 and a.bbox.height > 0 for a in axes)


def test_retained_publication_tick_title_collision_warns_without_moving_artists():
    import warnings

    from examples.panel_layouts import build_plot
    from mudplot._quality import drawn_texts

    p = build_plot().title_position(None, panel=2)
    original = p.to_json()
    with pytest.warns(UserWarning):
        figure = p.render()
    axes = panel_axes(figure)
    renderer = figure.canvas.get_renderer()
    decoration = axes[2].title.get_window_extent(renderer)
    eligible = {id(text) for text in drawn_texts(figure)}
    collisions = [
        text
        for text in axes[1].get_xticklabels()
        if id(text) in eligible
        and min(decoration.x1, text.get_window_extent(renderer).x1)
        - max(decoration.x0, text.get_window_extent(renderer).x0)
        > 1
        and min(decoration.y1, text.get_window_extent(renderer).y1)
        - max(decoration.y0, text.get_window_extent(renderer).y0)
        > 1
    ]
    assert collisions
    assert p.to_json() == original
    p.title_position([0.1, 0.8], panel=2)
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always", UserWarning)
        corrected = p.render()
    assert not [item for item in observed if issubclass(item.category, UserWarning)]
    native = panel_axes(corrected)
    title = native[2]._mudplot_title_artist
    np.testing.assert_allclose(
        title.get_transform().transform(title.get_position()),
        native[2].transAxes.transform([0.1, 0.8]),
    )
    bounds = title.get_window_extent(corrected.canvas.get_renderer())
    frame = native[2].get_window_extent()
    assert frame.x0 <= bounds.x0 < bounds.x1 <= frame.x1
    assert frame.y0 <= bounds.y0 < bounds.y1 <= frame.y1


@pytest.mark.parametrize("opt_in", ["geometry", "identities"])
def test_legacy_shared_raw_counts_render_but_new_incompatible_opt_in_is_atomic(opt_in):
    data = {"x": [1, 2, 4], "y": [2, 4, 3], "id": ["b", "a", "c"]}
    edges = [0, 1, 2, 3, 4, 5]
    p = (
        mp.plot(data)
        .layout(1, 2)
        .scatter("x", "y")
        .hist("x", stat="count", bins=edges, panel=1)
        .share(y="all")
    )
    figure = p.render()
    raw, counts = figure.axes
    assert raw.get_shared_y_axes().joined(raw, counts)
    np.testing.assert_array_equal(
        raw.collections[0].get_offsets(), [[1, 2], [2, 4], [4, 3]]
    )
    np.testing.assert_array_equal(
        [patch.get_height() for patch in counts.patches],
        np.histogram(data["x"], edges)[0],
    )
    before = p.to_json()
    with pytest.raises(ValueError, match="dimensions"):
        if opt_in == "geometry":
            p.nest(1, 1)
        else:
            p.rename_panel("panel1", "observed")
    assert p.to_json() == before
    assert p.spec.data.columns["id"] == ["b", "a", "c"]
