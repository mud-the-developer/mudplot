# Publication figures

Prepare physical size and figure references, then check the output at its actual publication size. For opt-in composition, see [scientific composition and QA](SCIENTIFIC_QUALITY.md).

## TeX WYSIWYG preview

```python
# Preview at the exact size/font it will have in the paper (mock text
# column + caption)
fig = (mp.plot(data).line("voltage", "current", group="order")
         .labels(x="Voltage (mV)", y="Current")
         .preview(tex="ieee", caption="Figure 1. ..."))
```

## Sizing the actual figure for a one- or two-column layout

`.tex_size(...)` applies the same column-width/font sizing as `.preview()`,
but to the figure you actually `.render()`/`.save()` — not just a mock
preview. Every layer (long titles, outside legends) is then laid out to fit
that exact size without clipping or overlap (see "Layout" below).

```python
p.tex_size("ieee", columns=1)   # a single column's width
p.tex_size("nature", columns=2) # spans the full text width (figure*)
```

## Layout: no clipped or overlapping text, at the exact configured size

`render()`/`save()` never crop or rescale the figure to fit its content —
the physical size you set (directly, via `.size()`, or via `.tex_size()`) is
what you get, which matters for TeX placement. Instead, before returning the
figure it:

- wraps titles/suptitle that would otherwise overflow the figure width
  (matplotlib's native text wrapping, measured against the real renderer —
  not a hand-rolled estimate);
- reserves exact canvas space for a named `"outside ..."` legend location so
  it's fully visible, never overlapping the axes or clipped at the edge.

An explicit `bbox_to_anchor=[x, y]` (see below) is trusted as-is and isn't
auto-adjusted, since overlapping the plot may be a deliberate placement
choice. This uses matplotlib's own layout engine and text-measurement
renderer throughout (no custom layout system) and is a no-op for figures
that already fit — font sizes stay exactly as configured unless something
would otherwise be clipped. 3-D panels fall back to `tight_layout()` for now
since matplotlib's constrained layout doesn't support 3-D Axes well.

## Citations and links inside the figure (LaTeX-native)

A legend entry or panel title can carry a BibTeX key and/or a URL. Nothing
is baked into the image: the *paper* resolves it at compile time, so the
number in the figure is the same `[1]` as in its References list.

```python
(mp.plot(data)
    .line("x", "y", label="RANSAC",
          citation="fischler1981",             # BibTeX key
          href="https://doi.org/10.1145/358669.358692")
    .labels(title="Robust fitting")
    .title_reference(citation="hartley2003")
    .tex_size("ieee", columns=1)
    .save("fig.pgf"))                          # .pgf -> LaTeX-native export
```

```latex
\input{preamble.tex}   % or paste mudplot.PREAMBLE once
\begin{figure}\centering
  \input{fig.pgf}
  \caption{Errors of two estimators.}
\end{figure}
```

The export emits `\figcite{fischler1981}`, not `\cite{...}` directly, so the
document decides what a figure citation means:

```latex
\providecommand{\figcite}[1]{\cite{#1}}   % mudplot.PREAMBLE; \citep, \autocite, ...
```

Each backend does what it can with the same spec:

| format | citation | href |
| --- | --- | --- |
| `.pgf` | `\figcite{key}` — numbered by the paper's bibliography | `\href{url}{...}` via hyperref |
| `.svg` | dropped (nothing to resolve against) | the text becomes a clickable link |
| `.png`/`.pdf` | dropped | dropped |

Metadata is substituted into LaTeX source verbatim, so `validate()` rejects
braces/backslashes in these two fields. Links must be absolute `http`, `https`,
or `mailto` URIs; active/file/data/custom schemes, relative links, controls,
and whitespace are rejected before SVG/PGF export. Ordinary URL punctuation
like `_`/`:`/`-`/`&`/`#`/`%` remains valid.

A `group=`-ed layer can cite a *different* paper per series via
`references=` (a `{group_value: mp.Reference(...)}` dict); a group value
not in the dict gets no citation/link:

```python
(mp.plot(data).line("snr", "bler", group="method", references={
    "RANSAC": mp.Reference(citation="fischler1981", href="https://doi.org/..."),
    "J-Linkage": mp.Reference(citation="toldo2008"),
}))
```

Pull citation/href straight out of an existing `.bib` file instead of typing
keys/URLs by hand with `mp.ReferenceCatalog` (a minimal, dependency-free
reader for the common BibTeX subset real `.bib` files use -- not a full
bibliography manager):

```python
refs = mp.ReferenceCatalog.from_bib("references.bib")
ref = refs["fischler1981"]   # -> ReferenceSpec(citation=..., href=...)
# href is resolved (offline, no network access) via mp.resolve_reference_href:
# a doi field (bare, "doi:"-prefixed, or a full doi.org URL -- all normalised
# the same way) -> https://doi.org/...; else an arXiv id (eprint +
# archiveprefix/eprinttype == "arxiv", the shape arXiv's own "export bibtex"
# produces) -> https://arxiv.org/abs/...; else a plain url field; else None.
p.line("x", "y", label="RANSAC", citation=ref.citation, href=ref.href)
```

By default, PGF layout is measured against a compact numeric citation style
(`"[12]"`); pass `.reference_style(measure_text="(Author, Year)")` if your
bibliography style is longer (e.g. author-year), so legend sizing predicts
the final compiled width instead of assuming the compact default.

## Placing the legend, title, or an annotation at an exact spot

```python
p.legend(bbox_to_anchor=[0.8, 0.5])   # figure-fraction [x, y], overrides location
p.legend(location="upper left")       # bbox_to_anchor=None restores named locations
p.title_position([0.1, 0.85])         # axes-fraction [x, y]; None restores default
p.set_layer_at(layer_index, [3, 0.5]) # move a text/annotate layer (data coords)
```

This is also what the interactive editor's draggable handles use (mouse or
arrow keys, right on the preview) — see [dashboard documentation](../dashboard/README.md).

## Figure lint / publication preflight

`validate()` only checks structural correctness ("is `axis='y2'` legal
here"); `.lint()` checks publication-quality *heuristics* instead — does
this actually work as a readable, greyscale/CVD-safe paper figure at its
configured size — as non-blocking findings to review, not hard failures:

```python
report = p.lint(journal="ieee")
print(report)
# ✓ width fits ieee single column (3.49in <= 3.49in)
# ✓ dpi (300) meets ieee recommendation (300 DPI)
# ✓ all text >= 6pt
# ⚠ palette does not pass the measured CVD-safety threshold for 9 series -- see Palette.report()
# ⚠ palette colours become ambiguous in true greyscale
# ✓ grouped series have redundant marker/line-style/hatch encoding
# ⚠ 9 series in one group exceeds the marker/line-style cycle length (4) -- ...
# ⚠ legend contains 9 entries (> 8) -- consider splitting into panels or using direct labelling
# ✓ citation/href metadata is well-formed

report.ok   # False only if an error-level finding exists (e.g. doesn't fit the page)
```

Checks: page-width fit and raster DPI against the named journal's profile,
minimum text size, palette CVD/greyscale safety (reusing `Palette.report()`),
redundant encoding for grouped series, marker/line-style cycle exhaustion,
legend size, and reference-metadata validity. Thresholds default to the
journal's own profile (see below) and can be overridden per call
(`min_font_pt=`, `max_legend_entries=`). Omitting `journal=` picks it up from
`.journal(...)` if you already set it. `mp.lint_figure(spec, ...)` is the
side-effect-free/agent-facing equivalent, needing only the `color` extra (numpy) — no
matplotlib required, since nothing is actually rendered.

## Journal profiles (publication constraints, not just a style sheet)

Each supported journal is one `JournalProfile` bundling its *style* (fonts,
line widths, conventional figure size), its *TeX geometry* (column/text
width, column count), and its *preflight constraints* (minimum font size,
recommended raster DPI, legend budget, greyscale policy) — so `.journal()`,
`.tex_size()`, and `.lint()` all agree on one definition instead of three
separate lookups:

```python
mp.AVAILABLE_JOURNALS          # ('nature', 'ieee', 'acm', 'revtex')
prof = mp.get_journal_profile("acm")
prof.columnwidth_pt            # 241.0
prof.min_font_pt               # 6.0
prof.recommended_dpi           # 300

# a profile object works anywhere a journal name does
p.journal(prof).tex_size(prof, columns=1).lint(journal=prof)
```

`mp.capabilities()["journal_profiles"]` exposes all of it as plain JSON for
agents.

## Using palettes directly

```python
pal = mp.color_palette(5, "qualitative")   # lightness jitter + hue contrast
print(pal.hex, pal.min_delta_e())
print(pal.report())      # includes final HEX metrics and explicit evaluation conditions
cmap = mp.color_palette(256, "sequential").to_cmap()

# Named, pre-verified presets (measured CVD-safe + true-greyscale-safe up to
# a documented category count -- see mp.capabilities()["palette_presets"]):
pal = mp.color_palette(6, "qualitative", preset="paper")   # or "vivid" / "soft"
p = mp.plot(data).line("x", "y", group="g").palette(preset="paper")

# Bar/box/violin fills also cycle a hatch pattern per group by default
# (ThemeSpec.hatches). Patterns repeat after their finite cycle; inspect the
# actual print size rather than treating colour/hatch count as a guarantee.
p2 = mp.plot(data).bar("category", "value", group="g")  # colour + hatch
p3 = p2.encoding(redundant_encoding=False)               # colour only
```

`Palette.report()` measures exported **8-bit HEX sRGB**, including quantization;
its `evaluation` records normal vision, selected CVD types, Machado 2009 full
severity, and existing ΔE00 ≥ 8 / L* gap ≥ 3 thresholds. The float `srgb` metric
methods can differ slightly. These are measured flags, not accessibility/print
certification; outside the preset's pre-verified count, inspect a fresh report.
`hue_start` seeds deterministic sampling; there is no random-seed option.
