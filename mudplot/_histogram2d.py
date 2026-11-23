"""Paired canonical tally and true-edge geometry for explicit bivariate histograms.

Histogram denominators are IN-BIN mass. An optional density model consumes the
same pre-tally rows, not these filtered counts. Effect imports remain local.
"""

from __future__ import annotations

import math
from bisect import bisect_right
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from ._density import histogram2d_config
from ._density_input import FieldInput, prepare_input
from ._histogram import MAX_BIVARIATE_BINS
from ._histogram_bins import discrete_bin_edges, named_bin_edges
from .spec import BivariateBinsSpec


@dataclass(slots=True)
class HistogramField:
    index: int
    hue: Any
    roles: dict
    rows: tuple[int, ...]
    pool: Any
    values: Any
    in_bin_units: int
    comparison_units: int
    leases: list = field(default_factory=list, repr=False)


@dataclass(slots=True)
class HistogramPlan:
    x_edges: tuple
    y_edges: tuple
    fields: list[HistogramField]
    selected_rows: tuple[int, ...]
    mass_denominator: int
    stat: str
    leases: list = field(default_factory=list, repr=False)
    cohort: FieldInput | None = None
    owns_input: bool = False

    def close(self):
        for item in self.fields:
            for lease in reversed(item.leases):
                lease.close()
            item.leases.clear()
            item.values = None
        for lease in reversed(self.leases):
            lease.close()
        self.leases.clear()
        if self.owns_input and self.cohort is not None:
            self.cohort.close()


def bin_choices(bins):
    if isinstance(bins, BivariateBinsSpec):
        return bins.x, bins.y
    if isinstance(bins, (list, tuple)) and len(bins) == 2:
        # Preserve NumPy's ambiguous old flat [2,3] per-axis COUNT meaning.
        return bins[0], bins[1]
    return bins, bins


def resolve_edges(values, choice, budget=None):
    """Reuse the pinned unweighted scalar bin definitions independently per axis."""
    import numpy as np

    if not values and not isinstance(choice, (list, tuple)):
        return ()
    scratch = None
    if budget is not None:
        # Source views/selector buffers, including the existing Stone candidates.
        scratch = budget.array_lease((len(values),), copies=4)
        if isinstance(choice, str):
            candidates = max(100, math.isqrt(len(values))) if choice == "stone" else 1
            budget.charge(
                "bin_rule_rows", len(values) * (candidates + len(values).bit_length())
            )
        else:
            budget.charge("bin_edge_rows", len(values))
    try:
        if choice == "discrete":
            result = discrete_bin_edges(values)
        elif isinstance(choice, str):
            result = named_bin_edges(values, choice)
        elif type(choice) is int:
            result = np.histogram_bin_edges(
                np.asarray(values, dtype=float), bins=choice
            )
        else:
            result = choice
        if not 2 <= len(result) <= MAX_BIVARIATE_BINS + 1:
            raise ValueError("bivariate histograms require1..512 bins per coordinate")
        edges = tuple(Fraction(value) for value in result)
        native = np.asarray(edges, dtype=float)
        with np.errstate(over="ignore", invalid="ignore"):
            widths = np.diff(native)
        if not np.all(np.isfinite(native)) or not np.all(
            np.isfinite(widths) & (widths > 0)
        ):
            raise ValueError(
                "histogram native edges/widths must remain finite and strictly "
                "increasing"
            )
        return edges
    finally:
        if scratch is not None:
            scratch.close()


def _index(edges, value):
    if value < edges[0] or value > edges[-1]:
        return None
    return min(bisect_right(edges, value) - 1, len(edges) - 2)


def _finite_stat(value):
    try:
        result = float(value)
    except OverflowError as error:
        raise ValueError("histogram statistic is not natively representable") from error
    if not math.isfinite(result) or (value and not result):
        raise ValueError(
            "positive histogram statistic overflowed/underflowed native precision"
        )
    return result


def prepare_histogram2d(columns, layer, panel, budget=None, *, input_plan=None):
    """Fit shared edges once and retain every selected paired physical instance."""
    import sys

    import numpy as np

    cohort = (
        prepare_input(columns, layer, panel, budget)
        if input_plan is None
        else input_plan
    )
    owns_input = input_plan is None
    budget = cohort.budget
    rows, groups = cohort.rows, cohort.groups
    config = histogram2d_config(layer)
    leases, scratch = [], []
    plan = HistogramPlan(
        (), (), [], rows, cohort.denominator, config.stat, leases, cohort, owns_input
    )
    try:
        if not rows:
            x_choice, y_choice = bin_choices(layer.bins)
            plan.x_edges = resolve_edges([], x_choice, budget)
            plan.y_edges = resolve_edges([], y_choice, budget)
            return plan
        x_values = [columns[layer.x][row] for row in rows]
        y_values = [columns[layer.y][row] for row in rows]
        x_choice, y_choice = bin_choices(layer.bins)
        plan.x_edges = resolve_edges(x_values, x_choice, budget)
        plan.y_edges = resolve_edges(y_values, y_choice, budget)
        nx, ny = len(plan.x_edges) - 1, len(plan.y_edges) - 1
        denominator = cohort.denominator
        mass_by_row = cohort.mass_by_row
        if budget is not None:
            leases.append(budget.account((plan.x_edges, plan.y_edges)))
            width = (
                max(mass.bit_length() for mass in cohort.masses)
                + len(rows).bit_length()
                + 1
            )
            scratch.append(
                budget.hashmap_lease(
                    len(rows),
                    key_bytes=sys.getsizeof((None, None)) + 2 * sys.getsizeof(nx),
                )
            )
            scratch.append(
                budget.integer_lease(width, count=len(rows) + len(groups) + 1)
            )
        sparse = []
        pool_totals = {}
        global_total = 0
        for group in groups:
            tally = {}
            total = 0
            for row in group["rows"]:
                ix = _index(plan.x_edges, columns[layer.x][row])
                iy = _index(plan.y_edges, columns[layer.y][row])
                if budget is not None:
                    budget.charge("bin_searches", nx.bit_length() + ny.bit_length())
                if ix is None or iy is None:
                    continue
                key = ix, iy
                weight = mass_by_row[row]
                old = tally.get(key, 0)
                if budget is not None:
                    budget.charge(
                        "integer_bin_add",
                        4,
                        bits=max(
                            old.bit_length(),
                            total.bit_length(),
                            global_total.bit_length(),
                            weight.bit_length(),
                        )
                        + 1,
                    )
                tally[key] = old + weight
                total += weight
                global_total += weight
                pool_totals[group["pool"]] = pool_totals.get(group["pool"], 0) + weight
            sparse.append((group, tally, total))
        if config.stat in ("count", "frequency"):
            _finite_stat(Fraction(global_total, denominator))
        normalized = config.stat in ("probability", "proportion", "percent", "density")
        if normalized and not global_total:
            raise ValueError(
                "observed histogram has no in-bin mass for requested normalization"
            )
        for group, tally, total in sparse:
            if not group["rows"]:
                continue
            comparison = (
                global_total
                if config.common_norm
                else pool_totals.get(group["pool"], 0)
            )
            if normalized and not comparison:
                # This effective-hue pool has no defined normalized field.
                continue
            item = HistogramField(
                group["index"],
                group["hue"],
                group["roles"],
                tuple(group["rows"]),
                group["pool"],
                None,
                total,
                comparison,
            )
            plan.fields.append(item)
            if budget is not None:
                # One temporary matrix, one native ScalarMappable copy.
                leases.append(budget.array_lease((nx, ny)))
                item.leases.append(budget.array_lease((nx, ny)))
                item.leases.append(budget.native_path_lease(5 * nx * ny, nx * ny))
                item.leases.append(budget.array_lease((ny + 1, nx + 1, 2), copies=2))
                # Native face colours/normalization temporaries are NOT canvas RGBA.
                item.leases.append(budget.array_lease((nx, ny, 4), copies=2))
                item.leases.append(budget.array_lease((nx, ny), dtype="bool"))
                budget.charge("statistic_output_cells", nx * ny)
            values = np.zeros((nx, ny), dtype=float)
            for (ix, iy), weight in tally.items():
                value = Fraction(weight, denominator)
                if normalized:
                    value = Fraction(weight, comparison)
                    if config.stat == "percent":
                        value *= 100
                if config.stat in ("frequency", "density"):
                    area = (plan.x_edges[ix + 1] - plan.x_edges[ix]) * (
                        plan.y_edges[iy + 1] - plan.y_edges[iy]
                    )
                    value /= area
                if budget is not None:
                    budget.charge(
                        "integer_statistic_ratio",
                        6,
                        bits=max(
                            value.numerator.bit_length(),
                            value.denominator.bit_length(),
                            1,
                        ),
                    )
                values[ix, iy] = _finite_stat(value)
            item.values = values
        return plan
    except Exception:
        plan.close()
        raise
    finally:
        for lease in reversed(scratch):
            lease.close()
