"""Visual previews of palettes, including CVD simulation strips."""

from __future__ import annotations

import numpy as np

from . import cvd
from .palette import Palette

__all__ = ["preview"]

_ROWS = [
    ("Normal", None),
    ("Protanopia", "protan"),
    ("Deuteranopia", "deutan"),
    ("Tritanopia", "tritan"),
    ("Greyscale", "__grayscale__"),
]


def preview(pal: Palette, ax=None, show_cvd: bool = True):
    """Draw a palette as colour swatches with CVD- and greyscale-simulated
    rows below (the greyscale row uses true relative luminance, not CIE L*,
    matching black-and-white print / full achromatopsia).

    Returns the matplotlib Axes.
    """
    import matplotlib.pyplot as plt

    rows = _ROWS if show_cvd else _ROWS[:1]
    n = len(pal)

    if ax is None:
        _, ax = plt.subplots(figsize=(max(4, n * 0.7), 0.6 * len(rows) + 0.6))

    for r, (label, t) in enumerate(rows):
        if t is None:
            colours = pal.srgb
        elif t == "__grayscale__":
            colours = pal.grayscale_srgb()
        else:
            colours = cvd.simulate(pal.srgb, t, 1.0)
        y = len(rows) - 1 - r
        for i in range(n):
            ax.add_patch(
                plt.Rectangle((i, y), 1, 0.9, facecolor=np.clip(colours[i], 0, 1))
            )
        ax.text(-0.15, y + 0.45, label, ha="right", va="center", fontsize=9)

    ax.set_xlim(-0.02, n)
    ax.set_ylim(0, len(rows))
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    title = f"{pal.kind} (n={n})"
    if pal.meta.get("min_delta_e") is not None:
        title += f"   worst-case min ΔE₀₀ = {pal.meta['min_delta_e']:.1f}"
    if hasattr(pal, "min_lightness_gap") and n > 1:
        title += f"   min L* gap = {pal.min_lightness_gap():.1f}"
    ax.set_title(title, fontsize=10)
    return ax
