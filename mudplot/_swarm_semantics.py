"""Shared raw-row mappings for native swarm paths and non-data guides."""

from ._semantics import (
    categorical_fractions,
    category_key,
    numeric_guides,
    numeric_mapping,
    semantic_levels,
)


def appearance(columns, layer, rows, color_iter, *, domain=None):
    from matplotlib import pyplot as plt

    from ._render import _continuous_cmap

    config = layer.semantics
    pool = rows if domain is None else domain["rows"]
    source = columns if domain is None else domain["columns"]
    levels, values, bounds, fractions = {}, {}, {}, {}
    for role in ("hue", "size", "style"):
        name = getattr(config, role)
        if name is None:
            continue
        values[role] = [source[name][i] for i in pool]
        actual = [columns[name][i] for i in rows]
        kind = "categorical" if role == "style" else getattr(config, f"{role}_kind")
        if kind == "categorical":
            levels[role] = semantic_levels(source, config, role, pool)
            fractions[role] = categorical_fractions(actual, levels[role])
        else:
            _, bounds[role] = numeric_mapping(
                values[role], getattr(config, f"{role}_norm")
            )
            fractions[role], _ = numeric_mapping(actual, bounds[role])
    cmap = _continuous_cmap(layer.cmap_kind) if config.hue_kind == "numeric" else None
    colors, diameters, markers = None, None, None
    hue_colors = {}
    if config.hue is not None:
        if config.hue_kind == "categorical":
            palette = plt.rcParams["axes.prop_cycle"].by_key()["color"]
            hue_colors = {
                category_key(value): next(color_iter)
                if domain is None
                else palette[domain["offset"] + i]
                for i, value in enumerate(levels["hue"])
            }
            colors = [hue_colors[category_key(columns[config.hue][i])] for i in rows]
        else:
            assert cmap is not None
            colors = cmap(fractions["hue"])
    if config.size is not None:
        low, high = config.sizes
        diameters = [low * (1 - t) + high * t for t in fractions["size"]]
    if config.style is not None:
        lookup = {
            category_key(value): config.markers[i]
            for i, value in enumerate(levels["style"])
        }
        markers = [lookup[category_key(columns[config.style][i])] for i in rows]
    return (
        colors,
        diameters,
        markers,
        {
            "levels": levels,
            "values": values,
            "bounds": bounds,
            "cmap": cmap,
            "hue_colors": hue_colors,
        },
    )


def guides(ax, layer, context, *, show=True):
    from ._scatter_semantics import draw_semantic_colourbar

    config = layer.semantics
    if config.hue is not None and config.hue_kind == "numeric":
        draw_semantic_colourbar(ax, layer, context["bounds"]["hue"], context["cmap"])
    if not show or not config.legend:
        return
    base = layer.color or "#4b5563"
    for role in ("hue", "size", "style"):
        name = getattr(config, role)
        if name is None or (
            role == "hue" and config.hue_kind == "numeric" and layer.colorbar
        ):
            continue
        kind = "categorical" if role == "style" else getattr(config, f"{role}_kind")
        selected = (
            context["levels"][role]
            if kind == "categorical"
            else numeric_guides(context["bounds"][role])
        )
        fractions = (
            categorical_fractions(selected, selected)
            if kind == "categorical"
            else numeric_mapping(selected, context["bounds"][role])[0]
        )
        observed = {category_key(value) for value in context["values"][role]}
        for i, (value, fraction) in enumerate(zip(selected, fractions, strict=True)):
            if kind == "categorical" and category_key(value) not in observed:
                continue
            color, diameter = base, 6
            marker = layer.marker or (config.markers[0] if config.style else "o")
            if role == "hue":
                color = (
                    context["hue_colors"][category_key(value)]
                    if kind == "categorical"
                    else context["cmap"](fraction)
                )
            elif role == "size":
                diameter = config.sizes[0] * (1 - fraction) + config.sizes[1] * fraction
            else:
                marker = config.markers[i]
            handle = ax.plot(
                [],
                [],
                linestyle="none",
                marker=marker,
                markersize=diameter,
                markeredgewidth=0.5 if layer.line_width is None else layer.line_width,
                markeredgecolor=layer.edge_color or "white",
                color=color,
                alpha=layer.alpha,
                label=f"{role}: {name}={value}",
            )[0]
            native = context.get("native_contexts")
            if native:
                from ._shared_guides import tag_entry

                index = next(
                    (
                        j
                        for j, actual in enumerate(context["actual_values"][role])
                        if category_key(actual) == category_key(value)
                    ),
                    0,
                )
                tag_entry(ax, handle, layer, role, value, context=native[index])
