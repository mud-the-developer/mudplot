"""OUT-04: actual Windows sharing locks, limited to synthetic temporary files."""

from __future__ import annotations

import ctypes
import os
from ctypes import wintypes

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import pytest
from mudplot import io


@pytest.mark.skipif(os.name != "nt", reason="Windows read-only attribute semantics")
@pytest.mark.parametrize("extension", ["json", "png", "pdf", "svg"])
def test_out_04_read_only_target_does_not_leave_read_only_staging(tmp_path, extension):
    destination = tmp_path / f"readonly.{extension}"
    destination.write_bytes(b"previous complete output")
    destination.chmod(0o444)
    original_mode = destination.stat().st_mode
    figures = set(plt.get_fignums())
    plot = mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y").size(4, 3)
    try:
        with pytest.raises(PermissionError):
            if extension == "json":
                mp.save_spec(plot.spec, destination)
            else:
                mp.save(plot.spec, destination)
        assert destination.read_bytes() == b"previous complete output"
        assert destination.stat().st_mode == original_mode
        assert list(tmp_path.iterdir()) == [destination]
        assert set(plt.get_fignums()) == figures
    finally:
        for path in tmp_path.iterdir():
            path.chmod(0o666)
            if path != destination:
                path.unlink()


@pytest.mark.skipif(os.name != "nt", reason="Win32 file sharing semantics only")
@pytest.mark.parametrize("extension", ["json", "png", "pdf", "svg"])
def test_out_04_windows_delete_sharing_lock_preserves_previous_file(
    tmp_path, monkeypatch, extension
):
    destination = tmp_path / f"한글 잠금 (review).{extension}"
    destination.write_bytes(b"previous complete output")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.CreateFileW(str(destination), 0x80000000, 0x1, None, 3, 0x80, None)
    assert handle != ctypes.c_void_p(-1).value, ctypes.get_last_error()
    figures = set(plt.get_fignums())
    attempted = []
    replace = io.os.replace

    def observed_replace(source, target):
        attempted.append((source, target))
        return replace(source, target)

    monkeypatch.setattr(io.os, "replace", observed_replace)
    plot = mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y").size(4, 3)
    try:
        with pytest.raises(PermissionError):
            if extension == "json":
                mp.save_spec(plot.spec, destination)
            else:
                mp.save(plot.spec, destination)
        assert len(attempted) == 1
        assert destination.read_bytes() == b"previous complete output"
        assert list(tmp_path.iterdir()) == [destination]
        assert set(plt.get_fignums()) == figures
    finally:
        assert kernel.CloseHandle(handle)
    if extension == "json":
        mp.save_spec(plot.spec, destination)
        assert mp.load_spec(destination) == plot.spec
    else:
        plt.close(mp.save(plot.spec, destination))
        assert destination.read_bytes() != b"previous complete output"
