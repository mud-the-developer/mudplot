"""Bounded native stairs geometry; no statistics or drawing on the core path."""

import math
from dataclasses import dataclass
from fractions import Fraction
from itertools import pairwise

from ._ecdf import finite_number
from ._semantics import MAX_ROWS, categorical, category_key
from ._stat import is_missing
from .spec import StairsRebinSpec, StairsSpec


def advanced_stairs(layer, panel):
    y = panel.y2 if layer.axis == "y2" else panel.y
    return layer.type == "stairs" and (
        layer.stairs is not None
        or layer.group is not None
        or layer.hue_order is not None
        or panel.filters
        or panel.dropna
        or panel.x.scale == "log"
        or (y is not None and y.scale == "log")
    )


@dataclass(frozen=True)
class StairWindow:
    edges: list[float]
    heights: list[float]


def stair_groups(columns, layer, rows, *, retain_rows=True):
    """Typed reserved order and eligible local row IDs, in source order."""
    from ._facet import _ordered

    if layer.group is None:
        if layer.hue_order is not None:
            raise ValueError("stairs hue_order requires an existing group column")
        if retain_rows and len(rows) > MAX_ROWS:
            raise ValueError(f"stairs exceeds {MAX_ROWS} selected source heights")
        return [(None, rows)]
    if not isinstance(layer.group, str) or layer.group not in columns:
        raise ValueError("stairs group must name an existing column")
    groups = columns[layer.group]
    fixed = layer.hue_order is not None
    order = _ordered((), layer.hue_order) if fixed else None
    reserved = {} if order is None else {category_key(value): [] for value in order}
    observed = []
    selected = 0
    for row in rows:
        value = groups[row]
        if fixed and is_missing(value):
            continue
        if not categorical(value):
            raise ValueError(
                "stairs groups require nonempty strings, booleans or finite numbers"
            )
        key = category_key(value)
        if key not in reserved:
            if fixed:
                continue
            reserved[key] = []
            observed.append(value)
            if len(observed) > 64:
                raise ValueError("stairs groups exceed 64 levels")
        if retain_rows:
            selected += 1
            if selected > MAX_ROWS:
                raise ValueError(f"stairs exceeds {MAX_ROWS} selected source heights")
            reserved[key].append(row)
    order = _ordered(observed) if order is None else order
    return [(value, reserved[category_key(value)]) for value in order]


def _edges(values, axis, name):
    from ._temporal_data import _temporal_bounds

    if not isinstance(values, (list, tuple)) or not 2 <= len(values) <= MAX_ROWS + 1:
        raise ValueError(f"stairs {name} needs 2..{MAX_ROWS + 1} explicit edges")
    try:
        view = (
            _temporal_bounds(values, axis.temporal)
            if axis.temporal is not None
            else values
        )
    except ValueError as error:
        raise ValueError(f"stairs {name} clock: {error}") from error
    if any(not finite_number(value) for value in view):
        raise ValueError(
            f"stairs {name} edges need finite numbers or an explicit ISO X clock"
        )
    result = [float(value) for value in view]
    if any(
        type(value) is int and value != point
        for value, point in zip(view, result, strict=True)
    ):
        raise ValueError(f"stairs {name} integer edge loses precision in binary64")
    if any(not a < b or not math.isfinite(b - a) for a, b in pairwise(result)):
        raise ValueError(
            f"stairs {name} edges must be increasing with representable widths"
        )
    return result


def _native_value(amount):
    try:
        value = float(amount)
    except OverflowError as error:
        raise ValueError("stairs rebin height overflows binary64") from error
    if amount > 0 and value == 0:
        raise ValueError("stairs rebin loses a positive height in binary64")
    return value


def _rebin(source, heights, target, measure):
    """Only two width-ratio terms per target; all other accumulation is dyadic."""
    i = 0
    result = []
    for left, right in pairwise(target):
        total = Fraction(0)
        partial = []
        while i < len(heights) and source[i] < right:
            a, b = source[i], source[i + 1]
            if measure == "mass" and left <= a and b <= right:
                total += heights[i]
            else:
                overlap = min(b, right) - max(a, left)
                if measure == "density":
                    total += heights[i] * overlap
                else:
                    partial.append(heights[i] * overlap / (b - a))
            if b > right:
                break
            i += 1
        if measure == "density":
            total /= right - left
        else:
            total += sum(partial)
        result.append(_native_value(total))
    return result


def _axis_values(axis, values, role):
    if axis.scale == "log" and any(value <= 0 for value in values):
        raise ValueError(f"log stairs {role} must be positive")
    if axis.scale == "logit" and any(not 0 < value < 1 for value in values):
        raise ValueError(f"logit stairs {role} must lie strictly inside (0,1)")


def plan_stairs(columns, layer, panel, row_ids):
    """Prepare one view, preserving each selected height's source bin identity."""
    from ._temporal import temporal_coordinates
    from ._temporal_data import temporal_options

    cfg = StairsSpec() if layer.stairs is None else layer.stairs
    if (
        not isinstance(cfg, StairsSpec)
        or type(cfg.fill) is not bool
        or type(cfg.open) is not bool
    ):
        raise ValueError("stairs requires StairsSpec with boolean fill/open")
    if cfg.open and (cfg.fill or layer.baseline not in (None, 0)):
        raise ValueError("open stairs cannot fill or declare a nonzero baseline")
    baseline = None if cfg.open else (0 if layer.baseline is None else layer.baseline)
    if layer.baseline is not None and not finite_number(layer.baseline):
        raise ValueError("stairs baseline must be finite numeric, not bool")
    if panel.projection != "2d" or layer.axis not in ("y", "y2") or layer.orient != "v":
        raise ValueError("stairs requires vertical Cartesian primary/y2 geometry")
    y = panel.y if layer.axis == "y" else panel.y2
    if y is None:
        raise ValueError("stairs needs an enabled y2 axis")
    edges = _edges(layer.bins, panel.x, "source")
    slots = len(edges) - 1
    if not isinstance(layer.x, str) or layer.x not in columns:
        raise ValueError("stairs heights must name an existing column")
    values = columns[layer.x]
    index = cfg.bin_index
    if index is not None and (not isinstance(index, str) or index not in columns):
        raise ValueError("stairs bin_index must name an existing source column")
    bin_ids = row_ids if index is None else columns[index]
    if index is None and not (panel.filters or panel.dropna) and len(values) != slots:
        raise ValueError(
            "stairs aligned source requires N+1 edges for the original table; "
            "use bin_index for separate groups"
        )
    groups = stair_groups(columns, layer, range(len(values)))
    selected = sum(len(rows) for _, rows in groups)
    if selected > MAX_ROWS:
        raise ValueError(f"stairs exceeds {MAX_ROWS} selected source heights")
    if not selected and not (panel.filters or panel.dropna or layer.hue_order):
        raise ValueError("stairs needs at least one selected height")
    target = None
    rebin = cfg.rebin
    if rebin is not None:
        if not isinstance(rebin, StairsRebinSpec) or rebin.measure not in (
            "mass",
            "density",
        ):
            raise ValueError(
                "stairs rebin requires StairsRebinSpec with mass or density measure"
            )
        if y.temporal is not None:
            raise ValueError(
                "stairs rebin heights are physical mass/density, not date-valued"
            )
        target = _edges(rebin.edges, panel.x, "target")
        if (edges[0], edges[-1]) != (target[0], target[-1]):
            raise ValueError("stairs rebin requires exact matching outer endpoints")
        if sum(bool(rows) for _, rows in groups) * (len(target) - 1) > MAX_ROWS:
            raise ValueError(f"stairs exceeds {MAX_ROWS} derived target heights")
        exact_edges, exact_target = (
            list(map(Fraction, edges)),
            list(map(Fraction, target)),
        )
    if selected and baseline is not None:
        _axis_values(y, [baseline], "baseline")
    planned = []
    for group, rows in groups:
        occupied = {}
        for row in rows:
            slot = bin_ids[row]
            if type(slot) is not int or not 0 <= slot < slots:
                raise ValueError(
                    "stairs bin_index must be a zero-based integer in the source "
                    "grid (not bool)"
                )
            if slot in occupied:
                raise ValueError("stairs duplicate selected (group, bin) height")
            occupied[slot] = values[row]
        windows = []
        if occupied:
            indices = sorted(occupied)
            heights = [occupied[i] for i in indices]
            if y.temporal is not None:
                try:
                    heights = temporal_coordinates(
                        heights, **temporal_options(y.temporal)
                    )
                except ValueError as error:
                    raise ValueError(f"stairs height clock: {error}") from error
            if any(not finite_number(value) for value in heights):
                raise ValueError(
                    "stairs selected heights must be finite numeric, not bool or "
                    "missing"
                )
            if target is not None:
                assert rebin is not None
                if len(indices) != slots:
                    raise ValueError(
                        "stairs rebin needs complete source support in each "
                        "nonempty group"
                    )
                if any(value < 0 for value in heights):
                    raise ValueError(
                        "stairs rebin heights must be nonnegative physical mass/density"
                    )
                _axis_values(panel.x, edges, "source edges")
                heights = _rebin(
                    exact_edges,
                    list(map(Fraction, heights)),
                    exact_target,
                    rebin.measure,
                )
                windows.append(StairWindow(target, heights))
            else:
                start = 0
                for end in range(1, len(indices) + 1):
                    if end == len(indices) or indices[end] != indices[end - 1] + 1:
                        windows.append(
                            StairWindow(
                                edges[indices[start] : indices[end - 1] + 2],
                                [float(v) for v in heights[start:end]],
                            )
                        )
                        start = end
            for window in windows:
                _axis_values(panel.x, window.edges, "edges")
                _axis_values(y, window.heights, "heights")
        planned.append((group, windows))
    return cfg, baseline, planned
