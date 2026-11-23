"""D03-D06 explicit-NEW figure resources, separate from legacy/D01/C07 work.

Composite units intentionally include overlapping primitive overhead. They are
neither FLOPs nor a latency/process-RSS promise. Original source/library/legacy
storage and backend RGBA buffers are not this working-state allowance.
"""

from __future__ import annotations

import math
import sys
from contextlib import contextmanager
from dataclasses import fields, is_dataclass
from fractions import Fraction

MAX_FIELD_WORK = 2_000_000_000
MAX_FIELD_BYTES = 268_435_456
MAX_FIELD_PAIR_ELEMENTS = 1_000_000
MAX_FIELD_VERTICES = 2_000_000


class FieldResourceError(ValueError):
    """The complete requested effect cannot fit its declared resource envelope."""


def owned_size(value, *, seen=None):
    """Size actual owned plans/integers/arrays, not references to source tables.

    Callers pass only NEW owned roots. Array bases are counted once; original
    observations should not be included as recursively owned plan storage.
    """
    if seen is None:
        seen = set()
    identity = id(value)
    if identity in seen:
        return 0
    seen.add(identity)
    size = sys.getsizeof(value)
    if hasattr(value, "dtype") and hasattr(value, "nbytes"):
        base = getattr(value, "base", None)
        return size + (owned_size(base, seen=seen) if base is not None else 0)
    if isinstance(value, Fraction):
        return (
            size
            + owned_size(value.numerator, seen=seen)
            + owned_size(value.denominator, seen=seen)
        )
    if isinstance(value, dict):
        return size + sum(
            owned_size(key, seen=seen) + owned_size(item, seen=seen)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple, set, frozenset)):
        return size + sum(owned_size(item, seen=seen) for item in value)
    if is_dataclass(value) and not isinstance(value, type):
        return size + sum(
            owned_size(getattr(value, f.name), seen=seen) for f in fields(value)
        )
    return size


class _Lease:
    __slots__ = ("budget", "bytes", "closed", "elements")

    def __init__(self, budget, size, elements):
        self.budget = budget
        self.bytes = size
        self.elements = elements
        self.closed = False

    def close(self):
        if self.closed:
            raise RuntimeError("field resource lease already released")
        self.budget.live_bytes -= self.bytes
        self.budget.pair_elements -= self.elements
        self.closed = True

    def grow(self, size, *, pair_elements=0):
        """Admit accumulator growth BEFORE its allocation, without a new lease."""
        if self.closed:
            raise RuntimeError("field resource lease already released")
        self.bytes += self.budget._admit(size, pair_elements)
        self.elements += pair_elements

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        self.close()
        return False


class FieldBudget:
    """ONE ledger shared by every NEW field/model/level in a rendered figure."""

    def __init__(self):
        self.units = 0
        self.by_kind = {}
        self.live_bytes = 0
        self.peak_bytes = 0
        self.pair_elements = 0
        self.peak_pair_elements = 0
        self.vertices = 0
        self.rgba_bytes = 0
        self._kind_leases = []
        self._lease_size = sys.getsizeof(object.__new__(_Lease))
        self.live_bytes = sys.getsizeof(self) + owned_size(vars(self))
        self.peak_bytes = self.live_bytes

    def charge(self, kind, count=1, *, bits=None):
        if type(count) is not int or count < 0:
            raise ValueError("field work count must be a nonnegative integer")
        if bits is not None:
            if type(bits) is not int or bits < 0:
                raise ValueError("field integer width must be nonnegative")
            count *= max(1, (bits + 63) // 64)
        if self.units + count > MAX_FIELD_WORK:
            raise FieldResourceError(
                "NEW density/empirical figure exceeds2,000,000,000 composite work units"
            )
        if kind not in self.by_kind:
            reference = sys.getsizeof((None,)) - sys.getsizeof(())
            self._kind_leases.append(
                self.hashmap_lease(
                    1, value_bytes=sys.getsizeof(MAX_FIELD_WORK) + reference
                )
            )
        self.units += count
        self.by_kind[kind] = self.by_kind.get(kind, 0) + count

    def _admit(self, size, pair_elements, *, overhead=0):
        if (
            type(size) is not int
            or size < 0
            or type(pair_elements) is not int
            or pair_elements < 0
        ):
            raise ValueError("field allocation accounting must be nonnegative integers")
        size += overhead
        if self.live_bytes + size > MAX_FIELD_BYTES:
            raise FieldResourceError(
                "NEW field working/native-plan storage exceeds256MiB"
            )
        if self.pair_elements + pair_elements > MAX_FIELD_PAIR_ELEMENTS:
            raise FieldResourceError(
                "NEW simultaneously active pair buffers exceed1M elements"
            )
        self.live_bytes += size
        self.peak_bytes = max(self.peak_bytes, self.live_bytes)
        self.pair_elements += pair_elements
        self.peak_pair_elements = max(self.peak_pair_elements, self.pair_elements)
        return size

    def lease(self, size, *, pair_elements=0):
        admitted = self._admit(size, pair_elements, overhead=self._lease_size)
        return _Lease(self, admitted, pair_elements)

    def account(self, value, *, headroom=0):
        """Retain an actual NEW product object plus explicit prospective headroom."""
        return self.lease(owned_size(value) + headroom)

    def array_lease(self, shape, dtype="float64", *, active=False, copies=1):
        """Admit actual NumPy dtype/header/payload BEFORE a large array allocation."""
        import numpy as np

        if not isinstance(shape, (list, tuple)):
            shape = (shape,)
        if (
            any(type(n) is not int or n < 0 for n in shape)
            or type(copies) is not int
            or copies < 1
        ):
            raise ValueError("field array shape/copies must be nonnegative integers")
        count = math.prod(shape)
        kind = np.dtype(dtype)
        # Actual ndarray product header, with alignment headroom derived from
        # the dtype rather than a per-cell sizeof constant copied from a lab.
        header = sys.getsizeof(np.empty((0,) * len(shape), dtype=kind))
        size = copies * (header + count * kind.itemsize + max(kind.alignment, 1))
        return self.lease(size, pair_elements=count * copies if active else 0)

    def integer_lease(self, bits, *, count=1, references=True):
        """Conservative CPython integer limbs before prefix/canonical allocation."""
        if type(bits) is not int or bits < 0 or type(count) is not int or count < 0:
            raise ValueError("field integer allocation shape is invalid")
        limbs = max(
            1, (bits + sys.int_info.bits_per_digit - 1) // sys.int_info.bits_per_digit
        )
        integer = sys.getsizeof(0) + limbs * sys.int_info.sizeof_digit
        reference = sys.getsizeof((None,)) - sys.getsizeof(()) if references else 0
        return self.lease(count * (integer + reference))

    def hashmap_lease(self, entries, *, key_bytes=0, value_bytes=0):
        """Prospective native dict slots plus caller-owned key/value payloads."""
        if any(
            type(value) is not int or value < 0
            for value in (entries, key_bytes, value_bytes)
        ):
            raise ValueError("field mapping allocation shape is invalid")
        empty = sys.getsizeof({})
        # A one-entry dict measures this interpreter's smallest resize quantum.
        # Paying that quantum PER entry conservatively covers later resizes.
        slot = sys.getsizeof({None: None}) - empty
        return self.lease(empty + entries * (slot + key_bytes + value_bytes))

    def scaled_lease(self, count):
        """Actual tuple/float headers plus a bit-aware finite-exp exponent bound."""
        if type(count) is not int or count < 0:
            raise ValueError("scaled probability buffer shape is invalid")
        # exp of a finite binary64 argument can have an integer binary exponent
        # with max_exp+O(1) BITS, not merely the small integer value1024.
        exponent_bits = sys.float_info.max_exp + 8
        limbs = (
            exponent_bits + sys.int_info.bits_per_digit - 1
        ) // sys.int_info.bits_per_digit
        exponent = sys.getsizeof(0) + limbs * sys.int_info.sizeof_digit
        reference = sys.getsizeof((None,)) - sys.getsizeof(())
        entry = (
            2 * sys.getsizeof((None, None))
            + 2 * sys.getsizeof(0.0)
            + exponent
            + 2 * reference
        )
        return self.lease(count * entry, pair_elements=3 * count)

    def admit_vertices(self, count):
        """Admit the upcoming native expansion without calling an estimate actual."""
        if type(count) is not int or count < 0:
            raise ValueError("native vertex count must be a nonnegative integer")
        if self.vertices + count > MAX_FIELD_VERTICES:
            raise FieldResourceError(
                "NEW figure native geometry exceeds2,000,000 path vertices"
            )

    def emit_vertices(self, count):
        """Count actual native instances, including every closure vertex."""
        self.admit_vertices(count)
        self.charge("output_vertices", count)
        self.vertices += count

    def native_path_lease(self, vertices, paths, *, emit=True):
        """Admit actual native Path storage or a declared prospective upper bound."""
        import numpy as np
        from matplotlib.path import Path

        if (
            type(vertices) is not int
            or type(paths) is not int
            or min(vertices, paths) < 0
        ):
            raise ValueError("native geometry allocation shape is invalid")
        # Path vertex views share their backend point buffer; count that payload
        # once, each actual instance/dict/view header, and allocation alignment.
        # Library-owned bools/constants/key tables are not NEW owned storage.
        prototype = Path(np.empty((0, 2), dtype=float))
        path_header = sys.getsizeof(prototype) + sys.getsizeof(vars(prototype))
        array_header = sys.getsizeof(np.empty((0, 2), dtype=float))
        reference = sys.getsizeof((None,)) - sys.getsizeof(())
        alignment = max(np.dtype(float).alignment, 1)
        size = vertices * (2 * np.dtype(float).itemsize + np.dtype("uint8").itemsize)
        size += paths * (path_header + array_header + reference + 2 * alignment)
        lease = self.lease(size)
        try:
            if emit:
                self.emit_vertices(vertices)
            else:
                self.admit_vertices(vertices)
        except Exception:
            lease.close()
            raise
        return lease

    @contextmanager
    def buffer(self, shape, dtype="float64", *, active=True, copies=1):
        with self.array_lease(shape, dtype, active=active, copies=copies):
            yield

    def report(self):
        return {
            "composite_units": self.units,
            "by_kind": dict(self.by_kind),
            "new_live_bytes": self.live_bytes,
            "new_peak_bytes": self.peak_bytes,
            "active_pair_elements": self.pair_elements,
            "peak_pair_elements": self.peak_pair_elements,
            "native_vertices_including_closure": self.vertices,
            "backend_rgba_bytes_outside_working_allowance": self.rgba_bytes,
        }
