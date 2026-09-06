"""Citation/href metadata on legend entries and titles.

The same spec renders differently per output format: plain text in raster
output, a clickable link in SVG, and real LaTeX macros in PGF (so the
*paper's* bibliography and hyperref resolve them at compile time).
"""

import matplotlib

matplotlib.use("Agg")

import shutil
import subprocess
import warnings

import matplotlib.pyplot as plt
import mudplot as mp
import pytest

DOI = "https://doi.org/10.1145/358669.358692"

# matplotlib's pgf backend measures text by running a real TeX engine, so
# .pgf export (unlike every other format) needs one installed.
needs_tex = pytest.mark.skipif(
    shutil.which(matplotlib.rcParams["pgf.texsystem"]) is None,
    reason="no TeX installation for .pgf export",
)


def _plot():
    return (
        mp.plot({"x": [1, 2, 3], "y": [1, 4, 9]})
        .line("x", "y", label="RANSAC", citation="fischler1981", href=DOI)
        .labels(title="Robust fitting")
        .title_reference(citation="hartley2003")
    )


def _save(tmp_path, name):
    path = tmp_path / name
    plt.close(mp.save(_plot().spec, str(path)))
    return path.read_text(encoding="utf-8")


@needs_tex
def test_pgf_export_emits_figcite_and_href_macros(tmp_path):
    pgf = _save(tmp_path, "fig.pgf")
    # the paper's own \figcite/\href, not a baked-in citation number
    assert "\\figcite{fischler1981}" in pgf
    assert "\\figcite{hartley2003}" in pgf
    assert f"\\href{{{DOI}}}{{" in pgf
    # the plain label survives, and no internal marker leaks into the output
    assert "RANSAC" in pgf
    assert "\u00ab" not in pgf and "\u00bb" not in pgf


def test_svg_export_makes_the_legend_entry_a_link(tmp_path):
    svg = _save(tmp_path, "fig.svg")
    assert DOI in svg
    # SVG has no bibliography to resolve a citation key against, so the key
    # must not be dumped into the visible text
    assert "fischler1981" not in svg


def test_raster_export_keeps_labels_plain(tmp_path):
    spec = _plot().spec
    fig = mp.save(spec, str(tmp_path / "fig.png"))
    try:
        labels = [t.get_text() for t in fig.axes[0].get_legend().get_texts()]
    finally:
        plt.close(fig)
    assert labels == ["RANSAC"]


@needs_tex
def test_references_do_not_disturb_layout(tmp_path):
    """The markers sit in the text matplotlib measures while laying out, so
    an over-long one silently wrecks the figure (a full URL collapsed the
    axes to zero size) -- a regression invisible in the file contents.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        plt.close(mp.save(_plot().spec, str(tmp_path / "fig.pgf")))


def test_reference_metadata_round_trips_through_json():
    p = _plot()
    restored = mp.Plot.from_json(p.to_json())
    layer = restored.spec.panels[0].layers[0]
    assert (layer.citation, layer.href) == ("fischler1981", DOI)
    panel = restored.spec.panels[0]
    assert (panel.title_citation, panel.title_href) == ("hartley2003", None)


def test_tex_unsafe_reference_metadata_is_rejected():
    # substituted into .pgf source verbatim -> a trust boundary
    p = mp.plot({"x": [1], "y": [1]}).line(
        "x", "y", label="L", citation="a} \\input{/etc/passwd"
    )
    issues = mp.validate(p.spec)
    assert any("citation" in i for i in issues)
    with pytest.raises(ValueError):
        mp.render(p.spec)


def test_pgf_export_without_tex_explains_itself(tmp_path, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    with pytest.raises(RuntimeError, match="needs a TeX installation"):
        mp.save(_plot().spec, str(tmp_path / "fig.pgf"))


needs_tectonic = pytest.mark.skipif(
    shutil.which("tectonic") is None or shutil.which("gs") is None,
    reason="needs tectonic (compile) and ghostscript (read the result back)",
)

PAPER_TEX = r"""\documentclass[10pt]{article}
\usepackage{pgf}
\input{preamble.tex}
\begin{document}
Robust estimation is standard practice.
\begin{figure}\centering
\input{fig.pgf}
\caption{Errors of two estimators.}
\end{figure}
\bibliographystyle{plain}
\bibliography{refs}
\end{document}
"""

REFS_BIB = """@article{fischler1981, title={Random sample consensus},
  author={Fischler, M and Bolles, R}, journal={CACM}, year={1981}}
@book{hartley2003, title={Multiple View Geometry},
  author={Hartley, R and Zisserman, A}, year={2003}}
"""


@needs_tex
@needs_tectonic
def test_exported_pgf_compiles_into_a_real_paper(tmp_path):
    """The end-to-end claim: a .pgf figure's citations resolve against the
    *document's* bibliography, producing real numbers in the final PDF.

    Generating the .pgf needs a TeX engine (matplotlib measures text with
    it); compiling the paper is done with tectonic, which fetches whatever
    packages it needs on its own.
    """
    plt.close(mp.save(_plot().spec, str(tmp_path / "fig.pgf")))
    (tmp_path / "preamble.tex").write_text(mp.PREAMBLE, encoding="utf-8")
    (tmp_path / "paper.tex").write_text(PAPER_TEX, encoding="utf-8")
    (tmp_path / "refs.bib").write_text(REFS_BIB, encoding="utf-8")

    proc = subprocess.run(
        ["tectonic", "--keep-intermediates", "--print", "paper.tex"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert proc.returncode == 0, proc.stderr[-3000:]
    assert "Citation" not in proc.stderr or "undefined" not in proc.stderr

    text = _pdf_text(tmp_path / "paper.pdf")
    # the numbers inside the figure are assigned by the document, and are the
    # same ones its References list uses
    assert "RANSAC [1]" in text
    assert "Robust fitting [2]" in text
    assert "[1] M Fischler" in text and "[2] R Hartley" in text


def _pdf_text(pdf) -> str:
    """Text of a compiled PDF, whitespace-normalised (ghostscript ships with
    every TeX install, so no extra tooling)."""
    proc = subprocess.run(
        [
            "gs",
            "-q",
            "-dNOPAUSE",
            "-dBATCH",
            "-sDEVICE=txtwrite",
            "-sOutputFile=-",
            str(pdf),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return " ".join(proc.stdout.split())
