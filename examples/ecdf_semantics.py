"""Unweighted/weighted empirical steps, percent, strict tails and count mass.

Run: python examples/ecdf_semantics.py [output-directory]
Default output: docs/images (PNG, SVG and editable .mplot.json).
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
    rng = np.random.default_rng(28)
    data = {
        "value": np.round(
            np.r_[rng.lognormal(0, 0.45, 60), rng.lognormal(0.4, 0.5, 80)], 1
        ),
        "weight": rng.integers(0, 5, 140),
        "group": ["Control"] * 60 + ["Treatment"] * 80,
    }
    options = {
        "group": "group",
        "hue_order": ["Control", "Treatment"],
        "line_width": 1.8,
    }
    p = mp.plot(data).theme("publication").layout(2, 2).size(11, 7)
    p.ecdf("value", **options, panel=0)
    p.labels(
        x="Observed value",
        y="P(X <= value)",
        title="Empirical CDF / no smoothing",
        panel=0,
    )
    p.ecdf("value", **options, weights="weight", stat="percent", panel=1)
    p.labels(
        x="Observed value",
        y="Within-curve percent",
        title="Weighted cumulative percent",
        panel=1,
    )
    p.ecdf(
        "value", **options, weights="weight", complementary=True, orient="h", panel=2
    )
    p.yscale("log", panel=2)
    p.labels(
        x="P(X > value)",
        y="Observed value (log)",
        title="Strict tail / horizontal log",
        panel=2,
    )
    p.ecdf("value", **options, weights="weight", stat="count", panel=3)
    p.labels(
        x="Observed value",
        y="Cumulative weight mass",
        title="Weighted count / not row count",
        panel=3,
    )
    for panel in range(4):
        p.legend(title="Group", location="outside right", panel=panel)
    return p


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="docs/images")
    destination = Path(parser.parse_args().directory)
    destination.mkdir(parents=True, exist_ok=True)
    p = build_plot()
    mp.assert_valid(p.spec)
    assert mp.Plot.from_json(p.to_json()).spec == p.spec
    assert mp.apply(p.action_log) == p.spec
    for fmt in ("png", "svg"):
        plt.close(p.save(str(destination / f"ecdf_semantics.{fmt}")))
    mp.save_spec(p.spec, destination / "ecdf_semantics.mplot.json")
    print("OK: ECDF empirical/weighted/percent/strict-tail/count comparison")


if __name__ == "__main__":
    main()
