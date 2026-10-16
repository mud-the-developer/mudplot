"""Public statistical plots: geometry, honest intervals and serialized settings."""

import json
from typing import Any

import matplotlib

matplotlib.use("Agg")

import mudplot as mp
import numpy as np
import pytest
from matplotlib.container import BarContainer, ErrorbarContainer
from mudplot import actions as A
from mudplot._estimate import summarize
from mudplot.spec import LayerSpec, StatSpec


def _data():
    return {
        "x": ["High"] * 3 + ["Control"] * 3 + ["High"] * 3 + ["Low"] * 3,
        "y": [3, 4, 5, 1, 2, 3, 6, 7, 8, 2, 3, 4],
        "g": ["A"] * 6 + ["B"] * 6,
    }


def _bars(ax):
    return [c for c in ax.containers if isinstance(c, BarContainer)]


def _ranges(ax):
    return [c for c in ax.containers if isinstance(c, ErrorbarContainer)]


def test_raw_barplot_aggregates_and_dodges_sd_ranges_on_real_bar_centers():
    p = mp.plot(_data()).barplot("x", "y", group="g", errorbar="sd")
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    bars = _bars(ax)
    assert len(bars) == 2
    for i, (values, centers) in enumerate(
        (([4, 2], [-0.2, 0.8]), ([7, 3], [0.2, 2.2]))
    ):
        np.testing.assert_allclose([b.get_height() for b in bars[i]], values)
        np.testing.assert_allclose(
            [b.get_x() + b.get_width() / 2 for b in bars[i]], centers
        )
        errors = bars[i].errorbar
        assert errors is not None
        segments = np.asarray(errors.lines[2][0].get_segments())
        np.testing.assert_allclose(segments[:, 0, 0], centers)
        np.testing.assert_allclose(segments[:, 0, 1], np.array(values) - 1)
        np.testing.assert_allclose(segments[:, 1, 1], np.array(values) + 1)
    assert [t.get_text() for t in ax.get_xticklabels()] == ["High", "Control", "Low"]
    assert ax.get_legend_handles_labels()[1] == ["A", "B"]


@pytest.mark.parametrize("kind", ["barplot", "pointplot"])
def test_percentile_interval_outside_estimate_is_not_clipped_or_rejected(kind):
    p = getattr(mp.plot({"x": ["A"] * 4, "y": [1, 2, 3, 100]}), kind)(
        "x", "y", estimator="min", errorbar=("pi", 50)
    )
    ax = p.render().axes[0]
    segments = _ranges(ax)[0].lines[2][0].get_segments()
    np.testing.assert_allclose(segments, [[[0, 1.75], [0, 27.25]]])
    if kind == "barplot":
        assert _bars(ax)[0][0].get_height() == 1
    else:
        assert ax.lines[0].get_ydata()[0] == 1
    assert ax.get_ylim()[1] > 27.25


def test_pointplot_dodge_and_missing_cells_break_the_line():
    ax = (
        mp.plot(_data())
        .pointplot("x", "y", group="g", errorbar=None, dodge=0.4)
        .render()
        .axes[0]
    )
    assert len(ax.lines) == 2
    np.testing.assert_allclose(np.asarray(ax.lines[0].get_xdata()), [-0.1, 0.9])
    np.testing.assert_allclose(np.asarray(ax.lines[0].get_ydata()), [4, 2])
    np.testing.assert_allclose(np.asarray(ax.lines[1].get_xdata()), [0.1, np.nan, 2.1])
    np.testing.assert_allclose(np.asarray(ax.lines[1].get_ydata()), [7, np.nan, 3])
    assert ax.get_legend_handles_labels()[1] == ["A", "B"]


def test_countplot_requires_no_y_and_counts_categories_not_summary_heights():
    data = {"x": ["B", "A", "B", "C", "A", None]}
    p = mp.plot(data).countplot("x")
    assert mp.validate(p.spec) == []
    bars = _bars(p.render().axes[0])[0]
    assert [b.get_height() for b in bars] == [2, 2, 1]
    assert bars.errorbar is None


def test_numeric_categories_are_ordinal_in_first_seen_order():
    p = mp.plot({"x": [100, 1, 100, 1], "y": [2, 3, 4, 5]}).barplot(
        "x", "y", errorbar=None
    )
    ax = p.render().axes[0]
    np.testing.assert_allclose(
        [b.get_x() + b.get_width() / 2 for b in _bars(ax)[0]], [0, 1]
    )
    assert [t.get_text() for t in ax.get_xticklabels()] == ["100", "1"]


@pytest.mark.parametrize("kind", ["barplot", "pointplot"])
def test_zero_error_width_caps_and_point_strokes_remain_explicit(kind):
    p = getattr(mp.plot(_data()), kind)(
        "x",
        "y",
        errorbar="se",
        line_width=0,
        capsize=0,
        capthick=0,
        error_line_width=0,
        **({"marker_size": 0} if kind == "pointplot" else {}),
    )
    ax = p.render().axes[0]
    for errors in _ranges(ax):
        assert errors.lines[1] == ()
        assert np.all(np.asarray(errors.lines[2][0].get_linewidth()) == 0)
    if kind == "pointplot":
        assert ax.lines[0].get_linewidth() == 0 and ax.lines[0].get_markersize() == 0
    else:
        assert all(b.get_linewidth() == 0 for b in ax.patches)


@pytest.mark.parametrize("kind", ["barplot", "pointplot", "countplot"])
def test_statistics_routes_to_secondary_axis_and_roundtrips_actions(kind):
    p = mp.plot(_data()).secondary_yaxis("Estimate")
    kwargs: dict[str, Any] = {"group": "g", "axis": "y2"}
    if kind == "countplot":
        p.countplot("x", **kwargs)
    else:
        getattr(p, kind)("x", "y", errorbar="sd", **kwargs)
    assert mp.Plot.from_json(p.to_json()).spec == p.spec
    assert mp.apply(p.action_log) == p.spec
    axes = p.render().axes
    assert not axes[0].patches and not axes[0].lines and not axes[0].collections
    assert axes[1].patches or axes[1].lines


@pytest.mark.parametrize("kind", ["barplot", "pointplot"])
def test_singleton_estimate_remains_visible_with_explicit_interval_warning(kind):
    p = getattr(mp.plot({"x": ["A"], "y": [3]}), kind)("x", "y")
    with pytest.warns(UserWarning, match="fewer than 2"):
        ax = p.render().axes[0]
    assert not _ranges(ax)
    assert ax.patches or ax.lines


def test_missing_rows_are_dropped_without_mutating_raw_data():
    data = {"x": ["A", "A", "A", None], "y": [1, None, 3, 100]}
    p = mp.plot(data).barplot("x", "y", errorbar=None)
    ax = p.render().axes[0]
    assert len(ax.patches) == 1 and _bars(ax)[0][0].get_height() == 2
    assert p.spec.data.columns == data


@pytest.mark.parametrize(
    "settings,message",
    [
        ({"estimator": "unknown"}, "unknown estimator"),
        ({"estimator": lambda x: 0}, "unknown estimator"),
        ({"errorbar": "SEM"}, "unknown errorbar"),
        ({"estimator": "median", "errorbar": "se"}, "sample-mean SEM"),
        ({"estimator": "count"}, "count estimator requires"),
        ({"errorbar": ("ci", 101)}, "at most 100"),
        ({"errorbar": ("sd", -1)}, "positive and finite"),
        ({"n_boot": 0}, "n_boot"),
        ({"n_boot": True}, "n_boot"),
        ({"n_boot": 100001}, "n_boot"),
        ({"seed": -1}, "seed"),
        ({"seed": True}, "seed"),
        ({"yerr": "y"}, "yerr is not supported"),
        ({"confidence": 95}, "confidence is not supported"),
    ],
)
def test_invalid_or_ignored_statistical_options_fail_before_rendering(
    settings, message
):
    p = mp.plot(_data()).barplot("x", "y", **settings)
    assert any(message in issue for issue in mp.validate(p.spec))
    with pytest.raises(ValueError, match="invalid FigureSpec"):
        p.render()


@pytest.mark.parametrize(
    "field,value", [("dodge", -1), ("dodge", True), ("marker_size", -1)]
)
def test_invalid_point_style_is_reported(field, value):
    p = mp.plot(_data()).pointplot("x", "y", **{field: value})
    assert any(field in issue for issue in mp.validate(p.spec))


@pytest.mark.parametrize(
    "values,message",
    [
        ([None, None], "no usable observations"),
        ([True, False], "finite numbers"),
        (["1", "2"], "finite numbers"),
    ],
)
def test_bad_or_empty_observation_data_has_a_clear_error(values, message):
    p = mp.plot({"x": ["A", "A"], "y": values}).barplot("x", "y")
    assert any(message in issue for issue in mp.validate(p.spec))


@pytest.mark.parametrize(
    "categories,message",
    [
        ([["A"], ["B"]], "strings or finite scalars"),
        ([1, "1"], "labels collide"),
    ],
)
def test_malformed_categories_fail_without_hashing_or_drawing_them(categories, message):
    p = mp.plot({"x": categories, "y": [1, 2]}).barplot("x", "y")
    assert any(message in issue for issue in mp.validate(p.spec))


@pytest.mark.parametrize("kind", ["barplot", "pointplot", "countplot"])
def test_unsupported_projection_and_ordinal_log_category_are_explicit(kind):
    p = mp.plot(_data())
    getattr(p, kind)("x", **({"y": "y"} if kind != "countplot" else {}))
    p.xscale("log")
    assert any(
        "log category axis requires native_scale=True" in issue
        for issue in mp.validate(p.spec)
    )
    p.xscale("linear").projection_polar()
    assert any("polar" in issue for issue in mp.validate(p.spec))


def test_countplot_rejects_other_statistics_and_primitive_bar_does_not_infer():
    p = mp.plot(_data()).dispatch(
        A.AddLayer(LayerSpec(type="countplot", x="x", stat=StatSpec()))
    )
    assert any("countplot requires" in issue for issue in mp.validate(p.spec))
    primitive = mp.plot(_data()).bar("x", "y", stat=StatSpec())
    assert any(
        "stat is not supported" in issue for issue in mp.validate(primitive.spec)
    )


def test_unknown_nested_statistics_options_are_not_silently_discarded():
    p = mp.plot(_data()).barplot("x", "y")
    raw = json.loads(p.to_json())
    raw["panels"][0]["layers"][0]["stat"]["callable"] = "custom"
    with pytest.raises(ValueError, match="unknown StatSpec field"):
        mp.Plot.from_json(json.dumps(raw))


def test_json_schema_recognizes_statistical_configuration():
    import jsonschema

    p = mp.plot(_data()).pointplot("x", "y", errorbar=("ci", 90), n_boot=101, seed=42)
    jsonschema.validate(p.spec.to_dict(), mp.json_schema())
    assert "StatSpec" in mp.json_schema()["$defs"]


def test_bootstrap_render_and_exports_are_reproducible(tmp_path):
    p = (
        mp.plot(_data())
        .theme("publication")
        .barplot("x", "y", group="g", errorbar=("ci", 95), n_boot=101, seed=42)
        .size(4, 3)
    )
    for extension in ("png", "svg"):
        first, second = tmp_path / f"a.{extension}", tmp_path / f"b.{extension}"
        p.save(first)
        mp.Plot.from_json(p.to_json()).save(second)
        assert first.read_bytes() == second.read_bytes()


def test_editor_json_path_accepts_statistical_layers_and_rejects_unknown_options():
    from dashboard.editor_server import EditorSession, _build_action

    session = EditorSession()
    session.dispatch_safe(A.SetData(_data()))
    session.dispatch_safe(
        _build_action(
            "add_layer_json",
            {
                "layer_type": "barplot",
                "layer_json": json.dumps(
                    {
                        "x": "x",
                        "y": "y",
                        "group": "g",
                        "stat": {"errorbar": "sd", "estimator": "mean"},
                    }
                ),
            },
            session.store.state,
        )
    )
    assert session.error is None and session.png.startswith(b"\x89PNG")
    assert b"<svg" in session.export("svg")
    with pytest.raises(ValueError, match="unknown StatSpec"):
        _build_action(
            "add_layer_json",
            {
                "layer_type": "barplot",
                "layer_json": json.dumps(
                    {
                        "x": "x",
                        "y": "y",
                        "stat": {"callable": "custom"},
                    }
                ),
            },
            session.store.state,
        )


def test_rendered_ci_matches_shared_numerical_effect():
    p = mp.plot(_data()).barplot("x", "y", errorbar=("ci", 80), n_boot=101, seed=42)
    summary = summarize(p.spec.data.columns, p.spec.panels[0].layers[0])
    ranges = _ranges(p.render().axes[0])[0].lines[2][0].get_segments()
    expected = []
    for point in summary.estimates:
        assert point.lower is not None and point.upper is not None
        expected.append([point.lower, point.upper])
    np.testing.assert_allclose(np.asarray(ranges)[:, :, 1], expected)
