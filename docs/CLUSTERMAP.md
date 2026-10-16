# Hierarchical clustered heatmaps

*[한국어 / Korean](CLUSTERMAP.ko.md)*

Unreleased source-tree `clustermap` is a matrix layer with optional hierarchical
clustering effects. The original matrix stays in JSON; transformed values and
leaf orders are computed when rendering, never stored as stale derived columns.

![Row-standardised synthetic profiles with aligned trees and metadata](images/clustered_profiles.png)

[Editable spec](images/clustered_profiles.mplot.json) ·
[SVG](images/clustered_profiles.svg) · [PDF](images/clustered_profiles.pdf) ·
[Source](../examples/clustered_profiles.py)

The example uses synthetic profiles, reviewed at 700px desktop width. Colour and
annotations show **row sample z-scores**, not original response units. The hidden
cell still participates in standardization/clustering. Neither tree nor colour
implies significance, causal structure or a universal readability certificate.

```bash
# From this source checkout, not the already-published v1.0.0 wheel:
pip install '.[cluster]'  # render plus SciPy>=1.10; base dependencies stay empty
```

```python
p = (mp.plot().matrix("m", values)
       .clustermap("m", cluster={"method": "average", "metric": "euclidean",
                    "row_cluster": True, "col_cluster": True},
                   heatmap={"xlabels": columns, "ylabels": rows},
                   clabel="Response")
       .size(7, 6))
```

Pure construction, validation, schema, actions and JSON do not import NumPy or
SciPy. `cluster`/`heatmap` accept strict ClusterSpec/HeatmapSpec or dict. Unknown
fields fail. All/dev extras include clustering; no required core dependency,
package/editor/spec-version bump or release publication is implied.

## Orders, trees and supplied linkage

Supported methods: single/complete/average/weighted/centroid/median/ward.
Metrics: euclidean/cityblock/cosine/correlation. Ward/centroid/median require
Euclidean distances. Finite vectors with undefined cosine/correlation distances
fail without jitter or imputation. Distances are computed in scaled units and
restored when appropriate; unrepresentable linkage heights fail.

`row_cluster=False`/`col_cluster=False` retain that original order. A one-item
axis has no invented tree. `optimal_ordering=True` applies to computed or supplied
trees using distances from the display matrix. Results are deterministic within
the locked SciPy version; equal-distance ties are not a cross-version guarantee.

Optional row_linkage/col_linkage use checked `(n-1) × 4` JSON arrays of
`[left,right,distance,count]`. Nodes must refer to distinct unconsumed previous
clusters, heights must be finite/nonnegative, and counts must equal merged leaf
counts. No opaque SciPy object or callable is serialized. Explicit linkages stay
explicit on data refresh; the caller is responsible for their meaning.

One leaf permutation controls each axis's matrix values, mask, tick labels and
colour strip. Dendrogram leaf positions match heatmap cell centres. One optional
categorical colour strip per axis uses row_colors/col_colors; these are colour
codes, not automatically inferred legend categories. tree_color/tree_width and
dendrogram_ratio (relative to body) control tree display.

## Display transformation and masks

Choose one of:

- `z_score='row'|'col'`: subtract mean and divide by sample SD (ddof=1).
- `standard_scale='row'|'col'`: min-max to [0,1].
- Neither: display original values.

Constant axes cannot be standardized. Fit-time scaling prevents unnecessary
large-unit overflow; it does not replace invalid data. A finite nonempty
rectangular numeric matrix is required, including masked cells; no NaN/null/
boolean coercion or missing-value interpolation is performed. Dimensions are
capped at 512 rows/columns for bounded pairwise-distance work.

Mask is display-only: it does not exclude values from clustering/standardization.
After reordering, masked cells remain hidden and do not affect colour bounds or
annotations, following HeatmapSpec. Text shows the transformed display value,
not a falsely relabelled original unit. Use a truthful clabel/format. Log colour
normalization cannot combine with z-score/min-max transformations.

## Geometry and editing

Each clustermap needs its own unfiltered primary Cartesian panel, without extra
layers, secondary axes, shared axes or cropped coordinate limits. Multiple
independent panels remain possible. Cell labels default to original numeric
indices if not supplied. The title sits above the topmost auxiliary axes.

Nested GridSpec and aligned auxiliary axes keep trees/colour strips/colorbar
inside the configured figure. Layout is frozen after fitting for deterministic
vector clip IDs; change size/DPI/config through the spec and rerender rather than
expecting direct Figure resizing to rebuild the clustered layout.

The same AddLayer config works in existing editors. A missing optional effect,
invalid linkage, metric failure or bad prospective spec preserves previous editor
state/output. Mask and labels must be updated when matrix shape changes.

```bash
uv run python -m examples.clustered_profiles
uv run pytest -q tests/test_clustermap.py tests/test_heatmap_options.py
```

Tests compare SciPy order/optimal leaves, displayed transforms, geometry and
metadata, reject malformed inputs, check data refresh, missing effects, schema/
actions/editor paths and exact PNG/PDF/SVG replay without global RNG consumption.
Multiple colour tracks/automatic strip legends, missing data, arbitrary metrics,
interactive cut selection and broader clustering layouts remain outside this scope.
