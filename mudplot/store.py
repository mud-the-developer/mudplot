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

    @property
    def state(self) -> FigureSpec:
        """An isolated snapshot; use actions to change the store."""
        return copy.deepcopy(self._state)

    @property
    def history(self) -> list[Action]:
        """Actions dispatched so far (in order). Enables replay / undo."""
        return copy.deepcopy(self._history)

    def dispatch(self, action: Action) -> FigureSpec:
        action = copy.deepcopy(action)
        self._state = self._reducer(self._state, action)
        self._history.append(copy.deepcopy(action))
        self._redo_stack.clear()
        for cb in tuple(self._listeners):
            cb(self.state, copy.deepcopy(action))
        return self.state

    def _replay(self) -> None:
        self._state = copy.deepcopy(self._initial)
        for action in self._history:
            self._state = self._reducer(self._state, action)

    def undo(self) -> FigureSpec:
        """Revert the last dispatched action by replaying from the start."""
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
            self.dispatch(action)
        return self.state

    def subscribe(self, listener: Listener) -> Callable[[], None]:
        self._listeners.append(listener)

        def unsubscribe() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return unsubscribe
