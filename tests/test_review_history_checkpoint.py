"""A single default-reducer checkpoint must not change observable Store semantics."""

import mudplot as mp
import pytest
from mudplot import actions as A
from mudplot.spec import FigureSpec
from mudplot.store import Store


def actions(count: int) -> list[A.Action]:
    return [
        A.SetTitle(f"title-{i}") if i % 2 else A.SetSize(4 + i / 10000, 3)
        for i in range(count)
    ]


def store_with_history(count: int) -> tuple[Store, FigureSpec, list[A.Action]]:
    initial = mp.plot({"x": [0, 1, 2], "y": [1, 3, 2]}).line("x", "y").spec
    batch = actions(count)
    store = Store(initial)
    store.dispatch_all(batch)
    return store, initial, batch


def test_near_tail_checkpoint_is_single_prior_state_and_replay_stays_exact():
    store, initial, batch = store_with_history(256)
    checkpoint = store._checkpoint
    assert checkpoint is not None and checkpoint[0] == 192
    events = []
    store.subscribe(lambda state, action: events.append((state, action)))
    for cursor in range(255, 179, -1):
        assert store.undo() == mp.apply(batch[:cursor], initial)
    for cursor in range(181, 257):
        assert store.redo() == mp.apply(batch[:cursor], initial)
    assert (
        store.history == batch
        and len(events) == 152
        and all(action is None for _, action in events)
    )
    assert store._checkpoint is checkpoint


def test_branch_below_checkpoint_invalidates_only_cache_not_history_semantics():
    store, initial, batch = store_with_history(130)
    for _ in range(70):
        store.undo()
    assert len(store.history) == 60
    new = A.SetTitle("branch")
    expected = mp.apply([*batch[:60], new], initial)
    assert store.dispatch(new) == expected
    assert store._checkpoint is None
    assert store.redo() == expected
    assert store.undo() == mp.apply(batch[:60], initial)


def test_branch_at_checkpoint_reuses_valid_prefix_and_clears_redo():
    store, initial, batch = store_with_history(130)
    store.undo()
    store.undo()
    before = store._checkpoint
    assert before is not None and before[0] == 128
    action = A.SetTitle("new129")
    expected = mp.apply([*batch[:128], action], initial)
    assert store.dispatch(action) == expected and store.redo() == expected
    assert store.undo() == mp.apply(batch[:128], initial)


def test_public_snapshot_mutation_cannot_change_internal_checkpoint():
    store, initial, batch = store_with_history(130)
    state = store.state
    state.data.columns["x"][0] = -99
    history = store.history
    history[0] = A.SetTitle("mutated external history")
    assert store.undo() == mp.apply(batch[:129], initial)
    result = store.undo()
    result.data.columns["x"][0] = -98
    assert store.redo() == mp.apply(batch[:129], initial)
    assert initial.data.columns["x"][0] == 0


def test_custom_reducer_keeps_full_replay_and_gets_no_default_cache():
    calls = []

    def custom(state, action):
        calls.append(action)
        return mp.reduce(state, action)

    store = Store(reducer=custom)
    batch = actions(130)
    store.dispatch_all(batch)
    before = len(calls)
    store.undo()
    assert len(calls) - before == 129
    assert store._checkpoint is None


def test_failed_dispatch_does_not_replace_valid_checkpoint():
    store, initial, batch = store_with_history(128)
    checkpoint = store._checkpoint
    with pytest.raises(ValueError):
        store.dispatch(A.SetTitle("invalid", panel=-1))
    assert store._checkpoint is checkpoint and store.history == batch
    assert store.state == mp.apply(batch, initial)


def test_listener_failure_after_checkpoint_commit_does_not_roll_back():
    store, initial, batch = store_with_history(64)

    def fail(state, action):
        raise RuntimeError("synthetic listener failure")

    remove = store.subscribe(fail)
    action = A.SetTitle("committed before listener")
    with pytest.raises(RuntimeError, match="listener failure"):
        store.dispatch(action)
    assert store.history == [*batch, action]
    assert store._checkpoint is not None and store._checkpoint[0] == 64
    remove()
    assert store.undo() == mp.apply(batch, initial)
    assert store.redo() == mp.apply([*batch, action], initial)


def test_noop_at_cache_boundary_is_still_an_event():
    store, _, batch = store_with_history(64)
    before = store.state
    events = []
    store.subscribe(lambda state, action: events.append(action))
    noop = A.SetTitle(before.panels[0].title)
    assert store.dispatch(noop) == before
    assert store.history == [*batch, noop] and events == [noop]
    assert store.undo() == before and len(store.history) == 64


def test_setdata_checkpoint_and_action_payloads_remain_detached():
    store, initial, _ = store_with_history(64)
    data = {"x": [10, 11], "y": [12, 13]}
    action = A.SetData(data)
    result = store.dispatch(action)
    data["x"][0] = -1
    result.data.columns["x"][0] = -2
    assert store.state.data.columns["x"] == [10, 11]
    assert store.undo().data.columns == initial.data.columns
    assert store.redo().data.columns["x"] == [10, 11]
