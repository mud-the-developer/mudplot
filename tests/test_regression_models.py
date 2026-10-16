"""Configured regression models and raw residuals; legacy polynomial path stays."""

from __future__ import annotations

import builtins
import copy
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import PathCollection
from mudplot._regression import MAX_LOWESS_ROWS, MAX_REGRESSION_ROWS


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def data():
    x = np.linspace(1, 8, 40)
    return {"x": x.tolist(), "y": (2 + 1.5 * x + 0.2 * np.sin(x)).tolist()}


def test_residuals_are_y_minus_row_predictions_in_original_order():
    raw = {"x": [4, 1, 3, 2, 5], "y": [8, 3, 5, 5, 12]}
    p = mp.plot(raw).residplot("x", "y", degree=2).size(6, 4)
    assert mp.validate(p.spec) == [] and p.spec.data.columns == raw
    ax = p.render().axes[0]
    points = np.asarray(ax.collections[0].get_offsets(), dtype=float)
    expected = np.asarray(raw["y"]) - np.polyval(
        np.polyfit(raw["x"], raw["y"], 2), raw["x"]
    )
    np.testing.assert_allclose(points[:, 0], raw["x"])
    np.testing.assert_allclose(points[:, 1], expected, atol=1e-12)
    assert len(ax.lines) == 1
    np.testing.assert_allclose(np.asarray(ax.lines[0].get_ydata(), dtype=float), [0, 0])
    assert mp.apply(p.action_log) == mp.Plot.from_json(p.to_json()).spec == p.spec


def test_logx_fit_and_normal_approximation_band_use_log_predictor():
    x = np.geomspace(0.1, 100, 30)
    y = 3 + 2 * np.log(x) + 0.05 * np.sin(np.arange(len(x)))
    p = (
        mp.plot({"x": x, "y": y})
        .regplot("x", "y", confidence=95, regression={"model": "logx"})
        .size(6, 4)
    )
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    line = ax.lines[0]
    grid = np.asarray(line.get_xdata(), dtype=float)
    fitted = np.asarray(line.get_ydata(), dtype=float)
    np.testing.assert_allclose(
        fitted, np.polyval(np.polyfit(np.log(x), y, 1), np.log(grid)), atol=1e-11
    )
    assert len(ax.collections) == 2


@pytest.mark.parametrize("model", ["robust", "logistic", "lowess"])
def test_optional_predictions_match_independent_statsmodels_reference(model):
    pytest.importorskip("statsmodels")
    raw = data()
    x, y = np.asarray(raw["x"]), np.asarray(raw["y"])
    if model == "robust":
        from statsmodels.robust.robust_linear_model import RLM

        y[-3:] += [15, -20, 25]
    elif model == "logistic":
        from statsmodels.genmod.families import Binomial
        from statsmodels.genmod.generalized_linear_model import GLM

        x = np.repeat(np.arange(-3, 4), 10)
        y = np.concatenate(
            [np.array([1] * n + [0] * (10 - n)) for n in [1, 2, 3, 5, 7, 8, 9]]
        )
    else:
        from statsmodels.nonparametric.smoothers_lowess import lowess
    p = (
        mp.plot({"x": x, "y": y})
        .regplot("x", "y", regression={"model": model})
        .size(6, 4)
    )
    assert mp.validate(p.spec) == []
    line = p.render().axes[0].lines[0]
    grid = np.asarray(line.get_xdata(), dtype=float)
    prediction = np.asarray(line.get_ydata(), dtype=float)
    design = np.column_stack((np.ones(len(x)), x))
    at = np.column_stack((np.ones(len(grid)), grid))
    if model == "robust":
        expected = RLM(y, design).fit().predict(at)
    elif model == "logistic":
        expected = GLM(y, design, family=Binomial()).fit().predict(at)
        assert np.all((prediction >= 0) & (prediction <= 1))
    else:
        expected = lowess(y, x, xvals=grid, missing="none")
    np.testing.assert_allclose(prediction, expected, rtol=1e-7, atol=1e-7)


def test_robust_exact_line_has_no_fabricated_scale_or_warning():
    pytest.importorskip("statsmodels")
    x = np.arange(6)
    p = mp.plot({"x": x, "y": 2 + 3 * x}).residplot(
        "x", "y", regression={"model": "robust"}
    )
    points = np.asarray(p.render().axes[0].collections[0].get_offsets(), dtype=float)
    np.testing.assert_allclose(points[:, 1], 0, atol=1e-12)


def test_residuals_are_fitted_per_selected_group_and_facet():
    raw = {
        "x": [1, 2, 3] * 4,
        "y": [1, 3, 2, 2, 4, 7, 10, 12, 11, 20, 23, 21],
        "g": ["B"] * 3 + ["A"] * 3 + ["B"] * 3 + ["A"] * 3,
        "site": ["N"] * 6 + ["S"] * 6,
    }
    p = mp.plot(raw).residplot("x", "y", group="g").facet(col="site").size(8, 4)
    assert p.spec.data.columns == raw and mp.validate(p.spec) == []
    axes = p.render().axes
    for cell, ax in enumerate(axes):
        collections = [c for c in ax.collections if isinstance(c, PathCollection)]
        assert len(collections) == 2
        for group_index, collection in enumerate(collections):
            start = cell * 6 + group_index * 3
            values = raw["y"][start : start + 3]
            expected = values - np.polyval(np.polyfit([1, 2, 3], values, 1), [1, 2, 3])
            np.testing.assert_allclose(
                np.asarray(collection.get_offsets(), dtype=float)[:, 1],
                expected,
                atol=1e-12,
            )
        assert len(ax.lines) == 1


@pytest.mark.parametrize(
    "config,degree,confidence",
    [
        ({"model": "bad"}, 1, None),
        ({"residual": "yes"}, 1, None),
        ({"model": "robust"}, 2, None),
        ({"model": "logx"}, 2, None),
        ({"residual": True}, 1, 95),
        ({"model": "robust"}, 1, 95),
        ({"model": "logistic"}, 1, 95),
        ({"model": "lowess"}, 1, 95),
        ({"frac": 0.5}, 1, None),
        ({"iterations": 2}, 1, None),
        ({"model": "lowess", "frac": 0}, 1, None),
        ({"model": "lowess", "frac": True}, 1, None),
        ({"model": "lowess", "iterations": -1}, 1, None),
    ],
)
def test_invalid_configuration_is_reported_without_mutation(config, degree, confidence):
    spec = mp.plot(data()).regplot("x", "y", degree=degree, confidence=confidence).spec
    spec.panels[0].layers[0].regression = mp.RegressionSpec(**config)
    before = copy.deepcopy(spec)
    assert mp.validate(spec) and spec == before


@pytest.mark.parametrize(
    "model,raw",
    [
        ("logx", {"x": [0, 1, 2], "y": [1, 2, 3]}),
        ("logistic", {"x": [1, 2, 3], "y": [1, 1, 1]}),
        ("logistic", {"x": [1, 2, 3], "y": [0, 1, 2]}),
        ("lowess", {"x": [1, 1, 2], "y": [1, 2, 3]}),
    ],
)
def test_unsafe_model_data_fail_before_optional_effects(model, raw):
    assert mp.validate(mp.plot(raw).regplot("x", "y", regression={"model": model}).spec)


def test_selected_groups_precede_data_validation_and_joint_rejects_residual_marginals():
    raw = {"x": [-1, 1, 2, 3], "y": [1, 2, 3, 4], "g": ["omit", "A", "A", "A"]}
    p = mp.plot(raw).regplot(
        "x", "y", group="g", hue_order=["A"], regression={"model": "logx"}
    )
    assert mp.validate(p.spec) == []
    assert p.render().axes[0].lines
    q = mp.plot(data()).residplot("x", "y")
    before, history = q.spec, q.action_log
    with pytest.raises(ValueError, match="raw y"):
        q.joint()
    assert q.spec == before and q.action_log == history
    assert mp.validate(q.yscale("log").spec)


def test_non_regression_layer_options_are_not_ignored_and_settings_are_copied():
    config = mp.RegressionSpec(residual=True)
    p = mp.plot(data()).regplot("x", "y", regression=config)
    config.residual = False
    stored = p.spec.panels[0].layers[0].regression
    assert stored is not None and stored.residual is True
    wrong = mp.plot(data()).scatter("x", "y", regression=config)
    assert any(
        "regression is not supported" in issue for issue in mp.validate(wrong.spec)
    )
    with pytest.raises(ValueError, match="unknown"):
        mp.plot(data()).regplot("x", "y", regression={"unknown": True})


def test_regression_resource_guards_are_bounded():
    raw = {
        "x": list(range(MAX_REGRESSION_ROWS + 1)),
        "y": list(range(MAX_REGRESSION_ROWS + 1)),
    }
    assert any(
        "at most" in issue
        for issue in mp.validate(mp.plot(raw).residplot("x", "y").spec)
    )
    raw = {"x": list(range(MAX_LOWESS_ROWS + 1)), "y": list(range(MAX_LOWESS_ROWS + 1))}
    assert any(
        "at most" in issue
        for issue in mp.validate(
            mp.plot(raw).regplot("x", "y", regression={"model": "lowess"}).spec
        )
    )
    assert mp.validate(
        mp.plot(data())
        .regplot("x", "y", regression={"model": "lowess", "frac": 0.01})
        .spec
    )


def test_optional_dependency_error_is_explicit_and_preserves_output(
    tmp_path, monkeypatch
):
    original_import = builtins.__import__

    def without_statsmodels(name, *args, **kwargs):
        if name.startswith("statsmodels"):
            raise ImportError("simulated absent extra")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_statsmodels)
    p = mp.plot(data()).regplot("x", "y", regression={"model": "robust"})
    path = tmp_path / "keep.png"
    path.write_bytes(b"previous output")
    with pytest.raises(ImportError, match=r"mudplot\[regression\]"):
        p.save(str(path))
    assert path.read_bytes() == b"previous output" and not plt.get_fignums()


def test_separation_is_not_a_silent_logistic_fit(tmp_path):
    pytest.importorskip("statsmodels")
    p = mp.plot({"x": list(range(8)), "y": [0] * 4 + [1] * 4}).regplot(
        "x", "y", regression={"model": "logistic"}
    )
    path = tmp_path / "keep.svg"
    path.write_bytes(b"previous output")
    with pytest.raises(ValueError, match="logistic regression fit failed"):
        p.save(str(path))
    assert path.read_bytes() == b"previous output" and not plt.get_fignums()


@pytest.mark.parametrize("model", ["poly", "logx", "robust", "lowess"])
@pytest.mark.parametrize("extension", ["png", "pdf", "svg"])
def test_models_exports_reproduce_and_leave_global_rng(tmp_path, model, extension):
    if model in ("robust", "lowess"):
        pytest.importorskip("statsmodels")
    state = np.random.get_state()
    p = mp.plot(data()).regplot("x", "y", regression={"model": model}).size(6, 4)
    assert mp.apply(p.action_log) == mp.Plot.from_json(p.to_json()).spec == p.spec
    a, b = tmp_path / f"a.{extension}", tmp_path / f"b.{extension}"
    plt.close(p.save(str(a)))
    plt.close(mp.Plot.from_json(p.to_json()).save(str(b)))
    assert a.read_bytes() == b.read_bytes()
    after = np.random.get_state()
    assert state[0] == after[0] and state[2:] == after[2:]
    np.testing.assert_array_equal(state[1], after[1])


def test_core_schema_editor_and_legacy_default_roundtrip():
    import jsonschema
    from dashboard.editor_server import EditorSession

    p = mp.plot(data()).residplot("x", "y").size(6, 4)
    jsonschema.validate(p.spec.to_dict(), mp.json_schema())
    session = EditorSession()
    session.load_spec(p.to_json())
    assert session.store.state == p.spec and b"<svg" in session.export("svg")
    old = mp.plot(data()).regplot("x", "y").spec.to_dict()
    del old["panels"][0]["layers"][0]["regression"]
    assert mp.FigureSpec.from_dict(old).panels[0].layers[0].regression is None


@pytest.mark.parametrize("scale", [1e-250, 1e250])
def test_typed_polynomial_scaling_stays_finite_in_extreme_units(scale):
    x = np.arange(1, 12, dtype=float) * scale
    y = (2 + 3 * np.arange(1, 12, dtype=float)) * scale
    p = mp.plot({"x": x, "y": y}).regplot("x", "y", regression={}).size(6, 4)
    line = p.render().axes[0].lines[0]
    grid = np.asarray(line.get_xdata(), dtype=float) / scale
    prediction = np.asarray(line.get_ydata(), dtype=float) / scale
    np.testing.assert_allclose(prediction, 2 + 3 * grid, rtol=1e-12, atol=1e-12)


def test_typed_log_coordinate_axes_reject_hidden_nonpositive_rows():
    p = (
        mp.plot({"x": [-1, 1, 2], "y": [1, 2, 3]})
        .regplot("x", "y", regression={})
        .xscale("log")
    )
    assert any("positive coordinates" in issue for issue in mp.validate(p.spec))
    q = (
        mp.plot({"x": [1, 2, 3], "y": [-1, 2, 3]})
        .regplot("x", "y", regression={})
        .yscale("log")
    )
    assert any("positive coordinates" in issue for issue in mp.validate(q.spec))


def test_pure_core_builds_all_models_without_optional_libraries():
    script = (
        "import sys; import mudplot as m; d={'x':[1,2,3,4],'y':[0,1,0,1]}; "
        "ps=[m.plot(d).regplot('x','y',regression={'model':k}) "
        "for k in ('poly','logx','robust','logistic','lowess')]; "
        "ps.append(m.plot(d).residplot('x','y')); "
        "assert all(m.validate(p.spec)==[] for p in ps); "
        "assert all(m.apply(p.action_log)==p.spec for p in ps); "
        "assert all(m.Plot.from_json(p.to_json()).spec==p.spec for p in ps); "
        "assert 'numpy' not in sys.modules and 'statsmodels' not in sys.modules "
        "and 'matplotlib' not in sys.modules"
    )
    subprocess.run([sys.executable, "-S", "-c", script], check=True)
