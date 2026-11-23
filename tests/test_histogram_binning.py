"""Fixed named rules and unit-preserving discrete integration contracts."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from mudplot._histogram import histogram_summary
from mudplot._histogram_bins import HISTOGRAM_BIN_RULES, named_bin_edges
from mudplot._temporal import temporal_coordinates


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.mark.parametrize("rule", HISTOGRAM_BIN_RULES)
def test_named_edges_use_usable_rows_once_and_weights_only_for_mass(rule):
    source = {
        "x": [0, 1, 2, 3, 100, 1000, None],
        "w": [1, 2, 3, 4, 5, 0, 9],
        "g": ["A", "B", "A", "B", "A", "B", "A"],
    }
    plot = mp.plot(source).hist("x", bins=rule, weights="w", group="g")
    assert mp.validate(plot.spec) == []
    before = plot.to_json()
    result = histogram_summary(source, plot.spec.panels[0].layers[0])
    np.testing.assert_array_equal(
        result.edges, named_bin_edges([0, 1, 2, 3, 100], rule)
    )
    scaled = {**source, "w": [value * 100 for value in source["w"]]}
    rescaled = histogram_summary(scaled, plot.spec.panels[0].layers[0])
    assert result.edges == rescaled.edges
    np.testing.assert_allclose(
        [curve.heights for curve in rescaled.curves],
        np.asarray([curve.heights for curve in result.curves]) * 100,
    )
    np.testing.assert_allclose(sum(sum(curve.heights) for curve in result.curves), 15)
    assert plot.to_json() == before and plot.spec.data.columns == source
    assert mp.Plot.from_json(before).spec == mp.apply(plot.action_log) == plot.spec


def test_discrete_alias_is_canonical_and_does_not_change_legacy_defaults():
    source = {"x": [-2, 0, 2], "w": [1, 2, 3]}
    plot = mp.plot(source).hist("x", discrete=True, weights="w")
    canonical = mp.plot(source).hist("x", bins="discrete", weights="w")
    assert plot.spec == canonical.spec
    result = histogram_summary(source, plot.spec.panels[0].layers[0])
    assert result.edges == (-2.5, -1.5, -0.5, 0.5, 1.5, 2.5)
    assert result.curves[0].heights == (1, 0, 2, 0, 3)
    for legacy in (
        mp.plot(source).hist("x"),
        mp.plot(source).hist("x", discrete=None),
        mp.plot(source).hist("x", discrete=False),
    ):
        assert legacy.spec.panels[0].layers[0].histogram is None
        assert legacy.spec.panels[0].layers[0].bins == 20


@pytest.mark.parametrize("bad", [0, 1, "yes", [], {}])
def test_discrete_alias_rejects_nonbool_before_mutating_plot(bad):
    plot = mp.plot({"x": [0, 1]})
    before = plot.to_json()
    with pytest.raises(TypeError, match="discrete"):
        plot.hist("x", discrete=bad)
    assert plot.to_json() == before


@pytest.mark.parametrize("bins", [2, [0, 1, 2], "fd"])
def test_discrete_does_not_silently_ignore_custom_bin_requests(bins):
    with pytest.raises(ValueError, match="custom bins"):
        mp.plot({"x": [0, 1]}).hist("x", bins=bins, discrete=True)
    with pytest.raises(ValueError, match="conflicts"):
        mp.plot({"x": [0, 1]}).hist("x", bins="discrete", discrete=False)


@pytest.mark.parametrize(
    "source", [{"x": [0.5, 1.5]}, {"x": [10**16]}, {"x": [0, 10000]}]
)
def test_discrete_invalid_grid_is_a_pure_validation_error(source):
    plot = mp.plot(source).hist("x", discrete=True)
    assert any("discrete" in issue for issue in mp.validate(plot.spec))
    with pytest.raises(ValueError, match="discrete"):
        plot.render()


def test_named_rules_are_only_typed_univariate_histograms():
    legacy = mp.plot({"x": [0, 1]}).hist("x")
    legacy_spec = legacy.spec
    legacy_spec.panels[0].layers[0].bins = "auto"
    assert any("typed histogram" in issue for issue in mp.validate(legacy_spec))
    bivariate = mp.plot({"x": [0, 1], "y": [1, 2]}).hist2d("x", "y")
    bivariate_spec = bivariate.spec
    bivariate_spec.panels[0].layers[0].bins = "auto"
    assert any("typed histogram" in issue for issue in mp.validate(bivariate_spec))


@pytest.mark.parametrize("unit", ["s", "ms", "day"])
@pytest.mark.parametrize("orient,axis", [("v", "y2"), ("h", "y")])
def test_numeric_temporal_discrete_uses_declared_unit_not_a_utc_day(unit, orient, axis):
    from test_temporal_distributions import _assert_geometry
    from test_temporal_secondary import _drawn

    source = {"t": [0, 1, 2], "w": [1, 2, 3]}
    options = {"timezone": "UTC", "unit": unit, "origin": "2026-01-01"}
    raw = temporal_coordinates(source["t"], **options)
    edges = temporal_coordinates([-0.5, 0.5, 1.5, 2.5], **options)
    plot = (
        mp.plot(source)
        .secondary_yaxis("Mass")
        .hist("t", discrete=True, weights="w", stat="density", orient=orient, axis=axis)
        .date_axis("x" if orient == "v" else "y", **options)
    )
    assert mp.validate(plot.spec) == []
    before = plot.to_json()
    reference = mp.plot({**source, "t": raw}).hist(
        "t",
        bins=edges,
        weights="w",
        stat="density",
        orient=orient,
    )
    actual_figure, expected_figure = plot.render(), reference.render()
    actual = actual_figure.axes[-1] if axis == "y2" else actual_figure.axes[0]
    _assert_geometry(_drawn(actual), _drawn(expected_figure.axes[0]))
    assert plot.to_json() == before and plot.spec.data.columns == source
    assert mp.Plot.from_json(before).spec == mp.apply(plot.action_log) == plot.spec


@pytest.mark.parametrize("zone", ["UTC", "+02:00", "-05:30"])
def test_iso_discrete_calendar_midnight_grid_and_empty_days(zone):
    from test_temporal_distributions import _assert_geometry
    from test_temporal_secondary import _drawn

    source = {"t": ["2026-01-01", "2026-01-03"], "w": [1, 3]}
    options = {"timezone": zone}
    values = temporal_coordinates(source["t"], **options)
    edges = temporal_coordinates(
        [
            "2025-12-31T12:00:00",
            "2026-01-01T12:00:00",
            "2026-01-02T12:00:00",
            "2026-01-03T12:00:00",
        ],
        **options,
    )
    plot = (
        mp.plot(source).hist("t", discrete=True, weights="w").date_axis("x", **options)
    )
    expected = mp.plot({**source, "t": values}).hist("t", bins=edges, weights="w")
    assert mp.validate(plot.spec) == []
    _assert_geometry(_drawn(plot.render().axes[0]), _drawn(expected.render().axes[0]))
    assert plot.spec.data.columns == source


@pytest.mark.parametrize("unit", ["us", "ns"])
def test_temporal_half_unit_precision_is_rejected_not_rounded(unit):
    plot = (
        mp.plot({"t": [0, 1000]})
        .hist("t", discrete=True)
        .date_axis("x", timezone="UTC", unit=unit, origin="2026-01-01")
    )
    assert any("finer than microseconds" in issue for issue in mp.validate(plot.spec))
    with pytest.raises(ValueError, match="finer than microseconds"):
        plot.render()


def test_iso_discrete_checks_display_clock_not_input_spelling():
    source = {"t": ["2026-01-01T00:00:00+02:00"]}
    plot = mp.plot(source).hist("t", discrete=True).date_axis("x", timezone="UTC")
    assert any(
        "midnight in the display clock" in issue for issue in mp.validate(plot.spec)
    )
    plot.date_axis("x", timezone="+02:00")
    assert mp.validate(plot.spec) == []
    plt.close(plot.render())


def test_discrete_selection_ignores_zero_weight_and_unselected_noninteger_rows():
    source = {"x": [0, 1, 0.25, 0.75], "w": [1, 2, 0, 5], "g": ["A", "A", "A", "B"]}
    plot = mp.plot(source).hist(
        "x", bins="discrete", weights="w", group="g", hue_order=["A"]
    )
    assert mp.validate(plot.spec) == []
    result = histogram_summary(source, plot.spec.panels[0].layers[0])
    assert result.edges == (-0.5, 0.5, 1.5) and result.curves[0].heights == (1, 2)
    assert plot.spec.data.columns == source


@pytest.mark.parametrize(
    "values",
    [[1.0, 1.000000000000001], [0.0, float.fromhex("0x0.0000000000001p-1022")]],
)
def test_stone_ignores_unselected_collapsed_candidate_grids(values):
    edges = named_bin_edges(values, "stone")
    np.testing.assert_array_equal(edges, values)


@pytest.mark.parametrize(
    "column,kwargs",
    [("missing", {}), ("t", {"weights": "missing"}), ("t", {"group": "missing"})],
)
def test_temporal_discrete_missing_columns_return_issues_not_keyerror(column, kwargs):
    plot = (
        mp.plot({"t": [0]})
        .hist(column, bins="discrete", **kwargs)
        .date_axis("x", timezone="UTC", unit="s", origin="2026-01-01")
    )
    issues = mp.validate(plot.spec)
    assert issues and all(isinstance(issue, str) for issue in issues)
    with pytest.raises(ValueError):
        plot.render()


@pytest.mark.parametrize("bins", ["auto", "discrete"])
def test_bins_schema_editor_history_rejected_state_and_cli(tmp_path, bins):
    import copy
    import json
    import subprocess
    import sys
    from pathlib import Path

    from dashboard.editor_server import EditorSession, _build_action
    from jsonschema import Draft202012Validator
    from mudplot import actions as A

    source = {"x": [0, 1, 2, 3, 100], "w": [1, 2, 3, 4, 5]}
    plot = mp.plot(source).hist("x", bins=bins, weights="w")
    wire = json.loads(plot.to_json())
    schema = Path(__file__).resolve().parents[1] / "schemas/figure_spec.schema.json"
    Draft202012Validator(json.loads(schema.read_text())).validate(wire)
    session = EditorSession()
    session.dispatch_safe(A.SetData(source))
    layer = wire["panels"][0]["layers"][0]
    payload = {"layer_type": "hist", "layer_json": json.dumps(layer)}
    session.dispatch_safe(_build_action("add_layer_json", payload, session.store.state))
    assert session.error is None and session.png.startswith(b"\x89PNG")
    before, preview = copy.deepcopy(session.store.state), session.png
    session.undo()
    assert not session.store.state.panels[0].layers
    session.redo()
    assert session.store.state == before and session.png == preview
    layer["bins"] = "adaptive"
    payload["layer_json"] = json.dumps(layer)
    session.dispatch_safe(_build_action("add_layer_json", payload, session.store.state))
    assert session.error and session.store.state == before and session.png == preview
    input_path, output = tmp_path / "bins.json", tmp_path / "bins.svg"
    mp.save_spec(plot.spec, input_path)
    subprocess.run(
        [sys.executable, "-m", "mudplot", "render", str(input_path), str(output)],
        check=True,
    )
    assert mp.load_spec(input_path) == plot.spec
    assert output.read_bytes().startswith(b"<?xml")
    assert plot.spec.data.columns == source
