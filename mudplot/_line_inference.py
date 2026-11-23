"""Complete original-unit line inference and render-local NEW resource admission.

Finite samples use the shared canonical reducer/interpolator. Only extended
undefined scores use infinity; finite calibration scores never become floats.
"""

from __future__ import annotations

import heapq
import math
import struct
import sys
import warnings
from dataclasses import dataclass, fields, is_dataclass, replace
from fractions import Fraction

import numpy as np

from ._ecdf import canonical_type7, finite_number
from ._estimate import (
    Estimate,
    Summary,
    _finite_float,
    _ResamplingWork,
    _Sample,
    summarize,
)
from ._facet import panel_rows
from ._line import (
    MAX_LINE_CHOICES,
    MAX_LINE_STATE_BYTES,
    MAX_LINE_WORK,
    MAX_UNIT_ROWS,
    categorical_predictor,
    known_line_work,
    line_structure,
    unit_request,
    whole_unit_shape,
)
from ._semantics import category_key, semantic_curve_input
from ._stat import (
    explicit_line_inference,
    new_stat_request,
    stat_config,
    stat_key,
    unit_key,
)
from ._temporal_data import prepare_temporal_layer, select_line_rows


class _Tail:
    """A public-heapq min heap; sign reversal supplies a bounded max heap."""

    __slots__ = ("capacity", "smallest", "values")

    def __init__(self, capacity, smallest):
        self.capacity = capacity
        self.smallest = smallest
        self.values = []

    def add(self, value):
        if len(self.values) < self.capacity:
            heapq.heappush(self.values, -value if self.smallest else value)
        elif self.smallest:
            if value < -self.values[0]:
                heapq.heapreplace(self.values, -value)
        elif value > self.values[0]:
            heapq.heapreplace(self.values, value)

    def rank_value(self):
        return -self.values[0] if self.smallest else self.values[0]

    def ordered(self):
        if self.smallest:
            return sorted(-value for value in self.values)
        return sorted(self.values)

    def clear(self):
        self.values.clear()


class _Ranks:
    __slots__ = ("positions", "size", "tails", "undefined")

    def __init__(self, size, level, simultaneous):
        self.size = size
        self.undefined = 0
        probability = Fraction(level) / 100
        if simultaneous:
            rank = math.ceil(probability * size)
            lower, upper = rank, size - rank + 1
            self.positions = None
            self.tails = (_Tail(min(lower, upper), lower <= upper),)
        else:
            self.positions = (
                (size - 1) * (1 - probability) / 2,
                (size - 1) * (1 + probability) / 2,
            )
            self.tails = (
                _Tail(math.ceil(self.positions[0]) + 1, True),
                _Tail(size - math.floor(self.positions[1]), False),
            )

    def add(self, value):
        if value is math.inf or (isinstance(value, float) and math.isinf(value)):
            self.undefined += 1
        for tail in self.tails:
            tail.add(value)

    def maximum_quantile(self):
        return self.tails[0].rank_value()

    def percentile(self):
        if self.undefined:
            raise ValueError(
                "complete-unit pointwise percentile requires every replicate defined; "
                f"{self.undefined} undefined replicates retained, no draws retried"
            )
        lower, upper = (tail.ordered() for tail in self.tails)
        result = []
        assert self.positions is not None
        for position in self.positions:
            low, high = math.floor(position), math.ceil(position)

            def observed(rank):
                if rank < len(lower):
                    return lower[rank]
                return upper[rank - (self.size - len(upper))]

            result.append(
                canonical_type7((observed(low), observed(high)), position - low)
            )
        return tuple(result)

    def clear(self):
        for tail in self.tails:
            tail.clear()


@dataclass(slots=True)
class _Cell:
    category: object
    group: object
    sample: _Sample
    unit_indices: np.ndarray
    center: Fraction
    n: int
    n_units: int


@dataclass(slots=True)
class PreparedLine:
    summary: Summary
    grids: dict
    point_rows: dict
    curves: list
    caption: str | None
    undefined: dict
    source_rows: tuple


def _owned_size(value):
    """Conservative product-graph charge; shared referents may be counted twice.

    Product inference structures have no owner back-references. Avoiding a
    visited-object registry also avoids an unbudgeted planner-sized cache.
    """
    size = sys.getsizeof(value)
    if isinstance(value, Fraction):
        return size + _owned_size(value.numerator) + _owned_size(value.denominator)
    if isinstance(value, dict):
        return size + sum(
            _owned_size(key) + _owned_size(item) for key, item in value.items()
        )
    if isinstance(value, (list, tuple, set)):
        return size + sum(_owned_size(item) for item in value)
    if isinstance(value, np.ndarray):
        return size + (_owned_size(value.base) if value.base is not None else 0)
    if is_dataclass(value) and not isinstance(value, type):
        size += sum(_owned_size(getattr(value, field.name)) for field in fields(value))
        if hasattr(value, "__dict__"):
            size += sys.getsizeof(value.__dict__)
        return size
    if hasattr(value, "__dict__"):
        return size + _owned_size(value.__dict__)
    slots = getattr(type(value), "__slots__", ())
    return size + sum(
        _owned_size(getattr(value, slot))
        for slot in slots
        if slot not in {"__weakref__", "__dict__"} and hasattr(value, slot)
    )


class FigureLineBudget:
    __slots__ = (
        "cell_base",
        "cell_reductions",
        "cell_unit_case",
        "coordinates",
        "peak_state",
        "retained",
        "whole_unit",
    )

    def __init__(self):
        self.whole_unit = self.cell_unit_case = self.cell_reductions = 0
        self.coordinates = 0
        self.retained = self.peak_state = 0
        self.cell_base = 0

    @property
    def total(self):
        return (
            self.whole_unit
            + self.cell_unit_case
            + self.cell_reductions
            + self.coordinates
        )

    def _check_work(self, extra):
        if self.total + extra > MAX_LINE_WORK:
            raise ValueError(
                "NEW line figure logical work exceeds2000000000 before its next chunk "
                f"(whole_unit={self.whole_unit}, cell_unit_case={self.cell_unit_case}, "
                f"cell_reductions={self.cell_reductions}, next={extra}); "
                "no partial native output was published"
            )

    def admit_unit(self, work):
        self._check_work(work)
        self.whole_unit += work

    def admit_cell(self, cases, reductions):
        self._check_work(cases + reductions)
        self.cell_unit_case += cases
        self.cell_reductions += reductions

    def admit_coordinates(self, work, storage):
        self._check_work(work)
        self.admit_state(storage)
        self.coordinates += work

    def admit_state(self, working):
        total = self.retained + working
        if total > MAX_LINE_STATE_BYTES:
            raise ValueError(
                "NEW line inference working state exceeds268435456 bytes "
                f"(retained_summaries={self.retained}, next_state={working}); "
                "exact values, confidence level and replicate count were not reduced"
            )
        self.peak_state = max(self.peak_state, total)

    def admit_cell_input(self, values, weights, estimator):
        self.admit_state(
            self.cell_base + _cell_sample_bound(values, weights, estimator)
        )

    def admit_cell_plan(self, sample):
        growth = 2 * max(1, len(sample.values)).bit_length()
        bits = (
            sample._product_max.bit_length()
            + sample._mass_max.bit_length()
            + sample.value_denominator.bit_length()
            + growth
            + sys.float_info.max_exp
            - sys.float_info.min_exp
            + sys.float_info.mant_dig
        )
        self.admit_state(
            self.cell_base
            + _owned_size(sample)
            + 8 * sys.getsizeof(1 << (2 * bits + 4))
        )

    def retain(self, prepared):
        # Include the outer render-local result table's conservative per-entry cost.
        entry = sys.getsizeof({0: None}) - sys.getsizeof({})
        self.retained += _owned_size(prepared) + entry + sys.getsizeof((0, 0))
        self.admit_state(0)

    def report(self):
        return {
            "whole_unit": self.whole_unit,
            "cell_unit_case": self.cell_unit_case,
            "cell_reductions": self.cell_reductions,
            "total": self.total,
            "peak_admitted_working_state_bytes": self.peak_state,
            "retained_summary_bytes": self.retained,
            **({"coordinates": self.coordinates} if self.coordinates else {}),
        }


def _input(spec, panel, layer, *, project=True, budget=None):
    from ._transforms import projection_storage, projects, stages_for

    columns = spec.data.columns
    candidates = panel_rows(columns, panel) if panel.filters or panel.dropna else None
    selected = select_line_rows(columns, layer, panel, candidates=candidates)
    predictor_axis = (
        (panel.y2 if layer.axis == "y2" else panel.y)
        if layer.orient == "h"
        else panel.x
    )
    if (
        not categorical_predictor(layer)
        and predictor_axis.temporal is None
        and not stages_for(layer, "x")
    ):
        selected = [row for row in selected if finite_number(columns[layer.x][row])]
    if unit_request(layer) and len(selected) > MAX_UNIT_ROWS:
        raise ValueError("complete-unit selected trajectory rows exceed10000")
    config = stat_config(layer)
    names = [layer.x, layer.y, layer.group, config.weights, config.units]
    if layer.semantics is not None:
        names += [getattr(layer.semantics, role) for role in ("hue", "size", "style")]
    names = list(dict.fromkeys(name for name in names if name is not None))
    if project and budget is not None and projects(layer):
        work = sum(
            len(stages_for(layer, role)) * (len(selected) + len(layer.order or ()))
            for role in ("x", "y")
        )
        scratch = projection_storage(columns, layer, len(selected))
        pointer = struct.calcsize("P")
        copied = len(names) * (sys.getsizeof([]) + 2 * len(selected) * pointer)
        budget.admit_coordinates(work, scratch + copied)
    view = {name: [columns[name][row] for row in selected] for name in names}
    converted, layer, _mask = prepare_temporal_layer(
        view, layer if project else replace(layer, transforms=None), panel
    )
    return converted, layer, tuple(selected)


def _caption(layer, undefined):
    config = stat_config(layer)
    level = 95.0 if config.level is None else config.level
    complete = unit_request(layer)
    simultaneous = layer.line.calibration == "max_deviation"
    empirical = config.estimator in {"min", "max"}
    scope = "layer" if layer.line.family == "layer" else "curve"
    if empirical:
        method = (
            f"simultaneous empirical deviation envelope ({scope} grid)"
            if simultaneous
            else "pointwise empirical bootstrap percentile envelope"
        )
        text = (
            f"{level:g}% {method}\n{config.estimator} is nonregular: "
            "not population endpoint confidence"
        )
        warnings.warn(text, UserWarning, stacklevel=4)
    else:
        method = (
            f"finite-grid simultaneous CI\nnominal {scope} family"
            if simultaneous
            else "pointwise percentile CI, nominal\nnot simultaneous"
        )
        text = f"{level:g}% {method}"
    text += (
        "\ncomplete original units"
        if complete
        else "\nper-cell unit then row resampling"
        if config.units is not None
        else "\nper-cell row resampling"
    )
    missing = sum(undefined.values())
    if missing:
        text += f"; {missing} undefined family replicates retained"
    return text


def _prepared(summary, structure, layer, source_ids, group_values, curves, undefined):
    grids, point_rows = {}, {}
    for (key, _hue), value in zip(structure.groups, group_values, strict=True):
        grids[stat_key(value)] = structure.grids[key]
        for category in structure.grids[key]:
            selected = structure.topology_cells.get((key, category_key(category)), ())
            point_rows[(stat_key(value), category_key(category))] = tuple(
                source_ids[row] for row in selected
            )
    return PreparedLine(
        summary,
        grids,
        point_rows,
        curves,
        _caption(layer, undefined) if summary.estimates else None,
        undefined,
        source_ids,
    )


def _multiplicities(rng, units, replicates):
    """Flat int64 choices; crossing a buffer boundary never redraws a unit."""
    remaining = units * replicates
    buffer, position = None, 0
    for _ in range(replicates):
        need, counts = units, None
        while need:
            if buffer is None or position == len(buffer):
                size = min(MAX_LINE_CHOICES, remaining)
                buffer = None
                buffer = rng.integers(0, units, size=size, dtype=np.int64)
                position = 0
                remaining -= size
            take = min(need, len(buffer) - position)
            part = np.bincount(buffer[position : position + take], minlength=units)
            if counts is None:
                counts = part
            else:
                counts += part
            position += take
            need -= take
        yield counts


def _state_bytes(
    cells,
    structure,
    unit_indices,
    source_ids,
    size,
    level,
    simultaneous,
    family,
    estimator,
):
    probe = _Ranks(size, level, simultaneous)
    groups = len({stat_key(cell.group) for cell in cells})
    vectors = len(cells) if not simultaneous else groups if family == "curve" else 1
    pointer = struct.calcsize("P")
    count_bits = max(1, (max(1, len(structure.rows) * len(unit_indices))).bit_length())
    originals = max(1, len(structure.rows)).bit_length()
    value_bits = max(
        (max(abs(value).bit_length() for value in cell.sample.units) for cell in cells),
        default=1,
    )
    mass_bits = max((max(cell.sample.masses).bit_length() for cell in cells), default=1)
    product_bits = max(
        (
            max(abs(value).bit_length() for value in cell.sample.products)
            for cell in cells
        ),
        default=1,
    )
    # Mean cancels the canonical weight denominator; a weighted total does not.
    # Carry that physical-mass denominator through scores, endpoints and scratch.
    denominator_bits = max(
        (
            cell.sample.value_denominator.bit_length()
            + (cell.sample.weight_denominator.bit_length() if estimator == "sum" else 0)
            for cell in cells
        ),
        default=1,
    )
    ordered = estimator in {"median", "min", "max"}
    if ordered:
        numerator, denominator = value_bits + 2, denominator_bits + 1
    else:
        numerator = product_bits + count_bits + 1
        denominator = denominator_bits + mass_bits + count_bits + 1
    if simultaneous:
        if ordered:
            numerator, denominator = numerator + denominator + 1, 2 * denominator
        else:
            center_numerator = product_bits + originals + 1
            center_denominator = denominator_bits + mass_bits + originals + 1
            numerator, denominator = (
                max(numerator + center_denominator, center_numerator + denominator) + 1,
                denominator + center_denominator,
            )
    fraction = (
        sys.getsizeof(Fraction())
        + sys.getsizeof(1 << numerator)
        + sys.getsizeof(1 << denominator)
    )
    retained = vectors * sum(tail.capacity for tail in probe.tails)
    # Double capacity plus fixed growth slack safely exceeds native list growth.
    lists = vectors * sum((2 * tail.capacity + 16) * pointer for tail in probe.tails)
    controls = vectors * _owned_size(probe)
    plans = _owned_size((cells, structure, unit_indices, source_ids))
    endpoint_n = (
        2 * numerator
        + 2 * denominator
        + Fraction(level).denominator.bit_length()
        + size.bit_length()
        + 8
    )
    endpoint_d = (
        2 * denominator
        + Fraction(level).denominator.bit_length()
        + size.bit_length()
        + 8
    )
    endpoint_fraction = (
        sys.getsizeof(Fraction())
        + sys.getsizeof(1 << endpoint_n)
        + sys.getsizeof(1 << endpoint_d)
    )
    endpoints = 2 * len(cells) * endpoint_fraction
    temporary_bits = max(
        2 * (numerator + denominator) + 4,
        product_bits + count_bits + 2,
        mass_bits + count_bits + 2,
        endpoint_n + endpoint_d + 4,
    )
    selection_scratch = (
        max((tail.capacity for tail in probe.tails), default=0) * 2 * pointer
    )
    if not simultaneous:
        # One vector finalizes at a time; all remaining heaps stay charged above.
        # Negating the lower tail creates Fraction/numerator objects. Its ordered
        # list remains live while the upper list and sort workspace are built.
        selection_scratch += probe.tails[0].capacity * (
            sys.getsizeof(Fraction()) + sys.getsizeof(1 << numerator)
        )
        selection_scratch += sum(
            sys.getsizeof(tail.values) + (2 * tail.capacity + 16) * pointer
            for tail in probe.tails
        )
    scratch = (
        min(MAX_LINE_CHOICES, size * len(unit_indices)) * np.dtype(np.int64).itemsize
        + (3 * len(unit_indices) + 2 * len(structure.rows)) * np.dtype(np.intp).itemsize
        + 8 * sys.getsizeof(1 << temporary_bits)
        + selection_scratch
        + max(1, groups) * fraction
        + endpoints
    )
    tables = vectors * (sys.getsizeof((None, None)) + sys.getsizeof({0: None}))
    return retained * fraction + lists + controls + plans + scratch + tables


def _native_bounds(center, lower, upper, axis_log, value_scale):
    exact_span = lower < upper
    numbers = np.asarray([_finite_float(value) for value in (center, lower, upper)])
    if exact_span and numbers[1] >= numbers[2]:
        raise ValueError(
            "positive complete-unit interval collapses in native coordinates"
        )
    if axis_log:
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            numbers = np.power(10.0, numbers)
        if np.any(~np.isfinite(numbers)) or np.any(numbers <= 0):
            raise ValueError(
                "inverse log complete-unit interval exceeds positive finite range"
            )
        if exact_span and numbers[1] >= numbers[2]:
            raise ValueError("positive inverse-log complete-unit interval collapses")
    if value_scale == "log" and np.any(numbers <= 0):
        raise ValueError("log-value complete-unit endpoints must be positive")
    return tuple(float(value) for value in numbers)


def _unit_summary(columns, layer, structure, source_ids, value_scale, budget):
    config = stat_config(layer)
    _n, _u, _k, work = whole_unit_shape(structure, columns, layer)
    budget.admit_unit(work)
    semantic = layer.semantics is not None
    group_values = [
        index if semantic else hue for index, (_key, hue) in enumerate(structure.groups)
    ]
    group_index = {key: index for index, (key, _hue) in enumerate(structure.groups)}
    curves = []
    for index, (key, hue) in enumerate(structure.groups):
        if semantic and any(target[0] == key for target in structure.cells):
            curves.append(
                {**structure.roles[index], "_index": index, "legacy_hue": hue}
            )
    if not structure.cells:
        budget.admit_state(_owned_size((structure, source_ids)))
        summary = Summary(structure.categories, group_values, [], True)
        return _prepared(
            summary, structure, layer, source_ids, group_values, curves, {}
        )
    lookup = {}
    for row in structure.rows:
        key = unit_key(columns[config.units][row], True)
        if key not in lookup:
            lookup[key] = len(lookup)
    axis_log = layer.stat_scale == "axis" and value_scale == "log"
    cells = []
    for (key, _category), rows in structure.cells.items():
        values = np.asarray([columns[layer.y][row] for row in rows], dtype=object)
        if axis_log:
            values = np.log10(np.asarray(values, dtype=float))
        weights = (
            None
            if config.weights is None
            else [columns[config.weights][row] for row in rows]
        )
        sample = _Sample(values, weights, ordered=config.estimator == "median")
        ids = np.asarray(
            [lookup[unit_key(columns[config.units][row], True)] for row in rows],
            dtype=np.intp,
        )
        contributors = len(set(ids.tolist()))
        if contributors < 2:
            raise ValueError(
                "complete-unit targets require at least2 contributing units"
            )
        raw_category = columns[layer.x][rows[0]]
        center = sample.estimate(config.estimator, exact=True)
        assert isinstance(center, Fraction)
        _finite_float(center)
        cells.append(
            _Cell(
                raw_category,
                group_values[group_index[key]],
                sample,
                ids,
                center,
                len(rows),
                contributors,
            )
        )
    simultaneous = layer.line.calibration == "max_deviation"
    family = layer.line.family or "curve"
    level = 95.0 if config.level is None else config.level
    budget.admit_state(
        _state_bytes(
            cells,
            structure,
            lookup,
            source_ids,
            config.n_boot,
            level,
            simultaneous,
            family,
            config.estimator,
        )
    )
    keys = (
        list(range(len(cells)))
        if not simultaneous
        else [
            stat_key(value)
            for value in group_values
            if any(stat_key(cell.group) == stat_key(value) for cell in cells)
        ]
        if family == "curve"
        else ["layer"]
    )
    ranks = {key: _Ranks(config.n_boot, level, simultaneous) for key in keys}
    rng = np.random.Generator(np.random.PCG64(config.seed))
    try:
        for multiplicity in _multiplicities(rng, len(lookup), config.n_boot):
            assert multiplicity is not None
            maxima = {key: Fraction(0) for key in keys} if simultaneous else None
            for index, cell in enumerate(cells):
                assert cell.unit_indices is not None
                counts = multiplicity[cell.unit_indices]
                value = (
                    cell.sample.estimate(config.estimator, counts, exact=True)
                    if np.any(counts)
                    else math.inf
                )
                if maxima is not None:
                    key = stat_key(cell.group) if family == "curve" else "layer"
                    delta = abs(value - cell.center)
                    if delta > maxima[key]:
                        maxima[key] = delta
                else:
                    ranks[index].add(value)
            if maxima is not None:
                for key, value in maxima.items():
                    ranks[key].add(value)
        undefined = {
            key: rank.undefined for key, rank in ranks.items() if rank.undefined
        }
        selected = {}
        if simultaneous:
            for key, rank in ranks.items():
                quantile = rank.maximum_quantile()
                if isinstance(quantile, float) and math.isinf(quantile):
                    raise ValueError(
                        "complete-unit finite band rejected: "
                        "selected upper rank is infinite "
                        f"for family {key!r}; "
                        f"{rank.undefined}/{config.n_boot} undefined "
                        "replicates retained, no conditional retries"
                    )
                selected[key] = quantile
        estimates = []
        for index, cell in enumerate(cells):
            if simultaneous:
                key = stat_key(cell.group) if family == "curve" else "layer"
                lower, upper = cell.center - selected[key], cell.center + selected[key]
            else:
                lower, upper = ranks[index].percentile()
            center, low, high = _native_bounds(
                cell.center, lower, upper, axis_log, value_scale
            )
            estimates.append(
                Estimate(
                    cell.category, cell.group, center, low, high, cell.n, cell.n_units
                )
            )
        summary = Summary(structure.categories, group_values, estimates, True)
        return _prepared(
            summary, structure, layer, source_ids, group_values, curves, undefined
        )
    finally:
        for rank in ranks.values():
            rank.clear()
        ranks.clear()
        cells.clear()
        lookup.clear()


def _cell_type_headers():
    # Derive headers from real product structs, then release the sizing sample.
    sample = _Sample([0], [1], ordered=True)
    sample_header = sys.getsizeof(sample) + sys.getsizeof(sample.__dict__)
    cdf_header = sys.getsizeof(sample.cdf) + sys.getsizeof(sample.cdf.__dict__)
    estimate = _owned_size(Estimate(None, None, 0.0, 0.0, 0.0, 0, None))
    return sample_header, cdf_header, estimate


_SAMPLE_HEADER_BYTES, _CDF_HEADER_BYTES, _ESTIMATE_HEADER_BYTES = _cell_type_headers()


def _ratio_bits(values):
    numerator = denominator = 1
    scalar = 0
    for value in values:
        if isinstance(value, np.generic):
            value = value.item()
        top, bottom = value.as_integer_ratio()
        numerator = max(numerator, abs(top).bit_length())
        denominator = max(denominator, bottom.bit_length())
        scalar = max(scalar, sys.getsizeof(value))
    return numerator, denominator, scalar


def _cell_sample_bound(values, weights, estimator):
    """Canonical storage/construction bound, never a second numerical reducer."""
    count = len(values)
    vn, vd, scalar = _ratio_bits(values)
    wn, wd, _weight_scalar = (
        (1, 1, sys.getsizeof(1)) if weights is None else _ratio_bits(weights)
    )
    value_bits, mass_bits = vn + vd, wn + wd
    product_bits = value_bits + mass_bits
    growth = 2 * max(1, count).bit_length()
    pointer, tuple_header = struct.calcsize("P"), sys.getsizeof(())

    def integer(bits):
        return sys.getsizeof(1 << max(1, bits))

    ordered = estimator == "median"
    # Values/units/masses/products and optional ordered indices, plus int64 caches.
    storage = (
        _SAMPLE_HEADER_BYTES
        + 5 * tuple_header
        + count
        * (
            (5 if ordered else 4) * pointer
            + scalar
            + integer(value_bits)
            + integer(mass_bits)
            + integer(product_bits)
            + (sys.getsizeof(count) if ordered else 0)
            + 2 * np.dtype(np.int64).itemsize
        )
        + integer(vd)
        + integer(wd)
        + integer(mass_bits + growth)
        + integer(product_bits)
        + integer(mass_bits)
    )
    fraction = sys.getsizeof(Fraction()) + integer(max(vn, wn)) + integer(max(vd, wd))
    # canonical_units constructs exact rational input lists, without row expansion.
    construction = 2 * count * (fraction + 2 * pointer)
    if ordered and weights is not None:
        storage += (
            _CDF_HEADER_BYTES
            + 5 * tuple_header
            + count
            * (
                5 * pointer
                + integer(mass_bits)
                + integer(mass_bits + growth)
                + sys.getsizeof(count)
            )
            + integer(wd)
        )
        construction += count * (
            sys.getsizeof((None, None)) + 2 * fraction + 6 * pointer
        )
    double_bits = (
        sys.float_info.max_exp - sys.float_info.min_exp + sys.float_info.mant_dig
    )
    temporary = 8 * integer(
        2 * (product_bits + mass_bits + vd + growth + double_bits) + 4
    )
    return storage + construction + temporary


def _cell_summary(columns, layer, source_ids, value_scale, budget):
    curves = []
    if layer.semantics is not None:
        columns, temporary, curves, rows = semantic_curve_input(columns, layer)
        source_ids = tuple(source_ids[row] for row in rows)
    else:
        temporary = layer
    structure = line_structure(columns, temporary)
    config = stat_config(temporary)
    # The inherited kernel keeps only its current cell's arrays/plan. Reserve
    # its remaining estimates and grouping state, never cache all cell plans.
    pointer = struct.calcsize("P")
    maximum = max((len(rows) for rows in structure.cells.values()), default=0)
    cluster_header = (
        (
            sys.getsizeof({0: None})
            - sys.getsizeof({})
            + sys.getsizeof([0])
            + sys.getsizeof((None, None))
            + sys.getsizeof(np.empty(0, dtype=np.intp))
            + sys.getsizeof(0)
        )
        if config.units is not None
        else 0
    )
    scratch = (
        min(MAX_LINE_CHOICES, max(1, maximum) * config.n_boot)
        * np.dtype(np.int64).itemsize
        + 2 * config.n_boot * np.dtype(float).itemsize
        + (10 * maximum + len(structure.rows)) * pointer
        + maximum * cluster_header
    )
    future = (
        len(structure.cells) * _ESTIMATE_HEADER_BYTES
        + (2 * len(structure.cells) + 16) * pointer
    )
    budget.cell_base = (
        _owned_size((columns, source_ids))
        + 2 * _owned_size(structure)
        + scratch
        + future
    )
    budget.admit_state(budget.cell_base)
    work = _ResamplingWork(new_stat_request(temporary), ledger=budget)
    summary = summarize(columns, temporary, value_scale=value_scale, work=work)
    groups = [hue for _key, hue in structure.groups]
    return _prepared(summary, structure, layer, source_ids, groups, curves, {})


def prepare_line_inference(spec):
    """Every render recharges stored NEW declarations before native creation."""
    known, entries = 0, []
    for pi, panel in enumerate(spec.panels):
        for li, original in enumerate(panel.layers):
            if not explicit_line_inference(original):
                continue
            # Admission counts original physical rows and injective predictor
            # cells. Only the execution pass needs calibrated coordinates.
            columns, layer, source_ids = _input(spec, panel, original, project=False)
            structure = line_structure(columns, layer)
            work = known_line_work(columns, layer, structure=structure)
            known += work
            if known > MAX_LINE_WORK:
                raise ValueError(
                    "known NEW line figure logical work exceeds2000000000 "
                    "before RNG/native; legacy and guide-only views were not charged"
                )
            entries.append((pi, li))
    if entries:
        del columns, layer, source_ids, structure
    budget, prepared = FigureLineBudget(), {}
    for pi, li in entries:
        panel = spec.panels[pi]
        columns, layer, source_ids = _input(
            spec, panel, panel.layers[li], budget=budget
        )
        value_axis = (
            panel.x
            if layer.orient == "h"
            else panel.y2
            if layer.axis == "y2"
            else panel.y
        )
        value_scale = value_axis.scale
        if unit_request(layer):
            structure = line_structure(columns, layer)
            result = _unit_summary(
                columns, layer, structure, source_ids, value_scale, budget
            )
            del structure
        else:
            result = _cell_summary(columns, layer, source_ids, value_scale, budget)
        budget.retain(result)
        prepared[(pi, li)] = result
        del columns, layer, source_ids, result
    return prepared, budget.report()
