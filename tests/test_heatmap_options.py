"""Typed heatmap display contracts: never change the stored matrix values."""

from __future__ import annotations

import copy
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.colors import LogNorm, TwoSlopeNorm
from mudplot._heatmap import MAX_HEATMAP_ANNOTATIONS
from mudplot.color.convert import srgb_to_linear


def build(config=None, *, values=None, cmap="sequential", **style):
    values = [[-2, 0, 3], [1, 4, 8]] if values is None else values
    return (
        mp.plot()
        .matrix("m", values)
        .heatmap("m", heatmap=config, cmap_kind=cmap, **style)
        .size(6, 4)
    )


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def test_mask_annotations_labels_grid_square_and_source_preservation():
    config = {
        "annot": True,
        "fmt": ".1f",
        "center": 0,
        "square": True,
        "mask": [[False, True, False], [False, False, False]],
        "xlabels": ["A", "B", "C"],
        "ylabels": ["North", "South"],
    }
    original = copy.deepcopy(config)
    p = build(config, cmap="diverging", line_width=0.5, edge_color="#ffffff")
    assert mp.validate(p.spec) == [] and config == original
    ax = p.render().axes[0]
    image = ax.images[0]
    assert isinstance(image.norm, TwoSlopeNorm) and image.norm(0) == pytest.approx(0.5)
    array = image.get_array()
    assert array is not None
    np.testing.assert_array_equal(np.ma.getmaskarray(array), config["mask"])
    assert [text.get_text() for text in ax.texts] == [
        "-2.0",
        "3.0",
        "1.0",
        "4.0",
        "8.0",
    ]
    assert [text.get_text() for text in ax.get_xticklabels()] == ["A", "B", "C"]
    assert [text.get_text() for text in ax.get_yticklabels()] == ["North", "South"]
    assert ax.get_aspect() == 1
    assert p.spec.data.matrices["m"] == [[-2, 0, 3], [1, 4, 8]]
    assert any(tick.gridline.get_visible() for tick in ax.xaxis.get_minor_ticks())


def test_normalization_uses_unmasked_values_and_robust_visible_percentiles():
    values = [[0, 1, 2, 3, 10000]]
    p = build(
        {"robust": True, "mask": [[False, False, False, False, True]]}, values=values
    )
    image = p.render().axes[0].images[0]
    np.testing.assert_allclose(image.get_clim(), np.percentile([0, 1, 2, 3], [2, 98]))
    q = build({"robust": True, "vmin": -2, "vmax": 5}, values=values)
    assert q.render().axes[0].images[0].get_clim() == (-2, 5)


def test_center_auto_bounds_are_symmetric_and_explicit_bounds_are_respected():
    p = build({"center": 0}, values=[[1, 2, 3]], cmap="diverging")
    image = p.render().axes[0].images[0]
    assert image.get_clim() == (-3, 3)
    q = build({"center": 0, "vmin": -1, "vmax": 4}, cmap="diverging")
    assert q.render().axes[0].images[0].get_clim() == (-1, 4)


def test_log_norm_masked_zero_and_original_value_annotation():
    p = build(
        {"norm": "log", "annot": True, "fmt": ".0f", "mask": [[True, False, False]]},
        values=[[0, 1, 100]],
    )
    ax = p.render().axes[0]
    assert isinstance(ax.images[0].norm, LogNorm)
    assert [text.get_text() for text in ax.texts] == ["1", "100"]
    assert ax.get_xscale() == ax.get_yscale() == "linear"
    assert p.spec.data.matrices["m"] == [[0, 1, 100]]


@pytest.mark.parametrize(
    "norm,value", [("linear", 0), ("linear", 1e308), ("log", 0.1), ("log", 1e-320)]
)
def test_constant_colour_ranges_remain_finite(norm, value):
    image = build({"norm": norm}, values=[[value, value]]).render().axes[0].images[0]
    low, high = image.get_clim()
    assert np.isfinite([low, high]).all() and low < high
    if norm == "log":
        assert low > 0


@pytest.mark.parametrize("alpha", [1, 0.2, 0])
def test_annotation_chooses_stronger_black_white_contrast_after_alpha(alpha):
    values = [[0, 0.5, 1]]
    p = build({"annot": True, "vmin": 0, "vmax": 1}, values=values, alpha=alpha)
    ax = p.render().axes[0]
    image = ax.images[0]
    background = np.asarray(ax.get_facecolor()[:3])
    for value, text in zip(values[0], ax.texts, strict=True):
        rgba = image.cmap(image.norm(value))
        opacity = alpha * rgba[3]
        rgb = np.asarray(rgba[:3]) * opacity + background * (1 - opacity)
        luminance = float(srgb_to_linear(rgb) @ np.array([0.2126, 0.7152, 0.0722]))
        black, white = (luminance + 0.05) / 0.05, 1.05 / (luminance + 0.05)
        assert text.get_color() == ("#000000" if black >= white else "#ffffff")
        assert max(black, white) >= 4.5


@pytest.mark.parametrize(
    "config",
    [
        {"norm": "bad"},
        {"vmin": True},
        {"vmax": float("inf")},
        {"vmin": 3, "vmax": 2},
        {"robust": 1},
        {"annot": "yes"},
        {"square": 1},
        {"fmt": "1000000f"},
        {"mask": [[True]]},
        {"mask": [[1, 0, 0], [0, 0, 0]]},
        {"mask": [[True] * 3] * 2},
        {"xlabels": ["A"]},
        {"ylabels": ["N", 2]},
        {"center": 0, "norm": "log"},
        {"center": 0, "vmin": 0},
        {"center": 0, "vmax": -1},
        {"norm": "log"},
    ],
)
def test_invalid_options_are_reported_without_mutating_spec(config):
    spec = build().spec
    spec.panels[0].layers[0].heatmap = mp.HeatmapSpec(**config)
    original = copy.deepcopy(spec)
    assert mp.validate(spec)
    assert spec == original


def test_center_requires_diverging_palette_and_cell_axes_are_not_log_colour_axes():
    assert mp.validate(build({"center": 0}).spec)
    assert mp.validate(build({"annot": True}).xscale("log").spec)
    assert mp.validate(build({"annot": True}, line_width=-1).spec)
    assert mp.validate(build({"annot": True}, edge_color="#wrong").spec)
    assert mp.validate(build(None, line_width=0.5).spec)


def test_annotations_resource_limit_and_empty_or_bad_matrices_are_rejected():
    p = build({"annot": True}, values=[[1] * (MAX_HEATMAP_ANNOTATIONS + 1)])
    assert any("at most" in issue for issue in mp.validate(p.spec))
    for values in ([], [[]], [[1, 2], [3]], [[True]], [[float("nan")]]):
        assert mp.validate(build({"annot": True}, values=values).spec)


def test_typed_heatmap_config_is_not_ignored_on_other_layer_types():
    p = mp.plot({"x": [1, 2], "y": [2, 3]}).line("x", "y", heatmap=mp.HeatmapSpec())
    assert any("heatmap is not supported" in issue for issue in mp.validate(p.spec))
    with pytest.raises(ValueError, match="unknown"):
        build({"unknown": True})


def test_derived_nonrepresentable_colour_span_preserves_existing_output(tmp_path):
    p = build({}, values=[[-1e308, 1e308]])
    path = tmp_path / "keep.png"
    path.write_bytes(b"previous output")
    with pytest.raises(ValueError, match="span is not representable"):
        p.save(str(path))
    assert path.read_bytes() == b"previous output" and not plt.get_fignums()


@pytest.mark.parametrize("extension", ["png", "pdf", "svg"])
def test_heatmap_json_actions_exports_and_global_rng(tmp_path, extension):
    state = np.random.get_state()
    p = build(
        {
            "annot": True,
            "center": 0,
            "mask": [[False, True, False], [False, False, False]],
        },
        cmap="diverging",
    )
    assert mp.apply(p.action_log) == mp.Plot.from_json(p.to_json()).spec == p.spec
    first, second = tmp_path / f"a.{extension}", tmp_path / f"b.{extension}"
    plt.close(p.save(str(first)))
    plt.close(mp.Plot.from_json(p.to_json()).save(str(second)))
    assert first.read_bytes() == second.read_bytes()
    after = np.random.get_state()
    assert state[0] == after[0] and state[2:] == after[2:]
    np.testing.assert_array_equal(state[1], after[1])


def test_heatmap_schema_editor_and_old_spec_defaults():
    import jsonschema
    from dashboard.editor_server import EditorSession

    p = build({"annot": True, "center": 0}, cmap="diverging")
    jsonschema.validate(p.spec.to_dict(), mp.json_schema())
    session = EditorSession()
    session.load_spec(p.to_json())
    assert session.store.state == p.spec and b"<svg" in session.export("svg")
    old = build().spec.to_dict()
    del old["panels"][0]["layers"][0]["heatmap"]
    assert mp.FigureSpec.from_dict(old).panels[0].layers[0].heatmap is None
    assert build().spec == build(None).spec


def test_heatmap_core_needs_no_optional_numeric_dependency():
    script = (
        "import sys; import mudplot as m; "
        "p=m.plot().matrix('m',[[1,2],[3,4]]).heatmap('m',heatmap={'annot':True}); "
        "assert m.validate(p.spec)==[] and m.apply(p.action_log)==p.spec; "
        "assert m.Plot.from_json(p.to_json()).spec==p.spec; "
        "assert 'numpy' not in sys.modules and 'matplotlib' not in sys.modules"
    )
    subprocess.run([sys.executable, "-S", "-c", script], check=True)
