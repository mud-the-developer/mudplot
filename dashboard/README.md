# mudplot-dashboard (source-tree tool)

*[한국어 문서 / Korean docs: README.ko.md](README.ko.md)*

The human-facing tool, **separated from the `mudplot` engine**. The engine's
dependency-free declarative core has no UI dependency; the dashboard imports
the engine in one direction only. The engine wheel deliberately excludes
`dashboard/` and the Rust editor. Use a matching source checkout and its locked
render/dev environment; a successful `pip install mudplot` is not a standalone
editor installation.

```
dashboard ──▶ mudplot   (one-way dependency)
```

## What's here now

### 1. A static docs + design-gallery site generator

```bash
python -m dashboard build --out dashboard/site_build   # or just: python -m dashboard --out ...
# Open dashboard/site_build/index.html in a browser.
```

- `site.py` — builds the engine reference from `mudplot.reference_markdown()`
  / `mudplot.capabilities()`, renders executable examples for every registered layer,
  and generates design-principle images (palette CVD/greyscale safety,
  redundant encoding, TeX WYSIWYG, secondary axes/heatmaps, etc.), bundling
  an index plus a self-contained reading review under `reading/`.
- `plot_gallery.py` + `../examples/plots/` — one runnable source file per
  registered layer. CI requires exact coverage, validates every resulting
  spec, round-trips it through JSON, and renders it with the live engine.
- `markdown_lite.py` — a tiny converter that only handles the Markdown
  subset mudplot itself generates (zero dependencies, stdlib only).
- **Reading examples are built from the same source as the editor drafts**:
  `reading/VISUAL_REVIEW.html` includes 700px/320px layouts, captions and numerical
  lookup, SVG/PDF/editable exports and locally rendered criteria pages. Source
  data, canonical specs and local links are tested. Curated explanations and
  aesthetic/readability judgments still need review; generated does not mean
  automatically good.

### 2. A local interactive editor

```bash
python -m dashboard serve            # http://127.0.0.1:8765/
python -m dashboard serve --port 9000
```

Under **Start from a sample → Complete figure drafts**, choose Response or
Endpoint at 700px or 320px. The link only prefills the **Open** form: the current
figure, PNG and action history remain unchanged. Review the draft and export any
current work before pressing **Open figure**; an accepted import starts fresh
undo history, as for opening a saved spec. Invalid imports preserve both the
current figure and the submitted JSON so it can be corrected. The editor opts
out of htmx's localStorage page-body history cache. Its workspace preview can be
scaled; use actual-size review/exports to judge delivered dimensions.

The running editor has two tabs (top nav): **Editor** and **Docs** — the
same engine reference as the static site's, served live from
`mp.reference_markdown()` so it can't drift from the running engine, without
needing a separate `dashboard build` process.

- `editor_server.py` / `editor_view.py` — a deliberately dependency-light,
  loopback-only local editor: Python's stdlib `http.server` (no web framework) plus
  `mudplot[render]`, plus one vendored, dependency-free JS file
  (`dashboard/static/htmx.min.js`, [htmx 1.9.12](https://github.com/bigskysoftware/htmx/releases/tag/v1.9.12),
  0BSD licensed) for partial-page updates. Packaging pins the official file's
  SHA-256 in `scripts/check_wheel.py`. It accepts only loopback binds/Hosts and
  same-origin mutations, bounds request/form bodies, and sends CSP plus
  `Cache-Control: no-store` on every response. Figure edits build real `Action`s
  and dispatch them through the *exact same* `Store`/reducer the fluent API
  uses — there is no separate editor-only state model. Native forms also have
  explicit POST actions, so missing/not-yet-wired JavaScript cannot put input
  values in GET URLs. Referrer policy is same-origin (none to external sites),
  without relaxing Origin/cross-site mutation rejection. Request bodies use
  Content-Length framing up to16MiB; unsupported Transfer-Encoding (including
  chunked), duplicate lengths and incomplete bodies are rejected before actions.
  No new chunked decoder is implied; normal bodyless local actions still work.
- Load sample data; tweak theme/journal/palette; edit the grid, active panel,
  Cartesian/polar/3-D projection, x/y/z scales and fixed/automatic limits, secondary y-axis,
  labels, references, suptitle, and size; add common
  series/annotations through quick forms or **any registered layer type**
  through a capabilities-driven checked-JSON form; undo/redo; or send
  a raw JSON action (the same shape an AI agent uses). The preview, layer
  list, and action log update **in place** after every change (an htmx partial
  swap of `#app-body`, not a full page navigation).
- Errors (bad theme name, missing column, malformed JSON, invalid spec, or
  render failure) are caught before committing the action/import and shown as
  a banner instead of crashing the server or corrupting editor history.
- Open a saved `.mplot.json`; export the current state as `.mplot.json`, a
  screen-preview PNG, or exact-size PDF/SVG. Preview rendering retains the
  configured DPI until either axis would exceed 2000 pixels; the spec and
  final exports remain unchanged.
- **Drag directly on the preview**: the Position panel's "Enable" buttons
  add a coloured handle over the figure for the **legend** (blue ✥) and
  **panel title** (purple T); any `text`/`annotate` layer gets a handle
  (green •) automatically. Drag with the mouse, or click a handle and use
  the arrow keys (Shift for a bigger step). These dispatch
  `SetLegend(bbox_to_anchor=...)`, `SetTitlePosition(...)`, and
  `SetLayerAt(...)` respectively — the same actions
  `.legend(bbox_to_anchor=...)`/`.title_position(...)`/`.set_layer_at(...)`
  use from the fluent API. "Reset" restores the named `location`/default.
  Legend anchors are figure fractions and manual titles are axes fractions;
  text/annotation anchors remain data values on their selected primary/y2 axis,
  including its actual log/inverted limits. Size/DPI changes do not change those
  meanings. This does not add unsupported non-Cartesian annotation modes.
- This is intentionally a *thin* UI: `editor_view.py` has no I/O (pure HTML
  string building, unit-testable on its own), and `editor_server.py` is
  just wiring around the engine's `Store` (plus caching the last render's
  PNG bytes and a bit of layout info the drag handles need — see
  `EditorSession.refresh()`).

## Engine APIs it reuses

The Python editor does not have its own state logic — it reuses the engine's
**action / reducer / store** directly. UI event → `Action` → `store.dispatch` → new
`FigureSpec` → `render`/`tex_preview` refreshes the screen.

```python
from mudplot import Store, actions as A, tex_preview

store = Store()
store.subscribe(lambda spec, action: rerender(spec))
store.dispatch(A.SetTheme("paper"))
store.dispatch(A.SetPalette(kind="qualitative", params={"hue_start": 30}))
```

The Rust (Askama+tokio+htmx) editor uses the same structure: capability-driven
controls and agent JSON both call `mudplot apply`, preserving Python reducer
semantics before `mudplot render` refreshes or exports the figure.

## Roadmap

1. **(done)** static docs+gallery site (`python -m dashboard build`)
2. **(done)** a Python local interactive editor (`python -m dashboard serve`),
   reusing the same Store
3. **(v1 essentials done)** the co-versioned `mudplot-editor/`
   Rust crate, sharing the JSON contract through the Python CLI and supporting
   visual controls, open, and vector export
