"""Run: python examples/letter_value_categories.py [output_directory].

Distribution bands are raw-data quantiles, not confidence intervals or KDE.
Compare exponential/linear/area widths and explicit/full tail depth.
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
    rng = np.random.default_rng(61)
    data = {"dose": [], "value": [], "group": []}
    for group, shift in (("A", 0), ("B", 0.4)):
        for dose, effect in (("Low", 0), ("High", 0.9)):
            values = rng.normal(1 + shift + effect, 0.4, 128)
            data["dose"].extend([dose] * len(values))
            data["group"].extend([group] * len(values))
            data["value"].extend(values.tolist())
    options = {
        "group": "group",
        "order": ["Low", "High"],
        "hue_order": ["B", "A"],
        "gap": 0.15,
        "marker_size": 2.5,
    }
    p = mp.plot(data).theme("publication").layout(1, 3).size(11.5, 3.5)
    p.boxenplot("dose", "value", **options, k_depth=4, panel=0)
    p.labels(x="Dose", y="Response", title="Exponential widths / four levels", panel=0)
    p.boxenplot(
        "dose",
        "value",
        **options,
        orient="h",
        k_depth=4,
        width_method="linear",
        panel=1,
    )
    p.labels(x="Response", y="Dose", title="Linear widths / horizontal", panel=1)
    p.boxenplot(
        "dose", "value", **options, k_depth="full", width_method="area", panel=2
    )
    p.labels(x="Dose", y="Response", title="Full depth / area widths", panel=2)
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
        plt.close(p.save(str(destination / f"letter_value_categories.{fmt}")))
    mp.save_spec(p.spec, destination / "letter_value_categories.mplot.json")
    print("OK: raw-data letter values, horizontal linear and full/area widths")


if __name__ == "__main__":
    main()
