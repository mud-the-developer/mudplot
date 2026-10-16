"""Render-only weighted bivariate Gaussian fits and conditional-grid HDR levels.

Stdlib at import/validation; NumPy is lazy. No jitter, RNG, sample replication,
log fitting or density renormalization after clip. Level fractions refer to
trapezoidal mass WITHIN the evaluated grid, not CI/full-space coverage promises.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from itertools import pairwise

from ._ecdf import ecdf_groups, ecdf_rows, finite_number
from ._kde import _positive_product
from ._kde import option_issues as univariate_option_issues
from ._stat import is_missing
from .spec import ECDFSpec, KDE2DSpec, KDESpec, LayerSpec

MAX_KDE2D_POINTS = 256
MAX_KDE2D_ROWS = 10000
MAX_KDE2D_LEVELS = 16
_POINT_CHUNK = 32
_ROW_CHUNK = 1024
_RANK_TOLERANCE = 64 * 2.220446049250313e-16


def kde2d_config(layer: LayerSpec) -> KDE2DSpec:
    return KDE2DSpec() if layer.kde2d is None else layer.kde2d


def kde2d_rows(columns: dict, layer: LayerSpec) -> list[int]:
    if layer.kde2d is not None and not isinstance(layer.kde2d, KDE2DSpec):
        return []
    if (
        not isinstance(layer.x, str)
        or layer.x not in columns
        or not isinstance(layer.y, str)
        or layer.y not in columns
        or not isinstance(columns[layer.x], (list, tuple))
        or not isinstance(columns[layer.y], (list, tuple))
        or len(columns[layer.x]) != len(columns[layer.y])
    ):
        return []
    config = kde2d_config(layer)
    view = replace(layer, ecdf=ECDFSpec(weights=config.weights))
    return [i for i in ecdf_rows(columns, view) if not is_missing(columns[layer.y][i])]


def kde2d_groups(columns: dict, layer: LayerSpec, rows: list[int]) -> list:
    return ecdf_groups(columns, layer, rows)


def option_issues(config: KDE2DSpec) -> list[str]:
    # Share only the actual scalar/boolean bandwidth contracts, not 1-D semantics.
    issues = univariate_option_issues(
        KDESpec(
            bw_method=config.bw_method,
            bw_adjust=config.bw_adjust,
            cut=config.cut,
            common_norm=config.common_norm,
            common_grid=config.common_grid,
            fill=config.fill,
            warn_singular=config.warn_singular,
        )
    )
    if type(config.gridsize) is not int or not 2 <= config.gridsize <= MAX_KDE2D_POINTS:
        issues.append(f"gridsize must be integer in [2,{MAX_KDE2D_POINTS}]")
    clip = config.clip
    if clip is not None:
        valid = isinstance(clip, (list, tuple)) and len(clip) == 2
        if valid:
            for bound in clip:
                if not isinstance(bound, (list, tuple)) or len(bound) != 2:
                    valid = False
                    break
                low, high = bound
                if not all(v is None or finite_number(v) for v in bound) or (
                    low is not None and high is not None and low >= high
                ):
                    valid = False
                    break
        if not valid:
            issues.append(
                "clip must be [[xlo,xhi],[ylo,yhi]] finite/None increasing bounds"
            )
    levels = config.levels
    valid = isinstance(levels, (list, tuple)) and 1 <= len(levels) <= MAX_KDE2D_LEVELS
    if valid:
        valid = all(finite_number(p) and 0 < p < 1 for p in levels)
        valid = valid and all(a < b for a, b in pairwise(levels))
    if not valid:
        issues.append(
            f"levels require 1..{MAX_KDE2D_LEVELS} increasing "
            "enclosed fractions in (0,1)"
        )
    return issues


@dataclass(frozen=True)
class KDE2DField:
    group: object
    x: tuple[float, ...]
    y: tuple[float, ...]
    density: tuple[tuple[float, ...], ...]
    bandwidths: tuple[float, float] | None
    correlation: float | None
    thresholds: tuple[float, ...] = ()  # ascending density for native contours
    requested_mass: tuple[float, ...] = ()  # aligned, hence descending fractions
    enclosed_mass: tuple[float, ...] = ()  # ties all included, may exceed request
    grid_mass: float = 0.0  # approximate raw-unit integral, NOT forcibly <=1
    singular: bool = False


@dataclass(frozen=True)
class _Fit2D:
    x: tuple[float, ...]
    y: tuple[float, ...]
    weights: tuple[float, ...]
    bandwidths: tuple[float, float]
    correlation: float
    residual: float  # sqrt(1-rho**2), stable via (1-rho)*(1+rho)


def _offsets(values):
    low, high = min(values), max(values)
    spread = high - low
    scale = (
        spread
        if math.isfinite(spread) and spread > 0
        else max(abs(low), abs(high)) or 1.0
    )
    offsets = [
        (v - low) / scale if math.isfinite(v - low) else v / scale - low / scale
        for v in values
    ]
    return offsets, scale


def _fit(pairs: list[tuple[float, float, float]], config: KDE2DSpec) -> _Fit2D | None:
    if len(pairs) < 3:
        return None
    x, y, weights = zip(*pairs, strict=True)
    if min(x) == max(x) or min(y) == max(y):
        return None
    weight_scale = max(weights)
    scaled = [w / weight_scale for w in weights]
    total = math.fsum(scaled)
    p = [w / total for w in scaled]
    neff = 1 / math.fsum(w * w for w in p)
    prefix = 0.0
    cross = []
    for weight in sorted(p):
        cross.append(weight * prefix)
        prefix += weight
    correction = 2 * math.fsum(cross)
    if correction <= 0:
        raise ValueError("KDE2D cannot resolve positive weighted covariance")
    ox, sx = _offsets(x)
    oy, sy = _offsets(y)
    mx = math.fsum(w * v for w, v in zip(p, ox, strict=True))
    my = math.fsum(w * v for w, v in zip(p, oy, strict=True))
    dx = [v - mx for v in ox]
    dy = [v - my for v in oy]
    xx = math.fsum(w * v * v for w, v in zip(p, dx, strict=True)) / correction
    yy = math.fsum(w * v * v for w, v in zip(p, dy, strict=True)) / correction
    xy = math.fsum(w * a * b for w, a, b in zip(p, dx, dy, strict=True)) / correction
    if xx <= 0 or yy <= 0:
        raise ValueError("KDE2D cannot resolve positive weighted covariance")
    denominator = _positive_product(math.sqrt(xx), math.sqrt(yy))
    if denominator <= 0:
        raise ValueError("KDE2D cannot resolve finite covariance correlation")
    rho = xy / denominator
    if not math.isfinite(rho):
        raise ValueError("KDE2D covariance correlation must be finite")
    if 1 - abs(rho) <= _RANK_TOLERANCE:
        return None  # rank deficient at double precision, never regularize/jitter
    factor = neff ** (-1 / 6) if isinstance(config.bw_method, str) else config.bw_method
    hx = _positive_product(math.sqrt(xx), factor, config.bw_adjust, sx)
    hy = _positive_product(math.sqrt(yy), factor, config.bw_adjust, sy)
    if not all(math.isfinite(h) and h > 0 for h in (hx, hy)):
        raise ValueError("KDE2D bandwidths must be positive and finite")
    return _Fit2D(x, y, weights, (hx, hy), rho, math.sqrt((1 - rho) * (1 + rho)))


def _support(fit: _Fit2D, config: KDE2DSpec):
    import numpy as np

    grids = []
    for axis, (values, width) in enumerate(
        zip((fit.x, fit.y), fit.bandwidths, strict=True)
    ):
        low, high = min(values) - config.cut * width, max(values) + config.cut * width
        if config.clip is not None:
            a, b = config.clip[axis]
            low = low if a is None else max(low, a)
            high = high if b is None else min(high, b)
        if not all(math.isfinite(v) for v in (low, high)):
            raise ValueError(
                "KDE2D derived support must be finite; reduce cut/provide clip"
            )
        if low >= high:
            raise ValueError(
                "KDE2D support is empty after cut/clip (fit rows unchanged)"
            )
        t = np.linspace(0, 1, config.gridsize)
        grid = low * (1 - t) + high * t
        if not np.all(np.isfinite(grid)) or not np.all(grid[1:] > grid[:-1]):
            raise ValueError("KDE2D grid must be finite strictly increasing")
        grids.append(grid)
    return tuple(grids)


def _ratio_product(numerators, denominators) -> float:
    if any(n == 0 for n in numerators):
        return 0.0
    mantissa, exponent = 1.0, 0
    for factors, sign in ((numerators, 1), (denominators, -1)):
        for factor in factors:
            part, power = math.frexp(factor)
            mantissa = mantissa * part if sign == 1 else mantissa / part
            exponent += sign * power
    try:
        value = math.ldexp(mantissa, exponent)
    except OverflowError as exc:
        raise ValueError("KDE2D derived density/grid mass must be finite") from exc
    if not math.isfinite(value):
        raise ValueError("KDE2D derived density/grid mass must be finite")
    return value


def _standardized(points, values, bandwidth):
    import numpy as np

    scale = max(float(np.max(np.abs(points))), float(np.max(np.abs(values)))) or 1.0
    delta = points[:, None] - values[None, :]
    return np.where(
        np.isfinite(delta),
        delta / bandwidth,
        (points[:, None] / scale - values[None, :] / scale) / (bandwidth / scale),
    )


def _evaluate(fit: _Fit2D, gx, gy, weight_scale, total):
    import numpy as np

    xx, yy = np.meshgrid(gx, gy)
    nodes = np.column_stack((xx.ravel(), yy.ravel()))
    local_scale = max(fit.weights)
    density = []
    for first in range(0, len(nodes), _POINT_CHUNK):
        points = nodes[first : first + _POINT_CHUNK]
        sums = [[] for _ in points]
        for start in range(0, len(fit.x), _ROW_CHUNK):
            x = np.asarray(fit.x[start : start + _ROW_CHUNK])
            y = np.asarray(fit.y[start : start + _ROW_CHUNK])
            mass = np.asarray(fit.weights[start : start + _ROW_CHUNK]) / local_scale
            with np.errstate(
                over="ignore", under="ignore", invalid="ignore", divide="ignore"
            ):
                a = _standardized(points[:, 0], x, fit.bandwidths[0])
                b = _standardized(points[:, 1], y, fit.bandwidths[1])
                valid = np.isfinite(a) & np.isfinite(b)
                residual = (b - fit.correlation * a) / fit.residual
                kernel = (
                    np.where(valid, np.exp(-0.5 * (a * a + residual * residual)), 0.0)
                    * mass
                )
            for accumulator, terms in zip(sums, kernel, strict=True):
                accumulator.append(math.fsum(terms.tolist()))
        for accumulator in sums:
            density.append(
                _ratio_product(
                    (math.fsum(accumulator), local_scale),
                    (weight_scale, total, 2 * math.pi, *fit.bandwidths, fit.residual),
                )
            )
    field = np.asarray(density).reshape(len(gy), len(gx))
    if not np.all(np.isfinite(field)) or np.any(field < 0):
        raise ValueError("KDE2D derived density must be finite nonnegative")
    return field


def _node_weights(grid):
    import numpy as np

    scale = max(abs(float(grid[0])), abs(float(grid[-1]))) or 1.0
    # Direct widths retain nearby-node low bits; scaled fallback avoids overflow.
    with np.errstate(over="ignore", invalid="ignore"):
        delta = np.diff(grid)
        widths = np.where(np.isfinite(delta), delta / scale, np.diff(grid / scale))
    weights = np.r_[widths[0] / 2, (widths[:-1] + widths[1:]) / 2, widths[-1] / 2]
    return weights, scale


def conditional_levels(gx, gy, density, levels):
    """Descending density strata + trapezoidal node masses, ties all included."""
    import numpy as np

    wx, sx = _node_weights(gx)
    wy, sy = _node_weights(gy)
    peak = float(np.max(density))
    minimum = float(np.min(density))
    if peak <= 0:
        raise ValueError(
            "KDE2D grid needs positive resolvable mass; change support/grid"
        )
    masses = (density / peak) * np.outer(wy, wx)
    total = math.fsum(masses.ravel().tolist())
    if not math.isfinite(total) or total <= 0:
        raise ValueError(
            "KDE2D grid needs positive resolvable mass; change support/grid"
        )
    raw_mass = _ratio_product((total, peak, sx, sy), ())
    if raw_mass <= 0:
        raise ValueError(
            "KDE2D grid mass is unresolvable; change normalization/support"
        )
    # Normalize dimensionless quadrature only for HDR selection. The density
    # field and reported raw integral are unchanged by conditional level choice.
    order = np.argsort(-density.ravel(), kind="stable")
    heights = density.ravel()[order]
    from ._ecdf import _cumulative

    prefixes = _cumulative(masses.ravel()[order].tolist())
    thresholds = []
    included = []
    for fraction in levels:
        index = int(np.searchsorted(prefixes, fraction * total, side="left"))
        height = float(heights[min(index, len(heights) - 1)])
        stop = int(np.searchsorted(-heights, -height, side="right")) - 1
        thresholds.append(height)
        included.append(prefixes[stop] / total)
    if len(set(thresholds)) != len(thresholds) or any(
        not minimum < h < peak for h in thresholds
    ):
        raise ValueError(
            "KDE2D enclosed levels are unresolved; increase grid/change levels"
        )
    return tuple(thresholds[::-1]), tuple(included[::-1]), raw_mass


def kde2d_summary(columns: dict, layer: LayerSpec) -> tuple[KDE2DField, ...]:
    config = kde2d_config(layer)
    if not isinstance(config, KDE2DSpec):
        raise ValueError("kde2d_summary requires KDE2DSpec or None")
    rows = kde2d_rows(columns, layer)
    groups = kde2d_groups(columns, layer, rows)
    pairs = {g: [] for g in groups}
    for i in rows:
        group = None if layer.group is None else columns[layer.group][i]
        weight = 1.0 if config.weights is None else float(columns[config.weights][i])
        pairs[group].append(
            (float(columns[layer.x][i]), float(columns[layer.y][i]), weight)
        )
    for data in pairs.values():
        data.sort()
    pooled = sorted(pair for data in pairs.values() for pair in data)
    scale = max((w for _, _, w in pooled), default=1.0)
    total = math.fsum(w / scale for _, _, w in pooled)
    fits = {g: _fit(data, config) if data else None for g, data in pairs.items()}
    pooled_fit = (
        _fit(pooled, config)
        if pooled and any(fits.values()) and config.common_grid
        else None
    )
    shared = _support(pooled_fit, config) if pooled_fit is not None else None
    result = []
    for group in groups:
        fit = fits[group]
        if fit is None:
            result.append(
                KDE2DField(group, (), (), (), None, None, singular=bool(pairs[group]))
            )
            continue
        gx, gy = _support(fit, config) if shared is None else shared
        denominator_scale = scale if config.common_norm else max(fit.weights)
        denominator = (
            total
            if config.common_norm
            else math.fsum(w / denominator_scale for w in fit.weights)
        )
        density = _evaluate(fit, gx, gy, denominator_scale, denominator)
        thresholds, enclosed, mass = conditional_levels(gx, gy, density, config.levels)
        result.append(
            KDE2DField(
                group,
                tuple(gx.tolist()),
                tuple(gy.tolist()),
                tuple(tuple(row) for row in density.tolist()),
                fit.bandwidths,
                fit.correlation,
                thresholds,
                tuple(config.levels[::-1]),
                enclosed,
                mass,
            )
        )
    return tuple(result)
