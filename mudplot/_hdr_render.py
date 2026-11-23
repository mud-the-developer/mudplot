"""Native full-HDR cell unions; fitting/probability stay in the shared model.

The calibrated set is not a smooth grid contour. Its source, boundary,
forward/serialized-vector and visible-clipping errors are kept separate.
"""

from __future__ import annotations

import bisect
import hashlib
import heapq
import itertools
import math
import struct
import sys
from collections import OrderedDict
from fractions import Fraction
from typing import Protocol, cast

import numpy as np
from matplotlib.collections import PolyCollection
from matplotlib.transforms import Bbox

from ._field_budget import FieldResourceError, owned_size
from ._hdr import MAX_HDR_ACTIVE_CELLS, children
from ._kernel_math import KernelPrecisionError


class _NativePathTopology(Protocol):
    _interpolation_steps: int


class _NativeLogPolicy(Protocol):
    _clip: bool


_NativeCertificate = tuple[
    bytes,
    tuple[tuple[float, bool] | None, ...],
    tuple[float, ...],
    tuple[float, ...],
    tuple[tuple[float, ...], float],
]


def _affine_radius(scale, offset, magnitude, dpi):
    """Exact pre-affine radius for separate binary64 rounds plus serialization."""
    if not all(math.isfinite(x) for x in (scale, offset, magnitude, dpi)):
        raise KernelPrecisionError("native HDR affine inputs must be finite")
    if scale == 0 or magnitude < 0 or dpi <= 0:
        raise KernelPrecisionError("native HDR affine scale or output DPI collapses")
    unit_roundoff = Fraction(1, 2**53)
    half_subnormal = Fraction(1, 2**1075)
    a, b, v = abs(Fraction(scale)), abs(Fraction(offset)), Fraction(magnitude)
    product = a * v
    multiply_error = unit_roundoff * product + half_subnormal
    added = product + multiply_error + b
    add_error = unit_roundoff * added + half_subnormal
    serialization = Fraction(dpi) / 2_000_000
    if added + add_error + serialization > sys.float_info.max:
        raise KernelPrecisionError("native HDR affine arithmetic can overflow")
    return (multiply_error + add_error + serialization) / a


def _point(value):
    return float(value), float(value)


def _magnitude(bound):
    return max(abs(bound[0]), abs(bound[1]))


class HDRCollection(PolyCollection):
    """One actual cell collection, recomputed from immutable fitted coordinates."""

    def __init__(self, axes, region, config, layer, query_bounds, *, cmap, norm, style):
        self.region = region
        self.model = region.model
        self.arithmetic = self.model.arithmetic
        self.budget = self.model.budget
        self._tolerance = config.hdr.tolerance
        self._orient = layer.orient
        self.query_bounds = query_bounds
        self._geometry_leases = []
        self._geometry_scales = axes.get_xscale(), axes.get_yscale()
        self._visible_key = None
        self._visible_result = None
        self._native_certificate: _NativeCertificate | None = None
        self._native_certificate_lease = None
        self._ideal_paths = []
        self._chords = []
        self._closed = False
        self._peak_probability = None
        if self.budget is None:
            raise ValueError("full HDR requires its NEW figure resource ledger")
        try:
            self._geometry_leases.append(
                self.budget.lease(8 * owned_size(region.levels))
            )
            polygons, bands = self._polygons()
            edge = style.get("edge_color")
            if config.fill:
                edge = edge or ("face" if style["width"] else "none")
                face = None
            else:
                face = "none"
            self._geometry_leases.append(
                self.budget.array_lease((len(bands),), copies=2)
            )
            # A redraw can hold old/new per-cell RGBA plus normal/index/mask
            # workspace concurrently. These are native artist bytes, not the
            # separate backend canvas RGBA allowance.
            self._geometry_leases.append(
                self.budget.array_lease((len(bands), 4), copies=3)
            )
            super().__init__(
                polygons,
                closed=True,
                array=np.asarray([region.levels[index].cutoff for index in bands]),
                cmap=cmap,
                norm=norm,
                facecolors=face,
                edgecolors=edge,
                linewidths=style["width"],
                linestyles="solid" if style["width"] == 0 else style["dash"],
                alpha=layer.alpha,
                antialiaseds=False,
                label="_nolegend_",
            )
            for path in self.get_paths():
                path.should_simplify = False
            self._bands = tuple(bands)
            self._mudplot_hdr = {
                "representation": "guaranteed-inside adaptive cell union",
                "source_row_indices": tuple(self.model.source_rows),
                "kernel": self.model.kernel,
                "density_space": region.density_space,
                "fit_logarithmic": self.model.log_axes,
                "conditional_support_error": region.support_error,
                "source_law_error": region.source_error,
                "classification_numerical_error": region.probability_error,
                "amplitude": str(self.model.amplitude),
                "stroke_is_physical_decoration_not_probability": True,
            }
            self._geometry_leases.append(self.budget.account(self._mudplot_hdr))
        except Exception:
            self._release()
            raise

    def _logical(self, display):
        return display if self._orient == "v" else display[::-1]

    def _display(self, logical):
        return logical if self._orient == "v" else logical[::-1]

    def _raw(self, q, *, enclose=False):
        """One exact representative/envelope, owned by the bounded caller."""
        key = tuple(q)
        fit = self.model._fit_box(tuple((value, value) for value in key))
        return tuple(
            self.model.native_coordinate(value[0], axis)[1 if enclose else 0]
            for axis, value in enumerate(fit)
        )

    def _raw_box(self, box):
        a, b, c, d = box
        values = [
            self._raw(point, enclose=True) for point in ((a, c), (b, c), (b, d), (a, d))
        ]
        return tuple(
            (
                min(value[axis][0] for value in values),
                max(value[axis][1] for value in values),
            )
            for axis in (0, 1)
        )

    def _chord_error(self, first, last, first_logs, last_logs):
        iv = self.arithmetic
        scales = self._logical(self._geometry_scales)
        errors = []
        for axis, (a, b, logarithmic, scale) in enumerate(
            zip(first, last, self.model.log_axes, scales, strict=True)
        ):
            if logarithmic == (scale == "log"):
                errors.append(0.0)
                continue
            if min(a, b) <= 0:
                raise KernelPrecisionError("full HDR has nonpositive log-view geometry")
            if scale == "log":
                la, lb = first_logs[axis], last_logs[axis]
                assert la is not None and lb is not None
                delta = _magnitude(iv.sub(lb, la))
                error = iv.div(
                    iv.mul(_point(max(a, b)), iv.mul(_point(delta), _point(delta))),
                    (8.0, 8.0),
                )[1]
            else:
                difference = iv.rational_sub((Fraction(b),) * 2, (Fraction(a),) * 2)
                squared = iv.rational_mul(difference, difference)
                denominator = 8 * Fraction(min(a, b)) ** 2
                ratio = iv.rational_div(squared, (denominator,) * 2)
                error = iv.div(iv.fraction_bounds(*ratio), iv.ln10)[1]
            errors.append(error)
        lower = self.model.lower
        dx = iv.div(_point(errors[0]), _point(lower[0]))[1]
        dy = iv.div(
            iv.add(_point(errors[1]), iv.mul(_point(abs(lower[1])), _point(dx))),
            _point(lower[2]),
        )[1]
        return max(dx, dy)

    def _polygons(self):
        iv, budget = self.arithmetic, self.budget
        cells = self.region.cells
        temporary = []
        cache, vertical_ranges, horizontal_ranges = {}, {}, {}
        polygons, bands = [], []
        scalar_logs = None
        try:
            log_empty_bytes = sys.getsizeof(OrderedDict())
            log_lease = budget.lease(log_empty_bytes + sys.getsizeof((None, None)))
            temporary.append(log_lease)
            scalar_logs = OrderedDict()
            event_count = 4 * len(cells)

            def edge_index(vertical):
                # Ordinal ties retain the first encountered representative,
                # including signed zero. Heapsort has no permutation/sort copy.
                dtype = np.dtype(
                    [("line", "float64"), ("position", "float64"), ("ordinal", "int64")]
                )
                with (
                    budget.array_lease((event_count, 3), active=True),
                    budget.lease(8 * dtype.itemsize),
                ):
                    events = np.empty(event_count, dtype=dtype)
                    index = 0
                    for box, _path, _depth, _band in cells:
                        a, b, c, d = box
                        lines, points = (
                            ((a, b), (c, d)) if vertical else ((c, d), (a, b))
                        )
                        for line in lines:
                            for position in points:
                                events[index] = line, position, index
                                index += 1
                    budget.charge(
                        "native_hdr_edge_index_sort",
                        16 * event_count * max(1, event_count.bit_length()),
                    )
                    events.sort(order=("line", "position", "ordinal"), kind="heapsort")
                    count = 0
                    previous = None
                    for event in events:
                        key = float(event["line"]), float(event["position"])
                        if key != previous:
                            count += 1
                            previous = key
                    temporary.append(budget.array_lease((count,), active=True))
                    positions = np.empty(count)
                    table = {}
                    table_lease = budget.hashmap_lease(0)
                    temporary.append(table_lease)
                    previous = None
                    count = 0
                    line_start = 0
                    line_value = None
                    for event in events:
                        line, position = float(event["line"]), float(event["position"])
                        key = line, position
                        if key == previous:
                            continue
                        if line_value is not None and line != line_value:
                            table_lease.grow(
                                sys.getsizeof({None: None})
                                - sys.getsizeof({})
                                + sys.getsizeof(0.0)
                                + owned_size((line_start, count))
                            )
                            table[line_value] = line_start, count
                            line_start = count
                        line_value = line
                        positions[count] = position
                        count += 1
                        previous = key
                    if line_value is not None:
                        table_lease.grow(
                            sys.getsizeof({None: None})
                            - sys.getsizeof({})
                            + sys.getsizeof(0.0)
                            + owned_size((line_start, count))
                        )
                        table[line_value] = line_start, count
                    return positions, table

            vertical_positions, vertical_ranges = edge_index(True)
            horizontal_positions, horizontal_ranges = edge_index(False)
            budget.charge("native_hdr_cell_edges", 4 * len(cells))
            perimeter = 0.0
            minimum = math.inf
            for box, _path, _depth, _band in cells:
                a, b, c, d = box
                perimeter = iv.add(_point(perimeter), _point((b - a) + (d - c)))[1]
                minimum = min(minimum, b - a, d - c)
            # Compact indices retain the same sorted T-junction positions;
            # no per-cell set/list or copied per-line array survives.
            peak = self._probability_peak()
            remaining = self._tolerance - self.region.probability_error
            if remaining <= 0:
                raise KernelPrecisionError("no remaining native HDR error allocation")
            epsilon = min(
                minimum / 64,
                remaining / (64 * peak * max(perimeter, 1.0)),
                1e-6,
            )
            if not math.isfinite(epsilon) or epsilon <= 0:
                raise KernelPrecisionError(
                    "native HDR tessellation precision is unresolved"
                )

            list_header = sys.getsizeof([])
            probe = []
            probe.append(None)
            append_slot = sys.getsizeof(probe) - list_header
            point_bytes = sys.getsizeof((0.0, 0.0)) + 2 * sys.getsizeof(0.0)
            # CPython append capacity is bounded by its first allocation quantum
            # per appended entry. Native point payloads are conservatively owned
            # here even when their coordinates also belong to the source/cache.
            point_scratch = 2 * append_slot + 2 * point_bytes
            # A depth-first traversal holds <=25 frontier entries at depth24.
            # Carry the SAME outward endpoint logarithms through the frontier.
            # Retrying both endpoints at every parent/child would redo the same
            # charged primitive; no global interval cache or changed bound is used.
            log_point_bytes = sys.getsizeof((None, None)) + 2 * point_bytes
            edge_fixed = 3 * list_header + (2 * 24 + 5) * (
                sys.getsizeof((None,) * 7) + 4 * point_bytes + 2 * log_point_bytes
            )
            # Each frontier endpoint owns two raw scalars and four log-bound
            # scalars; q/native output plans are separately byte-admitted.
            edge_endpoint_scalars = (2 * 24 + 5) * 12
            # This bounded memo owns only useful scalar-log results for THIS
            # construction. It is not a per-q point/envelope or persistent cache.
            log_capacity = 32768
            log_entry_bytes = (
                sys.getsizeof(OrderedDict([(None, None)]))
                - log_empty_bytes
                + sys.getsizeof(0.0)
                + sys.getsizeof((0.0, 0.0))
                + 2 * sys.getsizeof(0.0)
            )

            def scalar_log(value):
                budget.charge("native_hdr_log_memo_lookups")
                if value in scalar_logs:
                    budget.charge("native_hdr_log_memo_link_moves")
                    scalar_logs.move_to_end(value)
                    return scalar_logs[value]
                if len(scalar_logs) == log_capacity:
                    budget.charge("native_hdr_log_memo_evictions")
                    scalar_logs.popitem(last=False)
                else:
                    log_lease.grow(log_entry_bytes, pair_elements=3)
                # Misses run and charge the SAME original primitive. Capacity
                # affects reuse only, never the result or admission policies.
                result = iv.log_fraction(Fraction(value))
                scalar_logs[value] = result
                return result

            def endpoint(point, known_native=None, known_logs=None):
                native = self._raw(point)
                logarithms = []
                for axis, (value, logarithmic, scale) in enumerate(
                    zip(
                        native,
                        self.model.log_axes,
                        self._logical(self._geometry_scales),
                        strict=True,
                    )
                ):
                    if scale == "log" and value <= 0:
                        raise KernelPrecisionError(
                            "full HDR log-view support is nonpositive"
                        )
                    if known_native is not None and value == known_native[axis]:
                        assert known_logs is not None
                        logarithms.append(known_logs[axis])
                    else:
                        logarithms.append(
                            scalar_log(value)
                            if scale == "log" and not logarithmic
                            else None
                        )
                return native, tuple(logarithms)

            def edge(start, end, pending):
                scratch = budget.lease(edge_fixed, pair_elements=edge_endpoint_scalars)
                try:
                    start_native, start_logs = endpoint(start)
                    end_native, end_logs = endpoint(end, start_native, start_logs)
                    raw, ideal = [], []
                    stack = [
                        (start, end, start_native, end_native, start_logs, end_logs, 0)
                    ]
                    maximum = 0.0
                    while stack:
                        (
                            first,
                            last,
                            raw_start,
                            raw_end,
                            first_logs,
                            last_logs,
                            depth,
                        ) = stack.pop()
                        error = self._chord_error(
                            raw_start, raw_end, first_logs, last_logs
                        )
                        budget.charge("native_hdr_tessellation_vertices")
                        if error <= epsilon:
                            # This edge prefix and closure must fit BEFORE either
                            # output accumulator grows, not after edge returns.
                            budget.admit_vertices(pending + len(raw) + 2)
                            scratch.grow(point_scratch)
                            raw.append(raw_start)
                            ideal.append(first)
                            maximum = max(maximum, error)
                            continue
                        if depth >= 24:
                            raise KernelPrecisionError(
                                "native HDR edge subdivision is unresolved"
                            )
                        middle = tuple(
                            iv.midpoint((a, b))
                            for a, b in zip(first, last, strict=True)
                        )
                        if middle in (first, last):
                            raise KernelPrecisionError(
                                "native HDR edge midpoint collapses"
                            )
                        middle_native, middle_logs = endpoint(
                            middle, raw_start, first_logs
                        )
                        stack.append(
                            (
                                middle,
                                last,
                                middle_native,
                                raw_end,
                                middle_logs,
                                last_logs,
                                depth + 1,
                            )
                        )
                        stack.append(
                            (
                                first,
                                middle,
                                raw_start,
                                middle_native,
                                first_logs,
                                middle_logs,
                                depth + 1,
                            )
                        )
                    budget.admit_vertices(pending + len(raw) + 1)
                    scratch.grow(point_scratch)
                    raw.append(end_native)
                    ideal.append(end)
                    return raw, ideal, maximum, scratch
                except Exception:
                    scratch.close()
                    raise

            def shared(start, end, pending):
                reverse = start > end
                low, high = (end, start) if reverse else (start, end)
                key = low, high
                cached = cache.pop(key, None)
                if cached is None:
                    raw, ideal, error, scratch = edge(low, high, pending)
                    try:
                        lease = budget.hashmap_lease(
                            1,
                            key_bytes=owned_size(key),
                            value_bytes=owned_size((raw, ideal, error))
                            + sys.getsizeof((None,)),
                        )
                        cache[key] = raw, ideal, error, lease
                    finally:
                        scratch.close()
                    release = None
                else:
                    # Disjoint cell partitions have at most two users per
                    # split edge. The second use consumes its construction cache.
                    raw, ideal, error, release = cached
                return raw, ideal, error, reverse, release

            for box, _path, _depth, band in cells:
                with budget.lease(3 * list_header + 8 * point_bytes) as workspace:
                    a, b, c, d = box
                    corners = ((a, c), (b, c), (b, d), (a, d))
                    raw_points, ideal_points = [], []
                    error = 0.0
                    for start, end in zip(
                        corners, (*corners[1:], corners[0]), strict=True
                    ):
                        axis = 1 if start[0] == end[0] else 0
                        positions, ranges = (
                            (vertical_positions, vertical_ranges)
                            if axis
                            else (horizontal_positions, horizontal_ranges)
                        )
                        line_start, line_end = ranges[start[0] if axis else start[1]]
                        low, high = sorted((start[axis], end[axis]))
                        left = bisect.bisect_left(positions, low, line_start, line_end)
                        right = bisect.bisect_right(
                            positions, high, line_start, line_end
                        )
                        indices = (
                            range(left, right)
                            if start[axis] < end[axis]
                            else range(right - 1, left - 1, -1)
                        )
                        for first_index, last_index in itertools.pairwise(indices):
                            first = (
                                (start[0], float(positions[first_index]))
                                if axis
                                else (float(positions[first_index]), start[1])
                            )
                            last = (
                                (start[0], float(positions[last_index]))
                                if axis
                                else (float(positions[last_index]), start[1])
                            )
                            raw, ideal, bound, reverse, release = shared(
                                first, last, len(raw_points)
                            )
                            try:
                                budget.admit_vertices(len(raw_points) + len(raw))
                                # Raw/ideal accumulators plus the transient
                                # display-coordinate list are admitted in full.
                                workspace.grow(
                                    (len(raw) - 1) * (3 * append_slot + 3 * point_bytes)
                                )
                                order = (
                                    range(len(raw) - 1, 0, -1)
                                    if reverse
                                    else range(len(raw) - 1)
                                )
                                for index in order:
                                    raw_points.append(raw[index])
                                    ideal_points.append(ideal[index])
                                error = max(error, bound)
                            finally:
                                del raw, ideal
                                if release is not None:
                                    release.close()
                    count = len(raw_points)
                    if count < 3:
                        raise KernelPrecisionError(
                            "native HDR cell has no finite interior"
                        )
                    self._geometry_leases.append(budget.native_path_lease(count + 1, 1))
                    self._geometry_leases.append(
                        budget.array_lease((count, 2), copies=2)
                    )
                    polygons.append(
                        np.asarray([self._display(point) for point in raw_points])
                    )
                    ideal = (*ideal_points, ideal_points[0])
                    self._geometry_leases.append(budget.account(ideal))
                    self._ideal_paths.append(ideal)
                    self._chords.append(error)
                    bands.append(band)
            return polygons, bands
        finally:
            if scalar_logs is not None:
                scalar_logs.clear()
            vertical_ranges.clear()
            horizontal_ranges.clear()
            for _raw, _ideal, _error, lease in cache.values():
                lease.close()
            cache.clear()
            for lease in reversed(temporary):
                lease.close()

    def _probability_peak(self):
        if self._peak_probability is None:
            iv = self.arithmetic
            self._peak_probability = (
                iv.div((1.0, 1.0), iv.mul((2.0, 2.0), iv.pi))[1]
                if self.model.kernel == "gaussian"
                else iv.fraction(Fraction(9, 80))[1]
            )
        return self._peak_probability

    def get_datalim(self, trans_data):
        first, second = self._display(self.query_bounds)
        return Bbox.from_extents(first[0], second[0], first[1], second[1])

    def _query_clip(self):
        axes = self.axes
        if axes is None:
            raise KernelPrecisionError("native HDR has no drawn axes")
        first, second = self._display(self.query_bounds)
        query = Bbox.from_extents(first[0], second[0], first[1], second[1])
        display = query.transformed(axes.transData)
        box = Bbox.from_extents(
            min(display.x0, display.x1),
            min(display.y0, display.y1),
            max(display.x0, display.x1),
            max(display.y0, display.y1),
        )
        return Bbox.intersection(axes.bbox, box)

    def _preimage_storage(self):
        """Bound the fixed decoded-coordinate/canonical-coupling workspace."""
        point_bytes = sys.getsizeof((0.0, 0.0)) + 2 * sys.getsizeof(0.0)
        storage = (
            sys.getsizeof((None,) * 4)
            + sys.getsizeof((None, None))
            + 2 * sys.getsizeof((None,) * 5)
            + 4 * sys.getsizeof(0.0)
            + 2 * point_bytes
            + 64 * sys.getsizeof(Fraction(0))
            + 32 * point_bytes
            + 8 * sys.getsizeof([None, None])
            + 2 * sys.getsizeof(OrderedDict())
            + sys.getsizeof(struct.pack(">d", 0.0))
            + sys.getsizeof((None, None))
        )
        origin_bits = max(
            max(abs(value.numerator).bit_length(), value.denominator.bit_length())
            for value in self.model.origin
        )
        # Native binary64 endpoints have <=1074-bit canonical components.
        # x subtraction/division, l10*x, then y subtraction/division use at
        # most eight such widths plus two source-origin widths. The simultaneous
        # Fraction products/quotients and their integer temporaries are bounded
        # separately from their headers above and from scaled-exp exponents.
        bits = 8 * (1 - sys.float_info.min_exp + sys.float_info.mant_dig)
        levels = len(self.region.levels)
        # <=16 levels: 2*n+4 slots dominate each append-grown accumulator.
        storage += 2 * sys.getsizeof([None] * (2 * levels + 4))
        storage += 2 * levels * sys.getsizeof(0.0)
        return storage, bits + 2 * origin_bits + 8

    def _preimage_context(self, affine):
        """Immutable actual axes/model context for ONE proof invocation."""
        from matplotlib.scale import LogTransform

        axes = self.axes
        if axes is None:
            raise KernelPrecisionError("native HDR has no drawn axes")
        iv, model = self.arithmetic, self.model
        coordinates = []
        for axis in (0, 1):
            logical_axis = axis if self._orient == "v" else 1 - axis
            scale, offset = float(affine[axis, axis]), float(affine[axis, 2])
            if not math.isfinite(scale) or scale == 0:
                raise KernelPrecisionError("native HDR affine scale collapses")
            logarithm = None
            if self._geometry_scales[axis] == "log":
                actual_axis = axes.xaxis if axis == 0 else axes.yaxis
                native = actual_axis.get_transform()
                if not isinstance(native, LogTransform):
                    raise KernelPrecisionError(
                        "native HDR log transform is unsupported"
                    )
                logarithm = iv.log_fraction(Fraction(native.base))
            coordinates.append(
                (scale, offset, logical_axis, model.log_axes[logical_axis], logarithm)
            )
        entry_bytes = (
            sys.getsizeof(OrderedDict([(None, None)]))
            - sys.getsizeof(OrderedDict())
            + sys.getsizeof(struct.pack(">d", 0.0))
            + sys.getsizeof((0.0, 0.0))
            + 2 * sys.getsizeof(0.0)
        )
        return model, iv, tuple(coordinates), entry_bytes

    @staticmethod
    def _pixel_coordinate(iv, pixel, context):
        scale, offset, _logical_axis, logarithmic, logarithm = context
        coordinate = iv.div(iv.sub(pixel, _point(offset)), _point(scale))
        return HDRCollection._fit_coordinate(iv, coordinate, logarithmic, logarithm)

    @staticmethod
    def _fit_coordinate(iv, coordinate, logarithmic, logarithm):
        if logarithm is not None:
            log_raw = iv.mul(coordinate, logarithm)
            coordinate = (
                iv.div(log_raw, iv.ln10)
                if logarithmic
                else iv.finish_scaled(*iv.exp_signed_scaled(log_raw))
            )
        elif logarithmic:
            if coordinate[0] <= 0:
                raise KernelPrecisionError("native HDR log preimage is nonpositive")
            low = iv.log_fraction(Fraction(coordinate[0]))
            high = iv.log_fraction(Fraction(coordinate[1]))
            coordinate = iv.div((low[0], high[1]), iv.ln10)
        return coordinate

    def _decoded_chart(self, nonaffine, radii, context, caches, lease):
        model, iv, coordinates, entry_bytes = context
        fit: list[tuple[Fraction, ...] | None] = [None, None]
        for axis, (value, coordinate_context) in enumerate(
            zip(nonaffine, coordinates, strict=True)
        ):
            # Preserve ALL input bits, including distinct numeric-equal zeros.
            # The other inputs are immutable in this method-local context.
            iv.budget.charge("native_hdr_preimage_scalar_lookups")
            value = float(value)
            key = struct.pack(">d", value)
            cache = caches[axis]
            if key in cache:
                iv.budget.charge("native_hdr_preimage_scalar_link_moves")
                cache.move_to_end(key)
                coordinate = cache[key]
            else:
                if len(cache) == 8192:
                    iv.budget.charge("native_hdr_preimage_scalar_evictions")
                    cache.popitem(last=False)
                else:
                    lease.grow(entry_bytes, pair_elements=3)
                displacement = radii[axis]
                coordinate = self._fit_coordinate(
                    iv,
                    iv.add(_point(value), (-displacement, displacement)),
                    coordinate_context[3],
                    coordinate_context[4],
                )
                cache[key] = coordinate
            fit[coordinate_context[2]] = tuple(map(Fraction, coordinate))
        # Only the per-axis PRE-fit intervals are reused. Every native point
        # retains the SAME exact Fraction/Cholesky cross-axis coupling.
        return model.fit_chart(tuple(fit))

    def _pixel_chart(self, pixels, context):
        model, iv, coordinates, _entry_bytes = context
        fit: list[tuple[Fraction, ...] | None] = [None, None]
        for pixel, coordinate_context in zip(pixels, coordinates, strict=True):
            coordinate = self._pixel_coordinate(iv, pixel, coordinate_context)
            fit[coordinate_context[2]] = tuple(map(Fraction, coordinate))
        return model.fit_chart(tuple(fit))

    def _clip_preimage_error(self, clip, bounds):
        if clip is None:
            return 0.0
        axes = self.axes
        if axes is None:
            raise KernelPrecisionError("native HDR has no drawn axes")
        iv, budget = self.arithmetic, self.budget
        storage, bits = self._preimage_storage()
        with (
            budget.lease(storage, pair_elements=64 + 2 * len(self.region.levels)),
            budget.integer_lease(bits, count=128),
            budget.scaled_lease(8),
        ):
            affine = self.get_transform().get_affine().get_matrix()
            context = self._preimage_context(affine)
            serialization = iv.fraction(
                Fraction.from_float(self.figure.dpi) / 2_000_000
            )[1]
            display_bounds = self._display(bounds)
            inverted = axes.xaxis_inverted(), axes.yaxis_inverted()
            error = 0.0
            for x_side, y_side in itertools.product((0, 1), repeat=2):
                pixel = (
                    (clip.x0, clip.x1)[x_side],
                    (clip.y0, clip.y1)[y_side],
                )
                raw = tuple(
                    display_bounds[axis][1 - side if inverted[axis] else side]
                    for axis, side in enumerate((x_side, y_side))
                )
                expected, _fit = self.model.query_chart(self._logical(raw))
                actual = self._pixel_chart(
                    tuple(
                        iv.add(_point(value), (-serialization, serialization))
                        for value in pixel
                    ),
                    context,
                )
                for a, b in zip(actual, expected, strict=True):
                    error = max(error, _magnitude(iv.sub(a, b)))
            return error

    def _native_fingerprint(self, transform, *, measure):
        """Stream live path and pre-affine bytes (including all path codes)."""
        from matplotlib.path import Path

        budget = self.budget
        digest = hashlib.sha256()
        magnitude = [0.0, 0.0]
        # At most log, base division, nonpositive test/write and blend per
        # axis, plus a code comparison/reduction and optional four reductions.
        visits = 2 + (0 if transform.is_affine else 10) + (4 if measure else 0)
        # Fixed digest, headers and memoryviews, plus one native Path workspace.
        with budget.lease(4096):
            for path, ideal in zip(self.get_paths(), self._ideal_paths, strict=True):
                vertices = cast(np.ndarray, path.vertices)
                codes = cast("np.ndarray | None", path.codes)
                count = len(ideal)
                if (
                    vertices.shape != (count, 2)
                    or vertices.dtype != np.float64
                    or not vertices.flags.c_contiguous
                    or codes is None
                    or codes.shape != (count,)
                    or codes.dtype != np.uint8
                    or not codes.flags.c_contiguous
                    or path.should_simplify
                    or cast(_NativePathTopology, path)._interpolation_steps != 1
                ):
                    raise KernelPrecisionError("unsupported native HDR path topology")
                # Count streamed words, per-path setup, native transform and
                # explicit scans (not merely cache miss counts).
                budget.charge(
                    "native_hdr_path_authentication",
                    (vertices.nbytes * 2 + codes.nbytes + 7) // 8 + visits * count + 16,
                )
                with (
                    budget.array_lease((count, 2), active=True, copies=3),
                    budget.array_lease((count,), "bool"),
                ):
                    if (
                        codes[0] != Path.MOVETO
                        or codes[-1] != Path.CLOSEPOLY
                        or np.any(codes[1:-1] != Path.LINETO)
                        or not np.array_equal(vertices[0], vertices[-1])
                    ):
                        raise KernelPrecisionError("unsupported native HDR path codes")
                    native = transform.transform_path_non_affine(path)
                    native_vertices = cast(np.ndarray, native.vertices)
                    if (
                        native_vertices.shape != vertices.shape
                        or native_vertices.dtype != np.float64
                        or not native_vertices.flags.c_contiguous
                    ):
                        raise KernelPrecisionError(
                            "native HDR path transform changed topology"
                        )
                    if native.codes is not codes:
                        budget.charge("native_hdr_path_authentication", 2 * count)
                        if not np.array_equal(native.codes, codes):
                            raise KernelPrecisionError(
                                "native HDR path transform changed topology"
                            )
                    digest.update(struct.pack(">Q", count))
                    digest.update(vertices.data.cast("B"))
                    digest.update(codes.data)
                    digest.update(native_vertices.data.cast("B"))
                    if measure:
                        for axis in (0, 1):
                            values = native_vertices[:, axis]
                            low, high = float(values.min()), float(values.max())
                            if not (math.isfinite(low) and math.isfinite(high)):
                                raise KernelPrecisionError(
                                    "nonfinite native HDR path vertex"
                                )
                            magnitude[axis] = max(magnitude[axis], abs(low), abs(high))
                        del values
                    del native, native_vertices
        return digest.digest(), tuple(magnitude)

    def _geometry_error(self, clip_error):
        """Prove a pre-affine tube once; check the current renderer on every draw."""
        from matplotlib.scale import LogTransform

        axes = self.axes
        transform = self.get_transform()
        if (
            axes is None
            or axes.name != "rectilinear"
            or transform is not axes.transData
            or self.have_units()
            or len(self.get_transforms())
            or self.get_clip_path() is not None
            or not self.get_clip_on()
            or self.get_path_effects()
            or self.get_sketch_params() is not None
        ):
            raise KernelPrecisionError(
                "native HDR requires its declared Cartesian artist"
            )
        offsets = cast(np.ndarray, self.get_offsets())
        offset_transform = self.get_offset_transform()
        if (
            offsets.shape != (1, 2)
            or np.any(offsets)
            or not offset_transform.is_affine
            or not np.array_equal(offset_transform.get_matrix(), np.eye(3))
        ):
            raise KernelPrecisionError(
                "native HDR requires its declared Cartesian artist"
            )
        affine = transform.get_affine().get_matrix()
        if (
            not np.all(np.isfinite(affine))
            or affine[0, 1] != 0
            or affine[1, 0] != 0
            or not np.array_equal(affine[2], [0, 0, 1])
        ):
            raise KernelPrecisionError("native HDR requires separable Cartesian axes")
        policy = []
        for scale, axis in zip(
            self._geometry_scales, (axes.xaxis, axes.yaxis), strict=True
        ):
            native = axis.get_transform()
            if scale == "log":
                if (
                    type(native) is not LogTransform
                    or not math.isfinite(native.base)
                    or native.base <= 0
                    or native.base == 1
                ):
                    raise KernelPrecisionError(
                        "unsupported native HDR logarithmic policy"
                    )
                policy.append(
                    (float(native.base), cast(_NativeLogPolicy, native)._clip)
                )
            else:
                if scale != "linear" or not native.is_affine:
                    raise KernelPrecisionError("unsupported native HDR axis policy")
                policy.append(None)
        prior = self._native_certificate
        policy = tuple(policy)
        fingerprint, measured = self._native_fingerprint(
            transform, measure=prior is None
        )
        if prior is not None:
            if prior[0] == fingerprint:
                measured = prior[2]
            else:
                fingerprint, measured = self._native_fingerprint(
                    transform, measure=True
                )

        def acceptable(result):
            return self._total_error(result[0][-1], clip_error) <= self._tolerance

        iv = self.arithmetic
        with self.budget.integer_lease(8192, count=32):
            self.budget.charge("native_hdr_affine_radius", 40, bits=8192)
            radii = tuple(
                _affine_radius(
                    float(affine[i, i]),
                    float(affine[i, 2]),
                    measured[i],
                    self.figure.dpi,
                )
                for i in (0, 1)
            )
            if prior is not None:
                signature, old_policy, _measured, envelope, result = prior
                if (
                    signature == fingerprint
                    and old_policy == policy
                    and all(
                        radius <= bound
                        for radius, bound in zip(radii, envelope, strict=True)
                    )
                    and acceptable(result)
                ):
                    return result
            exact = tuple(iv.fraction(radius)[1] for radius in radii)
            # Optional 9/8 headroom for first layout settlement, never a gate.
            envelope = (
                tuple(iv.fraction(radius * Fraction(9, 8))[1] for radius in radii)
                if prior is None
                else exact
            )
        context = self._preimage_context(affine)
        # Fitted model, ordered cells, chords and ideals are construction-owned.
        # The externally accessible Matplotlib Paths are not: they must
        # authenticate under the current native policy, including when refitted.
        with self.budget.lease(4096):
            if envelope != exact:
                try:
                    result = self._certify_geometry(transform, context, envelope)
                except KernelPrecisionError:
                    envelope = exact
                else:
                    if not acceptable(result):
                        envelope = exact
            if envelope == exact:
                result = self._certify_geometry(transform, context, exact)
            if not acceptable(result):
                raise KernelPrecisionError(
                    "full HDR native geometry exceeds requested total error"
                )
            if self._native_certificate_lease is None:
                self._native_certificate_lease = self.budget.lease(4096)
            self._native_certificate = (fingerprint, policy, measured, envelope, result)
        return result

    def _total_error(self, geometry_error, clip_error):
        iv = self.arithmetic
        return iv.add(
            iv.add(_point(self.region.probability_error), _point(geometry_error)),
            _point(clip_error),
        )[1]

    def _certify_geometry(self, transform, context, radii):
        iv, budget = self.arithmetic, self.budget
        storage, bits = self._preimage_storage()
        with (
            budget.lease(
                storage, pair_elements=64 + 2 * len(self.region.levels)
            ) as lease,
            budget.integer_lease(bits, count=128),
            budget.scaled_lease(8),
        ):
            # No affine or serializer arithmetic inside the coupled vertex proof.
            caches = OrderedDict(), OrderedDict()
            by_band = [0.0] * len(self.region.levels)
            maximum_delta = 0.0
            try:
                for path, ideal, chord, cell in zip(
                    self.get_paths(),
                    self._ideal_paths,
                    self._chords,
                    self.region.cells,
                    strict=True,
                ):
                    count = len(np.asarray(path.vertices))
                    budget.charge("native_hdr_preimage_vertices", count)
                    with budget.array_lease((count, 2), active=True, copies=3):
                        vertices = np.asarray(
                            transform.transform_path_non_affine(path).vertices
                        )
                        error = 0.0
                        for point, expected in zip(vertices, ideal, strict=True):
                            actual = self._decoded_chart(
                                point, radii, context, caches, lease
                            )
                            for bound, value in zip(actual, expected, strict=True):
                                error = max(
                                    error, _magnitude(iv.sub(bound, _point(value)))
                                )
                        del point, vertices
                        delta = iv.add(_point(error), _point(chord))[1]
                        a, b, c, d = cell[0]
                        width, height = (
                            iv.sub(_point(b), _point(a)),
                            iv.sub(_point(d), _point(c)),
                        )
                        if delta >= min(width[0], height[0]) / 16:
                            raise KernelPrecisionError(
                                "native HDR preimage tube cannot resolve cell topology"
                            )
                        area = iv.add(
                            iv.mul(
                                iv.mul((4.0, 4.0), _point(delta)), iv.add(width, height)
                            ),
                            iv.mul((16.0, 16.0), iv.mul(_point(delta), _point(delta))),
                        )
                        band = cell[3]
                        by_band[band] = iv.add(
                            _point(by_band[band]),
                            iv.mul(area, _point(self._probability_peak())),
                        )[1]
                        maximum_delta = max(maximum_delta, delta)
                prefix = []
                for value in by_band:
                    prefix.append(
                        iv.add(_point(prefix[-1] if prefix else 0.0), _point(value))[1]
                    )
                return tuple(prefix), maximum_delta
            finally:
                for cache in caches:
                    cache.clear()

    def _visible_mass(self, bounds):
        iv, budget = self.arithmetic, self.budget
        lower = [0.0] * len(self.region.levels)
        upper = [0.0] * len(self.region.levels)
        heap = []
        serial = itertools.count()
        totals = [0.0, 0.0]
        pointer = sys.getsizeof([None]) - sys.getsizeof([])
        heap_lease = budget.lease(
            sys.getsizeof([]) + 2 * MAX_HDR_ACTIVE_CELLS * pointer
        )

        def classify(box):
            raw = self._raw_box(box)
            if any(
                high < clip[0] or low > clip[1]
                for (low, high), clip in zip(raw, bounds, strict=True)
            ):
                return -1
            if all(
                clip[0] <= low and high <= clip[1]
                for (low, high), clip in zip(raw, bounds, strict=True)
            ):
                return 1
            return 0

        def enqueue(box, band, depth, mass=None):
            budget.charge("native_hdr_visible_cells")
            status = classify(box)
            if status < 0:
                return
            if mass is None:
                mass = self.model.rectangle_mass(((box[0], box[1]), (box[2], box[3])))
            if status:
                lower[band] = iv.add(_point(lower[band]), _point(mass[0]))[0]
                upper[band] = iv.add(_point(upper[band]), _point(mass[1]))[1]
                totals[0] = iv.add(_point(totals[0]), _point(mass[0]))[0]
                totals[1] = iv.add(_point(totals[1]), _point(mass[1]))[1]
                return
            if len(heap) >= MAX_HDR_ACTIVE_CELLS:
                raise FieldResourceError(
                    "native HDR visible clipping exceeds65536 active cells"
                )
            sequence = next(serial)
            lease = budget.account((-mass[1], sequence, box, band, depth, mass, None))
            heapq.heappush(heap, (-mass[1], sequence, box, band, depth, mass, lease))
            upper[band] = iv.add(_point(upper[band]), _point(mass[1]))[1]
            totals[1] = iv.add(_point(totals[1]), _point(mass[1]))[1]

        try:
            for (box, _path, depth, band), mass in zip(
                self.region.cells, self.region.cell_masses, strict=True
            ):
                enqueue(box, band, depth, mass)
            target = self._tolerance / 128
            while heap and iv.sub(_point(totals[1]), _point(totals[0]))[1] > target:
                _priority, _serial, box, band, depth, mass, lease = heapq.heappop(heap)
                lease.close()
                upper[band] = iv.sub(_point(upper[band]), _point(mass[1]))[1]
                totals[1] = iv.sub(_point(totals[1]), _point(mass[1]))[1]
                for child in children(box, iv):
                    enqueue(child, band, depth + 1)
            result = []
            lo = hi = 0.0
            for a, b in zip(lower, upper, strict=True):
                lo = iv.add(_point(lo), _point(a))[0]
                hi = iv.add(_point(hi), _point(b))[1]
                result.append(
                    (
                        max(0.0, lo - self.model.source_tv),
                        min(1.0, hi + self.model.source_tv),
                    )
                )
            return tuple(result)
        finally:
            for entry in heap:
                entry[-1].close()
            heap.clear()
            heap_lease.close()

    def draw(self, renderer):
        if self.axes is None:
            return
        if (self.axes.get_xscale(), self.axes.get_yscale()) != self._geometry_scales:
            raise KernelPrecisionError(
                "native HDR scale changed; render the declared source again"
            )
        clip = self._query_clip()
        self.set_clip_box(clip if clip is not None else Bbox.from_bounds(0, 0, 0, 0))
        logical_limits = self._logical(
            (tuple(sorted(self.axes.get_xlim())), tuple(sorted(self.axes.get_ylim())))
        )
        bounds = tuple(
            (max(view[0], query[0]), min(view[1], query[1]))
            for view, query in zip(logical_limits, self.query_bounds, strict=True)
        )
        iv = self.arithmetic
        a, b, c, d = self.region.root
        clip_delta = (
            0.0
            if any(low >= high for low, high in bounds)
            else self._clip_preimage_error(clip, bounds)
        )
        extent = iv.add(
            iv.sub(_point(b), _point(a)),
            iv.sub(_point(d), _point(c)),
        )
        clip_area = iv.add(
            iv.mul(iv.mul((8.0, 8.0), _point(clip_delta)), extent),
            iv.mul((32.0, 32.0), iv.mul(_point(clip_delta), _point(clip_delta))),
        )
        clip_error = iv.mul(clip_area, _point(self._probability_peak()))[1]
        with self.budget.lease(4096):
            errors, delta = self._geometry_error(clip_error)
        if any(low >= high for low, high in bounds):
            visible = ((0.0, 0.0),) * len(self.region.levels)
        else:
            if bounds != self._visible_key:
                self._visible_result = self._visible_mass(bounds)
                self._visible_key = bounds
            visible = self._visible_result
            if visible is None:
                raise KernelPrecisionError(
                    "native HDR visibility certificate is missing"
                )
        records = []
        for level, error, clipped in zip(
            self.region.levels, errors, visible, strict=True
        ):
            total = self._total_error(error, clip_error)
            records.append(
                {
                    "target": level.target,
                    "cutoff": level.cutoff,
                    "full_region_probability": [level.mass_lower, level.mass_upper],
                    "native_included_probability": [
                        max(0.0, level.inside_lower - error),
                        min(1.0, level.mass_upper + error),
                    ],
                    "native_geometry_mass_error": error,
                    "total_conditional_error": total,
                    "visible_probability": [
                        max(0.0, clipped[0] - error - clip_error),
                        min(1.0, clipped[1] + error + clip_error),
                    ],
                    "visible_clip_precision_error": clip_error,
                    "visible_probability_is_not_target_mass": True,
                }
            )
        self._mudplot_hdr.update(
            levels=records,
            actual_logical_view=bounds,
            native_preimage_error=delta,
            actual_clip_preimage_error=clip_delta,
            backend_geometry_scope=(
                "supported PNG geometry/SVG/PDF/PGF vector paths; "
                "not raster-pixel probability"
            ),
        )
        self.region.geometry_error = max(errors, default=0.0)
        super().draw(renderer)

    def _release(self):
        if self._closed:
            return
        self._closed = True
        self._native_certificate = None
        if self._native_certificate_lease is not None:
            self._native_certificate_lease.close()
            self._native_certificate_lease = None
        for lease in reversed(self._geometry_leases):
            lease.close()
        self._geometry_leases.clear()
        self.region.close()
        self.model.close()

    def remove(self):
        super().remove()
        self._release()
