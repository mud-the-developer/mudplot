"""Opt-in weighted Gaussian KDE contracts and render-only numeric summaries.

Imports stay stdlib. Relative row weights (not replicated sample counts) set
unbiased covariance and effective sample size. Evaluation cut/clip never drop
fit rows or renormalize visible tails. CDF starts at -infinity, not grid.min().
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from itertools import islice

from ._ecdf import ecdf_groups, ecdf_rows, finite_number
from .spec import ECDFSpec, KDESpec, LayerSpec

MAX_KDE_POINTS = 4096
_EVALUATION_CHUNK = 2048  # never allocate a grid-by-all-observations matrix
_SQRT_TWO_PI = math.sqrt(2 * math.pi)


def kde_rows(columns: dict, layer: LayerSpec) -> list[int]:
    if not isinstance(layer.kde, KDESpec):
        return []
    return ecdf_rows(columns, replace(layer, ecdf=ECDFSpec(weights=layer.kde.weights)))


def kde_groups(columns: dict, layer: LayerSpec, rows: list[int]) -> list:
    return ecdf_groups(columns, layer, rows)


def option_issues(config: KDESpec) -> list[str]:
    issues = []
    if not (
        (
            isinstance(config.bw_method, str)
            and config.bw_method in ("scott", "silverman")
        )
        or (
            not isinstance(config.bw_method, str)
            and finite_number(config.bw_method)
            and 0 < config.bw_method <= 1000
        )
    ):
        issues.append("bw_method must be scott/silverman or finite factor in (0,1000]")
    if not finite_number(config.bw_adjust) or not 0 < config.bw_adjust <= 1000:
        issues.append("bw_adjust must be finite in (0,1000]")
    if type(config.gridsize) is not int or not 2 <= config.gridsize <= MAX_KDE_POINTS:
        issues.append(f"gridsize must be integer in [2,{MAX_KDE_POINTS}]")
    if not finite_number(config.cut) or not 0 <= config.cut <= 10:
        issues.append("cut must be finite in [0,10] bandwidth units")
    clip = config.clip
    if clip is not None:
        valid = isinstance(clip, (list, tuple)) and len(clip) == 2
        if valid:
            low, high = clip
            valid = all(v is None or finite_number(v) for v in clip)
            if valid and low is not None and high is not None:
                valid = low < high
        if not valid:
            issues.append("clip must be increasing finite/None [lower,upper] bounds")
    for name in ("common_norm", "common_grid", "cumulative", "fill", "warn_singular"):
        if type(getattr(config, name)) is not bool:
            issues.append(f"{name} must be boolean")
    return issues


@dataclass(frozen=True)
class KDECurve:
    group: object
    support: tuple[float, ...]
    heights: tuple[float, ...]
    bandwidth: float | None
    singular: bool = False


@dataclass(frozen=True)
class _Fit:
    values: tuple[float, ...]
    weights: tuple[float, ...]
    bandwidth: float


def _positive_product(*factors: float) -> float:
    """Multiply positive finite factors without premature scale overflow/underflow."""
    mantissa, exponent = 1.0, 0
    for factor in factors:
        part, power = math.frexp(factor)
        mantissa *= part
        exponent += power
    try:
        return math.ldexp(mantissa, exponent)
    except OverflowError as exc:
        raise ValueError("KDE bandwidth must be positive and finite") from exc


def _fit(pairs: list[tuple[float, float]], config: KDESpec) -> _Fit | None:
    if len(pairs) < 2 or pairs[0][0] == pairs[-1][0]:
        return None  # no finite continuous density; never invent fallback bandwidth
    values, weights = zip(*pairs, strict=True)
    wscale = max(weights)
    scaled = [weight / wscale for weight in weights]
    total = math.fsum(scaled)
    probabilities = [weight / total for weight in scaled]
    neff = 1 / math.fsum(p * p for p in probabilities)
    # 1-sum(p**2) loses a dominant weight's tiny companions. Sum cross-products
    # instead; positive-only ascending sums keep the unbiased correction usable.
    ordered = sorted(probabilities)
    prefix = 0.0
    cross = []
    for probability in ordered:
        cross.append(probability * prefix)
        prefix += probability
    correction = 2 * math.fsum(cross)
    scale = max(abs(v) for v in values) or 1.0
    anchor = values[0]
    # Direct differences retain nearby-value low bits; scaled differences avoid
    # overflow for opposite finite extremes. Center before computing variance.
    offsets = [
        (v - anchor) / scale
        if math.isfinite(v - anchor)
        else v / scale - anchor / scale
        for v in values
    ]
    mean = math.fsum(p * v for p, v in zip(probabilities, offsets, strict=True))
    variance = math.fsum(
        p * (v - mean) ** 2 for p, v in zip(probabilities, offsets, strict=True)
    )
    if correction <= 0 or variance <= 0:
        raise ValueError("KDE cannot resolve positive finite weighted bandwidth")
    factor = (
        neff ** (-0.2)
        if config.bw_method == "scott"
        else (neff * 0.75) ** (-0.2)
        if config.bw_method == "silverman"
        else float(config.bw_method)
    )
    bandwidth = _positive_product(
        math.sqrt(variance / correction), factor, config.bw_adjust, scale
    )
    if not math.isfinite(bandwidth) or bandwidth <= 0:
        raise ValueError("KDE bandwidth must be positive and finite")
    return _Fit(values, weights, bandwidth)


def _support(fit: _Fit, config: KDESpec):
    import numpy as np

    extension = config.cut * fit.bandwidth
    low, high = fit.values[0] - extension, fit.values[-1] + extension
    if config.clip is not None:
        low = low if config.clip[0] is None else max(low, config.clip[0])
        high = high if config.clip[1] is None else min(high, config.clip[1])
    if not all(math.isfinite(v) for v in (low, high)):
        raise ValueError(
            "KDE derived support must be finite; reduce cut or provide clip"
        )
    if low >= high:
        raise ValueError("KDE support is empty after cut/clip (fit rows unchanged)")
    t = np.linspace(0, 1, config.gridsize)
    # Avoid high-low overflow; exact endpoints and no unresolvable duplicate grid.
    grid = low * (1 - t) + high * t
    if not np.all(np.isfinite(grid)) or not np.all(grid[1:] > grid[:-1]):
        raise ValueError("KDE grid must be finite strictly increasing; change support")
    return grid


def _terms(point, fit: _Fit, weight_scale: float, *, cumulative: bool):
    import numpy as np

    values, weights = iter(fit.values), iter(fit.weights)
    scale = max(abs(point), abs(fit.values[0]), abs(fit.values[-1])) or 1.0
    while part := list(islice(values, _EVALUATION_CHUNK)):
        mass = np.array(list(islice(weights, _EVALUATION_CHUNK))) / weight_scale
        data = np.array(part)
        with np.errstate(
            over="ignore", under="ignore", invalid="ignore", divide="ignore"
        ):
            delta = point - data
            z = np.where(
                np.isfinite(delta),
                delta / fit.bandwidth,
                (point / scale - data / scale) / (fit.bandwidth / scale),
            )
            if cumulative:
                kernel = np.fromiter(
                    (0.5 * math.erfc(-v / math.sqrt(2)) for v in z), float, len(z)
                )
            else:
                kernel = np.exp(-0.5 * z**2)
        yield from (mass * kernel).tolist()


def kde_summary(columns: dict, layer: LayerSpec) -> tuple[KDECurve, ...]:
    """Fit all groups before artists; deterministic sorted rows, bounded evaluation."""
    config = layer.kde
    if not isinstance(config, KDESpec):
        raise ValueError("kde_summary requires KDESpec")
    rows = kde_rows(columns, layer)
    groups = kde_groups(columns, layer, rows)
    pairs = {group: [] for group in groups}
    for i in rows:
        group = None if layer.group is None else columns[layer.group][i]
        weight = 1.0 if config.weights is None else float(columns[config.weights][i])
        pairs[group].append((float(columns[layer.x][i]), weight))
    for observations in pairs.values():
        observations.sort()
    pooled = sorted(pair for observations in pairs.values() for pair in observations)
    shared_scale = max((w for _, w in pooled), default=1.0)
    shared_total = math.fsum(w / shared_scale for _, w in pooled)
    fits = {
        group: _fit(observations, config) if observations else None
        for group, observations in pairs.items()
    }
    # Empty/singular groups reserve slots, but never fabricate grid/density.
    pooled_fit = (
        _fit(pooled, config)
        if pooled and any(fits.values()) and config.common_grid
        else None
    )
    shared_grid = _support(pooled_fit, config) if pooled_fit is not None else None
    result = []
    for group in groups:
        fit = fits[group]
        if fit is None:
            result.append(KDECurve(group, (), (), None, bool(pairs[group])))
            continue
        grid = _support(fit, config) if shared_grid is None else shared_grid
        scale = shared_scale if config.common_norm else max(fit.weights)
        total = (
            shared_total
            if config.common_norm
            else math.fsum(w / scale for w in fit.weights)
        )
        heights = [
            math.fsum(_terms(point, fit, scale, cumulative=config.cumulative)) / total
            for point in grid
        ]
        if not config.cumulative:
            heights = [height / _SQRT_TWO_PI / fit.bandwidth for height in heights]
        if not all(math.isfinite(h) and h >= 0 for h in heights):
            raise ValueError("KDE derived density/CDF must be finite nonnegative")
        result.append(
            KDECurve(group, tuple(grid.tolist()), tuple(heights), fit.bandwidth)
        )
    return tuple(result)
