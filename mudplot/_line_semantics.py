"""Shared line-estimate/empirical-curve roles; guides never define data."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, cast

from matplotlib import pyplot as plt
from matplotlib.collections import Collection
from matplotlib.legend_handler import HandlerPatch
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, PathPatch
from matplotlib.path import Path
from matplotlib.transforms import IdentityTransform

from . import _semantics
from ._lineplot import draw_lineplot, draw_raw_lines
from ._semantics import (
    categorical_fractions,
    category_key,
    numeric_guides,
    numeric_mapping,
    semantic_curve_input,
    semantic_levels,
    semantic_partition,
    semantic_rows,
)

if TYPE_CHECKING:
    from matplotlib.typing import ColorType


def draw_semantic_curves(
    ax,
    columns,
    layer,
    color_iter,
    theme,
    *,
    domain=None,
    guides=True,
    panel=None,
    row_ids=None,
    prepared=None,
):
    from ._render import _continuous_cmap, _decorate

    cfg = layer.semantics
    rows = semantic_rows(columns, layer)
    statistical = layer.type in {"barplot", "pointplot", "countplot"}
    histogram = layer.type == "hist"
    body = histogram or layer.type == "countplot"
    bar = layer.type in {"barplot", "countplot"}
    point = layer.type == "pointplot"
    raw = layer.type == "line"
    cell_field = layer.type in {"hist2d", "ecdf2d", "kde2d"}
    kernel_curve = layer.type == "kde"
    density_mark = cell_field or kernel_curve
    pool = rows if domain is None else domain["rows"]
    mapping_columns = columns if domain is None else domain.get("columns", columns)
    hue_pools = slots = None
    if body:
        from ._body_semantics import body_plan

        ids, curves, hue_pools, slots = body_plan(columns, layer, rows, domain)
        names = {
            layer.x,
            getattr(layer.histogram if histogram else layer.stat, "weights", None),
        }
        data = {
            name: [columns[name][i] for i in rows] for name in names if name is not None
        }
        group = "__mudplot_body_tuple"
        while group in data:
            group += "_"
        data[group] = [ids[i] for i in rows]
        temporary = replace(
            layer, semantics=None, group=group, hue_order=list(slots), label=None
        )
    elif density_mark:
        data, temporary = columns, layer
        _ids, curves = semantic_partition(columns, cfg, rows)
    elif prepared is None:
        data, temporary, curves, source_rows = semantic_curve_input(columns, layer)
    else:
        data, temporary = columns, replace(layer, semantics=None)
        curves = prepared.curves
        source_rows = range(len(columns[layer.x]))
    if histogram and not rows:
        return False
    if statistical and not rows:
        from ._render import _draw_stat_layer

        _draw_stat_layer(
            ax,
            None,
            data,
            replace(temporary, axis="y"),
            color_iter,
            theme,
            curve_styles={},
            advanced=True,
        )
        return
    if not pool and layer.type in {"line", "lineplot"}:
        if raw:
            original = getattr(ax, "_mudplot_source_rows", range(len(columns[layer.x])))
            draw_raw_lines(
                ax,
                data,
                temporary,
                color_iter,
                theme,
                curve_styles={},
                source_rows=tuple(original[row] for row in source_rows),
            )
        else:
            draw_lineplot(
                ax,
                data,
                temporary,
                color_iter,
                theme,
                curve_styles={},
                prepared=prepared,
            )
        return
    legacy_levels = (
        (
            list(layer.hue_order)
            if layer.hue_order is not None
            else _semantics.levels(columns[layer.group][index] for index in rows)
        )
        if (statistical or histogram) and layer.group is not None and cfg.hue is None
        else []
    )
    legacy_colors = {category_key(value): next(color_iter) for value in legacy_levels}
    base = layer.color or (
        next(color_iter) if cfg.hue is None and not legacy_levels else "#4b5563"
    )
    if not pool:
        if density_mark:
            from ._field_render import draw_density_fields

            if panel is None:
                raise ValueError("field drawing requires the actual logical panel")
            draw_density_fields(
                ax,
                data,
                temporary,
                panel,
                color_iter,
                theme,
                curve_styles={},
                row_ids=row_ids,
            )
        return False
    levels, bounds, fractions, values = {}, {}, {}, {}
    for role in ("hue", "size", "style"):
        column = getattr(cfg, role)
        if column is None:
            continue
        values[role] = [mapping_columns[column][i] for i in pool]
        kind = "categorical" if role == "style" else getattr(cfg, f"{role}_kind")
        actual = [curve[role] for curve in curves]
        if kind == "categorical":
            levels[role] = semantic_levels(mapping_columns, cfg, role, pool)
            fractions[role] = categorical_fractions(actual, levels[role])
        else:
            _, bounds[role] = numeric_mapping(
                values[role], getattr(cfg, f"{role}_norm")
            )
            fractions[role], _ = numeric_mapping(actual, bounds[role])
    cmap = _continuous_cmap(layer.cmap_kind) if cfg.hue_kind == "numeric" else None
    hue_colors = {}
    if cfg.hue is not None and cfg.hue_kind == "categorical":
        palette = plt.rcParams["axes.prop_cycle"].by_key()["color"]
        hue_colors = {
            category_key(value): next(color_iter)
            if domain is None
            else palette[domain["offset"] + i]
            for i, value in enumerate(levels["hue"])
        }
    style_positions = {
        category_key(v): i for i, v in enumerate(levels.get("style", []))
    }
    if density_mark:
        from ._field_render import field_stroke_width

        base_width = field_stroke_width(layer)
    else:
        base_width = (
            (
                float(plt.rcParams["patch.linewidth"])
                if bar
                else float(plt.rcParams["lines.linewidth"])
                if raw
                else 1.25
            )
            if layer.line_width is None
            else layer.line_width
        )
    mapped = {}
    for i, curve in enumerate(curves):
        color = (
            legacy_colors.get(category_key(curve["legacy_hue"]), base)
            if legacy_levels
            else base
        )
        if cfg.hue is not None:
            if cfg.hue_kind == "categorical":
                color = hue_colors[category_key(curve["hue"])]
            else:
                assert cmap is not None
                color = cmap(fractions["hue"][i])
        width = base_width
        marker_size = (
            (float(plt.rcParams["lines.markersize"]) if raw else 5)
            if layer.marker_size is None
            else layer.marker_size
        )
        if cfg.size is not None:
            t = fractions["size"][i]
            size = cfg.sizes[0] * (1 - t) + cfg.sizes[1] * t
            if point:
                marker_size = size
            else:
                width = size
        marker, dash = (
            layer.marker or ("o" if point else "None"),
            layer.line_style or "-",
        )
        if cfg.style is not None:
            index = style_positions[category_key(curve["style"])]
            if not bar and not density_mark and not histogram:
                marker = cfg.markers[index]
            if cfg.dashes is not None or statistical or density_mark or histogram:
                dash = (cfg.dashes or ("-", "--", "-.", ":"))[index]
        mapped[curve.get("_index", i)] = {
            "color": color,
            "width": width,
            "marker": marker,
            "dash": dash,
            "marker_size": marker_size,
            "edge_color": layer.edge_color
            or (
                "#30343b"
                if (bar or histogram)
                and (cfg.size is not None or cfg.style is not None)
                else None
            ),
        }
    if density_mark:
        from ._field_render import draw_density_fields

        if panel is None:
            raise ValueError("field drawing requires the actual logical panel")
        draw_density_fields(
            ax,
            data,
            temporary,
            panel,
            color_iter,
            theme,
            curve_styles=mapped,
            row_ids=row_ids,
        )
        mapped = {index: style for index, style in mapped.items() if "artist" in style}
        if not mapped:
            return False
    elif layer.type == "ecdf":
        from ._render import _draw_ecdf_layer

        if not rows:
            return
        _draw_ecdf_layer(ax, data, temporary, color_iter, theme, curve_styles=mapped)
    elif histogram:
        from ._render import _draw_histogram_layer

        _draw_histogram_layer(
            ax,
            data,
            temporary,
            color_iter,
            theme,
            curve_styles=mapped,
            hue_pools=hue_pools,
            slots=slots,
        )
    elif statistical:
        from ._render import _draw_stat_layer

        _draw_stat_layer(
            ax,
            None,
            data,
            replace(temporary, axis="y"),
            color_iter,
            theme,
            curve_styles=mapped,
            advanced=True,
            hue_pools=hue_pools,
            slots=slots,
        )
    elif raw:
        original = getattr(ax, "_mudplot_source_rows", range(len(columns[layer.x])))
        draw_raw_lines(
            ax,
            data,
            temporary,
            color_iter,
            theme,
            curve_styles=mapped,
            source_rows=tuple(original[row] for row in source_rows),
        )
    else:
        draw_lineplot(
            ax,
            data,
            temporary,
            color_iter,
            theme,
            curve_styles=mapped,
            prepared=prepared,
        )
    if histogram and not any("artist" in style for style in mapped.values()):
        return False
    if not cell_field and rows and cfg.hue_kind == "numeric" and cfg.hue is not None:
        from ._scatter_semantics import draw_semantic_colourbar

        draw_semantic_colourbar(ax, layer, bounds["hue"], cmap)

    if histogram:
        mapped = {index: style for index, style in mapped.items() if "artist" in style}
    if not mapped:
        return False
    base_context = next(iter(mapped.values()))

    def context_for(role, value):
        key = category_key(value)
        return next(
            (
                mapped[curve.get("_index", index)]
                for index, curve in enumerate(curves)
                if curve.get("_index", index) in mapped
                and role in curve
                and category_key(curve[role]) == key
            ),
            base_context,
        )

    def update_bar_guide(handle, original):
        handle.update_from(original)
        handle.set_linestyle(original.get_linestyle())

    bar_handler = HandlerPatch(update_func=update_bar_guide) if bar else None

    def proxy(
        label,
        *,
        context=None,
        color=None,
        width=None,
        marker=None,
        dash=None,
        header=False,
        marker_size=None,
        role=None,
        value=None,
    ):
        context = base_context if context is None else context
        if (
            cell_field
            or (kernel_curve and context.get("filled"))
            or (
                histogram
                and context.get("filled")
                and hasattr(context["artist"], "get_edgecolors")
            )
        ):
            from ._field_render import field_guide

            handle = field_guide(
                ax, context, label, color=color, width=width, dash=dash, header=header
            )
            if role is not None:
                from ._shared_guides import tag_entry

                tag_entry(ax, handle, layer, role, value, context=handle)
            return
        artist = context.get("artist")
        patch_context = bar or (histogram and context.get("filled"))
        if histogram and not patch_context and not isinstance(artist, Line2D):
            artist = None
        if statistical:
            assert artist is not None
        override_color = color is not None
        if color is None:
            color = (
                (
                    cast("Patch | Collection", artist).get_facecolor()
                    if patch_context
                    else artist.get_color()
                )
                if artist is not None
                else context["color"]
            )
        if width is None:
            width = artist.get_linewidth() if artist is not None else context["width"]
        if dash is None:
            dash = artist.get_linestyle() if artist is not None else context["dash"]
        alpha = artist.get_alpha() if artist is not None else layer.alpha
        if patch_context:
            assert artist is not None
            body = cast("Patch | Collection", artist)
            handle = PathPatch(
                Path([(0, 0)], [Path.MOVETO]),
                transform=IdentityTransform(),
                facecolor="none" if header else color,
                edgecolor="none" if header else body.get_edgecolor(),
                linewidth=0 if header else width,
                linestyle="solid" if width == 0 or header else dash,
                hatch=None if header else body.get_hatch(),
                alpha=alpha,
                label=label,
            )
            ax.add_patch(handle)
            handlers = getattr(ax, "_mudplot_legend_handlers", {})
            handlers[handle] = bar_handler or HandlerPatch(update_func=update_bar_guide)
            ax._mudplot_legend_handlers = handlers
            if role is not None:
                from ._shared_guides import tag_entry

                tag_entry(ax, handle, layer, role, value, context=artist)
            return
        if marker is None:
            marker = artist.get_marker() if artist is not None else context["marker"]
        if marker_size is None:
            marker_size = (
                artist.get_markersize()
                if artist is not None
                else context["marker_size"]
            )
        line_color = cast("ColorType | None", color)
        handle = Line2D(
            [],
            [],
            color=line_color,
            linewidth=width,
            linestyle="None" if width == 0 or header else dash,
            marker="None" if header else marker,
            markersize=marker_size,
            markerfacecolor=line_color
            if override_color or artist is None
            else artist.get_markerfacecolor(),
            markeredgecolor=line_color
            if override_color or artist is None
            else artist.get_markeredgecolor(),
            markeredgewidth=None if artist is None else artist.get_markeredgewidth(),
            alpha=alpha,
            label=label,
        )
        ax.add_line(handle)
        if role is not None:
            from ._shared_guides import tag_entry

            tag_entry(ax, handle, layer, role, value, context=artist or context)

    if layer.label:
        proxy(_decorate(layer.label, layer.citation, layer.href), header=True)
    if not cfg.legend or not guides:
        return bool(mapped)
    for value in legacy_levels:
        if not any(
            category_key(curve["legacy_hue"]) == category_key(value) for curve in curves
        ):
            continue
        reference = (layer.references or {}).get(str(value))
        proxy(
            _decorate(
                str(value),
                reference.citation if reference else None,
                reference.href if reference else None,
            ),
            context=context_for("legacy_hue", value),
            color=legacy_colors[category_key(value)],
        )
    for role in ("hue", "size", "style"):
        column = getattr(cfg, role)
        if column is None:
            continue
        if (
            role == "hue"
            and cfg.hue_kind == "numeric"
            and layer.colorbar
            and not cell_field
        ):
            continue
        prefix = (
            (
                "size (marker diameter, pt)"
                if point
                else "size (body outline, pt)"
                if bar or cell_field or (histogram and base_context.get("filled"))
                else "size (line width, pt)"
            )
            if role == "size"
            else role
        )
        kind = "categorical" if role == "style" else getattr(cfg, f"{role}_kind")
        selected = (
            levels[role] if kind == "categorical" else numeric_guides(bounds[role])
        )
        ts = (
            categorical_fractions(selected, selected)
            if kind == "categorical"
            else numeric_mapping(selected, bounds[role])[0]
        )
        observed = {category_key(v) for v in values[role]}
        for i, (value, t) in enumerate(zip(selected, ts, strict=True)):
            if kind == "categorical" and category_key(value) not in observed:
                continue
            color = width = marker = dash = marker_size = None
            if role == "hue":
                if kind == "categorical":
                    color = hue_colors[category_key(value)]
                else:
                    assert cmap is not None
                    color = cmap(t)
            elif role == "size":
                size = cfg.sizes[0] * (1 - t) + cfg.sizes[1] * t
                if point:
                    marker_size = size
                else:
                    width = size
            elif role == "style":
                if not bar and not density_mark and not histogram:
                    marker = cfg.markers[i]
                if cfg.dashes is not None or statistical or density_mark or histogram:
                    dash = (cfg.dashes or ("-", "--", "-.", ":"))[i]
            proxy(
                f"{prefix}: {column}={value}",
                context=context_for(role, value),
                color=color,
                width=width,
                marker=marker,
                dash=dash,
                marker_size=marker_size,
                role=role,
                value=value,
            )
    return bool(mapped)
