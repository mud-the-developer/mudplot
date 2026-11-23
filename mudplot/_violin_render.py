"""C04 native effects using the shared samplecell, domain and geometry boundaries."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import numpy as np
from matplotlib.artist import Artist
from matplotlib.legend_handler import HandlerBase
from matplotlib.lines import Line2D
from matplotlib.patches import PathPatch
from matplotlib.path import Path

from ._box_render import _mapped_style, _semantic_mapping
from ._categorical import distribution_channels, distribution_plan, sample_rows
from ._components import (
    apply_component_style,
    finalize_component_stroke,
    set_component_linestyle,
)
from ._scatter_semantics import draw_semantic_colourbar
from ._semantics import category_key, numeric_guides, numeric_mapping
from ._violin import prepare_violin
from ._violin_options import (
    VIOLIN_DASHES,
    merged_violin_components,
    violin_config,
    violin_hues,
)
from .spec import SemanticSpec


class ViolinGuide(PathPatch):
    """Empty nondata artist: its native handler encodes a violin, not point area."""

    def __init__(self, body, marker, *, label):
        super().__init__(Path(np.empty((0, 2))), label=label)
        self.body_style = body
        self.inner_marker = marker


class _ViolinGuideHandler(HandlerBase):
    def create_artists(self, legend, handle, xd, yd, width, height, fontsize, trans):
        vertices = np.array(
            [
                [0.5, 0],
                [0.25, 0.15],
                [0.1, 0.35],
                [0.05, 0.5],
                [0.2, 0.75],
                [0.5, 1],
                [0.8, 0.75],
                [0.95, 0.5],
                [0.9, 0.35],
                [0.75, 0.15],
                [0.5, 0],
            ]
        )
        vertices[:, 0] = -xd + vertices[:, 0] * width
        vertices[:, 1] = -yd + vertices[:, 1] * height
        body = PathPatch(Path(vertices), **handle.body_style, transform=trans)
        finalize_component_stroke(body, body=True)
        artists: list[Artist] = [body]
        if handle.inner_marker is not None:
            artists.append(
                Line2D(
                    [-xd + width / 2],
                    [-yd + height / 2],
                    linestyle="none",
                    transform=trans,
                    **handle.inner_marker,
                )
            )
        return artists


def _proxy(ax, context, label, *, color=None, stroke=None, dash=None, marker=None):
    body = context["body"]
    face = body.get_facecolor()
    edge = body.get_edgecolor()
    styles = {
        "facecolor": color if color is not None else (face[0] if len(face) else "none"),
        "edgecolor": edge[0] if len(edge) else "none",
        "linewidth": float(body.get_linewidths()[0]) if stroke is None else stroke,
        "linestyle": context["dash"] if dash is None else dash,
        "alpha": body.get_alpha(),
        "hatch": body.get_hatch(),
    }
    glyph = None
    native_mark = context["mark"]
    if native_mark is not None:
        glyph = {
            "marker": native_mark.get_marker() if marker is None else marker,
            "markersize": native_mark.get_markersize(),
            "markerfacecolor": native_mark.get_markerfacecolor(),
            "markeredgecolor": native_mark.get_markeredgecolor(),
            "markeredgewidth": native_mark.get_markeredgewidth(),
            "alpha": native_mark.get_alpha(),
        }
    if styles["linewidth"] == 0:
        styles["linestyle"] = "solid"
    proxy = ViolinGuide(styles, glyph, label=label)
    ax.add_patch(proxy)
    handlers = getattr(ax, "_mudplot_legend_handlers", {})
    handlers[ViolinGuide] = _ViolinGuideHandler()
    ax._mudplot_legend_handlers = handlers
    return proxy


def _guides(ax, layer, mapping, contexts, columns, rows, domain):
    from ._render import _decorate

    config = layer.semantics
    if layer.label:
        _proxy(ax, contexts[0], _decorate(layer.label, layer.citation, layer.href))
    if not config.legend:
        return
    source = columns if domain is None else domain["columns"]
    selected_rows = rows if domain is None else domain["rows"]
    for role in ("hue", "size", "style"):
        name = getattr(config, role)
        if name is None or (
            role == "hue" and config.hue_kind == "numeric" and layer.colorbar
        ):
            continue
        kind = "categorical" if role == "style" else getattr(config, role + "_kind")
        if kind == "categorical":
            observed = {category_key(source[name][row]) for row in selected_rows}
            selected = mapping["levels"][role]
            values = [
                (value, 0.5 if len(selected) == 1 else index / (len(selected) - 1))
                for index, value in enumerate(selected)
                if category_key(value) in observed
            ]
        else:
            bounds = mapping["bounds"][role]
            values = numeric_guides(bounds)
            fractions, _ = numeric_mapping(
                values, bounds if bounds[0] != bounds[1] else None
            )
            values = list(zip(values, fractions, strict=True))
        for value, fraction in values:
            context = next(
                (
                    item
                    for item in contexts
                    if role in item["roles"]
                    and category_key(item["roles"][role]) == category_key(value)
                ),
                contexts[0],
            )
            color = stroke = dash = marker = None
            unit = ""
            if role == "hue":
                color = (
                    mapping["colors"][category_key(value)]
                    if kind == "categorical"
                    else mapping["cmap"](fraction)
                )
            elif role == "size":
                stroke = config.sizes[0] * (1 - fraction) + config.sizes[1] * fraction
                unit = " (body outline stroke pt)"
            else:
                index = [category_key(item) for item in mapping["levels"][role]].index(
                    category_key(value)
                )
                dash = (config.dashes or VIOLIN_DASHES)[index]
                if context["mark"] is not None:
                    marker = config.markers[index]
                unit = (
                    " (body dash / inner glyph)"
                    if marker is not None
                    else " (body dash)"
                )
            handle = _proxy(
                ax,
                context,
                f"{role}: {name}={value}{unit}",
                color=color,
                stroke=stroke,
                dash=dash,
                marker=marker,
            )
            from ._shared_guides import tag_entry

            tag_entry(ax, handle, layer, role, value)


def draw_violins(ax, columns, layer, color_iter, theme, *, domain=None, guides=True):
    from ._render import (
        _category_geometry,
        _decorate,
        _distribution_artists,
        _finish_category_axis,
        _set_url,
    )

    rows = sample_rows(columns, layer)
    categories, groups, cells = distribution_plan(
        columns, layer, rows=rows, domain=domain
    )
    if not categories:
        return
    positions, spacing, labels = _category_geometry(ax, categories, layer)
    if not cells:
        _finish_category_axis(ax, positions, spacing, labels, layer)
        return
    category, value, hue = distribution_channels(layer)
    one_column = not bool(layer.y)
    if one_column and not layer.native_scale:
        labels = [
            _decorate(layer.label, layer.citation, layer.href)
            if category is None
            else _decorate(
                str(item),
                ref.citation if ref is not None else None,
                ref.href if ref is not None else None,
            )
            for item in categories
            for ref in [(layer.references or {}).get(str(item))]
        ]
        ticks = ax.set_yticks if layer.orient == "h" else ax.set_xticks
        ticks(positions, labels=labels)
    width = (
        (0.5 if one_column and not layer.native_scale else 0.8)
        if layer.width is None
        else layer.width
    )
    if layer.native_scale:
        width *= spacing
    gap = 0 if layer.gap is None else layer.gap
    grouped, weight_cells = {}, {}
    norm_hues = {}
    members_by_group: dict[object, list[dict[str, Any]]] = {}
    for cell in cells:
        group = cell["group"]
        members_by_group.setdefault(group, []).append(cell)
        key = None if cell["category"] is None else category_key(cell["category"])
        grouped.setdefault(group, {})[key] = [
            columns[value][row] for row in cell["rows"]
        ]
        norm_hues[group] = None if cell["hue"] is None else category_key(cell["hue"])
        if layer.weights is not None:
            weight_cells.setdefault(group, {})[key] = [
                columns[layer.weights][row] for row in cell["rows"]
            ]
    value_axis = ax.xaxis if layer.orient == "h" else ax.yaxis
    profiles = prepare_violin(
        grouped,
        layer,
        weights=weight_cells if layer.weights is not None else None,
        log_value=layer.stat_scale == "axis" and value_axis.get_scale() == "log",
        normalization_hues=norm_hues,
    )
    config = layer.semantics
    mapping = (
        _semantic_mapping(
            columns,
            layer,
            rows,
            domain,
            color_iter if config.hue is not None else iter([layer.color or "#4b5563"]),
        )
        if isinstance(config, SemanticSpec)
        else None
    )
    hues = violin_hues(columns, layer, rows)
    hue_indices: dict[object, int] = {
        None if item is None else category_key(item): index
        for index, item in enumerate(hues)
    }
    category_indices: dict[object, int] = {
        None if item is None else category_key(item): index
        for index, item in enumerate(categories)
    }
    group_indices = {group["key"]: index for index, group in enumerate(groups)}
    colors = None
    if mapping is None or config.hue is None:
        color_levels = categories if one_column and hue is None else hues
        colors = {
            None if item is None else category_key(item): layer.color
            or next(color_iter)
            for item in color_levels
        }
    span = width if layer.dodge is None else layer.dodge * spacing
    dodged = (
        len(groups) > 1
        and span != 0
        and (not one_column or isinstance(config, SemanticSpec))
    )
    paired = layer.split and violin_config(layer).split_policy == "paired"
    contexts: list[dict[str, Any]] = []
    for group_key, members in members_by_group.items():
        first = members[0]
        hue_key = None if first["hue"] is None else category_key(first["hue"])
        offset, side, body_width = 0.0, 0, width
        if paired:
            pairs = (len(hues) + 1) // 2
            index = hue_indices[hue_key]
            offset = (index // 2 - (pairs - 1) / 2) * width / pairs
            body_width = width / pairs
            side = -1 if index % 2 == 0 else 1
        elif layer.split:
            side = -1 if hue_indices[hue_key] == 0 else 1
        elif dodged:
            offset = (
                (group_indices[group_key] - (len(groups) - 1) / 2) * span / len(groups)
            )
            body_width /= len(groups)
        body_width *= 1 - gap
        components = merged_violin_components(layer, first["hue"])
        glyphs = layer.inner in ("point", "box")
        mapped_color = stroke = dash = marker = None
        if mapping is not None:
            mapped_color, stroke, dash, marker = _mapped_style(
                first["roles"], config, mapping, glyphs=glyphs
            )
        temporary = replace(
            layer,
            components=components,
            marker=marker if marker is not None else layer.marker,
        )
        category_keys = [
            None if cell["category"] is None else category_key(cell["category"])
            for cell in members
        ]
        # One native call per actual raw-role group preserves native inner
        # defaults across its category cells; each fitted profile stays separate.
        drawn = _distribution_artists(
            ax,
            [grouped[group_key][key] for key in category_keys],
            [float(positions[category_indices[key]]) + offset for key in category_keys],
            body_width,
            [labels[category_indices[key]] for key in category_keys],
            temporary,
            [(profiles[group_key, key], side) for key in category_keys],
        )
        for cell, cat_key, body in zip(members, category_keys, drawn, strict=True):
            color = (
                mapped_color
                if colors is None
                else colors[cat_key if one_column and hue is None else hue_key]
            )
            body_style = components.body if components is not None else None
            if body_style is not None and body_style.color is not None:
                color = body_style.color
            body.set_facecolor(color)
            body.set_alpha(layer.alpha if layer.alpha < 1 else 0.6)
            redundant = (
                theme.redundant_encoding
                and len(hues if hue is not None else categories) > 1
            )
            if redundant and not (
                isinstance(config, SemanticSpec) and config.style is not None
            ):
                index = (
                    hue_indices[hue_key]
                    if hue is not None
                    else category_indices[cat_key]
                )
                body.set_hatch(theme.hatches[index % len(theme.hatches)])
            requested_stroke = (
                stroke is not None
                or dash is not None
                or layer.line_width is not None
                or layer.line_style is not None
                or (
                    body_style is not None
                    and (
                        body_style.line_width is not None
                        or body_style.line_style is not None
                    )
                )
            )
            if requested_stroke and not len(body.get_edgecolor()):
                body.set_edgecolor(layer.edge_color or "#4b5563")
            if layer.edge_color is not None:
                body.set_edgecolor(layer.edge_color)
            if layer.line_width is not None:
                body.set_linewidth(layer.line_width)
            declared_dash = layer.line_style or "-"
            if layer.line_style is not None:
                set_component_linestyle(body, layer.line_style)
            if body_style is not None:
                apply_component_style(body, body_style, body=True, include_color=False)
                declared_dash = body_style.line_style or declared_dash
            if stroke is not None:
                body.set_linewidth(stroke)
            if dash is not None:
                body.set_linestyle(dash)
                declared_dash = dash
            if declared_dash == "none":
                set_component_linestyle(body, "none")
            finalize_component_stroke(body, body=True)
            reference = (layer.references or {}).get(str(cell["hue"]))
            _set_url(body, reference.href if reference is not None else layer.href)
            part = (
                "point"
                if layer.inner == "point"
                else "median"
                if layer.inner == "box"
                else None
            )
            marks = body._mudplot_violin_parts.get(part, [])
            contexts.append(
                {
                    "body": body,
                    "mark": marks[0] if marks else None,
                    "roles": cell["roles"],
                    "dash": declared_dash,
                    "hue": cell["hue"],
                }
            )
    _finish_category_axis(ax, positions, spacing, labels, layer)
    if not isinstance(config, SemanticSpec):
        seen_hues = set()
        for context in contexts:
            raw_hue = context["hue"]
            key = None if raw_hue is None else category_key(raw_hue)
            if key in seen_hues:
                continue
            seen_hues.add(key)
            ref = (layer.references or {}).get(str(raw_hue))
            label = (
                _decorate(layer.label, layer.citation, layer.href)
                if hue is None
                else _decorate(
                    str(raw_hue),
                    ref.citation if ref is not None else None,
                    ref.href if ref is not None else None,
                )
            )
            if label:
                _proxy(ax, context, label)
    elif contexts and mapping is not None:
        if config.hue is not None and config.hue_kind == "numeric" and layer.colorbar:
            draw_semantic_colourbar(
                ax, layer, mapping["bounds"]["hue"], mapping["cmap"]
            )
        if guides:
            _guides(ax, layer, mapping, contexts, columns, rows, domain)
            if config.hue is None and hue is not None:
                for raw_hue in hues:
                    context = next(
                        (
                            item
                            for item in contexts
                            if category_key(item["hue"]) == category_key(raw_hue)
                        ),
                        None,
                    )
                    if context is not None:
                        ref = (layer.references or {}).get(str(raw_hue))
                        _proxy(
                            ax,
                            context,
                            _decorate(
                                str(raw_hue),
                                ref.citation if ref is not None else None,
                                ref.href if ref is not None else None,
                            ),
                        )
