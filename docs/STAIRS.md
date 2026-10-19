# Supplied-height stairs

*[한국어 / Korean](STAIRS.ko.md)*

![Synthetic supplied heights](images/plots/stairs.png)

[Executable source](../examples/plots/stairs.py) ·
[Editable spec](images/plots/stairs.mplot.json)

```python
p = (mp.plot({"height": [2, -1, 3]})
       .stairs("height", [0, 1, 3, 4], baseline=0)
       .labels(x="Bin edges", y="Supplied height"))
```

These are **already computed heights**, not observations to histogram again.
No sorting, normalization, rebinning or interpolation is performed. N supplied
heights require exactly N+1 finite strictly increasing edges, with finite positive
representable widths. The source table remains row-aligned at N rows; edges live
in the existing LayerSpec.bins list, and LayerSpec.x names the height column.
Their units need explicit axis labels because edges are configuration, not a named
data column. Original data, edges, JSON/actions and SetData are preserved. Changing
the number of heights requires explicit matching new edges; no silent regeneration.

The first subset is vertical unfilled outlines on linear Cartesian primary/y2 axes.
There must be 1..10,000 finite numeric heights (not bool/missing/categories).
Baseline is an existing finite raw scalar field, default zero; raw JSON None also
selects zero, not an open path. Negative heights/baselines are valid. Colour, dash,
alpha and finite line width in [0,1000] style the outline; explicit zero is retained.
Returned successful Figures remain caller-owned and must be closed.

No horizontal/fill/open-baseline/log/polar/3-D/group/semantic/weight/facet/dropna
mapping is exposed. Unsupported nondefault fields reject rather than disappearing.
These bounds are not a total CPU/RAM/sandbox guarantee, and the synthetic gallery
is not independent human readability/AT certification.

The existing raw action route needs no new fields:

```json
{"type":"AddLayer","layer":{"type":"stairs","x":"height","bins":[0,1,3,4],"baseline":0}}
```
