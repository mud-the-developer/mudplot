# Opt-in scientific composition and QA (Unreleased)

The existing Matplotlib renderer, default calls, FigureSpec and JSON schema stay
unchanged. No new dependency is required. These features are available from the
unpublished v1.1.0 checkout and its locally built wheel/sdist, not retroactively
from the published v1.0.0 wheel.

## Layout policy

```python
import matplotlib.pyplot as plt
import mudplot as mp

p = (mp.plot({"method": ["A", "B"], "score": [0.97, 0.99]})
       .bar("method", "score", group="method")
       .labels(x="Method", y="Measured score")
       .ylim(0, 1).size(3.5, 2.6))
fig = p.save("comparison.pdf", layout_policy="smart")
plt.close(fig)

# Keep the original redundant hatch encoding for print.
fig = p.render(layout_policy="smart-print")
plt.close(fig)
```

Both policies reuse the publication theme for an untouched default theme;
explicit custom themes/styles are respected. Policies are **render-time options**,
not persisted spec fields: select one again when reopening a saved JSON figure.

- Render and measure legend bounds against visible bars, lines, collections and
  images in display coordinates, including neighboring panels and inset axes.
  Intentionally clipped data outside the axes do not count as visible collisions.
- Prefer direct labels for two individually labelled vertical bars, if labels fit
  and match the actual bar entries. Error bars, references and more complex
  comparisons retain a legend. No interval or measurement is changed.
- `smart` removes hatches only from those directly labelled bars: text still
  distinguishes methods without depending on colour. `smart-print` preserves
  their original hatches. Other fills keep existing accessibility encoding.
- Deduplicate identical legends across panels, comparing labels **and styles**.
  Shared or colliding legends move outside; choose columns and top/bottom
  placement using measured bounds. Preserve distinct encodings and reference URLs.
- Draw again and validate the repaired layout. Unresolved problems are reported,
  not hidden by cropping, shrinking measurements, or deleting labels.
- Missing, unambiguous axis labels get a readable column-name fallback. This is
  **not** a scientific description or an inference of units. Supply known labels
  with `.labels()`; generic/internal descriptions remain QA findings.
- Small/large linear y values use scientific notation. Axes are never silently
  switched to log, and original data and explicit limits stay unchanged.

`render()` still returns a normal Matplotlib Figure. A smart figure additionally
has `figure.mudplot_quality`, a JSON-safe report with measurements and repairs.
This is not an accessibility certification or a guarantee of good composition for
arbitrarily long labels, unusual projections or arbitrarily many panels.

## Chart recommendations, not silent geometry changes

```python
advice = mp.recommend(data, x="elapsed", y="response", group="method", time=True)
# Inspect advice["profiles"], ["recommendations"], and ["warnings"].

pairs = mp.recommend(data, x="condition", y="response", paired="subject_id")
events = mp.recommend(data, x="timestamp", y="lane", event=True)
distribution = mp.recommend(data, y="response")
```

Advice profiles types, cardinality, missingness, finite values, zeros and
1.5-IQR tail candidates. Ordered ISO datetimes, or **explicitly declared** numeric
time, favor trends; numeric ordering alone never establishes a temporal role.
Time ordering is checked within groups. Unordered/missing time is not recommended
as a connected trend. Repeated categorical measurements favor distributions;
explicit complete two-condition subject identifiers with finite numeric
measurements permit paired comparisons;
explicit events use the existing native `eventplot` for a single numeric train,
or raster-like scatter markers for multiple lanes. Sparse, repeated, dense or
wide-range values come with cautions rather than a universal scatter default.

Integer extrema, integral medians, IQR fences and numeric time comparisons keep
the original integer precision. Supported numeric inputs use exact rational
interpolation before IQR fence comparisons, so subnormal floats do not invent
zero-width fences and mixed integer/float medians do not lose integer low bits.
JSON medians round once to the supported scalar representation; existing integer/
float result types and signed zero are retained. Fractional medians use ordinary
JSON floats.
`coordinate-precision` warns when the renderer's floating-point coordinates cannot
represent supplied integers exactly; it never changes values, units or offsets.
Native event offsets also retain their supplied integer values. Missing time
coordinates warn rather than crashing or recommending a trend across the gap.
Declaring `time=True` does not coerce boolean or numeric-looking text into time.
ISO strings with nonzero sub-microsecond time/offset precision receive
`time-precision` and no trend recommendation: Python's date parser would truncate
those digits. This is not reported as repeated timestamps or bad ordering.
Fractional UTC offsets discarded by the datetime parser receive the same
warning, even at microsecond precision. Zero-only fractional padding remains
supported. Original strings are retained. Selected role columns must have equal
lengths, and advice is withheld when no row has usable coordinates and
measurements; those rows are not silently deleted.

Recommendations name existing geometries and their prerequisites, not new plot
types or executable statistical claims. The author must choose/implement them.
No sorting, smoothing, imputation, pairing by row position, aggregation, outlier
removal, unit inference, significance test or causal interpretation is performed.
NaN/infinity follow the existing input normalization to missing values.

## Machine-readable preflight

```python
report = p.lint(visual=True, layout_policy="smart", min_font_pt=8)
print(report)
payload = report.to_dict()  # json.dumps(payload, allow_nan=False)
```

Default `p.lint()` retains its existing static checks. `visual=True` renders at
the actual configured inches/DPI, measures the canvas and closes its temporary
figure. New findings contain stable `code`, `level`, `panel`, `message` and
`suggestion` fields. Composition errors fail `report.ok`; semantic/density
heuristics are reviewable warnings. Existing static findings use `code="style"`.

Visual font checks respect an explicit `min_font_pt` or the selected journal's
minimum; without either, the visual threshold remains 8 pt. Configured secondary
y axes are checked for scientific descriptions using their own routed values,
not uncertainty-band endpoint columns. Collision checks
ignore fully transparent or masked data, but retain visible hatches and marker
faces. Raster opacity combines per-pixel and artist alpha.

Checks include legend/data collisions, duplicate legends, text bounding-box
overlaps, clipped text/legends, minimum rendered font size, undersized panels,
marker-cell overcrowding, hatch noise, generic labels/titles, all-zero values,
small numerical magnitudes and wide ranges. Small magnitudes **do not establish
scientific negligibility**. Log suggestions explicitly exclude nonpositive data.
Intentional clipping of measurements to an explicit viewport is not a defect.
Text/artist bounds are deterministic composition proxies, not aesthetic scores;
review unusual glyphs/projections and the final publication placement yourself.

```bash
python -m mudplot render figure.json figure.pdf --layout-policy smart
python -m mudplot lint figure.json --visual --json
python -m mudplot lint figure.json --layout-policy smart --json
```

`lint` exits 1 for error-level findings, 0 otherwise. `--layout-policy` implies
visual measurement. Normal saves retain physical size; `tight=True` remains a
separate explicit crop and should not be used to claim exact-size QA.

## PGF and output failure safety

PGF export stages the text and generated raster sidecars under their final
basenames, substitutes references, then publishes sidecars before the PGF.
Existing outputs are backed up first and ordinary publication failures trigger
rollback; new files are removed. Successful filenames, references and final
permissions are preserved. Existing outputs must be readable for backup and
publication requires writable target directories.

If recovery itself fails, the original exception retains notes identifying the
remaining backup; the CLI prints these notes. Preserve that backup for manual
recovery. Private `.mudplot-pgf-*`, `.mudplot-write-*` and `.mudplot-backup-*`
paths are excluded from distributions. This does **not** promise an atomic
multi-file view to concurrent readers or durability after process termination.
No sandbox or filesystem-failure SLA is implied.

An extensionless render still follows Matplotlib's configured default format;
the CLI now reports the actual resolved filename rather than the unsuffixed input.

## Reproduce the four synthetic failure categories

```bash
uv run python examples/scientific_quality.py
uv run pytest -q tests/test_smart_quality.py
```

Eight PNGs and [the complete report](images/scientific_quality/report.json) are
produced at **300 DPI**, 3.5 × 2.6 inches (single column) or 7 × 2.6 inches
(two panels), with a measured minimum text size of **8 pt**. Pixel dimensions are
checked against the actual saved PNG, not a resized preview. These are synthetic
reproductions, not the unavailable original failure figures or experimental data.

| Category | Before | After | Explicit scope |
| --- | --- | --- | --- |
| Legend/bar collision + hatch noise | [PNG](images/scientific_quality/legend_collision_before.png) | [PNG](images/scientific_quality/legend_collision_after.png) | Layout only: direct labels, no redundant hatches |
| Repeated panel legends | [PNG](images/scientific_quality/shared_legend_before.png) | [PNG](images/scientific_quality/shared_legend_after.png) | Layout only: one shared legend |
| Dense temporal scatter | [PNG](images/scientific_quality/temporal_scatter_before.png) | [PNG](images/scientific_quality/temporal_scatter_after.png) | Author explicitly accepts the trend recommendation; every row retained |
| Internal labels and tiny metrics | [PNG](images/scientific_quality/metric_semantics_before.png) | [PNG](images/scientific_quality/metric_semantics_after.png) | Author supplies synthetic metric descriptions; scale warning retained |

Every after image has zero measured legend/data collisions, text overlaps and
clipped elements. The tiny-metric warning deliberately remains. None of these
checks substitutes for printing the final paper or domain review of the metric.
