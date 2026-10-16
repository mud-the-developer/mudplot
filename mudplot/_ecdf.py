"""Dependency-free ECDF row contracts and deterministic empirical step values.

No binning, fit, interpolation, global RNG, censoring or implicit uncertainty.
Rendering calls the calculation only after validating the declarative spec.
"""

from __future__ import annotations

import math
from numbers import Real

from ._stat import is_missing
from .spec import ECDFSpec, LayerSpec

ECDF_STATS = ("proportion", "percent", "count")


def finite_number(value) -> bool:
    if isinstance(value, bool) or not isinstance(value, Real):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, ValueError):
        return False


def ecdf_config(layer: LayerSpec) -> ECDFSpec:
    return ECDFSpec() if layer.ecdf is None else layer.ecdf


def ecdf_rows(columns: dict, layer: LayerSpec) -> list[int]:
    """Listwise missing/zero-weight exclusion and optional hue selection."""
    if layer.ecdf is not None and not isinstance(layer.ecdf, ECDFSpec):
        return []
    config = ecdf_config(layer)
    if layer.hue_order is not None and (
        layer.group is None or not isinstance(layer.hue_order, (list, tuple))
    ):
        return []
    names = [layer.x]
    if layer.group is not None:
        names.append(layer.group)
    if config.weights is not None:
        names.append(config.weights)
    if not all(
        isinstance(name, str)
        and name in columns
        and isinstance(columns[name], (list, tuple))
        for name in names
    ):
        return []
    data = [columns[name] for name in names]
    if len({len(column) for column in data}) != 1:
        return []
    return [
        i
        for i, row in enumerate(zip(*data, strict=True))
        if not any(is_missing(value) for value in row)
        and (
            config.weights is None
            or not finite_number(columns[config.weights][i])
            or columns[config.weights][i] != 0
        )
        and (layer.hue_order is None or columns[layer.group][i] in layer.hue_order)
    ]


def ecdf_groups(columns: dict, layer: LayerSpec, rows: list[int]) -> list:
    """First-observed hues by default; explicit order reserves color slots."""
    if layer.group is None:
        return [None]
    if layer.hue_order is not None:
        return list(layer.hue_order)
    return list(dict.fromkeys(columns[layer.group][i] for i in rows))


def finite_mass(weights) -> float:
    """Count mass must remain finite; proportions can scale before summation."""
    try:
        total = math.fsum(weights)
    except OverflowError as exc:
        raise ValueError("ECDF count mass exceeds finite range") from exc
    if not math.isfinite(total):
        raise ValueError("ECDF count mass exceeds finite range")
    return total


def _cumulative(masses: list[float]) -> list[float]:
    """Accurate prefixes using an online non-overlapping float expansion.

    Tie subtotals must not be rounded before accumulating them: this can make
    the penultimate proportion exceed 1 and the last step decrease by one ULP.
    The expansion retains low bits; fsum rounds each prefix only once. Its
    length is bounded by the finite binary64 exponent range, not row count.
    """
    partials: list[float] = []
    result = []
    for value in masses:
        index = 0
        for partial in partials:
            if abs(value) < abs(partial):
                value, partial = partial, value
            high = value + partial
            low = partial - (high - value)
            if low:
                partials[index] = low
                index += 1
            value = high
        partials[index:] = [value]
        result.append(math.fsum(partials))
    return result


def empirical_steps(
    values,
    weights=None,
    *,
    stat: str = "proportion",
    complementary: bool = False,
) -> tuple[list[float], list[float]]:
    """Return tie-aggregated knots with a duplicated minimum for its full jump.

    The curve is defined by P(X <= t), or its strict P(X > t) complement.
    Both are right-continuous. No infinite/synthetic tail coordinates are drawn.
    A horizontal renderer swaps coordinates and uses steps-pre, not steps-post.
    """
    if stat not in ECDF_STATS or type(complementary) is not bool:
        raise ValueError(
            "ECDF requires proportion/percent/count and boolean complementary"
        )
    values = list(values)
    if not all(finite_number(value) for value in values):
        raise ValueError("ECDF observations must be finite numbers, not bool")
    weights = [1.0] * len(values) if weights is None else list(weights)
    if len(weights) != len(values):
        raise ValueError("ECDF weights must match observation length")
    if not all(finite_number(weight) and weight >= 0 for weight in weights):
        raise ValueError("ECDF weights must be finite nonnegative numbers, not bool")
    pairs = sorted(
        (float(value), float(weight))
        for value, weight in zip(values, weights, strict=True)
        if weight > 0
    )
    if not pairs:
        return [], []
    if stat == "count":
        total = finite_mass(weight for _, weight in pairs)
        scale = 1.0
    else:
        scale = max(weight for _, weight in pairs)
        total = math.fsum(weight / scale for _, weight in pairs)
    knots, stops = [], []
    for index, (knot, _) in enumerate(pairs):
        if knots and knot == knots[-1]:
            stops[-1] = index
        else:
            knots.append(knot)
            stops.append(index)
    masses = [weight / scale for _, weight in pairs]
    if complementary:
        # Accumulate from the tail: 1 - CDF would erase small positive tails.
        tail = _cumulative(masses[::-1])
        ordinates = [total] + [
            tail[len(pairs) - stop - 2] if stop < len(pairs) - 1 else 0.0
            for stop in stops
        ]
    else:
        prefixes = _cumulative(masses)
        ordinates = [0.0] + [prefixes[stop] for stop in stops]
    if stat != "count":
        factor = 100.0 if stat == "percent" else 1.0
        ordinates = [value / total * factor for value in ordinates]
    if not all(math.isfinite(value) for value in ordinates):
        raise ValueError("ECDF cumulative mass exceeds finite range")
    return [knots[0], *knots], ordinates
