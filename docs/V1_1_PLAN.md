# v1.1 development tracker

*[한국어 / Korean](V1_1_PLAN.ko.md)*

Target: **v1.1**, expanding the functional plotting/statistics coverage described
in [FEATURE_COVERAGE.md](FEATURE_COVERAGE.md). This is work in progress, not a
release announcement or a claim of full upstream parity. The package/editor
version remains 1.0.0 until the actual release gates pass; no tag or publication
is authorized by this tracker.

## Ordered batches

- [x] **B0 — Bar visual foundation:** supplied SD/asymmetric bounds, independent
  error/cap styling, publication theme, deterministic comparison previews.
- [x] **B1a — Shared estimation / first raw-data subset:** named estimators,
  SD/mean SEM/PI/seeded bootstrap CI; barplot/pointplot/countplot; honest ranges
  even outside point estimates, missing/singleton behavior, JSON/editor support,
  numeric/artist/reference tests and actual examples (2-D linear ordinal axes).
- [x] **B1b — Extended inference subset:** paired-row weighted mean/CI,
  two-stage unit/within-unit-row resampling with explicit assumptions and
  count/proportion/percent normalization. Safe named operations only.
- [x] **B2a — Statistical categorical geometry:** orientation, order/hue order,
  reserved empty slots, dodge/gaps, stacked counts and formatted bar/count labels.
- [x] **B2b1 — Box/violin first subset:** optional category/value columns, hue
  nesting, order/orientation/width/gap/numeric dodge, native box summaries,
  deterministic notches and violin bandwidth/grid/mean/median/extrema controls.
- [x] **B2b2 — Swarm first subset:** draw-time display-space circular packing,
  orientation/order/hue/dodge, actual layout/DPI and positive log-value transforms,
  all rows retained with explicit overcrowding reporting.
- [x] **B2b3 — Letter-value first subset:** boxenplot linear-interpolated
  quantile bands, four named/explicit depth rules, exponential/linear/area widths,
  median/tail controls and category/hue geometry with strict option validation.
- [x] **B2b4 — Native/log distribution subset:** box/violin/boxen/swarm numeric
  native categories, log-coordinate spacing, positive log values and explicit
  data/axis-space summaries/KDE; preserved defaults and shared-axis validation.
- [x] **B2b5 — Violin semantics subset:** four inner modes/None, two-hue split,
  area/count/width and explicit normalization scope, bandwidth adjustment and
  bounded cut/clip. Preserved defaults, logs/empty/singular cells and strict controls.
- [x] **B2b6 — Independent component subset:** typed named box body/whisker/cap/
  median/mean/flier and boxen body/median/flier styles; strict role/value/visibility
  controls, inherited defaults, hue/tier styles and unchanged native/log geometry.
- [x] **B2b7 — Statistical native/log subset:** bar/point/count physical numeric
  categories/spacing, positive log values, explicit log-fit inference and raw bar
  baselines, count semantics/labels, strict limits and preserved ordinal defaults.
- [x] **B2b8 — Weighted violin:** relative covariance/effective n, inverse weighted
  ECDF marks, count-mass widths, paired rows/native log geometry; 78 new tests,
  full 1923/minimum 1468 pass with real TeX and Rust 1.99/browser bridge.
- [x] **B2b9 — Numeric size-only swarm:** one selected layer-local cohort, stable
  diameter mapping/non-data numeric guides, scalar legacy and physical packing preserved.
- [x] **B2b10 — Categorical swarm sizes:** stable observed/explicit ranks,
  selected source rows, reserved size slots and observed-only guides.
- [x] **B2b11 — Named Swarm size domains:** pooled original-row sizes/guides,
  local observations/colours, duplicate-guide suppression and pure pooled limits.
- [ ] **B2b — Categorical remainder:** broader component/semantic mappings and
  swarm style/date/mixed-family shared/facet semantics.
- [x] **B3a — ECDF subset:** finite weighted empirical steps, tie/right-limit
  semantics, strict complements, per-curve proportion/percent/count, grouped
  color/dash slots, v/h/log observations and typed pure/JSON/editor contracts.
- [x] **B3b — Histogram statistics subset:** typed opt-in shared bins/paired
  weights, six statistics, pooled/per-curve in-range normalization, cumulative
  integration, v/h/raw logs and preserved legacy defaults; 95 new tests.
- [x] **B3c — Configurable weighted univariate Gaussian KDE:** strict opt-in
  bandwidth/grid/cut/clip, relative weighted covariance/effective n, pooled vs
  separate mass/common grid, analytic cumulative/fill/v-h/raw-log units,
  singular skip and legacy preservation; 125 new tests.
- [x] **B3d — Weighted bivariate Gaussian KDE:** strict kde2d/full covariance,
  paired x/y weights/raw grid/log display and conditional-grid HDR contours/
  fill, no singular regularization; 129 new tests + 1 registry-param regression.
- [x] **B3e — Numeric-x line estimates:** separate lineplot/shared named pointwise
  intervals and per-x weighted/unit CI, sort/bands/bars/raw-log contracts;66tests,
  full1990/minimum1534 + Rust1.99/real browser/TeX pass.
- [x] **B3f — Independent scatter semantics:** strict SemanticSpec/paired hue/size/
  style, explicit kinds/orders/global bounds/non-data guides;85tests,
  full2075/minimum1619 + Rust1.99/browser/TeX pass.
- [x] **B3g — Named figure-shared scatter scales:** pooled unique row IDs, same
  settings/global domains/colour blocks, pooled non-data guides once per panel;
  36tests, full2111/minimum1655 + Rust1.99/browser/TeX pass.
- [x] **B3h — Independent lineplot semantics:** raw tuple curves/shared scopes,
  widths/markers/optional dashes/paired pointwise inference;48tests,
  full2159/minimum1703 + Rust1.99/browser/TeX pass. Approved foreground rechecks
  recovered final exit receipts; original interrupted logs remain non-evidence.
- [x] **B3i — Histogram grouped geometry:** opt-in layer/stack/dodge with original
  weighted heights/normalization, ordered empty hue slots, v/h/raw-log bins and
  strict overflow/collapse checks before artists; 48 added regression cases.
- [x] **B3j — Histogram step outlines:** opt-in unfilled native stairs for
  layer/stack with unchanged weighted heights/edges, v/h/raw logs, reserved hue
  dashes and exact stroke style; 43 added regression cases, strict combinations.
- [x] **B4a — Automatic facet first subset:** row/col/wrap materialization,
  exact panel filters, stable selected orders, cell-local inference and pooled
  original-row semantic domains; pure/actions/JSON/schema/editors and example.
  See [supported limits](FACETS.md), not full FacetGrid/pair/joint parity.
- [x] **B4b — Raw grouped facets:** eight legacy raw layer types now support
  stable hue orders/slots without statistical conversion. Duplicate/nonmonotonic
  paths, gaps, supplied bars/errors and default unordered behavior are retained.
- [x] **B4c — Joint histogram first subset:** terminal raw scatter/regplot,
  three aligned panels, dynamic paired `dropna`, source retention, consistent
  group slots and independent density/value axes. [Scope](JOINT_GRID.md).
- [x] **B4d — Numeric pair grid:** pairwise scatter/histogram diagonals, group
  orders, dynamic complete cases and named primary value-axis groups excluding
  density y. API/actions/schema/editors and example. [Scope](PAIR_GRID.md).
- [x] **B4e — Configured KDE grids:** joint KDE marginals and pair KDE diagonals,
  strict copied KDESpec, density/cohort/axis preservation and singular skip rules.
  Histogram defaults unchanged; weights/CDF are explicitly rejected in grids.
- [x] **B4f — Binned joint centers:** ungrouped hist2d/hexbin, explicit colorbar=False,
  paired histogram/KDE/ECDF marginals; no general binned facet filters.
- [x] **B4g — ECDF grids:** unweighted count/probability/percent marginals and
  diagonals, exact cohorts/ties/log value axes; histogram/KDE defaults unchanged.
- [ ] **B3 — Relational/distribution remainder:** wider facet combinations/line inference,
  broader histogram/KDE variants and semantic controls.
- [ ] **B4 — Composition remainder:** live facet mapping/consolidated guides,
  wider pair and joint kinds.
- [x] **B5a — Typed heatmap display:** mask/raw annotation/labels, linear/log/
  centered/robust ranges, square/borders and stable finite colourbar computation.
  Legacy defaults and source matrix preserved. [Scope](HEATMAP.md).
- [x] **B5b — Configured regression:** raw residual/log-x/Huber/binomial-logit/
  LOWESS, conditioned fits, cell-local groups and optional statsmodels extra.
  Legacy polynomial and zero-dependency construction remain. [Scope](REGRESSION.md).
- [x] **B5c — Clustered heatmaps:** optional SciPy row/column trees/optimal leaves,
  validated supplied linkage, aligned display metadata, colour strips and
  z-score/min-max. Source matrix retained. [Scope](CLUSTERMAP.md).
- [x] **B5d — Relative weighted point fits:** poly/log-x and raw residuals, source
  retention/positive-row selection, explicit no weighted CI/advanced models.
- [ ] **B5 — Advanced statistics / matrices:** further heatmap/clustering controls,
  weighted CI/bootstrap/advanced-model CI and residual diagnostics/controls.
- [x] **B6a — Vertical numeric stem:** source order/duplicates, explicit baseline,
  primary/y2/positive log; closed unsupported mappings, raw-data gallery example.
- [x] **B6b — Pre-binned stairs:** explicit supplied heights/N+1 edges, vertical
  unfilled linear primary/y2/raw baseline; no implicit hist estimation/mappings.
- [x] **B6c — Numeric event train:** vertical raw-coordinate offset/length,
  duplicates/source preserved, strict linear primary/y2 single-train subset.
- [x] **B6d — Numeric interval band:** explicit start/positive duration and raw
  bottom/height, overlaps retained, strict float geometry/linear primary-y2 subset.
- [ ] **B6 — Native Matplotlib breadth:** remaining primitive/signal/vector/
  mesh/triangle/3-D families, richer axes/normalization/legends/layouts.

B1b extends B1a; neither is full upstream parity. Weights support only means
with no interval or paired-row CI, not weighted sampling probabilities. Units
require bootstrap CI; point estimates are observation-weighted, not equal-unit
means. Missing/zero-weight rows are excluded, and fewer than two effective rows
or units omit intervals with a warning. Count normalization uses all selected
usable rows. Arbitrary callables and unsupported combinations are rejected.
Small primitives may land early when they unblock another batch. Batch
completion requires its documented scope and tests, not merely a function name.

## Current checkpoint

**Operator target is now v1.1 completion**, superseding the earlier v1-only
stabilization limit. Implement documented subsets and verify backward behavior;
this is not full upstream parity or authorization to tag/publish. Operator-created
Loop8 is active every5minutes; do not delete it or recreate other expired schedules.

**Swarm-only named shared sizes.** Existing scale_id pools deduplicated original
source rows for numeric bounds/categorical ranks and per-panel size guides only.
Local observations/colours/refs/packing remain; mixed relational-family IDs,
facet/dropna/empty cells/style/date/y2 still reject. Validate per-layer2000/pool10000/
64levels/config conflicts and pooled area underflow before artists/output writes.
18new/1069related/floor167P3397deselected/CLI2/Rust22P6ignored/11checks/full Windows
nativeHTTP+browser8cases0. Active changedLSP12clean (earlier neighbor5unconfirmed,
not whole-workspace proof); main1/floor1058warnings retained.
[Scope](SWARM_SHARED_SIZE.md), separate PNG/spec and
[evidence](review_evidence/swarm_named_size_verification.json).
Exactee876CI39441022593 ALL5SUCCESS is categorical baseline, not this new runtime.
Publish for fresh wholeCI; no new fields/deps/versions; Loop8 active.

### Earlier review phase 89

**Categorical size-only swarm.** Existing size_kind/size_order use typed keys and
stable first-observed/explicit rank fractions; reserve empty size slots but show
only observed guides. Bool/numeric selections distinct; max64 unambiguous labels,
invalid classes not hidden by order; source/cohort/2000-row cap/packing preserved.
Pure rank helper moved with exact AST body+args, reused by scatter/line/swarm.
33new/1051related/floor149P3397deselected/CLI2/Rust22P6ignored/11checks/full Windows
nativeHTTP+browser7layer0/LSP12clean. Main1/floor1058warnings(1057Pyparsing+1native
invalidsetter) retained. [Scope](SWARM_CATEGORICAL_SIZE.md) and
[evidence](review_evidence/swarm_categorical_size_verification.json).
Exact1dbCI39431316561 ALL5SUCCESS is numeric baseline, not new categorical runtime.
Publish for fresh wholeCI; no new fields/deps/versions; Loop8 active.

### Earlier review phase 88

**Numeric size-only swarm.** Opt-in parsed SemanticSpec maps one numeric column
across selected category/hue rows, listwise missing-size drops, one layer-local
normalizer and exact empty-coordinate guides. Norms clip not filter; 2000 usable
rows/source/JSON/action/URL alignment and scalar legacy retained. Reject facet/
dropna/named scales/semantic hue-style/categorical size/date/y2/scalar override and
unrepresentable positive areas. [Scope](SWARM_SIZE.md), real separate PNG/spec.
31new/1018related/floor116P3397deselected/CLI2/Rust22P6ignored/11checks/full Windows
nativeHTTP+browser6layer0/LSP11clean. Main1/floor834warnings(833Pyparsing+1native
invalid setter) retained. [Evidence](review_evidence/swarm_numeric_size_verification.json).
Exact3d51CI39421985154 ALL5SUCCESS validates prior native fix, not new public
runtime. Publish for fresh wholeCI; no new fields/dependencies/versions. Loop8 active.

### Earlier review phase 86

**Native swarm resize calibration fix.** Returned artist size areas/linewidth
arrays now pack with actual per-pair radii and per-point gutters. Retain mixed
non-dodged hues jointly, source/raw values/uniform offset oracles/DPI/layout/log/
inversion/cycling and warn-once crowd retention. Invalid or nonrepresentable
native arrays reject before offset mutation; no public size-semantic API added.
30new/616related/floor83P3399deselected; main1native-setter warning/floor642warnings
(641Pyparsing+1same deliberate invalid setter),8checks/LSP3clean.
[Evidence](review_evidence/swarm_native_sizes_verification.json): measured native
pair gap18.750001875→52.083338542px for required52.083333333px, source unchanged.
Exact24cdCI39415317017 finished ALL5SUCCESS. Heldb7350de source/checks are
verified unchanged and published now for fresh wholeCI, without cancelling jobs.
B2b public size/style/date semantics remain open.

### Earlier review phase 84

**B6 subset: numeric interval band.** Existing x/y/baseline/width store starts/
positive durations/raw bottom/positive height. Retain overlaps/source/SetData/
JSON/actions, no sorting/merging/estimation. Finite numeric1..10000intervals and
representable distinct float endpoints; reject 2**53 unit collapse/overflow, zero/
negative duration-height and unsupported date/log/group/facet mappings.
39new/613related/floor41P3411deselected13Pyparsing/CLI2/Rust22P6ignored/11checks/
full Windows nativeHTTP+browser5layercases0/LSP11clean. [Scope](BROKEN_BARH.md),
real PNG/spec, [evidence](review_evidence/v11_interval_band_verification.json).
Exact8eeCI39408472076 completed ALL5SUCCESS. The held local480068a unit is
verified unchanged and published now; this interval runtime still needs fresh wholeCI.
No new model/action/spec fields, dependencies, locks or versions; Loop8 stays active.

### Earlier review phase 83

**B6 subset: numeric event train.** Reuse existing x/baseline/width fields for one
train of vertical raw offset±length/2 marks, not axis-fraction rug or rate inference.
Finite nonbool1..10000events/positive length/finite distinct endpoints, linear
Cartesian primary/y2 only. Duplicates/source/SetData/JSON/actions retained; native
sorts artist positions, not source. Strictly reject group/h/date/log/facet/weights.
32new/572related/floor34P3378deselected13Pyparsing,CLI2/Rust22P6ignored/11checks/
full Windows nativeHTTP+browser0/LSP11clean. First floor zero-width dashed legend
failure is retained; invisible dash pattern only removed at width0, no epsilon or
label removal, positive-width dash preserved. [Scope](EVENTPLOT.md), real PNG/spec,
[evidence](review_evidence/v11_eventplot_verification.json).
Exact5eCI39399554406ALL5SUCCESS validates prior HTMX wait, not new event runtime.
Publish this subset for fresh wholeCI; versions/dependencies/locks/schema fields unchanged.

### Earlier review phase 82

**Browser settlement follow-up.** Baseline071CI39377685379 passed minimum and both
native OS jobs; Python3.10 recovery timed out and3.12was cancelled. Normal probe
10P did not prove a fix. A controlled200ms-swap/100ms-settle reproduces stale DOM
while server state has advanced; networkidle alone is not the HTMX lifecycle.
Keep it, then wait for request/swapping/settling classes to disappear. Preserve all
recovery assertions/timeouts; add normal+delayed cases. Before1P1F→after2P;
all eight helper-importing browser files42P on main3.12 and isolated locked3.10.
A first3.10robust-compare1F remains recorded/notclaimedfixed; later isolated/core/
full checks pass. [Evidence](review_evidence/browser_htmx_settle_verification.json).
No app/schema/dependency changes; current Linux/fullCI still required.

### Earlier review phase 81

**Native smoke isolation fix.** The added recent-layer scenario ran before the
fresh-start history boundary test; Rust open is undoable, so restoring spec/PNG
alone left earlier history. Baseline6dCI39280267725failed the same assertion on
Windows and Python3.12's native browser step (its4151P/46skip pytest had passed).
Reproduce the failure, then run history boundaries first; no product behavior,
assertion or timeout change. Full Windows native HTTP+browser0,118connectedP,
Rust22P6ignored/10checks/LSP1clean. [Evidence](review_evidence/native_smoke_history_isolation.json).
One overall900s tool budget ended after the successful887s native run; remaining
checks completed separately, not counted as an interrupted pass. New CI required.

### Earlier review phase 80

**Post-merge integration verification.** Operator requested one normal merge/push.
Remote e752175 dependency updates and both local feature commits are preserved;
locked venv resynced. Full4165P/32skip/17warnings,requiredbrowser/PGF/Tectonic3P,
floor100P/Rust22P6ignored/nativeHTTP3/13qualitychecks and three Python lock audits
pass. A stairs required-bins fixture omission is fixed. Initial browser and Rust
elapsed-time failures remain recorded; unchanged serial/full rechecks pass, not a
claimed fix to timing flakiness. Cargo-audit unavailable; Windows Rust1.99 is not
LinuxMSRV1.88 proof. [Evidence](review_evidence/merged_dependencies_verification.json).
Publish the integrated source for fresh wholeCI; not entire v1.1/tag approval.

### Earlier review phase 79

**B6 subset: pre-binned stairs.** Existing x/bins/baseline fields store N supplied
heights/N+1 explicit edges/raw scalar baseline. Vertical unfilled linear primary/y2
only, no rebinning/normalization/interpolation. Preserve source, edges, JSON/actions/
SetData; require finite numeric1..10000heights/strict finite increasing edges with
representable widths. Reject unsupported fill/open/log/group/facet/semantic options.
[Scope](STAIRS.md), real PNG/spec/source.29new/382related/floor31passes/
3348deselected/13Pyparsing warnings,CLI2/nativeHTTP3cases/Rust22P6ignored/12checks,
activeLSP11clean. [Evidence](review_evidence/v11_stairs_verification.json).
Baseline24bafCI ended cancelled:minimumPASS/RustLinuxFAIL/other3cancelled—notpass.
Publish queued native count-contract fix plus stairs for fresh Linux/MSRV/fullCI.
No new model/action/spec fields/dependencies/locks/versions/tag/publish authority.

### Earlier review phase 78

**Native integration follow-up.** Baseline24bafCI39254853276RustLinux failed an
old hardcoded kind-count assertion (38actual/37expected);Windowscancelled,Python
jobs still running at this checkpoint. Preserve the failure, not a parser bug.
Replace the count with exact raw-JSON kind/required/optional preservation and
explicit stem/weighted-regplot contracts; all previous visual controls remain.

LocalRust1.99 tests22P/6ignored,Python291P,actualownedWindowsnativeHTTPstem/WLS
JSON/PNG/titleapply/undo-redo cache restoration and11quality checks pass,LSP2clean.
[Evidence](review_evidence/v11_native_contract_verification.json). Linux/MSRV1.88/
fullnativeGUI still need CI; no new runtime/schema/dependencies or stairs feature.
Keep this verification unit local while current jobs finish, then fresh whole CI.

### Earlier review phase 77

**B6 subset: vertical numeric stem plots.** Existing baseline fields encode raw
segments/heads without sorting or aggregation; duplicates/source/SetData/styles,
primary/y2 and positive log axes are preserved. Reject missing/nonfinite/bool data,
outside1..10000rows, invalid baseline/styles and unsupported horizontal/group/
semantic/facet/polar/3D mappings. [Scope](STEM.md), real executable gallery assets.
34new/343related/floor36passes/3313deselected/205Pyparsing warnings,CLI3/8checks,
activeLSP11clean. [Evidence](review_evidence/v11_stem_verification.json).
Baseline2dCI39246899201FAILED one generated gallery weights-list drift (full4082P,
minimum3275P,3.12cancel,bothRustP). Regenerate actual gallery and add it to the
cheap schema checker with real drift/restore tests; no weakened guard. An initial
packaging SVG placement failure is preserved; move only new vectors to image root,
then all checks pass. Publish fix/subset for fresh wholeCI—not historical success.

### Earlier review phase 76

**B5 subset: relative weighted polynomial/log-x point fits and raw residuals.**
Reuse LayerSpec.weights and typed RegressionSpec; positive-weight rows drive fit,
scatter, residual and sample/distinct-x checks. Preserve original data, group/hue/
facet/y2/SetData/JSON/actions, legacy unweighted paths and row limits. Missing/nonfinite
inputs, unrepresentable relative weights, weighted bands/bootstrap/advanced models
and weighted joint marginals are explicit failures, not invented inference.
35new/467related/floor35passes/3278deselected/13Pyparsing warnings, CLI3/8checks,
activeLSP10clean. [Evidence](review_evidence/v11_weighted_regression_verification.json).
ExactefdcCI39238007230ALL5SUCCESS validates previous ECDF grids, not new WLS paths.
This bounded B5 subset needs fresh whole CI; weighted inference/other batches remain.
No model/action/spec fields, version/dependency/lock/tag/publish changes.

### Earlier review phase 75

**B4 extension: empirical cumulative grids.** Opt-in ECDF joint marginals and
pair diagonals now support explicit count/probability/percent, preserve the exact
paired versus univariate cohorts, ties/minimum jumps, positive log observations
and independent statistic axes. Unused nondefault bins, KDE options, density and
weighted/complementary configuration are rejected, not silently converted.
27new/328related/floor27passes/3251deselected/CLI2/8checks andactiveLSP6clean.
Floor201warnings are10Pyparsing deprecations;1connected overflow warning belongs
to the unchanged plain-ECDF extreme-count ticker path, not a warning-free claim.
[Evidence](review_evidence/v11_ecdf_grid_verification.json). Exact3f2CI39227715054
ALL5SUCCESS validates binned joint support; publish this subset for fresh wholeCI.
Other v1.1 remainders/release gates stay open; no versions/dependencies/locks changed.

### Earlier review phase 74

**B4 extension: binned joint centers.** Ungrouped/unweighted hist2d and hexbin
with explicit colorbar=False now compose existing paired histogram/KDE marginals.
Complete x/y rows, original data, SetData refresh and independent density axes are
preserved. General binned facet filters, hue_order/group/weights/colorbars remain
explicitly unsupported; center grid/density settings are not marginal settings.
17new/198related/floor17passes/3234deselected/13Pyparsing warnings,2CLIapply-render
flows and8quality checks pass; activeLSP6clean. [Evidence](review_evidence/v11_binned_joint_verification.json).
This completes only this bounded B4 subset, not all remaining batches/gates.
Exactfa1CI39218632870ALL5SUCCESS validates prior state/visual tests; publish queued
supply-chain validation and new runtime for fresh whole CI. Versions/locks stay.

### Earlier review phase 73 (previous scope)

**Scope is now v1 stabilization only.** The operator narrowed work: no new
features/APIs/speculative optimizations/v1.1 expansion. Focus on existing
regressions, installation/output preservation, current CI and necessary safety
checks. Older recurring-loop wording does not broaden this scope or grant publish.

**Review phase 73 verifies an existing release and supply-chain policy.**
Exact v1.0.0 wheel/sdist/checksum assets match digests; verified OIDC certificate
policy pins repo/release workflow/tag/source986a168/hosted runner. Signed tag3db667
also targets986a168, not current main. Wrong-ref verification rejects and an owned
tampered copy mismatches hash; no downloaded code executed or release created.
CI/TeX read-only permissions, scoped build OIDC/publisher writes and fail-closed
source guards are tested; three locked Python audits have no ignored advisories.

6new/34related/floor6passes/3228deselected/13Pyparsing warnings and10checks pass,
activeLSP2clean. [Evidence](review_evidence/supply_chain_verification.json),
[tracker](REVIEW_CHECKLIST_STATUS.md): **PASS139/RUNNING6/OPEN4/DEFERRED1**.
CI-08/09 PASS is integrity/provenance/policy scope, not current runtime security
approval. Keep unit local duringfa1CI39218632870; runtime/versions/dependencies/
locks/tag/deploy unchanged. Finish only stabilization within the narrowed scope.

### Earlier review phase 72

**Review phase 72 pairs reviewed fixed-environment images with semantic oracles.**
Exact repeat pixels and independent integer point/group/axis/canvas assertions
cover different claims. A collapsed-group control has identical pixels but wrong
artist grouping; a colour-only control keeps numeric meaning but changes0.617%of
pixels. Averaged image error/noise is not blanket approval or cross-env tolerance.
Four NEW evidence images were viewed/diff-reviewed as author representative
baselines; no older baseline was replaced and no automatic rebaseline is added.

3new/76related/floor3passes/3225deselected/13Pyparsing warnings and9checks pass,
activeLSP2clean. [Evidence](review_evidence/visual_contract_verification.json),
[tracker](REVIEW_CHECKLIST_STATUS.md): **PASS137/RUNNING6/OPEN6/DEFERRED1**.
CI-04 PASS is not independent human AT/aesthetic or dense-low-DPI LAY-09 approval.
Exactce717CI39212306093ALL5SUCCESS validates the prior command-contract correction
and required JUnit paths; publish queued state/mutation+visual tests for freshCI.
Runtime/versions/dependencies/locks/tag/deploy unchanged.

### Earlier review phase 71

**Review phase 71 explores state space and selected test sensitivity.**
An independent field/history/future oracle checks5704bounded traces/21128generated
events, serialization and detached listener/public snapshots beyond the existing
fixed-seed corpus. A greedy deletion shrinker records two reviewed redo regressions;
deletion-minimal is not globally minimal or all-domain shrinking.

Five owned-copy mutants (axis/group/duplicate/atomic/redo) are detected after25
unmodified-control passes, with23intentional test failures. Real runtime was
never patched; import isolation and original hashes agree. This is selected
contract sensitivity, not whole-line mutation coverage.9new/52related/floor9/
3216deselected/13Pyparsing warnings and9checks pass, activeLSP2clean.
[Evidence](review_evidence/state_mutation_verification.json), [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS136/RUNNING6/OPEN7/DEFERRED1**. CI-03/05 are PASS only in this bounded scope.
Keep test unit local duringce717CI39212306093; no runtime/dependency/lock/version/
tag/deploy changes or release approval inferred.

### Earlier review phase 70

**Review phase 70 separates E2E costs and documents practical workload scope.**
Same1k/10k raw-line/title actions retain API/editor specs and PNG pixels. Warm
API public-save/close/read medians530/553ms, PythonHTTP+PNG561/597ms and Rust
4215/4431ms are different paths, not a language/SLA claim.100component repeats,
3freshCLI trials,5high-cost samples and cold default/open stages remain separate;
Rust's two Python children/action and larger HTML differ from resident Python.

[Guidance](PERFORMANCE.md)/[한글](PERFORMANCE.ko.md) keeps source/counts for explicit
aggregation, null timings for stopped large histories and no streaming/automatic
history cut. Existing checkpoint/source/contracts support PERF-05/07/08 PASS.
79related/floor15passes/3201deselected/13Pyparsing warnings,9checks/activeLSP3clean.
[Evidence](review_evidence/e2e_performance_verification.json), [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS134/RUNNING6/OPEN9/DEFERRED1**.21dCI39207855660FAILED one old literal-run
format assertion (3983passed/required tools passed);3.12cancelled,min/Rustpassed.
The test now reads actual folded command while retaining full-suite/60min/timing/
JUnit/no-selector constraints. Publish docs/test-only correction for fresh CI,
without weakening gates or changing runtime/versions/dependencies/locks/tag/deploy.

### Earlier review phase 69

**Review phase 69 makes required optional-tool execution visible and fail closed.**
Local optional fixtures still skip, but fixed JUnit required paths must pass once
for CI/minimum/TeX/release profiles. Missing/skip/xfail/failure/duplicate or malformed
report cannot green the gate. UTF-8/64MiB/NUL/DTD/entity bounds protect the reader.
Always diagnostic uploads do not repair failed jobs; profiles/artifacts/cache
namespaces are distinct and release/event/permission guards are unchanged.

Controlled absence yields3skips/pytest0/gate1; actual browser/PGF/four TeX routes
6pass/all4profiles0. Concurrent original/shuffled lanes each41pass/same IDs/new
order; no arbitrary-order or thread-safety guarantee.20new/37related/floor20/
3190deselected/13Pyparsing warnings and10checks pass, activeLSP3clean.
[Evidence](review_evidence/ci_path_matrix_verification.json), [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS131/RUNNING6/OPEN12/DEFERRED1**. Exactd221CI39201840394ALL5SUCCESS
validates prior layer/checkpoint runtime, not this new gate; publish queued docs+
CI controls for fresh whole CI. No version/dependency/lock/tag/deploy changes.

### Earlier review phase 68

**Review phase 68 reconciles paired docs and current author-review evidence.**
READMEs now qualify finite patterns/resource bounds/checkpoint scope and explicitly
close caller-owned save Figures in executable examples. The provenance recipe's
three-open-Figure example issue is fixed to0 without changing API ownership or
output bytes. Source inventory fromc4f40a finds additions (exports41→52/Plot70→84/
actions32→36), no removals; optional parameters/scatter capture/resource narrowing
are classified rather than claimed identical behavior. CLIcommands/flags unchanged.

8newdoccases/63relatedpasses,floor9/3181deselected/13Pyparsing warnings,
198relativefiletargets and9quality records pass, activeLSP3clean. [Receipt](review_evidence/documentation_review_verification.json),
[interim review](REVIEW_DECISION.md), [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS129/RUNNING6/OPEN14/DEFERRED1**. DOC-01/02/03 are PASS in this scope;
DOC-04/05/06 remain OPEN and the gate decision is NOT RELEASE APPROVED, not an
independent sign-off. Keep doc unit local duringd221CI39201840394; no runtime/
version/dependency/lock/tag/deploy changes or authority inferred.

### Earlier review phase 67

**Review phase 67 keeps gesture boundaries, adds one checkpoint and optional provenance.**
Real100-move gestures submit once on release; independent edits and undo boundaries
remain separate, without a new core coalescer. Default pure Store replay can start
from one preceding64-action state; custom reducers/history/noop/listener/snapshot
semantics stay intact.1k-row/1000-action undo~405→17ms;10k/256~860→219ms with
~280KBextra traced Python retention (not all-RAM/timing guarantees). History is never cut.

A tested [separate manifest recipe](OUTPUT_PROVENANCE.md) records hashes/selected
environment without volatile image metadata, path dumps or forced sidecars; output
bytes repeat and existing directories refuse overwrite. Hashes are not anonymization.
201related/4actualbrowserpasses/29deselected/floor10/3172deselected/13Pyparsing warnings
and11checks pass, activeLSP5clean. [Evidence](review_evidence/history_improvement_verification.json),
[tracker](REVIEW_CHECKLIST_STATUS.md): **PASS126/RUNNING6/OPEN17/DEFERRED1**.
Exact06fCI39196761559ALL5SUCCESS validates prior044/045; publish queued layer+
checkpoint effects for fresh whole CI. Versions/dependencies/locks/tag/deploy unchanged.

### Earlier review phase 66

**Review phase 66 bounds total layers before model/copy amplification.**
FIND-046 confirms explicit colours bypass palette candidate counts, so that is
not a layer cap. Shared1024TOTAL across panels now gates raw LayerSpec decoding,
AddLayer copying, facet/joint replication and direct-spec validation. Accepted
single/multi-panel/add/facet/joint boundaries and input snapshots are preserved;
pair's existing at-most64one-layer cells need no extra rule. Initial12tests8fail/
4valid become12pass, without truncation/new JSON fields/options.

591related/floor12passes/3160deselected/13Pyparsing warnings,6actualHTTP cases,
5before/5after guarded outcomes and10checks pass, activeLSP9clean.1024fixture
~217MBpeakRSS/~3.2sworker is not all data/artist capacity; text/algorithm/CPU/total
memory and rawJSON cost remain. [Evidence](review_evidence/layer_budget_verification.json),
[tracker](REVIEW_CHECKLIST_STATUS.md): **PASS123/RUNNING6/OPEN20/DEFERRED1**.
Keep layer effect local during06fCI39196761559; versions/dependencies/locks/tag/deploy stay.

### Earlier review phase 65

**Review phase 65 separates source DPI from native effect work bounds.**
FIND-045 now checks40million-pixel work before Figure creation and backend/save
DPI/tight padded bbox, not in spec validation. Large source DPI stays valid and
preview remains2000px/axis; oversized exact effects explicitly reject without
silent output clamping. Accepted6000²/6320²PNG and bounded oversized SVG fixtures,
old-target/cache/Figure ownership and explicit lower-DPI recovery agree.

18new/315relatedpasses/4OSsymlinkskips,floor18/3142deselected/13Pyparsing warnings,
8actualHTTP outcomes and10checks pass, activeLSP5clean. Scope is canvas area,
not total RAM/CPU/caller-direct-Matplotlib protection; SEC-04 remains RUNNING.
[Evidence](review_evidence/effect_budget_verification.json), [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS123/RUNNING6/OPEN20/DEFERRED1**. Exact2a96CI39191652835ALL5SUCCESS
validates prior041/042/043 and Linux/browser test fixes; publish queued structure+
effect runtime for new whole CI. Versions/dependencies/locks/tag/deploy unchanged.

### Earlier review phase 64

**Review phase 64 bounds panel/layout/decode expansion before allocation.**
FIND-044 uses one256panel/cell limit in shared decoding, action expansion and
validation. AddPanel/SetLayout share _ensure_panel; raw arrays reject before
individual panel decode. Auto-create99→100/255→256 and valid boundaries remain,
with no clamp/input mutation/new serialized field. Initial11tests8fail/3valid
become11pass; direct constructed specs and oversized indices fail explicitly.

489relatedpasses/2OSskips,floor11passes/3131deselected/13Pyparsing warnings,
6actualHTTP preservation cases and11before/13after guarded outcomes complete
10checks. Actual256panel fixture is~212MBpeakRSS/~5.1sworker—not all max-data
figure capacity. SEC-04 remains RUNNING for exact export/other complexity policy.
[Evidence](review_evidence/structure_expansion_verification.json), [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS123/RUNNING6/OPEN20/DEFERRED1**. Preserve local structure effect during
2a96CI39191652835(Rust/minsuccess,Pythonrunning). Versions/dependencies/locks/tag/deploy stay.

### Earlier review phase 63

**Review phase 63 measures resource amplification and bounds bivariate grids.**
Suspended Windows children are assigned private Job memory/CPU limits before
running; peakRSS/commit/time/exit outcomes distinguish completed work, validation
and budget stops. Preview stays2000px/axis for huge declared size/DPI. FIND-043
now rejects hist2d>512bins/axis(513edges) and hexbin>512 before native allocation,
retaining accepted data semantics. Initial11tests7fail/4valid become11pass.

263related/floor11passes/3120deselected/13Pyparsing warnings,4actualHTTP rejections
and18measurement records/10commands complete. Job guards are TESTcontainment,
not installed product limits; other structure/exact-export work still hits them.
SEC-04 becomes RUNNING, not PASS. [Resource evidence](review_evidence/resource_amplification_verification.json),
[tracker](REVIEW_CHECKLIST_STATUS.md): **PASS123/RUNNING6/OPEN20/DEFERRED1**.
cb2CI39187999070failed one CDPpinch Redo click interception; earlier focus/data
checks passed. [UI activation](review_evidence/browser_pinch_activation_verification.json)
keeps exact undo/redo expectations via native Enter (local4pass/newLinuxCIneeded),
not force-click/runtime geometry changes. Versions/dependencies/locks/tag/deploy stay.

### Earlier review phase 62

**Review phase 62 verifies matching-checkout assets and mismatch boundaries.**
One tracked htmx/license pair supplies Python/Rust and actual native Chromium
version/hash. Embedded spec/capabilities and declared metadata align. Controlled
current/compatible-label runtimes start; incompatible spec or missing required
capability fails meaningfully. Release preflight explains metadata mismatch;
there is no automatic package-label handshake or all-historical-release promise.

Newpure2/176related/floor2passes/3118deselected/13Pyparsing warnings and9quality
records pass. A focused actual native browser asset check passes; the earlier
full standard smoke exceeded an OUTER480sQA budget without an exit receipt and
remains inconclusive, not passed. RUST-07 is PASS only in the documented scope.
[Evidence](review_evidence/editor_asset_verification.json), [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS123/RUNNING5/OPEN21/DEFERRED1**. Baseline489aCI39183500953failed three
3.10immediate-focus assertions;3.12was cancelled. [Focused synchronization](review_evidence/browser_focus_sync_verification.json)
keeps exact expectations with bounded UI-focus waits (local4pass, newLinuxCI
still required), not a data/runtime change. Publish queued HTML/assets/testfix
for new whole CI. Versions/dependencies/locks/tag/deploy stay unchanged.

### Earlier review phase 61

**Review phase 61 adds missing error/current-page accessibility semantics.**
FIND-042 adds alert semantics to still-escaped errors and aria-current to the
active navigation link; three pure checks fail before/pass after. A real
Tab/Enter/typing/arrows-only journey selects a panel, edits a form, recovers from
JSON failure, moves a handle with normal/Shift steps and visits Docs/Editor.
Pointerdown0, labels/pressed state/focus outline/handle-focus restoration agree.

169related/6actualbrowserpasses/27deselected/floorpure3/3115deselected/13Pyparsing
warnings and9quality records pass, activeLSP4clean. EDIT-08 is PASS in current
Python scope, so EDIT01..09 are reviewed—not independent human AT/WCAG/native
control certification. Long77–86forwardTabpaths remain explicit, no new shortcuts.
[Evidence](review_evidence/keyboard_access_verification.json), [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS122/RUNNING5/OPEN22/DEFERRED1**. Keep new HTML effect local during489aCI
39183500953(Rustsuccess/3Pythonrunning); versions/dependencies/locks/tag/deploy stay.

### Earlier review phase 60

**Review phase 60 fixes lost field context and checks actual machine envelopes.**
FIND-041 made invalid width/height indistinguishable through CLI/native-agent
errors. Shared decoding now prefixes publicClass.field, preserving TypeError/
ValueError,cause,union alternatives and inputs. Initial5fail/3pass become final9pass.
Actual26CLI/UI/native cases check JSON FILE versus stdout,HTML versus JSON,and
binary exports versus500plain failure without changing routes or auth semantics.

386connectedpasses/2OSskips,3actualbrowserpasses/30deselected,floor9passes/
3106deselected/13Pyparsing warnings and10quality records pass. Two connected
singleton pointplot interval warnings are classified separately, not suppressed.
EDIT-07/09 are PASS in support; this is not universal value-redaction certification.
[Evidence](review_evidence/machine_error_verification.json), [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS121/RUNNING5/OPEN23/DEFERRED1**. B9CI39178688403is ALL5SUCCESS, validating
040whole. Publish scaled+recovery+newdecoder effect and obtain new exact whole CI.
Versions/dependencies/locks/tag/deploy stay unchanged.

### Earlier review phase 59

**Review phase 59 checks file and export recovery through real UI controls.**
ValidA→brokenJSON/invalidspec retains spec/PNG/history/layout and submitted draft;
validB opens fresh history and clears errors. A fault in the real SVG save path
returns400HTML, not partial vector output, with cached state/Figure cleanup intact.
PNG editing continues; clearing the fault restores SVG200/latest title and a
JSON download equal to current state. Source files remain byte-unchanged.

New actual browser1 plus229relatedpasses/6Windows-skips,4realbrowserpasses/
29deselected,floor43passes/4symlinkskips/3059deselected/13Pyparsing warnings and
9quality records pass. Initial browser helper timeout is preserved separately;
final runs use the existing post-file-read section visibility check. EDIT-06 is
PASS in current support, not a new export format or complete CLI/agent error audit.
[Evidence](review_evidence/editor_recovery_verification.json), [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS119/RUNNING5/OPEN25/DEFERRED1**. No runtime change; keep scaled+recovery
units local duringnewB9CI39178688403. Versions/dependencies/locks/tag/deploy stay.

### Earlier review phase 58

**Review phase 58 checks scaled/high-DPI browser data editing.** Actual Chromium
contexts assert DPR1/2, CSS125% and CDPvisual-viewport125% separately. Three
cases retain editable6×3inch/600DPI while preview remains2000×1000. Selected-panel
inverted-log/y2 drag and image-fraction keyboard steps map to expected data;
focus/undo/redo/other panels/specJSON stay intact. This is explicit emulation,
not all native browser zoom/OS/physical hardware or dense75DPI geometry proof.

New optionalbrowser3 plus178related/8actualbrowserpasses/28deselected/floorpure7/
3099deselected/289Pyparsing warnings and9quality records pass. EDIT-02 is PASS
in this scope without runtime changes. [Evidence](review_evidence/scaled_preview_verification.json),
[tracker](REVIEW_CHECKLIST_STATUS.md): **PASS118/RUNNING5/OPEN26/DEFERRED1**.
Baseline4bcCI ALL5SUCCESS allowed queued D535response fix+B9tests publication;
newB9CI39178688403is running and must validate that effect. Keep scaled-test/docs
local meanwhile. Versions/dependencies/locks/tag/deploy stay unchanged.

### Earlier review phase 57

**Review phase 57 checks two local pages and a raw-action client sharing state.**
Controlled first render holds the session lock while other bodies arrive;
state/PNG remain at the previous commit. Release yields AthenB/raw in either
allowed order, preserving all disjoint fields/history and pure-apply equivalence.
Final PNG matches a fresh EditorSession from final spec; both tabs refresh to it.
This is shared session/panel state, not per-tab selection or live collaboration;
raw form actions keep HTML responses and no new domain revision is introduced.

New actual browser1 plus169connectedpasses/1OSguard skip,4realbrowserpasses/
31deselected,floor8passes/3098deselected/13Pyparsing warnings and9quality records
pass. EDIT-05 is PASS in bounded local scope. [Evidence](review_evidence/shared_session_verification.json),
[tracker](REVIEW_CHECKLIST_STATUS.md): **PASS117/RUNNING5/OPEN27/DEFERRED1**.
No new runtime change; keep this unit with queued response-order effect local
during4bcCI(Rust/minsuccess,twoPythonrunning). Versions/dependencies/locks/tag/deploy stay.

### Earlier review phase 56

**Review phase 56 fixes late HTML replies replacing newer inspector state.**
FIND-040 reproduces committedA/committedB with Bdeliveredfirst then Adeliveredlate:
DOM reverted toA while spec/PNG stayedB. Private old-helper experiment fails as
expected. Additive local HTMX view generations now ignore older-than-latest-seen
fragments without dropping either action, changing spec or adding domain revisions.
Undo/reset/open/errors retain reply order; server restart requires a page reload.

New browser1/pureHTTP2 and179connected/8realbrowserpasses/26deselected/floor2passes/
3104deselected/13Pyparsing warnings,9quality records and activeLSP5clean pass.
Latest DOM/spec and real browser preview pixel SHA agree; focus/scroll/nudge/panel
regressions remain intact. EDIT-03/04 are PASS in local supported scope, not live
cross-tab collaboration or all zoom/highDPI access certification.
[Evidence](review_evidence/response_order_verification.json), [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS116/RUNNING5/OPEN28/DEFERRED1**. Keep runtime effect local during4bcCI
(2Rustsuccess/3Pythonrunning); versions/dependencies/locks/tag/deploy stay unchanged.

### Earlier review phase 55

**Review phase 55 fixes secondary data handles using the wrong y frame.**
FIND-039 clamped y2log100 against primary limits; a real drag saved2.605instead
of199.526. Per-rendered-secondary y metadata now reaches only its layer handle;
primary/title/legend frames remain data/axes/figure respectively. Fifteen size/
DPI/panel comparisons and actual artist transforms/JSON agree. Real browser
selected-panel inverted-log drag, unchanged other anchors and undo/redo pass.

New pure5/browser1 stay separate:209connectedpasses/1non-Windowsguard skip,
6realbrowserpasses/27deselected, floor17passes/3087deselected/289Pyparsing warnings,
10quality records and activeLSP6clean. PLOT-11 is PASS in current supported scope;
PLOT01..12 are reviewed, not universal API/native UI/preview-parity certification.
[Evidence](review_evidence/coordinate_frame_verification.json), [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS114/RUNNING5/OPEN30/DEFERRED1**. Baselineb8CI39171315500 is ALL5SUCCESS;
publish queued alpha+coordinate effects and obtain new exact whole CI.
Versions/dependencies/locks/tag/deploy stay unchanged.

### Earlier review phase 54

**Review phase 54 fixes ignored annotation alpha and checks overlay geometry.**
FIND-038 passed valid alpha through neither Text nor arrow;11initial regressions
failed before the shared branch fix. Non-default opacity now reaches both parts,
including y2; default RGBA colour opacity/native clip/z-order remain unchanged.
Twelve final regressions cover SVG/pixels/styles; alpha0changed9967channels before
and0after versus a matching no-annotation reference.

Signed/dodged/duplicate bars and asymmetric errors, native signed stack boundaries
and raw unsorted band edges match manual expectations.245related/floor12passes/
3087deselected/13Pyparsingwarnings and9quality records pass, activeLSP3clean.
PLOT-09/12 are PASS in supported scope, not a new zorder/clip/coordinate API.
[Evidence](review_evidence/overlay_alpha_verification.json), [comparison](review_evidence/annotation_alpha.png),
[tracker](REVIEW_CHECKLIST_STATUS.md): **PASS113/RUNNING5/OPEN31/DEFERRED1**.
Keep this runtime effect local duringb8CI(Rust/minsuccess,twoPytestrunning);
PLOT-11drag/browser coordinates and fresh alpha-source CI remain separate.
Versions/dependencies/locks/tag/deploy stay unchanged.

### Earlier review phase 53

**Review phase 53 checks shared scopes and log-domain outcomes.** Nine axis tables
retain column/named grouping, empty-panel/tick consistency and independent y/y2/
labels; three declaration conflicts reject. Legacy log clipping keeps raw values;
typed intervals reject invalid domains. Positive wide axes, independent linear-c
and supported heatmap LogNorm/masks agree without inventing unsupported symlog.

Selected214/floor214passes/458and2873deselected and11commands pass. Floor1843
warnings split1841Pyparsing+2Matplotlib3.8constant1e308image guard warnings.
A targeted8case run locates them; a separate pixel probe confirms expected RGB/raw
data and strict-warning output/resource preservation. Documented backend limit,
not a new silent suppression or data rewrite. PLOT-05/10 are PASS in this scope.
[Evidence](review_evidence/axis_domain_verification.json), [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS111/RUNNING5/OPEN33/DEFERRED1**. Exact3bCI39166807390 is ALL5SUCCESS
including the numerical fix runtime. Publish queued distribution/pairing/axis docs;
versions/dependencies/locks/tag/deploy stay unchanged and new docs CI is separate.

### Earlier review phase 52

**Review phase 52 traces role-aware statistical observations.** Twelve explicit
row-index expectations match required x/y/hue/weight/unit/style/size roles;
unused-column missing values are not dropped. Exact paired weighted means/n/
units and bin masses agree. Invalid required types/weights reject rather than
vanish; strict regplot rejects missing pairs, while selected valid B renders
original rows4/5/6/8. No validator/estimator/data-drop policy changes.

Boundary-selected388passes/444deselected and floor388passes/2699deselected/
489classified Pyparsing deprecations plus9quality records pass—not a new whole
suite count. STAT-08 is PASS in supported scope; STAT01..08 are now reviewed in
those documented corpora, not all statistics/adapters/UI. [Evidence](review_evidence/observation_pairs_verification.json),
[tracker](REVIEW_CHECKLIST_STATUS.md): **PASS109/RUNNING5/OPEN35/DEFERRED1**.
Keep distribution+pairing docs local during3bCI(2Rustsuccess/3Pythonrunning);
new numeric effect whole CI, versions/dependencies/locks/tag/deploy remain separate.

### Earlier review phase 51

**Review phase 51 checks manual distribution summaries and jitter determinism.**
Eight oriented box cells match hand quartiles/observed whiskers/fliers for odd/
even/single/constant samples.24violin profiles for unequal cells match independent
variance/Gaussian/normalization/quantile equations(max5.55e-16), without forcing
finite clipped area1 or merging missing samples. Fixed jitter matches seed0
positions under layer reordering; fresh PYTHONHASHSEED1/777processes retain
PNG/PDF/SVG hashes and NumPy/Python global RNG state for the same spec/environment.

Existing408related/floor407passes/2680deselected/1649warnings and9quality records
pass. All1649are Pyparsing deprecations, collected in the same floor run.
STAT-06/07 are PASS in supported scope, not every quantile convention/environment.
[Evidence](review_evidence/distribution_jitter_verification.json), [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS108/RUNNING5/OPEN36/DEFERRED1**. No new runtime/API/tests/framework.
Keep docs local during3bCI(2Rustsuccess/3Pythonrunning); numeric fix still needs
that exact whole result. Versions/dependencies/locks/tag/deploy stay.

### Earlier review phase 50

**Review phase 50 checks KDE moments, finite tails and degenerate inputs.**
Exact weighted mean5/2/variance117/22/neff18/7 match bandwidth and24Gaussian
mixture settings at2049points(maxerror2.22e-16). Clipped-tail analytic mass and
trapezoid error(max8.94e-9) are distinguished, not renormalized; singular mass4/10
stays in the common denominator. A4095point bimodal curve has two peaks near±3.

Existing285KDE1D/2D/grid cases rerun:359related/floor285passes/2802deselected/
317warnings; repeat285floorcases classify all317as Pyparsing deprecations.
Nine quality records pass. STAT-05 is PASS in supported corpus without new
runtime/kernel/fallback/tests. [Evidence](review_evidence/kde_integral_verification.json),
[tracker](REVIEW_CHECKLIST_STATUS.md): **PASS106/RUNNING5/OPEN38/DEFERRED1**.
BaselineefCI39162647649 is ALL5SUCCESS; publish queued numeric+histogram+KDE
units for new effect-source CI. Versions/dependencies/locks/tag/deploy stay.

### Earlier review phase 49

**Review phase 49 reuses histogram coverage and checks independent mass.**
Existing186cases cover weighted/unequal boundaries, raw widths, geometry, CDF,
legacy/native comparison and exports/RNG. An80-digit Decimal reference checks
38rows/19supported configurations: in-range mass15(A9/B6), outside198excluded,
common-density areas.6/.4 and separate1/1. Density is area, not a height sum;
dodge uses original statistical bin widths and unsupported frequency CDF stays rejected.

Related269/floor186passes/2901deselected/257warnings and9quality records pass.
A second186case floor pass classifies all257as Pyparsing deprecations, not product
numeric warnings. No normalization/runtime/newtest change. STAT-04 is PASS in
scope. [Evidence](review_evidence/histogram_normalization_verification.json),
[tracker](REVIEW_CHECKLIST_STATUS.md): **PASS105/RUNNING5/OPEN39/DEFERRED1**.
BaselineefCI has4success/3.10Pytestrunning; retain queued numeric/docs units locally.
Versions/dependencies/locks/tag/deploy stay unchanged.

### Earlier review phase 48

**Review phase 48 fixes degenerate polynomial confidence computation.** FIND-037
reproduces legacy raw-response covariance underflow(collapse) at1e-250 and
nonfinite/empty bands at1e250; a rank3/11 clustered design warned then returned
~4.67e10 predictions for ymax121. Before tests fail4/19. Shared predictor/response
normalization and scoped rank/arithmetic/nonfinite errors now preserve mean-fit
normal approximation, original units and output-file cleanup, without new fields.

Independent closed-form OLS and all200band/path points agree for three response
scales/legacy+typed; large predictor helper values and explicit invalid-input
boundaries pass. This is not universal huge-axis Matplotlib layout support.
Related201/floor19passes/3068deselected/13warnings and8quality/package records pass.
STAT-03 is PASS in this corpus. [Evidence](review_evidence/regression_degenerate_verification.json),
[tracker](REVIEW_CHECKLIST_STATUS.md): **PASS104/RUNNING5/OPEN40/DEFERRED1**.
Keep this effect unit local duringefCI(2Rustsuccess/3Pythonrunning);
versions/dependencies/locks/tag/deploy stay unchanged.

### Earlier review phase 47

**Review phase 47 checks projection coordinates and scalar guide meanings.**
Quiver polygon tips match independent data transforms under unequal axis units;
nonmonotonic3D xyz and polar radian cardinal positions retain data. Existing mesh/
transpose controls rerun. Explicit heatmap domains/masks/RGBA/colourbar relations
and legacy-c constants/missing data pass; typed null is rejected, not imputed.
Numeric semantic hue bounds keep out-of-range rows and use a mapping legend,
not a fabricated colourbar or row selection.

Related229/floor12passes/3056deselected/13warnings and8quality/package records pass.
PLOT-07/08 are PASS for currently supported combinations, not every projection/
scale option. [Evidence](review_evidence/projection_colour_verification.json),
[tracker](REVIEW_CHECKLIST_STATUS.md): **PASS103/RUNNING5/OPEN41/DEFERRED1**.
Runtime/API/schema are unchanged. Baselineb777CI has4success/last3.10sitebuild
running; keep this unit and preparation docs local until it completes.
Versions/dependencies/locks/tag/deploy stay unchanged.

### Earlier review phase 46

**Review phase 46 inventories synthetic inputs and records contract decisions.**
Five review fixtures and42shared JSON snapshots have provenance/hash/size and
input-vs-result scope. Targeted profile-path/private-key/token checks have no hits,
not a complete secret/privacy certificate; raw Temp logs/environment stay private.
Fixed/random-seed generation and actual consumers are linked separately from logs.

A conflict table explains preserved mutable snapshots/batch rules/ownership/size/
journal/HEX/pattern/PGF/tool distribution/native subset/release boundaries without
new compatibility authority. Existing313tests/2expected warnings and7quality checks
pass;19explicit paths exist. BASE-06/07 are PASS in this bounded preparation scope;
BASE-05's full150-ID symbol/test mapping remains RUNNING. [Preparation](REVIEW_PREPARATION.md),
[evidence](review_evidence/preparation_audit_verification.json), [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS101/RUNNING5/OPEN43/DEFERRED1**. Keep this docs unit local duringb777CI;
product runtime/versions/dependencies/locks/tag/deploy stay unchanged.

### Earlier review phase 45

**Review phase 45 proves generated drift is detected without corrupting the repo.**
Existing sync checker runs first; three isolated artifact copies pass, deliberate
schema/capabilities/reference drift fails with a regeneration hint, and restored
bytes pass again. Action36/fields, layer37 and generated declarations agree.
Layer kind remains a structural string in JSON Schema with separate semantic
validation, not a newly tightened enum contract.

Related231/floor4passes/3052deselected/13warnings and8quality/package records pass.
JSON-11 is PASS for sync/registry corpus, not all nullable UI meanings or BASE
mapping/privacy audits. [Evidence](review_evidence/generated_drift_verification.json)
and [tracker](REVIEW_CHECKLIST_STATUS.md): **PASS99/RUNNING7/OPEN43/DEFERRED1**.
Runtime/artifact contents are unchanged; keep test/docs local during161CI.
Versions/dependencies/locks/tag/deploy stay unchanged.

### Earlier review phase 44

**Review phase 44 verifies controlled output failures and Figure ownership.**
Actual Windows read-only/deny-delete targets fail without replacing prior JSON/
PNG/PDF/SVG bytes; synthetic ENOSPC/unsupported-extension controls preserve cleanup.
Successful render/save Figures stay open until caller close; weakrefs clear after
GC.80owned render/save/close effects keep live/open Figures and staging0, with
handles215→216/RSS85.5→90.8MB. This bounded series is not native/long-session
leak-freedom proof; PERF-04 remains separate.

Related128passes/6OSskips/8expected MPL warnings and floor17passes/3035deselected/
13warnings plus8quality records pass. OUT-04/05 are PASS in corpus, not every OS/
ACL permission certification. [Evidence](review_evidence/output_lifecycle_verification.json)
and [tracker](REVIEW_CHECKLIST_STATUS.md): **PASS98/RUNNING8/OPEN43/DEFERRED1**.
Runtime is unchanged; keep this unit local during161CI. Versions/locks/releases stay.

### Earlier review phase 43

**Review phase 43 separates finite patterns, luminance and real-size review.**
Artist/legend mapping across two panels agrees for7fill/9line-point groups and
shows hatch6/marker8/style4 cycles (paired line period8). Equal LCH and independent
linear-Y greyscale proxy are not category-separation guarantees. Fixed one-column
colour/grey plates expose thin/small-mark and alpha-band limits;6bands blend, so
fewer categories/boundaries/direct labels/panels are recommended, not certified.

Bilingual/generated/docstring/gallery claims now state finite cycles and measured
scope. Gallery uses paper5 and correctly describes3CVDrows plus normal/grey, not
all-row certification.77related/site9/floor8passes/3027deselected/13warnings and
9quality records pass. COLOR-06/07/09/10 are PASS for this corpus/review.
[Evidence](review_evidence/encoding_print_verification.json), [comparison](review_evidence/one_column_encoding.png),
[tracker](REVIEW_CHECKLIST_STATUS.md): **PASS96/RUNNING10/OPEN43/DEFERRED1**.
Baseline16aCI39148609011 is ALL5SUCCESS before queued report/gallery changes;
publish both units and obtain current CI. Versions/dependencies/locks/tag/deploy stay.

### Earlier review phase 42

**Review phase 42 corrects final-palette report metrics and states conditions.**
FIND-036 exposed nominal LCH gap3 reported safe while final HEX paper7/vivid7 gaps
are2.79209/2.79726. Float lightness now uses mapped RGB; report uses exported8-bit
HEX and adds explicit normal/CVD type/model/fullseverity1/representation/threshold
conditions. Existing keys, thresholds and generated colours/algorithm are unchanged.

Authors' Machado Table1 matrices, N-1/N/N+1 metrics/pairs and deterministic tie/
fresh-process checks pass. This is measured scope, not broader certification;
soft6 may measure pass beyond preverifiedN5. Related141/floor18passes/3009deselected/
13warnings and8quality records pass. COLOR-03/04/05/08 are PASS; remaining colour
pattern/readability/wording gates stay open. [Evidence](review_evidence/palette_report_verification.json)
and [tracker](REVIEW_CHECKLIST_STATUS.md): **PASS92/RUNNING10/OPEN47/DEFERRED1**.
Keep this effect unit local during16aCI; versions/dependencies/locks/tag/deploy stay.

### Earlier review phase 41

**Review phase 41 verifies style ownership and fixes DPI-dependent pixel padding.**
Alternating themes/journal retain all caller rcParams and match fresh-process
PNG/PDF/SVG under equivalent ambient settings; failure cleanup restores rc as well.
LAY-08 is PASS in this owned scope. FIND-035 replaces fixed pixel margins with
0.02inch padding, retaining former6px at300DPI. Dense150/300position error drops
0.02689→0.01041inch; source widths/state do not change.

Editor600DPI source/capped2000x1000preview differs from final geometry by<=.00334inch
and retains1.5pt lines/final720x360pt SVG. However75DPI dense layout still differs
.14594inch: LAY-09 is RUNNING, not universal WYSIWYG certification. Related88/floor6
passes/3003deselected/13warnings and8quality records pass. [Evidence](review_evidence/style_dpi_verification.json)
and [tracker](REVIEW_CHECKLIST_STATUS.md): **PASS88/RUNNING10/OPEN51/DEFERRED1**.
Baseline5caCI39142799672 is ALL5SUCCESS before queued guide/pad effects; publish
both units and inspect fresh CI. Versions/dependencies/locks/tag/deploy stay.

### Earlier review phase 40

**Review phase 40 fixes measured secondary-axis and repeated-guide collisions.**
FIND-034 reproduced y2-label/outside-legend overlap in a two-panel/two-colorbar/
shared-axis figure and repeated explicit-series labels. Physical measured spacing
replaces the fixed1.35axes multiplier; matching explicit ungrouped point/line
source/axis/reference identity shares one guide, not raw grouped/other identities.
Manual anchors, data/style/source and physical canvas remain unchanged.

Supported8x3.5/6x3bbox and actual PNG/PDF/SVG draw-event checks avoid data/label
coverage; the4.5x2.8secondary limit still warns.14newcases/185related passes and
floor14passes/2989deselected/13warnings plus8quality/package records pass. LAY-05
is PASS in measured scope. [Evidence](review_evidence/mixed_guide_verification.json),
[baseline](review_evidence/mixed_guides_baseline.png), [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS87/RUNNING9/OPEN53/DEFERRED1**. Keep this effect unit local during current5caCI;
versions/dependencies/locks/tag/deploy stay unchanged.

### Earlier review phase 39

**Review phase 39 records real system-font/glyph and CJK layout diagnostics.**
Missing-family fallback and DejaVu Hangul warnings are observable without changing
source fonts/text. Installed Malgun Gothic covers Hangul but lacks U+2212; selected
Noto Sans KR covers this corpus but logs weight fallback to100. File hashes,
glyph indices and measured bboxes identify the actual Windows environment, not
all-font or cross-system guarantees. No font binary/download/minus rewrite is added.

Two installed-family observations and narrow CJK/long-group outside-legend bounds
complement English/multiline/unbroken support/warning fixtures. LAY-04/07 are PASS
within this corpus; system-font tests skip explicitly if those families are absent.
Related97passes/14expected glyph/layout warnings, floor5passes/2984deselected/
26warnings and8quality/package records pass without product runtime change.
[Evidence](review_evidence/font_boundary_verification.json) and [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS86/RUNNING9/OPEN54/DEFERRED1**. Baseline66feCI39139498998 is ALL5SUCCESS before
queued layout diagnostics; publish both units and inspect fresh CI, not retroactive
proof. Versions/dependencies/locks/tag/deploy stay unchanged.

### Earlier review phase 38

**Review phase 38 diagnoses automatic text that cannot fit a fixed canvas.**
FIND-033 reproduced silent unbroken-title/suptitle clipping and an oversized
outside-legend negative-rect solver path. Valid rects alone reach the solver;
final automatic text bounds/overlap now warn generically with actionable choices.
Manual positions, source text/font size and physical canvas are not rewritten.
CLI diagnostics and warning-as-error rollback/lifecycle are verified.

Related145passes/8expected impossible-fixture MPL warnings and floor9passes/
2975deselected/21warnings pass with8quality/package records. LAY-06 is PASS for
this detection policy; LAY-04 is RUNNING for CJK/fonts/other combinations.
[Evidence](review_evidence/layout_boundary_verification.json) and [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS84/RUNNING10/OPEN55/DEFERRED1**. The805run ended with the known type failure
and successful floor/native jobs; hotfix5918/preset66fe are already published.
Current CI39139498998 predates this effect change. Keep this unit local during it;
versions/dependencies/locks/tag/deploy stay unchanged.

### Earlier review phase 37

**Review phase 37 checks every current TeX preset through real output boxes.**
Five presets×one/two columns×.75/1fractions match vector/mock preview, spec/render
and PNG/PDF/SVG dimensions in20recorded rows. TeX72.27pt/in and vector72pt/in are
not conflated; raster rounding stays within one pixel at100DPI. Original plot state
is not changed by preview. Registry values are documented assumptions, not fresh
publisher-guide certification.

Four journal priority controls retain last-size-action behavior and existing rc
style priority. Clearing journal style reveals explicit font fields without size
change. The old generic API doc overstated font-last-setter behavior; docs now
match the established implementation instead of adding flags/changing calibration.
Related58passes/floor24passes/2951deselected/13warnings and8quality/package records
pass, including both global platform type targets. LAY-03 is PASS in scope.
[Evidence](review_evidence/preset_geometry_verification.json) and [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS83/RUNNING9/OPEN57/DEFERRED1**. Keep this test/docs unit and the platform hotfix
local while prior floor runs; runtime behavior/versions/dependencies/locks/releases stay.

### Earlier review phase 36

**Review phase 36 fixes the cached Windows observer's platform type boundary.**
Baseline805CI39136943043 failed Python3.10Pyright with2unavailable ctypes.WinDLL
attributes; the full matrix sibling cancelled. The extracted factory lacked its
own Windows guard, hidden by local Windows checking. An explicit non-Windows
OSError before WinDLL restores the boundary without casts/ignores or changing
fresh PID sampling/CloseHandle/Linux reading.

Both global Linux/Windows Pyright targets now pass; sampler/history4passes/1local
OSskip and7quality/package records pass. The new non-Windows runtime regression
still needs Linux execution in the next CI; this is not a retroactive green result.
[Evidence](review_evidence/platform_guard_verification.json) and [tracker](REVIEW_CHECKLIST_STATUS.md)
retain **PASS82/RUNNING9/OPEN58/DEFERRED1**. Layout work was postponed for this
actual failure. Keep the tooling hotfix local until the remaining prior jobs settle;
product runtime/versions/dependencies/locks/tag/deploy stay unchanged.

### Earlier review phase 35

**Review phase 35 separates literal HTML/SVG from explicit trusted PGF TeX.**
Special characters/Unicode/inert script text recover once-decoded values without
script/event nodes; actual Python/Rust raw pages preserve attributes/state in4cases.
PGF raw ampersands fail clearly; escaped literals, harmless explicit TeX and math
compile with fitted paper/T1 encoding and retain the expected extracted text.
Reference keys/hrefs still reject TeX macro breakouts. No runtime sanitizer or
cross-format mutation is introduced; backend text-policy comments are clarified.

Connected72passes/no skips, floor6passes/2945deselected/185warnings and7quality/
package checks pass. All185warnings in this observed subset are recorded upstream
PyparsingDeprecationWarning, not globally suppressed or extrapolated to older runs.
OUT-09 is PASS in scope. [Evidence](review_evidence/string_boundary_verification.json)
and [tracker](REVIEW_CHECKLIST_STATUS.md): **PASS82/RUNNING9/OPEN58/DEFERRED1**.
Baseline06dCI39131994074 is ALL5SUCCESS; publish queued tooling/tests with their
separate local checks and inspect a new run. Versions/deps/locks/tag/deploy stay.

### Earlier review phase 34

**Review phase 34 verifies real reference exports and document results.**
Reference-bearing PNG/PDF/SVG repeat across time/fresh processes with equal hashes,
without dropping DOI links/labels; volatile dates are absent and SVG IDs are stable.
PGF+relative sidecars relocate/compile together; missing sidecars fail. Forced PGF
postprocessing failure closes the Figure but can overwrite the old PGF/leave images,
so the existing multi-file non-transactional limit is explicit, not silently fixed.
OUT-02/06/07 are PASS for these policies.

All70connected cases pass without skips, including actual tectonic, pdflatex+
bibtex, lualatex+bibtex and lualatex+biblatex. Reference numbers/text pass; installed
Poppler reports5embedded fonts and the DOI annotation in each compiled PDF. OUT-08
is PASS for this installed matrix, not every font/OS. Floor6passes/2939deselected/
13warnings and6quality/package records pass. [Evidence](review_evidence/output_reference_verification.json)
and [tracker](REVIEW_CHECKLIST_STATUS.md): **PASS81/RUNNING9/OPEN59/DEFERRED1**.
Runtime is unchanged; keep this test/docs unit local during06dCI. Versions/locks/
releases and separate string/permission/resource gaps remain unchanged.

### Earlier review phase 33

**Review phase 33 separates bounded session retention from observer artifacts.**
A137second/500row Python editor run exercised60edit/undo/redo/open cycles and10
failed effects, with15resource checkpoints. GC reclaimed owned Figures, handles
stayed198 and temp files0; history growth30and replacement1were intentional.
RSS87.9→96.4MB/lifetime peak246.6MB is not universal absence-of-native-leak proof.

FIND-031 is tooling: the Windows sampler created20ctypes Counter types/662objects
without rendering. Lazy binding/type reuse fixes that observer growth while each
PID value/handle is still fresh/closed; warm control adds0types/2objects. A new
regression and63related passes/2OSskips plus6quality/package records pass. The
corrected whole session was rerun; product renderer/state are unchanged.
PERF-04 remains RUNNING for longer horizons/other native workloads. [Evidence](review_evidence/session_resource_verification.json)
and [tracker](REVIEW_CHECKLIST_STATUS.md): **PASS77/RUNNING9/OPEN63/DEFERRED1**.
Keep this local tooling/docs unit during06dCI; versions/dependencies/locks/releases stay.

### Earlier review phase 32

**Review phase 32 serializes owned Matplotlib effects.**
FIND-030 reproduced concurrent PNG/SVG saves differing from their serial bytes.
A stdlib-only shared reentrant lock now covers render/save, TeX preview, Python
editor owned effects and site/gallery generation without eager optional imports.
This is isolation, not parallel throughput or arbitrary caller Figure/pyplot/Store
thread safety. Returned Figures remain caller-owned; independent spawned processes
are preferable for parallel drawing, not fork-during-threaded-render assumptions.

Six controlled/nested/three-format/two-session cases,231connected passes,9site
passes and floor6passes/2937deselected/13warnings pass in8recorded quality checks.
LSP8paths confirm clean; exact PNG/PDF/SVG serial/concurrent hashes agree. PERF-06
is PASS for this supported owned-call corpus. [Evidence](review_evidence/concurrent_render_verification.json)
and [tracker](REVIEW_CHECKLIST_STATUS.md): **PASS77/RUNNING8/OPEN64/DEFERRED1**.
Current31eCI still runs before this effect change; keep the local unit, preserve
state/core dependencies/versions/locks/releases, and obtain later current-source CI.

### Earlier review phase 31

**Review phase 31 records a bounded rows×history core matrix.**
Run `uv run --no-sync python scripts/profile_history_costs.py`:3row sizes×3history
targets use independent core workers with12second child/2.5second dispatch and
512MiB RSS observation budgets, not an OS resource sandbox. Six targets completed;
three stopped at375/39/38actions before larger targets and retain null undo/redo.
No actual timeout/OOM occurred;3stub regressions preserve partial/error checkpoints.
1k×1000undo/redo402.35/404.45ms and100k×10at362.61/392.95ms are observations, not SLOs.
Peak observed worker working set53,571,584bytes includes baseline, not renderer RSS.

PERF-02 is PASS for this bounded corpus. No alias/replay/checkpoint rewrite or
unmeasured-cell extrapolation is added; existing label None/empty handling also
needed no rewrite. Related62passes/2OSskips and6quality/package checks pass.
[Evidence](review_evidence/history_cost_verification.json) and [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS76/RUNNING8/OPEN65/DEFERRED1**. Keep the local script/test/docs unit while31eCI
runs; core runtime/versions/dependencies/locks/tag/deploy stay unchanged.

### Earlier review phase 30

**Review phase 30 keeps explicit empty render tokens distinct from auto/null.**
FIND-029 reproduced6artist mismatches while schema/codecs kept the empty string.
Shared renderer fallback now uses None, retaining supported no-marker/no-line
values, numeric0 and existing automatic/default and layer-specific restrictions.
The20representative renderable cases agree across schema/Python, CLI migration,
5fresh CLI renders, typed Rust→Python and40rawJSON editor/HTMX state+PNG checks.
This is not all139nullable fields/automatic values or every visual control; JSON-09
stays RUNNING. Compact fixtures preserve meaning without duplicating full specs.

Related266passes/2known singleton interval warnings, floor79passes/2858deselected/
15warnings, native22passes/6helpers ignored and10quality/codec/package records pass.
[Evidence](review_evidence/render_token_verification.json) and [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS75/RUNNING8/OPEN66/DEFERRED1**. Baselineea1CI39125371498 is ALL5SUCCESS before
this renderer change, not its verification. Publish this with queued performance
evidence and inspect a fresh run. Versions/dependencies/locks/tag/deploy stay.

### Earlier review phase 29

**Review phase 29 separates measured state/JSON/render costs.**
Run `uv run --no-sync python scripts/profile_state_costs.py` for the bounded warm
synthetic1k/10k/100k-row workload. Title dispatch medians are0.803/6.993/67.867ms;
100k JSON encode/decode174.954/182.815ms and full PNG save533.225ms. Median/p95,
repeat counts and environment/source hashes accompany the data. A separate profile
attributes99.923%of measured dispatch profile time to deepcopy, with no render/
validation calls; Python-only allocation peak4,828,472bytes is not native RSS.
PERF-01/03 are PASS for these bounded observations, not a new latency threshold.
Snapshot safety stays; no speculative zero-copy or long-history rewrite is added.

Exactea1Linux/Windows logs now pass foreground descendant/MSRV controls (20/21tests,
5/6helpers ignored), including Windows cleanup-tool failure recovery. RUST-04 is
PASS only for that supported foreground policy. [Performance](review_evidence/performance_verification.json)
and [cleanup evidence](review_evidence/remote_cleanup_verification.json) retain limits.
Related59passes/2OSskips and6quality/package checks pass. [Tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS75/RUNNING8/OPEN66/DEFERRED1**. Full current CI still runs; save this script/docs
unit locally without cancelling it. Core runtime/versions/locks/releases remain unchanged.

### Earlier review phase 28

**Review phase 28 fixes owned foreground descendant timeout cleanup.**
FIND-028 reproduced a grandchild surviving direct-child timeout. Shared transport
now targets only the held Windows tree or a fresh Unix process group; no shell or
interpreter fallback is introduced. The cleanup utility has a separate2second
budget, direct-child kill/reap is attempted, and failure remains diagnostic.
Detached/reparented workers remain outside this foreground policy.

Current Windows lib20+main1passes/6ignored helpers, controlled cleanup-tool failure/
recovery and a normal focused native bridge pass;9format/lint/type/contract/package
records pass. Unix/current MSRV remain unexecuted locally, so RUST-04 stays RUNNING.
Baselinee728CI39122032427 is now ALL5SUCCESS before this change, not its validation.
Publish the queued local units and inspect a new run. [Evidence](review_evidence/descendant_cleanup_verification.json)
and [tracker](REVIEW_CHECKLIST_STATUS.md): **PASS72/RUNNING9/OPEN68/DEFERRED1**.
Library timeout/body limits, versions/dependencies/locks/tag/deploy stay unchanged.

### Earlier review phase 27

**Review phase 27 records the completed e728 Linux floor and both native jobs.**
Job117659400040 passed the entire ordered60-file floor:2872passes/26skips/
3906warnings in943.69s. Skips are25optional adapters and1biber, not staging symlink
cases. Exact source plus whole-suite success/complete skip summary supports all
4symlink cases; this is not an individual verbose-case log claim. Warning details
are suppressed by the existing runner flag, so they are not all classified benign.

Both completed Linux/Windows native logs show18lib+1main passes/3helpers ignored
and the fixed HTTP path/header corpus. These complement prior Windows ownership/
path probes, so SEC-06 is PASS for the measured supported policies and limits.
The regular Python jobs still run; CI-01 remains RUNNING and no new privacy-only
test is retroactively included. [Evidence](review_evidence/remote_floor_verification.json)
and [tracker](REVIEW_CHECKLIST_STATUS.md): **PASS72/RUNNING9/OPEN68/DEFERRED1**.
Keep this evidence-only unit local during CI; runtime/versions/locks/releases stay.

### Earlier review phase 26

**Review phase 26 checks default error logging and current advisory snapshots.**
Synthetic validation/import/render/unknown-route probes on Python/Rust editors
leave no submitted token/research-row/traceback markers in default stdout/stderr,
while preserving state/PNG. Same-client error/draft/current-state responses remain
intentional editing output, not cross-user confidentiality or credential storage.
One permanent Python regression and211related passes/floor1pass/2898deselected/
13warnings plus7style/type/contract/package checks pass without runtime changes.

Three committed Python-lock audits return no known vulnerabilities; official OSV
querybatch returns no advisory for69Cargo registry crate/version pairs. This is
not cargo-audit/all-RustSec category execution, a timeless guarantee or coverage
of future dependency resolution. SEC-08 is PASS for the measured scope. [Evidence](review_evidence/privacy_audit_verification.json)
and [tracker](REVIEW_CHECKLIST_STATUS.md): **PASS71/RUNNING10/OPEN68/DEFERRED1**.
Thee728five-job CI is still active; save this test/docs unit locally without
cancelling it. Versions/dependencies/locks/tag/deploy remain unchanged.

### Earlier review phase 25

**Review phase 25 separates full and floor CI execution budgets.**
FIND-027 addresses the observed combined-job exhaustion after successful full
Pytest: the complete ordered60-file floor contract now has an independent Linux/
Python3.10job. Full3.10/3.12 remain; all3Python jobs have finite60minute budgets,
Rust jobs retain20minutes. The floor PEP723 dependencies/lock/not-browser filter
are unchanged and pinned TeX install commands/checksum match byte-for-byte.
Locked Playwright system/font dependencies remain without a floor browser download;
the full matrix retains browser coverage. Both suites now report25slowest timings.

New CI separation/runner guards pass, including complete argv and return-code
propagation. Local CI/release7passes, real critical floor39passes/4symlink skips/
2855deselected/13warnings, Ruff222/types/contracts/packaging and3pathLSP checks pass.
The full new5job remote run is still required; CI-01 remains RUNNING. [Evidence](review_evidence/ci_floor_split_verification.json)
and [tracker](REVIEW_CHECKLIST_STATUS.md): **PASS70/RUNNING10/OPEN69/DEFERRED1**.
Publish this with the queued ownership fix/docs; library/runtime/request limits,
versions/dependencies/locks/tag/deploy stay unchanged. No v1 completion is claimed.

### Earlier review phase 24

**Review phase 24 fixes staging ownership and verifies offline input sinks.**
FIND-026 reproduced JSON collision cleanup deleting another entry and PNG/PDF/SVG
overwriting it. Shared staging now reserves an exclusive entry before its cleanup
scope; text writing uses only that reservation. File/directory/hardlink controls
pass;4symlink cases are privilege-skipped on Windows, so SEC-06 stays RUNNING.
Fixed Python/native HTTP route/query tests retain state and do not expose file paths.

Plain JSON/reference metadata survives without object restoration; network/shell/
pickle sink guards show zero attempts for normal PNG/PDF/SVG after backend warmup.
Unsafe link/citation input is rejected. SEC-07 is PASS for these supported paths;
explicit TeX/PGF and caller-chosen export directories retain separate trust limits.
Related128passes/6OSskips, floor80passes/4skips/2814deselected/13warnings, native
focused HTTP and7style/type/contract/package records pass. [Evidence](review_evidence/file_sink_verification.json)
and [tracker](REVIEW_CHECKLIST_STATUS.md): **PASS70/RUNNING10/OPEN69/DEFERRED1**.

Baseline621CI cancelled after1hour in3.10: full Pytest already passed in36minutes,
then minimum step exhausted its remaining23minutes; annotation117639290243 confirms
budget exhaustion. Other3jobs passed. Next examine a separate finite-budget floor
job without dropping coverage; this source unit does not change CI yet. Save the
fix locally before that follow-up. Versions/deps/locks/tag/deploy stay unchanged.

### Earlier review phase 23

**Review phase 23 isolates the Windows venv/TMP startup boundary.**
Twelve six-second controls separate print/capabilities, pipe/file capture, base/
venv, site and TMP/TEMP. The observed venv fails before its print program with
321-character TMP, even with-S; base Python and longTEMP/shortTMP controls work.
These are measured interpreter/host outcomes, not a universal uv/CPython threshold
or a proven Rust capture defect. Five timed fixtures were stopped, not counted as
application successes. No runtime code, OS setting or automatic fallback changed.

The same selected interpreter then passes native startup/open/action/PNG, Unicode
metadata and336-character source preservation with shortTMP/longTEMP. Together
with earlier PowerShell path/lock tests, PKG-06 is PASS for the observed supported
configuration and explicit limits; RUST-04 general descendant cleanup stays open.
Related47checks and style/types/contracts/packaging pass in6recorded commands.
[Evidence](review_evidence/windows_tmp_boundary_verification.json) and [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS69/RUNNING9/OPEN71/DEFERRED1**. Hold docs publication while621CI runs;
versions/dependencies/locks/tag/deploy and broader completion limits stay unchanged.

### Earlier review phase 22

**Review phase 22 separates locked dev, fresh ranges and isolated builds.**
A disposable locked-dev install has43packages matching the lock and repeating
sync retains its version snapshot. Prior fresh range installs show16version
changes, not a claim that every user must match the dev lock. A separate fresh
PEP517 cache installed Hatchling1.32.0 plus its own transitive build dependencies;
sdist→isolated wheel and active-env builds agree on55members and observed bytes.
An independent no-dependency wheel consumer runs core outside the checkout.
PKG-09 is PASS for this scope, not universal byte reproducibility.

Both documented source-tree editor commands start from the matching621source/
artifact snapshot; HTML/spec/PNG/htmx/0BSD assets pass and owned processes stop.
The wheel deliberately lacks dashboard/Rust sources. PKG-08 is PASS. FIND-025
corrects stale 'Linux CI not observed' README text by citing the actuale14run.
No runtime code changed. Related12passes and style/types/contracts/final packaging
pass; private build/consumer/editor receipts retain exact scope. [Evidence](review_evidence/isolation_source_editor_verification.json)
and [tracker](REVIEW_CHECKLIST_STATUS.md): **PASS68/RUNNING10/OPEN71/DEFERRED1**.
Keep the docs unit local while621CI is active; versions/deps/locks/tag/deploy stay.

### Earlier review phase 21

**Review phase 21 verifies installed extras and outside-checkout CLI behaviour.**
FIND-024 reproduced9missing-install-hint surfaces. Expected NumPy/Matplotlib/
cycler absence now explains the colour/render extra without masking unrelated
transitive/compiled errors or making Matplotlib mandatory for colour operations.
The fresh installed-wheel environment progresses through7extras states;98console/
module CLI calls agree outside the checkout. Package-only browser installation is
separate from its controlled missing Chromium binary. PKG-02/04 are PASS.

Current82related and floor11cases pass, with2833deselected/13warnings on the floor;
Ruff221/types/contracts/packaging and installed/source/wheel hashes agree. The first
4point robust fixture correctly failed convergence; QA used the existing40point
regression fixture without loosening the product fit limit. Windows PowerShell7.6.7
short-cwd93/336character paths/locks/recovery pass, but long-cwd launcher startup
failed and a native long-TEMP readiness probe was incomplete; PKG-06 stays RUNNING.

Baselinee14CI39111782233 succeeded in all4jobs, including Python3.10/3.12 and
Rust Linux/Windows. It predates these optional-error guards, not current all-green
proof. CI-01 remains RUNNING pending the next integrated run. [Evidence](review_evidence/installed_matrix_verification.json)
and [tracker](REVIEW_CHECKLIST_STATUS.md): **PASS66/RUNNING10/OPEN73/DEFERRED1**.
Versions/dependencies/locks/tag/deploy and broader completion limits remain unchanged.

### Earlier review phase 20

**Review phase 20 preserves marker zero and verifies bounded JSON recovery.**
FIND-022 reproduced9artist failures: truthy fallbacks discarded explicit marker0,
while3Dlines ignored positive/zero sizes. Seven None checks plus forwarding3Dline
marker size retain omitted/null defaults.27artist cases and139nullable schema/
Python field cases pass; all-field CLI/Rust meanings remain pending in JSON-09.

API/CLI corrupt UTF-8/truncation/depth3000 preserve output/recover; nativeHTTP
rejects26/30/6042byte damaged inputs with unchanged spec/PNG and accepts188936byte
20k-row data losslessly. JSON-12 is PASS for this bounded corpus. Checks:249field/
marker+169connected passes, floor174passes/2659deselected/13warnings,18native
boundary cases and2CI guards. Ruff220/types/contracts/packaging pass. An aggregate
240s interrupted attempt was preserved, not credited; standalone continuation passed.

FIND-023 is confirmed CI budget starvation, not a Python test failure: baseline063
run39108112974 completed cancelled; annotation117618247815 says it exceeded45m.
Both Rust and3.12 passed. Keep full tests, use finite60minutes and--durations=25;
remote success under the new budget is not yet observed. Publishing the queued
local core unit can now resume. Versions/dependencies/locks/tag/deploy remain.
[Evidence](review_evidence/json_semantics_verification.json) and [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS64/RUNNING10/OPEN75/DEFERRED1**. This is not v1 or release completion.

### Earlier review phase 19

**Review phase 19 fixes plain-integer layer indices and verifies pure core boundaries.**
FIND-021 reproduced bool selecting real layer0/1 and other noninteger index failures
across RemoveLayer/SetColorbar/SetLayerAt. Three shared reducer guards now reject
unsupported indices while keeping valid panel auto-extension and commit semantics.

Thirty-five new cases cover references, recovery and validation/render agreement.
Fresh processes vary CWD/clock/hash+RNG seeds and interleaved styles with the same
normalized state hash. Core calls block data-file/write/network/subprocess effects
and optional imports; readonly Python source imports remain allowed, not sandboxed.
STATE-07/08/09 are PASS. Related **195 passed**, floor **35 passed/2628 deselected/
13warnings**; Ruff220/format/Pyright/contracts/packaging passed in7commands.
[Evidence](review_evidence/core_boundary_verification.json) retains source/log hashes.

[Tracker](REVIEW_CHECKLIST_STATUS.md): **PASS63/RUNNING11/OPEN75/DEFERRED1**.
Current work is committed locally; publishing waits for baseline063 CI completion
because the configured cancel-in-progress would otherwise cancel its active run.
No later full/browser/native/OS approval is implied. Versions/locks/tag/deploy remain.

### Earlier review phase 18

**Review phase 18 rejects empty artifacts and exercises actual bridge failures.**
FIND-020 reproduced an exit0 child committing an empty PNG. Shared render transport
now rejects empty artifacts before state/cache commit and before PDF/SVG export.
It does not attempt complete binary decoding or add a CPU/disk resource guarantee.

A private hook in an isolated Unicode-path venv exercises14output boundaries:
empty/badJSON/nonzero capabilities, successful JSON with1MiBstderr,8action faults
including real missing optional regression support, and empty PDF/SVG outputs.
Spec/PNG/redo hashes and recovery agree. RUST-03 is PASS. A100ms controlled stub
also times out then recovers, but RUST-04 descendant ownership remains RUNNING.

Recorded native **19passed/3helpers ignored**, Clippy/fault checker/Ruff219/format/
Pyright/contracts/packaging pass in8commands. The snapshot JSON exception diagnostic
was marked false-positive because malformed verification snapshots must fail.
[Evidence](review_evidence/bridge_fault_verification.json) and [tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS60/RUNNING11/OPEN78/DEFERRED1**. Baselinefe4449d CI39104961495 finished
cancelled: both Rust and3.12 passed,3.10 cancelled. This is not later-change proof.
Versions/dependencies/locks/tag/deploy stay unchanged; v1 is still unfinished.

### Earlier review phase 17

**Review phase 17 bounds bridge failure errors and verifies preview/cache contracts.**
FIND-019 reproduced a1MiB stderr response becoming a giant UI error. Failed stderr
now captures64KiB raw plus a truncation marker; successful stdout stays complete
and separate. UTF-8 replacement can expand text; disk/CPU/confidentiality/descendant
containment are not implied. RUST-03/04 remain RUNNING for unfinished fault paths.

Six real native HTTP preview cases cover both orientations at499/500/501DPI,
retaining JSON size/DPI and PDF/SVG physical sizes while capping PNG at2000px.
Apply/open/undo/redo/reset bridge failures preserve every session/cache field.
RUST-05/06 are PASS. Native18tests passed with2helpers ignored; Clippy, focused
preview, Ruff219/format/Pyright/clean packaging passed in7recorded commands.
A full smoke foreground240s timeout is not credited as success.

[Evidence](review_evidence/bridge_preview_verification.json) preserves scope.
[Tracker](REVIEW_CHECKLIST_STATUS.md): **PASS59/RUNNING12/OPEN78/DEFERRED1**.
Versions/dependencies/locks/tag/deploy remain unchanged; broader P1/P2 and v1
completion remain unfinished. No current full/browser/OS rerun is inferred.

### Earlier review phase 16

**Review phase 16 fixes mixed raw-group identity and verifies data/JSON policies.**
FIND-018 had string/numeric IDs merged by NumPy dtype inference, with null changing
membership. Object-valued masks now match original Python equality; numeric
1/1.0/True still merge by the legacy default, while ordered typed semantics remain.
Duplicate display captions still require caller normalization, not hidden data coercion.

Empty/singleton/row-order, known-version unknown fields, additive capabilities and
canonical-key/Unicode policies pass. Optional marker states and bounded Python
corrupt/deep/large JSON recovery are partial evidence, so JSON-09/12 stay RUNNING.
Recorded checks: **291 related passes**, minimum **61 passed/2567 deselected/
201warnings**, native **16 passed/1 helper ignored**; Ruff219/format/Pyright/
contracts/packaging pass in8commands. LSP confirmed4of6paths;2were inconclusive.
[Evidence](review_evidence/data_json_policy_verification.json) records exact scope.

[Tracker](REVIEW_CHECKLIST_STATUS.md): **PASS57/RUNNING10/OPEN82/DEFERRED1**.
Earlier full-suite/P0 evidence does not validate this later renderer change.
Versions/dependencies/locks/tag/deploy stay unchanged; v1 completion is not claimed.

### Earlier review phase 15

**Review phase 15 consolidates the supported-scope P0 evidence.** New independent
references cover all34Sharma pairs, adopted D65/IEC values, OLS mean-fit confidence
intervals, categorical/y2 ownership and asymmetric matrix coordinates. Fresh-process,
time-spaced PNG/PDF/SVG hashes and physical sizes agree; explicit tight preserves
its separate meaning. No production numeric defaults or calibration changed.

The full optional run recorded **3423 passed/2 OS skips/1 warning** before a
QA-only contour API adaptation and minimum-environment banner. The corrected72P0
cases separately pass on both current and floor stacks. Minimum coverage is
**2573 passed/25 optional skips** across8file-disjoint batches covering all53script
files, not a single ordered run. A real no-dependency wheel install outside the
repository passed core/schema/validate/JSON and console/module CLI checks.

[Evidence](review_evidence/completion_p0_verification.json) preserves toolchain,
font/lock/artifact/log hashes and incomplete attempts. The initial interrupted
minimum run and a timed-out native-browser attempt are not credited. Audit/style/
types/schema/native units/clean packaging passed. Baseline92238f3 CI39057547031
succeeded in all four jobs, but is not retroactive proof of later QA changes.

[Tracker](REVIEW_CHECKLIST_STATUS.md): **PASS52/RUNNING8/OPEN89/DEFERRED1**.
CI-01 stays RUNNING pending a new integrated run; CI-07 exact release/tag/publish
approval is explicitly deferred. Versions/core dependencies/locks/tags/deploy
remain unchanged. Remaining P1/P2 and vague broader-parity roadmap items are not
silently completed. This checkpoint is not a declaration that v1 is finished.

### Earlier review phase 14

**Review phase 14 verifies document/no-op/long-history policies.** Python opens/
resets fresh history; Rust snapshots are undoable and reset to startup default.
Downloads export the current state, not a bound imported filename; no new dirty-
bit/save-target feature was added. Equal-value actions remain events and clear
redo. Two seeds with768actions and128undo/128redo checkpoints replay exactly.
HIST-04/05/06 are PASS for these observed policies.

FIND-017 caught a real Rust browser pageerror when overlapping control requests
swapped the same detached app target. Root hx-disabled-elt now disables current
controls during requests without editing htmx vendor bytes or server history.
A bad form-selector assumption and an Open-details visibility assumption were
corrected in QA, not counted as extra product bugs. Final local checks: **199
history-target passes**, full Python browser **32 passes**, actual Rust HTTP/
browser passes; minimum history-only **20 passed/2506 deselected/13warnings**.
Ruff213formatted/Pyright/LSP5paths/contracts/packaging pass in9recorded commands.

Observed remote781f3f5 Rust Linux/Windows jobs, including MSRV1.88/interpreter/
body probes, both succeeded; RUST-02 is now PASS. Python3.12 also succeeded but
Python3.10 was cancelled, so workflow39050108296 was cancelled, not fully green.
The remote result does not validate this later UI change. See [phase14 receipts](review_evidence/history_policy_verification.json).
[Tracker](REVIEW_CHECKLIST_STATUS.md): **PASS34/RUNNING12/OPEN104**. Version/lock/
tag/deploy/source checklist unchanged; broader CI/release/performance gates remain.

### Earlier review phase 13

**Review phase 13 fixes unsupported scalar coercion/recursion.** FIND-015 had
Decimal/custom NaNs becoming null, signaling NaN leaking InvalidOperation, and
longdouble/same-type/alternating item chains recursing. Seven cases failed before
restricting missing detection to recognized NumPy/pandas scalars and item progress
to supported plain/date values. Seventy-one scalar checks retain supported types,
object identity and strict rejection without lossy float/string/null conversion.
DATA-06 is PASS, not a sandbox for caller Python methods.

The914a402 Linux CI passed its advanced-effect smoke, then failed missing default
provenance; Windows cancelled. Wrong interpreter selection and the exact remote
customizer origin are unproven. A unique disposable .pth/module recorder now
self-checks operation alongside a preserved foreign sitecustomize, retaining
all executable/prefix/version/argv assertions. Windows local4cases/12children
pass; RUST-02 stays RUNNING pending observed Linux rerun.

Recorded target **1116 passed/27 skipped**, optional overlay **244 passed/no
skips**, minimum subset **354 passed/25 skipped/2142 deselected/481warnings**;
Ruff212formatted/Pyright/LSP5paths/contracts/packaging and path probe pass in9
commands. [Phase13 evidence](review_evidence/scalar_provenance_verification.json)
preserves exact scope and sanitized failed-job-log digest. No new browser/native
unit counts are claimed. [Tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS30/RUNNING14/OPEN106**. Original checklist/versions/locks/tag/deploy stay
unchanged; whole-suite/OS/MSRV/audit/resource/release completion is not implied.

### Earlier review phase 12

**Committed/pushed snapshot359277c, then continued with temporal precision and
CI fixture setup.** FIND-013 fixes NumPy fine-unit datetime64 becoming integer
epochs and Polars datetime(ns) losing nanoseconds. Thirty-six cases failed before
preserving dtype/native formatting; native parse/equality prevents lossy output.
Coarse formats, real numeric epochs, NaT and generic2D protocols stay supported.
Fifty-eight temporal checks include UTC/offset/DST, child TZ/C locale, nested input
shapes and explicit unsupported numeric date-axis handling. Arrow follows upstream
safe conversion requirements; this is not every temporal history/OS/axis feature.

FIND-014 is a CI environment mismatch, not a new mandatory runtime dependency.
Run39045121490 for359277c completed: Python3.10/3.12 jobs succeeded; Linux Rust
MSRV/lint/unit succeeded but advanced-regression smoke failed400; Windows cancelled.
Source/logs plus a render-only reproduction identify missing optional effects.
The smoke job now installs extra all and has a pre-fix-failing static guard.
An isolated all-extra smoke passes locally; remote rerun success remains pending.

Recorded target **1045 passed/27 skipped**, optional overlays **173 passed/no
skips**, minimum subset **283 passed/25 skipped/2142 deselected/481warnings**.
Ruff211formatted/Pyright/LSP5paths/contracts/packaging also pass. Nine receipts
are in [phase12 evidence](review_evidence/temporal_ci_verification.json). New
browser/native-unit counts are not inferred. [Tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS29/RUNNING14/OPEN107**, with DATA-05 closed for the observed conversion scope.
Original checklist/versions/core dependencies/locks/tag/deploy stay unchanged;
full current suite/OS/MSRV/resource/security/release gates remain incomplete.

### Earlier review phase 11

**Review phase 11 completes the observed request-body boundary matrix.**
FIND-011 fixes Python ignoring unsupported Transfer-Encoding, duplicate lengths
and short bodies; six cases failed before the fix. Content-Length bodies are
read exactly, and bad framing fails before actions. Python chunked remains
unsupported and is explicitly rejected, not decoded by new custom code.

FIND-012 was Rust undo mutating before checking an unknown-size body. The probe
planned16MiB+1 but aborted after393216bytes yielded; it was not a complete
oversized-body acceptance claim. Existing limited Bytes extraction now runs
before every handler, retaining request parts, downstream limits and headers.
Form/JSON/chunked boundaries including undo/reset pass39sequential local cases.

Correct worker-PID observations (not the Windows venv launcher) show lifetime
server peaks of Python252.14MiB/Rust30.40MiB. Native renderer children are excluded;
these are not per-request resets, hard whole-app memory/CPU or concurrency bounds.
Owned process trees/listeners are closed. SEC-03 is PASS; SEC-04/PERF remain open.

Recorded results: **993 passed/20 skipped**, Python browser **31 passed**;
minimum subset **232 passed/18 skipped/2142 deselected/481 warnings**; native Rust
**15 passed/1 helper ignored**, actual Rust HTTP/browser, Clippy/fmt, Ruff209/
Pyright/LSP7paths/contracts/clean sdist→wheel pass.13commands and39observations
are in [phase11 receipts](review_evidence/body_boundary_verification.json).
CI is configured, not a remote/Linux/MSRV result. No runtime dependency/lock/
version/tag/deploy changes. [Tracker](REVIEW_CHECKLIST_STATUS.md):
**PASS28/RUNNING14/OPEN108**; broader release/resource/security gates remain open.

### Earlier review phase 10

**Review phase 10 completes observed-format equivalence and SQL ownership.**
Real PyArrow 26.0.0/Polars 2.0.0 were installed only in a disposable environment.
All **114 targeted checks passed without skips**; the configured CI command also
passed the same114 locally (not228unique tests). Fourteen ingestion paths include
Arrow chunks/dictionaries, Polars categorical, borrowed SQL cursor and generic
to_dict. Extra scalar/empty/duplicate cases verify values/types/source fidelity,
UTC microseconds and strict Decimal/infinity rejection. This is not every optional
version/precision/timezone/OS combination. DATA-01 is PASS for its documented scope.

FIND-010 reproduced five missing cleanup cases before the fix. Connection+query
now closes only the cursor it creates, on success and failure when supported;
borrowed cursor/connection and transaction control stay with the caller. Cleanup
errors propagate with exception context; minimal duck cursors still work. Ten
SQL ownership checks pass. DATA-07 is PASS; no package dependency or version changed.

Project regression subset: **980 passed/20 skipped** (18 optional-only,2Windows).
Minimum data-only subset: **95 passed/18 optional skips/2266 deselected/13warnings**,
not a repeat of the broader earlier minimum suite. The actual optional tests ran
separately without skips. Ruff207formatted/Pyright/LSP6paths/contracts/clean
sdist→wheel pass;9commands and environment cleanup are in [phase10 receipts](review_evidence/table_sql_verification.json).
The dedicated venv was removed, original project optional imports remain absent,
and project dependencies/locks remain unchanged. Browser/native Rust below are
historical, not new runs. Remote optional CI is configured, not observed.

[Tracker](REVIEW_CHECKLIST_STATUS.md): **PASS27/RUNNING15/OPEN108**. Source checklist,
versions/tags/deploy remain unchanged. Full suite/minimum/MSRV/Linux/security/
body-memory/release gates remain incomplete.

### Earlier review phase 9

**Review phase 9 completes modeled-field JSON coverage and Windows interpreter
path verification.**24model types/272fields have nondefault/alternate-union/null
structural fixtures plus nested-type and JSON primitive checks. These intentionally
incompatible options are schema-valid, not renderable feature-parity claims.
The37registered example specs are checked separately. A real Python→Rust→Python
artifact preserves3fixture figures, values/types/array order. JSON-01 is PASS.

A separate disposable Unicode/spaces/`&` venv verifies PATH/env/flag priority:
12real capabilities/apply/render children have the expected executable/prefix/
version/argv, while a bad explicit flag does not fall back. An offline setup
initially lacked cached wheels; preparation was explicitly allowed to download
same-version render packages only in that temporary venv. Project packages/locks
stay untouched; the test-only recorder is isolated and exclusively created.
RUST-02 stays RUNNING: actual Windows passed, Linux CI is configured but unobserved.

Recorded focused results: **968 passed/4 skipped**, minimum subset **207 passed/
2 skipped/2142 deselected/481 warnings**, native Rust **15 passed/1helper ignored**.
Ruff205formatted/Pyright/LSP6paths/Clippy/fmt/contracts/packaging pass.12primary
commands and5QA-isolation/style/package followups have separate source revisions
in [phase9 receipts](review_evidence/codec_path_verification.json). Browser31below
is historical, not a new run. No product bug or runtime rewrite was needed.

[Tracker](REVIEW_CHECKLIST_STATUS.md): **PASS25/RUNNING16/OPEN109**. Source checklist,
versions/core dependencies/tags/deploy remain unchanged. Full suite/minimum/
Linux/MSRV/audit/release gates are not claimed complete.

### Earlier review phase 8

**Review phase 8 verifies cross-path state/failure/local HTTP boundaries.**
FIND-008 fixes Rust Host/Origin rejections missing shared no-store/CSP headers;
access conditions are unchanged. FIND-009 adds pre-upload Content-Length>16MiB
rejection while retaining streaming limits. It is not proof of an unlimited
payload bypass or completion of content-type/chunked/RSS testing.

Shared10-step state fixtures compare fluent/functional/Store/CLI/Python/Rust
agent and supported forms at every state, including log axes, layout, styles,
references and typed heatmap. Both editors retain spec/PNG/redo across invalid
actions, damaged JSON and real rendering failures. Native IPv6 listener/HTTP,
Host/Origin matrices, all application-response headers and actual browser CSP
observations are recorded in [phase8 receipts](review_evidence/editor_boundary_verification.json).

Final results: **899 passed/4 skipped**, Python browser **31 passed**; minimum
subset **138 passed/2 skipped/2142 deselected/481 warnings**. A visible-warning
probe found old Matplotlib/modern pyparsing deprecation/diagnostic messages;
this is not a zero-warning claim. Native Rust **14 passed/1 helper ignored**,
real HTTP/browser, Clippy/fmt, Ruff203formatted/Pyright/LSP7paths/schema/clean
sdist→wheel and IPv6 checks all passed in13 recorded commands. Not MSRV1.88.

An earlier combined attempt failed with Windows10053 during body-carrying early
rejection, then log decoding failed; it was not credited as complete. Denied
Origin probes now separately require403 before body upload/decoding; allowed
origins still send real payloads. The transport cause is not claimed fixed.
[Tracker](REVIEW_CHECKLIST_STATUS.md): **PASS24/RUNNING16/OPEN110**, with SEC-03
still RUNNING. Original checklist/version/tag/deploy and core dependencies stay
unchanged; full suite/minimum/Linux/MSRV/security audit/release gates are open.

### Earlier review phase 7

**Review phase 7 fixes missing raw categorical x coordinates and verifies nested
state/history contracts.** FIND-007 turned null x values into a literal None
category. Ten cases failed before shared `_x_values` conversion was fixed to
leave missing rows as NaN. Lines break, scatter points are masked, real `"None"`
labels and shared/y2 positions remain intact; no continuous date-axis feature
or new statistics policy is implied.

Recorded focused checks: **859 passed, 4 skipped** (PyArrow/polars absent2,
Windows-specific2). Minimum Python3.10/NumPy1.23 subset: **98 passed, 2 optional
skips, 2142 deselected, 13 warnings**. Real Rust HTTP/browser smoke verifies
all history steps/PNG caches, boundaries and new branches as well as the JSON
corpus. Ruff201formatted/Pyright/LSP5paths/schema/clean sdist→wheel pass.
Native Rust unit/MSRV counts are not new runs in this phase.

Nested reducer inputs/actions, public snapshots/history/listeners, complete
undo/redo and post-undo branches are now evidenced; STATE-01/02, HIST-01/02 and
DATA-03 are PASS. DATA-01 remains RUNNING because actual PyArrow/polars are not
installed. HIST-04 remains RUNNING for wider reset/dirty/save-target cases.
An initial Rust probe incorrectly treated open as clearing history; the probe
was corrected, not the product. Python open/reset starts fresh history; Rust
open/reset is undoable. Existing behavior is now explicitly documented.

[Tracker](REVIEW_CHECKLIST_STATUS.md): **PASS17/RUNNING15/OPEN118**. The portable
[phase7 receipt](review_evidence/missing_state_verification.json) includes source/
log fingerprints, exact command scopes and canonical cursor hashes. Full suite/
minimum/MSRV/Linux/security/release gates remain open. Original checklist,
package/editor/spec versions, tags and deployment are unchanged.

### Earlier review phase 6

**Review phase 6 completes DATA-02 input-shape checks.** FIND-006 was mixed
records raising unlocated AttributeError and text/bytes/dict rows silently
becoming character/key columns. Nineteen cases failed before the fix. Record
mapping/index checks plus shared row-value validation now reject those inputs
before pivoting while sparse-record nulls/order and sqlite3.Row remain supported.
Column lengths still remain intact at ingestion and fail semantic validation;
no automatic resizing or new data coercion is introduced.

Starting from committed snapshot96a8592, the recorded focused run is **677 passed,
2 Windows-specific skips**. Minimum Python3.10/NumPy1.23 adapter checks report
**66 passed, 2142 deselected, 13 warnings**. Ruff200formatted/Pyright/contract sync/
clean sdist→wheel pass. Active LSP confirmed1 of2 paths; the other is inconclusive,
not a clean LSP result (explicit Pyright on both changed paths passed). New checks
include required x/y/group errors, pandas duplicate columns, malformed protocol
columns, and invalid editor import/action preserving state/history/PNG/redo plus
CLI source/output bytes. Actual PyArrow/polars are not installed or certified.

[Tracker](REVIEW_CHECKLIST_STATUS.md): **PASS12/RUNNING13/OPEN125**. A path-redacted
[phase6 receipt](review_evidence/data_shape_verification.json) preserves results/
source hashes beyond local temp logs. Original checklist/version/tag/release state
is unchanged. Rust/full-browser counts below predate this Python-only change;
full suite/minimum/MSRV/Linux/security audit remain incomplete.

### Earlier review phase 5

**Review phase 5 fixes two Rust JSON contract mismatches.** FIND-004 is serde
arbitrary_precision reinterpreting a literal reserved-key object as a number;
FIND-005 is rejecting an omitted version which Python defaults to current.
Both unit(exit101) and HTTP failures were reproduced before the shared-boundary
fixes. Original property-name token checks preserve big integers/text; version
fallback reads the embedded default without accepting null/unknown versions.

A shared 19-invalid-spec/11-invalid-action/2-valid-spec corpus now runs across
API/CLI/Python session/HTTP/Rust JSON/raw/open. Negative cases unrelated to
version explicitly use0.1, and accepted suptitles differ so old state cannot
masquerade as a successful import. A corpus regression enforces those properties.
The packaged sdist is checked for the source-tree smoke fixture.

Recorded Agg contract results: **597 passed, 2 Windows-only skips**; Rust all
native targets **lib13+main1 passed, 1 intentional helper ignored**, real HTTP/
browser corpus passed. Native Clippy-Dwarnings/fmt, Ruff200formatted/Pyright,
activeLSP6paths/schema/clean sdist→wheel pass. Compiler1.99 is NOTMSRV1.88.
See [tracker](REVIEW_CHECKLIST_STATUS.md) for manifests/logs/receipts and exact
scope. JSON-02/06/07 are now PASS; tracker **PASS11/RUNNING14/OPEN125**. No
whole-checklist/release/OS/security/performance guarantee or version/tag/deploy
change is implied. Full suite/minimum/MSRV/Linux remain deferred.

### Earlier review phase 4

**Review phase 4 fixes a DATA-02 silent-data-loss boundary.** Ragged positional
rows and DB cursor rows mismatched to description now fail before pivoting with
row index/actual/expected width. Before-fix fixture reported7fail/1pass; normal
rows/order/source inputs remain unchanged. No padding/truncation/default coercion
was introduced. See FIND-003 in the [tracker](REVIEW_CHECKLIST_STATUS.md).

The recorded Agg contract set reports **404 passed, 2 Windows-only skips**;
minimum Python3.10/NumPy1.23 adapter cases **25 passed, 2142 deselected,
13 warnings**. Ruff199formatted/Pyright/activeLSP4paths/schema sync pass. New
JSON/render cases separate adapter missing→null from strict NaN/Infinity/range
rejection, and prove unsupported giant-coordinate/style/size exports/editor
opens retain old files/state/history/preview and can recover. JSON-05 is now PASS;
DATA-02 stays RUNNING for remaining matrix/format/required-column coverage.
Tracker: **PASS8/RUNNING17/OPEN125**, not all-checklist/release approval. An initial
unrecorded regression attempt used Tk and failed on missing Tcl; it is not
credited as a product fix or successful run. Agg rerun and manifest are recorded
in phase4 evidence. Original checklist is unchanged. No version/dependency/tag/
deployment changes. Full suite/minimum/MSRV/Linux/GUI/security audit are deferred.

### Earlier review phases 2/3

**Review phases 2/3 complete for their bounded contracts.**
[Evidence tracker](REVIEW_CHECKLIST_STATUS.md) now has PASS7/RUNNING17/OPEN126.
JSON-03 recursive equal/different duplicate rejection, JSON-04 signed integer
structural fidelity and OUT-03 single-file fault isolation are newly PASS based
on Python/API/CLI/editor/Rust/HTTP evidence. JSON-06/07 and OUT-04 stay RUNNING
where broader field/platform/resource cases remain unverified.

Reproduced FIND-001 (Rust layer registry test expected36 vs actual37, exit101)
and fixed its integration assertions. Reproduced FIND-002 in JSON/PNG/PDF/SVG:
Windows read-only targets caused read-only staging leaks on failed replacement.
`io._atomic_destination` now copies POSIX modes only on non-Windows. It never
clears target read-only attributes or chmods unrelated files. Four read-only
cases failed before and pass after; actual Win32 delete-sharing locks and bad
paths/directories also preserve bytes, staging cleanup and Figure ownership.

Recorded phase2: Python338passed/2Windows skips; Rust lib11passed/1intentional
helper ignored; actual HTTP/browser smoke and strict fixture/state/preview checks
passed. Phase3 after production fix: **354 passed, 2 Windows-only skips**, all
commands exit0 including Ruff197formatted/Pyright/schema sync/clean sdist→wheel.
Eight actual Windows lock/read-only cases pass. Evidence includes manifests,
JUnit, logs, argv/exit receipts and summarized actual pre-fix failures. See exact
scope/temp paths in tracker. Source checklist SHA is unchanged. No version/tag/
deployment changes; full suite/minimum/MSRV/Linux/security audit/performance and
release gate approval are NOT inferred from these focused runs.

### Earlier review phase 1 and clustermap integration

**Operator review checklist adopted.** The 2026-10-16 source remains unchanged;
[150-ID evidence tracker](REVIEW_CHECKLIST_STATUS.md) links candidate code/tests
without treating them as verification. HEAD matches checklist SHA c4f40ab; local
uncommitted/untracked additions are fingerprinted separately. New batch/listener/
output fault regressions add 17 tests. A recorded core-contract subset reports
**127 passed, 2 Windows-only skips, exit0**, with environment/tree hashes, JUnit,
log and argv receipt in the tracker-linked temp evidence directory. Only BASE-01
and STATE-04/05/06 are PASS; 20 are RUNNING, 126 OPEN. No production defect was
newly reproduced in that limited run; no all-150 or release approval is claimed.

**B5c clustermap integration completed before the checklist pass.**
[Scope](CLUSTERMAP.md), [example](images/clustered_profiles.png). ClusterSpec
supports optional SciPy row/column linkage, supplied checked trees, optimal
leaves, display standardization and aligned labels/masks/colour strips. Source
matrices stay intact. Nested GridSpec fixes auxiliary/title clipping; clustered
positions are frozen to stabilize subpixel-sensitive SVG clip IDs. There are
now 37 registry layers, not complete plotting/statistics parity.

Its completed targeted receipt is **1240 passed, 2 Windows skips**; Python real
browser **30 passed**; isolated minimum Python3.10/NumPy1.23/Matplotlib3.8/
SciPy1.10/statsmodels0.14.1 cluster+regression checks **92 passed,
2050 deselected, 13 warnings**. These predate the new review-only test additions
and are not a full checklist run. Rust HTTP/browser, Ruff/Pyright, contract sync,
sdist-to-wheel/-S smoke and dependency consistency checks passed. Remaining 22
legacy demos gained only cluster=None with semantic identity checked. Optional
cluster extra includes SciPy>=1.10 (all/dev); mandatory core deps remain empty.
Package/editor1.0.0/spec0.1 and release assets/tags remain unchanged. Full suite/
full minimum/MSRV/security audit/Linux/TeX/performance/provenance remain open.

### Earlier B5b configured regression

**B5b configured regression is integrated** — [API/limits](REGRESSION.md),
[residual example](images/regression_residual.png),
[logistic example](images/regression_logistic.png),
[source](../examples/regression_modes.py). Opt-in RegressionSpec selects poly/
log-x/Huber/binomial-logit/LOWESS; residplot aliases observed-minus-in-sample-fit
with original row order and a zero guide. Group/facet selection precedes fits;
raw source data remains intact. Residual joint templates fail rather than
mislabel raw-y marginals. Legacy regression=None remains unchanged.

Added an explicit optional regression extra(statsmodels>=0.14.1, included by
all/dev), with root/script locks updated. Mandatory core dependencies stay empty;
poly/residual/log-x still need only render. Effect-only imports and strict
finite/model/convergence/separation guards preserve existing output on failure.
LOWESS uses finite-checked inputs with missing='none' because installed statsmodels
raises unconditionally for explicit xvals with missing='raise'; vendor code is
untouched. No jitter/regularization/callable fallback is introduced.

Current checks: **1184 targeted core/render/schema/reducer/statistical/property/
Python-editor tests passed, 2 Windows-only skips**; **29 Python real-browser tests
passed**, including all five regression imports/edits/SVG. Minimum Python3.10 /
NumPy1.23 / Matplotlib3.8 / statsmodels0.14.1 regression checks: **46 passed,
2050 deselected, 13 warnings**, not a full minimum run. Current effects also pass
with statsmodels0.15.0. Rust HTTP/real-browser smoke verifies all five raw AddLayer
configs and PNG/SVG. uv pip check confirms the optional dependency environment.

Ruff/Pyright/active LSP on 12 changed paths, generated-contract sync and clean
sdist-to-wheel/-S smoke pass. Demos/gallery/contracts were regenerated; remaining
22 old demo specs gained nullable regression config with semantic identity asserted
and raw JSON retained. Five synthetic single-question examples pass 700px font/
bounds/text checks, not independent readability grading. Package/editor1.0.0,
spec0.1 and published assets/tags/deployment remain unchanged; this is Unreleased
source functionality. Full Python/minimum, Rust unit/MSRV and dependency security
audit were not rerun. Weights/bootstrap/advanced CI, residual trends/diagnostics,
clustering and broader B2b/B3/B4/B5/B6 options remain open.

### Earlier B5a typed heatmap

**B5a typed heatmap controls are integrated** — [API/limits](HEATMAP.md),
[example](images/heatmap_controls.png), [editable spec](images/heatmap_controls.mplot.json).
Opt-in HeatmapSpec adds mask/raw formatted annotations/labels, explicit/log/
centered/robust colour ranges, square cells and borders. Mask excludes hidden
values from colour statistics/text without rewriting the finite matrix. Typed
colourbar boundaries/values avoid native large-value and subnormal failures.
Legacy heatmap=None remains unchanged; no new layer type or mandatory dependency.

A real browser regression also exposed native form fallback: unwired forms used
GET URLs, while POST under no-referrer produced null Origin. Shared editor forms
now have explicit POST actions and same-origin referrer policy (no external
referrer); existing cross-origin/null-Origin rejection is unchanged. Native
POST/Undo works with JS disabled; heatmap import/edit/SVG preserves full config.

Current checks: **1138 targeted core/render/schema/reducer/statistical/property/
Python-editor tests passed, 2 Windows-only skips**; **24 Python real-browser tests
passed**. Minimum Python 3.10 / NumPy 1.23 / Matplotlib 3.8 heatmap checks:
**37 passed, 2013 deselected, 15 warnings**, not a full minimum run. Rust HTTP/
real-browser smoke verifies typed masked/annotated heatmap action, source matrix
retention and PNG/SVG. Ruff/Pyright/active LSP/generated-contract sync and clean
sdist-to-wheel/-S smoke pass. Prospective derived span failures preserve output.

Contracts/demos/gallery were regenerated. Remaining 22 legacy demo specs gained
only nullable heatmap configuration with semantic identity asserted and raw JSON
fields retained. The synthetic example passes selected 700px font/bounds/text QA,
not independent readability or accessibility certification. No version
(package/editor1.0.0, spec0.1), tag/deploy/dependency changes. Full Python/minimum,
Rust-unit/MSRV/dependency auditing remain deferred. Custom annotation matrices,
clustering/more norms and other B2b/B3/B4/B5/B6 work are still open.

### Earlier B4e configured KDE grids

**B4e configured KDE grids are integrated.** Joint `marginal_kind='kde'` and
pair `diag_kind='kde'` accept strict KDESpec/dict bandwidth, grid, support,
normalization and fill settings without changing hist defaults. Cohorts, source
rows and axes stay as before; singular fits retain existing warning/skip rules.
Density only: nondefault hist bins/stats, weights and cumulative KDE are rejected.
See [joint KDE](JOINT_GRID.md#kde-marginals), [pair KDE](PAIR_GRID.md#configured-kde-diagonals)
and [synthetic source](../examples/kde_grids.py).

Current checks: **965 targeted core/render/KDE/schema/reducer/statistical/property
tests passed, 2 Windows-only skips**; **22 Python real-browser tests passed**,
covering both hist and KDE import/edit/SVG. Minimum Python 3.10 / NumPy 1.23 /
Matplotlib 3.8 KDE-grid checks: **31 passed, 1982 deselected, 13 warnings**, not a
full minimum run. Rust HTTP/real-browser smoke verifies configured KDE joint and
pair actions, unchanged input data and PNG/SVG. Global Pyright and active LSP on
10 changed paths are clean. Earlier imported-helper type reports were fixed by
narrowing KDESpec at the trust boundary and confirmed clean, not suppressed.

Ruff, generated contracts, rebuilt demos/gallery and sdist-to-wheel/-S import
pass. Nested KDESpec action payloads serialize as plain JSON; wheel smoke replays
KDE grids without optional dependencies. Two editable/vector synthetic examples
pass the selected 700px font/bounds/text checks, not independent readability
certification. No spec/dependency/package/editor version, tag or release changes.
Full Python/minimum, Rust-unit/MSRV/dependency audit were not rerun for this batch;
weighted/CDF/semantic/c/nested grids and broader B2b/B3/B5/B6 remain open.

### Earlier B4d pair matrix integration

**B4d numeric pair matrices and named value axes are integrated** —
[API/limits](PAIR_GRID.md), [image](images/pair_observations.png),
[editable spec](images/pair_observations.mplot.json). `pair()` / `SetPairGrid`
creates 2..8-variable raw scatter matrices with typed histogram diagonals,
pairwise/univariate complete cases and retained source data. `AxisSpec.share_id`
with `SetAxisShare` / `share_axis()` links primary measurement axes without
joining diagonal density/count y. Names cannot mix figure sharing or conflicting
scales/explicit limits. Old unnamed axes keep their existing behavior.

Current checks: **809 targeted core/render/schema/reducer/statistical/property
checks passed, 2 Windows-only skips**; **20 Python real-browser tests passed**,
including nine-cell pair file import, cell edit and SVG. Minimum pair tests on
Python 3.10 / NumPy 1.23 / Matplotlib 3.8: **34 passed, 1948 deselected,
13 warnings**, not a full minimum run. Rust HTTP/real-browser smoke passes pair
action → named axes → PNG/SVG. Ruff/Pyright/generated-contract sync and source
archive-to-wheel rebuild/import pass; wheel `-S` smoke constructs/replays pair
and joint grids without optional dependencies.

The 900px synthetic example was inspected and passes selected font/bounds/text
checks, not independent readability grading. Demos/contracts were regenerated;
22 remaining older demo specs gained only nullable named-axis defaults with
parsed semantic identity asserted. No source rows/styles were discarded. No
spec version (0.1), package/editor version (1.0.0), dependency, tag or deployment
change. Full Python/minimum, Rust unit/MSRV and dependency audit were not rerun.

Corner/KDE/semantic/weighted/nested pair grids, wider joint kinds, consolidated
legends/live mapping and remaining B2b/B3/B5/B6 work are still open.

### Earlier B4c joint histogram composition

**B4c joint histogram composition is integrated** — [API/limits](JOINT_GRID.md),
[example](images/joint_observations.png), [editable spec](images/joint_observations.mplot.json).
`joint()` / `SetJointGrid` materializes one raw scatter/regplot plus x/y histogram
marginals in three panels, with no padding axes. Optional `PanelSpec.dropna=[]`
keeps the original table intact while all views dynamically use identical complete
x/y/group rows. Shared value axes never link density/count to measurement units.
Source labels/styles/references and grouped slots are preserved. Pair grids,
semantic/c/weighted/KDE/hexbin joint kinds and nested grids remain open.

Current checks: **761 targeted core/render/schema/reducer/statistical tests passed,
2 Windows-only skips**; **19 Python real-browser tests passed**, including joint
file import, exactly three selectable panels and marginal-only edits/SVG export.
Minimum Python 3.10 / NumPy 1.23 / Matplotlib 3.8 joint tests: **41 passed,
1907 deselected, 193 warnings** (not a full minimum suite). Rust HTTP/real-browser
smoke passes SetJointGrid, source retention, paired selectors and PNG/SVG. Ruff,
Pyright, generated contracts and sdist-to-wheel rebuild/import pass; the wheel's
`-S` smoke constructs and replays a joint grid without optional dependencies.

Demos/gallery and contracts were regenerated. Remaining 22 legacy demo specs gained
only empty `dropna`, with parsed semantic identity asserted and raw JSON fields
preserved. The paired example was inspected and passes its selected 700px font/
bounds/text-overlap checks; no independent readability grading is claimed.
Derived log-bin failure retains the previous output, and dropna semantic pools
keep original row IDs rather than renumbering selected rows.

No dependency, version (package/editor 1.0.0, spec 0.1), tag or deployment changes.
The **2398 full-suite receipt below predates joint changes**. Full Python/minimum,
Rust unit/MSRV and dependency audit were not rerun for B4c. Wider B2b–B6 and
release gates remain open.

### Earlier B4b raw grouped facets

**B4b raw grouped facets are implemented** — [raw semantics and limits](FACETS.md#raw-groups-keep-raw-meaning).
Line/scatter/bar/errorbar/band/stripplot/regplot/rug now use selected/reserved
raw hue slots, including missing groups in individual cells. Input path order,
duplicate x, coordinate gaps, supplied bar values and paired uncertainties remain
raw; no statistical builder conversion occurs. Unordered defaults remain intact.

Current full locked Python run: **2398 passed, 2 Windows-only skips, 1 warning**
(including browser and TeX cases), exit 0. The earlier interrupted attempt is not
credited; this completed rerun is the current receipt. The warning remains the
known extreme-finite-ECDF native ticker overflow. Focused raw/facet checks are
**82 passed**. Minimum Python 3.10 / NumPy 1.23 / Matplotlib 3.8 raw-order checks:
**31 passed, 1876 deselected, 201 warnings**, not a full minimum-suite result.
Rust HTTP/real-browser smoke verifies sparse raw groups, preserved source data,
reserved hue order, absent statistical configuration, and PNG/SVG output.

Ruff lint/format, Pyright, generated-contract sync, regenerated demos/gallery and
sdist-to-wheel rebuild/import pass. No dependency, spec-version, package/editor
version, tag or deployment change. Full minimum/Rust unit/MSRV/dependency audit
remain deferred. Legacy c/colorbar faceting, live mapping, consolidated guides,
pair/joint grids and the other B2b/B3/B5/B6 work are not complete.

### Earlier B4a facet subset

**B4a automatic facet first subset is implemented** — [API/limits](FACETS.md),
[example](images/faceted_responses.png), [editable spec](images/faceted_responses.mplot.json).
`facet()` / `SetFacets` materializes row/col/wrapped cells with exact panel
filters, shared axes, pooled semantic mapping domains and cell-local inference.
The source table remains intact; category/hue slots and original row IDs are
preserved. Python/actions/JSON/schema/editor import/raw actions work, including
Rust HTTP/browser action → filtered panels → PNG/SVG. This is not all B4/B2b–B6:
legacy grouped series/c, live mapping, consolidated guides and pair/joint grids
remain explicitly unsupported, alongside the other planned families.

Current full locked Python suite: **2367 passed, 2 Windows-only skips, 1 warning**
(includes existing real-browser and TeX matrix tests). The warning remains the
known native ticker overflow for extreme finite ECDF mass. Targeted facet tests:
**51 passed on Python 3.10 / NumPy 1.23 / Matplotlib 3.8, 1825 deselected,
185 warnings**; this is not a new full minimum-suite run. Ruff lint/format,
Pyright, generated schema/capabilities/reference sync and sdist-to-wheel checks
pass. Rust editor HTTP/real-browser smoke passes with the new action.

The same spec version 0.1 now has optional `PanelSpec.filters={}`; older specs
remain unfiltered. Generated contracts/demos were regenerated, and 22 remaining
legacy demo specs were canonicalized by adding empty filters only, with semantic
identity asserted. Source/data/styles were not discarded. The facet sample was
inspected and passes its selected 900px font/bounds/text-overlap checks, but is
not independent readability certification or a mobile layout.

No dependencies, package/editor version (1.0.0), tags or deployment changed.
Full minimum/Rust-unit/MSRV/dependency-audit gates were not rerun here; the wider
implementation and release work remains open.

### Earlier gallery/editor integration

Gallery/editor integration: the built site's reading section links to freshly
rendered layouts, editable specs and self-contained local review/criteria pages.
The Python editor offers four complete figure drafts from the same builders.
Selecting one only fills the Open form: current figure, PNG and action history
are preserved until explicit Open. Invalid imports retain the submitted draft
and old figure. htmx page-body history caching is disabled; query IDs are
allowlisted/bounded, and draft text is HTML-escaped. Preview fitting is not a
new readability certification.

Current checks: **227 dashboard/editor/visual/lint/schema/layout/no-deps tests
passed**; minimum **28 visual tests passed, 1797 deselected, 13 warnings**;
**18 real-browser tests passed**, including draft → explicit Open → edit → SVG
and built-gallery download → file picker import. Static review/criteria local
links and builder/spec equality are checked; rendering failures keep previous
editable specs and unrelated files. Optional dependencies remain lazy on sample
module import. Full Python/minimum and Rust/TeX suites were not rerun for this
source-tree UI batch. Engine/defaults/schema/dependencies/versions are unchanged;
B2b–B6 and release gates remain open.

### Earlier reading-first rework

Reading-first rework: [desktop/mobile review](VISUAL_REVIEW.html) and
[criteria/references](VISUAL_QUALITY.md). The user rejected the earlier four-panel
prototype; the new candidate has separate response and horizontal endpoint charts,
direct line labels, captions and numerical endpoint lookup. Raw observations,
means, CI endpoints and numeric value ranges are checked against the prototype.

Saved-PNG QA now measures final display pixels and text-box intersections rather
than accepting original point sizes alone. Two explicit 700px/320px layouts are
used. Real browser viewports 900/600/360/320px show charts at 700/320/320/280px,
all meeting the selected 14px web-font floor; below-profile desktop downscaling
is a tested failure. The review table is checked against the same estimator.

Current checks: **82 visual/lint/schema/layout tests passed**; minimum environment
**27 visual tests passed, 1795 deselected, 13 warnings**; **15 real-browser tests
passed**, including 11 existing editor cases and four viewport variants. Ruff,
Pyright, generated contracts and sdist-to-wheel checks pass. Browser screenshots
at actual display widths were inspected. This is still not an independent reader
study or model-grade result: both are explicitly `not_run` in the QA report.

ONS, PLOS/Rougier, VisJudgeBench and graphical-perception references are mapped to
individual evidence/limitations; no aggregate aesthetic score is invented. Labels
are hand-placed for this fixed dataset, not a general placement engine. Core
renderer/default theme/schema/dependencies/versions are unchanged. Full Python/
minimum suites and Rust/TeX were not rerun for this sample rework; B2b–B6 remains
open and no release is authorized.

### Earlier visual prototype — rejected by user review

The following automated receipts did not establish readability and are retained
as history, not a successful design baseline.

Visual-quality/sample batch: [review method and before/after](VISUAL_QUALITY.md).
The controlled showcase keeps observations/statistics/limits/physical size fixed,
uses at least 8.5pt actual text and stays within native canvas bounds. Grey/CVD
views, JSON QA evidence and a refreshed Pandas demo were generated and inspected.
Both styles pass automated QA; there is no invented aesthetic score or independent
user preference study. Renderer/default theme/schema/version are unchanged;
lint now ignores disabled legends when estimating visible clutter (two regressions).

Targeted visual/lint/schema/layout tests: **66 passed**. Minimum-environment
visual tests: **11 passed, 1795 deselected, 13 warnings**. PNG/PDF/SVG repeatability,
JSON/actions, negative font/overflow/empty cases and unchanged data/statistics
are covered. The new sample is included in future full minimum checks. Whole
Python/minimum suites and Rust/browser/TeX were **not rerun after this visual-QA
batch**; the complete prior receipts below remain a baseline, not a new full run.
B2b–B6 feature work remains open; this is visual QA, not parity completion.

### Full checkout baseline before visual updates (after B3j)

- Locked environment synchronized without changes (Python 3.12.15, NumPy 2.5.2,
  Matplotlib 3.11.1): **2251 passed, 2 Windows-only skips, 1 warning**. Includes
  all 11 Python real-browser tests and four real-paper TeX/bibliography cases;
  browser cases are part of the total, not added to it.
- Minimum Python 3.10 / NumPy 1.23.0 / Matplotlib 3.8.0 script:
  **1795 passed, zero skips, 3532 warnings**. Warnings are reported, not hidden
  or presented as a warning-free result. The locked warning is the existing
  native tick overflow for extreme finite ECDF count mass.
- Rust 1.99 fmt/Clippy/tests pass (11 passed, 1 ignored); Rust real HTTP/browser
  and Python editor smoke, clean sdist-to-wheel rebuild/import, generated
  contracts, Ruff lint/format and Pyright pass.
- The initial full run stopped at 1541 passed / 1 failed because Ghostscript
  txtwrite emits UTF-8 while Windows subprocess text decoding used cp949.
  Explicit UTF-8 in the shared PDF-text test helper plus a portable non-ASCII/
  ligature subprocess regression fixed it; both complete suites then passed.
  No rendering/API behavior changed. Contributor browser selection now uses
  filenames: no `browser` marker is registered.

Rust 1.88 MSRV and dependency auditing were not rerun in this batch. The wider
B2b–B6 scope and global release gates remain open; package/editor 1.0.0 and spec
0.1 are unchanged. No tag, publication or release approval is implied.

### Earlier B3j targeted checkpoint

B3j targeted verification: **287 passed, 2 Windows-only skips** (186 histogram
cases and 101 pure-core/cross-module contract/render checks). Ruff lint/format,
Pyright and generated schema/capabilities/reference sync pass. Python editor
PNG/SVG and Rust HTTP/PNG smoke cover step layer/stack; native paths, unchanged
weighted/statistical heights and reproducible PNG/PDF/SVG/RNG behavior pass.
The bars/step-density/horizontal-dodge/stacked-step-CDF preview was inspected.
Step+dodge/filled steps/poly/custom dashes are outside this subset. Full/minimum/
browser/TeX/distribution release gates were **not rerun for B3j**; versions and
release state are unchanged (package/editor 1.0.0, spec 0.1).

### Earlier B3i checkpoint

B3i targeted verification: **244 passed, 2 Windows-only skips** (143 histogram
cases, the dependency-free check and 100 cross-module contract/render tests).
Ruff lint/format, Pyright and generated schema/capabilities/reference sync pass.
Python editor PNG/SVG and Rust HTTP/PNG smoke cover both grouped modes;
same-environment PNG/PDF/SVG reproducibility and global RNG isolation pass.
The regenerated four-panel stack/layer/horizontal-dodge/CDF preview was inspected.
Full/minimum/browser/TeX/distribution release gates were **not rerun for B3i**;
package/editor remain 1.0.0 and spec 0.1. No release is authorized.

### Earlier B3h baseline (before B3i)

B0 verification: 675 tests passed; 16 explicitly skipped for TeX/Windows
platform conditions. Ruff, Pyright, schema sync and wheel/sdist checks passed.

B1a/B1b/B2a/B2b1/B2b2/B2b3/B2b4/B2b5/B2b6/B2b7/B2b8/B3a/B3b/B3c/B3d/B3e/B3f/B3g/B3h are wired into Python, actions/JSON, validation, registry,
renderer and the Python editor. The locked full suite passes **2159 tests, 2 skipped**
(Windows platform only; actual TeX matrix executed), including 11 real-browser tests. The minimum
Python 3.10 / NumPy 1.23 / Matplotlib 3.8 contract passes **1703 tests, zero
skips**. Ruff lint/format, Pyright, schema/capabilities/reference/gallery sync,
wheel/sdist rebuilding, dashboard build and Python editor smoke tests pass.
36 gallery entries and 61 editable specs are synchronized; the new weighted/
unit-CI, horizontal-SEM and stacked-percent preview was inspected. Numeric
reference formulas, private-RNG/chunk behavior, same-environment PNG/SVG output
and labels clearing real endpoints on positive/negative/horizontal/singleton
bars are tested. Box/violin add 69 tests for numeric summaries/geometry, empty/
missing/singleton cells, strict options, actions/schema/editor PNG, deterministic
notches without global RNG consumption and repeatable editable PNG/SVG output.
Two refreshed nested box/horizontal violin gallery previews were inspected.
Swarm adds 53 tests: circle/stroke clearance at real pixel transforms, DPI/resize/
limits/layout/positive-log changes, row preservation, joint hue packing and empty
slots, strict limits/controls, schema/actions/editor PNG and repeatable PNG/PDF/SVG.
Swarm gallery and three-panel combined-box overlay/horizontal/log previews were
inspected. Packing is greedy, not optimal; at most 2000 usable rows per layer.
Overcrowded rows remain at gutters, warning once above warn_thresh (default .05).
The minimum suite reports 3468 warnings (reported, not a warning-free claim).
Letter values add 106 tests: published depth equations, independent NumPy quantiles/
area widths, exact ties/finite extreme inputs, native band/median/tail geometry,
orders/empty slots/hue colours/hatches, strict controls, actions/schema/editor PNG,
byte-identical PNG/PDF/SVG and no global RNG changes. Full depth includes min/max.
Area widths use actual interval mass, including extended full-depth outer bands;
zero-height bands have zero width, all-constant cells fall back to exponential.
Gallery and three-panel exponential/horizontal-linear/full-area previews inspected.
Native/log adds 60 tests: numeric spacing and reserved physical positions, both
orientations, raw vs explicit axis-space quantiles/KDE, inverse-mapped native
artists, swarm pixel clearance/bounds/DPI/inversion, strict flags/positivity/shared
axes, JSON/actions/editor PNG and reproducible PNG/PDF/SVG without ambient RNG.
Three-panel numeric/log-native comparison inspected. Default stat_scale is data;
axis explicitly selects log10 summaries/KDE. Numeric native IDs exclude bool/date/
strings; the statistical native/log extension is documented below. Broader
semantic mappings remain unsupported.
Violin adds 138 tests for independent Gaussian equations/bandwidth/grid,
normalization scopes/counts/empty references, all inner/split/orientation/native
log geometry, exact observations, singular/missing cells, strict ignored controls/
row bounds, core-only builders, JSON/actions/schema/editor and reproducible exports.
Four-panel inner/global-count, split quartile/density, horizontal observations and
log-native/clipped sticks preview inspected. Area is a shared fitted-coordinate
KDE density scale, not an exact truncated polygon-area promise. Clip restricts
support only; fitting rows/counts/inner observations remain. Split requires two
selected/reserved hues, not arbitrary-hue split. Default median/width/cut0 stay.
Component styles add 48 tests: independent artist properties and exact unchanged
coordinates/statistics, both orientations/native logs, pure typed/dict builders,
old defaults/one-based positions, inherited hue/hatch/tints/empty slots, strict
nested shape/unknown key/role/size/hidden controls, schema/actions/editor PNG,
byte-identical PNG/PDF/SVG and no global RNG use. Four-panel default/styled box,
letter tiers and horizontal log-fit comparison inspected. No arbitrary kwargs,
precomputed bxp, per-band/per-hue style maps or bootstrap inference is added.
Statistical scales add 73 tests: numeric/log geometry and reserved slots/hues,
physical-order point gaps/primitive overlays, orientation/limits/true range marks,
independent raw/log SD/SEM/PI/CI and weighted/unit bootstrap equations, positive
raw baselines/body endpoints/label direction/stacked global count labels, strict
no-op/unsupported/unsafe scales and derived positive/inverse overflow guards,
pure builders/legacy specs, JSON/actions/schema/editor and byte-identical exports/
RNG. Four-panel native raw-SEM, log raw-PI, horizontal log-fit CI/positive baseline
and log-native stacked percentages inspected. Axis log supports mean/median/min/
max, not sum/count. Count stat_scale and value-log stacking remain unsupported;
primary-only new subset, legacy linear ordinal y2 preserved. No endpoint clipping.

Rust 1.99 format/Clippy/tests and real Python/HTTP/browser bridge now pass.
TeX Live 2026 + CI-pinned Tectonic 0.15.0 pass all four real-paper engine/
bibliography combinations; Windows tests resolve actual bundled Ghostscript.
User chose Rust 1.99 development with 1.88 MSRV verification retained as a final
release gate (not passed or dropped). B2b–B6 and global release gates remain open. Current 1.0.0 Python/Rust/changelog metadata still agrees; no version,
tag or publication changes. Next implementation batch: broader semantic/component
mappings or broader histogram/KDE variants and semantic controls in B3.
ECDF adds 103 tests: independent weighted indicator equations/normalized and raw
mass, ties/full minimum jump/right-continuity, complements preserving tiny tails,
per-curve rather than pooled denominators, missing/zero-weight rows/hue slots,
orientation/log/limits/constant/empty behavior, strict ignored/unsafe controls,
legacy/new JSON/actions/schema/editor, native Matplotlib path right limits and
same-environment PNG/PDF/SVG bytes/RNG. A 10000-case wide-weight probe exposed
one-ULP nonmonotonicity from rounded tie subtotals: online float expansion now
accumulates unrounded row weights, with permanent equation/monotonic regressions.
Matplotlib3.8 rejects zero-width scaled dashes, even with alpha0; zero-width ECDF
artists/proxies retain data/style/metadata and are invisible rather than drawn.
Count mass1e308 triggers one native ticker overflow warning in the locked
suite's extreme stress test; it is reported, not silenced or claimed warning-free. Four-panel ordinary/
weighted-percent/horizontal-log strict-tail/weighted-count preview inspected.
ECDF is not fitted/censored survival inference, does not infer intervals or
extend infinite tails, and supports primary2D/linear mass only (no date/y2).
Violin remains partial: no callable KDE, arbitrary inner kwargs,
arbitrary-hue split or broader size/style mappings.

Histogram adds 95 tests: independent weighted unequal-bin equations and NumPy
references, endpoint inclusion/out-of-range denominators, pooled vs separate
areas, integrated cumulative density (not sum of heights), missing/zero/selected
row pairs, pooled integer edges, empty/constant/hue slots, raw log geometry,
small-bin mass after huge weights, scaled normalization/prefix monotonicity,
strict controls/overflow/projection/shared ordinal rejection, legacy native
histograms/default alpha, typed JSON/actions/schema/editor and repeatable exports.
Four-panel weighted common/separate density, horizontal-log percentages and
binned CDF plus refreshed gallery inspected. Numeric bins/statistics are lazy
NumPy effects; core remains stdlib. No engine behavior change after full/minimum.

Univariate KDE adds 125 tests: native Gaussian covariance/density and independent
weighted effective-n/variance/PDF/CDF formulas, pooled/per-curve integrals/common
support, unchanged fit under clipping/no visible-tail renormalization, singular
mass/empty hue slots/paired rows, raw observation logs/reversed bounds, exact
line/fill alpha/width/outline/dash/hatches, extreme dominant/huge weights/neighbor
low bits/tiny-group CDF/scaled bandwidth products, bounded deterministic chunks
and CDF monotonicity, strict/derived errors, legacy equations/constant fallback,
tuple clip/typed JSON/actions/schema/editor/export/reference/RNG. Weighted and
bandwidth/CDF four-panel and updated KDE gallery inspected. NumPy remains a lazy
numeric effect; no SciPy/new dependency. Only explicit new options opt in; old calls
retain their fit. The previous univariate checkpoint passed full/minimum before
B3d; this KDE method still does not implement log-fit. Weighted violin is a
separate violin option. Bivariate is
separate below.

Bivariate KDE adds 129 module tests plus 1 registry-param case. Independent full
weighted matrix covariance/PDF and native 2D Gaussian, Scott=Silverman rule,
analytic isotropic HDR/convergence/ties/trapezoidal quadrature/grid-conditional
clip levels, shared mass/grid and unchanged fit, missing/zero pairing/singular
mass, native paths/fills/exact alpha/width/dash/hatch/legend proxies, extreme
anisotropic units/weights/neighbor low bits, bounded chunks/permutation, raw
logs/limits, strict/derived/rank failures, schema/JSON/actions/editor/exports.
35 gallery/55 canonical specs and weighted/correlated/pooled/clip/log four-panel
inspected. Full 1825/minimum 1370 pass with no engine changes after; no SciPy/
new dependencies. Limits: 10000 rows/256 nodes/axis/16 levels; finite-grid HDR is
approximate conditional mass, NOT confidence/full-space coverage. Rust/full
TeX were unverified at that checkpoint; see current toolchain results above.
MSRV and wider feature/release gates below remain open.

Weighted violin adds 78 tests: independent covariance/effective-n/PDF, unchanged
clipped fit/row pairing, inverse-ECDF ties/quantiles and weighted mean, row vs mass
widths/singular references, huge weight totals/dominance/neighbor low bits/bounded
actual chunks, both orientations/split/native logs/style, old defaults/schema/
actions/Python and Rust editor/exports/RNG.56canonical specs/35gallery entries,
4-panel weighted/unweighted/count/log example inspected. Full1923/2Windows skips/
1preexisting ticker warning and minimum1468/0skips/3292warnings pass. Rust1.99
format/Clippy/11tests(1ignored subprocess helper exercised indirectly) and real
browser/HTTP/Python/weighted editor smoke pass. Fixed old28registry guard, stale
CI dashboard command and Windows process-tree cleanup. No new dependencies,
versions or release; no engine changes after final full/minimum verification.

Lineplot adds66tests +1registry case: independent numeric-x estimates, SD/SEM/
PI/seeded pointwise CI and within-x hierarchical weighted/unit bootstrap, real
line/band/bar paths, local order/sorting, missing-bounds honesty, data/axis-log
coordinates/invalid endpoints, exact alpha/zero-stroke exports, strict ignored/
unsupported contracts, core/old JSON/actions/Python/Rust editor and RNG. Raw
line stays raw.36gallery/58canonical specs and raw/weighted/log3-panel inspected.
Full1990/2Windows skips/1preexisting warning670.02s; minimum1534/0skips/3324warnings
531.80s. Rust1.99 format/Clippy/11tests+real browser/HTTP/bridge and actual TeX
matrix pass,1.88MSRV still final gate. No new dependencies/version/release and
no engine changes after final verification. Pointwise bands do NOT imply
simultaneous coverage or whole-curve resampling; unmeasured-x lines are display
interpolation. Broader semantic/date/y2/callable/curve inference remains open.

Scatter semantics adds85tests: independent categorical/numeric hue and size,
style markers, global auto/explicit linear bounds, clipped mapping not rows,
diameter-to-native-area conversion, constant/subnormal single guides, extreme/
neighbor normalization, positive-area underflow, ordered reserved slots/no ghost
data or labels, listwise masking/log checks, exact native offsets/styles/alpha,
strict conflicts/types/JSON, Python/Rust editor/export/RNG and legacy behavior.
Role guide proxies are non-data, never grow data limits.36gallery/59canonical
specs and4-panel category/numeric/global/order/log comparison inspected. Full2075/
2Windows skips/1preexisting warning659.71s, minimum1619/0skips/3348warnings539.80s.
Rust1.99 format/Clippy/11tests+real browser/HTTP/JSON/semantic scatter/export pass.
No dependency/version/release or engine change after final checks. Line/facet/
colourbar/outline/date/y2 semantics and MSRV/final release gates remain planned.

Named scatter scales add36tests: union domains despite missing coordinates,
categorical/numeric colours/diameters/marker order, independent names, stable
original row order/deduplication, legacy palette isolation, one pooled guide block
per panel and separate labels, legend suppression, invalid IDs/settings/cmaps/
boolean order/pooled limits/ambiguous labels, constants/subnormals, old JSON/
core/editor/export/RNG. Full2111/2Windows skips/1preexisting warning719.67s and
minimum1655/0skips/3348warnings596.76s pass; Rust1.99 real browser/HTTP/JSON/shared
scale/vector smoke passes.36gallery/60canonical specs and local/shared4-panel
inspected. No engine change after verifier launch (mtime/receipt checked); a
second launcher safely refused duplication of existing jobs. Both terminal
receipts exit0. No dependencies/version/release or automatic facet/line semantic
claim;1.88MSRV and wider gates remain open.

Line semantics B3h adds48tests for independent raw tuples/per-predictor cells,
physical stroke widths/markers/dashes, clip-without-merge, paired role/weight/unit
selection, independent SD band endpoints/v-h/log-fit, per-cell weighted/unit CI,
zero native strokes, strict config/limits/types, shared geometry-specific guides/
references and core/JSON/editor/exports/RNG. Three-panel synthetic example inspected.
User-approved foreground rechecks on unchanged sources: full2159/2Windows skips/
1preexisting warning699.96s, minimum1703/0skips/3468warnings573.59s. Both exit0 and
source hashes unchanged; v11-b3h-recheck-{full,minimum}-status.json consumed. Earlier
orphaned running receipts/partial logs preserved, not retroactively passed; cause
unconfirmed. Source/API/core/minimums/version unchanged; automatic facets and
remaining workflows/MSRV/final release gates stay open.

## Release gates

- [ ] Feature/option/statistical gaps accurately updated in the coverage audit.
- [ ] Batches and any remaining partial/deferred scope reviewed explicitly.
- [ ] Python/CLI/JSON/editor paths and old-spec migration/defaults verified.
- [ ] Numeric/artist/browser/reference and same-environment export tests pass.
- [ ] Minimum supported and locked environments, Rust and full TeX matrix pass.
- [ ] Ruff/Pyright/generated contracts and clean distribution checks pass.
- [ ] English/Korean docs, runnable previews and Unreleased changelog current.
- [ ] Only then synchronize 1.1.0 package/editor/release metadata; do not rewrite
  existing tags/assets or publish without the owner's release instruction.
