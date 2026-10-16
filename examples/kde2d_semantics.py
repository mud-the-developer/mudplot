"""Weighted joint Gaussian density and conditional finite-grid HDR contours.

Run: python examples/kde2d_semantics.py [output-directory]
Levels are grid-conditional enclosed mass, NOT confidence/full-space guarantees.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np


def build_plot() -> mp.Plot:
    rng = np.random.default_rng(47)
    a = rng.multivariate_normal([1.6, 2.0], [[0.25, 0.2], [0.2, 0.4]], size=90)
    b = rng.multivariate_normal([3.7, 3.5], [[0.4, -0.25], [-0.25, 0.35]], size=110)
    cloud = np.r_[a, b]
    raw = {
        "x": cloud[:, 0],
        "y": cloud[:, 1],
        "weight": rng.integers(1, 5, len(cloud)),
        "group": ["Control"] * len(a) + ["Treatment"] * len(b),
    }
    p = mp.plot(raw).theme("publication").layout(2, 2).size(14, 7.5)
    options = {
        "weights": "weight",
        "gridsize": 61,
        "levels": [0.5, 0.8, 0.95],
        "cut": 4,
    }
    p.kde2d(
        "x",
        "y",
        **options,
        group="group",
        hue_order=["Control", "Treatment"],
        common_grid=True,
        line_width=1.5,
        panel=0,
    )
    p.labels(
        x="Observed x",
        y="Observed y",
        title="Weighted joint contours / 50,80,95% grid HDR",
        panel=0,
    )
    p.legend(location="outside right", title="Group", panel=0)
    p.kde2d(
        "x",
        "y",
        **options,
        fill=True,
        alpha=0.7,
        line_width=0.8,
        label="Pooled observations",
        panel=1,
    )
    p.labels(
        x="Observed x",
        y="Observed y",
        title="Pooled density / conditional mass bands",
        panel=1,
    )
    p.kde2d(
        "x",
        "y",
        **options,
        fill=True,
        alpha=0.7,
        line_width=0.8,
        clip=((1.4, 3.8), (1.4, 3.6)),
        label="Same fit / clipped grid",
        panel=2,
    )
    p.labels(
        x="Observed x",
        y="Observed y",
        title="Clip changes HDR targets, NOT fitted covariance",
        panel=2,
    )
    p.kde2d(
        "x",
        "y",
        **options,
        group="group",
        hue_order=["Control", "Treatment"],
        common_grid=True,
        clip=((0.1, None), (0.1, None)),
        line_width=1.5,
        panel=3,
    )
    p.xscale("log", panel=3).yscale("log", panel=3)
    # Display the informative positive range without crowded unused log decades.
    p.xlim(0.3, 8, panel=3).ylim(0.25, 7, panel=3)
    p.labels(
        x="Observed x (log display)",
        y="Observed y (log display)",
        title="Raw-unit Gaussian / log display, no Jacobian",
        panel=3,
    )
    p.legend(location="outside right", title="Group", panel=3)
    return p


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="docs/images")
    destination = Path(parser.parse_args().directory)
    destination.mkdir(parents=True, exist_ok=True)
    p = build_plot()
    mp.assert_valid(p.spec)
    assert (
        mp.Plot.from_json(p.to_json()).spec == p.spec
        and mp.apply(p.action_log) == p.spec
    )
    for fmt in ("png", "svg"):
        plt.close(p.save(str(destination / f"kde2d_semantics.{fmt}")))
    mp.save_spec(p.spec, destination / "kde2d_semantics.mplot.json")
    print("OK: weighted/correlated/pooled/clipped/raw-log conditional KDE2D HDR")


if __name__ == "__main__":
    main()
