"""Run: python examples/native_categorical_scales.py [output_directory].

Numeric categories retain measured locations. Log-space statistics are explicit,
not an implicit change to existing raw-data summaries. Swarm values stay exact.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np


def build_plot() -> mp.Plot:
    rng = np.random.default_rng(95)
    data = {"dose": [], "value": [], "group": []}
    for group, shift in (("A", 0), ("B", 0.18)):
        for dose in (10, 30, 100):
            values = 10 ** rng.normal(np.log10(dose) / 3 + shift, 0.13, 24)
            data["dose"].extend([dose] * len(values))
            data["value"].extend(values.tolist())
            data["group"].extend([group] * len(values))
    options = {
        "group": "group",
        "native_scale": True,
        "hue_order": ["B", "A"],
        "gap": 0.1,
        "order": [10, 30, 100],
    }
    p = mp.plot(data).theme("publication").layout(1, 3).size(12, 3.5)
    p.box("dose", "value", **options, stat_scale="data", panel=0)
    p.labels(
        x="Measured dose", y="Response", title="Native linear / raw statistics", panel=0
    )
    p.boxenplot("dose", "value", **options, stat_scale="axis", k_depth=3, panel=1)
    p.xscale("log", panel=1).yscale("log", panel=1)
    p.labels(
        x="Dose (log)",
        y="Response (log)",
        title="Log-native / axis statistics",
        panel=1,
    )
    p.swarmplot("dose", "value", **options, marker_size=2, panel=2)
    p.xscale("log", panel=2).yscale("log", panel=2)
    p.labels(
        x="Dose (log)",
        y="Response (log)",
        title="Log-native / raw observations",
        panel=2,
    )
    for panel in range(3):
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
        plt.close(p.save(str(destination / f"native_categorical_scales.{fmt}")))
    mp.save_spec(p.spec, destination / "native_categorical_scales.mplot.json")
    print(
        "OK: native numeric/log geometry, explicit statistic coordinates and raw swarm"
    )


if __name__ == "__main__":
    main()
