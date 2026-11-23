# Compose coordinate transforms with named statistics

[한국어](COORDINATE_PIPELINE.ko.md) · [Runnable synthetic example](../examples/coordinate_pipeline.py)

`LayerSpec.transforms` declares ordered operations on logical inputs, not on already drawn artists. For each view mudplot selects the original observations, projects the requested coordinates, computes the existing statistic once, then applies the mark's native move and the panel's display scale. The saved source table, weights, units, categories, and semantic mappings are not rewritten.

```python
import mudplot as mp

p = mp.plot({"dose": [1, 1, 10, 10], "response": [1, 10, 10, 100],
             "mass": [1, 3, 1, 3]})
p.pointplot("dose", "response", weights="mass", errorbar=None, native_scale=True,
            transforms=[mp.TransformSpec("y", "log")])
p.axis_scale("x", "log", options={"base": 2}).labels(y="log10 response")
```

The first estimate is `(1×0 + 3×1)/4 = 0.75`, not `log10(7.75)`. The base-2 display is on the **other** axis. A response fitted with `stat_scale="axis"` is a different existing operation: it works in log10 and maps results back to native values. An O01 `log` leaves values in log10 coordinates and does not apply a data-space Jacobian.

## Stages and supported roles

Use 1–4 stages in total. Per role: `identity`, `log`, `standardize`, or `log` followed by `standardize`. Different roles can be interleaved in the list. `None`/omission keeps the old path and JSON; explicit identity records intent without changing the result. An empty list is invalid. Stages have exactly `role` and `name`; Python accepts `TransformSpec` or a dictionary for each entry.

- `log` requires positive finite numeric coordinates and uses base 10. `standardize` uses the selected view's population mean and standard deviation, after any preceding log. Each eligible physical row counts once for these moments, including duplicates; positive weights affect eligibility and the later statistic, not calibration. The fitted coordinates stay fixed during resampling. Empty views draw no invented results; a nonempty constant calibration, nonfinite result, or loss of distinct coordinates rejects.
- `barplot`/`pointplot`/`lineplot`: native numeric predictors and numeric measurements; count may not transform its measurement. Ordinary categorical predictors and clock coordinates accept identity only. `countplot` changes only its native numeric category coordinate. Supplied `line` retains source topology; it does not estimate. A strip uses its declared categorical route (`strip=mp.StripSpec(...)`, for example), with native numeric `x` and numeric `y` as applicable.
- `hist`/`kde`/`ecdf` take logical observation `x`, even horizontally. Named histogram/KDE declarations are required for nonidentity; old untyped compatibility calls are not silently reclassified. `hist2d`/`kde2d`/`ecdf2d` use logical observations `x` and `y`. The existing kernels, named bandwidths, bivariate levels/HDR, empirical complement, and statistical/inference combinations retain their own validation.
- No nonidentity stage shares its role with a clock, native log display, or a statistical axis fit. An eligible independent role can still use a clock or a native log display/fit. Mixing raw/derived coordinate units on the same data axis or an explicitly shared group rejects. Type-preserving raw orders, hue/size/style domains, weights, grouping and inference unit IDs retain their meanings, even when they share a source column with a coordinate.

## Coordinates, moves and editing

Supply explicit bins, clips, ECDF queries/bounds, axis limits, baselines and tick/reference positions in the units actually plotted. `order` still selects original coordinate keys; numeric native slots get derived positions. A separate clock still uses its existing day/ISO option rules. Density uses projected widths/areas; a histogram density is unchanged by a later dodge. Univariate histogram modes and univariate KDE stack/fill keep their existing contribution and normalization meanings. Count stacks use their existing raw cumulative mass; strip jitter uses the original seeded slot metric after dodge. An ECDF or paired field has no invented displacement or stack.

Saved figures contain declarations and raw data only. Both editors show the **Coordinate pipeline** help in the registered layer forms. In **Add layer** or a populated **Replace layer** form, set e.g. `"transforms":[{"role":"y","name":"log"}]` inside the layer; set it to `null` or remove it to clear. Use the axis controls for display scaling. In live facets, **Replace layer** edits just that cell; **Whole live facet template** explicitly replaces the fixed views. Reopen and undo/redo retain the same stored authority; there is no automatically stored transform result. Existing work/admission policies apply to the scientific route; legacy and identity routes acquire no O01 capacity cap.

```sh
python examples/coordinate_pipeline.py /path/to/output
python -m mudplot validate /path/to/output/coordinate-pipeline.mplot.json
python -m mudplot render /path/to/output/coordinate-pipeline.mplot.json /path/to/output/preview.png
```

The example writes editable JSON, PNG, SVG and PDF. This is the finite O01 contract, not a drop-in objects API. No dependency, platform or schema-version change is required.
