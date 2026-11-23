"""Bounded analytic kernel arithmetic, with figure-owned resource accounting.

DLMF7.6/7.9 alternating/positive continued-fraction brackets; outward IEEE
binary64 endpoints and exponent-preserving products. No numerical provider,
random integration or source observation conversion is hidden in this module.
"""

from __future__ import annotations

import heapq
import itertools
import math
import struct
import sys
from collections import OrderedDict
from contextlib import nullcontext
from fractions import Fraction
from types import CellType

U = math.ulp(0.0)


class KernelPrecisionError(ValueError):
    """Requested numerical enclosure cannot be resolved without false output."""


def _constant(text):
    lower = Fraction(text)
    upper = lower + Fraction(1, 10**50)
    lo, hi = float(lower), float(upper)
    if Fraction.from_float(lo) > lower:
        lo = math.nextafter(lo, -math.inf)
    if Fraction.from_float(hi) < upper:
        hi = math.nextafter(hi, math.inf)
    return lo, hi


_PI = _constant("3.14159265358979323846264338327950288419716939937510")
_LN2 = _constant("0.69314718055994530941723212145817656807550013436025")
_LN10 = _constant("2.30258509299404568401799145468436420760110148862877")

_ZERO = (0.0, 0.0)
_ONE = (1.0, 1.0)
_MAX_GAUSSIAN_INTERVALS = 65536
_CELL_HEADER_BYTES = sys.getsizeof(CellType())


def _point(value):
    return float(value), float(value)


def _magnitude(bound):
    return max(abs(bound[0]), abs(bound[1]))


class IntervalMath:
    """One render's optional ledger; mathematical errors always remain errors."""

    def __init__(self, budget=None):
        self.budget = budget
        self.pi = _PI
        self.ln2 = _LN2
        self.ln10 = _LN10
        self.phi0 = self.div((1.0, 1.0), self.sqrt_interval(self.mul((2.0, 2.0), _PI)))
        self.compact_radius = self.sqrt_point(5.0)

    def _charge(self, kind, count=1, *, bits=None):
        if self.budget is not None:
            self.budget.charge(kind, count, bits=bits)

    def reject(self, message):
        self._charge("domain_rejections", 1)
        raise KernelPrecisionError(message)

    def checked(self, a):
        if len(a) != 2 or not all(math.isfinite(x) for x in a) or a[0] > a[1]:
            self.reject("nonfinite/reversed interval is unresolved")
        return a

    def outward(self, x, direction):
        if not math.isfinite(x):
            self.reject("nonfinite arithmetic intermediate is unresolved")
        result = math.nextafter(x, direction)
        if not math.isfinite(result):
            self.reject("unbounded outward endpoint is unresolved")
        return result

    def down(self, x):
        return self.outward(x, -math.inf)

    def up(self, x):
        return self.outward(x, math.inf)

    def add(self, a, b):
        self.checked(a)
        self.checked(b)
        self._charge("arithmetic", 2)
        return (self.down(a[0] + b[0]), self.up(a[1] + b[1]))

    def sub(self, a, b):
        self.checked(a)
        self.checked(b)
        self._charge("arithmetic", 2)
        return (self.down(a[0] - b[1]), self.up(a[1] - b[0]))

    def mul(self, a, b):
        self.checked(a)
        self.checked(b)
        self._charge("arithmetic", 4)
        if a == (0.0, 0.0) or b == (0.0, 0.0):
            return (0.0, 0.0)
        products = [x * y for x in a for y in b]
        if not all(math.isfinite(x) for x in products):
            self.reject("product overflow is unresolved")
        return (self.down(min(products)), self.up(max(products)))

    def div(self, a, b):
        self.checked(a)
        self.checked(b)
        if b[0] <= 0 <= b[1]:
            self.reject("division through zero is unresolved")
        self._charge("arithmetic", 4)
        values = [x / y for x in a for y in b]
        if not all(math.isfinite(x) for x in values):
            self.reject("quotient overflow is unresolved")
        return (self.down(min(values)), self.up(max(values)))

    def nonnegative(self, a):
        self.checked(a)
        if a[1] < 0:
            self.reject("claimed nonnegative quantity is strictly negative")
        return (max(0.0, a[0]), a[1])

    def ratio(self, n, d):
        self._charge(
            "integer_endpoint_conversion",
            4,
            bits=max(abs(n).bit_length(), abs(d).bit_length(), 1)
            + min(1075, abs(abs(n).bit_length() - abs(d).bit_length()) + 55),
        )
        exact = Fraction(n, d)
        try:
            f = float(exact)
        except OverflowError:
            self.reject("rational endpoint overflow")
        if not math.isfinite(f):
            self.reject("rational endpoint nonfinite")
        return (
            self.down(f) if Fraction.from_float(f) > exact else f,
            self.up(f) if Fraction.from_float(f) < exact else f,
        )

    def sqrt_point(self, x):
        if not math.isfinite(x) or x < 0:
            self.reject("sqrt domain")
        if x == 0:
            return (0.0, 0.0)
        candidate = math.sqrt(x)
        lo = self.down(candidate)
        hi = self.up(candidate)
        n, d = x.as_integer_ratio()
        for _ in range(64):
            ln, ld = lo.as_integer_ratio()
            hn, hd = hi.as_integer_ratio()
            self._charge(
                "sqrt_dyadic_comparisons",
                4,
                bits=max(
                    n.bit_length() + 2 * ld.bit_length(),
                    2 * hn.bit_length() + d.bit_length(),
                ),
            )
            if ln * ln * d <= n * ld * ld and hn * hn * d >= n * hd * hd:
                return (lo, hi)
            if ln * ln * d > n * ld * ld:
                lo = self.down(lo)
            if hn * hn * d < n * hd * hd:
                hi = self.up(hi)
        self.reject("sqrt enclosure unresolved")

    def sqrt_interval(self, a):
        self.checked(a)
        return (self.sqrt_point(a[0])[0], self.sqrt_point(a[1])[1])

    def normalize(self, a, e):
        self.checked(a)
        if a[0] < 0:
            self.reject("scaled positive interval became negative")
        if a[1] == 0:
            return (a, e)
        shift = math.frexp(a[1])[1]
        self._charge("scaled_renormalizations", 1)
        return (
            (
                max(0.0, self.down(math.ldexp(a[0], -shift))),
                self.up(math.ldexp(a[1], -shift)),
            ),
            e + shift,
        )

    def exp_negative_scaled(self, t):
        if not math.isfinite(t) or t < 0:
            self.reject("negative-exp domain")
        if t == 0:
            return ((1.0, 1.0), 0)
        k = 0 if t <= 0.125 else max(0, math.frexp(t)[1] + 3)
        u = math.ldexp(t, -k)
        term = (1.0, 1.0)
        partial = (1.0, 1.0)
        lo = 0.0
        hi = 1.0
        for n in range(1, 13):
            self._charge("exp_terms", 1)
            term = self.div(self.mul(term, (u, u)), (float(n), float(n)))
            partial = self.sub(partial, term) if n % 2 else self.add(partial, term)
            if n % 2:
                lo = max(lo, partial[0])
            else:
                hi = min(hi, partial[1])
        result, e = self.normalize((lo, hi), 0)
        for _ in range(k):
            self._charge("exp_squares", 1)
            result, e = self.normalize(
                self.nonnegative(self.mul(result, result)), 2 * e
            )
        return (result, e)

    def finish_scaled(self, a, e):
        self.checked(a)
        if a[0] < 0:
            self.reject("scaled endpoint negative")
        if a[1] == 0:
            return (0.0, 0.0)
        a, e = self.normalize(a, e)
        if e < -1075:
            return (0.0, U)
        if e > 1024:
            self.reject("final scaled output overflow")
        try:
            lo = math.ldexp(a[0], e)
            hi = math.ldexp(a[1], e)
        except OverflowError:
            self.reject("final scaled output overflow")
        return (max(0.0, self.down(lo)), self.up(hi))

    def scaled_product(self, factors, scaled):
        a, e = scaled
        for factor in factors:
            self.checked(factor)
            if factor[0] < 0:
                self.reject("negative positive-product factor")
            if factor[1] == 0:
                return (0.0, 0.0)
            f, fe = self.normalize(factor, 0)
            a, e = self.normalize(self.nonnegative(self.mul(a, f)), e + fe)
        return self.finish_scaled(a, e)

    def exp_negative_point(self, t):
        return self.scaled_product([], self.exp_negative_scaled(t))

    def exp_negative(self, a):
        self.checked(a)
        if a[0] < 0:
            self.reject("negative magnitude interval")
        return (self.exp_negative_point(a[1])[0], self.exp_negative_point(a[0])[1])

    def mills(self, x):
        if not math.isfinite(x) or x <= 0:
            self.reject("Mills domain")

        def convergent(n):
            tail = (0.0, 0.0)
            for j in range(n, 0, -1):
                self._charge("continued_fraction_terms", 1)
                tail = self.div((float(j), float(j)), self.add((x, x), tail))
            return self.div((1.0, 1.0), self.add((x, x), tail))

        bracket = (0.0, self.up(1 / x))
        for n in (8, 16, 32, 64, 128, 256, 512, 1024):
            even = convergent(n)
            odd = convergent(n + 1)
            bracket = (max(bracket[0], odd[0]), min(bracket[1], even[1]))
            self.checked(bracket)
            if bracket[1] - bracket[0] <= 1e-12 * bracket[0]:
                return bracket
        self.reject("Mills width unresolved")

    def normal_tail(self, x):
        if x < 0 or not math.isfinite(x):
            self.reject("tail domain")
        if x == 0:
            return (0.5, 0.5)
        if x >= 40:
            return (0.0, U)
        if x <= 2:
            xx = (x, x)
            x2 = self.mul(xx, xx)
            term = xx
            partial = xx
            lo = 0.0
            hi = x
            for n in range(1, 33):
                self._charge("normal_series_terms", 1)
                term = self.div(
                    self.mul(self.mul(term, x2), (float(2 * n - 1), float(2 * n - 1))),
                    (float(2 * n * (2 * n + 1)), float(2 * n * (2 * n + 1))),
                )
                partial = self.sub(partial, term) if n % 2 else self.add(partial, term)
                if n % 2:
                    lo = max(lo, partial[0])
                else:
                    hi = min(hi, partial[1])
            result = self.sub((0.5, 0.5), self.mul(self.phi0, (lo, hi)))
            return (max(0.0, result[0]), min(0.5, result[1]))
        return self.normal_tail_scaled(x, 1.0)

    def normal_tail_scaled(self, x, scale):
        if not math.isfinite(x) or x < 0 or (not math.isfinite(scale)) or (scale < 0):
            self.reject("scaled tail domain")
        if x <= 2:
            return self.nonnegative(self.mul(self.normal_tail(x), (scale, scale)))
        exponent = self.nonnegative(self.div(self.mul((x, x), (x, x)), (2.0, 2.0)))
        factors = [self.phi0, self.mills(x), (scale, scale)]
        low = self.scaled_product(factors, self.exp_negative_scaled(exponent[1]))[0]
        high = self.scaled_product(factors, self.exp_negative_scaled(exponent[0]))[1]
        return (low, high)

    def normal_cdf(self, x):
        if x < 0:
            return self.normal_tail(-x)
        return self.nonnegative(self.sub((1.0, 1.0), self.normal_tail(x)))

    def pdf_scaled(self, x, factors):
        exponent = self.nonnegative(
            self.div(self.mul((abs(x), abs(x)), (abs(x), abs(x))), (2.0, 2.0))
        )
        lo = self.scaled_product(
            [self.phi0, *factors], self.exp_negative_scaled(exponent[1])
        )[0]
        hi = self.scaled_product(
            [self.phi0, *factors], self.exp_negative_scaled(exponent[0])
        )[1]
        return (lo, hi)

    def normal_interval_scaled(self, a, b, scale):
        endpoint_tail = self.normal_tail_scaled
        if not all(math.isfinite(x) for x in (a, b, scale)) or a > b or scale < 0:
            self.reject("scaled interval domain")
        if a == b or scale == 0:
            return (0.0, 0.0)
        width_exact = Fraction.from_float(b) - Fraction.from_float(a)
        width = self.ratio(width_exact.numerator, width_exact.denominator)
        far = max(abs(a), abs(b))
        near = 0.0 if a <= 0 <= b else min(abs(a), abs(b))
        low = self.pdf_scaled(far, [width, (scale, scale)])[0]
        high = self.pdf_scaled(near, [width, (scale, scale)])[1]
        if a >= 0:
            tail = self.nonnegative(
                self.sub(endpoint_tail(a, scale), endpoint_tail(b, scale))
            )
        elif b <= 0:
            tail = self.nonnegative(
                self.sub(
                    endpoint_tail(-b, scale),
                    endpoint_tail(-a, scale),
                )
            )
        else:
            tail = self.nonnegative(
                self.sub(
                    self.sub((scale, scale), endpoint_tail(-a, scale)),
                    endpoint_tail(b, scale),
                )
            )
        return (max(0.0, low, tail[0]), min(scale, high, tail[1]))

    def normal_interval(self, a, b):
        return self.normal_interval_scaled(a, b, 1.0)

    def compact_cdf(self, t):
        if not math.isfinite(t):
            self.reject("compact CDF domain")
        r = self.compact_radius
        if t <= -r[1]:
            return (0.0, 0.0)
        if t >= r[1]:
            return (1.0, 1.0)
        q = self.div((t, t), r)
        q = (max(-1.0, q[0]), min(1.0, q[1]))
        if q[0] >= 0:
            gap = self.sub((1.0, 1.0), q)
            tail = self.div(
                self.mul(self.mul(gap, gap), self.add((2.0, 2.0), q)),
                (4.0, 4.0),
            )
            result = self.sub((1.0, 1.0), tail)
        else:
            gap = self.add((1.0, 1.0), q)
            result = self.div(
                self.mul(self.mul(gap, gap), self.sub((2.0, 2.0), q)),
                (4.0, 4.0),
            )
        result = (max(0.0, result[0]), min(1.0, result[1]))
        return self.checked(result)

    def scaled_ratio(self, n, d):
        if not isinstance(n, int) or not isinstance(d, int) or n < 0 or (d <= 0):
            self.reject("canonical scaled ratio domain")
        if n == 0:
            return ((0.0, 0.0), 0)
        self._charge(
            "integer_scaled_ratio",
            2,
            bits=max(n.bit_length(), d.bit_length(), 1),
        )
        e = n.bit_length() - d.bit_length() + 1
        nn, dd = (n, d << e) if e >= 0 else (n << -e, d)
        return self.normalize(self.ratio(nn, dd), e)

    def combine_scaled(self, parts):
        result = (1.0, 1.0)
        exponent = 0
        for part, e in parts:
            self.checked(part)
            if part[0] < 0:
                self.reject("negative scaled positive factor")
            if part[1] == 0:
                return ((0.0, 0.0), 0)
            result, exponent = self.normalize(
                self.nonnegative(self.mul(result, part)), exponent + e
            )
        return (result, exponent)

    def rescale_endpoint(self, x, e, upper):
        if x == 0:
            return 0.0
        if e < -1075:
            return U if upper else 0.0
        try:
            value = math.ldexp(x, e)
        except OverflowError:
            self.reject("scaled endpoint overflow")
        return self.up(value) if upper else max(0.0, self.down(value))

    def to_shared_exponent(self, part, e, target):
        return (
            self.rescale_endpoint(part[0], e - target, False),
            self.rescale_endpoint(part[1], e - target, True),
        )

    def exp_negative_scaled_interval(self, a):
        self.checked(a)
        if a[0] < 0:
            self.reject("negative exp interval domain")
        low, le = self.exp_negative_scaled(a[1])
        high, he = self.exp_negative_scaled(a[0])
        e = max(le, he)
        return self.normalize(
            (
                self.rescale_endpoint(low[0], le - e, False),
                self.rescale_endpoint(high[1], he - e, True),
            ),
            e,
        )

    def normal_tail_representation(self, x):
        if not math.isfinite(x) or x < 0:
            self.reject("normal scaled representation domain")
        if x <= 2:
            return self.normalize(self.normal_tail(x), 0)
        exponent = self.nonnegative(self.div(self.mul((x, x), (x, x)), (2.0, 2.0)))
        return self.combine_scaled(
            [
                (self.phi0, 0),
                (self.mills(x), 0),
                self.exp_negative_scaled_interval(exponent),
            ]
        )

    def composition(self, parts):
        if not parts or all((part == (0.0, 0.0) for part, e in parts)):
            return None
        exponent = max((e for part, e in parts if part[1] > 0))
        normalized = [self.to_shared_exponent(part, e, exponent) for part, e in parts]
        denominator = (0.0, 0.0)
        for part in normalized:
            denominator = self.add(denominator, part)
        denominator = self.nonnegative(denominator)
        if denominator[0] <= 0:
            self.reject(
                "relative composition denominator unresolved;not a true-zero gap"
            )
        result = []
        for part in normalized:
            if part == (0.0, 0.0):
                result.append((0.0, 0.0))
                continue
            q = self.div(part, denominator)
            q = (max(0.0, q[0]), min(1.0, q[1]))
            self.checked(q)
            result.append(q)
        return result

    def logarithm(self, x):
        if not math.isfinite(x) or x <= 0:
            self.reject("positive logarithm domain")
        m, e = math.frexp(x)
        m *= 2
        e -= 1
        t = self.nonnegative(
            self.div(self.sub((m, m), (1.0, 1.0)), self.add((m, m), (1.0, 1.0)))
        )
        t2 = self.nonnegative(self.mul(t, t))
        power = t
        total = t
        for n in range(1, 65):
            self._charge("log_series_terms", 1)
            power = self.nonnegative(self.mul(power, t2))
            total = self.add(
                total, self.div(power, (float(2 * n + 1), float(2 * n + 1)))
            )
        next_power = self.nonnegative(self.mul(power, t2))
        remainder = self.div(
            self.mul((2.0, 2.0), next_power),
            self.mul((131.0, 131.0), self.sub((1.0, 1.0), t2)),
        )
        reduced = self.mul((2.0, 2.0), total)
        reduced = (reduced[0], self.up(reduced[1] + remainder[1]))
        return self.add(self.mul((float(e), float(e)), _LN2), reduced)

    def log10_interval(self, x):
        return self.div(self.logarithm(x), _LN10)

    def normal_cdf_representation(self, x):
        """Keep a lower-tail exponent until mixtures/compositions are resolved."""
        if x < 0:
            return self.normal_tail_representation(-x)
        return self.normalize(self.normal_cdf(x), 0)

    def sum_scaled(self, parts):
        """Positive interval sum without erasing a relative tail before division."""
        nonzero = [part for part in parts if part[0][1] > 0]
        if not nonzero:
            return (0.0, 0.0), 0
        exponent = max(part[1] for part in nonzero)
        total = (0.0, 0.0)
        for value, power in nonzero:
            total = self.add(total, self.to_shared_exponent(value, power, exponent))
        return self.normalize(self.nonnegative(total), exponent)

    def kernel_cdf(self, kind, value):
        """A scaled analytic CDF interval, not an empirical/source-data operator."""
        self.checked(value)
        if kind == "gaussian":
            low, le = self.normal_cdf_representation(value[0])
            high, he = self.normal_cdf_representation(value[1])
            exponent = max(le, he)
            return self.normalize(
                (
                    self.rescale_endpoint(low[0], le - exponent, False),
                    self.rescale_endpoint(high[1], he - exponent, True),
                ),
                exponent,
            )
        if kind != "epanechnikov_product":
            self.reject("unknown named kernel")
        return self.normalize(
            (self.compact_cdf(value[0])[0], self.compact_cdf(value[1])[1]), 0
        )

    def positive_part(self, value):
        """Interval image of max(0,x), distinct from claiming x is nonnegative."""
        self.checked(value)
        return max(0.0, value[0]), max(0.0, value[1])

    def kernel_pdf(self, kind, value):
        """Variance-one kernel, retaining its exponent before amplitude products."""
        self.checked(value)
        near = 0.0 if value[0] <= 0 <= value[1] else min(map(abs, value))
        far = max(map(abs, value))
        if kind == "gaussian":
            low = self.nonnegative(
                self.div(self.mul((near, near), (near, near)), (2.0, 2.0))
            )
            high = self.nonnegative(
                self.div(self.mul((far, far), (far, far)), (2.0, 2.0))
            )
            return self.combine_scaled(
                [(self.phi0, 0), self.exp_negative_scaled_interval((low[0], high[1]))]
            )
        if kind != "epanechnikov_product":
            self.reject("unknown named kernel")
        radius = self.compact_radius
        if value[0] >= radius[1] or value[1] <= -radius[1]:
            return (0.0, 0.0), 0
        maximum = self.div(
            self.mul(
                (3.0, 3.0),
                self.positive_part(
                    self.sub(
                        (1.0, 1.0),
                        self.div(self.mul((near, near), (near, near)), (5.0, 5.0)),
                    )
                ),
            ),
            self.mul((4.0, 4.0), radius),
        )[1]
        minimum = 0.0
        if far < radius[0]:
            minimum = self.div(
                self.mul(
                    (3.0, 3.0),
                    self.positive_part(
                        self.sub(
                            (1.0, 1.0),
                            self.div(self.mul((far, far), (far, far)), (5.0, 5.0)),
                        )
                    ),
                ),
                self.mul((4.0, 4.0), radius),
            )[0]
        return self.normalize((max(0.0, minimum), maximum), 0)

    def fraction(self, value):
        """Outward canonical scalar conversion, including signed subnormals."""
        value = Fraction(value)
        if not value:
            return (0.0, 0.0)
        if value < 0:
            low, high = self.ratio(-value.numerator, value.denominator)
            return -high, -low
        return self.ratio(value.numerator, value.denominator)

    def fraction_bounds(self, lower, upper):
        if lower > upper:
            self.reject("reversed canonical scalar bounds")
        return self.fraction(lower)[0], self.fraction(upper)[1]

    def sqrt_fraction(self, value):
        """Square-root before finishing an exponent, not an overflowing variance."""
        return self.finish_scaled(*self.sqrt_fraction_scaled(value))

    def sqrt_fraction_scaled(self, value):
        value = Fraction(value)
        if value < 0:
            self.reject("negative canonical square root")
        if not value:
            return (0.0, 0.0), 0
        mantissa, exponent = self.scaled_ratio(value.numerator, value.denominator)
        if exponent % 2:
            mantissa = self.mul(mantissa, (2.0, 2.0))
            exponent -= 1
        low, high = self.sqrt_point(mantissa[0]), self.sqrt_point(mantissa[1])
        return self.normalize((low[0], high[1]), exponent // 2)

    def log_fraction(self, value):
        """Keep a canonical value/exponent before logarithmic source fitting."""
        value = Fraction(value)
        if value <= 0:
            self.reject("logarithmic source values must be positive")
        if value == 1:
            return (0.0, 0.0)
        mantissa, exponent = self.scaled_ratio(value.numerator, value.denominator)
        low = self.logarithm(mantissa[0])[0]
        high = self.logarithm(mantissa[1])[1]
        return self.add(
            (low, high),
            self.mul((float(exponent), float(exponent)), self.ln2),
        )

    def log10_fraction(self, value):
        return self.div(self.log_fraction(value), self.ln10)

    def reciprocal_scaled(self, value):
        mantissa, exponent = value
        if mantissa[0] <= 0:
            self.reject("relative reciprocal denominator unresolved")
        return self.normalize(self.div((1.0, 1.0), mantissa), -exponent)

    def exp_signed_scaled(self, value):
        """Signed exponent range; combine its scale before any final conversion."""
        self.checked(value)

        def point(x):
            result = self.exp_negative_scaled(abs(x))
            return self.reciprocal_scaled(result) if x > 0 else result

        low, le = point(value[0])
        high, he = point(value[1])
        exponent = max(le, he)
        return self.normalize(
            (
                self.rescale_endpoint(low[0], le - exponent, False),
                self.rescale_endpoint(high[1], he - exponent, True),
            ),
            exponent,
        )

    def _rational_charge(self, a, b, operations):
        bits = max(
            max(abs(value.numerator).bit_length(), value.denominator.bit_length())
            for value in (*a, *b)
        )
        self._charge("integer_source_interval", operations, bits=2 * bits + 2)

    def rational_add(self, a, b):
        self._rational_charge(a, b, 2)
        return a[0] + b[0], a[1] + b[1]

    def rational_sub(self, a, b):
        self._rational_charge(a, b, 2)
        return a[0] - b[1], a[1] - b[0]

    def rational_mul(self, a, b):
        self._rational_charge(a, b, 4)
        values = [x * y for x in a for y in b]
        return min(values), max(values)

    def rational_div(self, a, b):
        if b[0] <= 0 <= b[1]:
            self.reject("canonical interval division includes zero")
        self._rational_charge(a, b, 4)
        values = [x / y for x in a for y in b]
        return min(values), max(values)

    def scaled_hull(self, low, high):
        """Keep exponent when one endpoint is a known compact-kernel zero."""
        parts = [part for part in (low, high) if part[0][1] > 0]
        if not parts:
            return (0.0, 0.0), 0
        exponent = max(part[1] for part in parts)
        return self.normalize(
            (
                self.rescale_endpoint(low[0][0], low[1] - exponent, False),
                self.rescale_endpoint(high[0][1], high[1] - exponent, True),
            ),
            exponent,
        )

    def midpoint(self, value):
        """Correctly rounded even midpoint, without sum overflow/subnormal loss."""
        bits = max(
            max(abs(numerator).bit_length(), denominator.bit_length())
            for endpoint in value
            for numerator, denominator in (endpoint.as_integer_ratio(),)
        )
        self._charge("integer_endpoint_midpoint", 3, bits=bits + 2)
        return float((Fraction(value[0]) + Fraction(value[1])) / 2)

    def composition_values(self, parts):
        """A feasible sum-one vector INSIDE adequately resolved ratio enclosures."""
        bounds = self.composition(parts)
        if bounds is None:
            return None
        for low, high in bounds:
            if self.sub((high, high), (low, low))[1] > 1e-6:
                self.reject("relative composition precision is unresolved")
        bits = (
            max(
                max(abs(numerator).bit_length(), denominator.bit_length())
                for bound in bounds
                for endpoint in bound
                for numerator, denominator in (endpoint.as_integer_ratio(),)
            )
            + len(bounds).bit_length()
            + 2
        )
        self._charge("integer_composition_bounds", 8 * len(bounds), bits=bits)
        lows = [Fraction(value[0]) for value in bounds]
        highs = [Fraction(value[1]) for value in bounds]
        values = [(low + high) / 2 for low, high in zip(lows, highs, strict=True)]
        if sum(lows) > 1 or sum(highs) < 1:
            self.reject("composition enclosures have no sum-one solution")
        remaining = Fraction(1) - sum(values)
        for index, value in enumerate(values):
            self._charge(
                "integer_composition_selection",
                4,
                bits=max(
                    value.numerator.bit_length(),
                    value.denominator.bit_length(),
                    remaining.numerator.bit_length(),
                    remaining.denominator.bit_length(),
                ),
            )
            if remaining >= 0:
                change = min(remaining, highs[index] - value)
            else:
                change = -min(-remaining, value - lows[index])
            values[index] += change
            remaining -= change
        if remaining:
            self.reject("composition enclosure selection is unresolved")
        return values

    def normal_cdf_interval(self, value):
        self.checked(value)
        return self.normal_cdf(value[0])[0], self.normal_cdf(value[1])[1]

    def normal_mass_interval(self, left, right):
        if left is None:
            return self.normal_cdf_interval(right)
        self.checked(left)
        self.checked(right)
        if left[0] > right[1]:
            self.reject("normal rectangle endpoints are reversed")
        if left == right and left[0] == left[1]:
            return 0.0, 0.0
        if left[0] >= 40 or right[1] <= -40:
            return 0.0, U
        low = self.normal_interval(left[1], right[0])[0] if left[1] < right[0] else 0.0
        high = self.normal_interval(left[0], right[1])[1]
        return low, high

    def gaussian_rectangle(
        self, xlo, xhi, ylo, yhi, slope, tolerance, *, workspace=None
    ):
        """True original-law Gaussian rectangle via signed Plackett/fourth-jet Simpson.

        Outward source/rho bounds and exact current-leaf dyadic totals; the optional
        private workspace belongs to one caller field, never this arithmetic object.
        Plackett1954 DOI10.1093/biomet/41.3-4.351; Meyer arXiv0912.2816 eq2.5-2.10."""
        iv = self
        budget = self.budget
        if budget is not None:
            slots = 12 * 5
            reference = sys.getsizeof((None,)) - sys.getsizeof(())
            fixed = (
                slots
                * (sys.getsizeof((0.0, 0.0)) + 2 * sys.getsizeof(0.0) + 2 * reference)
                + 12 * sys.getsizeof([])
                + 5 * sys.getsizeof((None, None))
                + 4 * sys.getsizeof((None, None, None))
                + sys.getsizeof([None] * 4)
                + sys.getsizeof({})
                + 3 * sys.getsizeof((None,) * 7)
                + 8 * sys.getsizeof(Fraction(0))
                + 20 * sys.getsizeof(IntervalMath.gaussian_rectangle)
                + 112 * _CELL_HEADER_BYTES
                + 20 * sys.getsizeof((None,) * 12)
            )
        with (
            budget.lease(fixed, pair_elements=2 * slots + 12)
            if budget is not None
            else nullcontext(),
            budget.scaled_lease(8) if budget is not None else nullcontext(),
        ):
            budget = iv.budget
            if workspace is not None:
                workspace.check(iv, tolerance)
            for bound in (xlo, xhi, ylo, yhi, slope):
                if bound is not None:
                    iv.checked(bound)
            if not math.isfinite(tolerance) or tolerance <= 0:
                iv.reject("Plackett tolerance domain")
            for low, high in ((xlo, xhi), (ylo, yhi)):
                if low is not None and high is not None and (low[0] > high[1]):
                    iv.reject("Plackett reversed rectangle")
            if xlo is None and xhi is None and (ylo is None) and (yhi is None):
                return _ONE

            def bounded_probability(result):
                result = iv.checked((max(0.0, result[0]), min(1.0, result[1])))
                if (
                    result[0] != result[1]
                    and iv.sub(_point(result[1]), _point(result[0]))[1] > tolerance
                ):
                    iv.reject("Plackett marginal endpoint precision unresolved")
                return result

            def marginal_raw(low, high):
                if low is None:
                    return _ONE if high is None else iv.normal_cdf_interval(high)
                if high is None:
                    return iv.normal_cdf_interval((-low[1], -low[0]))
                return iv.normal_mass_interval(low, high)

            def marginal(low, high):
                if workspace is None:
                    return marginal_raw(low, high)
                mask = int(low is None) + 2 * int(high is None)
                key = struct.pack(">B4d", mask, *(low or _ZERO), *(high or _ZERO))
                hit, value = workspace.lookup(1, key)
                if hit:
                    return value
                value = marginal_raw(low, high)
                workspace.put(1, key, value)
                return value

            if ylo is None and yhi is None:
                return bounded_probability(marginal(xlo, xhi))
            if slope == _ZERO:
                result = iv.nonnegative(iv.mul(marginal(xlo, xhi), marginal(ylo, yhi)))
                if (
                    result[0] != result[1]
                    and iv.sub(_point(result[1]), _point(result[0]))[1] > tolerance
                ):
                    iv.reject("Plackett independent endpoint precision unresolved")
                return bounded_probability(result)

            def mapping_raw():
                bits = (
                    2
                    * max(
                        (
                            max(abs(value).bit_length(), denominator.bit_length())
                            for value, denominator in (
                                bound.as_integer_ratio() for bound in slope
                            )
                        )
                    )
                    + 4
                )
                with (
                    budget.integer_lease(bits, count=24)
                    if budget is not None
                    else nullcontext()
                ):
                    if budget is not None:
                        budget.charge("plackett_exact_slope_mapping", 32, bits=bits)

                    def norm_at(value):
                        return iv.sqrt_fraction(Fraction(1) + Fraction(value) ** 2)

                    smallest = (
                        0.0
                        if slope[0] <= 0 <= slope[1]
                        else min(abs(slope[0]), abs(slope[1]))
                    )
                    largest = max(map(abs, slope))
                    norm = (norm_at(smallest)[0], norm_at(largest)[1])
                    rho = (
                        iv.div(_point(slope[0]), norm_at(slope[0]))[0],
                        iv.div(_point(slope[1]), norm_at(slope[1]))[1],
                    )
                return (norm, rho)

            if workspace is None:
                norm, rho = mapping_raw()
            else:
                map_key = struct.pack(">2d", *slope)
                hit, mapped = workspace.lookup(0, map_key)
                if not hit:
                    mapped = mapping_raw()
                    workspace.put(0, map_key, mapped)
                norm, rho = mapped
            ylo = None if ylo is None else iv.div(ylo, norm)
            yhi = None if yhi is None else iv.div(yhi, norm)
            base = iv.mul(marginal(xlo, xhi), marginal(ylo, yhi))
            corners = []
            for x, sx in ((xhi, 1), (xlo, -1)):
                for y, sy in ((yhi, 1), (ylo, -1)):
                    if x is not None and y is not None:
                        corners.append((x, y, sx * sy))
            if not corners:
                return bounded_probability(base)
            if not -1 < rho[0] <= rho[1] < 1:
                iv.reject(
                    "Plackett source correlation enclosure reaches singular endpoint"
                )
            inv2pi = iv.div(_ONE, iv.mul((2.0, 2.0), iv.pi))
            maximum = max(map(abs, rho))
            qmin = iv.sub(_ONE, iv.mul(_point(maximum), _point(maximum)))
            if qmin[0] <= 0:
                iv.reject(
                    "Plackett near-unit correlation cannot prove positive denominator"
                )
            peak = iv.div(inv2pi, iv.sqrt_interval(qmin))[1]
            centre = iv.midpoint(rho)
            strip = iv.mul(
                _point(
                    max(
                        iv.sub(_point(centre), _point(rho[0]))[1],
                        iv.sub(_point(rho[1]), _point(centre))[1],
                    )
                ),
                iv.mul(_point(len(corners)), _point(peak)),
            )[1]
            if strip >= tolerance:
                iv.reject(
                    "Plackett correlation endpoint uncertainty exceeds "
                    "numerical allocation"
                )
            cache_lease = None
            integral_lease = None
            midpoint_lease = None
            cache = {}
            heap = []
            serial = itertools.count()
            endpoint_bits = 1 - sys.float_info.min_exp + sys.float_info.mant_dig
            accumulator_bits = (
                sys.float_info.max_exp
                + endpoint_bits
                + _MAX_GAUSSIAN_INTERVALS.bit_length()
                + 4
            )

            def neg(value):
                return iv.sub(_ZERO, value)

            def correlation_jets_raw(domain, order):
                q = [
                    iv.sub(_ONE, iv.mul(domain, domain)),
                    iv.mul((-2.0, -2.0), domain),
                    (-1.0, -1.0),
                ]
                if q[0][0] <= 0:
                    iv.reject("Plackett integration cell meets singular correlation")
                inverse = [iv.div(_ONE, q[0])]
                for n in range(1, order + 1):
                    total = _ZERO
                    for k in range(1, min(2, n) + 1):
                        total = iv.add(total, iv.mul(q[k], inverse[n - k]))
                    inverse.append(neg(iv.div(total, q[0])))
                prefactor = [iv.div(_ONE, iv.sqrt_interval(q[0]))]
                for n in range(1, order + 1):
                    total = _ZERO
                    for k in range(1, min(2, n) + 1):
                        total = iv.add(
                            total,
                            iv.mul(
                                _point(n - k + k / 2), iv.mul(q[k], prefactor[n - k])
                            ),
                        )
                    prefactor.append(neg(iv.div(total, iv.mul(_point(n), q[0]))))
                return (inverse, prefactor)

            def correlation_jets(domain, order):
                if workspace is None:
                    return correlation_jets_raw(domain, order)
                kind = 2 if order == 0 else 3
                assert order in (0, 4)
                key = struct.pack(">B2d", order, *domain)
                hit, value = workspace.lookup(kind, key)
                if hit:
                    return value
                value = correlation_jets_raw(domain, order)
                workspace.put(kind, key, value)
                return value

            def density_jet_raw(x, y, domain, order, inverse, prefactor):
                cross = iv.mul((-2.0, -2.0), iv.mul(x, y))
                A = [
                    iv.add(iv.add(iv.mul(x, x), iv.mul(y, y)), iv.mul(cross, domain)),
                    cross,
                ]
                exponent = []
                for n in range(order + 1):
                    total = iv.mul(A[0], inverse[n])
                    if n:
                        total = iv.add(total, iv.mul(A[1], inverse[n - 1]))
                    exponent.append(iv.mul((-0.5, -0.5), total))
                gaussian = [iv.finish_scaled(*iv.exp_signed_scaled(exponent[0]))]
                for n in range(1, order + 1):
                    total = _ZERO
                    for k in range(1, n + 1):
                        total = iv.add(
                            total,
                            iv.mul(_point(k), iv.mul(exponent[k], gaussian[n - k])),
                        )
                    gaussian.append(iv.div(total, _point(n)))
                total = _ZERO
                for k in range(order + 1):
                    total = iv.add(total, iv.mul(gaussian[k], prefactor[order - k]))
                return iv.mul(inv2pi, total)

            def density_jet(x, y, domain, order, inverse, prefactor):
                if workspace is None:
                    return density_jet_raw(x, y, domain, order, inverse, prefactor)
                assert order in (0, 4)
                key = struct.pack(">B8d", order, *domain, *x, *y, *inv2pi)
                kind = 4 if order == 0 else 5
                hit, value = workspace.lookup(kind, key)
                if hit:
                    return value
                value = density_jet_raw(x, y, domain, order, inverse, prefactor)
                workspace.put(kind, key, value)
                return value

            def signed_jet(domain, order):
                if budget is not None:
                    budget.charge("plackett_shared_correlation_jet_domains")
                inverse, prefactor = correlation_jets(domain, order)
                result = _ZERO
                if budget is not None:
                    budget.charge("plackett_signed_corner_jets", len(corners))
                for x, y, sign in corners:
                    value = density_jet(x, y, domain, order, inverse, prefactor)
                    result = (
                        iv.add(result, value) if sign == 1 else iv.sub(result, value)
                    )
                return result

            def sample(domain):
                scalar = domain[0] == domain[1]
                key = domain[0] if scalar else domain
                if key not in cache:
                    if cache_lease is not None:
                        cache_lease.grow(
                            sys.getsizeof({None: None})
                            - sys.getsizeof({})
                            + sys.getsizeof(key)
                            + (0 if scalar else 2 * sys.getsizeof(0.0))
                            + sys.getsizeof((0.0, 0.0))
                            + 2 * sys.getsizeof(0.0),
                            pair_elements=3 if scalar else 4,
                        )
                    cache[key] = signed_jet(domain, 0)
                return cache[key]

            def cell(a, b):
                lease = None
                if budget is not None:
                    lease = budget.lease(
                        sys.getsizeof((None,) * 8)
                        + 5 * sys.getsizeof(0.0)
                        + sys.getsizeof(0),
                        pair_elements=5,
                    )
                    budget.charge("plackett_adaptive_intervals")
                try:
                    if budget is not None:
                        budget.charge(
                            "plackett_exact_midpoint_enclosures",
                            8,
                            bits=endpoint_bits + 4,
                        )
                    midpoint_domain = iv.fraction((Fraction(a) + Fraction(b)) / 2)
                    width = iv.fraction(Fraction(b) - Fraction(a))
                    simpson = iv.mul(
                        iv.div(width, (6.0, 6.0)),
                        iv.add(
                            iv.add(
                                sample(_point(a)),
                                iv.mul((4.0, 4.0), sample(midpoint_domain)),
                            ),
                            sample(_point(b)),
                        ),
                    )
                    fourth = iv.mul(
                        (24.0, 24.0), _point(_magnitude(signed_jet((a, b), 4)))
                    )[1]
                    fifth = width
                    for _ in range(4):
                        fifth = iv.mul(fifth, width)
                    remainder = iv.div(iv.mul(fifth, _point(fourth)), (2880.0, 2880.0))[
                        1
                    ]
                    enclosed = iv.add(simpson, (-remainder, remainder))
                    return (
                        -(enclosed[1] - enclosed[0]),
                        next(serial),
                        a,
                        b,
                        enclosed[0],
                        enclosed[1],
                        lease,
                    )
                except Exception:
                    if lease is not None:
                        lease.close()
                    raise

            def encode(value):
                numerator, denominator = value.as_integer_ratio()
                shift = endpoint_bits - (denominator.bit_length() - 1)
                if budget is not None:
                    budget.charge(
                        "plackett_endpoint_exact_dyadic",
                        1,
                        bits=max(1, abs(numerator).bit_length() + shift),
                    )
                return numerator << shift

            def accumulate(first, second, subtract=False):
                if budget is not None:
                    budget.charge(
                        "plackett_exact_signed_endpoint_add",
                        1,
                        bits=max(abs(first).bit_length(), abs(second).bit_length()) + 1,
                    )
                return first - second if subtract else first + second

            def finish(low, high):
                signed = (low, high) if centre >= 0 else (-high, -low)
                complete_low = accumulate(
                    accumulate(base_units[0], signed[0]), strip_units, True
                )
                complete_high = accumulate(
                    accumulate(base_units[1], signed[1]), strip_units
                )
                complete_low = max(0, complete_low)
                complete_high = min(denominator, complete_high)
                return iv.checked(
                    iv.fraction_bounds(
                        Fraction(complete_low, denominator),
                        Fraction(complete_high, denominator),
                    )
                )

            try:
                if budget is not None:
                    cache_lease = budget.hashmap_lease(0)
                    integral_lease = budget.integer_lease(accumulator_bits, count=32)
                    midpoint_lease = budget.integer_lease(endpoint_bits + 4, count=12)
                denominator = 1 << endpoint_bits
                base_units = tuple(map(encode, base))
                strip_units = encode(strip)
                if centre == 0:
                    result = finish(0, 0)
                    if (
                        result[0] != result[1]
                        and iv.sub(_point(result[1]), _point(result[0]))[1] > tolerance
                    ):
                        iv.reject(
                            "Plackett zero-width integral endpoint precision unresolved"
                        )
                    return result
                low, high = sorted((0.0, centre))
                initial = cell(low, high)
                heapq.heappush(heap, initial)
                lo, hi = map(encode, initial[4:6])
                del initial
                result = finish(lo, hi)
                while (
                    result[0] != result[1]
                    and iv.sub(_point(result[1]), _point(result[0]))[1] > tolerance
                ):
                    if len(heap) + 1 > _MAX_GAUSSIAN_INTERVALS:
                        iv.reject(
                            "Plackett original adaptive interval capacity unresolved"
                        )
                    old = heapq.heappop(heap)
                    _priority, _serial, a, b, oldlo, oldhi, lease = old
                    if lease is not None:
                        lease.close()
                    middle = iv.midpoint((a, b))
                    if not a < middle < b:
                        iv.reject("Plackett midpoint collapses")
                    lo = accumulate(lo, encode(oldlo), True)
                    hi = accumulate(hi, encode(oldhi), True)
                    for left, right in ((a, middle), (middle, b)):
                        child = cell(left, right)
                        lo = accumulate(lo, encode(child[4]))
                        hi = accumulate(hi, encode(child[5]))
                        heapq.heappush(heap, child)
                    result = finish(lo, hi)
                return result
            finally:
                cache.clear()
                for row in heap:
                    if row[6] is not None:
                        row[6].close()
                if cache_lease is not None:
                    cache_lease.close()
                if integral_lease is not None:
                    integral_lease.close()
                if midpoint_lease is not None:
                    midpoint_lease.close()

    def compact_rectangle(self, xlo, xhi, ylo, yhi, slope, tolerance):
        """Exact-degree-five product-kernel integral plus outward root slivers.

        In s=U/sqrt5 the density is3/4*(1-s²), and the interior CDF is cubic.
        Splitting BOTH endpoints of every uncertain support crossing makes
        five-node Boole quadrature an exact-real identity on each polynomial
        piece. Uncertain crossing strips use positive probability bounds.
        """
        radius = self.compact_radius
        xl = None if xlo is None else self.div(xlo, radius)
        xh = self.div(xhi, radius)
        yl = None if ylo is None else self.div(ylo, radius)
        yh = self.div(yhi, radius)
        a = -1.0 if xl is None else max(-1.0, xl[0])
        b = min(1.0, xh[1])
        if b <= a:
            return 0.0, 0.0

        def support_cdf(point):
            if point <= -1:
                return Fraction(0)
            if point >= 1:
                return Fraction(1)
            point = Fraction(point)
            self._charge(
                "integer_compact_cdf",
                5,
                bits=6
                * max(point.numerator.bit_length(), point.denominator.bit_length()),
            )
            return Fraction(1, 2) + Fraction(3, 4) * point - point**3 / 4

        def cdf_interval(value):
            return self.fraction_bounds(support_cdf(value[0]), support_cdf(value[1]))

        def conditional(domain):
            high = cdf_interval(self.sub(yh, self.mul(slope, domain)))
            if yl is None:
                return high
            low = cdf_interval(self.sub(yl, self.mul(slope, domain)))
            return self.nonnegative(self.sub(high, low))

        sliver = Fraction(0)
        for endpoint in (xl, xh):
            if endpoint is not None:
                sliver += support_cdf(endpoint[1]) - support_cdf(endpoint[0])
        edges = {a, b}
        root_intervals = {bound: [] for bound in ((yh,) if yl is None else (yh, yl))}
        if slope[0] > 0 or slope[1] < 0:
            for bound in (yh,) if yl is None else (yh, yl):
                for crossing in (-1.0, 1.0):
                    whole = self.sub(bound, self.mul(slope, (a, b)))
                    if not whole[0] <= crossing <= whole[1]:
                        continue
                    root = self.div(self.sub(bound, (crossing, crossing)), slope)
                    root_intervals[bound].append(root)
                    for value in root:
                        if a < value < b:
                            edges.add(value)
        pieces = sorted(edges)
        lo_total = hi_total = Fraction(0)

        def phase(bound, domain):
            if bound is None:
                return -1  # identically zero lower-orthant subtraction
            if any(
                domain[0] < root[1] and root[0] < domain[1]
                for root in root_intervals[bound]
            ):
                return None
            # There is no possible support crossing in this open piece.
            # Classify at an exact rational midpoint, not a rounded full-range
            # interval whose endpoint slack can spuriously straddle a root.
            middle = (Fraction(domain[0]) + Fraction(domain[1])) / 2
            value = self.rational_sub(
                tuple(map(Fraction, bound)),
                self.rational_mul(tuple(map(Fraction, slope)), (middle, middle)),
            )
            if value[1] <= -1:
                return -1
            if value[0] >= 1:
                return 1
            if value[0] >= -1 and value[1] <= 1:
                return 0
            return None

        fraction_slope = tuple(map(Fraction, slope))
        fraction_high = tuple(map(Fraction, yh))
        fraction_low = None if yl is None else tuple(map(Fraction, yl))

        def polynomial(bound, status, point):
            if status == -1:
                return Fraction(0), Fraction(0)
            if status == 1:
                return Fraction(1), Fraction(1)
            value = self.rational_sub(
                bound,
                self.rational_mul(fraction_slope, (point, point)),
            )
            square = self.rational_mul(value, value)
            inside = self.rational_sub(
                (Fraction(3, 4),) * 2,
                self.rational_mul((Fraction(1, 4),) * 2, square),
            )
            return self.rational_add(
                (Fraction(1, 2),) * 2, self.rational_mul(value, inside)
            )

        for left, right in itertools.pairwise(pieces):
            self._charge("compact_conditional_intervals")
            domain = left, right
            high_phase = phase(yh, domain)
            low_phase = -1 if yl is None else phase(yl, domain)
            mass = support_cdf(right) - support_cdf(left)
            safe = self.nonnegative(self.mul(self.fraction(mass), conditional(domain)))
            if high_phase is None or low_phase is None:
                low, high = map(Fraction, safe)
            else:
                width = Fraction(right) - Fraction(left)
                low = high = Fraction(0)
                for index, coefficient in enumerate((7, 32, 12, 32, 7)):
                    point = Fraction(left) + width * Fraction(index, 4)
                    upper_cdf = polynomial(fraction_high, high_phase, point)
                    lower_cdf = polynomial(fraction_low, low_phase, point)
                    value = self.rational_mul(
                        self.rational_sub(upper_cdf, lower_cdf),
                        (Fraction(3, 4) * (1 - point * point),) * 2,
                    )
                    scaled = self.rational_mul(value, (width * coefficient / 90,) * 2)
                    low += scaled[0]
                    high += scaled[1]
                low = max(low, Fraction(safe[0]), Fraction(0))
                high = min(high, Fraction(safe[1]))
                if low > high:
                    self.reject("compact polynomial and positive bounds disagree")
            self._charge(
                "integer_compact_probability_sum",
                2,
                bits=max(
                    low.denominator.bit_length(),
                    high.denominator.bit_length(),
                    lo_total.denominator.bit_length(),
                    hi_total.denominator.bit_length(),
                )
                + 2,
            )
            lo_total += low
            hi_total += high
        result = self.fraction_bounds(
            max(Fraction(0), lo_total - sliver), min(Fraction(1), hi_total)
        )
        if self.sub((result[1], result[1]), (result[0], result[0]))[1] > tolerance:
            self.reject("compact joint CDF endpoint/root precision unresolved")
        return result


class _GaussianRectangleWorkspace:
    """Concrete Gaussian-rectangle field workspace; no persistent/global cache.

    Retains exact constant slope mapping, 1D marginal windows, domain/order
    inverse/prefactor jets and bounded exact density jets. The underlying
    density/exponential/Simpson expressions and point selection stay untouched.
    Capacities are retention choices; fulltables evict oldest exact results.
    """

    __slots__ = (
        "closed",
        "constants",
        "entry_bytes",
        "header",
        "iv",
        "owners",
        "tables",
        "tolerance",
    )

    def __init__(self, iv, tolerance):
        if iv.budget is None:
            raise ValueError("field reuse requires its actual figure ledger")
        self.iv = iv
        self.tolerance = tolerance
        self.closed = False
        self.owners = []
        self.header = iv.budget.lease(
            sys.getsizeof(self)
            + 2 * sys.getsizeof((None,) * 6)
            + 6 * sys.getsizeof(OrderedDict())
            + 8192,
            pair_elements=64,
        )
        self.tables: tuple[OrderedDict[bytes, tuple], ...] = ()
        try:
            self.constants = struct.pack(">8d", *iv.pi, *iv.phi0, *iv.ln2, *iv.ln10)
            point_bytes = sys.getsizeof((0.0, 0.0)) + 2 * sys.getsizeof(0.0)
            values = (
                sys.getsizeof((None, None)) + 2 * point_bytes,
                point_bytes,
                sys.getsizeof((None, None))
                + 2 * sys.getsizeof([None])
                + 2 * point_bytes,
                sys.getsizeof((None, None))
                + 2 * sys.getsizeof([None] * 8)
                + 10 * point_bytes,
                point_bytes,
                point_bytes,
            )
            slot = sys.getsizeof(OrderedDict([(None, None)])) - sys.getsizeof(
                OrderedDict()
            )
            keys = (
                struct.pack(">2d", 0.0, 0.0),
                struct.pack(">B4d", 0, 0.0, 0.0, 0.0, 0.0),
                struct.pack(">B2d", 0, 0.0, 0.0),
                struct.pack(">B2d", 4, 0.0, 0.0),
                struct.pack(">B8d", 0, *[0.0] * 8),
                struct.pack(">B8d", 4, *[0.0] * 8),
            )
            self.entry_bytes = tuple(
                slot + sys.getsizeof(key) + value
                for key, value in zip(keys, values, strict=True)
            )
            for _ in range(6):
                self.owners.append(iv.budget.lease(0))
            self.tables = (
                OrderedDict(),
                OrderedDict(),
                OrderedDict(),
                OrderedDict(),
                OrderedDict(),
                OrderedDict(),
            )
        except Exception:
            self.close()
            raise

    def check(self, iv, tolerance):
        assert iv is self.iv and tolerance.hex() == self.tolerance.hex()
        assert self.constants == struct.pack(
            ">8d", *iv.pi, *iv.phi0, *iv.ln2, *iv.ln10
        ), "immutable arithmetic namespace changed"

    def lookup(self, kind, key):
        capacity = (1, 1024, 128, 128, 8192, 8192)[kind]
        scalars = (6, 7, 7, 23, 11, 11)[kind]
        self.iv.budget.charge(
            "plackett_field_reuse_key_words", max(1, (len(key) + 7) // 8)
        )
        table = self.tables[kind]
        if key in table:
            self.iv.budget.charge(
                (
                    "plackett_slope_reuse_hits",
                    "plackett_marginal_reuse_hits",
                    "plackett_q0_reuse_hits",
                    "plackett_q4_reuse_hits",
                    "plackett_density0_reuse_hits",
                    "plackett_density4_reuse_hits",
                )[kind]
            )
            table.move_to_end(key)
            return (True, table[key])
        self.iv.budget.charge(
            (
                "plackett_slope_reuse_misses",
                "plackett_marginal_reuse_misses",
                "plackett_q0_reuse_misses",
                "plackett_q4_reuse_misses",
                "plackett_density0_reuse_misses",
                "plackett_density4_reuse_misses",
            )[kind]
        )
        if len(table) == capacity:
            self.iv.budget.charge("plackett_field_reuse_evictions")
            table.popitem(last=False)
        else:
            self.owners[kind].grow(self.entry_bytes[kind], pair_elements=scalars)
        return (False, None)

    def put(self, kind, key, value):
        self.tables[kind][key] = value

    def close(self):
        if self.closed:
            return
        self.closed = True
        for table in self.tables:
            table.clear()
        for owner in reversed(self.owners):
            owner.close()
        self.owners.clear()
        self.header.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
