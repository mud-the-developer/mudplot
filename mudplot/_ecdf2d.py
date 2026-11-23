"""Canonical paired lower-orthant ECDF; no KDE or joint-survival substitution.

Each raw field keeps ALL its interior source knots plus requested queries and
finite bounds. Exact boundary/query masses remain in the derived effect plan;
the native cell at[left,right) evaluates the closed lower orthant at LEFT.
"""

from __future__ import annotations

import math
import sys
from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field
from fractions import Fraction
from itertools import chain
from typing import Any

from ._density import MAX_JOINT_EDGES
from ._density_input import FieldInput, prepare_input


@dataclass(slots=True)
class JointEmpiricalField:
    index: int
    hue: Any
    roles: dict
    rows: tuple[int, ...]
    x_edges: tuple
    y_edges: tuple
    prefix_units: Any
    total_units: int
    values: Any
    leases: list = field(default_factory=list, repr=False)


@dataclass(slots=True)
class JointEmpiricalPlan:
    bounds: tuple
    stat: str
    complementary: bool
    mass_denominator: int
    fields: list[JointEmpiricalField]
    cohort: FieldInput
    owns_input: bool
    leases: list = field(default_factory=list, repr=False)

    def close(self):
        for item in self.fields:
            item.prefix_units = None
            item.values = None
            for lease in reversed(item.leases):
                lease.close()
            item.leases.clear()
        self.fields.clear()
        for lease in reversed(self.leases):
            lease.close()
        self.leases.clear()
        if self.owns_input:
            self.cohort.close()


def joint_edges(values, bound, queries, budget=None):
    """No source-knot downsample; reject the prospective513th edge."""
    import numpy as np

    scratch = []
    found = None
    native = widths = None
    try:
        if budget is not None:
            reference = sys.getsizeof((None,)) - sys.getsizeof(())
            scratch.append(
                budget.lease(
                    sys.getsizeof(set())
                    + 2 * sys.getsizeof([])
                    + sys.getsizeof(())
                    + (24 * MAX_JOINT_EDGES + 32) * reference
                    + 4 * sys.getsizeof(Fraction(0))
                )
            )
            scratch.append(
                budget.integer_lease(
                    1 - sys.float_info.min_exp + sys.float_info.mant_dig + 4, count=8
                )
            )
            scratch.append(
                budget.array_lease((MAX_JOINT_EDGES,), copies=2, active=True)
            )
            scratch.append(
                budget.array_lease(
                    (MAX_JOINT_EDGES,), dtype="bool", copies=3, active=True
                )
            )
        found = set()
        low, high = bound
        for value in chain((low, high), queries or ()):
            if value < low or value > high:
                raise ValueError(
                    "joint ECDF queries must lie within their declared bounds"
                )
            if value not in found and len(found) >= MAX_JOINT_EDGES:
                raise ValueError("joint ECDF exceeds512 edges in a logical coordinate")
            found.add(value)
        for value in values:
            if low < value < high and value not in found:
                if len(found) >= MAX_JOINT_EDGES:
                    raise ValueError(
                        "joint ECDF source knots exceed512 edges; "
                        "use an explicit smaller viewport"
                    )
                found.add(value)
        if budget is not None:
            bits = max(
                max(
                    Fraction(value).numerator.bit_length(),
                    Fraction(value).denominator.bit_length(),
                )
                for value in found
            )
            budget.charge(
                "integer_coordinate_order",
                len(found) * max(1, len(found).bit_length()),
                bits=bits,
            )
            scratch.append(budget.integer_lease(2 * bits + 64, count=8))
        result = tuple(sorted(found))
        native = np.asarray(result, dtype=float)
        with np.errstate(over="ignore", invalid="ignore"):
            widths = np.diff(native)
        if not np.all(np.isfinite(native)) or not np.all(
            np.isfinite(widths) & (widths > 0)
        ):
            raise ValueError(
                "distinct joint ECDF knots/bounds collapse "
                "in native coordinate precision"
            )
        return result
    finally:
        if found is not None:
            found.clear()
        native = widths = None
        for lease in reversed(scratch):
            lease.close()


def joint_prefix(x, y, masses, x_edges, y_edges, budget=None):
    """x sweep + compressed-y Fenwick, preserving canonical ties before float."""
    import numpy as np

    count = len(x)
    width = (
        max((mass.bit_length() for mass in masses), default=1) + count.bit_length() + 1
    )
    scratch = []
    compressed, order, tree = (), [], []
    try:
        if budget is not None:
            reference = sys.getsizeof((None,)) - sys.getsizeof(())
            # Real set/list/tuple/index and keyed-Timsort pointers, not fictional
            # int64 arrays. Set resize overlap dominates the sorting workspace.
            scratch.append(
                budget.lease(
                    sys.getsizeof(set())
                    + 3 * sys.getsizeof([])
                    + sys.getsizeof(())
                    + (27 * count + 32) * reference
                    + count * sys.getsizeof(count)
                )
            )
            scratch.append(budget.integer_lease(width, count=count + 8))
            budget.charge("source_pair_order", count * max(1, count.bit_length()))
        compressed = tuple(sorted(set(y)))
        order = sorted(range(count), key=x.__getitem__)
        tree = [0] * (len(compressed) + 1)
        output = np.empty((len(x_edges), len(y_edges)), dtype=object)
        position = 0
        for ix, qx in enumerate(x_edges):
            while position < len(order) and x[order[position]] <= qx:
                row = order[position]
                at = bisect_left(compressed, y[row]) + 1
                mass = masses[row]
                while at < len(tree):
                    if budget is not None:
                        budget.charge("integer_fenwick_add", 1, bits=width)
                    tree[at] += mass
                    at += at & -at
                position += 1
            for iy, qy in enumerate(y_edges):
                at = bisect_right(compressed, qy)
                prefix = 0
                while at:
                    if budget is not None:
                        budget.charge("integer_fenwick_query", 1, bits=width)
                    prefix += tree[at]
                    at -= at & -at
                output[ix, iy] = prefix
        return output
    finally:
        compressed = ()
        order.clear()
        tree.clear()
        for lease in reversed(scratch):
            lease.close()


def _query_value(mass, total, denominator, stat, complementary):
    remaining = total - mass if complementary else mass
    if stat == "count":
        value = Fraction(remaining, denominator)
    else:
        value = Fraction(remaining * (100 if stat == "percent" else 1), total)
    try:
        result = float(value)
    except OverflowError as error:
        raise ValueError("joint ECDF count mass exceeds native precision") from error
    if not math.isfinite(result):
        raise ValueError("joint ECDF statistic exceeds native precision")
    return result


def prepare_joint_ecdf(columns, layer, panel, budget=None, *, input_plan=None):
    """Physical field rows set denominators; bounds/queries NEVER trim mass."""
    import numpy as np

    cohort = (
        prepare_input(columns, layer, panel, budget)
        if input_plan is None
        else input_plan
    )
    budget = cohort.budget
    cfg = layer.ecdf2d
    plan = None
    plan_storage = None
    reference = sys.getsizeof((None,)) - sys.getsizeof(())
    try:
        if budget is not None:
            plan_storage = budget.lease(
                sys.getsizeof(object.__new__(JointEmpiricalPlan))
                + 2 * sys.getsizeof([])
                + 3 * sys.getsizeof(())
                + (4 * len(cohort.groups) + 40) * reference
            )
        bounds = tuple(tuple(bound) for bound in cfg.bounds)
        plan = JointEmpiricalPlan(
            bounds,
            cfg.stat,
            cfg.complementary,
            cohort.denominator,
            [],
            cohort,
            input_plan is None,
        )
        if plan_storage is not None:
            plan.leases.append(plan_storage)
            plan_storage = None
        for group in cohort.groups:
            rows = group["rows"]
            if not rows:
                continue
            temporaries = []
            edge_storage = item_storage = None
            x, y, masses = [], [], []
            xe, ye = (), ()
            try:
                total = cohort.group_totals[group["index"]]
                if budget is not None:
                    temporaries.append(
                        budget.lease(
                            3 * sys.getsizeof([])
                            + (6 * len(rows) + 32) * reference
                            + 8 * sys.getsizeof(Fraction(0))
                        )
                    )
                    temporaries.append(
                        budget.integer_lease(
                            total.bit_length() + cohort.denominator.bit_length() + 8,
                            count=8,
                        )
                    )
                    edge_storage = budget.lease(
                        2 * (sys.getsizeof(()) + MAX_JOINT_EDGES * reference)
                    )
                x = [columns[layer.x][row] for row in rows]
                y = [columns[layer.y][row] for row in rows]
                masses = [cohort.mass_by_row[row] for row in rows]
                if cfg.stat == "count":
                    _query_value(total, total, cohort.denominator, "count", False)
                xe = joint_edges(x, bounds[0], cfg.query_x, budget)
                ye = joint_edges(y, bounds[1], cfg.query_y, budget)
                nx, ny = len(xe) - 1, len(ye) - 1
                if budget is not None:
                    item_storage = budget.lease(
                        sys.getsizeof(object.__new__(JointEmpiricalField))
                        + sys.getsizeof(())
                        + len(rows) * reference
                        + sys.getsizeof(xe)
                        + sys.getsizeof(ye)
                        + sys.getsizeof([None] * 8)
                    )
                item = JointEmpiricalField(
                    group["index"],
                    group["hue"],
                    group["roles"],
                    tuple(rows),
                    xe,
                    ye,
                    None,
                    total,
                    None,
                )
                plan.fields.append(item)
                if item_storage is not None:
                    item.leases.append(item_storage)
                    item_storage = None
                    assert edge_storage is not None
                    edge_storage.close()
                    edge_storage = None
                if budget is not None:
                    count = len(xe) * len(ye)
                    item.leases.append(
                        budget.integer_lease(
                            total.bit_length() + 1, count=count, references=False
                        )
                    )
                    item.leases.append(
                        budget.array_lease((len(xe), len(ye)), dtype="object")
                    )
                    plan.leases.append(budget.array_lease((nx, ny)))
                    item.leases.append(budget.array_lease((nx, ny)))
                    item.leases.append(
                        budget.array_lease((ny + 1, nx + 1, 2), copies=2)
                    )
                    item.leases.append(budget.array_lease((nx, ny, 4), copies=2))
                    item.leases.append(budget.array_lease((nx, ny), dtype="bool"))
                    item.leases.append(budget.native_path_lease(5 * nx * ny, nx * ny))
                    budget.charge("statistic_output_cells", nx * ny)
                prefix = joint_prefix(x, y, masses, xe, ye, budget)
                values = np.empty((nx, ny), dtype=float)
                for ix in range(nx):
                    for iy in range(ny):
                        if budget is not None:
                            budget.charge(
                                "integer_cdf_statistic",
                                4,
                                bits=total.bit_length()
                                + cohort.denominator.bit_length(),
                            )
                        values[ix, iy] = _query_value(
                            prefix[ix, iy],
                            total,
                            cohort.denominator,
                            cfg.stat,
                            cfg.complementary,
                        )
                item.prefix_units = prefix
                item.values = values
            finally:
                x.clear()
                y.clear()
                masses.clear()
                xe, ye = (), ()
                for temporary in (item_storage, edge_storage, *reversed(temporaries)):
                    if temporary is not None:
                        temporary.close()
        return plan
    except Exception:
        if plan is not None:
            plan.close()
        elif input_plan is None:
            cohort.close()
        raise
    finally:
        if plan_storage is not None:
            plan_storage.close()
