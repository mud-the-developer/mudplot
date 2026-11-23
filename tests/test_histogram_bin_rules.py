"""Independent equations and resource-bound regression tests for fixed v2 rules."""

import math
import subprocess
import sys

import numpy as np
import pytest
from mudplot._histogram_bins import (
    HISTOGRAM_BIN_RULES,
    MAX_HISTOGRAM_BINS,
    discrete_bin_edges,
    discrete_bounds,
    named_bin_edges,
)


@pytest.mark.parametrize(
    "rule,count", [("auto", 43), ("fd", 43), ("sturges", 4), ("sqrt", 3)]
)
def test_fixed_auto(rule, count):
    edges = named_bin_edges([0, 1, 2, 3, 100], rule)
    np.testing.assert_array_equal(edges, np.linspace(0, 100, count + 1))


@pytest.mark.parametrize("rule", HISTOGRAM_BIN_RULES)
def test_empty_constant_and_no_mutation(rule):
    assert named_bin_edges([], rule).size == 0
    np.testing.assert_array_equal(named_bin_edges([7], rule), [6.5, 7.5])
    x = np.array([1, 2, 4, 8, 16])
    original = x.copy()
    named_bin_edges(x, rule)
    np.testing.assert_array_equal(x, original)
    with pytest.raises(ValueError):
        named_bin_edges([float(2**54)], rule)


def test_manual_equations():
    x = np.array([0.0, 1.0, 2.0, 4.0, 8.0, 16.0])
    n, span = len(x), 16
    sigma = math.sqrt(sum((v - sum(x) / n) ** 2 for v in x) / n)
    skew = sum(((v - sum(x) / n) / sigma) ** 3 for v in x) / n
    widths = {
        "rice": span / (2 * n ** (1 / 3)),
        "scott": (24 * math.sqrt(math.pi) / n) ** (1 / 3) * sigma,
        "doane": span
        / (
            1
            + math.log2(n)
            + math.log2(1 + abs(skew) / math.sqrt(6 * (n - 2) / ((n + 1) * (n + 3))))
        ),
    }
    for rule, width in widths.items():
        assert len(named_bin_edges(x, rule)) - 1 == math.ceil(span / width)
    assert len(named_bin_edges([0, 1], "doane")) == 2
    assert len(named_bin_edges([0, 0, 0, 0, 1], "fd")) == 2
    assert len(named_bin_edges([0, 0, 0, 0, 1], "auto")) == 5


def test_stone_manual_cost():
    x = np.array([0.0, 1.0, 3.0, 6.0, 7.0, 9.0])

    def cost(k):
        counts = [0] * k
        for value in x:
            counts[min(int(value / 9 * k), k - 1)] += 1
        return (2 - (len(x) + 1) * sum((c / len(x)) ** 2 for c in counts)) / (9 / k)

    best = min(range(1, 101), key=cost)
    width = 9 / best
    assert len(named_bin_edges(x, "stone")) - 1 == math.ceil(9 / width)


@pytest.mark.parametrize("rule", ["fd", "auto"])
def test_cap_before_allocation(monkeypatch, rule):
    def forbidden(*args, **kwargs):
        pytest.fail("edge allocation happened before count validation")

    monkeypatch.setattr(np, "linspace", forbidden)
    with pytest.raises(ValueError, match="count"):
        named_bin_edges([0, 1e-100, 2e-100, 3e-100, 1e100], rule)
    with pytest.raises(ValueError, match="count"):
        discrete_bin_edges([0, MAX_HISTOGRAM_BINS])


@pytest.mark.parametrize(
    "values",
    [
        [True],
        [np.bool_(True)],
        [1.5],
        [math.inf],
        [math.nan],
        [2**53 + 1],
        [2**52],
        [10**400],
    ],
)
def test_discrete_rejections(values):
    with pytest.raises(ValueError):
        discrete_bounds(values)


def test_discrete_grid():
    assert discrete_bounds([]) is None
    assert discrete_bin_edges([]).size == 0
    values = [-2, 0, 2, 0]
    assert discrete_bounds(values) == (-2.5, 2.5, 5)
    np.testing.assert_array_equal(
        discrete_bin_edges(values), [-2.5, -1.5, -0.5, 0.5, 1.5, 2.5]
    )
    assert values == [-2, 0, 2, 0]
    assert len(discrete_bin_edges([0, 9999])) == 10001
    np.testing.assert_array_equal(
        discrete_bin_edges([2**51]), [2**51 - 0.5, 2**51 + 0.5]
    )


@pytest.mark.parametrize("values", [[math.inf], [math.nan], [-1e308, 1e308], [[1, 2]]])
def test_invalid_named(values):
    with pytest.raises(ValueError):
        named_bin_edges(values, "sqrt")


def test_import_and_bounds_are_stdlib_only():
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from mudplot._histogram_bins import discrete_bounds; "
            "assert discrete_bounds([1, 2]) == (0.5, 2.5, 2); "
            "assert 'numpy' not in sys.modules",
        ],
        check=True,
    )


def test_minimum_numpy_oracle():
    from pathlib import Path

    python = Path("artifacts/v2_counts_20261030/minimum/bin/python")
    if not python.exists():
        pytest.skip("optional NumPy 1.23.5 oracle environment unavailable")
    subprocess.run(
        [
            str(python),
            "-c",
            """
import numpy as np
from mudplot._histogram_bins import HISTOGRAM_BIN_RULES, named_bin_edges
assert np.__version__ == '1.23.5'
rng = np.random.default_rng(82)
for x in ([0, 1, 2, 3, 100], [0, 0, 0, 0, 1], [1, 2],
          rng.normal(size=75), rng.exponential(size=150)):
    for rule in HISTOGRAM_BIN_RULES:
        expected = np.histogram_bin_edges(np.asarray(x, dtype=float), bins=rule)
        np.testing.assert_array_equal(named_bin_edges(x, rule), expected)
""",
        ],
        check=True,
    )
