"""Dependency-free ECDF row contracts and deterministic empirical step values.

No binning, fit, interpolation, global RNG, censoring or implicit uncertainty.
Rendering calls the calculation only after validating the declarative spec.
"""

from __future__ import annotations

import math
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from fractions import Fraction
from numbers import Real

from ._stat import is_missing
from ._transforms import COLUMN_ARRAYS
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


def source_rows(
    columns: dict,
    layer: LayerSpec,
    *,
    coordinates=None,
    weights=None,
    typed_hue=False,
    row_limit=None,
    drop_missing=True,
) -> list[int]:
    """One paired source cohort; keep invalid selected values for validation.

    Zero weights and missing required columns are excluded before clock parsing.
    Typed hue equality is requested only by a resolved advanced family plan;
    ordinary legacy hue/order equality is unchanged.
    Strict model callers retain missing selected values with drop_missing=False;
    their role-specific validator, not this selector, decides whether they fail.
    """
    if layer.hue_order is not None and (
        layer.group is None or not isinstance(layer.hue_order, (list, tuple))
    ):
        return []
    names = list(coordinates if coordinates is not None else (layer.x,))
    if layer.group is not None:
        names.append(layer.group)
    if weights is not None:
        names.append(weights)
    if not all(
        isinstance(name, str)
        and name in columns
        and isinstance(columns[name], COLUMN_ARRAYS)
        for name in names
    ):
        return []
    data = [columns[name] for name in names]
    if len({len(column) for column in data}) != 1:
        return []
    selected = None
    if typed_hue and layer.hue_order is not None:
        from ._semantics import category_key

        try:
            selected = {category_key(value) for value in layer.hue_order}
        except ValueError:
            return []
    result = []
    for index, values in enumerate(zip(*data, strict=True)):
        if drop_missing and any(is_missing(value) for value in values):
            continue
        if (
            weights is not None
            and finite_number(columns[weights][index])
            and columns[weights][index] == 0
        ):
            continue
        if layer.hue_order is not None:
            value = columns[layer.group][index]
            if selected is None:
                if value not in layer.hue_order:
                    continue
            else:
                try:
                    key = category_key(value)
                except ValueError:
                    pass  # Invalid selected hue is reported, not silently hidden.
                else:
                    if key not in selected:
                        continue
        if row_limit is not None and len(result) >= row_limit:
            raise ValueError("new fields exceed10000 selected physical rows")
        result.append(index)
    return result


def ecdf_rows(columns: dict, layer: LayerSpec) -> list[int]:
    """Listwise missing/zero-weight exclusion and legacy hue selection."""
    if layer.ecdf is not None and not isinstance(layer.ecdf, ECDFSpec):
        return []
    return source_rows(columns, layer, weights=ecdf_config(layer).weights)


def ecdf_groups(columns: dict, layer: LayerSpec, rows: list[int]) -> list:
    """First-observed hues by default; explicit order reserves color slots."""
    if layer.group is None:
        return [None]
    if layer.hue_order is not None:
        return list(layer.hue_order)
    return list(dict.fromkeys(columns[layer.group][i] for i in rows))


def sqrt_fraction(value):
    """Take a square root without prematurely under/overflowing its variance."""
    if value < 0:
        raise ValueError("computed variance must be nonnegative")
    if not value:
        return 0.0
    exponent = (value.numerator.bit_length() - value.denominator.bit_length()) // 2
    scaled = value / (Fraction(2) ** (2 * exponent))
    try:
        return math.ldexp(math.sqrt(float(scaled)), exponent)
    except OverflowError as error:
        raise ValueError("computed spread exceeds finite plotting range") from error


def finite_mass(weights, *, context: str = "ECDF count") -> float:
    """Count mass must remain finite; proportions can scale before summation."""
    try:
        total = math.fsum(weights)
    except OverflowError as exc:
        raise ValueError(f"{context} mass exceeds finite range") from exc
    if not math.isfinite(total):
        raise ValueError(f"{context} mass exceeds finite range")
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
) -> tuple[list[int | float], list[float]]:
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
    if not any(weight > 0 for weight in weights):
        return [], []
    plan = canonical_cdf(values, weights)
    if stat == "count":
        finite_mass(weight for weight in weights if weight > 0)
    total = plan.total
    masses = [total if complementary else 0]
    masses.extend(
        total - prefix if complementary else prefix for prefix in plan.cumulative
    )
    factor = 100 if stat == "percent" else 1
    denominator = plan.denominator if stat == "count" else total
    try:
        ordinates = [float(Fraction(mass * factor, denominator)) for mass in masses]
    except OverflowError as exc:
        raise ValueError("ECDF cumulative mass exceeds finite range") from exc
    if not all(math.isfinite(value) for value in ordinates):
        raise ValueError("ECDF cumulative mass exceeds finite range")
    return [plan.knots[0], *plan.knots], ordinates


@dataclass(frozen=True)
class CanonicalCDF:
    """One exact dyadic mass plan; original values and row multiplicities stay raw."""

    values: tuple[int | float, ...]
    masses: tuple[int, ...]
    denominator: int
    order: tuple[int, ...]
    knots: tuple[int | float, ...]
    cumulative: tuple[int, ...]

    @property
    def total(self) -> int:
        return self.cumulative[-1]

    @property
    def effective_size(self) -> Fraction:
        return Fraction(self.total * self.total, sum(w * w for w in self.masses))

    def left(self, probability, counts=None):
        probability = Fraction(probability)
        if not 0 <= probability <= 1:
            raise ValueError("CDF probability must be in [0,1]")
        if counts is None:
            return self.knots[bisect_left(self.cumulative, probability * self.total)]
        total = sum(
            mass * int(count) for mass, count in zip(self.masses, counts, strict=True)
        )
        if total <= 0:
            raise ValueError("sampled CDF requires positive mass")
        target, cumulative = probability * total, 0
        for index in self.order:
            mass = self.masses[index] * int(counts[index])
            if mass:
                cumulative += mass
                if cumulative >= target:
                    return self.values[index]
        raise ValueError("sampled CDF mass was not conserved")

    def prefix(self, value, *, closed=False) -> int:
        end = (bisect_right if closed else bisect_left)(self.knots, value)
        return self.cumulative[end - 1] if end else 0


def canonical_cdf(values, weights=None) -> CanonicalCDF:
    """Shared canonical-before-float LEFT boundary extracted from letter values."""
    data = list(values)
    weights = [1] * len(data) if weights is None else list(weights)
    if len(data) != len(weights):
        raise ValueError("CDF weights must match observation length")
    if any(not finite_number(value) for value in data):
        raise ValueError("CDF observations require finite canonical numbers, not bool")
    if any(not finite_number(weight) or weight < 0 for weight in weights):
        raise ValueError("CDF weights require finite nonnegative numbers, not bool")
    pairs = [
        (value, Fraction(weight))
        for value, weight in zip(data, weights, strict=True)
        if weight > 0
    ]
    if not pairs:
        raise ValueError("CDF requires positive observation mass")
    denominator, masses = canonical_units(weight for _, weight in pairs)
    data = tuple(value for value, _ in pairs)
    order = tuple(sorted(range(len(data)), key=data.__getitem__))
    knots, cumulative, subtotal = [], [], 0
    for index in order:
        value = data[index]
        subtotal += masses[index]
        if knots and value == knots[-1]:
            cumulative[-1] = subtotal
        else:
            knots.append(value)
            cumulative.append(subtotal)
    return CanonicalCDF(
        data, masses, denominator, order, tuple(knots), tuple(cumulative)
    )


def canonical_type7(ordered, p) -> Fraction:
    """Unrounded type7 boundary, retaining canonical integer/float endpoints."""
    index = (len(ordered) - 1) * Fraction(p)
    low = index.numerator // index.denominator
    fraction = index - low
    lower = Fraction(ordered[low])
    if not fraction:
        return lower
    return lower * (1 - fraction) + Fraction(ordered[low + 1]) * fraction


def canonical_units(values):
    """Exact common integer units for canonical finite integers/dyadic floats."""
    fractions = [Fraction(value) for value in values]
    denominator = math.lcm(*(value.denominator for value in fractions))
    return denominator, tuple(
        value.numerator * (denominator // value.denominator) for value in fractions
    )


def covariance_units(
    x,
    y,
    masses,
    denominator_x,
    denominator_y,
    *,
    products_x=None,
    products_y=None,
    budget=None,
):
    """Exact reliability covariance/Kish size from the shared canonical units.

    The diagonal is sample spread, not estimator uncertainty. Physical source
    masses are squared before any tied-value aggregation. Kernels and existing
    statistical consumers use the same equation without binary64 normalization.
    """
    if len(x) != len(y) or len(x) != len(masses):
        raise ValueError("canonical covariance requires paired observations/masses")
    if denominator_x <= 0 or denominator_y <= 0:
        raise ValueError("canonical coordinate denominators must be positive")
    if budget is not None:
        mass_bits = max((value.bit_length() for value in masses), default=0)
        value_bits = max(
            max((abs(value).bit_length() for value in x), default=0),
            max((abs(value).bit_length() for value in y), default=0),
        )
        budget.charge(
            "integer_moments",
            4 * len(masses) + 4,
            bits=2 * (mass_bits + value_bits) + max(1, len(masses).bit_length()),
        )
    total = sum(masses)
    squared_mass = sum(mass * mass for mass in masses)
    correction = total * total - squared_mass
    if total <= 0 or correction <= 0:
        return None
    first_x = (
        sum(products_x)
        if products_x is not None
        else sum(mass * value for mass, value in zip(masses, x, strict=True))
    )
    first_y = (
        first_x
        if y is x
        else sum(products_y)
        if products_y is not None
        else sum(mass * value for mass, value in zip(masses, y, strict=True))
    )
    cross = sum(mass * a * b for mass, a, b in zip(masses, x, y, strict=True))
    covariance = Fraction(
        cross * total - first_x * first_y,
        correction * denominator_x * denominator_y,
    )
    return covariance, Fraction(total * total, squared_mass)
