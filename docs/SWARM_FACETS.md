# Swarm observations, packing scopes and live facet transactions

*[한국어 / Korean](SWARM_FACETS.ko.md)* · [Numeric size](SWARM_SIZE.md) · [Shared domains](SWARM_SHARED_SIZE.md)

C02 adds real native named glyphs, independent shared hue/size/style, explicit
cross-layer packing and an opt-in live-template transaction. The older
materialized-grid/SetData subset is retained; it is **not** the new live unit.
Package 1.1.0, schema 0.1 and dependency floors are unchanged.

## Individual marks and shared roles

```python
mapping = {
    "scale_id": "observations", "hue": "temperature", "hue_kind": "numeric",
    "size": "precision", "sizes": [3, 7],
    "style": "method", "markers": ["s", "^"]
}
p = (mp.plot(data)
     .swarmplot("category", "measurement", semantics=mapping, pack_scope="members")
     .swarmplot("category", "replicate", semantics=mapping, pack_scope="members"))
```

Every retained observation remains a separate native glyph in source order;
there is no estimate, weighting, averaging of role tuples or row pooling.
Missing category/measurement/required roles drop listwise. Numeric/categorical
hue and size, categorical style and selected/reserved orders use the existing
raw-row mapping domains and logical-panel guides shared with scatter, lineplot,
strip, ECDF and rug. Mapping domains deduplicate original source row IDs.

Size is the native **nominal diameter parameter in points**, squared to native
area; actual glyph extents depend on its path. It is not mass or stroke width.
Line/ECDF/rug interpret the same mapped physical values as their stroke points.
Finite named filled markers are `o s D ^ v P X d p h 8 *`, with enough distinct
style choices and no cycling. Scalar `marker_size` conflicts with mapped size;
scalar marker conflicts with mapped style; scalar colour conflicts with mapped
hue. Legacy group/hue_order plus size-only or size/style roles remain supported;
mapped semantic hue conflicts with that legacy colour/group channel. `c`, weights,
inference, arbitrary paths/callbacks and unused options are not serialized controls.

Explicit clocks apply to the actual category/measurement axes for v/h and y/y2.
Default strings remain ordinal. Native numeric/log/date coordinates preserve raw
observations, declared units and UTC spacing; log data require positive values.
Temporal category slot bounds enter only category dataLim before autoscaling,
so a single date does not acquire an origin-sized artificial viewport. Unrelated
measurement limits remain intact. Raw single-date lines have no category slots
and are not reframed by this rule.

## Explicit cross-layer packing

`pack_scope=None` leaves layers independent even when their semantic scale ID is
shared. A nonempty, control-free name (up to 64 characters) explicitly joins
compatible members in one logical panel and actual target axes. Same-name members
cannot mix y/y2 targets, orientation, category columns/orders/native geometry,
width/dodge/gap; dodged hue columns/orders must also match. Incompatible declarations
reject rather than silently becoming separate packs. Different panels never pack
together. Category/hue slot unions resolve before drawing.

Each layer retains its existing **2,000 usable-row maximum**. A new explicit
operation bound allows **4,000 physical instances per panel/packing scope**, checked
in pure validation before native point construction. The same original row drawn
by two layers counts **twice** for packing, unlike deduplicated mapping domains.
The bound follows measured worst-cell work/allocation; it is not an SLA, sandbox
promise, per-layer limit lift or justification derived from Store history changes.

An axes-owned coordinator packs visible, actually attached members once per draw
pass. Layout, limits/inversion, DPI, backend and live-grid changes repack from
immutable original measurements without RNG or accumulated drift. Native size
and linewidth arrays retain cycling semantics. Removed/hidden/moved members do
not occupy their old axes; moved artists pack on their current axes.

Legacy circles keep the exact old radius/placement. Other glyphs draw their real
native paths, with conservative actual-path bbox circles plus round stroke bounds,
not Bézier-control-hull inflation of circles. Path extents are measured once per
unique actual path per call and refreshed on later draws. Greedy packing is not
optimal: crowded or oversized observations remain at gutters, with truthful
clearance warnings. `warn_thresh` is [0,1], default 0.05; warnings occur once per
collection and `crowded_count` describes its current draw. No observations are
silently downsampled or deleted.

## Materialized defaults versus explicit live edits

```python
p.facet(col="cohort", col_order=["left", "empty", "right"], col_wrap=2, live=True)
p.layout(2, 2, width_ratios=[2, 1])  # Three fixed cells; no phantom fourth panel.
template = p.spec.facet_template.template
for layer in template.layers:
    layer.semantics.markers = ["D", "v"]
p.facet_template(template)  # Explicit SetFacetTemplate transaction across ALL cells.
```

Ordinary `.facet()` / SetFacets retain their old materialized JSON and behavior.
`live=True` uses SetLiveFacets and appends an optional `FigureSpec.facet_template`
recipe: a typed PanelSpec template and **resolved** row/column orders/selectors,
without copying source data or creating a new layout/ID hierarchy.

The stored template is a recipe for an **explicit transaction**, not an automatic
reactive renderer. Loading a file keeps its saved materialized views and local
overrides. Existing per-cell actions remain local. A later SetFacetTemplate
intentionally replaces all intended cells and supersedes their local layer/axis
overrides; undo restores those overrides. Saving/reopening does not apply the
template, but a post-reopen explicit template edit still updates every cell.

Known category/hue orders remain attached to the same declared channel. Explicit
new orders, or `reset_orders=True` with automatic orders requested, may recapture
slots from current data. A newly requested hue/group channel resolves its own
levels rather than inheriting unrelated old labels. SetData may fill/empty fixed
reserved cells but never introduces new facet cells or changes their identities.
All generated views validate under those frozen selectors: a bad observation in
an excluded cohort, or 3,000 global rows split into 1,500 per drawn layer/cell,
does not create a phantom unfiltered template layer. Invalid selected data still
reject. Empty cells have no invented collections or guide observations.

Current figure ratios/sharing survive whole-template edits. Compatible ratio-only
changes keep wrapped partially filled grids and their recipe; explicit structural
layout/facet/joint/pair replacement or panel extension detaches it. Inconsistent
saved recipe/selectors/layout reject without silently dropping the binding. Existing
64-cell/total-layer/domain and per-cell swarm operation bounds remain in force.
Swarm-only filtered y2 panels are supported; wider G01 family combinations remain
required work. This reusable G01 increment does not close G01 or global E01/REL01.

[Executable full workflow](../examples/swarm_workflow.py) saves editable JSON and
PNG/SVG/PDF with shared-family and date/y2/live-grid examples. Successful Figures
are caller-owned and should be closed. Synthetic previews are not independent
human accessibility certification or total CPU/RAM guarantees.
