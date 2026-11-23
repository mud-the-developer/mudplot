"""Hierarchical clustering effects with matched heatmap/dendrogram orders."""

from __future__ import annotations

import warnings
from contextlib import nullcontext
from dataclasses import dataclass, replace
from typing import Protocol, cast

import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgba
from matplotlib.image import AxesImage
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.transforms import blended_transform_factory

from ._heatmap_render import bar_geometry, draw_colourbar, draw_heatmap
from ._matrix_layout import align_axis, matrix_slots, side_plot
from .spec import ClusterSpec, HeatmapSpec


@dataclass
class ClusterResult:
    matrix: np.ndarray
    rows: tuple[int, ...]
    cols: tuple[int, ...]
    row_tree: dict | None
    col_tree: dict | None
    row_linkage: np.ndarray | None = None
    col_linkage: np.ndarray | None = None
    nulls: np.ndarray | None = None


def _standardize(matrix, config, nulls=None):
    axis_name = config.z_score or config.standard_scale
    if axis_name is None:
        return matrix
    axis = 1 if axis_name == "row" else 0
    if nulls is not None and nulls.any():
        result = matrix.copy()
        vectors, missing = (result, nulls) if axis == 1 else (result.T, nulls.T)
        for vector, absent in zip(vectors, missing, strict=True):
            observed = ~absent
            unit = vector[observed]
            if len(unit) < 2:
                raise ValueError("insufficient observed values for standardization")
            unit /= np.max(np.abs(unit)) or 1.0
            if config.z_score is not None:
                unit = (unit - unit.mean()) / unit.std(ddof=1)
            else:
                low = unit.min()
                unit = (unit - low) / (unit.max() - low)
            if not np.isfinite(unit).all():
                raise ValueError("cluster standardization is not representable")
            vector[observed] = unit
        return result
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


def _tree(values, config, provided, external, features, admission, *, strict_heights):
    n = len(values)
    if n < 2:
        return tuple(range(n)), None, None
    frame = admission.scipy_frame if admission is not None else lambda _n: nullcontext()
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
        if external is not None:
            distances = np.asarray(external.values, dtype=float)
            distance_scale = float(distances.max()) or 1.0
            if distance_scale != 1.0:
                scaled = distances / distance_scale
                if np.any((distances > 0) & (scaled == 0)):
                    raise ValueError("declared dissimilarity span is not representable")
                distances = scaled
        else:
            if features is not None:
                if not len(features):
                    raise ValueError("cluster metric has no common observed features")
                if len(features) != values.shape[1]:
                    values = values[:, features]
            if config.metric in ("cosine", "correlation"):
                scale = np.max(np.abs(values), axis=1, keepdims=True)
                fit = values / np.where(scale == 0, 1, scale)
                distance_scale = 1.0
            else:
                distance_scale = float(np.max(np.abs(values))) or 1.0
                fit = values / distance_scale
            with frame(n):
                distances = pdist(fit, metric=config.metric)
            del fit
        if not np.isfinite(distances).all():
            raise ValueError("cluster metric is undefined for these finite vectors")
    if provided is None:
        with frame(n):
            nodes = linkage(
                distances,
                method=config.method,
                optimal_ordering=config.optimal_ordering and admission is None,
            )
        if config.optimal_ordering and admission is not None:
            with frame(n):
                nodes = optimal_leaf_ordering(nodes, distances)
        heights = nodes[:, 2]
        if strict_heights and distance_scale < 1:
            for i, scaled in enumerate(heights):
                restored = float(scaled) * distance_scale
                if scaled > 0 and restored == 0:
                    raise ValueError(
                        "positive cluster linkage height is not representable"
                    )
                heights[i] = restored
        else:
            heights *= distance_scale
    else:
        nodes = np.array(provided, dtype=float, copy=True)
    if not np.isfinite(nodes).all():
        raise ValueError("cluster linkage distances are not representable")
    with frame(n):
        is_valid_linkage(nodes, throw=True)
    if provided is not None and config.optimal_ordering:
        with frame(n):
            nodes = optimal_leaf_ordering(nodes, distances)
    with frame(n):
        tree = dendrogram(nodes, no_plot=True)
    return tuple(int(value) for value in tree["leaves"]), tree, nodes


def cluster_summary(
    matrix, config: ClusterSpec, *, admission=None, layer=None
) -> ClusterResult:
    original = np.asarray(matrix, dtype=float)
    with (
        warnings.catch_warnings(),
        np.errstate(over="raise", invalid="raise", divide="raise"),
    ):
        warnings.simplefilter("error", RuntimeWarning)
        try:
            nulls = (
                np.isnan(original) if config.missing == "complete_features" else None
            )
            values = _standardize(original, config, nulls)
            axis_results = []
            for index, (name, items) in enumerate((("row", values), ("col", values.T))):
                if not getattr(config, name + "_cluster"):
                    axis_results.append((tuple(range(len(items))), None, None))
                    continue
                features = None
                if nulls is not None:
                    if admission is not None and layer is not None:
                        features = admission.features.get((id(layer), index))
                    else:
                        features = np.flatnonzero(~nulls.any(axis=index))
                external = getattr(config, name + "_distances")
                cut = getattr(config, name + "_cut")
                try:
                    axis_results.append(
                        _tree(
                            items,
                            config,
                            getattr(config, name + "_linkage"),
                            external,
                            features,
                            admission,
                            strict_heights=nulls is not None
                            or external is not None
                            or cut is not None,
                        )
                    )
                except (ValueError, FloatingPointError, Warning) as error:
                    raise ValueError(f"{name}: {error}") from error
            (rows, row_tree, row_linkage), (cols, col_tree, col_linkage) = axis_results
            indexes = np.ix_(rows, cols)
            return ClusterResult(
                values[indexes],
                rows,
                cols,
                row_tree,
                col_tree,
                row_linkage,
                col_linkage,
                None if nulls is None else nulls[indexes],
            )
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


class _ClearableLocator(Protocol):
    def set_axes_locator(self, locator: None) -> None: ...


def freeze_layout(fig):
    # Nested locators can differ below a pixel between vector draws, changing SVG IDs.
    from ._layout_render import native_axes

    axes = list(native_axes(fig))
    positions = [
        tuple(round(value, 12) for value in ax.get_position().bounds) for ax in axes
    ]
    fig.set_layout_engine(None)
    for ax, bounds in zip(axes, positions, strict=True):
        cast(_ClearableLocator, ax).set_axes_locator(None)
        ax.set_position(cast("tuple[float, float, float, float]", bounds))


def _cut_tree(ax, nodes, order, cut, *, row):
    n = len(order)
    heights = [-np.inf] * n
    monotone = True
    for left, right, height, _ in nodes:
        effective = max(heights[int(left)], heights[int(right)])
        monotone &= height >= effective
        heights.append(max(height, effective))
    # Each original leaf is visited once; do not grow a membership list at
    # every ancestor of an unbalanced tree.
    pending: list[tuple[int, int | None]] = [(2 * n - 2, None)]
    members = {}
    while pending:
        node, owner = pending.pop()
        if owner is None and heights[node] <= cut.height:
            owner = node
        if node < n:
            members.setdefault(owner, []).append(node)
        else:
            left, right = nodes[node - n, :2]
            pending.extend(((int(right), owner), (int(left), owner)))
    groups = sorted((sorted(items) for items in members.values()), key=lambda g: g[0])
    by_leaf = {leaf: g[0] for g in groups for leaf in g}
    group_ids = [by_leaf[leaf] for leaf in order]
    selected = None if cut.anchor is None else by_leaf[cut.anchor]
    changes = [10 * i for i in range(1, n) if group_ids[i - 1] != group_ids[i]]
    position = [i for i, g in enumerate(group_ids) if selected == g]
    transform = (
        blended_transform_factory(ax.transAxes, ax.transData)
        if row
        else blended_transform_factory(ax.transData, ax.transAxes)
    )

    def orient(a, b):
        return (a, b) if row else (b, a)

    fraction = 0.97 if row else 0.03
    marks = LineCollection(
        [[orient(fraction - 0.025, v), orient(fraction + 0.025, v)] for v in changes],
        colors="#30343b",
        linewidths=0.9,
        transform=transform,
    )
    ax.add_collection(marks, autolim=False)
    if position:
        selection = LineCollection(
            [
                [
                    orient(fraction, 10 * position[0] + 1),
                    orient(fraction, 10 * (position[-1] + 1) - 1),
                ]
            ],
            colors="#30343b",
            linewidths=2.8,
            transform=transform,
        )
        name = "row" if row else "col"
        owner = ax._mudplot_matrix_panel
        selection.set_gid(f"mudplot-{name}-cut-selection-{owner._mudplot_panel}")
        ax.add_collection(selection, autolim=False)
    if monotone and cut.height <= max(nodes[:, 2]):
        draw_line = ax.axvline if row else ax.axhline
        draw_line(cut.height, color="#697078", linewidth=0.8, linestyle="--", zorder=1)
    if not monotone:
        ax.text(
            0.02,
            0.02 if row else 0.98,
            "Subtree-max cut",
            transform=ax.transAxes,
            va="bottom" if row else "top",
            fontsize="small",
        )
    return {
        "groups": [{"id": g[0], "indices": g} for g in groups],
        "selected_id": selected,
        "selected": []
        if selected is None
        else next(g for g in groups if g[0] == selected),
        "inverted": not monotone,
    }


def _draw_tracks(owner, order, legacy, tracks, *, row):
    offset = 0.0
    legends = []

    def draw(values, ratio):
        nonlocal offset
        first, last = offset, offset + ratio
        offset = last
        if row:
            owner.imshow(
                values[:, None, :],
                extent=(first, last, len(order) - 0.5, -0.5),
                aspect="auto",
                interpolation="nearest",
            )
        else:
            owner.imshow(
                values[None, :, :],
                extent=(-0.5, len(order) - 0.5, first, last),
                aspect="auto",
                interpolation="nearest",
            )

    if legacy is not None:
        draw(np.asarray([to_rgba(legacy[i]) for i in order]), 0.04)
    for track in tracks:
        palette = np.rint(
            np.asarray([to_rgba(level.color) for level in track.levels]) * 255
        ).astype(np.uint8)
        if (palette[:, 3] == 0).any() or len({tuple(rgba) for rgba in palette}) != len(
            palette
        ):
            raise ValueError(
                f"track {track.id!r} needs distinct visible resolved colours"
            )
        map_key = {level.key: k for k, level in enumerate(track.levels)}
        indices = np.fromiter(
            (map_key[track.values[i]] for i in order), dtype=np.intp, count=len(order)
        )
        draw(palette[indices], track.ratio or 0.04)
        if track.legend is not False:
            handles = [
                Patch(facecolor=rgba / 255, label=level.label)
                for rgba, level in zip(palette, track.levels, strict=True)
            ]
            legends.append((track.id, track.title, handles))
    if row:
        owner.set(xlim=(offset, 0), ylim=(len(order) - 0.5, -0.5))
    else:
        owner.set(xlim=(-0.5, len(order) - 0.5), ylim=(0, offset))
    owner.set_axis_off()
    return legends


def _draw_advanced(ax, image, layer, display, config, summary):
    from matplotlib.legend import Legend

    side = {"left": [], "right": [], "top": [], "bottom": []}
    missing = getattr(ax, "_mudplot_matrix_missing", False)
    needs_legend = missing
    axes = (
        ("row", "left", summary.rows, summary.row_tree, summary.row_linkage),
        ("col", "top", summary.cols, summary.col_tree, summary.col_linkage),
    )
    ratios = {}
    for name, where, _, tree, _ in axes:
        tracks = getattr(config, name + "_tracks") or ()
        legacy = getattr(config, name + "_colors")
        total = (0.04 if legacy is not None else 0.0) + sum(
            track.ratio or 0.04 for track in tracks
        )
        if total:
            ratios[name + "_tracks"] = total
            side[where].append((name + "_tracks", total))
        if tree is not None:
            ratio = (
                getattr(config, name + "_dendrogram_ratio") or config.dendrogram_ratio
            )
            ratios[name + "_tree"] = ratio
            side[where].append((name + "_tree", ratio))
        needs_legend |= any(track.legend is not False for track in tracks)
    bar_side, fraction, pad = bar_geometry(display)
    if layer.colorbar:
        side[bar_side].extend((("pad", pad), ("bar", fraction)))
    if needs_legend:
        side[config.track_legend_side or "right"].append(("legend", 0.3))
    grid, slots = matrix_slots(ax, **side)
    title_axes = ax
    metadata = {}
    legend_requests = []
    for name, _, order, tree, nodes in axes:
        if name + "_tracks" in slots:
            track_axis = side_plot(
                ax, slots, name + "_tracks", ratios[name + "_tracks"]
            )
            if name == "col":
                title_axes = track_axis
            legend_requests.extend(
                (name, *item)
                for item in _draw_tracks(
                    track_axis,
                    order,
                    getattr(config, name + "_colors"),
                    getattr(config, name + "_tracks") or (),
                    row=name == "row",
                )
            )
        if tree is not None:
            tree_axis = side_plot(ax, slots, name + "_tree", ratios[name + "_tree"])
            _draw_tree(tree_axis, tree, len(order), config, row=name == "row")
            if name == "col":
                title_axes = tree_axis
            cut = getattr(config, name + "_cut")
            if cut is not None:
                metadata[name] = _cut_tree(
                    tree_axis, nodes, order, cut, row=name == "row"
                )
    ax._mudplot_matrix_cuts = metadata
    if layer.colorbar:
        cax = side_plot(ax, slots, "bar", ratio=fraction)
        draw_colourbar(
            ax, image, layer.clabel or "", cax=cax, config=display, calibrated=True
        )
        if bar_side == "top":
            title_axes = cax
    ax._mudplot_cluster_title_axes = title_axes
    if missing:
        legend_requests.append(
            (
                "missing",
                "",
                None,
                [
                    Line2D(
                        [],
                        [],
                        color="#697078",
                        linestyle="none",
                        marker="$/$",
                        label="Source missing",
                    )
                ],
            )
        )
    if legend_requests:
        owner = side_plot(ax, slots, "legend")
        owner.set_axis_off()
        _, horizontal, pos = slots["legend"]
        legends = []
        for name, track_id, title, handles in legend_requests:
            legend = Legend(
                owner,
                handles,
                [item.get_label() for item in handles],
                loc="center",
                title=title,
                ncols=min(len(handles), 4) if horizontal else 1,
                frameon=False,
                borderaxespad=0,
            )
            panel_id = getattr(ax, "_mudplot_panel_id", None) or ax._mudplot_panel
            legend.__dict__["_mudplot_track_id"] = (panel_id, 0, name, track_id)
            owner.add_artist(legend)
            legends.append(legend)
        if not hasattr(ax.figure, "_mudplot_matrix_legend_lanes"):
            ax.figure._mudplot_matrix_legend_lanes = []
        ax.figure._mudplot_matrix_legend_lanes.append(
            (ax, owner, grid, horizontal, pos, legends)
        )


def draw_clustermap(ax, matrix, layer, cmap, *, admission=None) -> AxesImage:
    config = ClusterSpec() if layer.cluster is None else layer.cluster
    display = HeatmapSpec() if layer.heatmap is None else layer.heatmap
    summary = cluster_summary(matrix, config, admission=admission, layer=layer)
    row_labels = display.ylabels or [str(i) for i in range(matrix.shape[0])]
    col_labels = display.xlabels or [str(i) for i in range(matrix.shape[1])]
    mask = (
        None
        if display.mask is None
        else np.asarray(display.mask, dtype=bool)[np.ix_(summary.rows, summary.cols)]
    )
    ordered = replace(
        display,
        annot_data=(
            None
            if display.annot_data is None
            else [
                [display.annot_data[i][j] for j in summary.cols] for i in summary.rows
            ]
        ),
        xlabels=[col_labels[i] for i in summary.cols],
        ylabels=[row_labels[i] for i in summary.rows],
    )
    image = draw_heatmap(
        ax,
        summary.matrix,
        replace(layer, heatmap=ordered),
        cmap,
        nulls=summary.nulls,
        display_mask=mask,
    )
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")
    ax._mudplot_cluster_order = {"rows": summary.rows, "cols": summary.cols}
    if admission is not None:
        _draw_advanced(ax, image, layer, display, config, summary)
        return image
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
        align_axis(strip, ax, horizontal=True)
        title_axes = strip
        strip.imshow(
            np.array([[to_rgba(config.col_colors[i]) for i in summary.cols]]),
            aspect="auto",
        )
        strip.set_axis_off()
    if config.row_colors is not None:
        strip = ax.figure.add_subplot(grid[body_row, body_col - 1])
        align_axis(strip, ax, horizontal=False)
        strip.imshow(
            np.array([[to_rgba(config.row_colors[i])] for i in summary.rows]),
            aspect="auto",
        )
        strip.set_axis_off()
    if summary.col_tree is not None:
        tree_axes = ax.figure.add_subplot(grid[0, body_col])
        align_axis(tree_axes, ax, horizontal=True)
        _draw_tree(tree_axes, summary.col_tree, len(summary.cols), config, row=False)
        title_axes = tree_axes
    if summary.row_tree is not None:
        tree_axes = ax.figure.add_subplot(grid[body_row, 0])
        align_axis(tree_axes, ax, horizontal=False)
        _draw_tree(tree_axes, summary.row_tree, len(summary.rows), config, row=True)
    ax._mudplot_cluster_title_axes = title_axes
    if layer.colorbar:
        cax = ax.figure.add_subplot(grid[body_row, body_col + 1])
        align_axis(cax, ax, horizontal=False)
        draw_colourbar(ax, image, layer.clabel or "", cax=cax)
    return image
