import numpy as np
from mudplot.color import palette as P


def test_qualitative_count_and_gamut():
    pal = P.qualitative(6)
    assert len(pal) == 6
    assert pal.srgb.shape == (6, 3)
    assert np.all(pal.srgb >= -1e-6) and np.all(pal.srgb <= 1 + 1e-6)


def test_qualitative_equal_lightness():
    # explicit lightness_jitter=0 preserves the exact equal-L* guarantee;
    # the default now applies a small jitter for greyscale safety (see
    # tests/test_palette_design.py).
    pal = P.qualitative(8, lightness=60.0, lightness_jitter=0)
    assert np.allclose(pal.lch[:, 0], 60.0, atol=1e-6)


def test_qualitative_cvd_safe_min_distance():
    # colourblind-safe palettes should keep a usable worst-case separation
    pal = P.qualitative(5)
    assert pal.min_delta_e(("protan", "deutan")) > 8.0


def test_qualitative_cvd_safe_beats_unsafe_on_worstcase():
    safe = P.qualitative(6, cvd_safe=True).min_delta_e()
    unsafe = P.qualitative(6, cvd_safe=False).min_delta_e()
    assert safe >= unsafe - 1e-9


def test_sequential_monotonic_lightness():
    pal = P.sequential(10)
    L = pal.lch[:, 0]
    assert np.all(np.diff(L) < 0)  # light -> dark


def test_diverging_symmetric_endpoints_lightness():
    pal = P.diverging(9)
    L = pal.lch[:, 0]
    assert L[0] < L[len(L) // 2]  # centre is lightest
    assert L[-1] < L[len(L) // 2]


def test_to_cmap():
    cmap = P.sequential(256).to_cmap()
    assert cmap.N == 256
