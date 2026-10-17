"""Checklist STATE-04/05/06: distinct failure contracts, not one batch rollback rule."""

from __future__ import annotations

import copy

import mudplot as mp
import pytest
from mudplot import actions as A


def _nested_plot():
    return (
        mp.plot(
            {
                "x": [1, 2],
                "y": [2, 3],
                "g": ["A", "A"],
                "meta": [{"tags": ["first"]}, {"tags": ["second"]}],
            }
        )
        .matrix("m", [[1, 2], [3, 4]])
        .line("x", "y", group="g", references={"A": mp.Reference(citation="original")})
    )


def _corrupt_snapshot(spec):
    spec.data.columns["meta"][0]["tags"].append("external")
    spec.data.matrices["m"][0][0] = 99
    spec.theme.hatches[0] = "external"
    references = spec.panels[0].layers[0].references
    assert references is not None
    references["A"].citation = "external"


def test_state_01_nested_reducer_output_cannot_mutate_input_or_action():
    initial = _nested_plot().spec
    action = A.AddLayer(copy.deepcopy(initial.panels[0].layers[0]))
    before, payload = copy.deepcopy(initial), copy.deepcopy(action)
    result = mp.reduce(initial, action)
    assert initial == before and action == payload
    _corrupt_snapshot(result)
    references = result.panels[0].layers[-1].references
    assert references is not None
    references["A"].citation = "changed new layer"
    assert initial == before and action == payload


@pytest.mark.parametrize(
    "action", [A.RemoveLayer(99), A.SetFont({"unknown": ["value"]})]
)
def test_state_01_nested_reducer_failure_preserves_both_inputs(action):
    initial = _nested_plot().spec
    before, payload = copy.deepcopy(initial), copy.deepcopy(action)
    with pytest.raises(ValueError):
        mp.reduce(initial, action)
    assert initial == before and action == payload


@pytest.mark.parametrize("surface", ["plot", "store", "dispatch"])
def test_state_02_nested_public_snapshots_are_independent(surface):
    plot = _nested_plot()
    if surface == "plot":
        snapshot = plot.spec
    elif surface == "store":
        snapshot = plot.store.state
    else:
        snapshot = plot.store.dispatch(A.SetTitle("committed"))
    before, other, history = plot.spec, plot.store.state, plot.store.history
    _corrupt_snapshot(snapshot)
    assert plot.spec == before == other
    assert plot.store.history == history


def test_state_02_nested_history_actions_are_independent_and_replay_is_unchanged():
    plot = _nested_plot()
    before, history = plot.spec, plot.store.history
    columns = history[0]
    assert isinstance(columns, A.SetData)
    columns.columns["meta"][0]["tags"].append("external")
    matrix = next(action for action in history if isinstance(action, A.SetMatrix))
    assert isinstance(matrix, A.SetMatrix)
    matrix.values[0][0] = 99
    history.append(A.SetTitle("not dispatched"))
    plot.store.undo()
    plot.store.redo()
    assert plot.spec == before and plot.store.history != history


def test_state_02_listeners_receive_separate_nested_snapshots_and_payloads():
    plot = _nested_plot()
    before = plot.spec
    observed = []

    def corrupt(spec, action):
        _corrupt_snapshot(spec)
        if isinstance(action, A.SetData):
            action.columns["meta"][0]["tags"].append("external")

    plot.store.subscribe(corrupt)
    plot.store.subscribe(lambda spec, action: observed.append((spec, action)))
    plot.store.dispatch(A.SetData(copy.deepcopy(before.data.columns)))
    assert plot.spec == before and observed[0][0] == before
    payload = observed[0][1]
    assert isinstance(payload, A.SetData) and payload.columns == before.data.columns


def test_hist_01_undo_redo_visits_every_expected_state_and_stops_at_boundaries():
    initial = _nested_plot().spec
    store = mp.Store(initial)
    actions = [A.SetTitle("A"), A.SetSize(4, 3), A.SetPalette(params={"hue_start": 45})]
    states = [initial]
    for action in actions:
        states.append(mp.reduce(states[-1], action))
        assert store.dispatch(action) == states[-1]
    assert store.redo() == states[-1]
    for cursor in range(len(actions) - 1, -1, -1):
        assert store.undo() == states[cursor]
        assert store.history == actions[:cursor]
    assert store.undo() == initial and store.history == []
    for cursor in range(1, len(actions) + 1):
        assert store.redo() == states[cursor]
        assert store.history == actions[:cursor]
    assert store.redo() == states[-1] and store.history == actions


def test_hist_02_editor_branch_keeps_saved_state_history_and_preview_on_new_branch(
    tmp_path,
):
    from dashboard.editor_server import EditorSession

    session = EditorSession()
    session.load_spec(
        mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y").size(4, 3).to_json()
    )
    for title in ("A", "B", "C"):
        session.dispatch_safe(A.SetTitle(title))
        assert session.error is None
    session.undo()
    assert session.store.state.panels[0].title == "B"
    session.dispatch_safe(A.SetTitle("D"))
    state, history, preview = session.store.state, session.store.history, session.png
    session.redo()
    assert session.store.state == state and session.store.history == history
    assert session.png == preview and state.panels[0].title == "D"
    assert [action.text for action in history if isinstance(action, A.SetTitle)] == [
        "A",
        "B",
        "D",
    ]
    path = tmp_path / "branch.json"
    mp.save_spec(state, path)
    assert mp.load_spec(path) == state


def test_state_04_functional_apply_failure_preserves_caller_inputs():
    initial = mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y").spec
    actions = [A.SetTitle("not a partial result"), A.RemoveLayer(99)]
    before_state, before_actions = copy.deepcopy(initial), copy.deepcopy(actions)
    with pytest.raises(ValueError, match="out of range"):
        mp.apply(actions, initial)
    assert initial == before_state and actions == before_actions


def test_state_04_functional_apply_parse_failure_does_not_leak_first_action():
    initial = mp.FigureSpec()
    before = copy.deepcopy(initial)
    actions = [{"type": "SetTitle", "text": "first"}, {"type": "NoSuchAction"}]
    original = copy.deepcopy(actions)
    with pytest.raises(ValueError):
        mp.apply(actions, initial)
    assert initial == before and actions == original


def test_state_05_plot_apply_keeps_completed_prefix_and_can_continue():
    plot = mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y")
    history = plot.action_log
    with pytest.raises(ValueError, match="out of range"):
        plot.apply(
            [A.SetTitle("committed prefix"), A.RemoveLayer(99), A.SetTitle("never")]
        )
    assert plot.spec.panels[0].title == "committed prefix"
    assert plot.action_log == [
        *history,
        A.action_to_dict(A.SetTitle("committed prefix")),
    ]
    plot.labels(title="still usable")
    assert plot.spec.panels[0].title == "still usable"


def test_state_05_store_dispatch_all_commits_prefix_and_invalidates_old_redo():
    store = mp.Store()
    store.dispatch(A.SetTitle("base"))
    store.dispatch(A.SetTitle("old redo"))
    store.undo()
    with pytest.raises(ValueError, match="out of range"):
        store.dispatch_all([A.SetTitle("new prefix"), A.RemoveLayer(99)])
    assert store.state.panels[0].title == "new prefix"
    assert store.history == [A.SetTitle("base"), A.SetTitle("new prefix")]
    assert store.redo().panels[0].title == "new prefix"
    assert store.undo().panels[0].title == "base"


def test_state_06_listener_failure_occurs_after_commit_and_is_not_rollback():
    store = mp.Store()
    seen = []
    store.subscribe(
        lambda state, action: seen.append(("first", state.panels[0].title, action))
    )

    def fail_after_commit(state, action):
        seen.append(("failing", state.panels[0].title, action))
        raise RuntimeError("synthetic listener failure")

    unsubscribe = store.subscribe(fail_after_commit)
    store.subscribe(
        lambda state, action: seen.append(("last", state.panels[0].title, action))
    )
    with pytest.raises(RuntimeError, match="synthetic listener failure"):
        store.dispatch(A.SetTitle("already committed"))
    assert store.state.panels[0].title == "already committed"
    assert store.history == [A.SetTitle("already committed")]
    assert [entry[0] for entry in seen] == ["first", "failing"]
    unsubscribe()
    store.dispatch(A.SetTitle("next action"))
    assert store.state.panels[0].title == "next action"
    assert store.undo().panels[0].title == "already committed"
