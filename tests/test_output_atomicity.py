"""Failure injection for single-file writes and PGF bundle publication."""

import errno
import os
import stat
from pathlib import Path

import mudplot as mp
import pytest
from mudplot import io


@pytest.fixture
def bundle(tmp_path):
    stage = tmp_path / "stage"
    output = tmp_path / "output"
    stage.mkdir()
    output.mkdir()
    names = ["figure-img0.png", "figure-img1.png", "figure.pgf"]
    files = []
    for name in names:
        source = stage / name
        source.write_bytes(b"new " + name.encode())
        files.append(source)
    originals = {
        "figure-img0.png": b"old image",
        "figure.pgf": b"old PGF",
        "notes.txt": b"unrelated",
    }
    for name, data in originals.items():
        (output / name).write_bytes(data)
    return files, output, originals


def _assert_originals(output, originals):
    assert {p.name for p in output.iterdir()} == set(originals)
    assert all((output / name).read_bytes() == data for name, data in originals.items())


def test_bundle_success_keeps_names_and_unrelated_files(bundle):
    files, output, _ = bundle
    io._publish_bundle(files, output)
    assert all((output / p.name).read_bytes() == p.read_bytes() for p in files)
    assert (output / "notes.txt").read_bytes() == b"unrelated"
    assert not list(output.glob(".*"))


def test_bundle_backup_failure_publishes_nothing(monkeypatch, bundle):
    files, output, originals = bundle

    def fail_copy(*args, **kwargs):
        raise OSError(errno.ENOSPC, "backup disk full")

    monkeypatch.setattr(io.shutil, "copy2", fail_copy)
    with pytest.raises(OSError, match="backup disk full"):
        io._publish_bundle(files, output)
    _assert_originals(output, originals)


@pytest.mark.parametrize("use_symlinks", [False, True])
def test_bundle_publication_failure_restores_old_files_and_removes_new_ones(
    monkeypatch, bundle, use_symlinks
):
    files, output, originals = bundle
    links = []
    if use_symlinks:
        if os.name == "nt":
            pytest.skip("symlink privileges are not part of the Windows baseline")
        physical = output.parent / "physical"
        physical.mkdir()
        for name in ("figure-img0.png", "figure.pgf"):
            target = output / name
            relocated = physical / name
            target.rename(relocated)
            target.symlink_to(relocated)
            links.append(target)
    if os.name != "nt":
        for name in ("figure-img0.png", "figure.pgf"):
            (output / name).chmod(0o640)
    replace = io.os.replace

    def fail_publication(source, target):
        if Path(source).suffix == ".tmp" and Path(target).suffix == ".pgf":
            raise OSError("blocked PGF publication")
        return replace(source, target)

    monkeypatch.setattr(io.os, "replace", fail_publication)
    with pytest.raises(OSError, match="blocked PGF publication"):
        io._publish_bundle(files, output)
    _assert_originals(output, originals)
    assert all(p.is_symlink() for p in links)
    if os.name != "nt":
        assert all(
            stat.S_IMODE((output / name).stat().st_mode) == 0o640
            for name in ("figure-img0.png", "figure.pgf")
        )
        assert not list(output.parent.rglob("*.bak"))


def test_bundle_preserves_recovery_backup_when_rollback_also_fails(monkeypatch, bundle):
    files, output, originals = bundle
    replace = io.os.replace

    def fail(source, target):
        if Path(source).suffix == ".tmp" and Path(target).suffix == ".pgf":
            raise OSError("publication failure")
        if Path(source).suffix == ".bak" and Path(target).name == "figure-img0.png":
            raise OSError("recovery blocked")
        return replace(source, target)

    monkeypatch.setattr(io.os, "replace", fail)
    with pytest.raises(OSError, match="publication failure") as caught:
        io._publish_bundle(files, output)
    backups = list(output.glob("*.bak"))
    assert len(backups) == 1 and backups[0].read_bytes() == originals["figure-img0.png"]
    assert str(backups[0]) in "\n".join(caught.value.__notes__)
    assert (output / "figure.pgf").read_bytes() == originals["figure.pgf"]
    assert not (output / "figure-img1.png").exists()


def test_bundle_backup_collision_does_not_remove_the_other_entry(monkeypatch, bundle):
    files, output, originals = bundle
    monkeypatch.setattr(io.secrets, "token_hex", lambda n: "collision")
    collision = output / ".mudplot-backup-collision.bak"
    collision.write_bytes(b"another writer")
    with pytest.raises(FileExistsError):
        io._publish_bundle(files, output)
    assert collision.read_bytes() == b"another writer"
    collision.unlink()
    _assert_originals(output, originals)


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlink baseline")
def test_bundle_rejects_aliased_destinations_before_writing(bundle):
    files, output, originals = bundle
    (output / "figure-img1.png").symlink_to(output / "figure-img0.png")
    with pytest.raises(ValueError, match="distinct"):
        io._publish_bundle(files, output)
    (output / "figure-img1.png").unlink()
    _assert_originals(output, originals)


@pytest.mark.skipif(os.name == "nt", reason="POSIX file mode baseline")
@pytest.mark.parametrize("mode", [None, 0o444, 0o600, 0o640])
def test_atomic_temporary_is_private_but_final_mode_is_preserved(tmp_path, mode):
    target = tmp_path / "private.txt"
    control = tmp_path / "control.txt"
    control.write_bytes(b"")
    expected = stat.S_IMODE(control.stat().st_mode)
    if mode is not None:
        target.write_bytes(b"old")
        target.chmod(mode)
        expected = mode
    with io._atomic_destination(target) as temporary:
        assert stat.S_IMODE(temporary.stat().st_mode) == 0o600
        temporary.write_bytes(b"new")
    assert target.read_bytes() == b"new"
    assert stat.S_IMODE(target.stat().st_mode) == expected


@pytest.mark.parametrize("phase", ["backend", "references"])
def test_pgf_render_or_reference_failure_does_not_touch_old_bundle(
    monkeypatch, tmp_path, phase
):
    plt = pytest.importorskip("matplotlib.pyplot")
    from mudplot import _render as renderer

    target = tmp_path / "figure.pgf"
    image = tmp_path / "figure-img0.png"
    target.write_bytes(b"old PGF")
    image.write_bytes(b"old image")
    before = plt.get_fignums()
    monkeypatch.setattr(renderer, "_require_texsystem", lambda: None)
    monkeypatch.setattr(renderer, "render", lambda *args, **kwargs: plt.figure())

    def staged_save(fig, spec, destination, fmt, **kwargs):
        assert destination != target and destination.name == target.name
        destination.write_text("new PGF", encoding="utf-8")
        destination.with_name("figure-img0.png").write_bytes(b"new image")
        if phase == "backend":
            raise RuntimeError("backend failure")

    def substitute(*args, **kwargs):
        raise RuntimeError("reference failure")

    monkeypatch.setattr(renderer, "_save_figure", staged_save)
    monkeypatch.setattr(renderer, "_substitute_pgf_references", substitute)
    with pytest.raises(RuntimeError, match="failure"):
        renderer.save(mp.FigureSpec(), str(target))
    assert target.read_bytes() == b"old PGF" and image.read_bytes() == b"old image"
    assert plt.get_fignums() == before
    assert {p.name for p in tmp_path.iterdir()} == {target.name, image.name}


@pytest.mark.parametrize("use_symlink", [False, True])
def test_pgf_success_keeps_logical_basename_references_and_symlink(
    monkeypatch, tmp_path, use_symlink
):
    plt = pytest.importorskip("matplotlib.pyplot")
    from mudplot import _render as renderer

    if use_symlink and os.name == "nt":
        pytest.skip("POSIX symlink baseline")
    target = tmp_path / "figure.pgf"
    physical = target
    if use_symlink:
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        physical = elsewhere / "physical-name.pgf"
        target.symlink_to(physical)
    physical.write_bytes(b"old PGF")
    monkeypatch.setattr(renderer, "_require_texsystem", lambda: None)
    monkeypatch.setattr(renderer, "render", lambda *args, **kwargs: plt.figure())

    def staged_save(fig, spec, destination, fmt, **kwargs):
        assert destination.name == target.name and destination != target
        destination.write_text("figure-img0.png SENTINEL", encoding="utf-8")
        destination.with_name("figure-img0.png").write_bytes(b"new image")

    monkeypatch.setattr(renderer, "_save_figure", staged_save)
    monkeypatch.setattr(
        renderer,
        "_substitute_pgf_references",
        lambda text, *args: text.replace("SENTINEL", "citation"),
    )
    figure = renderer.save(mp.FigureSpec(), str(target))
    try:
        assert target.read_text() == "figure-img0.png citation"
        assert (tmp_path / "figure-img0.png").read_bytes() == b"new image"
        assert target.is_symlink() == use_symlink
        assert not list(tmp_path.rglob(".mudplot-pgf-*"))
    finally:
        plt.close(figure)


def test_cli_surfaces_recovery_notes_without_hiding_original_error(
    monkeypatch, tmp_path, capsys
):
    pytest.importorskip("matplotlib.pyplot")
    from mudplot import _render as renderer
    from mudplot.__main__ import main

    source = tmp_path / "input.json"
    mp.save_spec(mp.FigureSpec(), source)
    error = OSError("publication failed")
    error.add_note("Recovery backup retained at /safe/location.bak")

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(renderer, "save", fail)
    assert main(["render", str(source), str(tmp_path / "output.pgf")]) == 1
    stderr = capsys.readouterr().err
    assert "error: publication failed" in stderr
    assert "note: Recovery backup retained at /safe/location.bak" in stderr
    assert "Traceback" not in stderr


@pytest.mark.parametrize("fmt", ["png", "svg"])
def test_cli_reports_actual_extensionless_output_path(tmp_path, capsys, fmt):
    plt = pytest.importorskip("matplotlib.pyplot")
    from mudplot.__main__ import main

    spec = tmp_path / "input.json"
    mp.save_spec(mp.plot({"x": [0, 1], "y": [1, 2]}).line("x", "y").spec, spec)
    original = spec.read_bytes()
    destination = tmp_path / "figure & 한글"
    before = plt.get_fignums()
    with plt.rc_context({"savefig.format": fmt}):
        assert main(["render", str(spec), str(destination)]) == 0
    actual = destination.with_name(f"{destination.name}.{fmt}")
    assert actual.is_file() and not destination.exists()
    assert f"wrote {actual}" in capsys.readouterr().err
    assert spec.read_bytes() == original and plt.get_fignums() == before
