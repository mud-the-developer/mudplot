"""Dependency-free materialized facet grids and panel row selections."""

from __future__ import annotations

import copy
from dataclasses import replace
from itertools import pairwise, product

from ._categorical import DISTRIBUTION_TYPES, distribution_columns, distribution_rows
from ._semantics import category_key
from ._stat import STAT_LAYER_TYPES, is_missing, new_stat_request, usable_rows
from ._strip import categorical_strip
from .spec import MAX_FIGURE_LAYERS, SemanticSpec

MAX_FACET_PANELS = 64
RAW_HUE_TYPES = frozenset(
    {"line", "scatter", "bar", "errorbar", "band", "stripplot", "regplot", "rug"}
)
FACET_LAYER_TYPES = frozenset(
    {
        "line",
        "stem",
        "stairs",
        "eventplot",
        "broken_barh",
        "quiver",
        "barbs",
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
        "hist2d",
        "ecdf2d",
        "ecdf",
        "rug",
        "hline",
        "vline",
        "text",
        "annotate",
    }
)
FILTERED_Y2_LAYER_TYPES = frozenset(
    {
        "swarmplot",
        "box",
        "violin",
        "boxenplot",
        "barplot",
        "pointplot",
        "line",
        "stem",
        "stairs",
        "eventplot",
        "broken_barh",
        "quiver",
        "barbs",
        "lineplot",
        "regplot",
        "hist2d",
        "kde",
        "kde2d",
        "ecdf",
        "ecdf2d",
    }
)
_HUE_ORDER_TYPES = (
    STAT_LAYER_TYPES
    | DISTRIBUTION_TYPES
    | {"stem", "stairs", "eventplot", "broken_barh", "quiver", "barbs"}
    | {"swarmplot", "hist", "hist2d", "kde", "kde2d", "ecdf", "ecdf2d"}
    | RAW_HUE_TYPES
)


def _allows_filtered_y2(layer):
    if layer.type == "scatter" and layer.scalar_display is not None:
        return True
    if layer.type == "regplot" and layer.semantics is not None:
        from ._regression import configured_regression

        return configured_regression(layer)
    return layer.type in FILTERED_Y2_LAYER_TYPES


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


def panel_filter_issues(columns, panel, *, resolve_bins=False):
    filters = panel.filters
    if not isinstance(filters, dict) or len(filters) > 2:
        return ["panel filters must be an object with at most two columns"]
    required = panel.dropna
    if panel.grid_cohort is not None and panel.grid_cohort is not True:
        return ["grid_cohort accepts True or omission"]
    if (
        not isinstance(required, (list, tuple))
        or len(required) > 8
        or any(not isinstance(name, str) or not name for name in required)
        or len(set(required)) != len(required)
    ):
        return ["panel dropna requires at most eight unique column names"]
    if panel.grid_cohort is True and not required:
        return ["grid_cohort requires original coordinate columns in dropna"]
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
    if panel.projection != "2d" or (
        panel.y2 is not None
        and any(
            not _allows_filtered_y2(layer)
            and not (
                panel.grid_cohort is True
                and layer.type
                in {
                    "hexbin",
                    "hist2d",
                    "hline",
                    "vline",
                    "scatter",
                    "text",
                    "annotate",
                }
            )
            for layer in panel.layers
        )
    ):
        issues.append(
            "filtered panels require Cartesian2D axes; only the declared "
            "categorical/statistical and density/empirical families route to y2"
        )
    for layer in panel.layers:
        if layer.type not in FACET_LAYER_TYPES and (layer.type != "hexbin" or filters):
            issues.append(f"{layer.type} does not support panel filters")
        if layer.type == "quiver" and layer.vector is None:
            issues.append(
                "legacy quiver does not support panel filters; use VectorSpec"
            )
        if layer.c is not None and not (
            layer.type == "scatter" and layer.scalar_display is not None
        ):
            issues.append("facets use SemanticSpec numeric hue, not legacy c/colorbars")
        category_group = layer.type in DISTRIBUTION_TYPES and not layer.y
        if (
            layer.group is not None
            and not category_group
            and layer.type not in _HUE_ORDER_TYPES
            and not (panel.grid_cohort is True and layer.type == "hexbin")
        ):
            issues.append(
                f"faceted grouped {layer.type} needs a statistical/semantic builder"
            )
        if layer.type == "hist" and (
            layer.histogram is None
            or (
                filters
                and not isinstance(layer.bins, (list, tuple))
                and not (resolve_bins and type(layer.bins) is int)
            )
        ):
            issues.append(
                "faceted hist requires HistogramSpec and explicit common bin edges"
            )
        if layer.type == "kde" and layer.kde is None:
            issues.append("faceted kde requires KDESpec")
    if panel.grid_cohort is True and not issues:
        try:
            panel_rows(columns, panel)
        except (KeyError, TypeError, ValueError) as error:
            issues.append(str(error))
    return issues


def panel_rows(columns, panel):
    """Original table row IDs; missing facet keys never select an observation."""
    length = len(next(iter(columns.values()), []))
    if not panel.filters and not panel.dropna:
        return list(range(length))
    keys = {name: _key(value) for name, value in panel.filters.items()}
    rows = [
        index
        for index in range(length)
        if all(not is_missing(columns[name][index]) for name in panel.dropna)
        and all(
            not is_missing(columns[name][index]) and _key(columns[name][index]) == value
            for name, value in keys.items()
        )
    ]
    if panel.grid_cohort is True:
        from ._grid_cohort import grid_owner, grid_rows

        return grid_rows(columns, grid_owner(panel), rows)
    return rows


def panel_columns(columns, panel):
    if not panel.filters and not panel.dropna:
        return columns
    rows = panel_rows(columns, panel)
    return {name: [values[index] for index in rows] for name, values in columns.items()}


def _finite_facet_hist_edges(columns, layer, panel, rows):
    """Resolve a fixed count once, from the actual selected cohort."""
    import math
    from fractions import Fraction

    from ._histogram import histogram_rows
    from ._histogram_bins import MAX_HISTOGRAM_BINS
    from ._temporal_data import prepare_temporal_layer
    from ._transforms import projects

    if not 1 <= layer.bins <= MAX_HISTOGRAM_BINS:
        raise ValueError("facet histogram bins must be within 1..10000")
    if projects(layer):
        raise ValueError(
            "transformed facet histograms require explicit working-coordinate edges"
        )
    config = layer.semantics
    names = {layer.x, layer.group, layer.histogram.weights}
    if config is not None:
        names.update((config.hue, config.size, config.style))
    try:
        selected = {
            name: [columns[name][i] for i in rows] for name in names if name is not None
        }
    except KeyError as error:
        raise ValueError("facet histogram roles require existing columns") from error
    projected, native, _ = prepare_temporal_layer(selected, layer, panel)
    usable = histogram_rows(projected, native)
    if not usable:
        raise ValueError("empty facet histogram needs explicit common bin edges")
    values = projected[native.x]
    low, high = min(values[i] for i in usable), max(values[i] for i in usable)
    if low == high:
        low, high = low - 0.5, high + 0.5
    if not math.isfinite(high - low) or low >= high:
        raise ValueError("facet histogram range is not representably increasing")
    left, width = Fraction(low), Fraction(high) - Fraction(low)
    edges = [float(left + width * i / layer.bins) for i in range(layer.bins + 1)]
    if any(a >= b for a, b in pairwise(edges)):
        raise ValueError("facet histogram edges collapse in binary64")
    return edges


def materialize_facets(
    spec,
    *,
    row,
    col,
    row_order,
    col_order,
    col_wrap,
    share_x,
    share_y,
    _validate_template=True,
):
    """Replace one template panel with explicit, independently editable cells."""
    from .validate import assert_valid

    new_statistics = len(spec.panels) == 1 and any(
        new_stat_request(layer, spec.panels[0]) for layer in spec.panels[0].layers
    )
    if (
        _validate_template
        and not new_statistics
        and not (
            len(spec.panels) == 1
            and any(
                layer.type == "scatter"
                and layer.c is not None
                and layer.scalar_display is None
                for layer in spec.panels[0].layers
            )
        )
    ):
        panel = spec.panels[0] if len(spec.panels) == 1 else None
        selector_owned = {
            "stem",
            "stairs",
            "eventplot",
            "broken_barh",
            "quiver",
            "barbs",
        }
        if panel is not None and any(
            layer.type in selector_owned for layer in panel.layers
        ):
            other_layers = [
                layer for layer in panel.layers if layer.type not in selector_owned
            ]
            if other_layers:
                assert_valid(
                    replace(spec, panels=[replace(panel, layers=other_layers)])
                )
        else:
            assert_valid(spec)
    # This was previously rejected: a legacy scatter-c facet becomes a
    # single named P01 calibration without changing nonfaceted scatter-c.
    from .spec import ScalarDisplaySpec, SharedGuideSpec

    original = spec.panels[0] if len(spec.panels) == 1 else None
    if original is not None and any(
        layer.type == "scatter" and layer.c is not None and layer.scalar_display is None
        for layer in original.layers
    ):
        scoped = copy.deepcopy(original)
        names = (
            {getattr(layer.scalar_display, "scale_id", None) for layer in scoped.layers}
            | {getattr(layer.semantics, "scale_id", None) for layer in scoped.layers}
            | {guide.scale_id for guide in (spec.shared_guides or ())}
        )
        requests: list[SharedGuideSpec] = list(spec.shared_guides or ())
        for i, layer in enumerate(scoped.layers):
            if (
                layer.type != "scatter"
                or layer.c is None
                or layer.scalar_display is not None
            ):
                continue
            scope = f"facet_scalar_{i}"
            while scope in names:
                scope += "_"
            names.add(scope)
            kind = layer.cmap_kind
            if kind not in ("sequential", "diverging"):
                raise ValueError(
                    "faceted scatter-c needs a legacy sequential or diverging palette"
                )
            layer.scalar_display = ScalarDisplaySpec(
                cmap=f"mudplot-{kind}", scale_id=scope
            )
            layer.cmap_kind = "sequential"
            if layer.colorbar:
                requests.append(
                    SharedGuideSpec(scope, location="outside bottom", kind="scalar")
                )
        spec.panels = [scoped]
        spec.shared_guides = requests or None
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
        panel.panel_id = None
        panel.placement = None
        panel.filters = {
            name: value
            for name, value in ((row, row_value), (col, col_value))
            if name is not None
        }
        issues = panel_filter_issues(columns, panel, resolve_bins=True)
        if issues:
            raise ValueError("; ".join(issues))
        selected.update(panel_rows(columns, panel))
        caption = " | ".join(
            f"{name} = {value}" for name, value in panel.filters.items()
        )
        panel.title = f"{caption}\n{template.title}" if template.title else caption
        cells.append(panel)
    rows = sorted(selected)
    for index, layer in enumerate(template.layers):
        if (
            layer.type == "hist"
            and layer.histogram is not None
            and type(layer.bins) is int
        ):
            layer.bins = _finite_facet_hist_edges(columns, layer, template, rows)
            for panel in cells:
                panel.layers[index].bins = list(layer.bins)
    if new_statistics:
        # Validate real fixed selector views, not an undrawn all-row macro.
        # Shallow Figure replacements reuse the original immutable data graph.
        for panel in cells:
            assert_valid(
                replace(
                    spec,
                    panels=[panel],
                    facet_template=None,
                    panel_layout=None,
                )
            )

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
        eligible = rows
        if layer.type == "stem":
            from ._stem import stem_group_levels, stem_rows

            eligible = stem_rows(columns, layer, candidates=rows)
            stem_group_levels(columns, layer, eligible)
        if layer.type == "stairs" and layer.group is not None:
            from ._stairs import stair_groups

            groups = stair_groups(columns, layer, rows, retain_rows=False)
            if layer.hue_order is None:
                layer.hue_order = [value for value, _ in groups] or None
        if layer.type in {"eventplot", "broken_barh"} and layer.group is not None:
            from ._lanes import lane_members

            levels, _ = lane_members(columns, layer, candidates=rows, order_only=True)
            if layer.hue_order is None:
                layer.hue_order = levels or None
        if (
            layer.type in {"quiver", "barbs"}
            and layer.vector is not None
            and layer.group is not None
        ):
            from ._vector import vector_members

            levels, _ = vector_members(columns, layer, rows, order_only=True)
            if layer.hue_order is None:
                layer.hue_order = levels or None
        if layer.type == "swarmplot":
            members = (
                [
                    member
                    for member in template.layers
                    if member.type == "swarmplot"
                    and member.pack_scope == layer.pack_scope
                ]
                if layer.pack_scope is not None
                else [layer]
            )
            usable = set()
            for member in members:
                usable.update(distribution_rows(columns, member))
            eligible = [row for row in rows if row in usable]
        if layer.type == "box":
            from ._box import advanced_box, box_rows

            if advanced_box(layer):
                usable = set(box_rows(columns, layer))
                eligible = [row for row in rows if row in usable]
        if layer.type == "violin":
            from ._violin_options import advanced_violin

            if advanced_violin(layer):
                usable = set(distribution_rows(columns, layer))
                eligible = [row for row in rows if row in usable]
        if layer.type == "boxenplot":
            from ._boxen import advanced_boxen

            if advanced_boxen(layer):
                usable = set(distribution_rows(columns, layer))
                eligible = [row for row in rows if row in usable]
        if layer.type in STAT_LAYER_TYPES and new_stat_request(layer, template):
            usable = set(usable_rows(columns, layer, advanced=True, limit=None))
            eligible = [row for row in rows if row in usable]
        from ._line import categorical_predictor

        if layer.type in {"line", "lineplot"} and categorical_predictor(layer):
            from ._temporal_data import select_line_rows

            eligible = select_line_rows(columns, layer, template, candidates=rows)
        category = None
        if (
            layer.type in DISTRIBUTION_TYPES
            or layer.type == "swarmplot"
            or categorical_strip(layer)
        ):
            category, _, hue = distribution_columns(layer)
        else:
            hue = layer.group
            if (layer.type in STAT_LAYER_TYPES and layer.type != "lineplot") or (
                layer.type in {"line", "lineplot"} and categorical_predictor(layer)
            ):
                category = layer.x
        from ._temporal_data import category_clock, inferred_clock_order

        if category is not None and layer.order is None:
            clock = category_clock(layer, template)
            slot_rows = eligible
            if clock is not None:
                if layer.type in STAT_LAYER_TYPES:
                    usable = set(
                        usable_rows(
                            columns,
                            layer,
                            advanced=new_stat_request(layer, template),
                            limit=None,
                        )
                    )
                else:
                    usable = set(distribution_rows(columns, layer))
                    if categorical_strip(layer) and layer.semantics is not None:
                        from ._semantics import semantic_rows

                        usable.intersection_update(semantic_rows(columns, layer))
                slot_rows = (i for i in eligible if i in usable)
            raw = (columns[category][i] for i in slot_rows)
            values = _ordered(
                raw if clock is None else inferred_clock_order(raw, clock)
            )
            layer.order = values or None
        if hue is not None and layer.hue_order is None:
            values = _ordered(columns[hue][i] for i in eligible)
            layer.hue_order = values or None
        for panel in cells:
            panel.layers[index] = copy.deepcopy(layer)

    cols = len(col_levels) if col_wrap is None else min(col_wrap, len(col_levels))
    spec.panels = cells
    if template.panel_id is not None:
        from ._layout import panel_ids

        panel_ids(spec)
    spec.layout = [(count + cols - 1) // cols, cols]
    spec.width_ratios = spec.height_ratios = None
    spec.share_x, spec.share_y = share_x, share_y
    # New per-hue box styles must see the shared resolved hue reservations
    # before an empty/materialized cell is validated. Unrelated old facets
    # retain their existing inferred-order serialization.
    box_scales = {
        layer.semantics.scale_id
        for layer in template.layers
        if layer.type in {"box", "violin", "boxenplot"}
        and getattr(
            getattr(layer, "boxen" if layer.type == "boxenplot" else layer.type),
            "hue_components",
            None,
        )
        and isinstance(layer.semantics, SemanticSpec)
    }
    if box_scales:
        _resolve_semantic_hue_orders(spec, scale_ids=box_scales)
    assert_valid(spec)


def _recipe_geometry(recipe):
    if recipe.row is None and recipe.col is None:
        raise ValueError("live facets require row or col")
    for name in (recipe.row, recipe.col):
        if name is not None and (not isinstance(name, str) or not name):
            raise ValueError("live facet columns must be nonempty names")
    if recipe.row is None:
        if recipe.row_order:
            raise ValueError("absent row dimension requires an empty resolved order")
        row_levels = [None]
    else:
        row_levels = _ordered((), recipe.row_order)
    if recipe.col is None:
        if recipe.col_order:
            raise ValueError("absent col dimension requires an empty resolved order")
        col_levels = [None]
    else:
        col_levels = _ordered((), recipe.col_order)
    if recipe.col_wrap is not None and (
        recipe.row is not None
        or recipe.col is None
        or type(recipe.col_wrap) is not int
        or not 1 <= recipe.col_wrap <= 64
    ):
        raise ValueError("live facet wrap requires col-only facets and integer1..64")
    count = len(row_levels) * len(col_levels)
    if not 1 <= count <= MAX_FACET_PANELS:
        raise ValueError("live facets require1..64 fixed cells")
    selectors = [
        {
            name: value
            for name, value in ((recipe.row, row), (recipe.col, col))
            if name is not None
        }
        for row, col in product(row_levels, col_levels)
    ]
    cols = (
        len(col_levels)
        if recipe.col_wrap is None
        else min(recipe.col_wrap, len(col_levels))
    )
    return selectors, [(count + cols - 1) // cols, cols]


def _selector_signature(selector):
    if not isinstance(selector, dict):
        raise ValueError("live facet selector must be an object")
    return tuple((name, _key(value)) for name, value in sorted(selector.items()))


def _live_cells(spec, selectors):
    """Resolve fixed typed selectors through authoritative saved N13 views."""
    expected = {_selector_signature(selector) for selector in selectors}
    found = {}
    for panel in spec.panels:
        signature = _selector_signature(panel.filters)
        if signature not in expected:
            continue
        if signature in found:
            raise ValueError("live facet selectors have ambiguous panel ownership")
        found[signature] = panel
    if found.keys() != expected:
        raise ValueError("materialized live cell selectors disagree with the recipe")
    return found


def _resolve_semantic_hue_orders(spec, *, scale_ids=None):
    from ._semantics import semantic_levels, shared_scale_domains

    domains = shared_scale_domains(spec)
    for panel in spec.panels:
        for layer in panel.layers:
            config = layer.semantics
            if (
                isinstance(config, SemanticSpec)
                and config.hue is not None
                and config.hue_kind == "categorical"
                and config.hue_order is None
                and (scale_ids is None or config.scale_id in scale_ids)
            ):
                domain = domains.get(config.scale_id)
                if domain is not None:
                    levels = semantic_levels(
                        domain["columns"], config, "hue", domain["rows"]
                    )
                    if levels:
                        config.hue_order = list(levels)


def _capture_live_template(spec, original, row, col, col_wrap):
    from .spec import FacetTemplateSpec

    original = copy.deepcopy(original)
    _resolve_semantic_hue_orders(spec)
    # Keep the original title/reference metadata, not the first cell's caption.
    original.layers = copy.deepcopy(spec.panels[0].layers)
    original.filters = {}
    selectors = [copy.deepcopy(panel.filters) for panel in spec.panels]
    row_order = [] if row is None else _ordered(selector[row] for selector in selectors)
    col_order = [] if col is None else _ordered(selector[col] for selector in selectors)
    spec.facet_template = FacetTemplateSpec(
        template=original,
        selectors=selectors,
        row=row,
        col=col,
        row_order=row_order,
        col_order=col_order,
        col_wrap=col_wrap,
    )


def materialize_live_facets(spec, **options):
    from .validate import assert_valid

    if len(spec.panels) != 1:
        raise ValueError("live facet creation requires one completed template panel")
    original = spec.panels[0]
    spec.facet_template = None
    materialize_facets(spec, **options, _validate_template=False)
    _capture_live_template(
        spec, original, options["row"], options["col"], options["col_wrap"]
    )
    assert_valid(spec)


def _category_source(layer):
    if layer.type in DISTRIBUTION_TYPES | {"swarmplot"} or categorical_strip(layer):
        return distribution_columns(layer)[0]
    return layer.x


def _preserve_template_orders(previous, replacement):
    for index, layer in enumerate(replacement.layers):
        # Cell slots are attached to their declared category channel, not marks.
        candidates = [
            old
            for old in previous.layers
            if _category_source(old) == _category_source(layer)
            and old.orient == layer.orient
            and old.axis == layer.axis
        ]
        old = (
            candidates[0]
            if candidates
            else previous.layers[index]
            if index < len(previous.layers)
            else None
        )
        if old is None:
            continue
        from ._line import categorical_predictor
        from ._temporal_data import category_clock

        clock = category_clock(layer, replacement)
        previous_clock = category_clock(old, previous)

        categorical = (
            layer.type in DISTRIBUTION_TYPES | {"swarmplot"}
            or categorical_strip(layer)
            or categorical_predictor(layer)
        )
        old_categorical = (
            old.type in DISTRIBUTION_TYPES | {"swarmplot"}
            or categorical_strip(old)
            or categorical_predictor(old)
        )
        if (
            (
                (
                    clock is None
                    and previous_clock is None
                    and categorical
                    and old_categorical
                )
                or (
                    clock is not None
                    and clock == previous_clock
                    and old.axis == layer.axis
                    and old.orient == layer.orient
                )
            )
            and layer.order is None
            and _category_source(layer) == _category_source(old)
        ):
            layer.order = copy.deepcopy(old.order)
        if (
            layer.group is not None
            and layer.group == old.group
            and layer.hue_order is None
        ):
            layer.hue_order = copy.deepcopy(old.hue_order)
        config, prior = layer.semantics, old.semantics
        if (
            isinstance(config, SemanticSpec)
            and isinstance(prior, SemanticSpec)
            and config.hue is not None
            and config.hue == prior.hue
            and config.hue_kind == prior.hue_kind == "categorical"
            and config.hue_order is None
        ):
            config.hue_order = copy.deepcopy(prior.hue_order)


def replace_facet_template(spec, template, *, reset_orders=False):
    from .spec import FacetTemplateSpec, PanelSpec
    from .validate import assert_valid

    recipe = spec.facet_template
    if not isinstance(recipe, FacetTemplateSpec):
        raise ValueError("SetFacetTemplate requires opt-in live facets")
    if not isinstance(template, PanelSpec) or type(reset_orders) is not bool:
        raise ValueError("template must be PanelSpec and reset_orders must be bool")
    selectors, layout = _recipe_geometry(recipe)
    if len(template.layers) * len(selectors) > MAX_FIGURE_LAYERS:
        raise ValueError("live template expansion exceeds the total-layer limit")
    saved_cells = _live_cells(spec, selectors)
    replacement = copy.deepcopy(template)
    replacement.panel_id = None
    replacement.placement = None
    if replacement.filters:
        raise ValueError(
            "facet template filters must be empty; use the frozen cell recipe"
        )
    if not reset_orders:
        _preserve_template_orders(recipe.template, replacement)

    candidate = replace(
        spec,
        panels=[replacement],
        facet_template=None,
        panel_layout=None,
        shared_guides=None,
        width_ratios=None,
        height_ratios=None,
    )
    materialize_facets(
        candidate,
        row=recipe.row,
        col=recipe.col,
        row_order=recipe.row_order if recipe.row is not None else None,
        col_order=recipe.col_order if recipe.col is not None else None,
        col_wrap=recipe.col_wrap,
        share_x=spec.share_x,
        share_y=spec.share_y,
        _validate_template=False,
    )
    if candidate.layout != layout or [
        _selector_signature(p.filters) for p in candidate.panels
    ] != [_selector_signature(s) for s in selectors]:
        raise ValueError("live template transaction changed fixed cell identities")
    refreshed = {}
    for panel in candidate.panels:
        signature = _selector_signature(panel.filters)
        saved = saved_cells[signature]
        panel.panel_id = saved.panel_id
        panel.placement = copy.deepcopy(saved.placement)
        refreshed[signature] = panel
    if candidate.shared_guides:
        existing = list(spec.shared_guides or ())
        names = {guide.scale_id for guide in existing}
        spec.shared_guides = existing + [
            guide for guide in candidate.shared_guides if guide.scale_id not in names
        ]
    spec.panels = [
        refreshed.get(_selector_signature(panel.filters), panel)
        for panel in spec.panels
    ]
    _capture_live_template(
        candidate, replacement, recipe.row, recipe.col, recipe.col_wrap
    )
    spec.facet_template = candidate.facet_template
    assert_valid(spec)


def facet_template_issues(spec):
    """Validate a stored recipe without replacing authoritative saved views."""

    from .spec import FacetTemplateSpec, PanelSpec

    recipe = spec.facet_template
    if recipe is None:
        return []
    if not isinstance(recipe, FacetTemplateSpec) or not isinstance(
        recipe.template, PanelSpec
    ):
        return ["facet_template requires a typed template and frozen selectors"]
    try:
        selectors, layout = _recipe_geometry(recipe)
        expected = [_selector_signature(s) for s in selectors]
        if [_selector_signature(s) for s in recipe.selectors] != expected:
            raise ValueError("stored selectors disagree with resolved facet orders")
        _live_cells(spec, selectors)
        if spec.panel_layout is None and (
            len(spec.panels) != len(selectors) or spec.layout != layout
        ):
            raise ValueError("stored live facet layout/cell count is inconsistent")
        if recipe.template.filters:
            raise ValueError("stored facet template filters must be empty")
        if len(recipe.template.layers) * len(selectors) > MAX_FIGURE_LAYERS:
            raise ValueError("live template expansion exceeds the total-layer limit")
        # Check the future transaction's options/data/resources in a temporary
        # pure graph; never rematerialize or rewrite saved per-cell overrides.
        candidate = replace(
            spec,
            panels=[recipe.template],
            facet_template=None,
            panel_layout=None,
            shared_guides=None,
            width_ratios=None,
            height_ratios=None,
        )
        materialize_facets(
            candidate,
            row=recipe.row,
            col=recipe.col,
            row_order=recipe.row_order if recipe.row is not None else None,
            col_order=recipe.col_order if recipe.col is not None else None,
            col_wrap=recipe.col_wrap,
            share_x=spec.share_x,
            share_y=spec.share_y,
            _validate_template=False,
        )
    except (ValueError, TypeError, KeyError) as error:
        return [f"facet_template: {error}"]
    return []
