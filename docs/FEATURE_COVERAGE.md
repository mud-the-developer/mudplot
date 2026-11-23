# Matplotlib / Seaborn feature coverage

*[한국어 / Korean](FEATURE_COVERAGE.ko.md)*

## Goal and audit scope

The product goal is to cover the plotting and statistical workflows available
in Matplotlib and Seaborn, with consistent publication styling, editable specs,
and reproducible output. **A plot name in the registry is not feature parity.**

This is the preserved **1.1.0 local-candidate** feature baseline, including its
Unreleased statistical/native subsets and agent-facing quality work. v2 scope,
acceptance and progress are tracked in [V2_SCOPE.md](V2_SCOPE.md); an unimplemented
v2 row is not support in this table. Reference interfaces are the official
Seaborn **0.13.2** and Matplotlib **3.11.2** documentation linked below. These
are comparison references, not automatic dependency upgrades. The scoped v1.1
security exception uses Python >=3.11 / Matplotlib >=3.8 / NumPy >=1.23.5 and
Pillow >=13.0.0 for rendering; Python API/JSON/default-render contracts remain.

Source of truth:

- [Layer registry and supported fields](../mudplot/capabilities.py)
- [Serializable layer / figure model](../mudplot/spec.py)
- [Public builders](../mudplot/api.py)
- [Rendering](../mudplot/_render.py) and [shared statistics](../mudplot/_estimate.py)
- [Compatibility policy](COMPATIBILITY.md)

Status vocabulary:

- **Partial**: related marks or workflows exist, but important upstream
  options, estimation, or composition are absent. This is not full parity.
- **Missing**: no dedicated declarative workflow. Manual preprocessing,
  composition, or a native Matplotlib call is not counted as implementation.
- **Python-native**: available through the returned Matplotlib Figure/Axes,
  but absent from the saved spec, action history, CLI and editor round-trip.

The current engine has **41 layer types**, including the bounded native
stem/stairs/eventplot/broken_barh subset. There is deliberately no invented
coverage percentage: a denominator must include options and semantics, not
just function names. The matrices below identify the major gaps, not every
argument in every upstream signature.

## 1. Seaborn function interface

| Upstream workflow | mudplot today | Important gaps |
| --- | --- | --- |
| `scatterplot` | Partial: independent hue/size/style, pooled domains, explicit numeric-hue colourbars/exact constants, finite point-unit outlines, existing temporal paths | Wider F01 family sharing/adapters and full frozen qualification remain required; not full upstream equivalence |
| `lineplot` | Declared complete-unit percentile / finite-grid max-deviation curve or layer families; native numeric/real-clock/categorical and v/h/y2; raw supplied hue/size/style, gaps, saved/live facets and scale_id-owned figure guides | Nominal selected-grid bootstrap only; extrema empirical envelopes, no continuum/population coverage or full upstream parity. Broader F01/F02/G01 remain separate |
| `histplot` | Explicit weighted univariate statistics plus paired Histogram2DSpec/BivariateBinsSpec: six cell statistics, nonuniform true edges, in-bin normalization and same pre-tally-cohort full KDE; legacy routes retained | Raw/day-coordinate widths/areas; no count-height KDE rescaling. [Scientific/resource contract](DENSITY_FIELDS.md); final coherent-artifact qualification remains separate |
| `kdeplot` | Named Gaussian/product-Epanechnikov H, shared-grid 1D layer/stack/fill, true joint CDF and explicit bounded full-model HDR alongside retained conditional-grid HDR; actual v/h/y2/clocks and declared log10 fit/Jacobian units | No radial-kernel fiction, 2D stack ordinate, arbitrary callbacks or universal/source-population guarantee. [Full contract](DENSITY_FIELDS.md); broader/final qualification remains separate |
| `ecdfplot` | Weighted/tied right-continuous proportion/percent/count, strict complement and raw roles/real-knot glyphs; explicit paired ecdf2d retains all knots and strict OR complement, actual v/h/y2/clocks | Finite saved/query bounds do not rebase denominators; no survival/censoring/inference. [Contract](DENSITY_FIELDS.md); final product qualification remains separate |
| `rugplot` | D07 implemented: x/y/y2 rugs, axes-fraction height, v/h, observation dates/logs, grouping/facets and shared raw-row hue/stroke/dash semantics | Existing semantic/resource bounds and finite named dash contract; no weight/inference/point-marker reinterpretation. Final frozen-product qualification remains separate |
| `stripplot` | Partial: accepted C01 category × hue order/dodge/native/log/date/jitter and independent shared hue/size/style adapter | C01 bounded acceptance stays closed; broader F01 families and final product qualification remain required |
| `swarmplot` | C02 implemented: real named glyphs, shared hue/size/style, date/native/log/v-h/y2, explicit compatible cross-layer scopes and live-template transactions | Layer maximum 2000 unchanged; new panel/scope maximum4000 physical instances, conservative glyph/stroke packing and truthful crowding; full qualification is separately evidenced |
| `boxplot` / `bxp` | C03 implemented: raw median bootstrap CI, column-reference summaries, final-body cap fractions, typed per-hue components, shared hue/body-stroke/flier-style, date/native/log/v-h/y2/facet/live | Available-only supplied means/CI/fliers; no reconstruction/bootstrap from quartiles or arbitrary kwargs. Advanced bounds:256 drawn cells,10000 source rows AND10000 declared flier values. [Full contract](BOX_WORKFLOW.md); qualification is separately evidenced |
| `violinplot` | C04 implementation: explicit paired multi-hue halves, native mode-specific/per-raw-hue components, weighted Gaussian/inner/mass normalization, shared hue/BODY-stroke/style, date/native/log/v-h/y2/facet/live | [Finite scientific/ownership contract](VIOLIN_WORKFLOW.md); no callbacks/arbitrary kernels/kwargs/new nonlinear statistics. Advanced10000 selected rows/256 drawn profiles; categorical64, not continuous-value64. Full qualification is separately evidenced |
| `boxenplot` | Declared C05: LEFT relative-weight quantiles, exact empirical band/tail mass, Kish depth, rank/side/raw-hue components, BODY hue/stroke/dash + actual flier mappings, clock/native/log/y2/live/N13 views | No CI/KDE/replicated-weight estimator, arbitrary kwargs or depth increase; named/explicit depth<=32 and finite source/effect work admission |
| `pointplot` | Declared C07: finite weighted methods, exact LEFT PI, canonical moments/arithmetic, typed raw hue/marker-diameter/style, actual date/native/log/v-h/y2, selected shared domains and explicit live edits | Mean-only SE, no count intervals, no axis-log/calendar sum/count or inferred nonlinear statistics; NEW-only resource guards, old dense-line/weight/unit admission retained. [Contract](STATISTICAL_WORKFLOW.md) |
| `barplot` | Declared C07: weighted quantities/paired CI, exact percent PI, BODY-stroke/style mappings, date/native/log/v-h/y2 and live transactions; precomputed `bar` remains separate | Width/height/mass are not semantic SIZE; positive log baseline, canonical-day NEW calendar baseline, finite methods/owned conflicts and actual work admission. [Contract](STATISTICAL_WORKFLOW.md) |
| `countplot` | Partial: global counts/proportions/percent, native/log category spacing, explicit log-value baseline, orientation/gaps/linear stacks/labels | Weighted counts, log-value stacking/stat_scale and wider normalization/semantic/date |
| `regplot` | Declared weighted paired-case percentile inference for all five models, full-basis/joint/two-stage partial fits, independent fit/scatter point-unit controls and explicit source-aligned query predictions | Nominal pointwise mean/operator uncertainty only; no precision/frequency/simultaneous/prediction-interval method or broader F01/F02/G01 claim; [scientific/API/resource scope](REGRESSION.md) |
| `residplot` | Existing residual flag with actual raw or mathematical binary deviance diagnostics, mapped mean-confidence sets and independently owned FULL-pipeline trend; original row identities retained | No clipped infinite diagnostics, fixed-fit trend, implicit hold-out split, causal claim or calendar-duration formatter; [scope](REGRESSION.md) |
| `heatmap` | Masks, independent custom text, rotations, square cells, linear/log/center/robust plus symlog/clipped-power/discrete norms and editable colourbar geometry/ticks | Finite scalar matrices and linear cell indices; P01 display can replace, not combine with, M01 colour calibration; [typed scope](HEATMAP.md) |
| `clustermap` | Hierarchical row/column trees, complete-feature missingness, explicit condensed distances, aligned categorical tracks/legends and editable original-ID subtree cuts | Optional SciPy; no implicit imputation, arbitrary callbacks, continuous track bins, or shared/secondary axes; [scope](CLUSTERMAP.md) |
| `relplot`, `displot`, `catplot`, `lmplot` | Finite builders over existing mark/actions, live templates, cell-local inference and eligible raw/semantic/scalar figure guides | No arbitrary mapping callbacks or full upstream parity; [supported kinds](FACETS.md) |
| `FacetGrid` | Materialized selectors, explicit live templates, reserved cells, shared axes and nested placements | Not an arbitrary reactive map; see [facet limits](FACETS.md) |
| `PairGrid` / `pairplot` | Square or lower corner, scatter with typed histogram/KDE/ECDF diagonals, weighted original-row cohorts, shared semantic scopes and nested N13 layout | No upstream object parity; exact scope and applicability: [pair grids](PAIR_GRID.md) |
| `JointGrid` / `jointplot` | Paired weighted histogram/KDE/ECDF, scalar c or typed semantic scatter, grouped binned fields, true linked measurement y2, and nested N13 layout | One Cartesian center and its matched marginals; see [joint grids](JOINT_GRID.md) for supported roles |
| Themes, palettes, legend/despine utilities | Named themes and typography contexts, LCH and authored categorical palettes, legend columns/native handler presets and despine controls | No arbitrary callbacks, upstream global registry changes, or unrestricted options |
| `seaborn.objects` | Finite named [coordinate/statistic/move/scale composition](COORDINATE_PIPELINE.md) | No drop-in object API; source qualification is tracked separately |

Seaborn's deprecated `distplot`, online example-dataset downloads, notebook
palette widgets and global-state aliases are not prerequisites for plotting
parity. They must not inflate or conceal the graph/statistics coverage count.

### Independent lineplot semantics

Strict same SemanticSpec/column-keyword path partitions raw role tuples per
curve/predictor cell; numerical clipping never pools distinct curves. Shared
estimators/pointwise intervals/weighted-unit CI preserved, no whole-path inference.
Sizes map main stroke widths in points, not marker areas/uncertainty magnitude;
unique filled markers and optional distinct named dashes, no ignored overrides.
Listwise role/stat missing/zero rows, v/h/sort/raw/log-fit/band breaks preserved.
Shared IDs also include line/scatter domains with per-geometry guides; non-data
proxies retain labels/limits.10000rows/256raw curves/64levels/enough glyphs/dashes.
48equation/geometry/bootstrap/strict/type/core/editor/JSON/export/RNG cases.
Raw-line mappings and wider inference/combinations remain planned. Explicit F02
clocks, numeric-hue colourbars and documented automatic facet materialization are
supported separately; see [FACETS](FACETS.md) and the F01 increment below.
[Executable comparison](../examples/line_semantics.py).

### Named figure-shared scatter scales

SemanticSpec.scale_id names a figure scope; None keeps layer-local behavior.
Pool unique selected row IDs from compatible members in original table order,
not duplicated observations. Roles/kinds/orders/bounds/sizes/markers and numeric
hue cmap must match; legend may differ. Missing panel coordinates do not reset
hue slots or size/marker/numeric domains. Independent names keep own domains.
One reserved categorical colour block per name precedes legacy entries. Shared
non-data guides describe pooled categories/calibration and appear once per
panel while dataset labels remain separate. Pool row/level/marker limits and
cross-member ambiguous labels are validated, not hidden by per-layer checks.
36tests cover numeric/categorical maps, masks/union/order/dedup, limits/cmap/type
conflicts, legacy palette isolation, legend rules/constants/subnormals, old
JSON/core/editor/exports/RNG. [Automatic facet materialization](FACETS.md) is now
supported separately; line extension is described above.
[Executable comparison](../examples/shared_semantics.py).

### Independent scatter semantics subset

SemanticSpec/dict or hue/size/style keywords opt in; old calls unchanged. Hue
categorical default/numeric explicit, size numeric default/categorical explicit,
style always categorical with distinct filled named markers. Orders select/
reserve; missing rows drop listwise before numeric/log checks. Bool/numeric
categories distinct; ambiguous label strings reject. All selected rows share
linear bounds, explicit bounds clip mapping not observations/per-style scaling.
Diameters interpolate in points then square to native areas; exact zero retains
invisible rows, positive area underflow fails. Constants/subnormals use midpoint
and one guide; scaled differences keep extreme/neighbor low bits. Role labels
separate observed category entries and numeric calibration guides; proxies add
no data limits or fake observations. Global references require explicit label.
Limits remain 10000 rows/64 levels/enough markers, with documented temporal/y2
restrictions and no legacy group/c/scalar-role conflicts. Explicit numeric-hue
colourbars and outlines are described below; wider family adapters stay required.
The original 85-case subset receipt remains historical, not whole-F01 acceptance.
[Executable comparison](../examples/scatter_semantics.py).

### Supplied and estimated lines

Inherited omitted/predictor-only lineplot calls retain C07 per-cell pointwise
percentile behavior, including unit-then-row draws and binary64 replicate/tail
boundaries. Explicit `LineSpec(resampling="unit")` instead repeats complete
original trajectories and paired masses. Percentile is pointwise;
max_deviation calibrates the exact upper empirical maximum over a finite curve
or selected-layer family, independently of bars/ribbons. Min/max complete-unit
results are empirical nonregular envelopes under both calibrations.

Numeric/date native grids belong to each raw curve before response omission,
plus explicit reservations; categorical predictors use pooled typed ordinal
slots. Actual primary/y2 and v/h routes preserve native spacing and grouped
gaps. Supplied raw lines retain source order/duplicates/barriers and map actual
physical stroke/marker traits without estimating. Figure guides use one stored
scale_id membership and distinguish actual named native effect contexts.
[Scientific/API/resource contract](LINE_WORKFLOW.md) ·
[Runnable synthetic examples](../examples/line_workflow.py).

### Paired fields, true cumulative laws and full-model HDR

`hist2d` accepts strict `Histogram2DSpec` and unambiguous logical x/y
`BivariateBinsSpec`. Count/frequency/probability/proportion/percent/density use
paired in-bin mass and true raw/day cell areas, never log-display areas.
The optional KDE consumes the same selected **pre-tally** paired cohort, including
out-of-bin observations; its actual full-fit density/CDF is not rescaled to counts.
Statistic mappables/raw values/colourbars remain distinct from semantic hue bars.

`kde2d` retains weighted full covariance and physical Kish/Scott/Silverman meaning.
Gaussian and Cholesky product-Epanechnikov are explicit; the latter is not radial.
True original-law joint CDF, absolute density levels, actual primary/y2/v-h/clocks
and declared log10-fit/Jacobian units do not infer unsupported nonlinear statistics.
Without `HDRSpec`, mass levels retain the existing finite-grid conditional HDR.
Explicit full mode instead calibrates all unknown ordered cutoffs against the
fitted law and emits disjoint earliest-band guaranteed-inside native cell unions.
Target, HDR-set symmetric difference, source/transform, native and visible-clipping
errors stay separate. Visible probability is not called the requested target p.
These finite IEEE/computed-model enclosures are not universal source-population
guarantees or smooth-contour/publication-QA claims.

`ecdf2d` uses literal proportion/percent/count and preserves every interior source
knot/query. The lower orthant is AND; its strict complement is OR, not joint
survival. Bounds/queries never remove denominator rows. Canonical masses precede
ties and final rounding, including percent units and strict right tails.

All NEW field work shares one figure-wide 2B composite/256MiB/1M-live-pair-scalar/
2M-native-vertex allowance; existing legacy and D01/C07 guards remain separate.
No reduced tolerance, missing level, partial state/output or conditional fallback
substitutes for a failed request.
[Scientific/API/resource contract](DENSITY_FIELDS.md) ·
[Executable whole workflow](../examples/density_fields.py).
Final installed/DOM/coherent-artifact qualification remains a distinct gate.

### Weighted univariate kernels and composition

Omitted `kde` calls retain the old unweighted1.06*sample-SD*n**(-1/5),
200-point/constant fallback. Explicit KDESpec options use paired relative mass,
unbiased physical-row covariance/Kish size, Scott/Silverman or finite scalar H.
Cut/clip changes evaluation only. Singular tuples warn/skip without jitter.
Common normalization uses effective hue or global pools, not each size/style tuple.

Named Gaussian and variance-one product-Epanechnikov support shared-grid
`layer`/`stack`/`fill`. Stack adds contributions; cumulative stack/fill remains
labelled contribution/composition, not a population CDF. True-zero compact support
remains a gap. Actual v/h/y2/clocks and explicit log10-fit data/fit density units
are supported; arbitrary kernels/callbacks or inferred symlog/asinh/logit fits are
not. SIZE is real stroke points and no fake field point glyph is introduced.
[Full contract](DENSITY_FIELDS.md) ·
[Retained Gaussian comparison](../examples/kde_semantics.py).

### Weighted histogram first subset

New hist options store strict HistogramSpec; None keeps old density/group/bin/
alpha effects. Six names: count=mass, frequency=mass/raw-width, probability/
proportion=mass/denominator, percent=100*proportion, density=mass/(denominator*
raw-width). Only included in-bin mass normalizes: pooled selected hues with
common_norm=True, per curve otherwise. Bin membership is half-open except the
closed final edge. Integer equal-width bins pool usable rows; explicit edges
share physical raw widths. Drop missing required/zero-weight rows, require
finite non-bool observations and nonnegative weights; preserve row pairing.

Cumulative density INTEGRATES mass, not sums heights; cumulative frequency is
unsupported. Shared cumulative endpoints are group shares, separate endpoints
1/100. Scaled normalized weights and independent bin sums retain small masses;
unrounded row prefix expansion keeps cumulative values monotone. Raw curve
mass/derived widths/heights must be finite. Empty curves have no bars/legend;
hue order reserves colors/hatches/dashes. Cartesian2D bars/steps support v/h,
positive observation logs, explicit date clocks and vertical-only y2 mass.
Widths remain raw even on logs; height axes are linear. Exact alpha/edge/width
and reference metadata. Multiple='layer' overlays full bins; grouped 'stack'
adds heights in hue order, 'dodge' splits raw bin width across ALL selected hue
slots (including empty/outside-support hues). Heights, normalization and cumulative
semantics are unchanged. Density/frequency still use original bin widths, so
dodging reduces rectangle area without height correction. Separate-normalized
stacks sum the original per-curve distributions, not a renormalized pooled fit.
Nonfinite/lost positive stack increments and collapsed dodge slots fail before
any artists. Element='step' adds one native stairs patch per observed
hue: layer closes to zero, stack outlines absolute top and previous baseline.
Edges/heights/statistics stay unchanged; empty hues reserve color/theme dashes,
edge_color overrides the stroke, exact alpha/width include zero. Dodge places
unchanged heights in their raw hue slots with zero-baseline geometry gaps, not
new observations or mass. Fill=None keeps filled bars/unfilled steps and is
omitted from old JSON; explicit True/False changes geometry only. Filled steps
use group facecolors/hatches; outlines use group-colored strokes/theme dashes
without hatches. Multiple=fill divides existing stat/common_norm/cumulative heights
by their bin-group sum; empty bins stay zero. The result is dimensionless
composition, not a raw-mass override. Cumulative fill is not a CDF and may decrease.
Poly connects raw-bin/slot centers with native straight lines or filled areas,
requires at least two representable centers, retains raw-bin/zero response bounds
and does not fit or jitter observations. None defaults to a line; True fills.
[Mode example](../examples/histogram_modes.py). This univariate HistogramSpec does
not attach KDE/bivariate/interval/callback controls; paired statistics and a
same-cohort KDE use Histogram2DSpec above. In-range normalization remains explicit.
[Executable comparison](../examples/histogram_statistics.py).

### ECDF first subset

Dedicated `ecdf` stores raw data and strict `ECDFSpec` (stat, complementary,
weights). Right-continuous F(t)=sum(w for X<=t)/sum(w) uses per-curve totals;
percent is 100*F, count sums weights (rows without weights). Complement is
strict X>t, not >= or a survival/censoring estimator. Aggregate tied knots into
full jumps; v uses post steps, h swaps coordinates/pre steps with x still the
observation column. Finite observed support/full min jump, no synthetic infinity
or tail extension. Independent indicator-sum equations and native Matplotlib
path right limits are tested; not complete upstream numerical equivalence.

Drop missing x/group/weights and zero-weight rows before positive-log checks.
Finite numeric values/weights exclude bool, weights nonnegative. Normalized
mass uses canonical dyadic source/row masses before tie aggregation and final
float conversion; percent combines its unit first and strict tails retain exact
right mass. Raw count-mass overflow still fails per curve. Empty hues have no
artist/legend; explicit hue order reserves shared colors/dashes. Actual Cartesian
v/h primary/y2 observation clocks, positive observation log/linear mass, real-knot
markers and independent raw roles are supported. Explicit paired cumulative
fields use ecdf2d above. No inferred interval/censoring/Kaplan-Meier/KDE or callbacks.
[Executable example](../examples/ecdf_semantics.py),
[Matplotlib reference](https://matplotlib.org/3.8.0/api/_as_gen/matplotlib.axes.Axes.ecdf.html),
[Seaborn reference](https://seaborn.pydata.org/generated/seaborn.ecdfplot.html).

### Shared statistics: first v1.1 subset

The existing `.bar()` remains a primitive for **precomputed values**. New
`barplot`, `pointplot`, and `countplot` builders store raw observations and a
plain `StatSpec`; a shared NumPy effect computes results when rendering.
Named estimators are mean/median/sum/min/max/count. Intervals support SD,
sample-mean SEM, observation percentiles, and seeded percentile-bootstrap CI.
Count estimates have no intervals; SEM is only a mean interval in the chosen
statistic coordinates (default raw arithmetic; explicit log mean below).
Bootstrap uniformly resamples paired original cases, never probability-weighted
rows or unit means. Weighted mean supports SD/SE/PI/CI; observed LEFT median/
min/max support SD/PI/CI; weighted total supports CI and count mass no intervals.
SD/SE use canonical reliability variance/physical-row Kish. NEW weighted PI uses
exact canonical percent targets, not premature binary tail subtraction. Missing/
zero rows drop pairwise; insufficient observations/units omit intervals honestly.
`order`/`hue_order` select and reserve categorical slots. Horizontal geometry,
bar gap/value labels, normalized and stacked counts are supported on linear axes.
The count denominator is all usable selected rows across categories and hues.
This is finite declared functionality, not complete Seaborn equivalence.
[C07 contract](STATISTICAL_WORKFLOW.md) covers main physical mark units, typed
source identities, canonical cancellation/endpoint repairs and NEW-only
10000row/256pointwise-cell/2Bactual-work guards with1M active chunks. Old weighted/
unit/plain or existing semantic dense-line routes receive no new cap merely
from those fields; no prefix CI, hidden truncation, SLA or RSS promise.

### Statistical native/log subset

Bar/point/count opt into finite numeric category locations with native_scale=True.
Order selects/reserves physical positions; widths/point dodge use minimum spacing
in declared axis coordinates (log10 on native logs; singleton1). Native bar width
is (0,1], point dodge [0,1]. Empty point cells break lines, not arbitrary physical
separation. Empty hue/color slots and shared-axis conflicts remain explicit.

Stat_scale='data' retains raw estimates on log value axes. Explicit 'axis' fits
mean/median/min/max and SD/SEM/PI/CI in log10 then inverse-maps endpoints; weights/
units retain original row pairing. Log sum/count are rejected, not products/powers.
Positive observations are required after selection, except counts do not log-fit.
Nonpositive computed bounds/inverse overflow fail before artists, not clipped.

Nonstack bar/count baseline is a finite raw value (linear default0), explicitly
positive on log values. Body ends at estimate, not baseline+estimate; label shows
estimate and clears real interval endpoint according to direction from baseline.
C06 stacks retain explicit positive log baselines/cumulative tops and unchanged
normalization scopes. Bar/point now have actual declared primary/y2/v-h/date/
native/log paths; line/count keep their separate target subsets. No inferred
nonlinear statistic, arbitrary callable or overall parity promise.
[Executable C07 workflow](../examples/statistical_workflow.py).

Required statistical distinctions:

- SD describes observation spread; SE describes estimator uncertainty.
- A percentile interval (PI) covers observations; a bootstrap CI is an
  interval over resampled estimates. Neither is generally `1.96 * SD`.
- Store estimator, method, level, bootstrap count and seed explicitly.
  Missing-value handling, sample SD (`ddof`), single-observation/empty groups,
  weights and repeated-measure resampling need documented semantics and tests.
- The current absolute bar/errorbar bounds must contain the central value.
  A general percentile interval need not contain the selected estimate;
  statistical range marks now represent that honestly without clipping or
  silently treating endpoints as positive error magnitudes.
- NumPy's current KDE and the normal-approximation regression band are
  limited algorithms, not proofs of equality to Seaborn's estimators.

### Swarm first subset

`swarmplot(category, value, group=hue)` defaults to uniform circles in display space
on every draw, not seeded jitter. Marker/stroke size, DPI, current limits and
layout, horizontal orientation and positive log-value transforms are tested.
Values remain exact; orders reserve empty slots and non-dodged hues pack jointly.
Packing is stable greedy O(n^2 log n), bounded to 2000 usable rows/layer. It is
not an optimal packing solver. Explicit compatible `pack_scope` members now pack
together once per axes draw; unnamed layers remain independent. The new operation
bound is4000 physical instances per panel/scope, with duplicate drawn rows counted
separately. Crowded/oversized rows remain at gutters with possible overlap.
Default warn_thresh=.05 warns once per collection. Named native glyphs, independent
hue/size/style, real dates, positive logs and applicable v/h/y2 use original data.

`semantics={"size": "mass"}` retains the numeric/categorical size-only workflow,
including legacy groups; size is nominal diameter points, never mass/weight.
Missing required roles drop jointly and norms clip mapping, not rows.
Compatible mixed-family mapping IDs share deduplicated source-row domains with
scatter/lineplot/strip/ECDF/rug; units remain mark-specific diameter versus stroke.
[Complete scopes/live-grid contract](SWARM_FACETS.md),
[numeric size](SWARM_SIZE.md), [shared domains](SWARM_SHARED_SIZE.md).
Categorical size uses stable observed/explicit level ranks, with size_order row
selection/reserved sizes and observed-only guides. Bool/numeric keys remain
distinct; at most64 unambiguous labels. [Categorical scope](SWARM_CATEGORICAL_SIZE.md).

Native edits on the returned Matplotlib collection may use `set_sizes` (areas in
pt²) and linewidth arrays (pt). Packing then uses pairwise radius sums and each
point's own gutter allowance at actual DPI/layout/scales. Nonempty finite
nonnegative arrays up to the retained row count are supported; shorter arrays
cycle, longer arrays reject rather than inventing marks. Nonrepresentable packing
geometry rejects before changing offsets. Oversized/colliding rows remain and
are counted once, with the existing warn-once policy. These are artist-only edits:
they do not alter LayerSpec or JSON. The separate numeric SemanticSpec mapping
above is the declarative path for serializable size-column semantics.

### Letter values: declared weighted C05 workflow

Unweighted `boxenplot` retains type7 (now one correctly rounded interpolation).
Explicit weights use the LEFT inverse empirical CDF: exact cumulative equality
returns the observed value, never an inter-value midpoint. Relative weights are
not replicated rows; explicit equal weights may differ from no-weight type7.
Unweighted tails compare canonical rows to FINAL correctly-rounded numeric
bounds; weighted LEFT tails use exact observed canonical bounds. Pre-rounding
band metadata diagnoses positive-span native precision collapse, not another
type7 tail/area estimator. Requested strict-tail ordering may fail clearly if
binary64 cannot show it; hidden unrequested tails do not fabricate nonconstancy.
No epsilon/rescaling/blanket large-int ban is used.

Physical-row Kish n_eff replaces n in the four named stopping formulas as a
declared NON-CI concentration heuristic. Tie splitting can change n_eff/depth;
integer k and cap32 stay fixed. Weighted area uses empirical `[low,high)`,
LAST right-closed masses; internal duplicate edges are empty, last zero-height
may own an atom, and band+strict-tail mass is exactly1. Constant geometry never
invents dispersion/density; positive unrepresentable geometry rejects.

`BoxenSpec`, `BoxenBandComponentsSpec` and `BoxenHueComponentsSpec` are strict,
append-only/omit-none models. Central rank0 and outward lower/upper ranks1..31
survive named-depth changes. Typed raw hue keys (bool!=number) and fieldwise
layer→hue→band→hue-band precedence control real ordered polygon traits.
Semantic HUE owns actual body fill with NO mapped-tail retint; size owns BODY
outline points, style BODY dash and actual observed FLIER glyphs. No fake glyph
guides when no glyph exists. Source selectors, tuple cells, shared domains,
component traits/no-line handling and native coordinate inversion are reused
from C03/C04, not another mapper/KDE layer. Selected missing/zero/invalid-weight
policy, original row order/IDs and full positive strict-tail instances are retained.
Compatible shared raw size domains also work across boxen/scatter/line and
accepted C04 families: normalize deduplicated original rows once, then retain
BODY stroke, point diameter and curve stroke units and separate visible guides.
Physical repeated Boxen views still count every requested cell/flier instance.
Scalar and flier components share registered legacy+/x/. and richer P/X/p/h/8;
the filled-only semantic style cycle remains a different unchanged contract.


Primary/y2, v/h, numeric/native/date/log, linear value clocks, data/log-axis
statistics, saved/live cells and N13 nested/inset views share public declarations.
Weights cannot be declared clock coordinates; unsupported nonlinear axis-space
statistics reject. Source validity does not compute a fit: options/refs/types/
selected rows/cells/static rank availability remain pure. Once-only render
preparation admits ACTUAL band/flier work before native allocation.
NEW advanced bounds:10000 selected positive physical instances/256 drawn cells
per layer;32768 actual band polygons and1000000 requested flier instances per
figure, including repeated uses/transparent or marker-none requests. Hidden
unrequested flier artists may be omitted, not summary tails. No aggregate source
row cap, sampling, dropping, SLA/RAM or marker-size promise. Legacy admission and
depth32/figure256panels/1024layers/40Mpixels remain.

Both editors populate collapsed full `ReplaceLayer` action JSON: existing
nonbool integer panel/layer indices only, authoritative replacement without
reordering/count/data/recipe changes. Normal preview success precedes commit;
invalid requests retain spec/PNG/history, undo/redo/reopen work, and explicit
whole-template replacement still supersedes local cells. This is not an overall
v2/REL01 completion claim. See [full policy](REFERENCE.md#letter-value-distributions),
[weighted executable](../examples/weighted_letter_values.py) and
[unweighted comparison](../examples/letter_value_categories.py).

### Box/violin categorical subset

One-column `.box(value, group=category)` / `.violin(value, group=category)`
retain native one-based positions. Adding y opts into category x/value y with
group-as-hue nesting; orientation does not change argument roles. Required
missing rows drop listwise and orders reserve empty slots without invented marks.
Numeric dodge is the total hue-offset span (None auto, 0 overlays); gap shrinks
allocated body width. Whiskers follow native IQR/percentile observed-endpoint
rules, not CIs; omitted-bootstrap notches retain native Gaussian approximation.
Violins use native Gaussian KDE, per-violin widths and observed min/max extent.
C03 adds the explicit box workflow below without claiming full upstream
semantics or changing unsupported combinations for other distributions.

### Independent box/boxen component subset

Typed named body/whisker/cap/median/mean/flier styles for box, only body/median/
flier for boxen. Missing properties inherit native/layer/hue defaults; component
properties override shorthand without changing observations/statistics/geometry.
Body color replaces the base hue while retaining letter-value tints. Explicit
alpha is exact (including 0/1); empty hatch removes redundant hatching. Line
stroke and marker face/edge are separate fields. Mean requires showmeans=True;
styles for explicitly hidden flier/boxen median fail. Explicit body/cap style
requests enable those box artists even if ambient rc hides them. Unknown nested
keys/shapes and role/value constraints fail, rather than disappearing. Colors/
styles/markers/sizes are bounded; no callback or arbitrary kwargs. Boxen per-band/
per-hue maps remain outside this subset. Box's explicit C03 workflow adds typed
per-hue components and columnar summaries without changing ordinary raw defaults.
[Executable comparison](../examples/distribution_components.py).

### Complete C03 box workflow

See [the scientific/units/ownership contract](BOX_WORKFLOW.md) and
[raw/supplied/shared-role/live executable](../examples/box_workflow.py).
`bxp` references existing columns, retaining IDs and optional unavailable marks.
Raw median CI uses private seeded row resampling, not whisker or observation PI.
Caps are fractions of final body width after dodge/gap; zero keeps cap geometry.
Size owns body outline stroke pt only; style owns body dash and real flier glyph
through serialized markers, including its default cycle. Other component styles
remain independent; mapped-property conflicts reject and native box guides reflect
actual properties. Native/date/log/v-h/y2, fixed-cell live transactions and
empty/reserved views share existing boundaries. New advanced work caps at256
drawn samplecells/10000 selected rows AND10000 declared fliers; old limits stay.
F01/F02/G01 and final frozen-product qualification remain separate.


### C04 violin workflow

See the [full scientific/units/ownership contract](VIOLIN_WORKFLOW.md) and
[paired/shared-family/live executable](../examples/violin_workflow.py).
Legacy omitted controls and two-hue split remain; explicit paired policy uses
frozen half-lanes, reserved hue slots and an odd left-only tail without fake rows.
Native component traits differ by inner mode; exact raw keys distinguish True
from1, and Box/boxen reject newly unavailable roles instead of dropping them.
HUE owns body fill, SIZE body-outline points, STYLE body dashes and only actual
inner glyphs. Independent tuple fits normalize by effective hue/global pool,
with references once per pool; weights remain relative mass and selected rows.
Native unextended inner defaults retain their actual flag/color/span precedence.
Applicable target/clock/log/native/live paths reuse one selector/domain/recipe
boundary. Advanced admission is10000 rows/256 drawn profiles, categorical64
levels/overrides, support1000; continuous numeric roles are not capped at64.
No callable/opaque kwargs/new nonlinear statistics, sampling or wider-row closure.

### Weighted violin subset

`weights` pairs finite nonnegative relative mass with selected observations.
Missing/zero-weight rows are excluded before positivity. Gaussian unbiased
covariance/effective n sets Scott/Silverman bandwidth; no row replication.
Inner quart/box/median use inverse weighted ECDF with all ties/no interpolation;
equal weights intentionally differ from old NumPy linear quantiles. Means use
weights in declared coordinates; point/stick retain each positive row once.
Count-normalized widths use total weight mass, not row count/effective n; common
weight rescaling preserves widths (comparable units across reference cells).
Area remains a common fitted-coordinate density scale, not equal clipped area.
Cut/clip never trim fit/inner rows or normalize visible tails. Singleton/constants
remain observed degenerate bodies with no fabricated bandwidth; count references
include their mass. Row limit10000, grid limit1000, bounded2048-row kernels and
stable scaled covariance/mass/mean; invalid derived support/density/mass ratios
fail. Unweighted fits/marks unchanged. No SciPy/new dependency or callable/kernel/
confidence inference. 78 tests include independent equations, extreme units/
weights/low bits/chunks, native styles/split/log geometry, schema/actions/editor/
export and RNG. [Executable comparison](../examples/weighted_violin.py).

### Native/log distribution subset

Box/violin/boxen/swarm opt into finite numeric category coordinates with
`native_scale=True`, excluding bool/string/date. Orders select/reserve locations,
not physical reorder. Width/dodge use minimum selected/reserved axis-coordinate
spacing (log10 for native logs, one for singletons). Default ordinal/one-based
coordinates remain. Shared axes reject conflicting modes/scales.

`stat_scale='data'` is the summary default; 'axis' explicitly computes log10
quantiles/KDE and inverse-maps every native artist. Swarm retains raw values.
Log observations/categories must be positive; no implicit inference or silent
clipping of nonfinite inverse geometry. Statistical bar/point/count now extend
this spacing as documented above; broader mappings remain gaps. [Executable comparison](../examples/native_categorical_scales.py).

## 2. Matplotlib plotting and customization

| Upstream family | mudplot today | Important gaps |
| --- | --- | --- |
| Lines, scatter, steps, errorbars, filled bands | Native styles, finite h/v data segments, asymmetric x/y magnitudes, horizontal/vertical native bands with mask/step/interpolation, and data spans | Finite declared traits and explicit unit guards; no arbitrary artist kwargs. [Scope](NATIVE_GEOMETRY.md) |
| Bars and pies | Native vertical/horizontal bars, explicit baseline/alignment/signed stacks, original per-mark styles/labels and authored pie wedge/text/value/callout controls | Supplied values only; finite native shapes and named formats. [Scope](NATIVE_GEOMETRY.md#supplied-bars-and-pie-wedges) |
| `stem` | Supplied rows and raw baseline; vertical/horizontal primary or twin axes, fixed groups/facets and shared hue, stroke width and marker/dash guides | Explicit native date/log scale domains; no estimates or weights. [Scope](STEM.md) |
| `stairs` | Native vertical supplied windows or explicit conservative rebin, open/fill, fixed groups/facets, date/log and primary/y2 | No horizontal, inferred weights/estimators or mapped semantics. [Scope](STAIRS.md) |
| `eventplot` | Raw disconnected ticks, fixed group/facet lanes, date/log and primary/y2; shared hue, stroke width and dash | No weights, rate estimation or horizontal marks. [Scope](EVENTPLOT.md) |
| `broken_barh` | Raw start/duration bands in source paint order; fixed group/facet lanes, dates with elapsed durations, log and primary/y2 | No statistical or semantic mappings. [Scope](BROKEN_BARH.md) |
| Histograms, boxplots, violins, ECDF | Partial families; dedicated weighted ECDF/proportion/percent/count/complement/v-h, grouped histogram stack/dodge/fill and bars/steps/poly with explicit fill/outline | Histogram bivariate controls, precomputed box statistics and wider distribution controls |
| Scalar images and contour fields | N07 explicit rectilinear meshes/images, masks, RGB(A), `spy` and contours; P01 calibration for scalar images/meshes | Primary linear numeric axes; no curvilinear grids or P01 control on contour levels or direct pixels. [Grid contract](HEATMAP.md#explicit-native-grid-fields) |
| Triangulated fields | N08: explicit masked connectivity for `triplot`, `tripcolor`, `tricontour`/`tricontourf` and native `trisurf` | No automatic triangulation or facet reindexing. [Triangle contract](#explicit-triangle-fields) |
| Vector fields | N09: native planar/spatial quiver, barbs, and uniform-grid streamplot | Finite numeric axes and native stepping; no magnitude-as-semantic-size mapping. [Vector contract](#native-vector-fields) |
| 3-D | N10: full-resolution explicit nonuniform surface/wireframe, signed bars, projected contours, voxels and camera/box aspect; reuses N08 `trisurf` and N09 `quiver3d` | Primary linear numeric axes for typed geometry; no automatic resampling, date/log or arbitrary camera callbacks. [3-D contract](#explicit-3-d-geometry) |
| Signals and spectra | N11: spectrogram, Welch PSD/CSD magnitude/coherence, whole-signal magnitude/wrapped angle/unwrapped phase; typed FFT/window/detrend/sides/scaling | Primary linear nontemporal Cartesian axes; no y2/group/weights/selectors; see N11 contract below. Integration qualification remains separate |
| Axes and layout | N12 finite locators/formatters, scale parameters and named derived axes; N13 typed stable IDs, native inset/nested/mosaic placement, spans/ratios/empty positions and shared components | [N13 contract](PANEL_LAYOUTS.md): bounded complete geometry, contained nonoverlapping sibling insets and explicit dimensional sharing. No arbitrary transforms/kwargs; isolated qualification is not integration/all-v2 closure |
| Color and legends | P01: native named/custom maps with under/over/bad, raw fixed/shared calibration, local colourbars, contexts and legend controls | Applicability and finite options in [scalar display](#scalar-display-and-guides); F01 role mapping is independent |
| Annotations, patches, tables | Named data/axes/figure literal patches and paths, shared spans, native tables, mixed-frame annotations and named stroke/shadow | Native data anchor drag only; no arbitrary callbacks or artist objects. [Scope](NATIVE_GEOMETRY.md#literal-patches-tables-and-annotation-coordinates) |
| Animation, GUI widgets, event callbacks, arbitrary artists | Python-native | A separate interaction scope, not automatically editable JSON features |

### Explicit triangle fields

`TriangulationSpec(triangles=[[0, 1, 2], [0, 2, 3]], mask=[False, True])`
uses original row positions from the named X/Y columns. IDs are zero-based
integers, not booleans. `True` omits a face; at least one face must remain.
Vertices must be finite and distinct on the XY plane. Faces must have nonzero
representable area, no duplicate faces, no crossed or overlapping interiors,
and no T-junctions. Shared full edges/vertices are permitted. Clockwise
faces are oriented counterclockwise for rendering only; JSON preserves the
authored triplet order. `SetData` replaces rows without renumbering indices;
the new coordinates must pass the same validation. No automatic topology,
facet/dropna reindexing, or interpolation of missing values.

- `triplot` draws only the edges of visible triangles without node glyphs.
- `tripcolor` requires an explicit `scalar_role`. `vertex` uses column `c`
  and averages its three values for each visible face; `face` uses one inline
  `face_values` entry per authored triangle, before masking. Equal face and
  vertex counts never decide the role.
- `tricontour`/`tricontourf` require `scalar_role="vertex"` and a `c` column.
  Pass ordered finite levels explicitly. Levels without geometry remain
  declared; only drawable lines can receive named-format labels. Filled
  boundaries and optional `extend` use the native contour convention.
- `trisurf` uses the same XY topology in a 3-D panel, with `z` in vertex
  height units. Its native colour represents the mean vertex Z for each
  visible face. It does not accept a second scalar role. Camera/vector
  features remain separate.

All axes are linear and numeric. Native autoscaling can include unused
vertices in the coordinate envelope even when their faces are hidden.
The new admission is limited to 10,000 vertices and 10,000 triangles per
layer, 50,000 active-box pair visits before exact intersection predicates,
and shared matrix work/storage, path, level and label limits. No broad
P01 or legacy normalization changes.
[Runnable PNG/SVG/PDF example](../examples/triangle_workflow.py).

### Native vector fields

`VectorSpec` opts into finite vector options; omitting it on `quiver` preserves
the old renderer and recipe. New vectors target linear numeric Cartesian axes.
Data quiver and barbs can target a configured Y2; `quiver3d` requires a 3-D
panel. Row marks use original aligned component columns. `mask_column` names
actual booleans (`True` excludes), and raw `group`/`hue_order` selects typed group
identity without changing row order. Fixed primary/Y2 facets work on planar
row vectors. Group ink is independent of magnitude. Signed components are
valid; zero displacements create no quiver arrow, and zero barbs use the
native calm symbol.

- Quiver `mode="data"` uses native `angles="xy", scale_units="xy", scale=1`;
  components are displacements, and `pivot` anchors tail, middle or tip.
  `mode="display"` uses screen-relative direction and length units of
  inches, axes width or dots, divided by `scale`. `width` uses `width_units`
  separately; head dimensions are native multiples of shaft width.
- Barbs use `length` in points. `half`, `full` and `flag` are increasing
  increments in the supplied component units, not an inferred wind unit.
  The native rounding and flip flags are optional; the visible magnitude
  cap is 64 half-increments per barb.
- `quiver3d` uses six original columns X/Y/Z/U/V/W. `length` is a dimensionless
  multiplier unless `normalize=True`, in which case it is the arrow length
  in the same units as the three coordinates. No automatic axis or view
  clipping option is introduced.
- `streamplot` uses strictly increasing uniform vectors `x_coords`, `y_coords`
  and named `u_matrix`, `v_matrix` with shape Y×X. A boolean mask or paired
  null excludes a grid node. Grid fields do not use row groups or selectors.
  `density` controls native mask resolution (0.25–1), seed coordinates are
  absolute XY data, and `minlength`/`maxlength` are normalized axes lengths
  (at most 4). `arrowsize` is dimensionless. Native stepping is not identical
  between provider versions. Use at most 64 explicit seeds, none in a masked
  interpolation stencil. Stationary-only fields have no trajectories; mixed
  visible stationary and moving nodes need an explicit stationary-node mask
  so the native speed floor can bound the stepping work.

The opt-in budget is 10,000 selected row vectors or grid vectors per layer,
with shared figure work, storage and native path admission. The stream
reservation bounds candidate seeds, native error retries and step storage
before entering the provider; requests exceeding that envelope are rejected,
not truncated. This is not a wall-clock guarantee or a custom solver.
[Runnable PNG/SVG/PDF example](../examples/vector_workflow.py).

### Explicit 3-D geometry

`projection3d()` selects an actual native 3-D panel. A `SpatialSpec` on
`surface` or `wireframe` gives finite increasing `x_coords` and `y_coords` for
the named Z matrix in `[y][x]` order. All cells or wire lines are rendered,
including grids larger than the native default sampling count. An omitted
`spatial` keeps legacy unit indices and native default sampling.

- `bar3d` reads the original aligned X/Y/Z anchor rows and named `dx`, `dy`,
  `dz` columns. XY deltas are positive footprints; Z is a raw base and `dz`
  is a signed nonzero difference. Native unshaded box faces preserve the
  two endpoints even for a down bar; both endpoints contribute to auto-view.
- `contour3d` and `contourf3d` use the original XY/Z field. Native directions
  `z`, `x`, `y` respectively contour the raw Z, X, Y scalar on the XY, YZ,
  ZX chart. Lateral charts require consistent strict Z monotonicity in the
  omitted original X or Y dimension, not a relabeled Z contour. Line levels
  need at least one strictly inside the actual scalar range. Filled levels
  are explicit boundaries, not labels. An optional finite absolute `offset`
  projects the geometry to one plane; otherwise native lines stay at levels
  and native filled bands at midpoints. Fixed limits still win.
- `voxels` takes rectangular boolean `occupancy[z][y][x]`. `True` occupies
  one cell, with native shaded exposed faces; adjacent occupied cells share
  their interior face. Supply all three edge vectors of length dimension+1,
  or none for unit edges. Colours and optional edge stroke are visual only.
- `camera3d(Camera3DSpec(...))` (or the same `SetCamera3D` action) sets the
  native elevation/azimuth/roll in degrees, vertical axis, perspective or
  orthographic projection, display-box ratios, and zoom. Focal length is
  perspective only. `camera3d(None)` restores native defaults. A camera
  changes the display, not raw coordinates or authored data limits.

Explicit geometry uses finite primary linear numeric axes without row
selectors, dates or log transforms. Coordinates and levels must stay
distinct after conversion to the native numbers; folded charts and
collapsed geometry are rejected before drawing. Each typed mark admits at
most 10,000 grid vertices, boxes or voxel cells plus shared figure-level
work, storage and path limits. No finite mesh is silently truncated.
[Runnable PNG/SVG/PDF example](../examples/spatial_workflow.py).

### Scalar display and guides

`context("paper"|"notebook"|"talk"|"poster")` selects typography factors
1, 1.15, 1.4 or 1.75 inside the existing render-local theme. Journal
overrides still win. Explicit marker diameters, strokes and data coordinates
do not scale. `palette(colors=[...])` cycles 1–64 literal categorical
swatches in authored order and cannot combine with a generated preset.

`ScalarDisplaySpec` on scatter with `c`, heatmap, scalar `imshow`, `pcolor`
or `pcolormesh` owns a named colormap (default `viridis`) or a 2–64 colour
evenly spaced ramp. Optional `under`, `over` and `bad` affect the actual
native mappable; `pcolor` omits masked cells, so use `pcolormesh` to colour
bad cells visibly. Missing point coordinates do not draw, while missing
colour on a finite scatter point uses `bad`. Raw selected finite values are
borrowed for calibration, not replaced. Scatter accepts numeric linear/log
axes, including an enabled twin; matrices use primary linear axes. Clocks,
F01 roles, direct RGB(A), contour/triangle scalar semantics and statistics
retain their separate owners. Competing M01 centre/norm/range/robust
options reject; masks and annotation geometry still apply.

Named `scale_id` pools the declared raw domain across applicable artists
with identical calibration/map settings. `linear` and `log` accept fixed
or inferred bounds (log requires positive visible values). `centered`
uses a symmetric range about the declared center. `two_slope` requires
explicit `vmin < center < vmax`. `boundary` uses 2–65 increasing edges,
uniform guide bins and native half-open membership, including the last
edge as over. `ColorbarOptionsSpec` configures each local bar's placement,
raw tick values/format, and `extend`; these do not change the shared
calibration. Legend `ncols` is 1–8; optional `line-pair` and `scatter-pair`
are registered native handlers for matching actual line/point handles.
[Runnable PNG/SVG/PDF example](../examples/scalar_display.py).

Use native Matplotlib methods when their semantics fit; do not rewrite its
plotting engine or introduce a hypothetical second-renderer abstraction.
Where newer upstream APIs are used, retain the supported minimum version with
an explicit guard/fallback, or leave the feature clearly version-gated.

### Finite saved axis controls — N12

`AxisSpec` appends optional `scale_options`, `major_ticks`, `minor_ticks`;
`PanelSpec` appends `secondary_x`, `secondary_y`. Absent fields omit from old
0.1 JSON. Core builders/actions/validation/schema/capabilities need no NumPy or
Matplotlib; rendering uses native Matplotlib ≥3.8 axes, locators and artists.

```python
p.axis_scale("x", "symlog", options={"base": 10, "linthresh": 1, "linscale": 1})
p.ticks("x", {"locator": {"kind": "multiple", "step": 2, "offset": .5},
              "formatter": {"kind": "number", "notation": "fixed", "precision": 1}})
p.secondary_xaxis({"kind": "celsius_fahrenheit"}, label="Temperature (°F)")
```

These are independent examples: `multiple` requires a linear numeric axis.
`ticks(axis, spec, which="major"|"minor", panel=...)` replaces one `TickSpec`;
None clears it. `axis_scale(..., options=None)` atomically replaces the scale
and clears/replaces parameters. Old SetScale retains unrelated fields and
rejects incompatible options rather than discarding them. Shared new fields
inherit only when None; conflicting explicit requests reject. Existing
named-share/figure-share mixing remains forbidden.

- Locators: auto/none/fixed/multiple(step/offset)/max_n(integer/pruning)/
  linear/auto_minor/log/symlog/asinh/logit/calendar. Max_n has 1–128 bins,
  linear 2–128 locations, minor 2–32 uniform subdivisions. Calendar supports
  auto/year/month/week/day/hour/minute/second/microsecond, integer intervals
  1–1,000,000, weekday 0–6, target 2–128. Fixed rejects bool/nonfinite and
  duplicates/collapse after float conversion. Ordinal auto preserves category
  positions/labels; only auto/none/fixed locators/formatters are compatible.
- Formatters: auto/none/fixed/scalar/number(general/fixed/scientific)/percent/
  engineering/log/logit/date/concise_date. Precision 0–12 decimals (general
  1–12), prefix/suffix/unit ≤32 characters, paired fixed literal labels ≤128
  characters. No user format templates, width, eval, callbacks or attribute lookup.
- Log base >1 and finite ordered subs work everywhere existing log is valid,
  including applicable statistical/native-category paths. Scale subs are
  **minor** policy; an explicit locator may override either rank. Symlog defaults
  base10/linthresh2/linscale1; asinh defaults linear_width1/integer base10
  (2–1024). Widths are coordinate units. New families permit supported raw
  numeric Cartesian primitives/applicable y2, not statistical/ordinal/polar/3-D
  geometry. Logit checks actual displayed open(0,1) geometry, including grouped
  rectangle edges. Constant p view uses native 0.1 widening on min(p,1−p),
  contains p/complement symmetry or reports open-view/inverse precision failure.
  Valid explicit limits are not replaced.
- Derived views: affine with finite nonzero factor/offset and explicit units,
  Celsius↔Fahrenheit, radians↔degrees, seconds↔milliseconds, hertz↔period,
  positive reciprocal with factor/units, canonical day→Unix seconds.
  reverse=True selects the inverse except Unix. Only **visible coordinates**
  convert, never source samples/units/IDs. Parents are linear/log; derived right
  y conflicts with independent y2. Every native refresh/zoom/get_tightbbox checks
  domain/nonfinite/distinct endpoints and target-ULP-conditioned inverse
  precision. Out-of-view zeros are valid for a positive reciprocal view.
  No epsilon/clipping/custom serialized function.
- Dedicated bounds before configured native tick expansion: 512 candidates
  per physical axis/rank, 16,384 across figure configured active operations,
  512 characters per formatted result. Shared/inherited and derived axes count
  physically; repeated calls replace current reservations, not accumulate.
  These are active-location/format algorithm bounds, **not** cached Tick RAM
  bounds, an SLA, a memory sandbox, or changes to old unrelated limits.
- Temporal fixed positions use canonical UTC1970 days, not source unit/origin.
  N12 date/auto/concise use canonical datetime plus declared UTC/fixed clock,
  distinguishing accepted 20/21µs ticks in 2100. Fixed auto/subsecond includes
  date+6digits. Concise follows Matplotlib3.8 finite level/zero/offset/trailing-zero
  policy on calendar or fixed temporal positions; unrepresentable native grids
  reject. No epoch mutation; no-N12 policies unchanged; no all-F02 closure claim.
- Both editors preserve parameters on label/limit edits and expose generic typed
  JSON/actions. New nonlinear DATA handles disable with a reason per actual
  primary/y2 target, not unaffected primary or title/legend handles. Linear/log
  inverse dragging remains valid for all bases; no incorrect linear fallback.

[Executable six-panel workflow](../examples/axis_controls.py) saves PNG/SVG/PDF
and JSON, edits scale parameters, undo/redoes and reopens. Qualification remains
separate from parent integration and other frozen v2 rows.

## 3. Two support lanes, not a misleading universal wrapper

### Declarative lane: the product contract

A feature is supported in the product only when its data/settings can be
represented, validated, rendered, exported and edited through the shared
Python/CLI/JSON/editor path. Named transforms and serializable options belong
here. Unknown/unsupported options must fail clearly, not disappear silently.

Do not put pickled functions, arbitrary `eval`/`exec`, callbacks or opaque
Matplotlib objects in JSON to claim compatibility. If an optional adapter is
introduced, keep it at the effect boundary and declare dependencies there;
the reducer/spec/validation core must remain dependency-free. Advanced
clustering or Seaborn adapters may justify further optional statistics layers.
Unreleased LOWESS/Huber/binomial-logit effects now use the explicit regression
extra with statsmodels>=0.14.1; base/core dependencies remain empty.

### Native Python lane: available today

`Plot.render()` already returns a real Matplotlib Figure:

```python
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import mudplot as mp

plot = mp.plot({"x": [0, 1, 2], "y": [1, 3, 2]}).line("x", "y")
figure = plot.render()
try:
    axis = figure.axes[0]
    axis.axvspan(0.4, 0.8, color="#64748b", alpha=0.15)
    axis.xaxis.set_major_locator(MaxNLocator(4))
    figure.savefig("native.svg")
finally:
    plt.close(figure)
```

An installed Seaborn axes-level function can likewise target one of these
Axes with `ax=`. Figure-level Seaborn functions create/manage their own grid
and are not equivalent to this escape hatch.

**Limitations:** native edits do not enter `FigureSpec`, undo/redo or JSON.
`Plot.save()` rerenders from the spec and will not preserve those edits; save
the modified Figure instead. Direct `figure.savefig()` is native Matplotlib
I/O, not mudplot's atomic/deterministic export contract. This lane is useful
compatibility, but must not be advertised as full declarative coverage.

## 4. Implementation order

These are proposed development batches, not delivery dates or completed work.

1. **Shared estimation and convenient statistical plots.** Named
   mean/median/count estimators; SD/SE/PI/seeded bootstrap CI; explicit raw-data
   `barplot`/`pointplot`/`countplot` paths. Begin with a clearly scoped subset,
   then add weighted/unit-aware semantics with reference tests. Preserve
   `.bar()` for already summarized data.
2. **Categorical completeness.** Horizontal orientation, order/hue order,
   dodge/gaps, bar stacking/labels; better box/violin controls; reliable swarm
   and extended swarm/letter-value semantics. First subsets are implemented;
   statistical native/log first subset is implemented; broader mappings/components
   remain. Reuse the
   publication visual language.
3. **Relational and distribution completeness.** Independent hue/size/style
   mappings, line aggregation/intervals, broader histogram variants and
   broader distribution variants. ECDF, weighted histogram and configurable
   univariate/bivariate KDE first subsets are implemented. Match statistical semantics, not
   merely names.
4. **Automatic composition.** Data-driven facets and shared semantic scales,
   followed by pair/joint grids with marginal/diagonal plots.
5. **Advanced statistics and matrices.** Rich heatmaps, residual/robust/
   logistic/LOWESS workflows and optional clustered heatmaps.
6. **Remaining native Matplotlib families.** Discrete/event/signal/vector/
   mesh/triangle/3-D plots and richer axes, normalization, colorbars, legends,
   annotations and layouts. Small primitives such as `barh`/`stairs` can land
   earlier when they unblock the previous batches.

## 5. Definition of supported

Every delivered feature/option needs:

1. A precise data/option/statistical contract, documented differences from
   upstream, dependency/version boundaries and invalid-input behavior.
2. Spec/action representation, reducer isolation, JSON/schema round-trip and
   truthful `capabilities()` metadata.
3. Renderer, Python builder and usable editor access; unsupported combinations
   must fail before silently producing a misleading plot.
4. Statistical/numeric reference tests (when applicable), artist-level tests
   for placement/properties and multi-panel/group/missing-data edge cases.
5. Executable examples and reviewed PNG/vector output, with readable defaults
   and consistent fonts, spacing, legends and accessibility behavior.
6. Same-environment reproducibility, the minimum supported environment and
   current locked environment, plus lint/type/schema/packaging checks.

Feature names, option coverage and statistical/composition coverage must be
reported separately. Do not label a family complete while its major options
or automatic statistics remain missing.

## Official references

- [Seaborn API reference](https://seaborn.pydata.org/api.html)
- [Seaborn statistical estimation and error bars](https://seaborn.pydata.org/tutorial/error_bars.html)
- [Seaborn axes-level vs figure-level functions](https://seaborn.pydata.org/tutorial/function_overview.html)
- [Matplotlib plot types](https://matplotlib.org/stable/plot_types/index.html)
- [Matplotlib Axes API](https://matplotlib.org/stable/api/axes_api.html)

## Fixed histogram bin rules

Typed univariate `hist` accepts `bins="auto"`, `"fd"`, `"doane"`, `"scott"`,
`"stone"`, `"rice"`, `"sturges"`, `"sqrt"` and `"discrete"`.
The eight named estimators use fixed classic NumPy 1.23 definitions, not the
installed NumPy version. For `[0, 1, 2, 3, 100]`, `auto` produces 43 bins.
Missing rows, zero weights and hue exclusions are removed first; each usable
observation selects edges once. Positive weight magnitudes affect heights only.
Derived grids above 10,000 bins reject before allocation; they are not clamped.

Ordinary discrete values must be integers: bins are unit-width and integer-centered,
including empty cells. `discrete=True` aliases only the default `bins=20` to
canonical `bins="discrete"`; custom bins conflict. `False`/`None` preserve legacy
defaults (explicit `bins="discrete", discrete=False` conflicts).
See [temporal axes](TEMPORAL_AXES.md) for declared-unit restrictions and
`examples/histogram_binning.py` for editable JSON and PNG/SVG/PDF output.

## Categorical strip contract (C01 bounded functional acceptance)

`strip=StripSpec(jitter_policy="uniform", seed=0)` opts into category geometry;
explicit order/orientation/native/dodge also opts in. Omitted new controls keep
the legacy raw-x jitter and old JSON. `hue_order` alone preserves prior behavior.
Arguments keep x categorical and y measured under either orientation. Missing
category/value/group rows drop listwise; source observations are never replaced.
Orders select and reserve empty levels. None/zero dodge overlays groups; positive
dodge is a total span fraction in [0,1] of minimum selected/reserved category
spacing (ordinal one, log10 spacing on native logs, canonical days on dates).
All reserved hues divide that span into slots. `jitter` is a half-width fraction
in [0,.5] of a slot when dodged, otherwise of category spacing. `uniform` samples
within that range using the named local seed; `none` adds no jitter. Seeds are
non-bool integers in [0,2**32-1]; global RNG and measured values stay untouched.
Explicit date clocks reuse [the temporal contract](TEMPORAL_AXES.md), not
implicit string coercion. [Executable example](../examples/strip_categories.py)
exports editable JSON and PNG/SVG/PDF.
[Bounded closure evidence](review_evidence/v2_strip_categories_closure.json)
records real Rust/browser history/reopen, installed minimum API/CLI and exact
frozen-source lineage. This is not F01, REL01 or whole-v2 completion.

## F01 numeric hue guide increment (in progress)

Scatter and lineplot support `colorbar=True` for explicit numeric hue; optional
`clabel` is a string of at most 512 characters and requires that request.
Negative semantic values/domains remain valid. The non-data colourbar uses
normalized [0,1] geometry with exact original-value tick labels from the same
clipped mapping and colormap as marks. Observation coordinates/limits/data are
unchanged. Constant domains show one solid midpoint swatch with one exact tick,
not an invented continuous range. Neighbouring/extreme/subnormal bounds retain
distinct exact labels rather than cosmetic rounding.

Guide intent is resolved before any member draws: one requested bar replaces
numeric-hue calibration legends throughout its panel/shared scope, including
earlier members and primary/y2 targets. Dataset/size/style guides remain.
`legend=False` does not hide the requested bar; empty local views do not invent
one. Requested members of a shared scale must have identical effective labels.
Scatter outlines accept bounded `edge_color` and `line_width` [0,1000] physical
points, independent of mapped diameter/area. Omission keeps native defaults.
[Executable example](../examples/semantic_colourbars.py) exports JSON/PNG/SVG/PDF.

This is an F01 increment, not row closure. The following strip/ECDF increment
adds a four-family scenario; all other named applicable adapters and final
installed/browser/product qualification remain mandatory.

Exact source/check/failure lineage for this increment is recorded in
[F01 guide evidence](review_evidence/v2_semantic_colourbars.json).

## F01 strip and empirical-curve adapters (in progress)

`stripplot(..., semantics=SemanticSpec(...))` maps independent hue/size/style
on retained observations. Size is marker diameter in points; C01 native/log/date
category geometry, order, reserved categorical hue slots and local jitter remain
category-only. Explicit numeric normalization clips appearance, never creates
fake hue slots or changes measurements. Required-role missing rows and category/
role orders select the same mapping/geometry cohort.

`ecdf(..., semantics=...)` partitions distinct raw role tuples into empirical
curves before paired weighting/ties/complement calculation. Size is stroke
width in points; style uses named markers and requested dashes. Markers denote
actual right-continuous values at observed knots, including strict complementary
mass X>t, never the prepended boundary sentinel. Clipped appearances do not merge
curves. Existing v/h, positive observation logs, date clocks and vertical-y2
contracts remain; horizontal ECDF+y2 explicitly rejects in this subset and
remains required wider F02/D06 work. No inference/bootstrap is added.

[Four-family example](../examples/shared_semantic_families.py) exports raw-data
JSON and PNG/SVG/PDF with one declared pool shared by scatter, lineplot, strip
and weighted ECDF. Existing default calls remain unchanged. LayerSpec's new strip
field appends after existing constructor parameters so old positional alpha
calls retain their actual rendered opacity; the original C01 closure is historical.
All other applicability-inventory families and full F01 qualification remain
mandatory, not excluded or postponed.


### Rug observations — D07

`plot.rug(observation, orient="v", height=None, semantics=None, axis="y")`
keeps the original column as observations. Vertical rugs use shared x and extend
inward from the bottom. Horizontal rugs use target y, extending from the left on
primary y or the right on y2; declare `secondary_yaxis` before choosing y2.
`height` is finite, non-bool `[0,1]` in **axes fractions**, with `None` retaining
the native 0.04. JSON/editor layer fields use the existing `width`; no new field
or default JSON shape is introduced. Zero height retains zero-length segments.

Only the observation axis contributes to data limits and requests temporal
conversion. Independent density/value limits and automatic framing are unchanged
when a rug is overlaid, even with log or temporal perpendicular axes. Fractions
are never density, mass, calendar durations or data-coordinate offsets.

`SemanticSpec`/strict dict maps categorical/numeric hue, physical **stroke width
in points**, and style to named dashes. Use `dashes=["-", "--", "-.", ":"]` or
omit it for that default order; select enough distinct patterns without cycling.
The common marker list does not turn rug strokes or their guide proxies into
filled points. Zero mapped stroke preserves rows/segments with native solid
zero-width geometry, including Matplotlib 3.8. Mapped hue/size/style reject
conflicting scalar colour/line-width/line-style overrides and legacy group/c.

One vectorized native collection contains each semantic rug, in retained source
order with duplicates. There is no pooling, estimation or 256-curve cap. Shared
scale IDs reuse original-row domains, normalization and logical-panel colourbar
planning; guide proxies have no data. Required-role missingness and declared
orders select rows without rewriting values, IDs or units. Semantic rows retain
the 10,000 bound; legacy/resource limits stay in place. Primary facets include
reserved empty cells. Weights, inference/bootstrap and arbitrary native kwargs
are not rug controls. See the executable
[API/action/history/reopen/export example](../examples/rug_workflow.py).

### Signal spectra — N11

`plot.spectrum(signal, second=None, fs=..., kind="psd", nfft=None,
pad_to=None, overlap=0, window="hann", detrend="none", sides="onesided",
scaling="density", scale="linear")` retains raw real samples, row IDs and order.
`fs` is required in Python and JSON: positive finite nonbool samples/second (Hz).
Missing/nonfinite/bool samples reject, not drop or impute; negative amplitudes
are valid. CSD/coherence alone accept a second signal, with equal paired length.

Segmented spectrogram/psd/csd/coherence use nfft=256 when omitted, require one
full window and step nfft-overlap. Trailing partial samples stay in source but
are unused; no implicit short-signal padding. Whole magnitude/angle/phase use
N=len(signal), nfft=None and overlap=0. Symmetric NumPy windows boxcar/hann/
hamming/blackman require N>=3. Named detrend none/mean/linear acts per window,
before weighting. pad_to defaults to N and must be >=N; overlap is integer [0,N).
Coherence needs >=2 computed full windows (overlap can supply them).

For raw Fourier X, density power divides by fs*sum(window²), spectrum by
|sum(window)|². One-sided power doubles positive bins except DC and, ONLY when
the actual padded FFT length M is even, Nyquist. Two-sided output is ascending
negative-to-positive frequency. CSD computes normalized mean(conj(X)*Y), displays
its magnitude and retains the complex result at the effect boundary, never as
raw JSON or fabricated zero phase. Coherence is
|mean(conj(X)*Y)|²/(mean(|X|²)*mean(|Y|²)), NOT mean segment coherence.
It is dimensionless [0,1] up to floating-point roundoff; overlapping-window
variance is not an independence/significance claim. No inferential guide is added.

Magnitude is |X|/|sum(window)| without one-sided doubling/peak-amplitude claims.
Wrapped angle/unwrapped phase are radians ordered by ascending plotted frequency.
Zero computed coefficients give phase gaps; unwrap each contiguous defined run
separately. Zero computed coherence power also gives gaps. Float64 window,
detrend and FFT can round tiny true bins to zero; masks are not physical evidence
of exact zeros. There is no high-dynamic-range exact/relative FFT guarantee.
Frequency-local normalization prevents underflow of nonzero computed coefficients,
not cancellation/conditioning error inside FFT. Linear power zero is
valid. dB is 10log10(power/CSD magnitude) or 20log10(magnitude), relative to 1
declared unit; computed zeros give gaps, never a positive floor. All-undefined
results reject. Leave scaling=density when unused (coherence/magnitude/angle/
phase); phase/coherence require scale=linear.

Default labels are Frequency (Hz), Elapsed time (s), power/density, coherence or
radians, never raw signal-column names. Explicit user labels are preserved.
Spectrogram native cells use centre-midpoint frequency edges and one-hop time
cells; cmap_kind/colorbar/clabel/alpha apply. Lines use scalar color/line_width/
line_style/alpha/label/references. Unused controls reject. Multiple direct panels
are supported; incompatible derived units/raw layers cannot share one panel.
This finite N11 scope is primary Cartesian linear nontemporal axes, no y2/group/
semantics/weights/row selectors; future meaningful combinations are not declared
mathematically impossible.

Dedicated preallocation caps: 1,000,000 real samples/channel, 65,536 effective
window/padded FFT length, 1,048,576 segments*pad_to complex cells (16 MiB for
one complex128 grid plus other bounded buffers). They are algorithm caps, not
SLA/RAM sandbox/existing-limit changes or silent truncation. Core build/validate/
JSON/capabilities remain dependency-free; NumPy/native artists retain existing
floors. `examples/signal_spectra.py` exercises seven kinds/history/reopen/PNG/SVG/
PDF. Rust's registered spectrum layer and generic JSON form expose these controls.


N11 numerical review correction: coherence alone divides each nonzero real
channel's consumed prefix by its positive maximum absolute amplitude **before**
detrending/FFT. That prefix ends at `(segment_count-1)*(nfft-overlap)+nfft`;
unused trailing samples remain stored/validated but cannot influence scaling.
If scaling would erase any nonzero consumed sample, the effect raises an
explicit floating-point precision error **before FFT**, not a mathematical-zero/
undefined-bin claim. This is a float64 arithmetic boundary, not arbitrary-
precision FFT support.
Each frequency's private vector of segment coefficients is then divided by its
positive maximum absolute coefficient, before averaging cross/powers. Both
channel factors cancel in the dimensionless ratio. A defined channel/bin has
mean power >=1/segment_count, preventing false gaps even when different
frequencies differ by hundreds of amplitude decades. Exact zero channels/bins
remain zero; no floor, clipping, jitter or raw-data rewrite is used. Only CSD
returns a physical complex cross-spectrum, in original channel units.
Zero-width lines use native no-line style while retaining all frequency/value
artist data, avoiding minimum-version all-zero dashed-pattern failures.
Scalar line colours use the shared finite
named/hex validator; labels/colourbar labels must be nonempty strings. `clabel`
requires a requested spectrogram colourbar. Citation/href require a line label,
reuse existing safe-reference validators and native SVG links/PGF macros.

