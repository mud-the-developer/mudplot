"""Native C05 effects: shared mappings/coordinate inversion, real band patches."""

from __future__ import annotations

import itertools
from typing import Any, cast

import numpy as np
from matplotlib.artist import Artist
from matplotlib.colors import to_rgb
from matplotlib.legend_handler import HandlerBase
from matplotlib.lines import Line2D
from matplotlib.patches import PathPatch, Polygon, Rectangle
from matplotlib.path import Path

from ._box import BOX_DASHES
from ._box_render import _mapped_style, _semantic_mapping
from ._boxen import (
    band_target,
    boxen_config,
    boxen_hues,
    hue_override,
    merged_band_body,
    merged_boxen_components,
)
from ._categorical import distribution_channels, sample_rows
from ._components import apply_component_style, finalize_component_stroke
from ._scatter_semantics import draw_semantic_colourbar
from ._semantics import category_key, numeric_guides, numeric_mapping
from .spec import SemanticSpec


class BoxenGuide(PathPatch):
    """Empty nondata handle; only actual body/median/flier styles are represented."""

    def __init__(self, body, median, flier, *, label):
        super().__init__(Path(np.empty((0, 2))), label=label)
        self.body_style, self.median_style, self.flier_style = body, median, flier


class _BoxenGuideHandler(HandlerBase):
    def create_artists(self, legend, handle, xd, yd, width, height, fontsize, trans):
        artists: list[Artist] = []
        for left, bottom, wide, tall in ((0.3, 0, 0.4, 1), (0.05, 0.3, 0.9, 0.4)):
            patch = Rectangle(
                (-xd + left * width, -yd + bottom * height),
                wide * width,
                tall * height,
                transform=trans,
                **handle.body_style,
            )
            finalize_component_stroke(patch, body=True)
            artists.append(patch)
        if handle.median_style is not None:
            line = Line2D(
                [-xd + width * 0.05, -xd + width * 0.95],
                [-yd + height * 0.5] * 2,
                transform=trans,
                **handle.median_style,
            )
            finalize_component_stroke(line)
            artists.append(line)
        if handle.flier_style is not None:
            artists.append(
                Line2D(
                    [-xd + width / 2],
                    [-yd + height * 1.15],
                    linestyle="none",
                    transform=trans,
                    **handle.flier_style,
                )
            )
        return artists


def _has_flier_glyph(context):
    flier = context["flier"]
    return flier is not None and flier.get_marker() not in (
        None,
        "None",
        "none",
        "",
        " ",
    )


def _proxy(ax, context, label, *, color=None, stroke=None, dash=None, marker=None):
    body = context["body"]
    styles = {
        "facecolor": body.get_facecolor() if color is None else color,
        "edgecolor": body.get_edgecolor(),
        "linewidth": body.get_linewidth() if stroke is None else stroke,
        "linestyle": body.get_linestyle() if dash is None else dash,
        "alpha": body.get_alpha(),
        "hatch": body.get_hatch(),
    }
    if styles["linewidth"] == 0:
        styles["linestyle"] = "solid"
    median = context["median"]
    median_style = (
        None
        if median is None
        else {
            "color": median.get_color(),
            "linewidth": median.get_linewidth(),
            "linestyle": median.get_linestyle(),
            "alpha": median.get_alpha(),
        }
    )
    flier = context["flier"]
    actual_glyph = flier is not None and flier.get_marker() not in (
        None,
        "None",
        "none",
        "",
        " ",
    )
    flier_style = (
        None
        if flier is None or not actual_glyph
        else {
            "marker": flier.get_marker() if marker is None else marker,
            "markersize": flier.get_markersize(),
            "markerfacecolor": flier.get_markerfacecolor(),
            "markeredgecolor": flier.get_markeredgecolor(),
            "markeredgewidth": flier.get_markeredgewidth(),
            "alpha": flier.get_alpha(),
        }
    )
    proxy = BoxenGuide(styles, median_style, flier_style, label=label)
    ax.add_patch(proxy)
    handlers = getattr(ax, "_mudplot_legend_handlers", {})
    handlers[BoxenGuide] = _BoxenGuideHandler()
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
                (value, 0.5 if len(selected) == 1 else i / (len(selected) - 1))
                for i, value in enumerate(selected)
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
            matches = [
                item
                for item in contexts
                if role in item["roles"]
                and category_key(item["roles"][role]) == category_key(value)
            ]
            # A style guide may show a glyph only from a real glyph-bearing cell
            # of that raw style, never a representative from another style.
            context = next(
                (item for item in matches if _has_flier_glyph(item)),
                matches[0] if matches else contexts[0],
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
                dash = (config.dashes or BOX_DASHES)[index]
                if matches and _has_flier_glyph(context):
                    marker = config.markers[index]
                unit = (
                    " (body dash / observed flier glyph)"
                    if marker is not None
                    else " (body dash)"
                )
                if not matches:
                    context = {**context, "flier": None}
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


def _band_has_color(layer, hue, target):
    entry = hue_override(layer, hue)
    return any(
        (band.rank, band.side) == target and band.body.color is not None
        for bands in (
            boxen_config(layer).band_components,
            None if entry is None else entry.band_components,
        )
        for band in bands or ()
    )


def native_boxen_artists(ax, contexts, layer):
    """Draw already admitted/derived statistics without another summary pass."""
    horizontal = layer.orient == "h"
    edge = layer.edge_color or "#4b5563"
    stroke = 0.8 if layer.line_width is None else layer.line_width
    bodies = []
    for context in contexts:
        summary, center, width = context["summary"], context["center"], context["width"]
        bands = []
        for index, ((low, high), relative) in enumerate(
            zip(itertools.pairwise(summary.values), summary.widths, strict=True)
        ):
            half = width * relative / 2
            if relative > 0 and (half <= 0 or center - half == center + half):
                raise ValueError("positive boxen band extent is unrepresentable")
            points = np.array(
                [
                    [center - half, low],
                    [center + half, low],
                    [center + half, high],
                    [center - half, high],
                ]
            )
            if horizontal:
                points = points[:, ::-1]
            target = band_target(summary, index)
            body_style = merged_band_body(layer, context["hue"], *target)
            color = context["color"]
            if body_style is not None and body_style.color is not None:
                color = body_style.color
            mapped_hue = (
                isinstance(layer.semantics, SemanticSpec)
                and layer.semantics.hue is not None
            )
            if (
                not mapped_hue
                and not _band_has_color(layer, context["hue"], target)
                and color != "none"
            ):
                tint = 0.55 * (1 - (summary.depth - target[0]) / summary.depth)
                color = np.asarray(to_rgb(color)) * (1 - tint) + tint
            patch = Polygon(
                points,
                closed=True,
                facecolor=color,
                edgecolor=edge,
                linewidth=stroke if context["stroke"] is None else context["stroke"],
                linestyle=context["dash"],
                alpha=layer.alpha if layer.alpha < 1 else 0.6,
                hatch=context["hatch"],
            )
            apply_component_style(patch, body_style, body=True, include_color=False)
            finalize_component_stroke(patch, body=True)
            native_low, native_high = context["native_values"][index : index + 2]
            cast(Any, patch)._mudplot_boxen_value_coordinates = (
                native_low,
                native_low,
                native_high,
                native_high,
                native_low,
            )[: len(cast(Any, patch.get_path().vertices))]
            ax.add_patch(patch)
            bands.append(patch)
        components = context["components"]
        median = None
        if layer.showmedians is not False:
            category = [center - width / 2, center + width / 2]
            value = [summary.median] * 2
            x, y = (value, category) if horizontal else (category, value)
            (median,) = ax.plot(
                x,
                y,
                color=edge,
                linewidth=stroke,
                linestyle=layer.line_style or "-",
                alpha=layer.alpha,
                solid_capstyle="butt",
            )
            apply_component_style(
                median, None if components is None else components.median
            )
            median._mudplot_boxen_value_coordinates = (
                context["native_median"],
                context["native_median"],
            )
        flier = None
        if layer.showfliers is not False and summary.fliers:
            category, value = (
                np.full(len(summary.fliers), center),
                np.asarray(summary.fliers),
            )
            x, y = (value, category) if horizontal else (category, value)
            (flier,) = ax.plot(
                x,
                y,
                linestyle="none",
                color=edge,
                marker=context["marker"] or layer.marker or "d",
                markersize=3 if layer.marker_size is None else layer.marker_size,
                markerfacecolor="none",
                markeredgewidth=stroke,
                alpha=layer.alpha,
            )
            apply_component_style(
                flier, None if components is None else components.flier
            )
            flier._mudplot_boxen_value_coordinates = context["original_fliers"]
        context.update(
            bands=bands, body=bands[summary.depth - 1], median=median, flier=flier
        )
        bodies.append(context["body"])
    return bodies


def draw_boxen(ax, plan, layer, color_iter, theme, *, domain=None, guides=True):
    from ._render import (
        _category_geometry,
        _decorate,
        _distribution_artists,
        _finish_category_axis,
        _set_url,
    )

    columns, categories, groups = plan.columns, plan.categories, plan.groups
    if not categories:
        return
    positions, spacing, labels = _category_geometry(ax, categories, layer)
    if not plan.cells:
        _finish_category_axis(ax, positions, spacing, labels, layer)
        return
    category, _, hue = distribution_channels(layer)
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
        (ax.set_yticks if layer.orient == "h" else ax.set_xticks)(
            positions, labels=labels
        )
    width = 0.8 if layer.width is None else layer.width
    if layer.native_scale:
        width *= spacing
    gap = 0 if layer.gap is None else layer.gap
    config, rows = layer.semantics, sample_rows(columns, layer)
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
    hues = boxen_hues(columns, layer, rows)

    def key(value):
        return None if value is None else category_key(value)

    hue_indices = {key(item): i for i, item in enumerate(hues)}
    category_indices = {key(item): i for i, item in enumerate(categories)}
    group_indices = {group["key"]: i for i, group in enumerate(groups)}
    colors = (
        None
        if mapping is not None and config.hue is not None
        else {
            key(item): layer.color or next(color_iter)
            for item in (categories if one_column and hue is None else hues)
        }
    )
    contexts = []
    for prepared in plan.cells:
        cell, summary = prepared.cell, prepared.summary
        cat_key, hue_key = key(cell["category"]), key(cell["hue"])
        center = float(positions[category_indices[cat_key]])
        drawn_width = width
        span = width if layer.dodge is None else layer.dodge * spacing
        if (
            len(groups) > 1
            and span != 0
            and (not one_column or isinstance(config, SemanticSpec))
        ):
            center += (
                (group_indices[cell["group"]] - (len(groups) - 1) / 2)
                * span
                / len(groups)
            )
            drawn_width /= len(groups)
        drawn_width *= 1 - gap
        actual_glyph = layer.showfliers is not False and bool(summary.fliers)
        color = stroke = dash = marker = None
        if mapping is not None:
            color, stroke, dash, marker = _mapped_style(
                cell["roles"], config, mapping, glyphs=actual_glyph
            )
        if colors is not None:
            color = colors[cat_key if one_column and hue is None else hue_key]
        components = merged_boxen_components(layer, cell["hue"])
        if (
            components is not None
            and components.body is not None
            and components.body.line_style is not None
        ):
            declared_dash = components.body.line_style
        else:
            declared_dash = layer.line_style or "-"
        redundant = (
            theme.redundant_encoding
            and len(hues if hue is not None else categories) > 1
        )
        hatch = (
            theme.hatches[
                (hue_indices[hue_key] if hue is not None else category_indices[cat_key])
                % len(theme.hatches)
            ]
            if redundant
            and not (isinstance(config, SemanticSpec) and config.style is not None)
            else None
        )
        contexts.append(
            {
                "summary": summary,
                "center": center,
                "width": drawn_width,
                "original_fliers": prepared.original_fliers,
                "native_values": prepared.native_values,
                "native_median": prepared.native_median,
                "hue": cell["hue"],
                "roles": cell["roles"],
                "components": components,
                "color": color,
                "stroke": stroke,
                "dash": dash or declared_dash,
                "marker": marker,
                "hatch": hatch,
            }
        )
    _distribution_artists(ax, [], [], width, [], layer, boxen_context=contexts)
    for context in contexts:
        reference = (layer.references or {}).get(str(context["hue"]))
        for body in context["bands"]:
            _set_url(body, reference.href if reference is not None else layer.href)
    _finish_category_axis(ax, positions, spacing, labels, layer)
    if not isinstance(config, SemanticSpec):
        seen = set()
        for context in contexts:
            raw = context["hue"]
            if key(raw) in seen:
                continue
            seen.add(key(raw))
            ref = (layer.references or {}).get(str(raw))
            label = (
                _decorate(layer.label, layer.citation, layer.href)
                if hue is None
                else _decorate(
                    str(raw), ref.citation if ref else None, ref.href if ref else None
                )
            )
            if label:
                _proxy(ax, context, label)
    elif mapping is not None:
        if config.hue is not None and config.hue_kind == "numeric" and layer.colorbar:
            draw_semantic_colourbar(
                ax, layer, mapping["bounds"]["hue"], mapping["cmap"]
            )
        if guides:
            _guides(ax, layer, mapping, contexts, columns, rows, domain)
            if config.hue is None and hue is not None:
                for raw in hues:
                    context = next(
                        (item for item in contexts if key(item["hue"]) == key(raw)),
                        None,
                    )
                    if context is not None:
                        ref = (layer.references or {}).get(str(raw))
                        _proxy(
                            ax,
                            context,
                            _decorate(
                                str(raw),
                                ref.citation if ref else None,
                                ref.href if ref else None,
                            ),
                        )
