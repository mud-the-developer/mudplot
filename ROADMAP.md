# Roadmap

*[한국어 문서 / Korean docs: ROADMAP.ko.md](ROADMAP.ko.md)*

This is a working list of concrete next steps, roughly in priority order
within each section. For what's already shipped, see
[`CHANGELOG.md`](CHANGELOG.md); for architecture and historical milestones
(M0–M12), see [`DESIGN.md`](DESIGN.md).

## Active target: v1.1

Follow the [v1.1 development tracker](docs/V1_1_PLAN.md) for ordered batches,
verified checkpoints and release gates. Work remains Unreleased; do not mark
full feature parity or bump/publish a release before the recorded checks pass.

## 0. Version 1 scope

Matplotlib remains mudplot's canonical renderer through 1.x. Keep the current
`FigureSpec → Matplotlib` boundary, but do not add a backend abstraction until
a real second renderer exists. Plotly or Cairo can be optional post-1.0
adapters without changing the reducer or JSON contract.

- **(done)** Executable bilingual documentation for all 28 registered layers,
  guarded against registry drift in CI.
- **(done)** Audited the public Python/CLI/schema surface and documented the
  [1.x compatibility and deprecation policy](docs/COMPATIBILITY.md).
- **Release gate:** locked Python/Rust/browser/full-TeX, clean-wheel, packaging,
  and reproducibility checks must pass before publishing.
- **Release metadata:** Python/editor `1.0.0`, serialized spec `0.1`, signed
  annotated tags, verified artifacts and provenance. PyPI remains a separate
  decision requiring trusted-publisher configuration.

## 1. Matplotlib / Seaborn feature parity

The current checkout has 37 layer types, including Unreleased raw-data
statistics, swarm, letter values and ECDF: `line`, `lineplot`, `regplot`, `scatter`, `stripplot`,
`swarmplot`, `bar`, `barplot`, `pointplot`, `countplot`, `errorbar`, `band`,
`stackplot`, `hist`, `hist2d`, `hexbin`, `quiver`, `box`, `boxenplot`, `violin`,
`kde`, `kde2d`, `ecdf`, `rug`, `heatmap`, `contour`, `contourf`, `pie`, `hline`, `vline`, `text`,
`annotate`, `scatter3d`, `line3d`, `surface`, `wireframe`.
Layer count is not a claim of feature parity.

The goal is functional coverage of Matplotlib/Seaborn plotting workflows,
not just more names in the registry. The
[feature/option/statistics coverage audit](docs/FEATURE_COVERAGE.md) records
partial and missing support, official reference interfaces, native Python
escape-hatch limitations, and the definition of supported. Native edits are
not counted as declarative JSON/editor coverage.

v1.1 batches, preserving `.bar()` as a precomputed-value primitive:

- [x] Shared named estimation for raw `barplot`/`pointplot`/`countplot`:
      mean/median/sum/min/max/count, SD/mean SEM/PI/seeded bootstrap CI,
      paired weighted mean/CI, two-stage unit bootstrap and count proportions.
      Only the documented named operations/assumptions are implemented.
- [x] First categorical subset for those statistical layers: horizontal
      orientation, order/hue order, dodge/gaps, stacked counts and value labels.
- [x] First box/violin subset: category/hue nesting, ordering/orientation,
      width/gap/numeric dodge, native box summaries and violin bandwidth/marks.
- [x] First swarm subset: circular display-space packing on each draw, actual
      layout/DPI and positive log-value transforms, explicit retained overcrowding.
- [x] First letter-value subset: per-cell quantiles, named/explicit depths,
      exponential/linear/area widths, median/observed tails and category/hue geometry.
- [x] Distribution native/log subset: numeric category coordinates and spacing,
      positive log values, explicit data/axis summary/KDE coordinates and strict
      shared-axis validation. Legacy defaults retained; 60 new regression tests.
- [x] Violin semantics subset: four named inner modes/None, two-hue split,
      width/area/count and normalization scope, bandwidth adjustment/cut/clip.
      Existing defaults retained; 138 new numerical/artist/editor/export tests.
- [x] Independent component subset: named typed box body/whisker/cap/median/
      mean/flier and boxen body/median/flier properties. Defaults and native/log
      geometry retained; strict settings and 48 new artist/editor/export tests.
- [x] Statistical native/log subset: bar/point/count numeric spacing/log axes,
      explicit raw/log-fit inference and positive log bar baseline; preserved count/
      default semantics and strict unsupported guards, 73 new tests.
- [x] Weighted violin subset: relative covariance/effective n, inverse weighted
      ECDF marks, count-mass widths, paired rows/native log geometry; 78 tests.
- [ ] Categorical remainder: broader components and size/style/date mappings.
- [x] ECDF subset: weighted/tied empirical steps, strict complement, per-curve
      proportion/percent/count, hue order/dashes, v/h/log observations and typed
      pure/JSON/editor/export contracts; 103 new tests, no inferred intervals.
- [x] Histogram statistics subset: opt-in shared bins/weights, count/frequency/
      proportion/percent/density, pooled/per-curve in-range normalization,
      cumulative mass/v-h/raw logs, legacy behavior preserved; 95 new tests.
- [x] Configurable weighted univariate KDE: typed relative covariance/effective
      n, bandwidth/cut/clip/grid, shared mass/grid, analytic CDF/fill/v-h/raw
      observation logs, singular skip and legacy preservation; 125 new tests.
- [x] Weighted bivariate KDE first subset: full covariance, raw grid/log display,
      conditional-grid HDR/native contours/fills, no regularization; 129 new tests.
- [x] Numeric-x line estimate subset: named pointwise bands/bars, weighted/per-x
      unit CI, sorting and raw/log fit; raw line unchanged,66new tests.
- [x] Independent scatter semantic subset: typed hue/size/style, explicit kinds/
      orders/global linear bounds, diameter-to-area mapping/non-data guides;85tests.
- [x] Named shared scatter scales: pooled figure domains/colour blocks, unique
      rows and same-setting checks, one pooled guide block per panel;36tests.
- [x] Independent lineplot semantic subset: raw tuple curves/shared scopes/
      stroke-point widths/marker-dashes/pointwise inference,48tests;
      approved foreground rechecks full2159/minimum1703, Rust1.99/browser/TeX pass.
- [x] Histogram grouped geometry subset: opt-in layer/stack/dodge, unchanged
      weighted heights/normalization, raw-width reserved hue slots and strict
      derived geometry guards; 48 added tests, Python/Rust editor smoke covered.
- [x] Histogram step subset: unfilled native stairs for layer/stack, preserved
      weighted heights/edges, hue dash slots and v/h/raw-log geometry; 43 added
      tests, pure/JSON/contracts and Python/Rust editor smoke covered.
- [x] Automatic facet first subset: terminal row/col grids, wrap/reserved cells,
      exact panel filters, shared axes/semantic domains and cell-local statistics;
      Python/actions/JSON/editor paths and executable example. See [scope](docs/FACETS.md).
- [x] Raw grouped facet support: line/scatter/bar/errorbar/band/stripplot/regplot/rug,
      reserved hue/style/dodge slots, original raw paths/values/errors and empty cells.
- [ ] Relational/distribution completeness: wider facet combinations,
      wider line inference, broader histogram/KDE variants and semantic controls.
- [x] Joint histogram subset: raw scatter/regplot + paired x/y histograms,
      complete-case row selectors and correct independent density/value axes.
      [Scope and example](docs/JOINT_GRID.md).
- [x] Numeric pair matrix subset: pairwise scatter, histogram diagonals, raw groups
      and named value-axis sharing without diagonal density/unit conflicts.
      [Scope and example](docs/PAIR_GRID.md).
- [x] Configured KDE grids: joint marginals and pair diagonals reuse KDESpec
      bandwidth/grid/support/normalization/fill; histogram defaults unchanged.
      Density only, singular curves warn/skip; weighted/CDF grids remain open.
- [ ] Composition remainder: live facet mapping/consolidated legends, wider pair
      and joint kinds.
- [x] Typed heatmap first subset: masks, raw-value annotations/labels, linear/log/
      centered/robust colour ranges, square cells and borders. [Scope](docs/HEATMAP.md).
- [x] Configured regression subset: residual/log-x/Huber/binomial-logit/LOWESS,
      selected raw groups and optional statsmodels effect extra. [Scope](docs/REGRESSION.md).
- [x] Hierarchical clustermap: row/column trees, supplied linkage/optimal leaves,
      metadata/colour strips and z-score/min-max. [Scope](docs/CLUSTERMAP.md).
- [ ] Further heatmap/clustering controls, weighted/bootstrap/advanced-regression inference
      and residual diagnostics/controls.
- [ ] Remaining native Matplotlib families and axes/layout/color/annotation
      controls. Small primitives can land earlier when they unblock a batch.

Checked items describe implemented Unreleased subsets; unchecked items are
plans, not implemented builders or delivery dates. Track details and pending
release gates in [V1_1_PLAN.md](docs/V1_1_PLAN.md). Every feature
needs truthful capabilities, JSON/action round-trip, renderer/editor access,
statistical/artist tests and reviewed examples. Keep the zero-dependency core
and version minimums; any advanced-statistics dependency belongs in an
explicit optional effect layer, not a new mandatory core dependency.

Foundational work below is shipped for its documented subset, **not** a claim
of complete upstream option/statistical parity:

- **(done) `regplot`**: scatter + a numerically scaled linear/polynomial
  `numpy.polyfit`, with an explicit opt-in normal-approximation confidence
  band for the mean fit. Degree/data/CI constraints fail validation before
  linear algebra runs; no SciPy dependency.
- **(done) `stripplot`**: categorical/raw-data scatter with bounded,
  deterministic horizontal jitter, grouping, and redundant markers. Fixed
  seeding makes every export reproducible.
- **(done, first subset) `swarmplot`**: draw-time circular display-space packing,
  order/hue nesting/orientation and positive log-value axes. Repack after DPI,
  layout/limits/size changes; overcrowding retains rows and warns. Greedy packing
  is not optimal; numeric native/log categories are supported, while broader
  semantic mappings stay deferred.
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
- **(done) polar panels**: `projection="polar"` / `.projection_polar()`
  reuses native `line`/`scatter`/`bar`; other layer types and y2 fail clearly.
  Polar panels coexist with Cartesian/3-D grids but are excluded from
  Cartesian shared-axis links.
- **(done) `step`**: implemented as `drawstyle` on the existing `line` layer
  (`"default"`/`"steps"`/`"steps-pre"`/`"steps-mid"`/`"steps-post"`), using
  native Matplotlib rather than adding a duplicate layer type.
- **(done) `rug`**: small native Matplotlib tick marks along the x-axis show
  individual observations as a cheap companion to `kde`/`hist`; grouped
  rugs also use redundant line styles.

Each addition should follow the same checklist the last two batches did:

1. `LayerSpec` fields (reuse existing ones where the semantics line up).
2. `capabilities.LAYER_TYPES` entry (required/optional fields).
3. `_render.py` drawing function + type-dispatch set membership.
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

The Python editor (`python -m dashboard serve`) now covers the 28-layer
engine, multi-panel controls, direct manipulation, and shared reference docs.
Completed work:

- **(done)** Added one executable, bilingual gallery entry for every registered
  layer, with real PNG output, copyable source, editable JSON, and a CI guard
  requiring exact coverage of `capabilities.LAYER_TYPES`.
- **(done)** Exposed every registered layer type through a generic advanced
  form driven directly by `capabilities.LAYER_TYPES`. It accepts checked
  `LayerSpec` JSON fields, shows required/optional fields for all 28 types,
  rejects typos/missing required fields, and automatically picks up future
  registry entries without another hand-maintained dropdown.
- **(done)** Multi-panel layout controls: grid size, active-panel selection
  for add/remove/edit operations, per-panel Cartesian/polar/3-D projection, and draggable
  title/legend/annotation handles scoped to the selected panel.
- **(done)** Open a saved `.mplot.json`; malformed/invalid specs leave the
  current figure untouched and report an editor error.
- **(done)** Panel-level controls: title/reference, x/y labels, scales,
  fixed/automatic limits, secondary-y-axis enable/configure/remove, 3-D z-axis
  setup, projection, and draggable positions. Prospective state is validated
  and rendered before it can enter editor history.
- **(done)** Replaced the full-page-reload-per-action UX with htmx partial
  swaps (`dashboard/static/htmx.min.js`, vendored, 0BSD, no Python
  dependency) — good practice run before the real Rust+htmx editor.
- **(done)** Drag-to-position for the legend, panel title, and any
  `text`/`annotate` layer directly on the preview (mouse or arrow keys).
- **(done)** Editor/Docs tabs within the one running server (`/docs`),
  reusing the same engine-reference renderer as the static site.

## 3. Rust interactive editor (M13)

**Version 1 local-editor essentials landed in-repo** as the co-versioned
`mudplot-editor/` crate:

- serde preserves the versioned `FigureSpec` and action envelopes while the
  generated schema/reference remain the contract.
- axum + Askama exposes PNG/PDF/SVG/JSON output and the shared vendored htmx
  asset; JSON `/action`, visual controls, all-layer capability metadata,
  spec open, undo/redo, and reset mutate one local session atomically.
- New dependency-free-core `mudplot apply` and existing `mudplot render` subprocesses
  keep reduction, validation, and rendering semantics in Python instead of
  duplicating 28-layer behavior in Rust.
- The crate is intentionally local/single-user and rejects non-loopback binds/
  HTTP Hosts plus cross-origin browser mutations; it has no authentication.

Next only after local usage justifies it: specialized axis/drag controls from
the mature Python editor, then cookie-keyed sessions/authentication if remote
use is actually wanted. A native Rust renderer remains optional; strongly
typing all schema fields only pays off if Rust takes over reduction or
rendering.

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
- **(done)** Capability-driven column contracts: validation rejects malformed
  or unsupported column fields before rendering, and consistency tests pin
  the exact groupable/routable layer sets.
- **Deep-copy performance boundary**: documented and measured. Internal
  fluent/batch dispatch no longer creates unused return snapshots, but each
  reducer action still copies the full mutable spec and undo/redo replays
  history. Add structural sharing or replay checkpoints only when profiling a
  real large-inline-data workflow justifies the added aliasing complexity.
- **(deferred)** Splitting `DESIGN.md`: its table of contents is sufficient;
  move audit history to `CHANGELOG.md` only when navigation or review becomes
  measurably painful. A file split alone adds churn, not user value.

## 5. Packaging / release

- **GitHub releases**: done — `.github/workflows/release.yml` checks tag/
  Python/pyproject/Rust manifest+lock/changelog/README version agreement,
  reruns Python + Rust + full TeX-engine preflight with locked dependencies,
  and attaches the sdist/wheel, SHA-256 checksums, and OIDC build-provenance attestations to
  every `v*` release.
- **Actual PyPI publish**: deliberately deferred. Register this repo as a
  trusted publisher on the PyPI project (project name `mudplot`, workflow
  `release.yml`, environment `pypi`; see
  <https://docs.pypi.org/trusted-publishers/>), create a matching `pypi`
  GitHub environment, then re-add a `publish` job to `release.yml` using
  `pypa/gh-action-pypi-publish` (trusted publishing, no stored token
  needed) -- attempted once already and failed with `invalid-publisher`
  since no publisher was registered yet.
- **Versioning**: package/editor `1.0.0`; spec `0.1` remains independent.
  Additive features can land in minor releases; incompatible public Python/CLI/
  JSON changes need advance deprecation and a major release. See the
  [compatibility policy](docs/COMPATIBILITY.md).
- `pyproject.toml`'s `[project.urls]` now point at the real repository
  (`https://github.com/mud-the-developer/mudplot`); keep the `Changelog`/
  `Roadmap` links in sync if these files ever move.
