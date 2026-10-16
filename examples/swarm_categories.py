"""Run: python examples/swarm_categories.py [output_directory].

Swarm packing follows actual draw-time transforms, including log value axes.
Duplicate observations remain present; overcrowding is never silently dropped.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp


def build_plot() -> mp.Plot:
    data = {"dose": [], "value": [], "group": []}
    for group, shift in (("A", 0), ("B", 0.3)):
        for dose, effect in (("Low", 0), ("High", 0.7)):
            for value in (1, 1, 1.05, 1.1, 1.1, 1.3, 1.35, 1.5, 1.5, 1.7):
                data["dose"].append(dose)
                data["group"].append(group)
                data["value"].append(value + shift + effect)
    options = {"group": "group", "order": ["Low", "High"], "hue_order": ["B", "A"]}
    p = mp.plot(data).theme("publication").layout(1, 3).size(11.5, 3.5)
    # Neutral combined boxes; hue colours belong to observations consistently
    # across panels (shared automatic semantics across layers remain deferred).
    p.box(
        "dose",
        "value",
        order=["Low", "High"],
        showfliers=False,
        color="#cbd5e1",
        edge_color="#4b5563",
        panel=0,
    )
    p.swarmplot("dose", "value", **options, dodge=0, marker_size=4, panel=0)
    p.labels(x="Dose", y="Value", title="Raw observations over native boxes", panel=0)
    p.swarmplot("dose", "value", **options, orient="h", marker_size=5, panel=1)
    p.labels(x="Value", y="Dose", title="Horizontal: values stay unchanged", panel=1)
    p.swarmplot("dose", "value", **options, marker_size=5, panel=2).yscale(
        "log", panel=2
    )
    p.labels(
        x="Dose", y="Value (log)", title="Packing after the log transform", panel=2
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
        plt.close(p.save(str(destination / f"swarm_categories.{fmt}")))
    mp.save_spec(p.spec, destination / "swarm_categories.mplot.json")
    print("OK: box/swarm overlay, horizontal geometry and positive log-value packing")


if __name__ == "__main__":
    main()
