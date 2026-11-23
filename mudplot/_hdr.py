"""Explicit full-model HDR: bounded whitening rectangles, not grid conditioning.

One model/root/Morton chart, strict ordered cutoffs, one figure ledger, current
heap<=65536, and48 updates plus the initial trial. Source/numerical/support error
is carried BEFORE membership. Native geometry consumes only guaranteed-inside
cells, with separate forward/chord/clip error; it never relabels visible mass p.
"""

from __future__ import annotations

import heapq
import itertools
import math
import sys
from dataclasses import dataclass, field
from fractions import Fraction

from ._field_budget import FieldResourceError, owned_size
from ._kernel_math import KernelPrecisionError

MAX_HDR_ACTIVE_CELLS = 65536
MAX_HDR_LAMBDA_UPDATES = 48


@dataclass(slots=True)
class HDRLevel:
    target: float | None
    cutoff: float
    mass_lower: float
    mass_upper: float
    inside_lower: float
    crossing_upper: float
    updates: int
    cells: int


@dataclass(slots=True)
class HDRCell:
    box: tuple[float, float, float, float]
    path: int
    depth: int
    mass: tuple[float, float]
    density: tuple
    lease: object


@dataclass(slots=True)
class HDRRegion:
    root: tuple
    levels: list[HDRLevel]
    cells: list[tuple]
    support_error: float
    source_error: float
    probability_error: float
    density_space: str
    model: object
    leases: list = field(default_factory=list)
    geometry_error: float = 0.0
    cell_masses: list[tuple[float, float]] = field(default_factory=list)

    def close(self):
        self.cells.clear()
        self.cell_masses.clear()
        for lease in reversed(self.leases):
            lease.close()
        self.leases.clear()


def children(box, arithmetic):
    a, b, c, d = box
    x = arithmetic.midpoint((a, b))
    y = arithmetic.midpoint((c, d))
    if not a < x < b or not c < y < d:
        raise KernelPrecisionError("HDR cell subdivision collapses")
    return ((a, x, c, y), (x, b, c, y), (a, x, y, d), (x, b, y, d))


def _point(value):
    return value, value


def _support(model, tolerance):
    iv = model.arithmetic
    budget = model.budget
    if model.kernel == "gaussian":
        tail_request = Fraction(tolerance) / 128
        logarithm = iv.log_fraction(tail_request)
        radius = iv.sqrt_fraction(-2 * Fraction(logarithm[0]))[1]
    else:
        radius = iv.compact_radius[1]
    l00, l10, l11 = (tuple(map(Fraction, bound)) for bound in model.lower_bounds)
    a00 = iv.rational_div(l00, (Fraction(model.lower[0]),) * 2)
    a10 = iv.rational_div(
        iv.rational_sub(
            l10,
            iv.rational_mul(
                (Fraction(model.lower[1]) / Fraction(model.lower[0]),) * 2, l00
            ),
        ),
        (Fraction(model.lower[2]),) * 2,
    )
    a11 = iv.rational_div(l11, (Fraction(model.lower[2]),) * 2)
    norms = (
        max(abs(value) for value in a00),
        max(abs(value) for value in a10) + max(abs(value) for value in a11),
    )
    root = []
    for axis, norm in enumerate(norms):
        low = min(Fraction(centre[axis][0]) for centre in model.centre_bounds)
        high = max(Fraction(centre[axis][1]) for centre in model.centre_bounds)
        extension = Fraction(radius) * norm
        root.extend((iv.fraction(low - extension)[0], iv.fraction(high + extension)[1]))
    # Certify the ACTUAL stored rectangle, not a rounded nominal R*R exponent.
    radii = []
    for centre in model.centre_bounds:
        for axis, norm in enumerate(norms):
            low, high = root[2 * axis : 2 * axis + 2]
            radii.extend(
                (
                    (Fraction(centre[axis][0]) - Fraction(low)) / norm,
                    (Fraction(high) - Fraction(centre[axis][1])) / norm,
                )
            )
    actual_radius = min(radii)
    if model.kernel == "gaussian":
        exponent = actual_radius * actual_radius / 2
        bound = iv.fraction(exponent)
        tail = iv.exp_negative(bound)[1]
    else:
        if actual_radius < Fraction(iv.compact_radius[1]):
            raise KernelPrecisionError("compact support rectangle is unresolved")
        tail = 0.0
    if budget is not None:
        budget.charge("hdr_support_components", len(model.centres))
    return tuple(root), tail


class _Bounds:
    """One bounded endpoint/coarse cache shared by every level of this model."""

    def __init__(self, model, space):
        self.model = model
        self.iv = model.arithmetic
        self.budget = model.budget
        self.space = space
        self.endpoints = {}
        self.coarse = {}
        self.leases = []

    def close(self):
        self.endpoints.clear()
        self.coarse.clear()
        for lease in reversed(self.leases):
            lease.close()
        self.leases.clear()

    def endpoint(self, axis, edge, component):
        key = axis, edge, component
        if key in self.endpoints:
            return self.endpoints[key]
        if self.budget is not None:
            self.leases.append(
                self.budget.hashmap_lease(
                    1,
                    key_bytes=sys.getsizeof(key)
                    + sys.getsizeof(edge)
                    + 2 * sys.getsizeof(0),
                    value_bytes=sys.getsizeof((None, None)) + 2 * sys.getsizeof(0.0),
                )
            )
            self.leases.append(self.budget.lease(0, pair_elements=3))
        mean = self.model.centres[component][axis]
        argument = self.iv.fraction(Fraction(edge) - Fraction(mean))
        value = self.iv.finish_scaled(*self.iv.kernel_cdf(self.model.kernel, argument))
        self.endpoints[key] = value
        return value

    def mass(self, box):
        """Original-law rectangle mass through this model's shared endpoint cache."""
        iv = self.iv
        total = ((0.0, 0.0), 0)
        for index, mass in enumerate(self.model.mass_parts):
            if self.budget is not None:
                self.budget.charge("component_rectangle_visits")
            probabilities = []
            for axis in (0, 1):
                left = self.endpoint(axis, box[2 * axis], index)
                right = self.endpoint(axis, box[2 * axis + 1], index)
                probability = iv.nonnegative(iv.sub(right, left))
                probabilities.append(iv.normalize(probability, 0))
            part = iv.combine_scaled([mass, *probabilities])
            total = iv.sum_scaled((total, part))
        return iv.finish_scaled(*total)

    def bounds(self, box, path, depth):
        key = path, depth
        if key in self.coarse:
            return self.coarse[key]
        density = self.model.pdf_box_scaled(
            ((box[0], box[1]), (box[2], box[3])),
            density_space=self.space,
        )
        mass = self.mass(box)
        result = mass, density
        if depth <= 6:
            if self.budget is not None:
                self.leases.append(
                    self.budget.hashmap_lease(
                        1, key_bytes=owned_size(key), value_bytes=owned_size(result)
                    )
                )
            self.coarse[key] = result
        return result


def _membership(iv, density, cutoff):
    mantissa, exponent = density
    cm, ce = math.frexp(cutoff)
    target = max(exponent, ce)
    low, high = iv.to_shared_exponent(mantissa, exponent, target)
    cut_low = iv.rescale_endpoint(cm, ce - target, False)
    cut_high = iv.rescale_endpoint(cm, ce - target, True)
    return low >= cut_high, high >= cut_low


def _cell(bounds, box, path, depth):
    mass, density = bounds.bounds(box, path, depth)
    lease = None
    if bounds.budget is not None:
        payload = owned_size((box, path, depth, mass, density))
        payload += sys.getsizeof(object.__new__(HDRCell))
        payload += sys.getsizeof((None,) * 3) + sys.getsizeof(0.0) + sys.getsizeof(0)
        lease = bounds.budget.lease(payload, pair_elements=10)
    return HDRCell(box, path, depth, mass, density, lease)


def _close_cell(cell):
    if cell.lease is not None:
        cell.lease.close()
        cell.lease = None


def _seed(model, root, targets, grid_size, space):
    """Finite-grid seed ONLY; no grid probability is an accepted HDR result."""
    import numpy as np

    iv, budget = model.arithmetic, model.budget
    lease = None
    if budget is not None:
        lease = budget.array_lease((grid_size * grid_size,), copies=4)
    try:
        qx = np.linspace(root[0], root[1], grid_size)
        qy = np.linspace(root[2], root[3], grid_size)
        density = []
        probability = []
        for x in qx:
            for y in qy:
                q = ((float(x), float(x)), (float(y), float(y)))
                value = model.pdf_box_scaled(q, density_space=space)
                bounds = iv.finish_scaled(*value)
                height = iv.midpoint(bounds)
                density.append(height if height > 0 else bounds[1])
                # Probability is the ORIGINAL unshifted mixture. This coarse
                # grid only initializes lambda; full rectangle bounds decide.
                p = ((0.0, 0.0), 0)
                for centre, mass in zip(model.centres, model.mass_parts, strict=True):
                    if budget is not None:
                        budget.charge("component_seed_probability_visits")
                    part = iv.combine_scaled(
                        [
                            mass,
                            iv.kernel_pdf(
                                model.kernel,
                                iv.fraction(Fraction(float(x)) - Fraction(centre[0])),
                            ),
                            iv.kernel_pdf(
                                model.kernel,
                                iv.fraction(Fraction(float(y)) - Fraction(centre[1])),
                            ),
                        ]
                    )
                    p = iv.sum_scaled((p, part))
                probability.append(iv.midpoint(iv.finish_scaled(*p)))
        order = np.argsort(-np.asarray(density), kind="stable")
        prefix = np.cumsum(np.asarray(probability)[order])
        if not prefix[-1] > 0:
            raise KernelPrecisionError("HDR initial finite-grid seed is unresolved")
        prefix /= prefix[-1]
        return [
            float(density[order[min(int(np.searchsorted(prefix, p)), len(order) - 1)]])
            for p in targets
        ]
    finally:
        if lease is not None:
            lease.close()


def solve_full_hdr(model, config):
    """Calibrate every requested full-model level; unresolved means NO output."""
    iv, budget = model.arithmetic, model.budget
    tolerance = config.hdr.tolerance
    if model.source_tv >= tolerance / 16:
        raise KernelPrecisionError("source-law uncertainty exceeds full HDR tolerance")
    root, tail = _support(model, tolerance)
    space = config.density_space or "data"
    cache = _Bounds(model, space)
    region = HDRRegion(root, [], [], tail, model.source_tv, 0.0, space, model)
    targets = list(config.levels)
    from ._density import level_kind

    mass_levels = level_kind(config) == "mass"
    seeds = (
        _seed(model, root, targets, config.gridsize, space) if mass_levels else targets
    )
    if not mass_levels:
        seeds = list(reversed(seeds))
    trie = {"band": None, "children": {}}
    trie_leases = []
    active = {}
    serial = itertools.count()

    def contributions(cell, cutoff):
        inside, possible = _membership(iv, cell.density, cutoff)
        return cell.mass[0] if inside else 0.0, cell.mass[1] if possible else 0.0

    def enqueue(box, path, depth, cutoff, queue):
        value = _cell(cache, box, path, depth)
        key = path, depth
        active[key] = value
        lo, hi = contributions(value, cutoff)
        heapq.heappush(queue, (-(hi - lo), next(serial), key))
        return lo, hi

    try:
        previous = math.inf
        for band, (target, seed) in enumerate(zip(targets, seeds, strict=True)):
            threshold = min(seed, math.nextafter(previous, 0.0))
            if not math.isfinite(threshold) or threshold <= 0:
                raise KernelPrecisionError("HDR cutoff is not a positive native scalar")
            low_lambda, high_lambda = 0.0, previous
            heap = []
            lower = upper = 0.0

            lo, hi = enqueue(root, 0, 0, threshold, heap)
            lower = iv.down(lower + lo)
            upper = iv.up(upper + hi)
            accepted = False
            classification = tolerance * 0.6
            updates = 0
            for updates in range(MAX_HDR_LAMBDA_UPDATES + 1):
                while iv.sub(_point(upper), _point(lower))[1] > classification:
                    if len(active) + 3 > MAX_HDR_ACTIVE_CELLS:
                        raise FieldResourceError(
                            "full HDR current-level adaptive cells exceed65536"
                        )
                    _priority, _serial, key = heapq.heappop(heap)
                    old = active.pop(key)
                    lo, hi = contributions(old, threshold)
                    lower = iv.down(lower - lo)
                    upper = iv.up(upper - hi)
                    box, path, depth = old.box, old.path, old.depth
                    _close_cell(old)
                    for digit, child in enumerate(children(box, iv)):
                        if budget is not None:
                            budget.charge("integer_morton_child", 1, bits=2 * depth + 2)
                        lo, hi = enqueue(
                            child, path * 4 + digit, depth + 1, threshold, heap
                        )
                        lower = iv.down(lower + lo)
                        upper = iv.up(upper + hi)
                full_low = max(0.0, iv.down(lower - model.source_tv))
                full_high = min(1.0, iv.up(upper + tail + model.source_tv))
                if not mass_levels or full_low <= target <= full_high:
                    accepted = True
                    break
                if updates == MAX_HDR_LAMBDA_UPDATES:
                    break
                if target > full_high:
                    high_lambda = min(high_lambda, threshold)
                else:
                    low_lambda = max(low_lambda, threshold)
                if math.isinf(high_lambda):
                    # A finite source/native peak bracket, never a conditional
                    # mass substitute. The next full trial still certifies it.
                    high_lambda = sys.float_info.max
                if low_lambda > 0:
                    log_low = iv.log_fraction(Fraction(low_lambda))
                    log_high = iv.log_fraction(Fraction(high_lambda))
                    candidate = iv.midpoint(
                        iv.finish_scaled(
                            *iv.exp_signed_scaled(
                                iv.fraction(
                                    (Fraction(log_low[1]) + Fraction(log_high[0])) / 2
                                )
                            )
                        )
                    )
                else:
                    candidate = high_lambda / 2
                if not low_lambda < candidate < high_lambda:
                    raise KernelPrecisionError(
                        "strict HDR lambda order/precision is unresolved"
                    )
                threshold = candidate
                lower = upper = 0.0
                heap.clear()
                for key, value in active.items():
                    lo, hi = contributions(value, threshold)
                    lower = iv.down(lower + lo)
                    upper = iv.up(upper + hi)
                    heapq.heappush(heap, (-(hi - lo), next(serial), key))
            if not accepted:
                raise KernelPrecisionError(
                    "full HDR requested level did not resolve in48 updates"
                )
            if not threshold < previous:
                raise KernelPrecisionError(
                    "requested HDR levels cannot be strictly ordered"
                )
            inside = crossing = numerical = 0.0
            for cell in active.values():
                definite, possible = _membership(iv, cell.density, threshold)
                if definite:
                    inside = iv.down(inside + cell.mass[0])
                    numerical = iv.up(numerical + cell.mass[1] - cell.mass[0])
                    node = trie
                    for level in range(cell.depth):
                        if node["band"] is not None and node["band"] <= band:
                            break
                        digit = (cell.path >> (2 * (cell.depth - level - 1))) & 3
                        if digit not in node["children"]:
                            if budget is not None:
                                trie_leases.append(
                                    budget.hashmap_lease(
                                        1,
                                        key_bytes=sys.getsizeof(0),
                                        value_bytes=owned_size(
                                            {"band": None, "children": {}}
                                        ),
                                    )
                                )
                            node["children"][digit] = {"band": None, "children": {}}
                        node = node["children"][digit]
                    else:
                        if node["band"] is None or band < node["band"]:
                            node["band"] = band
                elif possible:
                    crossing = iv.up(crossing + cell.mass[1])
            error = iv.up(crossing + numerical + tail + 2 * model.source_tv)
            if error >= tolerance:
                raise KernelPrecisionError(
                    "full HDR region error exceeds requested tolerance"
                )
            region.levels.append(
                HDRLevel(
                    config.levels[band] if mass_levels else None,
                    threshold,
                    full_low,
                    full_high,
                    max(0.0, inside - model.source_tv),
                    crossing,
                    updates,
                    len(active),
                )
            )
            region.probability_error = max(region.probability_error, error)
            previous = threshold
            for cell in active.values():
                _close_cell(cell)
            active.clear()
            heap.clear()

        def emit(node, box, path=0, depth=0, inherited=None):
            band = node["band"] if node["band"] is not None else inherited
            if not node["children"]:
                if band is not None:
                    payload = box, path, depth, band
                    mass = cache.mass(box)
                    if budget is not None:
                        region.leases.append(budget.account(payload))
                        region.leases.append(
                            budget.lease(owned_size(mass), pair_elements=2)
                        )
                    region.cells.append(payload)
                    region.cell_masses.append(mass)
                return
            for digit, child in enumerate(children(box, iv)):
                if digit in node["children"]:
                    emit(
                        node["children"][digit],
                        child,
                        path * 4 + digit,
                        depth + 1,
                        band,
                    )
                elif band is not None:
                    payload = child, path * 4 + digit, depth + 1, band
                    mass = cache.mass(child)
                    if budget is not None:
                        region.leases.append(budget.account(payload))
                        region.leases.append(
                            budget.lease(owned_size(mass), pair_elements=2)
                        )
                    region.cells.append(payload)
                    region.cell_masses.append(mass)

        emit(trie, root)
        # A previous inner U is NOT falsely equated with its enlarged U-star.
        # Guaranteed-inside nesting gives old inside lower<=P(U-star)<=P(R).
        return region
    except Exception:
        region.close()
        raise
    finally:
        for cell in active.values():
            _close_cell(cell)
        cache.close()
        trie.clear()
        for lease in reversed(trie_leases):
            lease.close()
