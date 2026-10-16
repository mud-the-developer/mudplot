"""Materialized facets: row selection precedes inference and appearance mapping."""

from __future__ import annotations

import copy
import json
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import LineCollection, PathCollection
from matplotlib.patches import Rectangle
from mudplot import actions as A
from mudplot._estimate import summarize
from mudplot._facet import panel_columns, panel_rows
from mudplot._semantics import shared_scale_domains
from mudplot.spec import PanelSpec


def data():
    columns = {name: [] for name in ("x", "y", "row", "col", "h", "m", "w")}
    for r, row in enumerate(("North", "South")):
        for c, col in enumerate(("low", "high")):
            for g, hue in enumerate(("B", "A")):
                for x in (1, 2):
                    values = (
                        x,
                        10 * r + 3 * c + g + x,
                        row,
                        col,
                        hue,
                        100 * r + 10 * c + x,
                        x,
                    )
                    for name, value in zip(columns, values, strict=True):
                        columns[name].append(value)
    return columns


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def test_facet_grid_copies_one_template_and_preserves_inputs_and_metadata():
    p = (
        mp.plot(data())
        .lineplot("x", "y", group="h", errorbar=None)
        .labels(title="Signal")
    )
    p.title_reference(citation="trial", href="https://example.org/trial")
    p.dispatch(A.SetPanelLabel("custom"))
    source = p.spec
    original = copy.deepcopy(source)
    p.facet(
        row="row", col="col", row_order=["South", "North"], col_order=["high", "low"]
    )
    assert source == original and p.spec.data == original.data
    assert p.spec.layout == [2, 2]
    assert p.spec.share_x == p.spec.share_y == "all"
    assert [panel.filters for panel in p.spec.panels] == [
        {"row": row, "col": col}
        for row in ("South", "North")
        for col in ("high", "low")
    ]
    assert all(panel.title.endswith("\nSignal") for panel in p.spec.panels)
    assert all(
        panel.title_citation == "trial" and panel.label == "custom"
        for panel in p.spec.panels
    )
    assert all(panel.layers[0].hue_order == ["B", "A"] for panel in p.spec.panels)
    spec = p.spec
    order = spec.panels[0].layers[0].hue_order
    assert order is not None
    order.append("local")
    assert spec.panels[1].layers[0].hue_order == ["B", "A"]
    assert mp.validate(p.spec) == []


@pytest.mark.parametrize("axis", ["row", "col"])
def test_single_dimension_first_seen_levels_and_free_axes(axis):
    p = (
        mp.plot(data())
        .scatter("x", "y")
        .facet(**{axis: axis}, share_x="none", share_y="none")
    )
    assert p.spec.layout == ([2, 1] if axis == "row" else [1, 2])
    assert len(p.render().axes) == 2
    assert p.spec.share_x == p.spec.share_y == "none"


def test_wrapping_reserves_empty_cells_and_does_not_add_a_padding_panel():
    p = (
        mp.plot(data())
        .scatter("x", "y")
        .facet(col="col", col_order=["empty", "high", "low"], col_wrap=2)
    )
    assert p.spec.layout == [2, 2] and len(p.spec.panels) == 3
    axes = p.render().axes
    assert len(axes) == 3 and not axes[0].collections
    assert all(
        np.asarray(ax.collections[0].get_offsets()).shape[0] == 8 for ax in axes[1:]
    )


def test_boolean_and_numeric_facet_keys_do_not_collapse():
    p = (
        mp.plot({"x": [1, 2], "y": [3, 4], "f": [True, 1]})
        .scatter("x", "y")
        .facet(col="f")
    )
    assert [panel_rows(p.spec.data.columns, panel) for panel in p.spec.panels] == [
        [0],
        [1],
    ]
    assert len(p.render().axes) == 2


def test_missing_facet_keys_are_dropped_without_modifying_source_data():
    raw = {"x": [1, 2, 3], "y": [3, 4, 5], "f": ["A", None, "B"]}
    p = mp.plot(raw).scatter("x", "y").facet(col="f")
    assert p.spec.data.columns == raw
    assert [panel_rows(p.spec.data.columns, panel) for panel in p.spec.panels] == [
        [0],
        [2],
    ]


def test_selection_precedes_log_validation_and_data_refresh_keeps_explicit_cells():
    p = mp.plot({"x": [1, -2], "y": [1, 2], "f": ["A", "B"]}).scatter("x", "y")
    p.facet(col="f", col_order=["A"]).xscale("log")
    assert mp.validate(p.spec) == []
    p.dispatch(A.SetData({"x": [3, -4, 5], "y": [6, 7, 8], "f": ["A", "B", "new"]}))
    assert len(p.spec.panels) == 1
    np.testing.assert_array_equal(
        p.render().axes[0].collections[0].get_offsets(), [[3, 6]]
    )


def test_group_colours_and_numeric_semantic_domains_use_original_selected_row_ids():
    p = mp.plot(data()).scatter("x", "y", hue="h", size="m", style="h")
    p.facet(col="col", col_order=["high", "low"])
    config = p.spec.panels[0].layers[0].semantics
    assert config is not None and config.scale_id is not None
    scale = config.scale_id
    for panel in p.spec.panels:
        member = panel.layers[0].semantics
        assert member is not None and member.scale_id == scale
    domain = shared_scale_domains(p.spec)[scale]
    assert domain["rows"] == list(range(16))
    axes = p.render().axes
    colours = []
    for panel, ax in zip(p.spec.panels, axes, strict=True):
        selected = panel_columns(p.spec.data.columns, panel)
        rows = len(selected["x"])
        collections = [c for c in ax.collections if isinstance(c, PathCollection)]
        assert sum(np.asarray(c.get_offsets()).shape[0] for c in collections) == rows
        colours.append([np.asarray(c.get_facecolor())[0] for c in collections])
    np.testing.assert_allclose(colours[0], colours[1])
    sizes = [
        size
        for ax in axes
        for collection in ax.collections
        if isinstance(collection, PathCollection)
        for size in collection.get_sizes()
    ]
    assert min(sizes) == pytest.approx(config.sizes[0] ** 2)
    assert max(sizes) == pytest.approx(config.sizes[1] ** 2)


def test_selected_semantic_pool_excludes_deselected_facets_and_deduplicates_layers():
    config = mp.SemanticSpec(hue="h", size="m", scale_id="study")
    p = mp.plot(data()).scatter("x", "y", semantics=config)
    p.scatter("x", "y", semantics=config)
    p.facet(col="col", col_order=["high"])
    expected = [i for i, value in enumerate(data()["col"]) if value == "high"]
    assert shared_scale_domains(p.spec)["study"]["rows"] == expected
    p.render()


def test_semantic_lineplot_uses_cell_data_with_global_mapping_rows():
    p = mp.plot(data()).lineplot("x", "y", hue="h", size="m", style="h", errorbar=None)
    p.legend(False).facet(row="row", col="col").size(8, 6)
    assert mp.validate(p.spec) == []
    for ax in p.render().axes:
        strokes = [line for line in ax.lines if np.asarray(line.get_xdata()).size]
        assert (
            strokes and sum(np.asarray(line.get_xdata()).size for line in strokes) == 4
        )


def test_reserved_only_semantic_facets_do_not_normalize_an_empty_numeric_domain():
    p = mp.plot(data()).scatter(
        "x", "y", semantics=mp.SemanticSpec(hue="m", hue_kind="numeric", size="m")
    )
    p.facet(col="col", col_order=["absent"])
    assert not p.render().axes[0].collections


def test_statistical_estimates_are_computed_within_each_cell():
    p = mp.plot(data()).barplot("h", "y", group="h", errorbar=None)
    p.facet(row="row", col="col")
    assert all(panel.layers[0].order == ["B", "A"] for panel in p.spec.panels)
    for panel, ax in zip(p.spec.panels, p.render().axes, strict=True):
        cols = panel_columns(p.spec.data.columns, panel)
        expected = [
            np.mean(
                [v for v, h in zip(cols["y"], cols["h"], strict=True) if h == group]
            )
            for group in ("B", "A")
        ]
        bars = [bar for bar in ax.patches if isinstance(bar, Rectangle)]
        assert len(bars) == len(ax.patches)
        np.testing.assert_allclose([bar.get_height() for bar in bars], expected)


def test_weighted_ci_intervals_use_cell_rows_and_the_declared_seed():
    p = (
        mp.plot(data())
        .barplot(
            "h", "y", group="h", weights="w", errorbar=("ci", 90), n_boot=39, seed=7
        )
        .facet(row="row", col="col")
    )
    for panel, ax in zip(p.spec.panels, p.render().axes, strict=True):
        expected = summarize(panel_columns(p.spec.data.columns, panel), panel.layers[0])
        bounds = []
        for estimate in expected.estimates:
            assert estimate.lower is not None and estimate.upper is not None
            bounds.append([estimate.lower, estimate.upper])
        segments = [
            np.asarray(segment)[:, 1].tolist()
            for collection in ax.collections
            if isinstance(collection, LineCollection)
            for segment in collection.get_segments()
        ]
        np.testing.assert_allclose(sorted(segments), sorted(bounds))


@pytest.mark.parametrize("method", ["box", "violin", "boxenplot", "swarmplot", "ecdf"])
def test_distribution_and_categorical_builders_use_filtered_rows(method):
    p = mp.plot(data())
    if method in ("box", "violin", "boxenplot"):
        getattr(p, method)("h", "y", group="h")
    elif method == "swarmplot":
        p.swarmplot("h", "y", group="h")
    else:
        p.ecdf("y", group="h")
    p.facet(col="col")
    assert mp.validate(p.spec) == []
    assert len(p.render().axes) == 2


@pytest.mark.parametrize(
    "options",
    [
        {},
        {"col": "missing"},
        {"row": "row", "col": "row"},
        {"col": "col", "col_wrap": True},
        {"col": "col", "col_wrap": 0},
        {"row": "row", "col_wrap": 2},
        {"row_order": ["North"], "col": "col"},
        {"col": "col", "col_order": []},
        {"col": "col", "col_order": 3},
        {"col": "col", "col_order": ["low", "low"]},
        {"col": "col", "col_order": [1, "1"]},
        {"col": "col", "share_x": "bad"},
        {"col": "col", "col_order": list(range(65))},
        {
            "row": "row",
            "col": "col",
            "row_order": list(range(9)),
            "col_order": list(range(8)),
        },
    ],
)
def test_invalid_facet_requests_do_not_mutate_the_plot_or_history(options):
    p = mp.plot(data()).scatter("x", "y")
    before, history = p.to_json(), p.action_log
    with pytest.raises(ValueError):
        p.facet(**options)
    assert p.to_json() == before and p.action_log == history


@pytest.mark.parametrize(
    "kind",
    [
        "legacy_c",
        "legacy_hist",
        "auto_hist",
        "legacy_kde",
        "matrix",
        "polar",
        "empty",
        "multiple",
    ],
)
def test_unsupported_faceting_fails_instead_of_silently_ignoring_options(kind):
    p = mp.plot(data())
    if kind == "legacy_c":
        p.scatter("x", "y", c="m", colorbar=True)
    elif kind == "legacy_hist":
        p.hist("x")
    elif kind == "auto_hist":
        p.hist("x", stat="count")
    elif kind == "legacy_kde":
        p.kde("x")
    elif kind == "matrix":
        p.matrix("m", [[1, 2], [3, 4]]).heatmap("m")
    elif kind in ("polar", "multiple"):
        p.line("x", "y")
        p.projection_polar() if kind == "polar" else p.layout(1, 2)
    with pytest.raises(ValueError):
        p.facet(col="col")


@pytest.mark.parametrize("extension", ["png", "pdf", "svg"])
def test_facets_roundtrip_actions_reproduce_exports_and_leave_global_rng_untouched(
    tmp_path, extension
):
    state = np.random.get_state()
    p = (
        mp.plot(data())
        .lineplot("x", "y", group="h", errorbar=None)
        .facet(col="col")
        .size(8, 3)
    )
    assert mp.apply(p.action_log) == mp.Plot.from_json(p.to_json()).spec == p.spec
    paths = [tmp_path / f"{name}.{extension}" for name in ("a", "b")]
    plt.close(p.save(str(paths[0])))
    plt.close(mp.Plot.from_json(p.to_json()).save(str(paths[1])))
    assert paths[0].read_bytes() == paths[1].read_bytes()
    after = np.random.get_state()
    assert state[0] == after[0] and state[2:] == after[2:]
    np.testing.assert_array_equal(state[1], after[1])


def test_facet_core_works_without_render_dependencies():
    script = (
        "import sys; import mudplot as m; "
        "p=m.plot({'x':[1,2],'y':[3,4],'f':['A','B']}).scatter('x','y'); "
        "p.facet(col='f'); "
        "assert m.validate(p.spec)==[]; assert m.apply(p.action_log)==p.spec; "
        "assert m.Plot.from_json(p.to_json()).spec==p.spec; "
        "assert 'numpy' not in sys.modules and 'matplotlib' not in sys.modules"
    )
    subprocess.run([sys.executable, "-S", "-c", script], check=True)


def test_facet_histograms_share_explicit_edges_and_normalize_per_cell():
    p = (
        mp.plot(data())
        .hist("x", bins=[0, 1.5, 3], stat="probability", weights="w", group="h")
        .facet(row="row", col="col")
    )
    for ax in p.render().axes:
        bars = [patch for patch in ax.patches if isinstance(patch, Rectangle)]
        np.testing.assert_allclose(
            [bar.get_height() for bar in bars], [1 / 6, 2 / 6] * 2
        )


def test_faceted_typed_kde_fits_the_cell_not_the_entire_table():
    p = (
        mp.plot(data())
        .kde("y", group="h", bw_method="scott", gridsize=31, cut=0)
        .facet(row="row", col="col", share_x="none", share_y="none")
    )
    for panel, ax in zip(p.spec.panels, p.render().axes, strict=True):
        values = panel_columns(p.spec.data.columns, panel)["y"]
        support = np.concatenate([np.asarray(line.get_xdata()) for line in ax.lines])
        assert support.min() >= min(values) and support.max() <= max(values)


def test_faceted_bivariate_kde_uses_local_covariance_and_support():
    raw = {
        "x": [1, 2, 3, 4, 5] * 2,
        "y": [2, 5, 3, 6, 4, 22, 25, 23, 26, 24],
        "f": ["A"] * 5 + ["B"] * 5,
    }
    p = (
        mp.plot(raw)
        .kde2d("x", "y", gridsize=31, levels=[0.5])
        .facet(col="f", share_y="none")
    )
    a, b = p.render().axes
    np.testing.assert_allclose(np.asarray(b.get_ylim()) - a.get_ylim(), [20, 20])


def test_facet_actions_schema_and_editor_import_are_consistent():
    import jsonschema
    from dashboard.editor_server import EditorSession

    p = mp.plot(data()).scatter("x", "y").facet(col="col")
    jsonschema.validate(p.spec.to_dict(), mp.json_schema())
    assert mp.capabilities()["facets"]["action"] == "SetFacets"
    session = EditorSession()
    session.load_spec(p.to_json())
    assert session.store.state == p.spec and session.png.startswith(b"\x89PNG")
    session.select_panel(1)
    session.dispatch_safe(A.SetTitle("Edited cell", panel=1))
    assert (
        session.error is None and session.store.state.panels[1].title == "Edited cell"
    )
    assert session.store.state.panels[0].filters == p.spec.panels[0].filters
    assert b"<svg" in session.export("svg")


def test_facet_action_is_available_in_editor_raw_action_dispatch():
    from dashboard.editor_server import EditorSession

    session = EditorSession()
    session.load_spec(mp.plot(data()).scatter("x", "y").to_json())
    session.dispatch_safe(A.action_from_dict({"type": "SetFacets", "col": "col"}))
    assert session.error is None and len(session.store.state.panels) == 2


def test_lint_uses_pooled_semantic_palette_not_isolated_cell_domains():
    p = mp.plot({"x": [1, 2], "y": [3, 4], "f": ["N", "S"], "h": ["A", "B"]})
    p.scatter("x", "y", hue="h", style="h").facet(col="f")
    assert any("2 series" in issue.message for issue in p.lint())


def test_manual_filters_and_old_spec_defaults():
    p = mp.plot(data()).scatter("x", "y")
    old = p.spec.to_dict()
    del old["panels"][0]["filters"]
    assert mp.FigureSpec.from_dict(old) == p.spec
    for filters in (
        {"absent": "A"},
        {"col": None},
        {"col": []},
        {"col": "high", "row": "North", "h": "A"},
    ):
        bad = p.spec
        bad.panels[0].filters = filters
        assert mp.validate(bad)
    assert PanelSpec().filters == {}
    action = A.SetFacets(col="col")
    assert (
        A.action_from_dict(json.loads(json.dumps(A.action_to_dict(action)))) == action
    )
