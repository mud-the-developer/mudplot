"""Pairwise rows and named value-axis sharing, independent of diagonal units."""

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
from matplotlib.collections import PathCollection
from matplotlib.patches import Rectangle
from mudplot import actions as A
from mudplot._facet import panel_rows
from mudplot.spec import AxisSpec


def data():
    return {
        "a": [1, 2, None, 4, 5],
        "b": [10, None, 30, 40, 50],
        "c": [100, 200, 300, None, 500],
        "h": ["B", "A", "B", "A", None],
        "unrelated": [None] * 5,
    }


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.mark.parametrize("group", [None, "h"])
def test_pair_matrix_preserves_source_and_uses_cell_pairwise_rows(group):
    p = (
        mp.plot(data())
        .pair(["a", "b", "c"], group=group, bins=3, diag_stat="count")
        .size(9, 9)
    )
    assert p.spec.data.columns == data()
    assert p.spec.layout == [3, 3] and len(p.spec.panels) == 9
    assert mp.validate(p.spec) == []
    axes = p.render().axes
    for index, (panel, ax) in enumerate(zip(p.spec.panels, axes, strict=True)):
        row, col = divmod(index, 3)
        names = ["a", "b", "c"]
        required = (
            [names[col]]
            + ([] if row == col else [names[row]])
            + ([group] if group else [])
        )
        expected = [
            i for i in range(5) if all(data()[name][i] is not None for name in required)
        ]
        assert panel_rows(p.spec.data.columns, panel) == expected
        if row == col:
            assert panel.layers[0].type == "hist" and panel.y.share_id is None
            assert sum(
                bar.get_height() for bar in ax.patches if isinstance(bar, Rectangle)
            ) == len(expected)
        else:
            assert panel.layers[0].type == "scatter"
            assert sum(
                np.asarray(c.get_offsets()).shape[0]
                for c in ax.collections
                if isinstance(c, PathCollection)
            ) == len(expected)
        if group:
            assert panel.layers[0].hue_order == ["B", "A"]
    assert axes[1].get_shared_y_axes().joined(axes[1], axes[2])
    assert not axes[0].get_shared_y_axes().joined(axes[0], axes[1])
    assert axes[0].get_shared_x_axes().joined(axes[0], axes[3])
    assert axes[3].get_shared_y_axes().joined(axes[3], axes[5])
    assert not axes[4].get_shared_y_axes().joined(axes[3], axes[4])


def test_pair_uses_univariate_diagonals_and_allows_empty_bivariate_cells():
    p = mp.plot({"a": [1, None], "b": [None, 2]}).pair(["a", "b"], bins=2).size(6, 6)
    axes = p.render().axes
    assert not axes[1].collections and not axes[2].collections
    assert axes[0].patches and axes[3].patches


def test_pair_group_selection_precedes_numeric_validation_and_preserves_hue_slots():
    raw = {"a": ["omit", 1, 2], "b": ["omit", 3, 4], "h": ["omit", "A", "A"]}
    p = (
        mp.plot(raw)
        .pair(["a", "b"], group="h", hue_order=["missing", "A"], bins=2)
        .size(6, 6)
    )
    assert mp.validate(p.spec) == []
    assert p.render().axes[1].get_legend_handles_labels()[1] == ["A"]
    assert p.spec.data.columns == raw


def test_pair_named_axes_refresh_ranges_and_complete_cases_on_set_data():
    p = mp.plot(data()).pair(["a", "b", "c"], bins=3).size(9, 9)
    new = {"a": [100, 200, 300], "b": [1000, None, 3000], "c": [10, 20, 30]}
    p.dispatch(A.SetData(new))
    assert panel_rows(new, p.spec.panels[1]) == [0, 2]
    axes = p.render().axes
    assert axes[1].get_ylim() == axes[2].get_ylim()
    assert axes[1].get_ylim()[0] < 100 < axes[1].get_ylim()[1]
    assert axes[1].get_ylim()[1] > 300
    assert axes[0].get_xlim() == axes[3].get_xlim() == axes[6].get_xlim()


def test_pair_empty_template_legends_and_figure_settings_are_preserved():
    p = (
        mp.plot(data())
        .theme("publication")
        .font(size=12)
        .legend(False)
        .suptitle("Study")
        .size(8, 8)
    )
    before = p.spec
    p.pair(["a", "b"])
    assert p.spec.theme == before.theme and p.spec.size == before.size
    assert p.spec.suptitle == "Study" and all(
        not panel.legend.show for panel in p.spec.panels
    )
    view = p.spec
    assert view.panels[0].layers[0].hue_order is None
    view.panels[0].dropna.append("local")
    assert view.panels[1].dropna == ["b", "a"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"columns": []},
        {"columns": ["a"]},
        {"columns": ["a", "a"]},
        {"columns": ["a", "missing"]},
        {"columns": ["a", None]},
        {"columns": ["a", "b"], "group": "missing"},
        {"columns": ["a", "b"], "hue_order": ["A"]},
        {"columns": ["a", "b"], "bins": True},
        {"columns": ["a", "b"], "bins": 0},
        {"columns": ["a", "b"], "diag_stat": "bad"},
        {"columns": ["a", "b"], "group": "h", "hue_order": []},
    ],
)
def test_invalid_pair_args_do_not_change_state_or_history(kwargs):
    p = mp.plot(data())
    original, history = p.to_json(), p.action_log
    with pytest.raises(ValueError):
        p.pair(**kwargs)
    assert p.to_json() == original and p.action_log == history


@pytest.mark.parametrize("value", ["category", True, float("inf"), None])
def test_pair_rejects_non_numeric_or_completely_missing_variables(value):
    p = mp.plot({"a": [value], "b": [2]})
    with pytest.raises(ValueError):
        p.pair(["a", "b"])


def test_pair_rejects_existing_layers_and_axis_settings_instead_of_discarding_them():
    for p in (
        mp.plot(data()).scatter("a", "b"),
        mp.plot(data()).xlim(0, 10),
        mp.plot(data()).layout(1, 2),
    ):
        original = p.spec
        with pytest.raises(ValueError, match="empty default panel"):
            p.pair(["a", "b"])
        assert p.spec == original


def test_pair_bounds_grid_allocation_to_eight_variables():
    raw = {f"v{i}": [i, i + 1] for i in range(9)}
    p = mp.plot(raw).pair(list(raw)[:8])
    assert len(p.spec.panels) == 64 and mp.validate(p.spec) == []
    with pytest.raises(ValueError, match=r"2\.\.8"):
        mp.plot(raw).pair(list(raw))


@pytest.mark.parametrize("extension", ["png", "pdf", "svg"])
def test_pair_actions_json_exports_and_global_rng(tmp_path, extension):
    state = np.random.get_state()
    p = mp.plot(data()).pair(["a", "b"], group="h", bins=3).size(6, 6)
    assert mp.apply(p.action_log) == mp.Plot.from_json(p.to_json()).spec == p.spec
    first, second = tmp_path / f"a.{extension}", tmp_path / f"b.{extension}"
    plt.close(p.save(str(first)))
    plt.close(mp.Plot.from_json(p.to_json()).save(str(second)))
    assert first.read_bytes() == second.read_bytes()
    after = np.random.get_state()
    assert state[0] == after[0] and state[2:] == after[2:]
    np.testing.assert_array_equal(state[1], after[1])


def test_pair_and_named_sharing_need_no_optional_core_dependencies():
    script = (
        "import sys; import mudplot as m; "
        "p=m.plot({'a':[1,2],'b':[3,4]}).pair(['a','b']); "
        "assert m.validate(p.spec)==[] and m.apply(p.action_log)==p.spec; "
        "assert m.Plot.from_json(p.to_json()).spec==p.spec; "
        "assert 'numpy' not in sys.modules and 'matplotlib' not in sys.modules"
    )
    subprocess.run([sys.executable, "-S", "-c", script], check=True)


def test_named_axis_sharing_rejects_conflicts_and_unsupported_spaces():
    p = mp.plot({"x": [1, 2], "y": [3, 4]}).scatter("x", "y").layout(1, 2)
    p.scatter("x", "y", panel=1).share_axis("y", "study").share_axis(
        "y", "study", panel=1
    )
    assert mp.validate(p.spec) == []
    p.yscale("log", panel=1)
    assert any("conflicting scale" in issue for issue in mp.validate(p.spec))
    p.yscale("linear", panel=1).share(y="all")
    assert any("cannot mix figure sharing" in issue for issue in mp.validate(p.spec))
    p.share(y="none").ylim(1, 5).ylim(2, 6, panel=1)
    assert any("conflicting limits" in issue for issue in mp.validate(p.spec))
    p.ylim(panel=1).projection_polar()
    assert any("primary Cartesian" in issue for issue in mp.validate(p.spec))


@pytest.mark.parametrize("name", ["", " ", "a\n", 3, []])
def test_invalid_named_axis_groups_report_issues(name):
    spec = mp.plot(data()).spec
    spec.panels[0].x.share_id = name
    before = copy.deepcopy(spec)
    assert mp.validate(spec)
    assert spec == before


def test_old_axis_json_defaults_and_actions_and_editor_roundtrip():
    import jsonschema
    from dashboard.editor_server import EditorSession

    original = mp.plot(data()).spec.to_dict()
    del original["panels"][0]["x"]["share_id"]
    assert mp.FigureSpec.from_dict(original).panels[0].x == AxisSpec()
    action = A.SetAxisShare("x", "study")
    assert (
        A.action_from_dict(json.loads(json.dumps(A.action_to_dict(action)))) == action
    )
    p = mp.plot(data()).pair(["a", "b"], bins=3).size(6, 6)
    jsonschema.validate(p.spec.to_dict(), mp.json_schema())
    session = EditorSession()
    session.load_spec(p.to_json())
    session.select_panel(3)
    session.dispatch_safe(A.SetTitle("Edited diagonal", panel=3))
    assert (
        session.error is None
        and session.store.state.panels[3].title == "Edited diagonal"
    )
    assert b"<svg" in session.export("svg")
