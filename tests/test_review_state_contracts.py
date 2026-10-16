"""Checklist STATE-04/05/06: distinct failure contracts, not one batch rollback rule."""

from __future__ import annotations

import copy

import mudplot as mp
import pytest
from mudplot import actions as A


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
