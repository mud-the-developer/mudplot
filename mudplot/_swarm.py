"""Draw-time native glyph packing, with exact legacy circles (render effect only).

The category coordinate alone changes. Layout, limits, DPI and backend changes
repack from original observations on every draw, without RNG or accumulated drift.
Overcrowding retains every row at a gutter and reports the compromised packing.
"""

from __future__ import annotations

import warnings

import numpy as np
from matplotlib.artist import Artist
from matplotlib.collections import PathCollection
from matplotlib.markers import MarkerStyle
from matplotlib.transforms import IdentityTransform


def pack_circles(
    values,
    diameter: float | np.ndarray,
    half_width: float | np.ndarray,
    *,
    crowded_rows: np.ndarray | None = None,
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
        if crowded_rows is not None:
            crowded_rows[i] = point_crowded
        active.append(int(i))
    return offsets, crowded


class SwarmCollection(PathCollection):
    """A normal PathCollection that recomputes its offsets just before drawing."""

    def __init__(
        self,
        offsets,
        cells,
        *,
        horizontal,
        size,
        line_width,
        warn_thresh,
        marker="o",
        markers=None,
        coordinator=None,
        cell_keys=None,
        **kwargs,
    ):
        named = [marker] if markers is None else markers
        lookup = {}
        for name in named:
            if name not in lookup:
                style = MarkerStyle(name)
                lookup[name] = style.get_path().transformed(style.get_transform())
        paths = (
            list(lookup.values())
            if len(lookup) == 1
            else [lookup[name] for name in named]
        )
        super().__init__(
            paths,
            sizes=[size**2],
            offsets=offsets,
            linewidths=[line_width],
            **kwargs,
        )
        self._circle_path = lookup.get("o")
        if any(name != "o" for name in named):
            self.set_joinstyle("round")
        self.set_transform(IdentityTransform())
        self._base_offsets = np.asarray(offsets, dtype=float).copy()
        self._cells = cells
        self._category_axis = int(horizontal)
        self._warn_thresh = warn_thresh
        self._warning_emitted = False
        self.crowded_count = 0
        self._coordinator = coordinator
        self._cell_keys = cell_keys
        if coordinator is not None:
            coordinator.add(self)

    def _diameters(self, renderer):
        """Native path extents plus stroke; retain the exact old circle radius."""
        n = len(self._base_offsets)
        paths = self.get_paths()
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
        if (
            any(path is not self._circle_path for path in paths)
            and self.get_joinstyle() != "round"
        ):
            raise ValueError("noncircular swarm markers require round stroke joins")
        # Cache only within this call: repeated named paths are shared objects,
        # but native path edits must be measured again on the next draw.
        by_identity = {}
        radii = []
        for path in paths:
            identity = id(path)
            if identity not in by_identity:
                if path is self._circle_path:
                    radius = 0.5
                else:
                    box = path.get_extents()
                    radius = np.hypot(
                        max(abs(box.x0), abs(box.x1)),
                        max(abs(box.y0), abs(box.y1)),
                    )
                    if not np.isfinite(radius):
                        raise ValueError("swarm marker extent must be finite")
                by_identity[identity] = radius
            radii.append(by_identity[identity])
        return (
            np.sqrt(np.resize(sizes, n)) * (2 * np.resize(radii, n))
            + np.resize(widths, n)
        ) * renderer.points_to_pixels(1)

    def _cell_half_widths(self, transform, display, indices, lower, upper, diameters):
        axis = self._category_axis
        edge_points = np.repeat(self._base_offsets[indices[:1]], 2, axis=0)
        edge_points[:, axis] = [lower, upper]
        edges = transform.transform(edge_points)[:, axis]
        center = display[indices[0], axis]
        available = 2 * min(abs(edges[0] - center), abs(edges[1] - center))
        return available / 2 - diameters[indices] / 2

    def _pack(self, renderer):
        assert self.axes is not None
        transform = self.axes.transData
        category_axis = self._category_axis
        value_axis = 1 - category_axis
        display = transform.transform(self._base_offsets)
        packed = display.copy()
        diameters = self._diameters(renderer)
        crowded = 0
        for indices, lower, upper in self._cells:
            half_widths = self._cell_half_widths(
                transform, display, indices, lower, upper, diameters
            )
            cell_diameters = diameters[indices]
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
        self._report_crowding(crowded)

    def _report_crowding(self, crowded):
        self.crowded_count = crowded
        result = self._base_offsets
        if crowded / len(result) > self._warn_thresh and not self._warning_emitted:
            conservative = self._coordinator is not None or any(
                path is not self._circle_path for path in self.get_paths()
            )
            reason = (
                "could not satisfy conservative glyph/stroke clearance or gutter bounds"
                if conservative
                else "could not be packed without overlap in the allocated width"
            )
            warnings.warn(
                f"swarmplot: {crowded}/{len(result)} observations {reason}; "
                "retained at gutters. "
                "Reduce marker_size, enlarge the figure or use stripplot.",
                UserWarning,
                stacklevel=2,
            )
            self._warning_emitted = True

    def draw(self, renderer):
        if not self.get_visible() or self.axes is None:
            return
        if self._coordinator is None or self._coordinator.axes is not self.axes:
            self._pack(renderer)
        super().draw(renderer)


class SwarmScope(Artist):
    """One axes-owned pre-collection packing pass for explicitly named members."""

    def __init__(self, ax):
        super().__init__()
        self.members = []
        self.set_zorder(-1)
        self.set_in_layout(False)
        ax.add_artist(self)

    def add(self, collection):
        self.members.append(collection)

    def draw(self, renderer):
        if not self.get_visible() or self.axes is None:
            return
        drawn = {id(collection) for collection in self.axes.collections}
        cells = {}
        prepared = []
        for collection in self.members:
            if (
                not collection.get_visible()
                or collection.axes is not self.axes
                or id(collection) not in drawn
            ):
                continue
            transform = collection.axes.transData
            display = transform.transform(collection._base_offsets)
            diameters = collection._diameters(renderer)
            item = {
                "collection": collection,
                "transform": transform,
                "display": display,
                "packed": display.copy(),
                "crowded": 0,
            }
            prepared.append(item)
            for key, (indices, lo, hi) in zip(
                collection._cell_keys, collection._cells, strict=True
            ):
                bounds = collection._cell_half_widths(
                    transform, display, indices, lo, hi, diameters
                )
                cells.setdefault(key, []).append(
                    (item, indices, diameters[indices], bounds)
                )
        for entries in cells.values():
            value_axis = 1 - entries[0][0]["collection"]._category_axis
            values = np.concatenate(
                [
                    item["display"][indices, value_axis]
                    for item, indices, _, _ in entries
                ]
            )
            diameters = np.concatenate([diameters for _, _, diameters, _ in entries])
            bounds = np.concatenate([bounds for _, _, _, bounds in entries])
            crowded = np.zeros(len(values), dtype=bool)
            offsets, _ = pack_circles(values, diameters, bounds, crowded_rows=crowded)
            start = 0
            for item, indices, _, _ in entries:
                end = start + len(indices)
                axis = item["collection"]._category_axis
                item["packed"][indices, axis] += offsets[start:end]
                item["crowded"] += int(np.count_nonzero(crowded[start:end]))
                start = end
        for item in prepared:
            collection = item["collection"]
            result = collection._base_offsets.copy()
            axis = collection._category_axis
            result[:, axis] = (
                item["transform"].inverted().transform(item["packed"])[:, axis]
            )
            collection.set_offsets(result)
            collection._report_crowding(item["crowded"])
        self.stale = False
