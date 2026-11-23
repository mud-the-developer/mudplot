# FigureSpec, CLI and local editors

`FigureSpec` **0.1** is the shared wire format. Keep the original before editing an older file. See the [compatibility policy](COMPATIBILITY.md), [JSON Schema](../schemas/figure_spec.schema.json) and [engine reference](REFERENCE.md).

## Save/load a spec (the same format used by the Rust editor)

```python
p = mp.plot(data).line("x", "y")
json_text = p.to_json()               # .mplot.json
p2 = mp.Plot.from_json(json_text)     # lossless round-trip
fig = p2.render()
```

## JSON capabilities and actions

The engine is designed to be machine-friendly: an agent can explore, build,
and render entirely through text/JSON (the human-facing side is
`dashboard/`):

```python
import mudplot as mp

caps = mp.capabilities()   # layers/themes/journals/TeX presets/action vocabulary
schema = mp.json_schema()  # full FigureSpec JSON Schema

spec = mp.apply([          # build from JSON actions without render/I/O effects
    {"type": "SetData", "columns": {"x": [1, 2, 3], "y": [1, 4, 9]}},
    {"type": "AddLayer", "layer": {"type": "line", "x": "x", "y": "y"}},
    {"type": "SetAxisLabel", "axis": "x", "text": "X"},
    {"type": "SetTheme", "name": "paper"},
])
issues = mp.validate(spec)  # side-effect-free pre-render agent feedback
mp.save(spec, "fig.pdf")   # effect (calls assert_valid internally)

# build history (replay/undo)
p = mp.plot(data).line("x", "y").theme("paper")
log = p.action_log         # [{"type": "SetData", ...}, ...]
assert mp.apply(log).to_dict() == p.spec.to_dict()   # reproducible
```

## CLI (for agent/shell automation)

```bash
python -m mudplot capabilities                    # print engine capabilities as JSON
python -m mudplot schema --out s.json              # save the FigureSpec JSON Schema
python -m mudplot validate fig.mplot.json          # validate a saved spec
python -m mudplot render fig.mplot.json out.pdf    # render PNG/PDF/SVG/PGF by suffix
python -m mudplot apply fig.mplot.json action.json -o next.mplot.json
```

## Using the reducer / store directly

```python
from mudplot import Store, actions as A

store = Store()
store.subscribe(lambda spec, action: print("changed:", type(action).__name__))
store.dispatch(A.SetTheme("paper"))
store.dispatch(A.SetPalette(kind="qualitative", params={"hue_start": 30}))
spec = store.state          # defensive snapshot; mutate through actions
```

## Supported input data formats

`mp.plot(data)` auto-detects all of the following (the dependency-free core
never imports numpy/pandas directly — it uses duck typing):

```python
mp.plot({"x": [1, 2], "y": [3, 4]})           # dict of columns
mp.plot([{"x": 1, "y": 3}, {"x": 2, "y": 4}]) # records (list[dict])
mp.plot([[1, 3], [2, 4]])                     # 2-D rows -> auto-named c0, c1
mp.plot(df)                                   # pandas / polars DataFrame
mp.plot(np_structured_array)                  # numpy structured array
mp.plot(np_2d_array)                          # numpy 2-D -> c0, c1, ...
mp.plot(arrow_table)                          # pyarrow Table
mp.plot(cursor)                               # an executed DB-API cursor
mp.plot(conn, query="SELECT x, y FROM t WHERE run = ?", params=(run_id,))
                                              # parameterized DB-API query (sqlite)
```

Input adapters normalize common missing sentinels (`NaN`, `pd.NA`, `NaT`) to
JSON `null`, date/time values to ISO 8601 strings, and NumPy scalars to their
plain Python equivalents. Infinity and unsupported objects still fail strict
JSON validation instead of being silently rewritten. Column names must be
unique after string conversion; collisions are rejected rather than overwritten.

## Dashboard (human-facing docs + design gallery)

`dashboard/` is a separate source-tree package from the engine (a one-way
`dashboard → engine` dependency). It reuses the engine's `capabilities()` /
`reference_markdown()` and its renderer directly, producing a static site
where the **docs and the actual figures always stay in sync with the
engine**.

```bash
python -m dashboard --out dashboard/site_build
# open dashboard/site_build/index.html -> a Markdown reference of the
# engine's capabilities plus a design gallery (palette safety, redundant
# encoding, TeX preview, secondary axes, heatmaps, etc.)
```

## Rust editor

```bash
MUDPLOT_PYTHON="$PWD/.venv/bin/python" \
  cargo run --locked --manifest-path mudplot-editor/Cargo.toml
```

It shares the Python action/reducer contract instead of duplicating its
semantics. Its unauthenticated server rejects non-loopback binds/HTTP Hosts
and cross-origin browser mutations; scope and routes are documented in [`mudplot-editor/README.md`](../mudplot-editor/README.md).


The dashboard is built from the matching checkout. `python -m dashboard serve` starts the loopback editor; on its **Editor** tab, choose **Start from a sample → Complete figure drafts** to fill the Open form without applying it. See the [dashboard instructions](../dashboard/README.md) for open/export, keyboard handles and security limits.
