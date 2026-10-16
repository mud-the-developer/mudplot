"""Run: python examples/distribution_components.py [output_directory].

Named native artist styles, not changes to raw statistics or observations.
Box/letter-value widths and log/statistic choices retain their earlier contracts.
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
    for group, shift in (("A", 0), ("B", 0.15)):
        for dose in (10, 30, 100):
            values = 10 ** rng.normal(0.3 + np.log10(dose) / 4 + shift, 0.18, 40)
            data["dose"].extend([dose] * len(values))
            data["response"].extend(values.tolist())
            data["group"].extend([group] * len(values))
    options = {
        "group": "group",
        "order": [10, 30, 100],
        "hue_order": ["A", "B"],
        "gap": 0.15,
        "edge_color": "#4b5563",
        "line_width": 0.7,
    }
    p = mp.plot(data).theme("publication").layout(2, 2).size(11, 7)
    p.box("dose", "response", **options, showmeans=True, panel=0)
    p.labels(x="Dose", y="Response", title="Default box / hue and hatch", panel=0)
    p.box(
        "dose",
        "response",
        **options,
        showmeans=True,
        components={
            "body": {"alpha": 1},
            "whisker": {"color": "#64748b", "line_style": "--"},
            "cap": {"color": "#007f87", "line_width": 1.4},
            "median": {"color": "#b54b00", "line_width": 2.2},
            "mean": {
                "marker": "s",
                "marker_size": 3.5,
                "face_color": "white",
                "edge_color": "#202020",
                "marker_edge_width": 0.8,
            },
            "flier": {
                "marker": "d",
                "marker_size": 3,
                "edge_color": "#0072b2",
                "face_color": "none",
                "marker_edge_width": 0.8,
            },
        },
        panel=1,
    )
    p.labels(
        x="Dose",
        y="Response",
        title="Independent box components / same statistics",
        panel=1,
    )
    p.boxenplot(
        "dose",
        "response",
        **options,
        k_depth=3,
        components={
            "body": {"alpha": 0.9},
            "median": {"color": "#202020", "line_width": 1.8},
            "flier": {
                "marker": "o",
                "marker_size": 2.5,
                "edge_color": "#0072b2",
                "face_color": "none",
                "marker_edge_width": 0.6,
            },
        },
        panel=2,
    )
    p.labels(
        x="Dose",
        y="Response",
        title="Letter-value tiers / styled median and tails",
        panel=2,
    )
    p.boxenplot(
        "dose",
        "response",
        **options,
        k_depth=3,
        orient="h",
        native_scale=True,
        stat_scale="axis",
        components={
            "body": {"alpha": 0.85},
            "median": {"color": "#b54b00", "line_width": 2},
            "flier": {
                "marker": "d",
                "marker_size": 2.5,
                "edge_color": "#0072b2",
                "face_color": "none",
            },
        },
        panel=3,
    )
    p.xscale("log", panel=3).yscale("log", panel=3)
    p.labels(
        x="Response (log fit)",
        y="Dose (native log)",
        title="Horizontal log-fit / styled native artists",
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
        plt.close(p.save(str(destination / f"distribution_components.{fmt}")))
    mp.save_spec(p.spec, destination / "distribution_components.mplot.json")
    print("OK: independent box/boxen native component comparison")


if __name__ == "__main__":
    main()
