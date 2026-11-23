"""Native scalar-field effects; statistic bars and raw row hue guides differ.

Every colourbar owns its actual field ScalarMappable. Raw-role context guides
copy real collection strokes/fill; these fields never invent point glyphs.
"""

from __future__ import annotations

import math
import sys
from contextlib import ExitStack, nullcontext
from dataclasses import replace
from typing import TYPE_CHECKING, Protocol, cast

from ._axis_render import capture_raw_limits, restore_raw_limits
from ._components import finalize_component_stroke
from ._density import bounded_density_request, observation_axes
from ._density_input import prepare_input
from ._field_budget import FieldBudget, owned_size
from ._transforms import unit as coordinate_unit


def figure_field_budget(figure, layer, panel):
    if not bounded_density_request(layer, panel) and not (
        layer.type == "hexbin" and panel.grid_cohort is True
    ):
        return None
    budget = getattr(figure, "_mudplot_field_budget", None)
    if budget is None:
        budget = FieldBudget()
        figure._mudplot_field_budget = budget
        figure._mudplot_field_leases = []

        def record_rgba(event):
            buffer = getattr(event.renderer, "buffer_rgba", None)
            if buffer is not None:
                budget.rgba_bytes = memoryview(buffer()).nbytes

        figure.canvas.mpl_connect("draw_event", record_rgba)
    return budget


def retain_leases(figure, leases):
    if not leases:
        return
    figure._mudplot_field_leases.extend(leases)
    leases.clear()


def field_stroke_width(layer):
    """One resolved native width for field marks and their role guides."""
    if layer.line_width is not None:
        return layer.line_width
    from matplotlib import pyplot as plt

    from ._density import kde_config

    body = layer.type in {"hist2d", "ecdf2d"} or (
        layer.type == "kde2d" and kde_config(layer).fill
    )
    return float(plt.rcParams["patch.linewidth" if body else "lines.linewidth"])


def collection_stroke(artist):
    widths = artist.get_linewidths()
    width = float(widths[0]) if len(widths) else 0.0
    styles = artist.get_linestyles()
    offset, lengths = styles[0] if len(styles) else (0.0, None)
    # Native Collection getters return width-SCALED dashes. Patch/Line2D
    # setters expect the unscaled pattern; do not multiply it twice in guides.
    dash = (
        "solid"
        if not width or lengths is None
        else (float(offset) / width, tuple(float(value) / width for value in lengths))
    )
    return width, dash


def field_guide(ax, context, label, *, color=None, width=None, dash=None, header=False):
    """One actual field context, never a fabricated scatter/observation proxy."""
    from matplotlib.legend_handler import HandlerPatch
    from matplotlib.lines import Line2D
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path
    from matplotlib.transforms import IdentityTransform

    artist = context["artist"]
    actual_width, actual_dash = collection_stroke(artist)
    width = actual_width if width is None else width
    dash = actual_dash if dash is None else dash
    color = context["color"] if color is None else color
    edges = artist.get_edgecolors()
    edge = context.get("edge", edges[0] if len(edges) else "none")
    if context.get("filled", True):
        handle = PathPatch(
            Path([(0, 0)], [Path.MOVETO]),
            transform=IdentityTransform(),
            facecolor="none" if header else color,
            edgecolor="none" if header else edge,
            linewidth=0 if header else width,
            linestyle="solid" if header or width == 0 else dash,
            hatch=None if header else artist.get_hatch(),
            alpha=artist.get_alpha(),
            label=label,
        )
        ax.add_patch(handle)

        def update(native, original):
            native.update_from(original)
            native.set_linestyle(original.get_linestyle())

        handlers = getattr(ax, "_mudplot_legend_handlers", {})
        handlers[handle] = HandlerPatch(update_func=update)
        ax._mudplot_legend_handlers = handlers
    else:
        handle = Line2D(
            [],
            [],
            color=color,
            linewidth=0 if header else width,
            linestyle="None" if header or width == 0 else dash,
            marker="None",
            alpha=artist.get_alpha(),
            label=label,
        )
        ax.add_line(handle)
    return handle


def _tinted_cmap(color):
    from matplotlib.colors import LinearSegmentedColormap, to_rgba

    rgba = to_rgba(color)
    return LinearSegmentedColormap.from_list(
        "mudplot_field_tint", [(1, 1, 1, rgba[3]), rgba]
    )


def field_unit_label(layer, panel):
    axes = observation_axes(layer, panel)
    units = [
        coordinate_unit(
            layer,
            "xy"[index],
            "day"
            if axis is not None and axis.temporal is not None
            else f"input{index + 1}",
        )
        for index, axis in enumerate(axes)
    ]
    if layer.type == "hist2d":
        from ._density import histogram2d_config

        cfg = histogram2d_config(layer)
        if cfg.stat in ("count", "frequency"):
            name = "mass" if cfg.weights is not None else "count"
            return name if cfg.stat == "count" else f"{name}/({units[0]} * {units[1]})"
        if cfg.stat in ("probability", "proportion", "percent"):
            return "in-bin " + cfg.stat
        return f"in-bin density/({units[0]} * {units[1]})"
    if layer.type == "ecdf2d":
        cfg = layer.ecdf2d
        if cfg.stat == "count":
            name = "mass" if cfg.weights is not None else "count"
        else:
            name = "percent" if cfg.stat == "percent" else "proportion"
        return ("strict OR complement " if cfg.complementary else "joint CDF ") + name
    raise ValueError("field unit label requires a cell-field layer")


def _reference(layer, item):
    from ._render import _decorate

    raw = str(item.hue) if layer.group is not None else layer.label
    ref = (
        (layer.references or {}).get(str(item.hue)) if layer.group is not None else None
    )
    citation = ref.citation if ref is not None else layer.citation
    href = ref.href if ref is not None else layer.href
    return _decorate(raw, citation, href), citation, href


if TYPE_CHECKING:
    from matplotlib.markers import MarkerStyle


class _LineMarkerGeometry(Protocol):
    _marker: MarkerStyle


def _guide_vertices(artist):
    """Actual new guide geometry; font outlines belong to the font provider."""
    import numpy as np
    from matplotlib.collections import QuadMesh
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    total, pending, seen = 0, [artist], set()
    while pending:
        item = pending.pop()
        if id(item) in seen:
            continue
        seen.add(id(item))
        if isinstance(item, QuadMesh):
            coordinates = cast(np.ndarray, item.get_coordinates())
            total += 5 * (coordinates.shape[0] - 1) * (coordinates.shape[1] - 1)
        elif isinstance(item, Line2D):
            vertices = len(cast(np.ndarray, item.get_path().vertices))
            total += vertices
            if item.get_marker() not in (None, "None", "", " "):
                marker = cast(_LineMarkerGeometry, item)._marker
                total += vertices * len(cast(np.ndarray, marker.get_path().vertices))
        elif isinstance(item, Patch):
            total += len(cast(np.ndarray, item.get_path().vertices))
        pending.extend(item.get_children())
    return total


def _statistic_decoration_boxes(axes, renderer):
    """Actual visible components, never the empty corners of a union rectangle."""
    result = [axes.get_window_extent(renderer)]

    def text_box(text):
        if text.get_visible() and text.get_alpha() != 0 and text.get_text():
            # Match Text.draw's temporary native wrap, preserving authored text.
            with text._cm_set(text=text._get_wrapped_text()):
                box = text.get_tightbbox(renderer)
            if box is not None:
                result.append(box)

    for axis in (axes.xaxis, axes.yaxis):
        text_box(axis.label)
        text_box(axis.offsetText)
        for tick in axis._update_ticks():
            text_box(tick.label1)
            text_box(tick.label2)
            for line in (tick.tick1line, tick.tick2line):
                if line.get_visible() and line.get_alpha() != 0:
                    box = line.get_tightbbox(renderer)
                    if box is not None:
                        result.append(box)
    seen = set()
    for text in (axes.title, getattr(axes, "_mudplot_title_artist", None)):
        if text is not None and id(text) not in seen:
            seen.add(id(text))
            text_box(text)
    legend = axes.get_legend()
    if legend is not None and legend.get_visible():
        box = legend.get_tightbbox(renderer)
        if box is not None:
            result.append(box)
    return result


def _statistic_component_slots(axes):
    """Prospective final-draw component capacity from already materialized ticks."""
    return 10 + 4 * sum(
        len(axis.majorTicks) + len(axis.minorTicks) for axis in (axes.xaxis, axes.yaxis)
    )


def _wrap_statistic_unit(bar, parts, renderer, height):
    """Wrap generated prose only; authored prefix/math/unit expressions stay atomic."""
    if parts is None:
        return
    prefix, units = parts
    if any(character in units for character in "\\${}\n\t"):
        return
    tokens, current, depth = [], "", 0
    for character in units:
        if character == " " and depth == 0:
            if current:
                tokens.append(current)
                current = ""
        else:
            current += character
            depth += (character == "(") - (character == ")")
    if current:
        tokens.append(current)
    if depth or len(tokens) > 12:
        return
    text = bar.ax.yaxis.label
    original = text.get_text()
    best, best_height = original, text.get_window_extent(renderer).height
    if best_height <= height:
        return
    leading = f"{prefix}: " if prefix else ""
    for index in range(1, len(tokens) + 1):
        candidate = leading + " ".join(tokens[:index])
        if index < len(tokens):
            candidate += "\n" + " ".join(tokens[index:])
        text.set_text(candidate)
        measured = text.get_window_extent(renderer).height
        if measured < best_height:
            best, best_height = candidate, measured
        if measured <= height:
            break
    text.set_text(best)


def _stack_statistic_guides(owner, record, renderer):
    """One owner-native lane, with each actual mappable in its own native row."""
    bars = record["bars"]
    if len(bars) < 2:
        return
    figure = owner.figure
    slot = record["slot"]
    bounds = slot.get_position(figure) if slot is not None else record["bounds"]
    height = bounds.height * figure.bbox.height / len(bars)
    for bar, parts in zip(bars, record["units"], strict=True):
        _wrap_statistic_unit(
            bar,
            parts,
            renderer,
            height - bar.ax.yaxis.label.get_fontsize() * figure.dpi / 72,
        )
    from matplotlib.transforms import Bbox

    needed = 0.0
    for bar in bars:
        frames = [bar.ax.get_window_extent(renderer)]
        for axis in (bar.ax.xaxis, bar.ax.yaxis):
            box = axis.get_tightbbox(renderer, for_layout_only=False)
            if box is not None:
                frames.append(box)
        needed = max(needed, Bbox.union(frames).width)
    needed += 0.04 * figure.dpi
    width = bounds.width * figure.bbox.width
    if not 0 < needed < width:
        raise ValueError("statistic guide decorations cannot fit the authored canvas")
    if slot is not None:
        container = record.get("container")
        if container is None:
            container = slot.subgridspec(
                1, 2, width_ratios=[width - needed, needed], wspace=0.05
            )
            record["container"] = container
        lane = container[0, 1].subgridspec(len(bars), 1, hspace=0.2)
        for twin in owner._twinned_axes.get_siblings(owner):
            twin.set_subplotspec(container[0, 0])
        for index, bar in enumerate(bars):
            for parent in getattr(bar.ax, "_colorbar_info", {}).get("parents", ()):
                if bar.ax in parent._colorbars:
                    parent._colorbars.remove(bar.ax)
            bar.ax.set_subplotspec(lane[index, 0])
            # The lane already reserves the widest measured bar. Reserve
            # constrained-layout padding once, not for every stacked sibling.
            bar.ax.set_in_layout(index == 0)
            native_locator = getattr(bar.ax, "_mudplot_statistic_native_locator", None)
            if native_locator is None:
                native_locator = bar.ax.get_axes_locator()
                bar.ax._mudplot_statistic_native_locator = native_locator

            def locate_grid_bar(
                axes, actual_renderer, index=index, native=native_locator
            ):
                box = (
                    native(axes, actual_renderer)
                    if native is not None
                    else axes.get_position(original=True)
                )
                body = owner.get_position()
                count = len(record["bars"])
                height = body.height / (count + 0.2 * (count - 1))
                gap = 0.2 * height
                return Bbox.from_bounds(
                    record["bars"][0].ax.get_position(original=True).x0,
                    body.y0 + (count - index - 1) * (height + gap),
                    box.width,
                    height,
                )

            bar.ax.set_axes_locator(locate_grid_bar)
        return
    # Fixed/inset owners keep their original locator/region; split that SAME
    # region into a body and measured lane instead of stealing another column.
    from matplotlib.transforms import Bbox

    fraction = needed / width
    original_locator = record["locator"]

    def region(axes, actual_renderer):
        return (
            original_locator(owner, actual_renderer)
            if original_locator is not None
            else record["bounds"]
        )

    def body(axes, actual_renderer):
        box = region(axes, actual_renderer)
        return Bbox.from_bounds(box.x0, box.y0, box.width * (1 - fraction), box.height)

    for twin in owner._twinned_axes.get_siblings(owner):
        twin.set_axes_locator(body)
    for index, bar in enumerate(bars):

        def locate(axes, actual_renderer, index=index):
            box = region(axes, actual_renderer)
            gap = 0.04 * figure.dpi / figure.bbox.height
            row_height = (box.height - gap * (len(bars) - 1)) / len(bars)
            if row_height <= 0:
                raise ValueError("statistic guides have no positive native height")
            return Bbox.from_bounds(
                box.x0 + box.width * (1 - fraction),
                box.y0 + (len(bars) - index - 1) * (row_height + gap),
                box.width * fraction,
                row_height,
            )

        bar.ax.set_axes_locator(locate)


def _statistic_guide_check(figure, budget):
    """Every real backend checks visible guide/body/title/twin components."""
    from matplotlib.artist import Artist
    from matplotlib.transforms import Bbox

    def box_storage():
        probe = Bbox.from_bounds(0, 0, 0, 0)
        reference = sys.getsizeof((None,)) - sys.getsizeof(())
        return sys.getsizeof(probe) + owned_size(vars(probe)) + 2 * reference

    class StatisticGuideCheck(Artist):
        def get_tightbbox(self, renderer=None):
            """Give tight exports the native extents omitted from layout."""
            if not self.get_visible():
                return None
            if renderer is None:
                renderer = figure._get_renderer()
            boxes = []
            with ExitStack() as leases:
                for record in figure._mudplot_statistic_guides:
                    if record["slot"] is None:
                        continue
                    for index, bar in enumerate(record["bars"]):
                        if not index:
                            continue
                        axes = bar.ax
                        if not axes.get_visible() or axes.get_in_layout():
                            continue
                        if budget is not None:
                            slots = _statistic_component_slots(axes)
                            leases.enter_context(
                                budget.lease((3 * slots + 16) * box_storage())
                            )
                        components = _statistic_decoration_boxes(axes, renderer)
                        if budget is not None:
                            budget.charge(
                                "statistic_guide_native_measurements", len(components)
                            )
                        boxes.extend(components)
                return Bbox.union(boxes) if boxes else None

        def draw(self, renderer):
            if not self.get_visible():
                return
            records = figure._mudplot_statistic_guides
            guide_slots = sum(
                _statistic_component_slots(bar.ax)
                for record in records
                for bar in record["bars"]
            )
            body_slots = max(
                (
                    sum(
                        _statistic_component_slots(twin)
                        for twin in record["owner"]._twinned_axes.get_siblings(
                            record["owner"]
                        )
                    )
                    for record in records
                ),
                default=0,
            )
            box_bytes = box_storage()
            # Held components plus native text/transform construction temporaries.
            slots = 3 * (guide_slots + body_slots) + 16
            with (
                budget.lease(slots * box_bytes + 8 * sys.getsizeof([]))
                if budget is not None
                else nullcontext()
            ):
                previous = []
                for record in records:
                    owner = record["owner"]
                    bodies = [
                        box
                        for twin in owner._twinned_axes.get_siblings(owner)
                        for box in _statistic_decoration_boxes(twin, renderer)
                    ]
                    if budget is not None:
                        budget.charge(
                            "statistic_guide_native_measurements", len(bodies)
                        )
                    for bar in record["bars"]:
                        components = _statistic_decoration_boxes(bar.ax, renderer)
                        if budget is not None:
                            budget.charge(
                                "statistic_guide_native_measurements", len(components)
                            )
                        for box in components:
                            if budget is not None:
                                budget.charge(
                                    "statistic_guide_native_comparisons",
                                    len(previous) + len(bodies) + 4,
                                )
                            if not all(math.isfinite(v) for v in box.bounds):
                                raise ValueError(
                                    "statistic guide native bounds are unresolved"
                                )
                            if (
                                box.x0 < figure.bbox.x0 - 1
                                or box.y0 < figure.bbox.y0 - 1
                                or box.x1 > figure.bbox.x1 + 1
                                or box.y1 > figure.bbox.y1 + 1
                                or any(box.overlaps(other) for other in previous)
                            ):
                                raise ValueError(
                                    "statistic guide decorations cannot fit "
                                    "the authored canvas"
                                )
                            if any(box.overlaps(body) for body in bodies):
                                raise ValueError(
                                    "statistic guide overlaps native "
                                    "body/twin decorations"
                                )
                        previous.extend(components)

    check = StatisticGuideCheck()
    check.set_visible(False)
    check.set_in_layout(True)
    check.set_zorder(1e9)
    figure.add_artist(check)
    figure._mudplot_statistic_guide_check = check


def statistic_colourbar(
    ax, mappable, label, budget, *, href=None, generated_units=None, domain_only=False
):
    """Actual raw mappable, with a normalized non-data calibration axis."""
    owner = getattr(ax, "_mudplot_semantic_guide_axis", ax)
    import numpy as np

    from ._semantics import numeric_guides

    original_limits = mappable.get_clim()
    raw = np.asarray(mappable.get_array()).reshape(-1)
    if budget is not None:
        budget.charge("statistic_colourbar_scan", 2 * len(raw))
    if len(raw) and not np.all(np.isfinite(raw)):
        raise ValueError("a statistic colourbar requires finite field values")
    constant = not domain_only and len(raw) and np.min(raw) == np.max(raw)
    low, high = original_limits
    if low is None or high is None:
        raise ValueError("statistic mappable has no resolved raw domain")
    if constant:
        ticks, labels = [0.5], [str(float(raw[0]))]
        values, boundaries = np.asarray([raw[0]]), np.asarray([0.0, 1.0])
    else:
        count = int(mappable.cmap.N)
        guides = numeric_guides((low, high))
        ticks = mappable.norm(guides)
        labels = [str(value) for value in guides]
        if budget is not None:
            budget.charge("statistic_colourbar_interpolation", 3 * count)
        values = low + (high - low) * ((np.arange(count) + 0.5) / count)
        boundaries = np.linspace(0, 1, count + 1)
    leases = []
    if budget is not None:
        count = len(values)
        # The native short axis is unticked; <=3 fixed major calibration ticks
        # and their native minor subdivisions fit this prospective allowance.
        # Report their ACTUAL allocated paths below, not this upper bound.
        leases.append(budget.native_path_lease(5 * count + 128, count + 32, emit=False))
        leases.append(budget.array_lease((count + 1, 2, 2), copies=4))
        leases.append(budget.array_lease((count, 4), copies=2))
        # Reserve real existing frame headers/containers with tick-growth
        # headroom; data arrays/paths have their own prospective reservations.
        frame = {
            key: value
            for key, value in vars(owner).items()
            if key
            not in {
                "figure",
                "_parent_figure",
                "_children",
                "containers",
                "child_axes",
                "_colorbars",
                "_projection_init",
            }
        }
        leases.append(budget.lease(8 * owned_size(frame)))
    try:
        record = getattr(owner, "_mudplot_statistic_guide_record", None)
        if record is None:
            record = {
                "owner": owner,
                "slot": owner.get_subplotspec(),
                "bars": [],
                "units": [],
                "bounds": owner.get_position(original=True).frozen(),
                "locator": owner.get_axes_locator(),
            }
            owner._mudplot_statistic_guide_record = record
        if record["bars"]:
            from matplotlib.axes import Axes

            first = record["bars"][0]
            cax = Axes(ax.figure, first.ax.get_position(original=True).bounds)
            ax.figure.add_axes(cax)
            cax.set_box_aspect(first.ax.get_box_aspect())
            cax.set_anchor(first.ax.get_anchor())
            placement = {"cax": cax}
        else:
            placement = {"ax": owner}
        bar = ax.figure.colorbar(
            mappable,
            label=label or "",
            boundaries=boundaries,
            values=values,
            ticks=ticks,
            **placement,
        )
        bar.set_ticklabels(labels)
        if mappable.get_clim() != original_limits:
            raise ValueError("native colourbar changed the raw statistic domain")
        bar.ax._mudplot_statistic_calibration = {
            "raw_domain": [float(raw[0]), float(raw[0])] if constant else [low, high],
            "normalized_nondata_axis": True,
        }
        from ._render import _set_url

        _set_url(bar.ax.yaxis.label, href)
        record["bars"].append(bar)
        record["units"].append(generated_units)
        if not hasattr(ax.figure, "_mudplot_statistic_guides"):
            ax.figure._mudplot_statistic_guides = []
            _statistic_guide_check(ax.figure, budget)
        if record not in ax.figure._mudplot_statistic_guides:
            ax.figure._mudplot_statistic_guides.append(record)
        renderer = ax.figure._get_renderer()
        if (
            len(record["bars"]) == 1
            and record["slot"] is not None
            and generated_units is not None
        ):
            from matplotlib.layout_engine import ConstrainedLayoutEngine

            figure = ax.figure
            if type(figure.get_layout_engine()) is ConstrainedLayoutEngine:
                text = bar.ax.yaxis.label
                before = text.get_text()
                text_bytes = sys.getsizeof(before)
                if budget is not None:
                    budget.charge("statistic_guide_unit_characters", 1 + len(before))
                with (
                    budget.lease(4096 + 8 * text_bytes)
                    if budget is not None
                    else nullcontext()
                ):
                    if text.get_window_extent(renderer).height > figure.bbox.height:
                        if budget is not None:
                            # Up to twelve measured whitespace break candidates.
                            budget.charge(
                                "statistic_guide_unit_characters",
                                13 * (1 + len(before)),
                            )
                            leases.append(budget.lease(2 * text_bytes))
                        row = record["slot"].get_position(figure)
                        height = row.height * figure.bbox.height
                        _wrap_statistic_unit(
                            bar,
                            generated_units,
                            renderer,
                            height - text.get_fontsize() * figure.dpi / 72,
                        )
                        if budget is not None and text.get_text() == before:
                            leases.pop().close()
        if len(record["bars"]) > 1:
            if budget is not None:
                slot = record["slot"]
                grid = slot.get_gridspec() if slot is not None else None
                template = owner if grid is None else grid
                frame = owned_size(vars(template), seen={id(ax.figure), id(owner)})
                leases.append(
                    budget.lease(
                        (len(record["bars"]) + 4)
                        * (
                            frame
                            + sys.getsizeof((None,) * 16)
                            + sys.getsizeof({None: None}) * 4
                        )
                        + 3 * sys.getsizeof(label or "")
                    )
                )
            _stack_statistic_guides(owner, record, renderer)
        if budget is not None:
            budget.emit_vertices(_guide_vertices(bar.ax))
            retain_leases(ax.figure, leases)
        return bar
    except Exception:
        for lease in reversed(leases):
            lease.close()
        raise


def _frame_bounds(ax, x, y, orient):
    if not x or not y:
        return
    points = [[float(x[0]), float(y[0])], [float(x[-1]), float(y[-1])]]
    if orient == "h":
        points = [[b, a] for a, b in points]
    ax.update_datalim(points)
    ax.autoscale_view()


def draw_mesh_fields(
    ax,
    columns,
    layer,
    panel,
    color_iter,
    theme,
    *,
    curve_styles=None,
    input_plan=None,
    row_ids=None,
):
    """True H.T/edge collections and right-continuous paired ECDF cell fields."""
    import numpy as np
    from matplotlib.colors import Normalize

    from ._render import _continuous_cmap, _set_url

    budget = (
        figure_field_budget(ax.figure, layer, panel)
        if input_plan is None
        else input_plan.budget
    )
    cohort = (
        prepare_input(columns, layer, panel, budget)
        if input_plan is None
        else input_plan
    )
    plan = None
    styles = {} if curve_styles is None else curve_styles
    try:
        if layer.type == "hist2d":
            from ._histogram2d import prepare_histogram2d

            plan = prepare_histogram2d(columns, layer, panel, input_plan=cohort)
        elif layer.type == "ecdf2d":
            from ._ecdf2d import prepare_joint_ecdf

            plan = prepare_joint_ecdf(columns, layer, panel, input_plan=cohort)
        else:
            raise ValueError("native cell fields require hist2d or ecdf2d")
        base_cmap = _continuous_cmap(layer.cmap_kind)
        if curve_styles is None:
            for group in cohort.groups:
                color = layer.color or (
                    next(color_iter) if layer.group is not None else base_cmap(1.0)
                )
                styles[group["index"]] = {
                    "color": color,
                    "width": field_stroke_width(layer),
                    "dash": layer.line_style or "-",
                    "edge_color": layer.edge_color,
                }
        for item in plan.fields:
            style = styles[item.index]
            color, width, dash = style["color"], style["width"], style["dash"]
            encoded = layer.semantics is not None and (
                layer.semantics.size is not None or layer.semantics.style is not None
            )
            edge = style.get("edge_color") or (
                "#30343b"
                if encoded
                or layer.line_width is not None
                or layer.line_style is not None
                else "none"
            )
            tinted = (
                layer.group is not None
                or layer.color is not None
                or (layer.semantics is not None and layer.semantics.hue is not None)
            )
            cmap = _tinted_cmap(color) if tinted else base_cmap
            xe, ye = (
                (plan.x_edges, plan.y_edges)
                if layer.type == "hist2d"
                else (item.x_edges, item.y_edges)
            )
            values = item.values
            maximum = float(np.max(values))
            norm = Normalize(0, maximum if maximum > 0 else 1)
            x, y, display = (
                (xe, ye, values.T) if layer.orient == "v" else (ye, xe, values)
            )
            state = capture_raw_limits(ax)
            mesh = ax.pcolormesh(
                np.asarray(x, dtype=float),
                np.asarray(y, dtype=float),
                display,
                shading="flat",
                cmap=cmap,
                norm=norm,
                alpha=layer.alpha,
                edgecolors=edge,
                linewidths=width,
                linestyles="solid" if width == 0 else dash,
                label="_nolegend_",
            )
            serial = getattr(ax.figure, "_mudplot_field_serial", 0)
            mesh.set_gid(f"mudplot-field-{serial}")
            ax.figure._mudplot_field_serial = serial + 1
            finalize_component_stroke(mesh, body=True)
            restore_raw_limits(ax, state)
            ax.autoscale_view()
            label, _citation, href = _reference(layer, item)
            _set_url(mesh, href)
            if mesh.get_url() is not None:
                mesh.set_urls([mesh.get_url()])
            style.update(artist=mesh, filled=True)
            summary = {
                "kind": layer.type,
                "field_index": item.index,
                "source_row_indices": tuple(
                    row if row_ids is None else row_ids[row] for row in item.rows
                ),
                "logical_x_edges": xe,
                "logical_y_edges": ye,
                "stat": plan.stat,
                "mass_denominator": plan.mass_denominator,
            }
            if layer.type == "ecdf2d":
                summary.update(
                    prefix_units=item.prefix_units,
                    total_units=item.total_units,
                    complementary=plan.complementary,
                )
            else:
                summary.update(
                    in_bin_units=item.in_bin_units,
                    comparison_units=item.comparison_units,
                )
            mesh._mudplot_field = summary
            if budget is not None:
                # Prefix integer arrays/native payloads already have leases.
                small = {
                    key: value
                    for key, value in summary.items()
                    if key != "prefix_units"
                }
                retain_leases(ax.figure, [budget.account(small)])
                retain_leases(ax.figure, item.leases)
            if layer.colorbar:
                field_name = label
                if layer.semantics is not None:
                    field_name = (
                        ", ".join(
                            f"{name}={value}" for name, value in item.roles.items()
                        )
                        or layer.label
                    )
                units = layer.clabel or field_unit_label(layer, panel)
                text = f"{field_name}: {units}" if field_name else units
                statistic_colourbar(
                    ax,
                    mesh,
                    text,
                    budget,
                    href=href,
                    generated_units=(field_name, units) if not layer.clabel else None,
                )
            if curve_styles is None and (
                layer.group is not None or (layer.label and not layer.colorbar)
            ):
                handle = field_guide(ax, style, label)
                _set_url(handle, href)
        if not plan.fields:
            if layer.type == "ecdf2d":
                _frame_bounds(ax, plan.bounds[0], plan.bounds[1], layer.orient)
            else:
                _frame_bounds(ax, plan.x_edges, plan.y_edges, layer.orient)
        if layer.type == "hist2d":
            from ._density import histogram2d_config

            overlay_config = histogram2d_config(layer).kde
            if overlay_config is not None:
                from ._kde2d_render import draw_kernel_fields

                overlay = replace(
                    layer,
                    type="kde2d",
                    histogram2d=None,
                    kde2d=overlay_config,
                    label=f"{layer.label}: KDE overlay"
                    if layer.label
                    else "KDE overlay",
                    clabel=None,
                )
                overlay_styles = {
                    index: {
                        key: value
                        for key, value in style.items()
                        if key not in {"artist", "filled", "edge"}
                    }
                    for index, style in styles.items()
                }
                draw_kernel_fields(
                    ax,
                    columns,
                    overlay,
                    panel,
                    color_iter,
                    theme,
                    curve_styles=overlay_styles,
                    input_plan=cohort,
                    row_ids=row_ids,
                )
        return styles
    finally:
        if plan is not None:
            plan.close()
        if input_plan is None:
            cohort.close()


def draw_univariate_kernel(
    ax,
    columns,
    layer,
    panel,
    color_iter,
    theme,
    *,
    curve_styles=None,
    input_plan=None,
    row_ids=None,
):
    """Named 1-D laws and real shared-grid layer/stack/composition geometry."""
    import itertools
    import warnings

    import numpy as np

    from ._density import kde_config
    from ._kde import evaluate_univariate, prepare_kernel_profiles
    from ._kernel_math import IntervalMath
    from ._render import _set_url
    from .spec import KDESpec

    budget = (
        figure_field_budget(ax.figure, layer, panel)
        if input_plan is None
        else input_plan.budget
    )
    cohort = (
        prepare_input(columns, layer, panel, budget)
        if input_plan is None
        else input_plan
    )
    config = cast(KDESpec, kde_config(layer))
    arithmetic = IntervalMath(cohort.budget)
    plan = values = None
    styles = {} if curve_styles is None else curve_styles
    try:
        plan = prepare_kernel_profiles(
            columns, layer, panel, config, input_plan=cohort, arithmetic=arithmetic
        )
        if curve_styles is None:
            redundant = theme.redundant_encoding and len(plan.profiles) > 1
            dashes = (
                itertools.cycle(theme.line_styles)
                if redundant
                else itertools.repeat("-")
            )
            hatches = (
                itertools.cycle(theme.hatches) if redundant else itertools.repeat(None)
            )
            for profile in plan.profiles:
                styles[profile.index] = {
                    "color": layer.color or next(color_iter),
                    "width": field_stroke_width(layer),
                    "dash": layer.line_style or next(dashes),
                    "edge_color": layer.edge_color,
                    "hatch": next(hatches),
                }
        for profile in plan.profiles:
            if profile.singular and config.warn_singular:
                warnings.warn(
                    f"KDE skipped singular/insufficient field {profile.hue!r}; "
                    "no bandwidth or observations were invented",
                    UserWarning,
                    stacklevel=3,
                )
        values = evaluate_univariate(plan)
        observation = ax.xaxis if layer.orient == "v" else ax.yaxis
        if observation.get_scale() == "log" and any(
            value <= 0 for grid in values.grids for value in grid
        ):
            raise ValueError(
                "derived log KDE query support must be positive; use clip/cut"
            )
        for index, profile in enumerate(values.profiles):
            style = styles[profile.index]
            color, width, dash = style["color"], style["width"], style["dash"]
            grid = np.asarray(values.grids[index], dtype=float)
            bottom = cast(np.ndarray, values.lower)[index]
            top = cast(np.ndarray, values.upper)[index]
            leases = []
            if cohort.budget is not None:
                # Native original xy, recached xy, normalization/where temporaries.
                leases.append(cohort.budget.array_lease((len(grid), 2), copies=3))
            label, _citation, href = _reference(layer, profile)
            native_label = "_nolegend_" if curve_styles is not None else label
            state = capture_raw_limits(ax)
            if config.fill:
                finite = np.isfinite(bottom) & np.isfinite(top)
                sizes = []
                start = None
                for point, valid in enumerate(finite):
                    if valid and start is None:
                        start = point
                    if start is not None and (not valid or point == len(grid) - 1):
                        stop = point if not valid else point + 1
                        sizes.append(stop - start)
                        start = None
                if cohort.budget is not None:
                    leases.append(
                        cohort.budget.native_path_lease(
                            sum(2 * count + 3 for count in sizes), len(sizes)
                        )
                    )
                draw = ax.fill_between if layer.orient == "v" else ax.fill_betweenx
                artist = draw(
                    grid,
                    bottom,
                    top,
                    color=color,
                    edgecolor=style.get("edge_color") or color,
                    linewidth=width,
                    linestyle="solid" if width == 0 else dash,
                    alpha=layer.alpha,
                    hatch=style.get("hatch"),
                    label=native_label,
                )
                finalize_component_stroke(artist, body=True)
                restore_raw_limits(ax, state)
            else:
                if cohort.budget is not None:
                    leases.append(cohort.budget.native_path_lease(len(grid), 1))
                x, y = (grid, top) if layer.orient == "v" else (top, grid)
                (artist,) = ax.plot(
                    x,
                    y,
                    color=color,
                    linewidth=width,
                    linestyle="None" if width == 0 else dash,
                    marker="None",
                    alpha=layer.alpha,
                    label=native_label,
                )
                finalize_component_stroke(artist)
            _set_url(artist, href)
            if config.fill and artist.get_url() is not None:
                artist.set_urls([artist.get_url()])
            style.update(artist=artist, filled=config.fill)
            assert profile.model is not None
            artist._mudplot_kernel = {
                "source_row_indices": tuple(
                    row if row_ids is None else row_ids[row] for row in profile.rows
                ),
                "source_law_probability_error": profile.model.source_tv,
                "density_interval_width": values.interval_widths[index],
                "kernel": profile.model.kernel,
                "multiple": config.multiple or "layer",
                "cumulative": config.cumulative,
                "density_space": config.density_space or "data",
            }
            if cohort.budget is not None:
                leases.append(cohort.budget.account(artist._mudplot_kernel))
                retain_leases(ax.figure, leases)
        return styles
    finally:
        if values is not None:
            values.close()
        if plan is not None:
            plan.close()
        if input_plan is None:
            cohort.close()


def draw_density_fields(
    ax,
    columns,
    layer,
    panel,
    color_iter,
    theme,
    *,
    curve_styles=None,
    input_plan=None,
    row_ids=None,
):
    if layer.type in {"hist2d", "ecdf2d"}:
        return draw_mesh_fields(
            ax,
            columns,
            layer,
            panel,
            color_iter,
            theme,
            curve_styles=curve_styles,
            input_plan=input_plan,
            row_ids=row_ids,
        )
    if layer.type == "kde":
        return draw_univariate_kernel(
            ax,
            columns,
            layer,
            panel,
            color_iter,
            theme,
            curve_styles=curve_styles,
            input_plan=input_plan,
            row_ids=row_ids,
        )
    if layer.type == "kde2d":
        from ._kde2d_render import draw_kernel_fields

        return draw_kernel_fields(
            ax,
            columns,
            layer,
            panel,
            color_iter,
            theme,
            curve_styles=curve_styles,
            input_plan=input_plan,
            row_ids=row_ids,
        )
    raise ValueError("density field dispatcher received an unrelated layer")


def density_ordinate_label(layer, panel):
    """Explicit contribution/composition units, never a population-CDF claim."""
    from ._density import density_space, kde_config, multiple

    config = kde_config(layer)
    mode = multiple(config)
    if mode == "fill":
        return (
            "composition of CDF contributions"
            if config.cumulative
            else "density composition"
        )
    if config.cumulative:
        return "stacked CDF contributions" if mode == "stack" else "CDF contribution"
    observation = observation_axes(layer, panel)[0]
    unit = coordinate_unit(
        layer,
        "x",
        "day"
        if observation is not None and observation.temporal is not None
        else "input",
    )
    if (
        density_space(config) == "fit"
        and layer.stat_scale == "axis"
        and observation is not None
        and observation.scale == "log"
    ):
        unit = "log10 input"
    prefix = "stacked density contributions" if mode == "stack" else "density"
    return f"{prefix} (1/{unit})"
