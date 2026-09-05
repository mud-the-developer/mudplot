# mudplot — design document

*[한국어 문서 / Korean docs: DESIGN.ko.md](DESIGN.ko.md)*

A Python plotting library for scientific papers, built on top of Matplotlib.
It provides **perceptually uniform, colourblind-safe** colour palettes and
paper-ready styles.

## 0. Goals / differentiation

- Make "nice paper figures" as easy as seaborn / SciencePlots do.
- Differentiator = **an LCH (CIELAB polar coordinates) colour-generation
  engine**
  - Equal lightness (fixed L) → fair under greyscale printing / contrast
  - Hue (H) evenly distributed → maximum contrast
  - Verified/optimised via protanopia/deuteranopia/tritanopia simulation
- Like SciencePlots, also ships static mplstyle files, but palettes are
  **generated dynamically** for any requested N.

## 1. Dependency policy

- Colour conversion / CVD simulation are **implemented directly with numpy**
  (verifiability + minimal dependencies).
- Runtime dependencies: `numpy` and `matplotlib` only (and only for the
  effect layer — see §4b).

## 2. Colour theory (implementation pipeline)

```
sRGB (0..1)
  ⇄ gamma decode/encode        (convert.py)
linear sRGB
  ⇄ 3x3 matrix (D65)
CIE XYZ
  ⇄ f(t) / f^-1(t)             (D65 white point)
CIELAB (L*, a*, b*)
  ⇄ polar coords                C = sqrt(a^2+b^2), H = atan2(b,a)
CIELCh (L, C, H)
```

- Reference white point: **D65** (2° observer).
- Distance metric: **CIEDE2000** (ΔE00) for perceptual colour difference
  (distance.py).
- CVD simulation: **Machado, Oliveira & Fernandes (2009)** 3x3 matrices
  (interpolated over severity 0–1). Supports protan/deutan/tritan (cvd.py).

## 3. Palette kinds

1. **Qualitative (categorical)**: equal lightness L, equal chroma C, evenly
   distributed H.
   - For N requested colours → sample many candidate hues, then optimise a
     hue subset/offset that maximises the minimum ΔE00 (normal vision + CVD
     simulation).
   - Chroma C is clipped down when it falls outside the sRGB gamut.
2. **Sequential**: L varies monotonically around a single H (+ chroma
   adjustment).
   - Guarantees perceptual uniformity (evenly-spaced brightness).
3. **Diverging**: two hues at the ends, a neutral (low-chroma) lightness
   peak in the middle.
4. **Cyclic**: for phase-like cyclic data (optional, lower priority).

## 4. Core architecture: spec-centric (declarative, serialisable)

Two requirements — (a) an intuitive API, (b) future Rust
(askama+tokio+htmx) interactive editing/saving — converge on a single
decision:

> **Represent all figure state as a declarative `FigureSpec` that can be
> serialised to JSON/TOML, and treat it as the single source of truth.**

```
   [ Python builder API ]                 [ Rust web editor (future) ]
   mp.plot(df).line(...)                  askama forms + htmx
         │  (create/modify)                      │ (edit)
         ▼                                        ▼
   ┌─────────────────────────────────────────────────────┐
   │   FigureSpec  (dataclass ⇆ JSON/TOML, language-neutral) │ ← saved as .mplot.json
   └─────────────────────────────────────────────────────┘
         │  (render)                               │ (render request)
         ▼                                        ▼
   matplotlib backend                       reuse the Python renderer
   → PNG/PDF/SVG                            → htmx swaps in the image
```

- The spec holds **plain data only** (no logic). Enums are strings, colours
  are hex/parameters.
- The renderer (`render.py`) is a pure function that turns a spec into a
  matplotlib Figure.
- The builder API (`api.py`) is just a fluent layer that **assembles the
  spec intuitively** — internally it always updates the spec, so editing via
  a GUI or writing code produces identical results.
- On-disk format: `.mplot.json` (+ optionally inline/referenced data). Rust
  only needs to know this schema; initially rendering is delegated to a
  Python process (subprocess/HTTP).

## 4b. State management: pure reducer + effects at the edges (functional core / imperative shell)

Rather than simply mutating the spec, state transitions are modelled as
**pure functions** (Elm/Redux style). This maps directly onto a future Rust
editor: the editor sends actions, the same reducer produces new state, and
effects do the drawing.

```
   Action (pure data)                 State (FigureSpec)
        │                                    │
        ▼                                    ▼
   reduce(state, action) -> state'   ...  pure function (immutable input, no side effects)
        │
        ▼  (new state)
   ── everything above is the functional core (pure) ──────────
   ── everything below is the imperative shell (effects) ──────
        │
        ▼
   Effects:  render (matplotlib) · io (files) · preview (screen/PNG)
```

- `actions.py` — action definitions (a tagged union of frozen dataclasses).
  E.g. `AddLayer`, `SetAxisLabel`, `SetTheme`, `SetPalette`, `SetLimits`, …
- `reducer.py` — `reduce(spec, action) -> FigureSpec`. **Input spec is never
  mutated**; a new spec is returned. No matplotlib/file access.
- `store.py` — the imperative-shell driver. Holds state, exposes
  `dispatch(action)` and `subscribe(...)`. Reused by dashboards/editors.
- Effects (`render`, `io`, `preview`) live only at the edges.
- The fluent builder in `api.py` is **just sugar for dispatching actions** —
  the same reducer runs whether you write code or edit through a GUI.

### Dashboard ↔ engine separation (machine-friendly vs human-friendly)

- `mudplot/` = **the pure engine, machine- (AI agent-) friendly**. Everything
  is manipulated via JSON/actions and is self-describing. No dependency on
  any particular UI.
- `dashboard/` = **a separate package, human-friendly UI**. Imports the
  engine's store/reducer/actions directly. Will eventually be replaced/
  complemented by a Rust (askama+tokio+htmx) editor.
- Dependency direction: dashboard → mudplot (one-way).

### Agent-friendly interface (so machines can drive it easily)

Since text/JSON is the natural medium for an AI agent, the engine provides
four things (all pure, zero dependencies):

1. **Capability discovery**: `mp.capabilities()` → returns layer types +
   fields, theme/journal/TeX-preset/palette kinds, and the entire action
   vocabulary as a machine-readable dict.
2. **Schema**: `mp.json_schema()` → the full JSON Schema of `FigureSpec`
   (for validation/form generation/agent planning).
3. **Build from JSON actions**: `mp.apply([{"type": "AddLayer", ...}, ...])`
   → produces a `FigureSpec` via pure reduction. `action_from_dict`/
   `action_to_dict` round-trip.
4. **Action history**: `Store.history` / `Plot.action_log` → how a figure
   was built can be replayed/reproduced, with undo support.

```python
caps = mp.capabilities()          # "what can I do?"
schema = mp.json_schema()         # "what does the structure look like?"
spec = mp.apply([                 # build the whole thing from JSON alone
    {"type": "SetData", "columns": {"x": [1,2,3], "y": [1,4,9]}},
    {"type": "AddLayer", "layer": {"type": "line", "x": "x", "y": "y"}},
    {"type": "SetTheme", "name": "paper"},
])
mp.save(spec, "fig.pdf")          # effect
```

## 4c. TeX-aware preview

Papers are written in TeX and figures are laid out to match it, so a
preview should show the **exact size and font it will have in the final
document** (WYSIWYG).

- `TexContext`: a document class's `\textwidth`, `\columnwidth` (pt), body
  font size, and column count. Presets: `article`, `ieee`, `revtex`,
  `nature`.
- The figure is rendered at the exact inch size of `columnwidth × fraction`,
  and its internal fonts are matched to the body font size (pt → inch =
  1/72.27).
- The preview places the figure **inside a mock text column** with a
  caption, so you get a sense of its relative size in the document's
  context.

## 4c2. Stability audit (2025-09 hardening pass)

An audit pass focused on **finding and fixing bugs / unintended behaviour**
rather than adding features. It found 10 real bugs (all locked in with
regression tests in `tests/test_bugfixes.py`):

1. **`.journal("ieee")` didn't actually change the figure size** —
   `render()` always passes `figsize=` explicitly, so the journal preset's
   rcParams `figure.figsize` entry was dead code. Fixed by applying the
   journal's size directly to the spec via `theme.JOURNAL_SIZES`.
2. **The auto panel label (a/b/c) font ignored journal overrides** — fixed
   by reading the *active* rcParams (`plt.rcParams["axes.titlesize"]`)
   during rendering instead of the theme value directly.
3. **The TeX `full_width=True` preview inflated the figure to roughly 2x its
   true rendered size** — `fig_w` was being incorrectly recomputed; replaced
   with the actual rendered size (`sized.size[0]`).
4. **`SetData` silently wiped previously-registered `matrices`** — fixed by
   updating `columns` in place instead of replacing the whole `DataSpec`.
5. **A flat list of strings was shredded character-by-character** —
   `to_columns(["apple", "banana"])` misdetected each string as a "row"
   (strings have `__len__` too). str/bytes are now explicitly excluded from
   row detection.
6. **`qualitative()`'s `min_delta_e` computation used a pure-Python O(n²)
   double loop**, which effectively hung at n=1000 — fully vectorised.
   Also fixed: requesting `n > n_candidates` silently produced duplicate
   colours instead of raising a clear error.
7. **`Store(spec)` didn't defensively copy the spec it was given**, so
   external mutations leaked into internal state — a violation of the "pure
   state" design principle. Fixed with a deep copy on construction.
8. **The CLI printed raw Python tracebacks** for missing files / JSON parse
   errors — cleaned up into a single-line stderr message that's easy for
   agents/shell scripts to parse.
9. **`hline`/`vline`/`text`/`annotate` ignored `axis="y2"`** and always drew
   on the primary axis (other layer types already routed correctly) — now
   routes consistently. Conversely, types that genuinely don't support
   secondary-axis routing (`heatmap`/`hist`/`box`) now get a clear rejection
   from `validate()` if `axis="y2"` is set on them.
10. **Grouped bar charts drew all groups at the same x position**, so
    shorter bars were completely hidden behind taller ones — a real
    data-integrity risk, not just cosmetic. Fixed with automatic
    side-by-side dodging based on group count.

### Follow-up audit (found while answering "what plot types are supported?")

11. **`capabilities()` under-reported real functionality**: `bar`/
    `errorbar`/`band`/`hline`/`vline`/`text`/`annotate` all correctly
    support `axis="y2"` routing in `render.py`/`validate.py`, but
    `LAYER_TYPES` only listed `axis` as a field for `line`/`scatter`. An
    agent trusting `capabilities()` to plan a figure would never have
    discovered this actually worked. Fixed, and locked in with a
    cross-module consistency test
    (`tests/test_capabilities_consistency.py`) that pins `LAYER_TYPES`,
    `LayerSpec`'s real fields, and `render`/`validate`'s type sets together.
12. **Categorical x-axis values crashed every series layer.** `_col()`
    forced `dtype=float` unconditionally, so an extremely common case for a
    bar chart — string category labels like `["control", "treatment"]` on
    x — failed with "could not convert string to float" instead of working
    the way plain matplotlib (which has native categorical-axis support)
    would. Fixed: non-numeric x columns are now mapped to evenly-spaced
    positions with the original strings applied as tick labels, for
    line/scatter/bar/errorbar/band alike (numeric x is unaffected).
13. **The lazy top-level API (`mp.render`, `mp.save`) broke after the
    first call in a process.** `mudplot/__init__.py`'s PEP 562
    `__getattr__` resolved these via `importlib.import_module("mudplot.render")`,
    but importing a submodule has the side effect of binding it onto the
    parent package's namespace *under its own name* — i.e. it set
    `mudplot.render = <submodule>` directly in `mudplot.__dict__`,
    invisibly shadowing the function just returned. The very next
    `mp.render(...)` access found the submodule sitting in `__dict__`
    (bypassing `__getattr__` entirely, since Python only calls it for
    *missing* attributes) and failed with "'module' object is not
    callable". `mp.save` was affected too (same backing submodule), in
    either access order. This slipped through 202 passing tests because
    almost all of them import the real function directly
    (`from mudplot.render import render`) rather than exercising the lazy
    top-level attribute repeatedly — exactly the pattern real scripts
    (rendering more than one figure) and the README's own usage examples
    rely on. Fixed by having `__getattr__` fix up *every* `_LAZY` entry
    backed by the same submodule in one pass, so the import side effect
    can no longer squat on a not-yet-requested name.

### Follow-up audit #2 (found while expanding plot coverage to 3-D/violin/kde/pie/contour)

14. **The bug #13 fix above was still incomplete.** Patching `__getattr__`
    only helps when resolution actually goes through it; an ordinary
    `from .render import save` *anywhere else* in the codebase (e.g.
    `Plot.save()`) triggers the exact same submodule/parent-binding side
    effect on `mudplot.render` without ever calling `__getattr__` at all,
    so it could still silently squat on the "render" slot before a single
    explicit `mp.render` access happened. There is no way to "catch" this
    from inside `__getattr__`, because Python simply never calls it once
    *any* value (even the wrong one) already sits in `mudplot.__dict__`.
    The only real fix was structural: renamed the implementation module
    from `mudplot/render.py` to `mudplot/_render.py` so the name no longer
    collides with the public `mp.render` attribute at all. (General lesson
    kept as a comment in `__init__.py`: a `_LAZY` key must never equal the
    last component of its own backing submodule's dotted name.)
15. **Pie charts drew a duplicate, overlapping legend on top of their own
    on-wedge labels.** `ax.pie(..., labels=...)` also registers each wedge
    as a legend handle (so callers can draw a separate legend instead of
    on-wedge labels if they prefer), which collided with mudplot's generic
    "draw a legend if there are any labelled handles" logic in
    `_draw_panel` — every pie chart got both. Fixed by clearing each
    wedge's legend label (`"_nolegend_"`) right after drawing.

Additional defensive validation was added: `validate()` now catches
mismatched data-column lengths, jagged matrices, empty panels, invalid
spine characters, out-of-range alpha, and wrong-length `at`/`to`. The
`SetColorbar`/`SetEncoding`/`SetFont`/`SetAxesStyle`/`SetGridStyle`/
`SetTicksStyle`/`SetPalette` actions now raise a clear `ValueError` for
out-of-range indices or unknown fields (previously a raw `IndexError`/
`TypeError`, or silently ignored).

## 4d. Self-validation (validate) — clear feedback for agents before rendering

`mudplot/validate.py` exposes a pure function `validate(spec) -> list[str]`
that catches things like references to non-existent columns, invalid layer
types, and layout mismatches ahead of time, returning human-readable
sentences. `render()` calls this before drawing, so instead of an unfriendly
`KeyError` it raises a `ValueError` listing every problem at once. Agents
can call `mp.validate(spec)` themselves to self-check before rendering.

## 4e. CLI — the shell/agent automation entry point

`python -m mudplot {capabilities,schema,validate,render}`. `capabilities`/
`schema`/`validate` only need the pure core; only `render` needs the
`[render]` extra. `schemas/figure_spec.schema.json` and
`schemas/capabilities.json` are static files generated by the CLI, and CI
always diffs them against a fresh generation to prevent drift (giving the
Rust side one trustworthy schema source).

## 4f. Expanded plot coverage (3-D, distributions, 2-D fields, pie)

To get closer to matplotlib/seaborn's breadth, the renderer grew a fourth
family of layers beyond the original "series/distribution/matrix/marker"
set:

- **3-D** (`scatter3d`, `line3d`, `surface`, `wireframe`): a `PanelSpec`
  now carries `projection: "2d" | "3d"` and an optional `z: AxisSpec`.
  Because `plt.subplots()` can't give individual panels their own
  projection, `render()` was restructured to build the grid with
  `fig.add_gridspec()` + one `fig.add_subplot(gs[r, c], projection=...)`
  call per panel, so 2-D and 3-D panels can coexist in one figure.
  `sharex`/`sharey` ("none"/"all"/"row"/"col") is re-implemented manually
  via `Axes.sharex`/`sharey` afterwards, since `plt.subplots()`'s
  convenience keyword isn't available with per-panel projections, and
  sharing is skipped entirely once any panel in the figure is 3-D (it
  isn't meaningful there).
- **Distributions**: `violin` (extends the existing box-plot data
  collection) and `kde` (a small numpy-only Gaussian density estimate,
  Scott's rule bandwidth — deliberately not using `scipy.stats.gaussian_kde`
  to keep the render effect layer's dependencies at just numpy+matplotlib).
- **2-D fields**: `contour`/`contourf` reuse the exact same
  `data.matrices` + LCH-colormap machinery as `heatmap`.
- **`pie`**: `x` is the category-label column, `y` the values column
  (consistent with every other layer's x/y convention rather than
  inventing new field names).

All of the above are registered the same way as any other layer: in
`capabilities.LAYER_TYPES` (so agents discover them), `validate.py` (so
misuse — e.g. a 3-D-only type on a 2-D panel — gets a clear message
instead of a matplotlib traceback), and `render.py`'s type-dispatch sets.
`tests/test_capabilities_consistency.py` cross-checks all three stay in
sync automatically.

## 5. Intuitive API principles

Removes the non-intuitive aspects of seaborn (`style="whitegrid"` strings)
and matplotlib (`rcParams['axes.linewidth']` dotted strings).

- **Structured, typed themes**: grouped attributes instead of string keys.
  ```python
  theme = mp.Theme.paper()
  theme.font.size = 10          # not rcParams['font.size']
  theme.axes.spines = "LB"      # left + bottom only
  theme.grid.show = True
  theme.ticks.direction = "in"
  theme.palette.kind = "qualitative"   # the palette is part of the theme too
  ```
- **Fluent builder**: method names carry their meaning; each call just
  updates the spec.
  ```python
  (mp.plot(df)
      .line(x="voltage", y="current", group="order")
      .labels(x="Voltage (mV)", y="Current (μA)")
      .theme("paper").journal("nature")
      .save("fig.pdf"))
  ```
- **Discoverability**: every option is a dataclass field → exposed directly
  through IDE autocomplete, docs, and the JSON Schema. A Rust form could be
  auto-generated from the same schema.
- **Sensible defaults**: picking just a paper preset (paper/nature/ieee)
  should already be usable.

## 6. Module structure

```
mudplot/                 # pure engine (no UI dependency)
  __init__.py            # public API surface
  color/                 # colour engine
    convert.py distance.py cvd.py palette.py preview.py
  spec.py                # FigureSpec and other serialisable dataclass models (state)
  actions.py             # Action definitions (a union of frozen dataclasses)
  reducer.py             # reduce(state, action) -> state (pure)
  store.py               # imperative-shell driver (dispatch/subscribe)
  theme.py               # ThemeSpec presets & rcParams mapping
  render.py              # effect: Spec -> matplotlib Figure
  tex.py                 # TeX-aware sizing/preview (effect)
  io.py                  # effect: spec <-> json (.mplot.json)
  api.py                 # fluent builder (sugar for dispatching actions)
dashboard/               # separate package: interactive UI (future)
tests/
  test_convert.py test_distance_cvd.py test_palette.py
  test_spec_roundtrip.py test_render.py test_reducer.py test_tex.py
```

## 7. Rust interactive editor roadmap (future)

- Deserialise the `.mplot.json` format with Rust `serde` (the same schema).
- Render Spec fields → an HTML form via askama templates. htmx sends a
  partial POST on field change → the server updates the Spec → only the
  re-rendered image fragment is swapped in.
- Rendering: phase 1 calls the Python renderer from tokio via subprocess/
  HTTP. Phase 2 (optional) could replace it with a pure-Rust renderer (e.g.
  `plotters`), which is possible precisely because the schema is fixed and
  the backend is swappable.
- **Key point**: Python and Rust only ever need to agree on the
  `FigureSpec` JSON schema.

## 8. Milestones

- [x] M0: environment/scaffolding
- [x] M1: colour conversion + tests
- [x] M2: colour difference + CVD simulation
- [x] M3: qualitative palette
- [x] M4: sequential / diverging + cmap
- [x] M5: spec model + JSON round-trip + renderer + fluent builder
- [x] M6: pure reducer + actions + store (functional core / imperative shell)
- [x] M6b: theme presets + TeX-aware WYSIWYG preview
- [x] M7: layer coverage (line/scatter/bar/errorbar/band/hline/vline/text/
      annotate) + multi-panel layouts
- [x] M7b: zero-dependency pure core split + ruff lint
- [x] M8: JSON schema/capabilities export (`schemas/`) + CI sync checks
      (Rust readiness)
- [x] M8b: pure spec validation (`validate`/`assert_valid`), auto-invoked
      before rendering
- [x] M8c: CLI (`python -m mudplot capabilities|schema|validate|render`)
- [x] M8d: more layers (hist/box), suptitle, auto panel labels, width/height
      ratios
- [x] M8e: `Store.undo()`/`redo()`
- [x] M9: expanded render coverage — heatmap, continuous colour-mapped
      scatter+colorbar, secondary y-axis (twin), shared axes
      (sharex/sharey), despine (spine offset), outside legends
- [x] M9b: design quality — colour+marker+line-style redundant encoding
      (`theme.redundant_encoding`), palette `lightness_jitter` for
      greyscale safety, `Palette.report()`
- [x] M10: automatic docs generation — `mudplot.docs` (reuses capabilities/
      schema, `docs/REFERENCE.md`, CI sync check) + `python -m mudplot docs`
- [x] M11: human-facing dashboard (separate package) — a static docs+design
      gallery site generator built from the engine's own introspection
      (`python -m dashboard`)
- [x] M11b: stability hardening pass #1 — 10 real bugs found/fixed (see
      §4c2), cross-module consistency tests added
- [x] M11c: a local interactive editor prototype (`python -m dashboard
      serve`), driving the same Store/actions/reducer as the fluent API
- [x] M11d: stability hardening pass #2 — 3 more real bugs found/fixed
      (capabilities() under-reporting, categorical x-axis crash, the
      deeper lazy-attribute root cause), see §4c2 "Follow-up audit"
- [x] M12: expanded plot coverage toward matplotlib/seaborn breadth —
      3-D (`scatter3d`/`line3d`/`surface`/`wireframe`), `violin`, `kde`,
      `contour`/`contourf`, `pie` (21 layer types total); 2 more bugs
      found/fixed (pie legend duplication, the render.py→_render.py
      rename), see §4f and §4c2 "Follow-up audit #2"
- [x] M12b: stability hardening pass #3 — 7 more real bugs found/fixed
      (categorical positions disagreeing across layers/twins/shared panels,
      grouped continuous scatter using independent colour normalizations,
      3-D panels ignoring axis scale/limits/legend/labels, palette-size
      under-counting independent series and pie slices, `Store` leaking
      mutable state through its return values/history/listeners, `save()`
      silently cropping the configured figure size); geometry/axis
      validation hardened; regression coverage in `tests/test_stabilization.py`.
- [x] M12c: three named, pre-verified qualitative palette presets
      (`paper`/`vivid`/`soft`, `mudplot.capabilities()["palette_presets"]`)
      each measured (not assumed) CVD-safe + true-greyscale-safe up to a
      documented category count; bar/box/violin fills also cycle a hatch
      pattern per group by default so grouped fills stay distinguishable
      after black & white printing regardless of colour count. See
      `docs/DEMO.md` §4/§5 for a real, pixel-converted B&W-print
      demonstration (not a mockup) and `tests/test_palette_presets.py`.
- [x] **v0.1.0 released** (first tagged release).
- [x] M12d: TeX single/double-column figure sizing (`Plot.tex_size()`);
      overlap-free layout pass (`_autofit`) using matplotlib's own
      constrained-layout engine and text-measurement renderer -- wraps
      overflowing titles/suptitle, reserves canvas space for named
      "outside ..." legends, no custom layout system, no-op when nothing
      would clip. `LegendSpec.bbox_to_anchor` / `PanelSpec.title_position`
      / `SetLayerAt` for pinning a legend/title/annotation to an exact
      spot. Dashboard editor gained: htmx partial-page updates (vendored,
      0BSD, no new Python dependency), draggable handles for the legend/
      title/annotations directly on the preview (mouse or arrow keys), a
      visual redesign, and Editor/Docs tabs sharing one running server.
      See `tests/test_layout.py`, `tests/test_dashboard_editor.py`.
- [ ] M13: Rust askama+tokio+htmx editor (separate crate)

See [`ROADMAP.md`](ROADMAP.md) for concrete, prioritised next steps beyond
this list.

## 9. Acceptance criteria

- Conversion: round-trip error < 1e-6, matches published reference values.
- Palettes: report the minimum ΔE00 under normal vision + protan/deutan.
- **Spec: build → to_json → from_json → identical spec (lossless
  round-trip)**.
- **Spec → render determinism: the same spec always produces the same
  figure.**
- Visual regression: gallery images.
