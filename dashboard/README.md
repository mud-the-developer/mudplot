# mudplot-dashboard (separate package)

*[한국어 문서 / Korean docs: README.ko.md](README.ko.md)*

The human-facing tool, **separated from the `mudplot` engine**. The engine
(pure core) has no UI dependency at all; the dashboard imports the engine in
one direction only.

```
dashboard ──▶ mudplot   (one-way dependency)
```

## What's here now

### 1. A static docs + design-gallery site generator

```bash
python -m dashboard build --out dashboard/site_build   # or just: python -m dashboard --out ...
open dashboard/site_build/index.html
```

- `site.py` — builds the engine reference from `mudplot.reference_markdown()`
  / `mudplot.capabilities()`, and uses the engine's renderer to generate
  gallery images demonstrating its design principles (palette CVD/greyscale
  safety, redundant encoding, TeX WYSIWYG, secondary axes/heatmaps, etc.),
  bundling everything into one HTML page.
- `markdown_lite.py` — a tiny converter that only handles the Markdown
  subset mudplot itself generates (zero dependencies, stdlib only).
- **The docs and the figures always match the engine**: both are produced by
  live engine calls, so they can never go stale the way hand-written docs
  can.

### 2. A local interactive editor (prototype)

```bash
python -m dashboard serve            # http://127.0.0.1:8765/
python -m dashboard serve --port 9000 --host 0.0.0.0
```

The running editor has two tabs (top nav): **Editor** and **Docs** — the
same engine reference as the static site's, served live from
`mp.reference_markdown()` so it can't drift from the running engine, without
needing a separate `dashboard build` process.

- `editor_server.py` / `editor_view.py` — a deliberately dependency-light
  local editor: Python's stdlib `http.server` (no web framework) plus
  `mudplot[render]`. Every click/form submit builds a real `Action` and
  dispatches it through the *exact same* `Store`/reducer the fluent API
  uses — there is no separate editor-only state model.
- Load sample data, tweak theme/journal/palette, add layers, edit the
  suptitle/size, undo/redo, or drop in a raw JSON action (the same shape an
  AI agent would send via `mp.apply([...])`) — the live preview
  (`/fig.png`) and the action log update after every change.
- Errors (bad theme name, missing column, invalid spec) are caught and
  shown as a banner instead of crashing the server.
- Export the current state as `.mplot.json` (`/spec.json`) or a PNG
  (`/fig.png`).
- **Drag the legend directly on the preview**: "Enable drag positioning" in
  the Legend position panel adds a ✥ handle over the figure — drag it with
  the mouse, or click it and use the arrow keys (Shift for a bigger step).
  Each drop/press dispatches `SetLegend(bbox_to_anchor=[x, y])` (figure-
  fraction coordinates), the same action `.legend(bbox_to_anchor=...)` uses
  from the fluent API. "Reset" clears it back to a named `location`.
- This is intentionally a *thin* UI: `editor_view.py` has no I/O (pure HTML
  string building, unit-testable on its own), and `editor_server.py` is
  just wiring around the engine's `Store`.

## Engine APIs it reuses

Once an interactive editor exists (see the roadmap below), it won't have
its own state logic — it will reuse the engine's **action / reducer /
store** directly. UI event → `Action` → `store.dispatch` → new
`FigureSpec` → `render`/`tex_preview` refreshes the screen.

```python
from mudplot import Store, actions as A, tex_preview

store = Store()
store.subscribe(lambda spec, action: rerender(spec))
store.dispatch(A.SetTheme("paper"))
store.dispatch(A.SetPalette(kind="qualitative", params={"hue_start": 30}))
```

This structure carries over directly to a future Rust
(askama+tokio+htmx) editor: the UI sends the same actions (as JSON), the
same reducer semantics update the `FigureSpec`, and it gets re-rendered.

## Roadmap

1. **(done)** static docs+gallery site (`python -m dashboard build`)
2. **(done)** a Python prototype interactive editor (`python -m dashboard serve`),
   reusing the same Store
3. A Rust (askama+tokio+htmx) editor — a separate crate, sharing the same
   JSON action/schema contract
