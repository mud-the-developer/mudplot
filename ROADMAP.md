# Roadmap

*[한국어 문서 / Korean docs: ROADMAP.ko.md](ROADMAP.ko.md)*

This is a working list of concrete next steps, roughly in priority order
within each section. For what's already shipped, see
[`CHANGELOG.md`](CHANGELOG.md); for architecture and historical milestones
(M0–M12), see [`DESIGN.md`](DESIGN.md).

## 1. More plot types (matplotlib/seaborn parity, continued)

Currently supported (21 layer types): `line`, `scatter`, `bar`, `errorbar`,
`band`, `hist`, `box`, `violin`, `kde`, `heatmap`, `contour`, `contourf`,
`pie`, `hline`, `vline`, `text`, `annotate`, `scatter3d`, `line3d`,
`surface`, `wireframe`.

Candidates for the next batch, roughly by expected value for scientific
papers:

- **`regplot`**: scatter + a fitted line (linear, or polynomial via
  `numpy.polyfit`) + an optional confidence band — no scipy needed, a
  simple least-squares fit is enough for the common case. Very common in
  papers showing a trend with uncertainty.
- **`stripplot`/`swarmplot`**: categorical scatter (points jittered or
  packed to avoid overlap) — seaborn staples for showing raw data points
  alongside/instead of box or violin plots.
- **`stackplot`**: stacked area chart. Semantically different from every
  other layer (`ax.stackplot()` wants *all* series at once, not drawn
  incrementally per group like our other layers), so it needs a bit of
  special-casing in `_draw_series_layer`/`_draw_dist_layer` rather than
  reusing the existing per-mask loop directly.
- **`hist2d`/`hexbin`**: 2-D density/count plots for two continuous
  variables — pairs naturally with the existing `heatmap`/`contour`
  colour-mapping infrastructure.
- **`quiver`**: vector field arrows — common in physics/engineering
  papers. Needs `u`/`v` (or `u`/`v`/`w` for a 3-D variant) component
  columns in addition to `x`/`y`.
- **polar plots**: a `projection="polar"` panel option (parallel to the
  existing `"3d"` one), plus whichever of the existing 2-D layer types
  make sense on it (`line`/`scatter`/`bar` mostly do, unchanged).
- **`step`**: a `drawstyle` option on the existing `line` layer
  (`"default"`/`"steps"`/`"steps-pre"`/`"steps-mid"`/`"steps-post"`)
  rather than a whole new layer type.
- **rug plot**: small tick marks along an axis showing individual
  observations — a cheap, useful companion to `kde`/`hist`.

Each addition should follow the same checklist the last two batches did:
1. `LayerSpec` fields (reuse existing ones where the semantics line up).
2. `capabilities.LAYER_TYPES` entry (required/optional fields).
3. `render.py` drawing function + type-dispatch set membership.
4. `validate.py` checks (required fields, column existence, any
   type-specific constraints).
5. `api.py` builder method.
6. Tests, including at least one `validate()` clean-spec check and one
   deliberately-broken-spec check.
7. Regenerate `schemas/*.json` + `docs/REFERENCE.md`
   (`python scripts/check_schema_sync.py` catches drift).
8. Run `tests/test_capabilities_consistency.py` — it's specifically there
   to catch the "advertised but not implemented" / "implemented but not
   advertised" class of bug found twice already.

## 2. Dashboard / editor completeness

The editor prototype (`python -m dashboard serve`) currently exposes
`line`/`scatter`/`bar` plus `text`/`annotate` in its "Add layer" forms,
while the engine supports 21 types. Concrete gaps:

- **Expose the remaining layer types** in the editor UI (at minimum a
  generic "advanced" form that lets you pick any registered layer type and
  fill in its fields, driven by `mp.capabilities()` rather than a
  hand-maintained dropdown — this would also make the editor automatically
  pick up any *future* layer type with zero UI changes).
- **Multi-panel layout controls**: `.layout(rows, cols)`, panel selection
  for "add layer"/"remove layer", and a `.projection3d()` toggle per panel.
  The new draggable title/legend/annotation handles are also currently
  panel-0-only; extending them to whichever panel is selected is a natural
  follow-on once multi-panel controls exist.
- **Load a spec from a file** (currently only export/download links exist;
  there's no upload/"open" counterpart).
- **Panel-level controls**: axis labels/scales/limits, secondary y-axis
  setup — currently only figure-level (theme/journal/palette/suptitle/
  size), legend/title position, and a flat "add layer" exist.
- **(done)** Replaced the full-page-reload-per-action UX with htmx partial
  swaps (`dashboard/static/htmx.min.js`, vendored, 0BSD, no Python
  dependency) — good practice run before the real Rust+htmx editor.
- **(done)** Drag-to-position for the legend, panel title, and any
  `text`/`annotate` layer directly on the preview (mouse or arrow keys).
- **(done)** Editor/Docs tabs within the one running server (`/docs`),
  reusing the same engine-reference renderer as the static site.

## 3. Rust interactive editor (M13)

Deferred by design until the Python prototype had exercised the action/
JSON contract enough to trust it (see `DESIGN.md` §7 for the original
plan). Now that the prototype has ~25 action types and 21 layer types
exercised through it, a reasonable first slice:

1. New crate (e.g. `mudplot-editor/`, separate from this Python repo, or a
   sibling directory here — decide based on whether Rust and Python stay
   co-versioned).
2. `serde` structs mirroring `schemas/figure_spec.schema.json` and the
   action shapes documented in `docs/REFERENCE.md`'s "Actions" section —
   these two files are the contract; regenerate/diff them
   (`scripts/check_schema_sync.py`) whenever the Python side changes.
3. `axum` (or similar) + `askama` templates mirroring the routes already
   proven out in `dashboard/editor_server.py`/`editor_view.py`
   (`GET /`, `GET /fig.png`, `POST /action`, `POST /action/raw`,
   `POST /undo`/`/redo`/`/reset`, `GET /spec.json`).
4. Rendering: phase 1 shells out to the Python `render()` (subprocess or a
   small local HTTP call to a `python -m mudplot render` invocation) so
   Rust doesn't need its own renderer yet. Phase 2 (optional, later): a
   native Rust renderer (e.g. `plotters`) behind the same
   `FigureSpec -> PNG` interface, swappable because the schema is fixed.
5. htmx for partial-page updates instead of the Python prototype's
   full-page-reload-per-action approach.

## 4. Quality / tooling

- **Static type checking**: run `mypy` or `pyright` over `mudplot/` and
  fix what it finds. Not done yet; `py.typed` is shipped (so *consumers*
  can type-check against mudplot) but the library's own type-correctness
  hasn't been externally verified with a type checker, only informally
  via consistent type hints.
- **Property-based testing** (e.g. `hypothesis`) for the colour engine
  (`convert.py` round-trips, `distance.py` metric properties) and for
  `validate()`/`reduce()` (e.g. "any sequence of valid actions produces a
  spec that passes `validate()`" as a property, if that invariant is
  meant to hold).
- **`CONTRIBUTING.md`**: contribution guidelines, dev setup
  (`uv sync --extra dev`), the "regenerate schemas" step, and the testing
  philosophy (one regression test per bug, cross-module consistency tests
  for anything with more than one source of truth).
- Consider whether `DESIGN.md` (now fairly long, spanning original
  architecture + two rounds of bug-audit narrative) should be split: a
  leaner `ARCHITECTURE.md` for the design itself, with the bug-audit
  history moved into (or cross-linked from) `CHANGELOG.md` where it
  arguably belongs longer-term.

## 5. Packaging / release

- **GitHub releases**: done — `.github/workflows/release.yml` builds the
  sdist/wheel and attaches them to a GitHub release on every `v*` tag.
- **Actual PyPI publish**: deliberately deferred. Register this repo as a
  trusted publisher on the PyPI project (project name `mudplot`, workflow
  `release.yml`, environment `pypi`; see
  https://docs.pypi.org/trusted-publishers/), create a matching `pypi`
  GitHub environment, then re-add a `publish` job to `release.yml` using
  `pypa/gh-action-pypi-publish` (trusted publishing, no stored token
  needed) -- attempted once already and failed with `invalid-publisher`
  since no publisher was registered yet.
- **Versioning**: `0.2.0` as of this release; semver policy: this is a
  young, fast-moving pre-1.0 project — breaking changes to `FigureSpec`
  bump the minor version even pre-1.0, since Rust/agent consumers depend on
  schema stability.
- `pyproject.toml`'s `[project.urls]` now point at the real repository
  (`https://github.com/mud-the-developer/mudplot`); keep the `Changelog`/
  `Roadmap` links in sync if these files ever move.
