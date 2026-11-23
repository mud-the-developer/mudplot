"""N13 named mosaic spans, nested ratios, real insets and empty positions."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp


def build_plot():
    time = [i / 20 for i in range(101)]
    columns = {
        "time_s": time,
        "response_mV": [math.sin(2 * math.pi * t) * math.exp(-t / 4) for t in time],
        "row_id": [f"sample-{i:03d}" for i in range(len(time))],
    }
    p = mp.plot(columns).theme("publication").size(11, 6.5)
    p.line("time_s", "response_mV", label="Observed response", color="#287f8e")
    p.mosaic(
        [
            ["signal", "signal", "distribution"],
            ["signal", "signal", "reserved"],
        ],
        width_ratios=[2, 1, 2],
        height_ratios=[2, 1],
    )
    p.nest(1, 1)
    p.hist(
        "time_s",
        stat="density",
        bins=[0, 1, 2, 3, 4, 5],
        panel=1,
        color="#df9b40",
        label="Sampling density",
    )
    p.share_axis("x", "observation_time", panel=0)
    p.share_axis("x", "observation_time", panel=1)
    p.labels(
        title="A · Time response with a real inset", x="Time (s)", y="Response (mV)"
    )
    p.labels(
        title="B · Distribution, independent density units",
        x="Time (s)",
        y="Density (1/s)",
        panel=1,
    )
    p.labels(title="C · Reserved empty panel", x="No observations added", y="", panel=2)
    p.title_position([0.1, 0.8], panel=2)
    p.inset("signal", [0.53, 0.12, 0.4, 0.32], panel_id="detail")
    p.line("time_s", "response_mV", color="#287f8e", panel=3)
    p.xlim(1.5, 2.5, panel=3).ylim(-0.8, 0.8, panel=3)
    p.labels(title="Inset · 1.5-2.5 s", x="Time (s)", y="mV", panel=3)
    p.font(size=10, title_size=11, label_size=10, tick_size=9)
    return p


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="artifacts/v2_panel_layouts")
    directory = Path(parser.parse_args().directory)
    directory.mkdir(parents=True, exist_ok=True)
    p = build_plot()
    before = p.to_json()
    p.place(
        "detail", {"inset": {"parent": "signal", "bounds": [0.5, 0.14, 0.43, 0.32]}}
    )
    edited = p.to_json()
    p.store.undo()
    assert p.to_json() == before
    p.store.redo()
    assert p.to_json() == edited and mp.apply(p.action_log) == p.spec
    mp.save_spec(p.spec, directory / "panel_layouts.mplot.json")
    reopened = mp.Plot.from_json(
        mp.to_json(mp.load_spec(directory / "panel_layouts.mplot.json"))
    )
    for extension in ("png", "svg", "pdf"):
        plt.close(reopened.save(str(directory / f"panel_layouts.{extension}")))
    print(
        "PASS N13 mosaic spans/nested ratios/inset/empty panel + "
        "placement edit/history/reopen/PNG SVG PDF"
    )


if __name__ == "__main__":
    main()
