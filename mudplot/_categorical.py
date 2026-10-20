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
from ._semantics import numeric_mapping, option_issues
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
            weight is None
            or not finite_number(columns[weight][i])
            or columns[weight][i] != 0
        )
    ]


def swarm_size_mapping(columns, layer, rows):
    """One selected layer domain; sizes are diameters, never observed counts."""
    config = layer.semantics
    fractions, bounds = numeric_mapping(
        [columns[config.size][row] for row in rows], config.size_norm
    )
    low, high = config.sizes
    diameters = [low * (1 - t) + high * t for t in fractions]
    if any(d > 0 and d * d == 0 for d in [low, high, *diameters]):
        raise ValueError("positive semantic marker area is not representable")
    return diameters, bounds


def swarm_size_issues(columns, layer, panel):
    config = layer.semantics
    if config is None:
        return []
    issues = option_issues(config)
    if issues or not isinstance(config, SemanticSpec):
        return issues
    defaults = SemanticSpec()
    allowed = {"size", "size_kind", "size_norm", "sizes", "legend"}
    for field in fields(config):
        if field.name not in allowed and getattr(config, field.name) != getattr(
            defaults, field.name
        ):
            issues.append(f"swarm semantic {field.name} is not supported")
    if config.size is None or config.size_kind != "numeric":
        issues.append("swarm semantics supports one numeric size column only")
    if layer.marker_size is not None:
        issues.append("scalar marker_size is not supported with mapped swarm size")
    if panel.filters or panel.dropna:
        issues.append("swarm size facet/dropna mappings are not supported")
    if issues:
        return issues
    if config.size not in columns:
        return ["swarm size column is missing"]
    rows = distribution_rows(columns, layer)
    if not rows:
        return ["swarm size mapping has no usable observations"]
    if any(not finite_number(columns[config.size][row]) for row in rows):
        return ["swarm sizes must be finite numeric, not bool, after selection"]
    try:
        swarm_size_mapping(columns, layer, rows)
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
