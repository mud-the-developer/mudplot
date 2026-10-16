"""Scaled numeric regression effects; optional models import only on demand."""

from __future__ import annotations

import warnings

import numpy as np


def _optional_fit(model, x, y, at, config):
    try:
        if model == "lowess":
            from statsmodels.nonparametric.smoothers_lowess import lowess

            return lowess(
                y,
                x,
                frac=config.frac,
                it=config.iterations,
                xvals=at,
                is_sorted=False,
                missing="none",  # finite values checked before optional effects
                return_sorted=False,
            )
        design = np.column_stack((np.ones(len(x)), x))
        prediction = np.column_stack((np.ones(len(at)), at))
        if model == "robust":
            from statsmodels.robust.norms import HuberT
            from statsmodels.robust.robust_linear_model import RLM

            # An exact line already minimizes every Huber loss; avoid a zero MAD fit.
            coefficients = np.linalg.lstsq(design, y, rcond=None)[0]
            if np.max(np.abs(y - design @ coefficients)) <= 32 * np.finfo(float).eps:
                return prediction @ coefficients
            result = RLM(y, design, M=HuberT()).fit(maxiter=50, tol=1e-8)
            if result.fit_history.get("iteration", 0) >= 50:
                raise ValueError(
                    "robust regression did not converge within 50 iterations"
                )
            return result.predict(prediction)
        from statsmodels.genmod.families import Binomial
        from statsmodels.genmod.generalized_linear_model import GLM

        result = GLM(y, design, family=Binomial()).fit(maxiter=100, tol=1e-8)
        if not result.converged:
            raise ValueError(
                "logistic regression did not converge within 100 iterations"
            )
        return result.predict(prediction)
    except ImportError as error:
        raise ImportError(
            "robust/logistic/LOWESS effects require optional mudplot[regression]"
        ) from error


def fit_regression(x, y, layer, polynomial_fit, *, at=None):
    """Return original-coordinate grid/response/CI; no mutation or global RNG."""
    config = layer.regression
    assert config is not None
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    model = config.model
    with (
        warnings.catch_warnings(),
        np.errstate(over="raise", invalid="raise", divide="raise"),
    ):
        warnings.simplefilter("error", RuntimeWarning)
        warnings.simplefilter("error", UserWarning)
        try:
            transformed = np.log(x) if model == "logx" else x
            magnitude = float(np.max(np.abs(transformed))) or 1.0
            unit = transformed / magnitude
            center = float(unit.min()) / 2 + float(unit.max()) / 2
            scale = (float(unit.max()) - float(unit.min())) / 2
            if not np.isfinite(scale) or scale <= 0:
                raise ValueError("regression x range is numerically singular")
            scaled = (unit - center) / scale
            points = None
            if at is not None:
                original_at = np.asarray(at, dtype=float)
                transformed_at = np.log(original_at) if model == "logx" else original_at
                points = (transformed_at / magnitude - center) / scale
            response_scale = float(np.max(np.abs(y))) or 1.0
            response = y / response_scale
            if model in ("poly", "logx"):
                grid, fitted, interval = polynomial_fit(
                    scaled,
                    response,
                    layer.degree,
                    layer.confidence,
                    at=points,
                )
            else:
                grid = (
                    np.linspace(float(scaled.min()), float(scaled.max()), 200)
                    if points is None
                    else points
                )
                if any(
                    not np.isfinite(values).all() for values in (scaled, response, grid)
                ):
                    raise ValueError("optional regression inputs must be finite")
                fitted = _optional_fit(model, scaled, response, grid, config)
                interval = None
            raw_grid = (grid * scale + center) * magnitude
            if model == "logx":
                raw_grid = np.exp(raw_grid)
            fitted = np.asarray(fitted, dtype=float) * response_scale
            if interval is not None:
                interval = tuple(
                    np.asarray(bound) * response_scale for bound in interval
                )
            arrays = [raw_grid, fitted, *(interval or ())]
            if any(not np.isfinite(array).all() for array in arrays):
                raise ValueError("regression produced nonfinite predictions")
            return raw_grid, fitted, interval
        except (
            ValueError,
            FloatingPointError,
            np.linalg.LinAlgError,
            Warning,
        ) as error:
            raise ValueError(f"{model} regression fit failed: {error}") from error
