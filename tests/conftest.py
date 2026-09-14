"""Shared pytest fixtures."""

import shutil

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
