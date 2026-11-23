"""V2 C06: selected-row weight mass, not weighted-mean or invented intervals."""

import copy
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import matplotlib.pyplot as plt
import mudplot as mp
import pytest
from matplotlib.container import BarContainer
from mudplot._estimate import summarize


def _data():
    return {
        "x": ["A", "A", "A", "B", "B", "C", None, "C"],
        "g": ["u", "u", "v", "u", "v", "v", "u", None],
        "w": [1.0, 2.0, 3.0, 4.0, 5.0, 0.0, 100.0, 50.0],
    }


def _summary(plot):
    assert mp.validate(plot.spec) == []
    return summarize(plot.spec.data.columns, plot.spec.panels[0].layers[0])


@pytest.mark.parametrize(
    ("mode", "factor"),
    [("count", 15), ("probability", 1), ("proportion", 1), ("percent", 100)],
)
def test_weighted_counts_and_global_normalization_match_mass_reference(mode, factor):
    data = _data()
    original = copy.deepcopy(data)
    plot = mp.plot(data).countplot("x", group="g", weights="w", stat=mode)
    result = _summary(plot)
    actual = {(e.category, e.group): e.value for e in result.estimates}
    expected = {("A", "u"): 3, ("A", "v"): 3, ("B", "u"): 4, ("B", "v"): 5}
    assert actual == pytest.approx(
        {key: value / 15 * factor for key, value in expected.items()}
    )
    assert result.categories == ["A", "B"] and result.groups == ["u", "v"]
    assert sum(e.n for e in result.estimates) == 5
    assert all(e.lower is None and e.upper is None for e in result.estimates)
    assert data == original and plot.spec.data.columns == original


@pytest.mark.parametrize("mode", ["count", "probability", "proportion", "percent"])
def test_unweighted_and_explicit_none_keep_previous_spec_and_values(mode):
    data = _data()
    old = mp.plot(data).countplot("x", group="g", stat=mode)
    explicit = mp.plot(data).countplot("x", group="g", stat=mode, weights=None)
    assert old.to_json() == explicit.to_json()
    result = _summary(old)
    counts = {("A", "u"): 2, ("A", "v"): 1, ("B", "u"): 1, ("B", "v"): 1, ("C", "v"): 1}
    factor = 1 if mode == "count" else (100 if mode == "percent" else 1) / 6
    assert {(e.category, e.group): e.value for e in result.estimates} == pytest.approx(
        {key: n * factor for key, n in counts.items()}
    )


def test_explicit_level_filters_define_weight_denominator_and_reserve_slots():
    plot = mp.plot(_data()).countplot(
        "x",
        group="g",
        weights="w",
        stat="percent",
        order=["missing", "B", "A"],
        hue_order=["v"],
    )
    result = _summary(plot)
    assert result.categories == ["missing", "B", "A"]
    assert [(e.category, e.group) for e in result.estimates] == [("B", "v"), ("A", "v")]
    assert [e.value for e in result.estimates] == pytest.approx([62.5, 37.5])


@pytest.mark.parametrize("mode", ["probability", "proportion", "percent"])
def test_normalized_weights_scale_only_when_raw_total_would_overflow(mode):
    plot = mp.plot({"x": ["A", "B"], "w": [1e308, 1e308]}).countplot(
        "x", weights="w", stat=mode
    )
    expected = [50, 50] if mode == "percent" else [0.5, 0.5]
    assert [e.value for e in _summary(plot).estimates] == expected


def test_ordinary_finite_weights_do_not_introduce_scaled_rounding():
    plot = mp.plot({"x": ["A", "A", "B"], "w": [1, 2, 5]}).countplot(
        "x", weights="w", stat="probability"
    )
    assert [e.value for e in _summary(plot).estimates] == [0.375, 0.625]


def test_raw_mass_overflow_is_explicit_and_leaves_previous_output(tmp_path):
    plot = mp.plot({"x": ["A", "A"], "w": [1e308, 1e308]}).countplot("x", weights="w")
    target = tmp_path / "existing.png"
    target.write_bytes(b"old output")
    before = plt.get_fignums()
    with pytest.raises(ValueError, match="weighted count mass exceeds finite range"):
        plot.save(target)
    assert target.read_bytes() == b"old output" and plt.get_fignums() == before


@pytest.mark.parametrize("value", [-1, True, "bad"])
def test_bad_weight_values_fail_before_render(value):
    plot = mp.plot({"x": ["A"], "w": [value]}).countplot("x", weights="w")
    assert any(
        "weights must be finite nonnegative" in issue
        for issue in mp.validate(plot.spec)
    )
    with pytest.raises(ValueError):
        plot.render()


@pytest.mark.parametrize("value", [float("inf"), float("-inf")])
def test_programmatic_nonfinite_weights_are_rejected(value):
    plot = mp.plot({"x": ["A"], "w": [1]}).countplot("x", weights="w")
    bad = replace(
        plot.spec, data=replace(plot.spec.data, columns={"x": ["A"], "w": [value]})
    )
    assert any("finite" in issue for issue in mp.validate(bad))


@pytest.mark.parametrize("weights", [[0, 0], [None, None]])
def test_no_positive_usable_weight_is_not_a_zero_measurement(weights):
    plot = mp.plot({"x": ["A", "B"], "w": weights}).countplot("x", weights="w")
    assert any("no usable observations" in issue for issue in mp.validate(plot.spec))


@pytest.mark.parametrize("orient", ["v", "h"])
def test_stacked_weighted_percentages_have_correct_endpoints_and_labels(orient):
    plot = mp.plot(_data()).countplot(
        "x",
        group="g",
        weights="w",
        stat="percent",
        stack=True,
        value_labels=True,
        label_format=".1f",
        orient=orient,
    )
    figure = plot.render()
    try:
        ax = figure.axes[0]
        containers = [c for c in ax.containers if isinstance(c, BarContainer)]
        assert len(containers) == 2
        first, second = containers[0][0], containers[1][0]
        assert (first.get_width() if orient == "h" else first.get_height()) == 20
        assert (second.get_x() if orient == "h" else second.get_y()) == 20
        assert (second.get_width() if orient == "h" else second.get_height()) == 20
        assert [t.get_text() for t in ax.texts] == ["20.0", "26.7", "20.0", "33.3"]
    finally:
        plt.close(figure)


def test_facet_normalization_is_cell_local_and_empty_reserved_cells_are_safe():
    data = {"x": ["A", "B", "A", "B"], "w": [1, 3, 4, 1], "f": ["u", "u", "v", "v"]}
    plot = (
        mp.plot(data)
        .countplot("x", weights="w", stat="percent")
        .facet(col="f", col_order=["missing", "u", "v"])
        .size(10, 3)
    )
    original = plot.to_json()
    figure = plot.render()
    try:
        heights = [
            [
                p.get_height()
                for c in ax.containers
                if isinstance(c, BarContainer)
                for p in c
            ]
            for ax in figure.axes
        ]
        assert heights[0] == []
        assert heights[1] == [25, 75] and heights[2] == [80, 20]
        assert plot.to_json() == original and plot.spec.data.columns == data
    finally:
        plt.close(figure)


@pytest.mark.parametrize("kind", ["countplot", "barplot", "pointplot", "lineplot"])
def test_reserved_empty_statistical_facets_keep_validation_and_no_invented_marks(kind):
    plot = mp.plot({"x": [1, 2], "y": [2, 3], "f": ["observed", "observed"]})
    if kind == "countplot":
        plot.countplot("x")
    else:
        getattr(plot, kind)("x", "y", errorbar=None)
    plot.facet(col="f", col_order=["empty", "observed"]).size(7, 3)
    assert mp.validate(plot.spec) == []
    figure = plot.render()
    plt.close(figure)


@pytest.mark.parametrize("weights", [[0, 0], [None, None]])
def test_nonempty_facet_with_no_usable_weight_still_fails(weights):
    plot = mp.plot({"x": ["A", "B"], "w": weights, "f": ["observed", "observed"]})
    plot.countplot("x", weights="w")
    with pytest.raises(ValueError, match="no usable observations"):
        plot.facet(col="f", col_order=["empty", "observed"])


@pytest.mark.parametrize(
    ("kind", "orient"),
    [
        (kind, orient)
        for kind in ("countplot", "barplot", "pointplot")
        for orient in ("v", "h")
    ]
    + [("lineplot", "v")],
)
def test_all_selected_native_statistical_facets_can_be_empty(kind, orient):
    data = {"x": [1], "y": [3], "w": [2], "f": ["seen"]}
    plot = mp.plot(data)
    if kind == "countplot":
        plot.countplot("x", weights="w", native_scale=True, orient=orient)
    elif kind == "lineplot":
        plot.lineplot("x", "y", weights="w", errorbar=None)
    else:
        getattr(plot, kind)(
            "x", "y", weights="w", errorbar=None, native_scale=True, orient=orient
        )
    plot.facet(col="f", col_order=["empty"]).size(6, 3)
    before = plot.to_json()
    assert mp.validate(plot.spec) == []
    figure = plot.render()
    try:
        assert all(
            not ax.lines and not ax.patches and not ax.collections for ax in figure.axes
        )
        assert plot.to_json() == before and plot.spec.data.columns == data
    finally:
        plt.close(figure)


def test_empty_reserved_facet_still_checks_statistical_configuration():
    plot = mp.plot({"x": [1, 2], "w": [1, 2], "f": ["observed", "observed"]})
    plot.countplot("x", weights="w").facet(col="f", col_order=["empty"])
    panel = plot.spec.panels[0]
    layer = panel.layers[0]
    assert layer.stat is not None
    bad = replace(layer, stat=replace(layer.stat, n_boot=0))
    spec = replace(plot.spec, panels=[replace(panel, layers=[bad])])
    assert any("n_boot" in issue for issue in mp.validate(spec))


def test_empty_reserved_facet_still_checks_native_geometry_options():
    plot = mp.plot({"x": [1, 2], "w": [1, 2], "f": ["observed", "observed"]})
    plot.countplot("x", weights="w", native_scale=True).facet(
        col="f", col_order=["empty"]
    )
    panel = plot.spec.panels[0]
    bad = replace(panel.layers[0], bar_width=2)
    spec = replace(plot.spec, panels=[replace(panel, layers=[bad])])
    assert any("native bar_width" in issue for issue in mp.validate(spec))


def test_weights_roundtrip_actions_and_schema_without_core_dependencies(tmp_path):
    plot = mp.plot(_data()).countplot("x", group="g", weights="w", stat="percent")
    assert mp.apply(plot.action_log) == plot.spec
    restored = mp.Plot.from_json(plot.to_json())
    assert restored.spec == plot.spec
    config = restored.spec.panels[0].layers[0].stat
    assert config is not None and config.weights == "w"
    code = (
        "import sys,mudplot as m; "
        "p=m.plot({'x':['a'],'w':[2]}).countplot('x',weights='w'); "
        "assert m.validate(p.spec)==[]; assert m.apply(p.action_log)==p.spec; "
        "assert 'numpy' not in sys.modules"
    )
    subprocess.run(
        [sys.executable, "-S", "-c", code],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
        check=True,
    )


def test_python_editor_can_add_reopen_and_export_weighted_countplot():
    from dashboard.editor_server import EditorSession, _build_action

    session = EditorSession()
    session.dispatch_safe(mp.actions.SetData(_data()))
    session.dispatch_safe(
        _build_action(
            "add_layer_json",
            {
                "layer_type": "countplot",
                "layer_json": json.dumps(
                    {
                        "x": "x",
                        "group": "g",
                        "stat": {
                            "estimator": "count",
                            "errorbar": None,
                            "weights": "w",
                            "normalize": "percent",
                        },
                    }
                ),
            },
            session.store.state,
        )
    )
    assert session.error is None and session.png.startswith(b"\x89PNG")
    config = session.store.state.panels[0].layers[0].stat
    assert config is not None and config.weights == "w"
    assert b"<svg" in session.export("svg")


@pytest.mark.parametrize("extension", ["png", "svg", "pdf"])
def test_weighted_count_exports_do_not_mutate_data(tmp_path, extension):
    plot = (
        mp.plot(_data())
        .countplot("x", group="g", weights="w")
        .labels(x="Condition", y="Declared weight mass")
    )
    before = plot.to_json()
    figure = plot.save(tmp_path / f"weighted.{extension}")
    plt.close(figure)
    assert plot.to_json() == before
    assert (tmp_path / f"weighted.{extension}").stat().st_size > 100
