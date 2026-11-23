"""Native observation segments with independent axes-fraction extent."""

from __future__ import annotations

from typing import Any, Literal, Protocol, cast

import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D

from ._semantics import (
    categorical_fractions,
    category_key,
    numeric_guides,
    numeric_mapping,
    semantic_levels,
    semantic_rows,
)


class _NativeStrokeWidths(Protocol):
    def get_linewidths(self) -> np.ndarray: ...


def draw_rug_collection(ax, values, layer, *, colors, widths, dashes, label):
    """Only the observation dimension contributes to dataLim/autoscaling.

    Explicit autolim=False avoids the older Matplotlib collection path treating
    the axes fraction as data, including on logarithmic/calendar perpendicular
    axes. The blended transform stays live through DPI/layout/limit changes.
    """
    vertical = layer.orient == "v"
    height = 0.04 if layer.width is None else layer.width
    start = 1.0 if not vertical and layer.axis == "y2" else 0.0
    end = start - height if start else height
    segments = np.empty((len(values), 2, 2), dtype=float)
    observation = 0 if vertical else 1
    segments[:, :, observation] = np.asarray(values)[:, None]
    segments[:, 0, 1 - observation] = start
    segments[:, 1, 1 - observation] = end
    collection = LineCollection(
        cast(Any, segments),
        colors=colors,
        linewidths=widths,
        linestyles=dashes,
        transform=ax.get_xaxis_transform() if vertical else ax.get_yaxis_transform(),
        alpha=layer.alpha,
        label=label,
    )
    ax.add_collection(collection, autolim=False)
    finite = np.isfinite(values)
    if finite.any():
        ax.update_datalim(
            segments[finite, 0, :], updatex=vertical, updatey=not vertical
        )
        # Native vlines/hlines request both views; keep their empty-axis framing
        # while the perpendicular data interval (and any populated view) is intact.
        ax._request_autoscale_view()
    return collection


def draw_semantic_rug(ax, columns, layer, color_iter, *, domain=None, guides=True):
    from matplotlib import pyplot as plt

    from ._render import _continuous_cmap, _decorate
    from ._scatter_semantics import draw_semantic_colourbar

    cfg = layer.semantics
    rows = semantic_rows(columns, layer)
    pool = rows if domain is None else domain["rows"]
    mapping_columns = columns if domain is None else domain["columns"]
    base = layer.color or (next(color_iter) if cfg.hue is None else "#4b5563")
    values, levels, bounds, fractions = {}, {}, {}, {}
    for role in ("hue", "size", "style"):
        name = getattr(cfg, role)
        if name is None:
            continue
        values[role] = [mapping_columns[name][i] for i in pool]
        actual = [columns[name][i] for i in rows]
        kind = "categorical" if role == "style" else getattr(cfg, f"{role}_kind")
        if kind == "categorical":
            levels[role] = semantic_levels(mapping_columns, cfg, role, pool)
            fractions[role] = categorical_fractions(actual, levels[role])
        elif pool:
            _, bounds[role] = numeric_mapping(
                values[role], getattr(cfg, f"{role}_norm")
            )
            fractions[role], _ = numeric_mapping(actual, bounds[role])
    cmap = _continuous_cmap(layer.cmap_kind) if cfg.hue_kind == "numeric" else None
    palette = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    hue_colors = {
        category_key(value): next(color_iter)
        if domain is None
        else palette[domain["offset"] + i]
        for i, value in enumerate(levels.get("hue", []))
    }
    colors = base
    if cfg.hue is not None and cfg.hue_kind == "categorical":
        colors = [hue_colors[category_key(columns[cfg.hue][i])] for i in rows]
    elif cfg.hue is not None and rows:
        assert cmap is not None
        colors = cmap(fractions["hue"])
    widths = layer.line_width
    if cfg.size is not None:
        low, high = cfg.sizes
        widths = [low * (1 - t) + high * t for t in fractions.get("size", [])]
    patterns = cfg.dashes or ("-", "--", "-.", ":")
    style_lookup = {
        category_key(value): patterns[i]
        for i, value in enumerate(levels.get("style", []))
    }
    dashes = layer.line_style or "-"
    if cfg.style is not None:
        dashes = [style_lookup[category_key(columns[cfg.style][i])] for i in rows]
    if widths is not None:
        if np.isscalar(widths):
            if widths == 0:
                dashes = "-"
        else:
            # A zero stroke has no dash geometry. Native solid zero-width lines
            # preserve all segments while avoiding 3.8's invalid all-zero dash.
            dashes = [
                "-" if width == 0 else dashes if isinstance(dashes, str) else dashes[i]
                for i, width in enumerate(widths)
            ]
    native = draw_rug_collection(
        ax,
        np.asarray([columns[layer.x][i] for i in rows], dtype=float),
        layer,
        colors=colors,
        widths=widths,
        dashes=dashes,
        label="_nolegend_",
    )
    if not pool:
        return
    if rows and cfg.hue is not None and cfg.hue_kind == "numeric":
        draw_semantic_colourbar(ax, layer, bounds["hue"], cmap)

    def proxy(
        label,
        *,
        color=base,
        width=1.25,
        dash: Literal["-", "--", "-.", ":"] = "-",
        header=False,
        role=None,
        value=None,
    ):
        handle = Line2D(
            [],
            [],
            color=color,
            linewidth=width,
            linestyle="None" if width == 0 or header else dash,
            alpha=layer.alpha,
            label=label,
        )
        ax.add_line(handle)
        if role is not None:
            primary = getattr(ax, "_mudplot_semantic_guide_axis", ax)
            collector = getattr(primary, "_mudplot_shared_guide_collector", None)
            if collector is not None and cfg.scale_id in collector.requests:
                if not rows:
                    handle.remove()
                    return
                from ._shared_guides import tag_entry

                index = next(
                    (
                        i
                        for i, row in enumerate(rows)
                        if category_key(columns[getattr(cfg, role)][row])
                        == category_key(value)
                    ),
                    0,
                )
                colors_actual, widths_actual = (
                    native.get_colors(),
                    cast(_NativeStrokeWidths, native).get_linewidths(),
                )
                context = {
                    "color": colors_actual[min(index, len(colors_actual) - 1)]
                    if len(colors_actual)
                    else "none",
                    "width": widths_actual[min(index, len(widths_actual) - 1)],
                    "dash": dashes if isinstance(dashes, str) else dashes[index],
                    "marker": "None",
                    "diameter": 0,
                    "edgecolor": "none",
                    "edge_fixed": True,
                    "alpha": native.get_alpha(),
                }
                tag_entry(ax, handle, layer, role, value, context=context)

    if layer.label:
        proxy(_decorate(layer.label, layer.citation, layer.href), header=True)
    if not cfg.legend or not guides:
        return
    for role in ("hue", "size", "style"):
        column = getattr(cfg, role)
        if column is None or (
            role == "hue" and cfg.hue_kind == "numeric" and layer.colorbar
        ):
            continue
        kind = "categorical" if role == "style" else getattr(cfg, f"{role}_kind")
        selected = (
            levels[role] if kind == "categorical" else numeric_guides(bounds[role])
        )
        ts = (
            categorical_fractions(selected, selected)
            if kind == "categorical"
            else numeric_mapping(selected, bounds[role])[0]
        )
        observed = {category_key(v) for v in values[role]}
        for i, (value, t) in enumerate(zip(selected, ts, strict=True)):
            if kind == "categorical" and category_key(value) not in observed:
                continue
            color, width, dash = base, 1.25, "-"
            if role == "hue":
                if kind == "categorical":
                    color = hue_colors[category_key(value)]
                else:
                    assert cmap is not None
                    color = cmap(t)
            elif role == "size":
                width = cfg.sizes[0] * (1 - t) + cfg.sizes[1] * t
            else:
                dash = patterns[i]
            prefix = "size (rug stroke, pt)" if role == "size" else role
            proxy(
                f"{prefix}: {column}={value}",
                color=color,
                width=width,
                dash=dash,
                role=role,
                value=value,
            )
