"""Native stems with bounded collection-based grouping and semantic styling."""

from collections.abc import Sequence
from typing import TYPE_CHECKING, cast

import numpy as np
from matplotlib import rcParams
from matplotlib.collections import LineCollection, PathCollection
from matplotlib.lines import Line2D
from matplotlib.markers import MarkerStyle
from matplotlib.transforms import IdentityTransform
from numpy.typing import ArrayLike

from ._semantics import (
    categorical_fractions,
    category_key,
    numeric_guides,
    numeric_mapping,
    semantic_levels,
)
from ._stem import stem_group_levels, stem_rows

if TYPE_CHECKING:
    from matplotlib.typing import ColorType


def draw_stems(ax, columns, layer, color_iter, *, domain=None):
    from ._render import _continuous_cmap, _decorate
    from ._scatter_semantics import draw_semantic_colourbar
    from ._shared_guides import tag_entry

    rows = stem_rows(columns, layer)
    groups = stem_group_levels(columns, layer, rows)
    group_colors = {
        category_key(value): layer.color or next(color_iter) for value in groups
    }
    if not rows:
        return
    x = np.array([columns[layer.x][i] for i in rows], dtype=float)
    y = np.array([columns[layer.y][i] for i in rows], dtype=float)
    bottom = 0 if layer.baseline is None else layer.baseline
    horizontal = layer.orient == "h"
    diameter = 6 if layer.marker_size is None else layer.marker_size
    marker = layer.marker or "o"
    dash = layer.line_style or "-"
    width = (
        rcParams["lines.linewidth"] if layer.line_width is None else layer.line_width
    )
    config = layer.semantics
    label = _decorate(layer.label, layer.citation, layer.href)
    if config is None and not groups:
        color = layer.color or next(color_iter)
        container = ax.stem(
            x,
            y,
            bottom=bottom,
            orientation="horizontal" if horizontal else "vertical",
            linefmt="-",
            markerfmt="o",
            basefmt="-",
            label=label,
        )
        container.markerline.set_marker(marker)
        container.markerline.set_markersize(diameter)
        container.markerline.set_color(color)
        container.markerline.set_alpha(layer.alpha)
        for artist in (container.stemlines, container.baseline):
            artist.set_color(color)
            artist.set_alpha(layer.alpha)
            artist.set_linestyle(dash if width else "-")
            if layer.line_width is not None:
                artist.set_linewidth(layer.line_width)
        return

    baseline_color = layer.color or "#4b5563"
    size = len(rows)
    group_keys = []
    if groups:
        group_keys = [category_key(columns[layer.group][i]) for i in rows]
        colors = [group_colors[key] for key in group_keys]
    else:
        assert config is not None
        base = layer.color or (
            next(color_iter) if config.hue is None else baseline_color
        )
        colors = [base] * size
    widths, markers, dashes = [width] * size, [marker] * size, [dash] * size
    pool = rows if domain is None else domain["rows"]
    source = columns if domain is None else domain["columns"]
    levels, bounds, hue_colors = {}, {}, {}
    cmap = None
    if config is not None:
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
                    colors = cmap(fractions)
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
                slots = {category_key(value): i for i, value in enumerate(levels[role])}
                indices = [slots[category_key(value)] for value in actual]
                markers = [config.markers[i] for i in indices]
                if config.dashes is not None:
                    dashes = [config.dashes[i] for i in indices]

    segments = np.empty((size, 2, 2))
    pos, val = (1, 0) if horizontal else (0, 1)
    segments[:, :, pos] = x[:, None]
    segments[:, 0, val] = bottom
    segments[:, 1, val] = y
    line = LineCollection(
        cast("Sequence[ArrayLike]", segments),
        colors=colors,
        linewidths=widths,
        linestyles=[
            style if w else "-" for style, w in zip(dashes, widths, strict=True)
        ],
        alpha=layer.alpha,
        zorder=2,
    )
    ax.add_collection(line, autolim=False)
    heads = segments[:, 1, :]
    edgewidth = rcParams["lines.markeredgewidth"]
    if diameter:
        batches = {}
        for i, shape in enumerate(markers):
            batches.setdefault(shape, []).append(i)
        for shape, indices in batches.items():
            style = MarkerStyle(shape)
            path = style.get_path().transformed(style.get_transform())
            head = PathCollection(
                [path],
                sizes=[diameter**2],
                offsets=heads[indices],
                offset_transform=ax.transData,
                facecolors=[colors[i] for i in indices],
                edgecolors="face",
                linewidths=edgewidth,
                alpha=layer.alpha,
                zorder=2.1,
            )
            head.set_transform(IdentityTransform())
            if not style.is_filled():
                head.set_edgecolor(
                    cast("list[ColorType]", [colors[i] for i in indices])
                )
                head.set_facecolor("none")
            ax.add_collection(head, autolim=False)
    ends = (
        ([bottom, bottom], [x.min(), x.max()])
        if horizontal
        else ([x.min(), x.max()], [bottom, bottom])
    )
    ax.plot(
        *ends,
        color=baseline_color,
        linewidth=width,
        linestyle=dash if width else "-",
        alpha=layer.alpha,
        label="_nolegend_",
    )
    ax.update_datalim(segments.reshape(-1, 2))
    ax.autoscale_view()

    def representative(index, text, *, role=None, value=None, color=None, stroke=None):
        main = colors[index] if color is None else color
        physical = widths[index] if stroke is None else stroke
        handle = Line2D(
            [],
            [],
            color=cast("ColorType", main),
            linewidth=physical,
            linestyle=dashes[index] if physical else "None",
            marker=markers[index],
            markersize=diameter,
            markeredgewidth=edgewidth,
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
                    "marker": markers[index],
                    "diameter": diameter,
                    "edgewidth": edgewidth,
                    "alpha": layer.alpha,
                },
            )

    if groups:
        observed = {}
        for i, key in enumerate(group_keys):
            observed.setdefault(key, i)
        for value in groups:
            key = category_key(value)
            if key in observed:
                representative(observed[key], str(value))
    elif label:
        representative(0, label)
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
        prefix = "size (stem stroke, pt)" if role == "size" else role
        if role in bounds:
            samples = numeric_guides(bounds[role])
            fractions, _ = numeric_mapping(samples, bounds[role])
            for value, t in zip(samples, fractions, strict=True):
                if role == "hue":
                    assert cmap is not None
                    representative(
                        0,
                        f"{prefix}: {name}={value}",
                        role=role,
                        value=value,
                        color=cmap(t),
                    )
                else:
                    low, high = config.sizes
                    representative(
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
                    representative(
                        observed[key],
                        f"{prefix}: {name}={value}",
                        role=role,
                        value=value,
                    )
