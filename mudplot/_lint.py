"""Figure lint / publication preflight (P2-4): a paper-figure *QA* pass,
distinct from :mod:`mudplot.validate` (which only checks structural
correctness -- "is `axis='y2'` legal on this layer type"). This checks
publication-quality *heuristics* -- "does this actually work as a
readable, greyscale/CVD-safe paper figure at its configured size" --
deliberately as non-blocking findings (ok/warning/error) an author reviews
and decides on, rather than `validate()`'s all-or-nothing raise.

This module itself needs nothing beyond the stdlib to *import* (matching
the rest of the pure engine); ``lint_figure()`` needs the colour engine
(numpy) the moment it actually runs the palette check, imported lazily
inside that one check only.
"""

from __future__ import annotations

from dataclasses import dataclass

from .spec import FigureSpec

__all__ = ["LintIssue", "LintReport", "lint_figure"]

_LEVEL_SYMBOL = {"ok": "\u2713", "warning": "\u26a0", "error": "\u2717"}


@dataclass(frozen=True)
class LintIssue:
    level: str  # "ok" | "warning" | "error"
    message: str

    def __str__(self) -> str:
        return f"{_LEVEL_SYMBOL[self.level]} {self.message}"


@dataclass(frozen=True)
class LintReport:
    issues: tuple[LintIssue, ...]

    @property
    def ok(self) -> bool:
        """No ``error``-level issues (``warning``s don't fail a report --
        they're judgment calls to review, not hard failures)."""
        return not any(i.level == "error" for i in self.issues)

    def __iter__(self):
        return iter(self.issues)

    def __len__(self) -> int:
        return len(self.issues)

    def __str__(self) -> str:
        return "\n".join(str(i) for i in self.issues)


def _series_counts(spec: FigureSpec) -> list[int]:
    """Distinct colour-cycle series per panel (reuses the exact same
    counting logic the renderer uses to size its palette, so a lint
    finding always agrees with what actually gets drawn)."""
    from ._render import _count_colors

    return [_count_colors(FigureSpec(panels=[p], data=spec.data)) for p in spec.panels]


def _legend_entry_counts(spec: FigureSpec) -> list[int]:
    counts = []
    for panel in spec.panels:
        n = 0
        for layer in panel.layers:
            if layer.group and layer.group in spec.data.columns:
                n += len({str(v) for v in spec.data.columns[layer.group]})
            elif layer.label:
                n += 1
        counts.append(n)
    return counts


def _max_group_size(spec: FigureSpec) -> int:
    sizes = [0]
    for panel in spec.panels:
        for layer in panel.layers:
            if layer.group and layer.group in spec.data.columns:
                sizes.append(len({str(v) for v in spec.data.columns[layer.group]}))
    return max(sizes)


def _check_geometry(spec: FigureSpec, journal: str | None, issues: list) -> None:
    if journal is None:
        return
    from .tex import PT_PER_INCH, TEX_PRESETS

    ctx = TEX_PRESETS.get(journal)
    if ctx is None:
        issues.append(
            LintIssue(
                "warning",
                f"no known TeX column geometry for journal {journal!r} "
                f"(known: {sorted(TEX_PRESETS)}) -- skipping width check",
            )
        )
        return
    width_in = spec.size[0]
    col_in = ctx.columnwidth_pt / PT_PER_INCH
    full_in = ctx.textwidth_pt / PT_PER_INCH
    if width_in <= col_in + 1e-9:
        issues.append(
            LintIssue(
                "ok",
                f"width fits {journal} single column "
                f"({width_in:.2f}in <= {col_in:.2f}in)",
            )
        )
    elif width_in <= full_in + 1e-9:
        issues.append(
            LintIssue(
                "ok",
                f"width fits {journal} full text width "
                f"({width_in:.2f}in <= {full_in:.2f}in), spans both columns",
            )
        )
    else:
        issues.append(
            LintIssue(
                "error",
                f"width {width_in:.2f}in exceeds {journal}'s full text width "
                f"({full_in:.2f}in)",
            )
        )


def _check_font_sizes(spec: FigureSpec, min_pt: float, issues: list) -> None:
    f = spec.theme.font
    sizes = {
        "body": f.size,
        "label": f.label_size,
        "title": f.title_size,
        "tick": f.tick_size,
    }
    too_small = {k: v for k, v in sizes.items() if v < min_pt}
    if too_small:
        detail = ", ".join(f"{k}={v:g}pt" for k, v in sorted(too_small.items()))
        issues.append(LintIssue("warning", f"text below {min_pt:g}pt: {detail}"))
    else:
        issues.append(LintIssue("ok", f"all text >= {min_pt:g}pt"))


def _check_palette(spec: FigureSpec, issues: list) -> None:
    n = max(_series_counts(spec), default=1)
    if n < 2:
        return  # nothing to distinguish -- palette safety is moot
    from .color import palette as P

    pal_spec = spec.theme.palette
    try:
        # Mirrors mudplot.theme._palette_rc()'s own construction exactly, so
        # a lint finding never disagrees with what render() actually draws.
        if pal_spec.preset:
            pal = P.preset_qualitative(pal_spec.preset, n, cvd_safe=pal_spec.cvd_safe)
        else:
            pal = P.qualitative(
                n,
                lightness=pal_spec.lightness,
                chroma=pal_spec.chroma,
                hue_start=pal_spec.hue_start,
                cvd_safe=pal_spec.cvd_safe,
            )
        report = pal.report()
    except Exception as e:  # pragma: no cover -- defensive, not expected
        issues.append(LintIssue("warning", f"could not evaluate palette safety: {e}"))
        return
    if report.get("cvd_safe"):
        issues.append(
            LintIssue("ok", f"palette passes CVD-safety threshold ({n} series)")
        )
    else:
        issues.append(
            LintIssue(
                "warning",
                f"palette does not pass the measured CVD-safety threshold for "
                f"{n} series -- see Palette.report()",
            )
        )
    if report.get("grayscale_safe"):
        issues.append(LintIssue("ok", "palette distinguishable in true greyscale"))
    else:
        issues.append(
            LintIssue("warning", "palette colours become ambiguous in true greyscale")
        )


def _check_redundant_encoding(spec: FigureSpec, issues: list) -> None:
    has_grouped = _max_group_size(spec) > 1
    if not has_grouped:
        return
    if spec.theme.redundant_encoding:
        issues.append(
            LintIssue(
                "ok",
                "grouped series have redundant marker/line-style/hatch encoding",
            )
        )
    else:
        issues.append(
            LintIssue(
                "warning",
                "grouped series rely on colour alone (theme.redundant_encoding is "
                "off) -- ambiguous for CVD viewers/greyscale print",
            )
        )


def _check_marker_style_repetition(spec: FigureSpec, issues: list) -> None:
    if not spec.theme.redundant_encoding:
        return  # already flagged by _check_redundant_encoding
    n = _max_group_size(spec)
    cycle_len = min(len(spec.theme.markers) or 1, len(spec.theme.line_styles) or 1)
    if n > cycle_len:
        issues.append(
            LintIssue(
                "warning",
                f"{n} series in one group exceeds the marker/line-style cycle "
                f"length ({cycle_len}) -- some series become ambiguous in "
                "greyscale once colour is removed",
            )
        )
    elif n > 1:
        issues.append(
            LintIssue("ok", "grouped series stay distinguishable in greyscale")
        )


def _check_legend_size(spec: FigureSpec, max_entries: int, issues: list) -> None:
    counts = _legend_entry_counts(spec)
    worst = max(counts, default=0)
    if worst == 0:
        return
    if worst > max_entries:
        issues.append(
            LintIssue(
                "warning",
                f"legend contains {worst} entries (> {max_entries}) -- consider "
                "splitting into panels or using direct labelling",
            )
        )
    else:
        issues.append(LintIssue("ok", f"legend size ({worst} entries) is reasonable"))


def _check_references(spec: FigureSpec, issues: list) -> None:
    from .validate import validate

    ref_problems = [
        p for p in validate(spec) if "citation" in p or "href" in p or "reference" in p
    ]
    if ref_problems:
        for p in ref_problems:
            issues.append(LintIssue("error", p))
    else:
        issues.append(LintIssue("ok", "citation/href metadata is well-formed"))


def lint_figure(
    spec: FigureSpec,
    *,
    journal: str | None = None,
    min_font_pt: float = 5.0,
    max_legend_entries: int = 8,
) -> LintReport:
    """Run a publication-preflight pass over ``spec``.

    Unlike :func:`mudplot.validate.validate` (structural correctness,
    all-or-nothing), this returns a mix of ``ok``/``warning``/``error``
    findings for an author to review -- most are judgment calls (a legend
    with 9 entries might be exactly right for a particular figure), not
    hard failures. ``report.ok`` is ``False`` only if an ``error``-level
    issue was found (e.g. the figure doesn't fit the named journal's page,
    or a reference field is malformed).

    ``journal`` names a preset from ``mp.capabilities()["tex_presets"]``
    (e.g. ``"ieee"``, ``"nature"``) to check the figure's configured
    physical size against; omit it to skip that one check.
    """
    issues: list[LintIssue] = []
    _check_geometry(spec, journal, issues)
    _check_font_sizes(spec, min_font_pt, issues)
    _check_palette(spec, issues)
    _check_redundant_encoding(spec, issues)
    _check_marker_style_repetition(spec, issues)
    _check_legend_size(spec, max_legend_entries, issues)
    _check_references(spec, issues)
    return LintReport(tuple(issues))
