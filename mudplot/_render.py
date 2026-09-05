"""Render a FigureSpec into a matplotlib Figure.

Pure-ish function: given the same spec it produces the same figure. All
matplotlib-specific logic lives here; the spec itself stays backend-agnostic.
"""

from __future__ import annotations

import itertools

import numpy as np

from .spec import FigureSpec, LayerSpec, PanelSpec
from .theme import spec_to_rcparams
from .validate import assert_valid

__all__ = ["render", "save"]

# layer types that draw one or more x/y series (and support ``group``)
_SERIES_TYPES = {"line", "scatter", "bar", "errorbar", "band"}
# layer types that draw a distribution of a single column (support ``group``)
_DIST_TYPES = {"hist", "box", "violin", "kde"}
# layer types that draw a 2-D matrix
_MATRIX_TYPES = {"heatmap", "contour", "contourf"}
# layer types only meaningful on a projection="3d" panel
_3D_TYPES = {"scatter3d", "line3d", "surface", "wireframe"}
# layer types with their own standalone drawing logic
_STANDALONE_TYPES = {"pie"}

_OUTSIDE_LEGEND_LOCS = {
    "outside right": {"loc": "center left", "bbox_to_anchor": (1.02, 0.5)},
    "outside top": {"loc": "lower center", "bbox_to_anchor": (0.5, 1.02), "ncol": 99},
    "outside bottom": {"loc": "upper center", "bbox_to_anchor": (0.5, -0.18)},
}

_SPINE_SIDES = {"L": "left", "R": "right", "T": "top", "B": "bottom"}


def _unique_stable(arr):
    seen = []
    for v in arr:
        if v not in seen:
            seen.append(v)
    return seen


def _col(data_cols, name):
    return np.asarray(data_cols[name], dtype=float)


def _x_values(ax, data_cols, name):
    """x-column values as plot-ready numeric positions.

    Numeric columns pass through unchanged. Categorical columns are mapped
    to evenly-spaced positions in first-seen order with automatic tick labels.

    Use Matplotlib's category registry so layers, twins and shared axes
    agree on the position of each category.
    """
    raw = data_cols[name]
    try:
        return np.asarray(raw, dtype=float)
    except (ValueError, TypeError):
        str_values = [str(v) for v in raw]
        ax.xaxis.update_units(str_values)
        return np.asarray(ax.convert_xunits(str_values), dtype=float)


def _series_masks(data_cols, layer: LayerSpec):
    """Yield (label, boolean-mask) for a layer, splitting by ``group``."""
    n = len(data_cols[layer.x])
    if layer.group is None:
        yield (layer.label, np.ones(n, dtype=bool))
        return
    g = np.asarray(data_cols[layer.group])
    for key in _unique_stable(g):
        yield (str(key), g == key)


def _continuous_cmap(kind: str):
    """A matplotlib Colormap built from our LCH sequential/diverging palettes."""
    from .color import palette as P

    pal = P.diverging(256) if kind == "diverging" else P.sequential(256)
    return pal.to_cmap()


def _color_norm(data_cols, layer):
    from matplotlib.colors import Normalize

    norm = Normalize()
    norm.autoscale(np.ma.masked_invalid(_col(data_cols, layer.c)))
    return norm


def _target_axes(ax, ax2, layer: LayerSpec):
    return ax2 if (layer.axis == "y2" and ax2 is not None) else ax


def _draw_series_layer(ax, ax2, data_cols, layer: LayerSpec, color_iter, theme):
    masks = list(_series_masks(data_cols, layer))
    # redundant marker/line-style encoding: only kicks in for *grouped*
    # (multi-series) layers, so a single clean line/scatter stays untouched.
    use_redundant = theme.redundant_encoding and layer.group is not None
    marker_cycle = (
        itertools.cycle(theme.markers) if use_redundant else itertools.repeat(None)
    )
    style_cycle = (
        itertools.cycle(theme.line_styles) if use_redundant else itertools.repeat("-")
    )
    hatch_cycle = (
        itertools.cycle(theme.hatches) if use_redundant else itertools.repeat(None)
    )
    target = _target_axes(ax, ax2, layer)
    n_series = len(masks)

    x_all = _x_values(target, data_cols, layer.x)
    norm = _color_norm(data_cols, layer) if layer.c is not None else None
    sc = None

    for series_i, (label, mask) in enumerate(masks):
        x = x_all[mask]
        y = _col(data_cols, layer.y)[mask]
        marker = layer.marker or next(marker_cycle)
        linestyle = layer.line_style or next(style_cycle)
        if layer.type == "line":
            color = layer.color or next(color_iter)
            target.plot(
                x,
                y,
                label=label,
                color=color,
                linewidth=layer.line_width,
                linestyle=linestyle,
                marker=marker,
                markersize=layer.marker_size,
                alpha=layer.alpha,
            )
        elif layer.type == "scatter":
            if layer.c is not None:
                values = _col(data_cols, layer.c)[mask]
                sc = target.scatter(
                    x,
                    y,
                    c=values,
                    cmap=_continuous_cmap(layer.cmap_kind),
                    norm=norm,
                    label=label,
                    s=(layer.marker_size or 6) ** 2,
                    marker=marker or "o",
                    alpha=layer.alpha,
                )
            else:
                color = layer.color or next(color_iter)
                target.scatter(
                    x,
                    y,
                    label=label,
                    color=color,
                    s=(layer.marker_size or 6) ** 2,
                    marker=marker or "o",
                    alpha=layer.alpha,
                )
        elif layer.type == "bar":
            color = layer.color or next(color_iter)
            hatch = next(hatch_cycle)
            if n_series > 1:
                # Dodge grouped bars side-by-side instead of stacking them
                # on top of each other at identical x positions -- plain
                # ax.bar() calls at the same x would silently overlap
                # (hiding shorter bars behind taller ones), which is a
                # correctness/readability problem for grouped bar charts,
                # not just cosmetic.
                bar_w = 0.8 / n_series
                offset = (series_i - (n_series - 1) / 2) * bar_w
                target.bar(
                    x + offset,
                    y,
                    width=bar_w * 0.92,
                    label=label,
                    color=color,
                    hatch=hatch,
                    alpha=layer.alpha,
                )
            else:
                target.bar(x, y, label=label, color=color, alpha=layer.alpha)
        elif layer.type == "errorbar":
            color = layer.color or next(color_iter)
            yerr = _col(data_cols, layer.yerr)[mask] if layer.yerr else None
            xerr = _col(data_cols, layer.xerr)[mask] if layer.xerr else None
            target.errorbar(
                x,
                y,
                yerr=yerr,
                xerr=xerr,
                label=label,
                color=color,
                fmt=marker or "o",
                markersize=layer.marker_size or 4,
                linewidth=layer.line_width,
                capsize=layer.capsize or 2,
                alpha=layer.alpha,
            )
        elif layer.type == "band":
            color = layer.color or next(color_iter)
            lower = _col(data_cols, layer.y2)[mask] if layer.y2 else y
            target.fill_between(
                x,
                lower,
                y,
                label=label,
                color=color,
                alpha=layer.alpha if layer.alpha < 1 else 0.25,
                linewidth=0,
            )

    if sc is not None and layer.colorbar:
        target.figure.colorbar(sc, ax=target, label=layer.clabel or "")


def _gaussian_kde(values: np.ndarray, n_points: int = 200):
    """A small numpy-only Gaussian KDE (Scott's rule bandwidth).

    Avoids adding scipy as a dependency for one feature; not as fast or
    feature-complete as scipy.stats.gaussian_kde, but numerically
    equivalent for the common case (no weights, Gaussian kernel).
    """
    values = np.asarray(values, dtype=float)
    n = len(values)
    std = values.std(ddof=1) if n > 1 else 1.0
    bandwidth = 1.06 * std * n ** (-1 / 5) if std > 0 else 1.0
    lo, hi = values.min() - 3 * bandwidth, values.max() + 3 * bandwidth
    grid = np.linspace(lo, hi, n_points)
    # sum of Gaussian kernels centred at each sample, evaluated on the grid
    diffs = (grid[:, None] - values[None, :]) / bandwidth
    density = np.exp(-0.5 * diffs**2).sum(axis=1) / (n * bandwidth * np.sqrt(2 * np.pi))
    return grid, density


def _draw_dist_layer(ax, data_cols, layer: LayerSpec, color_iter, theme):
    masks = list(_series_masks(data_cols, layer))
    # Same rationale as the marker/line-style cycle in _draw_series_layer:
    # a hatch pattern per series keeps grouped fills (bar-like area charts)
    # distinguishable in black & white print or full achromatopsia, where
    # colour alone (even equal-lightness colour) carries no information.
    use_redundant = theme.redundant_encoding and len(masks) > 1
    hatch_cycle = (
        itertools.cycle(theme.hatches) if use_redundant else itertools.repeat(None)
    )
    if layer.type == "hist":
        for label, mask in masks:
            values = _col(data_cols, layer.x)[mask]
            ax.hist(
                values,
                bins=layer.bins,
                density=layer.density,
                label=label,
                color=layer.color or next(color_iter),
                hatch=next(hatch_cycle),
                alpha=layer.alpha if layer.alpha < 1 else 0.6,
            )
    elif layer.type == "box":
        values = [_col(data_cols, layer.x)[mask] for _label, mask in masks]
        labels = [label for label, _mask in masks]
        try:  # matplotlib >= 3.9
            bp = ax.boxplot(values, tick_labels=labels, patch_artist=True)
        except TypeError:  # matplotlib < 3.9
            bp = ax.boxplot(values, labels=labels, patch_artist=True)
        for patch in bp["boxes"]:
            patch.set_facecolor(layer.color or next(color_iter))
            patch.set_hatch(next(hatch_cycle))
            patch.set_alpha(layer.alpha if layer.alpha < 1 else 0.6)
    elif layer.type == "violin":
        values = [_col(data_cols, layer.x)[mask] for _label, mask in masks]
        labels = [label for label, _mask in masks]
        positions = range(1, len(values) + 1)
        parts = ax.violinplot(values, positions=positions, showmedians=True)
        for body in parts["bodies"]:
            body.set_facecolor(layer.color or next(color_iter))
            body.set_hatch(next(hatch_cycle))
            body.set_alpha(layer.alpha if layer.alpha < 1 else 0.6)
        ax.set_xticks(list(positions))
        ax.set_xticklabels(labels)
    elif layer.type == "kde":
        for label, mask in masks:
            values = _col(data_cols, layer.x)[mask]
            grid, density = _gaussian_kde(values)
            ax.plot(
                grid,
                density,
                label=label,
                color=layer.color or next(color_iter),
                linewidth=layer.line_width,
                linestyle=layer.line_style or "-",
                alpha=layer.alpha,
            )


def _draw_matrix_layer(ax, spec: FigureSpec, layer: LayerSpec):
    matrix = np.asarray(spec.data.matrices[layer.matrix], dtype=float)
    cmap = _continuous_cmap(layer.cmap_kind)
    if layer.type == "heatmap":
        im = ax.imshow(matrix, aspect="auto", cmap=cmap, alpha=layer.alpha)
    elif layer.type == "contour":
        im = ax.contour(matrix, levels=layer.levels or 8, cmap=cmap, alpha=layer.alpha)
    elif layer.type == "contourf":
        im = ax.contourf(matrix, levels=layer.levels or 8, cmap=cmap, alpha=layer.alpha)
    else:
        raise ValueError(f"unknown matrix layer type: {layer.type!r}")
    if layer.colorbar:
        ax.figure.colorbar(im, ax=ax, label=layer.clabel or "")


def _draw_pie_layer(ax, data_cols, layer: LayerSpec, color_iter):
    values = _col(data_cols, layer.y)
    raw_labels = data_cols[layer.x]
    labels = [str(v) for v in raw_labels]
    colors = (
        [layer.color] * len(values)
        if layer.color
        else [next(color_iter) for _ in values]
    )
    wedges, _texts = ax.pie(
        values, labels=labels, colors=colors, wedgeprops={"alpha": layer.alpha}
    )
    # ax.pie() sets each wedge's legend label to the slice label too, so the
    # generic "draw a legend if there are any labelled handles" logic in
    # _draw_panel would add a second, redundant legend on top of the
    # on-wedge labels already drawn above. Pie charts conventionally use
    # one or the other, not both -- suppress the legend-registration half.
    for wedge in wedges:
        wedge.set_label("_nolegend_")
    ax.set_aspect("equal")


def _draw_marker_layer(ax, ax2, layer: LayerSpec, color_iter):
    # hline/vline/text/annotate can also target the secondary y-axis (e.g. a
    # threshold line drawn against the y2 scale) -- route consistently with
    # the series layers instead of silently always drawing on the primary
    # axis regardless of ``layer.axis``.
    target = _target_axes(ax, ax2, layer)
    color = layer.color or next(color_iter)
    if layer.type == "hline":
        target.axhline(
            layer.value,
            label=layer.label,
            color=color,
            linestyle=layer.line_style or "--",
            linewidth=layer.line_width,
            alpha=layer.alpha,
        )
    elif layer.type == "vline":
        target.axvline(
            layer.value,
            label=layer.label,
            color=color,
            linestyle=layer.line_style or "--",
            linewidth=layer.line_width,
            alpha=layer.alpha,
        )
    elif layer.type == "text":
        target.text(
            layer.at[0], layer.at[1], layer.text or "", color=color, alpha=layer.alpha
        )
    elif layer.type == "annotate":
        target.annotate(
            layer.text or "",
            xy=tuple(layer.to or layer.at),
            xytext=tuple(layer.at),
            color=color,
            arrowprops={"arrowstyle": "->", "color": color} if layer.to else None,
        )
    else:
        raise ValueError(f"unknown layer type: {layer.type!r}")


def _draw_3d_layer(ax, spec: FigureSpec, layer: LayerSpec, color_iter):
    data_cols = spec.data.columns
    if layer.type in ("scatter3d", "line3d"):
        masks = list(_series_masks(data_cols, layer))
        norm = _color_norm(data_cols, layer) if layer.c is not None else None
        sc = None
        for label, mask in masks:
            x = _col(data_cols, layer.x)[mask]
            y = _col(data_cols, layer.y)[mask]
            z = _col(data_cols, layer.z)[mask]
            if layer.type == "scatter3d":
                if layer.c is not None:
                    values = _col(data_cols, layer.c)[mask]
                    sc = ax.scatter(
                        x,
                        y,
                        z,
                        c=values,
                        cmap=_continuous_cmap(layer.cmap_kind),
                        norm=norm,
                        label=label,
                        s=(layer.marker_size or 6) ** 2,
                        marker=layer.marker or "o",
                        alpha=layer.alpha,
                    )
                else:
                    color = layer.color or next(color_iter)
                    ax.scatter(
                        x,
                        y,
                        z,
                        label=label,
                        color=color,
                        s=(layer.marker_size or 6) ** 2,
                        marker=layer.marker or "o",
                        alpha=layer.alpha,
                    )
            else:  # line3d
                color = layer.color or next(color_iter)
                ax.plot(
                    x,
                    y,
                    z,
                    label=label,
                    color=color,
                    linewidth=layer.line_width,
                    linestyle=layer.line_style or "-",
                    marker=layer.marker,
                    alpha=layer.alpha,
                )
        if sc is not None and layer.colorbar:
            ax.figure.colorbar(sc, ax=ax, label=layer.clabel or "")
    elif layer.type in ("surface", "wireframe"):
        matrix = np.asarray(spec.data.matrices[layer.matrix], dtype=float)
        ny, nx = matrix.shape
        xs, ys = np.meshgrid(np.arange(nx), np.arange(ny))
        if layer.type == "surface":
            surf = ax.plot_surface(
                xs,
                ys,
                matrix,
                cmap=_continuous_cmap(layer.cmap_kind),
                alpha=layer.alpha,
            )
            if layer.colorbar:
                ax.figure.colorbar(surf, ax=ax, label=layer.clabel or "")
        else:
            color = layer.color or next(color_iter)
            ax.plot_wireframe(xs, ys, matrix, color=color, alpha=layer.alpha)


def _apply_axis(ax, axis_spec, set_label, set_scale, set_limits):
    set_label(axis_spec.label)
    # Setting even the existing linear scale resets categorical tick locators.
    if axis_spec.scale != "linear":
        set_scale(axis_spec.scale)
    if axis_spec.limits:
        set_limits(axis_spec.limits)


def _legend_kwargs(leg, *, ax2_present: bool, fig) -> dict:
    """Build ax.legend() placement kwargs, honouring a dragged/explicit
    ``bbox_to_anchor`` override in figure-fraction coordinates (independent
    of the axes' own position, so it stays put if the axes later resize).

    Returns ``(kwargs, auto_margin)``: ``auto_margin`` tells the caller
    whether ``_autofit`` should reserve canvas space for this legend. An
    explicit ``bbox_to_anchor`` (e.g. dragged in the interactive editor) is
    trusted as-is -- the user may deliberately want it overlapping the plot
    -- so only the named "outside ..." locations get automatic margin.
    """
    if leg.bbox_to_anchor is not None:
        return {
            "loc": "center",
            "bbox_to_anchor": tuple(leg.bbox_to_anchor),
            "bbox_transform": fig.transFigure,
        }, False
    kw = dict(_OUTSIDE_LEGEND_LOCS.get(leg.location, {"loc": leg.location}))
    if leg.location == "outside right" and ax2_present:
        # leave room for the secondary axis's own ticks/label
        kw["bbox_to_anchor"] = (1.35, 0.5)
    return kw, leg.location in _OUTSIDE_LEGEND_LOCS


def _apply_despine(ax, theme_axes):
    for char, side in _SPINE_SIDES.items():
        if char in theme_axes.spines and theme_axes.spine_offset:
            ax.spines[side].set_position(("outward", theme_axes.spine_offset))


def _draw_panel_3d(ax, spec: FigureSpec, panel: PanelSpec):
    import matplotlib.pyplot as plt

    prop = plt.rcParams["axes.prop_cycle"].by_key().get("color", ["C0"])
    color_iter = itertools.cycle(prop)

    for layer in panel.layers:
        _draw_3d_layer(ax, spec, layer, color_iter)

    _apply_axis(ax, panel.x, ax.set_xlabel, ax.set_xscale, ax.set_xlim)
    _apply_axis(ax, panel.y, ax.set_ylabel, ax.set_yscale, ax.set_ylim)
    if panel.z is not None:
        _apply_axis(ax, panel.z, ax.set_zlabel, ax.set_zscale, ax.set_zlim)
    if panel.title:
        ax.set_title(panel.title, wrap=True)

    handles, labels = ax.get_legend_handles_labels()
    leg = panel.legend
    if leg.show and handles:
        kw, auto_margin = _legend_kwargs(leg, ax2_present=False, fig=ax.figure)
        legend_artist = ax.legend(
            handles, labels, title=leg.title, frameon=leg.frame, **kw
        )
        legend_artist._mudplot_auto_margin = auto_margin


def _draw_panel(ax, spec: FigureSpec, panel: PanelSpec):
    import matplotlib.pyplot as plt

    if panel.projection == "3d":
        _draw_panel_3d(ax, spec, panel)
        return

    prop = plt.rcParams["axes.prop_cycle"].by_key().get("color", ["C0"])
    color_iter = itertools.cycle(prop)
    theme = spec.theme

    ax2 = ax.twinx() if panel.y2 is not None else None

    for layer in panel.layers:
        if layer.type in _SERIES_TYPES:
            _draw_series_layer(ax, ax2, spec.data.columns, layer, color_iter, theme)
        elif layer.type in _DIST_TYPES:
            _draw_dist_layer(ax, spec.data.columns, layer, color_iter, theme)
        elif layer.type in _MATRIX_TYPES:
            _draw_matrix_layer(ax, spec, layer)
        elif layer.type in _STANDALONE_TYPES:
            _draw_pie_layer(ax, spec.data.columns, layer, color_iter)
        else:
            _draw_marker_layer(ax, ax2, layer, color_iter)

    _apply_axis(ax, panel.x, ax.set_xlabel, ax.set_xscale, ax.set_xlim)
    _apply_axis(ax, panel.y, ax.set_ylabel, ax.set_yscale, ax.set_ylim)
    if panel.y2 is not None:
        _apply_axis(ax2, panel.y2, ax2.set_ylabel, ax2.set_yscale, ax2.set_ylim)
    if panel.title:
        ax.set_title(panel.title, wrap=True)
    _apply_despine(ax, theme.axes)

    handles, labels = ax.get_legend_handles_labels()
    if ax2 is not None:
        h2, l2 = ax2.get_legend_handles_labels()
        handles, labels = handles + h2, labels + l2
    leg = panel.legend
    if leg.show and handles:
        kw, auto_margin = _legend_kwargs(
            leg, ax2_present=ax2 is not None, fig=ax.figure
        )
        legend_artist = ax.legend(
            handles, labels, title=leg.title, frameon=leg.frame, **kw
        )
        legend_artist._mudplot_auto_margin = auto_margin


def _panel_label(index: int) -> str:
    # a, b, c, ... z, aa, ab, ... (spreadsheet-style, in case of >26 panels)
    letters = ""
    n = index
    while True:
        n, r = divmod(n, 26)
        letters = chr(97 + r) + letters
        if n == 0:
            break
        n -= 1
    return letters


def _apply_panel_label(ax, spec: FigureSpec, panel: PanelSpec, index: int):
    import matplotlib.pyplot as plt

    label = panel.label
    if label is None and spec.auto_label_panels:
        label = _panel_label(index)
    if label:
        # Read the *effective* title size from the active rcParams rather
        # than spec.theme.font.title_size directly: a journal preset
        # overrides the theme's font sizes via rcParams (see theme.py), and
        # this function runs inside that rc_context, so this keeps panel
        # labels visually consistent with the (possibly journal-overridden)
        # panel titles instead of silently ignoring the override.
        fontsize = plt.rcParams.get("axes.titlesize", spec.theme.font.title_size)
        text = ax.text2D if panel.projection == "3d" else ax.text
        text(
            -0.12,
            1.05,
            f"{label})",
            transform=ax.transAxes,
            fontsize=fontsize,
            fontweight="bold",
            ha="left",
            va="bottom",
        )


def _grid_shape(spec: FigureSpec) -> tuple[int, int]:
    if spec.layout:
        return spec.layout[0], spec.layout[1]
    return 1, len(spec.panels)


def _count_colors(spec: FigureSpec) -> int:
    counts = []
    for p in spec.panels:
        count = 0
        for lyr in p.layers:
            if lyr.color or lyr.type in _MATRIX_TYPES | {"surface"}:
                continue
            if lyr.type in {"scatter", "scatter3d"} and lyr.c is not None:
                continue
            if lyr.type == "pie":
                count += len(spec.data.columns[lyr.y])
            elif lyr.group and lyr.group in spec.data.columns:
                count += len(_unique_stable(spec.data.columns[lyr.group]))
            else:
                count += 1
        counts.append(count)
    return max(counts, default=1)


def _link_shared_axes(axes_grid, rows: int, cols: int, mode: str, axis: str) -> None:
    """Emulate plt.subplots(sharex=...)'s "none"/"all"/"row"/"col" modes,
    but after the fact -- needed because 3-D-capable panels are built with
    fig.add_subplot() one at a time instead of plt.subplots(), which is the
    only way to give each panel its own projection.
    """
    if mode == "none":
        return

    def link(ax, base):
        (ax.sharex if axis == "x" else ax.sharey)(base)

    if mode == "all":
        base = next((a for row in axes_grid for a in row if a is not None), None)
        if base is None:
            return
        for row in axes_grid:
            for ax in row:
                if ax is not None and ax is not base:
                    link(ax, base)
    elif mode == "row":
        for row in axes_grid:
            base = next((a for a in row if a is not None), None)
            if base is None:
                continue
            for ax in row:
                if ax is not None and ax is not base:
                    link(ax, base)
    elif mode == "col":
        for c in range(cols):
            column = [axes_grid[r][c] for r in range(rows)]
            base = next((a for a in column if a is not None), None)
            if base is None:
                continue
            for ax in column:
                if ax is not None and ax is not base:
                    link(ax, base)


def _autofit(fig, pad_px: float = 6.0) -> None:
    """Precompute layout so text never overlaps or gets silently clipped,
    while keeping the figure at its exact configured size (needed for TeX
    column-width placement -- see ``mudplot.tex``).

    Two passes, using matplotlib's own accurate text-measurement renderer
    (the same role a browser's font engine plays for web text layout):

    1. Reserve canvas space for any *named* "outside ..." legend (not an
       explicit/dragged ``bbox_to_anchor``, which is trusted as-is) by
       shrinking the constrained-layout engine's working rectangle --
       constrained_layout still does its own tick-label-aware spacing
       *inside* that smaller rectangle, so this doesn't reimplement that.
    2. Panel titles/suptitle already wrap (``wrap=True``) at the figure
       width via matplotlib's native text layout; this only needs to ask
       for a redraw after step 1 changes that width.
    """
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    fig_w, fig_h = fig.bbox.width, fig.bbox.height

    left, bottom, right, top = 0.0, 0.0, 1.0, 1.0
    changed = False
    for ax in fig.axes:
        legend = ax.get_legend()
        if legend is None or not getattr(legend, "_mudplot_auto_margin", False):
            continue
        bb = legend.get_window_extent(renderer).transformed(fig.transFigure.inverted())
        if bb.x1 > 1:
            right = min(right, 1 - (bb.x1 - 1) - pad_px / fig_w)
            changed = True
        if bb.x0 < 0:
            left = max(left, -bb.x0 + pad_px / fig_w)
            changed = True
        if bb.y1 > 1:
            top = min(top, 1 - (bb.y1 - 1) - pad_px / fig_h)
            changed = True
        if bb.y0 < 0:
            bottom = max(bottom, -bb.y0 + pad_px / fig_h)
            changed = True

    if changed and fig.get_layout_engine() is not None:
        fig.get_layout_engine().set(rect=(left, bottom, right - left, top - bottom))

    # Re-draw so wrapped titles measure against the (possibly now smaller)
    # available width; harmless no-op if nothing changed above.
    fig.canvas.draw()


def render(spec: FigureSpec):
    """Build and return a matplotlib Figure for ``spec``.

    Raises ``ValueError`` (with all issues listed) if ``spec`` is invalid —
    see :mod:`mudplot.validate`.
    """
    import matplotlib.pyplot as plt

    assert_valid(spec)

    rc = spec_to_rcparams(
        spec.theme, spec.journal, n_colors=max(_count_colors(spec), 3)
    )

    with plt.rc_context(rc):
        rows, cols = _grid_shape(spec)
        gridspec_kw = {}
        if spec.width_ratios:
            gridspec_kw["width_ratios"] = spec.width_ratios
        if spec.height_ratios:
            gridspec_kw["height_ratios"] = spec.height_ratios

        # Built with fig.add_subplot() (one call per panel) rather than
        # plt.subplots(), which can't give individual panels their own
        # projection (needed for 3-D panels mixed with 2-D ones).
        #
        # constrained_layout (+ _autofit below) gives precise, overlap-free
        # spacing for 2-D panels, but matplotlib's 3-D Axes don't support it
        # well (e.g. the z-axis label routinely gets clipped) -- fall back
        # to the older tight_layout() pass for any figure containing a 3-D
        # panel rather than regress that case.
        has_3d = any(p.projection == "3d" for p in spec.panels)
        fig = plt.figure(
            figsize=tuple(spec.size),
            dpi=spec.dpi,
            layout=None if has_3d else "constrained",
        )
        try:
            gs = fig.add_gridspec(rows, cols, **gridspec_kw)
            axes_grid = [[None] * cols for _ in range(rows)]
            panel_axes = []
            for i, panel in enumerate(spec.panels):
                r, c = divmod(i, cols)
                projection = "3d" if panel.projection == "3d" else None
                ax = fig.add_subplot(gs[r, c], projection=projection)
                if projection is None:
                    axes_grid[r][c] = ax
                panel_axes.append(ax)

            # Share the 2-D subset, even when other panels are 3-D.
            _link_shared_axes(axes_grid, rows, cols, spec.share_x, "x")
            _link_shared_axes(axes_grid, rows, cols, spec.share_y, "y")

            for i, (ax, panel) in enumerate(zip(panel_axes, spec.panels, strict=False)):
                _draw_panel(ax, spec, panel)
                _apply_panel_label(ax, spec, panel, i)

            if spec.suptitle:
                fig.suptitle(spec.suptitle, wrap=True)
            if has_3d:
                fig.tight_layout()
            else:
                _autofit(fig)
        except Exception:
            plt.close(fig)
            raise
    return fig


def save(spec: FigureSpec, path: str, *, tight: bool = False):
    """Save at the exact spec size; ``tight=True`` opts into content cropping.

    Returns an open Figure, owned by the caller, on success.
    """
    import matplotlib.pyplot as plt

    fig = render(spec)
    try:
        # Explicitly disable ambient cropping too: bbox_inches=None alone
        # falls back to the caller's savefig.bbox rcParam.
        with plt.rc_context({"savefig.bbox": None}):
            fig.savefig(
                path,
                dpi=spec.dpi,
                bbox_inches="tight" if tight else None,
                pad_inches=0.05,
            )
    except Exception:
        plt.close(fig)
        raise
    return fig
