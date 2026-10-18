"""Serialize owned Matplotlib effects without importing optional render packages."""

from collections.abc import Iterator
from contextlib import contextmanager
from threading import RLock

_LOCK = RLock()


@contextmanager
def matplotlib_context() -> Iterator[None]:
    with _LOCK:
        yield
