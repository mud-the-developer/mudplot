"""Independent empirical equations, real step artists and pure ECDF contracts."""

from __future__ import annotations

import json
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from mudplot import actions as A
from mudplot._ecdf import empirical_steps
from mudplot.spec import ECDFSpec, LayerSpec


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def test_unweighted_ties_full_minimum_jump_and_right_continuity():
    p = mp.plot({"v": [3, 1, 3, 2, 3]}).ecdf("v", label="sample")
    assert mp.validate(p.spec) == []
    line = p.render().axes[0].lines[0]
    np.testing.assert_array_equal(line.get_xdata(), [1, 1, 2, 3])
    np.testing.assert_allclose(
        np.asarray(line.get_ydata(), dtype=float), [0, 0.2, 0.4, 1]
    )
    assert line.get_drawstyle() == "steps-post"
    np.testing.assert_allclose(
        np.asarray(line.get_path().vertices, dtype=float),
        [[1, 0], [1, 0], [1, 0.2], [2, 0.2], [2, 0.4], [3, 0.4], [3, 1]],
    )
    assert line.get_label() == "sample"


@pytest.mark.parametrize("stat", ["count", "proportion", "percent"])
@pytest.mark.parametrize("complementary", [False, True])
def test_independent_weighted_indicator_equations_and_input_order(stat, complementary):
    rng = np.random.default_rng(74)
    values = rng.integers(-3, 5, 125).tolist()
    weights = rng.uniform(0.01, 4, 125).tolist()
    knots, mass = empirical_steps(
        values, weights, stat=stat, complementary=complementary
    )
    unique = sorted(set(values))
    assert knots == [unique[0], *unique]
    total = math.fsum(weights)
    denominator = total if stat != "count" else 1
    factor = 100 if stat == "percent" else 1
    boundary = total if complementary else 0
    expected = [boundary / denominator * factor]
    for knot in unique:
        expected.append(
            math.fsum(
                weight
                for value, weight in zip(values, weights, strict=True)
                if (value > knot if complementary else value <= knot)
            )
            / denominator
            * factor
        )
    np.testing.assert_allclose(mass, expected, rtol=3e-15, atol=0)
    order = rng.permutation(len(values))
    assert empirical_steps(
        [values[i] for i in order],
        [weights[i] for i in order],
        stat=stat,
        complementary=complementary,
    ) == (knots, mass)
    differences = np.diff(mass)
    assert np.all(differences <= 0 if complementary else differences >= 0)


@pytest.mark.parametrize("stat", ["count", "proportion", "percent"])
@pytest.mark.parametrize("complementary", [False, True])
def test_wide_weight_range_prefixes_stay_monotone_without_probability_clipping(
    stat,
    complementary,
):
    rng = np.random.default_rng(21)
    for _ in range(90):
        values = rng.integers(0, 30, size=100).tolist()
        weights = np.power(10.0, rng.uniform(-300, 300, size=100)).tolist()
        knots, mass = empirical_steps(
            values,
            weights,
            stat=stat,
            complementary=complementary,
        )
        differences = np.diff(mass)
        assert np.all(differences <= 0 if complementary else differences >= 0)
        total = math.fsum(weights)
        limit = total if stat == "count" else 100 if stat == "percent" else 1
        assert min(mass) >= 0 and max(mass) <= limit
        assert mass[-1] == (0 if complementary else limit)
        for knot, actual in zip(knots[1:], mass[1:], strict=True):
            expected = math.fsum(
                weight
                for value, weight in zip(values, weights, strict=True)
                if (value > knot if complementary else value <= knot)
            )
            if stat != "count":
                expected = expected / total * (100 if stat == "percent" else 1)
            # Percent is proportion *100; one subnormal rounding unit in
            # the proportion is correspondingly 100 units in percent.
            atol = 5e-324 * (100 if stat == "percent" else 1)
            assert actual == pytest.approx(expected, rel=2e-15, abs=atol)


@pytest.mark.parametrize("stat", ["count", "proportion", "percent"])
def test_complement_excludes_all_ties_and_preserves_tiny_positive_tail(stat):
    knots, mass = empirical_steps(
        [1, 1, 2], [1e16, 1, 1], stat=stat, complementary=True
    )
    assert knots == [1, 1, 2]
    assert mass[1] > 0 and mass[-1] == 0
    expected = (
        1
        if stat == "count"
        else (100 if stat == "percent" else 1) / math.fsum([1e16, 1, 1])
    )
    assert mass[1] == pytest.approx(expected, rel=1e-15)


@pytest.mark.parametrize("complementary", [False, True])
def test_scaled_proportions_do_not_overflow_large_finite_weights(complementary):
    knots, mass = empirical_steps([1, 2, 2], [1e308] * 3, complementary=complementary)
    assert knots == [1, 1, 2]
    np.testing.assert_allclose(mass, [1, 2 / 3, 0] if complementary else [0, 1 / 3, 1])
    p = mp.plot({"v": [1, 2, 2], "w": [1e308] * 3}).ecdf("v", weights="w")
    assert mp.validate(p.spec) == []
    assert np.isfinite(p.render().axes[0].lines[0].get_ydata()).all()
    with pytest.raises(ValueError, match="count mass exceeds finite range"):
        empirical_steps([1, 2], [1e308] * 2, stat="count")
    q = mp.plot({"v": [1, 2], "w": [1e308] * 2}).ecdf("v", weights="w", stat="count")
    assert any(
        "count mass exceeds finite range" in issue for issue in mp.validate(q.spec)
    )
    with pytest.raises(ValueError, match="count mass exceeds finite range"):
        q.render()


def test_finite_count_mass_is_per_curve_not_pooled_across_groups():
    p = mp.plot({"v": [1, 2], "w": [1e308] * 2, "g": ["A", "B"]}).ecdf(
        "v",
        weights="w",
        stat="count",
        group="g",
    )
    assert mp.validate(p.spec) == []
    for line in p.render().axes[0].lines:
        np.testing.assert_array_equal(line.get_ydata(), [0, 1e308])


@pytest.mark.parametrize("complementary", [False, True])
def test_horizontal_coordinates_use_pre_steps_instead_of_wrong_post_steps(
    complementary,
):
    p = mp.plot({"v": [1, 2, 3, 3]}).ecdf("v", orient="h", complementary=complementary)
    line = p.render().axes[0].lines[0]
    mass = [1, 0.75, 0.5, 0] if complementary else [0, 0.25, 0.5, 1]
    np.testing.assert_array_equal(line.get_ydata(), [1, 1, 2, 3])
    np.testing.assert_allclose(np.asarray(line.get_xdata(), dtype=float), mass)
    assert line.get_drawstyle() == "steps-pre"
    path = [
        [mass[0], 1],
        [mass[0], 1],
        [mass[1], 1],
        [mass[1], 2],
        [mass[2], 2],
        [mass[2], 3],
        [mass[3], 3],
    ]
    np.testing.assert_allclose(np.asarray(line.get_path().vertices, dtype=float), path)


def test_missing_zero_weight_rows_and_hue_selection_preserve_original_pairs():
    p = (
        mp.plot(
            {
                "v": [4, 1, None, 2, -8, 3, 99, 0],
                "w": [4, 1, 99, None, 0, 2, -1, 7],
                "g": ["A", "A", "A", "A", "A", None, "omit", "omit"],
            }
        )
        .ecdf("v", weights="w", group="g", hue_order=["empty", "A"])
        .xscale("log")
    )
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    assert len(ax.lines) == 1
    np.testing.assert_array_equal(ax.lines[0].get_xdata(), [1, 1, 4])
    np.testing.assert_allclose(
        np.asarray(ax.lines[0].get_ydata(), dtype=float), [0, 0.2, 1]
    )
    assert ax.get_legend_handles_labels()[1] == ["A"]


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("complementary", [False, True])
def test_matplotlib_native_reference_equations_on_finite_unweighted_knots(
    orient,
    complementary,
):
    values = [4, 1, 3, 2, 3]
    p = mp.plot({"v": values}).ecdf("v", orient=orient, complementary=complementary)
    line = p.render().axes[0].lines[0]
    _, ax = plt.subplots()
    reference = ax.ecdf(
        values,
        complementary=complementary,
        orientation="vertical" if orient == "v" else "horizontal",
    )
    # Native boundary/step tables differ between ordinary/complement and
    # Matplotlib versions. Compare right limits of actual paths at every knot,
    # including the full tied jump, rather than assuming identical raw arrays.
    observed = np.asarray(
        line.get_xdata() if orient == "v" else line.get_ydata(), dtype=float
    )
    mass = np.asarray(
        line.get_ydata() if orient == "v" else line.get_xdata(), dtype=float
    )
    path = np.asarray(reference.get_path().vertices, dtype=float)
    native_observed = path[:, 0 if orient == "v" else 1]
    native_mass = path[:, 1 if orient == "v" else 0]
    finite = np.isfinite(native_observed)
    np.testing.assert_array_equal(observed[1:], np.unique(native_observed[finite]))
    right_limits = [native_mass[native_observed == knot][-1] for knot in observed[1:]]
    np.testing.assert_allclose(mass[1:], right_limits)


def test_group_normalization_is_within_curve_not_global_row_denominator():
    p = mp.plot({"v": [1, 2, 3, 1], "g": ["A"] * 3 + ["B"]}).ecdf("v", group="g")
    lines = p.render().axes[0].lines
    np.testing.assert_allclose(
        np.asarray(lines[0].get_ydata(), dtype=float), [0, 1 / 3, 2 / 3, 1]
    )
    np.testing.assert_array_equal(lines[1].get_ydata(), [0, 1])
    assert [line.get_label() for line in lines] == ["A", "B"]


def test_empty_hue_slots_reserve_colors_and_dashes_without_invented_curves():
    data = {"v": [1, 2, 2, 4], "g": ["A"] * 2 + ["B"] * 2}
    full = mp.plot(data).ecdf("v", group="g", hue_order=["A", "B"])
    reserved = mp.plot(data).ecdf("v", group="g", hue_order=["empty", "B"])
    a, b = full.render().axes[0].lines
    only = reserved.render().axes[0].lines[0]
    assert a.get_color() != b.get_color()
    assert only.get_color() == b.get_color()
    assert only.get_linestyle() == b.get_linestyle()
    assert only.get_label() == "B"


@pytest.mark.parametrize("data", [{"v": []}, {"v": [None]}, {"v": [1, 2], "w": [0, 0]}])
def test_empty_selected_curve_has_no_artist_legend_or_infinite_anchor(data):
    p = mp.plot(data).ecdf("v", weights="w" if "w" in data else None, label="no rows")
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    assert not ax.lines and ax.get_legend_handles_labels() == ([], [])
    assert empirical_steps([], []) == ([], [])


@pytest.mark.parametrize("values", [[3], [3, 3, 3], [-2, -2], [0, 0]])
@pytest.mark.parametrize("complementary", [False, True])
def test_singleton_and_constant_samples_have_finite_full_jumps(values, complementary):
    p = mp.plot({"v": values}).ecdf("v", complementary=complementary)
    line = p.render().axes[0].lines[0]
    np.testing.assert_array_equal(line.get_xdata(), [values[0]] * 2)
    np.testing.assert_array_equal(line.get_ydata(), [1, 0] if complementary else [0, 1])
    assert np.isfinite(line.get_path().vertices).all()


@pytest.mark.parametrize("orient", ["v", "h"])
def test_positive_observation_log_axis_limits_and_inversion_do_not_log_fit(orient):
    p = mp.plot({"v": [1, 10, 100]}).ecdf("v", orient=orient)
    if orient == "v":
        p.xscale("log").xlim(150, 0.8)
    else:
        p.yscale("log").ylim(150, 0.8)
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    line = ax.lines[0]
    observed = line.get_xdata() if orient == "v" else line.get_ydata()
    np.testing.assert_array_equal(observed, [1, 1, 10, 100])
    mass = np.asarray(
        line.get_ydata() if orient == "v" else line.get_xdata(), dtype=float
    )
    np.testing.assert_allclose(mass, [0, 1 / 3, 2 / 3, 1])
    assert ax.xaxis_inverted() if orient == "v" else ax.yaxis_inverted()


@pytest.mark.parametrize("orient", ["v", "h"])
def test_mass_log_axis_and_nonpositive_observation_logs_are_explicit_errors(orient):
    p = mp.plot({"v": [0, 1]}).ecdf("v", orient=orient)
    (p.yscale if orient == "v" else p.xscale)("log")
    assert any("cumulative mass axis must be linear" in i for i in mp.validate(p.spec))
    (p.yscale if orient == "v" else p.xscale)("linear")
    (p.xscale if orient == "v" else p.yscale)("log")
    assert any(
        "log ECDF observations must be positive" in i for i in mp.validate(p.spec)
    )


@pytest.mark.parametrize(
    "value", [True, False, "2", float("inf"), -float("inf"), 10**400]
)
def test_bad_selected_observations_fail_with_core_errors(value):
    p = mp.plot({"v": [1, value]}).ecdf("v")
    assert any(
        "ECDF observations must be finite" in issue for issue in mp.validate(p.spec)
    )


@pytest.mark.parametrize("weight", [True, False, -1, "2", float("inf"), 10**400])
def test_bad_selected_weights_are_rejected_including_false_not_ignored_as_zero(weight):
    p = mp.plot({"v": [1, 2], "w": [1, weight]}).ecdf("v", weights="w")
    assert any(
        "ECDF weights must be finite nonnegative" in i for i in mp.validate(p.spec)
    )


@pytest.mark.parametrize("weight", [None, float("nan")])
def test_missing_weight_rows_drop_without_repairing_pair_alignment(weight):
    p = mp.plot({"v": [1, 4, 9], "w": [1, weight, 3]}).ecdf("v", weights="w")
    np.testing.assert_array_equal(p.render().axes[0].lines[0].get_xdata(), [1, 1, 9])
    np.testing.assert_allclose(
        np.asarray(p.render().axes[0].lines[0].get_ydata(), dtype=float), [0, 0.25, 1]
    )


@pytest.mark.parametrize(
    "options,match",
    [
        ({"stat": "density"}, "stat must be"),
        ({"stat": ["count"]}, "stat must be"),
        ({"complementary": 1}, "complementary must be boolean"),
        ({"weights": "missing"}, "column 'missing'"),
        ({"weights": ""}, "nonempty column name"),
        ({"weights": []}, "nonempty column name"),
        ({"orient": "vertical"}, "orient must be"),
        ({"hue_order": ["A"]}, "hue_order requires group"),
        ({"group": "g", "hue_order": ["A", "A"]}, "levels must be unique"),
        ({"group": "g", "hue_order": []}, "nonempty array"),
        ({"group": "g", "hue_order": "A"}, "nonempty array"),
        ({"line_width": float("nan")}, "line_width must be finite"),
        ({"line_width": -1}, "line_width must be finite"),
        ({"line_width": True}, "line_width must be finite"),
        ({"line_style": "custom"}, "line_style must be"),
        ({"color": "not-a-color"}, "color must be"),
    ],
)
def test_bad_named_options_have_specific_diagnostics_without_validation_crashes(
    options, match
):
    p = mp.plot({"v": [1, 2], "g": ["A", "A"]}).ecdf("v", **options)
    assert any(match in issue for issue in mp.validate(p.spec))
    with pytest.raises(ValueError, match=match):
        p.render()


@pytest.mark.parametrize(
    "style",
    [
        {"bins": 8},
        {"density": True},
        {"marker": "o"},
        {"marker_size": 3},
        {"stat_scale": "axis"},
        {"native_scale": True},
        {"order": [1, 2]},
        {"baseline": 1},
        {"stack": True},
        {"confidence": 95},
        {"stat": mp.StatSpec()},
        {"y": "v"},
        {"yerr": "v"},
        {"drawstyle": "steps-post"},
        {"value_labels": True},
    ],
)
def test_ecdf_rejects_ignored_layer_fields_instead_of_changing_its_meaning(style):
    p = mp.plot({"v": [1, 2]}).dispatch(
        A.AddLayer(LayerSpec(type="ecdf", x="v", **style))
    )
    assert any("not supported for ecdf" in issue for issue in mp.validate(p.spec))


@pytest.mark.parametrize("projection", ["polar", "3d"])
def test_ecdf_rejects_projection_and_y2_routing(projection):
    p = mp.plot({"v": [1, 2]}).ecdf("v")
    spec = p.spec
    spec.panels[0].projection = projection
    assert any(projection in issue for issue in mp.validate(spec))
    q = mp.plot({"v": [1, 2]}).ecdf("v", axis="y2").secondary_yaxis(label="second")
    assert any("axis='y2' is not supported" in issue for issue in mp.validate(q.spec))


def test_typed_defaults_json_actions_schema_legacy_specs_and_strict_nested_config():
    import jsonschema

    p = mp.plot({"v": [1, 2, 2], "w": [1, 2, 3]}).ecdf(
        "v",
        stat="count",
        complementary=True,
        weights="w",
        orient="h",
        alpha=0.4,
    )
    assert p.spec.panels[0].layers[0].ecdf == ECDFSpec("count", True, "w")
    assert mp.Plot.from_json(p.to_json()).spec == p.spec
    assert mp.apply(p.action_log) == p.spec
    jsonschema.validate(p.spec.to_dict(), mp.json_schema())
    assert mp.json_schema()["$defs"]["ECDFSpec"]["additionalProperties"] is False
    raw = p.spec.to_dict()
    raw["panels"][0]["layers"][0]["ecdf"]["interpolation"] = "linear"
    with pytest.raises(ValueError, match="unknown ECDFSpec field"):
        mp.FigureSpec.from_dict(raw)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(raw, mp.json_schema())
    legacy = mp.plot({"v": [1, 2]}).kde("v").spec.to_dict()
    del legacy["panels"][0]["layers"][0]["ecdf"]
    assert mp.FigureSpec.from_dict(legacy).panels[0].layers[0].ecdf is None
    plain = mp.plot({"v": [1, 2]}).dispatch(A.AddLayer(LayerSpec(type="ecdf", x="v")))
    built = mp.plot({"v": [1, 2]}).ecdf("v")
    np.testing.assert_array_equal(
        plain.render().axes[0].lines[0].get_ydata(),
        built.render().axes[0].lines[0].get_ydata(),
    )


@pytest.mark.parametrize("config", [{"stat": "count"}, "count", 1])
def test_non_typed_ecdf_config_is_not_accepted_in_direct_specs(config):
    p = mp.plot({"v": [1, 2]}).ecdf("v")
    spec = p.spec
    spec.panels[0].layers[0].ecdf = config
    assert any("ecdf must be an ECDFSpec" in issue for issue in mp.validate(spec))


def test_ecdf_config_cannot_be_smuggled_into_other_layer_types():
    p = mp.plot({"v": [1, 2]}).kde("v", ecdf=ECDFSpec())
    assert any(
        "ecdf is not supported for kde" in issue for issue in mp.validate(p.spec)
    )


@pytest.mark.parametrize("alpha", [0, 1])
def test_explicit_zero_opacity_width_and_dashes_are_honored_exactly(alpha):
    p = mp.plot({"v": [1, 2]}).ecdf(
        "v",
        label="zero-width",
        color="#123456",
        line_style=":",
        line_width=0,
        alpha=alpha,
    )
    ax = p.render().axes[0]
    line = ax.lines[0]
    assert line.get_alpha() == alpha and line.get_linewidth() == 0
    assert line.get_color() == "#123456" and line.get_linestyle() == ":"
    assert not line.get_visible()
    assert ax.get_legend_handles_labels()[1] == ["zero-width"]


def test_svg_group_reference_metadata_stays_on_legend_not_invented_ci(tmp_path):
    p = mp.plot({"v": [1, 2], "g": ["A", "A"]}).ecdf(
        "v",
        group="g",
        references={"A": mp.Reference(href="https://example.com/ecdf")},
    )
    path = tmp_path / "linked.svg"
    plt.close(p.save(path))
    assert "https://example.com/ecdf" in path.read_text(encoding="utf-8")
    assert p.spec.panels[0].layers[0].stat is None


def test_editor_json_actions_export_and_reject_unknown_ecdf_options():
    from dashboard.editor_server import EditorSession, _build_action

    session = EditorSession()
    session.dispatch_safe(A.SetData({"v": [1, 2, 2], "w": [1, 2, 1]}))
    action = _build_action(
        "add_layer_json",
        {
            "layer_type": "ecdf",
            "layer_json": json.dumps(
                {"x": "v", "ecdf": {"weights": "w", "complementary": True}}
            ),
        },
        session.store.state,
    )
    session.dispatch_safe(action)
    assert session.error is None and session.png.startswith(b"\x89PNG")
    assert b"<svg" in session.export("svg")
    with pytest.raises(ValueError, match="unknown ECDFSpec"):
        _build_action(
            "add_layer_json",
            {
                "layer_type": "ecdf",
                "layer_json": '{"x":"v","ecdf":{"censor":true}}',
            },
            session.store.state,
        )


@pytest.mark.parametrize("extension", ["png", "pdf", "svg"])
def test_repeated_json_exports_are_byte_identical_without_global_rng_changes(
    tmp_path, extension
):
    p = (
        mp.plot({"v": [1, 4, 2, 2], "w": [1, 4, 2, 1]})
        .theme("publication")
        .ecdf(
            "v",
            weights="w",
            complementary=True,
        )
        .size(4, 3)
    )
    before = np.random.get_state()
    a, b = tmp_path / f"a.{extension}", tmp_path / f"b.{extension}"
    plt.close(p.save(a))
    plt.close(mp.Plot.from_json(p.to_json()).save(b))
    assert a.read_bytes() == b.read_bytes()
    after = np.random.get_state()
    assert before[0] == after[0] and before[2:] == after[2:]
    np.testing.assert_array_equal(before[1], after[1])


def test_capabilities_reference_and_schema_describe_ecdf_without_fake_stat_inference():
    caps = mp.capabilities()
    assert "ecdf" in caps["layers"] and "ecdf" in caps["layers"]["ecdf"]["optional"]
    assert caps["ecdf"]["statistics"] == ["proportion", "percent", "count"]
    assert caps["ecdf"]["defaults"] == ECDFSpec().to_dict()
    assert "axis" not in caps["layers"]["ecdf"]["optional"]
    assert "strict X>t" in mp.reference_markdown()
