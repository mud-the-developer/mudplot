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


def _grouped_plot():
    return mp.plot(
        {
            "snr": [1, 2, 3, 1, 2, 3],
            "bler": [0.9, 0.5, 0.1, 0.8, 0.4, 0.2],
            "method": ["RANSAC"] * 3 + ["J-Linkage"] * 3,
        }
    ).line(
        "snr",
        "bler",
        group="method",
        references={
            "RANSAC": mp.Reference(citation="fischler_1981", href=DOI),
            "J-Linkage": mp.Reference(citation="toldo_2008"),
        },
    )


def _save(make_plot, tmp_path, name):
    path = tmp_path / name
    plt.close(mp.save(make_plot().spec, str(path)))
    return path.read_text(encoding="utf-8")


@needs_tex
def test_pgf_export_emits_figcite_and_href_macros(tmp_path):
    pgf = _save(_plot, tmp_path, "fig.pgf")
    # the paper's own \figcite/\href, not a baked-in citation number
    assert "\\figcite{fischler1981}" in pgf
    assert "\\figcite{hartley2003}" in pgf
    assert f"\\href{{{DOI}}}{{" in pgf
    # the plain label survives, and no internal marker leaks into the output
    assert "RANSAC" in pgf
    assert "\u00ab" not in pgf and "\u00bb" not in pgf


def test_svg_export_makes_the_legend_entry_a_link(tmp_path):
    svg = _save(_plot, tmp_path, "fig.svg")
    assert DOI in svg
    # SVG has no bibliography to resolve a citation key against, so the key
    # must not be dumped into the visible text
    assert "fischler1981" not in svg


def test_raster_export_keeps_labels_plain(tmp_path):
    spec = _plot().spec
    fig = mp.save(spec, str(tmp_path / "fig.png"))
    try:
        legend = fig.axes[0].get_legend()
        assert legend is not None
        labels = [t.get_text() for t in legend.get_texts()]
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


@needs_tex
def test_grouped_references_do_not_disturb_layout(tmp_path):
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        plt.close(mp.save(_grouped_plot().spec, str(tmp_path / "fig.pgf")))


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


def test_grouped_reference_round_trips_through_json():
    p = _grouped_plot()
    restored = mp.Plot.from_json(p.to_json())
    refs = restored.spec.panels[0].layers[0].references
    assert refs is not None
    assert refs["RANSAC"].citation == "fischler_1981"
    assert refs["RANSAC"].href == DOI
    assert refs["J-Linkage"].citation == "toldo_2008"
    assert refs["J-Linkage"].href is None
    assert restored.to_json() == p.to_json()


def test_group_without_a_references_entry_gets_no_decoration():
    # J-Linkage has a citation but no href -> its legend text is plain
    p = _grouped_plot()
    fig = mp.render(p.spec)
    try:
        legend = fig.axes[0].get_legend()
        assert legend is not None
        labels = [t.get_text() for t in legend.get_texts()]
    finally:
        plt.close(fig)
    assert labels == ["RANSAC", "J-Linkage"]


@pytest.mark.parametrize(
    "citation", ["fischler_1981", "han:v2v_2019", "smith-2025-ai", "deepmimo_v3"]
)
def test_realistic_bibtex_keys_pass_validation(citation):
    # underscore/colon/dash are ordinary BibTeX-key characters; only
    # macro-injection-risk characters (braces, backslash, ...) are unsafe
    p = mp.plot({"x": [1], "y": [1]}).line("x", "y", citation=citation)
    assert mp.validate(p.spec) == []


@pytest.mark.parametrize(
    "href",
    [
        "https://example.org/paper_v2?x=1&format=pdf#section_2",
        "https://doi.org/10.1145/358669.358692",
        "https://example.org/a%20b?q=1~2",
    ],
)
def test_realistic_urls_with_query_fragment_pass_validation(href):
    # hyperref reads \href{URL}{...}'s URL argument with special catcodes
    # (like \url), so ordinary URL punctuation renders correctly as-is
    p = mp.plot({"x": [1], "y": [1]}).line("x", "y", href=href)
    assert mp.validate(p.spec) == []


@needs_tex
def test_url_with_query_and_fragment_compiles_as_href(tmp_path):
    href = "https://example.org/paper_v2?x=1&format=pdf#section_2"

    def make():
        return mp.plot({"x": [1], "y": [1]}).line("x", "y", label="L", href=href)

    pgf = _save(make, tmp_path, "fig.pgf")
    assert f"\\href{{{href}}}{{" in pgf


def test_brace_and_backslash_are_still_rejected_in_citation_and_href():
    p = mp.plot({"x": [1], "y": [1]}).line(
        "x", "y", citation="a} \\input{x", href="http://x/{y}"
    )
    issues = mp.validate(p.spec)
    assert any("citation" in i for i in issues)
    assert any("href" in i for i in issues)


def test_grouped_reference_entries_are_validated_too():
    p = mp.plot({"x": [1, 2], "y": [1, 2], "g": ["a", "b"]}).line(
        "x", "y", group="g", references={"a": mp.Reference(citation="a}bad")}
    )
    issues = mp.validate(p.spec)
    assert any("reference['a']" in i for i in issues)


def test_backend_capabilities_are_exposed():
    caps = mp.capabilities()["backends"]
    assert caps["pgf"] == {
        "vector": True,
        "citations": True,
        "hyperlinks": True,
        "requires_tex": True,
    }
    assert caps["png"]["citations"] is False
    assert caps["svg"]["hyperlinks"] is True
    assert caps["svg"]["citations"] is False


def test_pgf_export_without_tex_explains_itself(tmp_path, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    with pytest.raises(RuntimeError, match="needs a TeX installation"):
        mp.save(_plot().spec, str(tmp_path / "fig.pgf"))


# -- citation measurement policy (P0-3) --------------------------------------
#
# matplotlib lays a figure out *before* the document's own bibliography
# resolves \figcite{key}, so a compact numeric citation ("[12]") and an
# author-year one ("(Fischler and Bolles, 1981)") are measured identically
# by default -- WYSIWYG is only exact for the compact case.
# reference_style(measure_text=...) opts into measuring against a realistic
# example of the actual style instead.


def _legend_width(p):
    fig = mp.render(p.spec, fmt="pgf")
    try:
        fig.canvas.draw()
        legend = fig.axes[0].get_legend()
        assert legend is not None
        return legend.get_window_extent().width
    finally:
        plt.close(fig)


def test_reference_style_measure_text_widens_the_measured_legend():
    base = _plot()
    default_width = _legend_width(base)
    styled_width = _legend_width(
        base.reference_style(measure_text="(Fischler and Bolles, 1981)")
    )
    assert styled_width > default_width


def test_reference_style_measure_text_never_leaks_into_pgf_output(tmp_path):
    measure_text = "(Fischler and Bolles, 1981)"
    p = _plot().reference_style(measure_text=measure_text)
    assert mp.validate(p.spec) == []
    pgf = _save(lambda: p, tmp_path, "fig.pgf")
    assert "\\figcite{fischler1981}" in pgf
    assert "Fischler and Bolles" not in pgf
    assert "\u00ab" not in pgf and "\u00bb" not in pgf


def test_reference_style_none_restores_the_compact_default():
    p = _plot().reference_style(measure_text="(long author-year style)")
    restored = p.reference_style(measure_text=None)
    assert restored.spec.reference_measure_text is None
    assert _legend_width(restored) == _legend_width(_plot())


def test_reference_style_measure_text_rejects_pgf_escaped_characters():
    p = _plot().reference_style(measure_text="a}bad\\input{x")
    issues = mp.validate(p.spec)
    assert any("reference_measure_text" in i for i in issues)


def test_reference_style_round_trips_through_json():
    p = _plot().reference_style(measure_text="(Author, Year)")
    restored = mp.Plot.from_json(p.to_json())
    assert restored.spec.reference_measure_text == "(Author, Year)"


def test_measure_text_does_not_widen_a_wrapping_title_citation(tmp_path):
    """Regression: a long title (wrap=True) can split across several .pgf
    text blocks, so a measurement filler applied there can end up separated
    from its sentinel -- which would leak it into the final output instead
    of being stripped. ``_plot()`` already has both a legend citation and a
    ``.title_reference(citation="hartley2003")``; this is the one that
    previously broke when reference_style's filler wasn't title-scoped.
    """
    measure_text = "(Fischler and Bolles, 1981)"
    p = _plot().reference_style(measure_text=measure_text)
    pgf = _save(lambda: p, tmp_path, "fig.pgf")
    assert "\\figcite{fischler1981}" in pgf
    assert "\\figcite{hartley2003}" in pgf
    assert measure_text not in pgf
    assert "Fischler and Bolles" not in pgf


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
