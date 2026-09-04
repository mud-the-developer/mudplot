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
_DIST_TYPES = {"hist", "box"}
# layer types that draw a 2-D matrix
_MATRIX_TYPES = {"heatmap"}

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


def _x_values(data_cols, name):
    """x-column values as plot-ready numeric positions.

    Numeric columns pass through unchanged. Categorical columns (e.g. bar
    chart categories like "control"/"treatment") can't be coerced to float
    -- rather than crashing, they're mapped to evenly-spaced positions
    0..n-1 (in first-seen order) so bar/line/scatter/etc. can still plot
    them; the caller is responsible for applying the returned labels as
    tick labels.

    Returns ``(positions, labels)`` where ``labels`` is ``None`` for
    already-numeric columns, or the ordered list of unique category
    strings otherwise.
    """
    raw = data_cols[name]
    try:
        return np.asarray(raw, dtype=float), None
    except (ValueError, TypeError):
        str_values = [str(v) for v in raw]
        labels = _unique_stable(str_values)
        position_of = {label: i for i, label in enumerate(labels)}
        positions = np.array([position_of[v] for v in str_values], dtype=float)
        return positions, labels


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
    target = _target_axes(ax, ax2, layer)
    n_series = len(masks)

    x_all, x_labels = _x_values(data_cols, layer.x)

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
                    label=label,
                    s=(layer.marker_size or 6) ** 2,
                    marker=marker or "o",
                    alpha=layer.alpha,
                )
                if layer.colorbar:
                    target.figure.colorbar(sc, ax=target, label=layer.clabel or "")
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

    return target, x_labels


def _draw_dist_layer(ax, data_cols, layer: LayerSpec, color_iter):
    masks = list(_series_masks(data_cols, layer))
    if layer.type == "hist":
        for label, mask in masks:
            values = _col(data_cols, layer.x)[mask]
            ax.hist(
                values,
                bins=layer.bins,
                density=layer.density,
                label=label,
                color=layer.color or next(color_iter),
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
            patch.set_alpha(layer.alpha if layer.alpha < 1 else 0.6)


def _draw_matrix_layer(ax, spec: FigureSpec, layer: LayerSpec):
    matrix = np.asarray(spec.data.matrices[layer.matrix], dtype=float)
    im = ax.imshow(
        matrix,
        aspect="auto",
        cmap=_continuous_cmap(layer.cmap_kind),
        alpha=layer.alpha,
    )
    if layer.colorbar:
        ax.figure.colorbar(im, ax=ax, label=layer.clabel or "")


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


def _apply_axis(ax, axis_spec, set_label, set_scale, set_limits):
    set_label(axis_spec.label)
    if axis_spec.scale == "log":
        set_scale("log")
    if axis_spec.limits:
        set_limits(axis_spec.limits)


def _apply_despine(ax, theme_axes):
    for char, side in _SPINE_SIDES.items():
        if char in theme_axes.spines and theme_axes.spine_offset:
            ax.spines[side].set_position(("outward", theme_axes.spine_offset))


def _draw_panel(ax, spec: FigureSpec, panel: PanelSpec):
    import matplotlib.pyplot as plt

    prop = plt.rcParams["axes.prop_cycle"].by_key().get("color", ["C0"])
    color_iter = iter(prop * 100)  # cycle enough colours
    theme = spec.theme

    ax2 = ax.twinx() if panel.y2 is not None else None

    # Categorical x columns (e.g. bar-chart categories) get mapped to
    # numeric positions by _draw_series_layer; remember the first set of
    # labels seen per target axes so we can apply them as tick labels once,
    # after every layer has been drawn.
    categorical_ticks: dict[int, tuple] = {}

    for layer in panel.layers:
        if layer.type in _SERIES_TYPES:
            target, x_labels = _draw_series_layer(
                ax, ax2, spec.data.columns, layer, color_iter, theme
            )
            if x_labels is not None and id(target) not in categorical_ticks:
                categorical_ticks[id(target)] = (target, x_labels)
        elif layer.type in _DIST_TYPES:
            _draw_dist_layer(ax, spec.data.columns, layer, color_iter)
        elif layer.type in _MATRIX_TYPES:
            _draw_matrix_layer(ax, spec, layer)
        else:
            _draw_marker_layer(ax, ax2, layer, color_iter)

    for target, x_labels in categorical_ticks.values():
        target.set_xticks(range(len(x_labels)))
        target.set_xticklabels(x_labels)

    _apply_axis(ax, panel.x, ax.set_xlabel, ax.set_xscale, ax.set_xlim)
    _apply_axis(ax, panel.y, ax.set_ylabel, ax.set_yscale, ax.set_ylim)
    if panel.y2 is not None:
        _apply_axis(ax2, panel.y2, ax2.set_ylabel, ax2.set_yscale, ax2.set_ylim)
    if panel.title:
        ax.set_title(panel.title)
    _apply_despine(ax, theme.axes)

    handles, labels = ax.get_legend_handles_labels()
    if ax2 is not None:
        h2, l2 = ax2.get_legend_handles_labels()
        handles, labels = handles + h2, labels + l2
    leg = panel.legend
    if leg.show and handles:
        kw = dict(_OUTSIDE_LEGEND_LOCS.get(leg.location, {"loc": leg.location}))
        if leg.location == "outside right" and ax2 is not None:
            # leave room for the secondary axis's own ticks/label
            kw["bbox_to_anchor"] = (1.35, 0.5)
        ax.legend(handles, labels, title=leg.title, frameon=leg.frame, **kw)


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
        ax.text(
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
        for lyr in p.layers:
            if lyr.group and lyr.group in spec.data.columns:
                counts.append(len(_unique_stable(spec.data.columns[lyr.group])))
            else:
                counts.append(1)
    return max(counts, default=1)


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
        fig, axes = plt.subplots(
            rows,
            cols,
            figsize=tuple(spec.size),
            dpi=spec.dpi,
            squeeze=False,
            sharex=spec.share_x,
            sharey=spec.share_y,
            gridspec_kw=gridspec_kw or None,
        )
        flat = axes.ravel()
        for i, (ax, panel) in enumerate(zip(flat, spec.panels, strict=False)):
            _draw_panel(ax, spec, panel)
            _apply_panel_label(ax, spec, panel, i)
        # hide any unused axes in the grid
        for ax in flat[len(spec.panels) :]:
            ax.set_visible(False)
        if spec.suptitle:
            fig.suptitle(spec.suptitle)
        fig.tight_layout()
    return fig


def save(spec: FigureSpec, path: str):
    """Render ``spec`` and write it to ``path`` (format from extension)."""
    fig = render(spec)
    # rcParams' savefig.bbox="tight" only applies inside the rc_context used
    # during rendering, so pass it explicitly here too.
    fig.savefig(path, dpi=spec.dpi, bbox_inches="tight", pad_inches=0.05)
    return fig
