"""Dependency-free letter-value summaries, not confidence intervals or KDE.

Tail stopping rules follow the Seaborn 0.13.2 LetterValues definitions (based on
Hofmann/Wickham/Kafadar's letter-value plots). Quantiles use linear interpolation.
Named depths are capped at 32; explicit depths must be in 1..32. Sorting and all
calculations are deterministic and never use random state or optional packages.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import pairwise
from numbers import Real
from statistics import NormalDist

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


def _quantile(ordered: list[float], p: float) -> float:
    index = (len(ordered) - 1) * p
    low = int(index)
    fraction = index - low
    lower = ordered[low]
    if fraction == 0 or lower == ordered[low + 1]:
        return lower
    upper = ordered[low + 1]
    # Convex interpolation avoids overflow in upper-lower for opposite extremes.
    interpolated = lower * (1 - fraction) + upper * fraction
    return min(upper, max(lower, interpolated))


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
    values: tuple[float, ...]  # consecutive band boundaries, not nested whiskers
    levels: tuple[int, ...]
    widths: tuple[float, ...]  # relative widths, maximum 1
    median: float
    fliers: tuple[float, ...]  # raw order; strict outside the extreme letter values


def letter_value_summary(
    values,
    *,
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
    issues = option_issues(k_depth, width_method, outlier_prop, trust_alpha)
    data = list(values)
    if not data or any(
        not isinstance(v, Real) or isinstance(v, bool) or not math.isfinite(v)
        for v in data
    ):
        issues.append("letter values require nonempty finite numeric observations")
    if issues:
        raise ValueError("; ".join(issues))
    ordered = sorted(float(v) for v in data)
    k = letter_value_depth(len(data), k_depth, outlier_prop, trust_alpha)
    lower = [2.0**-e for e in range(k + 1, 1, -1)]
    percs = lower + [1 - p for p in reversed(lower)]
    if k_depth == "full":
        percs[0], percs[-1] = 0.0, 1.0
    boundaries = [_quantile(ordered, p) for p in percs]
    levels = list(range(k)) + list(range(k - 2, -1, -1))
    widths = [2.0 ** (level - k + 1) for level in levels]
    if width_method == "linear":
        widths = [(level + 1) / k for level in levels]
    elif width_method == "area":
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
        _quantile(ordered, 0.5),
        tuple(float(v) for v in data if v < boundaries[0] or v > boundaries[-1]),
    )
