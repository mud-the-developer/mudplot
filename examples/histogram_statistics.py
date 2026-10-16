"""Weighted shared-bin bars and unfilled steps, grouped geometry and binned CDF.

Run: python examples/histogram_statistics.py [output-directory]
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
    rng = np.random.default_rng(16)
    data = {
        "value": np.r_[rng.lognormal(0, 0.5, 70), rng.lognormal(0.4, 0.4, 110)],
        "weight": rng.integers(1, 5, 180),
        "group": ["Control"] * 70 + ["Treatment"] * 110,
    }
    options = {
        "bins": [0.2, 0.6, 1, 1.6, 2.6, 4.5],
        "weights": "weight",
        "group": "group",
        "hue_order": ["Control", "Treatment"],
        "alpha": 0.6,
        "edge_color": "#475569",
        "line_width": 0.5,
    }
    p = mp.plot(data).theme("publication").layout(2, 2).size(11, 7)
    p.hist(
        "value", **options, stat="density", common_norm=True, multiple="stack", panel=0
    )
    p.labels(
        x="Observed value",
        y="Density per raw unit",
        title="Stacked density / shared total",
        panel=0,
    )
    step_options = {**options, "edge_color": None, "line_width": 1.2, "alpha": 1.0}
    p.hist(
        "value",
        **step_options,
        stat="density",
        common_norm=False,
        element="step",
        panel=1,
    )
    p.labels(
        x="Observed value",
        y="Density per raw unit",
        title="Step density / per-curve total",
        panel=1,
    )
    p.hist("value", **options, stat="percent", orient="h", multiple="dodge", panel=2)
    p.yscale("log", panel=2)
    p.labels(
        x="Percent of included weight",
        y="Observed value (log)",
        title="Dodged percent / horizontal raw bins",
        panel=2,
    )
    p.hist(
        "value",
        **step_options,
        stat="density",
        cumulative=True,
        multiple="stack",
        element="step",
        panel=3,
    )
    p.labels(
        x="Observed value",
        y="Binned cumulative proportion",
        title="Stacked step CDF / shared total",
        panel=3,
    )
    for panel in range(4):
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
        plt.close(p.save(str(destination / f"histogram_statistics.{fmt}")))
    mp.save_spec(p.spec, destination / "histogram_statistics.mplot.json")
    print("OK: weighted histogram bars/steps, stack/dodge and cumulative comparison")


if __name__ == "__main__":
    main()
