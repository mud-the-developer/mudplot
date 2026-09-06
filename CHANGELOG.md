# Changelog

All notable changes to this project are documented here.

## [Unreleased]

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
- Canvas-first layout, direct title/axis-label editing, PDF/SVG export, and
  preserved scroll/collapse state across htmx swaps.
- Fixed: the htmx fragment carried its own `#app-body` wrapper while every
  swap targeted `#app-body` with `innerHTML`, so each edit nested another
  copy.

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
