# mudplot engine reference

_Auto-generated from `mudplot.capabilities()` / `mudplot.json_schema()` — spec version `0.1`. Do not edit by hand; regenerate with `python -m mudplot docs`._

## Layers

### `annotate`

- **required**: `text`, `at`
- **optional**: `to`, `color`, `alpha`, `axis`, `annotation`, `path_effects`

### `band`

- **required**: `x`, `y`, `y2`
- **optional**: `group`, `hue_order`, `label`, `color`, `alpha`, `axis`, `orient`, `fill`, `native_style`, `line_width`, `path_effects`

### `bar`

- **required**: `x`, `y`
- **optional**: `group`, `hue_order`, `label`, `color`, `bar_width`, `bar_geometry`, `edge_color`, `line_width`, `yerr`, `y_lower`, `y_upper`, `error_color`, `error_line_width`, `capsize`, `capthick`, `alpha`, `axis`

### `bar3d`

- **required**: `x`, `y`, `z`, `spatial`
- **optional**: `color`, `alpha`

### `barbs`

- **required**: `x`, `y`, `u`, `v`, `vector`
- **optional**: `color`, `line_width`, `alpha`, `axis`, `group`, `hue_order`, `label`

### `barh`

- **required**: `x`, `y`
- **optional**: `group`, `hue_order`, `label`, `color`, `bar_width`, `bar_geometry`, `edge_color`, `line_width`, `alpha`, `axis`

### `barplot`

- **required**: `x`, `y`
- **optional**: `semantics`, `cmap_kind`, `colorbar`, `clabel`, `group`, `stat`, `native_scale`, `stat_scale`, `baseline`, `orient`, `order`, `hue_order`, `gap`, `value_labels`, `label_format`, `label`, `color`, `bar_width`, `edge_color`, `line_width`, `error_color`, `error_line_width`, `capsize`, `capthick`, `alpha`, `axis`, `transforms`

### `box`

- **required**: `x`
- **optional**: `y`, `group`, `orient`, `order`, `hue_order`, `width`, `dodge`, `gap`, `native_scale`, `stat_scale`, `whis`, `components`, `notch`, `showmeans`, `showfliers`, `label`, `color`, `edge_color`, `line_width`, `line_style`, `marker`, `marker_size`, `alpha`, `box`, `semantics`, `axis`, `cmap_kind`, `colorbar`, `clabel`

### `boxenplot`

- **required**: `x`
- **optional**: `y`, `group`, `orient`, `order`, `hue_order`, `width`, `dodge`, `gap`, `native_scale`, `stat_scale`, `k_depth`, `components`, `boxen`, `weights`, `semantics`, `axis`, `colorbar`, `clabel`, `cmap_kind`, `width_method`, `outlier_prop`, `trust_alpha`, `showfliers`, `showmedians`, `label`, `color`, `edge_color`, `line_width`, `line_style`, `marker`, `marker_size`, `alpha`

### `broken_barh`

- **required**: `x`, `y`
- **optional**: `baseline`, `width`, `label`, `color`, `edge_color`, `line_width`, `line_style`, `alpha`, `axis`, `group`, `hue_order`, `lane_step`

### `clustermap`

- **required**: `matrix`
- **optional**: `cluster`, `heatmap`, `cmap_kind`, `colorbar`, `clabel`, `alpha`, `line_width`, `edge_color`

### `contour`

- **required**: `matrix`
- **optional**: `cmap_kind`, `colorbar`, `clabel`, `alpha`, `levels`, `grid`

### `contour3d`

- **required**: `matrix`, `levels`, `spatial`
- **optional**: `cmap_kind`, `colorbar`, `clabel`, `alpha`, `line_width`

### `contourf`

- **required**: `matrix`
- **optional**: `cmap_kind`, `colorbar`, `clabel`, `alpha`, `levels`, `grid`

### `contourf3d`

- **required**: `matrix`, `levels`, `spatial`
- **optional**: `cmap_kind`, `colorbar`, `clabel`, `alpha`

### `countplot`

- **required**: `x`
- **optional**: `group`, `stat`, `native_scale`, `baseline`, `orient`, `order`, `hue_order`, `gap`, `stack`, `value_labels`, `label_format`, `label`, `color`, `bar_width`, `edge_color`, `line_width`, `alpha`, `axis`, `semantics`, `colorbar`, `clabel`, `line_style`, `cmap_kind`, `transforms`

### `ecdf`

- **required**: `x`
- **optional**: `ecdf`, `semantics`, `cmap_kind`, `colorbar`, `clabel`, `marker`, `marker_size`, `group`, `hue_order`, `orient`, `label`, `color`, `line_width`, `line_style`, `alpha`, `axis`, `transforms`

### `ecdf2d`

- **required**: `x`, `y`, `ecdf2d`
- **optional**: `group`, `hue_order`, `semantics`, `orient`, `axis`, `label`, `color`, `edge_color`, `line_width`, `line_style`, `alpha`, `cmap_kind`, `colorbar`, `clabel`, `transforms`

### `errorbar`

- **required**: `x`, `y`
- **optional**: `yerr`, `xerr`, `y_lower`, `y_upper`, `group`, `hue_order`, `label`, `color`, `error_color`, `error_line_width`, `capsize`, `capthick`, `marker`, `marker_size`, `line_width`, `alpha`, `axis`, `error_magnitudes`, `native_style`

### `eventplot`

- **required**: `x`
- **optional**: `baseline`, `width`, `label`, `color`, `line_width`, `line_style`, `alpha`, `axis`, `group`, `hue_order`, `lane_step`, `semantics`, `colorbar`, `clabel`, `cmap_kind`

### `heatmap`

- **required**: `matrix`
- **optional**: `heatmap`, `scalar_display`, `cmap_kind`, `colorbar`, `clabel`, `alpha`, `line_width`, `edge_color`

### `hexbin`

- **required**: `x`, `y`
- **optional**: `gridsize`, `mincnt`, `cmap_kind`, `colorbar`, `clabel`, `alpha`, `axis`

### `hist`

- **required**: `x`
- **optional**: `bins`, `density`, `histogram`, `group`, `hue_order`, `orient`, `label`, `color`, `edge_color`, `line_width`, `alpha`, `axis`, `semantics`, `colorbar`, `clabel`, `line_style`, `cmap_kind`, `transforms`

### `hist2d`

- **required**: `x`, `y`
- **optional**: `bins`, `histogram2d`, `group`, `hue_order`, `semantics`, `orient`, `label`, `color`, `edge_color`, `line_width`, `line_style`, `density`, `cmap_kind`, `colorbar`, `clabel`, `alpha`, `axis`, `transforms`

### `hline`

- **required**: `value`
- **optional**: `label`, `color`, `line_style`, `line_width`, `alpha`, `axis`

### `hlines`

- **required**: `segments`
- **optional**: `native_style`, `label`, `color`, `line_style`, `line_width`, `alpha`, `axis`, `path_effects`

### `hspan`

- **required**: `span`
- **optional**: `native_style`, `label`, `color`, `alpha`, `axis`, `path_effects`

### `imshow`

- **required**: `grid`
- **optional**: `matrix`, `cmap_kind`, `colorbar`, `clabel`, `alpha`, `scalar_display`

### `kde`

- **required**: `x`
- **optional**: `kde`, `semantics`, `stat_scale`, `cmap_kind`, `colorbar`, `clabel`, `group`, `hue_order`, `orient`, `label`, `color`, `alpha`, `line_width`, `line_style`, `edge_color`, `axis`, `transforms`

### `kde2d`

- **required**: `x`, `y`
- **optional**: `kde2d`, `semantics`, `orient`, `axis`, `cmap_kind`, `colorbar`, `clabel`, `group`, `hue_order`, `label`, `color`, `alpha`, `line_width`, `line_style`, `edge_color`, `transforms`

### `line`

- **required**: `x`, `y`
- **optional**: `group`, `semantics`, `line`, `native_style`, `orient`, `order`, `cmap_kind`, `colorbar`, `clabel`, `hue_order`, `label`, `color`, `line_width`, `line_style`, `drawstyle`, `marker`, `marker_size`, `alpha`, `axis`, `path_effects`, `transforms`

### `line3d`

- **required**: `x`, `y`, `z`
- **optional**: `group`, `label`, `color`, `line_width`, `line_style`, `marker`, `alpha`

### `lineplot`

- **required**: `x`, `y`
- **optional**: `semantics`, `line`, `order`, `native_scale`, `cmap_kind`, `colorbar`, `clabel`, `group`, `stat`, `orient`, `stat_scale`, `hue_order`, `sort`, `error_style`, `error_alpha`, `label`, `color`, `line_width`, `line_style`, `marker`, `marker_size`, `error_color`, `error_line_width`, `capsize`, `capthick`, `alpha`, `axis`, `transforms`

### `patch`

- **required**: `patch`
- **optional**: `native_style`, `path_effects`, `label`, `color`, `edge_color`, `line_width`, `alpha`, `axis`

### `pcolor`

- **required**: `matrix`, `grid`
- **optional**: `cmap_kind`, `colorbar`, `clabel`, `alpha`, `edge_color`, `line_width`, `scalar_display`

### `pcolormesh`

- **required**: `matrix`, `grid`
- **optional**: `cmap_kind`, `colorbar`, `clabel`, `alpha`, `edge_color`, `line_width`, `scalar_display`

### `pie`

- **required**: `x`, `y`
- **optional**: `color`, `alpha`, `pie_geometry`

### `pointplot`

- **required**: `x`, `y`
- **optional**: `semantics`, `cmap_kind`, `colorbar`, `clabel`, `group`, `stat`, `native_scale`, `stat_scale`, `orient`, `order`, `hue_order`, `dodge`, `label`, `color`, `line_width`, `line_style`, `marker`, `marker_size`, `error_color`, `error_line_width`, `capsize`, `capthick`, `alpha`, `axis`, `transforms`

### `quiver`

- **required**: `x`, `y`, `u`, `v`
- **optional**: `c`, `cmap_kind`, `colorbar`, `clabel`, `label`, `color`, `line_width`, `quiver_scale`, `quiver_width`, `alpha`, `axis`, `vector`, `group`, `hue_order`

### `quiver3d`

- **required**: `x`, `y`, `z`, `u`, `v`, `w`, `vector`
- **optional**: `color`, `line_width`, `alpha`, `group`, `hue_order`, `label`

### `regplot`

- **required**: `x`, `y`
- **optional**: `regression`, `semantics`, `edge_color`, `cmap_kind`, `colorbar`, `clabel`, `weights`, `degree`, `confidence`, `group`, `hue_order`, `label`, `color`, `line_width`, `line_style`, `marker`, `marker_size`, `alpha`, `axis`, `orient`

### `rug`

- **required**: `x`
- **optional**: `group`, `hue_order`, `label`, `color`, `alpha`, `line_width`, `line_style`, `orient`, `width`, `axis`, `semantics`, `cmap_kind`, `colorbar`, `clabel`

### `scatter`

- **required**: `x`, `y`
- **optional**: `semantics`, `native_style`, `group`, `hue_order`, `label`, `color`, `marker`, `edge_color`, `line_width`, `marker_size`, `alpha`, `c`, `scalar_display`, `cmap_kind`, `colorbar`, `clabel`, `axis`, `path_effects`

### `scatter3d`

- **required**: `x`, `y`, `z`
- **optional**: `group`, `label`, `color`, `marker`, `marker_size`, `alpha`, `c`, `cmap_kind`, `colorbar`, `clabel`

### `spectrum`

- **required**: `x`, `spectrum`
- **optional**: `y`, `label`, `color`, `line_width`, `line_style`, `alpha`, `cmap_kind`, `colorbar`, `clabel`, `citation`, `href`

### `spy`

- **required**: `matrix`, `grid`
- **optional**: `alpha`, `color`, `marker`, `marker_size`

### `stackplot`

- **required**: `x`, `y`, `group`
- **optional**: `color`, `line_width`, `line_style`, `alpha`, `axis`

### `stairs`

- **required**: `x`, `bins`
- **optional**: `baseline`, `label`, `color`, `line_width`, `line_style`, `alpha`, `axis`, `stairs`, `group`, `hue_order`

### `stem`

- **required**: `x`, `y`
- **optional**: `baseline`, `label`, `color`, `line_width`, `line_style`, `marker`, `marker_size`, `alpha`, `axis`, `orient`, `group`, `hue_order`, `semantics`, `colorbar`, `clabel`, `cmap_kind`

### `streamplot`

- **required**: `vector`
- **optional**: `color`, `line_width`, `alpha`, `label`

### `stripplot`

- **required**: `x`, `y`
- **optional**: `jitter`, `strip`, `semantics`, `cmap_kind`, `colorbar`, `clabel`, `edge_color`, `line_width`, `orient`, `order`, `dodge`, `native_scale`, `group`, `hue_order`, `label`, `color`, `marker`, `marker_size`, `alpha`, `axis`, `transforms`

### `surface`

- **required**: `matrix`
- **optional**: `cmap_kind`, `colorbar`, `clabel`, `alpha`, `spatial`

### `swarmplot`

- **required**: `x`, `y`
- **optional**: `group`, `semantics`, `orient`, `order`, `hue_order`, `width`, `dodge`, `gap`, `native_scale`, `warn_thresh`, `label`, `color`, `edge_color`, `line_width`, `marker`, `marker_size`, `alpha`, `pack_scope`, `axis`, `cmap_kind`, `colorbar`, `clabel`

### `table`

- **required**: `table`
- **optional**: —

### `text`

- **required**: `text`, `at`
- **optional**: `color`, `alpha`, `axis`, `annotation`, `path_effects`

### `tricontour`

- **required**: `x`, `y`, `c`, `triangulation`, `levels`
- **optional**: `cmap_kind`, `colorbar`, `clabel`, `alpha`

### `tricontourf`

- **required**: `x`, `y`, `c`, `triangulation`, `levels`
- **optional**: `cmap_kind`, `colorbar`, `clabel`, `alpha`

### `tripcolor`

- **required**: `x`, `y`, `triangulation`
- **optional**: `c`, `cmap_kind`, `colorbar`, `clabel`, `alpha`, `edge_color`, `line_width`

### `triplot`

- **required**: `x`, `y`, `triangulation`
- **optional**: `color`, `line_width`, `line_style`, `alpha`, `label`

### `trisurf`

- **required**: `x`, `y`, `z`, `triangulation`
- **optional**: `cmap_kind`, `colorbar`, `clabel`, `alpha`

### `violin`

- **required**: `x`
- **optional**: `y`, `violin`, `components`, `semantics`, `axis`, `cmap_kind`, `colorbar`, `clabel`, `group`, `orient`, `order`, `hue_order`, `width`, `dodge`, `gap`, `native_scale`, `stat_scale`, `bw_method`, `points`, `weights`, `inner`, `split`, `density_norm`, `common_norm`, `bw_adjust`, `cut`, `clip`, `marker`, `marker_size`, `showmeans`, `showmedians`, `showextrema`, `label`, `color`, `edge_color`, `line_width`, `line_style`, `alpha`

### `vline`

- **required**: `value`
- **optional**: `label`, `color`, `line_style`, `line_width`, `alpha`, `axis`

### `vlines`

- **required**: `segments`
- **optional**: `native_style`, `label`, `color`, `line_style`, `line_width`, `alpha`, `axis`, `path_effects`

### `voxels`

- **required**: `spatial`
- **optional**: `color`, `edge_color`, `line_width`, `alpha`

### `vspan`

- **required**: `span`
- **optional**: `native_style`, `label`, `color`, `alpha`, `axis`, `path_effects`

### `wireframe`

- **required**: `matrix`
- **optional**: `color`, `alpha`, `spatial`

## Automatic facet grids

Build a single template's layers/axes first, then call `facet(row=..., col=..., row_order=..., col_order=..., col_wrap=..., share_x='all', share_y='all')`. The `SetFacets` action materializes ordinary panels with exact `filters`; the original data stays intact. Later edits address explicit panel indices. Figure size is unchanged.

- First-seen levels or explicit selecting/reserving orders; missing facet keys drop. Bool/numeric keys are distinct; duplicate/ambiguous labels fail. Row-major cross products, col-only wrapping, no padding panels. At most 64 cells.
- Selection precedes cell-local statistics, weights/units, normalization and coordinate validation. Category/hue slots reserve pooled levels. Independent scatter/lineplot roles get named shared mapping domains; pooling deduplicates original row IDs, not per-cell indices.
- Source layer/title/reference metadata is copied. Titles add facet keys. The finite relplot/displot/catplot/lmplot builders reuse existing mark actions and optionally collect actual mapping legends once per figure. New data keep the selected cells and orders.
- Raw line/scatter/bar/errorbar/band/stripplot/regplot/rug groups support hue_order selection/reservation. Facets pool stable raw group slots; missing groups consume colour/style/dodge positions without fake artists. Raw path order, duplicate x, gaps, supplied bars/errors stay unchanged; no automatic statistical conversion. Defaults without hue_order stay legacy.
- Cartesian2D only; use the listed layer/axis admission rules. Faceted scatter-c shares one P01 raw calibration and optional figure bar. Typed integer histogram bins resolve to shared edges before local statistics; transformed histograms require explicit working edges. Pair and joint remain independently documented constructions.
- Opt into `facet(..., live=True)` / SetLiveFacets to retain a typed FacetTemplateSpec recipe with resolved fixed cell orders/selectors. `facet_template(panel, reset_orders=False)` / SetFacetTemplate is an explicit whole-template transaction: replace ALL intended cells and supersede cell-local layer/axis overrides. Ordinary panel edits remain local and saved materialized views stay authoritative on reopen; neither load nor SetData automatically reapplies the stored template.
- Same-channel category/hue slots remain resolved unless explicit new orders or reset_orders=True requests recapture. Changing a declared hue channel resolves that channel's own levels, not stale old labels. New facet levels never add cells. Compatible ratio-only edits preserve wrapped partial-grid identities and current ratios/sharing; structural grid replacements detach the binding. Invalid recipes/selectors and invalid generated cell views reject without dropping the binding.

## Joint views and paired marginals

Build one Cartesian scatter, regplot, hist2d or hexbin plus optional annotations, then call `joint()` (`SetJointGrid`). The center is top-left, y is right, x is below; the unused corner has no axes.

- Complete cases include the original x/y, selected roles and scatter c. `weights=` names one nonnegative mass column. Missing weights and zero weights contribute no row. Center bins do not remove marginal fit rows.
- Marginals are typed hist/KDE/ECDF. Weighted ECDF supports `complementary=True` for strictly greater mass. The true center y2 can share its observation scale with the right y without joining primary y.
- Documented center semantic mappings and one scalar c bar are distinct. Typed grouped hist2d reuses the paired field owner; `joint(group=...)` uses one actual native hex lattice with physical-count `mincnt`.
- Nested layouts and ordinary panel/action edits retain the raw table. See [joint scope](JOINT_GRID.md) for applicable roles and exact limits.

## Pair scatter matrices and named axes

`plot(data).pair(columns)` uses `SetPairGrid` on one empty panel. Select 2..8 numeric or explicitly temporal variables. `corner=True` builds the real lower triangle including its diagonal.

- Scatter cells use pairwise complete rows; typed histogram/KDE/ECDF diagonals use only their own variable. A single `semantics=` scope and `weights=` name original source roles/mass; scales never select rows.
- Named x columns and off-diagonal value-y rows share; statistic y axes stay independent. `complementary=True` selects strict ECDF survival.
- `corner` creates genuine N13 placements, not hidden upper panels. Ordinary nested edits and refills do not duplicate the raw source. See [pair scope](PAIR_GRID.md).

## Typed heatmap display controls

`heatmap(matrix, heatmap=HeatmapSpec(...))` or a strict dict opts into finite colour bounds, linear/log normalization, diverging center, robust visible-value percentiles, boolean mask, independent cell annotations, labels and square cells. None retains the legacy imshow behavior.
- Mask does not rewrite source data. Masked values are excluded from normalization and text; all masked fails. robust uses 2nd/98th percentiles; explicit bounds override. center requires linear/diverging and bounds straddling it. log requires positive visible values and bounds.
- annot=True uses bounded fmt strings unless annot_data supplies a same-shaped string matrix (empty strings allowed, <=512 characters/cell). Custom text stays literal and never replaces scalar colour values; masked cells have no text. Stronger black/white contrast follows image alpha compositing, not a universal accessibility certificate. At most 4096 visible annotation cells. Typed line_width/edge_color control cell borders; xlabels/ylabels must match matrix shape. Optional xrotation/yrotation are finite degrees in [-360,360]; axes stay linear cell indices.
- Empty/nonfinite/jagged matrices, invalid masks/options and unrepresentable derived colour spans fail. Custom annotation text/masks/labels reorder together for clustermap.
- Use `symlog` with positive `linthresh`, clipped `power` with positive `gamma`, or `boundary` with increasing finite edges and one swatch per interval. Boundary mode excludes robust bounds, center and vmin/vmax. `ColorbarOptionsSpec` sets side, raw-value ticks, named formatting, thickness and pad; `colorbar` and `clabel` still toggle and label it. Cells are finite numbers; nullable data requires explicit clustermap missingness. This is not the full P01 palette/shared-guide workflow.

## Regression inference and source-aligned diagnostics

`regplot(x,y,regression=RegressionSpec(...))` or a strict dict selects poly/logx/Huber/binomial-logit/LOWESS. Omitted controls retain legacy point behavior and unweighted poly/logx approximate normal mean bands.
- One Layer.confidence and explicit bootstrap {n_boot,seed} select uniform paired positive physical cases carrying original criterion masses/nuisance/source indices. All B remain; any required undefined replicate rejects. No retries, finite-only ranks or probability-weight draws.
- The shared type7 boundary gives nominal pointwise mean/operator uncertainty, not simultaneous/continuum/future-observation coverage. Weighted Huber uses canonical original-mass MAD0; weighted LOWESS uses physical-neighbor local SVD and weighted median robust passes. CI presence alone cannot switch the point factory.
- Partial is a complete-basis/one-intercept linear design, joint conditional Huber/logit, or explicit LOWESS two_stage with response add-back. Conditional curves use references; query predictions use actual nuisance values. Partial scatter is adjusted on raw predictor x.
- Explicit disjoint train/query selectors preserve original physical rows/duplicates/types. Query-only prediction may omit y; actual raw/deviance diagnostics require it. No implicit listwise omission or imputation.
- Residual mode owns one zero reference and optional independently specified FULL-pipeline trend. First take mean-response percentile bounds, then map them to fixed-observation raw/deviance uncertainty; the separately refitted trend has its own complete-pipeline statistic. Genuine infinite diagnostics reject with original source row, never clip.
- Typed selected rows <= 10000; LOWESS <= 5000 per fitted group. NEW complete design <=19; NEW invocation/figure work <=6B includes all actual stages/targets/tails and variable seed conversion. The256MiB managed/provider-reserve admission estimate is not RSS/native-artists/opaque-provider allocation or CPU/SLA guarantee. Empty explicit query never becomes in-sample.
- Actual v/h primary/y2 roles and existing canonical clocks are used. Natural-ln is display independent and declared calendar ln is origin dependent. Calendar-response residual durations remain refused. Fit/scatter/trend own real ComponentStyleSpec traits, not fictional guides.
- Advanced effects retain optional mudplot[regression], statsmodels>=0.14.1; pure specs/actions/schema/caps/validation remain standard-library-only. No new result API/command/store, weight-kind/method or mandatory dependency. See docs/REGRESSION.md and its Korean counterpart for equations/examples.

## Hierarchical clustered heatmaps

`clustermap(matrix, cluster=ClusterSpec/dict, heatmap=HeatmapSpec/dict)` uses optional SciPy linkage/dendrogram effects, not a new core dependency. Row/column fits or validated supplied linkages define leaf order; labels, mask and colour strips follow exactly the same permutations.
- Row/col sample z_score or min-max standard_scale is opt-in and exclusive. Source values remain in JSON; numeric annotations/colour show the transformed display matrix, while annot_data remains literal text. Mask hides display only, not values used in clustering.
- Ward/centroid/median require Euclidean distances. Constant transforms, undefined distances, bad linkage topology/counts and nonfinite derived results fail without jitter, imputation or fabricated trees. Single-item axes omit their tree. Optimal ordering is deterministic for a locked SciPy.
- Explicit `missing='complete_features'` admits literal nulls. Each named fit uses the features observed by every item on that axis; no pairwise substitution, imputation or dropped leaves. Visible nulls get a labelled slash, not a value colour or annotation.
- `row_distances` and `col_distances` accept labelled finite nonnegative condensed distances in original position order. They remain caller-owned on refresh. Raw supplied links stay unchanged; computed positive merge heights must survive rescaling. Cuts include equal subtree-max heights and optionally highlight the group containing an original-index anchor.
- At most 512 rows/columns. Ordered categorical tracks have explicit levels, colours, widths and legends; no inferred continuous categories. An independent primary Cartesian panel is required without shared/cropped axes or overlays. Matrix reservations are not an RSS or CPU-time promise. Log display cannot combine with standardization.
- `pip install '.[cluster]'` from this Unreleased source tree supplies SciPy>=1.10 plus render. Pure specs/actions/validation stay dependency-free.

## Raw-data statistical layers

`barplot` and `pointplot` aggregate raw observations per category/hue; `countplot` counts observations without a y column. `bar` remains the precomputed-value primitive.

Set a layer's `stat` object to configure named estimation.

- `lineplot(x,y)` is a separate numeric-predictor workflow, leaving raw `line` unchanged. Per-x mean/seeded pointwise CI is the default; no simultaneous confidence-band or whole-curve bootstrap claim. Units resample within x cells, not longitudinal curves. Numeric/log predictor, data/axis-log response, horizontal display and reserved hue slots. sort=True ascending; False per-hue first-observed order. Bands require monotonic x and split at missing bounds; bars allow nonmonotonic paths. error_alpha sets exact band opacity (default0.2*line alpha); caps/stroke are bars-only. Valid explicit temporal predictors/linear temporal-y2 paths remain supported; broader categorical predictors, horizontal line-y2 and simultaneous inference remain D01/F02 work.
- Estimators: `mean`, `median`, `sum`, `min`, `max`, `count`
- Intervals: `sd` / `se` (sample ddof=1; multiplier default 1), `pi` (observation percentiles), `ci` (percentile-bootstrap estimates). PI/CI default to 95 percent; `None` disables intervals. SE is SEM and requires the mean estimator; count estimates require no intervals.
- Bootstrap uses a local stored seed (default 0), bounded chunks and 1..100000 resamples (default 1000).
- Missing required x/y/group/weight/unit rows and zero-weight rows are excluded; malformed values fail. Fewer than two observations or independent resampling units retain estimates but omit requested intervals with a warning.
- Categories default to ordinal first-seen or explicit `order`/`hue_order`. Orders select levels and reserve empty slots without invented estimates. General intervals need not contain the estimate and are not clipped.
- Bar/point use actual primary or declared y2 targets in either orientation, native numeric/date categories, positive log response and declared calendar-response coordinates. Existing line/count target subsets are separate, not silently expanded.
- Weighted mean supports None/SD/SE/PI/CI; weighted observed LEFT median/min/max support None/SD/PI/CI; weighted total supports None/CI and count mass requires None. SD is observation spread, SE is mean-specific uncertainty, PI observation quantiles and CI percentile resampled estimators. Weights never become sampling probabilities. Units require paired two-stage CI (unit, then row), not unit means.
- Canonical integers/binary floats precede arithmetic and interpolation; SUM/MEAN do not erase representable cancellation residuals by MaxAbs scaling. Weighted variance uses physical-row reliability mass/Kish before ties; LEFT PI probabilities derive exactly from canonical PERCENT level: p=(100-Fraction(level))/200. At95 percent, [0,10,20] with weights[1,38,1] gives [0,10]. Unweighted type7 meaning and seeded CI percentile policy remain unchanged. A requested strict interval that cannot survive native rounding rejects; true atoms do not invent uncertainty.
- Units are opaque IDs, including empty strings; missing None/NaN exclude paired rows. NEW bool/numeric identity remains typed. Weighted SUM response units are value*weight-mass in the existing explicit N13 sharing gate, not a mean/raw value or COUNT mass. Legacy no-N13 sharing admission remains unchanged.
- Count `normalize`: count, probability/proportion, percent; denominator is all usable selected rows across categories/hues, not per-cell totals.
- `orient='h'` swaps geometry, not argument roles: x is still the category. Use `gap`, bounded `label_format`/`value_labels`; countplots can `stack`. Horizontal bar/point y2 categories use y2, with measurements on shared x.
- `native_scale=True` selects physical numeric categories (not bool/ordinal strings); declared date clocks enable canonical day slots. Order selects/reserves, not reorders physical positions. Bar width/point dodge use minimum selected/reserved axis-coordinate spacing (log10 on log categories; singleton1). Native bar_width in (0,1], point dodge in [0,1].
- `stat_scale='data'` retains raw estimates on log value axes. Explicit 'axis' computes mean/median/min/max and SD/SEM/PI/CI in log10 coordinates and inverse-maps centers/endpoints. Weights and units stay paired to rows. Axis/log sum and count are rejected, not interpreted as products/powers.
- Nonstack bar/count `baseline` is a finite raw-value coordinate, default0 on linear values; positive explicit baseline is required on log values. Body runs baseline->estimate, not baseline+estimate. Labels show the estimate and clear actual interval endpoints toward/away from the baseline. Stacked count log endpoints retain C06's explicit positive baseline/cumulative-top contract and unchanged normalization scopes.
- Nonpositive derived log estimate/interval endpoints or inverse overflow fail before artists, never silently clipped. Pure validation checks row/scale/baseline contracts; derived bounds are checked in the NumPy effect. Unknown statistical options and serialized callables reject. Shared bar/point hue/size/style keep raw tuples and typed keys; SIZE means bar BODY outline pt versus point marker DIAMETER pt (lineplot remains main stroke pt). Errors/caps and point connecting strokes stay independent. Styles use real body dashes/actual glyphs, with nondata mark-specific guides and shared original-row domains.
- NEW requests only: new weighted combinations, bar/point semantics or newly admitted target routes. Bounds10000 selected positive rows/256 drawn pointwise cells and2B ACTUAL unit-choice+case work/layer never attach to old weightedmeanNone/CI, unitsCI, countplot mass, unweighted/plain or existing semantic dense line merely from those fields. Active random/sample arrays stay<=1M; compact case counts retain original seeded associations without data replication. Exceeding NEW actual work rejects the WHOLE effect before row chunks/artists/editor commit, never a prefix CI or reduced n_boot. No SLA/RSS promise; uncapped hierarchical potential can exceed ordinary1B work.
- Stored facet templates remain explicit whole transactions; local edits stay local, reopen alone does not refit. Actual fixed selected views validate before commit without treating the undrawn source recipe as a physical layer. Calendar SUM/COUNT is rejected; NEW calendar bars need an explicit canonical UTC-day baseline. See STATISTICAL_WORKFLOW.md / STATISTICAL_WORKFLOW.ko.md.

| stat field | type | default |
| --- | --- | --- |
| `estimator` | `str` | `'mean'` |
| `errorbar` | `str or None` | `'ci'` |
| `level` | `float or None` | `None` |
| `n_boot` | `int` | `1000` |
| `seed` | `int` | `0` |
| `weights` | `str or None` | `None` |
| `units` | `str or None` | `None` |
| `normalize` | `str` | `'count'` |
| `normalize_scope` | `str or None` | `None` |

## Independent scatter semantics

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
- Limits remain 10000 usable rows/64 levels/enough distinct markers. Existing
  explicit F02 clocks and temporal y2 restrictions are unchanged; no legacy
  group/c with independent roles. Wider F01 families remain required.
- Numeric hue optionally uses `colorbar=True`; `clabel` is a string <=512 only
  with that request. Negative raw values/domains are valid. Guide geometry uses
  non-data [0,1] coordinates with exact raw-value ticks from the same stable
  clipped mapping/cmap as marks; observation axes/data/limits are unchanged.
  Constant domains show one solid midpoint swatch and one exact raw tick.
- A requested bar replaces numeric-hue calibration legends for its logical
  panel/shared scope, including earlier members and primary/y2 targets.
  Dataset/size/style guides remain; legend=False does not hide a requested bar.
  Empty local views create no bar. Requested shared labels must match.
- Scatter `edge_color` and `line_width` in [0,1000] points control outlines,
  independently from mapped marker diameters/areas. Omitted fields preserve
  native defaults. Example: `examples/semantic_colourbars.py`.

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
10000 rows/256 raw curves/64levels/enough markers/dashes. Numeric-hue bars share
the preceding contract. Raw-line/category/wider-y2/whole-curve inference and
other F01 family adapters remain required; no whole-row closure is claimed.

| semantic field | type | default |\n| --- | --- | --- |\n| `scale_id` | `str or None` | `None` |\n| `hue` | `str or None` | `None` |\n| `hue_kind` | `str` | `'categorical'` |\n| `hue_order` | `list[Any] or None` | `None` |\n| `hue_norm` | `list[float] or None` | `None` |\n| `size` | `str or None` | `None` |\n| `size_kind` | `str` | `'numeric'` |\n| `size_order` | `list[Any] or None` | `None` |\n| `size_norm` | `list[float] or None` | `None` |\n| `sizes` | `list[float]` | `[3.0, 9.0]` |\n| `style` | `str or None` | `None` |\n| `style_order` | `list[Any] or None` | `None` |\n| `markers` | `list[str]` | `['o', 's', 'D', '^', 'v', 'P', 'X']` |\n| `dashes` | `list[str] or None` | `None` |\n| `legend` | `bool` | `True` |\n
## Empirical cumulative distributions

`plot.ecdf(x, stat='proportion', complementary=False, weights=None, group=None, hue_order=None, orient='v')` stores raw observations and a typed `ECDFSpec` in `layer.ecdf`; None selects the same defaults.
- F(t) = sum(w for X<=t)/sum(w); `count` uses cumulative weight mass (observation counts with no weights); `percent` is proportion times 100. Normalization is within each selected curve, never a pooled/global-hue denominator.
- Complement is strict X>t, including ties. Steps are right-continuous: post in v, pre after swapping coordinates in h; x stays the raw value argument. Knots aggregate ties and show the full jump at the minimum. Only observed support is drawn; no infinite tail or invented sample.
- Drop rows missing x/group/weights and zero-weight rows. Finite numeric values/weights exclude bool; weights must be nonnegative. Empty curves have no artist/legend; explicit hue order selects/reserves color/dashes. Weights preserve row pairs. Canonical source/mass precedes tied prefixes and final float conversion; percent combines its unit before rounding, and strict complement uses exact right mass.
- Cartesian2D v/h uses the actual observation x or target y/y2 clock; the mass axis is linear, includes0 and cannot be a date. Independent SemanticSpec raw tuples retain stroke-point SIZE, not mass. Named style markers sit at actual right-continuous knots, not the prepended boundary sentinel; explicit marker_size stays uniform. No fit/interval/censoring or callback interpretation. Explicit paired fields use `ecdf2d` below.

| ecdf field | type | default |
| --- | --- | --- |
| `stat` | `str` | `'proportion'` |
| `complementary` | `bool` | `False` |
| `weights` | `str or None` | `None` |

## Rug observations (D07)

`rug(x, orient='v', height=None, semantics=None, axis='y')` retains individual
observations, duplicates and order. Vertical marks use shared x and point inward
from the bottom; horizontal marks use target y, from the left on primary y or
from the right on y2. Configure y2 first with `secondary_yaxis`.

- Height is an **axes fraction**, finite non-bool [0,1]; None keeps 0.04.
  It serializes in the existing `LayerSpec.width`, not a new field. Zero height
  retains zero-length segments. The blended transform follows layout/DPI.
- Only the observation dimension affects data limits/autoscaling or requests a
  temporal clock. The perpendicular axis can be log/date and remains untouched;
  height is never density, mass or a calendar duration.
- SemanticSpec/dict maps hue, stroke width in physical points, and categorical
  named dashes (`dashes` or default `-`, `--`, `-.`, `:`). Enough distinct patterns
  are required; common filled-marker settings do not turn rugs into points.
  Zero stroke keeps rows/segments and uses native solid zero-width geometry.
  Legacy group/c and scalar overrides of mapped roles reject.
- Shared scale_id reuses deduplicated raw-row pools, normalization and logical-
  panel colourbar intent. Stroke-only guide proxies contain no observations or
  filled point markers. One vectorized native LineCollection holds each semantic
  rug, without aggregating rows or imposing the curve-count cap; the existing
  10,000 semantic-row and resource limits remain.
- Group selection, facets (primary axes), explicit observation dates and positive
  log observations are supported. Missing required values drop listwise without
  rewriting source values, IDs or units. Numeric weights, inference/bootstrap
  and arbitrary native kwargs are not rug controls.

See `examples/rug_workflow.py` and the English/Korean feature coverage contract.

## Signal spectra (N11)

- **api**: `Plot.spectrum / LayerSpec.spectrum / SpectrumSpec`
- **required**: `fs: finite positive nonbool samples/second (Hz)`
- **kinds**: `['spectrogram', 'psd', 'csd', 'coherence', 'magnitude', 'angle', 'phase']`
- **windows**: `['boxcar', 'hann', 'hamming', 'blackman']`
- **detrend**: `['none', 'mean', 'linear']`
- **sides**: `['onesided', 'twosided']`
- **scaling**: `['density', 'spectrum']`
- **scale**: `['linear', 'dB']`
- **segmented**: `nfft=None means 256; full windows only; trailing partial retained but unused`
- **whole**: `magnitude/angle/phase use entire signal; nfft=None, overlap=0`
- **padding**: `pad_to >= effective window length; actual FFT parity defines Nyquist`
- **source**: `real plain JSON samples; missing/nonfinite/bool reject; no row dropping`
- **csd**: `display abs(mean(conj(FFT_x)*FFT_y)); computed phase is not set to zero`
- **phase**: `radians in ascending frequency order; zero coefficients undefined gaps; unwrap contiguous defined runs`
- **coherence**: `>=2 complete windows; zero-power bins undefined; no significance claim`
- **coherence_numeric**: `positive consumed-prefix channel scaling before detrend/FFT, then per-frequency maxima across segment vectors before powers/cross; exact zero bins stay zero; physical CSD unchanged`
- **line_references**: `nonempty labels/citation/href validated by shared core helpers; native SVG links and PGF figcite/href`
- **scalar_color**: `shared finite named/hex colour contract; clabel requires a spectrogram colourbar`
- **zero_stroke**: `line_width=0 uses native no-line style, retaining exact frequency/value artist data`
- **coherence_precision**: `if channel normalization would erase nonzero consumed samples, raise floating-point precision error before FFT; unused trailing partial never influences normalization`
- **undefined**: `derived gaps; all undefined rejects; no positive floor`
- **axes**: `primary Cartesian linear nontemporal; no groups/semantics/weights/selectors`
- **max_samples_per_channel**: `1000000`
- **max_fft**: `65536`
- **max_complex_cells**: `1048576`
- **fft_precision_limit**: `zero computed coefficient/power yields derived gaps; float64 window/detrend/FFT may round tiny true bins to zero; masks are not physical proof of exact zeros or high-dynamic-range exact/relative accuracy`

Density is |FFT|²/(fs*sum(window²)); spectrum divides by |sum(window)|². One-sided power doubles positive bins except DC and Nyquist only for even actual padded FFT length. Magnitude is |FFT|/|sum(window)|, not a peak-amplitude claim. CSD displays magnitude of the averaged complex cross-spectrum; coherence uses the squared magnitude of the average cross-spectrum, not averaged segment coherence. Zero computed phase coefficients/coherence power give derived gaps; float64 window/detrend/FFT can round tiny true bins to zero. Masks are not physical proof of exact zeros or a relative-accuracy guarantee. All-undefined results reject. Phase unwraps contiguous defined runs in ascending frequency order. Linear power zero is valid; dB uses 10log10 power or 20log10 magnitude re 1 declared unit, masking zero without a floor. Named detrend precedes symmetric NumPy windows. Explicit user labels are preserved, otherwise derived Hz/elapsed-second/power/radian labels apply. No inferential significance is claimed. Dedicated limits are algorithm bounds, not an SLA/RAM sandbox or changes to existing limits. See examples/signal_spectra.py and bilingual FEATURE_COVERAGE.

## Finite axis controls (N12)

- **status**: `N12 isolated implementation; qualification/integration tracked separately`
- **ScaleOptionsSpec**: `[{'name': 'base', 'type': 'float or None', 'required': False, 'default': None}, {'name': 'subs', 'type': 'list[float] or None', 'required': False, 'default': None}, {'name': 'linthresh', 'type': 'float or None', 'required': False, 'default': None}, {'name': 'linscale', 'type': 'float or None', 'required': False, 'default': None}, {'name': 'linear_width', 'type': 'float or None', 'required': False, 'default': None}]`
- **LocatorSpec**: `[{'name': 'kind', 'type': 'str', 'required': False, 'default': 'auto'}, {'name': 'values', 'type': 'list[float] or None', 'required': False, 'default': None}, {'name': 'step', 'type': 'float or None', 'required': False, 'default': None}, {'name': 'offset', 'type': 'float or None', 'required': False, 'default': None}, {'name': 'nbins', 'type': 'int or None', 'required': False, 'default': None}, {'name': 'integer', 'type': 'bool or None', 'required': False, 'default': None}, {'name': 'prune', 'type': 'str or None', 'required': False, 'default': None}, {'name': 'count', 'type': 'int or None', 'required': False, 'default': None}, {'name': 'subdivisions', 'type': 'int or None', 'required': False, 'default': None}, {'name': 'subs', 'type': 'list[float] or None', 'required': False, 'default': None}, {'name': 'unit', 'type': 'str or None', 'required': False, 'default': None}, {'name': 'interval', 'type': 'int or None', 'required': False, 'default': None}, {'name': 'weekday', 'type': 'int or None', 'required': False, 'default': None}]`
- **FormatterSpec**: `[{'name': 'kind', 'type': 'str', 'required': False, 'default': 'auto'}, {'name': 'labels', 'type': 'list[str] or None', 'required': False, 'default': None}, {'name': 'scientific', 'type': 'bool or None', 'required': False, 'default': None}, {'name': 'use_offset', 'type': 'bool or None', 'required': False, 'default': None}, {'name': 'powerlimits', 'type': 'list[int] or None', 'required': False, 'default': None}, {'name': 'mathtext', 'type': 'bool or None', 'required': False, 'default': None}, {'name': 'notation', 'type': 'str or None', 'required': False, 'default': None}, {'name': 'precision', 'type': 'int or None', 'required': False, 'default': None}, {'name': 'prefix', 'type': 'str or None', 'required': False, 'default': None}, {'name': 'suffix', 'type': 'str or None', 'required': False, 'default': None}, {'name': 'xmax', 'type': 'float or None', 'required': False, 'default': None}, {'name': 'decimals', 'type': 'int or None', 'required': False, 'default': None}, {'name': 'unit', 'type': 'str or None', 'required': False, 'default': None}, {'name': 'separator', 'type': 'str or None', 'required': False, 'default': None}, {'name': 'style', 'type': 'str or None', 'required': False, 'default': None}, {'name': 'label_only_base', 'type': 'bool or None', 'required': False, 'default': None}, {'name': 'half', 'type': 'str or None', 'required': False, 'default': None}, {'name': 'use_overline', 'type': 'bool or None', 'required': False, 'default': None}, {'name': 'pattern', 'type': 'str or None', 'required': False, 'default': None}]`
- **TickSpec**: `[{'name': 'locator', 'type': 'LocatorSpec or None', 'required': False, 'default': None}, {'name': 'formatter', 'type': 'FormatterSpec or None', 'required': False, 'default': None}, {'name': 'rotation', 'type': 'float or None', 'required': False, 'default': None}]`
- **AxisTransformSpec**: `[{'name': 'kind', 'type': 'str', 'required': True, 'default': None}, {'name': 'factor', 'type': 'float or None', 'required': False, 'default': None}, {'name': 'offset', 'type': 'float or None', 'required': False, 'default': None}, {'name': 'source_unit', 'type': 'str or None', 'required': False, 'default': None}, {'name': 'target_unit', 'type': 'str or None', 'required': False, 'default': None}, {'name': 'reverse', 'type': 'bool', 'required': False, 'default': False}]`
- **SecondaryAxisSpec**: `[{'name': 'transform', 'type': 'AxisTransformSpec', 'required': True, 'default': None}, {'name': 'label', 'type': 'str or None', 'required': False, 'default': None}, {'name': 'major_ticks', 'type': 'TickSpec or None', 'required': False, 'default': None}, {'name': 'minor_ticks', 'type': 'TickSpec or None', 'required': False, 'default': None}]`
- **api**: `ticks / axis_scale / secondary_xaxis / secondary_axis`
- **actions**: `['SetAxisTicks', 'SetAxisScale', 'SetDerivedAxis']`
- **scales**: `['linear', 'log', 'symlog', 'asinh', 'logit']`
- **locators**: `['auto', 'none', 'fixed', 'multiple', 'max_n', 'linear', 'auto_minor', 'log', 'symlog', 'asinh', 'logit', 'calendar']`
- **formatters**: `['auto', 'none', 'fixed', 'scalar', 'number', 'percent', 'engineering', 'log', 'logit', 'date', 'concise_date']`
- **date_patterns**: `['iso_date', 'iso_datetime', 'time', 'month', 'year', 'subsecond']`
- **transforms**: `['affine', 'celsius_fahrenheit', 'radians_degrees', 'seconds_milliseconds', 'hertz_period', 'reciprocal', 'unix_seconds']`
- **axis_fields**: `['scale_options', 'major_ticks', 'minor_ticks']`
- **panel_fields**: `['secondary_x', 'secondary_y']`
- **legacy**: `all new fields appended/None/omit_none; old SetScale JSON unchanged; independent y2 not repurposed`
- **tick_units**: `axis coordinates; fixed temporal positions are UTC days since 1970, not source timestamp units`
- **fixed**: `finite nonbool strictly increasing/distinct after float conversion; literal labels require matching fixed positions`
- **formats**: `safe finite named notation/precision; no user format templates, width, eval, attribute lookup or serialized callbacks`
- **numeric_precision**: `0..12 decimals; general precision1..12; literal prefix/suffix/unit<=32 characters`
- **ordinal**: `auto preserves existing category locations/labels; only auto/none/fixed compatible, never numeric half-category ticks`
- **calendar**: `explicit TemporalSpec clock; UTC/fixed offset; named year/month/week/day/hour/minute/second/microsecond and auto`
- **calendar_precision**: `N12 date/auto/concise use canonical datetime/timedelta, not distant-epoch num2date rounding; fixed AUTO is date+6-digit ISO timestamp; old no-opt-in policies unchanged`
- **concise_policy**: `Matplotlib3.8 finite level/zero/offset/trailing-zero policy with canonical datetimes; fixed temporal positions supported; adapted-policy license/changes in bundled _matplotlib_notice.txt`
- **new_scales**: `symlog/asinh/logit: finite Cartesian raw numeric geometry; unsupported statistical/categorical/projection combinations reject`
- **domain_view**: `pure paired x/y (band x/y/y2) view ignores native missing/nonfinite gaps only for domain checks; source/native parsing/paths/order remain unchanged`
- **native_collection_limits**: `new-scale bar/errorbar/stem/broken_barh restore prior native DataLim/minpos/ignore then union actual raw new artist geometry, including embedded bar errors, for Matplotlib3.8 correctness. Event exception only actual logit Y-lane half-length geometry; other event/legacy log/linear paths unchanged, no fake origin`
- **log_parameters**: `base/subs apply everywhere existing log is valid; native log10 category spacing is multiplicatively equivalent. Scale subs are minor policy; automatic major locations remain base powers and explicit locator subs can override either rank`
- **logit_domain**: `strict open(0,1); constant p view uses native0.1 widening on min(p,1-p), contains data/complement symmetric; unrepresentable native inverse/domain precision errors, no epsilon/clipping`
- **secondary**: `derived top x/right y only; analytic closed registry with declared units, view-only conversion; linear/log parents; right derived y conflicts with independent y2`
- **secondary_precision**: `validate actual visible bounds on every native refresh, including later zoom; target ULP propagated through analytic inverse; collapse/nonfinite/domain failures reject`
- **secondary_date**: `unix_seconds converts canonical UTC1970 day*86400, never source input unit/origin or Matplotlib global epoch`
- **sharing**: `existing legal all/row/col/share_id groups; mixed named/figure modes remain rejected; exact explicit conflicts reject; None inheritance only new options in effective view, no source/clock mutation`
- **editor**: `both UIs keep granular fields; linear/log inverse correct for all bases; new nonlinear DATA drag disabled per actual target with reason, unaffected primary handles survive nonlinear y2; title/legend fractions remain`
- **max_ticks_per_level**: `512`
- **max_figure_configured_ticks**: `16384`
- **max_formatted_tick_characters**: `512`
- **resource_scope**: `physical axis/rank active-location/format operations, shared inheritance included; preflight before native grids/rules/requested expansion; repeated calls replace counts; not cached-Tick RAM bound/SLA or old-limit increase`

Use ticks(axis, TickSpec/dict, which='major'|'minor') to replace one rank; None clears. axis_scale atomically replaces scale/options, while legacy SetScale preserves unrelated fields. Scale subs are minor policy; explicit locator subs can override either rank. Named derived views convert only visible coordinates, never source data. See bilingual FEATURE_COVERAGE and examples/axis_controls.py. Adapted canonical concise policy license/changes are bundled in _matplotlib_notice.txt; distribution MIT AND LicenseRef-Matplotlib, own LICENSE MIT.

## Stable panel layouts (N13)

- **GridCellSpec**: `[{'name': 'grid', 'type': 'str', 'required': True, 'default': None}, {'name': 'row', 'type': 'int', 'required': True, 'default': None}, {'name': 'col', 'type': 'int', 'required': True, 'default': None}, {'name': 'row_span', 'type': 'int', 'required': False, 'default': 1}, {'name': 'col_span', 'type': 'int', 'required': False, 'default': 1}]`
- **InsetSpec**: `[{'name': 'parent', 'type': 'str', 'required': True, 'default': None}, {'name': 'bounds', 'type': 'list[float]', 'required': True, 'default': None}]`
- **PanelPlacementSpec**: `[{'name': 'cell', 'type': 'GridCellSpec or None', 'required': False, 'default': None}, {'name': 'inset', 'type': 'InsetSpec or None', 'required': False, 'default': None}]`
- **LayoutGridSpec**: `[{'name': 'grid_id', 'type': 'str', 'required': True, 'default': None}, {'name': 'rows', 'type': 'int', 'required': True, 'default': None}, {'name': 'cols', 'type': 'int', 'required': True, 'default': None}, {'name': 'cell', 'type': 'GridCellSpec or None', 'required': False, 'default': None}, {'name': 'width_ratios', 'type': 'list[float] or None', 'required': False, 'default': None}, {'name': 'height_ratios', 'type': 'list[float] or None', 'required': False, 'default': None}]`
- **PanelLayoutSpec**: `[{'name': 'grids', 'type': 'list[LayoutGridSpec]', 'required': True, 'default': None}]`
- **field**: `FigureSpec.panel_layout`
- **native_layout_policy**: `uniform native tight engine for explicit panel_layout, selected before axes/colourbars; legacy constrained/3D paths unchanged; unfittable decoration warnings retained; measured axis-label/eligible tick-decoration diagnostics, axis-side union broadphase, never all tick pairs`
- **sharing_role_boundary**: `new role checks require explicit panel_layout or stored panel IDs; all existing validation remains global, legacy sharing retained`
- **identity**: `PanelSpec.panel_id; deterministic allocation on opt-in only`
- **placement**: `PanelSpec.placement: exactly one grid cell/span or parent inset`
- **grids**: `one root; nested native GridSpec/subgridspec; ratios stored unchanged`
- **mosaic**: `rectangular repeated IDs; null empty positions; normalizes to placements`
- **inset**: `native child axes; contained nonoverlapping siblings; all 2d/polar/3d combinations`
- **sharing**: `one component resolver; row/col matches immediate grid and exact span; insets singleton unless all/named; known statistical/spectral dimensions kept separate`
- **new_panels**: `complete placements cover all existing final IDs; extra named keys add empty panels in lexicographic ID order, never object-key order`
- **vector_identity**: `identified native SVG axes use mudplot-panel-ID groups`
- **edits**: `['SetPanelLayout', 'SetMosaic', 'NestLayout', 'SetPanelPlacement', 'AddInset', 'RenamePanel', 'ReorderPanels', 'RemovePanel']`
- **legacy**: `panel_layout omitted retains regular-grid geometry and index action semantics`
- **limits**: `bounded IDs <=64; no opaque artists/callbacks/kwargs; explicit expansion needs complete placements; unrepresentable extents reject`

Complete SetPanelLayout payloads use final IDs for every key and reference; all existing IDs are mandatory, explicitly new panels append in lexicographic ID order independent of JSON key order. Mosaic first-occurrence assignment only consumes anonymous legacy panels. Native GridSpec/subgridspec/inset_axes render validated spans/ratios; empty positions differ from empty real panels. Nesting pair/joint cells preserves source selectors and density/value units; this does not close G02/G03. See docs/PANEL_LAYOUTS.md, its Korean counterpart and examples/panel_layouts.py.

## Weighted histogram statistics

Named/discrete bins and new statistics/geometry/style options use typed `HistogramSpec` at layer.histogram. None retains legacy hist density/group/bin/alpha behavior without numeric or default changes.
- Shared integer bins pool usable selected observations; explicit finite increasing raw edges are also supported. Half-open [left,right) bins, closed final edge. Missing required/zero-weight rows are excluded; finite numeric values/weights exclude bool. Weights are nonnegative row mass.
- Named auto/fd/doane/scott/stone/rice/sturges/sqrt rules use FIXED v2 classic NumPy1.23 definitions, not installed-version changes. Auto uses FD/Sturges. Each usable observation enters edge selection once; positive weight magnitudes affect heights/mass, not boundaries. Every derived count is checked before allocation; more than 10000 bins rejects without coarsening, outlier removal or a different rule.
- Bins='discrete' uses integer-centered input-unit bins. Hist(discrete=True) aliases it only with the default bin argument; conflicting custom bins reject. False/None preserve legacy calls. Fractional/non-bool or unrepresentable integer/half-unit grids reject, never round or jitter.
- Temporal discrete grids use the declared numeric input unit before conversion to UTC days. ISO/date grids require midnight in the display clock and use one day. Half-us/ns edges reject under the microsecond precision contract; finer/collapsed calendar edges are not widened. Named continuous-time rules operate on canonical UTC-day coordinates. Source timestamps, units and original order remain unchanged.
- count=bin mass; frequency=mass/raw width; probability/proportion=mass/denominator; percent=100*proportion; density=mass/(denominator*raw width). Only in-range mass enters denominators. Common_norm=True pools across selected hues; False normalizes within each curve. No-op raw normalization choices are rejected. Thus density integrates to1, not sums heights to1.
- Before multiple='fill': cumulative count sums mass; normalized cumulative sums probabilities; density cumulative integrates mass (a binned CDF), not density heights. No cumulative frequency. Shared normalizations end at each hue's mass share; separate at1/100. This is not an exact unsmoothed ECDF.
- Normalized weights are scaled before summing; bin masses are summed independently, not subtracted from a large prefix. Cumulative prefixes reuse the accurate unrounded row expansion. Nonfinite raw total mass/derived widths/heights fail before drawing, no silently clipped bins.
- Cartesian2D bars/steps/poly v/h; vertical-only y2 response axis. x is the observed column; explicit clocks follow the temporal contract. Observation logs need positive values/edges, density uses raw widths (not log units). Height axes are linear (include zero bins); generated invalid log/collapsed edges fail. Empty curves have no bars/legend; hue order reserves colors/hatches. Exact alpha/edge/line width and reference metadata supported.
- Multiple='layer' overlays full bins. Grouped 'stack' adds heights in hue order; 'dodge' splits each raw bin into equal hue slots, including reserved empty hues. Heights/normalization/cumulative semantics do not change. Density/frequency still use ORIGINAL bin widths: dodge reduces drawn area, with no height correction. Stacked tops must stay finite and increase for nonzero bins; collapsed dodge slots fail before drawing.
- Grouped multiple='fill' divides the EXISTING heights in each bin by their group sum, after stat/common_norm/cumulative. It is dimensionless composition in [0,1], not a raw-weight override. Empty bins stay zero and absent hues stay empty. Cumulative fill is cumulative composition, NOT a CDF, and may decrease. Overflow/subnormal sums use exact fallback; positive shares or stacked increments lost to float precision reject.
- Element='bars' draws bars; 'step' draws one native stairs patch per observed hue with the same edges/heights. Fill=None retains filled bars and unfilled step/poly and is omitted from old JSON. Explicit True/False controls geometry only. Filled steps use group facecolors/hatches with native edge contrast; outlines use group-colored strokes/dashes without hatches. Layer closes to zero; stack uses the absolute top and previous baseline. Empty hues reserve color/theme dash slots; edge_color overrides stroke color. Exact alpha/width, including zero, retained. Typed alpha=0 emits no hatch ink, including native fallback patterns. Dodge places unchanged heights in their raw hue slots, with zero-baseline geometry gaps; no new observations or mass.
- Element='poly' connects raw-bin/slot centers with native straight lines or native filled areas. At least two representable centers are required; no jitter or fitting. Axes retain the declared raw-bin range and zero response baseline without adding observations. Empty curves do not change other layers' limits. None is unfilled; explicit bool controls fill. Native collections participate in hatch diagnostics.
- No custom step dashes/KDE/bivariate/interval controls or arbitrary kwargs. Legacy hist still uses old Matplotlib effects. This first subset is not full upstream parity.

| histogram field | type | default |
| --- | --- | --- |
| `stat` | `str` | `'count'` |
| `weights` | `str or None` | `None` |
| `common_norm` | `bool` | `True` |
| `cumulative` | `bool` | `False` |
| `multiple` | `str` | `'layer'` |
| `element` | `str` | `'bars'` |
| `fill` | `bool or None` | `None` |

## Weighted named univariate KDE

Strict KDESpec/dict options use layer.kde; omitted calls keep their legacy fit. Full examples and scientific units: [DENSITY_FIELDS.md](DENSITY_FIELDS.md) / [한국어](DENSITY_FIELDS.ko.md).

- `max_points`: 4096
- `legacy`: kde=None keeps 1.06*sample-SD*n**(-1/5)/200-point fit
- `weights`: nonnegative relative row mass, not sample replication
- `bandwidth`: unbiased weighted SD times factor*bw_adjust; effective n
- `methods`: ['scott', 'silverman', 'positive covariance factor']
- `kernels`: ['gaussian', 'epanechnikov_product']
- `multiple`: ['layer', 'stack', 'fill']
- `rows`: paired missing/zero weights/hue deselection excluded
- `normalization`: all selected physical mass, including singular skipped tuples; effective hue only unless common_norm=True pools globally
- `clip`: evaluation only; never trims fit rows or renormalizes tails
- `common_grid`: persisted shared support with separate per-curve fits; required for stack/fill, no hidden interpolation
- `cumulative`: chosen kernel CDF from minus infinity; stacked contributions and fill composition are labelled as such, not population CDFs
- `singular`: skip without fake bandwidth; warn_singular controls warning
- `axes`: Cartesian2D v/h with observations on the actual x/y/y2 target; typed/new density/CDF ordinate linear, never a date clock; omitted legacy ordinate behavior retained
- `density_units`: default raw data/day units; explicit stat_scale=axis uses log10 only on the actual log observation axis, independent of display base; density_space=data includes Jacobian, fit is working units
- `style`: actual line/fill stroke points and dashes, no invented glyphs
- `limits`: finite named kernels/bandwidth only; explicit clocks for dates; no inferred symlog/asinh/logit statistical fit or callbacks
- `precision`: scaled sums/covariance, bounded chunks; invalid derived fail
| kde field | type | default |
| --- | --- | --- |
| `weights` | `str or None` | `None` |
| `bw_method` | `str or float` | `'scott'` |
| `bw_adjust` | `float` | `1.0` |
| `gridsize` | `int` | `200` |
| `cut` | `float` | `3.0` |
| `clip` | `list[float or str or None] or None` | `None` |
| `common_norm` | `bool` | `True` |
| `common_grid` | `bool` | `False` |
| `cumulative` | `bool` | `False` |
| `fill` | `bool` | `False` |
| `warn_singular` | `bool` | `True` |
| `kernel` | `str or None` | `None` |
| `multiple` | `str or None` | `None` |
| `density_space` | `str or None` | `None` |

## Weighted bivariate kernel fields and full-model HDR

Strict KDE2DSpec/dict options retain the old conditional grid definition unless a persisted scientific choice requests the explicit workflow. Density, true joint CDF and full HDR are distinct contracts, not aliases.

- `max_points_per_axis`: 256
- `max_usable_rows`: 10000
- `max_levels`: 16
- `kernels`: ['gaussian', 'epanechnikov_product']
- `weights`: canonical paired relative mass; physical Kish before ties
- `covariance`: unbiased full covariance; gaussian or variance-one Cholesky epanechnikov_product, explicitly nonradial
- `bandwidth`: d=2 Scott=Silverman=n_eff**(-1/6); finite scalar factor
- `normalization`: selected full cohort, including skipped singular fields; effective-hue/global pool, not each size/style tuple
- `support`: cut/clip choose evaluation/view only, never trim or rebase fit
- `level_kinds`: ['mass', 'density', 'cdf']
- `conditional_default`: absent HDRSpec retains finite-grid trapezoidal mass ranking with all tied heights; conditional, not full-space coverage
- `cumulative`: true original-law joint lower-orthant CDF; no finite-grid subtraction/renormalization or Jacobian; common_norm amplitude remains an explicit contribution
- `joint_cdf_absolute_error`: 1e-06
- `fit_scales`: logical per-input data/axis; actual log uses log10, never display base; density_space data/fit is explicit; no absolute-clock log fit
- `singular`: no jitter/regularization/fake bandwidth or observations
- `axes`: actual Cartesian2D primary/y2, v/h, declared input clocks
- `style`: real native contours/cells, physical outline points/dashes
- `limits`: no 2D stack/fill ordinate, CDF+mass-HDR or arbitrary callbacks
- `precision`: canonical source/mass before float; full-exponent scaled and outward primitives; unresolved derived coordinates stay errors
- `full_hdr.opt_in`: HDRSpec(scope=full,tolerance=0.01); absent stays conditional
- `full_hdr.conditional_tolerance`: 0<tolerance<=0.05; absolute probability
- `full_hdr.method`: one fitted source-enclosed whitening chart/root; unknown strictly ordered cutoffs, adaptive rectangle mass bounds, disjoint earliest-band guaranteed-inside native cell unions
- `full_hdr.working_active_cells_per_current_level`: 65536
- `full_hdr.max_lambda_updates`: 48
- `full_hdr.initial_trial_in_addition`: True
- `full_hdr.statement`: support/numeric/source-transform/classification/native/clip allocations remain separate; bounded conditional target and region symmetric-difference error under declared IEEE/computed-model assumptions, not an exact infinite-source law
- `full_hdr.visibility`: actual clipped probability is reported, not called p
- `full_hdr.failure`: unresolved order/precision/tolerance/resource rejects the whole effect; no level dropping/conditional fallback
| kde2d field | type | default |
| --- | --- | --- |
| `weights` | `str or None` | `None` |
| `bw_method` | `str or float` | `'scott'` |
| `bw_adjust` | `float` | `1.0` |
| `gridsize` | `int` | `80` |
| `cut` | `float` | `3.0` |
| `clip` | `list[list[float or str or None]] or None` | `None` |
| `common_norm` | `bool` | `True` |
| `common_grid` | `bool` | `False` |
| `levels` | `list[float]` | `[0.5, 0.8, 0.95]` |
| `fill` | `bool` | `False` |
| `warn_singular` | `bool` | `True` |
| `kernel` | `str or None` | `None` |
| `cumulative` | `bool or None` | `None` |
| `level_kind` | `str or None` | `None` |
| `fit_scales` | `list[str] or None` | `None` |
| `density_space` | `str or None` | `None` |
| `hdr` | `HDRSpec or None` | `None` |

## Paired histogram and empirical fields

Use explicit BivariateBinsSpec logical x/y bin choices, Histogram2DSpec statistics/KDE or the separate `ecdf2d` builder. Flat legacy bins retain their original meaning. Examples/units: [DENSITY_FIELDS.md](DENSITY_FIELDS.md) / [한국어](DENSITY_FIELDS.ko.md).

- `histogram2d.statistics`: ['count', 'frequency', 'probability', 'proportion', 'percent', 'density']
- `histogram2d.bins`: BivariateBinsSpec requires logical x/y counts, existing named rules or explicit numeric/clock edges; old flat lists keep their existing meaning
- `histogram2d.cohort`: positive complete paired rows BEFORE bin-range tally
- `histogram2d.denominator`: both coordinates in range; common_norm=True pooled, False effective-hue pool, never a separate size/style-tuple pool
- `histogram2d.geometry`: H(nx,ny) displayed H.T against true nonuniform edges
- `histogram2d.kde_overlay`: SAME pre-tally paired cohort, including out-of-bin rows; parent weights inherit/match, common_norm agrees; independent full-fit density/CDF levels, never count-height rescaling
- `joint_ecdf.statistics`: ['proportion', 'percent', 'count']
- `joint_ecdf.definition`: paired P(X<=qx AND Y<=qy), ties before float
- `joint_ecdf.complement`: strict X>qx OR Y>qy, not AND survival
- `joint_ecdf.bounds`: required finite bounds; every interior source knot and query retained; bounds/queries do not remove denominator rows
- `joint_ecdf.max_edges_per_axis`: 512
- `joint_ecdf.geometry`: right-continuous rectangular cells, no smoothing
- `joint_ecdf.prefix`: canonical exact integer Fenwick/prefix mass, bit-aware work
- `new_resources.selected_positive_complete_physical_rows_per_layer`: 10000
- `new_resources.raw_tuple_fields_per_layer`: 256
- `new_resources.categorical_levels`: 64
- `new_resources.composite_units_per_NEW_figure`: 2000000000
- `new_resources.working_retained_geometry_artist_bytes`: 268435456
- `new_resources.all_live_numerical_pair_elements`: 1000000
- `new_resources.native_path_vertices_including_closure`: 2000000
- `new_resources.scope`: persisted bivariate-stat/bin-pair/SEM/joint-ECDF or named nonlegacy kernel/multiple/actual-log-fit/joint-CDF/full-HDR; geometry-only and identity Gaussian requests gain no new guard; existing D01/C07 ledgers remain separate
- `new_resources.meaning`: one figure-wide actual composite cost proxy, including owned outward/special-function/scaled/native/limb-sensitive integer work; not FLOPs/RSS/SLA, no per-field/level reset
- `new_resources.raster`: backend RGBA buffers stay outside this allowance under40M pixels
- `new_resources.failure`: whole effect rejects prospectively; no truncated output
- `coordinates`: logical paired columns retain order/IDs; actual Cartesian2D primary/y2, v/h and declared per-coordinate clocks; explicit temporal bin/clip/bound/query numbers are canonical UTC days, not timestamp input units; ISO bounds use the declared zone
- `statistic_guides`: actual field collection ScalarMappable/raw values/norm; separate normalized non-data calibration with exact raw labels, never a semantic hue bar or a norm-changing tiny-range expansion

### BivariateBinsSpec

| field | type | default |
| --- | --- | --- |
| `x` | `int or str or list[float or str]` | `None` |
| `y` | `int or str or list[float or str]` | `None` |

### Histogram2DSpec

| field | type | default |
| --- | --- | --- |
| `stat` | `str` | `'count'` |
| `weights` | `str or None` | `None` |
| `common_norm` | `bool` | `True` |
| `kde` | `KDE2DSpec or None` | `None` |

### ECDF2DSpec

| field | type | default |
| --- | --- | --- |
| `bounds` | `list[list[float or str]]` | `None` |
| `stat` | `str` | `'proportion'` |
| `complementary` | `bool` | `False` |
| `weights` | `str or None` | `None` |
| `query_x` | `list[float or str] or None` | `None` |
| `query_y` | `list[float or str] or None` | `None` |

### HDRSpec

| field | type | default |
| --- | --- | --- |
| `scope` | `str` | `'full'` |
| `tolerance` | `float` | `0.01` |

## Box and violin distributions

- Legacy `box(value, group=category)` / `violin(value, group=category)` keep
  their one-column meaning and one-based native positions. With both columns,
  `box(category, value, group=hue)` / `violin(category, value, group=hue)` nest
  hue within ordinal categories; `orient='h'` changes geometry, not argument roles.
- `order`/`hue_order` select/reserve levels; required missing rows drop listwise.
  Empty cells have no invented marks/legend entries. Singleton/constant cells
  remain real degenerate distributions. Numeric native/log categories and positive
  log-value axes are supported; C03 box date/y2 paths are described separately below.
- `width` sets total distribution span (nested default 0.8); numeric `dodge`
  sets the total hue-offset span (None auto, 0 overlays). `gap` shrinks the
  allocated body width by that fraction; colours/hatches stay shared by hue.
- Box `whis` is a nonnegative IQR multiplier (native default 1.5) or increasing
  percentile pair such as [5, 95]. Whiskers use native observed endpoints;
  they are not confidence intervals. Without an explicit C03 median_ci request,
  raw notches use native deterministic Gaussian approximation, never ambient
  random bootstrap. Mean/flier and outline/marker controls remain independent.
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

## Independent distribution components

`box(..., components={...})` accepts body/whisker/cap/median/mean/flier;
`boxenplot` accepts only body/median/flier (no fictitious whiskers or means).
Typed ComponentStyleSpec and DistributionComponentsSpec are also public.
Absent components/properties inherit current native/layer/hue styles. Explicit
component properties override layer shorthands, never change observations or stats.
Body color overrides the base hue; unmapped boxen retains lighter tail tiers
(none hides fill). Mapped boxen hue is never retinted; an explicit unmapped
band color is final. Redundant hatches stay unless body.hatch overrides.
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
  Hatch uses at most32 native symbols. No callbacks/arbitrary kwargs. Boxen uses
  typed rank/side/per-raw-hue overrides below; C03 box uses its typed mode.

Unknown nested keys fail in loader/schema; wrong roles/value constraints fail
validation rather than being dropped. JSON/actions/editor and native/log/
orientation routes retain the same geometry; styles stay declarative, not
escape-hatch edits to a Figure.

## Complete box observations and columnar summaries

`box(..., median_ci={level,n_boot,seed}, cap_fraction=..., hue_components=[...])`
and `bxp(category,median,q1=...,q3=...,whislo=...,whishi=...,...)` share the existing
box layer. The one-column `bxp(median,group=category,...)` keeps one-based slots.
Options reference DataSpec columns; no copied summary table or callback is stored.

- Required absolute summary values obey whislo<=q1<=median<=q3<=whishi. One
  summary row/category/effective-hue/raw-role tuple; no averaging/dedup. Optional
  missing mean/CI/fliers never drop a valid box. Requested unavailable marks
  reject; supplied intervals/means are unclipped. Fliers are explicit finite
  lists outside closed whiskers: [] supplied none, None unavailable.
- Raw median CI uses private seeded row resampling and linear percentiles,
  existing n_boot1..100000/chunk target1m, no global RNG/weights/unit inference.
  Singleton box remains with warning/no bootstrap notch, never Gaussian fallback.
  Supplied quartiles cannot bootstrap missing original observations. The chosen
  raw/log statistic coordinates inverse-map once; clocks are explicit UTC-day views.
- Cap fraction[0,1] uses FINAL body width after dodge/gap, in category working
  coordinates, not measurement/point/mass units. Zero retains collapsed caps.
  Raw absent flags/whis inherit native/theme rc; requested caps don't enable an
  unrelated hidden body. Native zero stroke keeps independent markers/fill.
- Typed per-hue entries use raw category_key identity (bool!=number), known/
  reserved categorical hue only. One-column legacy group is category, not hue.
  Missing component fields inherit; actual mapped-property conflicts reject.
- Shared hue owns BODY facefill; size owns BODY outline stroke pt ONLY.
  Style always owns BODY dash AND actual FLIER glyph through serialized markers,
  including default cycle. Other component strokes/colors and mean/flier
  diameters/edges/faces remain independent. Guides are native box/line symbols,
  not fake point boxes or invented fliers; numeric huebars reuse shared raw labels.
- Box native/log/date/v-h/y2/facet/live paths retain original source/IDs/units.
  Existing explicit live recipes keep saved local views authoritative; whole
  replacement supersedes them. Effective category source owns inferred slots;
  literal explicit orders remain literal after channel changes.
- NEW advanced limits:256 DRAWN samplecells/layer,10000 selected source rows
  AND separately10000 total declared flier values; checked before native work.
  Existing semantic/facet/figure/bootstrap limits and legacy ordinary defaults
  remain unchanged. No arbitrary precision, curve/depth lift or wider row closure.

See [full scientific/availability/ownership contract](BOX_WORKFLOW.md) and
[executable raw/supplied/shared-role/live example](../examples/box_workflow.py).

## Violin workflow (C04)

The existing Gaussian/weighted/inner definitions remain. Omitted new controls keep
the old native/default JSON and artists. See [the complete scientific, ownership,
units and editor contract](VIOLIN_WORKFLOW.md), its Korean counterpart and
[the executable paired/shared/live examples](../examples/violin_workflow.py).

- Old `split=True` without `ViolinSpec` keeps exactly two selected/reserved hues
  at a shared center. Explicit `violin={'split_policy':'paired'}` supports frozen
  hue pairs in separate lanes, an odd final left half, H=1 and honest empty views.
  With P=ceil(H/2), pair j has center C+(j-(P-1)/2)*W/P and full span
  W/P*(1-gap). No additional positive dodge or invented counterpart.
- Raw hue/size/style tuples keep independent fits. Width/area/count normalization
  compares by effective hue only (one pool without independent hue), or globally
  with common_norm=True. Peak/mass references are resolved once per new-path pool.
  Area is a common density scale, not identical clipped polygon area.
- Weights are paired finite nonnegative relative mass; missing/zero rows drop
  before positivity, never replication/sampling. Weighted covariance/effective n
  and inverse right-continuous weighted-ECDF quartiles retain existing meanings.
  Unweighted inners retain linear sample quantiles. Point/stick draw actual rows;
  singleton/constants remain degenerate, not invented Gaussians.
- Gaussian Scott/Silverman/positive factor, bw_adjust(0,1000], points2..1000,
  cut0..10 bandwidths and raw absolute clip bounds remain finite. Clip restricts
  support, not fit/inner rows; declared measurement clocks parse calendar bounds.
  No callback, arbitrary inner kwargs, bootstrap or SciPy dependency.
- Existing DistributionComponentsSpec adds optional mode-specific box/quartile/
  point/stick/extrema roles; body/whisker/median/mean remain native traits.
  Segment roles reject glyph-only fields. Raw typed categorical per-hue keys
  distinguish True from1, permit declared reservations and reject unknown/numeric
  continuous overrides. Unavailable roles and explicit false-flag conflicts reject.
- HUE owns BODY fill; SIZE owns BODY outline stroke points only; STYLE owns BODY
  dashes plus actual point/box-median glyphs through the persisted marker cycle.
  Dash-only modes neither need unused marker capacity nor invent guide glyphs.
  Inner diameters/edges/faces/segments stay independent; actual mapped-property
  overrides reject at scalar/global/per-hue tiers. Native violin-shaped guides
  never alter data limits. Zero/absent strokes retain fill/segments/real glyphs.
- Applicable v/h/primary/y2/native/log/category+measurement-clock/facet/live paths
  reuse the existing pure selectors and explicit stored recipe. Data/axis fitting
  still means raw/log10 working units; N12 log base/subs are display controls.
  No new symlog/asinh/logit violin statistics. Saved local views remain truth;
  a later explicit whole-template replacement supersedes local overrides.
- New advanced admission is10000 selected rows AND256 drawn profiles/layer,
  categorical levels/override entries64; continuous numeric hue/size values are
  not capped at64. Existing1000support/facet/figure bounds remain. Backend path
  closure vertices are not mistaken for a strict2G+2 bound.

## Letter-value distributions

`boxenplot(value, group=category)` or `boxenplot(category, value, group=hue)`
computes letter-value bands, NOT confidence intervals, IQR whiskers or KDE.
Unweighted quantiles are type7 with one final correctly rounded interpolation.
Explicit `weights='column'` means relative paired probability weights, not
replicated observations: inverse empirical CDF LEFT, Q(p)=min{x:CDF(x)>=p};
endpoints are min/max, equality never inserts a midpoint. Thus explicit equal
weights may differ from unweighted type7. No quantile-method knob is inferred.
Canonical finite integer/binary-float VALUES are retained through sorting and
interpolation, not pre-rounded to float. Unweighted strict tails compare original
rows to the FINAL correctly-rounded type7 numeric bounds (so minsubnormal
`[u,2u]` has bounds `[u,2u]` and no invented tails). Its nominal-percentile area
width convention stays unchanged. Weighted LEFT instead uses exact observed
canonical bounds for quantiles/empirical masses/strict tails. Exact pre-rounding
boundary metadata is a separate geometry certificate: a genuinely positive band
span or requested strict-tail ordering lost at native binary64 conversion fails
clearly before commit. It is NOT another tail estimator or raw-min/max
nonconstancy rule. True atomic bands with unrequested hidden tails remain valid;
there is no blanket large-int ban, epsilon or automatic data rescaling.


- Required category/value/hue/size/style/weight columns are paired. Declared raw
  typed orders select/reserve before statistics; required missing rows drop
  listwise, zero weight is excluded, selected negative/nonfinite/bool weights
  reject. All-zero/empty views remain frames, not fabricated distributions.
  Exact canonical integer/binary-float weights preserve tiny positive masses
  even beside maxfinite weights; no epsilon, rescaling dropout or uniform fallback.
- `k_depth`: tukey (default), proportion, trustworthy, full or integer1..32.
  Named rules clamp1..32; explicit k is unchanged. For unweighted n,
  tukey is T(log2(n))-3; full T(log2(n))+1 and includes min/max; proportion
  T(log2(n))-T(log2(n*outlier_prop))+1 (default.007); trustworthy
  T(log2(n/(2*z*z)))+1, z=NormalDist.inv_cdf(trust_alpha/2), default.05.
  T truncates toward zero. Weighted rules substitute PHYSICAL-row Kish
  n_eff=(sum w)^2/sum(w^2), before tie aggregation, with exact rational exponent
  comparisons. This is a concentration stopping heuristic, NOT a CI or claim of
  independent observations. Splitting tied weight may change n_eff/depth/tails.
  `outlier_prop` is in(0,1), proportion only; `trust_alpha` in[1e-12,1),
  trustworthy only. The finite binary64 normal threshold is explicit.
- Weighted band mass is empirical `[low,high)`, LAST interval right-closed.
  Duplicate internal edges are empty; a last zero-height band may own an atom.
  Every boundary atom is assigned once; exact band masses plus strict-tail
  mass equal1. This is not a KDE/HDR/full-support density interpretation.
- `width_method`: exponential (default), linear or area. Weighted area normalizes
  empirical mass/band height within the cell; unweighted area retains nominal
  percentile interval mass. Zero-height/zero-mass area bands have zero width
  when positive-height densities exist; all-coincident boundaries retain
  exponential degenerate geometry, not invented dispersion/infinite density.
  Unrepresentable positive geometry rejects, never clamps/skips a band.
- `width` defaults.8 in(0,1]; `dodge` is total hue span<=width (None auto,
  0 overlays); gap shrinks slots. One-column legacy positions are one-based.
  `showmedians`/`showfliers` default True; tails retain EVERY strict-outside
  positive-weight original row, duplicate and source order. Full has no tails.
  Hidden fliers do not remove summary tails. Hollow diamond default3pt,
  median/outline.8pt; named component sizes stay in[0,1000]pt.
  Scalar and flier-component glyphs share one registered native contract,
  retaining legacy `+`/`x`/`.` and richer `P`/`X`/`p`/`h`/`8` choices.
  The filled-only SemanticSpec style cycle remains separate and unchanged;
  direct glyph overrides still reject when semantic style owns the flier marker.
- Append-only `BoxenSpec` owns `band_components` and `hue_components`.
  `BoxenBandComponentsSpec(rank,side,body)` uses central rank0,
  lower/upper ranks1..31 measured OUTWARD from central, not polygon indices.
  Rank r lower probabilities are[2^-(r+2),2^-(r+1)], upper complementary;
  full extends the outermost endpoints. Absent named-depth ranks are dormant;
  impossible explicit-k ranks, duplicate targets/unknown fields reject.
  `BoxenHueComponentsSpec(level,components,band_components)` uses exact RAW
  categorical keys (bool!=number), not labels; numeric-continuous hue cannot
  select per-hue components. Fieldwise precedence: native/theme/semantic traits,
  layer.components, raw-hue components, layer band BODY, raw-hue band BODY.
  Each band is a real ordered native polygon with independent hatch/fill/edge.
- `semantics` or `hue`/`size`/`style` sugar reuse the SAME selected raw tuple and
  shared-domain convention as box/violin. Hue owns actual BODY colour: mapped
  hue has NO implicit lighter-tail tint (numeric colourbars remain truthful).
  Unmapped defaults retain tints; explicit unmapped band.color is final.
  Size owns BODY outline stroke in POINTS only, not geometric/probability width
  or flier area. Style owns BODY dash and actual observed FLIER glyphs.
  Every mapped-owned conflict rejects at every override tier. Median/flier
  strokes/marker edges/faces/sizes remain independent; guides never invent a
  flier glyph for a cell with no actual glyph. Matching scale_id/config may share
  the RAW normalization domain across scatter/line/boxen and other accepted marks.
  Stroke/diameter physical units and visible guide blocks remain mark-specific;
  sharing a raw domain does not conflate those encodings.
- Primary/y2, vertical/horizontal, ordinal/native numeric/date category, declared
  linear value clocks, numeric linear/log display, data/axis statistic views,
  selected shared domains, saved/live facets and N13 nested/inset panels work
  through public declarations. Axis statistics support linear/log10 only;
  raw data statistics retain units on supported display scales. Actual clock
  targets use F02 canonical days without changing source strings/IDs/epoch;
  weights cannot be declared temporal coordinates. Category x remains category
  in horizontal views. Existing named-axis-share/figure-share restrictions stay.
- Advanced opt-in is BoxenSpec, weights, semantics, y2 or a newly supported
  flier glyph, NOT an old supported components object. NEW per-layer bounds:
  10000 selected positive PHYSICAL instances and256 DRAWN raw-tuple cells.
  Figure bounds:32768 actual C05 band polygons (including degenerate paths),
  1000000 requested native C05 flier instances. Repeated uses count across
  panels/layers; shared-scale row deduplication never discounts work.
  Transparent/marker-none styling still counts requested observations.
  Truly unrequested hidden flier artists need not be allocated. Pure source
  validity checks options/refs/types/selected finite weights/rows/cells/static
  band availability, NOT a full fit. Existing render/preview prepares each
  summary ONCE, admits actual aggregate band/flier work before native allocation,
  and reuses it for geometry. Valid saved source may exceed an owned EFFECT
  budget; CLI render leaves prior output and editors leave prior spec/PNG/history.
  Pure numerical helpers compute only when explicitly called. No CLI composition
  rewrite, serialized plan/global cache or hidden validation bypass. These are
  native-expansion
  bounds, NOT SLA/RAM/universal marker-size promises. Depth32, figure panels256,
  layers1024, render40M pixels and legacy no-C05 admission remain unchanged.
- Both editors expose collapsed, populated full `ReplaceLayer` action JSON for
  existing layer edits. `ReplaceLayer(layer_index,layer,panel=0)` is authoritative
  typed replacement, not a partial merge; both indices must already exist and
  be real nonbool ints. No expansion/reordering/implicit live-recipe detach.
  Normal candidate validation/render precedes commit; errors retain prior
  spec/PNG/history. Undo/redo/reopen restore content; later explicit whole live-
  template replacement supersedes cell-local edits. Public dispatch/apply is
  sufficient; no second style state or replacement API alias.

Example: [weighted executable](../examples/weighted_letter_values.py).
Arbitrary kwargs/callbacks, whis/notches,
means/CI/KDE controls and silent depth increases remain unsupported.

## Native and log categorical coordinates

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

## Categorical strip geometry

`stripplot(x, y, strip=StripSpec(...))` or explicit `semantics` opts into
category/hue slots. Explicit `order`, nondefault `orient`, `dodge` or
`native_scale` also opts in.
With none of those controls, legacy raw-x uniform jitter and old JSON are
unchanged; `hue_order` alone retains its prior group-selection behavior.

- x remains the category and y the measured value in both `orient='v'/'h'`.
  Missing category/value/group rows drop together; source data/order stay raw.
  `order` and `hue_order` select/reserve empty slots without invented marks.
- `dodge` is a total category-span fraction in [0,1]; None/0 overlays hues.
  For k selected/reserved hue slots, group i is offset by
  `(i-(k-1)/2)*dodge*spacing/k`. Empty hues consume the same slots/colors.
- `jitter` is a half-width fraction in [0,0.5], default .15.
  Undodged unit = minimum category axis spacing; dodged unit =
  `dodge*spacing/k`. Uniform jitter is sampled in ±jitter units with
  `StripSpec(jitter_policy='uniform', seed=0)`. Named policy 'none' adds zero.
  Seed is a non-bool integer in [0,2**32-1]; NumPy's local generator never
  changes process-global RNG. Jitter changes category geometry, not measurements.
- Ordinal spacing is one. `native_scale=True` uses minimum selected/reserved
  numeric spacing, log10 spacing on numeric log categories, singleton spacing
  one. Explicit `date_axis` uses F02 canonical day geometry and preserves raw
  timestamps/unit/origin. No implicit date parsing changes old string defaults.
- v/h, positive log measurements, configured y2, materialized facets and empty
  selected facet frames share the existing controls. Optional SemanticSpec maps
  independent hue/size/style with deduplicated original-row pools; mapped size
  is marker diameter in points. Category/hue selection precedes mapping/jitter,
  explicit normalization clips appearance only, and raw measurements stay fixed.
  Shared numeric-hue bars use the preceding logical-panel guide contract.

Executable create/save/reopen/export example: `examples/strip_categories.py`.
Bounded C01 functional acceptance includes real Rust/browser history/reopen and
installed minimum API/CLI evidence in `v2_strip_categories_closure.json`;
final frozen-product Linux/REL01 qualification and wider F01 roles stay separate.
The four-family `examples/shared_semantic_families.py` reuses these domains
across scatter, lineplot, strip and weighted ECDF. Other named F01 family
adapters and final installed/browser/product qualification remain mandatory.

## Swarm observations

`swarmplot(category, value, group=hue)` retains individual observations and source
order. Native named filled glyphs repack from immutable original measurements at
**every draw**, after layout/limits/DPI/backend transforms, without RNG or drift.
Only the category coordinate moves; x stays categorical in horizontal orientation.

- Missing category/measurement/required roles drop listwise. Explicit orders reserve
  empty slots. Opt-in scope/hue/style selection uses typed bool/numeric identities;
  legacy default and size-only group/order behavior remains unchanged.
- Hue/size/style use shared SemanticSpec raw-row domains with scatter/lineplot/
  strip/ECDF/rug. Size is nominal native diameter points, squared to native area;
  line/rug families use stroke points instead. Style uses distinct named MARKERS,
  never circle stand-ins. Categorical hue may dodge; numeric hue is continuous.
  Size/style-only roles retain legacy group/hue_order; semantic hue conflicts with
  them. Scalar mapped-role overrides and unsupported options reject.
- Numeric/native/log/date categories and measurements, v/h and applicable primary/
  secondary-y targets use their actual axis clocks. Ordinal string defaults stay
  unchanged. Swarm-only y2 facets and explicit live-template transactions are
  supported; other G01 families remain required.
- `width` is total category span (0,1], default0.8; dodge is total hue span <=width
  (None auto, 0 jointly packs hues), and gap shrinks it. Scalar marker_size remains
  positive points<=1000 (default6); line_width is points[0,1000] (default0.5).
  Native set_sizes/linewidth cycling repacks current physical extents.
- `pack_scope=None` keeps layers independent. A declared name groups compatible
  members in the same logical panel/actual target axes only: orientation/category
  channel/order/native geometry/width/dodge/gap match; dodged hue channel/orders
  match. Shared slots resolve before draw. Same original row drawn by two members
  counts TWICE physically, while mapping domains deduplicate original row IDs.
  One axes-owned coordinator packs each explicit scope once per draw pass.
- At most 2000 usable observations per LAYER, unchanged. The profiled new
  operation bound is4000 physical instances per panel/scope, rejected before
  native point construction. This is not an SLA or a per-layer limit increase.
  Greedy packing retains bounded O(n²logn) worst-case behavior; no downsampling.
- Legacy circles retain exact old radius. Other glyphs use conservative actual
  Path bbox circles and round stroke joins. Crowded/oversized rows stay at gutters,
  with truthful clearance warnings and current crowded_count; warn_thresh is
  [0,1], default0.05, once per collection. Conservative packing is not optimal.

## Palettes

LCH-based. Kinds: `qualitative`, `sequential`, `diverging`.

- `qualitative`: equal(-ish) lightness, maximum hue contrast, worst-case ΔE00 across normal vision + protan/deutan CVD simulation maximised. A `lightness_jitter` (default 6) adds lightness variation, not unlimited greyscale separation; `Palette.report()` measures final8-bitHEX under explicit CVD conditions, not printing/accessibility certification.
- `sequential` / `diverging`: perceptually-uniform ramps, gamut-clipped.

### Named presets (`.palette(preset="...")`)

Pre-tuned `qualitative` parameter sets, each measured (not assumed) CVD-safe (worst-case ΔE00 ≥ 8) and true-greyscale-safe (min L* gap ≥ 3) up to `max_verified_n` categories — see `tests/test_palette_presets.py`. Beyond that count, more colours are still generated but safety is no longer verified; pair with `.encoding(hatches=[...])` for bar/box/violin fills. Hatch, marker and dash cycles are finite and repeat; inspect the actual print size rather than assuming every category remains distinguishable.

| preset | max verified n | description |
| --- | --- | --- |
| `paper` | 6 | Balanced default; safe for up to 6 categories. |
| `soft` | 5 | Muted/pastel; safe for up to 5 categories. |
| `vivid` | 6 | More saturated; safe for up to 6 categories. |

## Themes

Available presets: paper, paper-grid, minimal, boxed, publication.

## Journals

- **acm**: default figure size [3.33, 2.5], base font 9pt
- **ieee**: default figure size [3.3, 2.5], base font 8pt
- **nature**: default figure size [3.5, 2.625], base font 7pt
- **revtex**: default figure size [3.4, 2.5], base font 8pt

## Panel projections

Available: `2d`, `polar`, `3d`.

## TeX presets (WYSIWYG sizing)

| preset | columnwidth (pt) | textwidth (pt) | font (pt) | cols |
| --- | --- | --- | --- | --- |
| `acm` | 241.0 | 506.0 | 9.0 | 2 |
| `article` | 345.0 | 345.0 | 10.0 | 1 |
| `ieee` | 252.0 | 516.0 | 10.0 | 2 |
| `nature` | 250.38425196850392 | 512.1496062992127 | 7.0 | 2 |
| `revtex` | 246.0 | 510.0 | 10.0 | 2 |

## Actions (JSON action vocabulary)

Every mutation is one of these — send as
`{"type": "<Name>", ...}` to `mp.apply([...])`.

### `AddInset`

| field | type | required | default |
| --- | --- | --- | --- |
| `parent` | `str` | True | `None` |
| `bounds` | `list[float]` | True | `None` |
| `panel_id` | `str or None` | False | `None` |

### `AddLayer`

| field | type | required | default |
| --- | --- | --- | --- |
| `layer` | `LayerSpec` | True | `None` |
| `panel` | `int` | False | `0` |

### `AddPanel`

| field | type | required | default |
| --- | --- | --- | --- |

### `NestLayout`

| field | type | required | default |
| --- | --- | --- | --- |
| `rows` | `int` | True | `None` |
| `cols` | `int` | True | `None` |
| `row` | `int` | False | `0` |
| `col` | `int` | False | `0` |
| `row_span` | `int` | False | `1` |
| `col_span` | `int` | False | `1` |
| `grid_id` | `str or None` | False | `None` |
| `width_ratios` | `list[float] or None` | False | `None` |
| `height_ratios` | `list[float] or None` | False | `None` |

### `RemoveLayer`

| field | type | required | default |
| --- | --- | --- | --- |
| `layer_index` | `int` | True | `None` |
| `panel` | `int` | False | `0` |

### `RemovePanel`

| field | type | required | default |
| --- | --- | --- | --- |
| `panel_id` | `str` | True | `None` |

### `RenamePanel`

| field | type | required | default |
| --- | --- | --- | --- |
| `panel_id` | `str` | True | `None` |
| `new_id` | `str` | True | `None` |

### `ReorderPanels`

| field | type | required | default |
| --- | --- | --- | --- |
| `panel_ids` | `list[str]` | True | `None` |

### `ReplaceLayer`

| field | type | required | default |
| --- | --- | --- | --- |
| `layer_index` | `int` | True | `None` |
| `layer` | `LayerSpec` | True | `None` |
| `panel` | `int` | False | `0` |

### `SetAutoLabel`

| field | type | required | default |
| --- | --- | --- | --- |
| `enabled` | `bool` | False | `True` |

### `SetAxesStyle`

| field | type | required | default |
| --- | --- | --- | --- |
| `params` | `dict` | False | `{}` |

### `SetAxisLabel`

| field | type | required | default |
| --- | --- | --- | --- |
| `axis` | `str` | True | `None` |
| `text` | `str` | True | `None` |
| `panel` | `int` | False | `0` |

### `SetAxisScale`

| field | type | required | default |
| --- | --- | --- | --- |
| `axis` | `str` | True | `None` |
| `scale` | `str` | True | `None` |
| `options` | `ScaleOptionsSpec or None` | False | `None` |
| `panel` | `int` | False | `0` |

### `SetAxisShare`

| field | type | required | default |
| --- | --- | --- | --- |
| `axis` | `str` | True | `None` |
| `share_id` | `str or None` | True | `None` |
| `panel` | `int` | False | `0` |

### `SetAxisTicks`

| field | type | required | default |
| --- | --- | --- | --- |
| `axis` | `str` | True | `None` |
| `which` | `str` | True | `None` |
| `ticks` | `TickSpec or None` | True | `None` |
| `panel` | `int` | False | `0` |

### `SetCamera3D`

| field | type | required | default |
| --- | --- | --- | --- |
| `camera` | `Camera3DSpec or None` | True | `None` |
| `panel` | `int` | False | `0` |

### `SetColorbar`

| field | type | required | default |
| --- | --- | --- | --- |
| `layer_index` | `int` | True | `None` |
| `show` | `bool` | False | `True` |
| `label` | `str or None` | False | `None` |
| `panel` | `int` | False | `0` |

### `SetContext`

| field | type | required | default |
| --- | --- | --- | --- |
| `name` | `str or None` | True | `None` |

### `SetData`

| field | type | required | default |
| --- | --- | --- | --- |
| `columns` | `dict` | True | `None` |

### `SetDerivedAxis`

| field | type | required | default |
| --- | --- | --- | --- |
| `axis` | `str` | True | `None` |
| `secondary` | `SecondaryAxisSpec or None` | True | `None` |
| `panel` | `int` | False | `0` |

### `SetDpi`

| field | type | required | default |
| --- | --- | --- | --- |
| `dpi` | `int` | True | `None` |

### `SetEncoding`

| field | type | required | default |
| --- | --- | --- | --- |
| `params` | `dict` | False | `{}` |

### `SetFacetTemplate`

| field | type | required | default |
| --- | --- | --- | --- |
| `template` | `PanelSpec` | True | `None` |
| `reset_orders` | `bool` | False | `False` |

### `SetFacets`

| field | type | required | default |
| --- | --- | --- | --- |
| `row` | `str or None` | False | `None` |
| `col` | `str or None` | False | `None` |
| `row_order` | `list[str or bool or int or float] or None` | False | `None` |
| `col_order` | `list[str or bool or int or float] or None` | False | `None` |
| `col_wrap` | `int or None` | False | `None` |
| `share_x` | `str` | False | `'all'` |
| `share_y` | `str` | False | `'all'` |

### `SetFont`

| field | type | required | default |
| --- | --- | --- | --- |
| `params` | `dict` | False | `{}` |

### `SetGridStyle`

| field | type | required | default |
| --- | --- | --- | --- |
| `params` | `dict` | False | `{}` |

### `SetJointGrid`

| field | type | required | default |
| --- | --- | --- | --- |
| `bins` | `int` | False | `20` |
| `ratio` | `float` | False | `3.0` |
| `marginal_stat` | `str` | False | `'density'` |
| `marginal_kind` | `str` | False | `'hist'` |
| `kde` | `KDESpec or None` | False | `None` |
| `weights` | `str or None` | False | `None` |
| `complementary` | `bool or None` | False | `None` |
| `group` | `str or None` | False | `None` |
| `hue_order` | `list[str or bool or int or float] or None` | False | `None` |

### `SetJournal`

| field | type | required | default |
| --- | --- | --- | --- |
| `name` | `str or None` | True | `None` |

### `SetLayerAt`

| field | type | required | default |
| --- | --- | --- | --- |
| `layer_index` | `int` | True | `None` |
| `at` | `list[float]` | True | `None` |
| `panel` | `int` | False | `0` |

### `SetLayout`

| field | type | required | default |
| --- | --- | --- | --- |
| `rows` | `int` | True | `None` |
| `cols` | `int` | True | `None` |
| `width_ratios` | `list[float] or None` | False | `None` |
| `height_ratios` | `list[float] or None` | False | `None` |

### `SetLegend`

| field | type | required | default |
| --- | --- | --- | --- |
| `show` | `bool` | False | `True` |
| `title` | `str or None` | False | `None` |
| `location` | `str` | False | `'best'` |
| `frame` | `bool` | False | `False` |
| `panel` | `int` | False | `0` |
| `bbox_to_anchor` | `list[float] or None` | False | `None` |
| `ncols` | `int or None` | False | `None` |
| `handler` | `str or None` | False | `None` |

### `SetLimits`

| field | type | required | default |
| --- | --- | --- | --- |
| `axis` | `str` | True | `None` |
| `lo` | `float or None` | True | `None` |
| `hi` | `float or None` | True | `None` |
| `panel` | `int` | False | `0` |

### `SetLiveFacets`

| field | type | required | default |
| --- | --- | --- | --- |
| `row` | `str or None` | False | `None` |
| `col` | `str or None` | False | `None` |
| `row_order` | `list[str or bool or int or float] or None` | False | `None` |
| `col_order` | `list[str or bool or int or float] or None` | False | `None` |
| `col_wrap` | `int or None` | False | `None` |
| `share_x` | `str` | False | `'all'` |
| `share_y` | `str` | False | `'all'` |

### `SetMatrix`

| field | type | required | default |
| --- | --- | --- | --- |
| `name` | `str` | True | `None` |
| `values` | `list[list[float or None]]` | True | `None` |

### `SetMosaic`

| field | type | required | default |
| --- | --- | --- | --- |
| `rows` | `list[list[str or None]]` | True | `None` |
| `width_ratios` | `list[float] or None` | False | `None` |
| `height_ratios` | `list[float] or None` | False | `None` |

### `SetPairGrid`

| field | type | required | default |
| --- | --- | --- | --- |
| `columns` | `list[str]` | True | `None` |
| `group` | `str or None` | False | `None` |
| `hue_order` | `list[str or bool or int or float] or None` | False | `None` |
| `bins` | `int` | False | `20` |
| `diag_stat` | `str` | False | `'density'` |
| `diag_kind` | `str` | False | `'hist'` |
| `kde` | `KDESpec or None` | False | `None` |
| `temporal` | `dict[str, TemporalSpec] or None` | False | `None` |
| `corner` | `bool or None` | False | `None` |
| `weights` | `str or None` | False | `None` |
| `complementary` | `bool or None` | False | `None` |
| `semantics` | `SemanticSpec or None` | False | `None` |

### `SetPalette`

| field | type | required | default |
| --- | --- | --- | --- |
| `kind` | `str or None` | False | `None` |
| `params` | `dict` | False | `{}` |

### `SetPanelLabel`

| field | type | required | default |
| --- | --- | --- | --- |
| `label` | `str or None` | True | `None` |
| `panel` | `int` | False | `0` |

### `SetPanelLayout`

| field | type | required | default |
| --- | --- | --- | --- |
| `layout` | `PanelLayoutSpec` | True | `None` |
| `placements` | `dict[str, PanelPlacementSpec]` | True | `None` |
| `panel_ids` | `list[str] or None` | False | `None` |

### `SetPanelPlacement`

| field | type | required | default |
| --- | --- | --- | --- |
| `panel_id` | `str` | True | `None` |
| `placement` | `PanelPlacementSpec` | True | `None` |

### `SetProjection`

| field | type | required | default |
| --- | --- | --- | --- |
| `projection` | `str` | True | `None` |
| `panel` | `int` | False | `0` |

### `SetReferenceMeasureText`

| field | type | required | default |
| --- | --- | --- | --- |
| `text` | `str or None` | True | `None` |

### `SetScale`

| field | type | required | default |
| --- | --- | --- | --- |
| `axis` | `str` | True | `None` |
| `scale` | `str` | True | `None` |
| `panel` | `int` | False | `0` |

### `SetSecondaryAxis`

| field | type | required | default |
| --- | --- | --- | --- |
| `label` | `str or None` | False | `''` |
| `scale` | `str` | False | `'linear'` |
| `limits` | `list[float] or None` | False | `None` |
| `panel` | `int` | False | `0` |

### `SetShare`

| field | type | required | default |
| --- | --- | --- | --- |
| `x` | `str or None` | False | `None` |
| `y` | `str or None` | False | `None` |

### `SetSharedGuides`

| field | type | required | default |
| --- | --- | --- | --- |
| `guides` | `list[SharedGuideSpec] or None` | True | `None` |

### `SetSize`

| field | type | required | default |
| --- | --- | --- | --- |
| `width` | `float` | True | `None` |
| `height` | `float` | True | `None` |

### `SetSuptitle`

| field | type | required | default |
| --- | --- | --- | --- |
| `text` | `str` | True | `None` |

### `SetTemporalAxis`

| field | type | required | default |
| --- | --- | --- | --- |
| `axis` | `str` | True | `None` |
| `temporal` | `TemporalSpec or None` | True | `None` |
| `panel` | `int` | False | `0` |

### `SetTheme`

| field | type | required | default |
| --- | --- | --- | --- |
| `name` | `str` | True | `None` |

### `SetTicksStyle`

| field | type | required | default |
| --- | --- | --- | --- |
| `params` | `dict` | False | `{}` |

### `SetTitle`

| field | type | required | default |
| --- | --- | --- | --- |
| `text` | `str` | True | `None` |
| `panel` | `int` | False | `0` |
| `citation` | `str or None` | False | `None` |
| `href` | `str or None` | False | `None` |

### `SetTitlePosition`

| field | type | required | default |
| --- | --- | --- | --- |
| `position` | `list[float] or None` | True | `None` |
| `panel` | `int` | False | `0` |

### `SetZAxis`

| field | type | required | default |
| --- | --- | --- | --- |
| `label` | `str` | False | `''` |
| `scale` | `str` | False | `'linear'` |
| `limits` | `list[float] or None` | False | `None` |
| `panel` | `int` | False | `0` |
