"""Run: python examples/statistical_categories.py [output_directory].

Synthetic repeated observations, positive analytic weights and explicit
categorical layouts. CI resamples units, then paired value/weight rows.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp


def build_plot() -> mp.Plot:
    data = {"dose": [], "response": [], "cell": [], "subject": [], "weight": []}
    for cell, effect in (("A", 0.4), ("B", 0.6)):
        for dose, step in (("Control", 0), ("Low", 1), ("High", 2)):
            for subject, shift in enumerate((-0.15, 0, 0.15)):
                for repeat, noise in enumerate((-0.05, 0.05)):
                    data["dose"].append(dose)
                    data["response"].append(1 + step * effect + shift + noise)
                    data["cell"].append(cell)
                    data["subject"].append(f"{cell}-{subject}")
                    data["weight"].append(1 + repeat)
    order, hues = ["Control", "Low", "High"], ["B", "A"]
    return (
        mp.plot(data)
        .theme("publication")
        .layout(1, 3)
        .size(11.5, 3.7)
        .barplot(
            "dose",
            "response",
            group="cell",
            weights="weight",
            units="subject",
            n_boot=1000,
            seed=42,
            order=order,
            hue_order=hues,
            gap=0.12,
            value_labels=True,
            label_format=".2f",
            panel=0,
        )
        .labels(
            x="Dose", y="Response", title="Weighted mean / unit bootstrap CI", panel=0
        )
        .legend(title="Cell", location="upper left", panel=0)
        .ylim(0, 2.7, panel=0)
        .pointplot(
            "dose",
            "response",
            group="cell",
            errorbar="se",
            orient="h",
            order=order,
            hue_order=hues,
            dodge=0.15,
            panel=1,
        )
        .labels(x="Response", y="Dose", title="Horizontal mean / sample SEM", panel=1)
        .legend(title="Cell", location="lower right", panel=1)
        .countplot(
            "dose",
            group="cell",
            stat="percent",
            stack=True,
            orient="h",
            order=order,
            hue_order=hues,
            value_labels=True,
            label_format=".1f",
            panel=2,
        )
        .labels(
            x="Percent of all observations",
            y="Dose",
            title="Stacked sample percentages",
            panel=2,
        )
        .legend(title="Cell", location="lower right", panel=2)
        .xlim(0, 42, panel=2)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="docs/images")
    destination = Path(parser.parse_args().directory)
    destination.mkdir(parents=True, exist_ok=True)
    p = build_plot()
    mp.assert_valid(p.spec)
    assert mp.Plot.from_json(p.to_json()).spec == p.spec
    for fmt in ("png", "svg"):
        plt.close(p.save(str(destination / f"statistical_categories.{fmt}")))
    mp.save_spec(p.spec, destination / "statistical_categories.mplot.json")
    print("OK: weighted/unit CI, horizontal SEM and normalized stacked counts")


if __name__ == "__main__":
    main()
