"""Render independent scatter roles, with explicit non-data legend guides."""

from __future__ import annotations

import numpy as np
from matplotlib.cm import ScalarMappable
from matplotlib.colors import ListedColormap, Normalize
from matplotlib.lines import Line2D

from ._semantics import (
    categorical_fractions,
    category_key,
    numeric_guides,
    numeric_mapping,
    semantic_levels,
    semantic_rows,
)


def draw_semantic_colourbar(ax, layer, bounds, cmap):
    """One requested hue guide per shared scale and panel, separate from size."""
    if not layer.colorbar:
        return
    ax = getattr(ax, "_mudplot_semantic_guide_axis", ax)
    scale_id = layer.semantics.scale_id
    collector = getattr(ax, "_mudplot_shared_guide_collector", None)
    if collector is not None and scale_id in collector.requests:
        return  # One figure-owned bar is created from the exact shared domain.
    shown = getattr(ax, "_mudplot_semantic_colourbars", set())
    if scale_id is not None and scale_id in shown:
        return
    low, high = bounds
    label = layer.clabel if layer.clabel is not None else layer.semantics.hue
    if low == high:
        # A constant maps to the midpoint, not an invented surrounding gradient.
        mappable = ScalarMappable(
            norm=Normalize(0, 1), cmap=ListedColormap([cmap(0.5)])
        )
        bar = ax.figure.colorbar(
            mappable,
            ax=ax,
            label=label,
            boundaries=[0, 1],
            values=[0.5],
            ticks=[0.5],
        )
        bar.set_ticklabels([str(low)])
    else:
        # Guide geometry is normalized, not a second observation coordinate
        # axis. Native raw-boundary meshes overflow for valid wide domains.
        values = numeric_guides(bounds)
        ticks, _ = numeric_mapping(values, bounds)
        bar = ax.figure.colorbar(
            ScalarMappable(norm=Normalize(0, 1), cmap=cmap),
            ax=ax,
            label=label,
            ticks=ticks,
        )
        bar.set_ticklabels([str(value) for value in values])
    if scale_id is not None:
        shown.add(scale_id)
        ax._mudplot_semantic_colourbars = shown


def marker_areas(diameters):
    """Use native scatter area units without losing a positive diameter."""
    diameters = np.asarray(diameters, dtype=float)
    areas = np.square(diameters)
    if np.any((diameters > 0) & (areas == 0)):
        raise ValueError("positive semantic marker area is not representable")
    return areas


def draw_semantic_scatter(ax, columns, layer, color_iter, *, domain=None, guides=True):
    from ._render import _continuous_cmap, _decorate, _scatter_outline

    config = layer.semantics
    rows = semantic_rows(columns, layer)
    primary = getattr(ax, "_mudplot_semantic_guide_axis", ax)
    collector = getattr(primary, "_mudplot_shared_guide_collector", None)
    root_owned = collector is not None and config.scale_id in collector.requests
    native_contexts: list[dict[str, object] | None] | None = None
    if root_owned:
        native_contexts = [None for _ in rows]
    x = np.asarray([columns[layer.x][i] for i in rows], dtype=float)
    y = np.asarray([columns[layer.y][i] for i in rows], dtype=float)
    base = layer.color or (next(color_iter) if config.hue is None else "#4b5563")
    mapping_rows = rows if domain is None else domain["rows"]
    mapping_columns = columns if domain is None else domain.get("columns", columns)
    if not mapping_rows:
        return
    role_levels = {}
    role_values = {}
    mapping_values = {}
    for role in ("hue", "size", "style"):
        name = getattr(config, role)
        role_values[role] = (
            [columns[name][i] for i in rows] if name is not None else [None] * len(rows)
        )
        mapping_values[role] = (
            [mapping_columns[name][i] for i in mapping_rows] if name is not None else []
        )
        kind = "categorical" if role == "style" else getattr(config, f"{role}_kind")
        if name is not None and kind == "categorical":
            role_levels[role] = semantic_levels(
                mapping_columns, config, role, mapping_rows
            )
    cmap = _continuous_cmap(layer.cmap_kind) if config.hue_kind == "numeric" else None
    hue_bounds = size_bounds = None
    color_lookup = {}
    if config.hue is None:
        colors = [base] * len(rows)
    elif config.hue_kind == "categorical":
        if domain is None:
            color_lookup = {
                category_key(value): next(color_iter) for value in role_levels["hue"]
            }
        else:
            import matplotlib.pyplot as plt

            palette = plt.rcParams["axes.prop_cycle"].by_key()["color"]
            color_lookup = {
                category_key(value): palette[domain["offset"] + i]
                for i, value in enumerate(role_levels["hue"])
            }
        colors = [color_lookup[category_key(value)] for value in role_values["hue"]]
    else:
        _, hue_bounds = numeric_mapping(mapping_values["hue"], config.hue_norm)
        fractions, _ = numeric_mapping(role_values["hue"], hue_bounds)
        assert cmap is not None
        colors = cmap(fractions)
    if config.size is None:
        diameters = [6.0 if layer.marker_size is None else layer.marker_size] * len(
            rows
        )
    else:
        if config.size_kind == "numeric":
            _, size_bounds = numeric_mapping(mapping_values["size"], config.size_norm)
            fractions, _ = numeric_mapping(role_values["size"], size_bounds)
        else:
            fractions = categorical_fractions(role_values["size"], role_levels["size"])
        low, high = config.sizes
        diameters = [low * (1 - t) + high * t for t in fractions]
    areas = marker_areas(diameters)
    styles = role_levels.get("style", [None])
    for index, value in enumerate(styles):
        selection = np.asarray(
            [
                config.style is None or category_key(item) == category_key(value)
                for item in role_values["style"]
            ],
            dtype=bool,
        )
        if not selection.any():
            continue  # Reserve marker slot; never invent observations/legend data.
        marker = (
            (layer.marker or "o") if config.style is None else config.markers[index]
        )
        outline = _scatter_outline(layer)
        native = ax.scatter(
            x[selection],
            y[selection],
            c=np.asarray(colors)[selection],
            s=areas[selection],
            marker=marker,
            alpha=layer.alpha,
            label="_nolegend_",
            **outline,
        )
        if native_contexts is not None:
            faces, edges = native.get_facecolors(), native.get_edgecolors()
            sizes, widths = native.get_sizes(), native.get_linewidths()
            for local, row_index in enumerate(np.flatnonzero(selection)):
                native_contexts[row_index] = {
                    "color": faces[min(local, len(faces) - 1)]
                    if len(faces)
                    else "none",
                    "edgecolor": edges[min(local, len(edges) - 1)]
                    if len(edges)
                    else "none",
                    "edge_fixed": layer.edge_color is not None,
                    "edgewidth": widths[min(local, len(widths) - 1)],
                    "diameter": float(np.sqrt(sizes[min(local, len(sizes) - 1)])),
                    "marker": marker,
                    "width": 0,
                    "dash": "None",
                    "alpha": native.get_alpha(),
                }
    if rows and hue_bounds is not None:
        draw_semantic_colourbar(ax, layer, hue_bounds, cmap)

    def proxy(label, *, color=base, marker="o", diameter=6, role=None, value=None):
        handle = Line2D(
            [],
            [],
            linestyle="None",
            marker=marker,
            markersize=diameter,
            markerfacecolor=color,
            markeredgecolor=(color if layer.edge_color is None else layer.edge_color),
            alpha=layer.alpha,
            **(
                {}
                if layer.line_width is None
                else {"markeredgewidth": layer.line_width}
            ),
            label=label,
        )
        ax.add_line(handle)
        if role is not None and root_owned:
            if not rows:
                handle.remove()
                return
            from ._shared_guides import tag_entry

            index = next(
                (
                    i
                    for i, actual in enumerate(role_values[role])
                    if category_key(actual) == category_key(value)
                ),
                0,
            )
            assert native_contexts is not None
            tag_entry(ax, handle, layer, role, value, context=native_contexts[index])

    if layer.label:
        proxy(_decorate(layer.label, layer.citation, layer.href), marker="None")
    if not config.legend or not guides:
        return
    for role in ("hue", "size", "style"):
        column = getattr(config, role)
        if column is None:
            continue
        if role == "hue" and config.hue_kind == "numeric" and layer.colorbar:
            continue
        kind = "categorical" if role == "style" else getattr(config, f"{role}_kind")
        if kind == "categorical":
            observed = {category_key(value) for value in mapping_values[role]}
            selected = role_levels[role]
            for i, value in enumerate(selected):
                if category_key(value) not in observed:
                    continue
                color = color_lookup[category_key(value)] if role == "hue" else base
                marker = config.markers[i] if role == "style" else "o"
                diameter = 6
                if role == "size":
                    t = 0.5 if len(selected) == 1 else i / (len(selected) - 1)
                    diameter = config.sizes[0] * (1 - t) + config.sizes[1] * t
                proxy(
                    f"{role}: {column}={value}",
                    color=color,
                    marker=marker,
                    diameter=diameter,
                    role=role,
                    value=value,
                )
        else:
            bounds = hue_bounds if role == "hue" else size_bounds
            assert bounds is not None
            guides = numeric_guides(bounds)
            fractions, _ = numeric_mapping(
                guides, bounds if bounds[0] != bounds[1] else None
            )
            for value, t in zip(guides, fractions, strict=True):
                if role == "hue":
                    assert cmap is not None
                    color = cmap(t)
                else:
                    color = base
                diameter = (
                    config.sizes[0] * (1 - t) + config.sizes[1] * t
                    if role == "size"
                    else 6
                )
                proxy(
                    f"{role}: {column}={value}",
                    color=color,
                    diameter=diameter,
                    role=role,
                    value=value,
                )
