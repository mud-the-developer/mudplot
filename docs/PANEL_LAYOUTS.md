# Named panels, nested grids, mosaics and insets

*[한국어](PANEL_LAYOUTS.ko.md)*

N13 is an opt-in declarative layout extension in the unpublished 1.1.0 candidate,
schema 0.1. It uses native Matplotlib GridSpec/subgridspec and child inset axes.
The pure builder/action/JSON/validation core has no third-party dependencies;
rendering retains NumPy ≥1.23.5, Matplotlib ≥3.8 and Pillow ≥13.0.0.
This layout capability does **not** complete the remaining G02/G03 pair/joint
semantics, weighted/corner/complementary-CDF workflows or the full v2 catalogue.

## Create, edit and reopen

```python
import mudplot as mp

p = (mp.plot({"time": [1, 2, 4], "value": [3, 1, 5]})
     .line("time", "value")
     .mosaic([["main", "main", "empty"], ["main", "main", None]],
             width_ratios=[1, 1, 2])
     .nest(1, 2, width_ratios=[3, 1])
     .inset("main", [0.1, 0.2, 0.3, 0.4], panel_id="zoom")
     .line("time", "value", panel=2))

p.place("zoom", {"inset": {"parent": "main", "bounds": [0.2, 0.1, 0.4, 0.4]}})
p.rename_panel("main", "measurement")  # rewrites saved inset-parent references
p.reorder_panels(["zoom", "empty", "measurement"])
p.store.undo()
p.store.redo()
reopened = mp.Plot.from_json(p.to_json())
reopened.save("figure.svg")
```

A mosaic is a nonempty rectangular list of rows. A string is a stable panel ID;
`None` is an unoccupied position, not an empty panel. Repeated IDs must form a
rectangle and become a single spanning panel. An empty PanelSpec is instead a
real editable frame, so `empty` above remains selectable and exportable.
On first opt-in only previously anonymous legacy panels are assigned labels in
first-occurrence order. Once a panel has an ID, a new mosaic label never silently
renames or consumes it: every existing ID must appear, and new IDs create new
empty panels. Remove/rename are explicit actions.

`nest` wraps the existing grid without changing the stored panel list, selectors,
source rows, ratios or named share IDs. It accepts outer `rows`, `cols`, zero-based
`row`/`col`, positive `row_span`/`col_span`, optional ratios and `grid_id`. An omitted
grid ID is the next free deterministic `gridN`; repeated `nest` is safe. Explicit
ID collisions reject. Existing `pair(...).nest(...)` and `joint(...).nest(...)`
need no manual data/native preprocessing. Insets are real child axes, including
2-D, polar and 3-D parent/child combinations on the supported Matplotlib floor.
Their `[left, bottom, width, height]` bounds are parent-axes fractions and follow
the parent's native transform. Bounds must be finite, positive and contained;
siblings may touch but may not overlap. Nested insets are allowed.

## Canonical complete geometry

`FigureSpec.panel_layout` contains a flat `PanelLayoutSpec(grids=[...])`. Each
`LayoutGridSpec` has `grid_id`, positive `rows`/`cols`, optional positive finite
`width_ratios`/`height_ratios`, and either no `cell` (the unique root) or a
`GridCellSpec(grid, row, col, row_span=1, col_span=1)` in its parent grid.
Each panel has an optional appended `panel_id` and `placement`; explicit layouts
require both. A `PanelPlacementSpec` contains **exactly one** of:

- `cell`: GridCellSpec, with zero-based top-left indices and positive spans;
- `inset`: InsetSpec(parent=panel_id, bounds=[left, bottom, width, height]).

`Plot.panel_layout(layout, placements, panel_ids=None)` replaces the complete
geometry atomically through SetPanelLayout. Pass typed dataclasses or their JSON
objects. Keys and **all incoming references use final IDs**, never old IDs. The
optional `panel_ids` list explicitly assigns/renames the current panels in index
order; this supports an ID swap without guessing whether references meant old or
new IDs. RenamePanel instead rewrites existing saved references. Duplicate targets
and missing final references reject; no alias, random state or callback is stored.

Every existing final ID must be included. Additional explicit placement keys
allocate empty real panels, appended in **lexicographic ID order**, independent
of JSON object key order. The 256-panel limit is checked before allocation.
The optional panel_ids array still renames only the existing panels. New inset
panels may reference other new panels in the same complete transaction. Thus
after pair/joint nesting, adding a placement in an empty outer grid cell creates
a real sibling without a temporary inset or a mosaic reset; omitted positions
remain empty.

IDs match `[A-Za-z][A-Za-z0-9_.-]{0,63}`. Panel and grid IDs have separate typed
namespaces and are unrelated to source row IDs, axis share IDs or semantic scale
names. Missing IDs on opt-in are the smallest unused `panelN` in panel-list order.
IDs survive reorder, placement changes, undo/redo and reopen. Existing actions
still target panel **indices**; indices intentionally change after reorder.
RemovePanel rejects referenced inset parents and the final panel; no cascade or
silent reparent is performed.

Explicit geometry cannot also store legacy `layout`, `width_ratios` or
`height_ratios`. Mosaic/nest/complete-layout actions perform the cutover. Calling
ordinary `layout(rows, cols, ...)` clears explicit placements, preserves existing
IDs, and restores regular-grid semantics. Explicit-mode AddPanel or out-of-range
index expansion rejects instead of inventing a panel with no placement.

## Sharing and dimensional roles

One pure component resolver governs validation, native sharing and N12 effective
ticks/scale options. Named AxisSpec.share_id remains incompatible with any
non-`none` figure sharing mode on that axis. In an explicit hierarchy:

- `row`/`col` groups only panels in the **same immediate grid** with the exact same
  occupied row/column interval. Local row 0 in two nested grids is not a group;
  partially overlapping spans do not imply sharing. Insets are singleton here.
- `all` includes all primary Cartesian panels, including insets, intentionally.
- Cross-grid/inset groups use existing `share_axis("x" or "y", name)` with figure
  sharing `none`. Polar/3-D, independent y2 and derived axes keep their existing
  sharing restrictions.

The new role compatibility checks apply only after actual N13 opt-in: explicit
panel_layout or a stored panel_id. Ordinary old documents with neither retain
their shared raw/count behavior. Existing category, sharing-mode, clock, domain
and layer validity checks remain global; opt-in does not weaken any of them.

Nonempty observation-value/clock axes cannot accidentally share mass/count,
density, proportion, percent or frequency axes with incompatible dimensions.
Mean/median/point estimates in the same response units can share raw value axes;
estimator name alone is not an incompatibility. Empty selected views contribute
no fabricated role. Column strings/labels are **not** physical-unit inference.
Temporal declarations and N12 tick conflicts retain their existing validation.
Pair diagonal density axes and joint marginal/value links survive nesting.
Known N11 derived axes use finite typed Hz, elapsed-second, power/power-density,
coherence/proportion and radian signatures, not source-column names. Compatible
phase/angle radians can share. C03 advanced boxes use their actual required
summary/semantic row cohort; entirely missing summaries contribute no value role.

## Boundaries, editors and upgrades

The existing 256 actual panels, 1024 total layers and 40-million-render-pixel
limits remain. Explicit layout additionally allows at most 256 grid nodes, 1024
aggregate declared grid cells and depth 16 (root grid depth 1, counting panel and
inset ancestry). Old regular grids retain their 256-cell limit. These finite work
bounds are not a RAM sandbox or latency promise. No sampling/drop-to-fit occurs.
Cycles, missing/duplicate refs, multiple roots, bad spans/ratios, grid sibling
overlap and unrepresentable positive native bounds reject before a misleading
figure is committed. Stored ratios are never changed; private native-only stable
normalization avoids overflow, and zero/collapsed extents reject rather than clamp.

Explicit layouts uniformly select native TightLayoutEngine **before** creating
axes and colourbars, for every projection. This avoids the native constrained
solver's excessive constraint insertion on full approved hierarchies. No timing
threshold or runtime fallback is used. Native tight layout still may be unable to
fit dense decorations: its warnings and measured fixed-canvas text warnings are
retained, not a legibility guarantee. Outside-guide rectangles use tight layout's
left/bottom/right/top convention; the unchanged legacy constrained branch uses
left/bottom/width/height. Insets continue to follow native parent axes on redraw,
resize and DPI changes; source ratios, units and limits are never rewritten.
Measured diagnostics reuse the existing visible/nonempty/nontransparent text
eligibility, including exclusion of off-view ticks. Actual axis labels and
tick-versus-automatic-decoration collisions can warn without moving artists.
Ticks are grouped per native axis/side with a union-box broadphase, never an
all-tick-pairs comparison; caller-owned data text/positions are not inferred.

Both Python and Rust editors expose populated typed layout-action forms for
mosaic/nest, complete geometry, active placement, inset, rename, reorder and safe
removal. Native metadata traverses real child axes and uses panel tags, not
`figure.axes` order; twins/colourbars are not panels. Active selection follows a
stable ID across reorder. Data handles retain N12 per-target linear/log support
and visible unsupported-scale reasons; title/legend handles remain available.
PNG editor downloads are capped previews, while installed API/CLI PNG exports use
configured dimensions and SVG/PDF preserve physical size. Generation/revision URLs
keep the visible image and native handles from different snapshots from mixing.

**Old 0.1 documents need no migration:** all new optional fields are appended and
omitted when absent, and the regular-grid render branch is unchanged. Creating a
new structural facet/pair/joint grid replaces its cells/geometry explicitly.
Geometry-only nesting, mosaic, placement, inset, reorder and rename preserve live
ownership when every fixed typed selector retains one authoritative panel.
Whole-template replacement keeps those actual IDs/placements, including outer
siblings; local saved views stay authoritative until that explicit transaction.
Removing a live cell leaves saved materialized views. Explicit facet/pair/joint
replacement or changing/extending the implicit regular grid detaches the recipe.
Ratio-only same-shape edits retain exact partial cell counts. Loading never
silently rebuilds cells. Figure shared guides use scale_id alone, so ID changes
do not require a duplicate guide membership rewrite.

Run the [executable publication example](../examples/panel_layouts.py):

```sh
python examples/panel_layouts.py /tmp/layout-example
python -m mudplot validate /tmp/layout-example/panel_layouts.mplot.json
python -m mudplot render /tmp/layout-example/panel_layouts.mplot.json /tmp/layout.pdf
```

Linux qualification and readable raster/vector/TeX evidence are recorded separately
from native functional stress. Windows/macOS, physical print and original
experiments are not claimed by this row.
