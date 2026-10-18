"""The observation helper must not grow ctypes pointer types per sample."""

import ctypes
import os

import pytest
from scripts.check_request_body_limits import _memory


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
