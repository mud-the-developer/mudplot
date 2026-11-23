"""Named kernel laws and native geometry, not field-adapter forwarding tests."""

from __future__ import annotations

import itertools
import math
from fractions import Fraction

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import PolyCollection


def _normal_cdf(value):
    return 0.5 * math.erfc(-value / math.sqrt(2))


def _kernel_value(value, bandwidth, kernel, cumulative):
    if kernel is None:
        return (
            _normal_cdf(value)
            if cumulative
            else math.exp(-0.5 * value**2) / (math.sqrt(2 * math.pi) * bandwidth)
        )
    radius = math.sqrt(5)
    if cumulative:
        if value <= -radius:
            return 0.0
        if value >= radius:
            return 1.0
        return 0.5 + 3 / (4 * radius) * (value - value**3 / 15)
    return (
        3 / (4 * radius * bandwidth) * (1 - value**2 / 5)
        if abs(value) < radius
        else 0.0
    )


def _weighted_bandwidth(values, weights, factor):
    total = sum(weights)
    mean = (
        sum(
            Fraction(value) * weight
            for value, weight in zip(values, weights, strict=True)
        )
        / total
    )
    variance = sum(
        weight * (Fraction(value) - mean) ** 2
        for value, weight in zip(values, weights, strict=True)
    ) / (total - Fraction(sum(weight * weight for weight in weights), total))
    return math.sqrt(float(variance)) * factor


@pytest.mark.parametrize("kernel", [None, "epanechnikov_product"])
@pytest.mark.parametrize("cumulative", [False, True])
@pytest.mark.parametrize("multiple", ["layer", "stack", "fill"])
def test_native_kernel_bands_match_independent_density_or_cdf_contributions(
    cumulative, multiple, kernel
):
    source = {
        "x": [1.0, 2.0, 3.0, 2.0, 4.0, 6.0],
        "w": [1, 2, 1, 2, 1, 3],
        "g": ["first"] * 3 + ["second"] * 3,
    }
    p = mp.plot(source).kde(
        "x",
        group="g",
        weights="w",
        bw_method=0.8,
        gridsize=17,
        cut=0,
        multiple=multiple,
        common_grid=True,
        common_norm=True,
        cumulative=cumulative,
        kernel=kernel,
        fill=True,
    )
    serialized = p.to_json()
    random_state = np.random.get_state()
    figure = mp.Plot.from_json(serialized).render()
    try:
        bands = [
            artist
            for artist in figure.axes[0].collections
            if isinstance(artist, PolyCollection)
        ]
        assert len(bands) == 2
        grids = [
            np.unique(np.asarray(artist.get_paths()[0].vertices)[:, 0])
            for artist in bands
        ]
        np.testing.assert_array_equal(grids[0], grids[1])
        grid = grids[0]
        expected = []
        for start in (0, 3):
            values, weights = (
                source["x"][start : start + 3],
                source["w"][start : start + 3],
            )
            bandwidth = _weighted_bandwidth(values, weights, 0.8)
            expected.append(
                np.array(
                    [
                        sum(
                            weight
                            * _kernel_value(
                                (query - value) / bandwidth,
                                bandwidth,
                                kernel,
                                cumulative,
                            )
                            for value, weight in zip(values, weights, strict=True)
                        )
                        / sum(source["w"])
                        for query in grid
                    ]
                )
            )
        previous = np.zeros(len(grid))
        denominator = expected[0] + expected[1]
        for index, artist in enumerate(bands):
            vertices = np.asarray(artist.get_paths()[0].vertices)
            actual_bottom, actual_top = [], []
            for query in grid:
                ordinates = vertices[vertices[:, 0] == query, 1]
                actual_bottom.append(float(np.min(ordinates)))
                actual_top.append(float(np.max(ordinates)))
            thickness = (
                expected[index] / denominator if multiple == "fill" else expected[index]
            )
            bottom = previous if multiple != "layer" else np.zeros(len(grid))
            np.testing.assert_allclose(actual_bottom, bottom, rtol=2e-13, atol=2e-15)
            np.testing.assert_allclose(
                actual_top, bottom + thickness, rtol=2e-13, atol=2e-15
            )
            if multiple != "layer":
                previous = bottom + thickness
        if multiple == "fill":
            np.testing.assert_allclose(previous, 1, rtol=2e-15, atol=0)
        assert p.to_json() == serialized and p.spec.data.columns == source
        after = np.random.get_state()
        assert random_state[0] == after[0] and random_state[2:] == after[2:]
        np.testing.assert_array_equal(random_state[1], after[1])
    finally:
        plt.close(figure)


@pytest.mark.parametrize("density_space", ["data", "fit"])
def test_log_fit_native_density_has_declared_jacobian_not_display_base(density_space):
    source = {"x": [1.0, 10.0, 100.0, 1000.0]}
    p = (
        mp.plot(source)
        .axis_scale("x", "log", options=mp.ScaleOptionsSpec(base=2))
        .kde(
            "x",
            stat_scale="axis",
            density_space=density_space,
            bw_method=0.5,
            cut=0,
            gridsize=17,
        )
    )
    figure = p.render()
    try:
        line = next(
            artist
            for artist in figure.axes[0].lines
            if len(np.asarray(artist.get_xdata()))
        )
        bandwidth = math.sqrt(5 / 3) * 0.5
        expected = []
        for query in np.asarray(line.get_xdata()):
            value = sum(
                math.exp(-0.5 * ((math.log10(float(query)) - centre) / bandwidth) ** 2)
                for centre in (0, 1, 2, 3)
            ) / (4 * bandwidth * math.sqrt(2 * math.pi))
            if density_space == "data":
                value /= query * math.log(10)
            expected.append(value)
        np.testing.assert_allclose(
            np.asarray(line.get_ydata()), expected, rtol=3e-13, atol=0
        )
        assert p.spec.data.columns == source
    finally:
        plt.close(figure)


def test_native_joint_cdf_ignores_view_exclusion_of_source_rows():
    source = {"x": [-1.0, -1.0, 1.0, 1.0], "y": [-1.0, 1.0, -1.0, 1.0]}
    p = mp.plot(source).kde2d(
        "x",
        "y",
        cumulative=True,
        clip=[[-0.25, 0.25], [-0.25, 0.25]],
        levels=[0.2, 0.25, 0.3],
        bw_method=0.6,
        gridsize=17,
        colorbar=True,
    )
    serialized = p.to_json()
    figure = p.render()
    try:
        artist = next(
            item
            for item in figure.axes[0].collections
            if hasattr(item, "_mudplot_kernel_field")
        )
        bandwidth = math.sqrt(4 / 3) * 0.6

        def joint(x, y):
            return (
                sum(
                    _normal_cdf((x - a) / bandwidth) * _normal_cdf((y - b) / bandwidth)
                    for a, b in zip(source["x"], source["y"], strict=True)
                )
                / 4
            )

        grid_step = 0.5 / 16
        second = 1 / (math.sqrt(2 * math.pi * math.e) * bandwidth**2)
        bound = second * (2 * grid_step**2) / 8 + 2e-6
        values = np.asarray(artist.get_array())
        assert len(values) == len(artist.get_paths())
        for path, level in zip(artist.get_paths(), values, strict=True):
            assert (
                max(
                    abs(joint(float(x), float(y)) - float(level))
                    for x, y in np.asarray(path.vertices)
                )
                <= bound
            )
        assert p.to_json() == serialized and p.spec.data.columns == source
    finally:
        plt.close(figure)


def test_variance_one_cholesky_product_density_has_real_native_height_levels():
    source = {"x": [-1.0, -1.0, 1.0, 1.0], "y": [-1.0, 1.0, -1.0, 1.0]}
    p = mp.plot(source).kde2d(
        "x",
        "y",
        kernel="epanechnikov_product",
        bw_method=0.6,
        clip=[[-0.25, 0.25], [-0.25, 0.25]],
        levels=[0.076, 0.078, 0.079],
        level_kind="density",
        gridsize=33,
    )
    figure = p.render()
    try:
        artist = next(
            item
            for item in figure.axes[0].collections
            if hasattr(item, "_mudplot_kernel_field")
        )
        bandwidth = math.sqrt(4 / 3) * 0.6

        def kernel(value):
            return (
                max(0.0, 3 / (4 * math.sqrt(5)) * (1 - value**2 / 5))
                if abs(value) <= math.sqrt(5)
                else 0.0
            )

        def density(x, y):
            return sum(
                kernel((x - a) / bandwidth) * kernel((y - b) / bandwidth)
                for a, b in zip(source["x"], source["y"], strict=True)
            ) / (4 * bandwidth**2)

        # This view is strictly inside every compact support; the density is
        # polynomial here: the ordinary second-derivative bound applies.
        step = 0.5 / 32
        # max |K''| * max K = 9/200 for variance-one Epanechnikov.
        second = 0.045 / bandwidth**4
        error = second * (2 * step**2) / 8 + 1e-12
        for path, level in zip(
            artist.get_paths(), np.asarray(artist.get_array()), strict=True
        ):
            assert (
                max(
                    abs(density(float(x), float(y)) - float(level))
                    for x, y in np.asarray(path.vertices)
                )
                <= error
            )
        assert p.spec.data.columns == source
    finally:
        plt.close(figure)


@pytest.mark.parametrize("rho", [0.0, 0.5, -0.5, 0.99, -0.99, 1 - 1e-8, -1 + 1e-8])
def test_gaussian_joint_quadrants_enclose_the_analytic_original_law(rho):
    from mudplot._kernel_math import IntervalMath

    slope = rho / math.sqrt(1 - rho * rho) if rho else 0.0
    tolerance = 1e-6 / (4 * 17**2)
    low, high = IntervalMath().gaussian_rectangle(
        None, (0.0, 0.0), None, (0.0, 0.0), (slope, slope), tolerance
    )
    # For the EXACT represented conditional slope, asin(rho)=atan(slope).
    # Unlike solving rho again in binary64, atan remains well conditioned
    # near unit correlation. This is an independent Gaussian quadrant identity.
    expected = 0.25 + math.atan(slope) / (2 * math.pi)
    assert low <= expected <= high
    assert high - low <= tolerance


def test_signed_finite_gaussian_rectangles_match_independent_conditional_mass():
    from mudplot._kernel_math import IntervalMath

    arithmetic = IntervalMath()
    slope = -0.99 / math.sqrt(1 - 0.99**2)
    tolerance = 1e-6 / (4 * 32**2)

    def probability(xlo, xhi, ylo, yhi):
        return arithmetic.gaussian_rectangle(
            (xlo, xlo),
            (xhi, xhi),
            (ylo, ylo),
            (yhi, yhi),
            (slope, slope),
            tolerance,
        )

    full = probability(-1.1, 0.8, -0.7, 1.2)
    left = probability(-1.1, 0.1, -0.7, 1.2)
    right = probability(0.1, 0.8, -0.7, 1.2)
    symmetric = probability(-0.8, 1.1, -1.2, 0.7)
    assert max(full[0], left[0] + right[0]) <= min(full[1], left[1] + right[1])
    assert max(full[0], symmetric[0]) <= min(full[1], symmetric[1])

    def reference(order):
        nodes, weights = np.polynomial.legendre.leggauss(order)
        result = 0.0
        for a, b in itertools.pairwise(np.linspace(-1.1, 0.8, 20)):
            points = (a + b) / 2 + (b - a) / 2 * nodes
            conditional = np.array(
                [
                    _normal_cdf(1.2 - slope * float(point))
                    - _normal_cdf(-0.7 - slope * float(point))
                    for point in points
                ]
            )
            result += (
                (b - a)
                / 2
                * float(
                    np.dot(
                        weights,
                        np.exp(-0.5 * points**2) / math.sqrt(2 * math.pi) * conditional,
                    )
                )
            )
        return result

    coarse, fine = reference(16), reference(32)
    discrepancy = abs(coarse - fine)
    assert discrepancy < 1e-11
    assert full[0] <= fine + discrepancy + 1e-12
    assert full[1] >= fine - discrepancy - 1e-12
    assert full[1] - full[0] <= tolerance


def test_gaussian_empty_strip_preserves_exact_zero_at_smallest_positive_tolerance():
    from mudplot._kernel_math import IntervalMath

    result = IntervalMath().gaussian_rectangle(
        (0.0, 0.0),
        (0.0, 0.0),
        None,
        None,
        (0.5, 0.5),
        math.ulp(0.0),
    )
    assert result == (0.0, 0.0)
