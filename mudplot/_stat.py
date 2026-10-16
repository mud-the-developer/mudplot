"""Dependency-free statistical contracts shared by builders and validation."""

from __future__ import annotations

import math
from numbers import Real

from .spec import LayerSpec, StatSpec

STAT_LAYER_TYPES = frozenset({"barplot", "pointplot", "countplot", "lineplot"})
ESTIMATORS = ("mean", "median", "sum", "min", "max", "count")
INTERVAL_METHODS = ("sd", "se", "pi", "ci")
INTERVAL_LEVELS = {"sd": 1.0, "se": 1.0, "pi": 95.0, "ci": 95.0}
MAX_BOOTSTRAPS = 100_000
COUNT_STATS = ("count", "probability", "proportion", "percent")
LABEL_FORMATS = ("g", ".0f", ".1f", ".2f", ".3f", ".1%", "e", ".2e")


def make_stat(
    estimator: str,
    errorbar: str | tuple[str, float] | None,
    n_boot: int,
    seed: int,
    *,
    weights: str | None = None,
    units: str | None = None,
    normalize: str = "count",
) -> StatSpec:
    """Parse an ergonomic interval choice into plain, serializable settings."""
    if errorbar is None or isinstance(errorbar, str):
        method, level = errorbar, None
    elif isinstance(errorbar, (list, tuple)) and len(errorbar) == 2:
        method, level = errorbar
    else:
        raise ValueError("errorbar must be None, a method name, or (method, level)")
    return StatSpec(
        estimator=estimator,
        errorbar=method,
        level=level,
        n_boot=n_boot,
        seed=seed,
        weights=weights,
        units=units,
        normalize=normalize,
    )


def stat_config(layer: LayerSpec) -> StatSpec:
    if layer.stat is not None:
        return layer.stat
    if layer.type == "countplot":
        return StatSpec(estimator="count", errorbar=None)
    return StatSpec()


def is_missing(value) -> bool:
    if value is None:
        return True
    if isinstance(value, Real) and not isinstance(value, bool):
        try:
            return math.isnan(value)
        except OverflowError:
            return False
    return False


def usable_rows(columns: dict, layer: LayerSpec) -> list[int]:
    """Drop only missing required observations; validation checks bad types."""
    for levels in (layer.order, layer.hue_order):
        if levels is not None and not isinstance(levels, (list, tuple)):
            return []
    if layer.hue_order is not None and layer.group is None:
        return []
    names = [layer.x]
    if layer.type != "countplot":
        names.append(layer.y)
    if layer.group is not None:
        names.append(layer.group)
    config = stat_config(layer)
    for name in (config.weights, config.units):
        if name is not None:
            names.append(name)
    if not all(isinstance(name, str) and name in columns for name in names):
        return []
    values = [columns[name] for name in names]
    if len({len(column) for column in values}) != 1:
        return []
    rows = [
        i
        for i, row in enumerate(zip(*values, strict=True))
        if not any(is_missing(value) for value in row)
        and (config.weights is None or columns[config.weights][i] != 0)
        and (layer.order is None or columns[layer.x][i] in layer.order)
        and (layer.hue_order is None or columns[layer.group][i] in layer.hue_order)
    ]
    if layer.type == "lineplot" and layer.semantics is not None:
        from ._semantics import semantic_rows

        selected = set(semantic_rows(columns, layer))
        rows = [i for i in rows if i in selected]
    return rows


def category_levels(
    columns: dict, layer: LayerSpec, rows: list[int]
) -> tuple[list, list]:
    """Reserve explicit level slots, even when a selected level has no rows."""
    categories = (
        list(layer.order)
        if layer.order is not None
        else list(dict.fromkeys(columns[layer.x][i] for i in rows))
    )
    groups = (
        [None]
        if layer.group is None
        else list(layer.hue_order)
        if layer.hue_order is not None
        else list(dict.fromkeys(columns[layer.group][i] for i in rows))
    )
    return categories, groups
