import numpy as np
import pytest
from mudplot.color import convert as cv


def test_roundtrip_srgb_lch():
    rng = np.random.default_rng(0)
    srgb = rng.random((1000, 3))
    back = cv.lch_to_srgb(cv.srgb_to_lch(srgb))
    assert np.allclose(srgb, back, atol=1e-9)


def test_roundtrip_srgb_lab():
    rng = np.random.default_rng(1)
    srgb = rng.random((500, 3))
    back = cv.lab_to_srgb(cv.srgb_to_lab(srgb))
    assert np.allclose(srgb, back, atol=1e-9)


def test_white_is_L100():
    lab = cv.srgb_to_lab(np.array([1.0, 1.0, 1.0]))
    assert lab[0] == pytest.approx(100.0, abs=1e-4)
    assert lab[1] == pytest.approx(0.0, abs=1e-3)
    assert lab[2] == pytest.approx(0.0, abs=1e-3)


def test_black_is_L0():
    lab = cv.srgb_to_lab(np.array([0.0, 0.0, 0.0]))
    assert lab[0] == pytest.approx(0.0, abs=1e-6)


def test_known_pure_red():
    # sRGB pure red under D65 -> well-known CIELAB reference values.
    lab = cv.srgb_to_lab(np.array([1.0, 0.0, 0.0]))
    assert lab[0] == pytest.approx(53.24, abs=0.02)
    assert lab[1] == pytest.approx(80.09, abs=0.05)
    assert lab[2] == pytest.approx(67.20, abs=0.05)


def test_known_pure_green():
    lab = cv.srgb_to_lab(np.array([0.0, 1.0, 0.0]))
    assert lab[0] == pytest.approx(87.74, abs=0.02)
    assert lab[1] == pytest.approx(-86.18, abs=0.05)
    assert lab[2] == pytest.approx(83.18, abs=0.05)


def test_hex_roundtrip():
    for h in ["#0C5DA5", "#00B945", "#FF9500", "#000000", "#FFFFFF"]:
        srgb = cv.hex_to_srgb(h)
        assert cv.srgb_to_hex(srgb) == h


def test_hex_short_form():
    assert np.allclose(cv.hex_to_srgb("#fff"), [1.0, 1.0, 1.0])
    assert np.allclose(cv.hex_to_srgb("#000"), [0.0, 0.0, 0.0])


def test_in_gamut():
    inside = cv.srgb_to_srgb_identity = np.array([[0.5, 0.5, 0.5], [1.2, 0.0, 0.0]])
    mask = cv.in_gamut(inside)
    assert mask.tolist() == [True, False]


def test_lch_hue_range():
    rng = np.random.default_rng(2)
    srgb = rng.random((200, 3))
    lch = cv.srgb_to_lch(srgb)
    assert np.all(lch[:, 2] >= 0.0)
    assert np.all(lch[:, 2] < 360.0)
