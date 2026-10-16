"""Run: python examples/statistical_scales.py [output_directory].

Explicit native spacing, raw/log-fit estimates and positive raw bar baselines.
No automatic scale inference or changed count normalization denominator.
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
    rng = np.random.default_rng(718)
    data = {"dose": [], "response": [], "group": []}
    for group, shift, counts in (("A", 0, (12, 20, 32)), ("B", 0.15, (8, 16, 24))):
        for dose, count in zip((10, 30, 100), counts, strict=True):
            values = 10 ** rng.normal(0.3 + np.log10(dose) / 4 + shift, 0.18, count)
            data["dose"].extend([dose] * count)
            data["response"].extend(values.tolist())
            data["group"].extend([group] * count)
    options = {
        "group": "group",
        "native_scale": True,
        "order": [10, 30, 100],
        "hue_order": ["A", "B"],
    }
    p = mp.plot(data).theme("publication").layout(2, 2).size(11, 7)
    p.barplot(
        "dose",
        "response",
        **options,
        errorbar="se",
        value_labels=True,
        label_format=".2f",
        gap=0.12,
        edge_color="#4b5563",
        line_width=0.7,
        panel=0,
    )
    p.labels(
        x="Dose (native)",
        y="Response",
        title="Native spacing / raw mean + SEM",
        panel=0,
    )
    p.pointplot(
        "dose", "response", **options, errorbar="pi", dodge=0.3, marker_size=4, panel=1
    )
    p.xscale("log", panel=1).yscale("log", panel=1)
    p.labels(
        x="Dose (native log)",
        y="Response (log axis)",
        title="Raw arithmetic mean / observed PI",
        panel=1,
    )
    p.barplot(
        "dose",
        "response",
        **options,
        orient="h",
        stat_scale="axis",
        baseline=0.5,
        errorbar="ci",
        n_boot=500,
        seed=7,
        value_labels=True,
        label_format=".2f",
        gap=0.12,
        edge_color="#4b5563",
        line_width=0.7,
        panel=2,
    )
    p.xscale("log", panel=2).yscale("log", panel=2)
    p.labels(
        x="Response (log fit; baseline 0.5)",
        y="Dose (native log)",
        title="Horizontal geometric mean / log-fit CI",
        panel=2,
    )
    p.countplot(
        "dose",
        **options,
        stat="percent",
        stack=True,
        value_labels=True,
        label_format=".1f",
        gap=0.12,
        edge_color="#4b5563",
        line_width=0.7,
        panel=3,
    )
    p.xscale("log", panel=3)
    p.labels(
        x="Dose (native log)",
        y="Percent of selected rows (linear)",
        title="Native stacked counts / global denominator",
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
    assert (
        mp.Plot.from_json(p.to_json()).spec == p.spec
        and mp.apply(p.action_log) == p.spec
    )
    for fmt in ("png", "svg"):
        plt.close(p.save(str(destination / f"statistical_scales.{fmt}")))
    mp.save_spec(p.spec, destination / "statistical_scales.mplot.json")
    print("OK: statistical native/log/baseline comparison")


if __name__ == "__main__":
    main()
