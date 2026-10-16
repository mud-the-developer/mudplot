"""Independent weighted violin equations, empirical marks and native geometry."""

from __future__ import annotations

import json
import math
from decimal import Decimal, localcontext

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import LineCollection, PolyCollection
from mudplot import actions as A
from mudplot._categorical import distribution_rows
from mudplot._violin import _mean, _quartiles, density_cell, prepare_violin
from mudplot.spec import LayerSpec


def _data():
    return {
        "c": [10] * 8 + [40] * 8,
        "h": (["A"] * 4 + ["B"] * 4) * 2,
        "v": [1, 2, 4, 9] * 4,
        "w": [1, 1, 6, 2, 4, 2, 1, 1, 1, 2, 2, 1, 1, 3, 2, 4],
    }


def _bodies(ax):
    return [c for c in ax.collections if isinstance(c, PolyCollection)]


@pytest.mark.parametrize("method", [None, "scott", "silverman", 0.45])
@pytest.mark.parametrize("adjust", [0.5, 1, 2])
@pytest.mark.parametrize("cut", [0, 2])
def test_weighted_gaussian_matches_independent_covariance_and_pdf(method, adjust, cut):
    values = np.array([-2, -0.4, 1, 3, 4])
    weights = np.array([1, 4, 2, 1, 3])
    p = weights / weights.sum()
    neff = 1 / np.sum(p * p)
    mean = np.sum(p * values)
    variance = np.sum(p * (values - mean) ** 2) / (1 - np.sum(p * p))
    factor = (
        (neff * 0.75) ** -0.2
        if method == "silverman"
        else neff**-0.2
        if method in (None, "scott")
        else method
    )
    bandwidth = math.sqrt(variance) * factor * adjust
    cell = density_cell(
        values, weights=weights, bw_method=method, bw_adjust=adjust, points=37, cut=cut
    )
    grid = np.linspace(
        values.min() - cut * bandwidth, values.max() + cut * bandwidth, 37
    )
    z = (grid[:, None] - values[None, :]) / bandwidth
    expected = np.sum(p[None, :] * np.exp(-0.5 * z * z), axis=1) / (
        bandwidth * math.sqrt(2 * math.pi)
    )
    np.testing.assert_allclose(cell.support, grid, atol=3e-15)
    np.testing.assert_allclose(cell.bandwidth, bandwidth, rtol=2e-14)
    np.testing.assert_allclose(cell.density, expected, rtol=2e-14)
    np.testing.assert_allclose(cell.profile, expected / expected.max(), rtol=2e-14)
    np.testing.assert_array_equal(cell.observations, values)
    np.testing.assert_array_equal(cell.weights, weights)


def test_equal_weights_match_unweighted_density_not_replication_bandwidth():
    values = [1, 2, 4, 9]
    unit = density_cell(values, weights=[1] * 4, points=71, cut=2)
    old = density_cell(values, points=71, cut=2)
    np.testing.assert_allclose(unit.bandwidth, old.bandwidth)
    np.testing.assert_allclose(unit.density, old.density, rtol=3e-14)
    relative = density_cell(values, weights=[1, 1, 6, 2], points=71, cut=2)
    repeated = density_cell([1, 2] + [4] * 6 + [9] * 2, points=71, cut=2)
    assert not np.isclose(relative.bandwidth, repeated.bandwidth)
    # Explicit weighted quantiles are inverse-ECDF, unlike old linear quantiles.
    np.testing.assert_array_equal(_quartiles(unit), [1, 2, 4])
    np.testing.assert_array_equal(_quartiles(old), [1.75, 3, 5.25])


def test_weight_scaling_permutation_and_clip_never_change_fit_or_inner_rows():
    v, w = [1, 2, 4, 9], [1, 1, 6, 2]
    base = density_cell(v, weights=w, clip=[2, 6], cut=3, points=41)
    rescaled = density_cell(
        v, weights=[x * 1e307 for x in w], clip=[2, 6], cut=0, points=41
    )
    reverse = density_cell(v[::-1], weights=w[::-1], clip=[2, 6], cut=3, points=41)
    # Convex interpolation avoids high-low overflow; it may differ by two ULPs
    # from NumPy's subtract-and-add linspace even on these finite bounds.
    np.testing.assert_array_equal(base.support[[0, -1]], [2, 6])
    assert (np.diff(base.support) > 0).all()
    np.testing.assert_array_max_ulp(base.support, np.linspace(2, 6, 41), maxulp=2)
    np.testing.assert_array_equal(base.support, rescaled.support)
    np.testing.assert_allclose(base.density, rescaled.density, rtol=2e-14)
    np.testing.assert_array_equal(base.density, reverse.density)
    np.testing.assert_allclose(base.bandwidth, rescaled.bandwidth)
    np.testing.assert_array_equal(base.observations, v)
    np.testing.assert_array_equal(_quartiles(base), [4, 4, 4])
    assert _mean(base) == pytest.approx(4.5)
    area = np.sum(np.diff(base.support) * (base.density[1:] + base.density[:-1]) / 2)
    assert area < 1


@pytest.mark.parametrize("mode", ["width", "area", "count"])
@pytest.mark.parametrize("common", [False, True])
def test_normalization_references_weight_mass_not_neff_or_row_count(mode, common):
    cells = {
        "A": {10: [1, 2, 4, 9], 40: [1, 2, 4, 9]},
        "B": {10: [1, 2, 4, 9]},
        "empty": {},
    }
    weights = {
        "A": {10: [1, 1, 6, 2], 40: [1, 1, 1, 1]},
        "B": {10: [1, 1, 1, 1]},
        "empty": {},
    }
    layer = LayerSpec(type="violin", weights="w", density_norm=mode, common_norm=common)
    profiles = prepare_violin(cells, layer, weights=weights)
    for (g, _c), cell in profiles.items():
        compare = [other for (h, _), other in profiles.items() if common or g == h]
        if mode == "width":
            expected = cell.density / cell.density.max()
        elif mode == "area":
            expected = cell.density / max(c.density.max() for c in compare)
        else:
            expected = (
                cell.density
                / cell.density.max()
                * cell.weights.sum()
                / max(c.weights.sum() for c in compare)
            )
        np.testing.assert_allclose(cell.profile, expected)
    if mode == "count":
        assert profiles["A", 40].profile.max() == pytest.approx(0.4)
        assert profiles["B", 10].profile.max() == pytest.approx(0.4 if common else 1)


def test_count_normalization_handles_mass_overflow_and_singular_reference():
    layer = LayerSpec(
        type="violin", weights="w", density_norm="count", common_norm=True
    )
    cells = {"A": {0: [1, 2, 3], 1: [7, 7]}}
    profiles = prepare_violin(
        cells, layer, weights={"A": {0: [1e308] * 3, 1: [1e308] * 2}}
    )
    assert profiles["A", 0].profile.max() == 1
    assert profiles["A", 1].profile.max() == pytest.approx(2 / 3)
    assert profiles["A", 1].singular and profiles["A", 1].bandwidth == 0
    np.testing.assert_array_equal(profiles["A", 1].support, [7, 7])
    np.testing.assert_array_equal(
        profiles["A", 1].support, density_cell([7, 7]).support
    )
    assert _mean(profiles["A", 1]) == 7
    with pytest.raises(ValueError, match="mass ratio"):
        prepare_violin(
            {"A": {0: [1, 2, 3], 1: [1, 2, 3]}},
            layer,
            weights={"A": {0: [1e308] * 3, 1: [1e-308] * 3}},
        )


def test_weighted_mean_keeps_adjacent_low_bits_and_opposite_extremes():
    lo = 1e308
    values = [
        lo,
        np.nextafter(lo, np.inf),
        np.nextafter(np.nextafter(lo, np.inf), np.inf),
    ]
    cell = density_cell(values, weights=[1, 2, 3], points=2)
    with localcontext() as context:
        context.prec = 100
        exact = (
            sum(
                Decimal.from_float(float(v)) * w
                for v, w in zip(values, [1, 2, 3], strict=True)
            )
            / 6
        )
    assert _mean(cell) == float(exact)
    opposite = density_cell([-1e308, 1e308], weights=[1, 1], points=31)
    assert _mean(opposite) == 0
    assert np.isfinite(opposite.density).all() and (opposite.density > 0).all()


@pytest.mark.parametrize("inner", [None, "legacy", "box", "quart", "point", "stick"])
@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("split", [False, True])
def test_real_weighted_geometry_inner_values_and_no_row_replication(
    inner, orient, split
):
    p = mp.plot(_data()).violin(
        "c",
        "v",
        group="h",
        weights="w",
        inner=inner,
        orient=orient,
        split=split,
        density_norm="count",
        common_norm=True,
        order=[10, "empty", 40],
        hue_order=["A", "B"],
        alpha=0.42,
        edge_color="#334155",
        line_width=0.7,
        line_style=":",
        cut=2,
        clip=(0.5, 10),
    )
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    bodies = _bodies(ax)
    assert len(bodies) == 4
    assert ax.get_legend_handles_labels()[1] == ["A", "B"]
    for body in bodies:
        assert body.get_alpha() == 0.42
        assert np.asarray(body.get_linewidth())[0] == 0.7
        assert np.isfinite(body.get_paths()[0].vertices).all()
    cd, vd = int(orient == "h"), int(orient != "h")
    first = np.asarray(bodies[0].get_paths()[0].vertices)
    if split:
        assert first[:, cd].max() == 0
        assert first[:, cd].min() == pytest.approx(-0.4)
    else:
        assert (first[:, cd].max() + first[:, cd].min()) / 2 == pytest.approx(-0.2)
    if inner == "quart":
        lines = [c for c in ax.collections if isinstance(c, LineCollection)]
        np.testing.assert_array_equal(
            np.asarray(lines[0].get_segments())[:, :, vd], [[4, 4]] * 3
        )
    elif inner == "box":
        np.testing.assert_array_equal(np.asarray(ax.lines[0].get_xydata())[:, vd], [4])
    elif inner == "point":
        assert sum(len(np.asarray(line.get_xydata())) for line in ax.lines) == 16
        np.testing.assert_array_equal(
            np.asarray(ax.lines[0].get_xydata())[:, vd], [1, 2, 4, 9]
        )
    elif inner == "stick":
        assert (
            sum(
                len(c.get_segments())
                for c in ax.collections
                if isinstance(c, LineCollection)
            )
            == 16
        )
    elif inner == "legacy":
        lines = [c for c in ax.collections if isinstance(c, LineCollection)]
        assert np.asarray(lines[0].get_segments())[0, 0, vd] == 4
    assert mp.apply(p.action_log) == p.spec
    assert mp.Plot.from_json(p.to_json()).spec == p.spec


@pytest.mark.parametrize("mode", ["data", "axis"])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_native_log_weighted_mean_and_step_median_in_declared_coordinates(mode, orient):
    p = (
        mp.plot({"c": [10] * 3, "v": [1, 4, 16], "w": [1, 2, 1]})
        .violin(
            "c",
            "v",
            weights="w",
            native_scale=True,
            orient=orient,
            stat_scale=mode,
            showmeans=True,
            showextrema=False,
            clip=(0.5, 20),
            cut=2,
        )
        .xscale("log")
        .yscale("log")
    )
    ax = p.render().axes[0]
    lines = [c for c in ax.collections if isinstance(c, LineCollection)]
    vd = int(orient != "h")
    assert np.asarray(lines[0].get_segments())[0, 0, vd] == pytest.approx(
        6.25 if mode == "data" else 4
    )
    assert np.asarray(lines[1].get_segments())[0, 0, vd] == pytest.approx(4)
    assert ax.get_xscale() == ax.get_yscale() == "log"


def test_listwise_missing_zero_and_selection_excluded_before_positivity():
    raw = {
        "c": [10] * 7,
        "v": [1, 3, -9, float("inf"), None, 8, 7],
        "h": ["A", "A", "A", "A", "A", "B", "A"],
        "w": [1, 2, 0, 0, 3, -1, None],
    }
    p = (
        mp.plot(raw)
        .violin(
            "c", "v", group="h", weights="w", hue_order=["empty", "A"], inner="point"
        )
        .yscale("log")
    )
    assert mp.validate(p.spec) == []
    assert distribution_rows(p.spec.data.columns, p.spec.panels[0].layers[0]) == [0, 1]
    ax = p.render().axes[0]
    assert ax.get_legend_handles_labels()[1] == ["A"]
    np.testing.assert_array_equal(np.asarray(ax.lines[0].get_ydata()), [1, 3])


@pytest.mark.parametrize("weights", [[1, -1], [1, float("inf")], [1, True], [1, "bad"]])
def test_invalid_selected_weights_fail_before_artists(weights):
    p = mp.plot({"v": [1, 2], "w": weights}).violin("v", weights="w")
    assert any("weights" in issue for issue in mp.validate(p.spec))
    with pytest.raises(ValueError, match="weights"):
        p.render()


@pytest.mark.parametrize("column", ["", "absent", False, ["w"]])
def test_invalid_weight_column_contract(column):
    p = mp.plot({"v": [1, 2], "w": [1, 2]}).violin("v", weights=column)
    assert mp.validate(p.spec)
    with pytest.raises(ValueError):
        p.render()


def test_zero_only_rows_bound_and_misplaced_weights_rejected():
    p = mp.plot({"v": [1, 2], "w": [0, 0]}).violin("v", weights="w")
    assert any("no usable" in i for i in mp.validate(p.spec))
    p = mp.plot({"v": [1] * 10001, "w": [1] * 10001}).violin(
        "v", weights="w", inner=None
    )
    assert any("10000" in i for i in mp.validate(p.spec))
    for kind in ("box", "kde", "line", "hist", "swarmplot"):
        p = mp.plot({"v": [1, 2], "w": [1, 2]}).dispatch(
            A.AddLayer(LayerSpec(type=kind, x="v", y="v", weights="w"))
        )
        assert any("weights" in i for i in mp.validate(p.spec)), kind


@pytest.mark.parametrize("kwargs", [{"clip": [20, 30]}, {"cut": 3, "bw_adjust": 1000}])
def test_weighted_derived_support_errors_not_hidden(kwargs):
    values = [1, 2, 3] if "clip" in kwargs else [-1e308, 1e308]
    with pytest.raises(ValueError, match=r"support|bandwidth"):
        density_cell(values, weights=[1] * len(values), **kwargs)


def test_json_schema_old_defaults_and_editor_preserve_weight_option():
    import jsonschema
    from dashboard.editor_server import EditorSession

    p = mp.plot(_data()).violin("c", "v", group="h", weights="w", inner="box")
    jsonschema.validate(p.spec.to_dict(), mp.json_schema())
    state = EditorSession()
    state.load_spec(p.to_json())
    assert state.error is None
    state.dispatch_safe(A.AddLayer(LayerSpec(type="violin", x="v", weights="w")))
    assert state.error is None
    assert state.store.state.panels[0].layers[-1].weights == "w"
    state.undo()
    assert len(state.store.state.panels[0].layers) == 1
    assert state.store.state.panels[0].layers[0].weights == "w"
    assert state.png.startswith(b"\x89PNG")
    old = mp.plot({"v": [1, 2, 3]}).violin("v").spec.to_dict()
    old["panels"][0]["layers"][0].pop("weights")
    assert mp.Plot.from_json(json.dumps(old)).spec.panels[0].layers[0].weights is None


def test_weighted_export_bytes_rng_and_no_sampling_are_repeatable(tmp_path):
    p = mp.plot(_data()).violin(
        "c", "v", group="h", weights="w", inner="quart", split=True
    )
    before = np.random.get_state()
    for suffix in ("png", "svg", "pdf"):
        first, second = tmp_path / f"a.{suffix}", tmp_path / f"b.{suffix}"
        plt.close(p.save(first))
        plt.close(p.save(second))
        assert first.read_bytes() == second.read_bytes()
    after = np.random.get_state()
    assert before[0] == after[0] and before[2:] == after[2:]
    np.testing.assert_array_equal(before[1], after[1])
    import mudplot._kde as kernel

    assert kernel._EVALUATION_CHUNK == 2048
    assert (tmp_path / "a.png").read_bytes().startswith(b"\x89PNG")


def test_weighted_kernel_uses_bounded_actual_row_chunks(monkeypatch):
    sizes = []
    original = np.exp

    def exp(values):
        sizes.append(len(values))
        return original(values)

    monkeypatch.setattr(np, "exp", exp)
    values = np.linspace(1, 10, 5001)
    cell = density_cell(values, weights=np.ones(5001), points=3)
    assert len(cell.observations) == 5001
    assert max(sizes) == 2048 and len(sizes) == 9
    assert np.isfinite(cell.density).all()


def test_dominant_weight_keeps_unbiased_correction_and_exact_empirical_ties():
    cell = density_cell([1, 5], weights=[1e300, 1e200], points=31)
    assert cell.bandwidth == pytest.approx(math.sqrt(8))
    assert _mean(cell) == 1
    np.testing.assert_array_equal(_quartiles(cell), [1, 1, 1])
    tied = density_cell([1, 1, 2, 4], weights=[1, 1, 2, 4])
    np.testing.assert_array_equal(_quartiles(tied), [1, 2, 4])
