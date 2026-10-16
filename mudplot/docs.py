"""Auto-generated documentation from the engine's own introspection.

The same data that powers ``capabilities()`` / ``json_schema()`` for AI agents
is turned into human-readable Markdown here — one source of truth, two
audiences. Pure and dependency-free; used by the CLI (``mudplot docs``) and by
``dashboard/`` to render a reference page alongside the interactive editor.
"""

from __future__ import annotations

from .capabilities import capabilities

__all__ = ["reference_markdown"]


def _layers_section(caps: dict) -> str:
    lines = ["## Layers\n"]
    for name, spec in sorted(caps["layers"].items()):
        req = ", ".join(f"`{f}`" for f in spec["required"]) or "—"
        opt = ", ".join(f"`{f}`" for f in spec["optional"]) or "—"
        lines.append(f"### `{name}`\n")
        lines.append(f"- **required**: {req}")
        lines.append(f"- **optional**: {opt}\n")
    return "\n".join(lines)


def _facets_section(caps: dict) -> str:
    facets = caps["facets"]
    return (
        "## Automatic facet grids\n\n"
        "Build a single template's layers/axes first, then call "
        "`facet(row=..., col=..., row_order=..., col_order=..., col_wrap=..., "
        "share_x='all', share_y='all')`. The `SetFacets` action materializes "
        "ordinary panels with exact `filters`; the original data stays intact. "
        "Later edits address explicit panel indices. Figure size is unchanged.\n\n"
        "- First-seen levels or explicit selecting/reserving orders; missing facet "
        "keys drop. Bool/numeric keys are distinct; duplicate/ambiguous labels fail. "
        "Row-major cross products, col-only wrapping, no padding panels. "
        f"At most {facets['max_panels']} cells.\n"
        "- Selection precedes cell-local statistics, weights/units, normalization "
        "and coordinate validation. Category/hue slots reserve pooled levels. "
        "Independent scatter/lineplot roles get named shared mapping domains; "
        "pooling deduplicates original row IDs, not per-cell indices.\n"
        "- Source layer/title/reference metadata is copied. Titles add facet keys; "
        "legends remain panel-scoped. Hide repeats explicitly. New data keep the "
        "materialized selectors/orders; rebuild the grid to add new levels.\n"
        "- Raw line/scatter/bar/errorbar/band/stripplot/regplot/rug groups support "
        "hue_order selection/reservation. Facets pool stable raw group slots; "
        "missing groups consume colour/style/dodge positions without fake artists. "
        "Raw path order, duplicate x, gaps, supplied bars/errors stay unchanged; "
        "no automatic statistical conversion. Defaults without hue_order stay legacy.\n"
        "- Primary Cartesian2D only. No matrices/3D/polar/y2 or legacy c/colorbars. "
        "Hist requires HistogramSpec and explicit common edges; KDE "
        "requires KDESpec. Full upstream parity remains open; pair matrices "
        "and joint histogram composition are documented separately.\n"
    )


def _joint_section(caps: dict) -> str:
    joint = caps["joint_grid"]
    return (
        "## Joint scatter/regression and histogram marginals\n\n"
        "Build one raw scatter/regplot plus optional annotations, then call "
        "`joint(bins=20, ratio=3, marginal_stat='density', marginal_kind='hist')`. The "
        f"`{joint['action']}` action creates three panels: main top-left, "
        "y marginal right, x below. The unused corner has no axes. "
        "Set total figure size explicitly.\n\n"
        "- All panels carry identical dynamic `dropna` x/y/group selectors. "
        "Original observations remain in the spec; unrelated missing columns do "
        "not remove cases. Hue orders select/reserve common group slots.\n"
        "- X is linked by column, y by row: counts/densities never share a scale "
        "with measurement values. Typed common-bin marginal histograms normalize "
        "over the paired cohort, not extra unpaired observations.\n"
        "- count/density/probability/percent; integer bins and ratio [1,10]. "
        "No complete pairs fails atomically. Main labels/styles/references remain; "
        "marginal legends are suppressed. Later edits are panel-scoped.\n"
        "- marginal_kind='kde' accepts strict KDESpec/dict via kde= for bandwidth, "
        "grid, cut/clip, common normalization/grid and fill. Density only: no "
        "custom histogram bins, weights or cumulative CDF. Singular fits keep "
        "existing skip/warning rules; finite support need not integrate to one.\n"
        "- Raw primary Cartesian2D only: no semantic roles, c/colourbar, "
        "y2, weights, hexbin joint kinds or nested facet composition. "
        "Histogram derived-bin/log guards still apply. Wider joint options remain "
        "planned; pair scatter matrices are a separate workflow.\n"
    )


def _pair_section(caps: dict) -> str:
    pair = caps["pair_grid"]
    return (
        "## Pair scatter matrices and named axes\n\n"
        "`plot(data).pair(columns, group=None, hue_order=None, bins=20, "
        "diag_stat='density', diag_kind='hist')` builds a square matrix from one empty "
        f"panel using `{pair['action']}`. Select 2..{pair['max_variables']} numeric "
        "columns; source data, theme, size and legend settings stay intact.\n"
        "- Off-diagonal scatter cells drop only missing x/y/group cases. Diagonal "
        "histograms use each variable's nonmissing observations, not global "
        "listwise deletion. Counts can differ by cell. Hue slots are shared.\n"
        "- AxisSpec.share_id links x by variable column and measurement y across "
        "off-diagonal rows; diagonal density/count y is never joined. Limits "
        "remain automatic after data refresh. Review final dimensions explicitly.\n"
        "- `share_axis('x'|'y', name, panel=...)` / SetAxisShare also names manual "
        "primary Cartesian groups. Figure sharing must be none; conflicting "
        "scales/explicit limits fail before rendering. None clears the name.\n"
        "- diag_kind='kde', kde=KDESpec/dict uses configured Gaussian densities "
        "on the same univariate cohorts. KDE requires density and default bins; "
        "weighted/CDF options are rejected, singular curves warn/skip.\n"
        "- Raw categorical-group subset: no corner/triangular grid, "
        "semantic/continuous hue, weights, callable or nested grid. "
        "All-missing or nonnumeric selected variables fail; empty bivariate cells "
        "remain empty without fake observations.\n"
    )


def _heatmap_section(caps: dict) -> str:
    heatmap = caps["heatmap"]
    return (
        "## Typed heatmap display controls\n\n"
        "`heatmap(matrix, heatmap=HeatmapSpec(...))` or a strict dict opts into "
        "finite colour bounds, linear/log normalization, diverging center, robust "
        "visible-value percentiles, boolean mask, raw-value cell annotations, "
        "labels and square cells. None retains the legacy imshow behavior.\n"
        "- Mask does not rewrite source data. Masked values are excluded from "
        "normalization and text; all masked fails. robust uses 2nd/98th percentiles; "
        "explicit bounds override. center requires linear/diverging and bounds "
        "straddling it. log requires positive visible values and bounds.\n"
        "- annot=True uses bounded fmt strings and stronger black/white contrast "
        "after image alpha compositing, not a universal accessibility certificate. "
        f"At most {heatmap['max_annotations']} visible annotation cells. "
        "Typed line_width/edge_color control cell borders; xlabels/ylabels must "
        "match matrix shape. Axis coordinates stay linear cell indices.\n"
        "- Empty/nonfinite/jagged matrices, invalid masks/options and unrepresentable "
        "derived colour spans fail. No input mutation, clustering or custom cell "
        "annotation matrix is implied. Existing colorbar/clabel controls remain.\n"
    )


def _regression_section(caps: dict) -> str:
    regression = caps["regression"]
    return (
        "## Configured regression and residuals\n\n"
        "`regplot(x,y,regression=RegressionSpec(...))` or a strict dict selects "
        "poly/logx/Huber robust/binomial-logit/LOWESS. None retains legacy "
        "polynomial behavior; degree remains 1..10 for poly, 1 for other models.\n"
        "- `residplot` is a regplot alias with residual=True: scatter observed y "
        "minus row predictions in original order plus one zero guide. No input "
        "rewrite/deviance conversion/automatic residual smoother. Joint rejects "
        "residual templates because its marginals use raw y.\n"
        "- Logx requires positive predictor values. Logistic needs both numeric "
        "0/1 response classes; separated/nonconverged fits fail without implicit "
        "regularization. LOWESS frac and iterations are checked; other models "
        "reject ignored smoothing options.\n"
        "- Poly/logx retain opt-in normal-approximation mean-fit CI only; residual "
        "and optional-model CI/weights/bootstrap remain unsupported. Fits happen "
        "per selected group/cell. Log coordinates/predictions must be positive.\n"
        f"- Typed models cap {regression['max_rows']} rows/layer, LOWESS "
        f"{regression['max_lowess_rows']} rows/group. Missing/nonfinite selected "
        "coordinates fail; existing panel selectors can select complete cases.\n"
        "- Robust/logistic/LOWESS effects require optional mudplot[regression] "
        "(statsmodels>=0.14.1). Pure construction/validation/JSON/actions stay "
        "standard-library-only. No global RNG or new mandatory dependency.\n"
    )


def _cluster_section(caps: dict) -> str:
    cluster = caps["clustermap"]
    return (
        "## Hierarchical clustered heatmaps\n\n"
        "`clustermap(matrix, cluster=ClusterSpec/dict, heatmap=HeatmapSpec/dict)` "
        "uses optional SciPy linkage/dendrogram effects, not a new core dependency. "
        "Row/column fits or validated supplied linkages define leaf order; labels, "
        "mask and colour strips follow exactly the same permutations.\n"
        "- Row/col sample z_score or min-max standard_scale is opt-in and exclusive. "
        "Source values remain in JSON; annotations/colour show the transformed "
        "display matrix. Mask hides display only, not values used in clustering.\n"
        "- Ward/centroid/median require Euclidean distances. Constant transforms, "
        "undefined distances, bad linkage topology/counts and nonfinite derived "
        "results fail without jitter, imputation or fabricated trees. Single-item "
        "axes omit their tree. Optimal ordering is deterministic for a locked SciPy.\n"
        f"- At most {cluster['max_dimension']} rows/columns; one categorical colour "
        "strip per axis. Own primary Cartesian panel only, no sharing/cropped "
        "limits/extra layers. Existing heatmap annotations/norms/borders apply; "
        "log display cannot combine with standardization.\n"
        "- `pip install '.[cluster]'` from this Unreleased source tree supplies "
        "SciPy>=1.10 plus render. Pure specs/actions/validation stay dependency-free.\n"
    )


def _statistics_section(caps: dict) -> str:
    stats = caps["statistics"]
    lines = ["## Raw-data statistical layers\n"]
    lines.append(
        "`barplot` and `pointplot` aggregate raw observations per category/hue; "
        "`countplot` counts observations without a y column. "
        "`bar` remains the precomputed-value primitive.\n"
    )
    lines.append("Set a layer's `stat` object to configure named estimation.\n")
    lines.append(
        "- `lineplot(x,y)` is a separate numeric-predictor workflow, leaving raw "
        "`line` unchanged. Per-x mean/seeded pointwise CI is the default; no "
        "simultaneous confidence-band or whole-curve bootstrap claim. Units "
        "resample within x cells, not longitudinal curves. Numeric/log predictor, "
        "data/axis-log response, horizontal display and reserved hue slots. "
        "sort=True ascending; False per-hue first-observed order. Bands require "
        "monotonic x and split at missing bounds; bars allow nonmonotonic paths. "
        "error_alpha sets exact band opacity (default0.2*line alpha); caps/stroke "
        "are bars-only. No category/date x, y2, dodge/order or independent "
        "size/style mappings in this subset."
    )
    lines.append("- Estimators: " + ", ".join(f"`{s}`" for s in stats["estimators"]))
    lines.append(
        "- Intervals: `sd` / `se` (sample ddof=1; multiplier default 1), "
        "`pi` (observation percentiles), `ci` (percentile-bootstrap estimates). "
        "PI/CI default to 95 percent; `None` disables intervals. SE is SEM "
        "and requires the mean estimator; count estimates require no intervals."
    )
    lines.append(
        "- Bootstrap uses a local stored seed (default 0), bounded chunks and "
        f"1..{stats['max_bootstraps']} resamples (default 1000)."
    )
    lines.append(
        "- Missing required x/y/group/weight/unit rows and zero-weight rows are "
        "excluded; malformed values fail. Fewer than two observations or independent "
        "resampling units retain estimates but omit requested intervals with a warning."
    )
    lines.append(
        "- Categories default to ordinal first-seen or explicit `order`/`hue_order`. "
        "Orders select levels and reserve empty slots without invented estimates. "
        "General intervals need not contain the estimate and are not clipped."
    )
    lines.append(
        "- Statistical layers use Cartesian 2-D; numeric native/log categories and "
        "positive log values are supported on primary axes. Linear ordinal y2 "
        "behavior stays unchanged; horizontal/native/log y2 is rejected."
    )
    lines.append(
        "- `weights` supports means with no interval or paired-row bootstrap CI; "
        "weights are not sampling probabilities. `units` opts into two-stage "
        "bootstrap (units then rows within selected units); the point estimate "
        "remains observation-weighted, not an equal-unit mean."
    )
    lines.append(
        "- Count `normalize`: count, probability/proportion, percent; denominator "
        "is all usable selected rows across categories/hues, not per-cell totals."
    )
    lines.append(
        "- `orient='h'` swaps geometry, not argument roles: x is still the category. "
        "Use `gap`, bounded `label_format`/`value_labels`; countplots can `stack`. "
        "Horizontal statistical plots do not route to y2."
    )
    lines.append(
        "- `native_scale=True` selects numeric physical categories, not bool/string/"
        "date; order selects/reserves, not reorders them. Bar width/point dodge "
        "use minimum selected/reserved axis-coordinate spacing (log10 on log "
        "categories; singleton1). Native bar_width in (0,1], point dodge in [0,1]."
    )
    lines.append(
        "- `stat_scale='data'` retains raw estimates on log value axes. Explicit "
        "'axis' computes mean/median/min/max and SD/SEM/PI/CI in log10 coordinates "
        "and inverse-maps centers/endpoints. Weights and units stay paired to rows. "
        "Axis/log sum and count are rejected, not interpreted as products/powers."
    )
    lines.append(
        "- Nonstack bar/count `baseline` is a finite raw-value coordinate, default0 "
        "on linear values; positive explicit baseline is required on log values. "
        "Body runs baseline->estimate, not baseline+estimate. Labels show the "
        "estimate and clear actual interval endpoints toward/away from the baseline. "
        "Stacked counts require linear values and reject explicit baseline, but "
        "support native/log categories; normalization denominators stay unchanged."
    )
    lines.append(
        "- Nonpositive derived log estimate/interval endpoints or inverse overflow "
        "fail before artists, never silently clipped. Pure validation checks row/"
        "scale/baseline contracts; derived bounds are checked in the NumPy effect. "
        "Callable estimators and broader size/style/date mappings are unsupported. "
        "Unknown statistical options are never silently ignored.\n"
    )
    lines.append("| stat field | type | default |")
    lines.append("| --- | --- | --- |")
    for f in stats["fields"]:
        lines.append(f"| `{f['name']}` | `{f['type']}` | `{f['default']!r}` |")
    lines.append("")
    return "\n".join(lines)


def _distributions_section() -> str:
    return """## Box and violin distributions

- Legacy `box(value, group=category)` / `violin(value, group=category)` keep
  their one-column meaning and one-based native positions. With both columns,
  `box(category, value, group=hue)` / `violin(category, value, group=hue)` nest
  hue within ordinal categories; `orient='h'` changes geometry, not argument roles.
- `order`/`hue_order` select/reserve levels; required missing rows drop listwise.
  Empty cells have no invented marks/legend entries. Singleton/constant cells
  remain real degenerate distributions. Numeric native/log categories and
  positive log-value axes are supported on primary Cartesian axes; no y2.
- `width` sets total distribution span (nested default 0.8); numeric `dodge`
  sets the total hue-offset span (None auto, 0 overlays). `gap` shrinks the
  allocated body width by that fraction; colours/hatches stay shared by hue.
- Box `whis` is a nonnegative IQR multiplier (native default 1.5) or increasing
  percentile pair such as [5, 95]. Whiskers use native observed endpoints;
  they are not confidence intervals. `notch` uses the native deterministic
  Gaussian median approximation, not ambient random bootstrap. `showmeans` /
  `showfliers`, outline/line styling and flier marker/size are supported.
- Violin `bw_method` is scott, silverman or a positive numeric KDE factor;
  `points` is 2..1000 (default 100). Native Gaussian densities normalize each
  violin to its allocated width and stop at observed min/max. `showmeans`,
  `showmedians` (default True), `showextrema`, outlines and inner-line styling
  are supported. Defaults retain that path; named inner/split/normalization/
  support options below opt into extended native geometry. Weighted KDE,
  arbitrary callable bandwidth and inner/component kwargs remain unsupported.
- Default fill alpha follows the existing distribution convention: alpha 1
  selects 0.6; smaller explicit alpha values are retained. Unsupported new
  options fail explicitly rather than silently changing distributions.
"""


def _actions_section(caps: dict) -> str:
    lines = ["## Actions (JSON action vocabulary)\n"]
    lines.append("Every mutation is one of these — send as")
    lines.append('`{"type": "<Name>", ...}` to `mp.apply([...])`.\n')
    for name, field_list in sorted(caps["actions"].items()):
        lines.append(f"### `{name}`\n")
        lines.append("| field | type | required | default |")
        lines.append("| --- | --- | --- | --- |")
        for f in field_list:
            lines.append(
                f"| `{f['name']}` | `{f['type']}` | {f['required']} | "
                f"`{f['default']!r}` |"
            )
        lines.append("")
    return "\n".join(lines)


def _themes_section(caps: dict) -> str:
    lines = ["## Themes\n", f"Available presets: {', '.join(caps['themes'])}.\n"]
    lines.append("## Journals\n")
    for name, prof in sorted(caps["journal_profiles"].items()):
        size = prof["figure_size_in"]
        fs = prof["base_font_pt"]
        lines.append(f"- **{name}**: default figure size {size}, base font {fs:g}pt")
    lines.append("")
    return "\n".join(lines)


def _projections_section(caps: dict) -> str:
    values = ", ".join(f"`{name}`" for name in caps["projections"])
    return f"## Panel projections\n\nAvailable: {values}.\n"


def _components_section() -> str:
    return """## Independent distribution components

`box(..., components={...})` accepts body/whisker/cap/median/mean/flier;
`boxenplot` accepts only body/median/flier (no fictitious whiskers or means).
Typed ComponentStyleSpec and DistributionComponentsSpec are also public.
Absent components/properties inherit current native/layer/hue styles. Explicit
component properties override layer shorthands, never change observations or stats.
Body color overrides the base hue; boxen retains lighter tail tiers (none hides
fill). Redundant hue hatches stay unless body.hatch overrides; empty disables.
Body alpha is exact [0,1], including opaque1/transparent0, unlike legacy alpha1->.6.

- Body: color (base fill), edge_color, line_width/style, alpha, hatch.
- Whisker/cap/median: color (stroke), line_width/style, alpha.
- Mean/flier: those line properties plus edge_color/face_color (marker outline/
  fill), marker, marker_size and marker_edge_width. Stroke color does not imply
  marker fill/edge changes. Mean style requires showmeans=True. Styles for explicitly
  hidden fliers/boxen medians fail clearly. Explicit cap/body styles enable their
  native artists even if ambient boxplot rc hides them; omitted defaults unchanged.
- Colors: hex RGB/RGBA, bounded basic names, C0..C9 or none. Line styles: named
  `-`/`--`/`:`/`-.`/`none` tokens. Sizes finite [0,1000], marker_size>0.
  Hatch uses at most32 native symbols. No callbacks, arbitrary kwargs, per-band/
  per-hue style maps, bootstrap or precomputed bxp interpretation.

Unknown nested keys fail in loader/schema; wrong roles/value constraints fail
validation rather than being dropped. JSON/actions/editor and native/log/
orientation routes retain the same geometry; styles stay declarative, not
escape-hatch edits to a Figure.
"""


def _violin_section() -> str:
    return """## Extended violin options

Defaults remain `inner='legacy'`, `density_norm='width'`, `common_norm=False`,
`split=False`, `bw_adjust=1`, `cut=0`, no clip: native median marks, fixed maximum
width and observed min/max support. New fields are only supported for violin.

- `inner`: 'box' (IQR, observed 1.5-IQR whiskers, median marker; not a CI), 'quart'
  (25/50/75 percentile spans), 'point' (all observations), 'stick' (one local
  profile-width segment per observation), or None (no inner marks). 'legacy'
  alone accepts `showmeans/showmedians/showextrema`. Named/None inner styles
  reject these flags instead of ignoring them. Marker/size apply to box/point;
  stroke style applies to all inner components. Point/stick cap at 10000 selected
  usable observations/layer without sampling. Singleton/constants stay degenerate.
- `split=True` requires exactly two selected/reserved hues in category/value
  nesting, sharing a category center; first hue left/below, second right/above.
  Empty halves are not invented. Explicit positive dodge is incompatible. Gap
  shrinks the outer half-widths, not the seam. This is not arbitrary-hue split.
- `density_norm`: 'width' normalizes each peak; 'area' divides all profiles by
  a common reference peak in fitted-coordinate units; 'count' additionally scales
  each peak-normalized profile by cell n / reference maximum n. `common_norm=False`
  compares within hue across categories; True compares all cells/hues. True is
  rejected for width where it has no effect. Cut/clip truncate finite grids, so
  'area' is a shared density scale, not an exact equal-polygon-area guarantee.
  Constant cells have no finite KDE area and remain finite degenerate bodies.
- `bw_adjust`: finite multiplier in (0,1000] on named/numeric sample-SD bandwidth.
  `cut`: [0,10] bandwidths beyond observed extrema. `clip`: [lower,upper] finite
  increasing raw-value bounds, either bound may be None; limits support only, not
  fitting data/counts/summaries/inner observations. Empty intersections fail clearly.
  No callable KDE and no SciPy requirement.
- `weights`: paired finite nonnegative relative row mass, NOT replicated samples.
  Missing/zero-weight rows are excluded before positivity; at most 10000 usable
  rows/layer. Gaussian covariance is unbiased weighted covariance with effective
  n for Scott/Silverman. `count` uses total weight mass, not row count or effective
  n; common scaling of all weights does not change widths. Quart/box/medians use
  inverse right-continuous weighted ECDF (all ties; no interpolation), so even
  unit weights intentionally differ from legacy NumPy linear quantiles. Legacy
  means are weighted in declared coordinates; point/stick retain each positive
  row once, never replicate or sample. Singleton/constants remain observed
  degenerate bodies, no invented bandwidth. Cut/clip never trim fit/inner rows.
  Bounded chunk evaluation; unresolvable bandwidth/support/mass ratios fail.
  Unweighted calls retain the existing native/linear-quantile behavior.
- `stat_scale` still chooses data vs explicit axis (log10) fitting coordinates;
  clip bounds stay in raw units, and all artists inverse-map. Log values and clip
  bounds must be positive; a data-space extended support crossing zero fails,
  rather than silently clipping. Use positive clip bounds or axis-space statistics.
"""


def _letter_values_section(caps: dict) -> str:
    maximum = caps["letter_values"]["max_depth"]
    return f"""## Letter-value distributions

`boxenplot(value, group=category)` or `boxenplot(category, value, group=hue)`
computes per-cell raw-data quantiles with linear interpolation, not confidence
intervals, IQR whiskers or KDE. Category x remains category in horizontal plots.
Numeric native/log categories and positive log-value axes are supported.
`stat_scale='data'` preserves raw quantiles; 'axis' opts into log10 quantiles.
No y2 or semantic size mappings yet.

- `k_depth`: tukey (default), proportion, trustworthy, full or integer 1..{maximum}.
  Named rules are bounded to 1..{maximum}. For n usable rows: tukey uses
  max(1, int(log2(n))-3); full uses int(log2(n))+1 and includes min/max.
- proportion uses int(log2(n))-int(log2(n*outlier_prop))+1 (default .007);
  `outlier_prop` must be in (0,1) and is rejected with any other rule.
- trustworthy uses int(log2(n/(2*z*z)))+1, z the standard-normal quantile
  at 1-trust_alpha/2 (default .05). `trust_alpha` must be in [1e-12,1) and
  is rejected with any other rule. These rules do not turn bands into a CI.
- `width_method`: exponential (default), linear or area. Largest band width
  is the allocated category/hue width. Area normalizes actual probability
  mass/band-height within each cell (including extended full-depth tails).
  Zero-height bands have zero area width; entirely constant cells use
  exponential widths. Median stays at its raw value, spanning allocated width.
- `width` defaults .8, in (0,1]; `dodge` is total hue span <=width (None auto,
  0 overlays), gap shrinks slots. Orders reserve empty slots without fake data;
  required missing rows drop listwise. One-column positions are one-based.
- `showmedians`/`showfliers` default True. Fliers are raw rows strictly outside
  outer letter values, not 1.5-IQR outliers; full depth has none. Hollow diamond
  flier default is 3pt, outline/median .8pt; sizes in [0,1000]. Named supported
  markers: o/d/D/s/^/v/+/x/./*. Colours, outlines, alpha and hue hatches are shared;
  outer tiers are lighter. Weights/units, arbitrary kwargs, whis/notches, means
  and KDE controls fail explicitly rather than silently changing semantics.
"""


def _categorical_scales_section() -> str:
    return """## Native and log categorical coordinates

Box, violin, boxenplot and swarmplot accept `native_scale=True` (default False)
for finite numeric category IDs, not strings/bools/datetimes. A category column
is required (legacy single-column group counts). Order selects/reserves numeric
locations; it does not physically reorder them. Native axes use automatic numeric
locators. Width/dodge are fractions of minimum selected/reserved spacing, measured
in log10 on a log category axis; one level uses spacing 1. Gap shrinks slots.

Positive log-value observations are required after selection/listwise dropping.
Summary types default to `stat_scale='data'`, preserving raw-data estimation
including legacy single-column logs. Explicit `stat_scale='axis'` computes
summaries/KDE in log10 coordinates and inverse-maps every band/line/tail. Neither
choice is a CI. Swarm always retains raw values; it accepts no statistic mode.
Legacy ordinal and one-based defaults stay unchanged. Nested ordinal categories
cannot be logged; use native numeric coordinates. Legacy one-column box/violin
log position behavior remains. Shared axes reject mode/scale conflicts.
Nonfinite inverse geometry (or data-space notches crossing zero on log axes)
fails clearly rather than clipping; choose axis-space statistics or adjust controls.
Statistical barplot/pointplot/countplot use the same native spacing/selection;
see raw-statistics above for explicit positive bar baselines and log estimates.
Broader size/style/date mappings remain outside the subset. No new required
dependencies or automatic scale inference.
"""


def _swarm_section(caps: dict) -> str:
    maximum = caps["swarm"]["max_observations"]
    return f"""## Swarm observations

`swarmplot(category, value, group=hue)` preserves each observed numeric value.
Circular markers pack greedily in display space at **every draw**, after actual
layout/axis transforms; DPI, size, limits and linear/positive-log value axes are
accounted for. x stays categorical in horizontal orientation. No RNG or jitter.

- First-seen or explicit `order`/`hue_order` select/reserve levels; required
  missing rows drop listwise. Empty cells have no invented marks or legend data.
- `width` is the total category span (0 < width <= 1; default 0.8). Numeric
  `dodge` is the total hue span <= width (None auto; 0 packs hues jointly).
  `gap` shrinks allocated widths. Palette slots remain shared/reserved by hue.
- Only uniform circular `marker='o'` is supported; marker_size is positive
  points (default 6), line_width is points (default 0.5), both <=1000. Stroke
  width contributes to collision diameters. Colour/edge/alpha are supported;
  shape/size semantic mappings and y2 are not. Numeric native/log category
  coordinates are supported with `native_scale=True`.
- At most {maximum} usable observations per layer, with bounded O(n^2 log n)
  worst-case packing. This is deterministic greedy packing, not an optimal
  arrangement or a guarantee against crowding/collisions across separate layers.
- If a slot cannot fit circles, all rows remain at gutters with possible overlap.
  `warn_thresh` is a fraction in [0,1], default 0.05 (0 reports any overcrowding).
  Warn once per collection; `crowded_count` on the returned collection reports
  its current draw. Reduce marker size, enlarge the figure or use stripplot.
"""


def _palettes_section(caps: dict) -> str:
    lines = ["## Palettes\n"]
    lines.append(
        "LCH-based. Kinds: " + ", ".join(f"`{k}`" for k in caps["palettes"]) + ".\n"
    )
    lines.append(
        "- `qualitative`: equal(-ish) lightness, maximum hue contrast, "
        "worst-case ΔE00 across normal vision + protan/deutan CVD "
        "simulation maximised. A `lightness_jitter` (default 6) keeps true "
        "greyscale/B&W print distinguishable; see `Palette.report()` for "
        "measured safety, not an assumed guarantee.\n"
        "- `sequential` / `diverging`: perceptually-uniform ramps, gamut-clipped.\n"
    )
    lines.append('### Named presets (`.palette(preset="...")`)\n')
    lines.append(
        "Pre-tuned `qualitative` parameter sets, each measured (not assumed) "
        "CVD-safe (worst-case ΔE00 ≥ 8) and true-greyscale-safe (min L* gap "
        "≥ 3) up to `max_verified_n` categories — see "
        "`tests/test_palette_presets.py`. Beyond that count, more colours are "
        "still generated but safety is no longer verified; pair with "
        "`.encoding(hatches=[...])` for bar/box/violin fills, which stays "
        "distinguishable in B&W print regardless of colour count.\n"
    )
    lines.append("| preset | max verified n | description |")
    lines.append("| --- | --- | --- |")
    for name, p in sorted(caps["palette_presets"].items()):
        lines.append(f"| `{name}` | {p['max_verified_n']} | {p['description']} |")
    lines.append("")
    return "\n".join(lines)


def _tex_section(caps: dict) -> str:
    lines = ["## TeX presets (WYSIWYG sizing)\n"]
    lines.append("| preset | columnwidth (pt) | textwidth (pt) | font (pt) | cols |")
    lines.append("| --- | --- | --- | --- | --- |")
    for name, p in sorted(caps["tex_presets"].items()):
        lines.append(
            f"| `{name}` | {p['columnwidth_pt']} | {p['textwidth_pt']} | "
            f"{p['fontsize_pt']} | {p['columns']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _ecdf_section(caps: dict) -> str:
    lines = [
        "## Empirical cumulative distributions\n",
        "`plot.ecdf(x, stat='proportion', complementary=False, weights=None, "
        "group=None, hue_order=None, orient='v')` stores raw observations and "
        "a typed `ECDFSpec` in `layer.ecdf`; None selects the same defaults.",
        "- F(t) = sum(w for X<=t)/sum(w); `count` uses cumulative weight mass "
        "(observation counts with no weights); `percent` is proportion times 100. "
        "Normalization is within each "
        "selected curve, never a pooled/global-hue denominator.",
        "- Complement is strict X>t, including ties. Steps are right-continuous: "
        "post in v, pre after swapping coordinates in h; x stays the raw value "
        "argument. Knots aggregate ties and show the full jump at the minimum. "
        "Only observed support is drawn; no infinite tail or invented sample.",
        "- Drop rows missing x/group/weights and zero-weight rows. Finite numeric "
        "values/weights exclude bool; weights must be nonnegative. Empty curves "
        "have no artist/legend; explicit hue order selects/reserves color/dashes. "
        "Weights preserve row pairs. Count-mass overflow fails; scaled "
        "proportion sums avoid it, and strict tails sum from the right rather "
        "than subtracting nearly-equal numbers.",
        "- Primary Cartesian 2-D only; observation axes may be positive log, "
        "mass axes stay linear (include 0). Supports theme/line color/dash/width/"
        "alpha and legend/reference metadata. No bins/KDE, intervals, censoring/"
        "Kaplan-Meier, arbitrary callables, date/2-D ECDF, markers or y2 routing. "
        "Unsupported/no-op options fail, not silently ignored. Not full parity.\n",
        "| ecdf field | type | default |",
        "| --- | --- | --- |",
    ]
    for field in caps["ecdf"]["fields"]:
        lines.append(
            f"| `{field['name']}` | `{field['type']}` | `{field['default']!r}` |"
        )
    lines.append("")
    return "\n".join(lines)


def _histogram_section(caps: dict) -> str:
    lines = [
        "## Weighted histogram statistics\n",
        "New statistics/geometry/style options, including multiple/element, use "
        "typed `HistogramSpec` at layer.histogram. None retains legacy hist "
        "density/group/bin/alpha behavior without numeric or default changes.",
        "- Shared integer bins pool usable selected observations; explicit finite "
        "increasing raw edges are also supported. Half-open [left,right) bins, "
        "closed final edge. Missing required/zero-weight rows are excluded; finite "
        "numeric values/weights exclude bool. Weights are nonnegative row mass.",
        "- count=bin mass; frequency=mass/raw width; probability/proportion=mass/"
        "denominator; percent=100*proportion; density=mass/(denominator*raw width). "
        "Only in-range mass enters denominators. Common_norm=True pools across "
        "selected hues; False normalizes within each curve. No-op raw normalization "
        "choices are rejected. Thus density integrates to1, not sums heights to1.",
        "- Cumulative count sums mass; normalized cumulative sums probabilities; "
        "density cumulative integrates mass (a binned CDF), not density heights. "
        "No cumulative frequency. Shared normalizations end at each hue's mass "
        "share; separate at1/100. This is not an exact unsmoothed ECDF.",
        "- Normalized weights are scaled before summing; bin masses are summed "
        "independently, not subtracted from a large prefix. Cumulative prefixes "
        "reuse the accurate unrounded row expansion. Nonfinite raw total mass/"
        "derived widths/heights fail before drawing, no silently clipped bins.",
        "- Primary2D bars/unfilled steps v/h; x is the observed column. Observation "
        "logs need positive values/edges, density uses raw widths (not log units). "
        "Height axes are linear (include zero bins); generated invalid log/"
        "collapsed edges fail. Empty curves have no bars/legend; hue order reserves "
        "colors/hatches. Exact alpha/edge/line width and reference metadata supported.",
        "- Multiple='layer' overlays full bins. Grouped 'stack' adds heights in "
        "hue order; 'dodge' splits each raw bin into equal hue slots, including "
        "reserved empty hues. Heights/normalization/cumulative semantics do not "
        "change. Density/frequency still use ORIGINAL bin widths: dodge reduces "
        "drawn area, with no height correction. Stacked tops must stay finite "
        "and increase for nonzero bins; collapsed dodge slots fail before drawing.",
        "- Element='bars' retains bars. Element='step' draws one unfilled native "
        "stairs patch per observed hue with the same edges/heights. Layer closes "
        "to zero; stack outlines the absolute top and previous baseline. Empty "
        "hues reserve color/theme dash slots; edge_color overrides stroke color. "
        "Exact alpha/width, including zero, retained. No step with dodge or fill.",
        "- No fill/poly/custom step dashes/discrete/named auto-bin/KDE/bivariate/"
        "date/y2/"
        "interval controls or arbitrary kwargs. Legacy hist still uses old "
        "Matplotlib effects. This first subset is not full upstream parity.\n",
        "| histogram field | type | default |",
        "| --- | --- | --- |",
    ]
    for field in caps["histogram"]["fields"]:
        lines.append(
            f"| `{field['name']}` | `{field['type']}` | `{field['default']!r}` |"
        )
    lines.append("")
    return "\n".join(lines)


def _kde_section(caps: dict) -> str:
    lines = [
        "## Weighted univariate Gaussian KDE\n",
        "New KDE options opt into strict `KDESpec` at layer.kde. None preserves "
        "the legacy unweighted 1.06*sample-SD*n**(-1/5),200-point curve, including "
        "constant fallback. This is not SciPy's default Scott factor/parity.",
        "- Paired finite numeric (not bool) observations/nonnegative weights; "
        "missing required/zero weights/hue deselection drop before positivity. "
        "Weights are RELATIVE, not replicated counts. With p=w/sum(w), effective "
        "n=1/sum(p**2); unbiased covariance=sum(p*(x-mean)**2)/(1-sum(p**2)). "
        "Scott factor=n_eff**(-1/5), Silverman=(3*n_eff/4)**(-1/5); numeric "
        "bw_method is a covariance factor, not absolute bandwidth. "
        "Bandwidth=sqrt(covariance)*factor*bw_adjust.",
        "- Density is sum(w_i*GaussianPDF_i)/denominator, analytic cumulative "
        "sum(w_i*GaussianCDF_i)/denominator from -infinity, NOT a grid integral/"
        "rebased clip CDF/ECDF. Common_norm=True divides by all usable selected "
        "mass INCLUDING skipped singular hues, False within each curve. "
        "Full-line areas/endpoints are shares or1; finite support need not be1.",
        "- Cut extends observed extremes by bandwidths; clip restricts evaluation "
        "only, never removes fit rows or renormalizes visible tails. Each curve "
        "fits its own bandwidth. Common_grid=True uses pooled weighted support "
        "but retains conditional bandwidths. Finite increasing grid required; "
        "nonfinite/empty/unresolvable support, bandwidth or heights fail clearly.",
        "- Singleton/constant positive-weight curves are skipped, no invented "
        "density/CDF/legend; warn_singular controls the warning. Empty hues reserve "
        "color/dash/hatch slots without warnings. Dominant-weight covariance uses "
        "positive cross-products (not cancelling1-sum(p**2)), normalized weights/"
        "coordinates are scaled, centered differences preserve nearby low bits, "
        "and evaluation streams bounded chunks with accurate positive sums.",
        "- Primary Cartesian2D line or fill, v/h; x remains observed column. "
        "Positive raw observations AND support required on log display axes: "
        "no implicit clipping or log fitting/Jacobian conversion. Density/CDF "
        "axis linear. Exact alpha/width, fill-only edge_color, hue dashes/hatches "
        "and legend references. Width0 hides stroke, not filled mass.",
        "- No bivariate/contours/stack/multiple/date/y2/callable bandwidth/other "
        "kernels/stat_scale/interval/kwargs. Weighted violin stays separate and "
        "unsupported; broader upstream mapping remains incomplete.\n",
        "| kde field | type | default |",
        "| --- | --- | --- |",
    ]
    for field in caps["kde"]["fields"]:
        lines.append(
            f"| `{field['name']}` | `{field['type']}` | `{field['default']!r}` |"
        )
    lines.append("")
    return "\n".join(lines)


def _kde2d_section(caps: dict) -> str:
    lines = [
        "## Weighted bivariate Gaussian KDE contours\n",
        "`kde2d(x,y,...)` stores strict KDE2DSpec. None on direct specs uses its "
        "defaults; univariate KDE/legacy behavior is unchanged.",
        "- Paired x/y/group/weights exclude missing/zero weights/hue deselection. "
        "Finite non-bool numeric coordinates and nonnegative relative weights, "
        "not replicated samples. Full unbiased weighted covariance and effective "
        "n; d=2 Scott and Silverman coincide at n_eff**(-1/6). Numeric method is "
        "a covariance factor, not absolute bandwidth. No jitter/regularization.",
        "- Common_norm uses all usable selected mass (including skipped singular "
        "hues) or each curve separately. Cut/clip restrict evaluation only, never "
        "fit rows or density tail normalization. Common_grid uses pooled fit "
        "support but each hue's conditional covariance. Singleton/collinear/"
        "numerically rank-deficient curves skip with optional warning, no fake "
        "2-D density/legend. Empty hues reserve color/dash/hatch slots.",
        "- Levels are increasing ENCLOSED HDR fractions conditional on trapezoidal "
        "mass WITHIN the evaluation grid. Sort density strata descending and "
        "include all threshold ties. Density itself stays raw-normalized; only "
        "HDR selection conditions on grid mass. Therefore changing clip/grid "
        "can change thresholds. Approximate finite-grid regions are NOT confidence "
        "intervals or guarantees of full-space probability. Unresolved tied "
        "thresholds fail, no fabricated level jitter.",
        "- Both axes use raw units, also on log display: positive observations "
        "AND generated support, no Jacobian/log fit or implicit clipping. "
        "Cartesian2D contours/fill, exact alpha/outline/width, per-hue dash/hatch "
        "and legend references. Fill uses single-hue light-to-dark bands, plus "
        "outlines. Native legend-only proxies carry no observations/limits.",
        "- Lazy NumPy only; scaled/centered covariance with positive cross-product "
        "correction and stable product/quotient avoid premature over/underflow; "
        "bounded32-point by1024-row matrices, not full grid-by-data allocation. "
        "Nonfinite/empty/unresolvable support, densities/grid mass/levels fail. "
        "Limits:10000 usable rows,2..256 nodes/axis,1..16 levels strictly in(0,1).",
        "- No cumulative/orient/date/y2/colorbar/arbitrary density levels/kernel/"
        "callable bandwidth/stat_scale/interval/stack/multiple/kwargs or upstream "
        "parity claim. Weighted violin remains separate.\n",
        "| kde2d field | type | default |",
        "| --- | --- | --- |",
    ]
    for field in caps["kde2d"]["fields"]:
        lines.append(
            f"| `{field['name']}` | `{field['type']}` | `{field['default']!r}` |"
        )
    lines.append("")
    return "\n".join(lines)


def _scatter_semantics_section(caps) -> str:
    config = caps["scatter_semantics"]
    return (
        """## Independent scatter semantics

`semantics=None` keeps old group/c/marker/colourbar calls. Opt into SemanticSpec
or a strict dict, or ergonomic hue/size/style column keywords. Do not combine
full config and active mapped keywords. Configuration arrays canonicalize tuples;
JSON decoding uses JSON scalar types. At least one independent role is required.

- Hue kind categorical(default) uses reserved LCH colour slots; numeric explicitly
  uses one linear normalization over all selected rows, not each style subset.
- Size kind numeric(default) or categorical; `sizes=[3,9]` are DIAMETERS in points,
  linearly mapped then squared to native scatter areas. No scalar size override.
  Bounds are clipped for mapping only, never observation filtering. Exact zero
  sizes retain invisible observations; positive area underflow fails explicitly.
- Style always categorical and independent, never inferred from hue. Distinct
  named filled markers, no recycling; reserve ordered empty slots without ghost
  points/legend data. Bool categories remain distinct from numeric values, and
  indistinguishable label strings are rejected.
- Missing required x/y/role rows excluded listwise; explicit categorical orders
  select/reserve. Numeric roles need finite non-bool values; x/y numeric with
  positive selected observations on logs. Bounds may be explicit finite increasing
  pairs or selected global min/max; auto-constant maps midpoint and one guide,
  including subnormal values. Stable scaling preserves extremes/nearby low bits.
- Legend entries identify roles: observed categorical levels, or numeric mapping
  calibration guides (NOT sampled/observed data). Guides add no data limits;
  `legend=False` disables role guides. Global reference metadata needs a layer
  label; per-hue references unsupported. No artificial observations/sampling/RNG.
- `scale_id`: optional figure-named scope. Members need identical role/kind/
  order/bounds/sizes/markers and numeric hue cmap (legend may differ). Pool the
  union of their selected row ids in original table order without duplicate
  observation weighting. Missing coordinates in one panel do not shrink shared
  normalizations or reset categorical colours/sizes/markers. Different names
  stay independent; None preserves layer-local behavior. Reserved shared colour
  blocks precede legacy entries. Shared category/numeric guides describe the
  pooled scope and occur once per panel; layer labels remain separate. No fake
  points/limits. Pooled rows/levels/marker counts are checked as well as members.
  This is a sharing foundation, not automatic data-driven faceting.
- Limits: 10000 usable rows,64levels, enough distinct allowed markers, primary
  Cartesian2D; no group/c conflict, outline override, colourbar/date/y2 in subset.
  Existing c/colourbar stays available outside this new role path. Automatic
  facets, colourbars and temporal semantics remain planned.

### Independent lineplot roles

Lineplot accepts the same typed/dict/column-keyword semantic configuration.
Each distinct RAW hue/size/style tuple defines its own curve; numeric clipping
never merges tuple identities. Estimates/pointwise intervals/weighted and within-x
unit bootstrap remain within predictor/curve cells, NOT whole-curve inference.
Missing roles and missing/zero weights/units drop listwise before domains/logs;
weight/unit column validity remains the existing statistical contract.
`sizes` interpolate MAIN LINE STROKE widths in points (not scatter areas or
uncertainty widths). Style maps unique filled markers; optional `dashes` are
1..4 distinct `-`, `--`, `-.`, `:` styles, enough for selected/reserved levels.
None leaves dashes uniform; no automatic hue-to-style inference. Marker size
may be uniform, mapped line width/marker/dash overrides reject. Zero width keeps
markers/intervals/rows but omits strokes (native zero-scaled-dash safe).
Shared scale_id also works across lineplot/scatter with matching config: pooled
colour/physical-point domains, but size means thickness vs diameter per geometry.
Guide blocks consolidate separately per geometry, clearly named line-width guides,
never fabricated points/datalim. References need explicit dataset label. Numeric
primary2D v/h/data/log-fit, sort/missing bounds preserve existing contracts. Limits
10000 rows/256 raw curves/64levels/enough markers/dashes. No raw-line semantic
builder/date/y2/colourbar/callable/simultaneous/bootstrap-whole-curve claim.

"""
        + "| semantic field | type | default |\\n| --- | --- | --- |\\n"
        + "\\n".join(
            f"| `{item['name']}` | `{item['type']}` | `{item['default']!r}` |"
            for item in config["fields"]
        )
        + "\\n"
    )


def reference_markdown() -> str:
    """Render the full engine reference as a Markdown document."""
    caps = capabilities()
    parts = [
        "# mudplot engine reference\n",
        "_Auto-generated from `mudplot.capabilities()` / `mudplot.json_schema()` "
        f"— spec version `{caps['spec_version']}`. Do not edit by hand; "
        "regenerate with `python -m mudplot docs`._\n",
        _layers_section(caps),
        _facets_section(caps),
        _joint_section(caps),
        _pair_section(caps),
        _heatmap_section(caps),
        _regression_section(caps),
        _cluster_section(caps),
        _statistics_section(caps),
        _scatter_semantics_section(caps),
        _ecdf_section(caps),
        _histogram_section(caps),
        _kde_section(caps),
        _kde2d_section(caps),
        _distributions_section(),
        _components_section(),
        _violin_section(),
        _letter_values_section(caps),
        _categorical_scales_section(),
        _swarm_section(caps),
        _palettes_section(caps),
        _themes_section(caps),
        _projections_section(caps),
        _tex_section(caps),
        _actions_section(caps),
    ]
    return "\n".join(parts)
