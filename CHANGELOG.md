# Changelog

All notable changes to this project are documented here.

## [Unreleased]

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

## [Unreleased] (continued): expanded plot coverage + 2 more bugs

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
