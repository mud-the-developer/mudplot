"""Native supplied curves and estimated lines with explicit missing topology.

Statistical arithmetic stays in _estimate and complete-unit _line_inference.
"""

from __future__ import annotations

import itertools
import warnings

import numpy as np

from ._ecdf import finite_number
from ._estimate import summarize
from ._line import categorical_predictor, line_rows
from ._semantics import category_key, levels
from ._stat import explicit_line_inference, stat_config, stat_key


def draw_lineplot(
    ax, columns, layer, color_iter, theme, *, curve_styles=None, prepared=None
):
    from ._render import _category_geometry, _decorate, _draw_stat_ranges

    horizontal = layer.orient == "h"
    scale = ax.get_xscale() if horizontal else ax.get_yscale()
    if prepared is None and explicit_line_inference(layer):
        raise ValueError("NEW line inference must be prepared before native creation")
    summary = (
        summarize(columns, layer, value_scale=scale)
        if prepared is None
        else prepared.summary
    )
    config = stat_config(layer)
    identity = stat_key if summary.typed else lambda value: value
    topology = line_rows(columns, layer, topology=True) if prepared is None else ()
    if prepared is None and not categorical_predictor(layer):
        topology = [row for row in topology if finite_number(columns[layer.x][row])]
    categorical = categorical_predictor(layer)
    categories = (
        list(layer.order)
        if layer.order is not None
        else levels(columns[layer.x][row] for row in topology)
        if categorical and prepared is None
        else summary.categories
    )
    locations = None
    if categorical and categories:
        positions, _spacing, _labels = _category_geometry(ax, categories, layer)
        locations = {
            category_key(value): position
            for value, position in zip(categories, positions, strict=True)
        }
    if config.errorbar is not None and any(p.lower is None for p in summary.estimates):
        warnings.warn(
            "lineplot pointwise intervals omitted for cells with fewer than 2 "
            "observations or independent resampling units",
            UserWarning,
            stacklevel=2,
        )
    contexts = []
    for index, group in enumerate(summary.groups):
        points = [p for p in summary.estimates if identity(p.group) == identity(group)]
        if not points:
            if curve_styles is None and layer.color is None:
                next(color_iter)  # Reserved slot, not a fictional curve/guide.
            continue
        color = (
            layer.color or next(color_iter)
            if curve_styles is None
            else curve_styles[group]["color"]
        )
        if prepared is None:
            selected = [
                row
                for row in topology
                if layer.group is None
                or identity(columns[layer.group][row]) == identity(group)
            ]
            grid = list(dict.fromkeys(columns[layer.x][row] for row in selected))
            if categorical:
                grid = categories
            elif layer.order is not None:
                observed = {identity(value) for value in grid}
                grid.extend(
                    value for value in layer.order if identity(value) not in observed
                )
        else:
            grid = list(prepared.grids[stat_key(group)])
        if not categorical and layer.sort:
            grid.sort(key=float)
        by_category = {identity(point.category): point for point in points}
        ordered = [by_category.get(identity(value)) for value in grid]
        if categorical:
            assert locations is not None
            displayed = [locations[category_key(value)] for value in grid]
        else:
            displayed = grid
        x = np.asarray(
            displayed,
            dtype=float,
        )
        y = np.asarray([np.nan if point is None else point.value for point in ordered])
        valid = np.asarray(
            [point is not None and point.lower is not None for point in ordered]
        )
        lower = np.asarray(
            [
                np.nan if point is None or point.lower is None else point.lower
                for point in ordered
            ]
        )
        upper = np.asarray(
            [
                np.nan if point is None or point.upper is None else point.upper
                for point in ordered
            ]
        )
        style = layer.error_style or "band"
        if (
            style == "band"
            and valid.any()
            and not (len(x) < 2 or (np.diff(x) > 0).all() or (np.diff(x) < 0).all())
        ):
            raise ValueError(
                "lineplot bands need monotonic x; use sort=True or error_style='bars'"
            )
        contexts.append((index, group, grid, x, y, valid, lower, upper, color, style))
    for index, group, grid, x, y, valid, lower, upper, color, style in contexts:
        reference = (layer.references or {}).get(str(group))
        label = (
            _decorate(layer.label, layer.citation, layer.href)
            if layer.group is None
            else _decorate(
                str(group),
                reference.citation if reference else None,
                reference.href if reference else None,
            )
        )
        redundant = theme.redundant_encoding and layer.group is not None
        dash = layer.line_style or (
            theme.line_styles[index % len(theme.line_styles)] if redundant else "-"
        )
        width = 1.25 if layer.line_width is None else layer.line_width
        marker = "None" if layer.marker is None else layer.marker
        marker_size = 5 if layer.marker_size is None else layer.marker_size
        mapped = None if curve_styles is None else curve_styles[group]
        if mapped is not None:
            color, width = mapped["color"], mapped["width"]
            marker, dash = mapped["marker"], mapped["dash"]
            marker_size = mapped["marker_size"]
            label = "_nolegend_"
        artist = ax.plot(
            *((y, x) if horizontal else (x, y)),
            color=color,
            label=label,
            marker=marker,
            markersize=marker_size,
            linewidth=width,
            linestyle="None" if width == 0 else dash,
            alpha=layer.alpha,
        )[0]
        if mapped is not None:
            mapped["artist"] = artist
        if prepared is not None:
            artist._mudplot_source_rows = tuple(
                prepared.point_rows.get((stat_key(group), category_key(value)), ())
                for value in grid
            )
        if not valid.any():
            continue
        if style == "bars":
            _draw_stat_ranges(
                ax,
                x[valid],
                lower[valid],
                upper[valid],
                layer,
                layer.error_color or color,
            )
        else:
            draw = ax.fill_betweenx if horizontal else ax.fill_between
            draw(
                x,
                lower,
                upper,
                where=valid,
                color=layer.error_color or color,
                alpha=0.2 * layer.alpha
                if layer.error_alpha is None
                else layer.error_alpha,
                linewidth=0,
                label="_nolegend_",
            )
    if prepared is not None and prepared.caption:
        title_axes = getattr(ax, "_mudplot_semantic_guide_axis", ax)
        captions = getattr(title_axes, "_mudplot_inference_captions", [])
        captions.append(prepared.caption)
        title_axes._mudplot_inference_captions = captions


def draw_raw_lines(
    ax, columns, layer, color_iter, theme, *, curve_styles=None, source_rows=None
):
    """Map supplied rows, with no estimator, sorting or duplicate removal."""
    from ._render import _col, _series_masks, _x_values

    horizontal = layer.orient == "h"
    selected = line_rows(columns, layer, topology=True, barriers=True)
    names = [layer.x, layer.y] + ([layer.group] if layer.group is not None else [])
    data = {name: [columns[name][row] for row in selected] for name in names}
    original = (
        getattr(ax, "_mudplot_source_rows", range(len(columns[layer.x])))
        if source_rows is None
        else source_rows
    )
    source_ids = [original[row] for row in selected]
    if categorical_predictor(layer):
        from ._render import _category_geometry

        categories = (
            list(layer.order)
            if layer.order is not None
            else levels(value for value in data[layer.x] if value is not None)
        )
        if not categories:
            return
        positions, _spacing, _labels = _category_geometry(ax, categories, layer)
        lookup = {
            category_key(value): position
            for value, position in zip(categories, positions, strict=True)
        }
        x = np.asarray(
            [
                np.nan if value is None else lookup[category_key(value)]
                for value in data[layer.x]
            ]
        )
    else:
        x = _x_values(ax, data, layer.x, horizontal=horizontal)
    y = _col(data, layer.y)
    if curve_styles is None:
        masks = list(_series_masks(data, layer))
        if layer.hue_order is None:
            masks = [
                (label, mask)
                for label, mask in masks
                if np.any(np.isfinite(x[mask]) & np.isfinite(y[mask]))
            ]
        redundant = theme.redundant_encoding and layer.group is not None
        markers = (
            itertools.cycle(theme.markers) if redundant else itertools.repeat(None)
        )
        dashes = (
            itertools.cycle(theme.line_styles) if redundant else itertools.repeat("-")
        )
        contexts = []
        for label, mask in masks:
            marker = next(markers) if layer.marker is None else layer.marker
            dash = next(dashes) if layer.line_style is None else layer.line_style
            color = layer.color or next(color_iter)
            if not np.any(np.isfinite(x[mask]) & np.isfinite(y[mask])):
                continue
            contexts.append(
                (
                    mask,
                    label,
                    color,
                    layer.line_width,
                    marker,
                    dash,
                    layer.marker_size,
                    None,
                )
            )
    else:
        identifiers = np.asarray(data[layer.group])
        contexts = []
        for identifier, mapped in curve_styles.items():
            mask = (identifiers == identifier) | (identifiers == -1)
            if not np.any(
                (identifiers == identifier) & np.isfinite(x) & np.isfinite(y)
            ):
                continue
            contexts.append(
                (
                    mask,
                    "_nolegend_",
                    mapped["color"],
                    mapped["width"],
                    mapped["marker"],
                    mapped["dash"],
                    mapped["marker_size"],
                    mapped,
                )
            )
    for mask, label, color, width, marker, dash, marker_size, mapped in contexts:
        predictor, response = x[mask], y[mask].copy()
        if curve_styles is not None:
            response[np.asarray(data[layer.group])[mask] == -1] = np.nan
        artist = ax.plot(
            *((response, predictor) if horizontal else (predictor, response)),
            label=label,
            color=color,
            linewidth=width,
            linestyle="None" if width == 0 else dash,
            drawstyle=layer.drawstyle,
            marker=marker,
            markersize=marker_size,
            alpha=layer.alpha,
        )[0]
        artist._mudplot_source_rows = tuple(
            source_ids[index] for index in np.flatnonzero(mask)
        )
        if mapped is not None:
            mapped["artist"] = artist
