"""Scientific composition regressions at a fixed, single-column export size."""

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.container import BarContainer
from matplotlib.patches import Circle, Rectangle
from mudplot._quality import _collisions, assess, drawn_texts


def _small(plot, *, dpi=100):
    return plot.size(3.5, 2.6).dispatch(mp.actions.SetDpi(dpi))


def _bars():
    return _small(
        mp.plot(
            {
                "condition": ["Low"] * 3 + ["High"] * 3,
                "score": [0.95, 0.98, 0.96, 0.97, 0.96, 0.99],
                "method": ["A", "B", "C"] * 2,
            }
        )
        .bar("condition", "score", group="method")
        .labels(x="Condition", y="Measured score")
        .ylim(0, 1)
        .legend(location="upper right")
    )


def _two_methods():
    return _small(
        mp.plot({"method": ["A", "B"], "score": [0.97, 0.99]})
        .bar("method", "score", group="method")
        .labels(x="Method", y="Measured score")
        .ylim(0, 1)
        .legend(location="upper right")
    )


def _panels():
    data = {
        "time": [0, 1, 2] * 2,
        "score": [1, 2, 3, 2, 3, 4],
        "method": ["A"] * 3 + ["B"] * 3,
    }
    plot = mp.plot(data).layout(1, 2)
    for index in range(2):
        plot.line("time", "score", group="method", panel=index)
        plot.labels(x="Elapsed time (s)", y="Measured score", panel=index)
    return mp.Plot.from_json(
        mp.to_json(
            replace(plot.size(7, 2.6).spec, dpi=100, suptitle="Controlled comparison")
        )
    )


def _codes(report):
    return {issue.code for issue in report}


def test_regression_bar_legends_use_actual_rectangles_and_are_repaired():
    plot = _bars()
    before = plot.to_json()
    raw = plot.render()
    assert assess(raw, plot.spec).measurements["legend_data_collisions"] > 0
    figure = plot.render(layout_policy="smart")
    after = assess(figure, plot.spec)
    assert after.measurements["legend_data_collisions"] == 0
    assert after.measurements["clipped_elements"] == 0
    assert after.measurements["text_overlaps"] == 0
    assert len(figure.legends) == 1
    assert plot.to_json() == before
    assert figure.get_size_inches() == pytest.approx([3.5, 2.6])


def test_regression_shared_legends_deduplicate_without_overlapping_suptitle():
    plot = _panels()
    assert "duplicate-legend" in _codes(plot.lint(visual=True))
    figure = plot.render(layout_policy="smart")
    report = assess(figure, plot.spec)
    assert report.measurements["duplicate_legends"] == 0
    assert report.measurements["legend_data_collisions"] == 0
    assert report.measurements["text_overlaps"] == 0
    assert len(figure.legends) == 1
    assert len(figure.legends[0].get_texts()) == 2


def test_two_method_preset_direct_labels_replace_hatches_but_preserve_print():
    plot = _two_methods()
    original = plot.to_json()
    normal = plot.render(layout_policy="smart")
    assert normal.axes[0].get_legend() is None
    assert not normal.legends
    assert {text.get_text() for text in normal.axes[0].texts} >= {"A", "B"}
    assert all(not patch.get_hatch() for patch in normal.axes[0].patches)
    printed = plot.render(layout_policy="smart-print")
    assert any(patch.get_hatch() for patch in printed.axes[0].patches)
    assert plot.to_json() == original


def test_regression_dense_scatter_recommends_time_not_silent_geometry_change():
    data = {"time": list(range(600)), "measurement": [i % 5 for i in range(600)]}
    plot = _small(mp.plot(data).scatter("time", "measurement"))
    before = plot.to_json()
    report = plot.lint(visual=True)
    assert "overcrowded-data" in _codes(report)
    advice = mp.recommend(data, x="time", y="measurement", time=True)
    assert advice["recommendations"][0]["kind"] == "trend"
    figure = plot.render(layout_policy="smart")
    offsets = np.asarray(figure.axes[0].collections[0].get_offsets())
    np.testing.assert_array_equal(offsets[:, 0], data["time"])
    np.testing.assert_array_equal(offsets[:, 1], data["measurement"])
    assert plot.to_json() == before
    assert not advice["data_changed"] and not advice["units_inferred"]


@pytest.mark.parametrize(
    ("values", "code"),
    [([0.0, 0.0, 0.0], "all-zero"), ([1e-12, 2e-12, 3e-12], "small-scale")],
)
def test_regression_metric_semantics_and_small_scales_are_not_silently_changed(
    values, code
):
    plot = _small(
        mp.plot({"internal_step": [0, 1, 2], "loss": values})
        .line("internal_step", "loss")
        .labels(y="metric", title="Panel 1")
    )
    before = plot.to_json()
    report = plot.lint(visual=True, layout_policy="smart")
    assert {code, "axis-description", "generic-title"} <= _codes(report)
    assert plot.spec.panels[0].y.scale == "linear"
    assert plot.to_json() == before
    encoded = json.loads(json.dumps(report.to_dict(), allow_nan=False))
    assert all(
        issue["suggestion"] for issue in encoded["issues"] if issue["code"] != "style"
    )
    assert encoded["measurements"]["size_inches"] == pytest.approx([3.5, 2.6])


def test_visual_report_detects_text_clipping_and_overlaps_at_actual_size():
    plot = _small(mp.plot({"x": [0, 1], "y": [1, 2]}).line("x", "y"))
    figure = plot.render()
    figure.text(0.5, 0.5, "Duplicate")
    figure.text(0.5, 0.5, "Duplicate")
    figure.text(1.1, 0.5, "Outside")
    assert {"text-overlap", "clipped"} <= _codes(assess(figure, plot.spec))


def test_invisible_or_clipped_bars_do_not_create_collisions():
    plot = _bars()
    figure = plot.render()
    for patch in figure.axes[0].patches:
        patch.set_visible(False)
    assert assess(figure, plot.spec).measurements["legend_data_collisions"] == 0


def test_legend_deduplication_checks_style_not_just_text():
    plot = mp.plot({"x": [0, 1], "y": [1, 2]}).layout(1, 2)
    plot.line("x", "y", label="A", color="red", panel=0)
    plot.line("x", "y", label="A", color="blue", panel=1)
    figure = _small(plot).render(layout_policy="smart")
    assert assess(figure, plot.spec).measurements["duplicate_legends"] == 0
    legends = [ax.get_legend() for ax in figure.axes if ax.get_legend()]
    assert sum(len(legend.get_texts()) for legend in [*legends, *figure.legends]) == 2


@pytest.mark.parametrize("extension", ["png", "pdf", "svg"])
def test_smart_export_is_deterministic_and_preserves_publication_size(
    tmp_path, extension
):
    plot = _bars()
    a, b = tmp_path / f"a.{extension}", tmp_path / f"b.{extension}"
    figure = plot.save(str(a), layout_policy="smart")
    plot.save(str(b), layout_policy="smart")
    assert a.read_bytes() == b.read_bytes()
    assert (
        cast(Any, figure).mudplot_quality["measurements"]["legend_data_collisions"] == 0
    )
    if extension == "png":
        assert plt.imread(a).shape[:2] == (260, 350)


def test_default_render_and_json_contract_remain_unchanged():
    plot = _two_methods()
    original = plot.to_json()
    default = plot.render()
    assert not hasattr(default, "mudplot_quality")
    assert default.axes[0].get_legend() is not None
    assert any(patch.get_hatch() for patch in default.axes[0].patches)
    plot.render(layout_policy="smart")
    restored = mp.Plot.from_json(original)
    assert restored.to_json() == original == plot.to_json()
    assert not restored.lint().measurements


def test_invalid_policy_does_not_leak_figures_or_replace_existing_file(tmp_path):
    plot = _bars()
    destination = tmp_path / "existing.png"
    destination.write_bytes(b"keep me")
    original = plt.get_fignums()
    with pytest.raises(ValueError, match="layout_policy"):
        plot.save(str(destination), layout_policy="unknown")
    assert destination.read_bytes() == b"keep me"
    assert plt.get_fignums() == original
    with pytest.raises(ValueError, match="visual=True"):
        plot.lint(layout_policy="smart")


def test_cli_render_and_machine_readable_lint(tmp_path):
    plot = _bars()
    spec = tmp_path / "figure.json"
    mp.save_spec(plot.spec, spec)
    command = [sys.executable, "-m", "mudplot"]
    bad = subprocess.run(
        [*command, "lint", str(spec), "--visual", "--json"],
        capture_output=True,
        text=True,
    )
    assert bad.returncode == 1
    assert "legend-data" in {i["code"] for i in json.loads(bad.stdout)["issues"]}
    good = subprocess.run(
        [*command, "lint", str(spec), "--layout-policy", "smart", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(good.stdout)["measurements"]["legend_data_collisions"] == 0
    output = tmp_path / "figure.png"
    subprocess.run(
        [*command, "render", str(spec), str(output), "--layout-policy", "smart"],
        capture_output=True,
        check=True,
    )
    assert output.exists()


@pytest.mark.parametrize(
    ("data", "kwargs", "kind"),
    [
        ({"t": ["2025-01-01", "2025-01-02"], "y": [1, 2]}, {"x": "t"}, "trend"),
        ({"y": [1, 1, 2, 3]}, {}, "distribution"),
        ({"g": ["A", "A", "B", "B"], "y": [1, 2, 3, 4]}, {"x": "g"}, "distribution"),
        ({"t": [0, 1, 1], "y": [0, 1, 0]}, {"x": "t", "event": True}, "event"),
        (
            {"g": ["A", "B", "A", "B"], "id": [1, 1, 2, 2], "y": [1, 2, 3, 4]},
            {"x": "g", "paired": "id"},
            "paired",
        ),
    ],
)
def test_chart_recommendations_follow_declared_roles(data, kwargs, kind):
    original = json.dumps(data)
    result = mp.recommend(data, y="y", **kwargs)
    assert result["recommendations"][0]["kind"] == kind
    assert not result["statistical_inference"]
    supported = mp.capabilities()["layers"]
    assert all(
        layer in supported
        for advice in result["recommendations"]
        for layer in advice["layers"]
    )
    assert json.dumps(data) == original
    json.dumps(result, allow_nan=False)


def test_numeric_order_does_not_imply_time_and_unordered_time_is_not_connected():
    data = {"t": [0, 2, 1], "y": [1, 2, 3]}
    numeric = mp.recommend(data, x="t", y="y")
    assert numeric["recommendations"][0]["kind"] == "relationship"
    timed = mp.recommend(data, x="t", y="y", time=True)
    assert "trend" not in {r["kind"] for r in timed["recommendations"]}
    assert "unordered-time" in {w["code"] for w in timed["warnings"]}


def test_invalid_pairing_does_not_claim_a_paired_design():
    result = mp.recommend(
        {"g": ["A", "B"], "id": [1, 2], "y": [1, 2]}, x="g", y="y", paired="id"
    )
    assert "paired" not in {r["kind"] for r in result["recommendations"]}
    assert "incomplete-pairs" in {w["code"] for w in result["warnings"]}


def test_sparsity_tail_values_and_small_scales_are_explicit_not_imputed():
    result = mp.recommend({"y": [None, float("nan"), 0, 1e-12, 1e-12, 9e-10]}, y="y")
    assert result["profiles"]["y"]["missing"] == 2
    assert result["profiles"]["y"]["nonfinite"] == 0
    assert {"missing-values", "tail-values", "small-scale"} <= {
        w["code"] for w in result["warnings"]
    }
    json.dumps(result, allow_nan=False)


def test_dependency_free_core_includes_recommendations():
    script = """
import sys
class Block:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"numpy", "matplotlib"}:
            raise ModuleNotFoundError(fullname)
sys.meta_path.insert(0, Block())
import mudplot
assert mudplot.recommend({"y": [1, 2]}, y="y")["recommendations"]
assert "numpy" not in sys.modules and "matplotlib" not in sys.modules
"""
    subprocess.run([sys.executable, "-c", script], check=True, capture_output=True)


def test_transparent_rectangles_are_not_visible_data():
    plot = _bars()
    figure = plot.render()
    for patch in figure.axes[0].patches:
        patch.set_facecolor("none")
        patch.set_edgecolor("none")
        patch.set_hatch("")
    assert assess(figure, plot.spec).measurements["legend_data_collisions"] == 0


def test_direct_labels_never_reassign_other_artists_legend_entries():
    plot = _small(
        mp.plot({"x1": [0], "x2": [1], "y1": [0.97], "y2": [0.99]})
        .bar("x1", "y1")
        .bar("x2", "y2")
        .scatter("x1", "y1", label="Observed")
        .line("x2", "y2", label="Reference")
        .ylim(0, 1)
        .legend(location="upper right")
    )
    figure = plot.render(layout_policy="smart")
    assert not figure.axes[0].texts
    legends = [ax.get_legend() for ax in figure.axes if ax.get_legend()]
    assert {
        text.get_text()
        for legend in [*legends, *figure.legends]
        for text in legend.get_texts()
    } == {"Observed", "Reference"}


def test_error_bars_are_retained_and_use_safe_outside_legends():
    plot = _small(
        mp.plot({"method": ["A", "B"], "y": [0.97, 0.99], "error": [0.01, 0.02]})
        .bar("method", "y", group="method", yerr="error")
        .ylim(0, 1.02)
        .legend(location="upper right")
    )
    figure = plot.render(layout_policy="smart")
    bars = [c for c in figure.axes[0].containers if isinstance(c, BarContainer)]
    assert len(bars) == 2 and all(c.errorbar is not None for c in bars)
    assert not figure.axes[0].texts
    assert assess(figure, plot.spec).measurements["legend_data_collisions"] == 0


def test_hatch_noise_and_internal_column_labels_have_actionable_warnings():
    plot = _bars().encoding(hatches=["///", "xxx"])
    plot.labels(x="condition", y="score", title="Figure 1")
    report = plot.lint(visual=True)
    assert {"hatch-noise", "generic-title"} <= _codes(report)
    assert next(issue for issue in report if issue.code == "hatch-noise").suggestion


def test_recommendation_handles_extreme_values_and_group_time_order():
    extreme = mp.recommend({"y": [-1e308, 1e308, 10**1000]}, y="y")
    json.dumps(extreme, allow_nan=False)
    assert extreme["profiles"]["y"]["nonfinite"] == 1
    grouped = mp.recommend(
        {"t": [1, 2, 0, 1], "y": [1, 2, 3, 4], "g": ["A", "A", "B", "B"]},
        x="t",
        y="y",
        group="g",
        time=True,
    )
    assert grouped["recommendations"][0]["kind"] == "trend"


def test_visual_lint_closes_its_figure_and_does_not_leak_style():
    import matplotlib

    before = plt.get_fignums()
    font_size = matplotlib.rcParams["font.size"]
    _bars().lint(visual=True, layout_policy="smart")
    assert plt.get_fignums() == before
    assert matplotlib.rcParams["font.size"] == font_size


def test_before_after_examples_verify_the_actual_publication_pixels(tmp_path):
    subprocess.run(
        [sys.executable, "-m", "examples.scientific_quality", str(tmp_path)],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        check=True,
    )
    report = json.loads((tmp_path / "report.json").read_text())
    assert report["synthetic"] and len(report["cases"]) == 4
    assert len(list(tmp_path.glob("*.png"))) == 8
    expected = {
        "legend_collision": {"legend-data", "hatch-noise"},
        "shared_legend": {"duplicate-legend"},
        "temporal_scatter": {"overcrowded-data"},
        "metric_semantics": {"axis-description", "generic-title", "small-scale"},
    }
    for name, codes in expected.items():
        assert codes <= {i["code"] for i in report["cases"][name]["before"]["issues"]}
    for case in report["cases"].values():
        assert not case["data_changed"]
        metrics = case["after"]["measurements"]
        assert metrics["pixels"] in ([1050, 780], [2100, 780])
        assert metrics["min_font_pt"] >= 8
        assert metrics["legend_data_collisions"] == 0
        assert metrics["text_overlaps"] == 0
        assert metrics["clipped_elements"] == 0


def test_single_numeric_event_train_reuses_existing_eventplot():
    report = mp.recommend(
        {"t": [1, 2, 3], "lane": [0, 0, 0]}, x="t", y="lane", event=True
    )
    assert len(report["recommendations"]) == 1
    assert report["recommendations"][0]["layers"] == ["eventplot"]
    assert report["recommendations"][0]["offset"] == 0
    assert "all-zero" not in {w["code"] for w in report["warnings"]}


def test_repeated_time_requires_a_replicate_or_event_decision():
    report = mp.recommend({"t": [0, 0, 1], "y": [1, 2, 3]}, x="t", y="y", time=True)
    assert "trend" not in {r["kind"] for r in report["recommendations"]}
    assert "repeated-time" in {w["code"] for w in report["warnings"]}


@pytest.mark.parametrize(
    "kwargs",
    [
        {"x": "missing"},
        {"time": 1},
        {"group": []},
        {"x": "x", "event": True, "paired": "id"},
    ],
)
def test_recommendation_role_boundaries_are_explicit(kwargs):
    with pytest.raises(ValueError):
        mp.recommend({"x": [0, 1], "y": [1, 2], "id": [1, 1]}, y="y", **kwargs)


@pytest.mark.parametrize(
    "metadata", [{"citation": "method_paper"}, {"href": "https://example.org/method"}]
)
def test_smart_legends_preserve_scientific_reference_metadata(metadata):
    plot = _two_methods()
    references = {method: mp.Reference(**metadata) for method in ("A", "B")}
    layer = replace(plot.spec.panels[0].layers[0], references=references)
    panel = replace(plot.spec.panels[0], layers=[layer])
    plot = mp.Plot.from_json(mp.to_json(replace(plot.spec, panels=[panel])))
    original = plot.to_json()
    figure = mp.render(plot.spec, fmt="svg", layout_policy="smart")
    assert not figure.axes[0].texts
    legends = list(figure.legends)
    for ax in figure.axes:
        legend = ax.get_legend()
        if legend is not None:
            legends.append(legend)
    assert sum(len(legend.get_texts()) for legend in legends) == 2
    if "href" in metadata:
        assert all(
            text.get_url() == metadata["href"]
            for legend in legends
            for text in legend.get_texts()
        )
    assert plot.to_json() == original
    assert assess(figure, plot.spec).measurements["legend_data_collisions"] == 0


@pytest.mark.parametrize(("colour", "alpha"), [("black", 0.1), ("#7d7d7d", 1)])
def test_direct_labels_use_composited_fill_contrast(colour, alpha):
    plot = _small(
        mp.plot({"method": ["A", "B"], "score": [0.97, 0.99]})
        .bar("method", "score", group="method", color=colour, alpha=alpha)
        .labels(x="Method", y="Score")
        .ylim(0, 1)
    )
    original = plot.to_json()
    figure = plot.render(layout_policy="smart")
    labels = figure.axes[0].texts
    assert len(labels) == 2
    assert all(label.get_color() == "black" for label in labels)
    assert plot.to_json() == original


def _collision_axes():
    figure, ax = plt.subplots()
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.plot([], [], label="data")
    legend = ax.legend(loc="upper left")
    figure.canvas.draw()
    renderer = cast(Any, figure.canvas).get_renderer()
    box = legend.get_window_extent(renderer)
    x, y = ax.transData.inverted().transform(
        [(box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2]
    )
    return figure, ax, renderer, x, y


@pytest.mark.parametrize(
    "kind",
    ["poly", "circle", "line-collection", "scatter", "scatter-alpha", "image", "line"],
)
@pytest.mark.parametrize("alpha", [0.0, 1.0])
def test_collision_checks_ignore_fully_transparent_artists(kind, alpha):
    figure, ax, renderer, x, y = _collision_axes()
    rgba = (1, 0, 0, alpha)
    if kind == "poly":
        ax.add_collection(
            PolyCollection(
                [[(0, 0), (1, 0), (1, 1), (0, 1)]], facecolors=[rgba], edgecolors="none"
            )
        )
    elif kind == "circle":
        ax.add_patch(Circle((x, y), 0.02, facecolor=rgba, edgecolor="none"))
    elif kind == "line-collection":
        ax.add_collection(
            LineCollection([[(0, y), (1, y)]], colors=[rgba], linewidths=5)
        )
    elif kind == "scatter":
        ax.scatter([x], [y], color=[rgba])
    elif kind == "scatter-alpha":
        ax.scatter([x, x], [y, y], color="red", alpha=cast(Any, [alpha, alpha]))
    elif kind == "image":
        ax.imshow([[rgba]], extent=(0, 1, 0, 1), aspect="auto")
    else:
        ax.plot([0, 1], [y, y], color=rgba)
    figure.canvas.draw()
    assert len(_collisions(figure, renderer)) == int(alpha > 0)


def test_collision_checks_ignore_invisible_members_of_visible_collection():
    figure, ax, renderer, x, y = _collision_axes()
    ax.scatter([x, 0.8], [y, 0.2], alpha=cast(Any, [0, 1]))
    ax.add_collection(
        LineCollection(
            [[(0, y), (1, y)], [(0, 0.2), (1, 0.2)]],
            colors=[(1, 0, 0, 0), (1, 0, 0, 1)],
        )
    )
    figure.canvas.draw()
    assert not _collisions(figure, renderer)


@pytest.mark.parametrize("fillstyle", ["full", "left"])
def test_collision_checks_retain_visible_alternate_marker_faces(fillstyle):
    figure, ax, renderer, x, y = _collision_axes()
    ax.plot(
        [x],
        [y],
        marker="o",
        linestyle="none",
        color=(1, 0, 0, 0),
        markerfacecolor=(1, 0, 0, 0),
        markeredgecolor=(1, 0, 0, 0),
        markerfacecoloralt="blue",
        fillstyle=fillstyle,
    )
    figure.canvas.draw()
    assert len(_collisions(figure, renderer)) == int(fillstyle == "left")


@pytest.mark.parametrize(
    ("color", "alpha", "visible"),
    [((0, 0, 0, 0), None, False), ((0, 0, 0, 0), 1, True), ("red", 0, False)],
)
def test_drawn_texts_respects_effective_color_alpha(color, alpha, visible):
    figure, ax = plt.subplots()
    text = ax.text(0.5, 0.5, "annotation", color=color, alpha=alpha)
    figure.canvas.draw()
    assert (text in drawn_texts(figure)) == visible


def test_collision_checks_ignore_fully_masked_images():
    figure, ax = plt.subplots()
    ax.imshow(np.ma.masked_all((2, 2)), extent=(0, 1, 0, 1))
    ax.plot([], [], label="data")
    ax.legend(loc="upper left")
    figure.canvas.draw()
    assert not _collisions(figure, cast(Any, figure.canvas).get_renderer())


@pytest.mark.parametrize("alpha", [0, 1])
def test_collision_checks_keep_hatch_only_patch_interiors(alpha):
    figure, ax, renderer, _, _ = _collision_axes()
    ax.add_patch(
        Rectangle(
            (0, 0), 1, 1, facecolor="none", edgecolor="black", hatch="///", alpha=alpha
        )
    )
    figure.canvas.draw()
    assert len(_collisions(figure, renderer)) == alpha


def test_collision_checks_combine_image_and_pixel_opacity():
    figure, ax, renderer, _, _ = _collision_axes()
    ax.imshow(
        [[[1.0, 0, 0, 0], [1.0, 0, 0, 1]]],
        alpha=np.array([[1.0, 0]]),
        extent=(0, 1, 0, 1),
        aspect="auto",
        interpolation="nearest",
    )
    figure.canvas.draw()
    assert not _collisions(figure, renderer)


@pytest.mark.parametrize(
    "label", ["", "   ", "metric", "Y2", "secondary_internal", "Secondary response (A)"]
)
def test_visual_lint_checks_secondary_axis_descriptions(label):
    plot = (
        mp.plot({"t": [0, 1], "primary": [1, 2], "secondary_internal": [3, 4]})
        .line("t", "primary")
        .secondary_yaxis(label)
        .line("t", "secondary_internal", axis="y2")
        .labels(x="Elapsed time (s)", y="Primary response (V)")
    )
    original = plot.to_json()
    report = plot.lint(visual=True)
    descriptions = [i for i in report if i.code == "axis-description"]
    assert bool(descriptions) == (label != "Secondary response (A)")
    assert all(i.message.startswith("y2-axis") for i in descriptions)
    assert all("secondary_yaxis" in i.suggestion for i in descriptions)
    assert plot.to_json() == original
    json.dumps(report.to_dict(), allow_nan=False)


def test_visual_lint_does_not_mistake_band_endpoint_for_secondary_metric():
    plot = (
        mp.plot(
            {"t": [0, 1], "lo": [1, 2], "upper_endpoint": [2, 3], "secondary": [4, 5]}
        )
        .band("t", "lo", "upper_endpoint")
        .secondary_yaxis("upper_endpoint")
        .line("t", "secondary", axis="y2")
        .labels(x="Elapsed time (s)", y="Primary response (V)")
    )
    assert not any(i.code == "axis-description" for i in plot.lint(visual=True))


def test_visual_lint_respects_journal_and_explicit_font_thresholds():
    plot = mp.plot({"x": [0, 1], "y": [1, 2]}).line("x", "y").journal("nature")
    assert not any(issue.code == "small-text" for issue in plot.lint(visual=True))
    assert any(
        issue.code == "small-text" for issue in plot.lint(visual=True, min_font_pt=7)
    )
