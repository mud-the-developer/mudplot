"""Weighted paired fields, kernel composition, true CDF and full-model HDR."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp


def build_plot() -> mp.Plot:
    data = {
        "x": [-2.0, -1.0, 0.0, 0.5, 1.0, 2.0, 3.0, 1.5],
        "y": [-1.0, 1.0, -0.5, 1.5, 0.25, 2.0, -0.5, -1.0],
        "w": [1, 2, 4, 1, 3, 2, 1, 2],
        "site": ["left"] * 4 + ["right"] * 4,
        "row_id": [f"observation-{index}" for index in range(8)],
    }
    plot = mp.plot(data).layout(2, 3).size(15, 9)
    plot.hist2d(
        "x",
        "y",
        panel=0,
        bins=mp.BivariateBinsSpec(x=[-3, 0, 1, 4], y=[-2, 0, 3]),
        stat="density",
        weights="w",
        colorbar=True,
        kde=mp.KDE2DSpec(weights="w", levels=[0.5, 0.8], gridsize=32),
    ).labels(title="In-bin density + full-cohort KDE", panel=0)
    plot.kde(
        "x",
        panel=1,
        group="site",
        weights="w",
        kernel="epanechnikov_product",
        multiple="stack",
        common_grid=True,
        fill=True,
        line_width=1,
    ).labels(title="Compact-kernel density contributions", panel=1)
    plot.kde2d(
        "x",
        "y",
        panel=2,
        weights="w",
        cumulative=True,
        level_kind="cdf",
        levels=[0.2, 0.5, 0.8],
        gridsize=32,
        colorbar=True,
    ).labels(title="True original-law joint CDF", panel=2)
    plot.kde2d(
        "x",
        "y",
        panel=3,
        weights="w",
        levels=[0.8, 0.95],
        gridsize=17,
        hdr=mp.HDRSpec(scope="full", tolerance=0.01),
        fill=True,
        line_width=0,
        line_style="--",
        colorbar=True,
    ).labels(title="Full-model HDR: guaranteed-inside cells", panel=3)
    plot.ecdf2d(
        "x",
        "y",
        panel=4,
        weights="w",
        stat="percent",
        complementary=True,
        bounds=[[-3, 4], [-2, 3]],
        query_x=[0, 1],
        query_y=[0, 1],
        colorbar=True,
    ).labels(title="Empirical strict OR complement (%)", panel=4)
    plot.kde(
        "x",
        panel=5,
        group="site",
        weights="w",
        kernel="epanechnikov_product",
        multiple="fill",
        common_grid=True,
        cumulative=True,
        fill=True,
    ).labels(title="CDF-contribution composition, not a CDF", panel=5)
    for panel in (0, 2, 3, 4):
        plot.labels(x="Original x observation", y="Original y observation", panel=panel)
    plot.labels(x="Original observation", panel=1)
    plot.labels(x="Original observation", panel=5)
    assert plot.spec.data.columns == data
    return plot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", default="docs/images/density_fields")
    options = parser.parse_args()
    directory = Path(options.directory)
    directory.mkdir(parents=True, exist_ok=True)
    plot = build_plot()
    mp.assert_valid(plot.spec)
    before = plot.to_json()
    reopened = mp.Plot.from_json(before)
    assert reopened.spec == mp.apply(plot.action_log) == plot.spec
    # Fit/calibrate once. Each actual backend draw still certifies its own final
    # native geometry/clip; this is not a cached image or copied probability field.
    figure = reopened.render()
    try:
        for extension in ("png", "svg", "pdf"):
            figure.savefig(directory / f"density_fields.{extension}")
    finally:
        plt.close(figure)
    mp.save_spec(plot.spec, directory / "density_fields.mplot.json")
    assert plot.to_json() == before
    print(
        "PASS paired statistics / named kernels / true joint CDF / full HDR / strict OR"
    )


if __name__ == "__main__":
    main()
