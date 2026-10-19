"""Bounded exhaustive state machine with an independent field oracle and shrinker."""

from __future__ import annotations

import copy
import itertools
import json
from functools import lru_cache
from pathlib import Path

import mudplot as mp
import pytest
from mudplot import actions as A
from mudplot.spec import DataSpec, FigureSpec, PanelSpec
from mudplot.store import Store

EVENTS = ("title-a", "title-b", "size", "panel", "undo", "redo", "invalid", "snapshot")
FIXTURE = Path(__file__).parent / "fixtures/state_machine_regressions.json"


@lru_cache(maxsize=3)
def template(prefix):
    initial = FigureSpec(data=DataSpec(columns={"x": [0, 1, 2]}), size=[4, 3])
    store = Store(initial)
    states: list[tuple[str, tuple[int, int], int]] = [
        (initial.panels[0].title, (4, 3), 1)
    ]
    for index in range(prefix):
        title = "A" if index % 2 == 0 else "B"
        store.dispatch(A.SetTitle(title))
        states.append((title, (4, 3), 1))
    return initial, store, states


class StaleRedo(list[A.Action]):
    def clear(self):
        """Controlled bad behavior used only to prove shrinking sensitivity."""


def run_trace(events, prefix=0, stale_redo=False):
    initial, original, original_states = template(prefix)
    store = copy.deepcopy(original)
    states = list(original_states)
    future = []
    if stale_redo:
        store._redo_stack = StaleRedo()
    delivered = []

    def listener(snapshot, action):
        delivered.append(action)
        snapshot.data.columns["x"][0] = -99

    store.subscribe(listener)
    expected_events = 0
    for event in events:
        title, size, panels = states[-1]
        if event in ("title-a", "title-b", "size", "panel"):
            if event.startswith("title-"):
                title = event[-1].upper()
                action = A.SetTitle(title)
            elif event == "size":
                size = (5, 3)
                action = A.SetSize(*size)
            else:
                panels += 1
                action = A.AddPanel()
            store.dispatch(action)
            states.append((title, size, panels))
            future.clear()
            expected_events += 1
        elif event == "undo":
            if len(states) > 1:
                future.append(states.pop())
                expected_events += 1
            store.undo()
        elif event == "redo":
            if future:
                states.append(future.pop())
                expected_events += 1
            store.redo()
        elif event == "invalid":
            try:
                store.dispatch(A.SetTitle("rejected", panel=-1))
            except ValueError:
                pass
            else:
                raise AssertionError("negative panel must reject")
        else:
            snapshot = store.state
            snapshot.data.columns["x"][0] = -98
            store.history.clear()
        expected = copy.deepcopy(initial)
        expected.panels = [PanelSpec() for _ in range(states[-1][2])]
        expected.panels[0].title = states[-1][0]
        expected.size = list(states[-1][1])
        actual = store.state
        assert actual == expected, event
        assert mp.from_json(mp.to_json(actual)) == expected
        assert len(store.history) == len(states) - 1
        assert len(delivered) == expected_events
        assert initial.data.columns["x"] == [0, 1, 2]
    return store


def shrink_trace(events, fails):
    result = list(events)
    while True:
        for index in range(len(result)):
            shorter = result[:index] + result[index + 1 :]
            if shorter and fails(shorter):
                result = shorter
                break
        else:
            return result


def checked_trace(events, prefix):
    try:
        run_trace(events, prefix)
    except AssertionError:

        def fails(candidate):
            try:
                run_trace(candidate, prefix)
            except AssertionError:
                return True
            return False

        minimal = shrink_trace(events, fails)
        pytest.fail(f"prefix={prefix}, deletion-minimal events={minimal!r}")


@pytest.mark.parametrize("depth", [1, 2, 3, 4])
def test_exhaustive_short_state_space(depth):
    for events in itertools.product(EVENTS, repeat=depth):
        checked_trace(events, 0)


@pytest.mark.parametrize("prefix", [64, 128])
def test_generated_sequences_cross_checkpoint_boundaries(prefix):
    for events in itertools.product(EVENTS, repeat=3):
        checked_trace(events, prefix)


def test_controlled_stale_redo_shrinks_to_recorded_regression():
    def fails(events):
        try:
            run_trace(events, stale_redo=True)
        except AssertionError:
            return True
        return False

    long = [
        "snapshot",
        "title-a",
        "snapshot",
        "undo",
        "title-b",
        "snapshot",
        "redo",
        "snapshot",
    ]
    minimal = shrink_trace(long, fails)
    recorded = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"][0]
    assert minimal == recorded["events"] and fails(minimal)
    assert all(
        not fails(minimal[:index] + minimal[index + 1 :])
        for index in range(len(minimal))
    )
    good = run_trace(recorded["events"])
    assert good.state.panels[0].title == recorded["expected_title"]
    assert len(good.history) == recorded["expected_history"]


@pytest.mark.parametrize(
    "case",
    json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"],
    ids=lambda case: case["name"],
)
def test_saved_shrunk_regressions_pass_without_mutant(case):
    store = run_trace(case["events"])
    assert store.state.panels[0].title == case["expected_title"]
    assert len(store.history) == case["expected_history"]
