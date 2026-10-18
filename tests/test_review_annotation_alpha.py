"""Annotation alpha applies to both text and optional arrows, including y2."""

import xml.etree.ElementTree as ET

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.text import Annotation


def base(secondary=False):
    p = (
        mp.plot(
            {"x": [0.0, 1.0, 2.0], "y": [0.0, 1.0, 2.0], "right": [10.0, 20.0, 30.0]}
        )
        .line("x", "y", color="#112233")
        .size(4, 3)
    )
    if secondary:
        p.secondary_yaxis("right units").line("x", "right", axis="y2", color="#556677")
    return p


@pytest.mark.parametrize("alpha", [0.0, 0.35])
@pytest.mark.parametrize("arrow", [False, True])
@pytest.mark.parametrize("secondary", [False, True])
def test_explicit_annotation_alpha_reaches_text_and_arrow_on_own_axis(
    alpha, arrow, secondary
):
    p = base(secondary).annotate(
        "alpha",
        at=[0.5, 22.0 if secondary else 1.5],
        to=[1.5, 15.0 if secondary else 0.5] if arrow else None,
        axis="y2" if secondary else "y",
        alpha=alpha,
        color="#ff0000",
    )
    before = p.to_json()
    fig = p.render()
    try:
        ax = fig.axes[-1] if secondary else fig.axes[0]
        text = next(t for t in ax.texts if isinstance(t, Annotation))
        assert text.axes is ax and text.get_alpha() == alpha
        if arrow:
            assert (
                text.arrow_patch is not None and text.arrow_patch.get_alpha() == alpha
            )
            assert text.arrow_patch.get_edgecolor()[-1] == alpha
        else:
            assert text.arrow_patch is None
        assert p.to_json() == before
    finally:
        plt.close(fig)


@pytest.mark.parametrize("secondary", [False, True])
def test_alpha_zero_adds_no_pixels_to_matching_base_figure(secondary):
    p = base(secondary)
    fig = p.render()
    try:
        assert isinstance(fig.canvas, FigureCanvasAgg)
        expected = np.asarray(fig.canvas.buffer_rgba()).copy()
    finally:
        plt.close(fig)
    p.annotate(
        "invisible",
        at=[0.5, 22.0 if secondary else 1.5],
        to=[1.5, 15.0 if secondary else 0.5],
        axis="y2" if secondary else "y",
        alpha=0,
        color="#ff0000",
    )
    fig = p.render()
    try:
        assert isinstance(fig.canvas, FigureCanvasAgg)
        np.testing.assert_array_equal(np.asarray(fig.canvas.buffer_rgba()), expected)
    finally:
        plt.close(fig)


def test_default_annotation_stays_opaque_and_svg_has_both_explicit_opacities(tmp_path):
    p = base().annotate("default", at=[1.0, 1.0], to=[1.5, 0.5], color="#ff0000")
    fig = p.render()
    try:
        text = next(t for t in fig.axes[0].texts if isinstance(t, Annotation))
        assert text.get_alpha() in (None, 1.0)
        assert text.arrow_patch is not None and text.arrow_patch.get_alpha() in (
            None,
            1.0,
        )
    finally:
        plt.close(fig)
    p = base().annotate(
        "alpha", at=[1.0, 1.0], to=[1.5, 0.5], alpha=0.35, color="#ff0000"
    )
    target = tmp_path / "alpha.svg"
    plt.close(p.save(str(target)))
    root = ET.parse(target).getroot()
    assert (
        sum(
            "opacity:0.35" in node.get("style", "").replace(" ", "")
            for node in root.iter()
        )
        >= 2
    )


def test_default_annotation_preserves_legacy_rgba_colour_opacity():
    p = base().annotate("rgba", at=[1.0, 1.0], to=[1.5, 0.5], color="#ff000080")
    fig = p.render()
    try:
        text = next(t for t in fig.axes[0].texts if isinstance(t, Annotation))
        assert text.get_alpha() is None
        assert text.arrow_patch is not None and text.arrow_patch.get_alpha() is None
        assert text.arrow_patch.get_edgecolor()[-1] == pytest.approx(128 / 255)
    finally:
        plt.close(fig)
