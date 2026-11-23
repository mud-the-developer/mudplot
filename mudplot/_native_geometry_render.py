"""Real Matplotlib artists for finite planar geometry; no statistical effects."""

from itertools import pairwise

from ._components import apply_component_style
from ._native_geometry import SEGMENTS, SPANS


def apply_scatter_style(artist, style):
    if style.color is not None or style.face_color is not None:
        artist.set_facecolors(style.face_color or style.color)
    if style.edge_color is not None:
        artist.set_edgecolors(style.edge_color)
    if style.marker_size is not None:
        artist.set_sizes([style.marker_size**2])
    if style.line_width is not None:
        artist.set_linewidth(style.line_width)
    if style.line_style is not None:
        artist.set_linestyle(
            "solid" if style.line_style == "none" else style.line_style
        )
        if style.line_style == "none":
            artist.set_linewidth(0)
    if style.alpha is not None:
        artist.set_alpha(style.alpha)


def draw_geometry(ax, layer, prepared, colors, index):
    import numpy as np

    from ._native_annotations import apply_path_effects, draw_literal
    from ._native_geometry import LITERALS
    from ._render import _decorate

    kind = layer.type
    style = layer.native_style
    if kind in LITERALS:
        draw_literal(ax, layer, prepared, colors, index)
        return
    if kind in {"bar", "barh", "pie"}:
        from ._native_bars import draw_bars, draw_pie

        (draw_pie if kind == "pie" else draw_bars)(ax, layer, prepared, colors)
        return
    if kind in SEGMENTS:
        draw = ax.hlines if kind == "hlines" else ax.vlines
        ink = layer.color or next(colors)
        artist = draw(
            *prepared,
            colors=ink,
            linewidths=layer.line_width,
            linestyles=layer.line_style or "solid",
            alpha=layer.alpha,
            label=_decorate(layer.label, layer.citation, layer.href),
        )
        apply_component_style(artist, style)
        apply_path_effects(artist, layer.path_effects)
        return
    if kind in SPANS:
        draw = ax.axhspan if kind == "hspan" else ax.axvspan
        artist = draw(
            *prepared,
            color=layer.color or next(colors),
            alpha=layer.alpha,
            label=_decorate(layer.label, layer.citation, layer.href),
        )
        apply_component_style(artist, style, body=True)
        apply_path_effects(artist, layer.path_effects, body=True)
        return
    for key, xs, ys, errors in prepared if kind == "errorbar" else ():
        ink = layer.color or next(colors)
        if not xs:
            continue
        label = layer.label if key is None else str(key)
        marker = (style.marker if style else None) or layer.marker or "o"
        # Line and error ranges have separate existing stroke owners.
        container = ax.errorbar(
            xs,
            ys,
            xerr=errors[0],
            yerr=errors[1],
            fmt=marker,
            label=_decorate(label, layer.citation, layer.href),
            color=ink,
            alpha=layer.alpha,
            markersize=layer.marker_size or 4,
            linewidth=layer.line_width,
            ecolor=layer.error_color,
            elinewidth=layer.error_line_width,
            capsize=2 if layer.capsize is None else layer.capsize,
            capthick=layer.capthick,
        )
        point = container.lines[0]
        if point is not None:
            apply_component_style(point, style)
    if kind == "band":
        draw = ax.fill_betweenx if layer.orient == "h" else ax.fill_between
        cfg = layer.fill
        for key, series, where in prepared:
            ink = layer.color or next(colors)
            if not any(a and b for a, b in pairwise(where)):
                continue
            native = [np.asarray(values, dtype=float) for values in series]
            label = layer.label if key is None else str(key)
            artist = draw(
                *native,
                where=where,
                step=None if cfg is None else cfg.step,
                interpolate=False if cfg is None else cfg.interpolate,
                label=_decorate(label, layer.citation, layer.href),
                color=ink,
                alpha=layer.alpha if layer.alpha < 1 else 0.25,
                linewidth=layer.line_width if layer.line_width is not None else 0.0,
            )
            apply_component_style(artist, style, body=True)
            apply_path_effects(artist, layer.path_effects, body=True)
