"""Executable README examples, documented resource limits, and behavior contracts."""

from pathlib import Path

import matplotlib.pyplot as plt
import mudplot as mp
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("file", ["README.md", "README.ko.md"])
def test_readme_builder_example_runs_and_closes_owned_figure(
    tmp_path, monkeypatch, file
):
    text = (ROOT / file).read_text(encoding="utf-8")
    snippet = text.split("```python\n", 1)[1].split("```", 1)[0]
    expected = {
        "voltage": [1, 2, 3],
        "current": [2, 4, 3],
        "order": ["synthetic", "synthetic", "synthetic"],
    }
    figures = plt.get_fignums()
    monkeypatch.chdir(tmp_path)
    namespace = {}
    exec(compile(snippet, "trusted-README-example", "exec"), namespace)
    assert (tmp_path / "fig.pdf").read_bytes().startswith(b"%PDF")
    assert plt.get_fignums() == figures and namespace["data"] == expected


@pytest.mark.parametrize("file", ["docs/INSTALL.md", "docs/INSTALL.ko.md"])
def test_paired_installation_guides_state_resource_limits(file):
    text = (ROOT / file).read_text(encoding="utf-8")
    for token in (
        "max_panels = 256",
        "max_layout_cells = 256",
        "max_layers = 1024",
        "max_bins_per_axis = 512",
        "max_canvas_pixels = 40_000_000",
    ):
        assert token in text


def test_legacy_scatter_appearance_kwargs_still_forward():
    plot = mp.plot({"x": [1, 2], "y": [3, 4], "g": ["a", "b"]})
    plot.scatter("x", "y", alpha=0.4, marker="s", marker_size=7, label="legacy")
    layer = plot.spec.panels[0].layers[0]
    assert (layer.alpha, layer.marker, layer.marker_size, layer.label) == (
        0.4,
        "s",
        7,
        "legacy",
    )
    assert layer.semantics is None
    plot.scatter("x", "y", style="g", alpha=0.5)
    semantic = plot.spec.panels[0].layers[1].semantics
    assert semantic is not None and semantic.style == "g"


@pytest.mark.parametrize("kind", ["box", "violin"])
def test_existing_single_numeric_positional_form_remains_supported(kind):
    plot = mp.plot({"values": [1, 2, 3, 4]})
    getattr(plot, kind)("values")
    layer = plot.spec.panels[0].layers[0]
    assert layer.x == "values" and layer.y == "" and mp.validate(plot.spec) == []


def test_author_review_is_not_release_or_independent_signoff():
    report = (ROOT / "docs/REVIEW_DECISION.md").read_text(encoding="utf-8")
    assert "NOT RELEASE APPROVED" in report and "not an independent" in report
    assert "DOC-04/05/06" in report and "BLOCKED" in report
    assert "No scalar quality score or stability probability" in report
