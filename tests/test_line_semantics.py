"""Independent curve partitions, physical widths and existing pointwise inference."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from mudplot._estimate import summarize
from mudplot._semantics import line_semantic_input, semantic_rows
from mudplot.spec import LayerSpec, SemanticSpec


def _raw():
    return {
        "t": [1, 1, 2, 2] * 4,
        "y": [1, 3, 3, 5, 2, 4, 4, 6, 8, 10, 10, 12, 9, 11, 11, 13],
        "h": ["A"] * 8 + ["B"] * 8,
        "s": (["X"] * 4 + ["Y"] * 4) * 2,
        "m": [0] * 8 + [10] * 8,
    }


def _cfg(**kwargs):
    return SemanticSpec(
        hue="h", size="m", sizes=[1, 3], style="s", dashes=["-", "--"], **kwargs
    )


def _data_lines(ax):
    return [l for l in ax.lines if len(l.get_xdata())]


@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("errors", ["sd", "se", "pi", None])
def test_independent_roles_do_not_pool_different_style_cells(orient, errors):
    raw = _raw()
    p = mp.plot(raw).lineplot(
        "t", "y", semantics=_cfg(), errorbar=errors, orient=orient
    )
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    lines = _data_lines(ax)
    assert len(lines) == 4
    for i, line in enumerate(lines):
        expected = (
            [2, 4] if i == 0 else [3, 5] if i == 1 else [9, 11] if i == 2 else [10, 12]
        )
        x, y = line.get_xdata(), line.get_ydata()
        np.testing.assert_array_equal(y if orient == "v" else x, expected)
        np.testing.assert_array_equal(x if orient == "v" else y, [1, 2])
        assert line.get_linewidth() == (1 if i < 2 else 3)
        assert line.get_marker() == ("o" if i % 2 == 0 else "s")
        assert line.get_linestyle() == ("-" if i % 2 == 0 else "--")
    assert lines[0].get_color() == lines[1].get_color()
    assert lines[2].get_color() == lines[3].get_color()
    labels = ax.get_legend_handles_labels()[1]
    assert "size (line width, pt): m=5.0" in labels
    assert all(np.asarray(l.get_xdata()).size == 0 for l in ax.lines if l not in lines)
    assert mp.apply(p.action_log) == p.spec
    assert mp.Plot.from_json(p.to_json()).spec == p.spec


@pytest.mark.parametrize("numeric", [False, True])
def test_numeric_hue_global_norm_and_categorical_sizes(numeric):
    p = mp.plot(_raw()).lineplot(
        "t",
        "y",
        errorbar=None,
        semantics=SemanticSpec(
            hue="m" if numeric else "h",
            hue_kind="numeric" if numeric else "categorical",
            size="h",
            size_kind="categorical",
            sizes=[1, 4],
            style="s",
        ),
    )
    assert mp.validate(p.spec) == []
    lines = _data_lines(p.render().axes[0])
    np.testing.assert_array_equal(lines[0].get_color(), lines[1].get_color())
    np.testing.assert_array_equal(lines[2].get_color(), lines[3].get_color())
    assert [l.get_linewidth() for l in lines] == [1, 1, 4, 4]


def test_clipped_numeric_roles_do_not_merge_raw_curve_tuples():
    raw = {
        "t": [1, 1, 2, 2] * 2,
        "y": [1, 3, 3, 5, 8, 10, 10, 12],
        "m": [10] * 4 + [20] * 4,
    }
    p = mp.plot(raw).lineplot(
        "t",
        "y",
        semantics=SemanticSpec(size="m", sizes=[1, 3], size_norm=[0, 5]),
        errorbar="sd",
    )
    assert mp.validate(p.spec) == []
    lines = _data_lines(p.render().axes[0])
    assert len(lines) == 2
    assert all(l.get_linewidth() == 3 for l in lines)
    np.testing.assert_array_equal(lines[0].get_ydata(), [2, 4])
    np.testing.assert_array_equal(lines[1].get_ydata(), [9, 11])


@pytest.mark.parametrize("orient", ["v", "h"])
def test_sort_false_is_per_semantic_curve_and_nonmonotonic_band_fails(orient):
    raw = {"t": [2, 1, 3, 2, 1, 3], "y": [2, 1, 3, 4, 3, 5], "s": ["X"] * 6}
    p = mp.plot(raw).lineplot(
        "t", "y", style="s", errorbar="sd", sort=False, orient=orient
    )
    assert mp.validate(p.spec) == []
    with pytest.raises(ValueError, match="monotonic"):
        p.render()
    p = mp.plot(raw).lineplot(
        "t",
        "y",
        style="s",
        errorbar="sd",
        sort=False,
        error_style="bars",
        orient=orient,
    )
    line = _data_lines(p.render().axes[0])[0]
    np.testing.assert_array_equal(
        line.get_xdata() if orient == "v" else line.get_ydata(), [2, 1, 3]
    )


@pytest.mark.parametrize("axis_fit", [False, True])
def test_log_raw_vs_explicit_axis_statistics_keep_observed_units(axis_fit):
    raw = {"t": [1, 1, 10, 10], "y": [1, 9, 4, 16], "s": ["X"] * 4}
    p = (
        mp.plot(raw)
        .lineplot(
            "t",
            "y",
            style="s",
            errorbar=None,
            stat_scale="axis" if axis_fit else "data",
        )
        .yscale("log")
        .xscale("log")
    )
    assert mp.validate(p.spec) == []
    line = _data_lines(p.render().axes[0])[0]
    np.testing.assert_allclose(
        np.asarray(line.get_ydata(), dtype=float), [3, 8] if axis_fit else [5, 10]
    )


def test_listwise_roles_weights_units_selection_precedes_domain_and_log_checks():
    raw = {
        "t": [1, 1, -3, 4, 0],
        "y": [1, 3, -2, 10, 0],
        "h": ["A", "A", None, "B", "A"],
        "w": [1, 3, 1, 0, 0],
    }
    p = (
        mp.plot(raw)
        .lineplot("t", "y", hue="h", weights="w", errorbar=None)
        .xscale("log")
        .yscale("log")
    )
    assert mp.validate(p.spec) == []
    assert semantic_rows(p.spec.data.columns, p.spec.panels[0].layers[0]) == [0, 1]
    lines = _data_lines(p.render().axes[0])
    assert len(lines) == 1
    assert np.asarray(lines[0].get_ydata(), dtype=float)[0] == 2.5
    assert p.render().axes[0].get_legend_handles_labels()[1] == ["hue: h=A"]


@pytest.mark.parametrize("weighted", [False, True])
def test_seeded_pointwise_bootstrap_matches_independent_existing_cell_reference(
    weighted,
):
    raw = _raw()
    raw["w"] = [1, 2, 1, 2] * 4
    raw["u"] = ["a", "b", "a", "b"] * 4
    p = mp.plot(raw).lineplot(
        "t",
        "y",
        semantics=_cfg(),
        units="u",
        weights="w" if weighted else None,
        errorbar="ci",
        n_boot=60,
        seed=7,
        error_style="bars",
    )
    layer = p.spec.panels[0].layers[0]
    cols, temp, curves = line_semantic_input(p.spec.data.columns, layer)
    actual = summarize(cols, temp)
    # Explicit integer IDs expose exactly the independent cell/curve contract.
    reference = mp.plot({**raw, "g": [0] * 4 + [1] * 4 + [2] * 4 + [3] * 4}).lineplot(
        "t",
        "y",
        group="g",
        units="u",
        weights="w" if weighted else None,
        errorbar="ci",
        n_boot=60,
        seed=7,
        error_style="bars",
    )
    expected = summarize(
        reference.spec.data.columns, reference.spec.panels[0].layers[0]
    )
    assert actual == expected and len(curves) == 4
    assert mp.validate(p.spec) == []
    p.render()


def test_private_curve_column_collision_preserves_user_input_and_stat_names():
    raw = _raw()
    raw["__mudplot_semantic_curve"] = [1] * 16
    p = mp.plot(raw).lineplot(
        "t", "y", hue="h", weights="__mudplot_semantic_curve", errorbar=None
    )
    before = p.to_json()
    cols, temp, _ = line_semantic_input(p.spec.data.columns, p.spec.panels[0].layers[0])
    assert temp.group == "__mudplot_semantic_curve_"
    assert cols["__mudplot_semantic_curve"] == [1] * 16
    p.render()
    assert p.to_json() == before


@pytest.mark.parametrize(
    "key,value",
    [
        ("group", "h"),
        ("color", "red"),
        ("line_width", 2),
        ("marker", "o"),
        ("line_style", "--"),
        ("hue_order", ["A"]),
        ("cmap_kind", "diverging"),
        ("edge_color", "black"),
    ],
)
def test_conflicting_scalar_and_legacy_settings_fail(key, value):
    p = mp.plot(_raw()).lineplot(
        "t", "y", semantics=_cfg(), errorbar=None, **{key: value}
    )
    assert mp.validate(p.spec)
    with pytest.raises(ValueError):
        p.render()


@pytest.mark.parametrize(
    "dashes", [True, [], ["bad"], ["--", "--"], ["-", "--", "-.", ":", "-"]]
)
def test_invalid_dash_lists_report_validation_not_effect_failure(dashes):
    cfg = _cfg()
    cfg.dashes = dashes
    p = mp.plot(_raw()).dispatch(
        mp.actions.AddLayer(LayerSpec(type="lineplot", x="t", y="y", semantics=cfg))
    )
    assert mp.validate(p.spec)


def test_dash_capacity_and_wrong_geometry_are_not_silent_noops():
    cfg = _cfg()
    cfg.dashes = ["-"]
    assert mp.validate(mp.plot(_raw()).lineplot("t", "y", semantics=cfg).spec)
    assert mp.validate(mp.plot(_raw()).scatter("t", "y", semantics=_cfg()).spec)
    p = mp.plot(_raw()).lineplot("t", "y", errorbar=None, cmap_kind="diverging")
    assert mp.validate(p.spec)
    with pytest.raises(ValueError, match="either"):
        mp.plot(_raw()).lineplot("t", "y", hue="h", semantics=_cfg())
    with pytest.raises(ValueError, match="unknown"):
        mp.plot(_raw()).lineplot("t", "y", semantics={"style": "s", "wrong": 0})


@pytest.mark.parametrize("constant", [0, 5e-324, -5e-324, 1e308])
def test_constant_numeric_roles_map_midpoint_with_one_width_guide(constant):
    raw = _raw()
    raw["m"] = [constant] * 16
    p = mp.plot(raw).lineplot(
        "t", "y", errorbar=None, semantics=SemanticSpec(size="m", sizes=[1, 3])
    )
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    assert len(_data_lines(ax)) == 1 and _data_lines(ax)[0].get_linewidth() == 2
    assert len(ax.get_legend_handles_labels()[1]) == 1


def test_zero_width_dash_export_keeps_points_bands_and_native_labels(tmp_path):
    cfg = _cfg()
    cfg.sizes = [0, 2]
    p = mp.plot(_raw()).lineplot(
        "t", "y", semantics=cfg, errorbar="sd", alpha=0.7, error_alpha=0.3, label="Data"
    )
    ax = p.render().axes[0]
    lines = _data_lines(ax)
    assert lines[0].get_linewidth() == 0 and lines[0].get_linestyle() == "None"
    assert all(c.get_alpha() == 0.3 for c in ax.collections)
    for ext in ("png", "svg", "pdf"):
        a, b = tmp_path / f"a.{ext}", tmp_path / f"b.{ext}"
        plt.close(p.save(str(a)))
        plt.close(p.save(str(b)))
        assert a.read_bytes() == b.read_bytes()


def test_named_shared_line_and_scatter_domains_and_distinct_size_guides():
    raw = _raw()
    raw["left"] = [v if i < 8 else None for i, v in enumerate(raw["t"])]
    raw["right"] = [v if i >= 8 else None for i, v in enumerate(raw["t"])]
    cfg = SemanticSpec(scale_id="study", hue="h", size="m", sizes=[1, 3], style="s")
    p = (
        mp.plot(raw)
        .layout(1, 2)
        .size(12, 5)
        .lineplot("left", "y", semantics=cfg, errorbar=None, panel=0)
        .lineplot("right", "y", semantics=cfg, errorbar=None, panel=1)
    )
    assert mp.validate(p.spec) == []
    a, b = p.render().axes
    assert a.get_legend_handles_labels()[1] == b.get_legend_handles_labels()[1]
    assert all(l.get_linewidth() == 1 for l in _data_lines(a)) and all(
        l.get_linewidth() == 3 for l in _data_lines(b)
    )
    p.scatter("t", "y", semantics=cfg, panel=0)
    assert mp.validate(p.spec) == []
    labels = p.render().axes[0].get_legend_handles_labels()[1]
    assert any(s.startswith("size (line width, pt)") for s in labels) and any(
        s.startswith("size:") for s in labels
    )


def test_curves_limit_and_boolean_numeric_style_identity():
    raw = {"t": list(range(257)), "y": [1] * 257, "m": list(range(257))}
    p = mp.plot(raw).lineplot("t", "y", size="m", errorbar=None)
    assert any("256" in v for v in mp.validate(p.spec))
    raw = {"t": [1, 2, 1, 2], "y": [1, 2, 3, 4], "s": [True, True, 1, 1]}
    p = mp.plot(raw).lineplot("t", "y", style="s", errorbar=None)
    assert mp.validate(p.spec) == [] and len(_data_lines(p.render().axes[0])) == 2


@pytest.mark.parametrize("orient", ["v", "h"])
def test_band_endpoints_are_independent_sample_sd_not_style_pooled(orient):
    p = mp.plot(_raw()).lineplot(
        "t", "y", semantics=_cfg(), errorbar="sd", orient=orient
    )
    ax = p.render().axes[0]
    assert len(ax.collections) == 4
    delta = float(np.std([1, 3], ddof=1))
    for index, band in enumerate(ax.collections):
        vertices = np.asarray(band.get_paths()[0].vertices)
        numbers = vertices[:, 1 if orient == "v" else 0]
        lo = [2, 3, 9, 10][index] - delta
        hi = [4, 5, 11, 12][index] + delta
        assert numbers.min() == pytest.approx(lo) and numbers.max() == pytest.approx(hi)


@pytest.mark.parametrize("show_first", [False, True])
def test_shared_line_guides_once_per_panel_and_dataset_references_kept(show_first):
    p = mp.plot(_raw()).size(8, 5)
    for index in range(2):
        cfg = SemanticSpec(
            scale_id="study", hue="h", legend=show_first if index == 0 else True
        )
        p.lineplot(
            "t",
            "y",
            semantics=cfg,
            errorbar=None,
            label=f"Data{index}",
            href="https://example.com/lines",
        )
    assert mp.validate(p.spec) == []
    labels = p.render().axes[0].get_legend_handles_labels()[1]
    assert labels.count("hue: h=A") == 1 and labels.count("hue: h=B") == 1
    assert len(labels) == 4


@pytest.mark.parametrize("orient", ["v", "h"])
def test_honest_singleton_intervals_and_declared_positive_log_axis(orient):
    raw = {"t": [1, 2, -3], "y": [1, 2, 0], "s": ["X", "X", None]}
    p = mp.plot(raw).lineplot("t", "y", style="s", errorbar="sd", orient=orient)
    p.xscale("log").yscale("log")
    assert mp.validate(p.spec) == []
    with pytest.warns(UserWarning, match="omitted"):
        ax = p.render().axes[0]
    assert not ax.collections and len(_data_lines(ax)) == 1
    invalid = p.spec
    invalid.data.columns["s"][-1] = "X"
    assert any("positive" in v for v in mp.validate(invalid))


def test_tuple_dash_and_reserved_style_slots_canonicalize_without_ghost_curves():
    p = mp.plot(_raw()).lineplot(
        "t",
        "y",
        errorbar=None,
        semantics={
            "style": "s",
            "style_order": ("absent", "Y", "X"),
            "markers": ("D", "s", "o"),
            "dashes": (":", "--", "-"),
        },
    )
    assert mp.validate(p.spec) == []
    ax = p.render().axes[0]
    assert len(_data_lines(ax)) == 2
    assert all("absent" not in label for label in ax.get_legend_handles_labels()[1])
    assert mp.Plot.from_json(p.to_json()).spec == p.spec


def test_typed_core_canonical_schema_python_editor_and_rng(tmp_path):
    import jsonschema
    from dashboard.editor_server import EditorSession

    cfg = _cfg()
    p = mp.plot(_raw()).lineplot("t", "y", semantics=cfg, n_boot=25)
    cfg.sizes[0] = 8
    assert p.spec.panels[0].layers[0].semantics != cfg
    assert mp.apply(p.action_log) == p.spec
    assert mp.Plot.from_json(p.to_json()).spec == p.spec
    jsonschema.validate(p.spec.to_dict(), mp.json_schema())
    before = np.random.get_state()
    p.render()
    after = np.random.get_state()
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]
    session = EditorSession()
    session.load_spec(p.to_json())
    assert session.error is None and session.png.startswith(b"\x89PNG")
