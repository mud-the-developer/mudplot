"""Dependency-free materialized facet grids and panel row selections."""

from __future__ import annotations

import copy
from itertools import product

from ._categorical import DISTRIBUTION_TYPES, distribution_columns
from ._semantics import category_key
from ._stat import STAT_LAYER_TYPES, is_missing
from .spec import MAX_FIGURE_LAYERS, SemanticSpec

MAX_FACET_PANELS = 64
RAW_HUE_TYPES = frozenset(
    {"line", "scatter", "bar", "errorbar", "band", "stripplot", "regplot", "rug"}
)
FACET_LAYER_TYPES = frozenset(
    {
        "line",
        "regplot",
        "scatter",
        "stripplot",
        "bar",
        "errorbar",
        "band",
        "barplot",
        "pointplot",
        "countplot",
        "lineplot",
        "swarmplot",
        "box",
        "boxenplot",
        "violin",
        "hist",
        "kde",
        "kde2d",
        "ecdf",
        "rug",
        "hline",
        "vline",
        "text",
        "annotate",
    }
)
_HUE_ORDER_TYPES = (
    STAT_LAYER_TYPES
    | DISTRIBUTION_TYPES
    | {"swarmplot", "hist", "kde", "kde2d", "ecdf"}
    | RAW_HUE_TYPES
)


def _key(value):
    if type(value) not in (str, bool, int, float):
        raise ValueError("facet keys must be JSON strings, booleans or finite numbers")
    return category_key(value)


def _ordered(values, order=None):
    if order is not None and (not isinstance(order, (list, tuple)) or not order):
        raise ValueError("facet orders must be nonempty lists")
    selected = list(values if order is None else order)
    result, seen = [], set()
    for value in selected:
        if order is None and is_missing(value):
            continue
        key = _key(value)
        if key in seen:
            if order is not None:
                raise ValueError("facet orders must contain unique levels")
            continue
        seen.add(key)
        result.append(value)
    if len(result) > MAX_FACET_PANELS or len({str(v) for v in result}) != len(result):
        raise ValueError("facet levels exceed 64 or have ambiguous display labels")
    return result


def ordered_group_columns(columns, layer):
    """Select raw groups, retaining within-group row order and coordinate gaps."""
    if layer.type not in RAW_HUE_TYPES or layer.hue_order is None:
        return columns
    order = _ordered((), layer.hue_order)
    if (
        not isinstance(columns, dict)
        or not isinstance(layer.group, str)
        or not layer.group
        or layer.group not in columns
    ):
        raise ValueError("raw hue_order requires an existing group column")
    if layer.c is not None:
        raise ValueError("raw hue_order does not support legacy c/colorbars")
    groups = columns[layer.group]
    if not isinstance(groups, (list, tuple)) or any(
        not isinstance(values, (list, tuple)) or len(values) != len(groups)
        for values in columns.values()
    ):
        raise ValueError("raw hue_order requires equal-length column arrays")
    keys = {_key(value) for value in order}
    rows = [
        index
        for index, value in enumerate(groups)
        if not is_missing(value) and _key(value) in keys
    ]
    return {name: [values[index] for index in rows] for name, values in columns.items()}


def panel_filter_issues(columns, panel):
    filters = panel.filters
    if not isinstance(filters, dict) or len(filters) > 2:
        return ["panel filters must be an object with at most two columns"]
    required = panel.dropna
    if (
        not isinstance(required, (list, tuple))
        or len(required) > 8
        or any(not isinstance(name, str) or not name for name in required)
        or len(set(required)) != len(required)
    ):
        return ["panel dropna requires at most eight unique column names"]
    if not filters and not required:
        return []
    issues = []
    if (
        not isinstance(columns, dict)
        or any(not isinstance(v, (list, tuple)) for v in columns.values())
        or len({len(v) for v in columns.values()}) > 1
    ):
        return ["filtered panels require equal-length column arrays"]
    for name in required:
        if name not in columns:
            issues.append(f"dropna column {name!r} does not exist")
    for name, value in filters.items():
        if not isinstance(name, str) or not name or name not in columns:
            issues.append(f"filter column {name!r} does not exist")
            continue
        try:
            _key(value)
            for item in columns[name]:
                if not is_missing(item):
                    _key(item)
        except ValueError as error:
            issues.append(str(error))
    if panel.projection != "2d" or panel.y2 is not None:
        issues.append("filtered panels support primary Cartesian 2D axes only")
    for layer in panel.layers:
        if layer.type not in FACET_LAYER_TYPES:
            issues.append(f"{layer.type} does not support panel filters")
        if layer.c is not None:
            issues.append("facets use SemanticSpec numeric hue, not legacy c/colorbars")
        category_group = layer.type in DISTRIBUTION_TYPES and not layer.y
        if (
            layer.group is not None
            and not category_group
            and layer.type not in _HUE_ORDER_TYPES
        ):
            issues.append(
                f"faceted grouped {layer.type} needs a statistical/semantic builder"
            )
        if layer.type == "hist" and (
            layer.histogram is None
            or (filters and not isinstance(layer.bins, (list, tuple)))
        ):
            issues.append(
                "faceted hist requires HistogramSpec and explicit common bin edges"
            )
        if layer.type == "kde" and layer.kde is None:
            issues.append("faceted kde requires KDESpec")
    return issues


def panel_rows(columns, panel):
    """Original table row IDs; missing facet keys never select an observation."""
    length = len(next(iter(columns.values()), []))
    if not panel.filters and not panel.dropna:
        return list(range(length))
    keys = {name: _key(value) for name, value in panel.filters.items()}
    return [
        index
        for index in range(length)
        if all(not is_missing(columns[name][index]) for name in panel.dropna)
        and all(
            not is_missing(columns[name][index]) and _key(columns[name][index]) == value
            for name, value in keys.items()
        )
    ]


def panel_columns(columns, panel):
    if not panel.filters and not panel.dropna:
        return columns
    rows = panel_rows(columns, panel)
    return {name: [values[index] for index in rows] for name, values in columns.items()}


def materialize_facets(
    spec, *, row, col, row_order, col_order, col_wrap, share_x, share_y
):
    """Replace one template panel with explicit, independently editable cells."""
    from .validate import assert_valid

    assert_valid(spec)
    if len(spec.panels) != 1 or spec.panels[0].filters or spec.panels[0].dropna:
        raise ValueError("facet requires one unfiltered source panel")
    if not spec.panels[0].layers:
        raise ValueError("facet needs completed source layers; build them before facet")
    if row is None and col is None:
        raise ValueError("facet requires row or col")
    if row is not None and row == col:
        raise ValueError("facet row and col must be different columns")
    columns = spec.data.columns
    for name, order in ((row, row_order), (col, col_order)):
        if name is None:
            if order is not None:
                raise ValueError("facet order requires its row/col column")
        elif not isinstance(name, str) or not name or name not in columns:
            raise ValueError("facet row/col must name existing columns")
    if share_x not in ("none", "all", "row", "col") or share_y not in (
        "none",
        "all",
        "row",
        "col",
    ):
        raise ValueError("facet share_x/share_y require none/all/row/col")
    if col_wrap is not None and (
        row is not None
        or col is None
        or type(col_wrap) is not int
        or not 1 <= col_wrap <= 64
    ):
        raise ValueError("col_wrap requires col-only faceting and an integer in [1,64]")
    row_levels = [None] if row is None else _ordered(columns[row], row_order)
    col_levels = [None] if col is None else _ordered(columns[col], col_order)
    count = len(row_levels) * len(col_levels)
    if not 1 <= count <= MAX_FACET_PANELS:
        raise ValueError("facet grid needs 1..64 cells; provide orders for empty data")

    if count * len(spec.panels[0].layers) > MAX_FIGURE_LAYERS:
        raise ValueError(f"facet expansion exceeds {MAX_FIGURE_LAYERS} total layers")
    template = copy.deepcopy(spec.panels[0])
    cells = []
    selected = set()
    for row_value, col_value in product(row_levels, col_levels):
        panel = copy.deepcopy(template)
        panel.filters = {
            name: value
            for name, value in ((row, row_value), (col, col_value))
            if name is not None
        }
        issues = panel_filter_issues(columns, panel)
        if issues:
            raise ValueError("; ".join(issues))
        selected.update(panel_rows(columns, panel))
        caption = " | ".join(
            f"{name} = {value}" for name, value in panel.filters.items()
        )
        panel.title = f"{caption}\n{template.title}" if template.title else caption
        cells.append(panel)

    rows = sorted(selected)
    used_names = {
        layer.semantics.scale_id
        for layer in template.layers
        if isinstance(layer.semantics, SemanticSpec)
        and layer.semantics.scale_id is not None
    }
    for index, layer in enumerate(template.layers):
        if (
            isinstance(layer.semantics, SemanticSpec)
            and layer.semantics.scale_id is None
        ):
            suffix = index
            name = f"facet_layer_{suffix}"
            while name in used_names:
                suffix += 1
                name = f"facet_layer_{suffix}"
            used_names.add(name)
            layer.semantics.scale_id = name
        category = None
        if layer.type in DISTRIBUTION_TYPES or layer.type == "swarmplot":
            category, _, hue = distribution_columns(layer)
        else:
            hue = layer.group
            if layer.type in STAT_LAYER_TYPES and layer.type != "lineplot":
                category = layer.x
        if category is not None and layer.order is None:
            values = _ordered(columns[category][i] for i in rows)
            layer.order = values or None
        if hue is not None and layer.hue_order is None:
            values = _ordered(columns[hue][i] for i in rows)
            layer.hue_order = values or None
        for panel in cells:
            panel.layers[index] = copy.deepcopy(layer)

    cols = len(col_levels) if col_wrap is None else min(col_wrap, len(col_levels))
    spec.panels = cells
    spec.layout = [(count + cols - 1) // cols, cols]
    spec.width_ratios = spec.height_ratios = None
    spec.share_x, spec.share_y = share_x, share_y
    assert_valid(spec)
