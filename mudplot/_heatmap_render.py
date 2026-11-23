"""Matplotlib effects for validated opt-in heatmap controls."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import cast

import numpy as np
from matplotlib.cm import ScalarMappable
from matplotlib.collections import LineCollection
from matplotlib.colors import (
    BoundaryNorm,
    ListedColormap,
    LogNorm,
    Normalize,
    PowerNorm,
    SymLogNorm,
    TwoSlopeNorm,
)
from matplotlib.ticker import FormatStrFormatter
from numpy.typing import ArrayLike

from ._estimate import _quantiles
from ._heatmap import advanced_heatmap, linear_constant_bounds
from .color.convert import srgb_to_linear
from .spec import HeatmapSpec


def colour_norm(values, config: HeatmapSpec) -> Normalize:
    if config.norm == "boundary":
        assert config.boundaries is not None
        return BoundaryNorm(config.boundaries, len(config.boundaries) - 1)
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
            a, b = linear_constant_bounds(low)
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
    if config.norm == "symlog":
        assert config.linthresh is not None
        norm = SymLogNorm(config.linthresh, linscale=1, base=10, vmin=low, vmax=high)
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            bounds = norm([low, high])
        if np.ma.is_masked(bounds) or not np.array_equal(bounds, [0, 1]):
            raise ValueError("symlog matrix colour transform is not representable")
        return norm
    if not math.isfinite(high - low):
        raise ValueError(
            "heatmap colour span is not representable; set explicit bounds"
        )
    if config.norm == "power":
        assert config.gamma is not None
        return PowerNorm(config.gamma, vmin=low, vmax=high, clip=True)
    return Normalize(vmin=low, vmax=high)


def bar_geometry(config, *, options=None):
    bar = config.colorbar_options if options is None else options
    return (
        (bar.location or "right") if bar is not None else "right",
        bar.fraction if bar is not None and bar.fraction is not None else 0.05,
        bar.pad if bar is not None and bar.pad is not None else 0.04,
    )


def _bar_calibration(image, config, *, options=None):
    norm = image.norm
    options = config.colorbar_options if options is None else options
    requested = None if options is None else options.ticks
    tick_format = None if options is None else options.tick_format
    low, high = image.get_clim()
    native = {}
    if isinstance(norm, BoundaryNorm):
        raw = norm.boundaries
        edges = np.linspace(0.0, 1.0, len(raw))
        inds = (
            np.linspace(0, len(raw) - 1, min(len(raw), 5), dtype=int)
            if requested is None
            else np.searchsorted(raw, requested)
        )
        ticks, positions = raw[inds], edges[inds]
        native.update(boundaries=edges, values=raw[:-1], spacing="uniform")
        if config is None:
            # P01 uses a dummy uniform guide mappable. These are colormap
            # centers rather than raw inputs to its [0,1] normalization.
            native["values"] = (edges[:-1] + edges[1:]) / 2
    else:
        if requested is None:
            with np.errstate(over="ignore", invalid="ignore"):
                ticks = np.asarray(norm.inverse(np.linspace(0, 1, 5)), dtype=float)
            ticks[0], ticks[-1] = low, high
            ticks = np.unique(
                ticks[np.isfinite(ticks) & (ticks >= low) & (ticks <= high)]
            )
        else:
            ticks = np.asarray(requested, dtype=float)
            if ticks[0] < low or ticks[-1] > high:
                raise ValueError(
                    "colourbar ticks must be in the resolved display-value domain"
                )
        positions = np.ma.filled(norm(ticks), np.nan)
        positions[ticks == low], positions[ticks == high] = 0, 1
    if not np.isfinite(positions).all() or np.any((positions < 0) | (positions > 1)):
        raise ValueError("colourbar tick positions are not representable")
    labels = []
    retained = []
    seen = set()
    for value, position in zip(ticks, positions, strict=True):
        text = repr(float(value)) if tick_format is None else format(value, tick_format)
        if (retained and position <= retained[-1]) or text in seen:
            if requested is not None:
                raise ValueError(
                    "explicit colourbar ticks must have distinct positions and labels"
                )
            continue
        seen.add(text)
        retained.append(position)
        labels.append(text)
    return retained, labels, native


def _calibrated_colourbar(ax, image, label, config, cax, options=None):
    low, high = image.get_clim()
    retained, labels, native = _bar_calibration(image, config, options=options)
    location, fraction, pad = bar_geometry(config, options=options)
    if options is not None:
        extend = options.extend or "neither"
        native["extend"] = extend
        if isinstance(image.norm, BoundaryNorm) and extend != "neither":
            # Explicit boundaries include extension segments when `values`
            # is supplied to Matplotlib; only interior bins own data.
            edges, vals = native["boundaries"], native["values"]
            if extend in ("min", "both"):
                edges, vals = np.r_[-1, edges], np.r_[-1, vals]
            if extend in ("max", "both"):
                edges, vals = np.r_[edges, 2], np.r_[vals, 2]
            native.update(boundaries=edges, values=vals)
    mappable = (
        image
        if isinstance(image.norm, BoundaryNorm) and options is None
        else ScalarMappable(
            norm=Normalize(0, 1),
            cmap=image.cmap,
        )
    )
    if cax is None:
        native.update(fraction=fraction, pad=pad)
    bar = ax.figure.colorbar(
        mappable,
        ax=ax,
        cax=cax,
        location=location,
        label=label,
        ticks=retained,
        alpha=image.get_alpha(),
        **native,
    )
    bar.set_ticklabels(labels)
    if image.get_clim() != (low, high):
        raise ValueError("colourbar changed the raw matrix colour domain")
    bar.ax._mudplot_matrix_decoration = True
    bar.ax._mudplot_matrix_panel = ax
    return bar


def draw_colourbar(
    ax, image, label, *, cax=None, config=None, calibrated=False, options=None
):
    if calibrated or advanced_heatmap(config):
        return _calibrated_colourbar(ax, image, label, config, cax, options)
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


def draw_heatmap(
    ax, matrix, layer, cmap, *, nulls=None, display_mask=None, scalar_norm=None
):
    config = layer.heatmap
    mask = display_mask
    if mask is None:
        mask = (
            np.zeros(matrix.shape, dtype=bool)
            if config.mask is None
            else np.asarray(config.mask, dtype=bool)
        )
    visible_nulls = (
        None
        if nulls is None or scalar_norm is not None
        else np.logical_and(nulls, ~mask)
    )
    if nulls is not None:
        mask = np.logical_or(mask, nulls)
    norm = colour_norm(matrix[~mask], config) if scalar_norm is None else scalar_norm
    if scalar_norm is None and isinstance(norm, BoundaryNorm):
        cmap = ListedColormap(cmap(np.linspace(0, 1, norm.Ncmap)))
    if advanced_heatmap(config):
        values = matrix[~mask]
        # Older native PowerNorm computes pow before scale (clip is still native).
        # Never silently turn an unrepresentable selected value into a bad cell.
        with np.errstate(
            over="ignore", invalid="ignore", divide="ignore", under="ignore"
        ):
            mapped = norm(values)
        if (
            np.ma.is_masked(mapped)
            or np.isnan(mapped).any()
            or (isinstance(norm, PowerNorm) and not np.isfinite(mapped).all())
        ):
            raise ValueError("matrix colour transform is not representable")
    image = ax.imshow(
        np.ma.array(matrix, mask=mask),
        cmap=cmap,
        norm=norm,
        aspect="equal" if config.square else "auto",
        alpha=layer.alpha,
    )
    if (
        not layer.colorbar
        and config.colorbar_options is not None
        and config.colorbar_options.ticks is not None
    ):
        _bar_calibration(image, config)
    ax.grid(False)
    rows, cols = matrix.shape
    if config.xlabels is not None:
        ax.set_xticks(np.arange(cols), labels=config.xlabels)
    if config.ylabels is not None:
        ax.set_yticks(np.arange(rows), labels=config.ylabels)
    if config.xrotation is not None:
        ax.tick_params(axis="x", labelrotation=config.xrotation)
    if config.yrotation is not None:
        ax.tick_params(axis="y", labelrotation=config.yrotation)
    if layer.line_width:
        ax.set_xticks(np.arange(cols + 1) - 0.5, minor=True)
        ax.set_yticks(np.arange(rows + 1) - 0.5, minor=True)
        ax.grid(
            which="minor",
            color=layer.edge_color or "#ffffff",
            linewidth=layer.line_width,
        )
        ax.tick_params(which="minor", bottom=False, left=False)
    if visible_nulls is not None and visible_nulls.any():
        positions = np.argwhere(visible_nulls)[:, ::-1]
        segments = positions[:, None, :] + [[[-0.24, 0.24], [0.24, -0.24]]]
        missing = LineCollection(
            cast("Sequence[ArrayLike]", segments),
            colors="#697078",
            linewidths=0.8,
            zorder=3,
        )
        ax.add_collection(missing, autolim=False)
        ax._mudplot_matrix_missing = True
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
                (
                    format(matrix[row, col], config.fmt)
                    if config.annot_data is None
                    else config.annot_data[row][col]
                ),
                ha="center",
                va="center",
                color="#000000" if black >= white else "#ffffff",
            )
            artist.set_in_layout(False)
    return image
