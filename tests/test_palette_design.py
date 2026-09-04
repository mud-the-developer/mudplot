"""Tests for the design-quality pass: lightness jitter (greyscale safety)
and the palette distinguishability report.
"""

import numpy as np
from mudplot.color import palette as P


def test_no_jitter_is_exactly_equal_lightness():
    pal = P.qualitative(5, lightness_jitter=0)
    assert np.allclose(pal.lch[:, 0], pal.lch[0, 0])


def test_no_jitter_greyscale_is_indistinguishable():
    pal = P.qualitative(5, lightness_jitter=0)
    gray = pal.grayscale_srgb()
    # every swatch collapses to (nearly) the same grey value
    assert np.allclose(gray, gray[0], atol=1e-3)
    assert pal.min_lightness_gap() < 1e-6


def test_jitter_gives_distinct_lightness_values():
    pal = P.qualitative(6, lightness_jitter=8)
    L = pal.lch[:, 0]
    assert len(set(np.round(L, 3))) == len(L)  # all distinct
    assert pal.min_lightness_gap() > 0


def test_jitter_improves_greyscale_separation():
    pal_flat = P.qualitative(5, lightness_jitter=0)
    pal_jit = P.qualitative(5, lightness_jitter=10)
    assert pal_jit.min_lightness_gap() > pal_flat.min_lightness_gap()


def test_jitter_keeps_cvd_safety_reasonable():
    pal = P.qualitative(5, lightness_jitter=6)
    assert pal.min_delta_e() > 5.0  # still clearly distinguishable


def test_grayscale_srgb_shape_and_range():
    pal = P.qualitative(4)
    gray = pal.grayscale_srgb()
    assert gray.shape == pal.srgb.shape
    assert np.all(gray >= 0) and np.all(gray <= 1)
    # r == g == b for every swatch (true greyscale)
    assert np.allclose(gray[:, 0], gray[:, 1])
    assert np.allclose(gray[:, 1], gray[:, 2])


def test_report_flags_flat_palette_as_not_grayscale_safe():
    pal = P.qualitative(5, lightness_jitter=0)
    report = pal.report()
    assert report["grayscale_safe"] is False
    assert report["note"] is not None


def test_report_flags_jittered_small_palette_as_grayscale_safe():
    pal = P.qualitative(3, lightness_jitter=10)
    report = pal.report()
    assert report["grayscale_safe"] is True
    assert report["note"] is None


def test_report_single_color_has_no_gap():
    pal = P.qualitative(1)
    report = pal.report()
    assert report["min_lightness_gap"] is None
    assert report["grayscale_safe"] is True


def test_sequential_and_diverging_unaffected_by_jitter_param():
    # jitter is qualitative-only; sequential/diverging already vary L by design
    seq = P.sequential(5)
    assert len(set(np.round(seq.lch[:, 0], 3))) == 5
