# mudplot Rust editor (M13, v0.6)

A local axum + Askama + htmx editor for the same `FigureSpec` and JSON actions
used by Python mudplot. It is intentionally in this repository and versioned
with the Python package so generated contracts cannot drift unnoticed.

## Run

From the repository root, after `uv sync --locked --extra render`:

```bash
MUDPLOT_PYTHON="$PWD/.venv/bin/python" \
  cargo run --locked --manifest-path mudplot-editor/Cargo.toml
```

Open <http://127.0.0.1:8766/>. Override the defaults with `--bind
LOOPBACK:PORT` and `--python PATH`, or `MUDPLOT_BIND` / `MUDPLOT_PYTHON`.

This is a local single-user tool with no authentication. Non-loopback bind
addresses, non-loopback HTTP Hosts, and cross-origin browser mutations are
rejected; all responses are `no-store` and carry restrictive CSP and browser
security headers.

## Contract and current scope

- Rust owns the local HTTP session, undo/redo stacks, compiled templates, and
  htmx fragments.
- `FigureSpec` and action envelopes preserve supported JSON fields, including
  integers beyond 64-bit range, with serde. Duplicate keys are rejected
  recursively. The sole reserved key, `$serde_json::private::Number`, is
  rejected by both Python and Rust because serde uses it internally for those
  arbitrary-precision numbers.
- The Python dependency-free core remains the only reducer/validator via
  `python -m mudplot apply`; rendering uses `python -m mudplot render`.
- Failed actions, imports, or renders do not mutate the current spec or
  history.
- Capabilities generate the all-layer selector/field reference plus theme and
  projection controls; title and exact figure-size controls use the same JSON
  actions as agents.
- Saved specs can be opened, and exact-size PDF/SVG plus JSON can be exported.
  Cached PNG previews retain the configured DPI until either axis would exceed
  2000 pixels, without changing the spec or final exports.
- htmx and its 0BSD license are reused from `dashboard/static/` rather than
  vendored a second time. Request bodies are bounded at 16 MiB, and Python
  bridge subprocesses time out after 120 seconds.

Routes: `GET /`, `/fig.{png,pdf,svg}`, `/spec.json`,
`/static/htmx.min.js`; `POST /action` accepts an action JSON object. Visual
controls use `/control/*` and `/layers`; `/open`, `/action/raw`, `/undo`,
`/redo`, and `/reset` return the `#app` htmx fragment.

Still deliberately out of scope: multi-user sessions/authentication, every
specialized axis/drag control from the mature Python editor, and a native Rust
renderer. Add them only when local usage warrants the extra state and code.
