"""Weighted 2-D Gaussian equations, conditional HDR quadrature, native contours."""

from __future__ import annotations

import json
import math
import warnings
from itertools import pairwise
from typing import Any, cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.container import BarContainer
from matplotlib.lines import Line2D
from matplotlib.mlab import GaussianKDE
from mudplot import actions as A
from mudplot._kde2d import conditional_levels, kde2d_summary
from mudplot.spec import LayerSpec


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def sample():
    return {
        "x": [-2, -1, 0, 0.5, 2, 3],
        "y": [1, -1, 2, 0.7, 4, 1],
        "w": [1, 2, 4, 1, 2, 3],
    }


def fields(p):
    assert mp.validate(p.spec) == []
    return kde2d_summary(p.spec.data.columns, p.spec.panels[0].layers[0])


def trapezoid_weights(grid):
    g = np.array(grid)
    dx = np.diff(g)
    return np.r_[dx[0] / 2, (dx[:-1] + dx[1:]) / 2, dx[-1] / 2]


def integrate(field):
    return float(
        np.sum(
            np.array(field.density)
            * np.outer(trapezoid_weights(field.y), trapezoid_weights(field.x))
        )
    )


@pytest.mark.parametrize("method", ["scott", "silverman", 0.6])
@pytest.mark.parametrize("adjust", [0.7, 1.4])
def test_full_weighted_covariance_and_pdf_match_independent_matrix_equations(
    method, adjust
):
    raw = sample()
    x = np.column_stack((raw["x"], raw["y"]))
    w = np.array(raw["w"], dtype=float)
    q = w / w.sum()
    mean = q @ x
    covariance = (x - mean).T @ (q[:, None] * (x - mean)) / (1 - np.dot(q, q))
    factor = (1 / np.dot(q, q)) ** (-1 / 6) if isinstance(method, str) else method
    kernel = covariance * (factor * adjust) ** 2
    p = mp.plot(raw).kde2d(
        "x",
        "y",
        weights="w",
        bw_method=method,
        bw_adjust=adjust,
        gridsize=31,
        levels=[0.5, 0.9],
    )
    field = fields(p)[0]
    assert field.bandwidths is not None and field.correlation is not None
    np.testing.assert_allclose(field.bandwidths, np.sqrt(np.diag(kernel)), rtol=5e-15)
    assert field.correlation == pytest.approx(
        kernel[0, 1] / np.sqrt(kernel[0, 0] * kernel[1, 1]), rel=5e-15
    )
    gx, gy = np.meshgrid(field.x, field.y)
    points = np.column_stack((gx.ravel(), gy.ravel()))
    delta = points[:, None, :] - x[None, :, :]
    energy = np.einsum("pni,ij,pnj->pn", delta, np.linalg.inv(kernel), delta)
    expected = (np.exp(-0.5 * energy) @ q) / (
        2 * math.pi * np.sqrt(np.linalg.det(kernel))
    )
    np.testing.assert_allclose(
        field.density, expected.reshape(gx.shape), rtol=8e-14, atol=3e-17
    )
    assert field.grid_mass == pytest.approx(integrate(field), rel=4e-15)


@pytest.mark.parametrize("method", ["scott", "silverman", 0.6])
def test_unweighted_gaussian_matches_native_multivariate_reference(method):
    raw = sample()
    p = mp.plot(raw).kde2d("x", "y", bw_method=method, gridsize=29, levels=[0.5, 0.9])
    field = fields(p)[0]
    grid = np.meshgrid(field.x, field.y)
    native = GaussianKDE(np.array([raw["x"], raw["y"]]), bw_method=method)
    expected = native(np.array([g.ravel() for g in grid])).reshape(
        len(field.y), len(field.x)
    )
    np.testing.assert_allclose(field.density, expected, rtol=8e-14, atol=3e-17)


def test_d2_scott_silverman_coincide_but_d1_rules_and_legacy_are_unchanged():
    raw = sample()
    a = fields(mp.plot(raw).kde2d("x", "y", bw_method="scott", gridsize=25))[0]
    b = fields(mp.plot(raw).kde2d("x", "y", bw_method="silverman", gridsize=25))[0]
    assert a == b
    from mudplot._kde import kde_summary

    p = mp.plot(raw).kde("x", bw_method="scott")
    q = mp.plot(raw).kde("x", bw_method="silverman")
    assert (
        kde_summary(p.spec.data.columns, p.spec.panels[0].layers[0])[0].bandwidth
        != kde_summary(q.spec.data.columns, q.spec.panels[0].layers[0])[0].bandwidth
    )
    assert mp.plot(raw).kde("x").spec.panels[0].layers[0].kde is None


@pytest.mark.parametrize("size", [81, 161])
def test_conditional_hdr_gaussian_thresholds_converge_and_enclose_ties(size):
    grid = np.linspace(-5, 5, size)
    x, y = np.meshgrid(grid, grid)
    density = np.exp(-0.5 * (x * x + y * y)) / (2 * math.pi)
    heights, enclosed, mass = conditional_levels(grid, grid, density, [0.5, 0.8, 0.95])
    np.testing.assert_allclose(
        heights, (1 - np.array([0.95, 0.8, 0.5])) / (2 * math.pi), rtol=0.025
    )
    for actual, target in zip(enclosed, [0.95, 0.8, 0.5], strict=True):
        assert target <= actual <= target + 0.015
    expected = float(
        np.sum(density * np.outer(trapezoid_weights(grid), trapezoid_weights(grid)))
    )
    assert mass == pytest.approx(expected, rel=5e-15)
    # The selected region includes ALL points tied exactly at the threshold.
    node_mass = density * np.outer(trapezoid_weights(grid), trapezoid_weights(grid))
    for height, actual in zip(heights, enclosed, strict=True):
        assert node_mass[density >= height].sum() / node_mass.sum() == pytest.approx(
            actual, rel=4e-15
        )


def test_clipped_hdr_is_conditional_on_visible_grid_not_full_space_or_confidence_ci():
    grid = np.linspace(-2, 2, 161)
    x, y = np.meshgrid(grid, grid)
    density = np.exp(-0.5 * (x * x + y * y)) / (2 * math.pi)
    thresholds, enclosed, mass = conditional_levels(grid, grid, density, [0.5])
    assert mass < 0.92 and enclosed[0] >= 0.5
    assert thresholds[0] == pytest.approx((1 - 0.5 * mass) / (2 * math.pi), rel=0.012)
    assert thresholds[0] != (1 - 0.5) / (2 * math.pi)


def test_independent_discrete_hdr_strata_and_trapezoid_node_mass_equations():
    grid = np.linspace(-3, 3, 15)
    x, y = np.meshgrid(grid, grid)
    density = np.exp(-0.5 * (x * x + y * y)) / (2 * math.pi)
    levels = [0.4, 0.8]
    thresholds, actual, mass = conditional_levels(grid, grid, density, levels)
    areas = np.outer(trapezoid_weights(grid), trapezoid_weights(grid))
    strata = sorted(set(density.ravel()), reverse=True)
    cumulative = 0
    expected = []
    covered = []
    target = iter(levels)
    fraction = next(target)
    for height in strata:
        cumulative += float(
            np.sum(density[density == height] * areas[density == height])
        )
        while cumulative / mass >= fraction:
            expected.append(height)
            covered.append(cumulative / mass)
            fraction = next(target, math.inf)
    np.testing.assert_array_equal(thresholds, expected[::-1])
    np.testing.assert_allclose(actual, covered[::-1], rtol=3e-15)


@pytest.mark.parametrize("common_grid", [False, True])
@pytest.mark.parametrize("common_norm", [False, True])
def test_grouped_density_integral_and_conditional_geometry_normalization(
    common_grid, common_norm
):
    raw = sample()
    raw = {key: values + values for key, values in raw.items()}
    raw["x"][6:] = [v + 6 for v in raw["x"][6:]]
    raw["g"] = ["A"] * 6 + ["B"] * 6
    raw["w"][6:] = [3 * v for v in raw["w"][6:]]
    p = mp.plot(raw).kde2d(
        "x",
        "y",
        group="g",
        weights="w",
        cut=7,
        gridsize=81,
        levels=[0.5, 0.9],
        common_grid=common_grid,
        common_norm=common_norm,
    )
    a, b = fields(p)
    np.testing.assert_allclose(
        [integrate(a), integrate(b)], [0.25, 0.75] if common_norm else [1, 1], atol=1e-8
    )
    assert (a.x == b.x and a.y == b.y) == common_grid
    independent = fields(
        mp.plot(raw).kde2d(
            "x",
            "y",
            group="g",
            weights="w",
            cut=7,
            gridsize=81,
            levels=[0.5, 0.9],
            common_grid=common_grid,
            common_norm=not common_norm,
        )
    )
    for first, second in zip((a, b), independent, strict=True):
        assert first.enclosed_mass == pytest.approx(second.enclosed_mass, rel=5e-15)
        assert first.requested_mass == second.requested_mass
        ratio = float(np.max(first.density)) / float(np.max(second.density))
        np.testing.assert_allclose(
            first.thresholds, np.array(second.thresholds) * ratio, rtol=5e-15
        )


def test_common_grid_uses_pooled_fit_support_but_conditional_covariance_is_retained():
    raw = sample()
    raw = {key: values + values for key, values in raw.items()}
    raw["x"][6:] = [v * 2 + 5 for v in raw["x"][6:]]
    raw["g"] = ["A"] * 6 + ["B"] * 6
    a, b = fields(
        mp.plot(raw).kde2d(
            "x",
            "y",
            group="g",
            weights="w",
            common_grid=True,
            gridsize=35,
            levels=[0.5, 0.9],
        )
    )
    pooled = fields(
        mp.plot(raw).kde2d("x", "y", weights="w", gridsize=35, levels=[0.5, 0.9])
    )[0]
    assert a.x == b.x == pooled.x and a.y == b.y == pooled.y
    assert a.bandwidths != b.bandwidths and a.bandwidths != pooled.bandwidths


def test_cut_and_clip_restrict_grid_only_not_covariance_or_density_normalization():
    raw = sample()
    a = fields(
        mp.plot(raw).kde2d("x", "y", weights="w", cut=6, gridsize=61, levels=[0.5])
    )[0]
    b = fields(
        mp.plot(raw).kde2d(
            "x",
            "y",
            weights="w",
            cut=6,
            clip=((-1, 1), (0, 2)),
            gridsize=61,
            levels=[0.5],
        )
    )[0]
    assert a.bandwidths == b.bandwidths and a.correlation == b.correlation
    assert b.x[0] == -1 and b.x[-1] == 1 and b.y[0] == 0 and b.y[-1] == 2
    assert a.grid_mass == pytest.approx(1, abs=1e-8) and b.grid_mass < 0.4
    canonical = mp.plot(raw).kde2d("x", "y", clip=((-1, 1), (0, 2)), levels=(0.5, 0.9))
    config = canonical.spec.panels[0].layers[0].kde2d
    assert config is not None and config.clip == [[-1, 1], [0, 2]]
    assert mp.Plot.from_json(canonical.to_json()).spec == canonical.spec


def test_x_y_weight_hue_missing_and_zero_rows_are_listwise_before_log_positivity():
    raw = {
        "x": [1, 2, 4, 3, None, 1, -1, False, 100],
        "y": [1, 4, 2, 3, 2, None, -1, False, 200],
        "w": [1, 2, 1, 3, 1, 1, 0, 0, -1],
        "g": ["A"] * 8 + ["omit"],
    }
    p = mp.plot(raw).kde2d(
        "x",
        "y",
        weights="w",
        group="g",
        hue_order=["empty", "A"],
        cut=0,
        gridsize=35,
        levels=[0.5],
    )
    a, b = fields(p)
    assert not a.x and not a.singular
    p.xscale("log").yscale("log")
    assert mp.validate(p.spec) == []
    reference = fields(
        mp.plot({"x": [1, 2, 4, 3], "y": [1, 4, 2, 3], "w": [1, 2, 1, 3]}).kde2d(
            "x", "y", weights="w", cut=0, gridsize=35, levels=[0.5]
        )
    )[0]
    assert b.density == reference.density and b.bandwidths == reference.bandwidths
    assert p.render().axes[0].get_legend_handles_labels()[1] == ["A"]


@pytest.mark.parametrize(
    "raw",
    [
        {"x": [], "y": []},
        {"x": [None], "y": [1]},
        {"x": [1, 2], "y": [2, 3], "w": [0, 0]},
    ],
)
def test_empty_inputs_have_no_fake_density_artists_warning_or_legend(raw):
    p = mp.plot(raw).kde2d("x", "y", weights="w" if "w" in raw else None, label="empty")
    with warnings.catch_warnings(record=True) as caught:
        ax = p.render().axes[0]
    assert not caught and not ax.collections and not ax.lines
    assert ax.get_legend_handles_labels() == ([], [])


@pytest.mark.parametrize(
    "raw",
    [
        {"x": [1], "y": [2]},
        {"x": [1, 2], "y": [1, 3]},
        {"x": [1, 1, 1], "y": [1, 2, 3]},
        {"x": [1, 2, 3], "y": [1, 1, 1]},
        {"x": [1, 2, 3, 4], "y": [2, 4, 6, 8]},
    ],
)
def test_rank_deficient_groups_skip_without_jitter_fake_fit_or_legend(raw):
    p = mp.plot(raw).kde2d("x", "y", label="singular")
    field = fields(p)[0]
    assert field.singular and not field.density and field.bandwidths is None
    with pytest.warns(UserWarning, match="KDE2D skipped singular"):
        ax = p.render().axes[0]
    assert not ax.collections and not ax.lines and not ax.get_legend_handles_labels()[0]
    with warnings.catch_warnings(record=True) as caught:
        mp.plot(raw).kde2d("x", "y", warn_singular=False).render()
    assert not caught


def test_singular_hue_mass_stays_in_common_denominator():
    raw = sample()
    raw = {key: [*values, 1, 2] for key, values in raw.items()}
    raw["g"] = ["A"] * 6 + ["B"] * 2
    raw["w"][-2:] = [13, 13]
    a, b = fields(
        mp.plot(raw).kde2d(
            "x",
            "y",
            weights="w",
            group="g",
            warn_singular=False,
            cut=7,
            gridsize=81,
            levels=[0.5, 0.9],
        )
    )
    assert b.singular and not b.x
    assert a.grid_mass == pytest.approx(1 / 3, abs=1e-8)


@pytest.mark.parametrize("fill", [False, True])
@pytest.mark.parametrize("alpha", [0, 1, 0.45])
@pytest.mark.parametrize("width", [0, 2])
def test_native_contours_fill_exact_alpha_width_and_legend_only_proxies(
    fill, alpha, width
):
    p = mp.plot(sample()).kde2d(
        "x",
        "y",
        fill=fill,
        alpha=alpha,
        line_width=width,
        line_style=":",
        gridsize=29,
        levels=[0.5, 0.9],
        label="joint",
        edge_color="#123456" if fill else None,
    )
    field = fields(p)[0]
    ax = p.render().axes[0]
    assert ax.get_legend_handles_labels()[1] == ["joint"]
    legend = ax.get_legend()
    assert legend is not None and legend.get_texts()[0].get_text() == "joint"
    for collection in ax.collections:
        assert collection.get_alpha() == alpha
        assert collection.get_paths()
    # Legend containers/proxy lines have no data and do not fabricate curves.
    assert all(np.asarray(line.get_xdata()).size == 0 for line in ax.lines)
    assert not ax.patches
    ax.figure.canvas.draw()
    # Native contour paths are finite; contourf shades/edges remain in raw x/y.
    vertices = np.concatenate(
        [path.vertices for coll in ax.collections for path in coll.get_paths()]
    )
    assert np.all(np.isfinite(vertices))
    assert vertices[:, 0].min() >= field.x[0] and vertices[:, 0].max() <= field.x[-1]
    assert vertices[:, 1].min() >= field.y[0] and vertices[:, 1].max() <= field.y[-1]


@pytest.mark.parametrize("fill", [False, True])
def test_missing_hue_reserves_native_legend_dash_or_hatch_slots(fill):
    raw = sample()
    raw = {key: values + values for key, values in raw.items()}
    raw["g"] = ["A"] * 6 + ["B"] * 6
    full = (
        mp.plot(raw)
        .kde2d(
            "x",
            "y",
            group="g",
            hue_order=["A", "B"],
            fill=fill,
            gridsize=25,
            levels=[0.5, 0.9],
        )
        .render()
        .axes[0]
    )
    partial = (
        mp.plot(raw)
        .kde2d(
            "x",
            "y",
            group="g",
            hue_order=["absent", "B"],
            fill=fill,
            gridsize=25,
            levels=[0.5, 0.9],
        )
        .render()
        .axes[0]
    )
    a = full.get_legend_handles_labels()[0][1]
    b = partial.get_legend_handles_labels()[0][0]
    if fill:
        pa, pb = cast(BarContainer, a).patches[0], cast(BarContainer, b).patches[0]
        assert pa.get_facecolor() == pb.get_facecolor()
        assert pa.get_hatch() == pb.get_hatch()
    else:
        la, lb = cast(Line2D, a), cast(Line2D, b)
        assert (
            la.get_color() == lb.get_color()
            and la.get_linestyle() == lb.get_linestyle()
        )
    assert partial.get_legend_handles_labels()[1] == ["B"]


@pytest.mark.parametrize("scale_x,scale_y", [(1e200, 1e-200), (1e-100, 1e100)])
def test_anisotropic_units_preserve_correlations_raw_density_and_hdr_mass(
    scale_x, scale_y
):
    raw = sample()
    base = fields(
        mp.plot(raw).kde2d("x", "y", weights="w", gridsize=25, levels=[0.5, 0.9])
    )[0]
    raw["x"] = [v * scale_x for v in raw["x"]]
    raw["y"] = [v * scale_y for v in raw["y"]]
    field = fields(
        mp.plot(raw).kde2d("x", "y", weights="w", gridsize=25, levels=[0.5, 0.9])
    )[0]
    assert field.correlation == pytest.approx(base.correlation, rel=8e-15)
    assert field.bandwidths is not None and base.bandwidths is not None
    np.testing.assert_allclose(
        field.bandwidths,
        [base.bandwidths[0] * scale_x, base.bandwidths[1] * scale_y],
        rtol=8e-15,
    )
    np.testing.assert_allclose(
        field.density,
        np.array(base.density) / (scale_x * scale_y),
        rtol=9e-14,
        atol=3e-16,
    )
    assert field.enclosed_mass == pytest.approx(base.enclosed_mass, rel=8e-15)
    assert field.grid_mass == pytest.approx(base.grid_mass, rel=8e-15)


def test_huge_weights_domination_and_neighboring_huge_x_keep_resolvable_covariance():
    raw = sample()
    equal = {**raw, "w": [1e308] * 6}
    a = fields(
        mp.plot(equal).kde2d("x", "y", weights="w", gridsize=25, levels=[0.5, 0.9])
    )[0]
    b = fields(mp.plot(raw).kde2d("x", "y", gridsize=25, levels=[0.5, 0.9]))[0]
    np.testing.assert_allclose(a.density, b.density, rtol=3e-15)
    dominant = fields(
        mp.plot({"x": [0, 1, 0], "y": [0, 0, 1], "w": [1e308, 1, 1]}).kde2d(
            "x", "y", weights="w", gridsize=25, levels=[0.5, 0.9]
        )
    )[0]
    assert dominant.bandwidths is not None
    np.testing.assert_allclose(dominant.bandwidths, [0.5, 0.5], rtol=3e-15)
    assert dominant.correlation == pytest.approx(0, abs=1e-15)
    first = 1e308
    step = float(np.nextafter(first, math.inf)) - first
    far = fields(
        mp.plot({"x": [first + i * step for i in range(4)], "y": [0, 2, 1, 3]}).kde2d(
            "x", "y", bw_method=1000, gridsize=25, levels=[0.5, 0.9]
        )
    )[0]
    assert far.bandwidths is not None
    assert far.bandwidths[0] == pytest.approx(
        np.std(np.arange(4), ddof=1) * step * 1000, rel=8e-15
    )
    assert all(a < b for a, b in pairwise(far.x)) and math.isfinite(far.grid_mass)


def test_bounded_point_row_evaluation_and_permutation_are_deterministic(monkeypatch):
    import mudplot._kde2d as backend

    rng = np.random.default_rng(61)
    cloud = rng.normal(size=(41, 2))
    weights = np.exp(rng.normal(size=41))
    p = mp.plot({"x": cloud[:, 0], "y": cloud[:, 1], "w": weights}).kde2d(
        "x", "y", weights="w", gridsize=19, levels=[0.5, 0.9]
    )
    expected = fields(p)[0]
    monkeypatch.setattr(backend, "_POINT_CHUNK", 7)
    monkeypatch.setattr(backend, "_ROW_CHUNK", 9)
    actual = fields(p)[0]
    np.testing.assert_allclose(actual.density, expected.density, rtol=5e-15, atol=0)
    order = rng.permutation(len(cloud))
    permuted = fields(
        mp.plot(
            {"x": cloud[order, 0], "y": cloud[order, 1], "w": weights[order]}
        ).kde2d("x", "y", weights="w", gridsize=19, levels=[0.5, 0.9])
    )[0]
    assert actual == permuted
    shapes = []
    original = np.exp

    def bounded(array):
        shapes.append(array.shape)
        assert array.ndim == 2 and array.shape[0] <= 7 and array.shape[1] <= 9
        return original(array)

    monkeypatch.setattr(np, "exp", bounded)
    fields(p)
    assert shapes


@pytest.mark.parametrize("logged", ["x", "y", "both"])
def test_log_display_uses_raw_units_positive_support_and_reversed_bounds(logged):
    raw = sample()
    raw["x"] = [v + 5 for v in raw["x"]]
    raw["y"] = [v + 5 for v in raw["y"]]
    p = mp.plot(raw).kde2d("x", "y", cut=0, gridsize=25, levels=[0.5, 0.9])
    base = fields(p)[0]
    if logged in ("x", "both"):
        p.xscale("log").xlim(10, 1)
    if logged in ("y", "both"):
        p.yscale("log").ylim(10, 1)
    assert fields(p)[0] == base
    ax = p.render().axes[0]
    if logged in ("x", "both"):
        assert ax.xaxis_inverted()
    if logged in ("y", "both"):
        assert ax.yaxis_inverted()
    q = mp.plot(raw).kde2d("x", "y", cut=10, gridsize=25, levels=[0.5, 0.9])
    if logged in ("x", "both"):
        q.xscale("log")
    if logged in ("y", "both"):
        q.yscale("log")
    assert mp.validate(q.spec) == []
    with pytest.raises(ValueError, match="derived log KDE2D support"):
        q.render()


@pytest.mark.parametrize(
    "options,match",
    [
        ({"bw_method": "bad"}, "bw_method must be"),
        ({"bw_method": True}, "bw_method must be"),
        ({"bw_method": 0}, "bw_method must be"),
        ({"bw_method": 1001}, "bw_method must be"),
        ({"bw_adjust": False}, "bw_adjust must be"),
        ({"bw_adjust": float("inf")}, "bw_adjust must be"),
        ({"cut": -1}, "cut must be"),
        ({"cut": 11}, "cut must be"),
        ({"cut": True}, "cut must be"),
        ({"gridsize": True}, "gridsize must be"),
        ({"gridsize": 1}, "gridsize must be"),
        ({"gridsize": 257}, "gridsize must be"),
        ({"clip": [0, 1]}, "clip must be"),
        ({"clip": [[0, 1]]}, "clip must be"),
        ({"clip": [[0, 1], [3, 2]]}, "clip must be"),
        ({"clip": [[False, 2], [0, 1]]}, "clip must be"),
        ({"clip": [[0, float("inf")], [0, 1]]}, "clip must be"),
        ({"levels": []}, "levels require"),
        ({"levels": [0, 0.5]}, "levels require"),
        ({"levels": [0.5, 1]}, "levels require"),
        ({"levels": [0.8, 0.5]}, "levels require"),
        ({"levels": [0.5, 0.5]}, "levels require"),
        ({"levels": [True]}, "levels require"),
        ({"levels": [float("nan")]}, "levels require"),
        ({"levels": list(np.linspace(0.01, 0.99, 17))}, "levels require"),
        ({"common_norm": 1}, "common_norm must be boolean"),
        ({"common_grid": 1}, "common_grid must be boolean"),
        ({"fill": 1}, "fill must be boolean"),
        ({"warn_singular": 1}, "warn_singular must be boolean"),
        ({"weights": "missing"}, "column 'missing'"),
        ({"weights": []}, "weights must be a nonempty"),
        ({"hue_order": ["A"]}, "hue_order requires group"),
        ({"group": "g", "hue_order": ["A", "A"]}, "levels must be unique"),
        ({"edge_color": "red"}, "edge_color requires fill=True"),
        ({"fill": True, "edge_color": "bad"}, "edge_color must be"),
        ({"line_style": "bad"}, "line_style must be"),
        ({"line_width": -1}, "line_width must be"),
    ],
)
def test_invalid_kernel_contour_and_style_options_fail_pure_validation(options, match):
    raw = {**sample(), "g": ["A"] * 6}
    p = mp.plot(raw).kde2d("x", "y", **options)
    assert any(match in issue for issue in mp.validate(p.spec))


@pytest.mark.parametrize("axis", ["x", "y"])
@pytest.mark.parametrize("value", [True, "1", float("inf"), 10**400])
def test_invalid_selected_coordinate_values_rejected(axis, value):
    raw = sample()
    raw[axis][-1] = value
    p = mp.plot(raw).kde2d("x", "y")
    assert any(
        "observations must be finite numeric" in issue for issue in mp.validate(p.spec)
    )


@pytest.mark.parametrize("weight", [True, False, -1, "2", float("inf"), 10**400])
def test_invalid_selected_weights_rejected_including_false_not_valid_zero(weight):
    raw = sample()
    raw["w"][-1] = weight
    p = mp.plot(raw).kde2d("x", "y", weights="w")
    assert any(
        "weights must be finite nonnegative" in issue for issue in mp.validate(p.spec)
    )


@pytest.mark.parametrize(
    "style",
    [
        {"stack": True},
        {"orient": "h"},
        {"stat_scale": "axis"},
        {"native_scale": True},
        {"order": [1, 2]},
        {"kde": mp.KDESpec()},
        {"ecdf": mp.ECDFSpec()},
        {"histogram": mp.HistogramSpec()},
        {"marker": "o"},
        {"colorbar": True},
        {"gridsize": 20},
    ],
)
def test_unsupported_flat_fields_or_univariate_controls_not_silently_ignored(style):
    if "gridsize" in style:
        # Flat field on direct LayerSpec, not the explicitly nested API argument.
        p = mp.plot(sample()).dispatch(
            A.AddLayer(LayerSpec(type="kde2d", x="x", y="y", **style))
        )
    else:
        p = mp.plot(sample()).kde2d("x", "y", **style)
    assert any("not supported" in issue for issue in mp.validate(p.spec))


@pytest.mark.parametrize(
    "style", [{"cumulative": True}, {"kernel": "epanechnikov"}, {"multiple": "stack"}]
)
def test_unknown_keywords_cannot_become_ignored_configuration(style):
    with pytest.raises(TypeError):
        mp.plot(sample()).kde2d("x", "y", **style)


def test_rows_bound_projection_secondary_and_shared_ordinal_axes():
    raw = {"x": list(range(10001)), "y": list(range(10001))}
    assert any(
        "at most 10000" in i for i in mp.validate(mp.plot(raw).kde2d("x", "y").spec)
    )
    p = mp.plot(sample()).kde2d("x", "y", axis="y2").secondary_yaxis("second")
    assert any("axis='y2' is not supported" in i for i in mp.validate(p.spec))
    assert any(
        "polar" in i
        for i in mp.validate(mp.plot(sample()).kde2d("x", "y").projection_polar().spec)
    )
    p = mp.plot(sample()).kde2d("x", "y").barplot("x", "y", errorbar=None)
    assert any("cannot mix ordinal" in i for i in mp.validate(p.spec))


@pytest.mark.parametrize(
    "raw,options,match",
    [
        (sample(), {"clip": [[20, 30], [20, 30]]}, "support is empty"),
        (sample(), {"gridsize": 2}, "enclosed levels are unresolved"),
        (
            {"x": [0, 1, 0], "y": [0, 0, 1], "w": [1e308, 1e-300, 1e-300]},
            {"weights": "w"},
            "cannot resolve positive weighted covariance",
        ),
        (
            {"x": [-1e308, 0, 1e308], "y": [0, 1, 0]},
            {"bw_method": 1000},
            "bandwidth must be",
        ),
    ],
)
def test_invalid_derived_quantities_fail_before_contours(raw, options, match):
    p = mp.plot(raw).kde2d("x", "y", **options)
    assert mp.validate(p.spec) == []
    with pytest.raises(ValueError, match=match):
        p.render()


def test_positive_observed_log_coordinates_and_clip_constraints():
    raw = sample()
    p = mp.plot(raw).kde2d("x", "y").xscale("log")
    assert any("log observations must be positive" in i for i in mp.validate(p.spec))
    raw["x"] = [v + 5 for v in raw["x"]]
    raw["y"] = [v + 5 for v in raw["y"]]
    p = mp.plot(raw).kde2d("x", "y", clip=[[0, None], [0.1, None]]).xscale("log")
    assert any("log clip bounds must be positive" in i for i in mp.validate(p.spec))
    p = (
        mp.plot(raw)
        .kde2d(
            "x", "y", clip=[[0.1, None], [0.1, None]], gridsize=31, levels=[0.5, 0.9]
        )
        .xscale("log")
        .yscale("log")
    )
    p.render()


def test_typed_json_action_schema_editor_and_wrong_layer_strict_configs():
    import jsonschema
    from dashboard.editor_server import EditorSession, _build_action

    p = mp.plot(sample()).kde2d(
        "x",
        "y",
        weights="w",
        fill=True,
        gridsize=29,
        levels=(0.5, 0.9),
        clip=((None, 4), (None, 5)),
    )
    assert (
        mp.Plot.from_json(p.to_json()).spec == p.spec
        and mp.apply(p.action_log) == p.spec
    )
    jsonschema.validate(p.spec.to_dict(), mp.json_schema())
    assert mp.json_schema()["$defs"]["KDE2DSpec"]["additionalProperties"] is False
    raw = p.spec.to_dict()
    raw["panels"][0]["layers"][0]["kde2d"]["cumulative"] = True
    with pytest.raises(ValueError, match="unknown KDE2DSpec"):
        mp.FigureSpec.from_dict(raw)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(raw, mp.json_schema())
    invalid = p.spec
    invalid.panels[0].layers[0].kde2d = cast(Any, {"fill": True})
    assert any("kde2d must be KDE2DSpec" in i for i in mp.validate(invalid))
    assert any(
        "kde2d is not supported" in i
        for i in mp.validate(mp.plot(sample()).kde("x", kde2d=mp.KDE2DSpec()).spec)
    )
    session = EditorSession()
    session.dispatch_safe(A.SetData(sample()))
    session.dispatch_safe(
        _build_action(
            "add_layer_json",
            {
                "layer_type": "kde2d",
                "layer_json": json.dumps(
                    {
                        "x": "x",
                        "y": "y",
                        "kde2d": {"gridsize": 25, "levels": [0.5, 0.9], "fill": True},
                    }
                ),
            },
            session.store.state,
        )
    )
    assert session.error is None and session.png.startswith(b"\x89PNG")
    assert b"<svg" in session.export("svg")
    direct = mp.plot(sample()).dispatch(
        A.AddLayer(LayerSpec(type="kde2d", x="x", y="y"))
    )
    assert fields(direct)[0].density
    assert mp.KDE2DSpec().levels is not mp.KDE2DSpec().levels


@pytest.mark.parametrize("fill", [False, True])
@pytest.mark.parametrize("fmt", ["png", "svg", "pdf"])
def test_repeatable_exports_native_legend_references_no_global_rng_mutation(
    tmp_path, fill, fmt
):
    p = (
        mp.plot(sample())
        .kde2d(
            "x",
            "y",
            weights="w",
            fill=fill,
            gridsize=31,
            levels=[0.5, 0.9],
            alpha=0.6,
            label="joint",
            href="https://example.org/joint",
            citation="smith2026",
        )
        .size(4, 3)
    )
    before = np.random.get_state()
    a, b = tmp_path / f"a.{fmt}", tmp_path / f"b.{fmt}"
    plt.close(p.save(str(a)))
    plt.close(mp.Plot.from_json(p.to_json()).save(str(b)))
    assert a.read_bytes() == b.read_bytes()
    if fmt == "svg":
        assert "https://example.org/joint" in a.read_text(encoding="utf-8")
    after = np.random.get_state()
    assert before[0] == after[0] and before[2:] == after[2:]
    np.testing.assert_array_equal(before[1], after[1])
