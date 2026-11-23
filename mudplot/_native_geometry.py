"""Finite native planar primitives: original units, gaps and pre-admission."""

from ._components import BODY_FIELDS, LINE_FIELDS, MARK_FIELDS, style_issues
from ._ecdf import finite_number
from ._facet import _ordered
from ._field_budget import MAX_FIELD_VERTICES
from ._semantics import category_key
from ._stat import is_missing
from ._temporal import (
    check_temporal_error_endpoint,
    temporal_coordinates,
    temporal_durations,
)
from ._temporal_data import temporal_options
from .spec import ErrorMagnitudesSpec, FillSpec, SegmentSpec, SpanSpec

SEGMENTS = {"hlines", "vlines"}
SPANS = {"hspan", "vspan"}
LITERALS = {"patch", "table", "text", "annotate"}
NATIVE_Y2_TYPES = SEGMENTS | SPANS | {"barh", "patch"}
EXTENDED = NATIVE_Y2_TYPES | {"table"}
SHAPE_FIELDS = {
    "segments": SEGMENTS,
    "span": SPANS,
    "error_magnitudes": {"errorbar"},
    "fill": {"band"},
    "bar_geometry": {"bar", "barh"},
    "pie_geometry": {"pie"},
    "patch": {"patch"},
    "table": {"table"},
    "annotation": {"text", "annotate"},
}
STYLE_FIELDS = {
    "line": MARK_FIELDS,
    "scatter": MARK_FIELDS - {"marker_edge_width"},
    "errorbar": MARK_FIELDS,
    "band": BODY_FIELDS,
    "patch": BODY_FIELDS,
    **dict.fromkeys(SEGMENTS, LINE_FIELDS),
    **dict.fromkeys(SPANS, BODY_FIELDS),
}


def extended_geometry(layer):
    return (
        layer.type in EXTENDED
        or any(getattr(layer, field) is not None for field in SHAPE_FIELDS)
        or (layer.type == "band" and layer.orient != "v")
        or (layer.type in {"band", "errorbar"} and layer.native_style is not None)
        or (
            layer.type in {"text", "annotate", "band"}
            and layer.path_effects is not None
        )
    )


def validate_style(layer):
    style = layer.native_style
    if style is None:
        return
    if layer.type not in STYLE_FIELDS:
        raise ValueError(f"native_style does not apply to {layer.type}")
    if layer.semantics is not None or layer.c is not None or layer.line is not None:
        raise ValueError(
            "native_style cannot override an existing mapped or configured mark"
        )
    issues = style_issues(style, STYLE_FIELDS[layer.type], "native_style", layer.type)
    if issues:
        raise ValueError("; ".join(issues))
    for name in (
        "color",
        "edge_color",
        "line_width",
        "line_style",
        "marker",
        "marker_size",
        "alpha",
    ):
        old = getattr(layer, name)
        if (
            getattr(style, name) is not None
            and old is not None
            and (name != "alpha" or old != 1)
        ):
            raise ValueError(f"native_style.{name} conflicts with layer {name}")
    if style.marker == "none" and layer.type == "scatter":
        raise ValueError("native scatter requires a visible marker geometry")


def check_coordinate(value, scale):
    if not finite_number(value):
        raise ValueError(
            "native geometry requires finite numeric or declared date coordinates"
        )
    value = float(value)
    if scale == "log" and value <= 0:
        raise ValueError("native geometry endpoints must be positive on log axes")
    if scale == "logit" and not 0 < value < 1:
        raise ValueError(
            "native geometry endpoints must be strictly inside (0,1) on logit axes"
        )
    return value


def coordinates(values, axis):
    if axis.temporal is not None:
        values = temporal_coordinates(values, **temporal_options(axis.temporal))
    return [
        None if value is None else check_coordinate(value, axis.scale)
        for value in values
    ]


def _defined_column(columns, name):
    if not isinstance(name, str) or not name or name not in columns:
        raise ValueError("native geometry column must name existing source data")
    return columns[name]


def cohorts(columns, layer, ids):
    if layer.group is None:
        if layer.hue_order is not None:
            raise ValueError("hue_order requires a raw group")
        return [(None, ids)]
    raw = _defined_column(columns, layer.group)
    groups = _ordered((raw[i] for i in ids if not is_missing(raw[i])), layer.hue_order)
    return [
        (
            key,
            [
                i
                for i in ids
                if not is_missing(raw[i]) and category_key(raw[i]) == category_key(key)
            ],
        )
        for key in groups
    ]


def _value_axes(layer, panel):
    if panel.projection != "2d" or layer.axis not in ("y", "y2"):
        raise ValueError("native planar geometry requires Cartesian x and y/y2")
    y = panel.y2 if layer.axis == "y2" else panel.y
    if y is None:
        raise ValueError("native geometry target y2 is not enabled")
    return panel.x, y


def _durations(raw, axis):
    values = []
    for value in raw:
        if not finite_number(value) or value < 0:
            raise ValueError(
                "native error magnitudes must be finite nonnegative numbers"
            )
        values.append(value)
    if axis.temporal is None:
        return [float(value) for value in values]
    return temporal_durations(values, unit=axis.temporal.unit or "day")


def _error_columns(layer, cfg):
    if cfg is not None and not isinstance(cfg, ErrorMagnitudesSpec):
        raise ValueError("error_magnitudes requires ErrorMagnitudesSpec")
    if cfg is not None and cfg.x is None and cfg.y is None:
        raise ValueError("provide at least one lower/upper error-magnitude pair")
    if layer.y_lower is not None or layer.y_upper is not None:
        raise ValueError(
            "use legacy absolute y endpoints or native magnitude options, not both"
        )
    names = []
    for role in ("x", "y"):
        pair = None if cfg is None else getattr(cfg, role)
        sym = getattr(layer, role + "err")
        if pair is not None:
            if not isinstance(pair, (tuple, list)) or len(pair) != 2 or sym is not None:
                raise ValueError(
                    f"{role} needs one two-column lower/upper magnitude or "
                    "symmetric error"
                )
            names.append(tuple(pair))
        else:
            names.append(None if sym is None else (sym, sym))
    return names


def _error_data(columns, layer, axes, groups):
    names = _error_columns(layer, layer.error_magnitudes)
    xc, yc = (_defined_column(columns, key) for key in (layer.x, layer.y))
    err = [
        None if p is None else tuple(_defined_column(columns, key) for key in p)
        for p in names
    ]
    needs = [xc, yc, *(series for pair in err if pair is not None for series in pair)]
    result = []
    for key, group in groups:
        ids = [i for i in group if all(not is_missing(series[i]) for series in needs)]
        xs, ys = (
            coordinates([vals[i] for i in ids], axis)
            for vals, axis in zip((xc, yc), axes, strict=True)
        )
        native_errors = []
        for vals, pair, axis in zip((xs, ys), err, axes, strict=True):
            if pair is None:
                native_errors.append(None)
                continue
            magnitudes = [_durations((series[i] for i in ids), axis) for series in pair]
            for center, low, high in zip(vals, *magnitudes, strict=True):
                lo, hi = center - low, center + high
                check_coordinate(lo, axis.scale)
                check_coordinate(hi, axis.scale)
                if axis.temporal is not None:
                    check_temporal_error_endpoint(center, low, lo, subtract=True)
                    check_temporal_error_endpoint(center, high, hi, subtract=False)
                if (low and lo == center) or (high and hi == center):
                    raise ValueError(
                        "error endpoint collapses at native coordinate precision"
                    )
            native_errors.append(magnitudes)
        result.append((key, xs, ys, native_errors))
    return result


def _band_data(columns, layer, axes, groups):
    cfg = layer.fill or FillSpec()
    if not isinstance(cfg, FillSpec) or type(cfg.interpolate) is not bool:
        raise ValueError("band fill needs a strict FillSpec")
    if cfg.step is not None and cfg.step not in ("pre", "post", "mid"):
        raise ValueError("fill step must be pre, post or mid")
    if cfg.interpolate and cfg.where is None:
        raise ValueError("fill interpolation requires a Boolean where column")
    along, lower, upper = (
        _defined_column(columns, key) for key in (layer.x, layer.y2, layer.y)
    )
    mask = None if cfg.where is None else _defined_column(columns, cfg.where)
    order_axes = axes[::-1] if layer.orient == "h" else axes
    result = []
    for key, ids in groups:
        usable = [all(not is_missing(s[i]) for s in (along, lower, upper)) for i in ids]
        if mask is not None and any(
            type(mask[i]) is not bool and not is_missing(mask[i]) for i in ids
        ):
            raise ValueError("fill where values must be Boolean or missing")
        values = [
            coordinates(
                [s[i] if ok else None for i, ok in zip(ids, usable, strict=True)], axis
            )
            for s, axis in zip(
                (along, lower, upper),
                (order_axes[0], order_axes[1], order_axes[1]),
                strict=True,
            )
        ]
        where = [
            ok and (mask is None or mask[i] is True)
            for i, ok in zip(ids, usable, strict=True)
        ]
        result.append((key, values, where))
    return result


def value_axes(layer):
    """Physical data dimensions, excluding fraction-only decorations."""
    if layer.type == "vspan":
        return ("x",)
    if layer.type == "hspan":
        return (layer.axis,)
    if layer.type in {"table", "text", "annotate", "pie"} or (
        layer.type == "patch" and layer.patch.coordinates != "data"
    ):
        return ()
    return ("x", layer.axis)


def prospective_size(columns, layer):
    kind = layer.type
    if kind in SEGMENTS:
        return (
            len(layer.segments.at)
            if isinstance(layer.segments, SegmentSpec)
            and isinstance(layer.segments.at, (list, tuple))
            else 0
        )
    if kind in SPANS:
        return 1
    if kind in LITERALS:
        from ._native_annotations import literal_size

        return literal_size(layer)
    return len(next(iter(columns.values()), ()))


def reserve(plan, columns, layer):
    n = prospective_size(columns, layer)
    group = 1 if layer.group is None else min(n, 64)
    vertices = n * {
        "band": 32,
        "errorbar": 12,
        "pie": 160,
        "bar": 5,
        "barh": 5,
    }.get(layer.type, 5)
    if layer.type == "patch":
        vertices = max(vertices, 26)
    passes = 1 if layer.path_effects is None else 3
    vertices *= passes
    plan.grid_vertices += vertices
    if plan.grid_vertices > MAX_FIELD_VERTICES:
        raise ValueError("native geometry exceeds 2000000 prospective path vertices")
    decorations = (
        n * 1800
        if layer.type in {"bar", "barh", "pie", "table", "text", "annotate"}
        else 0
    )
    plan.admit(
        (48 + group) * n * passes, 256 * vertices + 4096 * group + decorations, 320 * n
    )


def prepare(columns, layer, panel, selected=None):
    validate_style(layer)
    if layer.path_effects is not None:
        from ._native_annotations import effects_issues

        effects_issues(layer)
    for field, kinds in SHAPE_FIELDS.items():
        if getattr(layer, field) is not None and layer.type not in kinds:
            raise ValueError(f"{field} does not apply to {layer.type}")
    if not extended_geometry(layer):
        return None
    if layer.transforms is not None or layer.semantics is not None:
        raise ValueError(
            "native primitive geometry does not alter statistical roles or transforms"
        )
    kind = layer.type
    axes = _value_axes(layer, panel)
    if kind in LITERALS:
        from ._native_annotations import prepare_literal

        return prepare_literal(layer, axes)
    if kind in SEGMENTS:
        cfg = layer.segments
        if (
            not isinstance(cfg, SegmentSpec)
            or any(
                not isinstance(v, (list, tuple)) for v in (cfg.at, cfg.start, cfg.end)
            )
            or not 1 <= len(cfg.at) == len(cfg.start) == len(cfg.end) <= 10_000
        ):
            raise ValueError("finite segments need 1..10000 equal coordinate arrays")
        along, interval = axes if kind == "vlines" else axes[::-1]
        values = tuple(
            coordinates(v, a)
            for v, a in zip(
                (cfg.at, cfg.start, cfg.end), (along, interval, interval), strict=True
            )
        )
        if any(v is None for seq in values for v in seq):
            raise ValueError("finite literal segments cannot contain missing endpoints")
        return values
    if kind in SPANS:
        cfg = layer.span
        if (
            not isinstance(cfg, SpanSpec)
            or not isinstance(cfg.fractions, (list, tuple))
            or len(cfg.fractions) != 2
            or not all(finite_number(v) for v in cfg.fractions)
            or not 0 <= cfg.fractions[0] < cfg.fractions[1] <= 1
        ):
            raise ValueError(
                "span needs an increasing pair of orthogonal axes fractions in [0,1]"
            )
        axis = axes[0] if kind == "vspan" else axes[1]
        lo, hi = coordinates((cfg.start, cfg.end), axis)
        if lo is None or hi is None or lo >= hi:
            raise ValueError("span native endpoints must be finite and increasing")
        return lo, hi, *cfg.fractions
    if layer.orient not in ("v", "h") or (kind == "errorbar" and layer.orient != "v"):
        raise ValueError("native bands accept v/h; error magnitudes use actual x/y")
    n = prospective_size(columns, layer)
    if n > 10_000:
        raise ValueError(
            "extended native series geometry supports at most 10000 source rows"
        )
    ids = range(n) if selected is None else selected
    if kind in {"bar", "barh", "pie"}:
        from ._native_bars import bars, pie

        return (pie if kind == "pie" else bars)(columns, layer, panel, ids)
    groups = cohorts(columns, layer, ids)
    if len(groups) > 64:
        raise ValueError("extended native geometry supports at most 64 raw groups")
    return (_error_data if kind == "errorbar" else _band_data)(
        columns, layer, axes, groups
    )
