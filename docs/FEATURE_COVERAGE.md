# Matplotlib / Seaborn feature coverage

*[한국어 / Korean](FEATURE_COVERAGE.ko.md)*

## Goal and audit scope

The product goal is to cover the plotting and statistical workflows available
in Matplotlib and Seaborn, with consistent publication styling, editable specs,
and reproducible output. **A plot name in the registry is not feature parity.**

This is a static audit of the current checkout: 1.0.0 plus Unreleased bar
uncertainty / `publication` and the first v1.1 raw-data statistics subset. Reference interfaces are the official
Seaborn **0.13.2** and Matplotlib **3.11.2** documentation linked below. These
are comparison references, not changes to the runtime minimums: the existing
1.x contract still supports Python 3.10 / Matplotlib 3.8 / NumPy 1.23.

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

The current engine has **37 layer types**. There is deliberately no invented
coverage percentage: a denominator must include options and semantics, not
just function names. The matrices below identify the major gaps, not every
argument in every upstream signature.

## 1. Seaborn function interface

| Upstream workflow | mudplot today | Important gaps |
| --- | --- | --- |
| `scatterplot` | Partial: legacy group/c plus strict independent categorical/numeric hue/size, categorical style, ordering/global bounds/guide legends | Semantic colourbar/outline/date/y2, wider line/facet sharing and normalization; diameter-to-area policy explicit, not full upstream equivalence |
| `lineplot` | Partial: numeric-x named pointwise estimates/weighted/per-x unit CI plus independent raw hue/size/style curves, stroke widths/marker-dashes/shared domains; raw line retained | Whole-curve/simultaneous inference, temporal/category predictors/y2/raw-line mappings/colourbars/automatic facets; not full upstream numerical equivalence |
| `histplot` | Partial: opt-in weighted shared-bin count/frequency/probability/percent/density, pooled/per-curve normalization, cumulative integration, grouped stack/dodge and layer/stack steps, v/h/raw observation logs; legacy hist retained | Step+dodge/filled step, fill/poly/discrete/auto rules, bivariate weighted stats/KDE/date/y2; raw bin widths only |
| `kdeplot` | Partial: typed weighted univariate density/CDF and bivariate full covariance/native contours/fill, bandwidth/support/grid/common mass, grid-conditional HDR, raw-unit log display; legacy retained | 2-D cumulative/colorbar/absolute levels/full-space HDR guarantees/multiple/other kernels/callable/date/y2/log fitting; own semantics, not full upstream numerical equivalence |
| `ecdfplot` | Partial: right-continuous weighted/tied ECDF, strict complement, per-curve proportion/percent/count, group/order/dash, v/h and positive observation logs | Continuous hue/size/style/date, y2/2-D and arbitrary kwargs; finite observed support only |
| `rugplot` | Partial: x-axis `rug` | y-axis marks, height/orientation and semantic controls |
| `stripplot` | Partial: deterministic x jitter and grouping | Nested categories/hue dodge, order/native scale, orientation and more jitter controls |
| `swarmplot` | Partial: circular display-space packing on every draw; order/hue/dodge/orientation, layout/DPI/positive log values, native numeric/log categories; numeric/categorical size mapping/guides; retain/report overcrowding | Style/date/mixed-family shared/facet semantics, arbitrary markers and cross-layer collisions; limit 2000 usable rows/layer |
| `boxplot` | Partial: category × hue/geometry/native log, IQR/percentile whiskers/notches, mean/fliers, independently typed body/whisker/cap/median/mean/flier styles and explicit data/axis statistics | Precomputed bxp, bootstrap median CI, cap geometry and arbitrary/per-hue kwargs |
| `violinplot` | Partial: category × hue/native log, weighted relative Gaussian/inverse-ECDF marks/mass widths, bandwidth/grid/support, four inner modes/None, two-hue split, width/area/count and explicit data/axis fit | Callable KDE, arbitrary-hue split/inner kwargs and wider size/style mappings; weighted step quantiles differ from old linear quantiles |
| `boxenplot` | Partial: per-cell letter values/depths/widths, category/hue/native log, independently typed body/median/flier styles and explicit data/axis quantiles | Weights, arbitrary/per-band/per-hue component kwargs and wider mappings; named depths capped at 32 |
| `pointplot` | Partial: named/raw/log-fit estimates/intervals, weighted/unit CI, native numeric/log spacing, order/hue/orientation/dodge/gap-aware lines | Axis log sum/count, broader estimator/semantic/style/date options and log/native y2 |
| `barplot` | Partial: raw/log-fit estimates/intervals, weighted/unit CI, native numeric/log spacing, explicit positive log baseline, geometry/gap/labels; precomputed `bar` separate | Axis log sum/count, broader inference/semantic/date controls and log/native y2 |
| `countplot` | Partial: global counts/proportions/percent, native/log category spacing, explicit log-value baseline, orientation/gaps/linear stacks/labels | Weighted counts, log-value stacking/stat_scale and wider normalization/semantic/date |
| `regplot` | Partial: legacy polynomial plus configured poly/log-x/Huber/binomial-logit/LOWESS, selected raw groups; relative weighted poly/logx point fits/raw residuals; advanced models use optional extra | Weighted CI/bootstrap/advanced-model CI, partial residualization and more fit/scatter controls; see [regression scope](REGRESSION.md) |
| `residplot` | Partial: regplot residual mode, original y minus row predictions, zero guide and per-group/facet fitting | Separate residual trend, out-of-sample/deviance diagnostics and inference; see [scope](REGRESSION.md) |
| `heatmap` | Partial: legacy imshow plus opt-in masks, formatted raw annotations, row/column labels, explicit/robust/log/centered colour ranges, square cells and borders | Custom annotation matrices, more norms/rotations/colourbar controls and clustering; see [typed scope](HEATMAP.md) |
| `clustermap` | Partial: hierarchical row/column linkage, supplied trees/optimal leaves, aligned dendrograms/mask/labels/colour strips, sample z-score/min-max; optional SciPy | Multiple colour tracks/legends, missing data/interactive cuts/custom metrics/layouts; see [scope](CLUSTERMAP.md) |
| `relplot`, `displot`, `catplot`, `lmplot` | Partial composition: terminal `facet()` materializes row/col subsets, wrap/shared axes and semantic domains for supported 2-D templates | Full builder families, live template mapping, legacy c/colorbars, consolidated figure legends and broader inference |
| `FacetGrid` | Partial row/col materialization, shared axes/semantic domains and raw groups | Live mapping and wider grid controls; see [facet limits](FACETS.md) |
| `PairGrid` / `pairplot` | Partial numeric pair matrix: raw scatter, histogram/KDE/ECDF diagonals, pairwise complete cases and named value axes | Corner/semantic/weighted/complementary-CDF/nested grids; see [pair scope](PAIR_GRID.md) |
| `JointGrid` / `jointplot` | Partial: terminal `joint()` links raw scatter/regplot or ungrouped hist2d/hexbin (colorbar=False) with paired histogram/KDE/ECDF marginals; source data preserved | Semantic/c/weighted/complementary-CDF/grouped-binned kinds, nested composition and richer layout; see [joint scope](JOINT_GRID.md) |
| Themes, palettes, legend/despine utilities | Partial: named themes, LCH palettes, legend/despine controls | More contexts, upstream palette/colormap selection, legend columns and shared semantics |
| `seaborn.objects` | Partial mark-level equivalents only | A composable statistical transform/move/scale pipeline; no drop-in object API |

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
Raw line/date/y2/colourbar/wider inference remain planned. Automatic facet
materialization is supported separately for the documented subset in [FACETS](FACETS.md).
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
Limits10000rows/64levels/enough markers, primary numeric2D; no group/c/scalar-role
conflicts, colourbar/outline/date/y2/line/facet mapping in this subset. Broader
controls stay planned and legacy c/colourbar works.85tests cover equations/
geometry/global mapping/masks/strict JSON/types/editor/exports/legacy/RNG.
[Executable comparison](../examples/scatter_semantics.py).

### Numeric-x line estimates

Lineplot uses shared named estimation per predictor/hue cell, weighted mean/
paired CI and hierarchical units within x. Pointwise intervals only, NOT
simultaneous bands/longitudinal whole-curve resampling. Native lines and bands/
bars preserve numeric predictor spacing; horizontal swaps geometry, not roles.
Ascending sort default; per-hue first-observed order explicit. Ribbons need
monotonic x and split missing bounds; no fabricated singleton CI. Data/log10
response fit and positive raw/log predictors; derived invalid bounds fail, no
clipping. Exact independent band alpha/default .2*line alpha; bar-only caps/
stroke. Missing/zero selected rows handled by shared contracts; local seed, no
new dependence/global RNG. 66 independent estimator/interval/bootstrap/unit/
geometry/strict/core/JSON/editor/export tests. Raw line defaults/order unchanged.
No date/category x/y2/dodge/order/callable in subset; opt-in semantic maps described above.
[Executable comparison](../examples/line_estimates.py).

### Weighted bivariate KDE conditional-grid HDR subset

New kde2d/KDE2DSpec has paired x/y weights and full unbiased covariance,
effective n and d=2 Scott=Silverman=`n_eff**(-1/6)`. Relative weights not replicated
counts; cut/clip only evaluation, common mass includes skipped singular hues,
common grid uses pooled fit support and conditional covariance. No invented
bandwidth/jitter: insufficient/collinear/numerically rank-deficient curves skip
with optional warning and no contour/legend. Empty hues reserve slots.

Levels ENCLOSE highest-density trapezoidal node mass conditional on the finite
evaluation grid, ties all included, so clipping/grid refinement changes
thresholds without renormalizing density. Approximate grid regions are NOT
confidence intervals/full-space probability guarantees. Unresolved duplicate/
extreme thresholds fail. Native contours/monochromatic fill bands, exact alpha/
outline/width, hue dash/hatch/ref metadata, explicit legend-only no-data proxies.
Both raw observed axes may log-display with positive observations AND support,
no Jacobian/log fitting. Scaled/centered full covariance, stable products/
quotients and bounded 32×1024 point-row evaluation, no SciPy/whole-grid data
matrix. Limits: 10000 usable rows, 256 nodes/axis, 16 levels strictly in (0, 1). Invalid
support/density/grid mass/levels fail clearly. No cumulative/orient/date/y2/
colorbar/kernel/callable/absolute thresholds/regularization/stack/multiple/kwargs.
[Executable comparison](../examples/kde2d_semantics.py).

### Weighted univariate Gaussian KDE first subset

Strict KDESpec opt-in; None keeps the old unweighted1.06*sample-SD*n**(-1/5)
200-point/constant fallback. Paired relative (NOT replication) weights define
unbiased covariance and effective n=1/sum(p**2). Scott/Silverman or positive
covariance factor, bw_adjust, bounded grid/cut/clip. Common_norm denominators
include ALL usable selected mass, including skipped singular hues, or each
curve independently. Cut/clip bound evaluation only, never fit rows or tail
renormalization. Full-line areas/endpoints are group shares or1; visible tails
can be truncated. Common_grid uses pooled weighted support and conditional
bandwidths. Cumulative sums full analytic Gaussian CDFs from -infinity, not
rebased/integrated grid heights or an exact empirical CDF.

Missing/zero weights/hue deselection excluded together, finite non-bool numeric
observations/nonnegative weights. Empty hues reserve style/color slots; singular
positive-weight groups skip without invented bandwidth/CDF/legend, warning
configurable. Scaled weights/centered coordinates, positive cross-product
covariance correction, retained nearby-value low bits and accurate bounded
positive-sum evaluation preserve extreme cases; nonfinite/empty/unresolvable
derived quantities fail. Primary2D line/fill v-h with exact alpha/outline/width,
hue dash/hatch/ref metadata. Log display requires positive raw observations
AND support; fits raw density units with no Jacobian/log transform, linear
height axes. No bivariate/contours/stack/multiple/date/y2/callable/other kernels/
stat_scale/intervals/kwargs. Weighted violin is supported separately through violin weights.
[Executable comparison](../examples/kde_semantics.py).

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
hue order reserves colors/hatches/dashes. Primary2D bars/steps, v/h and positive observation
logs only, raw widths even on logs and linear height axes. Exact alpha/edge/width
and reference metadata. Multiple='layer' overlays full bins; grouped 'stack'
adds heights in hue order, 'dodge' splits raw bin width across ALL selected hue
slots (including empty/outside-support hues). Heights, normalization and cumulative
semantics are unchanged. Density/frequency still use original bin widths, so
dodging reduces rectangle area without height correction. Separate-normalized
stacks sum the original per-curve distributions, not a renormalized pooled fit.
Nonfinite/lost positive stack increments and collapsed dodge slots fail before
any artists. Element='step' adds one unfilled native stairs patch per observed
hue: layer closes to zero, stack outlines absolute top and previous baseline.
Edges/heights/statistics stay unchanged; empty hues reserve color/theme dashes,
edge_color overrides the stroke, exact alpha/width include zero. No step+dodge,
filled steps, custom step dashes, fill/poly/discrete/automatic bin estimator/KDE/
bivariate/date/y2/intervals/kwargs. This is not full upstream parity; own
in-range normalization is explicitly specified.
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
mass uses scaled, unrounded row prefixes with an online float expansion;
strict tails sum from the right, not unstable subtraction. Proportion/percent
avoid total-weight overflow; raw count-mass overflow fails per curve. Empty
hues have no artist/legend; explicit hue order reserves shared colors/dashes.
Primary Cartesian2D, v/h, positive log observation axes/linear mass, exact named
line width/style/alpha/color and reference metadata only. No bins/KDE/fitting,
intervals/Kaplan-Meier/censoring, markers, date/2-D/y2/continuous semantic maps or
arbitrary kwargs. [Executable example](../examples/ecdf_semantics.py),
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
Bootstrap defaults to independent rows; `weights` supports means with paired-row
CI and `units` supports two-stage (units then within-unit rows) bootstrap. Weights
are not sampling probabilities; zero-weight rows are excluded. Point estimates
remain observation-weighted, not equal-unit means. Missing required rows are
dropped; fewer than two observations or units omit intervals with a warning.
`order`/`hue_order` select and reserve categorical slots. Horizontal geometry,
bar gap/value labels, normalized and stacked counts are supported on linear axes.
The count denominator is all usable selected rows across categories and hues.
This remains **partial functionality**, not complete Seaborn equivalence.
Native/log extends this subset as below; arbitrary callable estimators and
broader audited inference/mapping gaps remain.

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
Stacked counts require linear values and no explicit baseline; native/log categories
and global denominator/center labels work. New subset is primary 2-D; old linear
ordinal y2 remains. No automatic scale inference, arbitrary callables or parity
promise. [Executable comparison](../examples/statistical_scales.py).

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
not an optimal packing solver or a cross-layer collision guarantee. Overcrowding
retains rows at gutters with possible overlap; warn_thresh defaults to .05 and
0 reports any crowding. Numeric native/log categories are supported;
arbitrary shape, style/date mappings and y2 remain unsupported.

Opt-in `semantics={"size": "mass"}` adds one numeric size role with a selected
layer-local domain and honest diameter guides. Missing size joins the same
category/value/hue cohort; norms clip rather than filter. Facet/dropna/mixed-family
scales and semantic hue/style are rejected. [Exact scope](SWARM_SIZE.md).
Swarm-only named sizes pool deduplicated original rows, not observations/colours;
guides share the size domain once per panel. [Shared scope](SWARM_SHARED_SIZE.md).
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

### Letter-value first subset

`boxenplot(value, group=category)` or `boxenplot(category, value, group=hue)`
uses linear-interpolated raw-data quantiles, not confidence intervals. Four named
stopping rules (tukey/proportion/trustworthy/full) follow the Seaborn 0.13.2
[LetterValues formulas](https://github.com/mwaskom/seaborn/blob/v0.13.2/seaborn/_statistics.py).
Named depths cap at 32; explicit integers are 1..32. Full extends to min/max.
Exponential/linear widths encode depth; area uses actual probability mass/band
height within a cell, including extended full-depth tails. Zero-height area
bands have zero width; constant cells use exponential widths. This robust tied/
full-area policy is explicit, not a blanket claim of upstream numerical identity.
Median and strictly outside raw observations can be hidden/styled separately.
Orders reserve empty slots and hue colours/hatches stay shared across cells.
Numeric native/log axes are supported with explicit data/axis statistics;
weights/units and arbitrary component kwargs remain unsupported. [Executable comparison](../examples/letter_value_categories.py).

### Box/violin categorical subset

One-column `.box(value, group=category)` / `.violin(value, group=category)`
retain native one-based positions. Adding y opts into category x/value y with
group-as-hue nesting; orientation does not change argument roles. Required
missing rows drop listwise and orders reserve empty slots without invented marks.
Numeric dodge is the total hue-offset span (None auto, 0 overlays); gap shrinks
allocated body width. Whiskers follow native IQR/percentile observed-endpoint
rules, not CIs; notches use deterministic Gaussian median approximations.
Violins use native Gaussian KDE, per-violin widths and observed min/max extent.
Numeric native/log and positive log-value primary axes are supported;
this is not full upstream semantics.

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
styles/markers/sizes are bounded; no callback, arbitrary kwargs, precomputed bxp,
per-band/per-hue maps or new inference. JSON/schema/actions/editor, horizontal/
vertical/native log and unchanged coordinates are verified; 48 new tests.
[Executable comparison](../examples/distribution_components.py).

### Violin inner/density subset

Named box/quart/point/stick or None inners, exactly two selected/reserved hue split,
width/area/count profiles and bandwidth/support controls are connected to JSON/
actions/editor/rendering. Defaults remain legacy median/width/cut0. Named/None
inners reject showmean/median/extrema flags; only legacy uses those controls.
Point/stick preserve selected rows up to 10000/layer, without sampling.

Area uses a common density peak in fitted coordinates, not a promise of identical
truncated polygon area. Count scales each peak-normalized profile by cell n /
reference maximum n. Common_norm=False compares within hue across categories;
True compares all cells/hues (area/count only). Cut is [0,10] bandwidths; clip
is raw finite/None bounds limiting support, not fitting rows/counts/inner marks.
Split halves share a seam; gap shrinks outer width, positive dodge is rejected.
Empty/singular cells stay honest; log inverse geometry covers every native artist.
Callable KDE, arbitrary-hue split, inner kwargs and wider mappings are
still unsupported. Relative weighted KDE/marks are described below. [Executable comparison](../examples/violin_semantics.py).

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
| Lines, scatter, steps, errorbars, filled bands | Partial | Full artist properties, finite hlines/vlines, arbitrary fills/spans, horizontal bands and asymmetric x errors |
| Bars and pies | Partial | `barh`, stacking/bottom/alignment, per-bar styling/labels, pie annotations and wedge/text options |
| `stem` | Partial: vertical numeric primary/y2 stems, explicit raw baseline, source order/duplicates and positive log axes | No horizontal/group/facet/semantic mappings; [scope](STEM.md) |
| `stairs` | Partial: supplied heights/explicit N+1 edges, vertical outline/raw baseline/linear primary-y2 | No rebinning, fill/open/log/group/facet; [scope](STAIRS.md) |
| `eventplot` | Partial: single numeric train, vertical raw offset/length, linear primary-y2 | No group/facet/log/date mappings; [scope](EVENTPLOT.md) |
| `broken_barh` | Partial: start/duration intervals in one raw bottom/height band, overlaps retained, linear primary-y2 | No dates/group/facet/log mappings; [scope](BROKEN_BARH.md) |
| Histograms, boxplots, violins, ECDF | Partial families; dedicated weighted ECDF/proportion/percent/count/complement/v-h, grouped histogram stack/dodge and unfilled layer/stack steps | Histogram step+dodge/filled steps/fill/poly/discrete/auto-bin/bivariate controls, precomputed box statistics and wider distribution controls |
| Scalar images and contour fields | Partial | Explicit coordinate grids/extents, masks, RGB(A) images, `pcolor`/`pcolormesh`, `spy` and detailed contour controls |
| Triangulated fields | Missing | `triplot`, `tripcolor`, `tricontour`/`tricontourf` and triangulated surfaces |
| Vector fields | Partial: 2-D `quiver` | `streamplot`, barbs, more vector controls and 3-D quiver |
| 3-D | Partial: scatter/line/unit-grid surface/wireframe | Explicit surface coordinates, trisurf, 3-D bars/contours/quiver, voxels and camera/aspect controls |
| Signals and spectra | Missing | Spectrogram, PSD/CSD/coherence and magnitude/phase spectrum workflows |
| Axes and layout | Partial: regular panels, ratios, shared axes, y2, polar/3-D | Real temporal axes (ISO strings currently become categories), tick locators/formatters, more scale parameters, secondary x axes, inset/nested/mosaic layouts |
| Color and legends | Partial: LCH colormaps and auto linear normalization | Named/custom colormaps, fixed/shared vmin/vmax, log/centered norms, colorbar placement/ticks and legend columns/handler controls |
| Annotations, patches, tables | Partial text/annotate and reference lines | Arbitrary patches/paths, spans, tables, annotation transforms and path effects |
| Animation, GUI widgets, event callbacks, arbitrary artists | Python-native | A separate interaction scope, not automatically editable JSON features |

Use native Matplotlib methods when their semantics fit; do not rewrite its
plotting engine or introduce a hypothetical second-renderer abstraction.
Where newer upstream APIs are used, retain the supported minimum version with
an explicit guard/fallback, or leave the feature clearly version-gated.

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
