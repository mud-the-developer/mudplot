"""Bar uncertainty is supplied, never inferred; styling must not move the data."""

from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.image as mimage
import mudplot as mp
import numpy as np
import pytest
from matplotlib.colors import to_rgba
from matplotlib.container import BarContainer, ErrorbarContainer
from mudplot import actions as A
from mudplot.spec import LayerSpec
from mudplot.theme import spec_to_rcparams, theme_preset


def _data():
    return {
        "dose": ["Control", "Low", "High"] * 2,
        "mean": [1.0, 1.4, 1.9, 0.9, 1.6, 2.3],
        "sd": [0.1, 0.2, 0.15, 0.08, 0.12, 0.18],
        "lo": [0.85, 1.3, 1.7, 0.8, 1.4, 2.2],
        "hi": [1.12, 1.6, 2.0, 1.15, 1.7, 2.55],
        "cell": ["A"] * 3 + ["B"] * 3,
    }


def _bars(ax):
    return [c for c in ax.containers if isinstance(c, BarContainer)]


def _segments(errors):
    return np.asarray(errors.lines[2][-1].get_segments())


def test_grouped_bar_sd_is_centered_on_each_dodged_bar_and_not_rescaled():
    data = _data()
    p = mp.plot(data).bar("dose", "mean", group="cell", yerr="sd")
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    for i, bars in enumerate(_bars(ax)):
        centers = np.array([b.get_x() + b.get_width() / 2 for b in bars])
        y = np.array(data["mean"][i * 3 : (i + 1) * 3])
        sd = np.array(data["sd"][i * 3 : (i + 1) * 3])
        expected = np.stack(
            [np.column_stack([centers, y - sd]), np.column_stack([centers, y + sd])],
            axis=1,
        )
        np.testing.assert_allclose(_segments(bars.errorbar), expected)
        np.testing.assert_allclose(centers, np.arange(3) + (-0.2 if i == 0 else 0.2))
    assert [t.get_text() for t in ax.get_xticklabels()] == ["Control", "Low", "High"]
    assert len(ax.get_legend_handles_labels()[0]) == 2


@pytest.mark.parametrize("kind", ["bar", "errorbar"])
def test_absolute_ci_endpoints_render_exactly_without_symmetrizing(kind):
    data = _data()
    p = getattr(mp.plot(data), kind)("dose", "mean", y_lower="lo", y_upper="hi")
    ax = p.render().axes[0]
    errors = next(c for c in ax.containers if isinstance(c, ErrorbarContainer))
    segments = _segments(errors)
    np.testing.assert_allclose(segments[:, 0, 1], data["lo"])
    np.testing.assert_allclose(segments[:, 1, 1], data["hi"])
    assert ax.get_ylim()[1] > max(data["hi"])


@pytest.mark.parametrize("interval", [False, True])
def test_missing_categories_keep_errorbars_with_their_own_group(interval):
    data = {
        "dose": ["High", "Control", "High", "Low"],
        "mean": [3, 1, 4, 2],
        "cell": ["A", "A", "B", "B"],
        "sd": [0.1, 0.2, 0.3, 0.4],
        "lo": [2.9, 0.8, 3.7, 1.6],
        "hi": [3.1, 1.2, 4.3, 2.4],
    }
    uncertainty: dict[str, Any] = (
        {"y_lower": "lo", "y_upper": "hi"} if interval else {"yerr": "sd"}
    )
    ax = mp.plot(data).bar("dose", "mean", group="cell", **uncertainty).render().axes[0]
    for bars in _bars(ax):
        centers = [b.get_x() + b.get_width() / 2 for b in bars]
        np.testing.assert_allclose(
            _segments(bars.errorbar)[:, :, 0],
            np.repeat(np.array(centers)[:, None], 2, axis=1),
        )
    np.testing.assert_allclose(_segments(_bars(ax)[0].errorbar)[:, 0, 1], [2.9, 0.8])
    np.testing.assert_allclose(_segments(_bars(ax)[1].errorbar)[:, 1, 1], [4.3, 2.4])
    assert [t.get_text() for t in ax.get_xticklabels()] == ["High", "Control", "Low"]


def test_bar_width_outlines_error_strokes_and_alpha_are_independent():
    p = mp.plot(_data()).bar(
        "dose",
        "mean",
        group="cell",
        yerr="sd",
        bar_width=0.6,
        edge_color="#445566",
        line_width=0.5,
        error_color="#112233",
        error_line_width=0.75,
        capsize=4,
        capthick=0.9,
        alpha=0.7,
    )
    for bars in _bars(p.render().axes[0]):
        assert bars.errorbar is not None
        for patch in bars:
            assert patch.get_width() == pytest.approx(0.3 * 0.92)
            assert patch.get_linewidth() == 0.5
            np.testing.assert_allclose(patch.get_edgecolor(), to_rgba("#445566", 0.7))
        caps = bars.errorbar.lines[1]
        assert len(caps) == 2
        for cap in caps:
            assert cap.get_markersize() == 8
            assert cap.get_markeredgewidth() == 0.9
            assert cap.get_alpha() == 0.7
        for line in bars.errorbar.lines[2]:
            assert np.atleast_1d(line.get_linewidth())[0] == 0.75
            np.testing.assert_allclose(
                np.asarray(line.get_colors()[0]), to_rgba("#112233", 0.7)
            )


@pytest.mark.parametrize("kind", ["bar", "errorbar"])
def test_explicit_zero_caps_and_error_widths_are_not_replaced_by_defaults(kind):
    p = getattr(mp.plot(_data()), kind)(
        "dose",
        "mean",
        yerr="sd",
        capsize=0,
        capthick=0,
        error_line_width=0,
        line_width=0,
    )
    errors = next(
        c for c in p.render().axes[0].containers if isinstance(c, ErrorbarContainer)
    )
    assert errors.lines[1] == ()
    assert np.atleast_1d(errors.lines[2][0].get_linewidth())[0] == 0


def test_bar_default_errors_are_thin_neutral_and_capped():
    bars = _bars(mp.plot(_data()).bar("dose", "mean", yerr="sd").render().axes[0])[0]
    assert bars.errorbar is not None
    assert len(bars.errorbar.lines[1]) == 2
    assert bars.errorbar.lines[1][0].get_markersize() == 6
    assert np.atleast_1d(bars.errorbar.lines[2][0].get_linewidth())[0] == 1.1
    np.testing.assert_allclose(
        np.asarray(bars.errorbar.lines[2][0].get_colors()[0]), to_rgba("#30343b")
    )


def test_existing_errorbar_defaults_still_use_two_point_caps_and_series_color():
    p = mp.plot(_data()).errorbar("dose", "mean", yerr="sd", color="#567890")
    errors = next(
        c for c in p.render().axes[0].containers if isinstance(c, ErrorbarContainer)
    )
    assert errors.lines[1][0].get_markersize() == 4
    np.testing.assert_allclose(
        np.asarray(errors.lines[2][0].get_colors()[0]), to_rgba("#567890")
    )


@pytest.mark.parametrize("interval", [False, True])
def test_bar_uncertainty_routes_to_secondary_axis(interval):
    fields: dict[str, Any] = (
        {"y_lower": "lo", "y_upper": "hi"} if interval else {"yerr": "sd"}
    )
    p = (
        mp.plot(_data())
        .secondary_yaxis("Response")
        .bar("dose", "mean", group="cell", axis="y2", **fields)
    )
    axes = p.render().axes
    assert not axes[0].patches and not axes[0].containers
    assert len(_bars(axes[1])) == 2
    assert all(b.errorbar is not None for b in _bars(axes[1]))


@pytest.mark.parametrize("interval", [False, True])
def test_polar_bar_uncertainty_uses_radius_and_angular_bar_centers(interval):
    data = {
        "angle": [0.2, 1.5],
        "mean": [1.0, 2.0],
        "sd": [0.1, 0.2],
        "lo": [0.85, 1.7],
        "hi": [1.2, 2.1],
    }
    fields: dict[str, Any] = (
        {"y_lower": "lo", "y_upper": "hi"} if interval else {"yerr": "sd"}
    )
    p = mp.plot(data).projection_polar().bar("angle", "mean", bar_width=0.4, **fields)
    ax = p.render().axes[0]
    assert ax.name == "polar"
    segments = _segments(_bars(ax)[0].errorbar)
    np.testing.assert_allclose(segments[:, 0, 0], data["angle"])
    np.testing.assert_allclose(
        segments[:, 0, 1], data["lo"] if interval else [0.9, 1.8]
    )
    np.testing.assert_allclose(
        segments[:, 1, 1], data["hi"] if interval else [1.1, 2.2]
    )


def test_negative_and_zero_bars_keep_errors_at_the_signed_value():
    ax = (
        mp.plot({"x": [0, 1], "mean": [-2, 0], "sd": [0.3, 0.2]})
        .bar("x", "mean", yerr="sd")
        .render()
        .axes[0]
    )
    np.testing.assert_allclose(
        _segments(_bars(ax)[0].errorbar)[:, :, 1], [[-2.3, -1.7], [-0.2, 0.2]]
    )


@pytest.mark.parametrize("kind", ["bar", "errorbar"])
@pytest.mark.parametrize(
    "fields,message",
    [
        ({"y_lower": "lo"}, "supplied together"),
        ({"y_upper": "hi"}, "supplied together"),
        ({"yerr": "sd", "y_lower": "lo", "y_upper": "hi"}, "not both"),
        ({"y_lower": "hi", "y_upper": "lo"}, "y_lower <= y <= y_upper"),
        ({"y_lower": "lo", "y_upper": "lo"}, "y_lower <= y <= y_upper"),
        ({"yerr": "missing"}, "not found"),
        ({"y_lower": "", "y_upper": "hi"}, "non-empty column"),
        ({"y_lower": 3, "y_upper": "hi"}, "non-empty column"),
    ],
)
def test_invalid_uncertainty_contracts_fail_before_matplotlib(kind, fields, message):
    p = getattr(mp.plot(_data()), kind)("dose", "mean", **fields)
    assert any(message in issue for issue in mp.validate(p.spec))
    with pytest.raises(ValueError, match="invalid FigureSpec"):
        p.render()


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), True, "0.1"])
@pytest.mark.parametrize("field", ["yerr", "xerr"])
def test_error_magnitudes_must_be_nonnegative_finite_numbers(value, field):
    data = {"x": [0], "y": [1], "error": [value]}
    options: dict[str, Any] = {field: "error"}
    p = mp.plot(data).errorbar("x", "y", **options)
    assert any("finite, nonnegative" in issue for issue in mp.validate(p.spec))


@pytest.mark.parametrize("field", ["lo", "hi", "mean"])
def test_nonfinite_interval_endpoints_and_centers_are_rejected(field):
    data = _data()
    data[field][0] = float("nan")
    p = mp.plot(data).bar("dose", "mean", y_lower="lo", y_upper="hi")
    assert any("must be finite numbers" in issue for issue in mp.validate(p.spec))


def test_finite_endpoints_with_overflowing_error_distance_are_rejected():
    p = mp.plot({"x": [0], "y": [1e308], "lo": [-1e308], "hi": [1e308]}).bar(
        "x", "y", y_lower="lo", y_upper="hi"
    )
    assert any("error magnitudes must be finite" in i for i in mp.validate(p.spec))


def test_zero_uncertainty_and_bounds_at_center_remain_valid():
    data = {"x": [0], "y": [1], "zero": [0]}
    symmetric = mp.plot(data).bar("x", "y", yerr="zero")
    interval = mp.plot(data).bar("x", "y", y_lower="y", y_upper="y")
    for p in (symmetric, interval):
        assert mp.validate(p.spec) == []
        errors = _bars(p.render().axes[0])[0].errorbar
        np.testing.assert_allclose(_segments(errors), [[[0, 1], [0, 1]]])


def test_misaligned_interval_columns_report_validation_issue_not_index_error():
    data = _data()
    data["lo"] = [0.5]
    p = mp.plot(data).bar("dose", "mean", y_lower="lo", y_upper="hi")
    assert any("mismatched lengths" in issue for issue in mp.validate(p.spec))


@pytest.mark.parametrize(
    "field,value",
    [
        ("bar_width", 0),
        ("bar_width", float("inf")),
        ("bar_width", True),
        ("line_width", -1),
        ("error_line_width", -1),
        ("capthick", -1),
        ("capsize", -1),
        ("capsize", True),
        ("error_color", ""),
        ("edge_color", 123),
    ],
)
def test_invalid_bar_style_is_caught_in_dependency_free_validation(field, value):
    p = mp.plot(_data()).bar("dose", "mean", **{field: value})
    assert any(field in issue for issue in mp.validate(p.spec))


@pytest.mark.parametrize(
    "field,value",
    [
        ("bar_width", 0.6),
        ("edge_color", "black"),
        ("error_line_width", 1),
        ("error_color", "gray"),
        ("capthick", 1),
        ("y_lower", "lo"),
        ("y_upper", "hi"),
    ],
)
def test_bar_and_error_style_fields_are_not_silently_ignored_by_other_layers(
    field, value
):
    p = mp.plot(_data()).line("dose", "mean", **{field: value})
    assert any(f"{field} is not supported" in issue for issue in mp.validate(p.spec))


def test_new_fields_roundtrip_through_json_and_actions_without_mutating_data():
    data = _data()
    p = (
        mp.plot(data)
        .theme("publication")
        .bar(
            "dose",
            "mean",
            group="cell",
            y_lower="lo",
            y_upper="hi",
            bar_width=0.64,
            edge_color="#777777",
            error_color="#333333",
            line_width=0.4,
            error_line_width=1.0,
            capsize=3,
            capthick=0.8,
        )
    )
    restored = mp.Plot.from_json(p.to_json())
    assert restored.spec == p.spec
    replayed = mp.apply(p.action_log)
    assert replayed == p.spec
    assert data == _data()
    layer = p.spec.panels[0].layers[0]
    action = A.AddLayer(layer=layer)
    assert A.action_from_dict(A.action_to_dict(action)) == action


def test_old_bar_specs_keep_geometry_and_default_hatches_without_errors():
    layer = LayerSpec.from_dict(
        {"type": "bar", "x": "dose", "y": "mean", "group": "cell"}
    )
    assert isinstance(layer, LayerSpec)
    p = mp.plot(_data()).dispatch(A.AddLayer(layer))
    bars = _bars(p.render().axes[0])
    assert len(bars) == 2
    assert all(b.errorbar is None for b in bars)
    assert bars[0][0].get_width() == pytest.approx(0.4 * 0.92)
    assert bars[0][0].get_hatch() == ""
    assert bars[1][0].get_hatch() == "//"
    assert p.spec.theme == theme_preset("paper")


def test_publication_theme_is_opt_in_and_keeps_grid_behind_bars():
    theme = theme_preset("publication")
    assert theme.redundant_encoding
    assert theme.palette.preset == "soft"
    assert theme.grid.show and theme.grid.axis == "y"
    assert "publication" in mp.capabilities()["themes"]
    assert spec_to_rcparams(theme)["axes.axisbelow"] is True
    p = mp.plot(_data()).bar("dose", "mean", yerr="sd").theme("publication")
    ax = p.render().axes[0]
    assert ax.get_axisbelow() is True
    assert any(line.get_visible() for line in ax.get_ygridlines())
    assert not any(line.get_visible() for line in ax.get_xgridlines())
    assert ax.yaxis.get_zorder() < ax.patches[0].get_zorder()
    assert not ax.spines["top"].get_visible()
    assert not ax.spines["right"].get_visible()
    assert theme_preset("paper").grid.show is False
    assert theme_preset("paper").palette.preset is None


def test_seeded_sd_and_ci_examples_are_valid_reproducible_and_distinct():
    from examples.bar_uncertainty import (
        MEANS,
        SDS,
        build_comparison,
        synthetic_summaries,
    )

    data = synthetic_summaries()
    assert synthetic_summaries() == data
    assert data["response"] == MEANS
    np.testing.assert_allclose(data["sd"], SDS)
    comparison = build_comparison(data)
    assert mp.validate(comparison.spec) == []
    layers = [p.layers[0] for p in comparison.spec.panels]
    assert layers[0].yerr == "sd"
    assert layers[1].y_lower == "ci_low" and layers[1].y_upper == "ci_high"
    assert layers[1].yerr is None
    lower_errors = np.asarray(data["response"]) - data["ci_low"]
    upper_errors = np.asarray(data["ci_high"]) - data["response"]
    assert not np.allclose(lower_errors, upper_errors)
    assert not np.allclose(lower_errors, data["sd"])


def test_dashboard_json_layer_and_theme_controls_accept_bar_intervals():
    import json

    from dashboard.editor_server import EditorSession, _build_action
    from dashboard.editor_view import render_page

    session = EditorSession()
    session.dispatch_safe(A.SetData(_data()))
    session.dispatch_safe(A.SetTheme("publication"))
    action = _build_action(
        "add_layer_json",
        {
            "layer_type": "bar",
            "layer_json": json.dumps(
                {
                    "x": "dose",
                    "y": "mean",
                    "group": "cell",
                    "y_lower": "lo",
                    "y_upper": "hi",
                    "bar_width": 0.6,
                    "capsize": 0,
                }
            ),
        },
        session.store.state,
    )
    session.dispatch_safe(action)
    assert session.error is None
    assert session.png.startswith(b"\x89PNG")
    assert b"<svg" in session.export("svg")
    page = render_page(session.store.state, [])
    assert 'value="publication"' in page
    assert "y_lower" in page and "y_upper" in page


def test_bar_png_and_svg_exports_remain_deterministic(tmp_path):
    p = mp.plot(_data()).bar("dose", "mean", yerr="sd").theme("publication").size(4, 3)
    for extension in ("png", "svg"):
        first, second = (
            tmp_path / f"first.{extension}",
            tmp_path / f"second.{extension}",
        )
        p.save(first)
        p.save(second)
        assert first.read_bytes() == second.read_bytes()
    assert mimage.imread(tmp_path / "first.png").shape[:2] == (900, 1200)
