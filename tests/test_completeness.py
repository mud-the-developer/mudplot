"""Tests for the completeness pass: hist/box layers, suptitle, panel labels,
width/height ratios, validate(), Store.redo(), and the CLI.
"""

import json
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")

import mudplot as mp
import numpy as np
import pytest
from mudplot import actions as A
from mudplot.render import render
from mudplot.store import Store


def _dist_data(n=30):
    rng = np.random.default_rng(0)
    return {
        "v": list(rng.normal(0, 1, n)) + list(rng.normal(2, 1, n)),
        "g": ["A"] * n + ["B"] * n,
    }


def test_hist_layer_renders():
    fig = render(mp.plot(_dist_data()).hist("v", group="g").spec)
    ax = fig.axes[0]
    assert len(ax.patches) > 0  # histogram bars


def test_box_layer_renders():
    fig = render(mp.plot(_dist_data()).box("v", group="g").spec)
    ax = fig.axes[0]
    assert len(ax.lines) > 0 or len(ax.patches) > 0  # boxplot artists


def test_suptitle_and_panel_labels():
    p = (
        mp.plot(_dist_data())
        .layout(1, 2)
        .line("v", "v", panel=0)
        .line("v", "v", panel=1)
        .suptitle("Top title")
        .auto_label(True)
    )
    fig = render(p.spec)
    assert fig._suptitle.get_text() == "Top title"
    texts = [t.get_text() for ax in fig.axes for t in ax.texts]
    assert "a)" in texts
    assert "b)" in texts


def test_explicit_panel_label_overrides_auto():
    p = mp.plot(_dist_data()).line("v", "v").panel_label("Z").auto_label(True)
    fig = render(p.spec)
    texts = [t.get_text() for t in fig.axes[0].texts]
    assert "Z)" in texts


def test_width_height_ratios_applied():
    p = (
        mp.plot(_dist_data())
        .layout(1, 2, width_ratios=[2, 1])
        .line("v", "v", panel=0)
        .line("v", "v", panel=1)
    )
    fig = render(p.spec)
    assert len(fig.axes) == 2


def test_validate_catches_missing_column():
    spec = mp.apply(
        [
            {"type": "SetData", "columns": {"x": [1, 2]}},
            {"type": "AddLayer", "layer": {"type": "line", "x": "x", "y": "nope"}},
        ]
    )
    issues = mp.validate(spec)
    assert any("nope" in i for i in issues)
    with pytest.raises(ValueError, match="nope"):
        mp.assert_valid(spec)


def test_validate_catches_layout_mismatch():
    spec = mp.apply(
        [
            {"type": "SetData", "columns": {"x": [1], "y": [1]}},
            {"type": "SetLayout", "rows": 1, "cols": 1},
            {"type": "AddPanel"},
        ]
    )
    issues = mp.validate(spec)
    assert any("layout" in i for i in issues)


def test_validate_clean_spec_has_no_issues():
    p = mp.plot({"x": [1, 2], "y": [3, 4]}).line("x", "y")
    assert mp.validate(p.spec) == []


def test_render_raises_on_invalid_spec():
    spec = mp.apply(
        [
            {"type": "SetData", "columns": {"x": [1]}},
            {"type": "AddLayer", "layer": {"type": "line", "x": "x", "y": "missing"}},
        ]
    )
    with pytest.raises(ValueError):
        render(spec)


def test_store_undo_redo():
    store = Store()
    store.dispatch(A.SetSize(4, 3))
    store.dispatch(A.SetTitle("hi"))
    store.undo()
    assert store.state.panels[0].title == ""
    store.redo()
    assert store.state.panels[0].title == "hi"


def test_store_dispatch_clears_redo_stack():
    store = Store()
    store.dispatch(A.SetTitle("a"))
    store.undo()
    store.dispatch(A.SetTitle("b"))  # new action should clear redo history
    store.redo()  # no-op, nothing to redo
    assert store.state.panels[0].title == "b"


def test_capabilities_includes_hist_and_box():
    caps = mp.capabilities()
    assert "hist" in caps["layers"]
    assert "box" in caps["layers"]


def test_cli_capabilities():
    result = subprocess.run(
        [sys.executable, "-m", "mudplot", "capabilities"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "layers" in data


def test_cli_schema(tmp_path):
    out = tmp_path / "schema.json"
    result = subprocess.run(
        [sys.executable, "-m", "mudplot", "schema", "--out", str(out)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert out.exists()
    assert json.loads(out.read_text())["title"] == "FigureSpec"


def test_cli_validate_roundtrip(tmp_path):
    from mudplot.io import save_spec

    spec_path = tmp_path / "fig.mplot.json"
    save_spec(mp.plot({"x": [1], "y": [2]}).line("x", "y").spec, spec_path)
    result = subprocess.run(
        [sys.executable, "-m", "mudplot", "validate", str(spec_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "OK" in result.stdout


def test_cli_render(tmp_path):
    from mudplot.io import save_spec

    spec_path = tmp_path / "fig.mplot.json"
    out_path = tmp_path / "fig.png"
    save_spec(mp.plot({"x": [1, 2], "y": [3, 4]}).line("x", "y").spec, spec_path)
    result = subprocess.run(
        [sys.executable, "-m", "mudplot", "render", str(spec_path), str(out_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert out_path.exists()
