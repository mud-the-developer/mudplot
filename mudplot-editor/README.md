# mudplot Rust editor (M13, phase 1)

A local axum + Askama + htmx editor for the same `FigureSpec` and JSON actions
used by Python mudplot. It is intentionally in this repository and versioned
with the Python package so generated contracts cannot drift unnoticed.

## Run

From the repository root, after `uv sync --extra render`:

```bash
MUDPLOT_PYTHON="$PWD/.venv/bin/python" \
  cargo run --manifest-path mudplot-editor/Cargo.toml
```

Open <http://127.0.0.1:8766/>. Override the defaults with `--bind
LOOPBACK:PORT` and `--python PATH`, or `MUDPLOT_BIND` / `MUDPLOT_PYTHON`.

This is a local single-user tool with no authentication. Non-loopback bind
addresses are rejected.

## Phase-1 contract

- Rust owns the local HTTP session, undo/redo stacks, compiled templates, and
  htmx fragments.
- `FigureSpec` and action envelopes preserve every JSON field with serde.
- The Python pure core remains the only reducer/validator via
  `python -m mudplot apply`; rendering uses `python -m mudplot render`.
- Failed actions or renders do not mutate the current spec or history.
- htmx and its 0BSD license are reused from `dashboard/static/` rather than
  vendored a second time.

Routes: `GET /`, `/fig.png`, `/spec.json`, `/static/htmx.min.js`; `POST
/action` accepts an action JSON object; `/action/raw`, `/undo`, `/redo`, and
`/reset` return the `#app` htmx fragment.

Not in this slice: multi-user sessions, authentication, the full visual form
set from the Python prototype, import/vector export, or a native Rust
renderer. Add those only after the bridge and route contract prove useful.
