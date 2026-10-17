"""HIST-04/05/06: existing document policies, no-op events and bounded long replay."""

from __future__ import annotations

import hashlib
import random

import mudplot as mp
import pytest
from dashboard.editor_server import EditorSession
from mudplot import actions as A


def _document(title, *, second=False):
    x, y = ("u", "v") if second else ("x", "y")
    return mp.plot({x: [1, 2], y: [2, 3]}).line(x, y).labels(title=title).size(4, 3)


def _saved(session, path):
    state = session.store.state
    mp.save_spec(state, path)
    assert mp.load_spec(path) == state
    assert b"<svg" in session.export("svg")
    return state, session.png


def test_python_open_and_reset_start_fresh_history_without_touching_imported_files(
    tmp_path,
):
    first, second = _document("A"), _document("B", second=True)
    source_a, source_b = tmp_path / "a.json", tmp_path / "b.json"
    mp.save_spec(first.spec, source_a)
    mp.save_spec(second.spec, source_b)
    original_a, original_b = source_a.read_bytes(), source_b.read_bytes()
    session = EditorSession()
    session.load_spec(mp.to_json(mp.load_spec(source_a)))
    session.dispatch_safe(A.SetTitle("A-edited"))
    session.dispatch_safe(A.SetTitle("A-future"))
    session.undo()
    assert session.store.state.panels[0].title == "A-edited"
    session.load_spec(mp.to_json(mp.load_spec(source_b)))
    opened, preview = _saved(session, tmp_path / "download-b.json")
    assert opened == second.spec and session.action_log() == []
    assert session.active_panel == 0
    session.undo()
    session.redo()
    assert session.store.state == opened and session.png == preview
    session.dispatch_safe(A.SetTitle("B-edited"))
    session.undo()
    session.reset()
    reset, reset_png = _saved(session, tmp_path / "download-reset.json")
    assert reset == mp.FigureSpec() and session.action_log() == []
    session.undo()
    session.redo()
    assert session.store.state == reset and session.png == reset_png
    assert source_a.read_bytes() == original_a and source_b.read_bytes() == original_b


def test_store_noop_is_an_event_and_clears_the_old_redo_branch():
    store = mp.Store()
    events = []
    store.subscribe(lambda state, action: events.append((state, action)))
    store.dispatch(A.SetTitle("A"))
    store.dispatch(A.SetTitle("B"))
    store.undo()
    before = store.state
    event_count = len(events)
    store.dispatch(A.SetTitle("A"))
    assert store.state == before
    assert store.history == [A.SetTitle("A"), A.SetTitle("A")]
    assert len(events) == event_count + 1 and events[-1][1] == A.SetTitle("A")
    assert store.redo() == before
    assert store.undo() == before and store.history == [A.SetTitle("A")]


def test_python_editor_noop_keeps_an_event_and_identical_successful_preview(tmp_path):
    session = EditorSession()
    session.load_spec(_document("A").to_json())
    session.dispatch_safe(A.SetTitle("B"))
    session.undo()
    before, preview = session.store.state, session.png
    session.dispatch_safe(A.SetTitle("A"))
    assert session.error is None and session.store.state == before
    assert session.action_log() == [A.action_to_dict(A.SetTitle("A"))]
    assert session.png == preview
    session.redo()
    assert session.store.state == before and session.png == preview
    assert _saved(session, tmp_path / "noop.json") == (before, preview)


@pytest.mark.parametrize("seed", [20261016, 24301])
def test_seeded_long_history_replay_matches_exact_states_without_numeric_drift(seed):
    rng = random.Random(seed)
    initial = _document("initial").spec
    store = mp.Store(initial)
    states = [initial]
    actions = []
    for index in range(768):
        choice = rng.randrange(4)
        if choice == 0:
            action = A.SetTitle(f"title-{index}-{rng.randrange(1000)}")
        elif choice == 1:
            action = A.SetSize(rng.uniform(3, 8), rng.uniform(2, 6))
        elif choice == 2:
            action = A.SetFont({"size": rng.uniform(8, 14)})
        else:
            action = A.SetLimits("x", -rng.random(), 3 + rng.random())
        actions.append(action)
        states.append(mp.reduce(states[-1], action))
        assert store.dispatch(action) == states[-1]
    # Full replay is deliberately linear in history; exercise bounded checkpoints.
    for cursor in range(767, 639, -1):
        assert store.undo() == states[cursor]
        assert len(store.history) == cursor
    for cursor in range(641, 769):
        assert store.redo() == states[cursor]
        assert len(store.history) == cursor
    assert store.history == actions
    assert mp.apply(actions, initial) == store.state == states[-1]
    expected = hashlib.sha256(
        mp.to_json(states[-1], sort_keys=True).encode()
    ).hexdigest()
    actual = hashlib.sha256(
        mp.to_json(store.state, sort_keys=True).encode()
    ).hexdigest()
    assert actual == expected
