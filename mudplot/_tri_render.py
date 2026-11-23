"""Native explicit triangle effects, including the one N08/N10 trisurf path."""

import numpy as np
from matplotlib.colors import Normalize
from matplotlib.tri import Triangulation

from ._grid_field import LABEL_FORMATS


def draw_triangles(ax, layer, plan, color_iter=None):
    from ._render import _continuous_cmap

    tri = Triangulation(plan.x, plan.y, plan.triangles, mask=plan.mask)
    kind = layer.type
    cfg = layer.triangulation
    if kind == "triplot":
        color = layer.color
        if not color:
            assert color_iter is not None
            color = next(color_iter)
        return ax.triplot(
            tri,
            linestyle=layer.line_style or "-",
            marker="None",
            color=color,
            linewidth=layer.line_width,
            alpha=layer.alpha,
            label=layer.label,
        )
    options = {
        "norm": Normalize(*plan.limits),
        "cmap": _continuous_cmap(layer.cmap_kind),
        "alpha": layer.alpha,
    }
    values = np.asarray(plan.values, dtype=float)
    if kind == "tripcolor":
        if layer.line_width is not None:
            options["linewidth"] = layer.line_width
        if layer.edge_color is not None:
            options["edgecolors"] = layer.edge_color
        if cfg.scalar_role == "face":
            artist = ax.tripcolor(tri, facecolors=values, shading="flat", **options)
        else:
            artist = ax.tripcolor(tri, values, shading="flat", **options)
    elif kind == "trisurf":
        artist = ax.plot_trisurf(tri, values, **options)
    else:
        if kind == "tricontourf":
            options["extend"] = cfg.extend or "neither"
        draw = ax.tricontour if kind == "tricontour" else ax.tricontourf
        artist = draw(tri, values, levels=layer.levels, **options)
        if not np.array_equal(artist.levels, layer.levels):
            raise ValueError(
                "native triangular contour changed explicitly declared levels"
            )
        if cfg.label_levels is not None:
            ax.clabel(
                artist,
                levels=cfg.label_levels,
                fmt=LABEL_FORMATS[cfg.label_format or "g"],
                inline=True if cfg.label_inline is None else cfg.label_inline,
            )
    if layer.colorbar:
        ax.figure.colorbar(artist, ax=ax, label=layer.clabel or "")
    return artist
