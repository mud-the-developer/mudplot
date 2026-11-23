"""Dependency-free, opt-in scatter role contracts and stable linear mapping."""

from __future__ import annotations

import math
from dataclasses import replace

from ._ecdf import ecdf_config, finite_number
from ._stat import is_missing
from ._transforms import COLUMN_ARRAYS
from .spec import ECDFSpec, SemanticSpec, StatSpec

MARKERS = ("o", "s", "D", "^", "v", "P", "X", "d", "p", "h", "8", "*")
MAX_LEVELS = 64
MAX_ROWS = 10000
MAX_CURVES = 256
ROLE_LAYER_TYPES = frozenset(
    {
        "scatter",
        "line",
        "stem",
        "lineplot",
        "swarmplot",
        "stripplot",
        "ecdf",
        "rug",
        "regplot",
        "eventplot",
        "box",
        "violin",
        "boxenplot",
        "hist",
        "countplot",
        "barplot",
        "pointplot",
        "kde",
        "kde2d",
        "hist2d",
        "ecdf2d",
    }
)


def categorical(value):
    return (
        isinstance(value, bool)
        or (isinstance(value, str) and bool(value))
        or finite_number(value)
    )


def category_key(value):
    if not categorical(value):
        raise ValueError(
            "semantic categories require nonempty strings or finite scalars"
        )
    # Bool and numeric categories are distinct; numbers retain exact integer keys.
    return (
        "str"
        if isinstance(value, str)
        else "bool"
        if isinstance(value, bool)
        else "number",
        value,
    )


def levels(values):
    result, seen = [], set()
    for value in values:
        key = category_key(value)
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def valid_scale_id(value):
    return (
        isinstance(value, str)
        and bool(value.strip())
        and len(value) <= 64
        and not any(ord(character) < 32 for character in value)
    )


def option_issues(config):
    issues = []
    if not isinstance(config, SemanticSpec):
        return ["semantics must be SemanticSpec or None"]
    if config.scale_id is not None and not valid_scale_id(config.scale_id):
        issues.append(
            "scale_id must be a nonempty <=64-character name without controls"
        )
    if all(getattr(config, role) is None for role in ("hue", "size", "style")):
        issues.append("semantics requires at least one hue/size/style column")
    for role in ("hue", "size", "style"):
        column = getattr(config, role)
        if column is not None and (not isinstance(column, str) or not column):
            issues.append(f"{role} must be a nonempty column name or None")
        kind = "categorical" if role == "style" else getattr(config, f"{role}_kind")
        if not isinstance(kind, str) or kind not in ("categorical", "numeric"):
            issues.append(f"{role}_kind must be categorical or numeric")
            continue
        order = getattr(config, f"{role}_order")
        if order is not None:
            if column is None or kind != "categorical":
                issues.append(f"{role}_order requires categorical {role}")
            if (
                not isinstance(order, (list, tuple))
                or not 1 <= len(order) <= MAX_LEVELS
                or not all(categorical(v) for v in order)
            ):
                issues.append(
                    f"{role}_order must contain 1..{MAX_LEVELS} scalar levels"
                )
            elif len(levels(order)) != len(order) or len(
                {str(v) for v in order}
            ) != len(order):
                issues.append(f"{role}_order needs unique, unambiguous labels")
        if role != "style":
            norm = getattr(config, f"{role}_norm")
            if norm is not None:
                if column is None or kind != "numeric":
                    issues.append(f"{role}_norm requires numeric {role}")
                if (
                    not isinstance(norm, (list, tuple))
                    or len(norm) != 2
                    or not all(finite_number(v) for v in norm)
                    or not norm[0] < norm[1]
                ):
                    issues.append(
                        f"{role}_norm must be finite increasing [lower,upper]"
                    )
            default = "categorical" if role == "hue" else "numeric"
            if column is None and kind != default:
                issues.append(f"{role}_kind requires {role}")
    sizes = config.sizes
    if (
        not isinstance(sizes, (list, tuple))
        or len(sizes) != 2
        or not all(finite_number(v) for v in sizes)
        or not 0 <= sizes[0] < sizes[1] <= 1000
    ):
        issues.append("sizes must be increasing diameters in [0,1000] points")
        return issues
    if config.size is None and list(sizes) != [3.0, 9.0]:
        issues.append("sizes requires size")
    markers = config.markers
    if (
        not isinstance(markers, (list, tuple))
        or not 1 <= len(markers) <= len(MARKERS)
        or not all(isinstance(v, str) and v in MARKERS for v in markers)
        or len(set(markers)) != len(markers)
    ):
        issues.append("markers must be distinct named filled markers")
        return issues
    if config.style is None and list(markers) != ["o", "s", "D", "^", "v", "P", "X"]:
        issues.append("markers requires style")
    dashes = config.dashes
    if dashes is not None:
        if config.style is None:
            issues.append("dashes requires style")
        if (
            not isinstance(dashes, (list, tuple))
            or not 1 <= len(dashes) <= 4
            or not all(
                isinstance(v, str) and v in ("-", "--", "-.", ":") for v in dashes
            )
            or len(set(dashes)) != len(dashes)
        ):
            issues.append("dashes must be 1..4 distinct named line styles")
    if type(config.legend) is not bool:
        issues.append("semantic legend must be boolean")
    return issues


def semantic_rows(columns, layer, *, row_limit=None, category_matches=None):
    config = layer.semantics
    if not isinstance(config, SemanticSpec):
        return []
    if layer.type == "stem":
        from ._stem import stem_rows

        return stem_rows(columns, layer)
    if layer.type == "eventplot":
        from ._lanes import lane_members

        return [row for row, _ in lane_members(columns, layer)[1]]
    if layer.type in {"line", "lineplot"}:
        if (
            layer.type == "lineplot"
            and layer.stat is not None
            and not isinstance(layer.stat, StatSpec)
        ):
            return []
        from ._line import line_rows

        # Mapping uses finite observations; topology retains missing responses.
        return line_rows(columns, layer)
    if layer.type == "box":
        from ._box import box_rows

        return box_rows(columns, layer, category_matches=category_matches)
    if layer.type in {"hist", "countplot"}:
        from ._body_semantics import body_rows

        return body_rows(columns, layer, category_matches=category_matches)
    if layer.type in {"barplot", "pointplot"}:
        from ._stat import usable_rows

        return usable_rows(
            columns, layer, advanced=True, category_matches=category_matches
        )
    if layer.type in {"swarmplot", "violin", "boxenplot"}:
        from ._categorical import distribution_rows

        return distribution_rows(columns, layer, category_matches=category_matches)
    coordinates = (
        [layer.x] if layer.type in {"ecdf", "rug", "kde"} else [layer.x, layer.y]
    )
    names = coordinates + [
        getattr(config, r)
        for r in ("hue", "size", "style")
        if getattr(config, r) is not None
    ]
    weights = None
    if layer.type == "ecdf":
        if layer.ecdf is not None and not isinstance(layer.ecdf, ECDFSpec):
            return []
        weights = ecdf_config(layer).weights
        if weights is not None:
            names.append(weights)
    elif layer.type in {"kde", "kde2d", "hist2d", "ecdf2d"}:
        from ._density import weight_column

        weights = weight_column(layer)
        if weights is not None:
            names.append(weights)
    if not all(
        isinstance(name, str)
        and name in columns
        and isinstance(columns[name], COLUMN_ARRAYS)
        for name in names
    ):
        return []
    if len({len(columns[name]) for name in names}) != 1:
        return []
    selections = []
    if (
        layer.type == "stripplot"
        and layer.order is not None
        and category_matches is None
    ):
        if not isinstance(layer.order, (list, tuple)) or not all(
            categorical(v) for v in layer.order
        ):
            return []
        selections.append((layer.x, {category_key(v) for v in layer.order}))
    for role in ("hue", "size", "style"):
        order = getattr(config, f"{role}_order")
        if order is not None:
            if not isinstance(order, (list, tuple)) or not all(
                categorical(v) for v in order
            ):
                return []
            selections.append((getattr(config, role), {category_key(v) for v in order}))
    rows = []
    for i, values in enumerate(zip(*(columns[name] for name in names), strict=True)):
        if any(is_missing(value) for value in values):
            continue
        if (
            weights is not None
            and finite_number(columns[weights][i])
            and columns[weights][i] == 0
        ):
            continue
        if any(
            name is not None
            and categorical(columns[name][i])
            and category_key(columns[name][i]) not in selected
            for name, selected in selections
        ):
            continue
        if category_matches is not None and not category_matches(columns[layer.x][i]):
            continue
        if row_limit is not None and len(rows) >= row_limit:
            raise ValueError("new fields exceed10000 selected physical rows")
        rows.append(i)
    return rows


def semantic_levels(columns, config, role, rows):
    name = getattr(config, role)
    if name is None:
        return [None]
    order = getattr(config, f"{role}_order")
    return list(order) if order is not None else levels(columns[name][i] for i in rows)


def axis_issues(layer, panel):
    """Reject unsupported semantic targets before converting coordinate views."""
    if layer.type in {"stem", "eventplot"}:
        if panel.projection != "2d" or layer.axis not in ("y", "y2"):
            return [f"semantic {layer.type} requires Cartesian primary/y2 axes"]
        if layer.axis == "y2" and panel.y2 is None:
            return [f"semantic {layer.type} y2 target must be configured"]
        return []
    if layer.type in {"kde", "kde2d", "hist2d", "ecdf2d"}:
        if panel.projection != "2d" or layer.axis not in {"y", "y2"}:
            return ["density/empirical fields require Cartesian2D targets"]
        target = panel.y2 if layer.axis == "y2" else panel.y
        if target is None:
            return ["density/empirical y2 target must be configured"]
        axes = (target, panel.x) if layer.orient == "h" else (panel.x, target)
        observation = axes[:1] if layer.type == "kde" else axes
        if any(axis.scale not in {"linear", "log"} for axis in observation):
            return ["density/empirical observations support linear/log display axes"]
        if layer.type == "kde":
            ordinate = panel.x if layer.orient == "h" else target
            if ordinate.scale != "linear" or ordinate.temporal is not None:
                return ["KDE density/CDF/composition ordinate must be numeric linear"]
        return []
    response_axis = panel.y2 if layer.axis == "y2" else panel.y
    temporal_secondary = (
        layer.axis == "y2"
        and response_axis is not None
        and layer.orient == "v"
        and layer.stat_scale == "data"
        and (panel.x.temporal is not None or response_axis.temporal is not None)
        and panel.x.scale == "linear"
        and response_axis.scale == "linear"
    )
    if (
        layer.axis != "y"
        and not temporal_secondary
        and layer.type
        not in {
            "line",
            "lineplot",
            "stripplot",
            "hist",
            "countplot",
            "ecdf",
            "rug",
            "swarmplot",
            "box",
            "violin",
            "boxenplot",
            "barplot",
            "pointplot",
        }
    ) or panel.projection != "2d":
        return [
            "semantic layers support primary Cartesian2D only; y2 needs an "
            "explicit vertical linear temporal x/y2 axis"
        ]
    return []


def data_issues(columns, layer, panel, *, allow_empty=False):
    if layer.type in {"kde", "kde2d", "hist2d", "ecdf2d"}:
        from ._density import density_semantic_issues

        return density_semantic_issues(columns, layer, panel)
    if layer.type == "box":
        from ._box import box_semantic_issues

        return box_semantic_issues(columns, layer, panel)
    if layer.type == "violin":
        from ._violin_options import violin_semantic_issues

        return violin_semantic_issues(columns, layer, panel)
    if layer.type == "boxenplot":
        from ._boxen import boxen_semantic_issues

        return boxen_semantic_issues(columns, layer, panel)
    if layer.type in {"barplot", "pointplot", "hist", "countplot"}:
        from ._stat import stat_semantic_issues

        return stat_semantic_issues(columns, layer, panel)
    config = layer.semantics
    issues = option_issues(config)
    if not isinstance(config, SemanticSpec) or issues:
        return issues
    legacy_swarm_group = layer.type == "swarmplot" and config.hue is None
    stem = layer.type == "stem"
    event = layer.type == "eventplot"
    legacy_group = legacy_swarm_group or (stem and config.hue is None) or event
    if (layer.group is not None and not legacy_group) or layer.c is not None:
        issues.append("semantics cannot combine with legacy group/c")
    line = layer.type in {"line", "lineplot", "ecdf"}
    rug = layer.type == "rug"
    stroke = line or rug or stem or event
    if event and list(config.markers) != SemanticSpec().markers:
        issues.append("eventplot styles map dashes, not markers")
    issues.extend(axis_issues(layer, panel))
    response_axis = panel.y2 if layer.axis == "y2" else panel.y
    if layer.hue_order is not None and not legacy_group:
        issues.append("use semantic hue_order, not legacy layer hue_order")
    if not stroke and config.dashes is not None:
        issues.append("semantic dashes require an applicable stroke layer")
    if (
        stroke
        and config.style is not None
        and layer.line_style is not None
        and (rug or event or config.dashes is not None)
    ):
        issues.append("line_style cannot override mapped dashes")
    numeric_hue = config.hue is not None and config.hue_kind == "numeric"
    if type(layer.colorbar) is not bool:
        issues.append("semantic colorbar must be boolean")
    if (layer.colorbar or layer.clabel is not None) and not numeric_hue:
        issues.append("semantic colorbar/clabel requires numeric hue")
    if layer.clabel is not None and (
        not layer.colorbar
        or not isinstance(layer.clabel, str)
        or len(layer.clabel) > 512
    ):
        issues.append("semantic clabel requires colorbar and a <=512-character string")
    if config.hue is not None and layer.color is not None:
        issues.append("color cannot override a mapped hue")
    size_override = layer.line_width if stroke else layer.marker_size
    if config.size is not None and size_override is not None:
        issues.append("line_width/marker_size cannot override mapped size")
    if config.style is not None and layer.marker is not None:
        issues.append("marker cannot override mapped style")
    if stroke and layer.edge_color is not None:
        issues.append("semantic stroke edge_color is not supported")
    if not stroke:
        from ._components import _color

        if layer.edge_color is not None and not _color(layer.edge_color):
            issues.append("semantic edge_color must be a bounded name or hex color")
        if layer.line_width is not None and (
            not finite_number(layer.line_width) or not 0 <= layer.line_width <= 1000
        ):
            issues.append(
                "semantic outline line_width must be finite in [0,1000] points"
            )
    if config.hue_kind != "numeric" and layer.cmap_kind != "sequential":
        issues.append("cmap_kind only applies to numeric hue")
    if config.hue_kind == "numeric" and (
        not isinstance(layer.cmap_kind, str)
        or layer.cmap_kind not in ("sequential", "diverging")
    ):
        issues.append("numeric hue cmap_kind must be sequential or diverging")
    if layer.references is not None and not legacy_swarm_group:
        issues.append("semantic per-group references are not supported")
    if (layer.citation is not None or layer.href is not None) and not layer.label:
        issues.append("semantic layer reference requires explicit label")
    try:
        rows = semantic_rows(columns, layer)
    except ValueError as error:
        return [*issues, str(error)]
    coordinates = (
        [layer.x] if layer.type in {"ecdf", "rug", "eventplot"} else [layer.x, layer.y]
    )
    names = coordinates + [
        getattr(config, r)
        for r in ("hue", "size", "style")
        if getattr(config, r) is not None
    ]
    for name in names:
        if not isinstance(name, str) or not name or name not in columns:
            issues.append(f"semantic column {name!r} must exist")
    literal_empty_swarm = (
        layer.type == "swarmplot"
        and isinstance(layer.x, str)
        and layer.x in columns
        and not columns[layer.x]
    )
    if (
        not rows
        and layer.type not in {"rug", "stem", "eventplot"}
        and not literal_empty_swarm
        and not allow_empty
        and not (layer.type in {"line", "lineplot"} and layer.line is not None)
        and not (panel.filters or panel.dropna)
    ):
        issues.append("no usable semantic rows after missing/selection exclusion")
    if not (stem or event) and len(rows) > MAX_ROWS:
        issues.append(f"semantic layers support at most {MAX_ROWS} usable rows")
    axes = (
        (response_axis, panel.x)
        if layer.orient == "h"
        and layer.type in {"line", "lineplot", "stripplot", "ecdf", "rug", "swarmplot"}
        else (panel.x, response_axis)
    )
    for coordinate_index, name in enumerate(() if stem or event else coordinates):
        axis = axes[coordinate_index]
        if layer.type in {"stripplot", "swarmplot"} and name == layer.x:
            continue  # Existing categorical validation owns category geometry.
        if axis is None:
            continue
        if not isinstance(name, str) or name not in columns:
            continue
        values = [columns[name][i] for i in rows]
        if coordinate_index == 0 and layer.type in {"line", "lineplot"}:
            from ._categorical import raw_x_is_categorical
            from ._line import categorical_predictor

            if categorical_predictor(layer) or (
                layer.type == "line"
                and layer.line is None
                and raw_x_is_categorical(values)
            ):
                if axis.scale != "linear":
                    issues.append("categorical line predictors require a linear axis")
                continue
        if any(not finite_number(v) for v in values):
            issues.append("semantic coordinates must be finite numeric, not bool/date")
        elif axis.scale == "log" and any(v <= 0 for v in values):
            issues.append("semantic log coordinates must be positive")
    for role in ("hue", "size", "style"):
        name = getattr(config, role)
        if not isinstance(name, str) or name not in columns:
            continue
        kind = "categorical" if role == "style" else getattr(config, f"{role}_kind")
        values = [columns[name][i] for i in rows]
        if kind == "numeric":
            if any(not finite_number(v) for v in values):
                issues.append(f"numeric {role} needs finite numbers, not bool")
        elif kind == "categorical":
            if any(not categorical(v) for v in values):
                issues.append(
                    f"categorical {role} needs nonempty strings or finite scalars"
                )
            else:
                selected = semantic_levels(columns, config, role, rows)
                if len(selected) > MAX_LEVELS or len({str(v) for v in selected}) != len(
                    selected
                ):
                    issues.append(
                        f"{role} levels exceed limit or have ambiguous labels"
                    )
                if (
                    role == "style"
                    and not (rug or event)
                    and isinstance(config.markers, (list, tuple))
                    and len(selected) > len(config.markers)
                ):
                    issues.append(
                        "style levels require enough distinct markers, no cycling"
                    )
                if (
                    (line or stem)
                    and role == "style"
                    and config.dashes is not None
                    and len(selected) > len(config.dashes)
                ):
                    issues.append("style levels require enough distinct dashes")
                if (
                    (rug or event)
                    and role == "style"
                    and len(selected) > len(config.dashes or ("-", "--", "-.", ":"))
                ):
                    issues.append(
                        f"{layer.type} style levels require enough distinct dashes"
                    )
    if layer.marker_size is not None and (
        not finite_number(layer.marker_size) or not 0 <= layer.marker_size <= 1000
    ):
        issues.append("marker_size must be finite in [0,1000]")
    if layer.marker is not None and (
        not isinstance(layer.marker, str) or layer.marker not in MARKERS
    ):
        issues.append("semantic marker must be a named filled marker")
    if line and not issues:
        roles = [
            getattr(config, r)
            for r in ("hue", "size", "style")
            if getattr(config, r) is not None
        ]
        curves = {tuple(category_key(columns[name][i]) for name in roles) for i in rows}
        if len(curves) > MAX_CURVES:
            issues.append(
                f"semantic curve layers support at most {MAX_CURVES} distinct curves"
            )
    return issues


def _scale_signature(value):
    """Typed structural identity; bool is not numeric1, tuple/list equivalent."""
    if isinstance(value, dict):
        return tuple((k, _scale_signature(v)) for k, v in sorted(value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_scale_signature(v) for v in value)
    if value is None:
        return ("null",)
    return category_key(value)


def shared_scale_domains(spec):
    """Pool deduplicated selected row ids in original table order, no effects."""
    from ._categorical import distribution_rows, swarm_semantic_issues
    from ._facet import panel_columns, panel_filter_issues, panel_rows
    from ._shared_guides import requested_scope_ids
    from ._temporal_data import prepare_temporal_layer

    domains = {}
    requested = requested_scope_ids(spec)
    for panel in spec.panels:
        if panel_filter_issues(spec.data.columns, panel):
            continue
        columns = panel_columns(spec.data.columns, panel)
        original_rows = (
            panel_rows(spec.data.columns, panel)
            if panel.filters or panel.dropna
            else None
        )
        for layer in panel.layers:
            config = layer.semantics
            if layer.type not in ROLE_LAYER_TYPES or not isinstance(
                config, SemanticSpec
            ):
                continue
            if config.scale_id is None:
                continue
            swarm = layer.type == "swarmplot"
            raw_regression_rows = None
            try:
                if layer.type == "regplot":
                    from ._regression_semantics import glyph_support

                    problems, raw_regression_rows = glyph_support(
                        spec.data.columns, layer, panel
                    )
                elif layer.type == "eventplot":
                    from ._lanes import plan_lanes

                    plan_lanes(columns, layer, panel)
                    # Role values stay raw, even when also used by the clock.
                    layer_columns = columns
                else:
                    layer_columns, layer, _observation_mask = prepare_temporal_layer(
                        columns, layer, panel
                    )
            except ValueError:
                continue
            if raw_regression_rows is None:
                problems = (
                    swarm_semantic_issues(layer_columns, layer, panel)
                    if swarm
                    else data_issues(
                        layer_columns,
                        layer,
                        panel,
                        allow_empty=(
                            isinstance(config.scale_id, str)
                            and config.scale_id in requested
                        ),
                    )
                )
            if problems:
                continue
            settings = config.to_dict()
            if config.hue is not None and config.hue_kind == "numeric":
                settings["cmap_kind"] = layer.cmap_kind
            for name in ("legend", "scale_id"):
                settings.pop(name)
            signature = _scale_signature(settings)
            domain = domains.setdefault(
                config.scale_id,
                {
                    "config": config,
                    "columns": spec.data.columns,
                    "signature": signature,
                    "rows": set(),
                    "conflict": False,
                    "offset": 0,
                    "colors": 0,
                    "colorbar_labels": set(),
                },
            )
            domain.setdefault("families", set()).add(layer.type)
            # Boxen glyph availability depends on the derived strict tails.
            domain["marker_required"] = domain.get("marker_required", False) or (
                layer.type
                not in {
                    "rug",
                    "eventplot",
                    "boxenplot",
                    "hist",
                    "countplot",
                    "barplot",
                    "kde",
                    "kde2d",
                    "hist2d",
                    "ecdf2d",
                }
                and not (layer.type == "violin" and layer.inner not in ("point", "box"))
            )
            if raw_regression_rows:
                domain.setdefault("regression_members", set()).add(id(layer))
            if (
                layer.colorbar
                and layer.type not in {"hist2d", "kde2d", "ecdf2d"}
                and (raw_regression_rows is None or raw_regression_rows)
            ):
                domain["colorbar_labels"].add(
                    layer.clabel if layer.clabel is not None else config.hue
                )
            if domain["signature"] != signature:
                domain["conflict"] = True
            if raw_regression_rows is not None:
                domain["rows"].update(raw_regression_rows)
                continue
            selected = (distribution_rows if swarm else semantic_rows)(
                layer_columns, layer
            )
            domain["rows"].update(
                selected
                if original_rows is None
                else [original_rows[i] for i in selected]
            )
            if layer.type in {"box", "violin", "boxenplot"}:
                domain.setdefault(layer.type + "_rows", set()).update(
                    selected
                    if original_rows is None
                    else [original_rows[i] for i in selected]
                )
            if swarm and config.size is not None:
                domain.setdefault("swarm_rows", set()).update(
                    selected
                    if original_rows is None
                    else [original_rows[i] for i in selected]
                )
    offset = 0
    for domain in domains.values():
        domain["rows"] = sorted(domain["rows"])
        domain["offset"] = offset
        config = domain["config"]
        if config.hue is not None and config.hue_kind == "categorical":
            try:
                domain["colors"] = len(
                    semantic_levels(
                        spec.data.columns,
                        config,
                        "hue",
                        domain["rows"],
                    )
                )
            except ValueError as exc:
                domain["invalid"] = str(exc)  # Reported by pure figure validation.
        offset += domain["colors"]
    return domains


def shared_scale_issues(spec):
    issues = []
    domains = shared_scale_domains(spec)
    for scale_id, domain in domains.items():
        prefix = f"semantic scale {scale_id!r}"
        if "invalid" in domain:
            issues.append(f"{prefix}: {domain['invalid']}")
        if domain["conflict"]:
            issues.append(f"{prefix}: members require identical mapping settings")
            continue
        if len(domain["colorbar_labels"]) > 1:
            issues.append(
                f"{prefix}: requested shared colorbars require identical labels"
            )
        if len(domain["rows"]) > MAX_ROWS:
            issues.append(f"{prefix}: pooled rows exceed {MAX_ROWS}")
            continue
        config = domain["config"]
        if domain.get("box_rows"):
            roles = [
                role
                for role in ("hue", "size", "style")
                if getattr(config, role) is not None
            ]
            tuples = {
                tuple(
                    category_key(domain["columns"][getattr(config, role)][row])
                    for role in roles
                )
                for row in domain["box_rows"]
            }
            if len(tuples) > MAX_CURVES:
                issues.append(f"{prefix}: pooled box role tuples exceed {MAX_CURVES}")
        if config.size is not None and domain.get("swarm_rows"):
            from ._categorical import swarm_size_mapping

            try:
                swarm_size_mapping(
                    domain["columns"],
                    config,
                    sorted(domain["swarm_rows"]),
                    domain=domain,
                )
            except (ValueError, OverflowError) as error:
                issues.append(f"{prefix}: {error}")
        for role in ("hue", "size", "style"):
            name = getattr(config, role)
            kind = "categorical" if role == "style" else getattr(config, f"{role}_kind")
            if name is None or kind != "categorical":
                continue
            try:
                selected = semantic_levels(
                    spec.data.columns, config, role, domain["rows"]
                )
            except ValueError as exc:
                issues.append(f"{prefix}: {exc}")
                continue
            if len(selected) > MAX_LEVELS or len({str(v) for v in selected}) != len(
                selected
            ):
                issues.append(
                    f"{prefix}: {role} pooled levels exceed limit/ambiguous labels"
                )
            if (
                role == "style"
                and domain["marker_required"]
                and len(selected) > len(config.markers)
            ):
                issues.append(f"{prefix}: pooled style needs enough distinct markers")
            if (
                role == "style"
                and config.dashes is not None
                and len(selected) > len(config.dashes)
            ):
                issues.append(f"{prefix}: pooled style needs enough distinct dashes")
            if (
                role == "style"
                and domain["families"]
                & {
                    "hist",
                    "countplot",
                    "rug",
                    "eventplot",
                    "box",
                    "violin",
                    "boxenplot",
                    "barplot",
                    "pointplot",
                    "kde",
                    "kde2d",
                    "hist2d",
                    "ecdf2d",
                }
                and len(selected) > len(config.dashes or ("-", "--", "-.", ":"))
            ):
                issues.append(
                    f"{prefix}: pooled rug style needs enough distinct dashes"
                )
    return issues


def semantic_partition(columns, config, rows):
    """One typed raw-role partition, retaining the selected source-row order."""
    roles = [
        role for role in ("hue", "size", "style") if getattr(config, role) is not None
    ]
    lookup, ids, curves = {}, [], []
    for row in rows:
        values = tuple(columns[getattr(config, role)][row] for role in roles)
        key = tuple(category_key(value) for value in values)
        if key not in lookup:
            lookup[key] = len(curves)
            curves.append(dict(zip(roles, values, strict=True)))
        ids.append(lookup[key])
    return ids, curves


def semantic_curve_input(columns, layer, *, project=None):
    """Private integer curve IDs, never caller data mutation or serialized columns.

    Every distinct raw hue/size/style tuple defines a curve, even if numeric
    bounds clip two tuple members to the same appearance. Callers compute their
    declared line estimate or full empirical curve without merging identities.
    """
    config = layer.semantics
    rows = semantic_rows(columns, layer)
    statistical = layer.type in {"barplot", "pointplot"}
    if statistical:
        from ._categorical import distribution_plan

        _categories, groups, cells = distribution_plan(columns, layer, rows=rows)
        indices = {group["key"]: index for index, group in enumerate(groups)}
        ids_by_row = {
            row: indices[cell["group"]] for cell in cells for row in cell["rows"]
        }
        observed = {cell["group"] for cell in cells}
        curves = [
            {
                **group["roles"],
                "_index": indices[group["key"]],
                "legacy_hue": group["hue"],
            }
            for group in groups
            if group["key"] in observed
        ]
        ids = [ids_by_row[row] for row in rows]
    else:
        curves = None
    if curves is None:
        ids, curves = semantic_partition(columns, config, rows)
        if layer.type in {"line", "lineplot"}:
            from ._line import line_rows

            for index, curve in enumerate(curves):
                curve["_index"] = index
            roles = [
                role
                for role in ("hue", "size", "style")
                if getattr(config, role) is not None
            ]
            lookup = {
                tuple(category_key(curve[role]) for role in roles): curve["_index"]
                for curve in curves
            }
            rows = line_rows(
                columns, layer, topology=True, barriers=layer.type == "line"
            )
            ids = []
            for row in rows:
                values = tuple(columns[getattr(config, role)][row] for role in roles)
                if any(is_missing(value) for value in values):
                    ids.append(-1)
                    continue
                key = tuple(category_key(value) for value in values)
                if key not in lookup:
                    lookup[key] = len(lookup)
                ids.append(lookup[key])
    names = columns if project is None else project
    data = {name: [columns[name][i] for i in rows] for name in names}
    name = "__mudplot_semantic_curve"
    while name in data:
        name += "_"
    data[name] = ids
    temporary = replace(
        layer,
        semantics=None,
        group=name,
        hue_order=list(range(len(groups))) if statistical else None,
        references=None,
        label=None,
    )
    return data, temporary, curves, rows


def categorical_fractions(values, selected):
    lookup = {category_key(value): i for i, value in enumerate(selected)}
    denominator = len(selected) - 1
    return [
        0.5 if denominator == 0 else lookup[category_key(value)] / denominator
        for value in values
    ]


def numeric_mapping(values, bounds=None):
    """Clipped linear fractions; direct differences retain narrow high-value bits."""
    values = [float(v) for v in values]
    lo, hi = (min(values), max(values)) if bounds is None else map(float, bounds)
    if lo == hi:
        return [0.5] * len(values), (lo, hi)
    span = hi - lo
    scale = max(abs(lo), abs(hi)) or 1.0
    result = []
    for value in values:
        if value <= lo:
            t = 0.0
        elif value >= hi:
            t = 1.0
        else:
            t = (
                (value - lo) / span
                if math.isfinite(span)
                else (value / scale - lo / scale) / (hi / scale - lo / scale)
            )
        if not math.isfinite(t):
            raise ValueError("semantic normalization must be finite")
        result.append(t)
    return result, (lo, hi)


def numeric_guides(bounds):
    lo, hi = bounds
    if lo == hi:
        return [lo]  # Halving a subnormal can underflow; constant has one guide.
    middle = max(lo, min(hi, lo * 0.5 + hi * 0.5))
    return list(dict.fromkeys((lo, middle, hi)))
