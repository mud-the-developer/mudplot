"""Render-local complete regression experiments and scoped NEW admission.

The estimate covers managed numerical structures and named provider reserves,
not process RSS, native artists or every opaque provider allocation. All known
figure work/state is checked before Generator construction/native publication.
"""

from __future__ import annotations

import math
import struct
import sys
from collections import Counter
from dataclasses import dataclass, replace
from fractions import Fraction

import numpy as np

from ._line_inference import _owned_size, _Ranks
from ._regression import (
    MAX_REGRESSION_DESIGN,
    MAX_REGRESSION_STATE,
    MAX_REGRESSION_WORK,
    configured_regression,
    new_regression,
    positive_regression_rows,
    regression_cohorts,
    regression_data_issues,
    regression_inputs,
)
from ._regression_model import affine_response, diagnostic, predict
from .spec import RegressionSpec


@dataclass(slots=True)
class RegressionCurve:
    group: object
    grid: np.ndarray
    mean: np.ndarray
    mean_bounds: tuple | None
    observation_x: np.ndarray
    observation_y: np.ndarray
    observation_rows: tuple
    query_x: np.ndarray
    query_mean: np.ndarray
    query_bounds: tuple | None
    query_rows: tuple
    trend_grid: np.ndarray
    trend_mean: np.ndarray
    trend_bounds: tuple | None
    caption: str | None


@dataclass(slots=True)
class PreparedRegression:
    layer: object
    curves: list
    source_rows: tuple


def _working_size(working, original):
    if working is original:
        return 0
    return (
        sys.getsizeof(working)
        + sys.getsizeof(vars(working))
        + sum(
            _owned_size(value)
            for name, value in vars(working).items()
            if value is not getattr(original, name)
        )
    )


def _input_size(columns, working, original, source_ids, source_columns):
    """New view containers/clock values, never recursively borrowed source."""
    size = sys.getsizeof(columns) + _owned_size(source_ids)
    aliases = {
        getattr(working, role)
        for role in ("x", "y")
        if getattr(working, role) != getattr(original, role)
    }
    for name, values in columns.items():
        if name in aliases:
            size += (
                sys.getsizeof(name)
                + sys.getsizeof(values)
                + sum(_owned_size(value) for value in values if value is not None)
            )
        elif values is not source_columns[name]:
            size += sys.getsizeof(values)
    return size + _working_size(working, original)


def _plans_size(cohorts, plans):
    # Cohort group labels borrow source values; row/index tuples are derived.
    return (
        _owned_size(plans)
        + sys.getsizeof(cohorts)
        + sum(
            sys.getsizeof(cohort) + _owned_size((cohort.train, cohort.query))
            for cohort in cohorts
        )
    )


def _prepared_size(result, original):
    size = (
        sys.getsizeof(result)
        + sys.getsizeof(result.curves)
        + _owned_size(result.source_rows)
        + _working_size(result.layer, original)
    )
    for curve in result.curves:
        size += sys.getsizeof(curve)
        for name in RegressionCurve.__slots__:
            value = getattr(curve, name)
            if name != "group" and value is not None:
                size += _owned_size(value)
    return size


def _caption(layer):
    if layer.confidence is None:
        return None
    config = layer.regression
    caption = (
        f"{layer.confidence:g}% nominal pointwise percentile CI\n"
        "IID paired physical cases"
        if config.bootstrap is not None
        else f"{layer.confidence:g}% approximate normal mean CI"
    )
    if config.residual:
        kind = "raw" if config.diagnostics is None else config.diagnostics.kind
        caption += f"\nMapped {kind}; fixed observed response"
    else:
        caption += "\nDeclared fitted response/operator"
    if config.diagnostics is not None and config.diagnostics.trend is not None:
        caption += "\nFULL primary+nuisance+trend refit"
    return caption


def _summary_reserve(layer, original, plans, source_ids):
    """Known output shapes and possible full-vector ndarray bases, not fits."""
    pointer = struct.calcsize("P")
    header = sys.getsizeof(np.empty(0))
    empty_tuple = sys.getsizeof(())
    size = (
        PreparedRegression.__basicsize__
        + empty_tuple
        + sys.getsizeof([])
        + (len(plans) * 2 + 8) * pointer
        + _owned_size(source_ids)
        + _working_size(layer, original)
    )
    config = layer.regression
    caption_size = _owned_size(_caption(layer))
    for plan in plans:
        if plan is None:
            continue
        n, q = len(plan["train"]), len(plan["query"])
        diagnostic_n = q if config.sampling is not None else n
        grid = 0 if config.residual else 200
        trend = (
            200
            if config.residual
            and diagnostic_n
            and config.diagnostics is not None
            and config.diagnostics.trend is not None
            else 0
        )
        e = plan["initial_evaluations"]
        arrays = [
            (grid, grid),
            (grid, e if grid else 0),
            (diagnostic_n if config.residual else n, 0),
            (diagnostic_n if config.residual else n, 0),
            (q, 0),
            (0 if config.residual else q, 0 if config.residual else e),
            (trend, trend),
            (trend, trend),
        ]
        if layer.confidence is not None and (
            config.bootstrap is not None or not config.residual
        ):
            bounds = [diagnostic_n] if config.residual else [grid, q]
            if trend:
                bounds.append(trend)
            for count in bounds:
                size += empty_tuple + 2 * pointer
                arrays.extend([(count, max(count, e))] * 2)
        size += RegressionCurve.__basicsize__ + empty_tuple + caption_size
        for count, base in arrays:
            size += header + 8 * count
            if base:
                size += header + 8 * base
        for rows in (
            plan["query"]
            if config.residual and config.sampling is not None
            else plan["train"],
            plan["query"],
        ):
            size += (
                empty_tuple
                + len(rows) * pointer
                + sum(sys.getsizeof(source_ids[row]) for row in rows)
            )
    return size


def _targets(layer, n, q, *, initial):
    config = layer.regression
    residual = config.residual
    diagnostic_n = q if config.sampling is not None else n
    trend = None if config.diagnostics is None else config.diagnostics.trend
    # Explicit empty OOS queries are not in-sample diagnostic observations.
    if residual:
        fixed = diagnostic_n
        evaluated = fixed + (diagnostic_n if trend is not None and not initial else 0)
        return (
            fixed + (200 if trend is not None and diagnostic_n else 0),
            evaluated,
            diagnostic_n,
        )
    evaluated = 200 + q
    if initial and config.partial is not None:
        evaluated += 2 * n
    return 200 + q, evaluated, diagnostic_n


def _point_charge(model, n, p, e, mass_bits, frac, iterations, partial):
    median = n * (2 * max(1, n.bit_length()) + mass_bits + 1)
    linear = n * p * p + p**3
    components = {
        "design": 0,
        "normalization": n * (p + 8) + e * (p + 4),
        "evaluation": e * p,
        "median": 0,
        "local": 0,
    }
    if model in ("poly", "logx"):
        components["design"] = linear * (2 if partial else 1)
    elif model in ("robust", "logistic"):
        steps = 50 if model == "robust" else 100
        components["design"] = (steps + 3) * linear
        components["median"] = (steps + 1) * median if model == "robust" else 0
    else:
        neighbors = min(n, max(2, int(frac * n + 1e-10)))
        components["design"] = 2 * linear if partial else 0
        components["evaluation"] = e
        components["median"] = iterations * median
        components["local"] = (iterations * n + e) * (n + 4 * neighbors + 8)
    return components


def _mass_bits(values):
    if values is None:
        return 1, 1, 2
    numerator = denominator = 1
    for value in values:
        fraction = Fraction(value)
        numerator = max(numerator, fraction.numerator.bit_length())
        denominator = max(denominator, fraction.denominator.bit_length())
    # Saved finite integer/binary64 masses have dyadic denominators.
    return numerator, denominator, numerator + denominator + 1


def _cdf_reserve(n, nb, db, mb):
    def integer(bits):
        return sys.getsizeof(1 << max(1, bits))

    pointer = struct.calcsize("P")
    fraction = sys.getsizeof(Fraction(1, 2))
    per_case = (
        2 * fraction
        + 2 * (integer(nb) + integer(db))
        + integer(mb)
        + integer(mb + n.bit_length() + 1)
        + sys.getsizeof((None, None))
        + integer(n.bit_length())
        + sys.getsizeof(0.0)
        + 20 * pointer
    )
    return (
        n * per_case
        + 12 * sys.getsizeof([])
        + 8 * sys.getsizeof(())
        + 32 * integer(nb + db + n.bit_length() + 8)
    )


def _collector_reserve(b, targets, level):
    if not targets:
        return 0, 0
    example = _Ranks(b, level, False)
    low, high = (tail.capacity for tail in example.tails)
    pointer = struct.calcsize("P")
    listing, floating = sys.getsizeof([]), sys.getsizeof(0.0)
    # Each rank object owns its positions/tails; future list growth and actual
    # float/sign nodes are additional to that measured empty product graph.
    controls = targets * _owned_size(example) + listing + (2 * targets + 8) * pointer
    heaps = targets * (
        ((2 * low + 8) + (2 * high + 8)) * pointer + (low + high) * floating
    )
    ordered = 2 * listing + (2 * low + 2 * high + 16) * pointer + low * floating
    sorting = ((max(low, high) + 1) // 2) * pointer
    assert example.positions is not None
    probability_bits = max(
        value.denominator.bit_length() for value in example.positions
    )
    integer = sys.getsizeof(1 << (2100 + probability_bits + b.bit_length() + 8))
    exact = 32 * integer + 12 * sys.getsizeof(Fraction())
    return controls + heaps + ordered + sorting + exact + 16 * targets, max(low, high)


def _seed_charge(seed):
    words = max(1, (seed.bit_length() + 31) // 32)
    pointer = struct.calcsize("P")
    storage = (
        4 * sys.getsizeof(seed)
        + 2 * (sys.getsizeof([]) + (2 * words + 8) * pointer)
        + words * (sys.getsizeof(np.uint32(0)) + 4)
    )
    # Fixed scalar/control reserve below includes pool/Generator headers.
    return words * words, storage


def _numeric_inventory(n, p, e, r, model, *, weighted, normal_e=0):
    """Reserve named product buffers, with model-specific provider lifetimes.

    High-level provider copies are conservative reserves, not a universal
    LAPACK/allocator guarantee. No N-by-N matrix or unused fit grid is created.
    """
    header = sys.getsizeof(np.empty((0, 0), dtype=float))
    shapes = {
        "source_and_sample_xyw": 6 * n,
        "source_and_sample_nuisance": 2 * n * r,
        "normalized_main_response_requested": 4 * n + 2 * e,
        "nuisance_lists_and_column_stacks": 2 * (n + e) * (r + 1),
        "fitted_residual_step_and_return": 5 * n + 3 * e,
    }
    if model == "lowess":
        shapes["physical_local_arrays_and_robust_training"] = 18 * n + e
        if r:
            shapes["two_stage_nuisance_solve_buffers"] = (
                2 * n * (p - 1) + 4 * n + (p - 1) ** 2 + 2 * (p - 1)
            )
    else:
        shapes.update(
            {
                "full_design_and_target": (n + e) * p,
                "weighted_SVD_design_and_provider_copy": 2 * n * p,
                "weighted_rhs_root_and_copy": 4 * n,
                "SVD_singular_beta_right_basis": 2 * p + p * p,
            }
        )
    if model == "robust":
        shapes["coupled_Huber_IRLS_vectors"] = 6 * n
    if model == "logistic" or (model == "robust" and not weighted):
        shapes.update(
            {
                "provider_weighted_design_and_pseudoinverse": 2 * n * p,
                "provider_mean_weights_derivative_response": 7 * n,
                "provider_covariance_and_Hessian": 2 * p * p,
            }
        )
    if normal_e:
        shapes["consumed_normal_covariance_projection"] = normal_e * p
    return sum(8 * elements + header for elements in shapes.values()), shapes


def _provider_history(model, parameters, weighted):
    steps = (
        100 if model == "logistic" else 50 if model == "robust" and not weighted else 0
    )
    if not steps:
        return 0
    header = sys.getsizeof(np.empty((0, 0), dtype=float))
    pointer = struct.calcsize("P")
    return (
        (steps + 3) * (header + 8 * parameters + 2 * sys.getsizeof(0.0) + 4 * pointer)
        + 4 * sys.getsizeof([])
        + (4 * steps + 16) * pointer
    )


def _affine_reserve(rows):
    """Object-vector/list conversion and one finite dyadic arithmetic step."""
    bits = 2 * sys.float_info.max_exp + sys.float_info.mant_dig + 16
    pointer = struct.calcsize("P")
    header = sys.getsizeof(np.empty((0,), dtype=object))
    return (
        header
        + 8 * rows
        + sys.getsizeof([])
        + (2 * rows + 8) * pointer
        + rows * sys.getsizeof(0.0)
        + 4 * sys.getsizeof(Fraction())
        + 12 * sys.getsizeof(1 << bits)
    )


def _curve_plan(columns, layer, cohort):
    config = layer.regression
    train = positive_regression_rows(columns, cohort.train, layer.weights)
    query = positive_regression_rows(columns, cohort.query, layer.weights)
    n, q = len(train), len(query)
    if not n or (config.residual and config.sampling is not None and not q):
        return None
    r = 0 if config.partial is None else len(config.partial.columns)
    p = (layer.degree if config.model == "poly" else 1) + r + 1
    if p > MAX_REGRESSION_DESIGN:
        raise ValueError("NEW complete regression design exceeds19 columns")
    masses = (
        None
        if layer.weights is None
        else tuple(columns[layer.weights][row] for row in (*train, *query))
    )
    nb, db, mb = _mass_bits(masses)
    bootstrap = config.bootstrap
    b = 0 if bootstrap is None else bootstrap.n_boot
    target_count, initial_e, diagnostic_n = _targets(layer, n, q, initial=True)
    _targets_count, replicate_e, _dn = _targets(layer, n, q, initial=False)
    components = _point_charge(
        config.model, n, p, initial_e, mb, config.frac, config.iterations, bool(r)
    )
    if b:
        repeated = _point_charge(
            config.model, n, p, replicate_e, mb, config.frac, config.iterations, bool(r)
        )
        for key in components:
            components[key] += b * repeated[key]
    trend = None if config.diagnostics is None else config.diagnostics.trend
    if trend is not None and diagnostic_n:
        tp = trend.degree + 1 if trend.model == "poly" else 2
        part = _point_charge(
            trend.model, diagnostic_n, tp, 200, mb, trend.frac, trend.iterations, False
        )
        for key in components:
            components[key] += (b + 1) * part[key]
    normal = (
        config.partial is not None
        and layer.confidence is not None
        and bootstrap is None
    )
    if normal:
        components["normal_covariance"] = n * p * p + p**3 + target_count * p * p
    components["case_choices"] = b * (n + q)
    components["paired_row_gathers"] = b * (n * (4 + r) + q * (4 + r))
    collector, capacity = (
        _collector_reserve(b, target_count, layer.confidence) if b else (0, 0)
    )
    components["tails"] = 2 * b * target_count * (2 * max(1, capacity.bit_length()) + 3)
    raw = config.residual and (
        config.diagnostics is None or config.diagnostics.kind == "raw"
    )
    affine_rows = n if r and not config.residual else diagnostic_n if raw else 0
    affine_steps = 3 * n if r and not config.residual else 0
    if raw:
        affine_steps += 3 * diagnostic_n * (1 + (b if trend is not None else 0))
        affine_steps += 4 * diagnostic_n if b else 0
    bits = 2 * sys.float_info.max_exp + sys.float_info.mant_dig + 16
    components["native_affine_word_upper"] = affine_steps * math.ceil(bits / 64)
    affine = _affine_reserve(affine_rows) if affine_rows else 0
    e = max(initial_e, replicate_e)
    weighted = layer.weights is not None
    numeric, inventory = _numeric_inventory(
        n,
        p,
        e,
        r,
        config.model,
        weighted=weighted,
        normal_e=target_count if normal else 0,
    )
    if trend is not None and diagnostic_n:
        tp = trend.degree + 1 if trend.model == "poly" else 2
        trend_numeric, trend_inventory = _numeric_inventory(
            diagnostic_n, tp, 200, 0, trend.model, weighted=weighted
        )
        numeric += trend_numeric
        inventory.update(
            {f"trend_{name}": value for name, value in trend_inventory.items()}
        )
    header = sys.getsizeof(np.empty((0, 0), dtype=float))
    history = _provider_history(config.model, p, weighted)
    if trend is not None and diagnostic_n:
        history += _provider_history(trend.model, tp, weighted)
    cdf_n = max(
        n if config.model in ("robust", "lowess") else 0,
        diagnostic_n
        if trend is not None and trend.model in ("robust", "lowess")
        else 0,
    )
    cdf = _cdf_reserve(cdf_n, nb, db, mb) if masses is not None and cdf_n else 0
    source = 4 * sys.getsizeof(()) + (n + q) * (
        sys.getsizeof(0) + 4 * struct.calcsize("P")
    )
    summaries = 8 * (4 * target_count + n + q) + 8 * header
    controls = (
        _owned_size(
            (components, inventory, cohort.train, cohort.query, source, summaries)
        )
        + np.random.PCG64.__basicsize__
        + np.random.Generator.__basicsize__
        + np.random.SeedSequence.__basicsize__
        + header
        + 4 * 4
    )
    state = collector + numeric + history + cdf + source + summaries + controls + affine
    return {
        "train": train,
        "query": query,
        "work": components,
        "state": state,
        "state_components": {
            "collector": collector,
            "numeric_buffers_provider_reserve": numeric,
            "provider_history": history,
            "canonical_CDF": cdf,
            "native_affine_objects_and_scratch": affine,
            "source_objects": source,
            "summary_arrays": summaries,
            "controls": controls,
            "numeric_inventory_float64_elements": inventory,
        },
        "targets": target_count,
        "initial_evaluations": initial_e,
        "replicate_evaluations": replicate_e,
        "nuisance": r,
        "design": p,
    }


def _grid(x, model):
    if model == "logx":
        return np.exp(np.linspace(float(np.log(x).min()), float(np.log(x).max()), 200))
    return np.linspace(float(x.min()), float(x.max()), 200)


def _rows_array(columns, name, rows):
    return np.asarray([columns[name][row] for row in rows], dtype=float)


def _nuisance(columns, config, rows):
    if config.partial is None:
        return None
    return np.column_stack(
        [_rows_array(columns, name, rows) for name in config.partial.columns]
    )


def _evaluate(x, y, masses, z, parts, layer, polynomial_fit, *, normal=False):
    at = np.concatenate([part[0] for part in parts])
    zat = None if z is None else np.concatenate([part[1] for part in parts])
    values, bounds = predict(
        x,
        y,
        masses,
        at,
        layer,
        polynomial_fit,
        nuisance=z,
        nuisance_at=zat,
        normal=normal,
        normal_count=sum(len(part[0]) for part in parts[:2]) if normal else None,
    )
    outputs, intervals, offset = [], [], 0
    for points, _nuisance_values in parts:
        end = offset + len(points)
        outputs.append(values[offset:end])
        intervals.append(
            None
            if bounds is None or end > len(bounds[0])
            else (bounds[0][offset:end], bounds[1][offset:end])
        )
        offset = end
    return outputs, intervals


def _native_bounds(lower, upper):
    left, right = float(lower), float(upper)
    if not math.isfinite(left) or not math.isfinite(right):
        raise ValueError("regression interval exceeds finite native coordinates")
    if lower < upper and left == right:
        raise ValueError("positive regression interval collapses in native coordinates")
    return left, right


def _finish(ranks, kind=None, y=None, source_rows=()):
    if not ranks:
        return None
    lower, upper = np.empty(len(ranks)), np.empty(len(ranks))
    for index, rank in enumerate(ranks):
        lo, hi = rank.percentile()
        if kind == "raw":
            assert y is not None
            lo, hi = Fraction(y[index]) - hi, Fraction(y[index]) - lo
        elif kind == "deviance":
            assert y is not None
            mean_lo, mean_hi = _native_bounds(lo, hi)
            lo = diagnostic([y[index]], [mean_hi], kind, [source_rows[index]])[0]
            hi = diagnostic([y[index]], [mean_lo], kind, [source_rows[index]])[0]
            if mean_lo < mean_hi and lo == hi:
                raise ValueError(
                    "positive mean interval collapses after native deviance mapping"
                )
        lower[index], upper[index] = _native_bounds(lo, hi)
        rank.clear()
    return lower, upper


def _compute(columns, layer, cohorts, plans, source_ids, polynomial_fit):
    config = layer.regression
    diagnostics = config.diagnostics
    kind = "raw" if diagnostics is None else diagnostics.kind
    trend = None if diagnostics is None else diagnostics.trend
    bootstrap = config.bootstrap
    b = 0 if bootstrap is None else bootstrap.n_boot
    entries = []
    for cohort, plan in zip(cohorts, plans, strict=True):
        if plan is None:
            continue
        train, query = plan["train"], plan["query"]
        diagnostic_rows = query if config.sampling is not None else train
        if config.residual and not diagnostic_rows:
            continue
        x, y = (
            _rows_array(columns, layer.x, train),
            _rows_array(columns, layer.y, train),
        )
        w = (
            None
            if layer.weights is None
            else tuple(columns[layer.weights][row] for row in train)
        )
        z = _nuisance(columns, config, train)
        dx = _rows_array(columns, layer.x, diagnostic_rows)
        dy = (
            np.asarray([columns[layer.y][row] for row in diagnostic_rows], dtype=object)
            if config.residual
            else None
        )
        dz = _nuisance(columns, config, diagnostic_rows)
        qx, qz = _rows_array(columns, layer.x, query), _nuisance(columns, config, query)
        grid = np.empty(0) if config.residual else _grid(x, config.model)
        reference = (
            None
            if z is None
            else np.asarray(
                [config.partial.reference[name] for name in config.partial.columns]
            )
        )
        grid_z = None if z is None else np.tile(reference, (len(grid), 1))
        parts = [(dx, dz)] if config.residual else [(grid, grid_z), (qx, qz)]
        if not config.residual and z is not None:
            parts += [(x, z), (x, np.tile(reference, (len(x), 1)))]
        point, normal_bounds = _evaluate(
            x,
            y,
            w,
            z,
            parts,
            layer,
            polynomial_fit,
            normal=layer.confidence is not None and bootstrap is None,
        )
        native_rows = tuple(
            source_ids[row] for row in (diagnostic_rows if config.residual else train)
        )
        if config.residual:
            observation_y = diagnostic(dy, point[0], kind, native_rows)
            observation_x = dx
            mean, query_mean = np.empty(0), np.empty(0)
            fixed_count = len(dx)
        else:
            mean, query_mean = point[:2]
            observation_y = (
                y
                if z is None
                else affine_response(
                    (columns[layer.y][row] for row in train),
                    point[2],
                    native_rows,
                    reference=point[3],
                )
            )
            observation_x = x
            fixed_count = len(grid) + len(qx)
        trend_grid = np.empty(0)
        trend_mean = np.empty(0)
        trend_layer = None
        dw = (
            None
            if layer.weights is None
            else tuple(columns[layer.weights][row] for row in diagnostic_rows)
        )
        if config.residual and trend is not None:
            trend_layer = replace(
                layer,
                degree=trend.degree,
                confidence=None,
                regression=RegressionSpec(
                    model=trend.model, frac=trend.frac, iterations=trend.iterations
                ),
            )
            trend_grid = _grid(dx, trend.model)
            trend_mean, _ = predict(
                dx, observation_y, dw, trend_grid, trend_layer, polynomial_fit
            )
        count = fixed_count + len(trend_grid)
        ranks = [_Ranks(b, layer.confidence, False) for _ in range(count)] if b else []
        entries.append(
            {
                "cohort": cohort,
                "plan": plan,
                "x": x,
                "y": y,
                "w": w,
                "z": z,
                "qx": qx,
                "qz": qz,
                "dx": dx,
                "dy": dy,
                "dz": dz,
                "dw": dw,
                "grid": grid,
                "grid_z": grid_z,
                "mean": mean,
                "query_mean": query_mean,
                "ox": observation_x,
                "oy": observation_y,
                "rows": native_rows,
                "trend_grid": trend_grid,
                "trend_mean": trend_mean,
                "trend_layer": trend_layer,
                "ranks": ranks,
                "normal": normal_bounds,
                "undefined": Counter(),
            }
        )
    if bootstrap is not None and entries:
        rng = np.random.Generator(np.random.PCG64(bootstrap.seed))
        draw_order = sorted(
            entries,
            key=lambda entry: min(
                source_ids[row]
                for role in ("train", "query")
                for row in entry["plan"][role]
            ),
        )
        for _replicate in range(b):
            for entry in draw_order:
                n, q = len(entry["x"]), len(entry["qx"])
                sampled = rng.integers(0, n, size=n, dtype=np.int64)
                query_sample = (
                    rng.integers(0, q, size=q, dtype=np.int64)
                    if config.sampling is not None and q
                    else None
                )
                try:
                    sx, sy = entry["x"][sampled], entry["y"][sampled]
                    sw = (
                        None
                        if entry["w"] is None
                        else tuple(entry["w"][int(i)] for i in sampled)
                    )
                    sz = None if entry["z"] is None else entry["z"][sampled]
                    parts = (
                        [(entry["dx"], entry["dz"])]
                        if config.residual
                        else [
                            (entry["grid"], entry["grid_z"]),
                            (entry["qx"], entry["qz"]),
                        ]
                    )
                    if entry["trend_layer"] is not None:
                        selected = (
                            query_sample if config.sampling is not None else sampled
                        )
                        tx = entry["dx"][selected]
                        tz = None if entry["dz"] is None else entry["dz"][selected]
                        parts.append((tx, tz))
                    predictions, _intervals = _evaluate(
                        sx, sy, sw, sz, parts, layer, polynomial_fit
                    )
                    scores = [predictions[0]] if config.residual else predictions[:2]
                    if entry["trend_layer"] is not None:
                        selected = (
                            query_sample if config.sampling is not None else sampled
                        )
                        assert selected is not None
                        residual = diagnostic(
                            entry["dy"][selected],
                            predictions[-1],
                            kind,
                            [entry["rows"][int(i)] for i in selected],
                        )
                        diagnostic_weights = entry["dw"]
                        tw = (
                            None
                            if diagnostic_weights is None
                            else tuple(diagnostic_weights[int(i)] for i in selected)
                        )
                        fitted, _ = predict(
                            entry["dx"][selected],
                            residual,
                            tw,
                            entry["trend_grid"],
                            entry["trend_layer"],
                            polynomial_fit,
                        )
                        scores.append(fitted)
                    for rank, value in zip(
                        entry["ranks"], np.concatenate(scores), strict=True
                    ):
                        rank.add(float(value))
                except (
                    ValueError,
                    FloatingPointError,
                    np.linalg.LinAlgError,
                    Warning,
                ) as error:
                    entry["undefined"][str(error)] += 1
        failed = [
            (entry["cohort"].group, dict(entry["undefined"]))
            for entry in entries
            if entry["undefined"]
        ]
        if failed:
            raise ValueError(
                f"regression percentile requires all{b} replicates defined; "
                f"undefined={failed!r}; all draws retained, no retries"
            )
    curves = []
    for entry in entries:
        grid, qx, ranks = entry["grid"], entry["qx"], entry["ranks"]
        if config.residual:
            fixed = len(entry["dx"])
            mapped = _finish(ranks[:fixed], kind, entry["dy"], entry["rows"])
            mean_bounds, query_bounds = mapped, None
        else:
            fixed = len(grid) + len(qx)
            mean_bounds = _finish(ranks[: len(grid)]) if b else entry["normal"][0]
            query_bounds = (
                _finish(ranks[len(grid) : fixed]) if b else entry["normal"][1]
            )
        trend_bounds = _finish(ranks[fixed:])
        caption = _caption(layer)
        curves.append(
            RegressionCurve(
                entry["cohort"].group,
                grid,
                entry["mean"],
                mean_bounds,
                entry["ox"],
                entry["oy"],
                entry["rows"],
                qx,
                entry["query_mean"],
                query_bounds,
                tuple(source_ids[row] for row in entry["plan"]["query"]),
                entry["trend_grid"],
                entry["trend_mean"],
                trend_bounds,
                caption,
            )
        )
    return PreparedRegression(layer, curves, source_ids)


def prepare_regressions(spec, polynomial_fit):
    """Preflight every known NEW figure work/state term before the first RNG."""
    entries = []
    total_work = total_seed_work = known_plans = known_inputs = 0
    for pi, panel in enumerate(spec.panels):
        for li, layer in enumerate(panel.layers):
            if layer.type != "regplot" or not configured_regression(layer):
                continue
            columns, working, source_ids = regression_inputs(
                spec.data.columns, panel, layer
            )
            problems = regression_data_issues(
                columns, working, panel, source_ids=source_ids
            )
            if problems:
                raise ValueError("; ".join(problems))
            cohorts = regression_cohorts(columns, working)
            plans = [_curve_plan(columns, working, cohort) for cohort in cohorts]
            is_new = new_regression(layer)
            work = (
                sum(sum(plan["work"].values()) for plan in plans if plan is not None)
                if is_new
                else 0
            )
            seed_state = 0
            if working.regression.bootstrap is not None and any(
                plan is not None for plan in plans
            ):
                seed_work, seed_state = _seed_charge(working.regression.bootstrap.seed)
                work += seed_work
                total_seed_work += seed_work
            if work > MAX_REGRESSION_WORK or total_work + work > MAX_REGRESSION_WORK:
                raise ValueError(
                    "NEW regression invocation/figure logical work "
                    "exceeds6000000000 before RNG/native"
                )
            total_work += work
            plan_size = _plans_size(cohorts, plans) if is_new else 0
            input_size = (
                _input_size(columns, working, layer, source_ids, spec.data.columns)
                if is_new
                else 0
            )
            known_plans += plan_size
            known_inputs += input_size
            summary = (
                _summary_reserve(working, layer, plans, source_ids) if is_new else 0
            )
            state = (
                sum(
                    plan["state"] - plan["state_components"]["summary_arrays"]
                    for plan in plans
                    if plan is not None
                )
                + summary
                + seed_state
                if is_new
                else 0
            )
            if known_plans + known_inputs + state > MAX_REGRESSION_STATE and is_new:
                raise ValueError(
                    "NEW regression managed/provider-reserve admission estimate "
                    "exceeds268435456 bytes before RNG/native; "
                    "known plans/input/stage state, not an RSS/native-artist bound"
                )
            entries.append(
                (
                    pi,
                    li,
                    columns,
                    working,
                    source_ids,
                    cohorts,
                    plans,
                    plan_size,
                    input_size,
                    summary,
                    state,
                )
            )
    if entries:
        del columns, working, source_ids, cohorts, plans
    # All input views are materialized once and remain live in the existing
    # render-local table. Known earlier output shapes join each prospective peak.
    remaining_inputs, remaining_plans = known_inputs, known_plans
    earlier_summary = peak = 0
    for entry in entries:
        pi, li, _columns, _working, _ids, _cohorts, _plans, ps, ins, summary, state = (
            entry
        )
        if new_regression(spec.panels[pi].layers[li]):
            prospective = remaining_inputs + remaining_plans + earlier_summary + state
            if prospective > MAX_REGRESSION_STATE:
                raise ValueError(
                    "NEW regression figure known managed/provider-reserve admission "
                    "estimate exceeds268435456 bytes before RNG/native; "
                    "not an RSS/native-artist bound"
                )
            peak = max(peak, prospective)
            earlier_summary += summary + sys.getsizeof({0: None}) - sys.getsizeof({})
        remaining_inputs -= ins
        remaining_plans -= ps
    if entries:
        del entry, _columns, _working, _ids, _cohorts, _plans
    retained, prepared = 0, {}
    work_components = Counter(seed_word_conversion=total_seed_work)
    for entry_index, entry in enumerate(entries):
        (
            pi,
            li,
            columns,
            working,
            source_ids,
            cohorts,
            plans,
            ps,
            ins,
            summary,
            state,
        ) = entry
        entries[entry_index] = None
        del entry
        original = spec.panels[pi].layers[li]
        is_new = new_regression(original)
        if is_new:
            actual_peak = known_inputs + known_plans + retained + state
            if actual_peak > MAX_REGRESSION_STATE:
                raise ValueError(
                    "NEW regression managed/provider-reserve admission estimate "
                    "exceeds268435456 bytes before RNG/native; "
                    "retained numerical results, not an RSS/native-artist bound"
                )
            peak = max(peak, actual_peak)
            for plan in plans:
                if plan is not None:
                    work_components.update(plan["work"])
            if plans:
                del plan
        result = _compute(columns, working, cohorts, plans, source_ids, polynomial_fit)
        if is_new:
            retained += (
                _prepared_size(result, original)
                + sys.getsizeof({0: None})
                - sys.getsizeof({})
            )
            if retained > MAX_REGRESSION_STATE:
                raise ValueError(
                    "NEW retained regression summaries exceed268435456 bytes; "
                    "no native output published"
                )
        prepared[(pi, li)] = result
        known_plans -= ps
        known_inputs -= ins
        del columns, working, source_ids, cohorts, plans, result
    return prepared, {
        "logical_work_upper": total_work,
        "components": dict(work_components),
        "peak_managed_provider_reserve_estimate_bytes": peak,
        "retained_summary_bytes": retained,
        "scope": "NEW conservative numerical admission estimate, not "
        "RSS/native-artists/opaque-provider universal bound",
    }
