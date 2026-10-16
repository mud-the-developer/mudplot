"""Hierarchical clustering effects with matched heatmap/dendrogram orders."""

from __future__ import annotations

import warnings
from dataclasses import dataclass, replace

import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgba
from matplotlib.image import AxesImage
from matplotlib.transforms import Bbox

from ._heatmap_render import draw_colourbar, draw_heatmap
from .spec import ClusterSpec, HeatmapSpec


@dataclass
class ClusterResult:
    matrix: np.ndarray
    rows: tuple[int, ...]
    cols: tuple[int, ...]
    row_tree: dict | None
    col_tree: dict | None


def _standardize(matrix, config):
    axis_name = config.z_score or config.standard_scale
    if axis_name is None:
        return matrix.copy()
    axis = 1 if axis_name == "row" else 0
    magnitude = np.max(np.abs(matrix), axis=axis, keepdims=True)
    unit = matrix / np.where(magnitude == 0, 1, magnitude)
    if config.z_score is not None:
        result = (unit - unit.mean(axis=axis, keepdims=True)) / unit.std(
            axis=axis, ddof=1, keepdims=True
        )
    else:
        low = unit.min(axis=axis, keepdims=True)
        result = (unit - low) / (unit.max(axis=axis, keepdims=True) - low)
    if not np.isfinite(result).all():
        raise ValueError("cluster standardization is not representable")
    return result


def _tree(values, config, provided):
    if len(values) < 2:
        return tuple(range(len(values))), None
    try:
        from scipy.cluster.hierarchy import (
            dendrogram,
            is_valid_linkage,
            linkage,
            optimal_leaf_ordering,
        )
        from scipy.spatial.distance import pdist
    except ImportError as error:
        raise ImportError(
            "clustering effects require optional mudplot[cluster]"
        ) from error
    if provided is None or config.optimal_ordering:
        if config.metric in ("cosine", "correlation"):
            scale = np.max(np.abs(values), axis=1, keepdims=True)
            fit = values / np.where(scale == 0, 1, scale)
            distance_scale = 1.0
        else:
            distance_scale = float(np.max(np.abs(values))) or 1.0
            fit = values / distance_scale
        distances = pdist(fit, metric=config.metric)
        if not np.isfinite(distances).all():
            raise ValueError("cluster metric is undefined for these finite vectors")
    if provided is None:
        nodes = linkage(
            distances, method=config.method, optimal_ordering=config.optimal_ordering
        )
        nodes[:, 2] *= distance_scale
    else:
        nodes = np.array(provided, dtype=float, copy=True)
    if not np.isfinite(nodes).all():
        raise ValueError("cluster linkage distances are not representable")
    is_valid_linkage(nodes, throw=True)
    if provided is not None and config.optimal_ordering:
        nodes = optimal_leaf_ordering(nodes, distances)
    tree = dendrogram(nodes, no_plot=True)
    return tuple(int(value) for value in tree["leaves"]), tree


def cluster_summary(matrix, config: ClusterSpec) -> ClusterResult:
    original = np.asarray(matrix, dtype=float)
    with (
        warnings.catch_warnings(),
        np.errstate(over="raise", invalid="raise", divide="raise"),
    ):
        warnings.simplefilter("error", RuntimeWarning)
        try:
            values = _standardize(original, config)
            rows, row_tree = (
                _tree(values, config, config.row_linkage)
                if config.row_cluster
                else (tuple(range(len(values))), None)
            )
            cols, col_tree = (
                _tree(values.T, config, config.col_linkage)
                if config.col_cluster
                else (tuple(range(values.shape[1])), None)
            )
            ordered = values[np.ix_(rows, cols)].copy()
            return ClusterResult(ordered, rows, cols, row_tree, col_tree)
        except (ValueError, FloatingPointError, Warning) as error:
            raise ValueError(f"clustermap fit failed: {error}") from error


def _draw_tree(ax, tree, count, config, *, row):
    segments = [
        list(zip(distances, indices, strict=True))
        if row
        else list(zip(indices, distances, strict=True))
        for indices, distances in zip(tree["icoord"], tree["dcoord"], strict=True)
    ]
    ax.add_collection(
        LineCollection(segments, colors=config.tree_color, linewidths=config.tree_width)
    )
    height = max(max(values) for values in tree["dcoord"]) or 1.0
    if row:
        ax.set_xlim(height, 0)
        ax.set_ylim(10 * count, 0)
    else:
        ax.set_xlim(0, 10 * count)
        ax.set_ylim(0, height)
    ax.set_axis_off()


def freeze_layout(fig):
    # Nested locators can differ below a pixel between vector draws, changing SVG IDs.
    positions = [
        tuple(round(value, 12) for value in ax.get_position().bounds) for ax in fig.axes
    ]
    fig.set_layout_engine(None)
    for ax, bounds in zip(fig.axes, positions, strict=True):
        ax.set_axes_locator(None)
        ax.set_position(bounds)


def _align_axis(axes, body, *, horizontal):
    def locate(_axes, _renderer):
        slot = axes.get_position(original=True)
        box = body.get_position()
        return (
            Bbox.from_extents(box.x0, slot.y0, box.x1, slot.y1)
            if horizontal
            else Bbox.from_extents(slot.x0, box.y0, slot.x1, box.y1)
        )

    axes.set_axes_locator(locate)


def draw_clustermap(ax, matrix, layer, cmap) -> AxesImage:
    config = ClusterSpec() if layer.cluster is None else layer.cluster
    display = HeatmapSpec() if layer.heatmap is None else layer.heatmap
    summary = cluster_summary(matrix, config)
    row_labels = display.ylabels or [str(i) for i in range(matrix.shape[0])]
    col_labels = display.xlabels or [str(i) for i in range(matrix.shape[1])]
    mask = (
        None
        if display.mask is None
        else np.asarray(display.mask, dtype=bool)[
            np.ix_(summary.rows, summary.cols)
        ].tolist()
    )
    ordered = replace(
        display,
        mask=mask,
        xlabels=[col_labels[i] for i in summary.cols],
        ylabels=[row_labels[i] for i in summary.rows],
    )
    image = draw_heatmap(ax, summary.matrix, replace(layer, heatmap=ordered), cmap)
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")
    ax._mudplot_cluster_order = {"rows": summary.rows, "cols": summary.cols}
    heights = [config.dendrogram_ratio] if summary.col_tree is not None else []
    heights += ([0.04] if config.col_colors is not None else []) + [1]
    widths = [config.dendrogram_ratio] if summary.row_tree is not None else []
    widths += ([0.04] if config.row_colors is not None else []) + [1]
    body_row, body_col = len(heights) - 1, len(widths) - 1
    if layer.colorbar:
        widths.append(0.05)
    grid = ax.get_subplotspec().subgridspec(
        len(heights),
        len(widths),
        height_ratios=heights,
        width_ratios=widths,
        wspace=0.06,
        hspace=0.04,
    )
    ax.set_subplotspec(grid[body_row, body_col])
    title_axes = ax
    if config.col_colors is not None:
        strip = ax.figure.add_subplot(grid[body_row - 1, body_col])
        _align_axis(strip, ax, horizontal=True)
        title_axes = strip
        strip.imshow(
            np.array([[to_rgba(config.col_colors[i]) for i in summary.cols]]),
            aspect="auto",
        )
        strip.set_axis_off()
    if config.row_colors is not None:
        strip = ax.figure.add_subplot(grid[body_row, body_col - 1])
        _align_axis(strip, ax, horizontal=False)
        strip.imshow(
            np.array([[to_rgba(config.row_colors[i])] for i in summary.rows]),
            aspect="auto",
        )
        strip.set_axis_off()
    if summary.col_tree is not None:
        tree_axes = ax.figure.add_subplot(grid[0, body_col])
        _align_axis(tree_axes, ax, horizontal=True)
        _draw_tree(tree_axes, summary.col_tree, len(summary.cols), config, row=False)
        title_axes = tree_axes
    if summary.row_tree is not None:
        tree_axes = ax.figure.add_subplot(grid[body_row, 0])
        _align_axis(tree_axes, ax, horizontal=False)
        _draw_tree(tree_axes, summary.row_tree, len(summary.rows), config, row=True)
    ax._mudplot_cluster_title_axes = title_axes
    if layer.colorbar:
        cax = ax.figure.add_subplot(grid[body_row, body_col + 1])
        _align_axis(cax, ax, horizontal=False)
        draw_colourbar(ax, image, layer.clabel or "", cax=cax)
    return image
