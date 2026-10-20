# Numeric event train

*[한국어 / Korean](EVENTPLOT.ko.md)*

![Synthetic events](images/plots/eventplot.png)

[Executable source](../examples/plots/eventplot.py) ·
[Editable spec](images/plots/eventplot.mplot.json)

```python
p = (mp.plot({"event": [2, 1, 2]})
       .eventplot("event", offset=0.5, length=0.4)
       .labels(x="Event position", y="Raw offset"))
```

This first subset draws one train of vertical marks. Event positions are x values;
mark endpoints are `offset - length/2` and `offset + length/2` in raw y units.
Unlike `rug`, the marks do not use an axis-fraction transform. No binning, density,
rate estimation or aggregation is implied. Repeated events remain separate marks.
Native Matplotlib sorts its EventCollection positions, so artist order is not the
input order; the original table/rows/duplicates/JSON/actions remain unchanged.

The existing LayerSpec.x column, baseline offset and width length fields are reused.
Default offset is zero and length one; raw JSON None selects those same defaults.
Require 1..10,000 finite numeric events (not bool/missing/dates/categories), a finite
numeric offset, positive finite length and finite distinct representable endpoints.
Overflow or collapsed endpoints fail before artists rather than clamping geometry.

Only linear Cartesian primary/y2 axes are supported. Source SetData updates events;
colour/dash/alpha/line-width apply to the train, including explicit zero line width.
Explicit line width is finite in [0,1000]. At zero width, the invisible dash pattern
is removed to avoid Matplotlib 3.8's degenerate legend dashes; source style and zero
stroke remain unchanged. Positive-width dashes are preserved.
Returned successful Figures are caller-owned
and must be closed. This is not a total CPU/RAM/sandbox guarantee.

Horizontal/group/hue/semantic/weight/facet/dropna/log/polar/3-D mappings are explicitly
unsupported. The synthetic example is not experimental data or independent human
readability/AT certification. Existing raw action routes require no new fields:

```json
{"type":"AddLayer","layer":{"type":"eventplot","x":"event","baseline":0.5,"width":0.4}}
```
