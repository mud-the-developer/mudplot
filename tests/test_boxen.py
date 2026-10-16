"""Letter-value formulas, real native bands, strict declarations and effects."""

from __future__ import annotations

import json
from statistics import NormalDist
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import PolyCollection
from mudplot._letter_value import (
    MAX_LETTER_DEPTH,
    letter_value_depth,
    letter_value_summary,
)
from mudplot._render import _count_colors
from mudplot.spec import LayerSpec


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def _bodies(ax) -> list[Any]:
    return [c for c in ax.collections if isinstance(c, PolyCollection)]


def _data():
    return {
        "cat": ["B", "B", "A", "A"] * 2,
        "value": [1, 3, 2, 4, 3, 5, 4, 6],
        "hue": ["u"] * 4 + ["v"] * 4,
    }


def test_known_letter_quantiles_widths_and_strict_raw_tail_points():
    summary = letter_value_summary(range(16), k_depth=3)
    assert summary.depth == 3 and summary.levels == (0, 1, 2, 1, 0)
    assert summary.percentiles == (1 / 16, 1 / 8, 1 / 4, 3 / 4, 7 / 8, 15 / 16)
    assert summary.values == (0.9375, 1.875, 3.75, 11.25, 13.125, 14.0625)
    assert summary.widths == (0.25, 0.5, 1, 0.5, 0.25)
    assert summary.median == 7.5 and summary.fliers == (0, 15)
    linear = letter_value_summary(range(16), k_depth=3, width_method="linear")
    assert linear.widths == (1 / 3, 2 / 3, 1, 2 / 3, 1 / 3)
    area = letter_value_summary(range(16), k_depth=3, width_method="area")
    np.testing.assert_allclose(area.widths, np.ones(5), atol=1e-14)
    reversed_data = letter_value_summary(reversed(range(16)), k_depth=3)
    assert reversed_data.values == summary.values
    assert reversed_data.fliers == (15, 0)


@pytest.mark.parametrize("n", [1, 2, 7, 16, 64, 127, 128, 1024])
@pytest.mark.parametrize("rule", ["tukey", "full", "proportion", "trustworthy"])
def test_depth_rules_match_published_reference_formulas(n, rule):
    # Independent equations from Seaborn 0.13.2 _statistics.LetterValues.
    if rule == "tukey":
        expected = int(np.log2(n)) - 3
    elif rule == "full":
        expected = int(np.log2(n)) + 1
    elif rule == "proportion":
        expected = int(np.log2(n)) - int(np.log2(n * 0.007)) + 1
    else:
        point_conf = 2 * NormalDist().inv_cdf(1 - 0.05 / 2) ** 2
        expected = int(np.log2(n / point_conf)) + 1
    assert letter_value_depth(n, rule) == max(1, expected)


def test_named_depth_cap_custom_policy_and_full_extremes():
    assert letter_value_depth(128) == 4
    assert letter_value_depth(128, "proportion", outlier_prop=1 / 16) == 5
    assert letter_value_depth(128, "trustworthy", trust_alpha=0.01) == 4
    assert letter_value_depth(1 << 80, "full") == MAX_LETTER_DEPTH
    assert letter_value_depth(16, "proportion", outlier_prop=1e-300) == 32
    full = letter_value_summary(range(16), k_depth="full")
    assert full.depth == 5 and len(full.widths) == 9
    assert full.values[0] == 0 and full.values[-1] == 15
    assert full.percentiles[0] == 0 and full.percentiles[-1] == 1
    assert full.fliers == ()
    assert letter_value_summary([4]).values == (4, 4)


@pytest.mark.parametrize("method", ["exponential", "linear", "area"])
def test_quantiles_and_widths_have_independent_numeric_references(method):
    data = np.random.default_rng(29).lognormal(size=257)
    s = letter_value_summary(data, k_depth=5, width_method=method)
    np.testing.assert_allclose(s.values, np.quantile(data, s.percentiles), rtol=1e-14)
    np.testing.assert_allclose(s.median, np.median(data))
    if method == "area":
        density = np.diff(s.percentiles) / np.diff(s.values)
        np.testing.assert_allclose(s.widths, density / density.max(), rtol=1e-14)
    assert len(s.values) == 10 and len(s.widths) == 9
    assert np.isfinite(s.widths).all() and max(s.widths) == 1
    expected = data[(data < s.values[0]) | (data > s.values[-1])]
    np.testing.assert_array_equal(s.fliers, expected)


@pytest.mark.parametrize(
    "values",
    [[4], [4] * 10, [0.1] * 10, [1e308] * 10, [0] * 50 + [1] * 50, [-1e308, 1e308]],
)
def test_area_handles_ties_singletons_and_extreme_finite_values(values):
    s = letter_value_summary(values, k_depth=5, width_method="area")
    assert np.isfinite(s.values).all() and np.isfinite(s.widths).all()
    assert max(s.widths) == 1 and all(0 <= w <= 1 for w in s.widths)
    if min(values) == max(values):
        assert s.widths == letter_value_summary(values, k_depth=5).widths
    elif len(values) == 100:
        assert any(w == 0 for w in s.widths)


def test_seeded_numeric_properties_and_tied_quantiles_remain_exact():
    rng = np.random.default_rng(518)
    for n in (1, 2, 7, 31, 128, 257):
        for k in (1, 2, 5, 32):
            data = rng.choice(np.linspace(-3, 3, 21), size=n)
            s = letter_value_summary(data, k_depth=k, width_method="area")
            np.testing.assert_allclose(s.values, np.quantile(data, s.percentiles))
            assert all(a <= b for a, b in zip(s.values[:-1], s.values[1:], strict=True))
            assert all(0 <= w <= 1 for w in s.widths)
            assert min(data) <= s.median <= max(data)
    s = letter_value_summary([0.1] * 23, k_depth=32)
    assert all(v == 0.1 for v in s.values) and s.fliers == ()


def test_full_area_uses_actual_mass_when_extreme_percentiles_extend_to_min_max():
    s = letter_value_summary(range(16), k_depth="full", width_method="area")
    density = np.diff(s.percentiles) / np.diff(s.values)
    np.testing.assert_allclose(s.widths, density / density.max(), atol=1e-14)


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("method", ["exponential", "linear", "area"])
def test_native_band_geometry_median_and_tail_points_match_summaries(orient, method):
    values = list(range(16))
    p = mp.plot({"cat": ["A"] * 16, "v": values}).boxenplot(
        "cat",
        "v",
        orient=orient,
        k_depth=3,
        width_method=method,
        width=0.6,
        edge_color="#112233",
        line_width=0.7,
        marker="s",
        marker_size=4,
        alpha=0.8,
    )
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    body = _bodies(ax)[0]
    s = letter_value_summary(values, k_depth=3, width_method=method)
    cat_axis = int(orient == "h")
    val_axis = 1 - cat_axis
    assert len(body.get_paths()) == 5
    for i, path in enumerate(body.get_paths()):
        verts = np.asarray(path.vertices)
        assert np.min(verts[:, val_axis]) == s.values[i]
        assert np.max(verts[:, val_axis]) == s.values[i + 1]
        np.testing.assert_allclose(
            [np.min(verts[:, cat_axis]), np.max(verts[:, cat_axis])],
            [-0.3 * s.widths[i], 0.3 * s.widths[i]],
        )
    median, fliers = ax.lines
    md = median.get_xdata() if orient == "h" else median.get_ydata()
    np.testing.assert_allclose(np.asarray(md), [7.5, 7.5])
    fd = fliers.get_xdata() if orient == "h" else fliers.get_ydata()
    np.testing.assert_array_equal(np.asarray(fd), [0, 15])
    assert median.get_linewidth() == 0.7 and fliers.get_markersize() == 4
    assert fliers.get_marker() == "s" and body.get_alpha() == 0.8
    assert all(v == 0.7 for v in body.get_linewidths())
    assert len(body.get_facecolors()) == 5
    assert ax.dataLim.ymin <= (0 if orient == "v" else -0.3)


@pytest.mark.parametrize("orient", ["v", "h"])
def test_nested_hues_reserve_empty_slots_colors_hatches_and_single_legend(orient):
    p = mp.plot(_data()).boxenplot(
        "cat",
        "value",
        group="hue",
        order=["A", "empty", "B"],
        hue_order=["v", "u", "absent"],
        orient=orient,
        k_depth=2,
        gap=0.25,
    )
    assert _count_colors(p.spec) == 3 and mp.validate(p.spec) == []
    ax = p.render().axes[0]
    bodies = _bodies(ax)
    assert len(bodies) == 4
    cat_axis = int(orient == "h")
    central = [np.asarray(b.get_paths()[1].vertices)[:, cat_axis] for b in bodies]
    np.testing.assert_allclose(
        [(c.max() + c.min()) / 2 for c in central],
        [-0.8 / 3, 2 - 0.8 / 3, 0, 2],
    )
    np.testing.assert_allclose([c.max() - c.min() for c in central], [0.2] * 4)
    labels = ax.get_yticklabels() if orient == "h" else ax.get_xticklabels()
    assert [t.get_text() for t in labels] == ["A", "empty", "B"]
    assert ax.get_legend_handles_labels()[1] == ["v", "u"]
    np.testing.assert_array_equal(
        bodies[0].get_facecolors(), bodies[1].get_facecolors()
    )
    assert bodies[0].get_hatch() == bodies[1].get_hatch() != bodies[2].get_hatch()
    assert mp.Plot.from_json(p.to_json()).spec == p.spec
    assert mp.apply(p.action_log) == p.spec


def test_one_column_group_order_selection_and_zero_dodge():
    p = mp.plot(_data()).boxenplot("value", group="hue", order=["v", "empty", "u"])
    ax = p.render().axes[0]
    assert [t.get_text() for t in ax.get_xticklabels()] == ["v", "empty", "u"]
    coords = [b.get_paths()[0].vertices[:, 0] for b in _bodies(ax)]
    np.testing.assert_allclose([(c.max() + c.min()) / 2 for c in coords], [1, 3])
    np.testing.assert_allclose([c.max() - c.min() for c in coords], [0.8, 0.8])
    joint = mp.plot(_data()).boxenplot("cat", "value", group="hue", dodge=0, width=0.6)
    coords = [b.get_paths()[0].vertices[:, 0] for b in _bodies(joint.render().axes[0])]
    np.testing.assert_allclose([(c.max() + c.min()) / 2 for c in coords], [0, 1, 0, 1])
    np.testing.assert_allclose([c.max() - c.min() for c in coords], [0.6] * 4)


def test_missing_rows_are_listwise_dropped_and_filtered_values_do_not_estimate():
    data = {
        "cat": ["A", "A", "A", "B", None, "A"],
        "v": [1, 3, None, 20, 50, 100],
        "hue": ["u", "u", "u", "v", "u", None],
    }
    p = mp.plot(data).boxenplot("cat", "v", group="hue", order=["A"], hue_order=["u"])
    body = _bodies(p.render().axes[0])[0]
    assert len(body.get_paths()) == 1
    verts = body.get_paths()[0].vertices
    np.testing.assert_allclose([verts[:, 1].min(), verts[:, 1].max()], [1.5, 2.5])


@pytest.mark.parametrize("method", ["exponential", "linear", "area"])
@pytest.mark.parametrize("values", [[4], [4] * 10])
def test_constant_cells_render_without_nan_or_fake_summary(method, values):
    p = mp.plot({"v": values}).boxenplot("v", k_depth=3, width_method=method)
    ax = p.render().axes[0]
    assert len(ax.lines) == 1  # Real median; no fake fliers.
    for path in _bodies(ax)[0].get_paths():
        assert np.isfinite(path.vertices).all() and (path.vertices[:, 1] == 4).all()


def test_visibility_flags_remove_only_requested_artists():
    p = mp.plot({"v": list(range(16))}).boxenplot(
        "v",
        k_depth=3,
        showmedians=False,
        showfliers=False,
    )
    assert len(p.render().axes[0].lines) == 0
    p = mp.plot({"v": list(range(16))}).boxenplot("v", k_depth="full")
    assert len(p.render().axes[0].lines) == 1  # Full depth has no outside rows.


@pytest.mark.parametrize(
    "options,message",
    [
        ({"k_depth": 0}, "k_depth"),
        ({"k_depth": 33}, "k_depth"),
        ({"k_depth": True}, "k_depth"),
        ({"k_depth": 2.5}, "k_depth"),
        ({"k_depth": "auto"}, "k_depth"),
        ({"k_depth": []}, "k_depth"),
        ({"width_method": "density"}, "width_method"),
        ({"outlier_prop": 0.1}, "requires"),
        ({"k_depth": "proportion", "outlier_prop": 0}, "outlier_prop"),
        ({"k_depth": "proportion", "outlier_prop": 1}, "outlier_prop"),
        ({"k_depth": "proportion", "outlier_prop": True}, "outlier_prop"),
        ({"trust_alpha": 0.1}, "requires"),
        ({"k_depth": "trustworthy", "trust_alpha": 1e-20}, "trust_alpha"),
        ({"k_depth": "trustworthy", "trust_alpha": 1}, "trust_alpha"),
        ({"k_depth": "trustworthy", "trust_alpha": float("nan")}, "trust_alpha"),
        ({"width": 0}, "width"),
        ({"width": 1.1}, "width"),
        ({"dodge": 1}, "dodge"),
        ({"gap": 1}, "gap"),
        ({"showfliers": 1}, "boolean"),
        ({"showmedians": "yes"}, "boolean"),
        ({"marker": "not-a-marker"}, "marker"),
        ({"line_width": 1001}, "line_width"),
        ({"marker_size": True}, "marker_size"),
        ({"whis": 1}, "not supported"),
        ({"notch": True}, "not supported"),
        ({"showmeans": True}, "not supported"),
        ({"bw_method": "scott"}, "not supported"),
        ({"warn_thresh": 0}, "not supported"),
        ({"stat": mp.StatSpec()}, "not supported"),
        ({"c": "value"}, "not supported"),
        ({"axis": "y2"}, "not supported"),
    ],
)
def test_bad_or_ignored_controls_fail_before_rendering(options, message):
    p = mp.plot(_data()).boxenplot("cat", "value", **options)
    assert any(message in i for i in mp.validate(p.spec))
    with pytest.raises(ValueError):
        p.render()


@pytest.mark.parametrize(
    "values", [[1, float("inf")], [1, True], [1, "2"], [None, None]]
)
def test_bad_observations_are_not_coerced_or_invented(values):
    p = mp.plot({"v": values}).boxenplot("v")
    assert mp.validate(p.spec)
    with pytest.raises(ValueError):
        p.render()


@pytest.mark.parametrize("projection", ["polar", "3d"])
def test_unsupported_projections_fail_explicitly(projection):
    from mudplot import actions as A

    p = mp.plot(_data()).boxenplot("cat", "value").dispatch(A.SetProjection(projection))
    assert mp.validate(p.spec)


@pytest.mark.parametrize("nested", [False, True])
def test_positive_log_values_support_both_single_and_nested_contracts(nested):
    p = mp.plot(_data())
    p.boxenplot("cat", "value") if nested else p.boxenplot("value")
    p.yscale("log")
    assert mp.validate(p.spec) == []
    assert p.render().axes[0].get_yscale() == "log"


def test_boxen_fields_are_rejected_on_other_layer_types():
    p = mp.plot(_data()).box("cat", "value", k_depth=3)
    assert any("k_depth is not supported" in i for i in mp.validate(p.spec))
    p = mp.plot(_data()).scatter("value", "value", width_method="area")
    assert any("width_method is not supported" in i for i in mp.validate(p.spec))


def test_shared_category_geometry_and_conflicting_order():
    p = mp.plot(_data()).box("cat", "value", order=["A", "B"])
    p.boxenplot("cat", "value", order=["A", "B"]).swarmplot(
        "cat", "value", order=["A", "B"]
    )
    assert mp.validate(p.spec) == [] and len(_bodies(p.render().axes[0])) == 2
    q = mp.plot(_data()).box("cat", "value", order=["A", "B"])
    q.boxenplot("cat", "value", order=["B", "A"])
    with pytest.raises(ValueError, match="conflicting category order"):
        q.render()


def test_declaration_schema_actions_editor_png_and_old_default_fields():
    import jsonschema
    from dashboard.editor_server import EditorSession, _build_action
    from mudplot import actions as A

    old = LayerSpec.from_dict({"type": "box", "x": "value"})
    assert isinstance(old, LayerSpec)
    assert old.k_depth is None and old.width_method is None
    assert old.outlier_prop is None and old.trust_alpha is None
    session = EditorSession()
    session.dispatch_safe(A.SetData(_data()))
    action = _build_action(
        "add_layer_json",
        {
            "layer_type": "boxenplot",
            "layer_json": json.dumps(
                {
                    "x": "cat",
                    "y": "value",
                    "group": "hue",
                    "orient": "h",
                    "k_depth": "trustworthy",
                    "trust_alpha": 0.01,
                    "width_method": "area",
                    "showfliers": False,
                }
            ),
        },
        session.store.state,
    )
    session.dispatch_safe(action)
    assert session.error is None and session.png.startswith(b"\x89PNG")
    jsonschema.Draft202012Validator(mp.json_schema()).validate(
        session.store.state.to_dict()
    )
    replay = mp.apply([A.action_to_dict(a) for a in session.store.history])
    assert replay == session.store.state
    assert mp.Plot.from_json(mp.to_json(replay)).spec == replay


def test_repeatable_png_pdf_svg_specs_and_unchanged_global_rng(tmp_path):
    data = {
        "cat": ["A"] * 128 + ["B"] * 128,
        "v": np.random.default_rng(48).normal(size=256).tolist(),
    }
    p = mp.plot(data).theme("publication").boxenplot("cat", "v", k_depth=4)
    before = np.random.get_state()
    for fmt in ("png", "pdf", "svg"):
        first, second = tmp_path / f"a.{fmt}", tmp_path / f"b.{fmt}"
        plt.close(p.save(str(first)))
        plt.close(p.save(str(second)))
        assert first.read_bytes() == second.read_bytes()
    after = np.random.get_state()
    assert before[0] == after[0] and before[2:] == after[2:]
    np.testing.assert_array_equal(before[1], after[1])
    path = tmp_path / "editable.mplot.json"
    mp.save_spec(p.spec, path)
    assert mp.load_spec(path) == p.spec
