# Configured regression and raw residuals

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
| `poly` | NumPy polynomial response fit, degree 1..10 | Existing normal-approximation mean-fit band only when requested |
| `logx` | Linear response fit against natural log(x) | Positive x, degree 1; this is not log(y) or a logistic model |
| `robust` | statsmodels RLM with HuberT loss | Degree 1, max 50 iterations, no automatic removal of outliers |
| `logistic` | statsmodels GLM Binomial with logit link | Both numeric y classes 0/1, degree 1, max 100 iterations |
| `lowess` | statsmodels local linear smoother | >=3 distinct x, frac in (0,1], iterations integer 0..20 |

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

## Residuals are not deviance or inference

`residplot` forces `residual=True` on a copied config. It plots **observed y minus
in-sample fitted response** at each original x, in original row order, plus one
zero guide per layer. Fits happen independently per selected raw group/facet.
It does not imply out-of-sample errors, deviance residuals, weights, correlation,
causal inference or an extra LOWESS trend of residuals. Choosing model='lowess'
computes residuals from a LOWESS fit to the original response.

Joint grids reject a residual template because their marginals describe raw y,
not residual y. Ordinary configured regplot templates can still use joint/facet
paths within their existing data/axis limits.

`confidence=95` remains opt-in normal-approximation mean-fit CI for poly/logx,
not bootstrap or simultaneous whole-curve coverage. Residual/robust/logistic/
LOWESS confidence bands are explicitly unsupported. Wider fit/scatter controls,
weighted regression and bootstrap inference remain separate work.

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
