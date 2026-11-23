"""Opt-in weighted Gaussian KDE contracts and render-only numeric summaries.

Imports stay stdlib. Relative row weights (not replicated sample counts) set
unbiased covariance and effective sample size. Evaluation cut/clip never drop
fit rows or renormalize visible tails. CDF starts at -infinity, not grid.min().
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from fractions import Fraction
from itertools import islice, pairwise
from typing import TYPE_CHECKING

from ._ecdf import (
    canonical_units,
    covariance_units,
    ecdf_groups,
    ecdf_rows,
    finite_number,
)
from ._field_budget import FieldBudget
from ._kernel_math import IntervalMath, KernelPrecisionError
from .spec import ECDFSpec, KDE2DSpec, KDESpec, LayerSpec

if TYPE_CHECKING:
    from ._density_input import FieldInput

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
                valid = float(low) < float(high)
        if not valid:
            issues.append("clip must be increasing finite/None [lower,upper] bounds")
    for name in ("common_norm", "common_grid", "cumulative", "fill", "warn_singular"):
        if type(getattr(config, name)) is not bool:
            issues.append(f"{name} must be boolean")
    from ._density import kde_extra_issues

    issues.extend(kde_extra_issues(config))
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
        low = low if config.clip[0] is None else max(low, float(config.clip[0]))
        high = high if config.clip[1] is None else min(high, float(config.clip[1]))
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


def _fraction_box(interval):
    return Fraction(interval[0]), Fraction(interval[1])


def _scaled_sqrt_bounds(arithmetic, lower, upper, factor):
    if lower < 0 or lower > upper:
        raise KernelPrecisionError("source covariance bounds are unresolved")
    low = arithmetic.combine_scaled(
        [
            arithmetic.sqrt_fraction_scaled(lower),
            factor,
        ]
    )
    high = arithmetic.combine_scaled(
        [
            arithmetic.sqrt_fraction_scaled(upper),
            factor,
        ]
    )
    return arithmetic.finish_scaled(*arithmetic.scaled_hull(low, high))


def _bandwidth_factor(arithmetic, effective_n, dimensions, config):
    if isinstance(config.bw_method, str):
        base = effective_n
        if config.bw_method == "silverman":
            base *= Fraction(dimensions + 2, 4)
        exponent = arithmetic.mul(
            arithmetic.log_fraction(base),
            arithmetic.fraction(Fraction(-1, dimensions + 4)),
        )
        factor = arithmetic.exp_signed_scaled(exponent)
    else:
        raw = Fraction(config.bw_method)
        factor = arithmetic.scaled_ratio(raw.numerator, raw.denominator)
    adjust = Fraction(config.bw_adjust)
    return arithmetic.combine_scaled(
        [
            factor,
            arithmetic.scaled_ratio(adjust.numerator, adjust.denominator),
        ]
    )


def _fit_coordinate(value, logarithmic, arithmetic):
    if not logarithmic:
        exact = Fraction(value)
        return exact, (exact, exact)
    lower, upper = arithmetic.log10_fraction(value)
    bounds = Fraction(lower), Fraction(upper)
    return (bounds[0] + bounds[1]) / 2, bounds


def _source_covariance_error(
    units_x,
    units_y,
    denominator_x,
    denominator_y,
    masses,
    total,
    correction,
    mean_x,
    mean_y,
    error_x,
    error_y,
    arithmetic,
):
    """Exact perturbation bound BEFORE native/source-law membership decisions."""
    if not error_x and not error_y:
        return Fraction(0)
    if arithmetic.budget is not None:
        bits = max(
            max(abs(value).bit_length() for value in (*units_x, *units_y)),
            max(value.bit_length() for value in masses),
        )
        arithmetic.budget.charge(
            "integer_source_covariance_error",
            6 * len(masses) + 8,
            bits=4 * bits + total.bit_length(),
        )
    spread_x = sum(
        mass * abs(Fraction(value, denominator_x) - mean_x)
        for mass, value in zip(masses, units_x, strict=True)
    )
    spread_y = (
        spread_x
        if units_y is units_x
        else sum(
            mass * abs(Fraction(value, denominator_y) - mean_y)
            for mass, value in zip(masses, units_y, strict=True)
        )
    )
    return (
        error_x * spread_y + error_y * spread_x + 2 * total * error_x * error_y
    ) * Fraction(total, correction)


def _source_lower(
    arithmetic, covariance, errors, dimensions, factor
) -> tuple[tuple[float, float], ...]:
    xx, xy, yy = covariance
    exx, exy, eyy = errors
    low_x, high_x = xx - exx, xx + exx
    if low_x <= 0:
        raise KernelPrecisionError("source variance positivity is unresolved")
    l00 = _scaled_sqrt_bounds(arithmetic, low_x, high_x, factor)
    if dimensions == 1:
        if l00[0] <= 0:
            raise KernelPrecisionError(
                "positive bandwidth collapses at native precision"
            )
        return (l00,)
    low_cross, high_cross = xy - exy, xy + exy
    square_high = max(low_cross * low_cross, high_cross * high_cross)
    square_low = (
        Fraction(0)
        if low_cross <= 0 <= high_cross
        else min(low_cross * low_cross, high_cross * high_cross)
    )
    schur_low = yy - eyy - square_high / low_x
    schur_high = yy + eyy - square_low / high_x
    if schur_low <= 0:
        raise KernelPrecisionError("source covariance rank/conditioning is unresolved")
    l11 = _scaled_sqrt_bounds(arithmetic, schur_low, schur_high, factor)
    if low_cross >= 0:
        l10 = _scaled_sqrt_bounds(
            arithmetic,
            low_cross * low_cross / high_x,
            high_cross * high_cross / low_x,
            factor,
        )
    elif high_cross <= 0:
        magnitude = _scaled_sqrt_bounds(
            arithmetic,
            high_cross * high_cross / high_x,
            low_cross * low_cross / low_x,
            factor,
        )
        l10 = -magnitude[1], -magnitude[0]
    else:
        negative = _scaled_sqrt_bounds(
            arithmetic,
            Fraction(0),
            low_cross * low_cross / low_x,
            factor,
        )
        positive = _scaled_sqrt_bounds(
            arithmetic,
            Fraction(0),
            high_cross * high_cross / low_x,
            factor,
        )
        l10 = -negative[1], positive[1]
    if l00[0] <= 0 or l11[0] <= 0:
        raise KernelPrecisionError("positive covariance factor collapses natively")
    return l00, l10, l11


@dataclass(slots=True)
class KernelModel:
    """ONE computed law with canonical source/parameter error propagated up front.

    Legacy omitted fits above retain their numerical route. All explicit new
    univariate/bivariate/overlay/CDF/HDR workflows share THIS fit and scalar
    kernel boundary; neither a viewport nor a histogram tally refits it.
    """

    dimensions: int
    kernel: str
    origin: tuple
    fit_bounds: tuple
    lower: tuple
    lower_bounds: tuple
    centres: tuple
    centre_bounds: tuple
    inverse: tuple
    offsets: tuple
    masses: tuple[int, ...]
    total: int
    mass_parts: tuple
    determinant_inverse: tuple
    amplitude_part: tuple
    log_shift: tuple
    raw_parts: tuple
    amplitude: Fraction
    log_axes: tuple[bool, ...]
    source_tv: float
    arithmetic: IntervalMath
    budget: FieldBudget | None
    source_rows: tuple[int, ...]
    leases: list = field(default_factory=list, repr=False)

    def close(self):
        for lease in reversed(self.leases):
            lease.close()
        self.leases.clear()
        self.centres = ()
        self.centre_bounds = ()
        self.offsets = ()
        self.masses = ()
        self.mass_parts = ()
        self.raw_parts = ()
        self.source_rows = ()

    def native_coordinate(self, value, logical_axis):
        """Return native coordinate AND its outward source/forward enclosure."""
        arithmetic = self.arithmetic
        if self.log_axes[logical_axis]:
            bounds = arithmetic.finish_scaled(
                *arithmetic.exp_signed_scaled(
                    arithmetic.mul(arithmetic.fraction(value), arithmetic.ln10)
                )
            )
            native = arithmetic.midpoint(bounds)
            if native <= 0:
                raise KernelPrecisionError(
                    "positive inverse-log coordinate collapses natively"
                )
        else:
            bounds = arithmetic.fraction(value)
            native = float(value)
        if not math.isfinite(native):
            raise KernelPrecisionError("kernel native coordinate is unrepresentable")
        return native, bounds

    def evaluation_bounds(self, config):
        """Cut/clip choose queries only; no model refit or tail rebasing."""
        result = []
        for axis, observed in enumerate(self.fit_bounds):
            if axis == 0:
                bandwidth = self.lower_bounds[0][1]
            else:
                bandwidth = self.arithmetic.sqrt_fraction(
                    Fraction(max(abs(value) for value in self.lower_bounds[1])) ** 2
                    + Fraction(self.lower_bounds[2][1]) ** 2
                )[1]
            extension = Fraction(config.cut) * Fraction(bandwidth)
            low, high = observed[0] - extension, observed[1] + extension
            clip = config.clip
            bound = (
                None if clip is None else clip if self.dimensions == 1 else clip[axis]
            )
            if bound is not None:
                if bound[0] is not None:
                    edge = _fit_coordinate(
                        bound[0], self.log_axes[axis], self.arithmetic
                    )[0]
                    low = max(low, edge)
                if bound[1] is not None:
                    edge = _fit_coordinate(
                        bound[1], self.log_axes[axis], self.arithmetic
                    )[0]
                    high = min(high, edge)
            if not low < high:
                raise ValueError("KDE cut/clip leaves no finite query interval")
            result.append((low, high))
        return tuple(result)

    def query_chart(self, coordinates):
        """Subtract canonical origins BEFORE float, including calendar epochs."""
        arithmetic = self.arithmetic
        fit = [
            _fit_coordinate(value, logarithmic, arithmetic)[1]
            for value, logarithmic in zip(coordinates, self.log_axes, strict=True)
        ]
        return self.fit_chart(fit), fit

    def fit_chart(self, fit):
        """The same canonical origin/Cholesky inverse for working intervals."""
        arithmetic = self.arithmetic
        x = tuple(
            (value - self.origin[0]) / Fraction(self.lower[0]) for value in fit[0]
        )
        chart = [arithmetic.fraction_bounds(*x)]
        if self.dimensions == 2:
            dx = arithmetic.rational_mul((Fraction(self.lower[1]),) * 2, x)
            y = arithmetic.rational_div(
                arithmetic.rational_sub(
                    tuple(value - self.origin[1] for value in fit[1]), dx
                ),
                (Fraction(self.lower[2]),) * 2,
            )
            chart.append(arithmetic.fraction_bounds(*y))
        return tuple(chart)

    def _fit_box(self, box):
        arithmetic = self.arithmetic
        x = arithmetic.rational_add(
            (self.origin[0],) * 2,
            arithmetic.rational_mul(
                (Fraction(self.lower[0]),) * 2, _fraction_box(box[0])
            ),
        )
        if self.dimensions == 1:
            return (x,)
        y = arithmetic.rational_add(
            (self.origin[1],) * 2,
            arithmetic.rational_add(
                arithmetic.rational_mul(
                    (Fraction(self.lower[1]),) * 2, _fraction_box(box[0])
                ),
                arithmetic.rational_mul(
                    (Fraction(self.lower[2]),) * 2, _fraction_box(box[1])
                ),
            ),
        )
        return x, y

    def jacobian_scaled(self, fit):
        """Raw-density Jacobian, NEVER applied to a cumulative probability."""
        arithmetic = self.arithmetic
        factors = []
        inverse_ln10 = arithmetic.reciprocal_scaled(
            arithmetic.normalize(arithmetic.ln10, 0)
        )
        for bounds, logarithmic in zip(fit, self.log_axes, strict=True):
            if logarithmic:
                exponent = arithmetic.mul(
                    arithmetic.fraction_bounds(-bounds[1], -bounds[0]),
                    arithmetic.ln10,
                )
                factors.extend(
                    [
                        arithmetic.exp_signed_scaled(exponent),
                        inverse_ln10,
                    ]
                )
        return arithmetic.combine_scaled(factors)

    def pdf_box_scaled(self, box, *, density_space="fit", amplitude=True):
        arithmetic = self.arithmetic
        common = self.determinant_inverse
        if amplitude:
            common = arithmetic.combine_scaled(
                [
                    common,
                    self.amplitude_part,
                ]
            )
        raw_gaussian = (
            density_space == "data" and any(self.log_axes) and self.kernel == "gaussian"
        )
        if density_space == "data" and any(self.log_axes) and not raw_gaussian:
            common = arithmetic.combine_scaled(
                [
                    common,
                    self.jacobian_scaled(self._fit_box(box)),
                ]
            )
        total = ((0.0, 0.0), 0)
        parts = self.raw_parts if raw_gaussian else self.mass_parts
        for mass_part, offset in zip(parts, self.offsets, strict=True):
            if self.budget is not None:
                self.budget.charge("component_density_visits")
            z = [arithmetic.add(arithmetic.mul(self.inverse[0], box[0]), offset[0])]
            if self.dimensions == 2:
                z.append(
                    arithmetic.add(
                        arithmetic.add(
                            arithmetic.mul(self.inverse[1], box[0]),
                            arithmetic.mul(self.inverse[2], box[1]),
                        ),
                        offset[1],
                    )
                )
            if raw_gaussian:
                # phi(z)*exp(-s.z) = exp(|s|²/2)*phi(z+s).
                # Probability integration below STILL uses the original law.
                z = [
                    arithmetic.add(value, shift)
                    for value, shift in zip(z, self.log_shift, strict=True)
                ]
            part = arithmetic.combine_scaled(
                [
                    mass_part,
                    *(arithmetic.kernel_pdf(self.kernel, value) for value in z),
                ]
            )
            total = arithmetic.sum_scaled((total, part))
        return arithmetic.combine_scaled([total, common])

    def pdf_scaled(self, coordinates, *, density_space="data"):
        chart, _fit = self.query_chart(coordinates)
        return self.pdf_box_scaled(chart, density_space=density_space)

    def cdf1d_scaled(self, coordinate):
        if self.dimensions != 1:
            raise ValueError("univariate analytic CDF requires one logical input")
        arithmetic = self.arithmetic
        chart, _fit = self.query_chart((coordinate,))
        total = ((0.0, 0.0), 0)
        for mass_part, offset in zip(self.mass_parts, self.offsets, strict=True):
            if self.budget is not None:
                self.budget.charge("component_cdf_visits")
            value = arithmetic.add(arithmetic.mul(self.inverse[0], chart[0]), offset[0])
            part = arithmetic.combine_scaled(
                [
                    mass_part,
                    arithmetic.kernel_cdf(self.kernel, value),
                ]
            )
            total = arithmetic.sum_scaled((total, part))
        return arithmetic.combine_scaled([total, self.amplitude_part])

    def rectangle_mass(self, box):
        """Computed ORIGINAL law mass; add source_tv ONCE to a region union."""
        arithmetic = self.arithmetic
        total = ((0.0, 0.0), 0)
        for mass_part, centre in zip(self.mass_parts, self.centres, strict=True):
            if self.budget is not None:
                self.budget.charge("component_rectangle_visits")
            marginal = []
            for bound, mean in zip(box, centre, strict=True):
                left = arithmetic.fraction(Fraction(bound[0]) - Fraction(mean))
                right = arithmetic.fraction(Fraction(bound[1]) - Fraction(mean))
                if self.kernel == "gaussian":
                    if left[0] >= 40 or right[1] <= -40:
                        probability = (0.0, math.ulp(0.0))
                    else:
                        lower = (
                            arithmetic.normal_interval(left[1], right[0])[0]
                            if left[1] < right[0]
                            else 0.0
                        )
                        upper = arithmetic.normal_interval(left[0], right[1])[1]
                        probability = lower, upper
                else:
                    low = arithmetic.compact_cdf(left[0])[0]
                    high = arithmetic.compact_cdf(right[1])[1]
                    other_low = arithmetic.compact_cdf(left[1])[1]
                    other_high = arithmetic.compact_cdf(right[0])[0]
                    probability = (
                        max(0.0, arithmetic.down(other_high - other_low)),
                        min(1.0, arithmetic.up(high - low)),
                    )
                marginal.append(arithmetic.normalize(probability, 0))
            part = arithmetic.combine_scaled([mass_part, *marginal])
            total = arithmetic.sum_scaled((total, part))
        return arithmetic.finish_scaled(*total)

    def logical_rectangle(
        self, xlo, xhi, ylo, yhi, tolerance, *, gaussian_workspace=None
    ):
        """True logical-input rectangle, NEVER a finite-grid conditional CDF."""
        if self.dimensions != 2:
            raise ValueError("joint CDF requires two logical inputs")
        arithmetic = self.arithmetic
        endpoints = []
        for pair, logarithmic in zip(
            ((xlo, xhi), (ylo, yhi)), self.log_axes, strict=True
        ):
            endpoints.append(
                tuple(
                    None
                    if value is None
                    else _fit_coordinate(value, logarithmic, arithmetic)[1]
                    for value in pair
                )
            )
        slope = arithmetic.fraction(Fraction(self.lower[1]) / Fraction(self.lower[2]))
        total = ((0.0, 0.0), 0)
        for centre, mass in zip(self.centres, self.mass_parts, strict=True):
            if self.budget is not None:
                self.budget.charge("component_logical_rectangle_visits")
            means = (
                self.origin[0] + Fraction(self.lower[0]) * Fraction(centre[0]),
                self.origin[1]
                + Fraction(self.lower[1]) * Fraction(centre[0])
                + Fraction(self.lower[2]) * Fraction(centre[1]),
            )
            standardized = []
            for axis, pair in enumerate(endpoints):
                scale = Fraction(self.lower[0 if axis == 0 else 2])
                standardized.append(
                    tuple(
                        None
                        if bound is None
                        else arithmetic.fraction_bounds(
                            (bound[0] - means[axis]) / scale,
                            (bound[1] - means[axis]) / scale,
                        )
                        for bound in pair
                    )
                )
            if self.kernel == "gaussian":
                probability = arithmetic.gaussian_rectangle(
                    standardized[0][0],
                    standardized[0][1],
                    standardized[1][0],
                    standardized[1][1],
                    slope,
                    tolerance,
                    workspace=gaussian_workspace,
                )
            else:
                probability = arithmetic.compact_rectangle(
                    standardized[0][0],
                    standardized[0][1],
                    standardized[1][0],
                    standardized[1][1],
                    slope,
                    tolerance,
                )
            total = arithmetic.sum_scaled(
                (
                    total,
                    arithmetic.combine_scaled(
                        [
                            mass,
                            arithmetic.normalize(probability, 0),
                        ]
                    ),
                )
            )
        return arithmetic.finish_scaled(*total)


def _parameter_tv(
    arithmetic, lower, bounds, centres, centre_bounds, mass_parts, kernel
):
    """Uniform probability error for source means/H versus the computed chart.

    Gaussian covariance uses Pinsker and an eigenvalue perturbation enclosure.
    Product-kernel affine change uses its integrated polynomial derivatives.
    These are derived bounds, not eps multipliers or validation sampling.
    """
    dimension = len(centres[0])
    a00 = arithmetic.rational_div(_fraction_box(bounds[0]), (Fraction(lower[0]),) * 2)
    deviations = [max(abs(value - 1) for value in a00)]
    infinity_norm = deviations[0]
    if dimension == 2:
        a10 = arithmetic.rational_div(
            arithmetic.rational_sub(
                _fraction_box(bounds[1]),
                arithmetic.rational_mul(
                    (Fraction(lower[1]) / Fraction(lower[0]),) * 2,
                    _fraction_box(bounds[0]),
                ),
            ),
            (Fraction(lower[2]),) * 2,
        )
        a11 = arithmetic.rational_div(
            _fraction_box(bounds[2]), (Fraction(lower[2]),) * 2
        )
        off = max(abs(value) for value in a10)
        diagonal = max(abs(value - 1) for value in a11)
        deviations.extend((off, diagonal))
        infinity_norm = max(infinity_norm, off + diagonal)
    if kernel == "gaussian":
        eta = arithmetic.sqrt_fraction(sum(value * value for value in deviations))[1]
        deviation = arithmetic.add(
            arithmetic.mul((2.0, 2.0), (eta, eta)),
            arithmetic.mul((eta, eta), (eta, eta)),
        )[1]
        covariance_tv = (
            1.0
            if deviation >= 1
            else arithmetic.mul(
                (deviation, deviation),
                arithmetic.sqrt_fraction(
                    Fraction(dimension, 8) / (Fraction(1) - Fraction(deviation))
                ),
            )[1]
        )
    else:
        covariance_tv = (
            1.0
            if infinity_norm >= 1
            else arithmetic.fraction(dimension * infinity_norm / (1 - infinity_norm))[1]
        )
    mixture = ((0.0, 0.0), 0)
    for centre, source, mass in zip(centres, centre_bounds, mass_parts, strict=True):
        deltas = [
            max(abs(Fraction(edge) - Fraction(mean)) for edge in bound)
            for mean, bound in zip(centre, source, strict=True)
        ]
        if kernel == "gaussian":
            squared = sum(value * value for value in deltas)
            mean_tv = 1.0 if squared >= 4 else arithmetic.sqrt_fraction(squared / 4)[1]
        else:
            length = sum(deltas)
            mean_tv = (
                1.0
                if length >= 3
                else arithmetic.mul(
                    arithmetic.fraction(length),
                    arithmetic.div(
                        (3.0, 3.0),
                        arithmetic.mul((4.0, 4.0), arithmetic.compact_radius),
                    ),
                )[1]
            )
        contribution = arithmetic.combine_scaled(
            [
                mass,
                arithmetic.normalize((0.0, min(1.0, mean_tv)), 0),
            ]
        )
        mixture = arithmetic.sum_scaled((mixture, contribution))
    return min(
        1.0,
        arithmetic.up(arithmetic.finish_scaled(*mixture)[1] + min(1.0, covariance_tv)),
    )


def fit_kernel(
    coordinates,
    masses,
    config,
    *,
    logarithmic=None,
    amplitude=Fraction(1),
    rows=(),
    arithmetic=None,
):
    """Canonical full-covariance fit shared by ALL explicit new KDE workflows.

    Physical Kish/covariance precede exact coincident-component aggregation.
    Raw source values are never binary64-normalized before moments or ties.
    """
    import sys

    from ._field_budget import owned_size

    dimensions = len(coordinates)
    if dimensions not in (1, 2):
        raise ValueError("named kernels require one or two logical coordinates")
    count = len(masses)
    if any(len(column) != count for column in coordinates):
        raise ValueError("kernel observations/masses must be paired")
    if any(type(value) is not int or value <= 0 for value in masses):
        raise ValueError("kernel physical masses must be positive canonical integers")
    if count < 2:
        return None
    logarithmic = (False,) * dimensions if logarithmic is None else tuple(logarithmic)
    if len(logarithmic) != dimensions:
        raise ValueError("kernel fit-scale choices must match logical coordinates")
    arithmetic = IntervalMath() if arithmetic is None else arithmetic
    budget = arithmetic.budget
    scratch = []
    model = None
    try:
        if budget is not None:
            coordinate_bits = max(
                max(
                    abs(Fraction(value).numerator).bit_length(),
                    Fraction(value).denominator.bit_length(),
                )
                for column in coordinates
                for value in column
            )
            mass_bits = max(value.bit_length() for value in masses)
            width = 2 * (coordinate_bits + mass_bits) + count.bit_length() + 8
            budget.charge(
                "integer_fit_canonicalization", 8 * dimensions * count, bits=width
            )
            scratch.append(budget.integer_lease(width, count=12 * dimensions * count))
            reference = sys.getsizeof((None,)) - sys.getsizeof(())
            protocol = (
                4 * sys.getsizeof(Fraction(0))
                + sys.getsizeof((None, None))
                + 4 * reference
            )
            scratch.append(
                budget.lease(
                    protocol * dimensions * count, pair_elements=7 * dimensions * count
                )
            )
            scratch.append(
                budget.hashmap_lease(
                    count,
                    key_bytes=sys.getsizeof((None,) * dimensions),
                    value_bytes=sys.getsizeof([None, None]),
                )
            )
        raw = [tuple(Fraction(value) for value in column) for column in coordinates]
        fitted = []
        source = []
        errors = []
        for column, logarithmic_axis in zip(raw, logarithmic, strict=True):
            transformed = [
                _fit_coordinate(value, logarithmic_axis, arithmetic) for value in column
            ]
            values = tuple(item[0] for item in transformed)
            bounds = tuple(item[1] for item in transformed)
            fitted.append(values)
            source.append(bounds)
            errors.append(
                max(
                    max(abs(edge - value) for edge in bound)
                    for value, bound in zip(values, bounds, strict=True)
                )
            )
        units = [canonical_units(column) for column in fitted]
        products = [
            tuple(mass * value for mass, value in zip(masses, column, strict=True))
            for _denominator, column in units
        ]
        total = sum(masses)
        squared_mass = sum(value * value for value in masses)
        correction = total * total - squared_mass
        if correction <= 0:
            return None
        origins = tuple(
            Fraction(sum(product), total * denominator)
            for product, (denominator, _column) in zip(products, units, strict=True)
        )
        dx, ux = units[0]
        first = covariance_units(
            ux, ux, masses, dx, dx, products_x=products[0], budget=budget
        )
        if first is None or first[0] <= 0:
            if len(set(raw[0])) > 1 and errors[0]:
                raise KernelPrecisionError("log-coordinate variation is unresolved")
            return None
        xx, effective_n = first
        exx = _source_covariance_error(
            ux,
            ux,
            dx,
            dx,
            masses,
            total,
            correction,
            origins[0],
            origins[0],
            errors[0],
            errors[0],
            arithmetic,
        )
        xy = yy = exy = eyy = Fraction(0)
        if dimensions == 2:
            dy, uy = units[1]
            cross = covariance_units(
                ux,
                uy,
                masses,
                dx,
                dy,
                products_x=products[0],
                products_y=products[1],
                budget=budget,
            )
            second = covariance_units(
                uy,
                uy,
                masses,
                dy,
                dy,
                products_x=products[1],
                budget=budget,
            )
            if cross is None or second is None:
                return None
            xy, yy = cross[0], second[0]
            if yy <= 0 or xx * yy - xy * xy <= 0:
                if any(errors) and len(set(zip(*raw, strict=True))) > 2:
                    raise KernelPrecisionError(
                        "log-coordinate covariance rank is unresolved"
                    )
                return None
            exy = _source_covariance_error(
                ux,
                uy,
                dx,
                dy,
                masses,
                total,
                correction,
                origins[0],
                origins[1],
                errors[0],
                errors[1],
                arithmetic,
            )
            eyy = _source_covariance_error(
                uy,
                uy,
                dy,
                dy,
                masses,
                total,
                correction,
                origins[1],
                origins[1],
                errors[1],
                errors[1],
                arithmetic,
            )
        factor = _bandwidth_factor(arithmetic, effective_n, dimensions, config)
        lower_bounds = _source_lower(
            arithmetic, (xx, xy, yy), (exx, exy, eyy), dimensions, factor
        )
        lower = tuple(arithmetic.midpoint(bound) for bound in lower_bounds)
        if lower[0] <= 0 or (dimensions == 2 and lower[2] <= 0):
            raise KernelPrecisionError(
                "positive kernel factors are not natively representable"
            )
        l00 = _fraction_box(lower_bounds[0])
        b00 = arithmetic.rational_div((Fraction(lower[0]),) * 2, l00)
        inverse = [arithmetic.fraction_bounds(*b00)]
        if dimensions == 2:
            l10, l11 = map(_fraction_box, lower_bounds[1:])
            b10 = arithmetic.rational_div(
                arithmetic.rational_sub(
                    (Fraction(lower[1]),) * 2,
                    arithmetic.rational_mul(l10, b00),
                ),
                l11,
            )
            b11 = arithmetic.rational_div((Fraction(lower[2]),) * 2, l11)
            inverse.extend(
                (arithmetic.fraction_bounds(*b10), arithmetic.fraction_bounds(*b11))
            )
        components = {}
        for index, key in enumerate(zip(*raw, strict=True)):
            if budget is not None:
                budget.charge(
                    "integer_coincident_component_mass", 1, bits=total.bit_length() + 1
                )
            if key in components:
                components[key][0] += masses[index]
            else:
                components[key] = [masses[index], index]
        centres, centre_bounds, offsets, component_masses = [], [], [], []
        component_source = []
        for mass, index in components.values():
            bounds = [column[index] for column in source]
            delta_x = tuple(value - origins[0] for value in bounds[0])
            qx = arithmetic.rational_div(delta_x, (Fraction(lower[0]),) * 2)
            bx = arithmetic.rational_div((-delta_x[1], -delta_x[0]), l00)
            chart = [arithmetic.fraction_bounds(*qx)]
            offset = [arithmetic.fraction_bounds(*bx)]
            if dimensions == 2:
                delta_y = tuple(value - origins[1] for value in bounds[1])
                qy = arithmetic.rational_div(
                    arithmetic.rational_sub(
                        delta_y,
                        arithmetic.rational_mul((Fraction(lower[1]),) * 2, qx),
                    ),
                    (Fraction(lower[2]),) * 2,
                )
                by = arithmetic.rational_div(
                    arithmetic.rational_sub(
                        (-delta_y[1], -delta_y[0]),
                        arithmetic.rational_mul(l10, bx),
                    ),
                    l11,
                )
                chart.append(arithmetic.fraction_bounds(*qy))
                offset.append(arithmetic.fraction_bounds(*by))
            centres.append(tuple(arithmetic.midpoint(bound) for bound in chart))
            centre_bounds.append(tuple(chart))
            offsets.append(tuple(offset))
            component_masses.append(mass)
            component_source.append(bounds)
        mass_parts = tuple(
            arithmetic.scaled_ratio(mass, total) for mass in component_masses
        )
        determinant = [
            arithmetic.reciprocal_scaled(arithmetic.normalize(lower_bounds[0], 0))
        ]
        if dimensions == 2:
            determinant.append(
                arithmetic.reciprocal_scaled(arithmetic.normalize(lower_bounds[2], 0))
            )
        kernel = config.kernel or "gaussian"
        shift, raw_parts = (), mass_parts
        if kernel == "gaussian" and any(logarithmic):
            shift0 = (0.0, 0.0)
            if logarithmic[0]:
                shift0 = arithmetic.mul(arithmetic.ln10, lower_bounds[0])
            if dimensions == 2 and logarithmic[1]:
                shift0 = arithmetic.add(
                    shift0, arithmetic.mul(arithmetic.ln10, lower_bounds[1])
                )
            shift = (shift0,)
            if dimensions == 2:
                shift += (
                    arithmetic.mul(arithmetic.ln10, lower_bounds[2])
                    if logarithmic[1]
                    else (0.0, 0.0),
                )
            squared = (0.0, 0.0)
            for value in shift:
                squared = arithmetic.add(
                    squared, arithmetic.nonnegative(arithmetic.mul(value, value))
                )
            half = arithmetic.div(squared, (2.0, 2.0))
            inv_ln10 = arithmetic.reciprocal_scaled(
                arithmetic.normalize(arithmetic.ln10, 0)
            )
            constants = [
                inv_ln10 for logarithmic_axis in logarithmic if logarithmic_axis
            ]
            raw_parts = []
            for mass_part, source_point in zip(
                mass_parts, component_source, strict=True
            ):
                dot = (Fraction(0), Fraction(0))
                for bound, logarithmic_axis in zip(
                    source_point, logarithmic, strict=True
                ):
                    if logarithmic_axis:
                        dot = arithmetic.rational_add(dot, bound)
                exponent = arithmetic.sub(
                    half,
                    arithmetic.mul(arithmetic.fraction_bounds(*dot), arithmetic.ln10),
                )
                raw_parts.append(
                    arithmetic.combine_scaled(
                        [mass_part, *constants, arithmetic.exp_signed_scaled(exponent)]
                    )
                )
            raw_parts = tuple(raw_parts)
        source_tv = _parameter_tv(
            arithmetic,
            lower,
            lower_bounds,
            centres,
            centre_bounds,
            mass_parts,
            kernel,
        )
        amplitude = Fraction(amplitude)
        model = KernelModel(
            dimensions=dimensions,
            kernel=kernel,
            origin=origins,
            fit_bounds=tuple(
                (min(bound[0] for bound in column), max(bound[1] for bound in column))
                for column in source
            ),
            lower=lower,
            lower_bounds=lower_bounds,
            centres=tuple(centres),
            centre_bounds=tuple(centre_bounds),
            inverse=tuple(inverse),
            offsets=tuple(offsets),
            masses=tuple(component_masses),
            total=total,
            mass_parts=mass_parts,
            determinant_inverse=arithmetic.combine_scaled(determinant),
            amplitude_part=arithmetic.scaled_ratio(
                amplitude.numerator, amplitude.denominator
            ),
            log_shift=shift,
            raw_parts=raw_parts,
            amplitude=amplitude,
            log_axes=logarithmic,
            source_tv=source_tv,
            arithmetic=arithmetic,
            budget=budget,
            source_rows=tuple(rows),
        )
        if budget is not None:
            model.leases.append(
                budget.lease(
                    owned_size(model),
                    pair_elements=(5 * dimensions + 7) * len(centres) + 16,
                )
            )
        return model
    except Exception:
        if model is not None:
            model.close()
        raise
    finally:
        for lease in reversed(scratch):
            lease.close()


@dataclass(slots=True)
class KernelProfile:
    index: int
    hue: object
    roles: dict
    rows: tuple[int, ...]
    model: KernelModel | None
    singular: bool


@dataclass(slots=True)
class KernelPlan:
    profiles: list[KernelProfile]
    pooled: KernelModel | None
    cohort: FieldInput
    config: KDESpec | KDE2DSpec
    owns_input: bool

    def close(self):
        for profile in self.profiles:
            if profile.model is not None:
                profile.model.close()
        if self.pooled is not None:
            self.pooled.close()
        if self.owns_input:
            self.cohort.close()


def prepare_kernel_profiles(
    columns,
    layer,
    panel,
    config: KDESpec | KDE2DSpec,
    *,
    input_plan=None,
    arithmetic=None,
):
    """Fit each raw tuple ONCE; normalization references are effective-hue/global."""
    from ._density import observation_axes
    from ._density_input import prepare_input

    cohort = (
        prepare_input(
            columns, layer, panel, None if arithmetic is None else arithmetic.budget
        )
        if input_plan is None
        else input_plan
    )
    arithmetic = IntervalMath(cohort.budget) if arithmetic is None else arithmetic
    if isinstance(config, KDESpec):
        dimensions = 1
        scales = (layer.stat_scale,)
    else:
        dimensions = 2
        scales = ("data", "data") if config.fit_scales is None else config.fit_scales
    axes = observation_axes(layer, panel)[:dimensions]
    logarithmic = tuple(
        choice == "axis" and axis is not None and axis.scale == "log"
        for choice, axis in zip(scales, axes, strict=True)
    )
    names = (layer.x,) if dimensions == 1 else (layer.x, layer.y)
    plan = KernelPlan([], None, cohort, config, input_plan is None)
    try:
        for group in cohort.groups:
            rows = tuple(group["rows"])
            model = None
            if rows:
                normalizer = (
                    cohort.total
                    if config.common_norm
                    else cohort.pool_totals[group["pool"]]
                )
                # Singular tuples remain in this precomputed comparison mass;
                # neither skipping a fit nor a viewport rebases its neighbours.
                amplitude = Fraction(cohort.group_totals[group["index"]], normalizer)
                model = fit_kernel(
                    [[columns[name][row] for row in rows] for name in names],
                    tuple(cohort.mass_by_row[row] for row in rows),
                    config,
                    logarithmic=logarithmic,
                    amplitude=amplitude,
                    rows=rows,
                    arithmetic=arithmetic,
                )
            plan.profiles.append(
                KernelProfile(
                    group["index"],
                    group["hue"],
                    group["roles"],
                    rows,
                    model,
                    bool(rows) and model is None,
                )
            )
        if config.common_grid and any(item.model is not None for item in plan.profiles):
            plan.pooled = fit_kernel(
                [[columns[name][row] for row in cohort.rows] for name in names],
                cohort.masses,
                config,
                logarithmic=logarithmic,
                rows=cohort.rows,
                arithmetic=arithmetic,
            )
            if plan.pooled is None:
                raise KernelPrecisionError("pooled shared-grid fit is unresolved")
        return plan
    except Exception:
        plan.close()
        raise


def kernel_query_grid(model, config):
    """Canonical fit-spaced queries, evaluated at their ACTUAL native positions."""
    grid = []
    for axis, (low, high) in enumerate(model.evaluation_bounds(config)):
        raw_low = model.native_coordinate(low, axis)[0]
        raw_high = model.native_coordinate(high, axis)[0]
        clip = config.clip
        bound = None if clip is None else clip if model.dimensions == 1 else clip[axis]
        if bound is not None:
            if bound[0] is not None:
                raw_low = max(raw_low, float(bound[0]))
            if bound[1] is not None:
                raw_high = min(raw_high, float(bound[1]))
        if not raw_low < raw_high:
            raise KernelPrecisionError("KDE native query range collapses")
        start = _fit_coordinate(raw_low, model.log_axes[axis], model.arithmetic)[0]
        stop = _fit_coordinate(raw_high, model.log_axes[axis], model.arithmetic)[0]
        points = [raw_low]
        for index in range(1, config.gridsize - 1):
            if model.budget is not None:
                model.budget.charge("query_grid_nodes")
            point = start + (stop - start) * Fraction(index, config.gridsize - 1)
            points.append(model.native_coordinate(point, axis)[0])
        points.append(raw_high)
        if any(a >= b for a, b in pairwise(points)):
            raise KernelPrecisionError(
                "requested KDE query nodes collapse at native coordinate precision"
            )
        grid.append(tuple(points))
    return tuple(grid)


@dataclass(slots=True)
class UnivariateKernelValues:
    profiles: list[KernelProfile]
    grids: tuple
    lower: object
    upper: object
    interval_widths: tuple[float, ...]
    leases: list = field(default_factory=list, repr=False)

    def close(self):
        self.grids = ()
        self.lower = self.upper = None
        for lease in reversed(self.leases):
            lease.close()
        self.leases.clear()


def evaluate_univariate(plan):
    """One point-major scaled computation; stack/fill never interpolate grids."""
    import numpy as np

    from ._density import density_space, multiple

    profiles = [item for item in plan.profiles if item.model is not None]
    config = plan.config
    if not isinstance(config, KDESpec):
        raise ValueError("univariate kernel evaluation requires KDESpec")
    mode = multiple(config)
    budget = plan.cohort.budget
    leases = []
    result = UnivariateKernelValues(profiles, (), None, None, (), leases)
    if not profiles:
        return result
    arithmetic = profiles[0].model.arithmetic
    if mode != "layer" and not config.common_grid:
        raise ValueError("KDE stack/fill requires stored common_grid=True")
    try:
        if budget is not None:
            leases.append(
                budget.array_lease((len(profiles), config.gridsize), copies=3)
            )
        if config.common_grid:
            shared = kernel_query_grid(plan.pooled, config)[0]
            grids = tuple(shared for _item in profiles)
        else:
            grids = tuple(kernel_query_grid(item.model, config)[0] for item in profiles)
        result.grids = grids
        lower = np.zeros((len(profiles), config.gridsize), dtype=float)
        upper = np.empty_like(lower)
        result.lower, result.upper = lower, upper
        maximum_width = [0.0] * len(profiles)
        previous_cdf = [0.0] * len(profiles)
        # Ratio representative Fraction vectors and interval endpoints are live
        # only for ONE query, never an all-profile/all-component broadcast.
        point_workspace = None
        if budget is not None:
            point_workspace = budget.integer_lease(1088, count=12 * len(profiles))
        try:
            for point in range(config.gridsize):
                parts = []
                for index, item in enumerate(profiles):
                    model = item.model
                    raw = grids[index][point]
                    if budget is not None:
                        budget.charge("curve_queries")
                    parts.append(
                        model.cdf1d_scaled(raw)
                        if config.cumulative
                        else model.pdf_scaled(
                            (raw,), density_space=density_space(config)
                        )
                    )
                if mode == "fill":
                    values = arithmetic.composition_values(parts)
                    if values is None:
                        lower[:, point] = upper[:, point] = np.nan
                        continue
                    cumulative = Fraction(0)
                    for index, value in enumerate(values):
                        if budget is not None:
                            budget.charge(
                                "integer_composition_prefix",
                                1,
                                bits=cumulative.denominator.bit_length() + 1,
                            )
                        lower[index, point] = float(cumulative)
                        cumulative += value
                        upper[index, point] = float(cumulative)
                    continue
                prefix = ((0.0, 0.0), 0)
                baseline = 0.0
                for index, part in enumerate(parts):
                    active = part
                    if mode == "stack":
                        prefix = arithmetic.sum_scaled((prefix, part))
                        active = prefix
                    bounds = arithmetic.finish_scaled(*active)
                    maximum_width[index] = max(
                        maximum_width[index], bounds[1] - bounds[0]
                    )
                    value = (
                        max(previous_cdf[index], bounds[0])
                        if config.cumulative
                        else arithmetic.midpoint(bounds)
                    )
                    if mode == "stack":
                        value = max(baseline, value)
                        lower[index, point] = baseline
                    if not bounds[0] <= value <= bounds[1]:
                        raise KernelPrecisionError(
                            "positive/monotone curve selection violates its enclosure"
                        )
                    upper[index, point] = value
                    previous_cdf[index] = value
                    baseline = value
            result.interval_widths = tuple(maximum_width)
            return result
        finally:
            if point_workspace is not None:
                point_workspace.close()
    except Exception:
        result.close()
        raise
