"""LAY-05: mixed guide geometry and safe explicit-series legend identity."""

import re
import struct
import warnings
from xml.etree import ElementTree as ET

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import pytest


def mixed(size=(6, 3), secondary=True):
    p = (
        mp.plot(
            {
                "x": [1, 2, 3, 4],
                "y": [2, 4, 3, 5],
                "right": [20, 40, 30, 50],
                "c": [0.1, 0.5, 0.8, 1],
            }
        )
        .layout(1, 2)
        .size(*size)
        .share(x="all", y="all")
    )
    for panel in (0, 1):
        p.scatter(
            "x",
            "y",
            c="c",
            colorbar=True,
            clabel=f"Scale {panel + 1}",
            label="measured",
            panel=panel,
        )
        p.line("x", "y", label="measured", panel=panel)
        if secondary:
            p.secondary_yaxis(f"Right {panel + 1}", panel=panel).line(
                "x", "right", axis="y2", label="right scale", panel=panel
            )
        p.legend(location="outside right", panel=panel)
    return p


def legend(ax):
    result = ax.get_legend()
    assert result is not None
    return result


def intersection(a, b):
    return max(0, min(a.x1, b.x1) - max(a.x0, b.x0)) * max(
        0, min(a.y1, b.y1) - max(a.y0, b.y0)
    )


@pytest.mark.parametrize("size", [(6, 3), (8, 3.5)])
@pytest.mark.parametrize("secondary", [False, True])
def test_two_panels_bars_shared_axes_and_outside_legends_do_not_cover_guides(
    size, secondary
):
    p = mixed(size, secondary)
    before = p.to_json()
    fig = p.render()
    try:
        mains = fig.axes[:2]
        assert mains[0].get_shared_x_axes().joined(*mains)
        assert mains[0].get_shared_y_axes().joined(*mains)
        legends = [legend(ax) for ax in mains]
        assert [[t.get_text() for t in leg.get_texts()] for leg in legends] == (
            [["measured", "right scale"]] * 2 if secondary else [["measured"]] * 2
        )
        legend_boxes = [leg.get_window_extent() for leg in legends]
        for box in legend_boxes:
            assert box.x0 >= fig.bbox.x0 - 1 and box.x1 <= fig.bbox.x1 + 1
            assert all(
                intersection(box, ax.get_window_extent()) <= 1 for ax in fig.axes
            )
            assert all(
                intersection(box, ax.yaxis.label.get_window_extent()) <= 1
                for ax in fig.axes
                if ax.get_ylabel()
            )
        assert p.to_json() == before and fig.get_size_inches() == pytest.approx(size)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("kind", ["line", "line3d"])
def test_duplicate_explicit_series_guides_keep_one_but_distinct_source_values_do_not(
    kind,
):
    p = mp.plot({"x": [1, 2, 3], "y": [2, 3, 4], "z": [3, 4, 5]}).size(5, 3)
    if kind.endswith("3d"):
        p.projection3d()
    for _ in range(2):
        getattr(p, kind)(
            "x", "y", *(["z"] if kind.endswith("3d") else []), label="same"
        )
    fig = p.render()
    try:
        assert [t.get_text() for t in legend(fig.axes[0]).get_texts()] == ["same"]
    finally:
        plt.close(fig)
    p = (
        mp.plot({"x": [1, 2], "y": [2, 3], "other": [5, 6]})
        .line("x", "y", label="same")
        .line("x", "other", label="same")
    )
    fig = p.render()
    try:
        assert [t.get_text() for t in legend(fig.axes[0]).get_texts()] == [
            "same",
            "same",
        ]
    finally:
        plt.close(fig)


def test_raw_group_equal_visible_labels_are_not_collapsed():
    p = mp.plot({"x": [1, 2, 3, 4], "y": [2, 3, 4, 5], "g": [1, 1, "1", "1"]}).line(
        "x", "y", group="g"
    )
    fig = p.render()
    try:
        assert [t.get_text() for t in legend(fig.axes[0]).get_texts()] == [
            "1",
            "1",
        ]
    finally:
        plt.close(fig)


@pytest.mark.parametrize("case", ["references", "axes", "markers"])
def test_same_label_keeps_distinct_reference_axis_or_marker_sources(case):
    p = mp.plot({"x": [1, 2], "y": [2, 3]}).size(5, 3)
    if case == "references":
        p.line("x", "y", label="same", citation="first")
        p.line("x", "y", label="same", citation="second")
    elif case == "axes":
        p.secondary_yaxis("other")
        p.line("x", "y", label="same").line("x", "y", axis="y2", label="same")
    else:
        p.hline(1, label="same").hline(2, label="same")
    fig = p.render()
    try:
        assert [t.get_text() for t in legend(fig.axes[0]).get_texts()] == [
            "same",
            "same",
        ]
    finally:
        plt.close(fig)


@pytest.mark.parametrize("extension", ["png", "pdf", "svg"])
def test_saved_mixed_guides_keep_canvas_and_secondary_label_gap(
    extension, tmp_path, monkeypatch
):
    from mudplot import _render

    p = mixed()
    before = p.to_json()
    path = tmp_path / f"guides.{extension}"
    original = _render._save_figure
    overlaps = []

    def capture(fig, *args, **kwargs):
        def measured(event):
            for ax in fig.axes[:2]:
                box = legend(ax).get_window_extent(event.renderer)
                overlaps.extend(
                    intersection(
                        box, other.yaxis.label.get_window_extent(event.renderer)
                    )
                    for other in fig.axes
                    if other.get_ylabel()
                )

        connection = fig.canvas.mpl_connect("draw_event", measured)
        try:
            return original(fig, *args, **kwargs)
        finally:
            fig.canvas.mpl_disconnect(connection)

    monkeypatch.setattr(_render, "_save_figure", capture)
    fig = p.save(str(path))
    try:
        assert overlaps and max(overlaps) <= 1
        raw = path.read_bytes()
        if extension == "png":
            assert struct.unpack(">II", raw[16:24]) == (
                int(6 * p.spec.dpi),
                int(3 * p.spec.dpi),
            )
        elif extension == "pdf":
            box = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([0-9.]+)\s+([0-9.]+)", raw)
            assert box is not None and [float(box[1]), float(box[2])] == pytest.approx(
                [432, 216]
            )
        else:
            root = ET.fromstring(raw)
            assert [
                float(root.attrib[k].removesuffix("pt")) for k in ("width", "height")
            ] == pytest.approx([432, 216])
        assert p.to_json() == before
    finally:
        plt.close(fig)


def test_too_small_mixed_guides_report_fixed_canvas_limit_not_successful_fit():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig = mixed((4.5, 2.8)).render()
    try:
        assert fig.get_size_inches() == pytest.approx([4.5, 2.8])
        assert any(
            "fixed canvas" in str(w.message) or "constrained_layout" in str(w.message)
            for w in caught
        )
    finally:
        plt.close(fig)
