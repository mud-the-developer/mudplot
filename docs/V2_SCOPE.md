# mudplot v2 scope and acceptance contract

*[한국어 요약](V2_SCOPE.ko.md)*

**Feature scope frozen: 2026-10-30. Implementation is not complete.**
Goal: `mvv0buln-hy7f1o`. This is a finite product-workflow scope, not a claim of
universal Matplotlib/Seaborn keyword equivalence. No row below is complete merely
because a related layer name already exists.

## Baseline and authority

- Preserve the unpublished, uncommitted **1.1.0** candidate and schema **0.1**.
  Its qualified Linux suites passed 4,547 cases each on locked Python 3.11/3.12
  and 3,735 in the pinned minimum environment; skips remain recorded.
- Baseline source, tracked working-tree patch and hashes are preserved locally in
  `artifacts/v2_baseline_20261030/`. Private `.pi` state remains in place and is
  deliberately absent from that archive. No commit or remote action was made.
- Baseline evidence: [numeric/export qualification](review_evidence/v1_1_numeric_export_quality.json).
- Scope sources: [ROADMAP §§1–5](../ROADMAP.md),
  [FEATURE_COVERAGE §1](FEATURE_COVERAGE.md#1-seaborn-function-interface),
  [§2](FEATURE_COVERAGE.md#2-matplotlib-plotting-and-customization),
  [support lanes](FEATURE_COVERAGE.md#3-two-support-lanes-not-a-misleading-universal-wrapper)
  and [supported definition](FEATURE_COVERAGE.md#5-definition-of-supported).
- Comparison references remain **Seaborn 0.13.2 / Matplotlib 3.11.2** as specified
  by the coverage audit. They do not upgrade runtime dependencies. Existing
  Python >=3.11, render NumPy >=1.23.5 / Matplotlib >=3.8 / Pillow >=13.0.0 floors
  remain unless the owner separately approves a change.
- The live registry has **41** layers. Older 1.0.0/Unreleased headings and the
  shorter prose list in ROADMAP are historical, not evidence of a missing layer.
  Existing stem/stairs/event/interval and clustermap subsets remain supported.

## Decisions and change control

The owner selected (1) all explicitly unfinished documented product features,
not unrestricted upstream equivalence; (2) **Linux required**, Windows/macOS
explicitly deferred; and (3) usage/profile-triggered conditional work stays
conditional. Required rows cannot be dropped or relabelled post-v2 without asking.
New ambiguity or a breaking API/schema/security change stops the affected work
for an owner decision, rather than weakening an acceptance test.

The catalogue freezes feature units and observable outcomes. A feature's typed
options, numerical assumptions and tolerances must be specified before its
implementation/reference tests; this is not permission to reduce its named scope.

## Common completion gates

Every required row needs all applicable gates, not only its short scenario:

1. Typed data/options and truthful capability/schema metadata, with explicit
   dependency/version boundaries and clear invalid-combination rejection.
2. Python builder, actions/reducer, JSON round-trip, CLI and usable Rust editor
   access. Native-only Figure edits or manual preprocessing do not count.
3. Legacy defaults and old 0.1 documents retained; observations, row identity,
   order and declared units unchanged unless a requested operation explicitly
   derives a result. Keep `.bar()` a precomputed-value primitive.
4. Independent numerical/statistical references where applicable, artist tests,
   empty/missing/group/multi-panel cases, deterministic local RNG, and actual
   create → save → reopen → edit → undo/redo → export scenarios.
5. Executable examples, reviewed raster/vector output and accurate documentation.
   Unsupported input must not become a silently misleading figure.
6. Relevant targeted checks per batch; supported minimum and locked Linux checks,
   real browser/Rust/bridge/TeX paths and installed artifacts at frozen milestones.

Status vocabulary: **pending**, **in progress**, **verified** (with evidence).
A baseline subset is not completion of a remaining row. All required rows below
start **pending**. Row IDs are stable; evidence is appended, not substituted for
unfinished work.

## Required catalogue

### Shared semantics, categorical and distribution workflows

These rows close ROADMAP's categorical and relational/distribution remainders
and FEATURE_COVERAGE §1, including the detailed subset limits.

| ID | Finite feature scope | Minimum acceptance scenario / reference |
| --- | --- | --- |
| F01 | Shared hue/size/style semantics across the documented applicable 2-D mark families; continuous hue colourbars, outlines, shared normalization and guides | One selected dataset drives line/scatter/categorical/distribution panels with consistent declared domains and correct mark-specific size units; JSON/editor edits preserve the mapping. Date coordinates are supplied by F02. |
| F02 | Explicit real temporal axes and date-valued predictors/categories, including timezone/unit/origin contracts and applicable y2/facet/distribution paths | Irregular ISO observations use elapsed-time spacing rather than categorical spacing after an explicit date request; old string defaults remain unchanged, exact source timestamps are retained and unsupported precision fails clearly. |
| C01 | Strip nesting/hue dodge, order, native scale, orientation and named jitter controls | Nested horizontal/vertical groups retain all observations and reserved hue slots; seeded jitter reproduces with native numeric/date category coordinates. |
| C02 | Swarm style/date/shared-family semantics, serializable marker choices, scoped cross-layer collision packing and live-grid behavior | Two declared packing members repack on redraw/DPI/layout changes without moving raw measurements or deleting crowded points; marker extents, grouping and guides are checked. Existing limits remain until CND02 justifies changes. |
| C03 | Precomputed `bxp` input, bootstrap median CI, box cap geometry and typed per-hue component overrides | Raw and equivalent supplied summaries have matching box/whisker/cap artists; seeded median bounds and component edits survive JSON and editor replay. |
| C04 | Violin multi-hue split policy, named inner/component controls, KDE configuration and wider size/style mappings | A declared multi-hue split/inner policy retains weighted observations and normalization; two-hue legacy output is unchanged. Named/registered configuration is used, not serialized callables. |
| C05 | Weighted letter values, per-band/per-hue component overrides and wider mappings | Weighted quantiles/depth/width/mass match a declared reference policy; each band's visual override is editable and tails remain observed values. No silent raise of the existing depth limit. |
| C06 | Weighted counts, named normalization scopes, scientifically defined log-value stacking/stat-scale combinations | Absolute weighted mass and normalized counts agree with hand/reference calculations; stacks have explicit baselines and coherent units, and invalid log/stat combinations reject rather than invent meaning. |
| C07 | Bar/point named estimator/inference extensions, semantic/date/native/log/y2 combinations | Shared estimation and requested intervals agree across bar/point/line views; sum/count log behavior is explicitly defined or rejected as statistically undefined, not silently exponentiated into a different quantity. |
| D01 | Whole-curve/simultaneous line inference plus temporal/category/y2 predictors, raw-line mappings and automatic facets | Resampling preserves complete declared units/curves, pointwise and simultaneous bands are distinguished, and date/category spacing and grouped gaps remain correct. |
| D02 | Univariate histogram step+dodge, filled step, fill/poly, discrete and named automatic-bin rules; explicit width-coordinate semantics | Weighted heights, edges and cumulative mass remain identical across geometry choices; automatic-bin/weight rules and log/date/y2 contracts are declared and checked. |
| D03 | Bivariate histogram weighted statistics, KDE integration and temporal/y2 controls | Paired missing rows and selected weights feed one documented 2-D statistic; normalization, bins/colourbar and optional KDE use consistent input rows and units. |
| D04 | KDE 2-D cumulative fields, colourbars/absolute levels, multiple modes, named kernel/bandwidth choices, date/y2 and explicit log-fit semantics | Density/CDF and level mass agree with numerical/analytic references on declared supports; domain checks, singular behavior and weighted normalization are explicit. |
| D05 | Full-support HDR contract beyond finite-grid conditional HDR | Distinguish finite-grid conditional mass from full-support claims; bound/measure omitted and numerical mass under a stated tolerance before claiming a full-support HDR. No exact infinite-support guarantee is fabricated. |
| D06 | ECDF continuous semantics/size/style/date/y2 and an explicit bivariate cumulative workflow | Ties, weights, complement, bounds and orientation match empirical definitions; a known paired sample gives the expected joint CDF and does not turn into KDE or a survival estimator. |
| D07 | Rug y-axis marks, height/orientation and semantic controls | x/y rugs use the intended coordinate transform, retain observations and do not contaminate density/value limits or guides. |
| O01 | Composable named statistical transform/move/scale pipeline | Compose existing named estimation/histogram/KDE/ECDF operations, explicit data/log/standardization transforms, jitter/dodge/stack moves and declared scales without changing source data; replay the chain through JSON/editor. This is not a drop-in `seaborn.objects` API. |

### Regression, matrices and composition

These rows close ROADMAP's advanced/statistical/composition remainders and the
corresponding FEATURE_COVERAGE §1 rows and linked scope documents.

| ID | Finite feature scope | Minimum acceptance scenario / reference |
| --- | --- | --- |
| R01 | Weighted CI/bootstrap and advanced poly/log-x/Huber/binomial-logit/LOWESS inference, partial residualization and typed fit/scatter controls | Model-specific assumptions and supported interval algorithms are stated; weighted fits/inference and nuisance-variable removal match appropriate references, use local seeded RNG and reject unsupported assumptions. |
| R02 | Independent residual trends, out-of-sample/deviance diagnostics and requested inference | Raw versus deviance residuals are distinguished for the applicable model; predictions are aligned to original row identities and no diagnostic silently refits or claims significance. |
| M01 | Custom heatmap annotation matrices, norm families, tick rotations and colourbar/layout controls | Annotation text can differ from the scalar colour values without replacing them; masks, robust/centered/log norms, labels and colourbar editing remain aligned. |
| M02 | Multiple cluster colour tracks/legends, explicit missingness, metric customization, interactive cuts and layout controls | Leaves, row/column IDs and tracks remain aligned; requested cuts select the correct original rows. Named/registered or declared precomputed metric contracts remain serializable; no implicit imputation or opaque callback is stored. |
| G01 | Complete documented rel/dis/cat/lm facet builder families, live templates, consolidated legends, legacy `c`/colourbar and inference combinations | A post-facet template edit updates all intended cells without duplicating rows; reserved empty cells, shared scales, per-cell stats and one correct figure guide are preserved. |
| G02 | Pair corner/semantic/weighted/complementary-CDF and nested-grid workflows | Asymmetric missingness uses correct pairwise rows and shared domains; diagonal density/CDF axes do not corrupt value-axis units, and corner/nested edits round-trip. |
| G03 | Joint semantic/`c`/weighted/complementary-CDF/grouped-binned kinds, nesting and richer layout | Joint/marginal panels share declared row selectors and weights; grouped hist2d/hexbin kinds, colourbars and complementary CDFs retain appropriate independent axes. |

### Native Matplotlib geometry and customization

These rows cover every named unfinished family in FEATURE_COVERAGE §2 and the
ROADMAP native remainder. Reuse the existing Matplotlib effects boundary.

| ID | Finite feature scope | Minimum acceptance scenario / reference |
| --- | --- | --- |
| N01 | Named serializable line/marker/collection properties; finite h/v segments; asymmetric x/y errors; horizontal bands; fills/spans and where/step/interpolation controls | Match native artist coordinates/properties, missing-gap behavior and horizontal/vertical roles; safe properties are enumerated in capability metadata, not arbitrary kwargs. |
| N02 | `barh`, bottom/stack/alignment, per-bar styling/labels and pie wedge/text/annotation options | Explicit bottoms and stacks match native endpoints; categorical/horizontal labels and named pie formatting retain original values and ordering. |
| N03 | Horizontal/group/facet/semantic stem workflows | Stems use the correct raw baseline and orientation with duplicated/ordered observations, date/native scales where meaningful and scoped guides. |
| N04 | Stairs rebinning, fill/open/log/group/facet workflows | Supplied or explicitly derived heights/edges retain interval mass and open/filled endpoints, with declared baselines and log validity. |
| N05 | Eventplot groups/facets/log/date and semantic mappings | Each event stays in its declared train/lane; spacing, lengths and offsets remain in named units and no events are connected or pooled implicitly. |
| N06 | Broken-bar date/group/facet/log workflows | Original start/duration intervals and overlaps are preserved across date conversion, lanes and log constraints. |
| N07 | Explicit image/grid coordinates/extents/masks, RGB(A), `pcolor`, `pcolormesh`, `spy` and detailed contours | Grid/cell topology and raw values match native artists; masks and nonuniform coordinates align, RGB(A) stays distinct from scalar normalization, contour levels/labels are editable. |
| N08 | `triplot`, `tripcolor`, `tricontour`/`tricontourf`, triangulated surfaces and explicit triangles/masks | Triangle connectivity, masks, values and surfaces match native rendering and survive JSON/editor reopening. |
| N09 | Streamplot, barbs, wider 2-D quiver controls and 3-D quiver | Vector components and declared coordinate/length units remain aligned; native field/reference checks cover masks, scales, grouping and applicable panels. |
| N10 | Explicit 3-D surface/wireframe coordinates, trisurf, 3-D bars/contours/voxels and camera/aspect controls | Camera/geometry changes round-trip without replacing source coordinates; supplied grids/triangles/voxel occupancy and native projections are checked. Trisurf shares N08 rather than a second implementation. |
| N11 | Spectrogram, PSD/CSD/coherence and magnitude/phase spectra | Explicit sampling frequency, named windows, FFT/overlap/detrend/sides/scaling contracts match reference arrays; preserve raw signals and label derived axes with declared units. |
| N12 | Tick locators/formatters, scale parameters and secondary-x/named secondary-axis transforms | Major/minor ticks, date axes via F02 and named conversions render consistently; no Python formatter function is hidden in JSON. |
| N13 | Inset/nested/mosaic layouts and richer panel placement | Stable panel identities, spans/ratios and shared-axis groups survive create/edit/reopen/undo; nested density/value units and empty panels remain valid. |
| P01 | Named/custom colormaps, palette/context selection, fixed/shared ranges and norm families; colourbar placement/ticks and legend columns/named handlers | Two panels share the requested colour domain and declared guides; under/over/bad values, log/centered/boundary normalization, legend columns and named handler choices match native behavior. |
| N14 | Serializable patches/paths, tables, spans, annotation coordinate transforms and named path effects | Data/axes/figure anchoring, vertices/codes, table cells and stroke/shadow effects round-trip and retain intended physical/data coordinates. |

### Product-wide rows

| ID | Finite feature scope | Minimum acceptance scenario / reference |
| --- | --- | --- |
| E01 | Python/action/JSON/CLI and Rust edit access for every delivered row | Use each feature from an installed package; edit it in Rust, undo/redo and reopen the same JSON without lost settings/data. Generic capability-driven forms are acceptable where usable. No smart toggle is required. |
| Q01 | Numerical/visual QA, readable publication output, failure safety, privacy and existing resource bounds | Contrastive/edge fixtures demonstrate truthful diagnostics and retained data; exact-size PNG/vector/PGF exports, ordinary-failure restoration and private-file exclusions remain tested. Do not hide resource limits by dropping observations. |
| DOC01 | Executable examples, current coverage, key English/Korean docs and upgrade guidance | Every row has an example and actual supported/unsupported/version status; old 0.1 documents reopen and documented migration/error behavior is exercised. |
| REL01 | Local 2.0.0 qualification and reproducible distributables | Freeze source, pass required Linux/Python/minimum/browser/Rust/bridge/TeX/static/security profiles, align version metadata and independently rebuild/install wheel and sdist outside the checkout. No release or git mutation without approval. |

## Conditional evaluations (owner confirmed)

These are **required evaluations**, not automatically required refactors.
A no-trigger outcome is recorded as **condition not triggered**, never as an
implemented feature. If a condition is triggered, its implementation and checks
must finish inside v2 or the owner must explicitly change scope.

| ID | Condition and evidence | Action if triggered |
| --- | --- | --- |
| CND01 | Compare actual Rust editing scenarios with Python's specialized axis/drag controls; record a concrete missing/unusable operation | Add the needed specialized controls and browser/history tests. Smart quality UI remains unnecessary. |
| CND02 | Profile a representative large-inline-data workflow and long undo/redo history; record reproducible workload, latency/allocation baseline and the decision before optimization | Add structural sharing/replay checkpoints or the smallest proven improvement, with aliasing/isolation/reference checks; do not invent an SLA or lift limits without evidence. |
| CND03 | Record whether DESIGN's current TOC actually obstructs navigation/review for this work | Split/reorganize only the affected material and verify links; do not churn historical receipts. |

## Closed interpretation boundaries

- Safe named/registered transforms, kernels, metrics, formatters and artist
  controls must have a finite typed contract. They do not mean pickled functions,
  `eval`/`exec`, arbitrary callbacks, opaque artists or unrestricted kwargs.
  Optional providers stay at the declared effect boundary; unknown/unavailable
  providers must fail clearly. New security/dependency boundaries need approval.
- Invalid scientific combinations are not implemented by silently changing the
  statistic. Named APIs must state assumptions and reject impossible/undefined
  combinations with explicit evidence. Such rejection is not a substitute for
  implementing the valid workflow named in a row.
- Native-only animation/GUI widgets/event callbacks/arbitrary artists remain the
  native lane, not declarative v2 requirements. Deprecated distplot, online example
  downloads, notebook palette widgets/global aliases and drop-in seaborn.objects
  compatibility are not requirements (FEATURE_COVERAGE §§1,3).
- Remote sessions/auth, a native Rust renderer, wholesale strong-typing of Rust
  schema fields and actual PyPI/GitHub publication are not this local goal.
- Preserve Matplotlib/defaults and readable legacy JSON. Any incompatible public
  API/schema change requires a separate owner decision; a v2 version number alone
  is not permission to break compatibility.
- Linux is the required execution platform. Windows/macOS and physical-print or
  unavailable original-dataset review must not be claimed as verified.
- PGF rollback is ordinary-failure protection, not concurrent all-files atomic
  visibility or process-kill durability; preserve recovery notes/backups on failure.

## Task mapping and evidence discipline

- `v2-scope`: this catalogue, baseline preservation and source cross-check.
- `v2-statistical-plots`: F01–F02, C01–C07, D01–D07, O01.
- `v2-advanced-composition`: R01–R02, M01–M02, G01–G03.
- `v2-matplotlib-features`: N01–N14, P01; shared work is counted once.
- `v2-agent-editor`: E01 across all rows and CND01's evaluation.
- `v2-quality-safety`: Q01 and CND02's evaluation.
- `v2-docs-examples`: DOC01 and CND03's evaluation.
- `v2-local-candidate`: REL01, final catalogue/evidence re-read and remaining limits.

Append batch evidence using the row IDs. Do not erase the original scope text,
replace failed receipts with success, or call v2 complete while a required row
lacks implementation and all applicable completion gates. Record any source gap
not mapped above as a scope blocker instead of silently excluding it.

## Implementation batch evidence

- **C06 — implemented; local feature checks passed:** weighted mass, the
  owner-approved panel-local `all/category/group` denominator scopes, and
  raw-cumulative log stacks with explicit positive baselines are implemented.
  Regression coverage includes extreme-range positive mass, empty selected
  facets, preserved legacy JSON, orientations/native axes, actual Chromium/Rust
  editing/history/export, CLI and installed-wheel rendering. See
  [the numerical contract](WEIGHTED_COUNTS.md) and
  [completed feature evidence](review_evidence/v2_count_scopes.json).
  The [earlier partial receipt](review_evidence/v2_weighted_counts.json) remains
  historical evidence, not a claim of completion at that earlier checkpoint.
- This is one required feature unit, not completion of the statistics task,
  G01/E01/Q01/DOC01/REL01 or the v2 candidate. Full supported-Python/Linux/TeX,
  security, installation-matrix and reproducibility gates remain for the frozen
  product milestone. The other required rows and all conditional evaluations
  remain unfinished unless individually evidenced.
- **F02 — in progress, core Cartesian paths verified:** explicit API/action/
  schema/JSON, raw/statistical/categorical/distribution/regression time views,
  local calendar ticks, actual Chromium/Rust metadata editing/history/export
  and installed-wheel/CLI checks are recorded in
  [core evidence](review_evidence/v2_temporal_core.json) and
  [the clock contract](TEMPORAL_AXES.md). The
  [pure groundwork receipt](review_evidence/v2_temporal_groundwork.json) remains
  historical. Source values, offsets, units and original selected IDs survive.
- **F02 raw/native extension verified:** bar/errorbar/band/stackplot/rug/hexbin
  time coordinates, absolute uncertainty endpoints, duration scaling without
  origin, and stem/stairs/event/start-duration paths have numerical and missing-
  data regressions, minimum-environment coverage, actual native Chromium/Rust
  history/reopen/export and installed-wheel/CLI proof in
  [raw/native evidence](review_evidence/v2_temporal_raw_native.json).
  This temporal integration does not complete the broader N01–N06/D07 units.
- **F02 ISO joint/pair extension verified:** explicit variable clocks, clock-
  matched marginals/diagonals, group selection and pairwise missingness have
  numeric-day geometry references, real Chromium/Rust raw-action/edit/history/
  reopen/export and installed-wheel/CLI proof in
  [grid evidence](review_evidence/v2_temporal_grids.json).
  Broader G02/G03 workflows remain required, not exclusions or postponed
  versions. No F02/E01/REL01 completion is claimed.
- **F02 secondary-y subset verified:** vertical hist/KDE/ECDF keep their shared
  observation x clock and move numeric mass/density to y2; explicit temporal
  semantic scatter/line and existing raw y2 paths have numeric-day geometry,
  source/JSON/action checks and real Chromium/Rust edit/history/reopen/three-
  format export proof. Independent review found primary-y category leakage and
  omitted y2 quality diagnostics; both were reproduced and corrected with
  regressions. See [secondary-y evidence](review_evidence/v2_temporal_secondary.json).
  Wider F01/D06 semantics, ECDF bivariate cumulative workflow and the remaining
  catalogue are still required; this does not close those rows or REL01.
- **D02 step+dodge subset verified:** unfilled grouped steps use the same raw
  hue slots and unchanged weighted/cumulative heights as dodged bars, including
  empty reservations, inverted log axes, horizontal orientation and date/y2
  intersections. Native-stairs numeric references, actual Chromium/Rust human
  geometry editing/history/reopen/three-format export and installed API/CLI
  checks are recorded in [step+dodge evidence](review_evidence/v2_histogram_step_dodge.r2.json).
  Other D02 units remain required; the row is not complete.
- **D02 explicit fill subset verified:** optional bool/null `fill` supports filled
  native steps and outline bars across layer/stack/dodge, with unchanged weighted
  heights and mass. Omission preserves the old six-field JSON and constructor;
  seven previous-wheel defaults match exact spec/action JSON and rendered pixels.
  Filled-step hatches retain native contrasting strokes; explicit alpha, edge,
  zero width, empty styles, log/date/y2 and rejected-edit preservation have numeric,
  SVG and actual Chromium/Rust lifecycle checks. See
  [fill evidence](review_evidence/v2_histogram_fill.json). The published schema,
  field fixture, installed API/CLI and English/Korean guidance are synchronized.
  Other required D02 units remain; see the composition/poly increment below.
- **D02 composition/poly subset verified:** the owner selected normalization of
  existing stat/common_norm/cumulative heights, followed by per-bin group sums.
  Cumulative fill is composition, not a CDF, and may decrease. Poly uses native
  raw-bin/slot-center segments/areas with an unfilled default, at least two
  representable centers, no fitting/jitter and no empty-layer framing changes.
  Numeric/native references, overflow/subnormal guards, v/h/log/inversion/date/y2,
  collection hatch diagnostics, API/action/JSON/CLI and actual Chromium/Rust
  edit/history/reopen/three-format export are recorded in
  [mode evidence](review_evidence/v2_histogram_modes.json). Old default JSON,
  actions and pixels match prior-wheel controls. Discrete/named automatic bins
  and the complete width-coordinate contract remain mandatory, not excluded or
  deferred; D02 and the statistical task are not complete.
- **D02 bounded binning functional evidence:** Fixed eight named rules, capped pre-allocation counts, weight-independent edge selection, integer/input-unit discrete bins and strict midnight/precision rejection are recorded in [binning evidence](review_evidence/v2_histogram_bins.json). Together with prior fill, modes and step+dodge receipts, the finite D02 functional rows are covered, subject to parent closure review and final RC qualification. Current/minimum core cohorts each passed 563 with zero skips; later interface checks are separate (41 current, 2 minimum), not a new final 563-tree run. Legacy defaults remain unchanged. D02 closure review/final qualification remains; neither the whole statistical goal nor v2.0 release is complete.
- **D02 bounded acceptance closed:** Parent verification and independent review now accept the frozen D02 functional scope. The [closure record](review_evidence/v2_histogram_bins_closure.json) links the immutable binning snapshot and prior geometry receipts, records current source lineage, actual browser/file checks, visual inspection and unchanged legacy defaults. This closes functional acceptance only: final frozen-source qualification, other catalogue rows and the local 2.0.0 release remain incomplete.
- **C01 categorical strip functional batch — in progress:** opt-in category × hue
  order/dodge reservations, v/h, native numeric/log/date spacing and typed local
  uniform/none jitter are implemented while omitted controls retain the legacy
  raw-x path/JSON. The exact slot-fraction/seed contract, 399-case targeted cohort,
  real editable JSON and PNG/SVG/PDF example exports are recorded in
  [functional evidence](review_evidence/v2_strip_categories.json). C01 remains
  open for actual browser/Rust edit/history/reopen/export, installed API/CLI,
  supported-minimum and parent acceptance; no F01 or v2 closure is implied.

- **CND03 evaluation complete — condition not triggered:** actual DESIGN/source/
  history/dependency navigation found no concrete table-of-contents obstruction.
  No structural split/reorganization is justified. The separate English/Korean
  correction describing the existing 64-action Store checkpoint is accuracy
  maintenance, not triggered reorganization. See
  [navigation evaluation](review_evidence/v2_design_navigation.json).
  This closes only CND03's required evaluation. CND01/CND02 have separate
  condition, implementation and qualification receipts.

- **CND01: condition triggered; specialized Rust controls implemented.** Actual Chromium comparison found no usable Rust second-panel axis forms or movement handles. Active-panel x/y/y2/z controls and supported native-coordinate title/legend/text/annotation movement now use the installed Python boundary, retaining generic layer/raw-action access. [The local feature receipt](review_evidence/v2_rust_specialized_controls.json) preserves attempts, installed/browser lifecycle results, native pixel references, and source/artifact hashes. This is scoped CND01/E01 evidence, not completion of E01 across every catalogue row or REL01. Package 1.1.0, schema 0.1, source measurements, and dependency floors remain unchanged.
- **M01 annotation/rotation subset — in progress:** optional same-shaped custom
  annotation strings and tick rotations preserve scalar colour values, masks
  and original row/column identity through clustermap reorder. The reviewed
  isolated patch is integrated; current-main numerical/artist/editor-history
  tests and the actual create/save/reopen/CLI/PNG/SVG/PDF workflow are recorded
  in [subset evidence](review_evidence/v2_heatmap_annotations.json).
  Wider norm/colourbar/layout controls, full Rust/browser/installed qualification
  and final Linux gates remain required. This does not close M01.

- **C01 bounded functional acceptance closed:** parent source/raster/vector-
  structure review, actual Rust/browser layer editing/history/reopen/export and
  the single frozen C01+M01-subset+CND02 installed/minimum snapshot are accepted.
  [Closure evidence](review_evidence/v2_strip_categories_closure.json) preserves
  the earlier partial receipt, exact commands, source/wheel hashes, corrected
  harness failure lineage and distinct current 407/minimum 369 cohorts.
  Full frozen-product Linux/REL01 qualification and wider F01 roles remain.
- **CND02 triggered evaluation resolved:** the approved immediate default-Store
  undo/redo improvement is integrated and accepted with alias/isolation/custom-
  replay/failure-boundary tests, the same complete 100k×1000 workload and installed
  core evidence. [History evidence](review_evidence/v2_history_immediate.json)
  preserves the provisional opinion, pre-implementation trigger decision and
  distinct isolated/integrated measurements. One extra retained graph, unchanged
  limits and nontransactional deeper-undo failure semantics are explicit.
  This resolves CND02 only, not Rust history, CND01 or final REL01.

- **F01 existing-family guide increment — in progress:** scatter/lineplot now
  share explicit numeric-hue colourbars and finite scatter point-unit outlines.
  Exact raw ticks use the same stable map/cmap in non-data normalized guide
  coordinates, including constants, signed extremes and neighbouring/subnormal
  bounds. Guide intent is planned per logical panel/shared scope before drawing,
  including later requests and primary/y2; conflicting requested labels reject.
  [Increment evidence](review_evidence/v2_semantic_colourbars.json) preserves
  the initial failures/reproductions, corrected current 197/minimum 30 cases,
  actual example exports and exact source hashes. All named family adapters,
  the four-family scenario and installed/browser/full-product gates remain
  mandatory. This does not close F01.

- **F01 four-family subset verified, not row closure:** shared scatter/line/strip/
  ECDF raw-row domains, mark-specific size units, weighted right-continuous ECDF
  knots and categorical reservations have current and supported-minimum cohorts
  of **726 passed each**, recorded separately in
  [subset evidence](review_evidence/v2_semantic_families.json). The unsupported
  horizontal semantic lineplot/y2 guard now precedes temporal conversion; the
  earlier 705-pass/1-failure run is not passing proof. The actual example and CLI
  raster/vector exports were rerun after this correction. Wider F01 remains open.
- **C01 positional compatibility supplement:** the appended optional strip
  configuration no longer displaces the existing positional alpha argument.
  An actual archived 1.1 engine and current engine both bind and visibly render
  alpha 0.25; the consumer regression passes in the separate current/minimum
  cohorts above. [Supplementary evidence](review_evidence/v2_strip_positional_compatibility.json)
  preserves lineage without modifying C01's original closure/archive.
- **D07 complete functional workflow — parent functional acceptance closed:**
  x/primary-y/y2 rugs use live blended observation/axes-fraction transforms,
  finite height and raw-row hue/stroke-point/dash semantics without contaminating
  unrelated data limits or automatic views. Zero height/stroke retains segments.
  [Workflow evidence](review_evidence/v2_rug.json) records independent native/
  date/log/DPI/layout/group/facet/empty references, actual Rust human-form rejected-
  edit preservation/history/download/reopen/three-format export and reviewed
  rasters. A freshly executed archived engine and frozen current source match
  exact old spec/actions/RGBA for four legacy cases; initial mismatches remain
  failure lineage, not passing evidence.
  Separate current/minimum broad cohorts each passed **987** before test-only
  review cleanup. The same single frozen 1.1.0 wheel then passed outside-checkout
  API/CLI consumers and separately **127 reviewed tests each**, plus explicit
  Python `-S` wheel-zip pure builder/validate/action/JSON paths with third-party
  effects actively unavailable. The no-deps scenario separately passed once per
  environment. These are distinct cohorts, not a sum or a new full-tree count.
  No engine rebuild was needed for the reviewed test-only changes. CND01 was not
  integrated; broader F01/F02 and frozen-product/REL01 qualification remain open.
  Parent reviewed the complete source/raster/proof chain, commands and limits,
  including installed and actively dependency-denied pure paths, and accepted
  D07. This does not close whole F01/F02/E01/Q01/DOC01/REL01 or v2.

- **CND01 coordinated integration — parent functional acceptance closed:**
  the reviewed specialized-control patch is merged into current F01/D07 source,
  retaining original renderer layer indices, shared guides, rugs and clocks.
  [Integrated evidence](review_evidence/v2_cnd01_integration.json) distinguishes
  current source **413 passed**, installed current **144 passed**, installed
  pinned minimum **16 passed, zero skips**, fractional native-pixel references,
  Rust **20 library + 1 binary passed / 5 helper tests ignored**, Rust 1.88,
  clippy/format, generated synchronization and clean project type checks.
  One new frozen snapshot/wheel serves both installed profiles; source-unset
  driver/native references/bridge origins and desktop/mobile surfaces are retained.
  The original isolated 54/16/2 and Rust proof remains historical, not integrated
  qualification. The prepared minimum harness was executed here after the peer's
  external service failed; no peer qualification is claimed. Earlier D07 archives
  remain immutable. This does not close whole E01/F01/F02 or product/REL01 gates.
  Parent accepted the integrated source/raster/proof chain and separate current/
  minimum profiles. All three conditional evaluations are resolved; this does
  not close global E01/QA/docs/REL01 or the remaining v2 catalogue.

- **C02 complete functional workflow — parent final functional acceptance closed:**
  native named markers, raw-row hue/diameter/style semantics and explicit
  panel/axis-local cross-layer packing are implemented with the unchanged
  2,000-usable-row/layer limit and a separately profiled, explicit new
  4,000-physical-instance/scope bound (not an SLA or CND02 limit lift).
  [Whole-row evidence](review_evidence/v2_swarm_workflow.json) records independent
  native path/stroke/measurement geometry, date/log/orientation/y2, redraw/DPI/
  layout/facet lifecycle, retained crowded instances, eight actual archived-
  engine exact legacy comparisons, installed actions/JSON/CLI/no-dependency
  use and real Rust human editing/history/reopen/PNG/SVG/PDF workflows.
  Source current/minimum **1,035 passed / 1 host-TeX skip each** are their own
  frozen test snapshot. Final installed current/minimum **302 passed / 1
  host-TeX skip each** qualify the reviewed test-only oracle cleanup, with the
  copied figure-isolation fixture and matching installed driver/native
  references/bridge. These cohorts are not summed. Parent accepted revised
  publication examples and a separate readable Rust surface/native vectors;
  the editor PNG download is its existing capped cached preview, while the
  same downloaded JSON produces exact **3,600×2,100** PNGs in both installed CLIs.
  Dense functional stress screenshots are not publication visual QA. Parent
  reviewed the final source/raster/proof chain and accepted the whole C02 row;
  wider catalogue and final product qualification remain mandatory.
- **G01 reusable live-template increment, not row closure:** C02 uses one typed,
  serializable explicit whole-template transaction recipe with frozen resolved
  selectors/orders, including reserved empty cells. Per-cell edits remain local;
  a later explicit whole replacement supersedes them. Saved materialized views
  remain authoritative on reopen, not automatic reactive regeneration. Ratio-
  only edits retain partially filled grids; structural replacement/real panel
  expansion detaches the recipe while preserving views. Real post-reopen Rust
  edits, native per-cell geometry, rejection preservation and history are in the
  same C02 receipt. Wider G01 families/combinations remain mandatory.
- **N11 coordinated integration — parent final functional acceptance closed:**
  [Integrated spectral evidence](review_evidence/v2_signal_spectra_integration.json)
  binds the reviewed source patch and seven native signal kinds to the same
  single C02+N11 wheel. Explicit sampling/window/FFT/parity/units, independent
  numerical references, weak even-bin coherence followed by well-conditioned
  odd padding, real generic Rust forms and installed current/minimum consumers
  are covered. The separate **integrated** offline TeX profiles install that
  wheel afresh and each compile seven PGFs/eight pages with LuaLaTeX→BibTeX→Lua×2;
  citations, PDF links and native/extracted Σ/² are verified. The formerly
  host-skipped PGF regression passes separately in each TeX profile; it is not
  added to the source cohort. Isolated PGF proof remains separately archived.
  Float64 computed-zero masks do not prove physical exact zeros or guarantee
  high-dynamic-range relative FFT accuracy. No version/floor/publication change
  or whole F01/F02/G01/E01/Q01/DOC01/REL01/v2 completion is claimed. Parent
  reviewed the integrated source, current/minimum consumers, actual Rust and
  compiled PGF proof and accepted all specified N11 local feature gates.

- **C03 whole functional workflow — parent final functional acceptance closed:**
  the existing box layer now supports typed column-reference `bxp`, raw seeded
  median bootstrap CI, final-body-fraction caps and exact raw-key per-hue
  components. [Complete evidence](review_evidence/v2_box_workflow.json) binds all
  **64 engine modules** to one immutable wheel/source archive, independent native/
  cbook/seeded/Fraction geometry, correct primary/y2/date/log/v-h paths, availability
  and component ownership, real source/Rust/installed lifecycle and exact
  archived-engine legacy parity in **12 cases**. New advanced limits are
  **256 drawn samplecells**, **10000 selected source rows AND separately10000
  declared flier values**; legacy no-new-request limits and JSON remain unchanged.
  Shared selector/percentile and zero-stroke roots retain actual observations,
  independent markers/fill and mean/sum arithmetic. Existing live boundaries now
  resolve new per-hue reservations before view validation and use the effective
  category source, not one-column measurement x. Literal old orders stay literal;
  `order=None` is the distinct inference request. Corrected causal attribution
  and the actual immutable-engine contrast are retained, not relabeled.
  Frozen source current/minimum **1674 passed / 2 host-PGF skips each**,
  installed current/minimum **586 passed / 2 host-PGF skips each**, and the
  postfreeze test-only primary/y2 native/log matrix **16 passed each** are
  separate snapshots/cohorts, not a summed count. Both formerly host-skipped
  Box/N11 PGF cases pass in each actual TeX profile; five native box PGFs compile
  to six pages/profile with LuaLaTeX→BibTeX→Lua×2, resolved citation/URI/μm and no
  missing characters. Parent accepted the actual example, readable installed
  Rust surface and compiled minimum contact-sheet visual proof, including honest
  unclipped CI outside IQR. Rust's PNG is its existing capped cached preview;
  the same downloaded JSON produces exact **3600×2100** PNGs in both installed CLIs.
  All specified local C03 feature gates are fulfilled; parent reviewed the final
  source/raster/proof chain and granted functional acceptance. No whole
  F01/F02/G01/E01/Q01/DOC01/REL01/v2 completion, N12 integrated proof,
  version/floor change or publication is claimed.

- **N12 coordinated integration — parent final functional acceptance closed:**
  the approved finite tick locator/formatter, native
  scale-parameter and derived-axis contracts are integrated without replacing
  newer C03/C02/live code. [Integrated evidence](review_evidence/v2_axis_controls_integrated.json)
  binds **66 engine modules** to one new wheel, source archive, current/minimum
  installed prefixes and independent native references. The immutable isolated
  N12 and accepted C03 archives remain distinct evidence.
  Frozen source current/minimum each report **2019 passed / 2 host-PGF skips**.
  Each original installed cohort remains **1156 passed / 1 private child-import
  harness failure / 2 host-PGF skips**; its affected case separately passes once
  per profile after an installed-only `-S` import-root correction, with all66
  hashes and exact installed origin verified. These are not summed or relabeled.
  Both installed Rust and Python frontends execute real human forms, contextual
  handle boundaries, frame-aware base-two pointer geometry, rejection/history,
  four downloads and reopen; actual displayed decoded RGBA equals the current
  cached PNG at every checkpoint. Parent accepted these functional stress
  surfaces and the separate readable **5100×3000** six-panel example.
  Fresh offline installs of that same wheel produce **8 native PGFs/profile**;
  LuaLaTeX→BibTeX→Lua×2 yields **10 document pages**, including blank wrapper
  page07 and bibliography page10—not ten plotted figures. Native hashes remain
  unchanged through the documented wrapper-header repair. Actual compiled
  μm/Σ/², distant2100 20/21µs labels, citations and PDF URI are verified;
  selected native PGF regressions separately report **3 passed / 187 deselected /
  0 skipped** per TeX profile. Parent accepted the compiled-page evidence.
  Actual immutable-C03-versus-integrated controls match JSON/actions/RGBA/limits/
  labels in **10 cases/profile**. Rust's downloaded PNG remains the capped
  **2000×533** preview; the same downloaded JSON renders exact **4500×1200** PNGs
  in both installed CLIs. Full MIT/Matplotlib notices and the composite
  `MIT AND LicenseRef-Matplotlib` expression are verified; own MIT, dependency
  floors, package1.1.0 and schema0.1 remain unchanged. Parent reviewed the final
  source/raster/proof/ledger chain and accepted the entire approved N12 workflow;
  no whole F01/F02/G01/E01/Q01/DOC01/REL01/v2 or N13 closure is claimed.

- **C04 whole workflow — parent final functional acceptance closed:**
  [Receipt](review_evidence/v2_violin.json) binds paired-half lanes (including
  one/odd/reserved hues), weighted normalization, real inner/component traits,
  body-outline stroke-point size, actual style glyphs, date/native/log/y2 and
  frozen live-template edits to one **69-module / 94de3f91… wheel**. Native raw
  inheritance and floor-safe absent strokes retain independent fill/glyphs.
  The original current SOURCE cohort remains **2662 passed / 1 obsolete-contract
  failure / 6 skips**; its corrected consumer case separately passes once.
  Minimum SOURCE with the explicit corrected-test overlay reports **2663 passed /
  6 skips**. Each installed current/minimum cohort reports **1718 passed /
  3 host-PGF skips**, with required browsers, matching native/bridge interpreter,
  no source fallback and per-test figure isolation. These cohorts are not summed.
  SOURCE skips are three host-PGF plus three unavailable-CJK-font cases, not font
  passes; actual offline TeX separately reports **4 passed / 279 deselected** per
  profile. Both real frontends/profile execute human forms, live/role/inner edits,
  rejection/history/download/reopen and decoded displayed-PNG revision equality.
  Parent accepted readable human surfaces and corrected publication/compiled
  examples: five hue guides occur once, shared guides do not cover tail strokes.
  Actual native maxima retain **256 profiles / 10000 selected rows / 1000 support
  points**, **512768 vertices including closures**, and separately all **10000
  stick segments / observed SVG diamond glyphs**. Capped readable PNG downloads
  are **2000×1166**; the same downloaded JSON produces **3600×2100** identical
  API/CLI RGBA, and invalid input retains the prior complete output.
  Actual accepted-N12-versus-new controls match JSON/actions/RGBA/limits/labels
  in **24 comparable cases/profile**. Original failures/archives remain; corrected
  SOURCE/SDIST-only test bytes have a separate final binding, not a runtime-wheel
  rebuild. Package1.1.0/schema0.1, own MIT/full notices and floors remain unchanged.

- **N13 coordinated integration — parent final functional acceptance closed:**
  [Integrated receipt](review_evidence/v2_panel_layout_integrated.json) is distinct
  from accepted isolated r4 evidence. The same combined wheel exercises one flat
  bounded graph, stable IDs, spans/ratios, real child insets and sharing, selector-
  stable partial live grids, explicit-only native Tight layout and opt-in unit
  checks without changing old no-opt-in sharing. Both installed profiles render
  thin **and** balanced **256-grid / 256-panel / 1024-cell / 1024-layer** graphs,
  valid depth16, rejected depth17/cycles with prior-output retention, and all
  **16384 configured tick labels** without sampling. These are functional cost
  proofs, not readable figures, RSS or an SLA. All four real frontend/profile
  flows have 15 decoded-current-PNG checkpoints; actual source-unset 69-hash
  driver/bridge/frontend envelopes bind them to this wheel. Whole 1400/540px
  screens expose eight populated controls without horizontal overflow.
  Each offline profile exports **13 native PGFs → 14 document pages** (13 plots
  plus bibliography), with resolved citations/URI and real μm/Σ/²/clock glyphs.
  Desktop and TeX current NumPy versions are recorded separately. Isolated
  counts are never relabeled integrated, and neither row closes broader
  F01/F02/G01/E01/Q01/DOC01/REL01 or the full v2 catalogue.

- **C05 whole Main workflow — parent final functional acceptance closed:**
  [Receipt](review_evidence/v2_boxen_workflow.json) preserves corrected R4's
  complete isolated evidence separately from the new **de3fe109… wheel /
  71-module aa6243b8… runtime**. Both fresh installed profiles exercise independent
  weighted LEFT bands/tails, typed True/1 roles, actual BODY stroke/flier glyphs,
  original IDs, date/log/y2 fixed selected and empty live cells, local-versus-whole
  template replacement, undo/redo/reopen, real CLI PNG/SVG/PDF and complete-output
  retention. Python-S actively refuses NumPy/Matplotlib/SciPy while the shipped
  pure C05/C07 builder/action/JSON workflow executes. Parent reviewed both the
  complete isolated named ledger and this distinct combined proof and accepted
  the whole C05 row; broader catalogue gates remain open.

- **C07 whole workflow — parent final functional acceptance closed:**
  [Same-artifact receipt](review_evidence/v2_statistical_workflow.json) binds the
  **de3fe109… wheel / 71-module aa6243b8… runtime**, the full immutable 906-file
  source-design SDK and corrected final SOURCE/SDIST-only consumer/docs lineage.
  Both frozen source profiles passed **3010 cases / 22 explicit TeX/CJK skips**
  separately. Original installed **2183-pass / 11-skip / 20-setup-error** cohorts
  remain failed; short-owned-TMP browser **32-pass / 1-disclosure-test-failure**
  cohorts and each separate **1-pass** real-disclosure continuation are not summed
  or relabelled. All actual frontends/installed profiles execute the required
  workflows and ten decoded-current-PNG checkpoints per readable flow, with real
  exports/reopen and exact API/CLI **3600×2100** PNG from downloaded JSON.
  Independent native geometry covers 72/300 DPI, v/h, primary/y2 and real inverted
  insets. Actual bounds exercise 10000 selected rows/256 cells and the full
  requested 100000 resamples: **2B unit+case work / 1B random elements**, exact
  independent CI and RNG state, not an SLA/RSS claim. Each offline profile exports
  **7 native PGFs → 8 document pages** with Lua/BibTeX, real glyphs/URI/references.
  Sixteen actual archived controls preserve spec/actions/RGBA/labels per profile;
  five native view endpoints differ by at most 2 ULPs, explicitly not exact limits.
  Parent reviewed the complete evidence matrix and exact seven-path nonruntime
  SOURCE/SDIST correction and accepted every specified local C07 gate. Original
  failed cohorts and all immutable identities remain unchanged; no broader
  F01/F02/G01/E01/Q01/DOC01/REL01/v2 closure is claimed.

- **C06 whole workflow and final-source lineage — parent accepted/closed:**
  [Companion](review_evidence/v2_count_scopes_final_source.json) keeps the original
  accepted owner decisions/cohorts/visual/editor evidence immutable and binds the
  current 71-module aa6243b8… runtime/de3fe109… wheel/corrected 908-file source.
  New matched current/minimum public native consumers independently verify all/
  category/group denominators, raw log-stack tops, selected panel-local and empty
  views, local/whole-template history, real CLI outputs and complete-output
  rejection. Python-S actively refuses optional libraries. No old cohort was
  rerun to confirm or relabelled as current; no new count feature was added.

- **D02 bounded whole workflow and final-source lineage — parent accepted/closed:**
  [Companion](review_evidence/v2_histogram_final_source.json) retains bounded whole
  D02 acceptance and the original eight-rule/native/visual/editor evidence.
  Both final-wheel installed smoke paths actually exercise weighted nonuniform
  filled step+dodge, outlines, fill/poly, auto/discrete/time-unit and date/y2
  geometry plus CLI/action/reopen; pure Python-S covers all fixed rule names.
  Histogram/bin math and the native histogram renderer seam are byte-identical
  to retained accepted sources. This closes the missing latest-source binding,
  not by hashes alone or another old full-cohort run; REL01 and broader rows stay open.
