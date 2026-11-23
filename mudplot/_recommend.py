"""Deterministic chart advice, not a chart builder or a statistical inference engine."""

from __future__ import annotations

import math
import re
from collections import Counter
from datetime import datetime
from fractions import Fraction
from numbers import Real

from .data import to_columns


def _finite(value):
    try:
        return math.isfinite(value)
    except (TypeError, ValueError, OverflowError):
        return False


def _numeric(values):
    numbers = []
    for value in values:
        if not isinstance(value, Real) or isinstance(value, bool):
            continue
        try:
            number = float(value)
        except OverflowError:
            continue
        if math.isfinite(number):
            numbers.append(value if isinstance(value, int) else number)
    return numbers


def numeric_warnings(values):
    """Describe magnitudes, never scientific importance or unknown units."""
    numbers = _numeric(values)
    if not numbers:
        return []
    nonzero = [abs(v) for v in numbers if v != 0]
    warnings = []
    if not nonzero:
        warnings.append(
            (
                "all-zero",
                "All finite measurements are zero.",
                "Check precision and metric semantics; do not use a log axis.",
            )
        )
    elif max(nonzero) < 1e-6:
        warnings.append(
            (
                "small-scale",
                "Small numerical magnitudes do not establish scientific negligibility.",
                "Use scientific notation and known units; retain original values.",
            )
        )
    if nonzero and math.log10(max(nonzero)) - math.log10(min(nonzero)) >= 4:
        warnings.append(
            (
                "wide-scale",
                "Nonzero magnitudes span at least four orders of magnitude.",
                "Use log only for positive values, or explicitly justified symlog.",
            )
        )
    if any(isinstance(value, int) and float(value) != value for value in numbers):
        warnings.append(
            (
                "coordinate-precision",
                "Some integers lose precision in floating-point plot coordinates.",
                "Keep original values; explicitly define relative or datetime "
                "coordinates with known units before plotting.",
            )
        )
    return warnings


def _quantile(ordered, fraction):
    index = (len(ordered) - 1) * fraction
    low = int(index)
    weight = index - low
    left, right = ordered[low], ordered[min(low + 1, len(ordered) - 1)]
    if weight == 0:
        return left
    # Exact interpolation avoids losing integer bits or subnormal float terms.
    result = Fraction(left) + (Fraction(right) - Fraction(left)) * Fraction(weight)
    if not result and isinstance(left, float) and isinstance(right, float):
        return left * (1 - weight) + right * weight  # Preserve signed zero.
    return result


def _profile(values):
    present = [v for v in values if v is not None]
    numeric = _numeric(present)
    if present and all(isinstance(v, bool) for v in present):
        kind = "boolean"
    elif present and all(
        isinstance(v, Real) and not isinstance(v, bool) for v in present
    ):
        kind = "numeric"
    elif present and all(isinstance(v, str) for v in present):
        try:
            for value in present:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            kind = "datetime"
        except ValueError:
            kind = "categorical"
    else:
        kind = "mixed" if present else "empty"
    try:
        cardinality = len(set(present))
    except TypeError as exc:
        raise ValueError("chart recommendations require scalar column values") from exc
    profile = {
        "type": kind,
        "count": len(values),
        "missing": len(values) - len(present),
        "cardinality": cardinality,
    }
    if kind == "numeric":
        ordered = sorted(numeric)
        profile.update(
            finite=len(numeric),
            nonfinite=len(present) - len(numeric),
            zeros=sum(v == 0 for v in numeric),
        )
        if ordered:
            q1, q3 = (Fraction(_quantile(ordered, q)) for q in (0.25, 0.75))
            iqr = q3 - q1
            median = _quantile(ordered, 0.5)
            if isinstance(median, Fraction):
                middle = ordered[(len(ordered) - 1) // 2 : len(ordered) // 2 + 1]
                median = (
                    median.numerator
                    if median.denominator == 1
                    and all(isinstance(value, int) for value in middle)
                    else float(median)
                )
            profile.update(min=ordered[0], max=ordered[-1], median=median)
            # Descriptive Tukey fences never justify deleting observations.
            spread = Fraction(3, 2) * iqr
            lower, upper = q1 - spread, q3 + spread
            profile["iqr_tail_count"] = (
                sum(v < lower or v > upper for v in ordered)
                if _numeric([iqr])
                else None
            )
    return profile


def recommend(
    data,
    *,
    y: str,
    x: str | None = None,
    group: str | None = None,
    time: bool | None = None,
    paired: str | None = None,
    event: bool = False,
) -> dict:
    """Return JSON-safe chart advice without modifying data.

    Numeric ordering alone does not establish time: pass ``time=True`` for numeric
    timestamps. ``paired`` names a subject identifier, never implicit row pairing.
    ``event=True`` explicitly identifies event observations, not a continuous metric.
    """
    if time is not None and not isinstance(time, bool):
        raise ValueError("time must be True, False or None")
    if not isinstance(event, bool):
        raise ValueError("event must be a boolean")
    if event and paired is not None:
        raise ValueError("event and paired roles cannot be combined")
    columns = to_columns(data)
    for name in (x, y, group, paired):
        if name is not None and (not isinstance(name, str) or not name):
            raise ValueError("recommendation column names must be nonempty strings")
        if name is not None and name not in columns:
            raise ValueError(f"unknown recommendation column: {name!r}")
    if not isinstance(y, str) or not y:
        raise ValueError("y must name a measurement column")
    if (time is True or event or paired is not None) and x is None:
        raise ValueError("time, events and paired comparisons require x")
    if len({len(columns[name]) for name in (x, y, group, paired) if name}) > 1:
        raise ValueError("recommendation role columns must have the same length")
    profiles = {name: _profile(values) for name, values in columns.items()}
    warnings = []
    for name in dict.fromkeys(name for name in (x, y) if name):
        for code, message, suggestion in numeric_warnings(columns[name]):
            if code == "coordinate-precision" or (name == y and not event):
                warnings.append(
                    {
                        "code": code,
                        "message": message,
                        "suggestion": suggestion,
                        "column": name,
                    }
                )
    recommendations = []

    def add(kind, layers, reason, **options):
        recommendations.append(dict(kind=kind, layers=layers, reason=reason, **options))

    def warn(code, message, suggestion):
        warnings.append({"code": code, "message": message, "suggestion": suggestion})

    yp = profiles[y]
    usable = (
        bool(yp.get("finite", 0))
        if x is None
        else any(
            xv is not None
            and (not isinstance(xv, Real) or _finite(xv))
            and yv is not None
            and (not isinstance(yv, Real) or _finite(yv))
            for xv, yv in zip(columns[x], columns[y], strict=True)
        )
    )
    for name in dict.fromkeys(name for name in (x, y) if name):
        if profiles[name]["missing"] or profiles[name].get("nonfinite", 0):
            warn(
                "missing-values",
                f"{name} contains missing, non-finite or unsupported-range values.",
                "Report missingness; never silently impute measurements.",
            )
    if yp.get("iqr_tail_count") and not event:
        warn(
            "tail-values",
            "Some measurements lie beyond descriptive 1.5-IQR fences.",
            "Retain tail observations in a distribution; these are not known errors.",
        )
    is_time = x is not None and (
        time is True or (time is None and profiles[x]["type"] == "datetime")
    )
    ordered = False
    if is_time and x is not None:
        last = {}
        ordered = True
        repeated = False
        unsupported_precision = False
        for i, value in enumerate(columns[x]):
            if value is None:
                ordered = False
                continue
            key = columns[group][i] if group else None
            try:
                if profiles[x]["type"] == "datetime":
                    # fromisoformat truncates sub-microsecond times and offsets.
                    parts = re.findall(r"[.,]([0-9]+)", value)
                    if any(digits[6:].strip("0") for digits in parts):
                        unsupported_precision = True
                        continue
                    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    # CPython can discard fractional seconds on zero UTC offsets.
                    offset_fraction = re.search(
                        r"[+-]\d{2}(?::?\d{2}){0,2}[.,](\d+)$", value
                    )
                    if (
                        stamp.tzinfo is not None
                        and not stamp.utcoffset()
                        and offset_fraction
                        and offset_fraction[1].strip("0")
                    ):
                        unsupported_precision = True
                        continue
                elif profiles[x]["type"] == "numeric":
                    stamp = value
                else:
                    ordered = False
                    continue
                valid = isinstance(stamp, datetime) or math.isfinite(stamp)
                if key in last and stamp == last[key]:
                    repeated = True
                if not valid or (key in last and stamp <= last[key]):
                    ordered = False
                last[key] = stamp
            except (TypeError, ValueError, OverflowError):
                ordered = False
        if unsupported_precision:
            warn(
                "time-precision",
                f"{x}: ISO times cannot be compared without precision loss.",
                "Keep original strings; explicitly supply precision-safe "
                "relative/numeric coordinates with known units.",
            )
        if repeated:
            warn(
                "repeated-time",
                "Time repeats within a group.",
                "Identify replicates/events before connecting or aggregating rows.",
            )
        if not ordered:
            warn(
                "unordered-time",
                "Time is missing, incompatible or not strictly ordered in groups.",
                "Inspect missingness and ordering before explicitly sorting a copy; "
                "do not connect the current rows as a trend.",
            )
        ordered = ordered and not unsupported_precision
    if event and x is not None and usable:
        native = (
            profiles[x]["type"] == "numeric"
            and profiles[x].get("finite", 0) == profiles[x]["count"]
            and group is None
            and yp["type"] == "numeric"
            and yp["cardinality"] == 1
            and yp.get("finite", 0) == yp["count"]
        )
        options = {"offset": columns[y][0]} if native else {"marker": "|"}
        add(
            "event",
            ["eventplot"] if native else ["scatter"],
            "Explicitly identified events suit a raster, not round marker clouds.",
            require="Use explicit time and event lanes; do not connect events.",
            **options,
        )
    elif paired is not None and x is not None:
        cells = {}
        for subject, condition in zip(columns[paired], columns[x], strict=True):
            cells[(subject, condition)] = cells.get((subject, condition), 0) + 1
        conditions = set(columns[x])
        subjects = set(columns[paired])
        complete = (
            yp.get("finite", 0) == yp["count"]
            and not profiles[x]["missing"]
            and not profiles[x].get("nonfinite", 0)
            and not profiles[paired]["missing"]
            and not profiles[paired].get("nonfinite", 0)
            and len(conditions) == 2
            and all(
                cells.get((subject, condition)) == 1
                for subject in subjects
                for condition in conditions
            )
        )
        if complete:
            add(
                "paired",
                ["line", "scatter"],
                "Subject identifiers give one observation in each of two conditions.",
                require="Connect only the same subject; do not infer significance.",
            )
        else:
            warn(
                "incomplete-pairs",
                "Pairs lack finite numeric measurements, complete identifiers, "
                "or a unique two-condition design.",
                "Resolve the design; do not pair by row order or aggregate silently.",
            )
    elif is_time and ordered and yp["type"] == "numeric" and usable:
        add(
            "trend",
            ["line"],
            "An explicitly temporal coordinate is ordered within groups.",
            require="Retain gaps and measurements; justify smoothing or aggregation.",
        )
    if yp["type"] == "numeric" and not event and usable:
        if x is not None and profiles[x]["type"] in {"categorical", "boolean"}:
            counts = list(Counter(columns[x]).values())
            if counts and max(counts) > 1:
                add(
                    "distribution",
                    ["box", "stripplot"],
                    "Repeated measurements need distributions, not unexplained bars.",
                    require=(
                        "Show observations; do not assume independence or intervals."
                    ),
                )
            else:
                add(
                    "comparison",
                    ["bar"],
                    "One value per category suits a directly labelled comparison.",
                    require="Use bars for meaningful zero baselines, otherwise points.",
                )
        elif (
            x is None
            or yp.get("finite", 0) > 200
            or yp["cardinality"] < max(3, yp["count"] // 10)
        ):
            add(
                "distribution",
                ["ecdf", "hist"],
                "Distributions expose repeats and tails without overlapping markers.",
                require="Choose bins explicitly; disclose temporal aggregation.",
            )
        if (
            x is not None
            and profiles[x]["type"] == "numeric"
            and not is_time
            and not event
            and paired is None
        ):
            add(
                "relationship",
                ["scatter"],
                "Two numeric variables describe a relationship, not necessarily time.",
                require="Check dependence; do not infer causality or significance.",
            )
    elif yp["type"] != "numeric" and not event:
        warn(
            "metric-semantics",
            "The measurement is not a consistently numeric variable.",
            "Specify category, state or event semantics before choosing geometry.",
        )
    if group and profiles[group]["cardinality"] > 8:
        warn(
            "many-groups",
            "More than eight groups would overload a small legend.",
            "Use facets or a justified subset; explicitly report omitted groups.",
        )
    if not recommendations:
        warn(
            "insufficient-semantics",
            "No safe chart recommendation follows from the supplied roles.",
            "Specify the metric, time/event roles or valid pairing explicitly.",
        )
    return {
        "profiles": profiles,
        "recommendations": recommendations,
        "warnings": warnings,
        "data_changed": False,
        "units_inferred": False,
        "statistical_inference": False,
    }
