"""LAY-04/06: fixed canvas bounds and explicit impossible-layout diagnostics."""

import os
import struct
import subprocess
import sys
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import pytest


def plot(size=(6, 3)):
    return (
        mp.plot({"x": [1, 2, 3], "y": [2, 3, 4]})
        .layout(1, 2)
        .size(*size)
        .line("x", "y", panel=0)
        .line("x", "y", panel=1)
    )


@pytest.mark.parametrize("where", ["title", "suptitle", "legend"])
def test_unbroken_automatic_text_warns_without_resizing_or_losing_source(where):
    spec = plot().spec
    text = "verylongpublicationtoken" * 7
    if where == "title":
        for panel in spec.panels:
            panel.title = text
    elif where == "suptitle":
        spec.suptitle = text
    else:
        for panel in spec.panels:
            panel.layers[0].label = text
            panel.legend.location = "outside right"
    before = mp.to_json(spec)
    with pytest.warns(UserWarning, match="fixed canvas"):
        fig = mp.render(spec)
    try:
        assert fig.get_size_inches() == pytest.approx([6, 3])
        assert mp.to_json(spec) == before
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "text",
    [
        "Long publication title that can use several well separated words",
        "First line\nSecond line\nThird line",
    ],
)
def test_fitting_automatic_titles_stay_inside_and_separate(text):
    p = plot((3.4, 2.2)).labels(title=text, panel=0).labels(title=text, panel=1)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig = p.render()
    try:
        boxes = [
            ax.title.get_window_extent().transformed(fig.transFigure.inverted())
            for ax in fig.axes
        ]
        assert all(
            bb.x0 >= -0.001 and bb.y0 >= -0.001 and bb.x1 <= 1.001 and bb.y1 <= 1.001
            for bb in boxes
        )
        assert boxes[0].x1 <= boxes[1].x0
        assert not any("fixed canvas" in str(w.message) for w in caught)
    finally:
        plt.close(fig)


def test_tiny_impossible_automatic_text_keeps_warning_and_dimensions():
    p = (
        plot((1, 0.7))
        .labels(title="First line\nSecond line\nThird line", panel=0)
        .labels(title="First line\nSecond line\nThird line", panel=1)
    )
    with pytest.warns(UserWarning, match="fixed canvas"):
        fig = p.render()
    try:
        assert fig.get_size_inches() == pytest.approx([1, 0.7])
    finally:
        plt.close(fig)


def test_cli_reports_automatic_overflow_without_changing_file_canvas(tmp_path):
    spec = plot().spec
    spec.panels[0].title = "verylongpublicationtoken" * 7
    source, output = tmp_path / "input.json", tmp_path / "figure.png"
    mp.save_spec(spec, source)
    result = subprocess.run(
        [sys.executable, "-m", "mudplot", "render", str(source), str(output)],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "MPLBACKEND": "Agg"},
    )
    assert result.returncode == 0 and "fixed canvas" in result.stderr
    assert "Traceback" not in result.stderr
    assert struct.unpack(">II", output.read_bytes()[16:24]) == (
        int(6 * spec.dpi),
        int(3 * spec.dpi),
    )
    assert mp.load_spec(source) == spec


def test_warning_as_error_keeps_previous_output_and_closes_owned_figure(tmp_path):
    spec = plot().spec
    spec.panels[0].title = "verylongpublicationtoken" * 7
    path = tmp_path / "previous.png"
    path.write_bytes(b"previous complete output")
    figures = set(plt.get_fignums())
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        with pytest.raises(UserWarning, match="fixed canvas"):
            mp.save(spec, str(path))
    assert path.read_bytes() == b"previous complete output"
    assert set(plt.get_fignums()) == figures
    assert not list(tmp_path.glob("*.tmp"))


def test_explicit_dragged_text_positions_remain_caller_owned():
    p = (
        mp.plot({"x": [1, 2], "y": [2, 3]})
        .line("x", "y", label="series")
        .size(4, 3)
        .labels(title="manual title")
        .title_position([1.5, 0.8])
        .legend(bbox_to_anchor=[1.4, 0.8])
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig = p.render()
    try:
        assert not any("fixed canvas" in str(w.message) for w in caught)
        assert fig.get_size_inches() == pytest.approx([4, 3])
    finally:
        plt.close(fig)
