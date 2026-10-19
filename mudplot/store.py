"""Store: the imperative shell that drives the pure reducer.

Holds the current state, applies actions through the reducer, and notifies
subscribers. Kept tiny and free of rendering/IO so both the Python API and a
future dashboard can reuse it.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Iterable

from .actions import Action
from .reducer import reduce
from .spec import FigureSpec

__all__ = ["Store"]

Listener = Callable[[FigureSpec, "Action | None"], None]


class Store:
    """Action history around mutable specs, isolated by defensive copies.

    Snapshot safety is deliberate, but copying scales with the full spec,
    including inline data. This is an editor state store, not a streaming data
    pipeline. The default pure reducer retains one preceding 64-action state
    to shorten near-tail replay, without dropping history. Custom reducers
    keep full replay and their existing call semantics.
    """

    def __init__(self, state: FigureSpec | None = None, *, reducer=reduce):
        # Defensive deep copy: without this, a caller mutating the
        # FigureSpec object they originally passed in would silently leak
        # that mutation into the store's "pure" state -- e.g. before any
        # dispatch() at all -- breaking the no-hidden-mutable-state guarantee
        # the rest of the engine (and its docs) rely on.
        self._initial = copy.deepcopy(state) if state is not None else FigureSpec()
        self._state = copy.deepcopy(self._initial)
        self._reducer = reducer
        self._listeners: list[Listener] = []
        self._history: list[Action] = []
        self._redo_stack: list[Action] = []
        self._checkpoint: tuple[int, FigureSpec] | None = None

    @property
    def state(self) -> FigureSpec:
        """An isolated snapshot; use actions to change the store."""
        return copy.deepcopy(self._state)

    @property
    def history(self) -> list[Action]:
        """Actions dispatched so far (in order). Enables replay / undo."""
        return copy.deepcopy(self._history)

    def _dispatch(self, action: Action) -> None:
        """Internal dispatch that skips only the public return snapshot."""
        action = copy.deepcopy(action)
        cursor, previous = len(self._history), self._state
        self._state = self._reducer(self._state, action)
        self._history.append(action)
        self._redo_stack.clear()
        if self._reducer is reduce:
            if self._checkpoint is not None and self._checkpoint[0] > cursor:
                self._checkpoint = None
            # Keep one prior pure-reducer state, never a cache of every snapshot.
            if cursor and cursor % 64 == 0:
                self._checkpoint = (cursor, previous)
        for cb in tuple(self._listeners):
            cb(self.state, copy.deepcopy(action))

    def dispatch(self, action: Action) -> FigureSpec:
        self._dispatch(action)
        return self.state

    def _replay(self) -> None:
        cursor, initial = 0, self._initial
        if (
            self._reducer is reduce
            and self._checkpoint is not None
            and self._checkpoint[0] <= len(self._history)
        ):
            cursor, initial = self._checkpoint
        self._state = copy.deepcopy(initial)
        for action in self._history[cursor:]:
            self._state = self._reducer(self._state, action)

    def undo(self) -> FigureSpec:
        """Revert the last action by replaying the retained history prefix."""
        if not self._history:
            return self.state
        self._redo_stack.append(self._history.pop())
        self._replay()
        for cb in tuple(self._listeners):
            cb(self.state, None)
        return self.state

    def redo(self) -> FigureSpec:
        """Re-apply the most recently undone action."""
        if not self._redo_stack:
            return self.state
        self._history.append(self._redo_stack.pop())
        self._replay()
        for cb in tuple(self._listeners):
            cb(self.state, None)
        return self.state

    def dispatch_all(self, actions: Iterable[Action]) -> FigureSpec:
        for action in actions:
            self._dispatch(action)
        return self.state

    def subscribe(self, listener: Listener) -> Callable[[], None]:
        self._listeners.append(listener)

        def unsubscribe() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return unsubscribe
