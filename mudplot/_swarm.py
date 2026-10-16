"""Draw-time, display-space circular-marker packing (render effect only).

The category coordinate alone changes. Layout, limits, DPI and backend changes
repack from original observations on every draw, without RNG or accumulated drift.
Overcrowding retains every row at a gutter and reports the compromised packing.
"""

from __future__ import annotations

import warnings

import numpy as np
from matplotlib.collections import PathCollection
from matplotlib.markers import MarkerStyle
from matplotlib.transforms import IdentityTransform


def pack_circles(values, diameter: float, half_width: float) -> tuple[np.ndarray, int]:
    """Greedy nearest-center packing with merged forbidden x intervals.

    Stable value sorting breaks ties by input order; exact equidistant candidates
    alternate left/right. Worst-case O(n^2 log n), not candidate-cubic.
    Crowded points use the nearest gutter and remain in the collision set.
    """
    values = np.asarray(values, dtype=float)
    offsets = np.zeros(len(values), dtype=float)
    crowded = 0
    active: list[int] = []
    # Tiny clearance absorbs inverse-transform/renderer roundoff at tangency.
    clearance = diameter * (1 + 1e-7)
    for rank, i in enumerate(np.argsort(values, kind="stable")):
        active = [j for j in active if values[i] - values[j] < clearance]
        if active:
            dy = values[i] - values[active]
            dx = np.sqrt(np.maximum(0, clearance**2 - dy**2))
            intervals = sorted(
                zip(offsets[active] - dx, offsets[active] + dx, strict=True)
            )
            left, right = intervals[0]
            candidate = 0.0
            for start, end in [*intervals[1:], (float("inf"), float("inf"))]:
                if start < right:
                    right = max(right, end)
                    continue
                if left < 0 < right:
                    choices = [
                        edge for edge in (left, right) if abs(edge) <= half_width
                    ]
                    if choices:
                        # Smallest absolute displacement; alternate exact ties.
                        candidate = min(
                            choices, key=lambda x: (abs(x), x if rank % 2 else -x)
                        )
                    else:
                        candidate = float(
                            np.clip(
                                left if abs(left) < abs(right) else right,
                                -half_width,
                                half_width,
                            )
                        )
                        crowded += 1
                    break
                left, right = start, end
            offsets[i] = candidate
        active.append(int(i))
    return offsets, crowded


class SwarmCollection(PathCollection):
    """A normal PathCollection that recomputes its offsets just before drawing."""

    def __init__(
        self, offsets, cells, *, horizontal, size, line_width, warn_thresh, **kwargs
    ):
        marker = MarkerStyle("o")
        super().__init__(
            [marker.get_path().transformed(marker.get_transform())],
            sizes=[size**2],
            offsets=offsets,
            linewidths=[line_width],
            **kwargs,
        )
        self.set_transform(IdentityTransform())
        self._base_offsets = np.asarray(offsets, dtype=float).copy()
        self._cells = cells  # (row indices, raw lower/upper category bounds)
        self._category_axis = int(horizontal)
        self._warn_thresh = warn_thresh
        self._warning_emitted = False
        self.crowded_count = 0

    def draw(self, renderer):
        if not self.get_visible() or self.axes is None:
            return
        ax = self.axes
        category_axis = self._category_axis
        value_axis = 1 - category_axis
        transform = ax.transData
        display = transform.transform(self._base_offsets)
        packed = display.copy()
        diameter = (
            np.sqrt(self.get_sizes()[0]) + np.asarray(self.get_linewidth())[0]
        ) * renderer.points_to_pixels(1)
        crowded = 0
        for indices, lower, upper in self._cells:
            edge_points = self._base_offsets[indices[:2]].copy()
            if len(edge_points) == 1:
                edge_points = np.repeat(edge_points, 2, axis=0)
            edge_points[:, category_axis] = [lower, upper]
            edges = transform.transform(edge_points)[:, category_axis]
            center = display[indices[0], category_axis]
            # Conservative on asymmetric transforms: never escape either gutter,
            # including after a native category axis scale/inversion changes.
            available = 2 * min(abs(edges[0] - center), abs(edges[1] - center))
            half_width = max(0, available / 2 - diameter / 2)
            offsets, count = pack_circles(
                display[indices, value_axis], diameter, half_width
            )
            packed[indices, category_axis] += offsets
            crowded += len(indices) if available < diameter else count
        # Keep raw value coordinates exactly (no inverse-transform rounding).
        result = self._base_offsets.copy()
        result[:, category_axis] = transform.inverted().transform(packed)[
            :, category_axis
        ]
        self.set_offsets(result)
        self.crowded_count = crowded
        if crowded / len(result) > self._warn_thresh and not self._warning_emitted:
            warnings.warn(
                f"swarmplot: {crowded}/{len(result)} observations could not be packed "
                "without overlap in the allocated width; retained at gutters. "
                "Reduce marker_size, enlarge the figure or use stripplot.",
                UserWarning,
                stacklevel=2,
            )
            self._warning_emitted = True
        super().draw(renderer)
