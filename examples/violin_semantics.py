"""Run: python examples/violin_semantics.py [output_directory].

Explicit inner, two-hue split, count/area references and fitted support choices;
legacy violin defaults remain unchanged. All observations/counts are retained.
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
    for group, shift, counts in (("A", 0, (8, 20, 40)), ("B", 0.13, (5, 15, 24))):
        for dose, count in zip((10, 30, 100), counts, strict=True):
            values = 10 ** rng.normal(0.3 + np.log10(dose) / 4 + shift, 0.12, count)
            data["dose"].extend([dose] * count)
            data["response"].extend(values.tolist())
            data["group"].extend([group] * count)
    options = {
        "group": "group",
        "order": [10, 30, 100],
        "hue_order": ["A", "B"],
        "edge_color": "#4b5563",
        "line_width": 0.7,
        "bw_adjust": 0.9,
    }
    p = mp.plot(data).theme("publication").layout(2, 2).size(11, 7)
    p.violin(
        "dose",
        "response",
        **options,
        inner="box",
        density_norm="count",
        common_norm=True,
        gap=0.12,
        panel=0,
    )
    p.labels(x="Dose", y="Response", title="IQR inner / global count widths", panel=0)
    p.violin(
        "dose",
        "response",
        **options,
        inner="quart",
        split=True,
        density_norm="area",
        cut=1,
        gap=0.05,
        panel=1,
    )
    p.labels(
        x="Dose", y="Response", title="Split quartiles / per-hue density scale", panel=1
    )
    p.violin(
        "dose",
        "response",
        **options,
        inner="point",
        orient="h",
        marker_size=2,
        gap=0.12,
        panel=2,
    )
    p.labels(
        x="Response",
        y="Dose",
        title="Horizontal points / peak-normalized width",
        panel=2,
    )
    p.violin(
        "dose",
        "response",
        **options,
        inner="stick",
        split=True,
        native_scale=True,
        stat_scale="axis",
        cut=2,
        clip=(0.5, 40),
        panel=3,
    )
    p.xscale("log", panel=3).yscale("log", panel=3)
    p.labels(
        x="Dose (log)",
        y="Response (log)",
        title="Split sticks / log-fit / raw clip",
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
        plt.close(p.save(str(destination / f"violin_semantics.{fmt}")))
    mp.save_spec(p.spec, destination / "violin_semantics.mplot.json")
    print("OK: inner/split/density/bandwidth/support violin comparison")


if __name__ == "__main__":
    main()
