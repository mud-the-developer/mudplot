"""Native Matplotlib expansion of the validated, finite layout graph."""

from __future__ import annotations

import math
import warnings
from typing import cast


def native_axes(figure):
    """Traverse actual axes, including insets, once; auxiliary axes stay auxiliary."""
    from matplotlib.axes import Axes

    seen = set()
    pending = [
        child for child in reversed(figure.get_children()) if isinstance(child, Axes)
    ]
    while pending:
        axes = pending.pop()
        if id(axes) in seen:
            continue
        seen.add(id(axes))
        yield axes
        pending.extend(reversed(cast("list[Axes]", axes.child_axes)))


def panel_legend(primary):
    """Resolve the one native legend from its logical panel."""
    legend = primary.get_legend()
    if legend is not None:
        return legend
    twin = getattr(primary, "_mudplot_secondary_axis", None)
    return None if twin is None else twin.get_legend()


def panel_axes(figure):
    """Return real tagged panels in spec-index order, never native draw order."""
    return sorted(
        (ax for ax in native_axes(figure) if hasattr(ax, "_mudplot_panel")),
        key=lambda ax: ax.__dict__["_mudplot_panel"],
    )


def _nested_column_spacing(figure, renderer, pad):
    """Measure whole axis-decoration bands, never all tick-label pairs."""
    grids = getattr(figure, "_mudplot_native_layout_grids", ())
    groups = {}
    for axes in native_axes(figure):
        owner = getattr(axes, "_mudplot_semantic_guide_axis", axes)
        bar = getattr(axes, "_colorbar", None)
        if bar is not None:
            owner = getattr(bar.mappable, "axes", None)
            owner = getattr(owner, "_mudplot_semantic_guide_axis", owner)
        cell = getattr(owner, "_mudplot_layout_cell", None)
        if cell is None or cell.get_topmost_subplotspec() == cell:
            continue
        grid = cell.get_gridspec()
        if grid not in grids:
            continue
        key = (
            cell.rowspan.start,
            cell.rowspan.stop,
            cell.colspan.start,
            cell.colspan.stop,
        )
        records = groups.setdefault(grid, {})
        frame = cell.get_position(figure).transformed(figure.transFigure)
        record = records.setdefault(
            key, {"frame": frame, "left": frame.x0, "right": frame.x1}
        )
        for axis in (axes.xaxis, axes.yaxis):
            bounds = axis.get_tightbbox(renderer)
            if bounds is not None:
                record["left"] = min(record["left"], bounds.x0)
                record["right"] = max(record["right"], bounds.x1)
    required, unresolved = figure.subplotpars.wspace, False
    for grid, records in groups.items():
        _rows, columns = grid.get_geometry()
        params = grid.get_subplot_params(figure)
        width = (params.right - params.left) * figure.bbox.width
        for left_key, left in records.items():
            for right_key, right in records.items():
                if left_key[3] != right_key[2] or (
                    min(left_key[1], right_key[1]) <= max(left_key[0], right_key[0])
                ):
                    continue
                needed = (
                    max(0.0, left["right"] - left["frame"].x1)
                    + max(0.0, right["frame"].x0 - right["left"])
                    + pad
                )
                if right["frame"].x0 - left["frame"].x1 >= needed:
                    continue
                remaining = width - (columns - 1) * needed
                if remaining <= 0:
                    unresolved = True
                    continue
                # Native GridSpec gap = W*wspace/(ncols+(ncols-1)*wspace).
                required = max(
                    required, math.nextafter(columns * needed / remaining, math.inf)
                )
    return required, unresolved


def nested_tight_layout_engine():
    """Keep native Tight layout, correcting only measured nested-column gaps."""
    from matplotlib.layout_engine import TightLayoutEngine

    class NestedTightLayoutEngine(TightLayoutEngine):
        def execute(self, figure):
            super().execute(figure)
            renderer = figure._get_renderer()
            for _ in range(3):
                needed, _blocked = _nested_column_spacing(
                    figure, renderer, 0.02 * figure.dpi
                )
                if needed <= figure.subplotpars.wspace:
                    break
                figure.subplots_adjust(wspace=needed)
            needed, blocked = _nested_column_spacing(
                figure, renderer, 0.02 * figure.dpi
            )
            unresolved = blocked or needed > figure.subplotpars.wspace
            if unresolved:
                warnings.warn(
                    "nested axis decorations cannot fit the fixed native grid; "
                    "source positions, ticks and canvas are unchanged",
                    UserWarning,
                    stacklevel=2,
                )

    return NestedTightLayoutEngine()


def normalized_ratios(ratios):
    if ratios is None:
        return None
    scale = max(ratios)
    relative = [value / scale for value in ratios]
    total = math.fsum(relative)
    result = [value / total for value in relative]
    if any(value <= 0 or not math.isfinite(value) for value in result):
        raise ValueError("layout ratios produce unrepresentable positive extents")
    return result


def _slice(cell):
    return (
        slice(cell.row, cell.row + cell.row_span),
        slice(cell.col, cell.col + cell.col_span),
    )


def tag_axes(axes, index, panel):
    axes._mudplot_panel = index
    if panel.panel_id is not None:
        axes._mudplot_panel_id = panel.panel_id
        axes.set_gid("mudplot-panel-" + panel.panel_id)
    if panel.projection == "polar":
        axes.set_rlabel_position(90)


def build_axes(figure, spec):
    grids = {}
    pending = list(spec.panel_layout.grids)
    while pending:
        remaining = []
        for node in pending:
            if node.cell is not None and node.cell.grid not in grids:
                remaining.append(node)
                continue
            options = {}
            for key in ("width_ratios", "height_ratios"):
                value = normalized_ratios(getattr(node, key))
                if value is not None:
                    options[key] = value
            if node.cell is None:
                grids[node.grid_id] = figure.add_gridspec(
                    node.rows, node.cols, **options
                )
            else:
                slot = grids[node.cell.grid][_slice(node.cell)]
                grids[node.grid_id] = slot.subgridspec(node.rows, node.cols, **options)
        pending = remaining
    figure._mudplot_native_layout_grids = frozenset(grids.values())
    axes_by_id = {}
    pending_panels = list(enumerate(spec.panels))
    while pending_panels:
        remaining = []
        for index, panel in pending_panels:
            place = panel.placement
            projection = None if panel.projection == "2d" else panel.projection
            if place.cell is not None:
                axes = figure.add_subplot(
                    grids[place.cell.grid][_slice(place.cell)], projection=projection
                )
            else:
                if place.inset.parent not in axes_by_id:
                    remaining.append((index, panel))
                    continue
                parent = axes_by_id[place.inset.parent]
                axes = parent.inset_axes(
                    tuple(place.inset.bounds), projection=projection
                )
            tag_axes(axes, index, panel)
            if place.cell is not None:
                axes._mudplot_layout_cell = axes.get_subplotspec()
            axes_by_id[panel.panel_id] = axes
        pending_panels = remaining
    result = [axes_by_id[panel.panel_id] for panel in spec.panels]
    check_extents(result)
    return result


def check_extents(axes):
    for panel in axes:
        box = panel.get_window_extent()
        if (
            not all(math.isfinite(v) for v in (box.x0, box.y0, box.x1, box.y1))
            or box.x1 <= box.x0
            or box.y1 <= box.y0
        ):
            raise ValueError("layout produces unrepresentable positive panel bounds")


def link_axes(axes, spec):
    from ._layout import shared_groups, twin_value_groups

    mixed = {i for group in twin_value_groups(spec) for i, role in group if role == "y"}

    for name in ("x", "y"):
        for members in shared_groups(spec, name):
            if name == "y" and members[0] in mixed:
                continue
            base = axes[members[0]]
            for index in members[1:]:
                getattr(axes[index], "share" + name)(base)


def link_twin_values(axes, spec):
    from ._layout import twin_value_groups

    for members in twin_value_groups(spec):
        index, _ = members[0]
        twin = axes[index]._mudplot_secondary_axis
        peers = [axes[i] for i, _ in members[1:]]
        auto = spec.panels[index].y2.limits is None
        if auto:
            limits = [axis.get_ylim() for axis in (twin, *peers)]
            lo = min(min(pair) for pair in limits)
            hi = max(max(pair) for pair in limits)
        for peer in peers:
            peer.sharey(twin)
        if auto:
            twin.set_ylim((hi, lo) if twin.yaxis_inverted() else (lo, hi), auto=True)
