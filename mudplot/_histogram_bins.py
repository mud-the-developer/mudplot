"""Bounded float64 bin rules, fixed to NumPy 1.23.5 histogram equations.

Reference: numpy/lib/histograms.py (v1.23.5), estimator formulas only.
No optional numeric dependency is imported until an edge effect is requested.
"""

import math
import warnings
from numbers import Real

MAX_HISTOGRAM_BINS = 10_000
HISTOGRAM_BIN_RULES = (
    "auto",
    "fd",
    "doane",
    "scott",
    "stone",
    "rice",
    "sturges",
    "sqrt",
)


def _count(count):
    if not math.isfinite(count) or count <= 0 or count > MAX_HISTOGRAM_BINS:
        raise ValueError("histogram bin count must be finite and within 1..10000")
    return math.ceil(count)


def _edges(low, high, count):
    import numpy as np

    count = _count(count)
    edges = np.linspace(low, high, count + 1)
    with np.errstate(over="ignore", invalid="ignore"):
        widths = np.diff(edges)
    if not np.all(np.isfinite(edges)) or not np.all(np.isfinite(widths) & (widths > 0)):
        raise ValueError("histogram edges and widths must be finite and increasing")
    return edges


def named_bin_edges(values, rule):
    """Estimate unweighted edges from selected observations, never coarsening."""
    import numpy as np

    if not isinstance(rule, str) or rule not in HISTOGRAM_BIN_RULES:
        raise ValueError("unknown histogram bin rule")
    x = np.asarray(values, dtype=np.float64)
    if x.ndim != 1 or not np.all(np.isfinite(x)):
        raise ValueError("histogram observations must be finite and one-dimensional")
    if not x.size:
        return np.array([], dtype=float)
    low, high = float(x.min()), float(x.max())
    if low == high:
        if not low - 0.5 < low < high + 0.5:
            raise ValueError("constant histogram half-unit edges are unrepresentable")
        return _edges(low - 0.5, high + 0.5, 1)
    span = high - low
    if not math.isfinite(span):
        raise ValueError("histogram range must be finite")
    n = x.size
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        if rule in ("fd", "auto"):
            width = 2 * float(np.subtract(*np.percentile(x, [75, 25]))) / n ** (1 / 3)
            if rule == "auto":
                sturges = span / (math.log2(n) + 1)
                width = min(width, sturges) if width else sturges
        elif rule == "sturges":
            width = span / (math.log2(n) + 1)
        elif rule == "sqrt":
            width = span / math.sqrt(n)
        elif rule == "rice":
            width = span / (2 * n ** (1 / 3))
        elif rule == "scott":
            width = (24 * math.sqrt(math.pi) / n) ** (1 / 3) * float(np.std(x))
        elif rule == "doane":
            width = 0.0
            if n > 2:
                sigma = float(np.std(x))
                if sigma > 0:
                    skew = float(np.mean(((x - np.mean(x)) / sigma) ** 3))
                    error = math.sqrt(6 * (n - 2) / ((n + 1) * (n + 3)))
                    width = span / (1 + math.log2(n) + math.log2(1 + abs(skew) / error))
        else:  # Stone: every candidate allocation is checked before histogram runs.
            upper = max(100, math.isqrt(n))
            _count(upper)

            def cost(bins):
                edges = np.linspace(low, high, bins + 1)
                indexes = np.searchsorted(edges, x, side="right") - 1
                indexes[x == high] = bins - 1
                probabilities = np.bincount(indexes, minlength=bins) / n
                # The positive common span cancels when ranking candidate costs.
                return (2 - (n + 1) * probabilities.dot(probabilities)) * bins

            best = min(range(1, upper + 1), key=cost)
            if best == upper:
                warnings.warn(
                    "Stone bin estimate may be suboptimal", RuntimeWarning, stacklevel=2
                )
            width = span / best
    if not math.isfinite(width) or width < 0:
        raise ValueError("histogram rule produced an invalid width")
    count = _count(span / width) if width else 1
    return _edges(low, high, count)


def discrete_bounds(values):
    """Validate exact integer observations and preflight their unit grid span."""
    integers = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError("discrete observations must be nonbool real integers")
        try:
            number = float(value)
            integer = int(number)
        except (ValueError, OverflowError) as exc:
            raise ValueError("discrete observations must be finite integers") from exc
        if not math.isfinite(number) or value != integer or number != integer:
            raise ValueError(
                "discrete observations must be exactly representable integers"
            )
        integers.append(integer)
    if not integers:
        return None
    low, high = min(integers), max(integers)
    count = high - low + 1
    if count > MAX_HISTOGRAM_BINS:
        raise ValueError("discrete histogram bin count exceeds 10000")
    left, right = float(low) - 0.5, float(high) + 0.5
    # Half edges must be exact, not merely distinct rounded floats.
    if (
        not math.isfinite(left)
        or not math.isfinite(right)
        or left.as_integer_ratio()[0] * 2 != (2 * low - 1) * left.as_integer_ratio()[1]
        or right.as_integer_ratio()[0] * 2
        != (2 * high + 1) * right.as_integer_ratio()[1]
        or right - left != count
    ):
        raise ValueError("discrete half-unit edges or unit grid are unrepresentable")
    return left, right, count


def discrete_bin_edges(values):
    """Construct an integer-centered unit grid only after span validation."""
    bounds = discrete_bounds(values)
    import numpy as np

    if bounds is None:
        return np.array([], dtype=float)
    edges = _edges(*bounds)
    if not np.all(np.diff(edges) == 1):
        raise ValueError("discrete grid must have exactly unit widths")
    return edges
