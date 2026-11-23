"""NumPy effect: deterministic grouped estimates, separate from the pure core.

The specification stores raw data and named statistical settings. Results
are derived at render time and never inject NaN into saved JSON. Bootstrap
allocation is bounded by chunking; the RNG is private to each computation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

import numpy as np

from ._ecdf import (
    canonical_cdf,
    canonical_type7,
    canonical_units,
    covariance_units,
    finite_mass,
    finite_number,
    sqrt_fraction,
)
from ._stat import (
    INTERVAL_LEVELS,
    MAX_ACTIVE_SAMPLE_ELEMENTS,
    MAX_ADVANCED_STAT_CELLS,
    MAX_ADVANCED_STAT_ROWS,
    MAX_RESAMPLING_WORK,
    category_levels,
    explicit_line_inference,
    new_stat_request,
    stat_config,
    stat_key,
    unit_key,
    usable_rows,
)
from ._transforms import projects
from .spec import LayerSpec, LineSpec, StatSpec


@dataclass(frozen=True)
class Estimate:
    category: Any
    group: Any
    value: float
    lower: float | None
    upper: float | None
    n: int
    n_units: int | None = None


@dataclass(frozen=True)
class Summary:
    categories: list
    groups: list
    estimates: list[Estimate]
    typed: bool = False


def _linear_quantiles(values, probabilities, *, exact=False):
    """Type7 selection through the one shared canonical interpolation boundary."""
    values = np.asarray(values).reshape(-1)
    positions = [
        Fraction(probability) * (len(values) - 1) for probability in probabilities
    ]
    lower = [position.numerator // position.denominator for position in positions]
    upper = [
        index if position == index else index + 1
        for position, index in zip(positions, lower, strict=True)
    ]
    selected = np.unique(lower + upper)
    partitioned = np.partition(values, selected)
    result = []
    for position, low, high in zip(positions, lower, upper, strict=True):
        a, b = partitioned[low], partitioned[high]
        a = a.item() if isinstance(a, np.generic) else a
        b = b.item() if isinstance(b, np.generic) else b
        result.append(canonical_type7((a, b), position - low))
    return np.asarray(result, dtype=object if exact else float)


def _finite_float(value):
    try:
        result = float(value)
    except (ValueError, OverflowError) as error:
        raise ValueError("computed statistic exceeds finite plotting range") from error
    if not math.isfinite(result):
        raise ValueError("computed statistic exceeds finite plotting range")
    return result


class _Sample:
    """A cell's canonical arithmetic/CDF plan, reused by every resampled case."""

    def __init__(self, values, weights=None, *, ordered=False):
        self.values = tuple(
            value.item() if isinstance(value, np.generic) else value for value in values
        )
        self.weighted = weights is not None
        weights = (
            (1,) * len(self.values)
            if weights is None
            else tuple(
                value.item() if isinstance(value, np.generic) else value
                for value in weights
            )
        )
        if not self.values or len(self.values) != len(weights):
            raise ValueError("statistical values and weights require paired rows")
        if any(not finite_number(value) for value in self.values):
            raise ValueError("statistics require finite canonical observations")
        if any(not finite_number(weight) or weight < 0 for weight in weights):
            raise ValueError("statistics require finite nonnegative row weights")
        self.value_denominator, self.units = canonical_units(self.values)
        self.weight_denominator, self.masses = canonical_units(weights)
        self.total = sum(self.masses)
        if self.total <= 0:
            raise ValueError("statistics require positive observation mass")
        self.products = tuple(
            value * mass for value, mass in zip(self.units, self.masses, strict=True)
        )
        self.order = (
            tuple(sorted(range(len(self.values)), key=self.values.__getitem__))
            if ordered
            else ()
        )
        self.cdf = (
            canonical_cdf(self.values, weights) if ordered and self.weighted else None
        )
        self._product_max = max(map(abs, self.products), default=0)
        self._mass_max = max(self.masses, default=0)
        limit = np.iinfo(np.int64).max
        self._small_products = (
            np.asarray(self.products, dtype=np.int64)
            if self._product_max <= limit
            else None
        )
        self._small_masses = (
            np.asarray(self.masses, dtype=np.int64) if self._mass_max <= limit else None
        )

    def _sum(self, values, counts, small, maximum):
        if counts is None:
            return sum(values)
        size = int(np.sum(counts))
        if small is not None and maximum * size <= np.iinfo(np.int64).max:
            return int(np.dot(small, counts))
        return sum(
            value * int(count) for value, count in zip(values, counts, strict=True)
        )

    def estimate(self, estimator, counts=None, *, exact=False):
        total = self._sum(self.masses, counts, self._small_masses, self._mass_max)
        if total <= 0:
            raise ValueError("sampled statistics require positive observation mass")
        if estimator == "count":
            result = Fraction(total, self.weight_denominator)
            return result if exact else _finite_float(result)
        if estimator in ("mean", "sum"):
            numerator = self._sum(
                self.products, counts, self._small_products, self._product_max
            )
            denominator = self.value_denominator * (
                total if estimator == "mean" else self.weight_denominator
            )
            result = Fraction(numerator, denominator)
            return result if exact else _finite_float(result)
        if estimator in ("min", "max"):
            selected = (
                self.values[index]
                for index in range(len(self.values))
                if self.masses[index] and (counts is None or counts[index])
            )
            result = (min if estimator == "min" else max)(selected)
            return Fraction(result) if exact else result
        if estimator != "median":
            raise ValueError(f"unknown estimator: {estimator!r}")
        if self.weighted:
            assert self.cdf is not None
            result = self.cdf.left(Fraction(1, 2), counts)
            return Fraction(result) if exact else result
        if counts is None:
            result = canonical_type7(
                [self.values[index] for index in self.order], Fraction(1, 2)
            )
            return result if exact else _finite_float(result)
        size = int(np.sum(counts))
        ranks = ((size - 1) // 2, size // 2)
        endpoints, cumulative = [], 0
        for index in self.order:
            previous = cumulative
            cumulative += int(counts[index])
            for rank in ranks[len(endpoints) :]:
                if previous <= rank < cumulative:
                    endpoints.append(self.values[index])
                else:
                    break
            if len(endpoints) == 2:
                break
        result = (Fraction(endpoints[0]) + Fraction(endpoints[1])) / 2
        return result if exact else _finite_float(result)

    def variance(self):
        # Same exact physical-row reliability equation as multivariate kernels.
        return covariance_units(
            self.units,
            self.units,
            self.masses,
            self.value_denominator,
            self.value_denominator,
            products_x=self.products,
        )


def _aggregate(values: np.ndarray, estimator: str, weights: np.ndarray | None = None):
    """Reduce canonical values before binary64 conversion, without MaxAbs erasure."""
    values = np.asarray(values)
    if values.ndim == 1:
        return _Sample(values, weights, ordered=estimator == "median").estimate(
            estimator
        )
    weights = None if weights is None else np.asarray(weights)
    return np.asarray(
        [
            _Sample(
                row,
                None if weights is None else weights[index],
                ordered=estimator == "median",
            ).estimate(estimator)
            for index, row in enumerate(values)
        ]
    )


def _count_mass(weights, denominator, factor):
    """Round once at extreme ranges; never erase mass by scaling each row."""
    if isinstance(denominator, Fraction):
        mass = sum((Fraction(float(w)) for w in weights), Fraction())
        return float(mass * factor / denominator)
    mass = finite_mass(weights, context="weighted count")
    ratio = mass / denominator
    if ratio < np.finfo(float).tiny:
        return float(Fraction(mass) * factor / Fraction(denominator))
    return ratio * factor


def _quantiles(values: np.ndarray, probabilities) -> tuple[float, float]:
    bounds = _linear_quantiles(values, probabilities)
    return float(bounds[0]), float(bounds[1])


class _ResamplingWork:
    def __init__(self, enabled=False, *, ledger=None):
        self.enabled = enabled
        self.used = 0
        self.ledger = ledger

    def admit(self, count):
        count = int(count)
        if self.enabled and self.used + count > MAX_RESAMPLING_WORK:
            raise ValueError(
                "requested NEW inference exceeds actual resampling work "
                f"{MAX_RESAMPLING_WORK}; no partial interval was produced"
            )
        if self.ledger is not None:
            self.ledger.admit_cell(count, 0)
        self.used += count


def _bootstrap_estimates(
    values,
    config,
    rng,
    weights=None,
    units=None,
    *,
    work=None,
    advanced=False,
    sample=None,
    typed_units=None,
):
    """Uniform paired-case schedule, with bounded counts rather than replicated data."""
    unit_identity = advanced if typed_units is None else typed_units
    sample = (
        _Sample(values, weights, ordered=config.estimator == "median")
        if sample is None
        else sample
    )
    estimates = np.empty(config.n_boot)
    work = _ResamplingWork() if work is None else work
    ledger = getattr(work, "ledger", None)
    if ledger is not None:
        ledger.admit_cell(0, config.n_boot)
    size = len(values)
    if units is None:
        if size <= MAX_ACTIVE_SAMPLE_ELEMENTS:
            chunk = max(1, MAX_ACTIVE_SAMPLE_ELEMENTS // size)
            for start in range(0, config.n_boot, chunk):
                stop = min(start + chunk, config.n_boot)
                work.admit((stop - start) * size)
                indices = rng.integers(0, size, size=(stop - start, size))
                for offset, row in enumerate(indices):
                    counts = np.bincount(row, minlength=size)
                    estimates[start + offset] = sample.estimate(
                        config.estimator, counts
                    )
        else:
            # Legacy datasets retain admission; a single resample may span chunks.
            for replicate in range(config.n_boot):
                work.admit(size)
                counts = np.zeros(size, dtype=np.int64)
                for start in range(0, size, MAX_ACTIVE_SAMPLE_ELEMENTS):
                    draw = rng.integers(
                        0, size, size=min(MAX_ACTIVE_SAMPLE_ELEMENTS, size - start)
                    )
                    counts += np.bincount(draw, minlength=size)
                estimates[replicate] = sample.estimate(config.estimator, counts)
    else:
        unit_rows = {}
        for index, unit in enumerate(units):
            unit_rows.setdefault(unit_key(unit, unit_identity), []).append(index)
        clusters = [np.asarray(rows, dtype=np.intp) for rows in unit_rows.values()]
        lengths = np.asarray([len(rows) for rows in clusters], dtype=np.intp)
        singleton_units = np.flatnonzero(lengths == 1)
        singleton_rows = np.asarray(
            [clusters[index][0] for index in singleton_units], dtype=np.intp
        )
        for replicate in range(config.n_boot):
            work.admit(len(clusters))
            if len(clusters) <= MAX_ACTIVE_SAMPLE_ELEMENTS:
                chosen = rng.integers(0, len(clusters), size=len(clusters))
            else:
                chosen = np.empty(len(clusters), dtype=np.intp)
                for start in range(0, len(clusters), MAX_ACTIVE_SAMPLE_ELEMENTS):
                    stop = min(start + MAX_ACTIVE_SAMPLE_ELEMENTS, len(clusters))
                    chosen[start:stop] = rng.integers(
                        0, len(clusters), size=stop - start
                    )
            multiplicity = np.bincount(chosen, minlength=len(clusters))
            work.admit(
                sum(
                    int(count) * len(rows)
                    for count, rows in zip(multiplicity, clusters, strict=True)
                )
            )
            counts = np.zeros(size, dtype=np.int64)
            counts[singleton_rows] = multiplicity[singleton_units]
            # high1 singleton draws consume no entropy. Every nontrivial range
            # stays in original chosen-unit order, including mixed-size ranges.
            selected = chosen[lengths[chosen] > 1]
            first = 0
            while first < len(selected):
                length = int(lengths[selected[first]])
                last = first + 1
                while last < len(selected) and lengths[selected[last]] == length:
                    last += 1
                if length > MAX_ACTIVE_SAMPLE_ELEMENTS:
                    for unit in selected[first:last]:
                        for start in range(0, length, MAX_ACTIVE_SAMPLE_ELEMENTS):
                            draw = rng.integers(
                                0,
                                length,
                                size=min(MAX_ACTIVE_SAMPLE_ELEMENTS, length - start),
                            )
                            original = clusters[unit][draw]
                            counts += np.bincount(original, minlength=size)
                    first = last
                    continue
                width = max(1, MAX_ACTIVE_SAMPLE_ELEMENTS // length)
                for offset in range(first, last, width):
                    part = selected[offset : min(offset + width, last)]
                    mapping = np.asarray(
                        [clusters[index] for index in part], dtype=np.intp
                    )
                    draw = rng.integers(0, length, size=(len(part), length))
                    original = np.take_along_axis(mapping, draw, axis=1)
                    counts += np.bincount(original.ravel(), minlength=size)
                first = last
            estimates[replicate] = sample.estimate(config.estimator, counts)
    return estimates


def _interval(
    values: np.ndarray,
    config: StatSpec,
    rng,
    weights: np.ndarray | None = None,
    units=None,
    *,
    work=None,
    advanced=False,
    sample=None,
    typed_units=None,
) -> tuple[float | None, float | None]:
    method = config.errorbar
    unit_identity = advanced if typed_units is None else typed_units
    if (
        method is None
        or len(values) < 2
        or (
            units is not None
            and len({unit_key(unit, unit_identity) for unit in units}) < 2
        )
    ):
        return None, None
    if sample is None:
        sample = _Sample(
            values,
            weights,
            ordered=config.estimator == "median"
            or (weights is not None and method == "pi"),
        )
    level = INTERVAL_LEVELS[method] if config.level is None else config.level
    if method in {"sd", "se"}:
        moments = sample.variance()
        if moments is None:
            return None, None
        variance, effective = moments
        spread = sqrt_fraction(variance if method == "sd" else variance / effective)
        if variance > 0 and spread == 0:
            raise ValueError(
                "requested positive spread is not representable in native coordinates"
            )
        delta = Fraction(level) * Fraction(spread)
        canonical_center = sample.estimate(config.estimator, exact=True)
        lower, upper = canonical_center - delta, canonical_center + delta
    else:
        tail = (1.0 - level / 100.0) / 2.0
        if method == "pi":
            if weights is None:
                lower, upper = _linear_quantiles(values, [tail, 1.0 - tail], exact=True)
            else:
                probability = (100 - Fraction(level)) / 200
                cdf = sample.cdf
                assert cdf is not None
                lower, upper = cdf.left(probability), cdf.left(1 - probability)
        elif method == "ci":
            estimates = _bootstrap_estimates(
                values,
                config,
                rng,
                weights,
                units,
                work=work,
                advanced=advanced,
                sample=sample,
                typed_units=typed_units,
            )
            lower, upper = _quantiles(estimates, [tail, 1.0 - tail])
        else:
            raise ValueError(f"unknown interval method: {method!r}")
    native_lower, native_upper = _finite_float(lower), _finite_float(upper)
    if lower < upper and native_lower >= native_upper:
        raise ValueError(
            "requested strict interval span collapses in native coordinates"
        )
    return native_lower, native_upper


def summarize(
    columns: dict,
    layer: LayerSpec,
    *,
    value_scale: str = "linear",
    advanced=None,
    work=None,
    hue_pools=None,
) -> Summary:
    """Group usable rows; explicit axis/log estimates inverse-map to raw units.

    Weights/units stay paired to original selected rows. Linear/default calls
    retain previous results and RNG order. Log sum/count are not multiplicative
    estimates and are explicitly outside this subset.
    """
    if value_scale not in ("linear", "log"):
        raise ValueError("value_scale must be linear or log")
    config = stat_config(layer)
    axis_log = layer.stat_scale == "axis" and value_scale == "log"
    if axis_log and config.estimator not in {"mean", "median", "min", "max"}:
        raise ValueError(
            "axis log estimation supports mean/median/min/max, not sum/count"
        )
    advanced = new_stat_request(layer) if advanced is None else advanced
    bounded = advanced or (layer.type != "countplot" and projects(layer))
    rows = usable_rows(columns, layer, advanced=advanced)
    if bounded and len(rows) > MAX_ADVANCED_STAT_ROWS:
        raise ValueError("NEW statistical selected rows exceed10000")
    categories, groups = category_levels(columns, layer, rows, advanced=advanced)
    count_normalizers = {}
    if layer.type == "countplot" and config.normalize != "count":
        partition_column = (
            layer.x
            if config.normalize_scope == "category"
            else layer.group
            if config.normalize_scope == "group"
            else None
        )
        pools: dict[object, list[int]] = (
            {None: rows} if partition_column is None else {}
        )
        if partition_column is not None:
            for i in rows:
                key = columns[partition_column][i]
                if hue_pools is not None:
                    key = (
                        hue_pools[key]
                        if config.normalize_scope == "group"
                        else stat_key(key)
                    )
                pools.setdefault(key, []).append(i)
        for key, pool in pools.items():
            if not pool:
                continue
            total = float(len(pool))
            if config.weights is not None:
                pool_weights = np.asarray(
                    [columns[config.weights][i] for i in pool], dtype=float
                )
                try:
                    total = finite_mass(pool_weights, context="weighted count")
                except ValueError:
                    total = sum((Fraction(float(w)) for w in pool_weights), Fraction())
            count_normalizers[key] = total
    typed = (
        advanced
        or explicit_line_inference(layer)
        or (
            layer.type == "lineplot"
            and isinstance(layer.line, LineSpec)
            and layer.line.predictor == "categorical"
        )
    )
    typed_units = True if explicit_line_inference(layer) else None
    identity = stat_key if typed else lambda value: value
    raw_categories = {identity(category): category for category in categories}
    raw_groups = {identity(group): group for group in groups}
    cells: dict[Any, dict[Any, list[int]]] = {identity(group): {} for group in groups}
    for i in rows:
        category = identity(columns[layer.x][i])
        group = identity(columns[layer.group][i] if layer.group is not None else None)
        cells[group].setdefault(category, []).append(i)
    if (
        bounded
        and sum(len(group) for group in cells.values()) > MAX_ADVANCED_STAT_CELLS
    ):
        raise ValueError("NEW drawn pointwise statistical cells exceed256")

    positions = {identity(category): i for i, category in enumerate(categories)}
    rng = np.random.default_rng(config.seed)
    work = _ResamplingWork(bounded) if work is None else work
    ledger = getattr(work, "ledger", None)
    estimates = []
    for group_key, group_cells in cells.items():
        group = raw_groups[group_key]
        for category_key in sorted(group_cells, key=positions.__getitem__):
            category = raw_categories[category_key]
            indices = group_cells[category_key]
            values = (
                np.ones(len(indices))
                if layer.type == "countplot"
                else np.asarray([columns[layer.y][i] for i in indices], dtype=object)
            )
            weights = (
                None
                if config.weights is None
                else np.asarray(
                    [columns[config.weights][i] for i in indices], dtype=object
                )
            )
            units = (
                None
                if config.units is None
                else [columns[config.units][i] for i in indices]
            )
            if (
                value_scale == "log"
                and config.estimator != "count"
                and any(not finite_number(value) or value <= 0 for value in values)
            ):
                raise ValueError("log-value observations must be positive and finite")
            if axis_log:
                values = np.log10(np.asarray(values, dtype=float))
            count_denominator = 1.0
            normalized_count = layer.type == "countplot" and config.normalize != "count"
            if normalized_count:
                key = (
                    category
                    if config.normalize_scope == "category"
                    else group
                    if config.normalize_scope == "group"
                    else None
                )
                if hue_pools is not None:
                    if config.normalize_scope == "group":
                        key = hue_pools[key]
                    elif config.normalize_scope == "category":
                        key = stat_key(key)
                count_denominator = count_normalizers[key]
            sample = None
            if layer.type == "countplot" and weights is not None:
                center = _count_mass(
                    weights,
                    count_denominator,
                    100 if config.normalize == "percent" else 1,
                )
            else:
                if ledger is not None:
                    ledger.admit_cell_input(values, weights, config.estimator)
                sample = _Sample(
                    values,
                    weights,
                    ordered=config.estimator == "median"
                    or (weights is not None and config.errorbar == "pi"),
                )
                if ledger is not None:
                    ledger.admit_cell_plan(sample)
                center = sample.estimate(config.estimator)
                if normalized_count:
                    center /= count_denominator
                    if config.normalize == "percent":
                        center *= 100
            lower, upper = _interval(
                values,
                config,
                rng,
                weights,
                units,
                work=work,
                advanced=advanced,
                sample=sample,
                typed_units=typed_units,
            )
            if axis_log:
                log_center = float(center)
                if lower is None:
                    assert upper is None
                    coordinates = [log_center]
                else:
                    assert upper is not None
                    coordinates = [log_center, lower, upper]
                with np.errstate(over="ignore", under="ignore", invalid="ignore"):
                    raw = np.power(10.0, coordinates)
                if np.any(~np.isfinite(raw)) or np.any(raw <= 0):
                    raise ValueError(
                        "inverse log statistics exceed finite positive range"
                    )
                if (
                    lower is not None
                    and upper is not None
                    and lower < upper
                    and raw[1] >= raw[2]
                ):
                    raise ValueError(
                        "positive working interval collapses after inverse log mapping"
                    )
                center = float(raw[0])
                if lower is not None:
                    lower, upper = float(raw[1]), float(raw[2])
            if value_scale == "log" and any(
                bound is not None and bound <= 0 for bound in (center, lower, upper)
            ):
                raise ValueError(
                    "log-value estimate/interval endpoints must be positive; "
                    "use axis statistics or another interval"
                )
            estimates.append(
                Estimate(
                    category,
                    group,
                    float(center),
                    lower,
                    upper,
                    len(values),
                    None
                    if units is None
                    else len(
                        {
                            unit_key(
                                unit, advanced if typed_units is None else typed_units
                            )
                            for unit in units
                        }
                    ),
                )
            )
    return Summary(categories, groups, estimates, typed)
