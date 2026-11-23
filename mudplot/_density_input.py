"""One resolved physical cohort for histogram, density and joint empirical fields.

A source-ID domain pool is not a fitting/normalization pool. Histogram tallies
and their optional KDE consume this SAME pre-tally plan, never a histogram's
in-range subset. No source observations or IDs are rewritten.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from fractions import Fraction

from ._density import (
    MAX_FIELD_ROWS,
    MAX_FIELDS,
    bounded_density_request,
    density_rows,
    field_groups,
    new_density_request,
    weight_column,
)
from ._ecdf import canonical_units
from ._field_budget import FieldBudget, owned_size


@dataclass(slots=True)
class FieldInput:
    rows: tuple[int, ...]
    groups: list[dict]
    denominator: int
    masses: tuple[int, ...]
    mass_by_row: dict[int, int]
    total: int
    pool_totals: dict
    group_totals: tuple[int, ...]
    new: bool
    budget: FieldBudget | None
    leases: list = field(default_factory=list, repr=False)

    def close(self):
        for lease in reversed(self.leases):
            lease.close()
        self.leases.clear()
        self.rows = ()
        self.groups.clear()
        self.masses = ()
        self.mass_by_row.clear()
        self.pool_totals.clear()
        self.group_totals = ()
        self.denominator = 1
        self.total = 0


def _construction_bytes(columns, layer):
    """Prospective CPython selection/partition/owned-size scratch, not source leaves."""
    source_count = len(columns.get(layer.x, ()))
    rows = min(source_count, MAX_FIELD_ROWS)
    orders = len(layer.hue_order) if layer.hue_order is not None else 0
    semantics = layer.semantics
    if semantics is not None:
        orders += sum(
            len(order)
            for role in ("hue", "size", "style")
            if (order := getattr(semantics, f"{role}_order", None)) is not None
        )
    groups = max(rows, len(layer.hue_order or ()), 1)
    reference = sys.getsizeof((None,)) - sys.getsizeof(())
    integer = sys.getsizeof(max(source_count, groups, 1))
    identity = sys.getsizeof(id(columns))
    dictionary = sys.getsizeof({})
    slot = sys.getsizeof({None: None}) - dictionary
    pair = sys.getsizeof((None, None))
    triple = sys.getsizeof((None, None, None))
    empty_list = sys.getsizeof([])
    # Lists grow to <2*n+8 pointers. A grow-only set's old+new resize tables
    # need <10 slots/item, each hash+pointer:20 pointers/item including overlap.
    selected = 2 * empty_list + (5 * rows + 16) * reference + rows * integer
    group_plans = (
        4 * empty_list
        + (6 * groups + 2 * rows + 32) * reference
        + groups * (3 * dictionary + 10 * slot + 5 * pair + triple + 2 * integer)
    )
    selection_keys = (
        3 * sys.getsizeof(set()) + orders * (20 * reference + pair) + 4 * pair
    )
    # Recursive owned_size adds container IDs to the borrowed-value/row ID set.
    ids = rows + 12 * groups + 32
    sizing = 2 * sys.getsizeof(set()) + ids * (20 * reference + identity)
    return (
        selected
        + group_plans
        + selection_keys
        + sizing
        + sys.getsizeof(object.__new__(FieldInput))
        + 8 * dictionary
        + 8 * empty_list
        + 16 * pair
    )


def prepare_input(columns, layer, panel, budget=None):
    """Resolve NEW once; admit construction BEFORE selecting/partitioning rows."""
    typed = new_density_request(layer, panel)
    new = bounded_density_request(layer, panel)
    accountant = budget if new else None
    leases = []
    result = None
    construction = None
    scratch = None
    weights_storage = None
    weight_probe = None
    try:
        if accountant is not None:
            construction = accountant.lease(_construction_bytes(columns, layer))
        rows = tuple(density_rows(columns, layer, panel))
        if new and len(rows) > MAX_FIELD_ROWS:
            raise ValueError(
                "new paired fields support at most10000 selected physical rows"
            )
        groups = field_groups(columns, layer, rows, typed=typed)
        if new and sum(bool(group["rows"]) for group in groups) > MAX_FIELDS:
            raise ValueError("new paired fields support at most256 drawn raw tuples")
        result = FieldInput(rows, groups, 1, (), {}, 0, {}, (), new, accountant, leases)
        if accountant is not None:
            leases.append(accountant.account(rows))
            source_values = {
                id(value)
                for group in groups
                for value in (group["hue"], *group["roles"].values())
            }
            source_values.update(map(id, rows))
            leases.append(accountant.lease(owned_size(groups, seen=source_values)))
            leases.append(
                accountant.lease(
                    sys.getsizeof(result)
                    + sys.getsizeof([None] * 8)
                    + 2 * sys.getsizeof(())
                    + sys.getsizeof([])
                )
            )
            del source_values
            assert construction is not None
            construction.close()
            construction = None
        weights_name = weight_column(layer)
        if weights_name is None:
            if accountant is not None:
                scratch = accountant.integer_lease(1, count=len(rows))
            masses = (1,) * len(rows)
            denominator = 1
        elif rows:
            if accountant is not None:
                reference = sys.getsizeof((None,)) - sys.getsizeof(())
                weights_storage = accountant.lease(
                    2 * sys.getsizeof([])
                    + (5 * len(rows) + 32) * reference
                    + (len(rows) + 3) * sys.getsizeof(Fraction(0))
                    + 3 * sys.getsizeof(())
                )
                weight_probe = accountant.integer_lease(
                    1 - sys.float_info.min_exp + sys.float_info.mant_dig + 4,
                    count=8,
                )
            weights = [columns[weights_name][row] for row in rows]
            if accountant is not None:
                bits = max(
                    max(
                        abs(Fraction(weight).numerator).bit_length(),
                        Fraction(weight).denominator.bit_length(),
                    )
                    for weight in weights
                )
                accountant.charge(
                    "integer_mass_canonicalization",
                    4 * len(rows),
                    bits=2 * bits + len(rows).bit_length(),
                )
                scratch = accountant.integer_lease(
                    2 * bits + len(rows).bit_length(), count=3 * len(rows) + 8
                )
            denominator, masses = canonical_units(weights)
            del weights
        else:
            denominator, masses = 1, ()
        if accountant is not None:
            width = max((mass.bit_length() for mass in masses), default=1)
            leases.append(accountant.integer_lease(width, count=len(rows)))
            leases.append(accountant.hashmap_lease(len(rows)))
            leases.append(accountant.hashmap_lease(len(groups)))
            leases.append(
                accountant.integer_lease(
                    width + len(rows).bit_length() + 1, count=2 * len(groups) + 1
                )
            )
            leases.append(
                accountant.integer_lease(denominator.bit_length(), references=False)
            )
        result.denominator = denominator
        result.masses = masses
        result.mass_by_row = dict(zip(rows, masses, strict=True))
        total = 0
        for mass in masses:
            if accountant is not None:
                accountant.charge(
                    "integer_selected_mass",
                    1,
                    bits=max(total.bit_length(), mass.bit_length()) + 1,
                )
            total += mass
        result.total = total
        group_totals = []
        for group in groups:
            subtotal = 0
            for row in group["rows"]:
                mass = result.mass_by_row[row]
                if accountant is not None:
                    accountant.charge(
                        "integer_pool_mass",
                        2,
                        bits=max(total.bit_length(), mass.bit_length()) + 1,
                    )
                subtotal += mass
            group_totals.append(subtotal)
            key = group["pool"]
            result.pool_totals[key] = result.pool_totals.get(key, 0) + subtotal
        result.group_totals = tuple(group_totals)
        return result
    except Exception:
        if result is not None:
            result.close()
        else:
            for lease in reversed(leases):
                lease.close()
        raise
    finally:
        for temporary in (scratch, weight_probe, weights_storage, construction):
            if temporary is not None:
                temporary.close()
