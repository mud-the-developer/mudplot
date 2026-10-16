"""NumPy effect: deterministic grouped estimates, separate from the pure core.

The specification stores raw data and named statistical settings. Results
are derived at render time and never inject NaN into saved JSON. Bootstrap
allocation is bounded by chunking; the RNG is private to each computation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from ._stat import INTERVAL_LEVELS, category_levels, stat_config, usable_rows
from .spec import LayerSpec, StatSpec

# Number of resampled elements per chunk, not a limit on dataset length.
_BOOTSTRAP_CHUNK_ELEMENTS = 1_000_000


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


def _aggregate(values: np.ndarray, estimator: str, weights: np.ndarray | None = None):
    """Aggregate the last dimension with scaling to avoid needless overflow."""
    if estimator == "count":
        return np.full(values.shape[:-1], values.shape[-1], dtype=float)
    operations = {
        "mean": np.mean,
        "median": np.median,
        "sum": np.sum,
        "min": np.min,
        "max": np.max,
    }
    if estimator not in operations:
        raise ValueError(f"unknown estimator: {estimator!r}")
    scale = np.max(np.abs(values), axis=-1, keepdims=True)
    scale = np.where(scale == 0, 1.0, scale)
    normalized = values / scale
    with np.errstate(over="ignore", invalid="ignore"):
        if weights is None:
            result = operations[estimator](normalized, axis=-1) * scale[..., 0]
        else:
            if estimator != "mean":
                raise ValueError("weighted estimation requires estimator='mean'")
            weight_scale = np.max(weights, axis=-1, keepdims=True)
            normalized_weights = weights / weight_scale
            result = (
                np.sum(normalized * normalized_weights, axis=-1)
                / np.sum(normalized_weights, axis=-1)
            ) * scale[..., 0]
    if not np.all(np.isfinite(result)):
        raise ValueError("computed estimate is outside the finite plotting range")
    return result


def _quantiles(values: np.ndarray, probabilities) -> tuple[float, float]:
    scale = float(np.max(np.abs(values))) or 1.0
    bounds = np.quantile(values / scale, probabilities, method="linear") * scale
    return float(bounds[0]), float(bounds[1])


def _bootstrap_estimates(values, config, rng, weights=None, units=None):
    estimates = np.empty(config.n_boot)
    if units is None:
        chunk = max(1, _BOOTSTRAP_CHUNK_ELEMENTS // len(values))
        for start in range(0, config.n_boot, chunk):
            stop = min(start + chunk, config.n_boot)
            indices = rng.integers(0, len(values), size=(stop - start, len(values)))
            sampled_weights = None if weights is None else weights[indices]
            estimates[start:stop] = _aggregate(
                values[indices], config.estimator, sampled_weights
            )
    else:
        # Resample independent units, then rows within each selected unit.
        # Unit sizes need not be equal; the observation-weighted point estimate
        # remains unchanged. Values and weights always travel as row pairs.
        unit_rows: dict[Any, list[int]] = {}
        for i, unit in enumerate(units):
            unit_rows.setdefault(unit, []).append(i)
        clusters = [np.asarray(rows) for rows in unit_rows.values()]
        for i in range(config.n_boot):
            selected = rng.integers(0, len(clusters), size=len(clusters))
            indices = np.concatenate(
                [
                    clusters[j][
                        rng.integers(0, len(clusters[j]), size=len(clusters[j]))
                    ]
                    for j in selected
                ]
            )
            sampled_weights = None if weights is None else weights[indices]
            estimates[i] = _aggregate(
                values[indices], config.estimator, sampled_weights
            )
    return estimates


def _interval(
    values: np.ndarray,
    center: float,
    config: StatSpec,
    rng,
    weights: np.ndarray | None = None,
    units=None,
) -> tuple[float | None, float | None]:
    method = config.errorbar
    if method is None or len(values) < 2 or (units is not None and len(set(units)) < 2):
        return None, None
    level = INTERVAL_LEVELS[method] if config.level is None else config.level
    if method in {"sd", "se"}:
        scale = float(np.max(np.abs(values))) or 1.0
        spread = float(np.std(values / scale, ddof=1)) * scale
        if method == "se":
            spread /= float(np.sqrt(len(values)))
        delta = level * spread
        lower, upper = center - delta, center + delta
    else:
        tail = (1.0 - level / 100.0) / 2.0
        if method == "pi":
            lower, upper = _quantiles(values, [tail, 1.0 - tail])
        elif method == "ci":
            estimates = _bootstrap_estimates(values, config, rng, weights, units)
            lower, upper = _quantiles(estimates, [tail, 1.0 - tail])
        else:
            raise ValueError(f"unknown interval method: {method!r}")
    if not np.isfinite(lower) or not np.isfinite(upper):
        raise ValueError("computed interval is outside the finite plotting range")
    return float(lower), float(upper)


def summarize(
    columns: dict, layer: LayerSpec, *, value_scale: str = "linear"
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
    rows = usable_rows(columns, layer)
    categories, groups = category_levels(columns, layer, rows)
    cells: dict[Any, dict[Any, list[int]]] = {group: {} for group in groups}
    for i in rows:
        category = columns[layer.x][i]
        group = columns[layer.group][i] if layer.group is not None else None
        cells[group].setdefault(category, []).append(i)

    positions = {category: i for i, category in enumerate(categories)}
    rng = np.random.default_rng(config.seed)
    estimates = []
    for group, group_cells in cells.items():
        for category in sorted(group_cells, key=positions.__getitem__):
            indices = group_cells[category]
            values = (
                np.ones(len(indices))
                if layer.type == "countplot"
                else np.asarray([columns[layer.y][i] for i in indices], dtype=float)
            )
            weights = (
                None
                if config.weights is None
                else np.asarray(
                    [columns[config.weights][i] for i in indices], dtype=float
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
                and (np.any(~np.isfinite(values)) or np.any(values <= 0))
            ):
                raise ValueError("log-value observations must be positive and finite")
            if axis_log:
                values = np.log10(values)
            center = float(_aggregate(values, config.estimator, weights))
            if layer.type == "countplot" and config.normalize != "count":
                center /= len(rows)
                if config.normalize == "percent":
                    center *= 100
            lower, upper = _interval(values, center, config, rng, weights, units)
            if axis_log:
                coordinates = [center] if lower is None else [center, lower, upper]
                with np.errstate(over="ignore", under="ignore", invalid="ignore"):
                    raw = np.power(10.0, coordinates)
                if np.any(~np.isfinite(raw)) or np.any(raw <= 0):
                    raise ValueError(
                        "inverse log statistics exceed finite positive range"
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
                    center,
                    lower,
                    upper,
                    len(values),
                    None if units is None else len(set(units)),
                )
            )
    return Summary(categories, groups, estimates)
