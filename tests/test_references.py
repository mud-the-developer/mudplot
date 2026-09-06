"""Citation/href metadata on legend entries and titles.

The same spec renders differently per output format: plain text in raster
output, a clickable link in SVG, and real LaTeX macros in PGF (so the
*paper's* bibliography and hyperref resolve them at compile time).
"""

import matplotlib

matplotlib.use("Agg")

import warnings

import matplotlib.pyplot as plt
import mudplot as mp
import pytest

DOI = "https://doi.org/10.1145/358669.358692"


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
