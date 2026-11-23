"""Typed row membership, clock projection and raw lane geometry for N05/N06."""

from dataclasses import dataclass
from fractions import Fraction

from ._ecdf import finite_number
from ._semantics import MAX_ROWS, categorical, category_key
from ._stat import is_missing
from .spec import SemanticSpec

LANE_TYPES = frozenset({"eventplot", "broken_barh"})


def lane_axis(layer, panel):
    return panel.y2 if layer.axis == "y2" else panel.y


def advanced_lanes(layer, panel):
    if layer.type not in LANE_TYPES:
        return False
    y = lane_axis(layer, panel)
    return (
        layer.group is not None
        or layer.hue_order is not None
        or layer.lane_step is not None
        or layer.semantics is not None
        or bool(panel.filters or panel.dropna)
        or panel.x.scale == "log"
        or (y is not None and y.scale == "log")
    )


def lane_members(columns, layer, *, candidates=None, order_only=False):
    """Return typed slots, then (local row, slot) pairs in physical row order."""
    from ._facet import MAX_FACET_PANELS, _ordered

    candidates = (
        range(len(next(iter(columns.values()), ())))
        if candidates is None
        else candidates
    )
    fixed = layer.hue_order is not None
    group = layer.group
    if group is None and fixed:
        raise ValueError(f"{layer.type} hue_order requires an existing lane group")
    if group is not None and (not isinstance(group, str) or group not in columns):
        raise ValueError(f"{layer.type} group must name an existing lane column")
    levels = _ordered((), layer.hue_order) if fixed else [None] if group is None else []
    slots: dict[tuple[str, object], int] = (
        {category_key(value): i for i, value in enumerate(levels)}
        if group is not None
        else {}
    )
    groups = columns[group] if group is not None else None
    filters = []
    config = layer.semantics
    if not order_only and isinstance(config, SemanticSpec):
        for role in ("hue", "size", "style"):
            name = getattr(config, role)
            order = getattr(config, f"{role}_order")
            if (
                isinstance(order, (list, tuple))
                and isinstance(name, str)
                and name in columns
                and all(categorical(value) for value in order)
            ):
                filters.append(
                    (columns[name], {category_key(value) for value in order})
                )
    members = []
    for row in candidates:
        index = 0
        if groups is not None:
            value = groups[row]
            if fixed and is_missing(value):
                continue
            key = category_key(value)
            if key not in slots:
                if fixed:
                    continue
                if len(levels) == MAX_FACET_PANELS:
                    raise ValueError(
                        f"{layer.type} exceeds {MAX_FACET_PANELS} lane levels"
                    )
                slots[key] = len(levels)
                levels.append(value)
            index = slots[key]
        if order_only:
            continue
        if any(
            categorical(values[row]) and category_key(values[row]) not in keys
            for values, keys in filters
        ):
            continue
        if len(members) == MAX_ROWS:
            raise ValueError(f"{layer.type} exceeds {MAX_ROWS} selected rows")
        members.append((row, index))
    if groups is not None and not fixed:
        _ordered(levels)  # Same ambiguous display-label check as fixed groups.
    return levels, members


@dataclass(frozen=True)
class LaneGeometry:
    levels: list
    members: list[tuple[int, int]]
    starts: list[float]
    ends: list[float] | None
    spans: dict[int, tuple[float, float]]


def _rounded(value, role):
    try:
        return float(value)
    except OverflowError as error:
        raise ValueError(f"{role} overflows finite raw coordinates") from error


def _positive_domain(axis, values, role):
    if axis.scale == "log" and any(v <= 0 for v in values):
        raise ValueError(f"log {role} must be positive")
    if axis.scale == "logit" and any(not 0 < v < 1 for v in values):
        raise ValueError(f"logit {role} must lie strictly inside (0,1)")


def plan_lanes(columns, layer, panel):
    from ._temporal import temporal_coordinates, temporal_durations
    from ._temporal_data import temporal_options

    kind = layer.type
    event = kind == "eventplot"
    y = lane_axis(layer, panel)
    if panel.projection != "2d" or layer.axis not in ("y", "y2") or y is None:
        raise ValueError(f"{kind} requires Cartesian primary or enabled y2 axes")
    literal = 0 if layer.baseline is None else layer.baseline
    width = 1 if layer.width is None else layer.width
    step = layer.lane_step
    if not finite_number(literal):
        raise ValueError(f"{kind} lane center/bottom must be finite numeric, not bool")
    if not finite_number(width) or width <= 0:
        raise ValueError(f"{kind} lane length/height must be finite and positive")
    if step is not None and (
        not finite_number(step) or step <= 0 or layer.group is None
    ):
        raise ValueError(
            f"{kind} lane_step requires a real group and a finite positive step"
        )
    names = (layer.x,) if event else (layer.x, layer.y)
    if not all(isinstance(name, str) and name in columns for name in names):
        raise ValueError(
            f"{kind} requires existing position/start and applicable duration columns"
        )
    levels, members = lane_members(columns, layer)
    c = layer.semantics
    fixed = layer.hue_order is not None or (
        isinstance(c, SemanticSpec)
        and any(
            getattr(c, f"{role}_order") is not None for role in ("hue", "size", "style")
        )
    )
    if not members and not (fixed or panel.filters or panel.dropna):
        raise ValueError(f"{kind} requires 1..{MAX_ROWS} selected rows")
    spans = {}
    absolute, size = Fraction(literal), Fraction(width)
    stride = None if step is None else Fraction(step)
    for index in dict.fromkeys(index for _, index in members):
        center = absolute if stride is None else absolute + index * stride
        displayed = _rounded(center, f"{kind} lane position")
        if (
            stride is not None
            and index
            and _rounded(center - stride, f"{kind} prior lane position") >= displayed
        ):
            raise ValueError(f"{kind} lane_step collapses adjacent raw lane positions")
        half = size / 2 if event else 0
        lower = _rounded(center - half, f"{kind} lane endpoint")
        upper = _rounded(center + size - half, f"{kind} lane endpoint")
        if lower >= upper or (event and not lower < displayed < upper):
            raise ValueError(f"{kind} lane endpoints collapse in raw coordinates")
        _positive_domain(y, (lower, upper), f"{kind} lane endpoints")
        spans[index] = lower, upper
    positions = [columns[layer.x][i] for i, _ in members]
    durations = None if event else [columns[layer.y][i] for i, _ in members]
    if panel.x.temporal is not None:
        clock = panel.x.temporal
        try:
            positions = temporal_coordinates(positions, **temporal_options(clock))
            if durations is not None:
                durations = temporal_durations(durations, unit=clock.unit or "day")
        except ValueError as error:
            raise ValueError(
                f"{kind} position/elapsed-duration clock: {error}"
            ) from error
    if any(not finite_number(v) for v in positions):
        raise ValueError(
            f"{kind} selected positions/starts must be finite numeric or explicit "
            "clock values"
        )
    starts = [float(v) for v in positions]
    _positive_domain(panel.x, starts, f"{kind} positions/starts")
    ends = None
    if durations is not None:
        ends = []
        for i, (start, duration) in enumerate(zip(positions, durations, strict=True)):
            if not finite_number(duration) or duration <= 0:
                raise ValueError(
                    "broken_barh selected durations must be finite and positive"
                )
            end = _rounded(
                Fraction(start) + Fraction(duration), "broken_barh interval endpoint"
            )
            if end <= starts[i]:
                raise ValueError(
                    "broken_barh interval endpoints collapse in raw coordinates"
                )
            ends.append(end)
        _positive_domain(panel.x, ends, "broken_barh interval endpoints")
    return LaneGeometry(levels, members, starts, ends, spans)
