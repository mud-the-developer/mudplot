"""Matplotlib effects for validated opt-in heatmap controls."""

from __future__ import annotations

import math

import numpy as np
from matplotlib.colors import LogNorm, Normalize, TwoSlopeNorm
from matplotlib.ticker import FormatStrFormatter

from ._estimate import _quantiles
from .color.convert import srgb_to_linear
from .spec import HeatmapSpec


def colour_norm(values, config: HeatmapSpec) -> Normalize:
    low, high = (
        _quantiles(values, (0.02, 0.98))
        if config.robust
        else (float(values.min()), float(values.max()))
    )
    low = low if config.vmin is None else config.vmin
    high = high if config.vmax is None else config.vmax
    if config.center is not None:
        center = config.center
        span = max(abs(low - center), abs(high - center)) or 0.5
        if config.vmin is None:
            low = center - span
        if config.vmax is None:
            high = center + span
        if (
            not all(math.isfinite(v) for v in (low, center, high))
            or not low < center < high
        ):
            raise ValueError(
                "derived heatmap bounds must straddle a representable center"
            )
        return TwoSlopeNorm(vcenter=center, vmin=low, vmax=high)
    if low == high:
        if config.norm == "log":
            a, b = low / 10, high * 10
            if a <= 0:
                a = low
        else:
            padding = abs(low) * 0.05 or 0.5
            a, b = low - padding, high + padding
        if config.vmin is None and math.isfinite(a):
            low = a
        if config.vmax is None and math.isfinite(b):
            high = b
        if low == high:
            if config.vmin is None:
                low = math.nextafter(low, -math.inf)
            if config.vmax is None:
                high = math.nextafter(high, math.inf)
    if not all(math.isfinite(v) for v in (low, high)) or low >= high:
        raise ValueError("derived heatmap colour range must be finite and increasing")
    if config.norm == "log":
        if low <= 0:
            raise ValueError("derived log heatmap bounds must be positive")
        return LogNorm(vmin=low, vmax=high)
    if not math.isfinite(high - low):
        raise ValueError(
            "heatmap colour span is not representable; set explicit bounds"
        )
    return Normalize(vmin=low, vmax=high)


def draw_colourbar(ax, image, label, *, cax=None):
    # Explicit values avoid native midpoint overflow and subnormal auto-expansion.
    edges = np.unique(
        np.asarray(image.norm.inverse(np.linspace(0, 1, 257)), dtype=float)
    )
    if not np.isfinite(edges).all() or len(edges) < 2:
        raise ValueError("heatmap colourbar boundaries are not representable")
    values = edges[:-1] / 2 + edges[1:] / 2
    ticks = np.unique(np.asarray(image.norm.inverse(np.linspace(0, 1, 5)), dtype=float))
    return ax.figure.colorbar(
        image,
        ax=ax,
        cax=cax,
        label=label,
        boundaries=edges,
        values=values,
        ticks=ticks,
        format=FormatStrFormatter("%g"),
    )


def draw_heatmap(ax, matrix, layer, cmap):
    config = layer.heatmap
    mask = (
        np.zeros(matrix.shape, dtype=bool)
        if config.mask is None
        else np.asarray(config.mask, dtype=bool)
    )
    values = matrix[~mask]
    image = ax.imshow(
        np.ma.array(matrix, mask=mask),
        cmap=cmap,
        norm=colour_norm(values, config),
        aspect="equal" if config.square else "auto",
        alpha=layer.alpha,
    )
    ax.grid(False)
    rows, cols = matrix.shape
    if config.xlabels is not None:
        ax.set_xticks(np.arange(cols), labels=config.xlabels)
    if config.ylabels is not None:
        ax.set_yticks(np.arange(rows), labels=config.ylabels)
    if layer.line_width:
        ax.set_xticks(np.arange(cols + 1) - 0.5, minor=True)
        ax.set_yticks(np.arange(rows + 1) - 0.5, minor=True)
        ax.grid(
            which="minor",
            color=layer.edge_color or "#ffffff",
            linewidth=layer.line_width,
        )
        ax.tick_params(which="minor", bottom=False, left=False)
    if config.annot:
        background = np.asarray(ax.get_facecolor()[:3])
        for position in np.argwhere(~mask):
            row, col = position[0], position[1]
            rgba = image.cmap(image.norm(matrix[row, col]))
            alpha = layer.alpha * rgba[3]
            rgb = np.asarray(rgba[:3]) * alpha + background * (1 - alpha)
            luminance = float(srgb_to_linear(rgb) @ np.array([0.2126, 0.7152, 0.0722]))
            black = (luminance + 0.05) / 0.05
            white = 1.05 / (luminance + 0.05)
            artist = ax.text(
                col,
                row,
                format(matrix[row, col], config.fmt),
                ha="center",
                va="center",
                color="#000000" if black >= white else "#ffffff",
            )
            artist.set_in_layout(False)
    return image
