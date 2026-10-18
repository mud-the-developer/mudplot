"""The observation helper must not grow ctypes pointer types per sample."""

import ctypes
import os

import pytest
from scripts.check_request_body_limits import _memory, _windows_memory_bindings


@pytest.mark.skipif(os.name != "nt", reason="Windows ctypes memory observer")
def test_repeated_memory_samples_reuse_counter_type(monkeypatch):
    seen = []
    original = ctypes.POINTER

    def pointer(kind):
        seen.append(kind)
        return original(kind)

    monkeypatch.setattr(ctypes, "POINTER", pointer)
    for _ in range(20):
        result = _memory(os.getpid())
        assert result["rss_bytes"] > 0
    assert len(set(seen)) <= 1


@pytest.mark.skipif(os.name == "nt", reason="non-Windows API guard")
def test_windows_binding_factory_rejects_other_platforms_explicitly():
    with pytest.raises(OSError, match="only available on Windows"):
        _windows_memory_bindings()
