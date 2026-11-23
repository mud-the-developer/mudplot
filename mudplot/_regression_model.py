"""Regression numerical point factories; inference never selects the estimator.

Original masses enter canonical medians; already-float64 derived local masses
use the same SVD/relative-normalization boundary without scalar reconversion.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import replace
from fractions import Fraction
from statistics import NormalDist

import numpy as np

from ._ecdf import canonical_cdf
from ._regression import OPTIONAL_REGRESSION_MODELS


def relative_masses(values):
    masses = np.asarray(values, dtype=float)
    if (
        masses.ndim != 1
        or not len(masses)
        or not np.isfinite(masses).all()
        or np.any(masses <= 0)
    ):
        raise ValueError("regression numerical masses must be finite and positive")
    with np.errstate(under="ignore"):
        relative = masses / float(masses.max())
    if np.any(relative <= 0):
        raise ValueError("positive regression criterion mass erased by normalization")
    return relative


def weighted_solve(design, response, masses):
    """One normalized SVD solve, never normal equations or a rank fallback."""
    relative = relative_masses(masses)
    root = np.sqrt(relative)
    matrix = design * root[:, None]
    values = response * root
    beta, _residual, rank, _singular = np.linalg.lstsq(matrix, values, rcond=None)
    if rank != design.shape[1] or not np.isfinite(beta).all():
        raise ValueError(
            "rank-deficient or nonfinite complete weighted regression design"
        )
    return beta


def _normalized(training, requested):
    magnitude = float(np.max(np.abs(training))) or 1.0
    unit = training / magnitude
    center = float(unit.min()) / 2 + float(unit.max()) / 2
    scale = (float(unit.max()) - float(unit.min())) / 2
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("regression design column is numerically singular")
    return (unit - center) / scale, (requested / magnitude - center) / scale


def _median_absolute(residual, original_masses):
    return float(
        canonical_cdf(np.abs(residual).tolist(), original_masses).left(Fraction(1, 2))
    )


def _huber(design, response, original_masses, at):
    relative = relative_masses(original_masses)
    beta = weighted_solve(design, response, relative)
    fitted = design @ beta
    factor = NormalDist().inv_cdf(0.75)
    scale = _median_absolute(response - fitted, original_masses) / factor
    for iteration in range(51):
        if scale == 0:
            if np.all(response == fitted):
                return at @ beta
            raise ValueError("zero canonical weighted MAD with nonzero residuals")
        if not math.isfinite(scale) or scale < 0:
            raise ValueError("Huber residual scale is not finite positive")
        if iteration == 50:
            break
        standardized = np.abs((response - fitted) / scale)
        robust = np.ones(len(response))
        outside = standardized > 1.345
        robust[outside] = 1.345 / standardized[outside]
        combined = relative * robust
        if np.any(combined <= 0):
            raise ValueError("positive Huber criterion mass erased numerically")
        next_beta = weighted_solve(design, response, combined)
        next_fitted = design @ next_beta
        next_scale = _median_absolute(response - next_fitted, original_masses) / factor
        stable_beta = np.max(np.abs(next_beta - beta)) <= 1e-8 * (
            1 + np.max(np.abs(beta))
        )
        stable_scale = abs(next_scale - scale) <= 1e-8 * max(next_scale, scale)
        beta, fitted, scale = next_beta, next_fitted, next_scale
        if stable_beta and stable_scale:
            if scale == 0 and not np.all(response == fitted):
                raise ValueError("zero canonical weighted MAD with nonzero residuals")
            return at @ beta
    raise ValueError("case-mass Huber did not converge within50 iterations")


def _lowess(x, response, original_masses, at, config):
    n = len(x)
    if n < 3 or len(np.unique(x)) < 3 or config.frac * n < 2:
        raise ValueError("insufficient physical LOWESS support")
    k = min(n, max(2, int(config.frac * n + 1e-10)))
    relative = relative_masses(original_masses)
    robust = np.ones(n)

    def evaluate(points):
        out = np.empty(len(points))
        for index, point in enumerate(points):
            distance = np.abs(x - point)
            radius = float(np.partition(distance, k - 1)[k - 1])
            if not math.isfinite(radius) or radius <= 0:
                raise ValueError("zero or nonfinite physical LOWESS neighbor radius")
            selected = distance < radius
            coordinate = (x[selected] - point) / radius
            kernel = (1 - np.abs(coordinate) ** 3) ** 3
            base = relative[selected] * robust[selected]
            if np.any((robust[selected] > 0) & (base == 0)):
                raise ValueError(
                    "positive LOWESS robust criterion mass erased numerically"
                )
            masses = base * kernel
            if np.any((base > 0) & (kernel > 0) & (masses == 0)):
                raise ValueError(
                    "positive LOWESS kernel criterion mass erased numerically"
                )
            positive = masses > 0
            if np.count_nonzero(positive) < 2:
                raise ValueError("fewer than two positive local LOWESS cases")
            design = np.column_stack(
                (np.ones(np.count_nonzero(positive)), coordinate[positive])
            )
            beta = weighted_solve(
                design, response[selected][positive], masses[positive]
            )
            out[index] = beta[0]
        return out

    for _ in range(config.iterations):
        residual = np.abs(response - evaluate(x))
        median = _median_absolute(residual, original_masses)
        if median == 0:
            robust = (residual == 0).astype(float)
        else:
            scaled = residual / median / 6
            robust = np.where(scaled < 1, (1 - np.minimum(scaled, 1) ** 2) ** 2, 0)
    return evaluate(at)


def predict(
    x,
    y,
    original_masses,
    at,
    layer,
    polynomial_fit,
    *,
    nuisance=None,
    nuisance_at=None,
    normal=False,
    normal_count=None,
):
    """Fit once, evaluate all consumed targets; no RNG, provider cache or mutation."""
    from ._regression_render import fit_regression

    config = layer.regression
    x, y, at = (np.asarray(values, dtype=float) for values in (x, y, at))
    if any(not np.isfinite(values).all() for values in (x, y, at)):
        raise ValueError("regression point inputs must be finite")
    if config.model == "logx" and (np.any(x <= 0) or np.any(at <= 0)):
        raise ValueError(
            "natural-log regression requires positive predictor coordinates"
        )
    if config.model in OPTIONAL_REGRESSION_MODELS:
        try:
            import statsmodels.api as sm
        except ImportError as error:
            raise ImportError(
                "advanced regression effects require optional mudplot[regression]"
            ) from error
    if nuisance is None and (
        original_masses is None or config.model in ("poly", "logx")
    ):
        plain = replace(layer, confidence=layer.confidence if normal else None)
        _grid, values, interval = fit_regression(
            x, y, plain, polynomial_fit, at=at, weights=original_masses
        )
        return values, interval
    masses = np.ones(len(x)) if original_masses is None else original_masses
    relative = relative_masses(masses)
    raw = np.log(x) if config.model == "logx" else x
    requested = np.log(at) if config.model == "logx" else at
    main, main_at = _normalized(raw, requested)
    response_scale = float(np.max(np.abs(y))) or 1.0
    response = y / response_scale
    base, base_at = [np.ones(len(x))], [np.ones(len(at))]
    if nuisance is not None:
        nuisance, nuisance_at = (
            np.asarray(nuisance, dtype=float),
            np.asarray(nuisance_at, dtype=float),
        )
        if nuisance.ndim != 2 or nuisance_at.shape != (len(at), nuisance.shape[1]):
            raise ValueError("actual nuisance evaluation shape mismatch")
        for column in range(nuisance.shape[1]):
            normalized, evaluated = _normalized(
                nuisance[:, column], nuisance_at[:, column]
            )
            base.append(normalized)
            base_at.append(evaluated)
    Z, Zat = np.column_stack(base), np.column_stack(base_at)
    if config.model == "lowess":
        if nuisance is not None:
            gx = weighted_solve(Z, main, relative)
            gy = weighted_solve(Z, response, relative)
            rx, ry, rat = main - Z @ gx, response - Z @ gy, main_at - Zat @ gx
            if original_masses is None:
                adjusted = replace(layer, regression=replace(config, partial=None))
                _grid, values, _bounds = fit_regression(
                    rx, ry, adjusted, polynomial_fit, at=rat
                )
            else:
                values = _lowess(rx, ry, masses, rat, config)
            values = (values + Zat @ gy) * response_scale
        else:
            values = _lowess(main, response, masses, main_at, config) * response_scale
        interval = None
    else:
        powers = layer.degree if config.model == "poly" else 1
        D = np.column_stack((Z, *[main**power for power in range(1, powers + 1)]))
        Dat = np.column_stack(
            (Zat, *[main_at**power for power in range(1, powers + 1)])
        )
        if np.linalg.matrix_rank(D) != D.shape[1]:
            raise ValueError("rank-deficient complete regression design")
        if config.model in ("poly", "logx"):
            beta = weighted_solve(D, response, relative)
            values = Dat @ beta * response_scale
            interval = None
            if normal:
                df = len(x) - D.shape[1]
                if original_masses is not None or df <= 0:
                    raise ValueError(
                        "unweighted full-design normal band "
                        "requires positive residual DF"
                    )
                _u, singular, vh = np.linalg.svd(D, full_matrices=False)
                residual = response - D @ beta
                sigma2 = float(residual @ residual) / df
                count = len(at) if normal_count is None else normal_count
                leverage = np.sum((Dat[:count] @ vh.T / singular) ** 2, axis=1)
                working_spread = (
                    NormalDist().inv_cdf(0.5 + layer.confidence / 200)
                    * math.sqrt(sigma2)
                    * np.sqrt(leverage)
                )
                spread = working_spread * response_scale
                interval = values[:count] - spread, values[:count] + spread
                if np.any((working_spread > 0) & (interval[0] >= interval[1])):
                    raise ValueError(
                        "positive full-design normal interval collapses natively"
                    )
        elif config.model == "robust" and original_masses is not None:
            values = _huber(D, response, masses, Dat) * response_scale
            interval = None
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("error", RuntimeWarning)
                warnings.simplefilter("error", UserWarning)
                if config.model == "robust":
                    fitted = sm.RLM(response, D, M=sm.robust.norms.HuberT()).fit(
                        maxiter=50, tol=1e-8
                    )
                    if fitted.fit_history.get("iteration", 0) >= 50:
                        raise ValueError(
                            "joint Huber did not converge within50 iterations"
                        )
                    values = fitted.predict(Dat) * response_scale
                else:
                    if set(y.tolist()) != {0.0, 1.0}:
                        raise ValueError(
                            "logit training requires both numeric response classes0/1"
                        )
                    fitted = sm.GLM(
                        y, D, family=sm.families.Binomial(), freq_weights=relative
                    ).fit(maxiter=100, tol=1e-8)
                    if not fitted.converged:
                        raise ValueError(
                            "binomial-logit did not converge within100 iterations"
                        )
                    values = fitted.predict(Dat)
                interval = None
    values = np.asarray(values, dtype=float)
    if not np.isfinite(values).all() or (
        interval is not None and any(not np.isfinite(bound).all() for bound in interval)
    ):
        raise ValueError("regression produced nonfinite native mean predictions")
    return values, interval


def affine_response(observed, mean, rows, *, reference=None):
    """One native rounding of actual y-minus-mean, optionally plus reference."""
    if reference is None and all(
        isinstance(value, (float, np.floating))
        or (isinstance(value, (int, np.integer)) and abs(value) <= 2**53)
        for value in observed
    ):
        return np.asarray(observed, dtype=float) - mean
    additions = (0.0 for _ in range(len(mean))) if reference is None else reference
    values = []
    for row, value, fitted, addback in zip(
        rows, observed, mean, additions, strict=True
    ):
        exact = Fraction(value) - Fraction(float(fitted)) + Fraction(float(addback))
        try:
            native = float(exact)
        except OverflowError as error:
            raise ValueError(
                f"nonfinite affine diagnostic at source row{row}"
            ) from error
        if not math.isfinite(native):
            raise ValueError(f"nonfinite affine diagnostic at source row{row}")
        values.append(native)
    return np.asarray(values, dtype=float)


def diagnostic(y, mean, kind, source_rows):
    """Mathematical diagnostic at fixed actual rows; never probability clipping."""
    mean = np.asarray(mean, dtype=float)
    if kind == "raw":
        values = affine_response(y, mean, source_rows)
    else:
        y = np.asarray(y, dtype=float)
        if not np.all((y == 0) | (y == 1)) or np.any((mean < 0) | (mean > 1)):
            raise ValueError(
                "binomial deviance requires binary observations and probabilities"
            )
        with np.errstate(divide="ignore", invalid="raise"):
            values = np.where(
                y == 1, np.sqrt(-2 * np.log(mean)), -np.sqrt(-2 * np.log1p(-mean))
            )
    invalid = np.flatnonzero(~np.isfinite(values))
    if len(invalid):
        raise ValueError(
            f"nonfinite {kind} diagnostic at original source "
            f"row{source_rows[int(invalid[0])]}"
        )
    return values
