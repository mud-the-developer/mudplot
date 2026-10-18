"""STAT-03: stable mean-fit intervals or explicit degenerate-design failures."""

import warnings
from statistics import NormalDist

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from mudplot._render import _regression_fit


@pytest.mark.parametrize("response_scale", [1.0, 1e-250, 1e250])
@pytest.mark.parametrize("typed", [False, True])
def test_mean_band_matches_independent_ols_without_covariance_scale_loss(
    response_scale, typed
):
    x = np.arange(5.0, dtype=float)
    raw_y = np.array([1.0, 2.0, 1.0, 4.0, 3.0])
    p = (
        mp.plot({"x": x, "y": raw_y * response_scale})
        .regplot("x", "y", confidence=95, regression={} if typed else None)
        .size(4, 3)
    )
    before = p.to_json()
    fig = p.render()
    try:
        line = fig.axes[0].lines[0]
        grid = np.asarray(line.get_xdata())
        prediction = np.asarray(line.get_ydata()) / response_scale
        slope = np.sum((x - x.mean()) * (raw_y - raw_y.mean())) / np.sum(
            (x - x.mean()) ** 2
        )
        expected = raw_y.mean() + slope * (grid - x.mean())
        mse = np.sum((raw_y - (raw_y.mean() + slope * (x - x.mean()))) ** 2) / (
            len(x) - 2
        )
        delta = NormalDist().inv_cdf(0.975) * np.sqrt(
            mse * (1 / len(x) + (grid - x.mean()) ** 2 / np.sum((x - x.mean()) ** 2))
        )
        np.testing.assert_allclose(prediction, expected, atol=1e-12)
        polygons = np.asarray(fig.axes[0].collections[0].get_paths()[0].vertices)
        assert np.isfinite(polygons).all()
        for coordinate, mean, half_width in zip(grid, expected, delta, strict=True):
            matching = polygons[polygons[:, 0] == coordinate, 1] / response_scale
            assert min(matching) == pytest.approx(mean - half_width, abs=1e-12)
            assert max(matching) == pytest.approx(mean + half_width, abs=1e-12)
        assert p.to_json() == before
    finally:
        plt.close(fig)


@pytest.mark.parametrize("typed", [False, True])
@pytest.mark.parametrize("confidence", [None, 95])
def test_numerical_rank_deficiency_fails_with_cause_and_preserves_previous_output(
    tmp_path, typed, confidence
):
    p = (
        mp.plot({"x": [*np.arange(11) * 1e-10, 1.0], "y": list(np.arange(12.0) ** 2)})
        .regplot(
            "x", "y", degree=10, confidence=confidence, regression={} if typed else None
        )
        .size(4, 3)
    )
    assert mp.validate(p.spec) == []
    target = tmp_path / "keep.svg"
    target.write_bytes(b"previous complete output")
    before = p.to_json()
    figures = set(plt.get_fignums())
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with pytest.raises(ValueError, match="fit failed") as error:
            p.save(str(target))
    assert error.value.__cause__ is not None and not caught
    assert target.read_bytes() == b"previous complete output" and not list(
        tmp_path.glob("*.tmp")
    )
    assert p.to_json() == before and set(plt.get_fignums()) == figures


@pytest.mark.parametrize("scale", [1e-250, 1e250, 1e308])
def test_polynomial_computation_scales_large_and_small_predictor_units(scale):
    x = np.array([0.5, 0.6, 0.7, 0.8, 0.9]) * scale
    y = np.array([1.0, 2.0, 1.0, 4.0, 3.0])
    before = x.copy()
    old_y = y.copy()
    grid, fit, band = _regression_fit(x, y, 1, 95)
    assert band is not None and np.isfinite(grid).all() and np.isfinite(fit).all()
    np.testing.assert_allclose(fit, 1.0 + 0.6 * (grid / scale - 0.5) / 0.1, atol=1e-12)
    assert np.isfinite(band).all()
    np.testing.assert_array_equal(x, before)
    np.testing.assert_array_equal(y, old_y)


@pytest.mark.parametrize(
    "raw,degree,confidence,reason",
    [
        ({"x": [1], "y": [2]}, 1, None, "observations"),
        ({"x": [1, 2], "y": [2, 3]}, 1, 95, "observations"),
        ({"x": [1, 1, 1], "y": [2, 3, 4]}, 1, None, "distinct"),
        ({"x": [1, 2, 3, 4], "y": [2, 3, 4, 5]}, 10, None, "observations"),
        ({"x": [1, 2, None, 4], "y": [2, 3, 4, 5]}, 1, 95, "finite"),
        ({"x": [1, 2, 3, 4], "y": [2, 3, None, 5]}, 1, 95, "finite"),
    ],
)
def test_structural_degenerate_inputs_are_explicit_without_silent_row_deletion(
    raw, degree, confidence, reason
):
    p = mp.plot(raw).regplot("x", "y", degree=degree, confidence=confidence)
    before = p.to_json()
    assert any(reason in issue for issue in mp.validate(p.spec))
    with pytest.raises(ValueError, match=reason):
        p.render()
    assert p.to_json() == before
