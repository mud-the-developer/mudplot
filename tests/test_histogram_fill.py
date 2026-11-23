"""Explicit histogram fill changes geometry, not measurements or legacy defaults."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from jsonschema import Draft202012Validator
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle, StepPatch
from mudplot.spec import HistogramSpec

DATA = {
    "x": [0.25, 0.75, 1, 2, 3],
    "w": [1, 2, 3, 9, 6],
    "g": ["A", "B", "A", "B", "A"],
}


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.mark.parametrize("element", ["bars", "step"])
@pytest.mark.parametrize("fill", [False, True])
@pytest.mark.parametrize("multiple", ["layer", "stack", "dodge"])
@pytest.mark.parametrize("orient", ["v", "h"])
@pytest.mark.parametrize("cumulative", [False, True])
def test_explicit_fill_matches_independent_weighted_native_geometry(
    element, fill, multiple, orient, cumulative
):
    plot = mp.plot(copy.deepcopy(DATA)).hist(
        "x",
        bins=[0, 1, 3],
        weights="w",
        group="g",
        stat="density",
        element=element,
        fill=fill,
        multiple=multiple,
        orient=orient,
        cumulative=cumulative,
    )
    assert mp.validate(plot.spec) == []
    before = plot.to_json()
    ax = plot.render().axes[0]
    _, reference = plt.subplots()
    baseline = np.zeros(2)
    expected = []
    for slot, counts in enumerate(([1, 9], [2, 9])):
        heights = np.asarray(counts, dtype=float)
        if cumulative:
            heights = np.cumsum(heights) / 21
        else:
            heights /= np.array([1, 2]) * 21
        base = baseline.copy() if multiple == "stack" else np.zeros(2)
        if element == "step":
            edges = [0, 1, 3]
            values = base + heights
            native_base = base if multiple == "stack" else 0
            if multiple == "dodge":
                edges = (
                    [0, 0, 0.5, 1, 1, 2, 3] if slot == 0 else [0, 0.5, 1, 1, 2, 3, 3]
                )
                values = np.array([0, heights[0], 0, 0, heights[1], 0])
            expected.append(
                reference.stairs(
                    values,
                    edges,
                    baseline=native_base,
                    fill=fill,
                    orientation="vertical" if orient == "v" else "horizontal",
                )
            )
        else:
            starts = np.array([0, 1])
            widths = np.array([1, 2])
            if multiple == "dodge":
                starts = np.array([0, 1]) if slot == 0 else np.array([0.5, 2])
                widths = np.array([0.5, 1])
            if orient == "v":
                bars = reference.bar(
                    starts, heights, width=widths, bottom=base, align="edge", fill=fill
                )
            else:
                bars = reference.barh(
                    starts, heights, height=widths, left=base, align="edge", fill=fill
                )
            expected.extend(bars.patches)
        baseline += heights
    assert len(ax.patches) == len(expected)
    for actual, native in zip(ax.patches, expected, strict=True):
        assert actual.get_fill() is fill
        if element == "step":
            assert isinstance(actual, StepPatch) and isinstance(native, StepPatch)
            for observed, wanted in zip(
                actual.get_data(), native.get_data(), strict=True
            ):
                np.testing.assert_allclose(observed, wanted)
            np.testing.assert_allclose(
                np.asarray(actual.get_path().vertices),
                np.asarray(native.get_path().vertices),
            )
        else:
            assert isinstance(actual, Rectangle) and isinstance(native, Rectangle)
            np.testing.assert_allclose(
                actual.get_bbox().get_points(), native.get_bbox().get_points()
            )
    assert ax.get_legend_handles_labels()[1] == ["A", "B"]
    assert plot.to_json() == before and plot.spec.data.columns == DATA


@pytest.mark.parametrize("element", ["bars", "step"])
@pytest.mark.parametrize("fill", [False, True])
@pytest.mark.parametrize("edge", [None, "#7C3AED"])
@pytest.mark.parametrize("alpha,width", [(0.35, 1.4), (0, 0), (1, 0)])
def test_fill_face_outline_hatch_reserved_style_and_legend(
    element, fill, edge, alpha, width
):
    plot = (
        mp.plot({"x": [0.5, 2.5], "w": [1, 2], "g": ["B", "B"]})
        .encoding(
            redundant_encoding=True,
            hatches=["/", "xx", ".."],
            line_styles=["-", "--", ":"],
        )
        .hist(
            "x",
            bins=[0, 1, 3],
            group="g",
            weights="w",
            hue_order=["empty", "A", "B"],
            element=element,
            fill=fill,
            multiple="dodge",
            color="#0E7490",
            edge_color=edge,
            alpha=alpha,
            line_width=width,
        )
        .legend(location="outside right")
    )
    figure = plot.render()
    ax = figure.axes[0]
    for patch in ax.patches:
        assert patch.get_fill() is fill
        assert patch.get_hatch() == (".." if fill and alpha != 0 else None)
        assert patch.get_linewidth() == width and patch.get_alpha() == alpha
        if fill and edge is None:
            if element == "bars" or alpha == 0:
                assert to_rgba(patch.get_edgecolor())[3] == 0
            else:
                assert to_rgba(patch.get_edgecolor()) != to_rgba(patch.get_facecolor())
        else:
            np.testing.assert_allclose(
                to_rgba(patch.get_edgecolor()), to_rgba(edge or "#0E7490", alpha)
            )
        if fill:
            np.testing.assert_allclose(
                to_rgba(patch.get_facecolor()), to_rgba("#0E7490", alpha)
            )
        else:
            assert to_rgba(patch.get_facecolor())[3] == 0
        if element == "step" or not fill:
            assert patch.get_linestyle() == ("-" if width == 0 else ":")
    legend = ax.get_legend()
    assert legend is not None and [t.get_text() for t in legend.get_texts()] == ["B"]
    handle = legend.legend_handles[0]
    if isinstance(handle, Patch):
        assert to_rgba(handle.get_facecolor())[3] == (alpha if fill else 0)
        assert handle.get_hatch() == (".." if fill and alpha != 0 else None)
    else:
        assert isinstance(handle, Line2D) and element == "step" and not fill
    if alpha == 0:
        from matplotlib.backends.backend_agg import FigureCanvasAgg

        canvas = FigureCanvasAgg(figure)
        canvas.draw()
        # Isolate opacity from Matplotlib 3.8's iterative constrained layout.
        figure.set_layout_engine("none")
        before = np.asarray(canvas.buffer_rgba()).copy()
        limits = ax.get_xlim(), ax.get_ylim()
        for patch in ax.patches:
            patch.set_visible(False)
        canvas.draw()
        np.testing.assert_array_equal(before, np.asarray(canvas.buffer_rgba()))
        assert (ax.get_xlim(), ax.get_ylim()) == limits
        assert [text.get_text() for text in legend.get_texts()] == ["B"]


def test_omitted_and_null_fill_keep_old_wire_and_render_defaults():
    old_options = {
        "stat": "count",
        "weights": None,
        "common_norm": True,
        "cumulative": False,
        "multiple": "layer",
        "element": "bars",
    }
    assert HistogramSpec().to_dict() == old_options
    for wire in (old_options, {**old_options, "fill": None}):
        decoded = HistogramSpec.from_dict(wire)
        assert isinstance(decoded, HistogramSpec) and decoded.to_dict() == old_options
    legacy = mp.plot(DATA).hist("x", fill=None)
    assert legacy.spec.panels[0].layers[0].histogram is None
    for element, filled in (("bars", True), ("step", False)):
        plot = mp.plot(DATA).hist("x", stat="count", element=element)
        before = plot.to_json()
        assert "fill" not in json.loads(before)["panels"][0]["layers"][0]["histogram"]
        assert mp.Plot.from_json(before).to_json() == before
        assert all(
            patch.get_fill() is filled for patch in plot.render().axes[0].patches
        )
    explicit = mp.plot(DATA).hist("x", fill=False)
    config = explicit.spec.panels[0].layers[0].histogram
    assert config is not None and config.to_dict()["fill"] is False


@pytest.mark.parametrize("element", ["bars", "step"])
@pytest.mark.parametrize("fill", [False, True])
def test_fill_action_schema_and_python_editor_roundtrip(element, fill):
    from dashboard.editor_server import EditorSession, _build_action
    from mudplot import actions as A

    plot = mp.plot(DATA).hist(
        "x",
        bins=[0, 1, 3],
        weights="w",
        group="g",
        element=element,
        fill=fill,
        multiple="stack",
    )
    wire = json.loads(plot.to_json())
    assert wire["panels"][0]["layers"][0]["histogram"]["fill"] is fill
    assert mp.Plot.from_json(plot.to_json()).spec == plot.spec
    assert mp.apply(json.loads(json.dumps(plot.action_log))) == plot.spec
    validator = Draft202012Validator(mp.json_schema())
    validator.validate(wire)
    published = Path(__file__).resolve().parents[1] / "schemas/figure_spec.schema.json"
    Draft202012Validator(json.loads(published.read_text())).validate(wire)
    assert any(
        field["name"] == "fill" for field in mp.capabilities()["histogram"]["fields"]
    )
    session = EditorSession()
    session.dispatch_safe(A.SetData(copy.deepcopy(DATA)))
    payload = {
        "layer_type": "hist",
        "layer_json": json.dumps(wire["panels"][0]["layers"][0]),
    }
    session.dispatch_safe(_build_action("add_layer_json", payload, session.store.state))
    assert session.error is None and session.png.startswith(b"\x89PNG")
    config = session.store.state.panels[0].layers[0].histogram
    assert config is not None and config.to_dict()["fill"] is fill
    before, png = copy.deepcopy(session.store.state), session.png
    wire["panels"][0]["layers"][0]["histogram"]["fill"] = "yes"
    payload["layer_json"] = json.dumps(wire["panels"][0]["layers"][0])
    with pytest.raises((TypeError, ValueError), match="fill"):
        _build_action("add_layer_json", payload, session.store.state)
    assert session.store.state == before and session.png == png


@pytest.mark.parametrize("value", [0, 1, 1.0, "yes", [], {}])
def test_fill_is_strict_bool_or_null_at_api_json_and_schema_boundaries(value):
    plot = mp.plot(DATA).hist("x", fill=value)
    assert any("histogram fill" in issue for issue in mp.validate(plot.spec))
    config = {**HistogramSpec().to_dict(), "fill": value}
    with pytest.raises((TypeError, ValueError), match="fill"):
        HistogramSpec.from_dict(config)
    assert list(Draft202012Validator(mp.json_schema()).iter_errors(plot.spec.to_dict()))


@pytest.mark.parametrize("element", ["bars", "step"])
@pytest.mark.parametrize("fill", [False, True])
def test_fill_on_inverted_log_axes_keeps_raw_edges_and_linear_mass(element, fill):
    plot = (
        mp.plot(DATA)
        .hist(
            "x",
            bins=[0.1, 1, 3],
            group="g",
            weights="w",
            element=element,
            fill=fill,
            multiple="dodge",
            stat="density",
        )
        .xscale("log")
        .xlim(3, 0.1)
    )
    ax = plot.render().axes[0]
    assert ax.get_xscale() == "log" and ax.get_yscale() == "linear"
    assert ax.get_xlim() == (3, 0.1)
    assert all(patch.get_fill() is fill for patch in ax.patches)
    for patch in ax.patches:
        if isinstance(patch, StepPatch):
            assert np.all(patch.get_data()[1] > 0)
        else:
            assert isinstance(patch, Rectangle) and patch.get_x() > 0


@pytest.mark.parametrize("element", ["bars", "step"])
@pytest.mark.parametrize("fill", [False, True])
def test_fill_temporal_y2_matches_numeric_reference(element, fill):
    from test_temporal_secondary import DATES, DAYS, _assert_secondary_matches

    source = {"t": DATES, "g": ["A", "B"] * 3, "w": [1, 2, 3, 4, 2, 1]}

    def build(data, axis):
        return mp.plot(data).hist(
            "t",
            bins=3,
            group="g",
            weights="w",
            element=element,
            fill=fill,
            multiple="stack",
            stat="density",
            axis=axis,
        )

    plot = build(source, "y2").secondary_yaxis("Density").date_axis("x", timezone="UTC")
    _assert_secondary_matches(plot, build({**source, "t": DAYS}, "y"))


def test_opaque_filled_step_hatches_have_visible_contrasting_strokes(tmp_path):
    plot = (
        mp.plot(DATA)
        .encoding(redundant_encoding=True, hatches=["/", "xx"])
        .hist(
            "x",
            bins=[0, 1, 3],
            group="g",
            element="step",
            fill=True,
            color="#0E7490",
            alpha=1,
        )
    )
    output = tmp_path / "hatches.svg"
    plt.close(plot.save(output))
    paths = ET.parse(output).findall(
        ".//{http://www.w3.org/2000/svg}pattern/{http://www.w3.org/2000/svg}path"
    )
    assert paths
    for path in paths:
        style = dict(
            item.strip().split(":", 1)
            for item in path.get("style", "").split(";")
            if ":" in item
        )
        assert style.get("stroke", "none").strip().lower() not in {"none", "#0e7490"}
        assert float(style.get("stroke-opacity", "1")) > 0


@pytest.mark.parametrize("fill", [False, True])
def test_fill_cli_preserves_boolean_and_renders(tmp_path, fill):
    plot = mp.plot(DATA).hist("x", bins=[0, 1, 3], group="g", element="step", fill=fill)
    source, output = tmp_path / "plot.json", tmp_path / "plot.svg"
    mp.save_spec(plot.spec, source)
    subprocess.run(
        [sys.executable, "-m", "mudplot", "render", str(source), str(output)],
        check=True,
    )
    assert output.read_bytes().startswith(b"<?xml")
    assert mp.load_spec(source) == plot.spec
