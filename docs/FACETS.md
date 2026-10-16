# Automatic facets: first supported subset

*[한국어 / Korean](FACETS.ko.md)*

A facet repeats **one question** across subsets of the same source table. It is
not a collection of unrelated charts and not full Seaborn figure-level parity.

![Synthetic response curves by site](images/faceted_responses.png)

[Editable spec](images/faceted_responses.mplot.json) ·
[SVG](images/faceted_responses.svg) · [PDF](images/faceted_responses.pdf) ·
[Runnable source](../examples/faceted_responses.py)

The example is designed for a 900px desktop display, not an arbitrary mobile
thumbnail. All data are synthetic: each site contains six independent observations
per method/timepoint. Bands are pointwise 95% percentile-bootstrap CIs for means,
not SD, simultaneous bands or a pooled cross-site estimate.

## Build the template first

```python
p = (mp.plot(raw)
       .lineplot("time", "response", group="method", errorbar=("ci", 95),
                 n_boot=399, seed=17)
       .labels(x="Time (h)", y="Mean response (a.u.)")
       .legend(False)
       .suptitle("Response by site")
       .facet(col="site", col_order=["North", "South"])
       .size(9, 3.6))
p.legend(location="upper left", panel=0)
```

`facet()` consumes one completed, unfiltered source panel. It copies its layers,
axis settings, titles, references and explicit panel label into independently
editable cells. Cell titles add facet keys. Figure size is **not** multiplied:
set an appropriate total size explicitly. Use a suptitle for the overall question
rather than a long template title repeated in every cell. Legends are copied;
hide repeats explicitly, as above.

```python
p.facet(row="batch", col="site", row_order=["B", "A"],
        col_order=["North", "South"], share_x="all", share_y="row")
# Or, on a fresh single-panel template:
p.facet(col="site", col_wrap=2)
```

These are alternatives, not two facet calls on the same plot. Row/column grids
are row-major; wrapping is col-only and adds no empty padding panel. Defaults
share x/y across the grid; `none`, `all`, `row` and `col` follow existing axis
sharing. Explicit orders select/reserve levels, including empty cells. At most
64 cells/levels are supported. Keys are nonempty JSON strings, bools or finite
numbers; bool and numeric identities differ. Ambiguous display labels fail.
Missing facet keys drop rows.

## Data and statistics

The original `FigureSpec.data` is unchanged. Cells serialize exact selections:

```json
{"filters": {"batch": "A", "site": "North"}}
```

Selection precedes coordinate validation and all cell-level statistics, including
paired weights, per-x unit resampling, counts, normalization and KDE fits. Sharing
an axis or semantic mapping does **not** pool estimates across cells.

Typed category/hue slots reserve levels pooled across selected cells. Independent
scatter/lineplot semantics receive named shared scale domains; domains pool unique
**original** source row IDs, not cell-local indices. Repeated layers do not double
count rows, and deselected facets do not enter mapping bounds. Legends may show
pooled mapping guides; these are not additional observations.

This is a **materialized grid**. Later `.labels()`, layer or axis operations use
explicit panel indices, just like manual layouts. `SetData` refreshes observations
inside the stored selectors/orders; it does not add new facet/hue/category levels.
Rebuild a fresh template to change grid membership. `.facet(...).scatter(...)` is
not a mapping API; add the layers before faceting.

## Raw groups keep raw meaning

`line`, `scatter`, `bar`, `errorbar`, `band`, `stripplot`, `regplot` and `rug`
now support group-based facets. Faceting reserves pooled hue slots automatically.
An explicit `hue_order=[...]` also selects/reorders/reserves raw groups before
coordinate mapping, error validation and fitting. Missing group keys drop; values
must be unambiguous nonempty JSON strings, bools or finite numbers (up to 64 levels).

Raw line input order, duplicate/nonmonotonic x and coordinate gaps remain intact.
Supplied bars and paired uncertainty columns are not re-estimated. Empty reserved
groups consume colour, line/marker/hatch and bar-dodge slots but add no fictional
artists or legend entries. Regression still needs enough finite/distinct x values
in every observed group; reserved empty groups are not fitted. Raw defaults with
`hue_order=None` retain the previous observed-only behavior.

```python
raw = {"x": [2, 1, 1, 1, 2], "y": [8, 4, 5, 2, 3],
       "method": ["B", "B", "B", "A", "A"],
       "site": ["North"] * 3 + ["South"] * 2}
p = (mp.plot(raw).line("x", "y", group="method", hue_order=["B", "A"])
       .facet(col="site").size(8, 3))
# North still draws x=[2,1,1], y=[8,4,5]; it is not averaged to two points.
```

## Limits are rejected, not silently converted

- Primary Cartesian 2-D row-based layers only. No matrices, 3-D, polar, secondary
  axes, pie/stackplot/vector/count-map faceting in this subset.
- Raw groups are **not** silently converted into estimated lineplots or
  barplots: duplicate-x trajectories and precomputed bar values retain their
  different meanings. Stackplot/vector/count-map faceting is still unsupported.
- Legacy `c`/colourbars are unsupported; use explicit numeric SemanticSpec hue
  for a shared mapping.
- Histograms require `HistogramSpec` (for example `stat="density"`) and common
  explicit bin edges. Legacy histogram behavior is not changed. KDE needs typed
  KDESpec options; each cell fits its own bandwidth/density and may skip singular
  cells under the existing rules.
- Source layers must be valid before faceting. No arbitrary query strings,
  callables, predicate evaluation or live template mapping.
  [Numeric pair matrices](PAIR_GRID.md) are a separate data-construction workflow.
  [Joint histogram composition](JOINT_GRID.md) is a separate terminal workflow;
  nested facet/joint grids remain unsupported.

## JSON, actions and editors

```json
{"type": "SetFacets", "col": "site", "share_x": "all", "share_y": "all"}
```

The action follows the existing reducer/Store path, is dependency-free, and can
be replayed from Python, CLI or the editor's raw-action form. It requires an
existing single-panel template and the named source columns. Alternatively open
the editable example above in either editor; cell selection and existing panel
controls still work. No spec version bump or new layer type is involved.

```bash
uv run python -m examples.faceted_responses
uv run pytest -q tests/test_facets.py tests/test_raw_group_order.py tests/test_shared_semantics.py
```

Tests cover selected-row identities, independent cells, cell-local weighted CIs,
shared mappings, empty slots, invalid actions preserving state/history, old specs,
JSON/actions/schema/editor paths, repeatable PNG/PDF/SVG and no global RNG use.
This does not certify arbitrary facet layouts as readable: review final size,
labels, guides and empty/singular cases using the [reading criteria](VISUAL_QUALITY.md).
