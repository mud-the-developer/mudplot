"""PLOT-11: data anchors use their own axes; title and legend keep their spaces."""

import json
import math
from html.parser import HTMLParser

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from dashboard.editor_server import EditorSession
from dashboard.editor_view import _preview_handles_html


class Handles(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.items = {}
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "button" and "drag-handle" in (values.get("class") or ""):
            self.items[values["data-handle-id"]] = values


def document(size=(6, 3), dpi=300, panels=2):
    index = panels - 1
    p = (
        mp.plot({"x": [1, 10, 100], "y": [1, 2, 3], "right": [10, 100, 1000]})
        .layout(1, panels)
        .size(*size)
    )
    p.line("x", "y", label="primary", panel=index)
    p.secondary_yaxis("right units", scale="log", limits=[10, 1000], panel=index).line(
        "x", "right", axis="y2", label="right", panel=index
    )
    p.text("primary text", at=[10, 1], panel=index)
    p.text("secondary text", at=[10, 100], axis="y2", panel=index)
    p.annotate("secondary arrow", at=[20, 200], to=[10, 100], axis="y2", panel=index)
    spec = p.spec
    spec.dpi = dpi
    panel = spec.panels[index]
    panel.x.scale = "log"
    panel.x.limits = [100, 1]
    panel.y.limits = [0, 4]
    panel.title = "selected"
    panel.title_position = [0.25, 0.9]
    panel.legend.bbox_to_anchor = [0.8, 0.7]
    return spec, index


@pytest.mark.parametrize(
    "size,dpi,panels", [((4, 3), 96, 1), ((6, 3), 300, 2), ((5, 4), 150, 2)]
)
def test_layout_handle_frames_match_selected_primary_secondary_axes_and_figure(
    size, dpi, panels
):
    spec, active = document(size, dpi, panels)
    session = EditorSession()
    session.load_spec(mp.to_json(spec))
    session.select_panel(active)
    assert session.error is None
    before = mp.to_json(session.store.state)
    layout = session.layout
    handles = Handles(_preview_handles_html(session.store.state, layout, active)).items
    x0, y0, x1, y1 = layout["panel_bbox"]
    for index, fx, fy in (
        (2, 0.5, 0.25),
        (3, 0.5, 0.5),
        (4, (2 - math.log10(20)) / 2, (math.log10(200) - 1) / 2),
    ):
        handle = handles[f"layer-at:{index}:{active}"]
        assert float(handle["data-imgx"]) == pytest.approx(
            x0 + fx * (x1 - x0), abs=1e-5
        )
        assert float(handle["data-imgy"]) == pytest.approx(
            y0 + fy * (y1 - y0), abs=1e-5
        )
        assert handle["data-xscale"] == "log"
        assert json.loads(handle["data-xlim"]) == [100, 1]
        assert handle["data-yscale"] == ("linear" if index == 2 else "log")
        assert json.loads(handle["data-ylim"]) == ([0, 4] if index == 2 else [10, 1000])
    title = handles[f"title::{active}"]
    assert float(title["data-imgx"]) == pytest.approx(x0 + 0.25 * (x1 - x0), abs=1e-5)
    assert float(title["data-imgy"]) == pytest.approx(y0 + 0.9 * (y1 - y0), abs=1e-5)
    legend = handles[f"legend::{active}"]
    assert float(legend["data-imgx"]) == 0.8 and float(legend["data-imgy"]) == 0.7
    assert legend["data-space"] == "figure" and title["data-space"] == "axes"
    assert mp.to_json(session.store.state) == before
    assert mp.from_json(mp.to_json(spec)) == spec


def test_renderer_artist_positions_match_data_axes_and_figure_transforms():
    spec, active = document()
    fig = mp.render(spec)
    try:
        ax = next(a for a in fig.axes if getattr(a, "_mudplot_panel", None) == active)
        secondary = getattr(ax, "_mudplot_secondary_axis", None)
        assert secondary is not None
        primary_text = next(t for t in ax.texts if t.get_text() == "primary text")
        secondary_text = next(
            t for t in secondary.texts if t.get_text() == "secondary text"
        )
        np.testing.assert_allclose(
            primary_text.get_transform().transform(primary_text.get_position()),
            ax.transData.transform([10, 1]),
        )
        np.testing.assert_allclose(
            secondary_text.get_transform().transform(secondary_text.get_position()),
            secondary.transData.transform([10, 100]),
        )
        title = next(t for t in ax.texts if t.get_text() == "selected")
        np.testing.assert_allclose(
            title.get_transform().transform(title.get_position()),
            ax.transAxes.transform([0.25, 0.9]),
        )
        legend = ax.get_legend()
        assert legend is not None
        np.testing.assert_allclose(
            legend.get_bbox_to_anchor().bounds[:2],
            fig.transFigure.transform([0.8, 0.7]),
        )
    finally:
        plt.close(fig)


def test_unsupported_noncartesian_text_is_rejected_before_handle_layout():
    p = (
        mp.plot({"theta": [0.0, 1.0], "radius": [1.0, 2.0]})
        .projection_polar()
        .line("theta", "radius")
        .text("polar", at=[0.5, 1.5])
    )
    spec = p.spec
    spec.panels[0].title = "polar title"
    spec.panels[0].title_position = [0.25, 0.9]
    spec.panels[0].legend.bbox_to_anchor = [0.8, 0.7]
    session = EditorSession()
    before, preview, layout = session.store.state, session.png, session.layout
    with pytest.raises(ValueError, match="not supported on a polar"):
        session.load_spec(mp.to_json(spec))
    assert (
        session.store.state == before
        and session.png == preview
        and session.layout == layout
    )
