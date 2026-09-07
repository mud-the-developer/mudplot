"""Figure lint / publication preflight (P2-4): ``p.lint(journal=...)`` ->
a mix of ok/warning/error findings for a paper author to review, distinct
from ``validate()``'s all-or-nothing structural checks.
"""

import mudplot as mp


def _levels(report) -> set[str]:
    return {i.level for i in report}


def _messages(report) -> list[str]:
    return [i.message for i in report]


def test_lint_needs_no_numpy_or_matplotlib_to_import():
    """mudplot._lint itself is part of the pure engine -- only running the
    palette check inside lint_figure() actually needs the colour engine.
    Runs in a fresh subprocess (like tests/test_no_deps.py) so the check
    isn't polluted by other tests in the same process already having
    imported numpy/matplotlib for unrelated reasons.
    """
    import subprocess
    import sys

    script = (
        "import sys\n"
        "import mudplot._lint\n"
        "assert 'numpy' not in sys.modules\n"
        "assert 'matplotlib' not in sys.modules\n"
        "print('OK')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "OK"


def test_clean_small_figure_has_no_errors():
    p = mp.plot({"x": [1, 2, 3], "y": [1, 4, 9]}).line("x", "y")
    report = p.lint()
    assert report.ok
    assert "error" not in _levels(report)


def test_oversized_figure_fails_the_journal_width_check():
    p = mp.plot({"x": [1], "y": [1]}).line("x", "y").size(10, 5)
    report = p.lint(journal="ieee")
    assert not report.ok
    assert any("exceeds" in m for m in _messages(report))


def test_figure_within_a_single_column_passes():
    p = mp.plot({"x": [1], "y": [1]}).line("x", "y").tex_size("ieee", columns=1)
    report = p.lint(journal="ieee")
    assert report.ok
    assert any("single column" in m for m in _messages(report))


def test_figure_within_full_text_width_passes():
    p = mp.plot({"x": [1], "y": [1]}).line("x", "y").tex_size("ieee", columns=2)
    report = p.lint(journal="ieee")
    assert report.ok
    assert any("full text width" in m for m in _messages(report))


def test_unknown_journal_warns_instead_of_crashing():
    p = mp.plot({"x": [1], "y": [1]}).line("x", "y")
    report = p.lint(journal="not_a_real_journal")
    assert report.ok  # a warning, not an error
    assert any("no known TeX column geometry" in m for m in _messages(report))


def test_no_journal_skips_the_geometry_check_entirely():
    p = mp.plot({"x": [1], "y": [1]}).line("x", "y")
    report = p.lint()
    assert not any("column" in m or "text width" in m for m in _messages(report))


def test_tiny_font_is_flagged_as_a_warning_not_an_error():
    p = mp.plot({"x": [1], "y": [1]}).line("x", "y").font(size=3)
    report = p.lint()
    assert report.ok
    assert any(i.level == "warning" and "3pt" in i.message for i in report)


def test_custom_min_font_pt_threshold_is_respected():
    p = mp.plot({"x": [1], "y": [1]}).line("x", "y").font(size=6)
    assert not any(i.level == "warning" for i in p.lint(min_font_pt=5))
    assert any(i.level == "warning" for i in p.lint(min_font_pt=7))


def test_grouped_series_without_redundant_encoding_warns():
    p = (
        mp.plot({"x": [1, 2, 1, 2], "y": [1, 2, 3, 4], "g": ["a", "a", "b", "b"]})
        .line("x", "y", group="g")
        .encoding(redundant_encoding=False)
    )
    report = p.lint()
    assert any("rely on colour alone" in m for m in _messages(report))


def test_grouped_series_with_redundant_encoding_is_ok():
    p = mp.plot({"x": [1, 2, 1, 2], "y": [1, 2, 3, 4], "g": ["a", "a", "b", "b"]}).line(
        "x", "y", group="g"
    )
    report = p.lint()
    assert any(i.level == "ok" and "redundant" in i.message for i in report)


def test_ungrouped_single_series_skips_the_redundant_encoding_check():
    p = mp.plot({"x": [1, 2], "y": [1, 2]}).line("x", "y")
    report = p.lint()
    assert not any("redundant" in m or "rely on colour" in m for m in _messages(report))


def test_group_larger_than_the_marker_style_cycle_warns():
    n = 10
    data = {
        "x": list(range(n)) * 2,
        "y": list(range(n)) * 2,
        "g": [f"g{i}" for i in range(n) for _ in range(2)],
    }
    p = mp.plot(data).line("x", "y", group="g")
    report = p.lint()
    assert any(
        "exceeds the marker/line-style cycle length" in m for m in _messages(report)
    )


def test_legend_size_within_the_default_threshold_is_ok():
    p = mp.plot({"x": [1], "y": [1]}).line("x", "y", label="only one")
    report = p.lint()
    assert any(i.level == "ok" and "legend size" in i.message for i in report)


def test_legend_size_over_the_default_threshold_warns():
    n = 9
    data = {
        "x": list(range(n)) * 2,
        "y": list(range(n)) * 2,
        "g": [f"g{i}" for i in range(n) for _ in range(2)],
    }
    p = mp.plot(data).line("x", "y", group="g")
    report = p.lint()
    assert any("legend contains 9 entries" in m for m in _messages(report))


def test_custom_max_legend_entries_threshold_is_respected():
    p = mp.plot({"x": [1], "y": [1]}).line("x", "y", label="one")
    assert not any(i.level == "warning" for i in p.lint(max_legend_entries=8))
    # threshold of 0 makes even a single legend entry "too many"
    assert any(i.level == "warning" for i in p.lint(max_legend_entries=0))


def test_no_labelled_layers_skips_the_legend_size_check():
    p = mp.plot({"x": [1], "y": [1]}).line("x", "y")
    report = p.lint()
    assert not any("legend" in m for m in _messages(report))


def test_malformed_citation_is_a_lint_error():
    p = mp.plot({"x": [1], "y": [1]}).line("x", "y", citation="a}bad")
    report = p.lint()
    assert not report.ok
    assert any(i.level == "error" for i in report)


def test_well_formed_reference_metadata_is_ok():
    p = mp.plot({"x": [1], "y": [1]}).line("x", "y", label="L", citation="fischler1981")
    report = p.lint()
    assert any(i.level == "ok" and "well-formed" in i.message for i in report)


def test_report_str_matches_symbol_per_level():
    p = mp.plot({"x": [1], "y": [1]}).line("x", "y").size(10, 5)
    text = str(p.lint(journal="ieee"))
    assert "\u2713" in text  # ok
    assert "\u2717" in text  # error


def test_report_is_iterable_and_sized():
    report = mp.plot({"x": [1], "y": [1]}).line("x", "y").lint()
    assert len(report) == len(list(report))
    assert len(report) > 0


def test_lint_figure_top_level_function_matches_the_fluent_method():
    p = mp.plot({"x": [1], "y": [1]}).line("x", "y")
    assert mp.lint_figure(p.spec).ok == p.lint().ok
