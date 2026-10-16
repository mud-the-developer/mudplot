"""Check delivered web sizes and data fidelity, not aesthetic preference."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from examples.publication_showcase import (
    KINDS,
    METHODS,
    REPLICATES,
    WIDTHS,
    build_plot,
    render_examples,
    save_and_assess,
)
from mudplot._estimate import summarize

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("width", WIDTHS)
def test_visual_redesign_preserves_prototype_observations_and_statistics(kind, width):
    prototype = mp.load_spec(ROOT / "docs/images/visual_after.mplot.json")
    plot = build_plot(kind, width_px=width)
    assert len(plot.spec.panels) == 1
    assert not plot.spec.panels[0].legend.show
    assert plot.spec.theme.redundant_encoding
    columns = plot.spec.data.columns
    old = prototype.data.columns
    for name in ("time", "response"):
        np.testing.assert_allclose(columns[name], old[name], rtol=1e-12, atol=1e-14)
    assert columns["method"] == old["method"]
    assert [v is None for v in columns["endpoint"]] == [
        v is None for v in old["endpoint"]
    ]
    np.testing.assert_allclose(
        [v for v in columns["endpoint"] if v is not None],
        [v for v in old["endpoint"] if v is not None],
        rtol=1e-12,
        atol=1e-14,
    )
    for method in METHODS:
        assert (
            sum(
                group == method and value is not None
                for group, value in zip(
                    columns["method"], columns["endpoint"], strict=True
                )
            )
            == REPLICATES
        )
    before = prototype.panels[0 if kind == "response" else 1].layers[0]
    after = plot.spec.panels[0].layers[0]
    assert before.stat == after.stat
    expected, actual = summarize(old, before), summarize(columns, after)
    assert expected.categories == actual.categories and expected.groups == actual.groups
    for left, right in zip(expected.estimates, actual.estimates, strict=True):
        assert left.category == right.category and left.group == right.group
        assert left.n == right.n == REPLICATES
        assert left.lower is not None and left.upper is not None
        assert right.lower is not None and right.upper is not None
        np.testing.assert_allclose(
            [left.value, left.lower, left.upper],
            [right.value, right.lower, right.upper],
            rtol=1e-12,
            atol=1e-14,
        )
    if kind == "response":
        assert plot.spec.panels[0].x.limits == prototype.panels[0].x.limits
        assert plot.spec.panels[0].y.limits == prototype.panels[0].y.limits
        assert [layer.text for layer in plot.spec.panels[0].layers[1:]] == METHODS
    else:
        assert after.orient == "h"
        assert plot.spec.panels[0].x.limits == prototype.panels[1].y.limits


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("width", WIDTHS)
def test_visual_actual_png_fonts_bounds_labels_json_and_actions(tmp_path, kind, width):
    plot = build_plot(kind, width_px=width)
    assert mp.validate(plot.spec) == []
    assert (
        mp.Plot.from_json(plot.to_json()).spec == mp.apply(plot.action_log) == plot.spec
    )
    report = save_and_assess(plot, tmp_path / "chart.png", display_width_px=width)
    assert report["source_pixels"] == [width * 2, 800 if kind == "response" else 600]
    assert report["display_pixels"] == [width, 400 if kind == "response" else 300]
    assert report["min_display_font_px"] >= 14
    assert report["font_floor_14px_ok"] and report["content_bounds_ok"]
    assert report["text_overlap_ok"] and not report["overlapping_text"]
    assert not any("legend" in issue["message"] for issue in report["lint"])
    assert not plt.get_fignums()


def _use_native_figure(monkeypatch, figure):
    def save(self, path):
        figure.savefig(path, dpi=self.spec.dpi)
        return figure

    monkeypatch.setattr(mp.Plot, "save", save)
    return mp.plot().size(2, 2).dispatch(mp.actions.SetDpi(100))


@pytest.mark.parametrize(
    "x,size,inside,font_ok",
    [(0.5, 12, True, True), (-0.5, 12, False, True), (0.5, 4, True, False)],
)
def test_visual_qa_detects_clipping_and_small_delivered_text(
    tmp_path, monkeypatch, x, size, inside, font_ok
):
    figure = plt.figure(figsize=(2, 2), dpi=100)
    figure.text(x, 0.5, "QA", fontsize=size)
    plot = _use_native_figure(monkeypatch, figure)
    report = save_and_assess(plot, tmp_path / "qa.png", display_width_px=200)
    assert report["content_bounds_ok"] is inside
    assert report["font_floor_14px_ok"] is font_ok
    assert not plt.fignum_exists(figure.number)


def test_visual_qa_detects_internal_text_overlap(tmp_path, monkeypatch):
    figure = plt.figure(figsize=(2, 2), dpi=100)
    for text in ("first", "second"):
        figure.text(0.3, 0.5, text, fontsize=12)
    plot = _use_native_figure(monkeypatch, figure)
    report = save_and_assess(plot, tmp_path / "qa.png", display_width_px=200)
    assert report["content_bounds_ok"]
    assert not report["text_overlap_ok"]
    assert report["overlapping_text"] == [["first", "second"]]


def test_visual_qa_ignores_ticks_not_drawn_in_the_saved_view(tmp_path, monkeypatch):
    figure = plt.figure(figsize=(2, 2), dpi=100)
    axes = figure.add_subplot()
    figure.subplots_adjust(left=0.3, right=0.9, bottom=0.3, top=0.9)
    axes.set_xticks([-1, 0, 0.5, 1, 2])
    axes.set_xlim(0, 1)
    plot = _use_native_figure(monkeypatch, figure)
    report = save_and_assess(plot, tmp_path / "qa.png", display_width_px=200)
    assert report["content_bounds_ok"]


def test_visual_qa_does_not_pass_an_empty_png(tmp_path, monkeypatch):
    figure = plt.figure(figsize=(2, 2), dpi=100)
    plot = _use_native_figure(monkeypatch, figure)
    report = save_and_assess(plot, tmp_path / "qa.png", display_width_px=200)
    assert not report["font_floor_14px_ok"]
    assert not report["content_bounds_ok"]


def test_visual_downscaled_desktop_is_not_mistaken_for_the_mobile_layout(tmp_path):
    report = save_and_assess(
        build_plot("response", width_px=700),
        tmp_path / "small.png",
        display_width_px=320,
    )
    assert not report["font_floor_14px_ok"]


@pytest.mark.parametrize(
    "kind,width", [("other", 700), ("response", 0), ("response", 701)]
)
def test_visual_builder_rejects_unreviewed_layouts(kind, width):
    with pytest.raises(ValueError, match="700px or 320px"):
        build_plot(kind, width_px=width)


@pytest.mark.parametrize("filename,width", [("qa.svg", 200), ("qa.png", 0)])
def test_visual_qa_rejects_invalid_export_arguments(tmp_path, filename, width):
    path = tmp_path / filename
    with pytest.raises(ValueError, match="PNG and a positive"):
        save_and_assess(mp.plot(), path, display_width_px=width)
    assert not path.exists()


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("extension", ["png", "pdf", "svg"])
def test_visual_exports_repeat_without_consuming_global_rng(tmp_path, kind, extension):
    state = np.random.get_state()
    plot = build_plot(kind)
    paths = [tmp_path / f"{name}.{extension}" for name in ("a", "b")]
    plt.close(plot.save(str(paths[0])))
    plt.close(mp.Plot.from_json(plot.to_json()).save(str(paths[1])))
    assert paths[0].read_bytes() == paths[1].read_bytes()
    after = np.random.get_state()
    assert state[0] == after[0] and state[2:] == after[2:]
    np.testing.assert_array_equal(state[1], after[1])


def test_visual_render_failure_keeps_previous_spec_and_unrelated_files(
    tmp_path, monkeypatch
):
    contents = {
        "visual_response.mplot.json": b"previous spec",
        "notes.txt": b"keep notes",
    }
    for name, data in contents.items():
        (tmp_path / name).write_bytes(data)

    def fail_save(*args, **kwargs):
        raise ValueError("simulated render failure")

    monkeypatch.setattr(mp.Plot, "save", fail_save)
    with pytest.raises(ValueError, match="simulated render"):
        render_examples(tmp_path)
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == contents
    assert not plt.get_fignums()


def test_visual_reports_and_previews_come_from_real_saved_charts(tmp_path):
    report = render_examples(tmp_path)
    assert (
        json.loads((tmp_path / "visual_quality.json").read_text(encoding="utf-8"))
        == report
    )
    assert report["independent_human_review"] == report["model_judge"] == "not_run"
    assert len(report["charts"]) == 4
    for name, qa in report["charts"].items():
        assert mp.validate(mp.load_spec(tmp_path / f"{name}.mplot.json")) == []
        assert (
            qa["font_floor_14px_ok"]
            and qa["content_bounds_ok"]
            and qa["text_overlap_ok"]
        )
        assert (tmp_path / f"{name}.png").stat().st_size > 1000
    rgb = plt.imread(tmp_path / "visual_response.png")
    gray = plt.imread(tmp_path / "visual_response_gray.png")
    assert rgb.shape == gray.shape
    np.testing.assert_array_equal(gray[..., 0], gray[..., 1])
    np.testing.assert_array_equal(gray[..., 1], gray[..., 2])
    for vision in ("protan", "deutan"):
        simulated = plt.imread(tmp_path / f"visual_response_{vision}.png")
        assert simulated.shape == rgb.shape and not np.array_equal(simulated, rgb)
