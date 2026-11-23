"""N12 pure contracts: no numerical or renderer dependency in specs/validation."""

from __future__ import annotations

import math
from dataclasses import fields, replace
from itertools import pairwise

from ._ecdf import finite_number
from ._stat import is_missing
from .spec import (
    AxisSpec,
    AxisTransformSpec,
    FormatterSpec,
    LocatorSpec,
    ScaleOptionsSpec,
    SecondaryAxisSpec,
    TickSpec,
)

SCALES = ("linear", "log", "symlog", "asinh", "logit")
NEW_SCALES = ("symlog", "asinh", "logit")
MAX_TICKS_PER_LEVEL = 512
MAX_FIGURE_CONFIGURED_TICKS = 16_384
MAX_FORMATTED_TICK_CHARACTERS = 512
LOCATORS = (
    "auto",
    "none",
    "fixed",
    "multiple",
    "max_n",
    "linear",
    "auto_minor",
    "log",
    "symlog",
    "asinh",
    "logit",
    "calendar",
)
FORMATTERS = (
    "auto",
    "none",
    "fixed",
    "scalar",
    "number",
    "percent",
    "engineering",
    "log",
    "logit",
    "date",
    "concise_date",
)
DATE_PATTERNS = ("iso_date", "iso_datetime", "time", "month", "year", "subsecond")
TRANSFORMS = (
    "affine",
    "celsius_fahrenheit",
    "radians_degrees",
    "seconds_milliseconds",
    "hertz_period",
    "reciprocal",
    "unix_seconds",
)
RAW_NONLINEAR_TYPES = frozenset(
    {
        "line",
        "scatter",
        "bar",
        "stem",
        "stairs",
        "errorbar",
        "band",
        "eventplot",
        "broken_barh",
        "hline",
        "vline",
        "text",
        "annotate",
        "rug",
    }
)


def _integer(value, lo, hi):
    return type(value) is int and lo <= value <= hi


def _text(value, maximum, *, empty=True):
    return (
        isinstance(value, str)
        and (empty or bool(value.strip()))
        and len(value) <= maximum
        and not any(ord(c) < 32 and c not in "\n\t" for c in value)
    )


def _unused(config, allowed):
    return [
        f"{f.name} is not used by {getattr(config, 'kind', 'this scale')}"
        for f in fields(config)
        if f.name not in allowed and getattr(config, f.name) is not None
    ]


def fixed_values(values):
    if (
        not isinstance(values, (list, tuple))
        or len(values) > MAX_TICKS_PER_LEVEL
        or any(not finite_number(v) for v in values)
    ):
        raise ValueError(
            f"fixed positions require at most {MAX_TICKS_PER_LEVEL} "
            "finite nonbool numbers"
        )
    result = [float(v) for v in values]
    if any(a >= b for a, b in pairwise(result)):
        raise ValueError(
            "fixed positions must be strictly increasing and distinct "
            "after float conversion"
        )
    return result


def scale_kwargs(axis):
    options = {
        "symlog": {"base": 10, "linthresh": 2, "linscale": 1},
        "asinh": {"base": 10, "linear_width": 1},
        "logit": {"nonpositive": "mask"},
    }.get(axis.scale, {}).copy()
    c = axis.scale_options
    if c is not None:
        options.update(
            (f.name, getattr(c, f.name))
            for f in fields(c)
            if getattr(c, f.name) is not None
        )
    return options


def scale_issues(axis):
    if axis.scale not in SCALES:
        return [f"scale must be one of {SCALES}"]
    c = axis.scale_options
    if c is None:
        return []
    if not isinstance(c, ScaleOptionsSpec):
        return ["scale_options must be ScaleOptionsSpec or None"]
    allowed = {
        "linear": set(),
        "log": {"base", "subs"},
        "symlog": {"base", "subs", "linthresh", "linscale"},
        "asinh": {"base", "subs", "linear_width"},
        "logit": set(),
    }[axis.scale]
    issues = _unused(c, allowed)
    if c.base is not None and (not finite_number(c.base) or c.base <= 1):
        issues.append("scale base must be finite nonbool >1")
    if (
        axis.scale == "asinh"
        and c.base is not None
        and (
            not finite_number(c.base)
            or c.base != int(c.base)
            or not 2 <= c.base <= 1024
        )
    ):
        issues.append("asinh tick-rounding base must be an integer in [2,1024]")
    for name in ("linthresh", "linscale", "linear_width"):
        value = getattr(c, name)
        if value is not None and (not finite_number(value) or value <= 0):
            issues.append(f"{name} must be positive finite nonbool")
    if c.subs is not None:
        issues.extend(subs_issues(c.subs, c.base if finite_number(c.base) else 10))
    return issues


def subs_issues(values, base):
    if (
        not isinstance(values, (list, tuple))
        or not 1 <= len(values) <= 32
        or any(not finite_number(v) or not 0 < v < base for v in values)
    ):
        return ["subs need 1..32 finite positive values below the axis base"]
    if any(a >= b for a, b in pairwise(values)):
        return ["subs must be strictly increasing"]
    return []


def tick_issues(config, axis, which):
    if config is None:
        return []
    if not isinstance(config, TickSpec):
        return ["ticks must be TickSpec or None"]
    issues = []
    if config.rotation is not None and (
        not finite_number(config.rotation) or not -360 <= config.rotation <= 360
    ):
        issues.append("tick rotation must be finite nonbool degrees in [-360,360]")
    loc = config.locator
    if loc is not None:
        if not isinstance(loc, LocatorSpec):
            issues.append("locator must be LocatorSpec")
        elif loc.kind not in LOCATORS:
            issues.append(f"locator kind must be one of {LOCATORS}")
        else:
            allowed = {
                "auto": set(),
                "none": set(),
                "fixed": {"values"},
                "multiple": {"step", "offset"},
                "max_n": {"nbins", "integer", "prune"},
                "linear": {"count"},
                "auto_minor": {"subdivisions"},
                "log": {"subs"},
                "symlog": {"subs"},
                "asinh": {"count", "subs"},
                "logit": set(),
                "calendar": {"unit", "interval", "weekday", "count"},
            }[loc.kind] | {"kind"}
            issues.extend(_unused(loc, allowed))
            if loc.kind == "fixed":
                try:
                    fixed_values(loc.values)
                except (ValueError, OverflowError) as error:
                    issues.append(str(error))
            if loc.kind == "multiple" and (
                loc.step is None or not finite_number(loc.step) or loc.step <= 0
            ):
                issues.append("multiple locator step must be positive finite nonbool")
            if loc.offset is not None and not finite_number(loc.offset):
                issues.append("multiple offset must be finite nonbool")
            for name, lo, hi in (
                ("nbins", 1, 128),
                ("count", 2, 128),
                ("subdivisions", 2, 32),
                ("interval", 1, 1_000_000),
                ("weekday", 0, 6),
            ):
                value = getattr(loc, name)
                if value is not None and not _integer(value, lo, hi):
                    issues.append(f"locator {name} must be integer in [{lo},{hi}]")
            if loc.integer is not None and type(loc.integer) is not bool:
                issues.append("max_n integer must be bool")
            if loc.prune is not None and loc.prune not in (
                "none",
                "lower",
                "upper",
                "both",
            ):
                issues.append("max_n prune must be none/lower/upper/both")
            if loc.kind == "auto_minor" and (
                which != "minor" or axis.scale != "linear" or axis.temporal is not None
            ):
                issues.append("auto_minor requires linear numeric minor ticks")
            if loc.kind in ("multiple", "max_n", "linear") and (
                axis.scale != "linear" or axis.temporal is not None
            ):
                issues.append(f"{loc.kind} requires a linear numeric axis")
            if (
                loc.kind in ("log", "symlog", "asinh", "logit")
                and axis.scale != loc.kind
            ):
                issues.append(f"{loc.kind} locator requires matching scale")
            if loc.subs is not None:
                base = (
                    10
                    if axis.scale_options is None or axis.scale_options.base is None
                    else axis.scale_options.base
                )
                issues.extend(
                    subs_issues(loc.subs, base)
                    if finite_number(base)
                    else ["invalid axis base"]
                )
            if loc.kind == "calendar":
                unit = loc.unit or "auto"
                if axis.temporal is None:
                    issues.append(
                        "calendar locator requires an explicit TemporalSpec clock"
                    )
                if unit not in (
                    "auto",
                    "year",
                    "month",
                    "week",
                    "day",
                    "hour",
                    "minute",
                    "second",
                    "microsecond",
                ):
                    issues.append("invalid calendar tick unit")
                if loc.weekday is not None and unit != "week":
                    issues.append("calendar weekday is only used by week")
                if loc.interval is not None and unit == "auto":
                    issues.append("calendar interval is not used by auto")
                if loc.count is not None and unit != "auto":
                    issues.append("calendar count is only used by auto")
    fmt = config.formatter
    if fmt is not None:
        if not isinstance(fmt, FormatterSpec):
            return [*issues, "formatter must be FormatterSpec"]
        if fmt.kind not in FORMATTERS:
            return [*issues, f"formatter kind must be one of {FORMATTERS}"]
        allowed = {
            "auto": set(),
            "none": set(),
            "fixed": {"labels"},
            "scalar": {"scientific", "use_offset", "powerlimits", "mathtext"},
            "number": {"notation", "precision", "prefix", "suffix"},
            "percent": {"xmax", "decimals"},
            "engineering": {"unit", "precision", "separator"},
            "log": {"style", "label_only_base"},
            "logit": {"half", "use_overline"},
            "date": {"pattern"},
            "concise_date": set(),
        }[fmt.kind] | {"kind"}
        issues.extend(_unused(fmt, allowed))
        for name in (
            "scientific",
            "use_offset",
            "mathtext",
            "label_only_base",
            "use_overline",
        ):
            value = getattr(fmt, name)
            if value is not None and type(value) is not bool:
                issues.append(f"formatter {name} must be bool")
        if fmt.powerlimits is not None and (
            not isinstance(fmt.powerlimits, (list, tuple))
            or len(fmt.powerlimits) != 2
            or any(not _integer(v, -12, 12) for v in fmt.powerlimits)
            or fmt.powerlimits[0] > fmt.powerlimits[1]
        ):
            issues.append("scalar powerlimits need two ordered integers in [-12,12]")
        for name in ("precision", "decimals"):
            value = getattr(fmt, name)
            if value is not None and not _integer(value, 0, 12):
                issues.append(f"{name} must be integer in [0,12]")
        if fmt.notation is not None and fmt.notation not in (
            "fixed",
            "scientific",
            "general",
        ):
            issues.append("number notation must be fixed/scientific/general")
        if (
            fmt.kind == "number"
            and (fmt.notation or "general") == "general"
            and fmt.precision == 0
        ):
            issues.append("general notation needs at least one significant digit")
        for name in ("prefix", "suffix", "unit"):
            value = getattr(fmt, name)
            if value is not None and not _text(value, 32):
                issues.append(f"formatter {name} must be literal text <=32 characters")
        if fmt.xmax is not None and (not finite_number(fmt.xmax) or fmt.xmax <= 0):
            issues.append("percent xmax must be positive finite nonbool")
        if fmt.separator is not None and fmt.separator not in (
            "",
            " ",
            "\u2009",
            "\u202f",
        ):
            issues.append(
                "engineering separator must be "
                "empty/space/thin-space/narrow-no-break-space"
            )
        if fmt.style is not None and fmt.style not in (
            "plain",
            "exponent",
            "mathtext",
            "scientific",
        ):
            issues.append("log style must be plain/exponent/mathtext/scientific")
        if fmt.half is not None and fmt.half not in ("fraction", "decimal"):
            issues.append("logit half must be fraction or decimal")
        if fmt.kind in ("date", "concise_date") and axis.temporal is None:
            issues.append("date formatting requires an explicit TemporalSpec clock")
        if fmt.pattern is not None and fmt.pattern not in DATE_PATTERNS:
            issues.append(f"date pattern must be one of {DATE_PATTERNS}")
        if (
            fmt.kind == "concise_date"
            and isinstance(loc, LocatorSpec)
            and loc.kind not in ("auto", "calendar", "fixed")
        ):
            issues.append("concise_date requires a calendar or fixed temporal locator")
        if fmt.kind == "log" and axis.scale not in ("log", "symlog", "asinh"):
            issues.append("log formatter requires log/symlog/asinh scale")
        if fmt.kind == "logit" and axis.scale != "logit":
            issues.append("logit formatter requires logit scale")
        if fmt.kind == "fixed":
            if not isinstance(loc, LocatorSpec) or loc.kind != "fixed":
                issues.append("fixed labels require an explicit fixed locator")
            if (
                not isinstance(fmt.labels, (list, tuple))
                or any(not _text(s, 128) for s in fmt.labels)
                or len(fmt.labels) > MAX_TICKS_PER_LEVEL
            ):
                issues.append(
                    "fixed labels need at most512 literal strings <=128 characters"
                )
            elif (
                isinstance(loc, LocatorSpec)
                and isinstance(loc.values, (list, tuple))
                and len(fmt.labels) != len(loc.values)
            ):
                issues.append("fixed label count must match fixed positions")
    return issues


def axis_issues(axis):
    issues = scale_issues(axis)
    if axis.temporal is not None and axis.scale != "linear":
        issues.append("temporal clocks require a linear scale")
    for which in ("major", "minor"):
        issues.extend(tick_issues(getattr(axis, which + "_ticks"), axis, which))
    if (
        configured(axis)
        and axis.limits is not None
        and isinstance(axis.limits, (list, tuple))
        and len(axis.limits) == 2
        and all(finite_number(v) for v in axis.limits)
    ):
        if float(axis.limits[0]) == float(axis.limits[1]):
            issues.append("configured view limits collapse after float conversion")
        if axis.scale == "logit" and any(not 0 < v < 1 for v in axis.limits):
            issues.append("logit view limits must lie strictly inside (0,1)")
    return issues


def configured(axis):
    return axis.scale in NEW_SCALES or any(
        getattr(axis, name) is not None
        for name in ("scale_options", "major_ticks", "minor_ticks")
    )


def effective_panels(spec):
    from ._layout import shared_groups

    panels = list(spec.panels)
    issues = []
    for axis_name in ("x", "y"):
        for members in shared_groups(spec, axis_name):
            for name in ("scale_options", "major_ticks", "minor_ticks"):
                explicit = [
                    getattr(getattr(spec.panels[i], axis_name), name)
                    for i in members
                    if getattr(getattr(spec.panels[i], axis_name), name) is not None
                ]
                if not explicit:
                    continue
                first = explicit[0]
                try:
                    conflict = any(value != first for value in explicit[1:])
                except (ValueError, TypeError):
                    conflict = True
                if conflict:
                    issues.append(
                        f"shared {axis_name} axes have conflicting explicit {name}"
                    )
                    continue
                for i in members:
                    old = getattr(panels[i], axis_name)
                    if getattr(old, name) is None:
                        panels[i] = replace(
                            panels[i], **{axis_name: replace(old, **{name: first})}
                        )
    return panels, issues


def transform_issues(config):
    if not isinstance(config, AxisTransformSpec):
        return ["transform must be AxisTransformSpec"]
    if config.kind not in TRANSFORMS:
        return [f"transform kind must be one of {TRANSFORMS}"]
    issues = []
    allowed = {"kind", "reverse"} | (
        {"factor", "offset", "source_unit", "target_unit"}
        if config.kind == "affine"
        else {"factor", "source_unit", "target_unit"}
        if config.kind == "reciprocal"
        else set()
    )
    issues.extend(_unused(config, allowed))
    if type(config.reverse) is not bool:
        issues.append("transform reverse must be bool")
    if config.kind == "unix_seconds" and config.reverse:
        issues.append(
            "unix_seconds requires a temporal canonical-day parent, not reverse mode"
        )
    if config.kind in ("affine", "reciprocal"):
        if (
            config.factor is None
            or not finite_number(config.factor)
            or config.factor == 0
            or (config.kind == "reciprocal" and config.factor < 0)
        ):
            issues.append(
                "transform factor must be finite nonzero (positive for reciprocal)"
            )
        for name in ("source_unit", "target_unit"):
            if not _text(getattr(config, name), 64, empty=False):
                issues.append(
                    f"{name} must explicitly declare nonempty units <=64 characters"
                )
    if config.offset is not None and not finite_number(config.offset):
        issues.append("affine offset must be finite nonbool")
    return issues


def transform_units(config):
    units = {
        "celsius_fahrenheit": ("°C", "°F"),
        "radians_degrees": ("rad", "degree"),
        "seconds_milliseconds": ("s", "ms"),
        "hertz_period": ("Hz", "s"),
        "unix_seconds": ("UTC day since 1970", "Unix seconds (UTC)"),
    }
    pair = (
        (config.source_unit, config.target_unit)
        if config.kind in ("affine", "reciprocal")
        else units[config.kind]
    )
    return pair[::-1] if config.reverse else pair


def affine_parameters(config):
    """Closed registry shared by scalar checks and native array transforms."""
    if config.kind == "affine":
        return float(config.factor), float(config.offset or 0)
    return {
        "celsius_fahrenheit": (9 / 5, 32),
        "radians_degrees": (180 / math.pi, 0),
        "seconds_milliseconds": (1000, 0),
        "unix_seconds": (86400, 0),
    }[config.kind]


def transform_scalar(value, config, *, inverse=False):
    inverse = inverse != config.reverse
    if config.kind in ("hertz_period", "reciprocal"):
        if not value > 0:
            raise ValueError("reciprocal secondary view must be strictly positive")
        result = (1 if config.kind == "hertz_period" else config.factor) / value
    else:
        factor, offset = affine_parameters(config)
        result = (value - offset) / factor if inverse else value * factor + offset
    if not math.isfinite(result):
        raise ValueError("secondary conversion exceeds finite floating-point range")
    return result


def secondary_issues(config, parent):
    if config is None:
        return []
    if not isinstance(config, SecondaryAxisSpec):
        return ["derived secondary axis must be SecondaryAxisSpec"]
    issues = transform_issues(config.transform)
    if config.label is not None and not isinstance(config.label, str):
        issues.append("derived label must be literal text or None")
    if parent.scale not in ("linear", "log"):
        issues.append(
            "native minimum secondary conversion supports linear/log parents only"
        )
    if isinstance(config.transform, AxisTransformSpec):
        if config.transform.kind == "unix_seconds":
            if parent.temporal is None:
                issues.append("unix_seconds requires an explicit TemporalSpec parent")
        elif parent.temporal is not None:
            issues.append(
                "temporal derived conversion must explicitly use unix_seconds"
            )
    derived = AxisSpec(scale=parent.scale, scale_options=parent.scale_options)
    issues.extend(tick_issues(config.major_ticks, derived, "major"))
    issues.extend(tick_issues(config.minor_ticks, derived, "minor"))
    if (
        parent.limits is not None
        and isinstance(parent.limits, (list, tuple))
        and len(parent.limits) == 2
        and all(finite_number(v) for v in parent.limits)
        and not issues
    ):
        try:
            check_conversion_bounds(parent.limits, config.transform, parent.scale)
        except (ValueError, OverflowError, ZeroDivisionError) as error:
            issues.append(str(error))
    return issues


def check_conversion_bounds(bounds, config, scale):
    low, high = map(float, bounds)
    converted = [transform_scalar(value, config) for value in (low, high)]
    if low == high or converted[0] == converted[1]:
        raise ValueError(
            "secondary view conversion collapses at floating-point precision"
        )
    if scale == "log" and any(value <= 0 for value in converted):
        raise ValueError("log-parent secondary view must remain positive")
    for before, after in zip((low, high), converted, strict=True):
        restored = transform_scalar(after, config, inverse=True)
        # Propagate forward target rounding through the CLOSED inverse.
        # Offset conversions naturally lose more than a few source ULP near
        # zero; that is not endpoint collapse or arbitrary regularization.
        if config.kind in ("hertz_period", "reciprocal"):
            uncertainty = abs(restored) * (math.ulp(after) / abs(after))
        else:
            factor, _ = affine_parameters(config)
            uncertainty = (
                math.ulp(after) * abs(factor)
                if config.reverse
                else math.ulp(after) / abs(factor)
            )
        tolerance = 8 * max(math.ulp(before), math.ulp(restored), uncertainty)
        if not math.isfinite(tolerance) or abs(restored - before) > tolerance:
            raise ValueError(
                "secondary view cannot roundtrip at floating-point precision"
            )
    return converted


def _geometry_values(columns, layer, horizontal):
    """Coordinates, not primitive magnitudes (stairs edges/event lane extents)."""
    # Domain-only view: native paths break when ANY paired coordinate is
    # missing/nonfinite. Keep original columns for native parsing and drawing.
    rows = None
    if layer.type == "stem":
        from ._stem import stem_rows

        if not all(
            isinstance(name, str) and name in columns for name in (layer.x, layer.y)
        ):
            return []
        try:
            selected = stem_rows(columns, layer)
        except ValueError:
            return []  # The stem validator owns invalid membership.
        positions = horizontal != (layer.orient == "h")
        values = columns[layer.x if positions else layer.y]
        drawn = [values[i] for i in selected]
        if drawn and not positions:
            drawn.append(0 if layer.baseline is None else layer.baseline)
        return drawn
    if layer.type in ("line", "scatter", "bar", "errorbar", "band"):
        names = [layer.x, layer.y]
        if layer.type == "band" and layer.y2 is not None:
            names.append(layer.y2)
        if all(isinstance(name, str) and name in columns for name in names):
            paired = [columns[name] for name in names]
            if len({len(values) for values in paired}) == 1:
                rows = [
                    not any(
                        is_missing(value)
                        or (isinstance(value, float) and not math.isfinite(value))
                        for value in point
                    )
                    for point in zip(*paired, strict=True)
                ]
                if not any(rows):
                    return []  # No primitive or literal baseline is drawn.

    def col(name):
        if not isinstance(name, str) or name not in columns:
            return []
        values = columns[name]
        if rows is None:
            return values
        return [value for value, visible in zip(values, rows, strict=True) if visible]

    if layer.type in ("hline", "vline"):
        return [layer.value] if horizontal == (layer.type == "vline") else []
    if layer.type in ("text", "annotate"):
        return [
            point[0 if horizontal else 1]
            for point in (layer.at, layer.to)
            if isinstance(point, (list, tuple)) and len(point) == 2
        ]
    if layer.type == "rug":
        return col(layer.x) if horizontal == (layer.orient == "v") else []
    baseline = 0 if layer.baseline is None else layer.baseline
    if not finite_number(baseline):
        return [baseline]
    if layer.type == "stairs":
        return (
            layer.bins
            if horizontal and isinstance(layer.bins, (list, tuple))
            else []
            if horizontal
            else [*col(layer.x), baseline]
        )
    if layer.type == "eventplot":
        length = 1 if layer.width is None else layer.width
        if not finite_number(length):
            return [length]
        return (
            col(layer.x)
            if horizontal
            else [baseline - length / 2, baseline + length / 2]
        )
    if layer.type == "broken_barh":
        if layer.width is not None and not finite_number(layer.width):
            return [layer.width]
        if not horizontal:
            return [baseline, baseline + (1 if layer.width is None else layer.width)]
        return [
            point
            for start, duration in zip(col(layer.x), col(layer.y), strict=False)
            if finite_number(start) and finite_number(duration)
            for point in (start, start + duration)
        ]
    values = list(col(layer.x if horizontal else layer.y))
    if layer.type == "band" and not horizontal:
        values.extend(col(layer.y2))
    if layer.type == "bar" and not horizontal:
        values.append(0)
    if layer.type == "bar" and horizontal and layer.group is None:
        width = 0.8 if layer.bar_width is None else layer.bar_width
        if not finite_number(width):
            return [width]
        values = [
            point
            for value in values
            if finite_number(value)
            for point in (value - width / 2, value + width / 2)
        ]
    if layer.type in ("bar", "errorbar"):
        error = layer.xerr if horizontal else layer.yerr
        centers = col(layer.x if horizontal else layer.y)
        if isinstance(error, str) and error in columns:
            values.extend(
                point
                for center, magnitude in zip(centers, col(error), strict=False)
                if finite_number(center) and finite_number(magnitude)
                for point in (center - magnitude, center + magnitude)
            )
        if not horizontal:
            values.extend(col(layer.y_lower))
            values.extend(col(layer.y_upper))
    return values


def ordinal_axis(columns, panel, name):
    """Reuse existing category roles and the raw-x float/category distinction."""
    from ._categorical import category_axis_mode, raw_x_is_categorical
    from ._facet import ordered_group_columns

    axis = getattr(panel, name)
    if axis is None or axis.temporal is not None:
        return False
    coordinate = "y" if name == "y2" else name
    for layer in panel.layers:
        if layer.type in {"stem", "eventplot", "broken_barh"}:
            continue  # Native raw marks never use inferred ordinal coordinates.
        if coordinate == "y" and layer.axis != ("y2" if name == "y2" else "y"):
            continue
        role = category_axis_mode(layer)
        if role is not None:
            if role == (coordinate, "ordinal"):
                return True
            continue
        if (
            coordinate == "x"
            and layer.x
            and layer.y
            and layer.x in columns
            and layer.y in columns
        ):
            selected = columns
            if layer.group and layer.hue_order is not None:
                try:
                    selected = ordered_group_columns(columns, layer)
                except ValueError:
                    continue
            if raw_x_is_categorical(selected[layer.x]):
                return True
    return False


def panel_issues(columns, panel):
    issues = []
    for name in ("x", "y", "y2", "z"):
        axis = getattr(panel, name)
        if axis is None:
            continue
        if (
            configured(axis)
            and (panel.projection != "2d" or name == "z")
            # Explicit log parameters retain existing valid native log paths.
            and not (
                axis.scale == "log"
                and axis.major_ticks is None
                and axis.minor_ticks is None
            )
        ):
            issues.append(f"N12 configured {name} controls require Cartesian2D axes")
        if (
            axis.major_ticks is not None or axis.minor_ticks is not None
        ) and ordinal_axis(columns, panel, name):
            for ticks in (axis.major_ticks, axis.minor_ticks):
                if not isinstance(ticks, TickSpec):
                    continue
                if isinstance(
                    ticks.locator, LocatorSpec
                ) and ticks.locator.kind not in ("auto", "none", "fixed"):
                    issues.append(
                        "ordinal axes require auto/none/fixed locators, "
                        "not numeric families"
                    )
                if isinstance(
                    ticks.formatter, FormatterSpec
                ) and ticks.formatter.kind not in ("auto", "none", "fixed"):
                    issues.append("ordinal axes require auto/none/fixed literal labels")
        if axis.scale not in NEW_SCALES:
            continue
        if ordinal_axis(columns, panel, name):
            issues.append(f"{axis.scale} does not support ordinal category geometry")
            continue
        for layer in panel.layers:
            if (name == "y" and layer.axis != "y") or (
                name == "y2" and layer.axis != "y2"
            ):
                continue
            if layer.type in {"eventplot", "broken_barh"}:
                from ._lanes import advanced_lanes

                if advanced_lanes(layer, panel):
                    continue  # Validate actual selected coordinates in the lane plan.
            if layer.type == "stairs":
                from ._stairs import advanced_stairs

                if advanced_stairs(layer, panel):
                    continue  # Its typed plan validates the actual drawn windows.
            if layer.type not in RAW_NONLINEAR_TYPES:
                issues.append(
                    f"{layer.type} does not support new {axis.scale} display geometry"
                )
                continue
            selected = columns
            if layer.hue_order is not None and layer.group:
                from ._facet import ordered_group_columns

                try:
                    selected = ordered_group_columns(selected, layer)
                except ValueError:
                    continue  # Existing per-layer validation reports this.
            if layer.semantics is not None and layer.type != "stem":
                from ._semantics import semantic_rows

                try:
                    rows = semantic_rows(selected, layer)
                    selected = {
                        key: [value[i] for i in rows] for key, value in selected.items()
                    }
                except (ValueError, KeyError):
                    continue
            for value in _geometry_values(selected, layer, name == "x"):
                if value is None or (
                    isinstance(value, float) and not math.isfinite(value)
                ):
                    continue  # Retain native raw-path missing/nonfinite gaps.
                if not finite_number(value):
                    issues.append(
                        f"{axis.scale} requires numeric coordinates, "
                        "not categories/bool"
                    )
                    break
                if axis.scale == "logit" and not 0 < value < 1:
                    issues.append("logit geometry must lie strictly inside (0,1)")
                    break
    for name in ("x", "y"):
        config = getattr(panel, "secondary_" + name)
        if config is not None and panel.projection != "2d":
            issues.append("derived secondary axes require Cartesian2D")
        issues.extend(secondary_issues(config, getattr(panel, name)))
    if panel.secondary_y is not None and panel.y2 is not None:
        issues.append(
            "derived secondary_y conflicts with independent y2 on the right spine"
        )
    return issues
