"""Independent density/covariance/CDF equations and opt-in KDE contracts."""

from __future__ import annotations

import json
import math
import warnings
from statistics import NormalDist
from typing import Any, cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import PolyCollection
from matplotlib.colors import to_rgba
from matplotlib.mlab import GaussianKDE
from mudplot import actions as A
from mudplot._kde import kde_summary
from mudplot.spec import KDESpec, LayerSpec


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def summarize(p, index=0):
    assert mp.validate(p.spec) == []
    return kde_summary(p.spec.data.columns, p.spec.panels[0].layers[index])


def integral(curve):
    y = np.array(curve.heights)
    return float(np.dot(np.diff(curve.support), (y[1:] + y[:-1]) / 2))


def sample():
    return {
        "x": [0, 1, 3, 8, 9, 12],
        "w": [1, 2, 1, 3, 1, 2],
        "g": ["A"] * 3 + ["B"] * 3,
    }


@pytest.mark.parametrize("method", ["scott", "silverman", 0.4])
@pytest.mark.parametrize("adjust", [0.7, 1.6])
def test_unweighted_fit_matches_native_gaussian_covariance_and_evaluation(
    method, adjust
):
    values = [-3, -1, 0, 0.2, 0.7, 2, 4]
    p = mp.plot({"x": values}).kde(
        "x", bw_method=method, bw_adjust=adjust, gridsize=31, cut=2
    )
    curve = summarize(p)[0]
    factor = (
        len(values) ** (-0.2)
        if method == "scott"
        else (len(values) * 0.75) ** (-0.2)
        if method == "silverman"
        else method
    )
    reference = GaussianKDE(values, bw_method=factor * adjust)
    bandwidth = float(np.sqrt(np.asarray(reference.covariance)[0, 0]))
    assert curve.bandwidth == pytest.approx(bandwidth, rel=3e-15)
    np.testing.assert_allclose(
        curve.support,
        np.linspace(min(values) - 2 * bandwidth, max(values) + 2 * bandwidth, 31),
        rtol=3e-15,
        atol=2e-15,
    )
    np.testing.assert_allclose(
        curve.heights, reference.evaluate(curve.support), rtol=6e-15, atol=2e-17
    )


@pytest.mark.parametrize("method", ["scott", "silverman", 0.6])
@pytest.mark.parametrize("cumulative", [False, True])
def test_weighted_analytic_covariance_effective_n_and_gaussian_mixture(
    method, cumulative
):
    x = np.array([-2, 0, 1, 5], dtype=float)
    w = np.array([1, 2, 4, 3], dtype=float)
    p = mp.plot({"x": x, "w": w}).kde(
        "x",
        weights="w",
        bw_method=method,
        bw_adjust=0.8,
        cut=1,
        gridsize=37,
        cumulative=cumulative,
    )
    curve = summarize(p)[0]
    q = w / w.sum()
    mean = np.dot(q, x)
    variance = np.dot(q, (x - mean) ** 2) / (1 - np.dot(q, q))
    effective_n = 1 / np.dot(q, q)
    factor = (
        effective_n ** (-0.2)
        if method == "scott"
        else (effective_n * 0.75) ** (-0.2)
        if method == "silverman"
        else method
    )
    h = math.sqrt(variance) * factor * 0.8
    assert curve.bandwidth == pytest.approx(h, rel=3e-15)
    reference = []
    for point in curve.support:
        if cumulative:
            reference.append(
                sum(
                    weight * NormalDist(mu, h).cdf(point)
                    for mu, weight in zip(x, q, strict=True)
                )
            )
        else:
            reference.append(
                sum(
                    weight * NormalDist(mu, h).pdf(point)
                    for mu, weight in zip(x, q, strict=True)
                )
            )
    np.testing.assert_allclose(curve.heights, reference, rtol=4e-15, atol=4e-17)
    if cumulative:
        assert curve.heights[0] > 0 and curve.heights[-1] < 1
        assert np.all(np.diff(curve.heights) >= 0)


@pytest.mark.parametrize("common_grid", [False, True])
@pytest.mark.parametrize("common_norm", [False, True])
def test_grouped_density_integrates_to_mass_share_or_one_on_shared_and_separate_grids(
    common_grid, common_norm
):
    p = mp.plot(sample()).kde(
        "x",
        group="g",
        weights="w",
        cut=8,
        gridsize=1001,
        common_grid=common_grid,
        common_norm=common_norm,
    )
    curves = summarize(p)
    np.testing.assert_allclose(
        [integral(c) for c in curves],
        [0.4, 0.6] if common_norm else [1, 1],
        rtol=2e-9,
        atol=2e-10,
    )
    if common_grid:
        assert curves[0].support == curves[1].support
    else:
        assert curves[0].support != curves[1].support


@pytest.mark.parametrize("common_norm", [False, True])
def test_cdf_is_full_gaussian_integral_not_grid_sum_or_rebased_visible_cdf(common_norm):
    p = mp.plot(sample()).kde(
        "x",
        group="g",
        weights="w",
        cumulative=True,
        common_norm=common_norm,
        common_grid=True,
        cut=8,
        gridsize=45,
    )
    curves = summarize(p)
    for curve, values, weights in zip(
        curves, ([0, 1, 3], [8, 9, 12]), ([1, 2, 1], [3, 1, 2]), strict=True
    ):
        assert curve.bandwidth is not None
        denominator = 10 if common_norm else sum(weights)
        expected = [
            math.fsum(
                w * 0.5 * math.erfc((v - t) / (curve.bandwidth * math.sqrt(2)))
                for v, w in zip(values, weights, strict=True)
            )
            / denominator
            for t in curve.support
        ]
        np.testing.assert_allclose(curve.heights, expected, rtol=4e-15, atol=1e-16)
        assert np.all(np.diff(curve.heights) >= 0)
    np.testing.assert_allclose(
        [c.heights[-1] for c in curves],
        [0.4, 0.6] if common_norm else [1, 1],
        atol=1e-14,
    )


def test_tiny_group_cdf_is_summed_directly_not_cancelled_from_a_pooled_one():
    p = mp.plot(
        {"x": [0, 1, 1000, 1001], "w": [1e100, 1e100, 1, 1], "g": ["A", "A", "B", "B"]}
    ).kde(
        "x",
        group="g",
        weights="w",
        common_grid=True,
        cut=0,
        gridsize=31,
        cumulative=True,
    )
    curve = summarize(p)[1]
    assert curve.bandwidth is not None
    expected = (
        sum(NormalDist(v, curve.bandwidth).cdf(1001) for v in (1000, 1001)) / 2e100
    )
    assert 0 < curve.heights[-1] < 1e-100
    assert curve.heights[-1] == pytest.approx(expected, rel=3e-15, abs=0)


def test_wide_weight_cdf_prefixes_are_monotone_in_normalized_range():
    rng = np.random.default_rng(51)
    for _ in range(10):
        p = mp.plot(
            {"x": rng.normal(size=61), "w": 10.0 ** rng.uniform(-100, 100, 61)}
        ).kde(
            "x",
            weights="w",
            cumulative=True,
            gridsize=31,
            cut=8,
        )
        heights = np.array(summarize(p)[0].heights)
        assert heights.min() >= 0 and heights.max() <= 1
        assert np.all(np.diff(heights) >= 0)


def test_cut_clip_only_change_evaluation_support_not_fit_rows_or_tail_normalization():
    values = [-5, -1, 0, 2, 8]
    p = mp.plot({"x": values}).kde("x", bw_method="scott", cut=8, gridsize=1001)
    q = mp.plot({"x": values}).kde(
        "x", bw_method="scott", cut=8, clip=[0, 1], gridsize=1001
    )
    a, b = summarize(p)[0], summarize(q)[0]
    assert a.bandwidth == b.bandwidth
    assert b.support[0] == 0 and b.support[-1] == 1
    assert integral(a) == pytest.approx(1, abs=1e-10) and 0 < integral(b) < 0.3
    reference = GaussianKDE(values, bw_method="scott")
    np.testing.assert_allclose(b.heights, reference(b.support), rtol=3e-15)
    c = summarize(
        mp.plot({"x": values}).kde("x", bw_method="scott", clip=[0, 1], cumulative=True)
    )[0]
    assert c.heights[0] > 0.2 and c.heights[-1] < 0.8  # not 0..1 conditional clip CDF


def test_common_grid_uses_pooled_support_but_keeps_conditional_bandwidth():
    raw = sample()
    p = mp.plot(raw).kde(
        "x", group="g", weights="w", common_grid=True, cut=2, gridsize=41
    )
    curves = summarize(p)
    pooled = summarize(mp.plot(raw).kde("x", weights="w", cut=2, gridsize=41))[0]
    assert curves[0].support == curves[1].support == pooled.support
    assert curves[0].bandwidth != curves[1].bandwidth
    assert all(c.bandwidth != pooled.bandwidth for c in curves)


def test_paired_missing_zero_weight_and_selected_hues_define_fit_and_mass():
    raw = {
        "x": [1, 2, 4, 8, None, -99, 1000, 3, False],
        "w": [1, 2, 3, 4, 10, 0, -1, None, 0],
        "g": ["A", "A", "B", "B", "A", "A", "omit", "A", "A"],
    }
    p = mp.plot(raw).kde(
        "x",
        weights="w",
        group="g",
        hue_order=["absent", "A", "B"],
        common_grid=True,
        cut=0,
    )
    curves = summarize(p)
    assert curves[0].support == () and not curves[0].singular
    pooled = summarize(
        mp.plot({"x": [1, 2, 4, 8], "w": [1, 2, 3, 4]}).kde("x", weights="w", cut=0)
    )[0]
    assert curves[1].support == curves[2].support == pooled.support
    assert p.render().axes[0].get_legend_handles_labels()[1] == ["A", "B"]


@pytest.mark.parametrize("raw", [{"x": []}, {"x": [None]}, {"x": [1, 2], "w": [0, 0]}])
def test_empty_groups_have_no_artists_warning_or_legend(raw):
    p = mp.plot(raw).kde(
        "x", weights="w" if "w" in raw else None, bw_method="scott", label="empty"
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ax = p.render().axes[0]
    assert caught == [] and not ax.lines and not ax.collections
    assert ax.get_legend_handles_labels() == ([], [])


@pytest.mark.parametrize("values", [[3], [3, 3, 3]])
@pytest.mark.parametrize("cumulative", [False, True])
def test_singular_curves_skip_without_fake_gaussian_or_cdf(values, cumulative):
    p = mp.plot({"x": values}).kde(
        "x", bw_method="scott", cumulative=cumulative, label="singular"
    )
    curve = summarize(p)[0]
    assert curve.singular and curve.bandwidth is None and not curve.support
    with pytest.warns(UserWarning, match="KDE skipped singular"):
        ax = p.render().axes[0]
    assert not ax.lines and not ax.collections and not ax.get_legend_handles_labels()[0]
    q = mp.plot({"x": values}).kde("x", warn_singular=False)
    with warnings.catch_warnings(record=True) as caught:
        q.render()
    assert not caught


def test_singular_hue_retains_usable_mass_in_common_denominator():
    raw = {"x": [-1, 0, 2, 5, 5], "w": [1, 2, 1, 3, 3], "g": ["A"] * 3 + ["B"] * 2}
    p = mp.plot(raw).kde(
        "x",
        weights="w",
        group="g",
        common_norm=True,
        warn_singular=False,
        cut=8,
        gridsize=1001,
    )
    curves = summarize(p)
    assert integral(curves[0]) == pytest.approx(0.4, abs=1e-10) and curves[1].singular
    assert p.render().axes[0].get_legend_handles_labels()[1] == ["A"]


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("fill", [False, True])
@pytest.mark.parametrize("alpha", [0, 1, 0.45])
def test_primary_native_line_or_filled_geometry_and_exact_alpha_outline_width(
    orient, fill, alpha
):
    p = mp.plot({"x": [1, 2, 4, 8]}).kde(
        "x",
        orient=orient,
        fill=fill,
        gridsize=31,
        cut=0,
        alpha=alpha,
        line_width=0,
        line_style=":",
        edge_color="#123456" if fill else None,
    )
    curve = summarize(p)[0]
    ax = p.render().axes[0]
    expected = np.column_stack((curve.support, curve.heights))
    if orient == "h":
        expected = expected[:, ::-1]
    if fill:
        body = cast(PolyCollection, ax.collections[0])
        assert (
            body.get_alpha() == alpha
            and np.asarray(body.get_linewidth()).ravel()[0] == 0
        )
        assert not ax.lines
        vertices = body.get_paths()[0].vertices
        for point in expected:
            assert np.any(np.all(vertices == point, axis=1))
        np.testing.assert_allclose(
            np.asarray(body.get_edgecolor(), dtype=float)[0], to_rgba("#123456", alpha)
        )
    else:
        line = ax.lines[0]
        assert (
            line.get_alpha() == alpha
            and line.get_linewidth() == 0
            and not line.get_visible()
        )
        np.testing.assert_array_equal(
            np.column_stack((line.get_xdata(), line.get_ydata())), expected
        )
    ax.figure.canvas.draw()


@pytest.mark.parametrize("fill", [False, True])
def test_hue_order_reserves_dash_or_hatch_and_color_slots_even_with_empty_hues(fill):
    raw = sample()
    full = mp.plot(raw).kde("x", group="g", hue_order=["A", "B"], fill=fill, cut=0)
    partial = mp.plot(raw).kde(
        "x", group="g", hue_order=["absent", "B"], fill=fill, cut=0
    )
    a, b = full.render().axes[0], partial.render().axes[0]
    if fill:
        ca, cb = (
            cast(PolyCollection, a.collections[1]),
            cast(PolyCollection, b.collections[0]),
        )
        np.testing.assert_array_equal(ca.get_facecolor(), cb.get_facecolor())
        assert ca.get_hatch() == cb.get_hatch() and cb.get_hatch()
    else:
        assert a.lines[1].get_color() == b.lines[0].get_color()
        assert a.lines[1].get_linestyle() == b.lines[0].get_linestyle()
    assert b.get_legend_handles_labels()[1] == ["B"]


@pytest.mark.parametrize("orient", ["v", "h"])
def test_observation_logs_keep_raw_density_and_reversed_limits(orient):
    values = [1, 2, 4, 8]
    p = mp.plot({"x": values}).kde("x", bw_method="scott", orient=orient, cut=0)
    (p.xscale if orient == "v" else p.yscale)("log")
    (p.xlim if orient == "v" else p.ylim)(10, 0.5)
    curve = summarize(p)[0]
    ax = p.render().axes[0]
    line = ax.lines[0]
    np.testing.assert_array_equal(
        line.get_xdata() if orient == "v" else line.get_ydata(), curve.support
    )
    np.testing.assert_allclose(
        curve.heights, GaussianKDE(values, bw_method="scott")(curve.support), rtol=3e-15
    )
    assert ax.xaxis_inverted() if orient == "v" else ax.yaxis_inverted()


@pytest.mark.parametrize("orient", ["v", "h"])
def test_log_support_crossing_zero_fails_and_explicit_positive_clip_works(
    orient,
):
    p = mp.plot({"x": [1, 2, 4, 8]}).kde("x", bw_method="scott", orient=orient)
    (p.xscale if orient == "v" else p.yscale)("log")
    assert mp.validate(p.spec) == []
    with pytest.raises(ValueError, match="derived log KDE support"):
        p.render()
    q = mp.plot({"x": [1, 2, 4, 8]}).kde(
        "x", bw_method="scott", orient=orient, clip=[0.1, None]
    )
    (q.xscale if orient == "v" else q.yscale)("log")
    q.render()
    r = mp.plot({"x": [1, 2, 4, 8]}).kde(
        "x", bw_method="scott", orient=orient, clip=[0, 10]
    )
    (r.xscale if orient == "v" else r.yscale)("log")
    assert any(
        "log clip bounds must be positive" in issue for issue in mp.validate(r.spec)
    )


@pytest.mark.parametrize("orient", ["v", "h"])
def test_log_density_axis_and_nonpositive_observations_rejected(orient):
    p = mp.plot({"x": [1, 2]}).kde("x", bw_method="scott", orient=orient)
    (p.yscale if orient == "v" else p.xscale)("log")
    assert any("density/CDF axis must be linear" in i for i in mp.validate(p.spec))
    q = mp.plot({"x": [0, 1]}).kde("x", bw_method="scott", orient=orient, cut=0)
    (q.xscale if orient == "v" else q.yscale)("log")
    assert any("log observations must be positive" in i for i in mp.validate(q.spec))


def test_scaled_huge_weights_and_dominant_weight_covariance_remain_finite():
    a = summarize(mp.plot({"x": [-1, 0, 2], "w": [1e308] * 3}).kde("x", weights="w"))[0]
    b = summarize(mp.plot({"x": [-1, 0, 2]}).kde("x", bw_method="scott"))[0]
    assert a.bandwidth == b.bandwidth and a.heights == b.heights
    c = summarize(mp.plot({"x": [0, 1], "w": [1e308, 1]}).kde("x", weights="w", cut=0))[
        0
    ]
    assert c.bandwidth == pytest.approx(1 / math.sqrt(2), rel=2e-15)
    assert all(math.isfinite(v) for v in c.heights)


def test_relative_weights_are_scale_invariant_but_not_replication_weights():
    values = [0, 2, 5]
    a = summarize(mp.plot({"x": values, "w": [1, 2, 3]}).kde("x", weights="w"))[0]
    b = summarize(
        mp.plot({"x": values, "w": [1e100, 2e100, 3e100]}).kde("x", weights="w")
    )[0]
    c = summarize(mp.plot({"x": [0, 2, 2, 5, 5, 5]}).kde("x", bw_method="scott"))[0]
    assert a.bandwidth == pytest.approx(b.bandwidth, rel=2e-15)
    np.testing.assert_allclose(a.heights, b.heights, rtol=3e-15)
    assert a.bandwidth != pytest.approx(c.bandwidth, rel=1e-4)


def test_neighboring_huge_values_keep_covariance_low_bits_and_support_resolves():
    a = 1e308
    b = float(np.nextafter(a, math.inf))
    curve = summarize(mp.plot({"x": [a, b]}).kde("x", bw_method=1000, gridsize=31))[0]
    assert curve.bandwidth == pytest.approx((b - a) / math.sqrt(2) * 1000, rel=2e-15)
    assert all(
        x < y for x, y in zip(curve.support[:-1], curve.support[1:], strict=True)
    )
    assert all(math.isfinite(y) and y >= 0 for y in curve.heights)


def test_large_support_finite_clip_rescues_expansion_without_density_divisor_overflow():
    p = mp.plot({"x": [-1e308, 1e308]}).kde("x", bw_method=1, clip=[-1, 1], gridsize=3)
    curve = summarize(p)[0]
    assert curve.bandwidth == pytest.approx(math.sqrt(2) * 1e308, rel=3e-15)
    expected = math.exp(-0.25) / math.sqrt(2 * math.pi) / (math.sqrt(2) * 1e308)
    np.testing.assert_allclose(curve.heights, expected, rtol=3e-15, atol=0)
    assert all(v > 0 for v in curve.heights)


def test_scale_product_does_not_underflow_before_a_large_scale_recovers_bandwidth():
    p = mp.plot({"x": [-1e308, 1e308]}).kde(
        "x",
        bw_method=1e-300,
        bw_adjust=1e-300,
        cut=0,
        clip=[-1, 1],
        gridsize=3,
        cumulative=True,
    )
    curve = summarize(p)[0]
    assert curve.bandwidth == pytest.approx(math.sqrt(2) * 1e-292, rel=3e-15)
    np.testing.assert_allclose(curve.heights, 0.5, atol=0)


@pytest.mark.parametrize("cumulative", [False, True])
def test_chunked_evaluation_and_row_permutation_have_no_sampling_or_large_matrix(
    monkeypatch, cumulative
):
    import mudplot._kde as backend

    rng = np.random.default_rng(12)
    x = rng.normal(size=51)
    w = np.exp(rng.normal(size=51))
    p = mp.plot({"x": x, "w": w}).kde(
        "x", weights="w", gridsize=31, cumulative=cumulative
    )
    reference = summarize(p)[0]
    monkeypatch.setattr(backend, "_EVALUATION_CHUNK", 7)
    result = summarize(p)[0]
    np.testing.assert_array_equal(result.heights, reference.heights)
    perm = rng.permutation(len(x))
    permuted = summarize(
        mp.plot({"x": x[perm], "w": w[perm]}).kde(
            "x", weights="w", gridsize=31, cumulative=cumulative
        )
    )[0]
    assert result == permuted
    if cumulative:
        assert (
            np.all(np.diff(result.heights) >= 0)
            and 0 <= min(result.heights) <= max(result.heights) <= 1
        )
    else:
        lengths = []
        original = np.exp

        def checked(values):
            lengths.append(len(values))
            assert values.ndim == 1 and len(values) <= 7
            return original(values)

        monkeypatch.setattr(np, "exp", checked)
        summarize(p)
        assert lengths and max(lengths) == 7


@pytest.mark.parametrize(
    "options,match",
    [
        ({"bw_method": "bad"}, "bw_method must be"),
        ({"bw_method": []}, "bw_method must be"),
        ({"bw_method": True}, "bw_method must be"),
        ({"bw_method": 0}, "bw_method must be"),
        ({"bw_adjust": 0}, "bw_adjust must be"),
        ({"bw_adjust": float("inf")}, "bw_adjust must be"),
        ({"bw_adjust": True}, "bw_adjust must be"),
        ({"gridsize": True}, "gridsize must be"),
        ({"gridsize": 1}, "gridsize must be"),
        ({"gridsize": 4097}, "gridsize must be"),
        ({"cut": -1}, "cut must be"),
        ({"cut": 11}, "cut must be"),
        ({"cut": True}, "cut must be"),
        ({"clip": [0]}, "clip must be"),
        ({"clip": [2, 1]}, "clip must be"),
        ({"clip": [float("inf"), None]}, "clip must be"),
        ({"clip": [False, 2]}, "clip must be"),
        ({"common_norm": 1}, "common_norm must be boolean"),
        ({"common_grid": 1}, "common_grid must be boolean"),
        ({"cumulative": 0}, "cumulative must be boolean"),
        ({"fill": 0}, "fill must be boolean"),
        ({"warn_singular": 1}, "warn_singular must be boolean"),
        ({"weights": "missing"}, "column 'missing'"),
        ({"weights": []}, "weights must be a nonempty"),
        ({"orient": "horizontal"}, "orient must be"),
        ({"hue_order": ["A"]}, "hue_order requires group"),
        ({"group": "g", "hue_order": ["A", "A"]}, "levels must be unique"),
        ({"edge_color": "red"}, "edge_color requires fill=True"),
        ({"fill": True, "edge_color": "bad"}, "edge_color must be"),
        ({"line_style": "bad"}, "line_style must be"),
        ({"line_width": -1}, "line_width must be"),
    ],
)
def test_bad_options_fail_pure_validation_without_ignored_controls(options, match):
    p = mp.plot({"x": [1, 2, 3], "g": ["A"] * 3}).kde(
        "x", **{"bw_method": "scott", **options}
    )
    assert any(match in issue for issue in mp.validate(p.spec))


@pytest.mark.parametrize("value", [True, "1", float("inf"), 10**400])
def test_invalid_selected_observations_rejected(value):
    p = mp.plot({"x": [1, value]}).kde("x", bw_method="scott")
    assert any("observations must be finite numeric" in i for i in mp.validate(p.spec))


@pytest.mark.parametrize("weight", [True, False, -1, "2", float("inf"), 10**400])
def test_invalid_selected_weights_rejected_including_false_not_valid_zero(weight):
    p = mp.plot({"x": [1, 2], "w": [1, weight]}).kde("x", weights="w")
    assert any("weights must be finite nonnegative" in i for i in mp.validate(p.spec))


@pytest.mark.parametrize(
    "style",
    [
        {"stack": True},
        {"stat_scale": "axis"},
        {"native_scale": True},
        {"order": [1, 2]},
        {"ecdf": mp.ECDFSpec()},
        {"histogram": mp.HistogramSpec()},
        {"y": "other"},
        {"marker": "o"},
        {"bins": 30},
        {"common_norm": True, "kde": mp.KDESpec()},
    ],
)
def test_unsupported_flat_fields_or_duplicate_config_cannot_be_silently_ignored(style):
    if "kde" in style:
        with pytest.raises(ValueError, match="not both"):
            mp.plot({"x": [1, 2]}).kde("x", **style)
    else:
        p = mp.plot({"x": [1, 2], "other": [2, 3]}).kde("x", bw_method="scott", **style)
        assert any("not supported" in i for i in mp.validate(p.spec))


@pytest.mark.parametrize(
    "raw,options,match",
    [
        ({"x": [0, 1]}, {"clip": [4, 5]}, "support is empty"),
        ({"x": [-1e308, 1e308]}, {"bw_method": 1, "cut": 3}, "support must be finite"),
        ({"x": [-1e308, 1e308]}, {"bw_method": 1000}, "bandwidth must be"),
        (
            {"x": [1e308, float(np.nextafter(1e308, math.inf))]},
            {"cut": 0},
            "grid must be",
        ),
        (
            {"x": [0, 1], "w": [1e308, 1e-300]},
            {"weights": "w"},
            "cannot resolve positive",
        ),
        (
            {"x": [0, 1e-310]},
            {"bw_method": 1e-10, "cut": 0},
            "density/CDF must be finite",
        ),
    ],
)
def test_nonfinite_or_unresolvable_derived_quantities_fail_before_any_kde_artist(
    raw, options, match
):
    p = mp.plot(raw).kde("x", **{"bw_method": "scott", "cut": 0, **options})
    assert mp.validate(p.spec) == []
    with pytest.raises(ValueError, match=match):
        p.render()


def test_legacy_equations_constant_fallback_and_old_json_default_behavior_preserved():
    values = [-2, -1, 0, 1, 4]
    p = mp.plot({"x": values}).kde("x")
    assert p.spec.panels[0].layers[0].kde is None
    line = p.render().axes[0].lines[0]
    h = 1.06 * np.std(values, ddof=1) * len(values) ** (-0.2)
    grid = np.linspace(min(values) - 3 * h, max(values) + 3 * h, 200)
    expected = np.exp(-0.5 * ((grid[:, None] - values) / h) ** 2).sum(axis=1) / (
        len(values) * h * np.sqrt(2 * np.pi)
    )
    np.testing.assert_array_equal(line.get_xdata(), grid)
    np.testing.assert_array_equal(line.get_ydata(), expected)
    legacy = p.spec.to_dict()
    del legacy["panels"][0]["layers"][0]["kde"]
    assert mp.FigureSpec.from_dict(legacy).panels[0].layers[0].kde is None
    ax = mp.plot({"x": [2, 2]}).kde("x").render().axes[0]
    assert len(ax.lines) == 1 and np.asarray(ax.lines[0].get_xdata()).size == 200


def test_wrong_layer_flat_legacy_styles_shared_ordinal_and_projection_contracts():
    p = mp.plot({"x": [1, 2]}).ecdf("x", kde=mp.KDESpec())
    assert any("kde is not supported" in i for i in mp.validate(p.spec))
    p = mp.plot({"x": [1, 2]}).dispatch(
        A.AddLayer(LayerSpec(type="kde", x="x", orient="h"))
    )
    assert any("options require KDESpec" in i for i in mp.validate(p.spec))
    p = (
        mp.plot({"x": [1, 2], "c": [1, 2]})
        .kde("x", bw_method="scott")
        .barplot("c", "x", errorbar=None)
    )
    assert any("cannot mix ordinal" in i for i in mp.validate(p.spec))
    q = (
        mp.plot({"x": [1, 2], "c": [1, 2]})
        .kde("x", bw_method="scott")
        .barplot("c", "x", native_scale=True, errorbar=None)
    )
    assert mp.validate(q.spec) == []
    r = (
        mp.plot({"x": [1, 2]})
        .kde("x", bw_method="scott", axis="y2")
        .secondary_yaxis("second")
    )
    assert any("axis='y2' is not supported" in i for i in mp.validate(r.spec))
    assert any(
        "polar" in i
        for i in mp.validate(
            mp.plot({"x": [1, 2]}).kde("x", bw_method="scott").projection_polar().spec
        )
    )


def test_tuple_clip_is_canonical_and_explicit_typed_config_allows_geometry_styles():
    p = mp.plot({"x": [1, 2, 4]}).kde("x", clip=(0.1, None), bw_method="scott")
    config = p.spec.panels[0].layers[0].kde
    assert config is not None and config.clip == [0.1, None]
    assert mp.Plot.from_json(p.to_json()).spec == p.spec
    assert mp.apply(p.action_log) == p.spec
    q = mp.plot({"x": [1, 2, 4]}).kde(
        "x",
        kde=KDESpec(fill=True),
        orient="h",
        edge_color="#123456",
    )
    assert mp.validate(q.spec) == []
    assert len(q.render().axes[0].collections) == 1


def test_typed_json_action_schema_and_editor_contract_unknown_fields_rejected():
    import jsonschema
    from dashboard.editor_server import EditorSession, _build_action

    p = mp.plot(sample()).kde(
        "x",
        weights="w",
        bw_method="silverman",
        bw_adjust=0.8,
        gridsize=51,
        common_grid=True,
        clip=[None, 13],
        group="g",
        hue_order=["B", "A"],
        cumulative=True,
        fill=True,
        orient="h",
    )
    assert isinstance(p.spec.panels[0].layers[0].kde, KDESpec)
    assert (
        mp.Plot.from_json(p.to_json()).spec == p.spec
        and mp.apply(p.action_log) == p.spec
    )
    jsonschema.validate(p.spec.to_dict(), mp.json_schema())
    assert mp.json_schema()["$defs"]["KDESpec"]["additionalProperties"] is False
    raw = p.spec.to_dict()
    raw["panels"][0]["layers"][0]["kde"]["kernel"] = "epanechnikov"
    with pytest.raises(ValueError, match="unknown KDESpec"):
        mp.FigureSpec.from_dict(raw)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(raw, mp.json_schema())
    invalid = p.spec
    invalid.panels[0].layers[0].kde = cast(Any, {"fill": True})
    assert any("kde must be KDESpec" in i for i in mp.validate(invalid))
    session = EditorSession()
    session.dispatch_safe(A.SetData(sample()))
    session.dispatch_safe(
        _build_action(
            "add_layer_json",
            {
                "layer_type": "kde",
                "layer_json": json.dumps(
                    {"x": "x", "kde": {"weights": "w", "fill": True}}
                ),
            },
            session.store.state,
        )
    )
    assert session.error is None and session.png.startswith(b"\x89PNG")
    assert b"<svg" in session.export("svg")
    with pytest.raises(ValueError, match="unknown KDESpec"):
        _build_action(
            "add_layer_json",
            {"layer_type": "kde", "layer_json": '{"x":"x","kde":{"kernel":"custom"}}'},
            session.store.state,
        )


@pytest.mark.parametrize("fmt", ["png", "svg", "pdf"])
@pytest.mark.parametrize("fill", [False, True])
def test_exports_and_legend_reference_metadata_are_reproducible_without_rng_mutation(
    tmp_path, fmt, fill
):
    p = (
        mp.plot(sample())
        .kde(
            "x",
            group="g",
            weights="w",
            fill=fill,
            bw_method="scott",
            alpha=0.6,
            line_width=1,
            references={
                "B": mp.Reference(href="https://example.org/b", citation="smith2026")
            },
        )
        .size(4, 3)
    )
    before = np.random.get_state()
    a, b = tmp_path / f"a.{fmt}", tmp_path / f"b.{fmt}"
    plt.close(p.save(str(a)))
    plt.close(mp.Plot.from_json(p.to_json()).save(str(b)))
    assert a.read_bytes() == b.read_bytes()
    if fmt == "svg":
        assert "https://example.org/b" in a.read_text(encoding="utf-8")
    after = np.random.get_state()
    assert before[0] == after[0] and before[2:] == after[2:]
    np.testing.assert_array_equal(before[1], after[1])
