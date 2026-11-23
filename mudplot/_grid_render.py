"""Native N07 artist effects for pre-admitted grid fields."""

import numpy as np
from matplotlib.colors import Normalize

from ._grid_field import LABEL_FORMATS, MESH_TYPES


def draw_grid(ax, layer, plan):
    from ._render import _continuous_cmap

    cfg, kind = plan.config, layer.type
    raw = np.asarray(plan.data, dtype=float)
    mask = None if cfg.mask is None else np.asarray(cfg.mask, dtype=bool)
    if plan.depth:
        if plan.depth == 3:
            pixels = np.empty((plan.rows, plan.cols, 4))
            pixels[..., :3] = raw
            pixels[..., 3] = layer.alpha
        else:
            pixels = raw
            pixels[..., 3] *= layer.alpha
        if mask is not None:
            pixels[..., 3][mask] = 0
        return ax.imshow(
            pixels,
            origin=cfg.origin or "upper",
            extent=cfg.extent,
            aspect="auto",
            interpolation="nearest",
        )

    values = np.ma.masked_invalid(raw, copy=False)
    if mask is not None:
        values.mask = np.logical_or(values.mask, mask)
    if kind == "spy":
        # Native spy owns index geometry and row-major order. Its dense marker
        # path ignores a numpy mask, so materialize only bounded presence bits.
        present = (
            np.ma.abs(values) > (0 if cfg.threshold is None else cfg.threshold)
        ).filled(False)
        style = {} if layer.color is None else {"color": layer.color}
        return ax.spy(
            present,
            marker=layer.marker or "s",
            markersize=layer.marker_size,
            origin=cfg.origin or "upper",
            alpha=layer.alpha,
            **style,
        )

    scalar = layer.scalar_display is not None
    if scalar:
        from ._scalar_render import scalar_style

        options = {**scalar_style(ax, layer), "alpha": layer.alpha}
    else:
        low, high = plan.limits
        options = {
            "norm": Normalize(low, high),
            "cmap": _continuous_cmap(layer.cmap_kind),
            "alpha": layer.alpha,
        }
    if kind == "imshow":
        artist = ax.imshow(
            values,
            origin=cfg.origin or "upper",
            extent=cfg.extent,
            aspect="auto",
            interpolation="nearest",
            **options,
        )
    elif kind in MESH_TYPES:
        draw = ax.pcolor if kind == "pcolor" else ax.pcolormesh
        edges = layer.edge_color if layer.line_width != 0 else None
        if layer.line_width is not None:
            options["linewidth"] = layer.line_width
        artist = draw(
            cfg.x,
            cfg.y,
            values,
            shading=cfg.shading,
            edgecolors=edges or "none",
            **options,
        )
    else:
        draw = ax.contour if kind == "contour" else ax.contourf
        if kind == "contourf":
            options["extend"] = cfg.extend or "neither"
        artist = draw(
            cfg.x,
            cfg.y,
            values,
            levels=layer.levels,
            corner_mask=cfg.corner_mask is True,
            **options,
        )
        if not np.array_equal(artist.levels, layer.levels):
            raise ValueError("native contour changed explicitly declared levels")
        if cfg.label_levels is not None:
            ax.clabel(
                artist,
                levels=cfg.label_levels,
                fmt=LABEL_FORMATS[cfg.label_format or "g"],
                inline=True if cfg.label_inline is None else cfg.label_inline,
            )
    if scalar and layer.colorbar:
        from ._scalar_render import draw_scalar_bar

        draw_scalar_bar(ax, layer, artist)
    elif layer.colorbar:
        ax.figure.colorbar(artist, ax=ax, label=layer.clabel or "")
    return artist
