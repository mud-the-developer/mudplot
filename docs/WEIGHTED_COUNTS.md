# Weighted counts and normalization (v2)

This implements the [C06 contract](V2_SCOPE.md). The overall v2 release candidate
is still in progress. [한국어](WEIGHTED_COUNTS.ko.md)

```python
from pathlib import Path

import mudplot as mp

p = (
    mp.plot({"condition": ["A", "A", "B"], "frequency": [1, 2, 5]})
    .countplot("condition", weights="frequency", stat="percent")
    .labels(x="Condition", y="Declared frequency mass (%)")
)
mp.save_spec(p.spec, "counts.mplot.json")
p = mp.Plot.from_json(Path("counts.mplot.json").read_text(encoding="utf-8"))
p.save("counts.svg")
```

## Numerical contract

`weights=None` retains ordinary row counts. With an explicit weight column,
`stat="count"` sums usable weights in each category/hue cell. Fractional weights
are not rounded or expanded into invented observations.

`probability` and `proportion` divide by the selected mass in the requested
scope; `percent` multiplies by 100. The example above gives 0.375/0.625 or
37.5/62.5. All scopes are **local to each panel/facet**:

| `normalize_scope` | Denominator |
| --- | --- |
| `None` or `"all"` | All usable selected categories and hues (existing default) |
| `"category"` | All usable hues within that category |
| `"group"` | All usable categories within that hue/group |

The latter two require normalized counts; `"group"` also requires `group`.
They do not silently change raw `stat="count"`. Figure-wide denominators and
aliases such as `"hue"` are not supported.

- Explicit category/hue orders select contributing rows and reserve empty
  slots; source rows retain their original order.
- Required missing observations and zero weights do not contribute.
  Nonmissing weights at the validation boundary must be finite, numeric,
  non-boolean and nonnegative. Existing ingestion/missing-value rules remain.
- No usable positive weight is an error in a nonempty selected cell, not an
  invented zero measurement. A genuinely empty reserved facet has no marks;
  invalid statistical configuration still fails there.
- Ordinary sums use compensated finite-mass arithmetic. At overflow/subnormal
  boundaries, exact standard-library rational arithmetic preserves representable
  positive normalized mass, including percentage factors. Rows are not
  individually scaled to zero. Absolute mass outside the finite range errors.
- No count confidence interval or significance claim is inferred. Input
  measurements and declared units remain unchanged.

## Explicit log-value stacks

For `stack=True` on a log value axis, supply a finite positive `baseline`
strictly below the **first positive cell mass in every category**. Tops remain
raw cumulative mass. With masses 2 and 3 and baseline 1, rectangles run 1→2 and
2→5: the top is **5**, not 6. The first rectangle is truncated by the explicitly
chosen display baseline; its label still reports the raw segment mass 2.

```python
import mudplot as mp

p = (
    mp.plot({"x": ["A", "A"], "g": ["u", "v"], "w": [2, 3]})
    .countplot("x", group="g", weights="w", stack=True, baseline=1)
    .yscale("log")
    .labels(x="Condition", y="Declared frequency mass")
)
p.save("log_counts.svg")
```

This applies in both orientations and with native/log category coordinates.
Missing hue slots are skipped. Labels retain segment values and use the visible
log-space midpoint. An invalid baseline, overflowing cumulative endpoint or
collapsed positive segment raises before publication; no fake geometry is used.
Choose the baseline in the units of the selected statistic (e.g. percentage
points for `percent`). No baseline is added to totals and no log-space
multiplication is performed.

Counts use data-space statistics; axis-log count estimation remains rejected.
Existing primary/secondary-axis restrictions otherwise remain. Linear stacks
retain their zero-origin defaults and reject an explicitly supplied baseline.

## Editing and compatibility

Existing `StatSpec.weights` and optional `StatSpec.normalize_scope` carry the
contract through Python, JSON, actions and advanced FigureSpec editing:

```json
{"type":"countplot","x":"condition","group":"cohort","stat":{"estimator":"count","errorbar":null,"weights":"frequency","normalize":"percent","normalize_scope":"category"}}
```

Old `0.1` FigureSpecs without the new optional field remain readable. The schema
version stays `0.1`; as with other additive features, new settings require an
updated reader. The unset new scope is omitted so legacy JSON round trips
without an added field; other nullable defaults are unchanged. No new required
field, core dependency or callback is introduced.

Run [the executable example](../examples/weighted_counts.py):

```sh
python examples/weighted_counts.py --out artifacts/weighted_counts
```

It saves a global linear example and a category-normalized log-stack example
as PNG/SVG/PDF (explicit opt-in smart layout) and JSON, reopens JSON and
checks data/state preservation.
Regressions are in `tests/test_weighted_counts.py` and
`tests/test_count_scopes.py`. [Batch evidence](review_evidence/v2_count_scopes.json)
distinguishes feature checks from final v2 qualification.
