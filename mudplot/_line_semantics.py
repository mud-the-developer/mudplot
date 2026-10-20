"""Lineplot role effects; raw tuples define curves, guides never define data."""

from __future__ import annotations

from typing import Literal

from matplotlib import pyplot as plt
from matplotlib.lines import Line2D

from ._lineplot import draw_lineplot
from ._semantics import (
    categorical_fractions,
    category_key,
    line_semantic_input,
    numeric_guides,
    numeric_mapping,
    semantic_levels,
    semantic_rows,
)


def draw_semantic_lineplot(
    ax, columns, layer, color_iter, theme, *, domain=None, guides=True
):
    from ._render import _continuous_cmap, _decorate

    cfg = layer.semantics
    rows = semantic_rows(columns, layer)
    pool = rows if domain is None else domain["rows"]
    mapping_columns = columns if domain is None else domain.get("columns", columns)
    data, temporary, curves = line_semantic_input(columns, layer)
    base = layer.color or (next(color_iter) if cfg.hue is None else "#4b5563")
    if not pool:
        return
    levels, bounds, fractions, values = {}, {}, {}, {}
    for role in ("hue", "size", "style"):
        column = getattr(cfg, role)
        if column is None:
            continue
        values[role] = [mapping_columns[column][i] for i in pool]
        kind = "categorical" if role == "style" else getattr(cfg, f"{role}_kind")
        actual = [curve[role] for curve in curves]
        if kind == "categorical":
            levels[role] = semantic_levels(mapping_columns, cfg, role, pool)
            fractions[role] = categorical_fractions(actual, levels[role])
        else:
            _, bounds[role] = numeric_mapping(
                values[role], getattr(cfg, f"{role}_norm")
            )
            fractions[role], _ = numeric_mapping(actual, bounds[role])
    cmap = _continuous_cmap(layer.cmap_kind) if cfg.hue_kind == "numeric" else None
    hue_colors = {}
    if cfg.hue is not None and cfg.hue_kind == "categorical":
        palette = plt.rcParams["axes.prop_cycle"].by_key()["color"]
        hue_colors = {
            category_key(value): next(color_iter)
            if domain is None
            else palette[domain["offset"] + i]
            for i, value in enumerate(levels["hue"])
        }
    style_positions = {
        category_key(v): i for i, v in enumerate(levels.get("style", []))
    }
    mapped = {}
    for i, curve in enumerate(curves):
        color = base
        if cfg.hue is not None:
            if cfg.hue_kind == "categorical":
                color = hue_colors[category_key(curve["hue"])]
            else:
                assert cmap is not None
                color = cmap(fractions["hue"][i])
        width = 1.25 if layer.line_width is None else layer.line_width
        if cfg.size is not None:
            t = fractions["size"][i]
            width = cfg.sizes[0] * (1 - t) + cfg.sizes[1] * t
        marker, dash = layer.marker or "None", layer.line_style or "-"
        if cfg.style is not None:
            index = style_positions[category_key(curve["style"])]
            marker = cfg.markers[index]
            if cfg.dashes is not None:
                dash = cfg.dashes[index]
        mapped[i] = {"color": color, "width": width, "marker": marker, "dash": dash}
    # Existing pointwise estimator/cell resampling/order/band checks, one RNG.
    draw_lineplot(ax, data, temporary, color_iter, theme, curve_styles=mapped)

    def proxy(
        label,
        *,
        color=base,
        width=1.25,
        marker="None",
        dash: Literal["-", "--", "-.", ":"] = "-",
        header=False,
    ):
        ax.add_line(
            Line2D(
                [],
                [],
                color=color,
                linewidth=width,
                linestyle="None" if width == 0 or header else dash,
                marker=marker,
                markersize=5 if layer.marker_size is None else layer.marker_size,
                alpha=layer.alpha,
                label=label,
            )
        )

    if layer.label:
        proxy(_decorate(layer.label, layer.citation, layer.href), header=True)
    if not cfg.legend or not guides:
        return
    for role in ("hue", "size", "style"):
        column = getattr(cfg, role)
        if column is None:
            continue
        prefix = "size (line width, pt)" if role == "size" else role
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
            color, width, marker, dash = base, 1.25, "None", "-"
            if role == "hue":
                if kind == "categorical":
                    color = hue_colors[category_key(value)]
                else:
                    assert cmap is not None
                    color = cmap(t)
            elif role == "size":
                width = cfg.sizes[0] * (1 - t) + cfg.sizes[1] * t
            elif role == "style":
                marker = cfg.markers[i]
                if cfg.dashes is not None:
                    dash = cfg.dashes[i]
            proxy(
                f"{prefix}: {column}={value}",
                color=color,
                width=width,
                marker=marker,
                dash=dash,
            )
