"""Immediate history transitions preserve public isolation and replay semantics."""

from __future__ import annotations

import copy

import mudplot as mp
import pytest
from mudplot import actions as A


def test_mutable_inputs_listeners_and_history_cannot_change_undo_redo_states():
    initial = mp.plot({"x": [1, 2], "y": [3, 4]}).line("x", "y").spec
    expected_initial = copy.deepcopy(initial)
    store = mp.Store(initial)
    initial.data.columns["x"][0] = -1
    payload = {"x": [10, 20], "y": [30, 40]}
    action = A.SetData(payload)
    observed = []

    def corrupt(state, event):
        state.data.columns["x"][0] = -100
        if isinstance(event, A.SetData):
            event.columns["x"][0] = -200

    store.subscribe(corrupt)
    store.subscribe(lambda state, event: observed.append((state, event)))
    result = store.dispatch(action)
    expected_changed = mp.reduce(expected_initial, A.SetData(copy.deepcopy(payload)))
    payload["x"][0] = -2
    result.data.columns["x"][0] = -3
    external_history = store.history
    assert isinstance(external_history[0], A.SetData)
    external_history[0].columns["x"][0] = -4
    assert store.state == expected_changed
    assert observed[0][0] == expected_changed
    assert isinstance(observed[0][1], A.SetData)
    assert observed[0][1].columns["x"] == [10, 20]
    undone = store.undo()
    assert undone == expected_initial and observed[-1] == (expected_initial, None)
    undone.data.columns["x"][0] = -5
    redone = store.redo()
    assert redone == expected_changed and observed[-1] == (expected_changed, None)
    redone.data.columns["x"][0] = -6
    assert store.undo() == expected_initial
    assert store.redo() == expected_changed
    assert store.history == [A.SetData({"x": [10, 20], "y": [30, 40]})]


@pytest.mark.parametrize("count", [63, 64, 65, 129])
def test_repeated_undo_redo_and_branch_match_independent_prefix_states(count):
    initial = mp.plot({"x": [0, 1], "y": [2, 3]}).line("x", "y").spec
    batch = [A.SetTitle(f"title-{i}") for i in range(count)]
    store = mp.Store(initial)
    store.dispatch_all(batch)
    for cursor in range(count - 1, count - 4, -1):
        assert store.undo() == mp.apply(batch[:cursor], initial)
        assert store.history == batch[:cursor]
    assert store.redo() == mp.apply(batch[: count - 2], initial)
    assert store.undo() == mp.apply(batch[: count - 3], initial)
    branch = A.SetTitle("branch")
    expected = mp.apply([*batch[: count - 3], branch], initial)
    assert store.dispatch(branch) == expected
    assert store.redo() == expected
    assert store.undo() == mp.apply(batch[: count - 3], initial)
    assert store.redo() == expected


def test_failed_default_redo_preserves_state_history_and_pending_action(monkeypatch):
    store = mp.Store()
    store.dispatch(A.SetTitle("A"))
    store.dispatch(A.SetTitle("B"))
    store.undo()
    state, history = store.state, store.history
    original_deepcopy = copy.deepcopy

    def fail_state_copy(value, memo=None):
        if isinstance(value, mp.FigureSpec):
            raise MemoryError("synthetic state allocation failure")
        return original_deepcopy(value, memo)

    with monkeypatch.context() as patch:
        patch.setattr(copy, "deepcopy", fail_state_copy)
        with pytest.raises(MemoryError, match="state allocation"):
            store.redo()
    assert store.state == state and store.history == history
    assert store.redo().panels[0].title == "B"
    assert store.undo() == state


def test_custom_reducer_retains_exact_full_replay_call_order():
    calls = []

    def custom(state, action):
        calls.append((state.panels[0].title, action.text))
        return mp.reduce(state, action)

    store = mp.Store(reducer=custom)
    store.dispatch(A.SetTitle("A"))
    store.dispatch(A.SetTitle("B"))
    store.dispatch(A.SetTitle("C"))
    calls.clear()
    assert store.undo().panels[0].title == "B"
    assert calls == [("", "A"), ("A", "B")]
    calls.clear()
    assert store.redo().panels[0].title == "C"
    assert calls == [("", "A"), ("A", "B"), ("B", "C")]
