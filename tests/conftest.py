"""Shared pytest fixtures."""

import os
import shutil
import socket
import subprocess
import time

import pytest


def _pick_pgf_texsystem() -> None:
    """matplotlib's pgf backend defaults to ``xelatex``, which pulls in a
    much heavier TeX Live install than ``pdflatex`` just to get *any* of
    the ``needs_tex``-marked PGF-export tests running (Ubuntu's
    ``texlive-xetex`` drags in nearly the same dependency tree as
    ``texlive-latex-extra``, whereas ``texlive-latex-base`` -- providing
    ``pdflatex`` -- is comparatively small). matplotlib accepts pdflatex/
    lualatex for this rcParam just as well, so if xelatex specifically
    isn't installed but one of those is, use it instead. Runs at collection
    time (module-level code in conftest.py, not a fixture) since
    ``tests/test_references.py``'s own ``needs_tex`` skip marker is built
    from this rcParam at *import* time, before any fixture would run. This
    only ever widens which environments those tests run in -- it never
    disables a test that would otherwise run with the compiled-in default.
    """
    import matplotlib

    current = matplotlib.rcParams["pgf.texsystem"]
    if shutil.which(current) is not None:
        return
    for candidate in ("pdflatex", "xelatex", "lualatex"):
        if shutil.which(candidate) is not None:
            matplotlib.rcParams["pgf.texsystem"] = candidate
            return


_pick_pgf_texsystem()


@pytest.fixture(autouse=True)
def _close_figures():
    """Close all matplotlib figures after each test to avoid the pyplot
    'too many open figures' warning across the whole suite."""
    yield
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return
    plt.close("all")


@pytest.fixture(scope="module")
def rust_editor_server(tmp_path_factory):
    binary = os.getenv("MUDPLOT_EDITOR_BIN")
    python = os.getenv("MUDPLOT_BRIDGE_PYTHON")
    required = os.getenv("MUDPLOT_REQUIRE_BROWSER") == "1"
    if not binary or not python:
        if required:
            pytest.fail("required Rust browser binary/interpreter setup is missing")
        pytest.skip("explicit source or installed Rust browser profile not selected")
    directory = tmp_path_factory.mktemp("rust-specialized")
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    env = os.environ.copy()
    if os.getenv("MUDPLOT_BRIDGE_SOURCE_ROOT"):
        env["PYTHONPATH"] = os.environ["MUDPLOT_BRIDGE_SOURCE_ROOT"]
    else:
        env.pop("PYTHONPATH", None)
    env["MPLBACKEND"] = "Agg"
    with (directory / "server.log").open("w+") as log:
        process = subprocess.Popen(
            [binary, "--bind", f"127.0.0.1:{port}", "--python", python],
            cwd=directory,
            env=env,
            stdout=log,
            stderr=log,
        )
        try:
            deadline = time.monotonic() + 30
            while True:
                if process.poll() is not None:
                    log.seek(0)
                    pytest.fail(log.read())
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                        break
                except OSError:
                    if time.monotonic() > deadline:
                        raise
                    time.sleep(0.05)
            yield f"http://127.0.0.1:{port}", directory
        finally:
            process.terminate()
            process.wait(timeout=10)
