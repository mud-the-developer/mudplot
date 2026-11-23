"""Dependency-free statistical contracts shared by builders and validation."""

from __future__ import annotations

import math
from dataclasses import replace
from numbers import Real

from .spec import LayerSpec, LineSpec, StatSpec

STAT_LAYER_TYPES = frozenset({"barplot", "pointplot", "countplot", "lineplot"})
ESTIMATORS = ("mean", "median", "sum", "min", "max", "count")
INTERVAL_METHODS = ("sd", "se", "pi", "ci")
INTERVAL_LEVELS = {"sd": 1.0, "se": 1.0, "pi": 95.0, "ci": 95.0}
MAX_BOOTSTRAPS = 100_000
COUNT_STATS = ("count", "probability", "proportion", "percent")
COUNT_SCOPES = ("all", "category", "group")
LABEL_FORMATS = ("g", ".0f", ".1f", ".2f", ".3f", ".1%", "e", ".2e")

MAX_ADVANCED_STAT_ROWS = 10000
MAX_ADVANCED_STAT_CELLS = 256
MAX_RESAMPLING_WORK = 2_000_000_000
MAX_ACTIVE_SAMPLE_ELEMENTS = 1_000_000


def new_stat_request(layer, panel=None) -> bool:
    """Persisted NEW combinations only; old weighted/unit/line routes stay old."""
    if layer.type not in {"barplot", "pointplot", "lineplot"}:
        return False
    config = stat_config(layer)
    if (
        layer.type == "lineplot"
        and isinstance(layer.line, LineSpec)
        and layer.line.resampling == "unit"
    ):
        return False  # D01 has its own trajectory/target/work admission.
    if config.weights is not None and not (
        config.estimator == "mean" and config.errorbar in (None, "ci")
    ):
        return True
    if layer.type == "lineplot":
        return False
    if layer.semantics is not None:
        return True
    if panel is None or layer.axis != "y2":
        return False
    if layer.orient == "h":
        return True
    category = panel.x
    value = panel.y2
    if value is None:
        return False
    old_temporal = (
        (category.temporal is not None or value.temporal is not None)
        and layer.stat_scale == "data"
        and category.scale == value.scale == "linear"
    )
    return not old_temporal and (
        layer.native_scale
        or layer.stat_scale == "axis"
        or category.scale == "log"
        or value.scale == "log"
    )


def make_stat(
    estimator: str,
    errorbar: str | tuple[str, float] | None,
    n_boot: int,
    seed: int,
    *,
    weights: str | None = None,
    units: str | None = None,
    normalize: str = "count",
    normalize_scope: str | None = None,
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
        normalize_scope=normalize_scope,
    )


def stat_config(layer: LayerSpec) -> StatSpec:
    if layer.stat is not None:
        return layer.stat
    if layer.type == "countplot":
        return StatSpec(estimator="count", errorbar=None)
    return StatSpec()


def explicit_line_inference(layer: LayerSpec) -> bool:
    return (
        layer.type == "lineplot"
        and isinstance(layer.line, LineSpec)
        and any(
            value is not None
            for value in (
                layer.line.resampling,
                layer.line.calibration,
                layer.line.family,
            )
        )
        and isinstance(stat_config(layer), StatSpec)
        and stat_config(layer).errorbar == "ci"
    )


def is_missing(value) -> bool:
    if value is None:
        return True
    if isinstance(value, Real) and not isinstance(value, bool):
        try:
            return math.isnan(value)
        except OverflowError:
            return False
    return False


def usable_rows(
    columns: dict,
    layer: LayerSpec,
    *,
    advanced=None,
    limit: int | None = MAX_ADVANCED_STAT_ROWS,
    category_matches=None,
) -> list[int]:
    """Drop only missing required observations; validation checks bad types."""
    advanced = new_stat_request(layer) if advanced is None else advanced
    if (
        layer.type == "lineplot"
        and isinstance(layer.line, LineSpec)
        and (explicit_line_inference(layer) or layer.line.predictor == "categorical")
    ):
        from ._line import line_rows

        return line_rows(columns, layer)
    if layer.type == "countplot" and layer.semantics is not None:
        from ._body_semantics import body_rows

        return body_rows(columns, layer, category_matches=category_matches)
    if advanced and layer.type == "countplot":
        from ._categorical import sample_rows

        return sample_rows(
            columns, replace(layer, y=layer.x), weight_column=stat_config(layer).weights
        )
    if advanced:
        from ._categorical import sample_rows

        config = stat_config(layer)
        return sample_rows(
            columns,
            layer,
            required=tuple(
                name for name in (config.weights, config.units) if name is not None
            ),
            weight_column=config.weights,
            limit=limit,
            category_matches=category_matches,
        )
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
        and (
            category_matches(columns[layer.x][i])
            if category_matches is not None
            else layer.order is None or columns[layer.x][i] in layer.order
        )
        and (layer.hue_order is None or columns[layer.group][i] in layer.hue_order)
    ]
    if layer.type == "lineplot" and layer.semantics is not None:
        from ._semantics import semantic_rows

        selected = set(semantic_rows(columns, layer))
        rows = [i for i in rows if i in selected]
    return rows


def category_levels(
    columns: dict, layer: LayerSpec, rows: list[int], *, advanced=None
) -> tuple[list, list]:
    """Reserve explicit level slots, even when a selected level has no rows."""
    advanced = new_stat_request(layer) if advanced is None else advanced
    if (
        advanced
        or explicit_line_inference(layer)
        or (
            layer.type == "lineplot"
            and isinstance(layer.line, LineSpec)
            and layer.line.predictor == "categorical"
        )
    ):
        from ._semantics import levels

        categories = (
            list(layer.order)
            if layer.order is not None
            else levels(columns[layer.x][index] for index in rows)
        )
        groups = (
            [None]
            if layer.group is None
            else (
                list(layer.hue_order)
                if layer.hue_order is not None
                else levels(columns[layer.group][index] for index in rows)
            )
        )
        return categories, groups
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


def stat_key(value):
    """Typed scalar identity, with one explicit ungrouped sentinel."""
    if value is None:
        return ("ungrouped",)
    from ._semantics import category_key

    return category_key(value)


def unit_key(value, typed):
    if typed:
        from ._semantics import category_key

        if isinstance(value, str):
            return "str", value

        return category_key(value)
    return value


def stat_semantic_issues(columns, layer, panel):
    """Bar/point role ownership; scientific data/cohort checks stay shared."""
    from ._semantics import (
        MAX_LEVELS,
        categorical,
        finite_number,
        option_issues,
        semantic_levels,
    )
    from .spec import SemanticSpec

    config = layer.semantics
    issues = option_issues(config)
    if issues or not isinstance(config, SemanticSpec):
        return issues
    if layer.group is not None and config.hue is not None:
        issues.append("independent semantic hue conflicts with legacy group")
    if layer.c is not None:
        issues.append("statistical roles do not accept legacy c")
    if config.hue is not None and layer.color is not None:
        issues.append("color cannot override mapped hue")
    if config.size is not None and (
        layer.line_width is not None
        if layer.type in {"barplot", "hist", "countplot"}
        else layer.marker_size is not None
    ):
        issues.append("scalar main size cannot override a mapped size")
    if config.style is not None and (
        layer.line_style is not None
        or (layer.type == "pointplot" and layer.marker is not None)
    ):
        issues.append("scalar style cannot override mapped style")
    if layer.hue_order is not None and config.hue is not None:
        issues.append("semantic hue_order and legacy hue_order cannot be combined")
    if layer.references is not None and config.hue is not None:
        issues.append(
            "independent semantic hue does not accept legacy group references"
        )
    numeric_hue = config.hue is not None and config.hue_kind == "numeric"
    if type(layer.colorbar) is not bool:
        issues.append("statistical colorbar must be boolean")
    if (layer.colorbar or layer.clabel is not None) and not numeric_hue:
        issues.append("statistical colorbar/clabel requires numeric semantic hue")
    if layer.clabel is not None and (
        not layer.colorbar
        or not isinstance(layer.clabel, str)
        or len(layer.clabel) > 512
    ):
        issues.append("clabel requires a colorbar and bounded text")
    if layer.cmap_kind not in ("sequential", "diverging") or (
        not numeric_hue and layer.cmap_kind != "sequential"
    ):
        issues.append("statistical cmap_kind requires a matching numeric hue")
    if (layer.citation is not None or layer.href is not None) and not layer.label:
        issues.append("semantic layer reference requires an explicit label")
    if layer.type in {"hist", "countplot"}:
        from ._body_semantics import body_plan
        from ._semantics import semantic_rows

        rows = semantic_rows(columns, layer)
        if layer.type == "hist":
            histogram = layer.histogram
            if histogram is None:
                issues.append("semantic histogram requires HistogramSpec")
            elif (
                not (
                    histogram.element == "bars"
                    if histogram.fill is None
                    else histogram.fill
                )
                and config.hue is not None
                and layer.edge_color is not None
            ):
                issues.append(
                    "edge_color cannot override mapped unfilled histogram hue"
                )
        if len(rows) > MAX_ADVANCED_STAT_ROWS:
            issues.append("semantic body exceeds 10000 selected rows")
        try:
            body_plan(columns, layer, rows)
        except ValueError as error:
            issues.append(str(error))
    else:
        rows = usable_rows(columns, layer, advanced=True)
    for role in ("hue", "size", "style"):
        name = getattr(config, role)
        if name is None:
            continue
        if not isinstance(name, str) or name not in columns:
            issues.append(f"semantic column {name!r} must exist")
            continue
        kind = "categorical" if role == "style" else getattr(config, role + "_kind")
        values = [columns[name][index] for index in rows]
        if kind == "numeric":
            if any(not finite_number(value) for value in values):
                issues.append(f"numeric {role} needs finite numbers, not bool")
        elif any(not categorical(value) for value in values):
            issues.append(f"categorical {role} needs declared scalar levels")
        else:
            levels = semantic_levels(columns, config, role, rows)
            if len(levels) > MAX_LEVELS or len({str(value) for value in levels}) != len(
                levels
            ):
                issues.append(
                    f"categorical {role} exceeds64 levels or has ambiguous labels"
                )
            if role == "style":
                if len(levels) > len(config.dashes or ("-", "--", "-.", ":")):
                    issues.append("style needs enough distinct named dash patterns")
                if layer.type == "pointplot" and len(levels) > len(config.markers):
                    issues.append("point style needs enough distinct real markers")
    return issues
