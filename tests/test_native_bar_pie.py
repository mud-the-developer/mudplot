import math

import matplotlib.pyplot as plt
import mudplot as mp
import pytest
from matplotlib.colors import to_rgba
from matplotlib.patches import Wedge


def test_horizontal_signed_stack_alignment_uses_original_row_heights():
    data = {
        "lane": [True, 1, True, 1, True, 1],
        "delta": [2, -3, 4, -2, -1, 5],
        "group": ["A", "A", "B", "B", "C", "C"],
        "baseline": [10, 20, 10, 20, 10, 20],
    }
    style = mp.ComponentStyleSpec(color="#a44a3f", hatch="/", line_width=1.4)
    p = (
        mp.plot(data)
        .size(8, 5)
        .xlim(8, 28)
        .barh(
            "lane",
            "delta",
            group="group",
            bar_width=0.5,
            geometry=mp.BarGeometrySpec(
                bottom="baseline",
                align="edge",
                multiple="stack",
                styles=[None, None, style, None, None, None],
                value_format=".1f",
            ),
        )
    )
    figure = p.render()
    try:
        ax = figure.axes[0]
        patches = [m for c in ax.containers for m in c.patches]
        assert [
            (r.get_x(), r.get_y(), r.get_width(), r.get_height()) for r in patches
        ] == [
            (10, 0, 2, 0.5),
            (20, 1, -3, 0.5),
            (12, 0, 4, 0.5),
            (17, 1, -2, 0.5),
            (10, 0, -1, 0.5),
            (20, 1, 5, 0.5),
        ]
        assert list(ax.get_yticks()) == [0.25, 1.25]
        assert [t.get_text() for t in ax.get_yticklabels()] == ["True", "1"]
        assert [item.get_text() for item in ax.texts] == [
            "2.0",
            "-3.0",
            "4.0",
            "-2.0",
            "-1.0",
            "5.0",
        ]
        assert (
            patches[2].get_facecolor() == to_rgba("#a44a3f")
            and patches[2].get_hatch() == "/"
        )
        assert p.spec.data.columns == data and mp.apply(p.action_log) == p.spec
    finally:
        plt.close(figure)
    before = p.to_json()
    history = p.action_log
    from mudplot.actions import SetData

    with pytest.raises(ValueError, match="same explicit bottom"):
        p.dispatch(SetData({**data, "baseline": [10, 20, 11, 20, 10, 20]}))
    assert p.to_json() == before and p.action_log == history


def test_vertical_bar_native_edge_alignment_and_nonstatistical_labels():
    data = {
        "pos": [1, 4],
        "height": [3, 2],
        "baseline": [2, 5],
        "labels": ["initial", "repeat"],
    }
    p = mp.plot(data).bar(
        "pos",
        "height",
        bar_width=0.75,
        geometry={"align": "edge", "bottom": "baseline", "labels": "labels"},
    )
    fig = p.render()
    try:
        ax = fig.axes[0]
        assert [
            (v.get_x(), v.get_y(), v.get_width(), v.get_height()) for v in ax.patches
        ] == [(1, 2, 0.75, 3), (4, 5, 0.75, 2)]
        assert [t.get_text() for t in ax.texts] == ["initial", "repeat"]
        assert [t.xy for t in ax.texts] == [(1.375, 5), (4.375, 7)]
    finally:
        plt.close(fig)


def test_pie_uses_native_wedges_and_original_raw_annotations():
    raw = {"names": ["A", "B", "C"], "v": [2, 3, 5]}
    style = mp.ComponentStyleSpec(color="#5494ad", edge_color="white", line_width=2.0)
    p = (
        mp.plot(raw)
        .size(7, 6)
        .pie(
            "names",
            "v",
            geometry=mp.PieGeometrySpec(
                start_angle=90,
                counterclock=False,
                radius=1.2,
                center=[0.1, -0.2],
                width=0.42,
                explode=[0, 0.08, 0],
                styles=[style, None, None],
                text_size=11,
                value="raw",
                value_format=".0f",
                label_distance=1.1,
                value_distance=0.8,
                annotations=[None, "native edge", None],
            ),
        )
    )
    fig = p.render()
    try:
        ax = fig.axes[0]
        wedges = [item for item in ax.patches if isinstance(item, Wedge)]
        assert len(wedges) == 3 and math.isclose(wedges[0].theta2, 90)
        assert [w.theta2 - w.theta1 for w in wedges] == pytest.approx(
            [72, 108, 180], rel=2e-6
        )
        assert all(w.width == 0.42 and w.r == 1.2 for w in wedges)
        assert wedges[0].center == (0.1, -0.2) and wedges[1].center != wedges[0].center
        assert wedges[0].get_edgecolor() == to_rgba("white")
        texts = {item.get_text(): item for item in ax.texts}
        assert set(texts) == {"A", "B", "C", "2", "3", "5", "native edge"}
        # Native insertion order differs across providers; require visible
        # positions and row-to-wedge ownership instead.
        for wedge, label, value in zip(
            wedges, ("A", "B", "C"), ("2", "3", "5"), strict=True
        ):
            for key, distance in ((label, 1.1), (value, 0.8)):
                point = texts[key].get_position()
                assert math.dist(point, wedge.center) == pytest.approx(
                    distance * wedge.r
                )
        edge = texts["native edge"]
        assert edge.anncoords == "offset points" and edge.arrow_patch is not None
        assert math.dist(edge.xy, wedges[1].center) == pytest.approx(wedges[1].r)
        assert (
            mp.Plot.from_json(p.to_json()).spec == p.spec and p.spec.data.columns == raw
        )
    finally:
        plt.close(fig)


def test_partial_pie_uses_absolute_fraction_and_checks_original_total():
    raw = {"label": ["Small", "Large"], "fraction": [0.25, 0.5]}
    plot = (
        mp.plot(raw)
        .size(6, 5)
        .pie(
            "label",
            "fraction",
            geometry=mp.PieGeometrySpec(normalize=False, value="percent", labels=False),
        )
    )
    figure = plot.render()
    try:
        axes = figure.axes[0]
        assert [w.theta2 - w.theta1 for w in axes.patches] == [90, 180]
        assert [text.get_text() for text in axes.texts if text.get_text()] == [
            "25.0%",
            "50.0%",
        ]
    finally:
        plt.close(figure)
    before = plot.to_json()
    from mudplot.actions import SetData

    with pytest.raises(ValueError, match="total <= 1"):
        plot.dispatch(SetData({**raw, "fraction": [0.75, 0.75]}))
    assert plot.to_json() == before
