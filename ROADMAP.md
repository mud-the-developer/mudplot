# Roadmap

*[한국어 문서 / Korean docs: ROADMAP.ko.md](ROADMAP.ko.md)*

This is a working list of concrete next steps, roughly in priority order
within each section. For what's already shipped, see
[`CHANGELOG.md`](CHANGELOG.md); for architecture and historical milestones
(M0–M12), see [`DESIGN.md`](DESIGN.md).

## 1. More plot types (matplotlib/seaborn parity, continued)

Currently supported (28 layer types): `line`, `regplot`, `scatter`,
`stripplot`, `bar`, `errorbar`, `band`, `stackplot`, `hist`, `hist2d`,
`hexbin`, `quiver`, `box`, `violin`, `kde`, `rug`, `heatmap`, `contour`,
`contourf`, `pie`, `hline`, `vline`, `text`, `annotate`, `scatter3d`, `line3d`,
`surface`, `wireframe`.

Candidates for the next batch, roughly by expected value for scientific
papers:

- **(done) `regplot`**: scatter + a numerically scaled linear/polynomial
  `numpy.polyfit`, with an explicit opt-in normal-approximation confidence
  band for the mean fit. Degree/data/CI constraints fail validation before
  linear algebra runs; no SciPy dependency.
- **(done) `stripplot`**: categorical/raw-data scatter with bounded,
  deterministic horizontal jitter, grouping, and redundant markers. Fixed
  seeding makes every export reproducible.
- **`swarmplot`**: pack points to avoid overlap. Defer the substantially more
  complex collision algorithm until stripplot overlap is a demonstrated
  problem rather than shipping a fragile approximation.
- **(done) `stackplot`**: native stacked areas from the existing long-form
  `x`/`y`/`group` contract. Validation requires every group to share the same
  ordered x sequence and finite values; hatch cycling keeps stacks distinct
  in grayscale.
- **(done) `hist2d`/`hexbin`**: native rectangular and hexagonal count maps
  for finite numeric x/y data, sharing the existing LCH colormap, colorbar,
  y2, and exact-layout paths. Bin/grid/count constraints fail validation.
- **(done) 2-D `quiver`**: numeric x/y positions plus u/v components, native
  data-coordinate arrow angles, optional magnitude colouring/colorbar, y2,
  and explicit scale/width calibration controls. Invalid vectors fail before
  Matplotlib. A 3-D u/v/w variant remains deferred.
- **polar plots**: a `projection="polar"` panel option (parallel to the
  existing `"3d"` one), plus whichever of the existing 2-D layer types
  make sense on it (`line`/`scatter`/`bar` mostly do, unchanged).
- **(done) `step`**: implemented as `drawstyle` on the existing `line` layer
  (`"default"`/`"steps"`/`"steps-pre"`/`"steps-mid"`/`"steps-post"`), using
  native Matplotlib rather than adding a duplicate layer type.
- **(done) `rug`**: small native Matplotlib tick marks along the x-axis show
  individual observations as a cheap companion to `kde`/`hist`; grouped
  rugs also use redundant line styles.

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
while the engine supports 28 types. Concrete gaps:

- **(done)** Exposed every registered layer type through a generic advanced
  form driven directly by `capabilities.LAYER_TYPES`. It accepts checked
  `LayerSpec` JSON fields, shows required/optional fields for all 28 types,
  rejects typos/missing required fields, and automatically picks up future
  registry entries without another hand-maintained dropdown.
- **(done)** Multi-panel layout controls: grid size, active-panel selection
  for add/remove/edit operations, per-panel 2-D/3-D projection, and draggable
  title/legend/annotation handles scoped to the selected panel.
- **(done)** Open a saved `.mplot.json`; malformed/invalid specs leave the
  current figure untouched and report an editor error.
- **(done)** Panel-level controls: title/reference, x/y labels, scales,
  fixed/automatic limits, secondary-y-axis enable/configure/remove, 3-D z-axis
  setup, projection, and draggable positions. Invalid prospective states are
  rejected before they can enter editor history.
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
plan). Now that the prototype has ~25 action types and 28 layer types
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

- **(done)** Static type checking: `pyright` runs over `mudplot/`, the
  dashboard, and maintenance scripts in CI against the Python 3.10 language
  level. `py.typed` remains packaged so consumers can check their own use of
  mudplot too.
- **(done)** Property-based testing (`hypothesis`) for `reduce()`
  (state/action immutability, JSON round-trip of its output), the
  citation/href validator, and the colour engine (`convert.py` round-trips,
  8-bit hex identity, and `distance.py` metric properties), all in
  `tests/test_property_based.py`.
- **(done)** `CONTRIBUTING.md` / `CONTRIBUTING.ko.md`: development setup,
  pre-PR checks, optional browser/TeX setup, schema regeneration, dependency
  boundaries, and the testing/documentation conventions.
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
  <https://docs.pypi.org/trusted-publishers/>), create a matching `pypi`
  GitHub environment, then re-add a `publish` job to `release.yml` using
  `pypa/gh-action-pypi-publish` (trusted publishing, no stored token
  needed) -- attempted once already and failed with `invalid-publisher`
  since no publisher was registered yet.
- **Versioning**: `0.5.0` as of this release; semver policy: this is a
  young, fast-moving pre-1.0 project — breaking changes to `FigureSpec`
  bump the minor version even pre-1.0, since Rust/agent consumers depend on
  schema stability.
- `pyproject.toml`'s `[project.urls]` now point at the real repository
  (`https://github.com/mud-the-developer/mudplot`); keep the `Changelog`/
  `Roadmap` links in sync if these files ever move.
