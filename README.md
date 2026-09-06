# mudplot

*[한국어 문서 / Korean docs: README.ko.md](README.ko.md)*

A Python plotting library for scientific papers, built on Matplotlib. It
provides **perceptually uniform, colourblind-safe** colour palettes and
styles.

At its core is an **LCH (CIELAB polar coordinates) colour engine**:

- **Equal lightness (fixed L\*)** → fair under greyscale printing / contrast
- **Maximum contrast** → maximises the minimum perceptual colour distance
  (CIEDE2000) between colours
- **Colourblind-aware** → optimises the worst-case contrast across normal
  vision and protanopia/deuteranopia simulation (measured via
  `Palette.report()`, not a certified accessibility guarantee); see
  [named, pre-verified presets](docs/DEMO.md#4-colour-palette-presets-measured-not-assumed)
  below
- **Black & white print-safe** → grouped bar/box/violin fills also cycle a
  hatch pattern by default, so groups stay distinguishable even where
  colours compress to similar greys — see the
  [B&W print demo](docs/DEMO.md#5-grouped-bar-chart-readable-after-black--white-printing)

## Architecture: spec-centric + pure reducer (functional core / imperative shell)

Every bit of figure state is represented as a **serialisable, declarative
`FigureSpec`**, and all state transitions go through a **pure reducer**.
Effects (render/io/preview) are pushed to the edges.

```
 Action (pure data)
     │
     ▼  reduce(state, action) -> state'      ─┐ functional core (pure)
 FigureSpec (dataclass ⇆ JSON, .mplot.json) ─┘
     │
     ▼  render / io / preview                ── imperative shell (effects)
 matplotlib → PNG/PDF/SVG
```

- The fluent builder is just **sugar for dispatching actions** — a `Store`
  drives the reducer underneath.
- The `mudplot/` engine has no UI dependency. `dashboard/` is a separate
  package (see below).
- Python and a future Rust GUI would only ever need to agree on the same
  action/JSON schema.

## Status

**v0.3.0**, pre-1.0 and moving fast. See [`DESIGN.md`](DESIGN.md) for
architecture and the full milestone log, [`CHANGELOG.md`](CHANGELOG.md) for
version-by-version detail, and [`ROADMAP.md`](ROADMAP.md) for concrete next
steps (more layer types, dashboard editor gaps, the Rust editor).

**Engine (`mudplot/`) — usable now, 345 tests passing:**

- [x] Colour engine: sRGB ↔ linear ↔ XYZ ↔ Lab ↔ LCH (numpy-only); CIE76/
      CIEDE2000 colour difference (Sharma 2005 reference values); Machado
      2009 colour-vision-deficiency simulation; qualitative/sequential/
      diverging palette generators + preview
- [x] **Three named, pre-verified qualitative palette presets**
      (`paper`/`vivid`/`soft`) — measured (not assumed) CVD-safe and
      true-greyscale-safe up to a documented category count; bar/box/violin
      fills cycle a hatch pattern per group by default so they stay
      distinguishable in black & white print regardless of colour count
- [x] Declarative spec model (`FigureSpec`) + lossless JSON round-trip +
      pure reducer + actions + store (`Store.undo()`/`redo()`) — effects
      (render/io/preview) kept at the edges
- [x] Renderer: 21 layer types (line/scatter/bar/errorbar/band/hline/vline/
      text/annotate/hist/box/violin/kde/heatmap/contour/contourf/pie/
      scatter3d/line3d/surface/wireframe), multi-panel layouts, secondary
      y-axis, shared axes, despine, outside legends, continuous colour
      mapping + colorbar
- [x] **TeX-ready sizing and overlap-free layout**: `.tex_size(preset,
      columns=1|2)` sizes the actual figure to a document column/full text
      width; `render()` wraps overflowing titles and reserves canvas space
      for outside legends automatically (matplotlib's own layout engine +
      text-measurement renderer, no custom layout system) so figures stay
      at their exact configured physical size without clipped/overlapping
      text — also the basis of the TeX-aware WYSIWYG `.preview()`
      (article/ieee/revtex/nature/acm)
- [x] **Exact-position placement**: pin the legend
      (`.legend(bbox_to_anchor=...)`), a panel title (`.title_position(...)`),
      or a `text`/`annotate` layer (`.set_layer_at(...)`) to an exact spot —
      also what the interactive editor's drag handles dispatch
- [x] **LaTeX-native references**: attach a BibTeX key and/or URL to a legend
      entry or panel title; `.pgf` export emits `\figcite{}`/`\href{}` for
      the paper's own bibliography and hyperref to resolve, SVG gets a
      clickable link, raster stays plain (verified by compiling a real paper
      with tectonic and reading the numbers back out of the PDF)
- [x] Zero dependencies in the pure core (numpy/matplotlib are effect-only
      extras); broad input-format support (dict/records/DataFrame/numpy/
      pyarrow/SQL); AI-agent-friendly interface (`capabilities()`/
      `json_schema()`/`apply()`/`action_log`); pure `validate()`/
      `assert_valid()` run automatically before rendering
- [x] CLI (`python -m mudplot capabilities|schema|docs|validate|render`);
      JSON schema/capabilities/docs export files + CI sync checks
- [x] Three stability-hardening passes, ~20 real bugs found/fixed and
      locked in with regression tests (journal size not applied, `Store`
      state leaking external mutations, categorical axis positions
      disagreeing across layers/panels, `save()` silently cropping the
      configured size, and more) — see `DESIGN.md` §4c2 and
      `tests/test_bugfixes.py`/`tests/test_stabilization.py`

**Dashboard (`dashboard/`, separate package) — human-facing, prototype-grade:**

- [x] Static docs + design-gallery site generated straight from the
      engine's own introspection (`python -m dashboard build`)
- [x] Local interactive editor (`python -m dashboard serve`) driving the
      exact same Store/actions/reducer as the fluent API — **Editor**/
      **Docs** tabs in one running server, htmx partial-page updates (no
      full reloads; vendored, 0BSD, no new Python dependency), and
      draggable handles to reposition the legend/title/annotations
      directly on the preview (mouse or arrow keys)
- [x] Canvas-first layout, multi-panel editing (grid + per-panel controls),
      direct title/axis/citation editing, open a saved `.mplot.json`, and
      export PDF/SVG at the exact configured size
- [x] Real-browser test coverage (Playwright, optional `browser` extra) for
      the drag/keyboard/multi-panel paths that HTML-level tests can't see
- [ ] Remaining layer types in the editor UI, and replacing the
      full-body swap with targeted updates — see `ROADMAP.md` §2
- [ ] Rust interactive editor (separate crate) — see `ROADMAP.md` §3

## Installation

```bash
# Pure engine only (zero dependencies) — spec/actions/reducer/store/io/tex sizing
pip install mudplot

# Colour engine + rendering (numpy + matplotlib)
pip install "mudplot[render]"
```

Development:

```bash
uv venv && uv pip install -e ".[dev]"
```

### Dependency layers

| layer | modules | dependencies |
|---|---|---|
| pure engine | `spec` `actions` `reducer` `store` `io` `tex` (sizing) | **none** |
| colour engine | `color/*` | numpy |
| render effect | `render` `tex_preview` | numpy + matplotlib |

## Rendered demo

![Actual mudplot output from a synthetic pandas DataFrame: line, scatter, violin and KDE](docs/images/pandas_demo.png)

Generated by `python -m scripts.render_docs_demo` using a seeded pandas
DataFrame, not experimental measurements. See the **[demo gallery](docs/DEMO.md)**
for editing before/after, heatmap + 3-D output, **named colour-palette presets
measured CVD-safe and true-greyscale-safe**, a grouped bar chart verified
readable after simulated black & white printing, vector PDFs, editable JSON,
and runnable checks. Requires pandas in addition to `mudplot[render]`.

## Usage

### Intuitive fluent builder

```python
import mudplot as mp

(mp.plot(data)                        # any of the formats below
    .line(x="voltage", y="current", group="order")
    .labels(x="Voltage (mV)", y="Current (μA)")
    .legend(title="Order")
    .theme("paper").journal("nature")
    .palette("qualitative", hue_start=30)
    .save("fig.pdf"))
```

`save()` preserves the configured figure size; use `save("fig.pdf", tight=True)`
to crop to content instead. The returned Matplotlib figure remains open; close
it with `plt.close(fig)` when finished. `Plot.spec` and `Store.state` are isolated
snapshots: edit through builder methods/actions, not by mutating these snapshots.

### Supported plot types

| category | types | notes |
|---|---|---|
| basic | `line`, `scatter`, `bar`, `errorbar`, `band` | `group=` for multiple series; bars auto-dodge when grouped; categorical or numeric x |
| distributions | `hist`, `box`, `violin`, `kde` | `kde` uses a small numpy-only Gaussian KDE (no scipy dependency) |
| 2-D fields | `heatmap`, `contour`, `contourf` | share a matrix registered via `.matrix(name, values)`; use the same LCH colormaps as the palettes |
| 3-D | `scatter3d`, `line3d`, `surface`, `wireframe` | panel needs `.projection3d()` first; mixable with 2-D panels in the same figure |
| annotations | `hline`, `vline`, `text`, `annotate` | |
| other | `pie` | |

Most types support a continuous colour mapping (`c=` + `colorbar=True`),
a secondary y-axis (`axis="y2"`), multi-panel layouts, and redundant
marker/line-style encoding for series (see `mp.capabilities()` for the
exact, always-up-to-date field list per type).

```python
# distributions side by side
(mp.plot(data).layout(1, 2)
    .violin("value", group="condition", panel=0)
    .kde("value", group="condition", panel=1))

# a 3-D scatter, colour-mapped by a fourth variable
(mp.plot(data).projection3d()
    .scatter3d("x", "y", "z", c="temperature", colorbar=True))

# a scalar field as a heatmap + contour
(mp.plot({}).matrix("field", grid_values)
    .heatmap("field").contour("field", levels=8))
```

### Save/load a spec (same format a future Rust editor would use)

```python
p = mp.plot(data).line("x", "y")
json_text = p.to_json()               # .mplot.json
p2 = mp.Plot.from_json(json_text)     # lossless round-trip
fig = p2.render()
```

### TeX WYSIWYG preview

```python
# Preview at the exact size/font it will have in the paper (mock text
# column + caption)
fig = (mp.plot(data).line("voltage", "current", group="order")
         .labels(x="Voltage (mV)", y="Current")
         .preview(tex="ieee", caption="Figure 1. ..."))
```

### Sizing the actual figure for a one- or two-column layout

`.tex_size(...)` applies the same column-width/font sizing as `.preview()`,
but to the figure you actually `.render()`/`.save()` — not just a mock
preview. Every layer (long titles, outside legends) is then laid out to fit
that exact size without clipping or overlap (see "Layout" below).

```python
p.tex_size("ieee", columns=1)   # a single column's width
p.tex_size("nature", columns=2) # spans the full text width (figure*)
```

### Layout: no clipped or overlapping text, at the exact configured size

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

### Citations and links inside the figure (LaTeX-native)

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
|---|---|---|
| `.pgf` | `\figcite{key}` — numbered by the paper's bibliography | `\href{url}{...}` via hyperref |
| `.svg` | dropped (nothing to resolve against) | the text becomes a clickable link |
| `.png`/`.pdf` | dropped | dropped |

Metadata is substituted into LaTeX source verbatim, so `validate()` rejects
braces/backslashes in these two fields.

### Placing the legend, title, or an annotation at an exact spot

```python
p.legend(bbox_to_anchor=[0.8, 0.5])   # figure-fraction [x, y], overrides location
p.legend(location="upper left")       # bbox_to_anchor=None restores named locations
p.title_position([0.1, 0.85])         # axes-fraction [x, y]; None restores default
p.set_layer_at(layer_index, [3, 0.5]) # move a text/annotate layer (data coords)
```

This is also what the interactive editor's draggable handles use (mouse or
arrow keys, right on the preview) — see `dashboard/README.md`.

### For AI agents (drive everything via JSON)

The engine is designed to be machine-friendly: an agent can explore, build,
and render entirely through text/JSON (the human-facing side is
`dashboard/`):

```python
import mudplot as mp

caps = mp.capabilities()   # layers/themes/journals/TeX presets/action vocabulary
schema = mp.json_schema()  # full FigureSpec JSON Schema

spec = mp.apply([          # build a figure from JSON actions alone (pure reduce)
    {"type": "SetData", "columns": {"x": [1, 2, 3], "y": [1, 4, 9]}},
    {"type": "AddLayer", "layer": {"type": "line", "x": "x", "y": "y"}},
    {"type": "SetAxisLabel", "axis": "x", "text": "X"},
    {"type": "SetTheme", "name": "paper"},
])
issues = mp.validate(spec)  # self-check before rendering (pure, agent feedback)
mp.save(spec, "fig.pdf")   # effect (calls assert_valid internally)

# build history (replay/undo)
p = mp.plot(data).line("x", "y").theme("paper")
log = p.action_log         # [{"type": "SetData", ...}, ...]
assert mp.apply(log).to_dict() == p.spec.to_dict()   # reproducible
```

### CLI (for agent/shell automation)

```bash
python -m mudplot capabilities                    # print engine capabilities as JSON
python -m mudplot schema --out s.json              # save the FigureSpec JSON Schema
python -m mudplot validate fig.mplot.json          # validate a saved spec
python -m mudplot render fig.mplot.json out.pdf    # render
```

### Using the pure reducer / store directly

```python
from mudplot import Store, actions as A

store = Store()
store.subscribe(lambda spec, action: print("changed:", type(action).__name__))
store.dispatch(A.SetTheme("paper"))
store.dispatch(A.SetPalette(kind="qualitative", params={"hue_start": 30}))
spec = store.state          # purely accumulated state
```

### Supported input data formats

`mp.plot(data)` auto-detects all of the following (the pure core never
imports numpy/pandas directly — it uses duck typing):

```python
mp.plot({"x": [1, 2], "y": [3, 4]})           # dict of columns
mp.plot([{"x": 1, "y": 3}, {"x": 2, "y": 4}]) # records (list[dict])
mp.plot([[1, 3], [2, 4]])                     # 2-D rows -> auto-named c0, c1
mp.plot(df)                                   # pandas / polars DataFrame
mp.plot(np_structured_array)                  # numpy structured array
mp.plot(np_2d_array)                          # numpy 2-D -> c0, c1, ...
mp.plot(arrow_table)                          # pyarrow Table
mp.plot(cursor)                               # an executed DB-API cursor
mp.plot(conn, query="SELECT x, y FROM t")     # DB-API connection + query (sqlite, etc.)
```

### Using palettes directly

```python
pal = mp.color_palette(5, "qualitative")   # equal lightness, max contrast
print(pal.hex, pal.min_delta_e())
print(pal.report())      # {'cvd_safe': True, 'grayscale_safe': ..., 'note': ...}
cmap = mp.color_palette(256, "sequential").to_cmap()

# Named, pre-verified presets (measured CVD-safe + true-greyscale-safe up to
# a documented category count -- see mp.capabilities()["palette_presets"]):
pal = mp.color_palette(6, "qualitative", preset="paper")   # or "vivid" / "soft"
p = mp.plot(data).line("x", "y", group="g").palette(preset="paper")

# Bar/box/violin fills also cycle a hatch pattern per group by default
# (ThemeSpec.hatches), so grouped fills stay distinguishable in black &
# white print regardless of how many colours are used.
p2 = mp.plot(data).bar("category", "value", group="g")  # colour + hatch
p3 = p2.encoding(redundant_encoding=False)               # colour only
```

### Dashboard (human-facing docs + design gallery)

`dashboard/` is a separate package from the engine (a one-way dependency:
engine → dashboard). It reuses the engine's `capabilities()` /
`reference_markdown()` and its renderer directly, producing a static site
where the **docs and the actual figures always stay in sync with the
engine**.

```bash
python -m dashboard --out dashboard/site_build
# open dashboard/site_build/index.html -> a Markdown reference of the
# engine's capabilities plus a design gallery (palette safety, redundant
# encoding, TeX preview, secondary axes, heatmaps, etc.)
```

## Development

```bash
uv run pytest        # or .venv/bin/python -m pytest
```
