import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib import patheffects
from matplotlib.patches import Ellipse, PathPatch, Polygon, Rectangle
from matplotlib.path import Path
from matplotlib.table import Table
from mudplot._editor import extract_layout
from mudplot.actions import SetLayerAt


def test_native_paths_effects_and_literal_table_without_ghost_axes():
    vertices = [[1, 2], [2, 4], [3, 2], [4, 3], [5, 4], [6, 2], [1, 2]]
    code = ["MOVETO", "CURVE3", "CURVE3", "CURVE4", "CURVE4", "CURVE4", "CLOSEPOLY"]
    p = (
        mp.plot()
        .size(10, 6)
        .layout(1, 2)
        .patch(
            mp.PatchSpec("path", vertices, codes=code),
            native_style=mp.ComponentStyleSpec(color="teal", edge_color="navy"),
            path_effects=[
                mp.PathEffectSpec("shadow", offset=[2, -2], alpha=0.25),
                mp.PathEffectSpec("stroke", color="white", width=1.5),
            ],
        )
        .patch(
            mp.PatchSpec("rectangle", [[0.11, 0.2], [0.19, 0.27]], coordinates="figure")
        )
        .patch(
            mp.PatchSpec("ellipse", [[0.2, 0.3], [0.4, 0.5]], coordinates="axes"),
            panel=1,
        )
        .patch(
            mp.PatchSpec(
                "polygon", [[0.5, 0.14], [0.7, 0.22], [0.8, 0.13]], coordinates="axes"
            ),
            panel=1,
        )
        .table(
            mp.LiteralTableSpec(
                [["3", "5"], ["7", "9"]],
                [0.12, 0.55, 0.76, 0.33],
                row_labels=["Day 1", "Day 2"],
                column_labels=["A", "B"],
                font_size=10,
                header_color="#e4eef1",
                text_color="navy",
            ),
            panel=1,
        )
    )
    fig = p.render()
    try:
        left, right = fig.axes
        assert len(fig.axes) == 2
        native = left.patches[0]
        assert isinstance(native, PathPatch)
        np.testing.assert_array_equal(native.get_path().vertices, vertices)
        np.testing.assert_array_equal(
            native.get_path().codes,
            [
                Path.MOVETO,
                Path.CURVE3,
                Path.CURVE3,
                Path.CURVE4,
                Path.CURVE4,
                Path.CURVE4,
                Path.CLOSEPOLY,
            ],
        )
        assert [type(x) for x in native.get_path_effects()] == [
            patheffects.SimplePatchShadow,
            patheffects.Stroke,
            patheffects.Normal,
        ]
        rect = next(a for a in fig.artists if isinstance(a, Rectangle))
        np.testing.assert_allclose(
            rect.get_window_extent().get_points(),
            fig.transFigure.transform([[0.11, 0.2], [0.19, 0.27]]),
        )
        assert isinstance(right.patches[0], Ellipse) and isinstance(
            right.patches[1], Polygon
        )
        table = right.tables[0]
        assert isinstance(table, Table)
        cells = table.get_celld()
        assert [
            [cells[i, j].get_text().get_text() for j in range(3)] for i in range(3)
        ] == [["", "A", "B"], ["Day 1", "3", "5"], ["Day 2", "7", "9"]]
        np.testing.assert_allclose(
            table.get_window_extent(fig.canvas.get_renderer()).get_points(),
            right.transAxes.transform([[0.12, 0.55], [0.88, 0.88]]),
            atol=1e-9,
        )
        assert p.spec == mp.Plot.from_json(p.to_json()).spec == mp.apply(p.action_log)
    finally:
        plt.close(fig)
    before, history = p.to_json(), p.action_log
    with pytest.raises(ValueError, match="two/three consecutive"):
        p.patch(
            mp.PatchSpec(
                "path", [[1, 1], [2, 2], [3, 3]], codes=["MOVETO", "CURVE4", "LINETO"]
            )
        )
    assert p.to_json() == before and p.action_log == history


def test_fraction_annotations_only_advertise_supported_drag_owners():
    p = (
        mp.plot({"x": [0, 4], "y": [0, 10]})
        .size(8, 6)
        .line("x", "y")
        .xlim(0, 4)
        .ylim(0, 10)
        .text(
            "Axes caption",
            [0.25, 0.65],
            annotation=mp.AnnotationSpec(at_coordinates="axes"),
        )
        .annotate(
            "Figure callout",
            [0.60, 0.75],
            to=[2, 5],
            annotation=mp.AnnotationSpec(
                at_coordinates="figure", to_coordinates="data", arrow="filled"
            ),
        )
        .annotate(
            "Data anchor",
            [3, 7],
            to=[0.1, 0.8],
            annotation=mp.AnnotationSpec(to_coordinates="axes", arrow="line"),
        )
    )
    p.dispatch(SetLayerAt(3, [2.8, 7.5]))
    fig = p.render()
    try:
        ax = fig.axes[0]
        a, b, c = ax.texts
        assert b.arrow_patch is not None and c.arrow_patch is not None
        for native, expected in (
            (a, ax.transAxes.transform([0.25, 0.65])),
            (b, fig.transFigure.transform([0.60, 0.75])),
            (c, ax.transData.transform([2.8, 7.5])),
        ):
            np.testing.assert_allclose(
                native.get_transform().transform(native.get_position()), expected
            )
        assert b.xy == (2.0, 5.0) and c.xy == (0.1, 0.8)
        info = extract_layout(p.spec, fig, 0)
        assert [entry["coordinates"] for entry in info["text_layers"]] == [
            "axes",
            "figure",
            "data",
        ]
        assert [
            h["layer_index"] for h in info["handles"] if h["kind"] == "layer-at"
        ] == [3]
        assert all(
            "not data drags" in row["drag_disabled_reason"]
            for row in info["text_layers"][:2]
        )
    finally:
        plt.close(fig)
    before = p.to_json()
    with pytest.raises(ValueError, match="fractions"):
        p.dispatch(SetLayerAt(1, [1.1, 0.5]))
    assert p.to_json() == before
