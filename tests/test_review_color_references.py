"""Independent numeric references: adopted D65/IEC matrix and Sharma's 34 pairs.

sRGB matrix: http://www.brucelindbloom.com/Eqn_RGB_XYZ_Matrix.html (D65 sRGB).
CIEDE2000: Sharma/Wu/Dalal supplementary data; source URL is in the fixture.
These test numeric calibration, not a universal accessibility certification.
"""

from pathlib import Path

import numpy as np
import pytest
from mudplot.color import convert as cv
from mudplot.color.distance import delta_e2000

SHARMA = np.loadtxt(Path(__file__).parent / "fixtures/sharma_ciede2000.txt")


@pytest.mark.parametrize(
    "index", range(34), ids=lambda index: f"Sharma-{index + 1:02d}"
)
def test_all_original_sharma_pairs_scalar_and_symmetric(index):
    first, second, expected = SHARMA[index, :3], SHARMA[index, 3:6], SHARMA[index, 6]
    assert np.isfinite(delta_e2000(first, second))
    assert delta_e2000(first, second) == pytest.approx(expected, abs=5e-5)
    assert delta_e2000(second, first) == pytest.approx(expected, abs=5e-5)


def test_sharma_vectorization_and_original_case_count():
    assert SHARMA.shape == (34, 7)
    result = delta_e2000(SHARMA[:, :3], SHARMA[:, 3:6])
    np.testing.assert_allclose(result, SHARMA[:, 6], rtol=0, atol=5e-5)
    assert np.max(np.abs(result - SHARMA[:, 6])) <= 5e-5
    np.testing.assert_array_equal(
        delta_e2000(SHARMA[:, :3], SHARMA[:, :3]), np.zeros(34)
    )


@pytest.mark.parametrize(
    "rgb,xyz,lab",
    [
        ([0, 0, 0], [0, 0, 0], [0, 0, 0]),
        ([1, 1, 1], [0.95047, 1.0000001, 1.08883], [100, 0, 0]),
        ([1, 0, 0], [0.4124564, 0.2126729, 0.0193339], [53.24079, 80.09246, 67.20320]),
        ([0, 1, 0], [0.3575761, 0.7151522, 0.1191920], [87.73472, -86.18272, 83.17932]),
        (
            [0, 0, 1],
            [0.1804375, 0.0721750, 0.9503041],
            [32.29701, 79.18752, -107.86016],
        ),
    ],
)
def test_d65_primary_reference_values_not_just_round_trip(rgb, xyz, lab):
    np.testing.assert_allclose(cv.linear_to_xyz(rgb), xyz, rtol=0, atol=1e-7)
    np.testing.assert_allclose(cv.srgb_to_lab(rgb), lab, rtol=0, atol=4e-5)
    np.testing.assert_allclose(cv.xyz_to_linear(xyz), rgb, rtol=0, atol=1e-6)


@pytest.mark.parametrize(
    "encoded,linear",
    [
        (0, 0),
        (0.02, 0.0015479876160990713),
        (0.04045, 0.0031308049535603713),
        (0.5, 0.21404114048223255),
        (1, 1),
    ],
)
def test_standard_srgb_transfer_reference_values(encoded, linear):
    # Exact intersection and rounded IEC cutoff differ by <3e-9 here.
    np.testing.assert_allclose(
        cv.srgb_to_linear([encoded] * 3), [linear] * 3, rtol=0, atol=3e-9
    )


@pytest.mark.parametrize(
    "lab,lch",
    [
        ([50, 3, 4], [50, 5, 53.130102354156]),
        ([50, -3, -4], [50, 5, 233.130102354156]),
        ([50, 0, -4], [50, 4, 270]),
        ([0, 0, 0], [0, 0, 0]),
    ],
)
def test_independent_polar_coordinate_references(lab, lch):
    np.testing.assert_allclose(cv.lab_to_lch(lab), lch, atol=1e-10)
    np.testing.assert_allclose(cv.lch_to_lab(lch), lab, atol=1e-10)
