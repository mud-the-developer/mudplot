"""Full-model HDR native cells against an independent separable mixture law."""

from __future__ import annotations

import math
from fractions import Fraction
from itertools import pairwise

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
from matplotlib.collections import PolyCollection


def _normal_interval(left, right):
    root = math.sqrt(2)
    if left >= 0:
        return 0.5 * (math.erfc(left / root) - math.erfc(right / root))
    if right <= 0:
        return 0.5 * (math.erfc(-right / root) - math.erfc(-left / root))
    return 0.5 * (math.erf(right / root) - math.erf(left / root))


def test_full_hdr_native_cell_union_matches_independent_mixture_mass():
    source = {
        "x": [-1.0, -1.0, 1.0, 1.0],
        "y": [-1.0, 1.0, -1.0, 1.0],
        "id": ["southwest", "northwest", "southeast", "northeast"],
    }
    targets, tolerance = [0.5, 0.8], 0.04
    plot = mp.plot(source).kde2d(
        "x",
        "y",
        levels=targets,
        gridsize=12,
        hdr=mp.HDRSpec(scope="full", tolerance=tolerance),
        fill=True,
        line_width=0,
        line_style="--",
        alpha=1,
        colorbar=True,
    )
    serialized = plot.to_json()
    figure = mp.Plot.from_json(serialized).render()
    try:
        figure.canvas.draw()
        collection = next(
            artist
            for artist in figure.axes[0].collections
            if isinstance(artist, PolyCollection)
        )
        values = np.asarray(collection.get_array())
        cutoffs = np.unique(values)[::-1]
        assert len(cutoffs) == len(targets)
        assert all(width == 0 for width in collection.get_linewidths())
        assert np.all(np.asarray(collection.get_facecolors())[:, 3] == 1)
        # The four physical rows have covariance diag(4/3,4/3). Scott d=2
        # multiplies its square root by 4**(-1/6); no runtime fit helper is used.
        sigma = math.sqrt(4 / 3) * 4 ** (-1 / 6)
        masses = []
        for path in collection.get_paths():
            vertices = np.asarray(path.vertices)
            np.testing.assert_array_equal(vertices[0], vertices[-1])
            low, high = vertices.min(axis=0), vertices.max(axis=0)
            # Diagonal H makes each true native cell an axis-aligned rectangle;
            # Ordered segments must cover one whole boundary, not merely put
            # triangle/bowtie vertices on a rectangle's edges.
            exact = [(Fraction(float(x)), Fraction(float(y))) for x, y in vertices]
            edges = list(pairwise(exact))
            left, bottom = (Fraction(float(value)) for value in low)
            right, top = (Fraction(float(value)) for value in high)
            assert all(
                (a[0] == b[0] and a[0] in (left, right))
                or (a[1] == b[1] and a[1] in (bottom, top))
                for a, b in edges
            )
            perimeter = sum(abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in edges)
            twice_area = abs(sum(a[0] * b[1] - a[1] * b[0] for a, b in edges))
            assert perimeter == 2 * (right - left + top - bottom)
            assert twice_area == 2 * (right - left) * (top - bottom)
            masses.append(
                math.fsum(
                    0.25
                    * _normal_interval((low[0] - x) / sigma, (high[0] - x) / sigma)
                    * _normal_interval((low[1] - y) / sigma, (high[1] - y) / sigma)
                    for x, y in zip(source["x"], source["y"], strict=True)
                )
            )
        masses = np.asarray(masses)
        for target, cutoff in zip(targets, cutoffs, strict=True):
            included = math.fsum(masses[values >= cutoff])
            assert abs(included - target) <= tolerance
        assert plot.to_json() == serialized and plot.spec.data.columns == source
    finally:
        plt.close(figure)
