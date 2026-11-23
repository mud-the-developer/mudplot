# Violin workflow: paired halves, native components and shared roles

C04 extends the existing `violin` layer. It does not claim full upstream parity or completion of broader F01/F02/G01/E01/Q01/REL01 or all v2. Package1.1.0, schema0.1, dependency floors and the dependency-free declarative core remain unchanged.

Run the complete synthetic examples:

```sh
python -m examples.violin_workflow artifacts/v2_violin
python -m mudplot render artifacts/v2_violin/violin_paired_profiles.mplot.json exact.png
```

The examples save editable JSON and actual PNG/SVG/PDF. Data are deterministic synthetic observations with retained original IDs, not experimental results. No source observations are rewritten, replicated, sampled or silently pooled.

## Compatibility and input roles

`.violin(value, group=category)` keeps the one-column meaning; `.violin(category, value, group=hue)` keeps category/value roles even with `orient='h'`. Omitted new controls preserve the legacy native/default path and JSON. Existing `split=True` without a new `ViolinSpec` remains exactly two selected/reserved hues at one shared center.

The optional `LayerSpec.violin` is appended after earlier fields and omitted when None. `ViolinSpec` and `ViolinHueComponentsSpec` accept the same strict typed/dict forms through builders, actions and JSON. Components stay in the existing `LayerSpec.components: DistributionComponentsSpec`; the new optional role fields are appended and omitted when None. No callback, Path object or arbitrary Matplotlib kwargs is serialized.

```python
p = mp.plot(raw).violin(
    "season", "response", group="treatment", weights="weight",
    inner="box", split=True, density_norm="count", common_norm=True,
    violin={
        "split_policy": "paired",
        "hue_components": [
            {"level": "control", "components": {"whisker": {"color": "red"}}}
        ],
    },
    components={"body": {"alpha": 0.9}, "box": {"line_width": 1.5}},
)
```

## Explicit multi-hue split policy

`violin={"split_policy":"paired"}` requires `split=True` and an independent categorical hue. It never silently replaces the old two-hue contract. Numeric continuous hue supports full profiles but not automatic pairing.

For H frozen hue slots, let P=ceil(H/2), C be the working category center and W the full pre-gap body width. Hue i uses pair j=floor(i/2), center `C+(j-(P-1)/2)*W/P`, and full pair span `W/P*(1-gap)`. Even hues occupy left/below halves, odd hues right/above halves. An odd last hue has only a left half; H=1 is a legitimate single left half. H=2 has the old mathematical half geometry. Reserved empty hue slots keep pair assignment but create no body, inner observation or observed legend entry.

Only automatic/zero dodge is accepted: this policy owns pair placement, with no extra hue dodge. Width and gap stay category-coordinate controls, not point size or probability mass. All size/style raw tuples within a hue retain separate fitted profiles in that hue's lane.

## Gaussian fitting, weights and normalization

The existing Gaussian evaluator is reused. `bw_method` is Scott, Silverman or a positive finite factor; `bw_adjust` is in(0,1000], `points` in2..1000, and `cut` in0..10 bandwidth units. There is no SciPy requirement, callable bandwidth/kernel, bootstrap or alternate evaluator.

Clip bounds are increasing raw absolute measurement values, with either endpoint None. A declared measurement clock parses calendar literals through the actual target axis. Clipping limits support only: fitted rows, positive weight mass and inner observations/summaries remain available outside that support. Empty or unresolvable support fails clearly.

Weights are paired finite nonnegative relative masses. Missing/zero rows are excluded before positivity; positive observations are never replicated. Gaussian covariance uses the existing unbiased weighted/effective-n policy. Weighted quartiles use the inverse right-continuous weighted ECDF, not interpolated NumPy quantiles. Singleton/constant profiles remain observed degenerate bodies, not invented Gaussians or confidence intervals.

Raw hue/size/style tuples partition fitting, but **normalization pools use effective hue only**. Without independent hue there is one comparison pool. `common_norm=True` uses the global pool. Peak/mass references are resolved once per new-path pool:

- `width`: each profile has unit peak.
- `area`: densities use a common reference peak in fitted-coordinate units, not a guarantee of identical clipped polygon areas.
- `count`: each unit-peak profile is scaled by its row count or positive relative weight mass divided by the pool maximum.

Semantic size is never weight, effective n, density or area. Shared semantic domains do not change these statistical pools. Raw unextended `inner='legacy'` uses public native `Axes.violin` on already fitted statistic dictionaries, preserving native inner color/span grouping and existing wrapper/explicit flag precedence without refitting. Extended, weighted, split and named-inner paths retain their declared profile normalization.

## Components and actual native traits

| Inner mode | Available component roles | Native meaning |
| --- | --- | --- |
| any | body | Filled profile collection, outline, alpha and bounded hatch |
| legacy | mean, median, extrema | Native statistic segments; existing show flags apply |
| box | whisker, box, median | Observed Tukey whisker segment, Q1-Q3 trunk, actual median glyph |
| quart | quartile | Three true weighted/unweighted quartile spans |
| point | point | Each positive-weight observed row once |
| stick | stick | Each observed row's local profile-width segment |
| None | body only | No invented inner marks |

`ComponentStyleSpec` remains the shared bounded property vocabulary. Segment roles reject marker-only fields; box median/point accept actual glyph properties. Box and boxen reject these newly unavailable violin roles rather than silently ignoring them. A requested applicable legacy statistic component may enable its mark when the flag is None; explicit false conflicts. Mean/CI/outlier observations are not fabricated.

Unowned precedence is native/theme → scalar layer → global component → exact per-hue component, merged fieldwise. Raw hue keys retain typed identity (`True` differs from numeric1); override entries must be unique, known categorical levels, including declared reservations. Numeric continuous per-value overrides reject. Scalar/global/per-hue owned-property conflicts reject before artists.

Zero-width dashed components retain native segment coordinates, body fill/hatch and independently requested real glyphs. Stroke absence is represented natively; no epsilon width, hidden whole artist, row deletion or suppressed warning is used. The accepted minimum-renderer prerequisite itself showed no existing quart zero-dash defect; it is not claimed as a repaired bug.

## Shared hue, physical size and style

Use `semantics=SemanticSpec(...)` or the equivalent strict dict:

- HUE owns **body fill only**; categorical/numeric mapping and raw labels share the existing original-row domain pools.
- SIZE owns **body outline stroke points only**. It does not change profile width, probability/mass, inner strokes or marker diameter.
- STYLE owns **body named dashes** and, only in point/box modes, the actual point/median glyph. The persisted markers cycle always applies, default cycle included. Dash-only legacy/quart/stick modes do not require unused marker-cycle capacity or invent guide glyphs.

Other inner/mean marker diameters, edge/face properties and segment styles remain independent. Mapped body fill/width/dash or actual inner marker cannot be overridden at scalar/global/per-hue tiers. Harmless independent whisker/quartile/stick colors and widths remain valid. Registered markers are real native glyphs, not circle approximations.

Guides use a violin-shaped native legend handler with actual owned body/glyph properties, not scatter-area or box proxies. They do not update observed data limits. Original rows are deduplicated for shared domains; separate rendered layers still retain their own physical instances. Shared logical primary+y2 colorbar intent/deduplication remains the existing foundation behavior.

## Coordinates, live views and bounds

Applicable vertical/horizontal, primary/y2, numeric-native/log category and category/measurement clocks are supported. Resolve the real target y/y2 before parsing or scale checks. Temporal coordinates are canonical UTC days with the declared label clock; physical stroke or category fractions are not date/density units. Positive log observations and clip bounds are required. `stat_scale='data'` fits raw values; `axis` fits existing log10 working values and inverse-maps once. N12 base2/subs are display controls, not a redefinition of statistical units. New symlog/asinh/logit violin statistics are not inferred from raw-primitive support.

An `axis='y2'` request requires an existing `.secondary_yaxis(...)` declaration.
Missing target configuration rejects instead of silently drawing on the primary axis.

Existing live recipes keep frozen selectors, resolved category/hue orders and cell IDs. Local edits stay local; a later explicit whole `SetFacetTemplate` replaces all intended cells and supersedes those overrides. Saved materialized views are truth on reopen; recipe storage does not rerender on load. SetData can refill reserved cells without adding selectors or parsing excluded rows. Filtered/reserved-empty new views fit nothing while options/references/resources still validate. The ordinary unfiltered all-missing policy stays unchanged. This reuses the existing G01 increment, not a new mapper or whole-G01 closure.

New advanced paths admit at most **10000 selected source rows and256 DRAWN profiles/layer**. Categorical category/hue/size/style levels and override entries are bounded at64; continuous numeric hue/size values are not capped at64. Support points stay2..1000 and point/stick retain all selected rows. Fitting work is bounded by10M Gaussian terms/layer for that envelope; accepted preflight reports measured tracemalloc/time, not RSS or an SLA. Native paths include backend closing vertices, so support-array arithmetic is not a strict Path-length claim. Existing facet64/figure256panels/1024layers and render bounds remain, with admission before large coordinate/native work. No limit lift or silent sampling is introduced.

## Editor, saving and qualification

Both local frontends expose registered layer JSON and RAW actions for `ViolinSpec`, roles, components and explicit live-template transactions. Invalid requests must retain accepted Spec/PNG/history; undo/redo, downloads, reopen and post-reopen edits use the same pure reducer. The actual displayed PNG revision is checked against decoded current-cache RGBA during qualification.

Rust PNG download remains its existing capped preview; exact requested-DPI PNG comes from the installed CLI/API using the same downloaded JSON. SVG/PDF are actual vector exports. Current/minimum installed drivers and native references use one frozen wheel and matching source-unset origins; pure Python-S actively denies optional dependencies. Independent numeric/native/legacy, actual UI and compiled PGF/glyph/citation/URI evidence is recorded separately, never summed or relabeled. Broader F01/F02/G01 and product qualification remain open.
