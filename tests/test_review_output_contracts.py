"""Checklist OUT-03/04: fault injection must never replace the previous output."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import pytest
from matplotlib.figure import Figure
from mudplot import io


@pytest.mark.parametrize("extension", ["json", "png", "pdf", "svg"])
@pytest.mark.parametrize("existing", ["file", "directory", "hardlink", "symlink"])
def test_unowned_staging_collision_is_never_removed_or_overwritten(
    tmp_path, monkeypatch, extension, existing
):
    destination = tmp_path / f"previous.{extension}"
    destination.write_bytes(b"previous complete output")
    external = tmp_path / "external.txt"
    external.write_bytes(b"not owned by this export")
    collision = tmp_path / f".{destination.name}.collision.tmp"
    if existing == "directory":
        collision.mkdir()
        (collision / "keep.txt").write_bytes(b"directory data")
    elif existing == "hardlink":
        try:
            collision.hardlink_to(external)
        except (OSError, NotImplementedError):
            pytest.skip("hardlink creation is not supported by this host")
    elif existing == "symlink":
        try:
            collision.symlink_to(external)
        except (OSError, NotImplementedError):
            pytest.skip("symlink creation requires host privileges")
    else:
        collision.write_bytes(b"pre-existing staging file")
    monkeypatch.setattr(io.secrets, "token_hex", lambda _length: "collision")
    plot = mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y").size(4, 3)
    figures = set(plt.get_fignums())
    with pytest.raises(OSError if existing == "directory" else FileExistsError):
        if extension == "json":
            mp.save_spec(plot.spec, destination)
        else:
            mp.save(plot.spec, destination)
    assert destination.read_bytes() == b"previous complete output"
    assert external.read_bytes() == b"not owned by this export"
    assert set(plt.get_fignums()) == figures
    if existing == "directory":
        assert (collision / "keep.txt").read_bytes() == b"directory data"
    elif existing == "hardlink":
        assert collision.read_bytes() == external.read_bytes()
        assert collision.stat().st_ino == external.stat().st_ino
    elif existing == "symlink":
        assert collision.is_symlink() and collision.resolve() == external
    else:
        assert collision.read_bytes() == b"pre-existing staging file"


@pytest.mark.parametrize("extension", ["json", "png", "pdf", "svg"])
@pytest.mark.parametrize("kind", ["missing_parent", "directory_target"])
def test_out_04_invalid_output_location_has_no_partial_output(
    tmp_path, extension, kind
):
    destination = tmp_path / "missing" / f"output.{extension}"
    protected = tmp_path / "protected.txt"
    protected.write_bytes(b"unrelated complete file")
    if kind == "directory_target":
        destination = tmp_path / f"directory.{extension}"
        destination.mkdir()
        (destination / "keep.txt").write_bytes(b"directory contents")
    figures = set(plt.get_fignums())
    plot = mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y").size(4, 3)
    with pytest.raises(OSError):
        if extension == "json":
            mp.save_spec(plot.spec, destination)
        else:
            mp.save(plot.spec, destination)
    assert protected.read_bytes() == b"unrelated complete file"
    assert not list(tmp_path.rglob("*.tmp"))
    assert set(plt.get_fignums()) == figures
    if kind == "directory_target":
        assert (destination / "keep.txt").read_bytes() == b"directory contents"
    else:
        assert not destination.parent.exists()


@pytest.mark.parametrize("extension", ["json", "png", "pdf", "svg"])
@pytest.mark.parametrize("stage", ["write", "flush_close", "sync", "replace"])
def test_out_03_atomic_failure_retains_previous_bytes_and_cleans_staging(
    tmp_path, monkeypatch, extension, stage
):
    directory = tmp_path / "한글 경로 (review)"
    directory.mkdir()
    destination = directory / f"previous.{extension}"
    destination.write_bytes(b"previous complete output")
    plot = mp.plot({"x": [1, 2, 3], "y": [1, 4, 9]}).line("x", "y").size(4, 3)
    open_figures = set(plt.get_fignums())

    if stage == "replace":

        def fail_replace(_source, _target):
            raise OSError("synthetic replace failure")

        monkeypatch.setattr(io.os, "replace", fail_replace)
    elif stage == "sync":

        def fail_sync(_descriptor):
            raise OSError("synthetic sync failure")

        monkeypatch.setattr(io.os, "fsync", fail_sync)
    elif stage == "flush_close":
        original_open = Path.open

        class FlushCloseFailure:
            def __init__(self, handle):
                self.handle = handle

            def __enter__(self):
                self.handle.__enter__()
                return self

            def fileno(self):
                return self.handle.fileno()

            def flush(self):
                raise OSError("synthetic flush_close failure")

            def __exit__(self, *_error):
                try:
                    self.flush()
                finally:
                    self.handle.close()

        def flush_failure_open(path, *args, **kwargs):
            handle = original_open(path, *args, **kwargs)
            if args and args[0] == "rb+" and path.suffix == ".tmp":
                return FlushCloseFailure(handle)
            return handle

        monkeypatch.setattr(Path, "open", flush_failure_open)
    elif extension == "json":
        original_open = Path.open

        class PartialTextWrite:
            def __init__(self, handle):
                self.handle = handle

            def __enter__(self):
                return self

            def __exit__(self, *error):
                return self.handle.__exit__(*error)

            def write(self, text):
                self.handle.write(text[: max(1, len(text) // 2)])
                raise OSError("synthetic write failure")

        def partial_open(path, *args, **kwargs):
            handle = original_open(path, *args, **kwargs)
            if args and args[0] == "w" and path.suffix == ".tmp":
                return PartialTextWrite(handle)
            return handle

        monkeypatch.setattr(Path, "open", partial_open)
    else:

        def partial_save(_figure, target, **_kwargs):
            Path(target).write_bytes(b"partial encoded data")
            raise OSError("synthetic write failure")

        monkeypatch.setattr(Figure, "savefig", partial_save)

    with pytest.raises(OSError, match=f"synthetic {stage} failure"):
        if extension == "json":
            mp.save_spec(plot.spec, destination)
        else:
            mp.save(plot.spec, destination)
    assert destination.read_bytes() == b"previous complete output"
    assert list(directory.iterdir()) == [destination]
    assert set(plt.get_fignums()) == open_figures
