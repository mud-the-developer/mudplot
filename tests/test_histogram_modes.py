"""Owner-approved post-height composition and raw-center native poly geometry."""

import copy
import json
from fractions import Fraction

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from mudplot._histogram import histogram_summary

from test_histogram_statistics import data


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.mark.parametrize(
    "stat", ["count", "frequency", "probability", "percent", "density"]
)
@pytest.mark.parametrize("common", [False, True])
@pytest.mark.parametrize("cumulative", [False, True])
def test_fill_normalizes_existing_heights_not_raw_mass(stat, common, cumulative):
    plot = mp.plot(data()).hist(
        "x",
        bins=[0, 1, 3],
        weights="w",
        group="g",
        stat=stat,
        common_norm=common,
        cumulative=cumulative,
        multiple="fill",
    )
    before = plot.to_json()
    issues = mp.validate(plot.spec)
    if stat in {"count", "frequency"} and not common:
        assert any("common_norm=False" in issue for issue in issues)
        return
    if stat == "frequency" and cumulative:
        assert any("cumulative frequency" in issue for issue in issues)
        return
    assert issues == []
    result = histogram_summary(plot.spec.data.columns, plot.spec.panels[0].layers[0])
    reference = []
    for counts in ([1, 9], [2, 9]):
        values = np.asarray(counts, dtype=float)
        if cumulative:
            values = np.cumsum(values)
        if stat in {"probability", "percent", "density"}:
            values /= 21 if common else sum(counts)
            if stat == "percent":
                values *= 100
        if stat == "frequency" or (stat == "density" and not cumulative):
            values /= [1, 2]
        reference.append(values)
    expected = np.array(reference)
    expected /= expected.sum(axis=0)
    np.testing.assert_allclose([curve.heights for curve in result.curves], expected)
    assert plot.to_json() == before and plot.spec.data.columns == data()
    assert mp.apply(json.loads(json.dumps(plot.action_log))) == plot.spec
    assert mp.Plot.from_json(before).spec == plot.spec


def test_cumulative_fill_is_composition_and_can_decrease():
    source = {"x": [0.5, 1.5, 2.5, 2.5], "w": [9, 9, 1, 1], "g": ["A", "B", "A", "B"]}
    plot = mp.plot(source).hist(
        "x",
        bins=[0, 1, 2, 3],
        weights="w",
        group="g",
        stat="probability",
        common_norm=False,
        cumulative=True,
        multiple="fill",
    )
    result = histogram_summary(source, plot.spec.panels[0].layers[0])
    np.testing.assert_allclose(result.curves[0].heights, [1, 0.5, 0.5])
    np.testing.assert_allclose(result.curves[1].heights, [0, 0.5, 0.5])


def test_fill_empty_bins_and_hues_stay_empty():
    source = {"x": [0.5, 2.5], "g": ["B", "B"]}
    plot = mp.plot(source).hist(
        "x",
        bins=[0, 1, 2, 3],
        group="g",
        hue_order=["empty", "A", "B"],
        multiple="fill",
    )
    result = histogram_summary(source, plot.spec.panels[0].layers[0])
    assert [curve.group for curve in result.curves] == ["empty", "A", "B"]
    assert [curve.heights for curve in result.curves] == [(), (), (1, 0, 1)]


@pytest.mark.parametrize("small,large", [(1e308, 1e308), (1e-320, 1.0)])
def test_fill_handles_overflowing_sums_and_preserves_subnormal_shares(small, large):
    source = {"x": [0.5, 0.5], "w": [small, large], "g": ["A", "B"]}
    plot = mp.plot(source).hist(
        "x", bins=[0, 1], weights="w", group="g", multiple="fill"
    )
    result = histogram_summary(source, plot.spec.panels[0].layers[0])
    denominator = Fraction(small) + Fraction(large)
    expected = [float(Fraction(weight) / denominator) for weight in (small, large)]
    assert [curve.heights[0] for curve in result.curves] == expected
    assert all(value > 0 for value in expected)


def test_fill_rejects_unrepresentable_positive_share():
    source = {
        "x": [0.5, 0.5],
        "w": [float.fromhex("0x0.0000000000001p-1022"), 1e308],
        "g": ["A", "B"],
    }
    plot = mp.plot(source).hist(
        "x", bins=[0, 1], weights="w", group="g", multiple="fill"
    )
    with pytest.raises(ValueError, match="fill fractions lose positive"):
        plot.render()


@pytest.mark.parametrize("fill", [False, True])
@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("multiple", ["layer", "stack", "dodge", "fill"])
def test_poly_matches_independent_native_centers_and_paths(fill, orient, multiple):
    plot = mp.plot(copy.deepcopy(data())).hist(
        "x",
        bins=[0, 1, 3],
        weights="w",
        group="g",
        stat="density",
        element="poly",
        fill=fill,
        multiple=multiple,
        orient=orient,
    )
    assert mp.validate(plot.spec) == []
    before = plot.to_json()
    ax = plot.render().axes[0]
    _, reference = plt.subplots()
    heights = np.array([[1 / 21, 9 / 42], [2 / 21, 9 / 42]])
    if multiple == "fill":
        heights = np.array([[1 / 3, 0.5], [2 / 3, 0.5]])
    baseline = np.zeros(2)
    for slot, values in enumerate(heights):
        centers = [0.5, 2]
        if multiple == "dodge":
            centers = [0.25, 1.5] if slot == 0 else [0.75, 2.5]
        base = baseline.copy() if multiple in {"stack", "fill"} else np.zeros(2)
        top = base + values
        if fill:
            draw = reference.fill_between if orient == "v" else reference.fill_betweenx
            native = draw(centers, top, base)
            actual = ax.collections[slot]
            np.testing.assert_allclose(
                np.asarray(actual.get_paths()[0].vertices),
                np.asarray(native.get_paths()[0].vertices),
            )
        else:
            x, y = (centers, top) if orient == "v" else (top, centers)
            line = ax.lines[slot]
            np.testing.assert_allclose(np.asarray(line.get_xdata()), x)
            np.testing.assert_allclose(np.asarray(line.get_ydata()), y)
        baseline += values
    mass_limits = ax.get_ylim() if orient == "v" else ax.get_xlim()
    assert mass_limits[0] == 0
    observed_limits = ax.get_xlim() if orient == "v" else ax.get_ylim()
    assert observed_limits[0] <= 0 and observed_limits[1] >= 3
    assert ax.get_legend_handles_labels()[1] == ["A", "B"]
    assert (
        mp.Plot.from_json(before).spec == plot.spec
        and mp.apply(plot.action_log) == plot.spec
    )
    assert plot.to_json() == before and plot.spec.data.columns == data()


def test_poly_default_is_a_line_and_one_bin_rejects_clearly():
    plot = mp.plot(data()).hist("x", bins=[0, 1, 3], stat="count", element="poly")
    ax = plot.render().axes[0]
    assert len(ax.lines) == 1 and not ax.collections and not ax.patches
    invalid = mp.plot(data()).hist("x", bins=1, element="poly")
    assert any(
        "poly requires at least two bins" in issue
        for issue in mp.validate(invalid.spec)
    )


def test_poly_does_not_jitter_unrepresentable_centers():
    edge = np.nextafter(1.0, 2.0)
    plot = mp.plot({"x": [1.0, edge]}).hist(
        "x",
        bins=[1.0, edge, np.nextafter(edge, 2.0)],
        element="poly",
    )
    assert mp.validate(plot.spec) == []
    with pytest.raises(ValueError, match="representable bin centers"):
        plot.render()


@pytest.mark.parametrize("fill", [False, True])
def test_empty_poly_does_not_expand_other_layer_limits(fill):
    base = mp.plot(data()).line("x", "w", label="kept")
    plot = (
        mp.plot(data())
        .line("x", "w", label="kept")
        .hist("x", bins=[10, 11, 12], group="g", element="poly", fill=fill)
    )
    expected, actual = base.render().axes[0], plot.render().axes[0]
    assert actual.get_xlim() == expected.get_xlim()
    assert actual.get_ylim() == expected.get_ylim()
    assert len(actual.lines) == 1 and not actual.collections
    assert actual.get_legend_handles_labels()[1] == ["kept"]


@pytest.mark.parametrize("axis", ["y", "y2"])
def test_poly_collections_keep_hatch_quality_diagnostics(axis):
    source = {
        "x": [0.5, 1.5, 2.5] * 6,
        "g": [f"g{i}" for i in range(6) for _ in range(3)],
    }
    plot = (
        mp.plot(source)
        .secondary_yaxis("Mass")
        .encoding(redundant_encoding=True, hatches=["///"])
        .hist("x", bins=[0, 1, 2, 3], group="g", element="poly", fill=True, axis=axis)
    )
    before = plot.to_json()
    issues = [issue for issue in plot.lint(visual=True) if issue.code == "hatch-noise"]
    assert len(issues) == 1 and issues[0].panel == 0
    assert plot.to_json() == before


@pytest.mark.parametrize("fill", [False, True])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_poly_zero_alpha_and_stroke_preserve_legend_limits_and_no_ink(fill, orient):
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    plot = mp.plot(data()).hist(
        "x",
        bins=[0, 1, 3],
        group="g",
        element="poly",
        fill=fill,
        orient=orient,
        alpha=0,
        line_width=0,
    )
    figure = plot.render()
    canvas = FigureCanvasAgg(figure)
    canvas.draw()
    figure.set_layout_engine("none")
    before = np.asarray(canvas.buffer_rgba()).copy()
    ax = figure.axes[0]
    limits = ax.get_xlim(), ax.get_ylim()
    for artist in (*ax.lines, *ax.collections):
        assert artist.get_alpha() == 0
        artist.set_visible(False)
    canvas.draw()
    np.testing.assert_array_equal(before, np.asarray(canvas.buffer_rgba()))
    assert (ax.get_xlim(), ax.get_ylim()) == limits
    assert ax.get_legend_handles_labels()[1] == ["A", "B"]


@pytest.mark.parametrize("element", ["bars", "step"])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_fill_bar_and_step_match_manual_fraction_stack(element, orient):
    from test_temporal_distributions import _assert_geometry
    from test_temporal_secondary import _drawn

    actual = mp.plot(data()).hist(
        "x",
        bins=[0, 1, 3],
        weights="w",
        group="g",
        multiple="fill",
        element=element,
        orient=orient,
    )
    reference = mp.plot(
        {
            "x": [0.5, 2, 0.5, 2],
            "w": [1 / 3, 0.5, 2 / 3, 0.5],
            "g": ["A", "A", "B", "B"],
        }
    ).hist(
        "x",
        bins=[0, 1, 3],
        weights="w",
        group="g",
        multiple="stack",
        element=element,
        orient=orient,
    )
    _assert_geometry(
        _drawn(actual.render().axes[0]), _drawn(reference.render().axes[0])
    )


@pytest.mark.parametrize("fill", [False, True])
def test_poly_fill_temporal_y2_matches_numeric_reference(fill):
    from test_temporal_secondary import DATES, DAYS, _assert_secondary_matches

    source = {"t": DATES, "w": [1, 2, 3, 4, 2, 1], "g": ["A", "B"] * 3}

    def build(columns, axis):
        return mp.plot(columns).hist(
            "t",
            bins=3,
            weights="w",
            group="g",
            element="poly",
            fill=fill,
            multiple="fill",
            stat="density",
            axis=axis,
        )

    plot = (
        build(source, "y2")
        .secondary_yaxis("Composition")
        .date_axis("x", timezone="UTC")
    )
    _assert_secondary_matches(plot, build({**source, "t": DAYS}, "y"))


@pytest.mark.parametrize(
    "element,fill,multiple",
    [
        ("bars", None, "fill"),
        ("step", None, "fill"),
        ("poly", None, "layer"),
        ("poly", True, "fill"),
    ],
)
def test_modes_editor_cli_and_rejected_state(tmp_path, element, fill, multiple):
    import subprocess
    import sys
    from pathlib import Path

    from dashboard.editor_server import EditorSession, _build_action
    from jsonschema import Draft202012Validator
    from mudplot import actions as A

    plot = mp.plot(data()).hist(
        "x",
        bins=[0, 1, 3],
        weights="w",
        group="g",
        stat="probability",
        common_norm=False,
        element=element,
        fill=fill,
        multiple=multiple,
    )
    wire = json.loads(plot.to_json())
    published = Path(__file__).resolve().parents[1] / "schemas/figure_spec.schema.json"
    Draft202012Validator(json.loads(published.read_text())).validate(wire)
    session = EditorSession()
    session.dispatch_safe(A.SetData(data()))
    payload = {
        "layer_type": "hist",
        "layer_json": json.dumps(wire["panels"][0]["layers"][0]),
    }
    session.dispatch_safe(_build_action("add_layer_json", payload, session.store.state))
    assert session.error is None and session.png.startswith(bytes.fromhex("89504e47"))
    before, preview = copy.deepcopy(session.store.state), session.png
    wire["panels"][0]["layers"][0]["histogram"]["multiple"] = "mirror"
    payload["layer_json"] = json.dumps(wire["panels"][0]["layers"][0])
    session.dispatch_safe(_build_action("add_layer_json", payload, session.store.state))
    assert session.error and session.store.state == before and session.png == preview
    source, output = tmp_path / "mode.json", tmp_path / "mode.svg"
    mp.save_spec(plot.spec, source)
    subprocess.run(
        [sys.executable, "-m", "mudplot", "render", str(source), str(output)],
        check=True,
    )
    assert mp.load_spec(source) == plot.spec and output.read_bytes().startswith(
        b"<?xml"
    )


@pytest.mark.parametrize("filled", [False, True])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_poly_log_inversion_keeps_raw_arithmetic_centers(filled, orient):
    plot = mp.plot({"x": [1, 2, 4, 8], "g": ["A", "B", "A", "B"]}).hist(
        "x",
        bins=[1, 3, 10],
        group="g",
        element="poly",
        fill=filled,
        multiple="fill",
        orient=orient,
    )
    if orient == "v":
        plot.xscale("log").xlim(10, 1)
    else:
        plot.yscale("log").ylim(10, 1)
    ax = plot.render().axes[0]
    assert (ax.get_xlim() if orient == "v" else ax.get_ylim()) == (10, 1)
    if filled:
        vertices = np.asarray(ax.collections[0].get_paths()[0].vertices)
        np.testing.assert_array_equal(
            np.unique(vertices[:, 0 if orient == "v" else 1]), [2, 6.5]
        )
    else:
        values = ax.lines[0].get_xdata() if orient == "v" else ax.lines[0].get_ydata()
        np.testing.assert_array_equal(np.asarray(values), [2, 6.5])
