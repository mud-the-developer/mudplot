"""Dependency-free grouping contracts for box/violin/boxen/swarm distributions.

One-column box/violin builders retain x-as-value/group-as-category semantics. Supplying
both x and y opts into category-by-hue nesting, with x always categorical.
"""

from __future__ import annotations

import math
from dataclasses import fields
from itertools import pairwise
from numbers import Real

from ._ecdf import finite_number
from ._semantics import (
    MAX_LEVELS,
    categorical,
    categorical_fractions,
    category_key,
    numeric_guides,
    numeric_mapping,
    option_issues,
    semantic_levels,
)
from ._stat import is_missing
from .spec import LayerSpec, SemanticSpec

DISTRIBUTION_TYPES = frozenset({"box", "violin", "boxenplot"})
MAX_VIOLIN_POINTS = 1000
MAX_SWARM_POINTS = 2000  # bounded display-space packing per layer
CATEGORY_TYPES = DISTRIBUTION_TYPES | {"swarmplot"}


def native_category_geometry(categories, scale="linear"):
    """Numeric positions/min spacing in axis coordinates; order only selects.

    Includes reserved levels. Dates, strings, booleans and collapsed float/log
    coordinates are rejected, not coerced into ambiguous category positions.
    """
    positions = []
    for value in categories:
        if not isinstance(value, Real) or isinstance(value, bool):
            raise ValueError("native_scale requires numeric finite category levels")
        try:
            number = float(value)
        except (ValueError, OverflowError) as exc:
            raise ValueError("native category levels must be finite") from exc
        if not math.isfinite(number):
            raise ValueError("native category levels must be finite")
        if scale == "log":
            if number <= 0:
                raise ValueError("native log category levels must be positive")
            number = math.log10(number)
        positions.append(number)
    if not positions or len(set(positions)) != len(positions):
        raise ValueError("native category coordinates collapse or are empty")
    ordered = sorted(positions)
    spacing = min((b - a for a, b in pairwise(ordered)), default=1)
    if not math.isfinite(spacing) or spacing <= 0:
        raise ValueError("native category spacing must be positive and finite")
    return positions, spacing


def distribution_columns(layer: LayerSpec) -> tuple[str | None, str, str | None]:
    """Return category, observation and hue column names (None means one level)."""
    if layer.y:
        return layer.x, layer.y, layer.group
    return layer.group, layer.x, None


def distribution_rows(columns: dict, layer: LayerSpec) -> list[int]:
    """Listwise-drop missing rows and apply explicit category/hue selection."""
    category, value, hue = distribution_columns(layer)
    weight = layer.weights if layer.type == "violin" else None
    size = (
        layer.semantics.size
        if layer.type == "swarmplot" and isinstance(layer.semantics, SemanticSpec)
        else None
    )
    selected_sizes = None
    if (
        size is not None
        and isinstance(layer.semantics, SemanticSpec)
        and layer.semantics.size_order is not None
    ):
        order = layer.semantics.size_order
        if not isinstance(order, (list, tuple)) or not all(
            categorical(v) for v in order
        ):
            return []
        selected_sizes = {category_key(v) for v in order}
    names = [name for name in (category, value, hue, weight, size) if name is not None]
    if not all(isinstance(name, str) and name in columns for name in names):
        return []
    if any(
        levels is not None and not isinstance(levels, (list, tuple))
        for levels in (layer.order, layer.hue_order)
    ):
        return []
    if (layer.order is not None and category is None) or (
        layer.hue_order is not None and hue is None
    ):
        return []
    arrays = [columns[name] for name in names]
    if len({len(array) for array in arrays}) != 1:
        return []
    return [
        i
        for i, row in enumerate(zip(*arrays, strict=True))
        if not any(is_missing(v) for v in row)
        and (layer.order is None or columns[category][i] in layer.order)
        and (layer.hue_order is None or columns[hue][i] in layer.hue_order)
        and (
            selected_sizes is None
            or not categorical(columns[size][i])
            or category_key(columns[size][i]) in selected_sizes
        )
        and (
            weight is None
            or not finite_number(columns[weight][i])
            or columns[weight][i] != 0
        )
    ]


def swarm_size_mapping(columns, config, rows, *, domain=None):
    """Map local observations against a selected local or named size domain."""
    values = [columns[config.size][row] for row in rows]
    mapping_columns = columns if domain is None else domain["columns"]
    mapping_rows = rows if domain is None else domain["rows"]
    mapping_values = [mapping_columns[config.size][row] for row in mapping_rows]
    if config.size_kind == "numeric":
        fractions, bounds = numeric_mapping(mapping_values, config.size_norm)
        if domain is not None:
            fractions, _ = numeric_mapping(
                values, bounds if bounds[0] != bounds[1] else None
            )
        guide_values = numeric_guides(bounds)
        guide_fractions, _ = numeric_mapping(
            guide_values, bounds if bounds[0] != bounds[1] else None
        )
        guides = list(zip(guide_values, guide_fractions, strict=True))
    else:
        selected = semantic_levels(mapping_columns, config, "size", mapping_rows)
        fractions = categorical_fractions(values, selected)
        observed = {category_key(value) for value in mapping_values}
        guides = [
            (value, t)
            for value, t in zip(
                selected, categorical_fractions(selected, selected), strict=True
            )
            if category_key(value) in observed
        ]
    low, high = config.sizes
    diameters = [low * (1 - t) + high * t for t in fractions]
    mapped_guides = [(value, low * (1 - t) + high * t) for value, t in guides]
    if any(d > 0 and d * d == 0 for d in [low, high, *diameters]):
        raise ValueError("positive semantic marker area is not representable")
    return diameters, mapped_guides


def swarm_size_issues(columns, layer, panel):
    config = layer.semantics
    if config is None:
        return []
    issues = option_issues(config)
    if issues or not isinstance(config, SemanticSpec):
        return issues
    defaults = SemanticSpec()
    allowed = {
        "size",
        "size_kind",
        "size_order",
        "size_norm",
        "sizes",
        "legend",
        "scale_id",
    }
    for field in fields(config):
        if field.name not in allowed and getattr(config, field.name) != getattr(
            defaults, field.name
        ):
            issues.append(f"swarm semantic {field.name} is not supported")
    if config.size is None:
        issues.append("swarm semantics requires one size column")
    if layer.marker_size is not None:
        issues.append("scalar marker_size is not supported with mapped swarm size")
    if any(d > 0 and d * d == 0 for d in config.sizes):
        issues.append("positive semantic marker area is not representable")
    if issues:
        return issues
    if config.size not in columns:
        return ["swarm size column is missing"]
    rows = distribution_rows(columns, layer)
    if not rows:
        return (
            []
            if panel.filters or panel.dropna
            else ["swarm size mapping has no usable observations"]
        )
    values = [columns[config.size][row] for row in rows]
    if config.size_kind == "numeric":
        if any(not finite_number(value) for value in values):
            return ["swarm sizes must be finite numeric, not bool, after selection"]
    else:
        if not all(categorical(value) for value in values):
            return ["swarm size categories must be nonempty strings or finite scalars"]
        selected = semantic_levels(columns, config, "size", rows)
        if len(selected) > MAX_LEVELS or len({str(value) for value in selected}) != len(
            selected
        ):
            return [f"swarm size levels exceed {MAX_LEVELS}/have ambiguous labels"]
    try:
        swarm_size_mapping(columns, config, rows)
    except (ValueError, OverflowError) as exc:
        issues.append(str(exc))
    return issues


def distribution_levels(columns: dict, layer: LayerSpec, rows: list[int]):
    """Reserve selected levels, including empty category/hue slots."""
    category, _value, hue = distribution_columns(layer)
    categories = (
        [None]
        if category is None
        else list(layer.order)
        if layer.order is not None
        else list(dict.fromkeys(columns[category][i] for i in rows))
    )
    groups = (
        [None]
        if hue is None
        else list(layer.hue_order)
        if layer.hue_order is not None
        else list(dict.fromkeys(columns[hue][i] for i in rows))
    )
    return categories, groups
