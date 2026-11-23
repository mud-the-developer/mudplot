"""Draw row-aligned native lane paths without sorting or autoscale hints."""

from collections.abc import Sequence
from typing import cast

import numpy as np
from matplotlib import rcParams
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from numpy.typing import ArrayLike

from ._lanes import plan_lanes
from ._semantics import (
    categorical_fractions,
    category_key,
    numeric_guides,
    numeric_mapping,
    semantic_levels,
)

EVENT_DASHES = ("-", "--", "-.", ":")


def draw_lanes(ax, columns, layer, panel, color_iter, *, domain=None):
    from ._render import _continuous_cmap, _decorate
    from ._scatter_semantics import draw_semantic_colourbar
    from ._shared_guides import tag_entry

    plan = plan_lanes(columns, layer, panel)
    config = layer.semantics
    mapped = config is not None and config.hue is not None
    group_colors = (
        [] if mapped else [layer.color or next(color_iter) for _ in plan.levels]
    )
    if not plan.members:
        return
    rows, slots = zip(*plan.members, strict=True)
    event = layer.type == "eventplot"
    size = len(rows)
    colors = [group_colors[i] for i in slots] if not mapped else ["#4b5563"] * size
    width = (
        rcParams["lines.linewidth"] if layer.line_width is None else layer.line_width
    )
    dash = layer.line_style or "-"
    widths, dashes = [width] * size, [dash] * size
    levels, bounds = {}, {}
    cmap = None
    if config is not None:
        pool = rows if domain is None else domain["rows"]
        source = columns if domain is None else domain["columns"]
        for role in ("hue", "size", "style"):
            name = getattr(config, role)
            if name is None:
                continue
            actual = [columns[name][i] for i in rows]
            numeric = role != "style" and getattr(config, f"{role}_kind") == "numeric"
            if numeric:
                _, bounds[role] = numeric_mapping(
                    [source[name][i] for i in pool], getattr(config, f"{role}_norm")
                )
                fractions, _ = numeric_mapping(actual, bounds[role])
            else:
                levels[role] = semantic_levels(source, config, role, pool)
                fractions = categorical_fractions(actual, levels[role])
            if role == "hue":
                if numeric:
                    cmap = _continuous_cmap(layer.cmap_kind)
                    colors = [tuple(color) for color in cmap(fractions)]
                else:
                    palette = rcParams["axes.prop_cycle"].by_key()["color"]
                    hue_colors = {
                        category_key(value): next(color_iter)
                        if domain is None
                        else palette[domain["offset"] + i]
                        for i, value in enumerate(levels[role])
                    }
                    colors = [hue_colors[category_key(value)] for value in actual]
            elif role == "size":
                low, high = config.sizes
                widths = [low * (1 - t) + high * t for t in fractions]
            else:
                patterns = config.dashes or EVENT_DASHES
                styles = {
                    category_key(value): patterns[i]
                    for i, value in enumerate(levels[role])
                }
                dashes = [styles[category_key(value)] for value in actual]

    points = np.empty((size, 2 if event else 4, 2))
    for i, (start, index) in enumerate(zip(plan.starts, slots, strict=True)):
        bottom, top = plan.spans[index]
        if event:
            points[i] = ((start, top), (start, bottom))
        else:
            assert plan.ends is not None
            right = plan.ends[i]
            points[i] = ((start, bottom), (start, top), (right, top), (right, bottom))
    styles = [style if w else "-" for style, w in zip(dashes, widths, strict=True)]
    options = {
        "linewidths": widths,
        "linestyles": styles,
        "alpha": layer.alpha,
        "label": "_nolegend_",
    }
    native_points = cast("Sequence[ArrayLike]", points)
    if event:
        artist = LineCollection(native_points, colors=colors, **options)
    else:
        artist = PolyCollection(
            native_points,
            facecolors=colors,
            edgecolors=layer.edge_color or colors,
            **options,
        )
    ax.add_collection(artist, autolim=False)
    ax.update_datalim(points.reshape(-1, 2))
    ax.autoscale_view()

    def proxy(index, text, *, role=None, value=None, color=None, stroke=None):
        ink = colors[index] if color is None else color
        physical = widths[index] if stroke is None else stroke
        linestyle = dashes[index] if physical else "None"
        if event:
            handle = Line2D(
                [],
                [],
                color=ink,
                linewidth=physical,
                linestyle=linestyle,
                alpha=layer.alpha,
                label=text,
            )
            ax.add_line(handle)
            if role is not None:
                tag_entry(
                    ax,
                    handle,
                    layer,
                    role,
                    value,
                    context={
                        "color": colors[index],
                        "width": widths[index],
                        "dash": dashes[index],
                        "marker": "None",
                        "diameter": 0,
                        "edgecolor": "none",
                        "edge_fixed": True,
                        "alpha": layer.alpha,
                    },
                )
        else:
            handle = Rectangle(
                (0, 0),
                0,
                0,
                visible=False,
                facecolor=ink,
                edgecolor=layer.edge_color or ink,
                linewidth=physical,
                linestyle=linestyle,
                alpha=layer.alpha,
                label=text,
            )
            ax.add_artist(handle)  # No geometry or data-limit contribution.

    if layer.group is not None and not mapped:
        observed = {}
        for i, slot in enumerate(slots):
            observed.setdefault(slot, i)
        for slot, label in enumerate(plan.levels):
            if slot in observed:
                proxy(observed[slot], _decorate(str(label), layer.citation, layer.href))
    elif layer.label:
        proxy(0, _decorate(layer.label, layer.citation, layer.href))
    if config is None:
        return
    if cmap is not None:
        draw_semantic_colourbar(ax, layer, bounds["hue"], cmap)
    if not config.legend:
        return
    for role in ("hue", "size", "style"):
        name = getattr(config, role)
        if name is None or (role == "hue" and layer.colorbar):
            continue
        prefix = "size (event tick stroke, pt)" if role == "size" else role
        if role in bounds:
            samples = numeric_guides(bounds[role])
            fractions, _ = numeric_mapping(samples, bounds[role])
            for value, t in zip(samples, fractions, strict=True):
                if role == "hue":
                    assert cmap is not None
                    proxy(
                        0,
                        f"{prefix}: {name}={value}",
                        role=role,
                        value=value,
                        color=tuple(cmap(t)),
                    )
                else:
                    low, high = config.sizes
                    proxy(
                        0,
                        f"{prefix}: {name}={value}",
                        role=role,
                        value=value,
                        stroke=low * (1 - t) + high * t,
                    )
        else:
            observed = {}
            for i, row in enumerate(rows):
                observed.setdefault(category_key(columns[name][row]), i)
            for value in levels[role]:
                key = category_key(value)
                if key in observed:
                    proxy(
                        observed[key],
                        f"{prefix}: {name}={value}",
                        role=role,
                        value=value,
                    )
