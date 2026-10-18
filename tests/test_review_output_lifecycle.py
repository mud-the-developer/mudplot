"""OUT-04/05: controlled output failures and returned Figure ownership."""

import ctypes
import errno
import os
import stat
import weakref
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import pytest
from matplotlib.figure import Figure


def plot():
    return mp.plot({"x": [1, 2, 3], "y": [2, 1, 3]}).line("x", "y").size(4, 3)


def save(spec, path, extension):
    if extension == "json":
        mp.save_spec(spec, path)
    else:
        return mp.save(spec, str(path))


@pytest.mark.parametrize("extension", ["json", "png", "pdf", "svg"])
@pytest.mark.parametrize("failure", ["read_only", "locked"])
@pytest.mark.skipif(os.name != "nt", reason="Windows readonly/deny-delete boundary")
def test_windows_readonly_or_locked_target_retains_old_bytes(
    tmp_path, extension, failure
):
    if os.name != "nt":
        pytest.skip("Windows API boundary")
    from ctypes import wintypes

    target = tmp_path / f"previous.{extension}"
    target.write_bytes(b"previous complete output")
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
    handle = None
    if failure == "locked":
        handle = kernel.CreateFileW(str(target), 0x80000000, 3, None, 3, 0, None)
        assert handle != ctypes.c_void_p(-1).value
    else:
        target.chmod(stat.S_IREAD)
    figures = set(plt.get_fignums())
    try:
        with pytest.raises(PermissionError):
            save(plot().spec, target, extension)
        assert target.read_bytes() == b"previous complete output"
        assert not list(tmp_path.glob("*.tmp"))
        assert set(plt.get_fignums()) == figures
    finally:
        if handle is not None:
            assert kernel.CloseHandle(handle)
        target.chmod(stat.S_IWRITE | stat.S_IREAD)


@pytest.mark.parametrize("extension", ["json", "png", "pdf", "svg"])
def test_synthetic_disk_full_retains_previous_output_and_reports_cause(
    tmp_path, monkeypatch, extension
):
    target = tmp_path / f"previous.{extension}"
    target.write_bytes(b"previous complete output")
    figures = set(plt.get_fignums())

    def full(*args, **kwargs):
        raise OSError(errno.ENOSPC, "synthetic disk full")

    if extension == "json":
        original_open = Path.open

        def open_file(path, *args, **kwargs):
            if path.suffix == ".tmp" and args and args[0] == "w":
                full()
            return original_open(path, *args, **kwargs)

        monkeypatch.setattr(Path, "open", open_file)
    else:
        monkeypatch.setattr(Figure, "savefig", full)
    with pytest.raises(OSError) as caught:
        save(plot().spec, target, extension)
    assert caught.value.errno == errno.ENOSPC
    assert target.read_bytes() == b"previous complete output" and not list(
        tmp_path.glob("*.tmp")
    )
    assert set(plt.get_fignums()) == figures


def test_unsupported_extension_fails_without_touching_destination(tmp_path):
    target = tmp_path / "previous.unsupported"
    target.write_bytes(b"previous complete output")
    figures = set(plt.get_fignums())
    with pytest.raises(ValueError, match=r"format|extension"):
        mp.save(plot().spec, str(target))
    assert (
        target.read_bytes() == b"previous complete output"
        and set(plt.get_fignums()) == figures
    )


@pytest.mark.parametrize("extension", [None, "png", "pdf", "svg"])
def test_returned_figures_are_open_until_caller_closes_and_failure_is_clean(
    tmp_path, extension
):
    p = plot()
    baseline = set(plt.get_fignums())
    refs = []
    for index in range(5):
        fig = (
            mp.render(p.spec)
            if extension is None
            else mp.save(p.spec, str(tmp_path / f"{index}.{extension}"))
        )
        assert fig.number in plt.get_fignums() and isinstance(fig, Figure)
        refs.append(weakref.ref(fig))
        plt.close(fig)
        assert set(plt.get_fignums()) == baseline
    del fig
    import gc

    gc.collect()
    assert all(ref() is None for ref in refs)
    bad = p.spec
    bad.panels[0].layers[0].color = "invalid lifecycle colour"
    with pytest.raises(ValueError):
        mp.render(bad)
    assert set(plt.get_fignums()) == baseline
