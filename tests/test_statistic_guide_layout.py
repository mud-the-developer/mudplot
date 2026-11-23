"""Public native geometry proposal; no mock guide or statistical effect."""

from xml.etree import ElementTree

import mudplot as mp
import pytest


def test_measured_owner_lane_native_prints(tmp_path):
    from matplotlib import pyplot as plt
    from matplotlib.image import imread

    source = {
        "x": [-2.0, -1.0, 0.0, 0.5, 1.0, 2.0, 3.0, 1.5],
        "y": [-1.0, 1.0, -0.5, 1.5, 0.25, 2.0, -0.5, -1.0],
        "w": [1, 2, 4, 1, 3, 2, 1, 2],
        "cdf_weight": [1, 2, 3, 1, 2, 1, 1, 1],
        "site": ["left"] * 4 + ["right"] * 4,
    }
    plot = (
        mp.plot(source)
        .layout(1, 3)
        .size(15, 4.5)
        .hist2d(
            "x",
            "y",
            bins=mp.BivariateBinsSpec(x=[-3, 0, 1, 4], y=[-2, 0, 3]),
            stat="density",
            weights="w",
            colorbar=True,
            kde=mp.KDE2DSpec(weights="w", levels=[0.5, 0.8], gridsize=32),
        )
        .labels(title="In-bin density + full-cohort KDE")
        .kde(
            "x",
            panel=1,
            group="site",
            weights="w",
            kernel="epanechnikov_product",
            multiple="stack",
            common_grid=True,
            fill=True,
        )
        .ecdf2d(
            "x",
            "y",
            panel=2,
            weights="cdf_weight",
            bounds=[[-4, 0.25], [-3, 0]],
            colorbar=True,
        )
        .labels(title="Outer empirical cumulative field", panel=2)
    )
    before = plot.to_json()
    fig = mp.Plot.from_json(before).render()
    try:
        for ext, magic in {
            "png": b"\x89PNG\r\n\x1a\n",
            "svg": b"<?xml",
            "pdf": b"%PDF-",
        }.items():
            output = tmp_path / f"measured.{ext}"
            fig.savefig(output)
            assert output.read_bytes().startswith(magic)
            if ext == "svg":
                assert ElementTree.parse(output).getroot().tag.endswith("svg")
        renderer = fig.canvas.get_renderer()
        records = {r["owner"]._mudplot_panel: r for r in fig._mudplot_statistic_guides}
        overlay = records[0]["bars"][1]
        outer = records[2]["bars"]
        assert len(outer) == 1
        assert [t.get_text() for t in outer[0].ax.get_yticklabels()] == [
            "0.0",
            "0.16666666666666666",
            "0.3333333333333333",
        ]
        box = overlay.ax.yaxis.label.get_window_extent(renderer)
        represented = fig._mudplot_statistic_guide_check.get_tightbbox(renderer)
        assert (
            represented is not None
            and represented.contains(*box.p0)
            and represented.contains(*box.p1)
        )
        expected = fig.get_tightbbox(renderer)
        tight = tmp_path / "measured-tight.png"
        fig.savefig(tight, bbox_inches="tight", pad_inches=0)
        height, width, *_ = imread(tight).shape
        assert (
            width >= expected.width * fig.dpi - 5
            and height >= expected.height * fig.dpi - 5
        )
    finally:
        plt.close(fig)
    assert plot.to_json() == before and plot.spec.data.columns == source

    output = tmp_path / "measured.png"
    previous = output.read_bytes()
    bad = (
        mp.plot(source)
        .size(3.5, 2.625)
        .ecdf2d(
            "x",
            "y",
            group="site",
            bounds=[[-4, 4], [-4, 4]],
            colorbar=True,
            clabel="indivisible-label-" * 40,
        )
    )
    with pytest.raises(ValueError, match="statistic guide"):
        bad.save(output)
    assert output.read_bytes() == previous
