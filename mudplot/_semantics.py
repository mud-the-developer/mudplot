"""Dependency-free, opt-in scatter role contracts and stable linear mapping."""

from __future__ import annotations

import math
from dataclasses import replace

from ._ecdf import finite_number
from ._stat import is_missing, stat_config
from .spec import SemanticSpec, StatSpec

MARKERS = ("o", "s", "D", "^", "v", "P", "X", "d", "p", "h", "8", "*")
MAX_LEVELS = 64
MAX_ROWS = 10000
MAX_CURVES = 256


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


def option_issues(config):
    issues = []
    if not isinstance(config, SemanticSpec):
        return ["semantics must be SemanticSpec or None"]
    if config.scale_id is not None and (
        not isinstance(config.scale_id, str)
        or not config.scale_id.strip()
        or len(config.scale_id) > 64
        or any(ord(c) < 32 for c in config.scale_id)
    ):
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


def semantic_rows(columns, layer):
    config = layer.semantics
    if not isinstance(config, SemanticSpec):
        return []
    names = [layer.x, layer.y] + [
        getattr(config, r)
        for r in ("hue", "size", "style")
        if getattr(config, r) is not None
    ]
    weights = None
    if layer.type == "lineplot":
        if layer.stat is not None and not isinstance(layer.stat, StatSpec):
            return []
        stat = stat_config(layer)
        weights = stat.weights
        names += [name for name in (stat.weights, stat.units) if name is not None]
    if not all(
        isinstance(name, str)
        and name in columns
        and isinstance(columns[name], (list, tuple))
        for name in names
    ):
        return []
    if len({len(columns[name]) for name in names}) != 1:
        return []
    selections = []
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
        if weights is not None and columns[weights][i] == 0:
            continue
        if any(
            name is not None
            and categorical(columns[name][i])
            and category_key(columns[name][i]) not in selected
            for name, selected in selections
        ):
            continue
        rows.append(i)
    return rows


def semantic_levels(columns, config, role, rows):
    name = getattr(config, role)
    if name is None:
        return [None]
    order = getattr(config, f"{role}_order")
    return list(order) if order is not None else levels(columns[name][i] for i in rows)


def data_issues(columns, layer, panel):
    config = layer.semantics
    issues = option_issues(config)
    if not isinstance(config, SemanticSpec) or issues:
        return issues
    if layer.group is not None or layer.c is not None:
        issues.append("semantics cannot combine with legacy group/c")
    line = layer.type == "lineplot"
    if layer.axis != "y" or panel.projection != "2d":
        issues.append("semantic layers support primary Cartesian2D only")
    if layer.hue_order is not None:
        issues.append("use semantic hue_order, not legacy layer hue_order")
    if not line and config.dashes is not None:
        issues.append("semantic dashes only apply to lineplot")
    if line and config.dashes is not None and layer.line_style is not None:
        issues.append("line_style cannot override mapped dashes")
    if layer.colorbar or layer.clabel is not None:
        issues.append(
            "semantic mapping uses legend guides; no colorbar/clabel in subset"
        )
    if config.hue is not None and layer.color is not None:
        issues.append("color cannot override a mapped hue")
    size_override = layer.line_width if line else layer.marker_size
    if config.size is not None and size_override is not None:
        issues.append("line_width/marker_size cannot override mapped size")
    if config.style is not None and layer.marker is not None:
        issues.append("marker cannot override mapped style")
    if (not line and layer.line_width is not None) or layer.edge_color is not None:
        issues.append("semantic outline overrides are not supported")
    if config.hue_kind != "numeric" and layer.cmap_kind != "sequential":
        issues.append("cmap_kind only applies to numeric hue")
    if config.hue_kind == "numeric" and (
        not isinstance(layer.cmap_kind, str)
        or layer.cmap_kind not in ("sequential", "diverging")
    ):
        issues.append("numeric hue cmap_kind must be sequential or diverging")
    if layer.references is not None:
        issues.append("semantic per-group references are not supported")
    if (layer.citation is not None or layer.href is not None) and not layer.label:
        issues.append("semantic layer reference requires explicit label")
    rows = semantic_rows(columns, layer)
    names = [layer.x, layer.y] + [
        getattr(config, r)
        for r in ("hue", "size", "style")
        if getattr(config, r) is not None
    ]
    for name in names:
        if not isinstance(name, str) or not name or name not in columns:
            issues.append(f"semantic column {name!r} must exist")
    if not rows and not (panel.filters or panel.dropna):
        issues.append("no usable semantic rows after missing/selection exclusion")
    if len(rows) > MAX_ROWS:
        issues.append(f"semantic layers support at most {MAX_ROWS} usable rows")
    axes = (panel.y, panel.x) if line and layer.orient == "h" else (panel.x, panel.y)
    for name, axis in zip((layer.x, layer.y), axes, strict=True):
        if not isinstance(name, str) or name not in columns:
            continue
        values = [columns[name][i] for i in rows]
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
                    and isinstance(config.markers, (list, tuple))
                    and len(selected) > len(config.markers)
                ):
                    issues.append(
                        "style levels require enough distinct markers, no cycling"
                    )
                if (
                    line
                    and role == "style"
                    and config.dashes is not None
                    and len(selected) > len(config.dashes)
                ):
                    issues.append("style levels require enough distinct dashes")
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
                f"semantic lineplot supports at most {MAX_CURVES} distinct curves"
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
    from ._facet import panel_columns, panel_filter_issues, panel_rows

    domains = {}
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
            if layer.type not in ("scatter", "lineplot") or not isinstance(
                config, SemanticSpec
            ):
                continue
            if config.scale_id is None or data_issues(columns, layer, panel):
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
                },
            )
            if domain["signature"] != signature:
                domain["conflict"] = True
            selected = semantic_rows(columns, layer)
            domain["rows"].update(
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
        if len(domain["rows"]) > MAX_ROWS:
            issues.append(f"{prefix}: pooled rows exceed {MAX_ROWS}")
        config = domain["config"]
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
            if role == "style" and len(selected) > len(config.markers):
                issues.append(f"{prefix}: pooled style needs enough distinct markers")
            if (
                role == "style"
                and config.dashes is not None
                and len(selected) > len(config.dashes)
            ):
                issues.append(f"{prefix}: pooled style needs enough distinct dashes")
    return issues


def line_semantic_input(columns, layer):
    """Private integer curve IDs, never caller data mutation or serialized columns.

    Every distinct raw hue/size/style tuple defines a curve, even if numeric
    bounds clip two tuple members to the same appearance. Statistics remain
    per observed predictor cell and semantic curve, not across whole paths.
    """
    config = layer.semantics
    rows = semantic_rows(columns, layer)
    roles = [r for r in ("hue", "size", "style") if getattr(config, r) is not None]
    lookup = {}
    curves = []
    ids = []
    for i in rows:
        values = tuple(columns[getattr(config, role)][i] for role in roles)
        key = tuple(category_key(v) for v in values)
        if key not in lookup:
            lookup[key] = len(curves)
            curves.append(dict(zip(roles, values, strict=True)))
        ids.append(lookup[key])
    data = {name: [column[i] for i in rows] for name, column in columns.items()}
    name = "__mudplot_semantic_curve"
    while name in data:
        name += "_"
    data[name] = ids
    temporary = replace(
        layer, semantics=None, group=name, hue_order=None, references=None, label=None
    )
    return data, temporary, curves


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
