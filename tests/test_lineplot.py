"""Numeric predictors, pointwise inference and native line/band contracts."""

from __future__ import annotations

import json
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import LineCollection, PolyCollection


def _data():
    return {"x": [3, 3, 1, 1, 2, 2], "y": [4, 6, 1, 3, 3, 5]}


def _values(ax, orient="v"):
    points = np.asarray(ax.lines[0].get_xydata())
    return points[:, ::-1] if orient == "h" else points


@pytest.mark.parametrize(
    "estimator,expected",
    [
        ("mean", [2, 4, 5]),
        ("median", [2, 4, 5]),
        ("sum", [4, 8, 10]),
        ("min", [1, 3, 4]),
        ("max", [3, 5, 6]),
        ("count", [2, 2, 2]),
    ],
)
@pytest.mark.parametrize("orient", ["v", "h"])
def test_named_estimates_use_real_numeric_x_not_ordinal_ticks(
    estimator, expected, orient
):
    p = mp.plot(_data()).lineplot(
        "x", "y", estimator=estimator, errorbar=None, orient=orient
    )
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    np.testing.assert_array_equal(
        _values(ax, orient), np.column_stack(([1, 2, 3], expected))
    )
    assert len(ax.collections) == 0
    assert ax.lines[0].get_marker() == "None"
    assert mp.apply(p.action_log) == p.spec
    assert mp.Plot.from_json(p.to_json()).spec == p.spec


@pytest.mark.parametrize("method", ["sd", "se", "pi"])
@pytest.mark.parametrize("style", [None, "band", "bars"])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_pointwise_bounds_match_independent_equations_and_real_paths(
    method, style, orient
):
    options = {} if style != "bars" else {"capsize": 3, "capthick": 0.7}
    p = mp.plot(_data()).lineplot(
        "x",
        "y",
        errorbar=method,
        error_style=style,
        orient=orient,
        error_color="#bb4400",
        **options,
    )
    ax = p.render().axes[0]
    low, high = [], []
    for center, values in [(2, [1, 3]), (4, [3, 5]), (5, [4, 6])]:
        if method == "pi":
            a, b = np.percentile(values, [2.5, 97.5])
        else:
            delta = np.std(values, ddof=1) / (math.sqrt(2) if method == "se" else 1)
            a, b = center - delta, center + delta
        low.append(a)
        high.append(b)
    if style == "bars":
        segments = np.asarray(
            next(
                c for c in ax.collections if isinstance(c, LineCollection)
            ).get_segments()
        )
        vd = int(orient != "h")
        np.testing.assert_allclose(segments[:, :, vd], np.column_stack((low, high)))
    else:
        body = next(c for c in ax.collections if isinstance(c, PolyCollection))
        vertices = np.asarray(body.get_paths()[0].vertices)
        if orient == "h":
            vertices = vertices[:, ::-1]
        for x, lo, hi in zip([1, 2, 3], low, high, strict=True):
            actual = vertices[vertices[:, 0] == x, 1]
            assert actual.min() == pytest.approx(lo) and actual.max() == pytest.approx(
                hi
            )
        assert body.get_alpha() == 0.2 and np.asarray(body.get_linewidth())[0] == 0


def test_ci_is_seeded_per_cell_not_simultaneous_or_global_rng():
    p = mp.plot(_data()).lineplot("x", "y", n_boot=127, seed=42)
    before = np.random.get_state()
    ax = p.render().axes[0]
    rng = np.random.default_rng(42)
    bounds = {}
    for x, values in [(3, [4, 6]), (1, [1, 3]), (2, [3, 5])]:
        draws = rng.integers(0, 2, size=(127, 2))
        draws = np.array(values)[draws].mean(axis=1)
        bounds[x] = np.percentile(draws, [2.5, 97.5])
    vertices = np.asarray(ax.collections[0].get_paths()[0].vertices)
    for x, (lo, hi) in bounds.items():
        actual = vertices[vertices[:, 0] == x, 1]
        assert actual.min() == lo and actual.max() == hi
    after = np.random.get_state()
    assert before[0] == after[0] and before[2:] == after[2:]
    np.testing.assert_array_equal(before[1], after[1])


def test_weights_units_pair_within_x_and_not_whole_curve_bootstrap():
    raw = {
        "x": [1] * 4 + [2] * 4,
        "y": [1, 3, 4, 8, 2, 6, 8, 16],
        "w": [1, 3, 2, 1] * 2,
        "u": ["A", "A", "B", "B"] * 2,
    }
    p = mp.plot(raw).lineplot("x", "y", weights="w", units="u", n_boot=83, seed=17)
    ax = p.render().axes[0]
    np.testing.assert_allclose(
        _values(ax)[:, 1],
        [
            np.average(raw["y"][:4], weights=raw["w"][:4]),
            np.average(raw["y"][4:], weights=raw["w"][4:]),
        ],
    )
    # Independent hierarchical bootstrap, each predictor cell uses its paired rows.
    rng = np.random.default_rng(17)
    expected = []
    for values in (np.array(raw["y"][:4]), np.array(raw["y"][4:])):
        draws = []
        for _ in range(83):
            picked = []
            for unit in rng.integers(0, 2, size=2):
                indexes = np.array([0, 1]) if unit == 0 else np.array([2, 3])
                picked.extend(indexes[rng.integers(0, len(indexes), size=len(indexes))])
            draws.append(
                np.average(values[picked], weights=np.array(raw["w"][:4])[picked])
            )
        expected.append(np.percentile(draws, [2.5, 97.5]))
    vertices = np.asarray(ax.collections[0].get_paths()[0].vertices)
    for x, (lo, hi) in zip([1, 2], expected, strict=True):
        values = vertices[vertices[:, 0] == x, 1]
        assert values.min() == pytest.approx(lo) and values.max() == pytest.approx(hi)


def test_first_observed_x_order_is_per_hue_and_bands_reject_self_crossing():
    raw = {"x": [3, 1, 2, 1, 3, 2], "y": [6, 2, 4, 3, 7, 5], "h": ["A"] * 3 + ["B"] * 3}
    p = mp.plot(raw).lineplot("x", "y", group="h", sort=False, errorbar=None)
    ax = p.render().axes[0]
    np.testing.assert_array_equal(np.asarray(ax.lines[0].get_xdata()), [3, 1, 2])
    np.testing.assert_array_equal(np.asarray(ax.lines[1].get_xdata()), [1, 3, 2])
    bad = {key: values * 2 for key, values in raw.items()}
    p = mp.plot(bad).lineplot("x", "y", group="h", sort=False, errorbar="sd")
    with pytest.raises(ValueError, match="monotonic"):
        p.render()
    p = mp.plot(bad).lineplot(
        "x", "y", group="h", sort=False, errorbar="sd", error_style="bars"
    )
    p.render()


def test_singletons_break_bands_but_do_not_invent_or_remove_point_estimates():
    p = mp.plot({"x": [1, 1, 2, 3, 3], "y": [1, 3, 4, 5, 7]}).lineplot(
        "x", "y", errorbar="sd"
    )
    with pytest.warns(UserWarning, match="omitted"):
        ax = p.render().axes[0]
    np.testing.assert_array_equal(_values(ax), [[1, 2], [2, 4], [3, 6]])
    paths = ax.collections[0].get_paths()
    assert len(paths) == 2
    assert all(len(np.unique(np.asarray(path.vertices)[:, 0])) == 1 for path in paths)


@pytest.mark.parametrize("mode,expected", [("data", 8.5), ("axis", 4)])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_raw_log_and_explicit_log_fit_estimates_inverse_map(mode, expected, orient):
    p = (
        mp.plot({"x": [1, 1, 10, 10], "y": [1, 16, 1, 16]})
        .lineplot("x", "y", errorbar=None, orient=orient, stat_scale=mode)
        .xscale("log")
        .yscale("log")
    )
    ax = p.render().axes[0]
    np.testing.assert_allclose(_values(ax, orient), [[1, expected], [10, expected]])
    assert ax.get_xscale() == ax.get_yscale() == "log"


@pytest.mark.parametrize("style", [None, "band", "bars"])
def test_negative_raw_log_intervals_fail_not_clip(style):
    p = (
        mp.plot({"x": [1, 1, 2, 2], "y": [1, 16, 1, 16]})
        .lineplot("x", "y", errorbar="sd", error_style=style)
        .yscale("log")
    )
    with pytest.raises(ValueError, match="endpoints"):
        p.render()


@pytest.mark.parametrize("opacity", [0, 0.45, 1])
def test_band_alpha_is_exact_and_reference_palette_slots_are_reserved(opacity):
    p = mp.plot({"x": [1, 1, 2, 2], "y": [1, 3, 4, 6], "h": ["A"] * 4}).lineplot(
        "x",
        "y",
        group="h",
        hue_order=["empty", "A"],
        errorbar="sd",
        error_alpha=opacity,
        alpha=0.7,
        line_style=":",
        label="ignored",
        references={"A": mp.Reference(href="https://example.org")},
    )
    ax = p.render().axes[0]
    assert ax.collections[0].get_alpha() == opacity
    assert ax.lines[0].get_alpha() == 0.7
    assert ax.get_legend_handles_labels()[1] == ["A"]
    assert ax.lines[0].get_linestyle() == ":"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"sort": 1},
        {"error_style": "bad"},
        {"error_alpha": True},
        {"error_alpha": 2},
        {"error_style": "bars", "error_alpha": 0.3},
        {"capsize": 2},
        {"error_line_width": 1},
        {"dodge": 0.2},
        {"order": [1, 2]},
        {"native_scale": True},
        {"axis": "y2"},
        {"stat_scale": "bogus"},
        {"line_width": False},
        {"line_width": -1},
        {"units": "u", "errorbar": None},
        {"errorbar": None, "error_alpha": 0.2},
    ],
)
def test_invalid_noop_or_unsupported_options_fail_before_native_artists(kwargs):
    p = mp.plot({"x": [1, 1, 2, 2], "y": [1, 3, 4, 6], "u": ["A", "B"] * 2}).lineplot(
        "x", "y", **kwargs
    )
    assert mp.validate(p.spec)
    with pytest.raises(ValueError):
        p.render()


@pytest.mark.parametrize("x", [["1", "2"], [True, False], [1, float("inf")]])
def test_non_numeric_predictors_are_not_coerced(x):
    p = mp.plot({"x": x, "y": [1, 2]}).lineplot("x", "y", errorbar=None)
    assert mp.validate(p.spec)


def test_line_primitive_and_old_schema_defaults_unchanged():
    raw = mp.plot(_data()).line("x", "y")
    np.testing.assert_array_equal(
        _values(raw.render().axes[0]), np.column_stack((_data()["x"], _data()["y"]))
    )
    old = raw.spec.to_dict()
    for name in ("sort", "error_style", "error_alpha"):
        old["panels"][0]["layers"][0].pop(name)
    assert mp.Plot.from_json(json.dumps(old)).spec == raw.spec
    raw = mp.plot(_data()).line("x", "y", sort=False)
    assert any("sort" in issue for issue in mp.validate(raw.spec))


def test_lineplot_roundtrips_editor_and_repeatable_zero_width_exports(tmp_path):
    import jsonschema
    from dashboard.editor_server import EditorSession

    p = mp.plot(_data()).lineplot(
        "x", "y", errorbar="sd", line_width=0, line_style="--", error_alpha=0
    )
    jsonschema.validate(p.spec.to_dict(), mp.json_schema())
    session = EditorSession()
    session.load_spec(p.to_json())
    assert session.error is None and session.png.startswith(b"\x89PNG")
    for suffix in ("png", "svg", "pdf"):
        a, b = tmp_path / f"a.{suffix}", tmp_path / f"b.{suffix}"
        plt.close(p.save(str(a)))
        plt.close(p.save(str(b)))
        assert a.read_bytes() == b.read_bytes()
    assert mp.apply(p.action_log) == p.spec


def test_log_predictors_reject_nonpositive_and_ordinal_overlays():
    p = (
        mp.plot({"x": [-1, -1, 1, 1], "y": [1, 2, 3, 4]})
        .lineplot("x", "y", errorbar=None)
        .xscale("log")
    )
    assert mp.validate(p.spec)
    p = (
        mp.plot(_data())
        .lineplot("x", "y", errorbar=None)
        .pointplot("x", "y", errorbar=None)
    )
    assert any("native and ordinal" in issue for issue in mp.validate(p.spec))
