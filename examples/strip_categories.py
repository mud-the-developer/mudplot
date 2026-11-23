"""Named local jitter, reserved hue slots, native logs and real date spacing."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp


def build_plot() -> mp.Plot:
    source = {
        "category": ["control", "control", "treated", "treated"] * 2,
        "value": [1.2, 2.4, 2.1, 3.6, 1.5, 2.8, 2.7, 4.2],
        "hue": ["A"] * 4 + ["C"] * 4,
        "dose": [1, 1, 10, 10] * 2,
        "date": ["2026-01-01", "2026-01-01", "2026-01-11", "2026-01-11"] * 2,
    }
    plot = mp.plot(source).theme("publication").layout(2, 2).size(10, 7)
    for panel, orient in ((0, "v"), (1, "h")):
        plot.stripplot(
            "category",
            "value",
            group="hue",
            orient=orient,
            order=["control", "empty", "treated"],
            hue_order=["A", "reserved", "C"],
            dodge=0.8,
            strip={"seed": 73},
            panel=panel,
        )
        plot.labels(title=f"Reserved slots / {orient}", panel=panel)
    plot.stripplot(
        "dose", "value", native_scale=True, strip={"seed": 73}, panel=2
    ).xscale("log", panel=2)
    plot.labels(
        x="Dose (log)", y="Response", title="Jitter in log-axis spacing", panel=2
    )
    plot.stripplot(
        "date", "value", orient="h", strip={"jitter_policy": "none"}, panel=3
    ).date_axis("y", timezone="UTC", panel=3)
    plot.labels(
        x="Response", y="UTC observation date", title="Ten elapsed days", panel=3
    )
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
        plt.close(plot.save(str(directory / f"strip_categories.{extension}")))
    mp.save_spec(plot.spec, directory / "strip_categories.mplot.json")
    assert before == plot.to_json()
    print(
        "PASS nested v/h, reserved slots, native log, dates, "
        "JSON/action/source preservation"
    )


if __name__ == "__main__":
    main()
