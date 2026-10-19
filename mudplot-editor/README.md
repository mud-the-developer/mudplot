# mudplot Rust editor (v1.0)

A local axum + Askama + htmx editor for the same `FigureSpec` and JSON actions
used by Python mudplot. It is intentionally in this repository and versioned
with the Python package so generated contracts cannot drift unnoticed.
The engine wheel does not contain this editor or its dashboard assets. Build it
from the matching source checkout with that checkout's Python environment.

There is no automatic Python **package-label** handshake at editor startup.
Release preflight compares Python/project/Rust/Cargo.lock metadata; an engine
with incompatible spec/default or required capabilities fails through the real
bridge startup checks. A compatible runtime with a different package label can
still start, so use the matching checkout rather than treating acceptance as a
cross-release compatibility guarantee. Controlled version/capability probes and
served htmx hashes are recorded in `docs/review_evidence/editor_asset_verification.json`;
these are not tests of every historical published Python distribution.

## Run

From the repository root, after `uv sync --locked --extra render`:

```bash
MUDPLOT_PYTHON="$PWD/.venv/bin/python" \
  cargo run --locked --manifest-path mudplot-editor/Cargo.toml
```

Open <http://127.0.0.1:8766/>. Override the defaults with `--bind
LOOPBACK:PORT` and `--python PATH`, or `MUDPLOT_BIND` / `MUDPLOT_PYTHON`.
Interpreter precedence is `--python` > `MUDPLOT_PYTHON` > `python3` on PATH.
The executable and each argument are passed directly, not evaluated by a shell;
a bad explicit executable fails rather than falling back to another Python.
On Windows, for example:

```powershell
cargo run --locked --manifest-path mudplot-editor/Cargo.toml -- --python ".venv/Scripts/python.exe"
```

`uv run python scripts/check_python_bridge_paths.py` verifies a separate venv
with Unicode/spaces/`&` in executable and temporary data paths. It may download
same-version render wheels into that disposable venv; project dependencies stay
unchanged. Windows was executed locally; baselinee14 CI39111782233 also observed
successful Linux/Windows jobs including this probe. Later changes still need their
own CI result; the evidence is not a promise that every checkout was tested.

This is a local single-user tool with no authentication. Non-loopback bind
addresses, non-loopback HTTP Hosts, and cross-origin browser mutations are
rejected; application responses (including these rejections) are `no-store`
and carry restrictive CSP/browser headers. Same-origin requests and local agents
without an Origin remain supported; this is not remote-user authentication.

## Contract and current scope

- Rust owns the local HTTP session, undo/redo stacks, compiled templates, and
  htmx fragments.
- `FigureSpec` and action envelopes preserve supported JSON fields, including
  integers beyond 64-bit range, with serde. Duplicate keys are rejected
  recursively. The sole reserved key, `$serde_json::private::Number`, is
  rejected by both Python and Rust because serde uses it internally for those
  arbitrary-precision numbers. Original key tokens are checked before serde can
  reinterpret literal reserved-key objects; the same spelling in a string value
  remains text. Omitted spec versions use the embedded current default, matching
  Python; explicit null/unknown versions still fail. This is structural JSON preservation; numeric
  coordinates/styles outside the renderer's floating-point range fail cleanly.
- The Python dependency-free core remains the only reducer/validator via
  `python -m mudplot apply`; rendering uses `python -m mudplot render`.
  Successful stdout remains complete; failed stderr captures at most64KiB raw
  plus a truncation marker before becoming a UI error. UTF-8 replacement can
  expand display bytes; this is not a disk/CPU or descendant-process hard bound.
  Missing or empty render artifacts are rejected before preview/cache commit or
  export, even if the child exited successfully; this is not a full binary decoder.
  On the measured Windows/uv-venv setup, keep cwd/TMP short and use absolute long
  data paths. A long TMP blocked even interpreter startup, independently of capture;
  long TEMP with short TMP passed. Verify the selected interpreter first; the bridge
  does not silently switch interpreters or promise general process-tree cleanup.
- Failed actions, imports, or renders do not mutate the current spec or
  history. Successful open/reset are undoable snapshots in this Rust editor;
  Python open/reset instead start fresh history. Successful new edits clear redo.
- Capabilities generate the all-layer selector/field reference plus theme and
  projection controls; title and exact figure-size controls use the same JSON
  actions as agents.
- Saved specs can be opened, and exact-size PDF/SVG plus JSON can be exported.
  Cached PNG previews retain the configured DPI until either axis would exceed
  2000 pixels, without changing the spec or final exports.
- htmx and its 0BSD license are reused from `dashboard/static/` rather than
  vendored a second time. Request bodies are bounded at 16 MiB, and Python
  bridge subprocesses time out after 120 seconds. On timeout/wait failure, Windows
  uses its System32 taskkill on the held child tree; Unix creates a fresh child
  process group and signals only that group via /bin/kill. The cleanup command has
  a separate two-second budget, then direct-child kill/reap is attempted. Cleanup
  failure stays in the returned error. This covers foreground owned trees/groups,
  not detached/reparented workers, hard CPU/disk limits or instantaneous OS waits.
  Exactea1 Linux/Windows controlled descendant and MSRV steps passed, including
  Windows missing-tool failure/recovery; later changes still need fresh evidence.
  A declared Content-Length over
  16 MiB is rejected before waiting for body frames. The existing limited Bytes
  extractor caps decoded bodies before every handler, including undo/reset,
  rather than relying only on routes that happen to read the body. Bounded
  chunked requests are supported. Local N-1/N/N+1 probes record server-PID
  lifetime peak RSS, not renderer-child/whole-app memory, CPU or concurrent-load
  guarantees; see the review ledger for observed scope.

Routes: `GET /`, `/fig.{png,pdf,svg}`, `/spec.json`,
`/static/htmx.min.js`; `POST /action` accepts an action JSON object. Visual
controls use `/control/*` and `/layers`; `/open`, `/action/raw`, `/undo`,
`/redo`, and `/reset` return the `#app` htmx fragment.

The JSON `/action` route returns a FigureSpec on200 or an `{error:string}`
object on400(action failure),415(media type) or422(JSON/UTF-8/duplicate keys).
Field decoder diagnostics include public `Class.field` context while preserving
Python's error kinds and validation rules. `apply` writes its result JSON file
with empty stdout; progress/errors use stderr, while capabilities use JSON stdout.
Exports are PNG/PDF/SVG media on success; a bridge vector-export failure is
500text/plain. Check status and Content-Type before decoding—not every route or
failure is JSON, and the UI form endpoints intentionally return HTML/redirects.

Still deliberately out of scope: multi-user sessions/authentication, every
specialized axis/drag control from the mature Python editor, and a native Rust
renderer. Add them only when local usage warrants the extra state and code.
