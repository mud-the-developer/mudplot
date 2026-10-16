"""Native numeric-x estimates and pointwise ranges, not simultaneous bands.

Rendering only: shared estimators/bootstrap contracts remain in _estimate.
"""

from __future__ import annotations

import warnings

import numpy as np

from ._estimate import summarize
from ._stat import stat_config, usable_rows


def draw_lineplot(ax, columns, layer, color_iter, theme, *, curve_styles=None):
    # Import native reference/range helpers only at the effect boundary.
    from ._render import _decorate, _draw_stat_ranges

    horizontal = layer.orient == "h"
    scale = ax.get_xscale() if horizontal else ax.get_yscale()
    summary = summarize(columns, layer, value_scale=scale)
    config = stat_config(layer)
    rows = usable_rows(columns, layer)
    if config.errorbar is not None and any(p.lower is None for p in summary.estimates):
        warnings.warn(
            "lineplot pointwise intervals omitted for cells with fewer than 2 "
            "observations or independent resampling units",
            UserWarning,
            stacklevel=2,
        )
    contexts = []
    for index, group in enumerate(summary.groups):
        points = [p for p in summary.estimates if p.group == group]
        color = (
            (layer.color or next(color_iter))
            if curve_styles is None
            else curve_styles[group]["color"]
        )
        if not points:
            continue  # Consume reserved hue slot; no fictional curve or legend.
        if layer.sort:
            points.sort(key=lambda point: float(point.category))
        else:
            order = dict.fromkeys(
                columns[layer.x][row]
                for row in rows
                if layer.group is None or columns[layer.group][row] == group
            )
            ranks = {value: i for i, value in enumerate(order)}
            points.sort(key=lambda point: ranks[point.category])
        x = np.asarray([point.category for point in points], dtype=float)
        y = np.asarray([point.value for point in points])
        valid = np.asarray([point.lower is not None for point in points])
        lower = np.asarray([np.nan if p.lower is None else p.lower for p in points])
        upper = np.asarray([np.nan if p.upper is None else p.upper for p in points])
        style = "band" if layer.error_style is None else layer.error_style
        if (
            style == "band"
            and valid.any()
            and not (len(x) < 2 or (np.diff(x) > 0).all() or (np.diff(x) < 0).all())
        ):
            raise ValueError(
                "lineplot bands need monotonic x; use sort=True or error_style='bars'"
            )
        contexts.append((index, group, x, y, valid, lower, upper, color, style))
    # All derived statistics/band ordering are checked before native artists.
    for index, group, x, y, valid, lower, upper, color, style in contexts:
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
        line_style = layer.line_style or (
            theme.line_styles[index % len(theme.line_styles)] if redundant else "-"
        )
        width = 1.25 if layer.line_width is None else layer.line_width
        marker = "None" if layer.marker is None else layer.marker
        if curve_styles is not None:
            mapped = curve_styles[group]
            color, width = mapped["color"], mapped["width"]
            marker, line_style = mapped["marker"], mapped["dash"]
            label = "_nolegend_"
        ax.plot(
            *((y, x) if horizontal else (x, y)),
            color=color,
            label=label,
            marker=marker,
            markersize=5 if layer.marker_size is None else layer.marker_size,
            linewidth=width,
            linestyle="None" if width == 0 else line_style,
            alpha=layer.alpha,
        )
        if not valid.any():
            continue
        error_color = layer.error_color or color
        if style == "bars":
            _draw_stat_ranges(
                ax, x[valid], lower[valid], upper[valid], layer, error_color
            )
        else:
            draw = ax.fill_betweenx if horizontal else ax.fill_between
            draw(
                x,
                lower,
                upper,
                where=valid,
                color=error_color,
                alpha=0.2 * layer.alpha
                if layer.error_alpha is None
                else layer.error_alpha,
                linewidth=0,
                label="_nolegend_",
            )
