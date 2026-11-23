"""Post-height composition and raw-bin-center polygons; no new measurements."""

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
    source = {
        "value": np.r_[rng.lognormal(0, 0.5, 70), rng.lognormal(0.4, 0.4, 110)],
        "weight": rng.integers(1, 5, 180),
        "group": ["Control"] * 70 + ["Treatment"] * 110,
    }
    options = {
        "bins": [0.2, 0.6, 1, 1.6, 2.6, 4.5],
        "weights": "weight",
        "group": "group",
        "hue_order": ["Control", "Treatment"],
        "line_width": 1.2,
    }
    plot = mp.plot(source).theme("publication").layout(2, 2).size(11, 7)
    plot.hist("value", **options, multiple="fill", panel=0)
    plot.labels(
        x="Observed value",
        y="Within-bin share (dimensionless)",
        title="Composition / weighted count heights",
        panel=0,
    )
    plot.hist(
        "value",
        **options,
        stat="probability",
        common_norm=False,
        multiple="fill",
        element="step",
        panel=1,
    )
    plot.labels(
        x="Observed value",
        y="Within-bin share (dimensionless)",
        title="Composition / per-curve probability heights",
        panel=1,
    )
    plot.hist(
        "value", **options, stat="density", common_norm=False, element="poly", panel=2
    )
    plot.labels(
        x="Observed value (raw-bin centers)",
        y="Density per raw unit",
        title="Bin-center lines / no fitted curve",
        panel=2,
    )
    plot.hist(
        "value",
        **options,
        stat="density",
        cumulative=True,
        multiple="fill",
        element="poly",
        fill=True,
        alpha=0.7,
        panel=3,
    )
    plot.labels(
        x="Observed value",
        y="Cumulative composition (not CDF)",
        title="Composition of cumulative heights",
        panel=3,
    )
    for panel in range(4):
        plot.legend(location="outside right", title="Group", panel=panel)
    return plot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="docs/images")
    directory = Path(parser.parse_args().directory)
    directory.mkdir(parents=True, exist_ok=True)
    plot = build_plot()
    mp.assert_valid(plot.spec)
    before = plot.to_json()
    assert mp.Plot.from_json(before).spec == mp.apply(plot.action_log) == plot.spec
    for extension in ("png", "svg", "pdf"):
        plt.close(plot.save(str(directory / f"histogram_modes.{extension}")))
    mp.save_spec(plot.spec, directory / "histogram_modes.mplot.json")
    assert plot.to_json() == before
    print("PASS post-height composition and raw-center polygons; source unchanged")


if __name__ == "__main__":
    main()
