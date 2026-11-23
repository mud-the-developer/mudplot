"""C03 effects: native bxp artists through the shared distribution geometry map."""

from __future__ import annotations

import inspect
import warnings

import matplotlib as mpl
import numpy as np
from matplotlib.cbook import boxplot_stats
from matplotlib.legend_handler import HandlerBase
from matplotlib.lines import Line2D
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path

from ._box import (
    BOX_DASHES,
    box_config,
    box_rows,
    merged_components,
)
from ._categorical import distribution_channels, distribution_plan
from ._components import apply_component_style, finalize_component_stroke
from ._estimate import _aggregate, _bootstrap_estimates, _linear_quantiles
from ._scatter_semantics import draw_semantic_colourbar
from ._semantics import (
    categorical_fractions,
    category_key,
    numeric_guides,
    numeric_mapping,
    semantic_levels,
)
from .spec import SemanticSpec, StatSpec


def _line_style(line):
    return {
        "color": line.get_color(),
        "linewidth": line.get_linewidth(),
        "linestyle": line.get_linestyle(),
        "alpha": line.get_alpha(),
    }


class BoxGuide(PathPatch):
    """Empty nondata Path; its legend handler draws actual box component styles."""

    def __init__(self, body, lines, *, marker=None, label=""):
        super().__init__(Path(np.empty((0, 2))), label=label)
        self.box_body = body
        self.box_lines = lines
        self.flier_marker = marker


class _BoxGuideHandler(HandlerBase):
    def create_artists(self, legend, handle, xd, yd, width, height, fontsize, trans):
        center = -xd + width / 2
        low, high = -yd + height * 0.25, -yd + height * 0.75
        artists = []
        for role, x, y in (
            ("whisker", [center, center], [-yd, -yd + height]),
            ("cap", [-xd + width * 0.35, -xd + width * 0.65], [-yd, -yd]),
            (
                "cap",
                [-xd + width * 0.35, -xd + width * 0.65],
                [-yd + height, -yd + height],
            ),
        ):
            if role not in handle.box_lines:
                continue
            line = Line2D(x, y, **handle.box_lines[role])
            finalize_component_stroke(line)
            artists.append(line)
        if handle.box_body is not None:
            body = Rectangle(
                (-xd + width * 0.2, low), width * 0.6, high - low, **handle.box_body
            )
            finalize_component_stroke(body, body=True)
            artists.append(body)
        median = Line2D(
            [-xd + width * 0.2, -xd + width * 0.8],
            [-yd + height * 0.5] * 2,
            **handle.box_lines["median"],
        )
        finalize_component_stroke(median)
        artists.append(median)
        if handle.flier_marker is not None:
            artists.append(
                Line2D(
                    [center],
                    [-yd + height * 1.25],
                    linestyle="none",
                    **handle.flier_marker,
                )
            )
        for artist in artists:
            artist.set_transform(trans)
        return artists


def _body_style(patch):
    return {
        "facecolor": patch.get_facecolor(),
        "edgecolor": patch.get_edgecolor(),
        "linewidth": patch.get_linewidth(),
        "linestyle": patch.get_linestyle(),
        "alpha": patch.get_alpha(),
        "hatch": patch.get_hatch(),
    }


def _flier_style(parts, layer, marker):
    if parts["fliers"]:
        artist = parts["fliers"][0]
        return {
            "marker": marker if marker is not None else artist.get_marker(),
            "markersize": artist.get_markersize(),
            "markerfacecolor": artist.get_markerfacecolor(),
            "markeredgecolor": artist.get_markeredgecolor(),
            "markeredgewidth": artist.get_markeredgewidth(),
            "alpha": artist.get_alpha(),
        }
    return {
        "marker": marker,
        "markersize": layer.marker_size
        if layer.marker_size is not None
        else mpl.rcParams["boxplot.flierprops.markersize"],
        "markerfacecolor": mpl.rcParams["boxplot.flierprops.markerfacecolor"],
        "markeredgecolor": layer.edge_color
        or mpl.rcParams["boxplot.flierprops.markeredgecolor"],
        "markeredgewidth": mpl.rcParams["boxplot.flierprops.markeredgewidth"],
    }


def _proxy(
    ax, context, layer, label, *, color=None, width=None, dash=None, marker=None
):
    parts = context["parts"]
    body = _body_style(parts["boxes"][0]) if parts["boxes"] else None
    if body is not None:
        if color is not None:
            body["facecolor"] = color
        if width is not None:
            body["linewidth"] = width
        if dash is not None:
            body["linestyle"] = dash
    lines = {
        role: _line_style(parts[name][0])
        for role, name in (
            ("whisker", "whiskers"),
            ("cap", "caps"),
            ("median", "medians"),
        )
        if parts[name]
    }
    proxy = BoxGuide(
        body,
        lines,
        marker=None if marker is None else _flier_style(parts, layer, marker),
        label=label,
    )
    ax.add_patch(proxy)  # Empty path neither draws observations nor updates dataLim.
    handlers = getattr(ax, "_mudplot_legend_handlers", {})
    handlers[BoxGuide] = _BoxGuideHandler()
    ax._mudplot_legend_handlers = handlers
    return proxy


def _semantic_mapping(columns, layer, rows, domain, color_iter):
    from ._render import _continuous_cmap

    config = layer.semantics
    mapping_columns = columns if domain is None else domain["columns"]
    mapping_rows = rows if domain is None else domain["rows"]
    result = {
        "levels": {},
        "bounds": {},
        "colors": {},
        "base": layer.color or "#4b5563",
    }
    if config.hue is None:
        result["base"] = layer.color or next(color_iter)
    for role in ("hue", "size", "style"):
        name = getattr(config, role)
        if name is None:
            continue
        kind = "categorical" if role == "style" else getattr(config, role + "_kind")
        if kind == "categorical":
            result["levels"][role] = semantic_levels(
                mapping_columns, config, role, mapping_rows
            )
        else:
            _, result["bounds"][role] = numeric_mapping(
                [mapping_columns[name][row] for row in mapping_rows],
                getattr(config, role + "_norm"),
            )
    if config.hue is not None:
        if config.hue_kind == "categorical":
            if domain is None:
                colors = [next(color_iter) for _ in result["levels"]["hue"]]
            else:
                palette = mpl.rcParams["axes.prop_cycle"].by_key()["color"]
                colors = [
                    palette[domain["offset"] + i]
                    for i in range(len(result["levels"]["hue"]))
                ]
            result["colors"] = {
                category_key(value): color
                for value, color in zip(result["levels"]["hue"], colors, strict=True)
            }
        else:
            result["cmap"] = _continuous_cmap(layer.cmap_kind)
    return result


def _mapped_style(values, config, mapping, *, glyphs=True):
    color = mapping["base"]
    if config.hue is not None:
        value = values["hue"]
        if config.hue_kind == "categorical":
            color = mapping["colors"][category_key(value)]
        else:
            bounds = mapping["bounds"]["hue"]
            fraction, _ = numeric_mapping(
                [value], bounds if bounds[0] != bounds[1] else None
            )
            color = mapping["cmap"](fraction[0])
    width = None
    if config.size is not None:
        value = values["size"]
        if config.size_kind == "numeric":
            bounds = mapping["bounds"]["size"]
            fractions, _ = numeric_mapping(
                [value], bounds if bounds[0] != bounds[1] else None
            )
        else:
            fractions = categorical_fractions([value], mapping["levels"]["size"])
        t = fractions[0]
        width = config.sizes[0] * (1 - t) + config.sizes[1] * t
    dash = marker = None
    if config.style is not None:
        selected = [category_key(value) for value in mapping["levels"]["style"]]
        index = selected.index(category_key(values["style"]))
        dash = (BOX_DASHES if config.dashes is None else config.dashes)[index]
        if glyphs:
            marker = config.markers[index]
    return color, width, dash, marker


def _raw_summary(values, layer, axis_log):
    data = np.log10(values) if axis_log else values
    whis = mpl.rcParams["boxplot.whiskers"] if layer.whis is None else layer.whis
    summary = boxplot_stats(data, whis=whis, bootstrap=None)[0]
    ci = box_config(layer).median_ci
    notches = bool(
        mpl.rcParams["boxplot.notch"] if layer.notch is None else layer.notch
    )
    if ci is not None:
        summary["med"] = float(_aggregate(data, "median"))
        if len(data) < 2:
            warnings.warn(
                "Median bootstrap CI omitted for a singleton box; observation retained",
                UserWarning,
                stacklevel=3,
            )
            notches = False
        else:
            config = StatSpec(
                estimator="median",
                errorbar="ci",
                level=ci.level,
                n_boot=ci.n_boot,
                seed=ci.seed,
            )
            estimates = _bootstrap_estimates(
                data, config, np.random.default_rng(ci.seed)
            )
            tail = (1 - ci.level / 100) / 2
            low, high = _linear_quantiles(estimates, [tail, 1 - tail])
            summary["cilo"], summary["cihi"] = float(low), float(high)
            notches = True
    means = (
        mpl.rcParams["boxplot.showmeans"]
        if layer.showmeans is None
        else layer.showmeans
    )
    fliers = (
        mpl.rcParams["boxplot.showfliers"]
        if layer.showfliers is None
        else layer.showfliers
    )
    return summary, notches, bool(means), bool(fliers)


def _supplied_summary(columns, row, layer, axis_log):
    config = box_config(layer).summary
    _category, value, _hue = distribution_channels(layer)
    summary = {"med": columns[value][row]}
    for role in ("q1", "q3", "whislo", "whishi", "mean", "cilo", "cihi", "fliers"):
        if role == "mean" and not layer.showmeans:
            continue
        if role in ("cilo", "cihi") and not layer.notch:
            continue
        if role == "fliers" and layer.showfliers is False:
            continue
        name = getattr(config, role)
        raw = None if name is None else columns[name][row]
        if raw is not None:
            summary[role] = raw
    if axis_log:
        summary = {
            role: np.log10(raw) if role == "fliers" else float(np.log10(raw))
            for role, raw in summary.items()
        }
    return (
        summary,
        bool(layer.notch),
        bool(layer.showmeans),
        layer.showfliers is not False and "fliers" in summary,
    )


def native_box_artists(ax, contexts, layer):
    """Create actual bxp components; the caller maps all geometry exactly once."""
    parameters = inspect.signature(ax.bxp).parameters
    bodies = []
    for context in contexts:
        common = {
            name: value
            for name, value in (
                ("linewidth", layer.line_width),
                ("linestyle", layer.line_style),
            )
            if value is not None
        }
        outline, lines, fliers = dict(common), dict(common), {}
        if layer.edge_color is not None:
            outline["edgecolor"] = layer.edge_color
            lines["color"] = layer.edge_color
            fliers["markeredgecolor"] = layer.edge_color
        if layer.marker is not None:
            fliers["marker"] = layer.marker
        if layer.marker_size is not None:
            fliers["markersize"] = layer.marker_size
        if context["marker"] is not None:
            fliers["marker"] = context["marker"]
        kwargs = {
            "positions": [context["position"]],
            "widths": [context["width"]],
            "patch_artist": True,
            "manage_ticks": False,
            "showbox": bool(mpl.rcParams["boxplot.showbox"]),
            "showcaps": bool(mpl.rcParams["boxplot.showcaps"]),
            "shownotches": context["notches"],
            "showmeans": context["means"],
            "showfliers": context["fliers"],
            "boxprops": outline,
            "whiskerprops": lines,
            "capprops": lines,
            "medianprops": lines,
            "flierprops": fliers,
        }
        kwargs["orientation" if "orientation" in parameters else "vert"] = (
            ("horizontal" if layer.orient == "h" else "vertical")
            if "orientation" in parameters
            else layer.orient != "h"
        )
        fraction = box_config(layer).cap_fraction
        if fraction is not None:
            kwargs["capwidths"] = [context["width"] * fraction]
            # Like an explicit cap component, requested cap geometry enables caps.
            kwargs["showcaps"] = True
        if isinstance(layer.semantics, SemanticSpec):
            # Every box semantic role owns an actual body appearance property.
            kwargs["showbox"] = True
        components = context["components"]
        if components is not None:
            if components.body is not None:
                kwargs["showbox"] = True
            if components.cap is not None:
                kwargs["showcaps"] = True
        parts = ax.bxp([context["stats"]], **kwargs)
        body = parts["boxes"][0] if parts["boxes"] else None
        if body is not None:
            if layer.href:
                from ._render import _set_url

                _set_url(body, layer.href)
            body.set_facecolor(context["color"])
            body.set_alpha(layer.alpha if layer.alpha < 1 else 0.6)
            if context["width_pt"] is not None:
                body.set_linewidth(context["width_pt"])
            if context["dash"] is not None:
                body.set_linestyle(context["dash"])
            body.set_hatch(context["hatch"])
        for role, key in (
            ("body", "boxes"),
            ("whisker", "whiskers"),
            ("cap", "caps"),
            ("median", "medians"),
            ("mean", "means"),
            ("flier", "fliers"),
        ):
            style = getattr(components, role) if components is not None else None
            for artist in parts[key]:
                apply_component_style(artist, style, body=role == "body")
                finalize_component_stroke(artist, body=role == "body")
        context["parts"] = parts
        if body is not None:
            bodies.append(body)
    return bodies


def _guides(ax, layer, mapping, contexts, columns, rows, domain):
    from ._render import _decorate

    config = layer.semantics
    if layer.label:
        _proxy(
            ax, contexts[0], layer, _decorate(layer.label, layer.citation, layer.href)
        )
    if not config.legend:
        return
    mapping_columns = columns if domain is None else domain["columns"]
    mapping_rows = rows if domain is None else domain["rows"]
    for role in ("hue", "size", "style"):
        name = getattr(config, role)
        if name is None or (
            role == "hue" and config.hue_kind == "numeric" and layer.colorbar
        ):
            continue
        kind = "categorical" if role == "style" else getattr(config, role + "_kind")
        if kind == "categorical":
            observed = {
                category_key(mapping_columns[name][row]) for row in mapping_rows
            }
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
            color = width = dash = marker = None
            if role == "hue":
                color = (
                    mapping["colors"][category_key(value)]
                    if kind == "categorical"
                    else mapping["cmap"](fraction)
                )
            elif role == "size":
                width = config.sizes[0] * (1 - fraction) + config.sizes[1] * fraction
            else:
                index = [category_key(v) for v in mapping["levels"][role]].index(
                    category_key(value)
                )
                dash = (BOX_DASHES if config.dashes is None else config.dashes)[index]
                marker = config.markers[index]
            unit = (
                " (body stroke pt)"
                if role == "size"
                else " (body dash / flier glyph)"
                if role == "style"
                else ""
            )
            handle = _proxy(
                ax,
                context,
                layer,
                f"{role}: {name}={value}{unit}",
                color=color,
                width=width,
                dash=dash,
                marker=marker,
            )
            from ._shared_guides import tag_entry

            tag_entry(ax, handle, layer, role, value)


def draw_boxes(ax, columns, layer, color_iter, theme, *, domain=None, guides=True):
    from ._render import (
        _category_geometry,
        _decorate,
        _distribution_artists,
        _finish_category_axis,
    )

    rows = box_rows(columns, layer)
    categories, groups, cells = distribution_plan(
        columns, layer, rows=rows, domain=domain
    )
    if not categories:
        return
    positions, spacing, labels = _category_geometry(ax, categories, layer)
    if not cells:
        if len(positions):
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
                reference.citation if reference is not None else None,
                reference.href if reference is not None else None,
            )
            for item in categories
            for reference in [(layer.references or {}).get(str(item))]
        ]
    if one_column and not layer.native_scale:
        ticks = ax.set_yticks if layer.orient == "h" else ax.set_xticks
        ticks(positions, labels=labels)
    width = layer.width
    if width is None:
        width = (
            float(np.clip(0.15 * np.ptp(positions), 0.15, 0.5))
            if one_column and not layer.native_scale
            else 0.8
        )
    if layer.native_scale:
        width *= spacing
    gap = 0 if layer.gap is None else layer.gap
    span = (
        (width if layer.dodge is None else layer.dodge * spacing)
        if (not one_column or layer.semantics is not None)
        else 0
    )
    dodged = len(groups) > 1 and span != 0
    body_width = width / len(groups) if dodged else width
    body_width *= 1 - gap
    category_indices: dict[object, int] = {
        None if c is None else category_key(c): i for i, c in enumerate(categories)
    }
    group_indices = {group["key"]: i for i, group in enumerate(groups)}
    config = layer.semantics
    mapping = (
        _semantic_mapping(columns, layer, rows, domain, color_iter)
        if isinstance(config, SemanticSpec)
        else None
    )
    colors = (
        [
            layer.color or next(color_iter)
            for _ in (categories if one_column else groups)
        ]
        if mapping is None
        else None
    )
    axis_log = (
        layer.stat_scale == "axis"
        and (ax.get_xscale() if layer.orient == "h" else ax.get_yscale()) == "log"
    )
    contexts = []
    for cell in cells:
        ci = category_indices[
            None if cell["category"] is None else category_key(cell["category"])
        ]
        gi = group_indices[cell["group"]]
        center = positions[ci] + (
            (gi - (len(groups) - 1) / 2) * span / len(groups) if dodged else 0
        )
        if box_config(layer).summary is not None:
            stats, notches, means, fliers = _supplied_summary(
                columns, cell["rows"][0], layer, axis_log
            )
        else:
            values = np.asarray(
                [columns[value][row] for row in cell["rows"]], dtype=float
            )
            stats, notches, means, fliers = _raw_summary(values, layer, axis_log)
        if mapping is None:
            assert colors is not None
            color, width_pt, dash, marker = (
                colors[ci if one_column else gi],
                None,
                None,
                None,
            )
        else:
            color, width_pt, dash, marker = _mapped_style(
                cell["roles"], config, mapping
            )
        style_index = ci if one_column else gi
        hatch = (
            theme.hatches[style_index % len(theme.hatches)]
            if theme.redundant_encoding
            and len(categories if one_column else groups) > 1
            else None
        )
        contexts.append(
            {
                **cell,
                "stats": stats,
                "notches": notches,
                "means": means,
                "fliers": fliers,
                "position": center,
                "width": body_width,
                "components": merged_components(layer, cell["hue"]),
                "color": color,
                "width_pt": width_pt,
                "dash": dash,
                "marker": marker,
                "hatch": hatch,
            }
        )
    _distribution_artists(ax, (), (), None, (), layer, box_context=contexts)
    _finish_category_axis(ax, positions, spacing, labels, layer)
    if one_column and not layer.native_scale:
        low, high = positions.min() - 0.5, positions.max() + 0.5
        (ax.set_ylim if layer.orient == "h" else ax.set_xlim)(low, high)
    if mapping is not None:
        if "hue" in mapping["bounds"]:
            draw_semantic_colourbar(
                ax, layer, mapping["bounds"]["hue"], mapping["cmap"]
            )
        if guides:
            _guides(ax, layer, mapping, contexts, columns, rows, domain)
    elif layer.y:
        seen = set()
        for context in contexts:
            key = None if context["hue"] is None else category_key(context["hue"])
            if key in seen:
                continue
            seen.add(key)
            reference = (layer.references or {}).get(str(context["hue"]))
            label = (
                _decorate(layer.label, layer.citation, layer.href)
                if hue is None
                else _decorate(
                    str(context["hue"]),
                    reference.citation if reference is not None else None,
                    reference.href if reference is not None else None,
                )
            )
            if label:
                _proxy(ax, context, layer, label)
