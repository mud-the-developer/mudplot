"""Dependency-free configuration and selected-row contracts for regression."""

from __future__ import annotations

from dataclasses import dataclass

from ._ecdf import finite_number, source_rows
from .spec import (
    ComponentStyleSpec,
    PanelSpec,
    RegressionBootstrapSpec,
    RegressionComponentsSpec,
    RegressionDiagnosticsSpec,
    RegressionPartialSpec,
    RegressionSamplingSpec,
    RegressionSpec,
    RegressionTrendSpec,
    SemanticSpec,
)

REGRESSION_MODELS = ("poly", "logx", "robust", "logistic", "lowess")
OPTIONAL_REGRESSION_MODELS = ("robust", "logistic", "lowess")
MAX_REGRESSION_ROWS = 10000
MAX_LOWESS_ROWS = 5000
MAX_REGRESSION_DESIGN = 19
MAX_REGRESSION_WORK = 6_000_000_000
MAX_REGRESSION_STATE = 268_435_456


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
    if type(degree) is not int or not 1 <= degree <= 10:
        return [*issues, "degree must be an integer from1 to10"]
    if config.model != "poly" and degree != 1:
        issues.append("non-polynomial regression requires degree=1")
    if (
        confidence is not None
        and (config.residual or config.model in OPTIONAL_REGRESSION_MODELS)
        and config.bootstrap is None
    ):
        issues.append(
            "residual/advanced confidence requires explicit regression.bootstrap"
        )
    if not finite_number(config.frac) or not 0 < config.frac <= 1:
        issues.append("LOWESS frac must be finite in (0,1]")
    if type(config.iterations) is not int or not 0 <= config.iterations <= 20:
        issues.append("LOWESS iterations must be an integer in [0,20]")
    if config.model != "lowess" and (config.frac != 2 / 3 or config.iterations != 3):
        issues.append("frac/iterations options require the LOWESS model")
    issues.extend(_declaration_issues(config, degree, confidence))
    return issues


def weighted_option_issues(config, confidence, weights):
    if weights is None:
        return []
    issues = []
    if not isinstance(weights, str) or not weights:
        issues.append("regression weights must be a nonempty column name")
    if not isinstance(config, RegressionSpec):
        issues.append("weighted regression requires RegressionSpec")
    if confidence is not None and (
        not isinstance(config, RegressionSpec) or config.bootstrap is None
    ):
        issues.append("weighted confidence requires explicit regression.bootstrap")
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


def new_regression(layer):
    """Only genuinely new numerical work acquires the R01/R02 ledger."""
    config = layer.regression
    return isinstance(config, RegressionSpec) and (
        any(
            getattr(config, name) is not None
            for name in ("bootstrap", "partial", "sampling", "diagnostics")
        )
        or (layer.weights is not None and config.model in OPTIONAL_REGRESSION_MODELS)
    )


def configured_regression(layer):
    """Pure selection of the actual typed target route, not a visibility flag."""
    config = layer.regression
    return isinstance(config, RegressionSpec) and (
        new_regression(layer)
        or config.components is not None
        or layer.orient == "h"
        or layer.semantics is not None
    )


def _declaration_issues(config, degree, confidence):
    from ._components import MARK_FIELDS, style_issues

    issues = []
    for name, kind in (
        ("bootstrap", RegressionBootstrapSpec),
        ("partial", RegressionPartialSpec),
        ("sampling", RegressionSamplingSpec),
        ("diagnostics", RegressionDiagnosticsSpec),
        ("components", RegressionComponentsSpec),
    ):
        value = getattr(config, name)
        if value is not None and not isinstance(value, kind):
            issues.append(f"regression.{name} must be {kind.__name__}")
    if issues:
        return issues
    bootstrap = config.bootstrap
    if bootstrap is not None:
        if confidence is None:
            issues.append("regression.bootstrap requires Layer.confidence")
        if type(bootstrap.n_boot) is not int or not 1 <= bootstrap.n_boot <= 100000:
            issues.append("regression.bootstrap.n_boot must be integer1..100000")
        if type(bootstrap.seed) is not int or bootstrap.seed < 0:
            issues.append("regression.bootstrap.seed must be a nonnegative integer")
    partial = config.partial
    if partial is not None:
        if (
            not isinstance(partial.columns, list)
            or not partial.columns
            or any(not isinstance(name, str) or not name for name in partial.columns)
            or len(set(partial.columns)) != len(partial.columns)
        ):
            issues.append("partial.columns requires unique nonempty nuisance names")
        elif (
            not isinstance(partial.reference, dict)
            or set(partial.reference) != set(partial.columns)
            or any(not finite_number(value) for value in partial.reference.values())
        ):
            issues.append(
                "partial.reference requires exactly the finite nuisance values"
            )
        if partial.method != ("two_stage" if config.model == "lowess" else "joint"):
            issues.append("partial method is joint, or explicit two_stage for LOWESS")
        if isinstance(partial.columns, list):
            dimension = (
                len(partial.columns) + (degree if config.model == "poly" else 1) + 1
            )
            if dimension > MAX_REGRESSION_DESIGN:
                issues.append("NEW complete regression design exceeds19 columns")
    diagnostics = config.diagnostics
    if diagnostics is not None:
        if not config.residual:
            issues.append("regression.diagnostics requires residual=True")
        if diagnostics.kind not in ("raw", "deviance"):
            issues.append("diagnostics.kind must be raw or deviance")
        if diagnostics.kind == "deviance" and config.model != "logistic":
            issues.append("deviance diagnostics require a binomial-logit primary")
        trend = diagnostics.trend
        if trend is not None:
            if not isinstance(trend, RegressionTrendSpec):
                issues.append("diagnostics.trend must be RegressionTrendSpec")
            else:
                if trend.model not in ("poly", "logx", "robust", "lowess"):
                    issues.append("residual trend requires a continuous-response model")
                if type(trend.degree) is not int or not 1 <= trend.degree <= 10:
                    issues.append("trend.degree must be integer1..10")
                if trend.model != "poly" and trend.degree != 1:
                    issues.append("non-polynomial trend requires degree=1")
                if not finite_number(trend.frac) or not 0 < trend.frac <= 1:
                    issues.append("trend.frac must be finite in (0,1]")
                if type(trend.iterations) is not int or not 0 <= trend.iterations <= 20:
                    issues.append("trend.iterations must be integer0..20")
                if trend.model != "lowess" and (
                    trend.frac != 2 / 3 or trend.iterations != 3
                ):
                    issues.append("trend.frac/iterations require LOWESS")
                if trend.style is not None:
                    issues.extend(
                        style_issues(trend.style, MARK_FIELDS, "trend.style", "regplot")
                    )
    components = config.components
    if components is not None:
        for name in ("show_fit", "show_scatter"):
            if type(getattr(components, name)) is not bool:
                issues.append(f"components.{name} must be boolean")
        for role in ("fit", "scatter"):
            style = getattr(components, role)
            if style is not None:
                allowed = MARK_FIELDS if role == "fit" else MARK_FIELDS - {"line_style"}
                issues.extend(
                    style_issues(
                        style, allowed, f"regression.components.{role}", "regplot"
                    )
                )
                if (
                    role == "scatter"
                    and isinstance(style, ComponentStyleSpec)
                    and (
                        style.line_width is not None
                        and style.marker_edge_width is not None
                        and style.line_width != style.marker_edge_width
                    )
                ):
                    issues.append(
                        "scatter line_width/marker_edge_width must agree "
                        "on the actual outline"
                    )
    return issues


@dataclass(frozen=True, slots=True)
class RegressionCohort:
    """Original local source indices, never arbitrary caller ID joins."""

    group: object
    train: tuple[int, ...]
    query: tuple[int, ...]


def regression_cohorts(columns, layer):
    """Resolve strict roles through the existing typed selectors/partition."""
    from ._facet import panel_filter_issues, panel_rows
    from ._semantics import semantic_partition

    config = layer.regression
    if not isinstance(config, RegressionSpec):
        raise ValueError("regression cohorts require RegressionSpec")
    selected = source_rows(
        columns, layer, coordinates=(layer.x,), typed_hue=True, drop_missing=False
    )
    sampling = config.sampling
    if sampling is None:
        train, query = set(selected), set()
    else:
        if not isinstance(sampling, RegressionSamplingSpec):
            raise ValueError("sampling must be RegressionSamplingSpec")
        roles = []
        for selectors in (sampling.train, sampling.query):
            # Sampling selects rows from the already selected panel table.
            # This is not a rendered facet and owns no axes or sibling marks.
            view = PanelSpec(filters=selectors)
            problems = panel_filter_issues(columns, view)
            if problems:
                raise ValueError("; ".join(problems))
            roles.append(set(panel_rows(columns, view)) & set(selected))
        train, query = roles
        if train & query:
            raise ValueError("regression training/query rows must be disjoint")
    rows = [row for row in selected if row in train or row in query]
    ids, groups = semantic_partition(columns, SemanticSpec(hue=layer.group), rows)
    buckets = [[[], []] for _ in groups]
    for row, group in zip(rows, ids, strict=True):
        buckets[group][0 if row in train else 1].append(row)
    return tuple(
        RegressionCohort(group.get("hue"), tuple(parts[0]), tuple(parts[1]))
        for group, parts in zip(groups, buckets, strict=True)
    )


def regression_columns(layer, panel=None):
    """Names consumed by canonical regression/clock/selection helpers."""
    names = [layer.x, layer.y, layer.group, layer.c, layer.weights]
    config = layer.regression
    if isinstance(config, RegressionSpec):
        if isinstance(config.partial, RegressionPartialSpec):
            names.extend(config.partial.columns)
        if isinstance(config.sampling, RegressionSamplingSpec):
            for selectors in (config.sampling.train, config.sampling.query):
                if isinstance(selectors, dict):
                    names.extend(selectors)
    if panel is not None:
        names.extend(panel.filters)
        names.extend(panel.dropna)
    return tuple(dict.fromkeys(name for name in names if isinstance(name, str)))


def regression_inputs(raw_columns, panel, layer):
    """Original R4 view and row IDs; no semantic-value selection."""
    from ._facet import panel_rows
    from ._temporal_data import prepare_temporal_layer

    ids = panel_rows(raw_columns, panel)
    filtered = bool(panel.filters or panel.dropna)
    columns = {
        name: [raw_columns[name][row] for row in ids] if filtered else raw_columns[name]
        for name in regression_columns(layer, panel)
        if name in raw_columns
    }
    prepared, working, _ = prepare_temporal_layer(columns, layer, panel)
    return prepared, working, tuple(ids)


def positive_regression_rows(columns, rows, weight):
    return tuple(row for row in rows if weight is None or columns[weight][row] > 0)


def regression_data_issues(columns, layer, panel=None, *, source_ids=None):
    """Strict role-specific inputs, before optional numerical effects."""
    config = layer.regression
    problems = option_issues(config, layer.degree, layer.confidence)
    problems.extend(weighted_option_issues(config, layer.confidence, layer.weights))
    if problems:
        return problems
    try:
        cohorts = regression_cohorts(columns, layer)
    except (ValueError, TypeError, KeyError) as error:
        return [str(error)]
    if (
        not cohorts
        and config.sampling is None
        and layer.hue_order is None
        and not (panel is not None and (panel.filters or panel.dropna))
    ):
        return ["regression requires observations or an explicit empty selection"]
    if (
        len(
            source_rows(
                columns,
                layer,
                coordinates=(layer.x,),
                typed_hue=True,
                drop_missing=False,
            )
        )
        > MAX_REGRESSION_ROWS
    ):
        return ["typed regression supports at most10000 selected rows"]
    nuisance = () if config.partial is None else config.partial.columns
    required = [layer.x, layer.y, *nuisance]
    if layer.weights is not None:
        required.append(layer.weights)
    missing = [name for name in required if name not in columns]
    if missing:
        return [f"regression columns do not exist: {missing!r}"]
    if config.partial is not None and any(
        name in (layer.x, layer.y, layer.weights) for name in nuisance
    ):
        return [
            "nuisance columns must be distinct from predictor/response/weight roles"
        ]
    for cohort in cohorts:
        positive = {}
        for role, rows in (("training", cohort.train), ("query", cohort.query)):
            kept = []
            for row in rows:
                original_row = row if source_ids is None else source_ids[row]
                names = [layer.x, *nuisance]
                if role == "training" or config.residual:
                    names.append(layer.y)
                if any(not finite_number(columns[name][row]) for name in names):
                    problems.append(
                        f"{role} source row{original_row}: required regression inputs "
                        "must be finite"
                    )
                    continue
                if panel is not None:
                    other = panel.y2 if layer.axis == "y2" else panel.y
                    predictor_axis, response_axis = (
                        (other, panel.x) if layer.orient == "h" else (panel.x, other)
                    )
                    if (
                        predictor_axis is not None
                        and predictor_axis.scale == "log"
                        and columns[layer.x][row] <= 0
                    ):
                        problems.append(
                            f"{role} source row{original_row}: native log predictor "
                            "must be positive"
                        )
                    if (
                        layer.y in names
                        and response_axis is not None
                        and response_axis.scale == "log"
                        and columns[layer.y][row] <= 0
                    ):
                        problems.append(
                            f"{role} source row{original_row}: native log response "
                            "must be positive"
                        )
                weight = 1 if layer.weights is None else columns[layer.weights][row]
                if not finite_number(weight) or weight < 0:
                    problems.append(
                        f"{role} source row{original_row}: criterion mass "
                        "must be finite nonnegative"
                    )
                elif weight > 0:
                    kept.append(row)
            positive[role] = kept
        train = positive["training"]
        if cohort.train and not train:
            problems.append(f"group{cohort.group!r}: no positive training cases")
        if positive["query"] and not train:
            query_row = positive["query"][0]
            original_row = query_row if source_ids is None else source_ids[query_row]
            problems.append(
                f"query source row{original_row} has no fitted training group"
            )
        if not train:
            continue
        pairs = [(columns[layer.x][row], columns[layer.y][row]) for row in train]
        problems.extend(group_issues(config, pairs, len({x for x, _ in pairs})))
        dimension = (layer.degree if config.model == "poly" else 1) + len(nuisance) + 1
        if len(train) < dimension + (
            layer.confidence is not None and config.bootstrap is None
        ):
            problems.append(
                f"regression requires enough cases for its complete design{dimension}"
            )
        if config.model == "logx" and any(
            columns[layer.x][row] <= 0 for row in (*cohort.train, *cohort.query)
        ):
            problems.append(
                "logx regression requires positive native predictor coordinates"
            )
        diagnostics = config.diagnostics
        if diagnostics is not None and diagnostics.trend is not None:
            trend = diagnostics.trend
            rows = positive["query"] if config.sampling is not None else train
            if rows:
                pairs = [(columns[layer.x][row], columns[layer.y][row]) for row in rows]
                problems.extend(
                    group_issues(
                        RegressionSpec(
                            model=trend.model,
                            frac=trend.frac,
                            iterations=trend.iterations,
                        ),
                        pairs,
                        len({x for x, _ in pairs}),
                    )
                )
    return problems
