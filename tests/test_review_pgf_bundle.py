"""OUT-06: PGF sidecars are relocatable together, not a transactional bundle."""

import shutil
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import pytest

needs_tex = pytest.mark.skipif(
    shutil.which(matplotlib.rcParams["pgf.texsystem"]) is None
    or shutil.which("pdflatex") is None,
    reason="PGF generation and pdflatex bundle check need installed TeX",
)


def heatmap():
    return mp.plot({}).matrix("m", [[1, 2], [3, 4]]).heatmap("m").size(4, 3)


def compile_paper(directory: Path):
    (directory / "paper.tex").write_text(
        r"\documentclass{article}\usepackage{pgf}\begin{document}"
        r"\input{figure.pgf}\end{document}",
        encoding="utf-8",
    )
    return subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "paper.tex"],
        cwd=directory,
        capture_output=True,
        timeout=45,
    )


@needs_tex
def test_pgf_relative_sidecars_move_together_and_missing_sidecar_fails(tmp_path):
    source, moved, missing = (
        tmp_path / name for name in ("source", "moved", "missing")
    )
    for directory in (source, moved, missing):
        directory.mkdir()
    path = source / "figure.pgf"
    plt.close(heatmap().save(str(path)))
    images = sorted(source.glob("figure-img*.png"))
    assert images
    pgf = path.read_text(encoding="utf-8")
    assert all(image.name in pgf for image in images)
    assert str(source) not in pgf
    for artifact in [path, *images]:
        shutil.copyfile(artifact, moved / artifact.name)
    shutil.copyfile(path, missing / path.name)
    success = compile_paper(moved)
    assert success.returncode == 0, success.stdout.decode("utf-8", errors="replace")[
        -2000:
    ]
    assert (moved / "paper.pdf").read_bytes().startswith(b"%PDF")
    failure = compile_paper(missing)
    assert failure.returncode != 0
    assert b"figure-img" in failure.stdout
    assert all(image.is_file() for image in images)


@needs_tex
def test_pgf_postprocess_failure_closes_figure_but_is_not_atomic(tmp_path, monkeypatch):
    from mudplot import _render

    path = tmp_path / "figure.pgf"
    path.write_bytes(b"previous user PGF")
    figures = set(plt.get_fignums())

    def fail(*_args):
        raise OSError("synthetic PGF postprocess failure")

    monkeypatch.setattr(_render, "_substitute_pgf_references", fail)
    with pytest.raises(OSError, match="synthetic PGF"):
        heatmap().save(str(path))
    assert set(plt.get_fignums()) == figures
    assert sorted(tmp_path.glob("figure-img*.png"))
    assert path.read_bytes() != b"previous user PGF"
