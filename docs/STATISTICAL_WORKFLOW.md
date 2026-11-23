# Raw statistical estimates: weighted methods, shared roles and live views

`barplot`, `pointplot` and the applicable pointwise `lineplot` routes store original observations and a named `StatSpec`. `.bar()` remains a precomputed-value primitive. There are six estimator names, not arbitrary serialized callables. This page describes inherited C07 pointwise behavior; [supplied-line and complete-unit inference](LINE_WORKFLOW.md) adds explicit finite-grid calibration without claiming complete upstream parity.

[한국어](STATISTICAL_WORKFLOW.ko.md) · [Runnable synthetic examples](../examples/statistical_workflow.py)

```sh
python examples/statistical_workflow.py artifacts/v2_c07/examples
python -m mudplot render artifacts/v2_c07/examples/statistical_live_dates.mplot.json exact.png
```

## Estimators and intervals

| Weighted estimator | Quantity | Supported intervals |
|---|---|---|
| mean | sum(w*x)/sum(w) | None, SD, SE, PI, CI |
| median | observed LEFT inverse weighted empirical CDF at1/2 | None, SD, PI, CI |
| min/max | selected positive-weight observed extreme | None, SD, PI, CI |
| sum | weighted total sum(w*x), not a normalized mean | None, CI |
| count | selected positive mass; ordinary count without weights | None |

Existing unweighted combinations remain supported, including unweighted sum None/SD/PI/CI. SE is explicitly mean-specific, never a generic mean-SE relabelled as median/sum/extrema uncertainty. Count intervals are not inferred. Weighted SD/PI for a displayed median or extreme remain descriptive observation intervals, not uncertainty for that estimator.

- SD: sample observation spread. For relative row weights p=w/sum(w), use reliability sample variance `sum(p*(x-mu)^2)/(1-sum(p^2))`. The denominator is computed in exact canonical mass units, not by subtracting two rounded nearly equal floats.
- SE: SD/sqrt(n_eff), with physical-row Kish n_eff=1/sum(p^2). This is an independent weighted-row approximation, not cluster-aware analytic SE. Equal-valued source rows remain separate cases before ties.
- PI: observation quantiles. Unweighted interpolation remains type7. NEW weighted PI is LEFT observed Q(p)=min{x:CDF(x)>=p}, with exact canonical PERCENT arithmetic `L=Fraction(level); p=(100-L)/200; upper=1-p`. For x=[0,10,20], w=[1,38,1], level95, PI is **[0,10]**, including the exact1/40 and39/40 knots. Equal weights can intentionally differ from unweighted type7; there is no hidden quantile-method switch.
- CI: percentile bootstrap of the requested estimator, not an observation PI. Resample original cases uniformly; values/weights travel together. Weights do not become sampling probabilities. Declared units select independent units and then rows within each selected unit, not equal-unit means. Units require CI.

Unit IDs are opaque: every string, including the empty string, is a valid ID rather than a displayed category label. Required missing None/NaN IDs exclude their paired rows. NEW routes distinguish bool True from numeric1 while retaining numeric identity1==1.0; ordinary display categories/roles still require nonempty string labels.

SD/SE levels are positive multipliers (default1); PI/CI levels are coverage percentages (default95). `errorbar=None` disables intervals. Singleton/no-independent-unit cells retain their estimate, omit requested intervals with a truthful warning and perform no bootstrap. A true atom can have a collapsed interval; requested strictly different canonical endpoints that cannot survive native rounding reject rather than fabricate zero uncertainty. Absolute native interval segments need not bracket the center and are never clipped to do so.

## Arithmetic and source identity

Canonical finite integer/binary-float values and exact integer mass units precede binary64 coordinates. Selected values, type7 endpoints, sums/means and moments are not globally MaxAbs-normalized and silently erased. The shared pure canonical boundary is also used by letter-value statistics; there is no copied private CDF. For example sum([1e300,-1e300,1e-300]) retains the representable1e-300 residual. Nonfinite results and undrawable requested interval spans reject; no zero, uniform-weight or epsilon fallback is inserted. Final coordinates still undergo native rounding: this is not a promise of exact floating geometry for every dynamic range.

Required missing values and zero weights are excluded as paired cases. Negative/nonfinite/bool weights reject. Original columns, row identities/order, clocks and user-declared units remain source truth. Typed categories/roles in NEW routes distinguish True from1. Raw role tuples partition estimates even when mapped appearances clip to the same style. Shared mapping domains deduplicate original row identities; drawn cases, cells and bootstrap multiplicities are not deduplicated.

## Independent roles and physical units

```python
cfg = mp.SemanticSpec(hue="temperature", hue_kind="numeric",
                      size="precision", sizes=[2, 4], style="method",
                      markers=["D", "^"], scale_id="original-rows")
p.barplot("dose", "response", weights="weight", estimator="median",
          errorbar=("pi", 95), semantics=cfg)
p.pointplot("dose", "response", semantics=cfg, errorbar=None)
```

`SemanticSpec`, its dictionary and JSON replay use the same strict stored policy. Do not combine independent mapped hue with another legacy group/hue-order channel; legacy grouping can coexist with independent size/style. Scalar overrides of owned mapped properties reject; harmless error/cap/other stroke properties remain independent.

- HUE: bar body fill; actual point/connecting-line color. Numeric hue uses the established normalized nondata colorbar with exact raw labels; constant domains use a midpoint swatch.
- SIZE: **bar BODY outline stroke points**, versus **pointplot actual marker DIAMETER points**. Lineplot remains MAIN LINE stroke points. Never bar width/height/area/mass or an uncertainty/connecting stroke width.
- STYLE: actual bar body dash; point glyph plus connecting dash. Persisted named dash/marker cycles must have sufficient distinct capacity. A dash-only bar does not require unused glyph capacity. No fake observations, filled-point stand-in for a bar or global string-label dedup.

Matching scale_id members share raw normalization while keeping mark-specific units/guides. Zero/absent strokes retain independent fill, glyphs, source segments and requested marker edges on the minimum renderer. Guides inherit the actual main native context, including independently requested zero/nonzero connecting stroke, body fill/edge and real glyph/diameter; each guide changes only its owned role. Guides have no data coordinates and do not affect data limits.

## Coordinates and source views

X remains the category/predictor argument and y the measurement even with `orient="h"`. Bar/point support actual primary or declared y2 targets: horizontal y2 categories live on y2, measurements on shared x. Numeric/date native slots, order/dodge/gap, limits/inversion/DPI/layout and unrelated layers reuse the common category geometry. Declared single-date slots prevent an epoch-dependent autoscale frame without rewriting measurement limits.

For log measurements, observations and requested derived endpoints must be positive; bars require an explicit positive baseline. `stat_scale="data"` estimates raw values then displays them. `stat_scale="axis"` fits mean/median/min/max in **log10** working units then inverses centers/endpoints. N12 display base2 does not change this definition. Axis/log SUM/COUNT reject, never become products/powers. No symlog/asinh/logit statistical fit is inferred from raw primitive scale support.

Calendar category and measurement clocks are distinct. Absolute calendar response mean/median/min/max/intervals use canonical UTC days; SD/SE widths are durations. Calendar SUM/COUNT reject. NEW calendar bars require an explicit canonical-day baseline, like numeric temporal bounds; it is not silently reinterpreted as seconds or density. Existing unextended source admission/defaults are not reclassified just because it has a clock.

Facets/live templates retain fixed selectors/IDs/resolved slots. A per-cell `ReplaceLayer` edit stays local. An explicit whole-template transaction supersedes local overrides in all intended populated and reserved-empty cells. Pure JSON loading preserves the saved recipe and selected materialized views, including local overrides. Rendering or reopening an editor preview deterministically recomputes the requested statistics from saved observations and seed; it does not perform a whole-template replacement. The undrawn stored recipe is not a physical all-row layer. Validate actual selected views/options before commit, including after source refill; excluded bad rows do not become phantom observations. N13 placement/nesting/ratios remain a single shared layout graph.

Explicit N13 geometry or stored panel identities apply the existing unit-sharing gate. A declared weighted SUM response is value×weight-mass, distinct from a mean/raw value or a COUNT mass. Compatible weighted-total responses can share, as can unweighted sums with other values; sharing a category axis does not change these response units. The legacy no-N13 unit gate remains unchanged. No physical-units API or inference from column labels is introduced.

When a panel draws secondary-y data, its combined legend is drawn on the
populated twin so its handles and text stay above both axes. An empty twin
does not take the legend from primary data. Native `best` placement does not
guarantee an empty region; explicit placement and figure-fraction dragging
remain available.

## C07 NEW-only resource policy

The persisted NEW predicate is: newly admitted weighted estimator/inference combination, OR bar/point SemanticSpec, OR specifically newly admitted bar/point target-axis route. Existing weighted mean None/CI, units CI, countplot mass, unweighted/plain or existing semantic dense line do **not** acquire new limits merely from those fields or arithmetic repair. A genuinely new line statistic counts predictor×raw-role pointwise cells, not old curve vertices.

NEW layers admit at most **10000 selected positive complete physical source rows AND256 drawn pointwise cells**, with existing64 categorical levels (not64 distinct continuous numeric values). Existing100000 bootstrap/facet64/panel256/layer1024/40M-pixel limits and dependency floors remain unchanged.

Active random/sample arrays are <=1M elements. Compact original-case multiplicities keep O(rows+units+n_boot) working storage and the original local seeded schedule, including singleton and oversized legacy unit streams. NEW eligible CI work counts unit-choice plus sampled-case instances across the layer, capped at **2,000,000,000 ACTUAL instances**. Admit an ordinary chunk before generation, hierarchical unit choices before drawing them, and row work from the chosen multiplicities before row chunks. If the request crosses the budget, reject the WHOLE effect before artists/editor commit: no prefix CI, lower n_boot, masked resamples or probability sampling. Actual-work admission can depend on the declared seed. Old admitted routes receive no new work/row/cell cap.

Ordinary maximum source sampling can be1B cases; hierarchical potential is NOT that bound (10000 rows/5001 uneven units can request25,005,000 cases in one replicate and2.5005e12 uncapped cases at100000). The active-memory/work policy is finite, not an SLA, RSS or universal latency promise. Figure multiplication remains explicit.

The additional D01 complete-unit limits, persisted declaration identity boundary and NEW-only figure/working-state ledgers are specified in [the line workflow](LINE_WORKFLOW.md#bounded-new-inference-work). They do not reclassify omitted/predictor-only or cheap raw/no-inference views, and do not replace this C07 local kernel/policy.

## Complete consumer workflow and evidence

Both local frontends expose registered layer controls and populated existing-layer `ReplaceLayer` JSON through the same reducer/candidate admission. Invalid scientific/work requests preserve accepted Spec/current complete PNG/history; CLI failures preserve prior complete outputs. Undo/redo, JSON save/reopen/post-reopen edit and actual SVG/PDF/PNG exports are qualified independently of source tests. Displayed DOM PNG revision is checked by decoded RGBA, not an image URL or placeholder. Rust PNG download remains the existing capped preview; exact requested-DPI PNG is produced by installed CLI/API from that same downloaded JSON.

Executable examples, source/current/minimum/installed/native/Rust/static/generated/active-denial Python-S, real UI and actual offline PGF/glyph/citation/URI evidence are distinct cohorts. Failures, corrections, original artifacts and provider limitations are never relabelled or summed. No whole F01/F02/D01/G01/E01/Q01/DOC01/REL01/v2 closure is implied by this workflow.

`examples/statistical_workflow.py` uses explicitly **synthetic** data. Its shared table declares deterministic response offsets per raw hue/size/style tuple, and its live table declares different positive response factors for bool True versus numeric1. The same original IDs, weights and table feed every mark; no display jitter or mark-specific preprocessing separates the curves. The six-estimator hand-reference dataset is independent and unchanged.
