import numpy as np
import pytest
from mudplot.color import convert as cv
from mudplot.color import cvd
from mudplot.color import distance as dist


def test_delta_e_zero_for_identical():
    lab = cv.srgb_to_lab(np.array([0.3, 0.6, 0.2]))
    assert dist.delta_e2000(lab, lab) == pytest.approx(0.0, abs=1e-9)
    assert dist.delta_e76(lab, lab) == pytest.approx(0.0, abs=1e-9)


def test_delta_e2000_sharma_reference():
    # One of the Sharma et al. (2005) verification pairs.
    lab1 = np.array([50.0000, 2.6772, -79.7751])
    lab2 = np.array([50.0000, 0.0000, -82.7485])
    assert dist.delta_e2000(lab1, lab2) == pytest.approx(2.0425, abs=1e-3)


def test_delta_e2000_sharma_reference2():
    lab1 = np.array([50.0000, 2.5000, 0.0000])
    lab2 = np.array([50.0000, 0.0000, -2.5000])
    assert dist.delta_e2000(lab1, lab2) == pytest.approx(4.3065, abs=1e-3)


def test_cvd_severity_zero_is_identity():
    rng = np.random.default_rng(0)
    srgb = rng.random((50, 3))
    for t in cvd.CVD_TYPES:
        sim = cvd.simulate(srgb, t, severity=0.0)
        assert np.allclose(srgb, sim, atol=1e-6)


def test_cvd_reduces_red_green_contrast():
    red = np.array([0.8, 0.1, 0.1])
    green = np.array([0.1, 0.7, 0.1])
    lab_r, lab_g = cv.srgb_to_lab(red), cv.srgb_to_lab(green)
    normal = dist.delta_e2000(lab_r, lab_g)

    sr = cv.srgb_to_lab(cvd.simulate(red, "deutan", 1.0))
    sg = cv.srgb_to_lab(cvd.simulate(green, "deutan", 1.0))
    deut = dist.delta_e2000(sr, sg)

    assert deut < normal
