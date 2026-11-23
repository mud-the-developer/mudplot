"""Native colour effects for a pre-admitted P01 scalar plan."""

import numpy as np
from matplotlib import colormaps
from matplotlib.colors import (
    BoundaryNorm,
    LinearSegmentedColormap,
    ListedColormap,
    LogNorm,
    Normalize,
    TwoSlopeNorm,
)

from ._heatmap_render import draw_colourbar
from .spec import ColorbarOptionsSpec


def native_scalar_maps(plans):
    result, pooled = {}, {}
    for key, plan in plans.items():
        ident = id(plan)
        if ident not in pooled:
            cfg = plan.config
            if cfg.cmap in ("mudplot-sequential", "mudplot-diverging"):
                from ._render import _continuous_cmap

                cmap = _continuous_cmap(cfg.cmap.removeprefix("mudplot-"))
            elif cfg.colors is not None:
                cmap = LinearSegmentedColormap.from_list("mudplot-scalar", cfg.colors)
            else:
                cmap = colormaps[cfg.cmap or "viridis"]
            low, high = plan.bounds
            if cfg.norm == "boundary":
                bins = len(cfg.boundaries) - 1
                cmap = ListedColormap(
                    cmap(np.linspace(0, 1, bins) if bins > 1 else [0.5])
                )
                norm = BoundaryNorm(cfg.boundaries, bins)
            elif cfg.norm == "log":
                norm = LogNorm(low, high)
            elif cfg.norm in ("centered", "two_slope"):
                norm = TwoSlopeNorm(cfg.center, low, high)
            else:
                norm = Normalize(low, high)
            cmap = cmap.with_extremes(under=cfg.under, over=cfg.over, bad=cfg.bad)
            pooled[ident] = {"norm": norm, "cmap": cmap}
        result[key] = pooled[ident]
    return result


def scalar_style(ax, layer):
    return ax.figure._mudplot_scalar_maps[id(layer)]


def draw_scalar_bar(ax, layer, artist):
    if not layer.colorbar:
        return None
    collector = getattr(ax, "_mudplot_shared_guide_collector", None)
    if collector is not None and collector.add_scalar(ax, layer, artist):
        return None
    config = layer.scalar_display
    options = config.colorbar_options or ColorbarOptionsSpec()
    return draw_colourbar(
        ax, artist, layer.clabel or "", calibrated=True, options=options
    )
