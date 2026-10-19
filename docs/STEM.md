# Vertical numeric stem plots

*[한국어 / Korean](STEM.ko.md)*

![Synthetic discrete observations](images/plots/stem.png)

[Executable example](../examples/plots/stem.py) ·
[Editable spec](images/plots/stem.mplot.json) ·
[SVG](images/stem.svg) · [PDF](images/stem.pdf)

```python
p = (mp.plot({"x": [2, 1, 2], "y": [3, -1, 4]})
       .stem("x", "y", baseline=0, marker="o", marker_size=5, line_width=1.2)
       .labels(x="Position", y="Response"))
```

The first subset is vertical numeric stems on primary Cartesian or y2 axes.
Each supplied row becomes a marker and a segment from the raw scalar baseline
to its y value. Input order, repeated positions, negative linear values and the
original source table are preserved: no sorting, binning, aggregation or inferred
intervals. SetData changes the artists without storing stale derived segments.

`baseline` is an existing LayerSpec field, default zero (`None` in raw JSON also
means zero). Log x requires positive positions; log response axes require positive
heads **and baseline**, never a substituted epsilon. All x/y/baseline values must
be finite numeric, not bool; 1..10,000 rows are supported. Missing values reject
rather than disappearing. Explicit marker size zero is retained. Line width and
marker size must be finite in [0,1000] when set. Colour/alpha/dash apply consistently
to stems and baseline; marker shape/size style the heads. Returned Figures remain
caller-owned and must be closed after use.

Horizontal, group/hue/semantic/weight mappings, facet/dropna selectors, polar/3-D,
colorbars and unrelated layer options are explicitly unsupported. These resource
bounds are not a total CPU/RAM or sandbox guarantee. The synthetic example is not
experimental data or independent human readability/AT certification.

The existing AddLayer/JSON/editor raw-action route is unchanged:

```json
{"type":"AddLayer","layer":{"type":"stem","x":"x","y":"y","baseline":0}}
```
