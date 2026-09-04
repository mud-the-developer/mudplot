# mudplot

*[한국어 문서 / Korean docs: README.ko.md](README.ko.md)*

A Python plotting library for scientific papers, built on Matplotlib. It
provides **perceptually uniform, colourblind-safe** colour palettes and
styles.

At its core is an **LCH (CIELAB polar coordinates) colour engine**:

- **Equal lightness (fixed L\*)** → fair under greyscale printing / contrast
- **Maximum contrast** → maximises the minimum perceptual colour distance
  (CIEDE2000) between colours
- **Colourblind-safe** → worst-case optimisation across normal vision and
  protanopia/deuteranopia simulations

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

Early development. See [`DESIGN.md`](DESIGN.md) for architecture and past
milestones, [`CHANGELOG.md`](CHANGELOG.md) for what's shipped, and
[`ROADMAP.md`](ROADMAP.md) for concrete next steps.

- [x] Colour conversion engine (sRGB ↔ linear ↔ XYZ ↔ Lab ↔ LCH), numpy-only
- [x] Colour difference (CIE76, CIEDE2000) — passes Sharma 2005 reference values
- [x] Colour-vision-deficiency simulation (Machado 2009)
- [x] Palette generators (qualitative / sequential / diverging) + preview
- [x] Declarative spec model + JSON round-trip + renderer + fluent builder
- [x] Pure reducer + actions + store (effects separated)
- [x] TeX-aware WYSIWYG preview (article/ieee/revtex/nature/acm)
- [x] Layer coverage: line/scatter/bar/errorbar/band/hline/vline/text/annotate/
      hist/box/heatmap/violin/kde/pie/contour/contourf + multi-panel layouts
- [x] 3-D plots: scatter3d/line3d/surface/wireframe, mixable with 2-D panels
      in the same figure
- [x] Zero dependencies in the pure core (numpy/matplotlib are effect-only extras)
- [x] ruff lint rules + CI
- [x] Broad input-format support (dict/records/DataFrame/numpy/pyarrow/SQL)
- [x] AI-agent-friendly interface (capabilities/json_schema/apply/action_log)
- [x] Stability hardening pass: 10 real bugs found, fixed, and locked in with
      regression tests (journal size not applied, panel-label font mismatch,
      TeX preview size ~2x inflation, `SetData` wiping `matrices`, string
      lists shredded character-by-character, O(n²) palette perf/duplicate
      colours, `Store` state leaking external mutations, raw CLI tracebacks,
      inconsistent secondary-axis routing, overlapping grouped bars) — see
      `DESIGN.md` §4c2 and `tests/test_bugfixes.py`
- [x] More layers: histogram/boxplot/heatmap, continuous colour-mapped
      scatter+colorbar
- [x] Paper-ready finishing touches: suptitle, auto panel labels (a/b/c),
      width/height ratios
- [x] Render coverage: secondary y-axis (twin), shared axes
      (sharex/sharey), despine (spine offset), outside legends
- [x] Design quality: colour+marker+line-style redundant encoding, palette
      `lightness_jitter` for greyscale safety, `Palette.report()`
- [x] Pure spec validation (`validate`/`assert_valid`) + automatic
      pre-render checks
- [x] `Store.undo()`/`redo()`
- [x] CLI (`python -m mudplot capabilities|schema|docs|validate|render`)
- [x] JSON schema/capabilities/docs export files + CI sync checks
      (`schemas/`, `docs/`)
- [x] Human-facing dashboard: a static docs+gallery site generated straight
      from the engine's own introspection (`python -m dashboard`)
- [ ] Rust interactive editor (separate crate, later)

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
pal = mp.color_palette(5, "qualitative")   # equal lightness, max contrast, CVD-safe
print(pal.hex, pal.min_delta_e())
print(pal.report())      # {'cvd_safe': True, 'grayscale_safe': ..., 'note': ...}
cmap = mp.color_palette(256, "sequential").to_cmap()
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
