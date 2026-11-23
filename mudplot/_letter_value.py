"""Dependency-free letter-value summaries, not confidence intervals or KDE.

Tail stopping rules follow the Seaborn 0.13.2 LetterValues definitions (based on
Hofmann/Wickham/Kafadar's letter-value plots). Unweighted quantiles are type 7;
relative weights use the left inverse empirical CDF, not replicated rows.
Named depths are capped at 32; explicit depths must be in 1..32. Sorting and all
calculations are deterministic and never use random state or optional packages.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from itertools import pairwise
from numbers import Real
from statistics import NormalDist

from ._ecdf import canonical_cdf, canonical_type7, finite_number

MAX_LETTER_DEPTH = 32
DEPTH_METHODS = ("tukey", "proportion", "trustworthy", "full")
WIDTH_METHODS = ("exponential", "linear", "area")


def _fraction(value, minimum=0.0):
    if not isinstance(value, Real) or isinstance(value, bool):
        return False
    try:
        number = float(value)
    except (ValueError, OverflowError):
        return False
    return math.isfinite(number) and minimum <= number < 1 and number > 0


def option_issues(k_depth, width_method, outlier_prop, trust_alpha) -> list[str]:
    """Validate named/bounded options even before observations are supplied."""
    issues = []
    depth = "tukey" if k_depth is None else k_depth
    if not (
        (isinstance(depth, str) and depth in DEPTH_METHODS)
        or (type(depth) is int and 1 <= depth <= MAX_LETTER_DEPTH)
    ):
        issues.append(
            f"k_depth must be a named rule or integer in 1..{MAX_LETTER_DEPTH}"
        )
    if width_method is not None and not (
        isinstance(width_method, str) and width_method in WIDTH_METHODS
    ):
        issues.append("width_method must be exponential, linear or area")
    if outlier_prop is not None:
        if not _fraction(outlier_prop):
            issues.append("outlier_prop must be a finite fraction in (0, 1)")
        if depth != "proportion":
            issues.append("outlier_prop requires k_depth='proportion'")
    if trust_alpha is not None:
        if not _fraction(trust_alpha, 1e-12):
            issues.append("trust_alpha must be finite in [1e-12, 1)")
        if depth != "trustworthy":
            issues.append("trust_alpha requires k_depth='trustworthy'")
    return issues


def letter_value_depth(n: int, k_depth=None, outlier_prop=None, trust_alpha=None):
    """Return the capped number of lower/upper tail levels for n usable rows."""
    issues = option_issues(k_depth, None, outlier_prop, trust_alpha)
    if type(n) is not int or n < 1:
        issues.append("letter values require at least one observation")
    if issues:
        raise ValueError("; ".join(issues))
    depth = "tukey" if k_depth is None else k_depth
    log_n = math.log2(n)
    if depth == "full":
        k = int(log_n) + 1
    elif depth == "tukey":
        k = int(log_n) - 3
    elif depth == "proportion":
        prop = 0.007 if outlier_prop is None else outlier_prop
        # Separate logarithms avoid underflow in n * prop.
        k = int(log_n) - int(log_n + math.log2(prop)) + 1
    elif depth == "trustworthy":
        alpha = 0.05 if trust_alpha is None else trust_alpha
        # Symmetric negative quantile avoids cancellation in 1-alpha/2.
        point_conf = 2 * NormalDist().inv_cdf(alpha / 2) ** 2
        k = int(log_n - math.log2(point_conf)) + 1
    else:
        k = depth
    return min(MAX_LETTER_DEPTH, max(1, k))


def _log_span(lower: float, upper: float) -> float:
    span = upper - lower
    if math.isfinite(span):
        return math.log(span)
    scale = max(abs(lower), abs(upper))
    return math.log(scale) + math.log(upper / scale - lower / scale)


@dataclass(frozen=True)
class LetterValueSummary:
    depth: int
    percentiles: tuple[float, ...]  # fractions, including extremes in full mode
    values: tuple[int | float, ...]  # weighted LEFT retains observed scalar values
    levels: tuple[int, ...]
    widths: tuple[float, ...]  # relative widths, maximum 1
    median: int | float
    fliers: tuple[int | float, ...]  # actual source order, no pre-rounding
    masses: tuple[Fraction, ...] | None = None  # empirical weighted intervals
    tail_mass: Fraction | None = None
    effective_size: Fraction | None = None  # physical-row Kish, NOT a CI
    exact_values: tuple[Fraction, ...] | None = None  # BEFORE type7 final rounding


def letter_value_summary(
    values,
    *,
    weights=None,
    k_depth=None,
    width_method=None,
    outlier_prop=None,
    trust_alpha=None,
) -> LetterValueSummary:
    """Compute disjoint tail bands and median without inventing missing values.

    Area widths normalize probability-mass / band-height density within a cell.
    Zero-height bands have zero area width when any positive-height band exists;
    an entirely constant cell falls back to exponential widths. No infinities.
    Fliers are observations outside outer quantiles, not IQR-whisker outliers.
    """
    if weights is not None:
        return _weighted_summary(
            values,
            weights,
            k_depth=k_depth,
            width_method=width_method,
            outlier_prop=outlier_prop,
            trust_alpha=trust_alpha,
        )
    issues = option_issues(k_depth, width_method, outlier_prop, trust_alpha)
    data = list(values)
    if not data or any(not finite_number(v) for v in data):
        issues.append("letter values require nonempty finite numeric observations")
    if issues:
        raise ValueError("; ".join(issues))
    ordered = sorted(data)
    k = letter_value_depth(len(data), k_depth, outlier_prop, trust_alpha)
    lower = [2.0**-e for e in range(k + 1, 1, -1)]
    percs = lower + [1 - p for p in reversed(lower)]
    if k_depth == "full":
        percs[0], percs[-1] = 0.0, 1.0
    exact_boundaries = [canonical_type7(ordered, p) for p in percs]
    boundaries = [float(value) for value in exact_boundaries]
    levels = list(range(k)) + list(range(k - 2, -1, -1))
    widths = [2.0 ** (level - k + 1) for level in levels]
    if width_method == "linear":
        widths = [(level + 1) / k for level in levels]
    elif width_method == "area":
        # Preserve the existing nominal-percentile / FINAL numeric-height rule.
        log_densities = [
            math.log(percs[i + 1] - percs[i]) - _log_span(lo, hi)
            if hi > lo
            else -math.inf
            for i, (lo, hi) in enumerate(pairwise(boundaries))
        ]
        maximum = max(log_densities)
        if math.isfinite(maximum):
            widths = [math.exp(d - maximum) for d in log_densities]
    return LetterValueSummary(
        k,
        tuple(percs),
        tuple(boundaries),
        tuple(levels),
        tuple(widths),
        float(canonical_type7(ordered, 0.5)),
        # Type7 tails use its FINAL correctly-rounded numeric bounds, not a
        # different exact-rational tail estimator. Canonical rows stay intact.
        tuple(v for v in data if v < boundaries[0] or v > boundaries[-1]),
        exact_values=tuple(exact_boundaries),
    )


def _trunc_log2(ratio: Fraction) -> int:
    """Exact exponent comparisons, with truncation toward zero like int(log2)."""
    n, d = ratio.numerator, ratio.denominator
    exponent = n.bit_length() - d.bit_length()
    below = n < d << exponent if exponent >= 0 else n << -exponent < d
    if below:
        exponent -= 1
    exact = n == d << exponent if exponent >= 0 else n << -exponent == d
    return exponent if exponent >= 0 or exact else exponent + 1


def _weighted_depth(effective, k_depth, outlier_prop, trust_alpha):
    method = "tukey" if k_depth is None else k_depth
    if method == "full":
        depth = _trunc_log2(effective) + 1
    elif method == "tukey":
        depth = _trunc_log2(effective) - 3
    elif method == "proportion":
        prop = Fraction(0.007 if outlier_prop is None else outlier_prop)
        depth = _trunc_log2(effective) - _trunc_log2(effective * prop) + 1
    elif method == "trustworthy":
        alpha = 0.05 if trust_alpha is None else trust_alpha
        threshold = Fraction(2 * NormalDist().inv_cdf(alpha / 2) ** 2)
        depth = _trunc_log2(effective / threshold) + 1
    else:
        depth = method
    return min(MAX_LETTER_DEPTH, max(1, depth))


def _weighted_summary(
    values, weights, *, k_depth, width_method, outlier_prop, trust_alpha
):
    issues = option_issues(k_depth, width_method, outlier_prop, trust_alpha)
    if issues:
        raise ValueError("; ".join(issues))
    cdf = canonical_cdf(values, weights)
    total = cdf.total
    effective = cdf.effective_size

    depth = _weighted_depth(effective, k_depth, outlier_prop, trust_alpha)
    lower = [2.0**-e for e in range(depth + 1, 1, -1)]
    percentiles = lower + [1 - p for p in reversed(lower)]
    if k_depth == "full":
        percentiles[0], percentiles[-1] = 0.0, 1.0
    boundaries = [cdf.left(p) for p in percentiles]
    levels = list(range(depth)) + list(range(depth - 2, -1, -1))
    widths = [2.0 ** (level - depth + 1) for level in levels]
    band_masses = [
        Fraction(
            cdf.prefix(hi, closed=i == len(boundaries) - 2) - cdf.prefix(lo), total
        )
        for i, (lo, hi) in enumerate(pairwise(boundaries))
    ]
    tail_mass = Fraction(
        cdf.prefix(boundaries[0]) + total - cdf.prefix(boundaries[-1], closed=True),
        total,
    )
    if sum(band_masses, tail_mass) != 1:
        raise ValueError("weighted letter-value interval mass is not conserved")
    if width_method == "linear":
        widths = [(level + 1) / depth for level in levels]
    elif width_method == "area":
        widths = _area_widths(band_masses, boundaries, widths)
    return LetterValueSummary(
        depth,
        tuple(percentiles),
        tuple(boundaries),
        tuple(levels),
        tuple(widths),
        cdf.left(0.5),
        tuple(v for v in cdf.values if v < boundaries[0] or v > boundaries[-1]),
        tuple(band_masses),
        tail_mass,
        effective,
        tuple(Fraction(value) for value in boundaries),
    )


def _area_widths(masses, boundaries, fallback):
    """One exact span/density rule; zero-height atoms never invent dispersion."""
    spans = [Fraction(hi) - Fraction(lo) for lo, hi in pairwise(boundaries)]
    if not any(spans):
        return fallback
    densities = [
        mass / span if span > 0 else Fraction(0)
        for mass, span in zip(masses, spans, strict=True)
    ]
    maximum = max(densities)
    if maximum <= 0:
        raise ValueError("letter-value intervals lost positive mass")
    widths = [float(density / maximum) for density in densities]
    if any(d > 0 and width == 0 for d, width in zip(densities, widths, strict=True)):
        raise ValueError("positive letter-value area width is unrepresentable")
    return widths
