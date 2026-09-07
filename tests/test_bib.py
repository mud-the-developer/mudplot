"""``.bib`` -> ``ReferenceSpec`` resolution (P2-1's ``ReferenceCatalog``).

mudplot is not a bibliography manager: this only needs to cover the common
subset of BibTeX syntax real ``.bib`` files use well enough to resolve
citation/href metadata for a figure, not full grammar compliance.
"""

import mudplot as mp
import pytest

SAMPLE_BIB = r"""
% a leading line comment (outside any entry) is just ignored as stray text
@comment{a whole comment block, including @fake{nested, ...} junk, is
  skipped entirely rather than mistaken for a real entry}

@article{fischler1981,
  title = {Random sample consensus: a paradigm for model fitting},
  author = {Fischler, Martin A. and Bolles, Robert C.},
  journal = {Communications of the ACM},
  year = 1981,
  doi = {10.1145/358669.358692},
}

@book{hartley2003,
  title = "Multiple View Geometry in Computer Vision",
  author = "Hartley, R. and Zisserman, A.",
  year = {2003},
  url = {https://example.org/mvg},
}

@misc{no_link_2020,
  title = {Neither a DOI nor a URL},
  year = {2020},
}
"""


def test_from_bib_text_parses_multiple_entries():
    cat = mp.ReferenceCatalog.from_bib_text(SAMPLE_BIB)
    assert len(cat) == 3
    assert set(cat) == {"fischler1981", "hartley2003", "no_link_2020"}
    assert "fischler1981" in cat
    assert "nonexistent" not in cat


def test_comment_block_is_not_mistaken_for_an_entry():
    cat = mp.ReferenceCatalog.from_bib_text(SAMPLE_BIB)
    assert "fake" not in cat


def test_doi_resolves_to_a_doi_dot_org_href():
    ref = mp.ReferenceCatalog.from_bib_text(SAMPLE_BIB)["fischler1981"]
    assert ref.citation == "fischler1981"
    assert ref.href == "https://doi.org/10.1145/358669.358692"


def test_url_is_used_when_there_is_no_doi():
    ref = mp.ReferenceCatalog.from_bib_text(SAMPLE_BIB)["hartley2003"]
    assert ref.href == "https://example.org/mvg"


def test_neither_doi_nor_url_gives_a_citation_only_reference():
    ref = mp.ReferenceCatalog.from_bib_text(SAMPLE_BIB)["no_link_2020"]
    assert ref.citation == "no_link_2020"
    assert ref.href is None


def test_raw_exposes_every_bibtex_field():
    raw = mp.ReferenceCatalog.from_bib_text(SAMPLE_BIB).raw("hartley2003")
    assert raw["title"] == "Multiple View Geometry in Computer Vision"
    assert raw["year"] == "2003"


def test_missing_key_raises_a_clear_key_error():
    cat = mp.ReferenceCatalog.from_bib_text(SAMPLE_BIB)
    with pytest.raises(KeyError, match="fischler1981"):
        cat["nonexistent_key"]
    with pytest.raises(KeyError):
        cat.raw("nonexistent_key")


def test_nested_braces_in_a_field_value_are_preserved():
    """A common BibTeX idiom for protecting a substring's capitalisation
    (e.g. an acronym) from a citation style's case-folding.
    """
    cat = mp.ReferenceCatalog.from_bib_text(
        r"@article{x, title = {A study of {RANSAC} robustness}}"
    )
    assert cat.raw("x")["title"] == "A study of {RANSAC} robustness"


def test_multiline_field_values_have_whitespace_collapsed():
    cat = mp.ReferenceCatalog.from_bib_text(
        "@article{x,\n  title = {A title\n    spanning lines},\n}"
    )
    assert cat.raw("x")["title"] == "A title spanning lines"


def test_from_bib_reads_a_real_file(tmp_path):
    path = tmp_path / "refs.bib"
    path.write_text(SAMPLE_BIB, encoding="utf-8")
    cat = mp.ReferenceCatalog.from_bib(path)
    assert len(cat) == 3
    # a plain str path works the same as a Path
    assert len(mp.ReferenceCatalog.from_bib(str(path))) == 3


def test_reference_from_catalog_composes_with_the_fluent_api():
    """The actual end-to-end promise: a catalog entry's citation/href
    plug directly into the existing .line(citation=..., href=...) kwargs.
    """
    cat = mp.ReferenceCatalog.from_bib_text(SAMPLE_BIB)
    ref = cat["fischler1981"]
    p = mp.plot({"x": [1, 2], "y": [3, 4]}).line(
        "x", "y", label="RANSAC", citation=ref.citation, href=ref.href
    )
    assert mp.validate(p.spec) == []
    layer = p.spec.panels[0].layers[0]
    assert layer.citation == "fischler1981"
    assert layer.href == "https://doi.org/10.1145/358669.358692"


def test_empty_bib_text_gives_an_empty_catalog():
    cat = mp.ReferenceCatalog.from_bib_text("")
    assert len(cat) == 0
    assert list(cat) == []
