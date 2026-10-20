# Numeric size-only swarm

*[한국어 / Korean](SWARM_SIZE.ko.md)*

![Synthetic size mapping](images/swarm_size_semantics.png)

[Executable example](../examples/swarm_size_semantics.py) ·
[Editable source spec](images/swarm_size_semantics.mplot.json)

```python
p = mp.plot(data).swarmplot(
    "category", "response", group="group", dodge=0,
    semantics={"size": "mass", "size_norm": [0, 10], "sizes": [3, 9]},
)
```

The existing SemanticSpec supplies one numeric size column. Sizes are marker
**diameters in points**, mapped linearly before squaring into Matplotlib pt² areas.
For masses 0/5/10 with the bounds above, actual areas are 9/36/81. These are
mappings of individual observations, not group counts, density or weights.

Listwise-missing category/value/group/size rows are dropped together. Explicit
category/hue orders select the same source row IDs for packing, area mapping,
legend observations and the 2,000-usable-row limit. Missing size is not imputed;
source rows/data/actions/JSON are not rewritten. Selected bool/Inf/string sizes
reject. An unselected invalid size does not affect a plot, but strict JSON still
rejects nonfinite numbers anywhere in the source table.

By default, one layer's selected cohort defines its numeric domain.
[Swarm-only named scales](SWARM_SHARED_SIZE.md) can opt into pooled size domains.
Explicit
size_norm clips the mapping, never filters observations. Stable normalization
handles narrow high-magnitude and wide finite ranges; a constant domain maps to
the midpoint diameter and one guide. Guide circles use that same scale and have
no data coordinates. Semantic legend=False omits size guides, not size mapping;
legacy group colour guides remain controlled by the panel legend. Size guides do
not acquire group references/URLs. A group legend uses the midpoint diameter.

Circle packing uses actual per-point radii, strokes and gutters at final
DPI/layout/scales, including existing orientation/dodge/native-category modes.
Positive diameters whose areas underflow reject before artists. No arbitrary
shape, semantic hue/style, facet/dropna or cross-family shared scale,
date role or y2 support is implied. [Categorical size/order](SWARM_CATEGORICAL_SIZE.md)
is a separate opt-in subset. Scalar marker_size plus mapped size rejects.
The legacy semantics=None path remains unchanged. No new model/action/spec fields
or dependencies are required; raw semantic JSON is preserved by both editors.
Dedicated size controls are not claimed. Successful Figures remain caller-owned.

Synthetic data is not an independent human readability/AT certification or a
total CPU/RAM/sandbox guarantee. Broader style/date/facet semantics remain open.
