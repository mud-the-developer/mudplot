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


def pack_circles(
    values, diameter: float | np.ndarray, half_width: float | np.ndarray
) -> tuple[np.ndarray, int]:
    """Greedy nearest-center packing with merged forbidden x intervals.

    Stable value sorting breaks ties by input order; exact equidistant candidates
    alternate left/right. Worst-case O(n^2 log n), not candidate-cubic.
    Crowded points use the nearest gutter and remain in the collision set.
    Diameters/bounds may be scalar or per-row; negative bounds mean oversized.
    """
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or not np.isfinite(values).all():
        raise ValueError("swarm packing values must be finite and one-dimensional")
    diameters = np.broadcast_to(np.asarray(diameter, dtype=float), values.shape)
    bounds = np.broadcast_to(np.asarray(half_width, dtype=float), values.shape)
    if (
        not np.isfinite(diameters).all()
        or np.any(diameters < 0)
        or not np.isfinite(bounds).all()
        or diameters.max(initial=0) > np.sqrt(np.finfo(float).max) / (1 + 1e-7)
    ):
        raise ValueError("swarm packing sizes/bounds must be finite and representable")
    radii = diameters / 2
    max_radius = float(radii.max(initial=0))
    offsets = np.zeros(len(values), dtype=float)
    crowded = 0
    active: list[int] = []
    for rank, i in enumerate(np.argsort(values, kind="stable")):
        # A later larger marker can still collide with a currently distant row.
        active = [
            j
            for j in active
            if values[i] - values[j] < (radii[j] + max_radius) * (1 + 1e-7)
        ]
        neighbors = [
            j
            for j in active
            if values[i] - values[j] < (radii[i] + radii[j]) * (1 + 1e-7)
        ]
        limit = max(0, float(bounds[i]))
        point_crowded = bounds[i] < 0
        if neighbors:
            dy = values[i] - values[neighbors]
            # Tiny clearance absorbs inverse-transform roundoff at tangency.
            clearance = (radii[i] + radii[neighbors]) * (1 + 1e-7)
            dx = np.sqrt(np.maximum(0, clearance**2 - dy**2))
            intervals = sorted(
                zip(offsets[neighbors] - dx, offsets[neighbors] + dx, strict=True)
            )
            left, right = intervals[0]
            candidate = 0.0
            for start, end in [*intervals[1:], (float("inf"), float("inf"))]:
                if start < right:
                    right = max(right, end)
                    continue
                if left < 0 < right:
                    choices = [edge for edge in (left, right) if abs(edge) <= limit]
                    if choices:
                        # Smallest absolute displacement; alternate exact ties.
                        candidate = min(
                            choices, key=lambda x: (abs(x), x if rank % 2 else -x)
                        )
                    else:
                        candidate = float(
                            np.clip(
                                left if abs(left) < abs(right) else right,
                                -limit,
                                limit,
                            )
                        )
                        point_crowded = True
                    break
                left, right = start, end
            offsets[i] = candidate
        crowded += int(point_crowded)
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
        n = len(self._base_offsets)
        sizes = np.asarray(self.get_sizes(), dtype=float)
        widths = np.atleast_1d(np.asarray(self.get_linewidth(), dtype=float))
        for name, values in (("sizes", sizes), ("linewidths", widths)):
            if (
                values.ndim != 1
                or not 1 <= len(values) <= n
                or not np.isfinite(values).all()
                or np.any(values < 0)
            ):
                raise ValueError(f"swarm {name} must be finite nonnegative row arrays")
        diameters = (
            np.sqrt(np.resize(sizes, n)) + np.resize(widths, n)
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
            cell_diameters = diameters[indices]
            half_widths = available / 2 - cell_diameters / 2
            offsets, count = pack_circles(
                display[indices, value_axis], cell_diameters, half_widths
            )
            packed[indices, category_axis] += offsets
            crowded += count
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
