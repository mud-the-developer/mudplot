# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Figure lint / publication preflight (P2-4)
- `p.lint(journal=None, *, min_font_pt=5.0, max_legend_entries=8)` /
  `mp.lint_figure(spec, ...)`: publication-quality *heuristics* distinct
  from `validate()`'s structural correctness -- does this actually work
  as a readable, greyscale/CVD-safe paper figure at its configured size,
  as a mix of `ok`/`warning`/`error` findings for an author to review
  rather than an all-or-nothing raise.
- Checks: page-width fit against a named journal's real TeX column
  geometry (`mp.capabilities()["tex_presets"]`); minimum text size across
  body/label/title/tick fonts; palette CVD-safety and true-greyscale
  safety (reusing `Palette.report()`, with the exact same palette
  construction `render()` itself uses, so a finding never disagrees with
  what's actually drawn); redundant marker/line-style/hatch encoding for
  grouped series; marker/line-style cycle-length exhaustion (more grouped
  series than distinct markers -- some become indistinguishable once
  colour is removed); legend entry count; and citation/href metadata
  validity (surfaced from `validate()`'s own reference checks).
  `report.ok` is `False` only when an `error`-level finding exists (an
  oversized figure, malformed reference metadata) -- everything else is a
  judgement call to review, not a hard failure.
- `mudplot/_lint.py` needs nothing beyond the stdlib to *import* (stays
  part of the pure engine's zero-dependency promise); only actually
  *running* the palette check needs the colour engine (numpy), imported
  lazily inside that one check -- verified in a fresh subprocess, the
  same pattern `tests/test_no_deps.py` uses for the rest of the pure core.
- Regression coverage: 22 new tests in `tests/test_lint.py`.

### DOI/URL resolver: arXiv-only `.bib` entries now resolve to a real link

- `mp.resolve_reference_href(fields)`: offline (no network access) DOI/
  arXiv-id/URL normalisation, extracted from `ReferenceCatalog` into its
  own documented, directly-usable function. Tries, in order: a `doi`
  field (bare, `doi:`-prefixed, or a full `doi.org`/`dx.doi.org` URL --
  all normalised to the same `https://doi.org/...` form); an arXiv id
  (`eprint` + `archiveprefix`/`eprinttype` == `"arxiv"`, the shape arXiv's
  own "export bibtex" feature produces) resolved to
  `https://arxiv.org/abs/...`; then a plain `url` field; `None` if none of
  those are present.
- Fixes a real gap in `ReferenceCatalog` (not just an added feature): an
  arXiv-only entry -- extremely common for ML/CS papers, `eprint` +
  `archiveprefix` and *no* `doi`/`url` field at all -- previously resolved
  to `href=None` silently, since the original doi-or-url-only fallback
  never looked at `eprint`. `ReferenceCatalog.__getitem__` now uses
  `resolve_reference_href` internally, so existing `.bib` files with
  arXiv-only entries start producing real links with no code changes.
- Regression coverage: 13 new tests in `tests/test_bib.py` (bare/prefixed/
  full-URL DOI forms all normalise identically, arXiv id resolution via
  both field-name variants, priority order when multiple are present, no
  link when none are present, and the exact arXiv-only-entry regression
  end-to-end through `ReferenceCatalog`).

### `.bib` integration: `ReferenceCatalog` (P2-1)

- `mp.ReferenceCatalog.from_bib(path)` / `.from_bib_text(text)`: a minimal,
  dependency-free reader for the common subset of BibTeX entry syntax real
  `.bib` files use (nested `{...}` field values, both quoting styles,
  unquoted numeric fields like `year = 1981`, `@comment`/`@string`/
  `@preamble` blocks correctly skipped rather than mistaken for real
  entries). Not a bibliography manager -- no cross-reference resolution,
  no `@string` macro expansion, no formatted-citation rendering (that's
  the *document*'s job, same as everywhere else reference metadata is
  used in mudplot).
- `catalog[key]` resolves straight to a ready-to-use `ReferenceSpec`:
  `citation=key`, `href` from the entry's `doi` field (as a
  `https://doi.org/...` link), falling back to its `url` field, or `None`
  if neither is present. `catalog.raw(key)` exposes every parsed field
  (title/author/year/...) for anything beyond citation/href, e.g. a
  paper-metadata preview in an editor. A missing key raises a `KeyError`
  naming the keys that *are* available.
- Plugs directly into the existing `citation=`/`href=` kwargs and the
  grouped-series `references=` dict (v0.4) -- no new layer-level API
  needed.
- Regression coverage: 12 new tests in `tests/test_bib.py` (multiple
  entries, comment/string blocks not mistaken for entries, DOI-vs-URL
  fallback, no-link entries, nested braces in a field value preserved,
  multiline values whitespace-collapsed, missing-key error, reading a
  real file by both `Path` and `str`, composing with the fluent API).

## [0.4.0] - 2026-09-07

A reference-system stabilization release: grouped-series citations/links,
a saner citation/URL validator, a documented FigureSpec version/migration
policy (+ `mudplot migrate` CLI), a citation-measurement policy for PGF
layout, a real JSON-Schema-validator compatibility test, Hypothesis-based
property tests for reducer purity, and a cross-referenced journal-profile
view. This closes every item in `mudplot_v0.3_improvement_and_reference_
repos.md`'s v0.4 checklist. 395 tests passing.

### Journal profile registry cleanup (P2-3)

- Two registries have always independently covered a "journal": `theme.
  AVAILABLE_JOURNALS`/`journal_overrides` (a style -- fonts/linewidths/
  default figure size, applied via `.journal(name)`) and `tex.TEX_PRESETS`
  (a TeX document class's column geometry, applied via `.tex_size(name,
  ...)`/`.preview(tex=name)`). They overlap only for a name that's both a
  journal *and* a well-known LaTeX class ("nature"/"ieee" are in both;
  "article"/"revtex"/"acm" are generic document classes with no house
  style, so TeX-only) -- this distinction previously existed only in the
  maintainer's head, with no cross-reference between the two modules and
  no test guarding against them silently drifting apart.
- `mp.capabilities()["journal_profiles"]`: the two merged for every name
  that has both (figure size, base/tick font, line width, column/text
  width, columns), so an agent building a coherent "IEEE-style figure"
  doesn't have to separately cross-reference the `"journals"` and
  `"tex_presets"` sections and guess whether they're meant to compose.
- `mudplot/theme.py`/`mudplot/tex.py` docstrings now cross-reference each
  other and `journal_profiles` explicitly.
- New `tests/test_journal_profiles.py`: every `AVAILABLE_JOURNALS` name
  has a matching `TEX_PRESETS` entry (so `.tex_size(name)` never fails for
  a name `.journal(name)` accepts) and a `JOURNAL_SIZES` entry;
  `journal_profiles` matches the underlying registries field-for-field;
  and an end-to-end check that `.journal(name).tex_size(name)` composes
  into one valid, renderable figure for every journal.
- Also fixed (found while cross-referencing these modules): `mudplot/
  tex.py`'s WYSIWYG mock-page preview used `plt.Rectangle`, which
  matplotlib re-exports at runtime but isn't in `pyplot`'s public type
  surface -- switched to importing `Rectangle` from `matplotlib.patches`
  directly (its actual home), no behaviour change.

### Hypothesis-based property tests

- New dev dependency: `hypothesis` (test-only). New
  `tests/test_property_based.py` widens several existing example-based
  guarantees into properties checked against a much larger randomised
  input space:
  - **reducer purity**: `reduce(state, action)` never mutates its `state`
    or `action` arguments, and its output is always still
    JSON-round-trippable -- checked over a curated slice of the action
    vocabulary (the single-field actions whose validity doesn't depend on
    other spec state) with Hypothesis-generated parameters, not just the
    handful of hand-picked actions the existing tests happen to dispatch.
  - **migration idempotency**: `migrate_spec_dict()` is a true no-op on
    any spec already at the current `SPEC_VERSION`, across many different
    resulting specs (not just the default one).
  - **citation/href character safety, as a property instead of a fixed
    example list**: any string built only from characters outside both
    unsafe sets always passes validation; any string containing at least
    one unsafe character always gets rejected -- restates P0-2's own rule
    generatively, so a future change to either unsafe-character set is
    checked against arbitrary strings, not just the four hand-picked
    examples in `test_references.py`.
  - a wider **JSON round-trip** over random figure-level settings (size,
    dpi, suptitle text including arbitrary/unicode content, theme).
  - Found one real edge case worth naming explicitly while writing this:
    a whitespace-only citation/href (e.g. `" "`) is *safe* under the
    character-safety rule but still correctly rejected by the separate
    "must be non-empty after stripping" check -- the property test filters
    for this so it verifies the character-safety rule specifically,
    without a false failure attributed to the wrong check.

### JSON Schema compatibility test

- New dev dependency: `jsonschema` (used only by tests, not the pure
  engine). `mp.json_schema()`'s existing sync guard (`test_schema_export.py`)
  only checked that the checked-in file matches a fresh regeneration
  byte-for-byte and that it superficially "looks like" a JSON Schema
  (has `$schema`, a `title`, ...) -- it never actually ran a real JSON
  Schema validator against it, so a schema that was technically malformed,
  or too permissive to catch real mistakes, could still pass every
  existing check.
- New `tests/test_json_schema_compat.py`: the schema itself is checked
  against the Draft 2020-12 meta-schema (`Draft202012Validator.check_schema`);
  a range of real specs (grouped references, multi-panel + secondary axis,
  matrix/heatmap, 3-D, the bare default) are round-tripped through
  `.to_dict()` and validated against the exported schema; and a couple of
  deliberately-wrong instances (wrong field type) are confirmed to actually
  get rejected, not silently accepted -- proving the schema is a real
  constraint an external (Rust/serde, form-generator) consumer could rely
  on, not just documentation-shaped JSON.
- Documents one real, existing gap found this way (not a bug -- a
  deliberate scope boundary made explicit): `LayerSpec`'s fields all carry
  defaults, so nothing is "required" at the *schema* level for e.g. a
  `line` layer's `x`/`y` -- that's mudplot's own semantic `validate()`'s
  job, not the JSON Schema's.

### Citation measurement policy (P0-3)

- WYSIWYG layout for a citation is only exact for compact/numeric styles
  (e.g. `"[12]"`): matplotlib lays a figure out *before* the document's own
  bibliography resolves `\figcite{key}`, so it has no way to know the real
  rendered width of e.g. an author-year citation (`"(Fischler and Bolles,
  1981)"`) ahead of time. This guarantee scope is now documented explicitly
  (`FigureSpec.reference_measure_text`, `Plot.reference_style()`).
- `.reference_style(measure_text="(Fischler and Bolles, 1981)")`: measure
  PGF legend citations against a representative example of your actual
  citation style instead of the compact default, so `_autofit()`/legend
  sizing predicts the final compiled width more accurately. The text is
  stripped back out at PGF-substitution time and never emitted to output;
  rejects characters matplotlib's PGF backend would escape (which would
  break that strip-back-out).
- Deliberately **panel-title citations don't widen** even when
  `reference_measure_text` is set: a title can wrap (`wrap=True`) across
  multiple lines, which can split the measurement filler from its sentinel
  into separate .pgf text blocks -- silently leaking the filler text into
  the final output instead of being stripped. Found by testing this
  feature against the existing two-citation demo spec (legend + title),
  not by inspection.
- Regression coverage: 6 new tests in `tests/test_references.py`
  (measured width actually widens, filler never leaks into output inc. the
  title-wrap case that broke first, `None` restores the compact default,
  PGF-unsafe characters rejected, JSON round-trip).
- Also fixed: `mudplot/docs.py`'s Markdown table dividers were an
  inconsistent mix of `|---|` and (accidentally, via editor auto-format)
  `| --- |` styles across sections, which could make a freshly generated
  `docs/REFERENCE.md` disagree with itself byte-for-byte depending on which
  tool last touched it. Standardised on `| --- |` everywhere.

### FigureSpec version/migration policy

- Package version (`mudplot.__version__`) and spec version (`SPEC_VERSION`,
  the on-disk `.mplot.json` contract) are now formally independent: not
  every release changes the serialized shape, and `SPEC_VERSION` is the one
  a Rust/agent consumer, or a saved file, actually needs to check
  compatibility against. Documented in `mudplot/spec.py`.
- `FigureSpec.from_dict()` (and therefore `from_json`/`load_spec`/
  `Plot.from_json`, every deserialisation path) now checks the saved
  `version` field: an older *known* version gets upgraded through a new
  `MIGRATIONS` registry (empty for now -- nothing predates `"0.1"` yet);
  an unrecognised version (older with no migration, or newer than this
  mudplot understands) now raises a clear `ValueError` instead of silently
  loading with whatever fields happen to match. `validate()` catches the
  same problem for a `FigureSpec` built directly (bypassing `from_dict`)
  with a mismatched `version`.
- New CLI subcommand: `mudplot migrate old.mplot.json -o new.mplot.json`
  (upgrades and rewrites a saved spec; a no-op write if it's already
  current).
- Regression coverage: 4 new tests in `tests/test_spec_roundtrip.py`, a new
  `tests/test_cli_migrate.py` (4 tests).

### Reference metadata: grouped series, saner citation/URL validation

- `ReferenceSpec` (`mp.Reference`/`mp.ReferenceSpec`): the citation/href pair
  used to live only on `LayerSpec`/title fields; now also the type of
  `LayerSpec.references`, a `{group_value: ReferenceSpec}` dict for
  attaching a *different* citation/href to each series of a `group=`-ed
  layer (previously impossible -- every series in a group shared one
  `label`/`citation`/`href` at most, so e.g. `group="method"` with RANSAC/
  J-Linkage/PEARL series couldn't cite a different paper per method). Wired
  through PGF `\figcite`/`\href` decoration and SVG per-legend-entry links,
  the same as the existing ungrouped case; a group value absent from
  `references` gets no decoration (no silent fallback to a shared citation).
- Citation/href validation split into separate rules instead of one shared
  TeX-unsafe-character blocklist: a citation is only ever used as a
  `\figcite{KEY}` lookup argument (never typeset), so ordinary BibTeX-key
  punctuation (`_`, `:`, `-`) is now allowed -- previously `fischler_1981`
  or `han:v2v_2019` were rejected outright. `href` becomes a
  `\href{URL}{...}` argument, which hyperref itself reads with special
  URL-safe catcodes (like `\url`), so query strings/fragments (`_`, `&`,
  `#`, `%`, `~`) are now allowed there too. Brace/backslash/control
  characters (the actual macro-injection risk) are still rejected in both.
- `mp.capabilities()["backends"]`: which of `citations`/`hyperlinks`/
  `vector`/`requires_tex` each output format (`png`/`pdf`/`svg`/`pgf`)
  actually preserves, so an agent/editor can show e.g. "citations are only
  kept in PGF export" instead of that being implicit renderer behaviour.
- Regression coverage: 14 new tests in `tests/test_references.py`.

## [0.3.0] - 2026-09-06

LaTeX-native citations/links in figure text, a genuinely usable editor
(multi-panel, drag-to-position, open/export), and the first real-browser
test coverage -- which found three bugs the HTML-level tests could not see.
345 tests passing.

### LaTeX-native citations and links inside a figure

- `LayerSpec.citation`/`href` (legend entries) and `PanelSpec.title_citation`/
  `title_href` (via `.title_reference(...)`): attach a BibTeX key and/or URL
  to figure text. Nothing is baked into the image -- the document resolves
  it, so a figure's `[1]` is the same `[1]` as in its References list.
- `.pgf` export (`save("fig.pgf")`): emits `\figcite{key}` and
  `\href{url}{...}`. Deliberately `\figcite`, not `\cite`, so the paper
  decides what a figure citation means (`\cite`/`\citep`/`\autocite`/
  nothing) -- `mudplot.PREAMBLE` provides the default mapping.
- Backend-dependent by design: PGF gets real macros, SVG turns the text into
  a clickable link, raster output stays plain.
- Metadata is substituted into LaTeX source verbatim, so `validate()`
  rejects braces/backslashes/newlines in these fields (a trust boundary:
  the user's document compiles the result).
- Verified end to end against a real TeX installation: a generated .pgf
  compiles with pdflatex+bibtex, and the citation numbers in the figure
  match the paper's bibliography (`tests/test_references.py` covers the
  export contract; the compile check was manual).
- The markers used to survive pgf's text escaping are kept short on purpose:
  they sit in the text matplotlib measures during layout, and an embedded
  full URL collapsed the axes to zero size. Locked in with a test that
  fails on the layout warning.

### Editor

- Canvas-first layout: the figure is a large sticky workspace, controls sit
  in an independently scrolling inspector, secondary sections collapse.
  Single column below 800px.
- **Multi-panel editing**: set the grid, then pick which panel every control
  edits. Titles/axes, layer list, position toggles and all three drag
  handles follow the selection; panel-scoped actions default to it
  server-side. The selection is session state, never written to the spec.
- Direct editing of panel title and x/y axis labels, plus legend-label,
  citation and link fields -- no more raw JSON for ordinary edits.
- **Open** a saved `.mplot.json` (validated first, so a bad file reports the
  problem instead of wedging the editor) and **export** PDF/SVG at the exact
  configured size, not just the preview PNG.
- Fixed: the htmx fragment carried its own `#app-body` wrapper while every
  swap targeted `#app-body` with `innerHTML`, so each edit nested another
  copy.
- Fixed (found by the new browser tests): arrow-key nudging never worked --
  clicking a handle to focus it counted as an edit, which swapped in a new
  overlay and stole that focus; scroll restore ran before layout and was
  clamped away; form labels were never bound to their inputs, so every field
  was unlabelled for screen readers.
- Nudges are coalesced, so holding an arrow key produces one action instead
  of one per keypress.

### Renderer

- Each Axes records `ax._mudplot_panel`. `fig.axes` also collects twin (y2)
  and colorbar axes, so its order stops matching panel order after the first
  panel -- anything mapping a rendered Axes back to its spec needs this.

### Testing

- `tests/test_editor_browser.py`: real Chrome via Playwright (optional
  `browser` extra; skipped when absent) covering drag, keyboard nudge,
  multi-panel targeting, open-from-file, and swap behaviour.
- `tests/test_references.py`: the exported `.pgf` is compiled by tectonic
  and the resulting PDF read back, so "the citation resolves against the
  paper's bibliography" is checked rather than asserted.

## [0.2.0] - 2026-09-05

TeX-ready figure sizing/layout, position-anywhere legends/titles/
annotations, and a substantially more usable interactive editor (htmx
partial updates, drag-to-position, visual redesign). 322 tests passing.

### TeX column sizing, overlap-free layout, draggable legends, docs/editor tabs

- `Plot.tex_size(preset, columns=1|2)`: size the *actual* figure (not just
  `.preview()`) to a TeX document's single-column width or full text width
  (for a double-column-spanning figure), matching the same column/font
  metrics `.preview(tex=...)` already used.
- `render()`/`save()` now precompute layout so text never overlaps or gets
  silently clipped, while still preserving the exact configured physical
  size (needed for TeX placement): titles/suptitle wrap natively at the
  figure width instead of overflowing it, and canvas space is reserved for
  any named `"outside ..."` legend location so it's never cut off. Uses
  matplotlib's own constrained-layout engine and text-measurement renderer
  throughout -- no custom layout system, and a no-op when nothing would
  otherwise be clipped. 3-D panels keep the previous `tight_layout()`
  fallback (matplotlib's constrained layout doesn't support 3-D Axes well).
- `LegendSpec.bbox_to_anchor` / `.legend(bbox_to_anchor=[x, y])`: pin a
  legend to an exact figure-fraction position, overriding `location`.
  Trusted as-is (not auto-adjusted) since an explicit position may
  deliberately overlap the plot.
- Dashboard editor: a ✥ handle to drag the legend directly on the preview
  (mouse drag, or click + arrow keys), dispatching the same
  `SetLegend(bbox_to_anchor=...)` action as the fluent API. Also split into
  **Editor**/**Docs** tabs within the one running server (`/docs` serves
  the live engine reference), instead of needing the separate static
  `dashboard build` for documentation.
- Regression coverage: `tests/test_layout.py`, additions to
  `tests/test_dashboard_editor.py`.

### Dashboard editor: htmx partial updates, title/annotation dragging, redesign

- Converted the editor's full-page-reload-per-action UX to htmx partial
  swaps: every form/drag now updates the preview, layer list, and action
  log in place. Vendored `htmx.min.js` (0BSD licensed, `dashboard/static/`)
  -- no new Python dependency, plain form-post fallback still works for
  non-JS clients (`HX-Request` header detection).
- `PanelSpec.title_position` / `.title_position([x, y])`: pin a panel
  title to an exact axes-fraction spot (bypasses matplotlib's title-
  specific y-offset transform, which otherwise silently discards a
  repositioned y under constrained_layout -- draws a plain axes-fraction
  text artist instead once a position is set).
- `SetLayerAt` action / `.set_layer_at(layer_index, at)`: reposition a
  `text`/`annotate` layer's anchor (data coordinates) -- also usable by an
  agent, not just the editor.
- Dashboard editor: draggable handles for the legend (blue), panel title
  (purple), and any `text`/`annotate` layer (green, one per layer,
  automatic) directly on the preview -- mouse drag or click + arrow keys.
  A dedicated "Add text / annotation" form. New `EditorSession.refresh()`
  caches one render's PNG + layout info (panel bbox/limits/scale) so
  `/fig.png` and the drag handles' placement can't disagree.
- Visual redesign: consistent spacing/typography/colour system, card
  shadows, a checkerboard preview background (so a white figure is visibly
  bounded), clearer button/error/log styling.
- `text`/`annotate` layers are now excluded from constrained_layout's
  space-reservation solve (`Artist.set_in_layout(False)`) -- their data-
  coordinate position isn't known until axes limits are, which previously
  produced spurious "constrained_layout not applied" warnings.
- Regression coverage: additions to `tests/test_layout.py` and
  `tests/test_dashboard_editor.py` (23 new tests).

## [0.1.0] - 2026-09-05

First tagged release: the pure spec/reducer/store engine, the LCH colour
engine, the Matplotlib renderer (21 layer types), TeX-aware preview, the
fluent + agent-facing APIs, the CLI, and the human-facing dashboard, plus
three stability-hardening passes and named colour-palette presets. See
`docs/DEMO.md` for a reproducible, pandas-driven demo of the actual output.

### Colour: named palette presets + black & white print safety

- Added three named, pre-verified `qualitative` palette presets
  (`mudplot.capabilities()["palette_presets"]`): `paper` (default, safe up to
  6 categories), `vivid` (higher chroma, safe up to 6), `soft` (lower chroma
  for large-area fills, safe up to 5). "Safe" = measured via
  `Palette.report()` (worst-case ΔE00 ≥ 8 across normal + protanopia/
  deuteranopia simulation, min CIE L* gap ≥ 3 in true relative-luminance
  greyscale), not an assumed or certified guarantee — see
  `tests/test_palette_presets.py`. Use via `.palette(preset="paper")` or
  `mp.color_palette(n, preset="paper")`.
- `ThemeSpec.hatches`: bar/box/violin fills now also cycle a hatch pattern
  per group by default (alongside the existing marker/line-style cycle for
  line/scatter), so grouped fills stay distinguishable in black & white
  print/photocopy regardless of how similar the underlying greys are.
  Disable via `.encoding(redundant_encoding=False)`.
- `docs/DEMO.md` §4/§5: palette presets previewed under normal/CVD/true
  greyscale vision, plus a grouped bar chart converted pixel-by-pixel to
  true relative-luminance greyscale to demonstrate hatches remain readable
  after printing (not a mockup).
- Softened the top-level README colour claims from "colourblind-safe" to
  "colourblind-aware" / measured, to match what is actually verified.

### Stabilization: data fidelity and editing

- Categorical x positions now use Matplotlib's shared category registry across
  layers, secondary axes and shared panels instead of independent mappings.
- Grouped 2-D/3-D continuous scatter uses a single normalization and colorbar.
- 3-D panels honor axis scales/limits, legend placement and panel labels;
  mixed-projection figures retain sharing between their 2-D panels.
- Palette size accounts for all independent series and pie slices per panel.
- Store state/history/return values/listener notifications are isolated
  snapshots, and reducer results no longer alias mutable action payloads.
  Change store state through actions rather than mutating `plot.spec`.
- `save()` now preserves the configured physical size by default, including
  with ambient Matplotlib tight-crop settings. Use `save(path, tight=True)`
  (or `mp.save(spec, path, tight=True)`) for the previous cropped output.
- TeX preview avoids cropping/rescaling the embedded figure; context-free
  preview returns the actual vector figure rather than a rasterized copy.
- Failed render/save operations close their figures; successful calls still
  return an open figure owned by the caller.
- Validate figure geometry, ratios, all axis scales/limits and empty encoding
  cycles; reject negative/non-integer panel indices and invalid layout actions.
- Regression coverage: `tests/test_stabilization.py`.

### Added

- **Colour engine**: sRGB ↔ linear ↔ XYZ ↔ Lab ↔ LCH conversions (numpy-only);
  CIE76/CIEDE2000 colour difference (validated against Sharma et al. 2005);
  Machado et al. (2009) colour-vision-deficiency simulation
  (protan/deutan/tritan); qualitative/sequential/diverging palette
  generators optimised for maximum contrast and CVD safety.
- **Declarative spec model**: `FigureSpec` and friends — a fully
  serialisable dataclass tree with lossless JSON round-tripping.
- **Pure reducer architecture**: `actions` + `reducer` + `store`
  (functional core / imperative shell); `Store.undo()`/`redo()`.
- **Renderer**: line/scatter/bar/errorbar/band/hline/vline/text/annotate/
  hist/box/heatmap layers; multi-panel layouts with width/height ratios;
  secondary y-axis; shared axes; despine; outside legends; continuous
  colour-mapped scatter + colorbar (using the same LCH colormaps).
- **Design-quality features**: redundant marker/line-style encoding for
  greyscale/CVD safety; palette `lightness_jitter`;
  `Palette.report()`/`grayscale_srgb()`.
- **TeX-aware WYSIWYG preview**: renders a figure at its true final size
  and font inside a mock document column (article/ieee/revtex/nature/acm
  presets).
- **Fluent builder API** (`mp.plot(...)`) accepting dict/records/rows/
  pandas/polars/numpy/pyarrow/DB-API cursor or connection+query inputs.
- **Agent-facing interface**: `capabilities()`, `json_schema()`, `apply()`,
  action history/replay (`action_log`), pure `validate()`/`assert_valid()`.
- **CLI**: `python -m mudplot {capabilities,schema,docs,validate,render}`.
- **Docs generation**: `mudplot.docs.reference_markdown()` — the same
  introspection that powers `capabilities()`, turned into a Markdown
  reference (`docs/REFERENCE.md`), kept in sync with CI.
- **Dashboard** (separate package, human-facing):
  - a static docs + design-gallery site generator
    (`python -m dashboard build`)
  - a local interactive editor prototype (`python -m dashboard serve`),
    driving the exact same Store/actions/reducer as the fluent API
- Packaging: `py.typed` marker, MIT `LICENSE`, English-first docs with
  Korean translations kept alongside (`*.ko.md`).

### Fixed (stability hardening pass)

- `.journal(...)` didn't actually change the figure size (a dead rcParams
  entry was shadowed by an explicit `figsize=`); now applied directly to
  the spec.
- Auto panel labels (a/b/c) used the theme's font size directly instead of
  the effective (possibly journal-overridden) rcParams value.
- The TeX `full_width=True` preview inflated the embedded figure to
  roughly 2x its true rendered size.
- `SetData` silently discarded previously-registered `data.matrices`.
- A flat list of strings passed as plotting data was shredded
  character-by-character instead of being rejected/treated as one column.
- `qualitative()`'s own `min_delta_e` reporting used an O(n²) pure-Python
  loop (impractically slow beyond a few hundred colours); requesting more
  colours than `n_candidates` silently produced duplicates.
- `Store(spec)` didn't defensively copy its initial state, so external
  mutations could leak into "pure" store state.
- The CLI printed raw Python tracebacks for ordinary errors (missing file,
  malformed JSON) instead of a clean one-line message.
- `hline`/`vline`/`text`/`annotate` ignored `axis="y2"` and always drew on
  the primary axis.
- Grouped bar charts drew every group at the same x position, hiding
  shorter bars behind taller ones; bars are now dodged automatically.
- `capabilities()` under-reported that `bar`/`errorbar`/`band`/`hline`/
  `vline`/`text`/`annotate` all support `axis="y2"` routing (only
  `line`/`scatter` listed it), even though it worked correctly at render
  time. Added a cross-module consistency test to prevent this class of
  drift from recurring.
- Categorical x-axis values (e.g. bar-chart category labels like
  `"control"`/`"treatment"`) crashed every series layer with "could not
  convert string to float". Non-numeric x columns are now mapped to
  positions with the original strings applied as tick labels.
- The lazy top-level API (`mp.render`, `mp.save`) broke after the *first*
  call in a process: resolving one lazy attribute had the side effect of
  shadowing another (or itself, on the next access) with the raw
  submodule instead of the intended function, due to how Python binds
  submodules onto their parent package. This slipped past 202 passing
  tests because they mostly import the real functions directly rather
  than exercising the lazy `mp.*` attributes repeatedly -- exactly the
  pattern real multi-figure scripts (and the README's own examples) use.

See `DESIGN.md` §4c2 and `tests/test_bugfixes.py` for full details on each
of the above.

### Expanded plot coverage + 2 more bugs

### Added

- **3-D plots**: `scatter3d`, `line3d`, `surface`, `wireframe`. A panel
  opts in via `.projection3d()`; 2-D and 3-D panels can coexist in the same
  multi-panel figure. `render()` was restructured to build axes with
  `fig.add_subplot()` per panel (instead of `plt.subplots()`) so each panel
  can have its own projection, with `sharex`/`sharey` re-implemented
  manually via `Axes.sharex`/`sharey` for the (2-D-only) "all"/"row"/"col"
  modes.
- **Distribution plots**: `violin`, `kde` (a small numpy-only Gaussian KDE
  -- no scipy dependency).
- **2-D field plots**: `contour`, `contourf` (share the same
  `data.matrices` + LCH-colormap infrastructure as `heatmap`).
- **`pie`** charts.
- Categorical x-axis values (already fixed for 2-D series layers) and the
  redundant-encoding/colour-mapping machinery all extend to the new types
  where it makes sense.

### Fixed

- **Pie charts silently drew a duplicate, overlapping legend.**
  `ax.pie(..., labels=...)` also registers each wedge as a legend handle
  (so `ax.legend()` can be called separately), which collided with
  mudplot's generic "draw a legend if there are labelled handles" logic --
  every pie chart got its on-wedge labels *and* a redundant legend on top.
  Fixed by clearing each wedge's legend label after drawing.
- **The deepest root cause of the lazy `mp.render`/`mp.save` bug (from the
  previous pass) was still only partially fixed.** The original fix patched
  up the colliding `_LAZY` entries inside `__getattr__`, but *any* ordinary
  import elsewhere in the codebase -- e.g. `Plot.save()`'s own
  `from .render import save` -- triggers the exact same submodule/parent-
  binding side effect *without* ever calling `__getattr__`, so it could
  still silently squat on the "render" slot before a single `mp.render`
  access happened. The real, permanent fix was renaming the implementation
  module from `mudplot/render.py` to `mudplot/_render.py` so the collision
  is structurally impossible rather than something to keep patching around.

## Supported plot types (current)

`line`, `scatter` (continuous colour mapping + colorbar), `bar`
(auto-dodges when grouped; categorical or numeric x), `errorbar`, `band`,
`hist`, `box`, `violin`, `kde`, `heatmap`, `contour`, `contourf`, `pie`,
`hline`/`vline`, `text`/`annotate`, and 3-D `scatter3d`/`line3d`/`surface`/
`wireframe`. Most support secondary y-axis routing (`heatmap`/`hist`/`box`/
`violin`/`kde`/`pie`/`contour`/`contourf`/3-D types don't, since it isn't
meaningful for them). See `docs/REFERENCE.md` (or `mp.capabilities()`) for
the authoritative, always-up-to-date list.
