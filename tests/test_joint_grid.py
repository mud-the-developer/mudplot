"""Joint composition uses one complete-case cohort without altering source rows."""

from __future__ import annotations

import copy
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import PathCollection
from matplotlib.patches import Rectangle
from mudplot import actions as A
from mudplot._facet import panel_columns, panel_rows


def data():
    return {
        "x": [1, 2, None, 4, 6, 7, 8],
        "y": [2, 4, 5, None, 7, 8, 9],
        "h": ["B", "A", "B", "A", None, "A", "B"],
        "unused": [None] * 7,
    }


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.mark.parametrize("grouped", [False, True])
def test_joint_uses_identical_paired_rows_in_all_views_and_preserves_original(grouped):
    p = mp.plot(data()).scatter("x", "y", group="h" if grouped else None)
    before = p.spec
    p.labels(x="Input (u)", y="Output (u)", title="Joint question")
    p.joint(bins=3, marginal_stat="count").size(7, 6)
    spec = p.spec
    assert spec.data == before.data and spec.layout == [2, 2]
    assert len(spec.panels) == 3
    expected = [0, 1, 5, 6] if grouped else [0, 1, 4, 5, 6]
    assert [panel_rows(spec.data.columns, panel) for panel in spec.panels] == [
        expected
    ] * 3
    assert spec.panels[0].title == "Joint question"
    assert (
        spec.panels[2].x.label == "Input (u)" and spec.panels[0].y.label == "Output (u)"
    )
    assert spec.panels[0].x.label == spec.panels[1].y.label == ""
    if grouped:
        assert all(panel.layers[0].hue_order == ["B", "A"] for panel in spec.panels)
    axes = p.render().axes
    assert len(axes) == 3
    assert axes[0].get_shared_x_axes().joined(axes[0], axes[2])
    assert axes[0].get_shared_y_axes().joined(axes[0], axes[1])
    assert not axes[0].get_shared_x_axes().joined(axes[0], axes[1])
    assert not axes[0].get_shared_y_axes().joined(axes[0], axes[2])
    assert sum(
        np.asarray(c.get_offsets()).shape[0]
        for c in axes[0].collections
        if isinstance(c, PathCollection)
    ) == len(expected)
    assert sum(
        patch.get_width() for patch in axes[1].patches if isinstance(patch, Rectangle)
    ) == len(expected)
    assert sum(
        patch.get_height() for patch in axes[2].patches if isinstance(patch, Rectangle)
    ) == len(expected)


@pytest.mark.parametrize(
    "stat,total", [("density", 1), ("probability", 1), ("percent", 100), ("count", 4)]
)
def test_joint_marginal_statistics_are_normalized_in_the_paired_cohort(stat, total):
    p = (
        mp.plot(data())
        .scatter("x", "y", group="h")
        .joint(bins=2, marginal_stat=stat)
        .size(7, 6)
    )
    _, y_axis, x_axis = p.render().axes
    for axis in (y_axis, x_axis):
        bars = [patch for patch in axis.patches if isinstance(patch, Rectangle)]
        values = (
            [patch.get_width() * patch.get_height() for patch in bars]
            if stat == "density"
            else [
                patch.get_width() if axis is y_axis else patch.get_height()
                for patch in bars
            ]
        )
        assert sum(values) == pytest.approx(total)


def test_joint_refreshes_complete_cases_from_new_data_without_stale_derived_columns():
    p = mp.plot(data()).scatter("x", "y", group="h").joint(bins=2)
    raw = {"x": [10, None, 30], "y": [20, 5, 40], "h": ["A", "B", "B"]}
    p.dispatch(A.SetData(raw))
    assert p.spec.data.columns == raw
    assert all(panel_rows(raw, panel) == [0, 2] for panel in p.spec.panels)
    assert all(panel_columns(raw, panel)["x"] == [10, 30] for panel in p.spec.panels)
    assert mp.validate(p.spec) == []


def test_joint_uses_hue_selection_before_coordinate_validation_and_keeps_slots():
    raw = {"x": ["bad", 1, 2], "y": [0, 3, 4], "h": ["omit", "A", "A"]}
    p = mp.plot(raw).scatter("x", "y", group="h", hue_order=["missing", "A"])
    p.joint(bins=2).size(7, 6)
    assert mp.validate(p.spec) == []
    assert all(panel.layers[0].hue_order == ["missing", "A"] for panel in p.spec.panels)
    assert p.render().axes[0].get_legend_handles_labels()[1] == ["A"]


def test_joint_complete_cases_precede_log_checks_and_preserve_axis_limits():
    raw = {"x": [-2, 2, 3], "y": [None, 3, 4]}
    p = mp.plot(raw).scatter("x", "y").xscale("log").xlim(1, 4).joint(bins=2).size(7, 6)
    assert mp.validate(p.spec) == []
    a, _, b = p.render().axes
    assert a.get_xscale() == b.get_xscale() == "log"
    assert a.get_xlim() == b.get_xlim() == (1, 4)


def test_joint_copies_reference_styles_and_annotations_without_mutating_inputs():
    p = mp.plot(data()).scatter("x", "y", group="h", marker_size=4, alpha=0.8)
    p.labels(title="Question").title_reference(href="https://example.org/paper")
    p.hline(4, color="#333333").text("Note", [2, 3], color="#333333")
    before = p.spec
    p.joint(ratio=4)
    assert before.panels[0].dropna == [] and before.data == p.spec.data
    main = p.spec.panels[0]
    assert len(main.layers) == 3 and main.title_href == "https://example.org/paper"
    assert main.layers[0].marker_size == 4 and main.layers[0].alpha == 0.8
    assert p.spec.width_ratios == p.spec.height_ratios == [4, 1]
    view = p.spec
    assert view.width_ratios is not None and view.height_ratios is not None
    view.width_ratios[0] = 7
    assert view.height_ratios == [4, 1]


def test_joint_regression_and_histograms_use_the_same_finite_pairs():
    raw = {"x": [1, 2, 3, None], "y": [2, 4, 5, 8], "h": ["A"] * 4}
    p = mp.plot(raw).regplot("x", "y", group="h").joint(bins=2).size(7, 6)
    assert all(
        panel_rows(p.spec.data.columns, panel) == [0, 1, 2] for panel in p.spec.panels
    )
    assert len(p.render().axes) == 3


@pytest.mark.parametrize(
    "options",
    [
        {"bins": 0},
        {"bins": True},
        {"bins": [0, 1]},
        {"ratio": 0},
        {"ratio": True},
        {"ratio": float("inf")},
        {"ratio": 11},
        {"marginal_stat": "bad"},
    ],
)
def test_bad_joint_options_leave_state_and_history_unchanged(options):
    p = mp.plot(data()).scatter("x", "y")
    before, history = p.to_json(), p.action_log
    with pytest.raises(ValueError):
        p.joint(**options)
    assert p.to_json() == before and p.action_log == history


@pytest.mark.parametrize(
    "kind", ["empty", "line", "multiple", "semantic", "c", "polar", "y2"]
)
def test_unsupported_joint_templates_fail_before_partial_composition(kind):
    p = mp.plot({"x": [1, 2, 3], "y": [2, 3, 4], "h": ["A"] * 3})
    if kind == "line":
        p.line("x", "y")
    elif kind != "empty":
        if kind == "semantic":
            p.scatter("x", "y", hue="h")
        elif kind == "c":
            p.scatter("x", "y", c="y")
        else:
            p.scatter("x", "y")
        if kind == "multiple":
            p.layout(1, 2)
        elif kind == "polar":
            p.projection_polar()
        elif kind == "y2":
            p.secondary_yaxis()
    before = p.spec
    with pytest.raises(ValueError):
        p.joint()
    assert p.spec == before


@pytest.mark.parametrize(
    "raw",
    [
        {"x": [None], "y": [3]},
        {"x": ["cat"], "y": [3]},
        {"x": [True], "y": [3]},
    ],
)
def test_joint_rejects_no_pairs_and_categorical_or_boolean_coordinates(raw):
    p = mp.plot(raw).scatter("x", "y")
    with pytest.raises(ValueError):
        p.joint()


@pytest.mark.parametrize("extension", ["png", "pdf", "svg"])
def test_joint_roundtrips_and_reproduces_exports_without_global_randomness(
    tmp_path, extension
):
    state = np.random.get_state()
    p = mp.plot(data()).scatter("x", "y", group="h").joint(bins=3).size(7, 6)
    assert mp.apply(p.action_log) == mp.Plot.from_json(p.to_json()).spec == p.spec
    first, second = tmp_path / f"a.{extension}", tmp_path / f"b.{extension}"
    plt.close(p.save(str(first)))
    plt.close(mp.Plot.from_json(p.to_json()).save(str(second)))
    assert first.read_bytes() == second.read_bytes()
    after = np.random.get_state()
    assert state[0] == after[0] and state[2:] == after[2:]
    np.testing.assert_array_equal(state[1], after[1])


def test_joint_core_and_dropna_actions_do_not_import_optional_dependencies():
    script = (
        "import sys; import mudplot as m; "
        "p=m.plot({'x':[1,None,3],'y':[2,4,5]}).scatter('x','y').joint(); "
        "assert m.validate(p.spec)==[] and len(p.spec.panels)==3; "
        "assert m.apply(p.action_log)==p.spec; "
        "assert m.Plot.from_json(p.to_json()).spec==p.spec; "
        "assert 'numpy' not in sys.modules and 'matplotlib' not in sys.modules"
    )
    subprocess.run([sys.executable, "-S", "-c", script], check=True)


def test_dropna_schema_and_editor_import_and_old_defaults():
    import jsonschema
    from dashboard.editor_server import EditorSession

    p = mp.plot(data()).scatter("x", "y", group="h").joint().size(7, 6)
    jsonschema.validate(p.spec.to_dict(), mp.json_schema())
    session = EditorSession()
    session.load_spec(p.to_json())
    assert session.store.state == p.spec
    session.select_panel(2)
    session.dispatch_safe(A.SetTitle("Marginal", panel=2))
    assert session.error is None and b"<svg" in session.export("svg")
    old = mp.plot(data()).scatter("x", "y").spec.to_dict()
    del old["panels"][0]["dropna"]
    assert mp.FigureSpec.from_dict(old).panels[0].dropna == []


@pytest.mark.parametrize("required", [None, "x", ["missing"], ["x", "x"], [[]]])
def test_bad_dropna_selectors_are_reported_without_mutation(required):
    spec = mp.plot(data()).scatter("x", "y").spec
    spec.panels[0].dropna = required
    before = copy.deepcopy(spec)
    assert mp.validate(spec)
    assert spec == before


def test_dropna_shared_semantic_domains_keep_original_row_ids():
    from mudplot._semantics import shared_scale_domains

    raw = {
        "x": [1, 2, 3, 4],
        "y": [2, 3, 4, 5],
        "h": ["A", "B", "A", "B"],
        "m": [1, 20, 3, 9],
        "keep": ["yes", None, "yes", "yes"],
    }
    config = mp.SemanticSpec(hue="h", size="m", sizes=[3, 8], scale_id="study")
    spec = mp.plot(raw).scatter("x", "y", semantics=config).spec
    spec.panels[0].dropna = ["keep"]
    assert shared_scale_domains(spec)["study"]["rows"] == [0, 2, 3]
    plot = mp.Plot.from_json(mp.to_json(spec))
    collection = plot.render().axes[0].collections[0]
    assert isinstance(collection, PathCollection)
    np.testing.assert_allclose(collection.get_sizes(), [9, 4.25**2, 64])


def test_joint_derived_log_bin_failure_preserves_existing_output(tmp_path):
    plot = mp.plot({"x": [0.1, 0.1], "y": [1, 2]}).scatter("x", "y")
    plot.xscale("log").joint(bins=3).size(6, 6)
    path = tmp_path / "keep.png"
    path.write_bytes(b"previous output")
    with pytest.raises(ValueError, match="derived log histogram bin edges"):
        plot.save(str(path))
    assert path.read_bytes() == b"previous output"
    assert not plt.get_fignums()
