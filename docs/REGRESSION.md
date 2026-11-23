# Regression inference and source-aligned diagnostics

*[한국어 / Korean](REGRESSION.ko.md)*

The existing `regplot` layer now has opt-in `RegressionSpec`/strict-dict settings.
`regression=None` retains the legacy polynomial renderer. `residplot` is a fluent
alias, not a new layer type. Source observations are never rewritten.

## Install only the effects you need

```bash
# From this Unreleased source checkout, not the old published v1.0.0 wheel:
pip install '.[render]'      # polynomial, residual and log-x effects
pip install '.[regression]'  # additionally Huber, binomial logit and LOWESS
```

The advanced extra adds statsmodels>=0.14.1; base `mudplot` still has no mandatory
dependencies. `all` and development extras include advanced regression. Pure
construction, validation, JSON, actions and replay import neither NumPy nor
statsmodels. A render request without the extra gives an explicit installation
error, preserving existing output/editor state.

## Models

```python
p = mp.plot(raw).regplot("x", "y", regression={"model": "robust"})
r = mp.plot(raw).residplot("x", "y", degree=2)
l = mp.plot(binary).regplot("x", "y", regression=mp.RegressionSpec(model="logistic"))
s = mp.plot(raw).regplot("x", "y", regression={"model": "lowess", "frac": 0.4})
```

| Model | Meaning | Important limits |
| --- | --- | --- |
| `poly` | Degree1–10 polynomial criterion fit | Complete basis and one intercept; full-design partial normal approximation or explicit paired-case percentile |
| `logx` | Linear response against natural ln(x) | Positive predictor; degree1; independent of display log base, not log(y) |
| `robust` | Huber loss; original unweighted RLM or declared weighted-MAD0 operator | Degree1,50 iterations; weighted zero-MAD/nonconvergence rules below |
| `logistic` | Binary logit criterion model | Both numeric classes0/1, degree1,100 iterations; no frequency/trial covariance interpretation |
| `lowess` | Local-linear fixed-frac smoother | Physical cases define neighbors; >=3 distinct x; frac (0,1], residual iterations0–20 |

`frac` (default 2/3) and `iterations` (default 3) are LOWESS-only; nondefault
values on another model fail instead of being ignored. Neighbourhoods need at
least two rows. Typed regression caps 10000 selected rows/layer; LOWESS caps 5000
rows/group. Missing/nonfinite selected coordinates and singular designs fail.
Existing panel selectors/hue orders are applied before group fitting.

Typed fits scale predictors and responses before linear algebra and restore raw
coordinates afterwards. Nonfinite predictions, separation, nonconvergence and
unrepresentable residuals fail without regularization, jitter or an invented fit.
An exact line is already a Huber minimum; it does not need a fictitious MAD scale.
Log coordinate axes require positive input/predicted values; residual y is linear.

## Relative criterion masses and explicit confidence

```python
p = mp.plot(raw).regplot(
    "x", "y", weights="mass", confidence=95,
    regression={"model": "poly", "bootstrap": {"n_boot": 399, "seed": 17}},
)
```

`weights` is the existing source column, never a sampling probability or trial
count. Polynomial/log-x minimizes `sum(w_i*(y_i-P(x_i))**2)` using square-root
relative numerical weights. Weighted Huber and LOWESS use the general operators
below for point-only and confidence requests alike. CI presence cannot change the
point estimator. Positive common mass scaling leaves the criterion unchanged.

`confidence` is the only coverage percentage. An explicit `bootstrap` selects
uniform IID paired **physical cases**: each draw carries predictor, response,
nuisance values, original criterion mass and original source index together.
Default n_boot1000, domain1–100000 and seed0/nonnegative integer are naming
domains, not permission for every row/grid/iteration product. Each fitted
replicate evaluates the same original requested targets. All B draws remain;
any required singular, separated, unconverged, nonfinite or undefined replicate
rejects the ordinary percentile result. No retry, finite-only ranking or smaller B.
The traversal is replicate-major, then curve by its first positive selected
training **or query** original physical occurrence, then training/query draws.
Zero-mass predecessors and display hue order do not reorder that experiment.

Bounds use the shared exact type7 interpolation of actual finite binary64 model
predictions. They are **nominal pointwise estimator/operator uncertainty**, not
simultaneous/continuum coverage or future-observation intervals. IID representative
cases, identifiable stable fits and regular targets are assumptions, not guaranteed
by rendering. LOWESS intervals target the fixed smoother and do not remove bias.
Empirical atoms can have zero width without proving population certainty.
Positive intervals lost at the native floating boundary reject.

Omitted controls retain legacy point behavior and unweighted poly/log-x
normal-approximation mean-fit bands. Weighted/advanced/residual confidence requires
the explicit paired-case declaration. No precision/frequency/wild/BCa/simultaneous
or prediction-interval method is exposed.

### Weighted robust operators

Weighted Huber alternates complete weighted least-squares coefficient steps for
HuberT threshold1.345 and `s=Q_left,w(abs(residual),0.5)/Phi_inverse(0.75)`.
The scale uses original canonical criterion masses, not changing IRLS weights.
Both normalized coefficients and relative scale must stabilize within50 steps.
Zero MAD with any nonzero positive-mass residual is undefined; an actual empirical
exact line is legal. No epsilon scale/rank fallback is invented. Equal explicit
weights at even N use the lower observed median, which can differ from unweighted
RLM's average median. There is no equal-weight shim.

Weighted LOWESS uses physical kth-neighbor distance with
`k=min(N,max(2,int(frac*N+1e-10)))`, zero tricube weight at boundary ties, and
local regression on `[1,(x-t)/h]` with criterion×kernel×robust masses.
Robust passes use the original-mass CDF-left absolute-residual median and
bisquare factors. A zero median uses its exact zero-residual limit, not a floor.
Zero radius, unsupported local rank, erased positive mass or nonfinite prediction
rejects. Unweighted provider behavior remains inherited; near-degenerate/even-N
weighted behavior is deliberately not claimed identical to that provider.

## Partial, held-out and independently owned trend workflows

```python
p = mp.plot(raw).residplot(
    "x", "y", weights="mass", confidence=95,
    regression={
        "model": "poly",
        "partial": {"columns": ["z"], "reference": {"z": 0}, "method": "joint"},
        "sampling": {"train": {"split": "train"}, "query": {"split": "query"}},
        "bootstrap": {"n_boot": 399, "seed": 17},
        "diagnostics": {
            "kind": "raw",
            "trend": {"model": "lowess", "frac": 0.8, "iterations": 1},
        },
        "components": {
            "fit": {"color": "#075985", "line_width": 1.5},
            "scatter": {"color": "#64748b", "marker_size": 4},
        },
    },
)
```

Poly/log-x partial fits use the **entire** polynomial/log basis with nuisance
columns and one intercept. FWL residualizes every basis column and response, not
raw x before squaring. The permitted unweighted partial normal band uses full
model residual rank/DF/covariance. Huber/logit partial fits are joint conditional
models, not nonlinear FWL. LOWESS requires explicit `method="two_stage"`:
training nuisance projections residualize both predictor and response; the
smoother predicts those coordinates and adds the response projection back.
Every nuisance stage is refitted in each bootstrap.

The displayed conditional curve uses the persisted nuisance reference.
Default partial observations use `y-m(x,z)+m(x,z_ref)` on the **raw predictor**
axis, not residualized x; logit-adjusted observations can lie outside[0,1] and
are not raw Bernoulli outcomes. Held-out prediction glyphs use each query's
**actual nuisance values**, never reference-value imputation.

Explicit train/query filters use the existing typed equality selector language
(at most two columns each) and must be disjoint original physical rows. No
complement/random split or arbitrary-ID join is inferred. Query-only prediction
may omit y; a requested raw/deviance diagnostic needs its actual observed y.
Required selected training/nuisance values remain strict: no listwise deletion
or imputation. Explicit panel dropna stays a caller decision. Zero masses remain
in saved source, but not fitting/draws/glyphs. True empty reservations have no
fake estimate/guide. A positive query group without a fitted training group errors.
Strict-input and missing-training-group errors identify the original physical
source row even after sparse panel filtering; zero mass does not waive strict
required-input validation.

Residual mode keeps one zero reference and actual `y-m(x,z)` or mathematical
signed square-root binary deviance. For y1, deviance is `sqrt(-2*log(p))`;
for y0, `-sqrt(-2*log1p(-p))`. Matching p0/1 is0, mismatch is genuine infinity:
a finite native request rejects with original row identity, never clips/drops it.

At a fixed observed row, first take the **mean-response** percentile set[L,U],
then map it to raw `[y-U,y-L]` or monotone deviance `[g_y(U),g_y(L)]`.
This is conditional mean-fit uncertainty, not type7 of transformed diagnostic
draws or future residual/error variability. A declared independent trend has
its own continuous model/style and **full-pipeline** percentile: resample/refit
primary+nuisance, form resampled residuals, refit trend. Explicit OOS draws train
then independently query cases per replicate; query responses never train the
primary. In-sample has no second query draw. Empty explicit query stays empty.
No fixed-fit alternative or binomial model of arbitrary residuals is exposed.

Fit/scatter ComponentStyleSpec properties affect only their real native marks;
the trend owns its own style. Hide/show, title, guide and DPI edits do not change
the declared experiment. Source columns/IDs/duplicates and native row attribution
survive actions/history/download/reopen; no computed result store/API is added.

## Map the points, not the experiment

Pass `semantics=SemanticSpec(...)` to `regplot` or `residplot` to map the face
colour, diameter in points, or marker of the emitted observations, partial
adjusted observations, held-out fitted responses, or diagnostics. Choose
`hue_kind="numeric"` and `colorbar=True` for the raw hue calibration, or use
the same named `scale_id` as `scatter` to share a calibration. Point style is
a marker, not a dash. The existing outline colour and width are independent.
A mapped diameter of zero is legal; a positive diameter that underflows
when converted to a native point area is rejected.

Roles are read from the original selected rows, even if the same column is
converted to a date coordinate for display. A missing role or a value outside
its declared order hides only the corresponding point. Hidden components
and zero criterion masses do not calibrate a guide; legend keys come from
emitted glyphs rather than reserved slots. A raw point with an intentionally
zero mapped diameter can still calibrate the scale.

`group`, layer `hue_order`, R4 train/query selectors, criterion masses and
model options control the experiment, not the mapping. The map does not
alter sampling, fit, interval, residual, trend, or reference. Styling in
`regression.components.scatter` cannot also own a mapped property on a
visible glyph; `components.fit` still owns its independent stroke, band and
uncertainty. Explicit query marker traits cannot duplicate a mapped role.
Use actual primary or enabled twin axes, including supported fixed facets.
Omitting `semantics` preserves the unmapped point route.
[Runnable example](../examples/regression_glyphs.py).

## Native coordinates and finite admission

Logical x is predictor and logical y response in both orientations: v/primary
uses X/Y, v/y2 X/Y2, h/primary Y/X and h/y2 Y2/X. Raw fitting and natural ln are
display-base independent. Calendar predictors use the declared canonical UTC-day
clock; ln(UTC days since1970) is explicitly origin-dependent and positive-only.
Timestamp predictions remain timestamps. Calendar-response residual/trend
durations are refused rather than displayed with a date formatter.

Typed selected rows10,000, LOWESS5,000/group and inherited degree/iteration/native
limits remain. NEW complete design is at most19 columns. Before RNG/native output,
actual NEW invocation and figure aggregate upper work is bounded by6,000,000,000:
original point/allB/query/nuisance/trend/gathers/local/median/evaluation/tails and
variable seed conversion all count. Only scientifically consumed targets are
computed; residual-only does not invent a primary fit grid.

The268,435,456-byte conservative numerical managed/provider-reserve admission
estimate counts actual product plans/buffers, canonical CDF bigints, exact tail
heaps and overlapping one-vector ordering/sign/interpolation scratch, controls
and earlier retained summaries. It is **not an RSS, native-artist or universal
opaque-provider allocation bound**, nor a CPU/SLA promise. Known oversized requests
reject without reducing rows/B/grid or changing legacy omission/admission.
Consumed input columns are prepared once per layer. Existing source/spec values
and group labels are borrowed, not recursively charged as NEW allocations; new
view containers, clock values and row bookkeeping are charged. Every known
figure input/plan/stage and earlier output-shape bound is checked before the
first RNG, including an oversized later layer. Actual retained numerical results
are still checked before native publication.
Full renderer/editor failures retain accepted state and previous native output.
Joint marginals still cannot pretend raw y/weights are residual distributions.

## One question per executable example

All data below are synthetic; each figure is checked at 700px desktop width.
There is no independent readability score or causal/model-selection claim.

- [Residuals](images/regression_residual.png) · [spec](images/regression_residual.mplot.json)
- [Log-x response](images/regression_logx.png) · [spec](images/regression_logx.mplot.json)
- [Huber with retained outliers](images/regression_robust.png) · [spec](images/regression_robust.mplot.json)
- [Binary probability](images/regression_logistic.png) · [spec](images/regression_logistic.mplot.json)
- [Local trend](images/regression_lowess.png) · [spec](images/regression_lowess.mplot.json)

PDF/SVG companions have the same basename. [Source](../examples/regression_modes.py).

```bash
uv run python -m examples.regression_modes
uv run pytest -q tests/test_regression_models.py tests/test_new_layers.py
```

## JSON and editors

```json
{"type": "AddLayer", "layer": {"type": "regplot", "x": "x", "y": "y",
 "regression": {"model": "robust", "residual": true}}}
```

Unknown config fields fail. The same spec opens in existing editors and uses the
same validated action path. No spec or package/editor version bump is required;
old JSON defaults to `regression=None`. Tests compare fits to independent
statsmodels/NumPy references, verify group/facet residuals and extreme-unit
scaling, reject unsafe requests, simulate missing optional effects and check
JSON/action/schema/editor and deterministic PNG/PDF/SVG without global RNG.
