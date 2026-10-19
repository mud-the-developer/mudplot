"""Dependency-free configuration and selected-row contracts for regression."""

from __future__ import annotations

from ._ecdf import finite_number
from .spec import RegressionSpec

REGRESSION_MODELS = ("poly", "logx", "robust", "logistic", "lowess")
OPTIONAL_REGRESSION_MODELS = ("robust", "logistic", "lowess")
MAX_REGRESSION_ROWS = 10000
MAX_LOWESS_ROWS = 5000


def prepare_regression(config, *, residual=False) -> RegressionSpec | None:
    if config is None:
        return RegressionSpec(residual=True) if residual else None
    result = RegressionSpec.from_dict(
        config.to_dict() if isinstance(config, RegressionSpec) else config
    )
    if not isinstance(result, RegressionSpec):
        raise TypeError("regression must decode to RegressionSpec")
    if residual:
        result.residual = True
    return result


def option_issues(config, degree, confidence):
    if config is None:
        return []
    if not isinstance(config, RegressionSpec):
        return ["regression must be RegressionSpec or None"]
    issues = []
    if config.model not in REGRESSION_MODELS:
        issues.append("regression model must be poly/logx/robust/logistic/lowess")
    if type(config.residual) is not bool:
        issues.append("regression residual must be boolean")
    if config.model != "poly" and degree != 1:
        issues.append("non-polynomial regression requires degree=1")
    if confidence is not None and (
        config.residual or config.model in OPTIONAL_REGRESSION_MODELS
    ):
        issues.append(
            "residual/robust/logistic/LOWESS confidence bands are not supported"
        )
    if not finite_number(config.frac) or not 0 < config.frac <= 1:
        issues.append("LOWESS frac must be finite in (0,1]")
    if type(config.iterations) is not int or not 0 <= config.iterations <= 20:
        issues.append("LOWESS iterations must be an integer in [0,20]")
    if config.model != "lowess" and (config.frac != 2 / 3 or config.iterations != 3):
        issues.append("frac/iterations options require the LOWESS model")
    return issues


def weighted_option_issues(config, confidence, weights):
    if weights is None:
        return []
    issues = []
    if not isinstance(weights, str) or not weights:
        issues.append("regression weights must be a nonempty column name")
    if not isinstance(config, RegressionSpec) or config.model not in ("poly", "logx"):
        issues.append("weighted regression requires poly/logx RegressionSpec")
    if confidence is not None:
        issues.append("weighted regression confidence bands are not supported")
    return issues


def group_issues(config: RegressionSpec, pairs, distinct_x):
    issues = []
    if config.model == "logx" and any(x <= 0 for x, _y in pairs):
        issues.append("logx regression requires positive x values")
    if config.model == "logistic":
        values = {y for _x, y in pairs}
        if values != {0, 1}:
            issues.append(
                "logistic regression requires both numeric response classes 0/1"
            )
        if len(pairs) < 3:
            issues.append("logistic regression requires at least three observations")
    if config.model == "lowess":
        if distinct_x < 3:
            issues.append("LOWESS requires at least three distinct x values")
        if len(pairs) > MAX_LOWESS_ROWS:
            issues.append(
                f"LOWESS supports at most {MAX_LOWESS_ROWS} observations per group"
            )
        if finite_number(config.frac) and int(config.frac * len(pairs)) < 2:
            issues.append(
                "LOWESS frac selects fewer than two neighbouring observations"
            )
    return issues
