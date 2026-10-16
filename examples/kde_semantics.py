"""Weighted Gaussian KDE: bandwidth, pooled/separate mass and analytic CDF.

Run: python examples/kde_semantics.py [output-directory]
Default output: docs/images (PNG/SVG/editable JSON).
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
    rng = np.random.default_rng(21)
    data = {
        "value": np.r_[rng.normal(1.5, 0.4, 70), rng.normal(3, 0.7, 110)],
        "weight": rng.integers(1, 5, 180),
        "group": ["Control"] * 70 + ["Treatment"] * 110,
    }
    options = {
        "weights": "weight",
        "group": "group",
        "hue_order": ["Control", "Treatment"],
        "gridsize": 201,
        "common_grid": True,
        "cut": 4,
    }
    p = mp.plot(data).theme("publication").layout(2, 2).size(11, 7)
    p.kde(
        "value",
        **options,
        fill=True,
        alpha=0.4,
        line_width=1,
        common_norm=True,
        panel=0,
    )
    p.labels(
        x="Observed value",
        y="Density per raw unit",
        title="Weighted KDE / shared total",
        panel=0,
    )
    p.kde(
        "value",
        **options,
        fill=True,
        alpha=0.4,
        line_width=1,
        common_norm=False,
        panel=1,
    )
    p.labels(
        x="Observed value",
        y="Density per raw unit",
        title="Weighted KDE / per-curve total (tails unscaled)",
        panel=1,
    )
    pooled = {
        key: value
        for key, value in options.items()
        if key not in ("group", "hue_order")
    }
    p.kde(
        "value",
        **pooled,
        common_norm=False,
        bw_adjust=0.5,
        line_style="-",
        color="#475569",
        label="adjust=0.5",
        panel=2,
    )
    p.kde(
        "value",
        **pooled,
        common_norm=False,
        bw_adjust=1.5,
        line_style=":",
        color="#475569",
        label="adjust=1.5",
        panel=2,
    )
    p.labels(
        x="Observed value",
        y="Density per raw unit",
        title="Bandwidth adjustment / solid 0.5 vs dotted 1.5",
        panel=2,
    )
    p.legend(location="upper right", title="Pooled rows", panel=2)
    p.kde("value", **options, cumulative=True, common_norm=True, orient="h", panel=3)
    p.labels(
        x="Cumulative share of selected weight",
        y="Observed value",
        title="Analytic Gaussian CDF / not clipped or ECDF",
        panel=3,
    )
    for panel in (0, 1, 3):
        p.legend(location="outside right", title="Group", panel=panel)
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
        plt.close(p.save(str(destination / f"kde_semantics.{fmt}")))
    mp.save_spec(p.spec, destination / "kde_semantics.mplot.json")
    print("OK: weighted/shared/separate/bandwidth/analytic-CDF KDE comparison")


if __name__ == "__main__":
    main()
