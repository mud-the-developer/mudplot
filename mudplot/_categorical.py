"""Dependency-free grouping contracts for box/violin/boxen/swarm distributions.

One-column box/violin builders retain x-as-value/group-as-category semantics. Supplying
both x and y opts into category-by-hue nesting, with x always categorical.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from itertools import pairwise
from numbers import Real
from typing import TypedDict

from ._ecdf import finite_number
from ._semantics import (
    categorical,
    categorical_fractions,
    category_key,
    levels,
    numeric_guides,
    numeric_mapping,
    semantic_levels,
)
from ._stat import is_missing
from ._transforms import COLUMN_ARRAYS
from .spec import LayerSpec, SemanticSpec

DISTRIBUTION_TYPES = frozenset({"box", "violin", "boxenplot"})
MAX_VIOLIN_POINTS = 1000
MAX_SWARM_POINTS = 2000  # bounded display-space packing per layer
CATEGORY_TYPES = DISTRIBUTION_TYPES | {"swarmplot"}


def category_axis_mode(layer):
    """Existing statistical/distribution category-role convention, shared by QA."""
    from ._line import categorical_predictor
    from ._stat import STAT_LAYER_TYPES
    from ._strip import categorical_strip

    if layer.type in {"line", "lineplot"} and categorical_predictor(layer):
        return ("y" if layer.orient == "h" else "x"), "ordinal"
    if layer.type in CATEGORY_TYPES | STAT_LAYER_TYPES or categorical_strip(layer):
        name = "y" if layer.orient == "h" else "x"
        mode = (
            "native"
            if layer.type == "lineplot"
            or (type(layer.native_scale) is bool and layer.native_scale)
            else "ordinal"
        )
        return name, mode
    return None


def raw_x_is_categorical(values):
    """Match the scalar-column float conversion preceding _x_values fallback."""
    try:
        for value in values:
            if value is not None:
                float(value)
    except (ValueError, TypeError):
        return True
    except OverflowError:
        return False  # A numeric range error, never a category conversion.
    return False


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


class ClockCategoryArgs(TypedDict, total=False):
    category_key_for: Callable[[object], object]


def _sample_key(value):
    return None if value is None else category_key(value)


def distribution_plan(
    columns,
    layer,
    *,
    rows=None,
    domain=None,
    max_cells=256,
    category_key_for=_sample_key,
):
    """Bounded raw-tuple samplecells, retaining every selected source instance."""
    rows = distribution_rows(columns, layer) if rows is None else rows
    category, _value, hue = distribution_channels(layer)
    config = layer.semantics
    categories = (
        [None]
        if category is None
        else list(layer.order)
        if layer.order is not None
        else levels(columns[category][row] for row in rows)
    )
    role_names = [
        (role, getattr(config, role))
        for role in ("hue", "size", "style")
        if isinstance(config, SemanticSpec) and getattr(config, role) is not None
    ]
    groups, group_keys, cells = [], {}, {}
    pool = () if domain is None else domain.get(layer.type + "_rows", ())
    if pool and domain is not None:
        original = domain["columns"]
        for row in sorted(pool):
            values = {role: original[name][row] for role, name in role_names}
            raw_hue = None if hue is None else original[hue][row]
            key = (
                _sample_key(raw_hue),
                tuple((role, _sample_key(value)) for role, value in values.items()),
            )
            if key not in group_keys:
                group_keys[key] = len(groups)
                groups.append({"key": key, "hue": raw_hue, "roles": values})
    for row in rows:
        values = {role: columns[name][row] for role, name in role_names}
        raw_hue = None if hue is None else columns[hue][row]
        key = (
            _sample_key(raw_hue),
            tuple((role, _sample_key(value)) for role, value in values.items()),
        )
        if key not in group_keys:
            group_keys[key] = len(groups)
            groups.append({"key": key, "hue": raw_hue, "roles": values})
        raw_category = None if category is None else columns[category][row]
        cell_key = (category_key_for(raw_category), key)
        if cell_key not in cells:
            cells[cell_key] = {
                "category": raw_category,
                "group": key,
                "hue": raw_hue,
                "roles": values,
                "rows": [],
            }
            if len(cells) > max_cells:
                return categories, groups, list(cells.values())
        cells[cell_key]["rows"].append(row)
    hue_order = layer.hue_order
    if (
        isinstance(config, SemanticSpec)
        and config.hue is not None
        and config.hue_kind == "categorical"
    ):
        hue_order = semantic_levels(columns, config, "hue", rows)
    if hue_order is not None:
        indices = {_sample_key(v): i for i, v in enumerate(hue_order)}
        for value in hue_order:
            if not any(
                _sample_key(group["hue"]) == _sample_key(value) for group in groups
            ):
                groups.append(
                    {"key": ("reserved", _sample_key(value)), "hue": value, "roles": {}}
                )
        groups.sort(
            key=lambda group: indices.get(_sample_key(group["hue"]), len(indices))
        )
    category_indices = {
        category_key_for(value): index for index, value in enumerate(categories)
    }
    group_indices = {group["key"]: index for index, group in enumerate(groups)}
    ordered = sorted(
        cells.values(),
        key=lambda cell: (
            group_indices[cell["group"]],
            category_indices[category_key_for(cell["category"])],
        ),
    )
    return categories, groups, ordered


def distribution_channels(layer):
    category, value, legacy_hue = distribution_columns(layer)
    config = layer.semantics
    hue = (
        config.hue
        if isinstance(config, SemanticSpec) and config.hue is not None
        else legacy_hue
    )
    return category, value, hue


def sample_rows(
    columns,
    layer,
    *,
    required=(),
    limit: int | None = 10000,
    weight_column=None,
    category_matches=None,
):
    """Paired original-row cohort with typed orders and bounded physical work."""
    category, value, hue = distribution_channels(layer)
    config = layer.semantics
    roles = {
        role: getattr(config, role)
        for role in ("hue", "size", "style")
        if isinstance(config, SemanticSpec) and getattr(config, role) is not None
    }
    weight = (
        weight_column
        if weight_column is not None
        else (layer.weights if layer.type in {"violin", "boxenplot"} else None)
    )
    names = [
        name
        for name in (category, value, hue, weight, *roles.values(), *required)
        if name is not None
    ]
    if not names or any(
        not isinstance(name, str)
        or name not in columns
        or not isinstance(columns[name], COLUMN_ARRAYS)
        for name in names
    ):
        return []
    count = len(columns[names[0]])
    if any(len(columns[name]) != count for name in names):
        return []
    selections = [
        (category, None if category_matches else layer.order),
        (hue, layer.hue_order),
    ]
    selections.extend(
        (name, getattr(config, role + "_order")) for role, name in roles.items()
    )
    selected = []
    for name, order in selections:
        if order is None:
            continue
        if (
            name is None
            or not isinstance(order, (list, tuple))
            or not all(categorical(item) for item in order)
        ):
            return []
        selected.append((name, {category_key(item) for item in order}))
    rows = []
    for row in range(count):
        if any(is_missing(columns[name][row]) for name in names):
            continue
        if any(
            not categorical(columns[name][row])
            or category_key(columns[name][row]) not in order
            for name, order in selected
        ):
            continue
        if (
            weight is not None
            and finite_number(columns[weight][row])
            and (columns[weight][row] == 0)
        ):
            continue
        if category_matches is not None and not category_matches(
            columns[category][row]
        ):
            continue
        rows.append(row)
        if limit is not None and len(rows) > limit:
            break
    return rows


def typed_swarm(layer):
    config = layer.semantics
    return layer.type == "swarmplot" and (
        layer.pack_scope is not None
        or (
            isinstance(config, SemanticSpec)
            and (config.hue is not None or config.style is not None)
        )
    )


def distribution_rows(
    columns: dict, layer: LayerSpec, *, category_matches=None
) -> list[int]:
    """Listwise-drop missing rows and apply explicit category/hue selection."""
    if layer.type == "box":
        from ._box import advanced_box, box_rows

        if advanced_box(layer):
            return box_rows(columns, layer, category_matches=category_matches)
    if layer.type == "violin":
        from ._violin_options import advanced_violin

        if advanced_violin(layer):
            return sample_rows(columns, layer, category_matches=category_matches)
    if layer.type == "boxenplot":
        from ._boxen import advanced_boxen

        if advanced_boxen(layer):
            return sample_rows(columns, layer, category_matches=category_matches)
    category, value, hue = distribution_columns(layer)
    weight = layer.weights if layer.type == "violin" else None
    config = (
        layer.semantics
        if (layer.type == "swarmplot" and isinstance(layer.semantics, SemanticSpec))
        else None
    )
    roles = [
        getattr(config, role)
        for role in ("hue", "size", "style")
        if config is not None and getattr(config, role) is not None
    ]
    selections = []
    for role in ("hue", "size", "style"):
        order = getattr(config, f"{role}_order", None)
        if order is not None:
            if not isinstance(order, (list, tuple)) or not all(
                categorical(v) for v in order
            ):
                return []
            if not isinstance(getattr(config, role), str):
                return []
            selections.append((getattr(config, role), {category_key(v) for v in order}))
    names = [
        name for name in (category, value, hue, weight, *roles) if name is not None
    ]
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
    typed = typed_swarm(layer)
    category_order = None if category_matches else layer.order
    selected_categories = selected_hues = None
    if typed:
        for order in (category_order, layer.hue_order):
            if order is not None and not all(categorical(v) for v in order):
                return []
        selected_categories = (
            None
            if category_order is None
            else {category_key(v) for v in category_order}
        )
        selected_hues = (
            None
            if layer.hue_order is None
            else {category_key(v) for v in layer.hue_order}
        )
    arrays = [columns[name] for name in names]
    if len({len(array) for array in arrays}) != 1:
        return []
    return [
        i
        for i, row in enumerate(zip(*arrays, strict=True))
        if not any(is_missing(v) for v in row)
        and (
            category_order is None
            or (
                categorical(columns[category][i])
                and selected_categories is not None
                and category_key(columns[category][i]) in selected_categories
            )
            if typed
            else category_order is None or columns[category][i] in category_order
        )
        and (
            layer.hue_order is None
            or (
                categorical(columns[hue][i])
                and selected_hues is not None
                and category_key(columns[hue][i]) in selected_hues
            )
            if typed
            else layer.hue_order is None or columns[hue][i] in layer.hue_order
        )
        and (
            all(
                not categorical(columns[name][i])
                or category_key(columns[name][i]) in selected
                for name, selected in selections
            )
        )
        and (
            weight is None
            or not finite_number(columns[weight][i])
            or columns[weight][i] != 0
        )
        and (category_matches is None or category_matches(columns[category][i]))
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


def swarm_semantic_issues(columns, layer, panel):
    """Full shared roles, preserving legacy group + independent size/style."""
    from ._semantics import data_issues

    config = layer.semantics
    if config is None:
        return []
    issues = data_issues(columns, layer, panel)
    if not isinstance(config, SemanticSpec) or issues:
        return issues
    if (
        config.hue is not None
        and config.hue_kind == "numeric"
        and layer.dodge not in (None, 0)
    ):
        issues.append("numeric hue has no discrete dodge slots; use None or 0")
    if any(finite_number(d) and d > 0 and d * d == 0 for d in config.sizes):
        issues.append("positive semantic marker area is not representable")
    if config.size is not None and not issues:
        rows = distribution_rows(columns, layer)
        if rows:
            try:
                swarm_size_mapping(columns, config, rows)
            except (ValueError, OverflowError) as error:
                issues.append(str(error))
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


def swarm_levels(columns, layer, rows):
    categories, groups = distribution_levels(columns, layer, rows)
    config = layer.semantics
    if typed_swarm(layer):
        from ._semantics import levels

        if layer.order is None:
            categories = levels(columns[layer.x][i] for i in rows)
        if layer.group is not None and layer.hue_order is None:
            groups = levels(columns[layer.group][i] for i in rows)
    if isinstance(config, SemanticSpec) and config.hue is not None:
        groups = (
            semantic_levels(columns, config, "hue", rows)
            if config.hue_kind == "categorical"
            else [None]
        )
    return categories, groups
