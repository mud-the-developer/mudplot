# Joint plot with paired histogram marginals

*[한국어 / Korean](JOINT_GRID.ko.md)*

This joint-grid subset links one raw scatter/regression or ungrouped hist2d/hexbin
view to x/y histogram/KDE marginals. It does not implement every Seaborn joint kind.

![Synthetic paired dose and response observations](images/joint_observations.png)

[Editable spec](images/joint_observations.mplot.json) ·
[SVG](images/joint_observations.svg) · [PDF](images/joint_observations.pdf) ·
[Source](../examples/joint_observations.py)

All 80 observations are synthetic and independent. The example is checked at a
700px desktop display; this is not mobile or independent readability certification.

## Build a main view, then compose

```python
p = (mp.plot(raw)
       .scatter("dose", "response", group="condition", marker_size=3.5)
       .labels(x="Dose (mg)", y="Response (a.u.)", title="Paired observations")
       .joint(bins=10, ratio=3, marginal_stat="density")
       .size(7, 6.5))
```

- Panel 0: main graph at top-left, preserving its styles, title/references and
  optional hline/vline/text/annotation layers.
- Panel 1: horizontal y histogram on the right.
- Panel 2: vertical x histogram below the main graph.
- There is **no fourth axes** in the unused bottom-right corner.

The template must contain exactly one raw `scatter`, `regplot`, `hist2d` or `hexbin`, optionally
with reference/annotation layers, on primary Cartesian 2-D axes. Axes labels
fall back to column names when empty. The main x label moves to the lower
marginal; the repeated right-side y label is hidden. Marginal legends are hidden,
and raw group colours/slots match the main view.

`ratio` is the main-to-marginal width/height ratio, finite in [1,10]. `bins` is a
positive integer within the existing histogram cap; each variable derives its
own bins, common across its groups. `marginal_stat` is `count`, `density`,
`probability` or `percent`. With density, total area over all groups is one per
marginal; probability/percent total one/100 and count totals paired observations.

Total figure size is unchanged: set it explicitly. X is shared by column and y
by row. Consequently measurement values align, while density/count axes remain
independent of the main measurement axes. Display limits remain display limits,
not additional data filtering.

## Binned centers

```python
p = (mp.plot(raw).hist2d("dose", "response", bins=12, colorbar=False)
       .joint(bins=10, marginal_stat="count").size(7, 6.5))
# Or: hexbin("dose", "response", gridsize=20, colorbar=False)
```

Binned centers require ungrouped, unweighted raw numeric x/y and an explicitly
disabled colorbar. The center's bins/gridsize/density remain its own settings;
`joint(bins=...)` configures histogram marginals only. The paired selector is
applied before center and marginal validation/rendering, and SetData refreshes it.
Hist/KDE marginals both work. No general binned facet filters, hue_order/group or
implicit colorbar removal is introduced.

## KDE marginals

```python
p = (mp.plot(raw).scatter("dose", "response", group="condition")
       .joint(marginal_kind="kde", kde={"bw_method": "silverman",
              "bw_adjust": 0.8, "gridsize": 128, "cut": 0})
       .size(7, 6.5))
```

[Example](images/kde_joint.png) · [Editable spec](images/kde_joint.mplot.json) ·
[Source](../examples/kde_grids.py). KDE keeps the same paired cohort and value-axis
orientation. The strict KDESpec/dict controls bandwidth, grid, cut/clip, common
normalization/grid and fill; each marginal receives its own copy. The histogram
stat totals described above apply to histograms, not finite-support KDE curves.
Cut/clip bound evaluation without dropping fit rows, so displayed KDE area can
be less than one. Singular/singleton groups warn and skip without invented fits;
common normalization still includes their usable mass under existing KDE rules.

KDE supports density only: leave bins at its unused default 20 and do not request
count/probability/percent, weights or cumulative CDF. The same config is copied
across variables: shared clip bounds must make sense for both units. Histogram
remains the default and is unchanged.

## One cohort, original data intact

Every panel serializes the same complete-case selector:

```json
{"dropna": ["dose", "response", "condition"]}
```

Rows missing x/y or the mapped group are excluded from all three views. Missing
unrelated columns do not exclude observations. Explicit raw `hue_order` selection
also applies before coordinate validation and marginal calculation. Coordinates
must be finite numeric, not bool or category labels. No complete selected pair
fails without changing plot state/history.

The full original table stays in `FigureSpec.data`; no duplicated/stale derived
columns are stored. `SetData` refreshes complete cases dynamically. Group orders
are materialized snapshots like [facets](FACETS.md): rebuild a fresh template to
include newly introduced group levels. Later edits are panel-scoped. Histograms
are not estimates from extra unpaired x/y rows.

## JSON and editors

```json
{"type": "SetJointGrid", "bins": 10, "ratio": 3, "marginal_stat": "density"}
```

The action uses the same pure reducer/Store path as `.joint()`, with no optional
numeric/render dependency in construction, validation or serialization. Open the
example spec in either editor, or apply the action to a ready raw scatter/regplot
via its raw-action form. Old specs omit `dropna` and remain unselected by default;
spec version is still 0.1.

## Explicit limits

- No semantic roles, legacy c/colourbar, secondary axes, weighted marginals,
  grouped/weighted binned centers or nested facet/joint composition yet.
  [Numeric pair matrices](PAIR_GRID.md) use a separate constructor.
- Raw lines/bands are not converted into scatter or mean curves: dropping pairs
  could otherwise change path gaps. Only the stated main kinds are accepted.
- Existing histogram derived-bin/log guards still apply. For example, an
  automatic bin range for a tiny constant positive log variable can be rejected;
  no fabricated positive edges are substituted.
- Existing regression sample/distinct-x requirements remain active after pairing.

```bash
uv run python -m examples.joint_observations
uv run pytest -q tests/test_joint_grid.py tests/test_facets.py tests/test_raw_group_order.py
```

Tests check paired row IDs, dynamic refresh, source preservation, sharing,
normalization, empty/invalid requests, copied metadata, JSON/actions/schema/editor
paths and deterministic PNG/PDF/SVG without global RNG consumption. Automated
checks do not replace review at the intended final size.
