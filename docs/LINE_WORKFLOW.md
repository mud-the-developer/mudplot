# Supplied lines and complete-unit inference

[한국어](LINE_WORKFLOW.ko.md) · [Statistical estimators](STATISTICAL_WORKFLOW.md) · [Facets](FACETS.md)

A supplied `.line()` is not an estimated `.lineplot()`. It retains selected observations, order, duplicate predictors and continuity barriers. `.lineplot()` estimates measurements at predictor cells. Its inherited default remains per-cell pointwise percentile CI with numeric native coordinates; `native_scale=False` is not reinterpreted as categorical spacing.

## Declare the scientific experiment

```python
import mudplot as mp

p = mp.plot({
    "time": [0, 1, 0, 1], "response": [1, 4, 3, 8],
    "subject": ["a", "a", "b", "b"],
}).lineplot(
    "time", "response", units="subject", n_boot=1999, seed=17,
    errorbar=("ci", 95), error_style="bars",
    line=mp.LineSpec(resampling="unit", calibration="max_deviation", family="curve"),
).labels(title="My experiment").size(8, 5)
p.save("complete-units.svg")
```

`LineSpec` is strict, optional and stored on `LayerSpec.line`. Its fields are:

| Field | Values | Meaning |
|---|---|---|
| predictor | native (default), categorical | Native numeric/declared real clock, or pooled ordinal slots |
| resampling | None, cell, unit | Inherited per-cell experiment or complete original trajectories |
| calibration | None, percentile, max_deviation | Pointwise percentile or finite-grid simultaneous maximum calibration |
| family | None, curve, layer | Maximum over one raw curve (default) or every curve/target in one selected layer |

Every explicit non-None inference field requires CI. `max_deviation` additionally requires explicit `resampling="unit"` and `StatSpec.units`; family requires max_deviation. Predictor-only declarations work with all otherwise valid inherited interval methods and None. Raw line accepts predictor declarations but rejects inference fields. There is no band alias: `error_style="band"|"bars"` controls geometry independently of calibration. Units still require CI.

### What a complete-unit replicate contains

Select eligible positive-mass original rows in the selected panel/layer. Form the typed unit union in first-source order, including units whose finite predictor trajectories have only missing responses. Draw U units uniformly with replacement, U times, once per replicate. A chosen unit repeats **all its original rows and paired masses**, across all predictors and raw curves. Duplicate rows remain physical cases. There are no within-unit draws, unit averages, weight-probability sampling, hidden imputation or conditional retries. An unbalanced trajectory retains its original row/mass contribution; a mean is a ratio of repeated original totals, not a mean of unit means.

This experiment assumes the declared units are independently exchangeable sampling objects and the fixed selected grid/missingness mechanism is scientifically appropriate. It does not repair informative missingness, dependence between units or selection of the grid after looking at results. Mean/median/sum bootstrap interpretations additionally require their usual regularity, support and moment assumptions. A sum concerns the declared repeated-unit total, not a hidden equal-weight subject average.

Let theta(c,j) be the original estimator in working coordinates and theta_b(c,j) the estimator after one complete-unit draw. For each requested family F, compute exactly

`D_b = max((c,j) in F) abs(theta_b(c,j) - theta(c,j))`.

For level L percent and B replicates, take the `ceil(Fraction(L)*B/100)`-th score in ascending order. The endpoints are theta(c,j) +/- q in those same working units, then inverse-mapped to native coordinates. This nonstudentized empirical maximum calibration has upper empirical rank mass at least L/100. It is **nominal finite-grid bootstrap inference**, not continuum, finite-sample or population coverage assurance. Curve families do not cover other hues; layer families cover that layer's finite curve/target union only. No cross-layer, panel, facet or figure coverage is claimed.

`calibration="percentile"` instead takes separate type7 bootstrap estimator quantiles at each target. It is pointwise, not simultaneous, and its interpolated tails do not have the maximum score's upper empirical-rank mass guarantee. Complete-unit percentile endpoints retain exact canonical interpolation. Explicit cell/percentile declarations retain the inherited two-stage per-cell schedule and binary64 replicate/probability boundary; they do not silently become the complete-unit experiment.

### Named estimators, missing support and atoms

Mean, median and sum support complete-unit percentile and max_deviation under the stated assumptions. Complete-unit min/max support **empirical envelopes only** under both calibrations: pointwise empirical bootstrap percentile envelopes or simultaneous empirical deviation envelopes. They emit a nonregular warning and caption, not population endpoint confidence claims. Count supports None only. Existing pointwise/descriptive workflows remain available: unweighted sum retains None/SD/PI/CI; weighted sum retains None/CI. SE is mean-only. SD and PI describe observations, not estimator uncertainty.

Every estimable target requires at least two contributing units. A reserved or entirely missing target has no invented estimate and is not a covered target. A genuinely empty selected facet has no family and zero inference work. If a replicate leaves any simultaneous target undefined, its family score is +Infinity. Keep **all B** scores. An infinite selected rank rejects the entire finite band; a finite rank reports undefined counts. Complete-unit percentile requires every target defined in all B replicates, otherwise the transaction rejects. Never use finite-only percentiles, change B, drop all-missing topology units or redraw until support appears.

A genuine empirical atom can have zero width. That does not establish zero population uncertainty. Positive canonical spans that collapse under native rounding reject rather than fabricate certainty.

The shared cell/C07 inverse-log effect boundary also rejects a positive working
interval whose mapped endpoints coincide. This correctness repair can reject
previously rendered false-zero intervals on inherited routes; it does not change
their samples, working estimates/percentiles or draw schedule. Genuine zero
working spans remain valid.

## Coordinates, topology and source identity

The x argument is the predictor and y the measurement, even horizontally. Actual primary/y2, vertical/horizontal numeric, categorical and declared real-clock routes use their actual target axes. Native numeric/date structural grids are built **per raw curve**, before response omission, plus explicit requested reservations. Observed x=[1,3] in A and x=[2,4] in B remain connected irregular curves: another curve's observations are not missing vertices. Units within one curve do contribute to its structural union. Categorical predictors use pooled declared ordinal slots; an absent selected group slot is a true gap.

Explicit missing responses and grouped missing cells break estimate paths and ribbons without changing estimates, old seeded ordering or admission. Raw missing coordinates or semantic keys remain barriers, while unrelated known-role rows are not fabricated missing observations. Raw lines never sort, average or deduplicate supplied observations to imitate lineplot.

`stat_scale="data"` estimates raw values, even on a log display. `stat_scale="axis"` on an applicable log response means log10 working coordinates, regardless of the display base, followed by inverse-mapping. Log observations/endpoints must remain positive. Log-working sum/count reject rather than become products/powers. Calendar responses use canonical UTC-day native units; calendar sum/count reject. Predictor clocks do not turn a numeric response into a calendar response. There are no callbacks or inferred statistical meanings for other primitive scales.

Persisted explicit inference controls choose the NEW typed unit identity: True differs from 1, False from 0, while numeric 1 equals 1.0. Opaque strings, including empty strings, remain valid unit IDs; required None/NaN exclude paired rows. Omitted-LineSpec and predictor-only inference retain inherited C07 unit identity and numerics. The decision comes from stored non-None controls, never keyword presence. Original columns/IDs survive JSON, actions and reopening.

The complete-unit generator is local explicit PCG64, first-selected-unit order, replicate-major uniform int64 draws in chunks of at most one million active choices. Sort, DPI, ribbon style and guide edits do not change its stream. Current/minimum provider parity is qualified on actual cases, not promised for every future NumPy/architecture.

## Raw mappings and one figure-owned guide

Raw line supports independent hue, size and style with the existing `SemanticSpec`. Hue controls actual color, size physical main stroke points, and style actual markers/dashes. A shared raw domain can therefore mean body outline points, point diameter points and line stroke points on different marks. These are not interchangeable units. Guides inherit actual native context and change only owned traits; a zero stroke keeps independent fill/glyphs. Numeric hue uses the same exact raw-label normalized colourbar and constant midpoint policy.

```python
mapping = mp.SemanticSpec(hue="condition", size="precision", style="method",
                         markers=["o", "s"], scale_id="original-rows")
p.line("time", "response", semantics=mapping)
p.shared_guides([mp.SharedGuideSpec("original-rows", location="outside right",
                                  title="Shared raw mapping")])
```

`SemanticSpec.scale_id` is the **sole persisted membership authority**. A strict `SharedGuideSpec(scale_id, location="outside right", title=None, frame=False, bbox_to_anchor=None)` request targets every stored compatible member and template in that named scope, including reserved empty facet cells. One request per unique name. No panel-ID list, implicit label matching, FacetGuide alias or second live store exists. Different families needing independent guides use different scale IDs.

`FigureSpec.shared_guides` is an optional omit-None list. `Plot.shared_guides(typed_or_dict_list_or_None)` dispatches the whole authoritative `SetSharedGuides` action. Named locations are outside right/top/bottom; a finite [x,y] anchor is trusted figure-fraction placement, not clamped. Panel LegendSpec remains unchanged. Consolidation preserves stored semantic legend/colourbar intent, suppresses only matching owned semantic guides and collects effect-specific contexts from all matching members. Dataset-label legends and unrelated scales remain. Conflicting mappings/labels or duplicate/unowned requests reject atomically. Empty selected data creates no fictional guide artist. Removing the last persisted owner requires clearing its request first; latent compatible live templates still count as owners.

Saved/local facet views remain authoritative. Local edits affect their cell; explicit SetFacetTemplate replaces all frozen cells and supersedes overrides, preserving selected rows, N13 IDs/nesting/placements and scale membership. SetData/reopen never rematerialize silently. Removing a live cell leaves saved materialized views rather than an incomplete live transaction. Both editors provide populated authoritative layer, whole-template and shared-guide JSON controls, with normal undo/redo/download/reopen behavior. This increment does not close broader F01/F02/G01.

## Bounded NEW inference work

Only persisted explicit inference controls classify D01 NEW work. Raw mappings, predictor-only, omitted, no-inference and SD/SE/PI routes receive no unexplained new inference row/cell/work cap. Shared-guide edits alone do not reclassify old layers; every render still charges every stored actual NEW invocation.

Complete-unit limits per layer are N<=10000 selected trajectory rows, R<=4096 structural/reserved slots, K<=4096 estimable targets and the existing B<=100000. Admit conservative `W_unit=B*(U+N+K)<=2000000000` before RNG/native creation. The NEW-only figure ledger sums actual W_unit invocations plus C07 actual unit/case work and bootstrap estimator reductions for explicit cell/percentile invocations. Its limit is also 2000000000, with separate components, not a CPU/SLA metric. Unknown cell work is admitted before its next chunk; no prefix/reduced CI is published. C07 local used/work limits and numerical kernel remain unchanged.

The conservative NEW inference working-state allowance is 268435456 bytes. It uses real product structures and canonical integer/Fraction bit bounds, including plans, heap/list slack, controls, active choices/scratch, wide temporary products, current scores/endpoints and retained NEW summaries. Exact bounded smaller-tail heaps retain only necessary order statistics, not B-by-family/target matrices or rounded finite scores; completed heaps/plans are released. This is not a source-data/native/RSS sandbox. Existing semantic rows/curves/categorical, facet64, panel256, layer1024 and 40M-pixel bounds remain. No D03–D06 metric is substituted for this ledger.

Schema remains0.1 and package1.1.0 until all-v2 release. Existing dependency/provider/security floors and Linux-only qualification remain unchanged; there is no other-OS or physical-print claim.
