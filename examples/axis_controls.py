"""N12 finite ticks, native scales, declared clocks and derived units."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp


def build_plot():
    columns = {
        "signed": [-100, -10, -1, -0.1, 0, 0.1, 1, 10, 100],
        "length": [3, 4, 2, 1, 0, 1, 2, 4, 3],
        "probability": [0.001, 0.01, 0.1, 0.3, 0.5, 0.7, 0.9, 0.99, 0.999],
        "celsius": [-40, -20, 0, 20, 40, 60, 80, 100, 120],
        "frequency": [1, 2, 4, 8, 16, 32, 64, 128, 256],
        "local_day": [f"2026-01-{day:02d}T00:00:00+05:30" for day in range(1, 10)],
        "row_id": [f"observation-{i}" for i in range(9)],
    }
    p = mp.plot(columns).theme("publication").size(17, 10).layout(2, 3)
    p.line("signed", "length", panel=0, marker="o")
    p.axis_scale(
        "x", "symlog", options={"base": 10, "linthresh": 1, "linscale": 1}, panel=0
    )
    p.ticks(
        "x",
        {
            "locator": {"kind": "symlog"},
            "formatter": {"kind": "log", "style": "mathtext"},
        },
        panel=0,
    )
    p.ticks(
        "x", {"locator": {"kind": "symlog", "subs": [2, 5]}}, which="minor", panel=0
    )
    p.labels(
        title="Signed symlog: declared linear region",
        x="Signed coordinate",
        y="Length (m)",
        panel=0,
    )

    p.line("signed", "length", panel=1, marker="o")
    p.axis_scale("x", "asinh", options={"linear_width": 2, "base": 10}, panel=1)
    p.ticks(
        "x",
        {
            "locator": {"kind": "asinh", "count": 9},
            "formatter": {"kind": "number", "notation": "general", "precision": 3},
        },
        panel=1,
    )
    p.labels(
        title="Smooth asinh; no source standardization",
        x="Signed coordinate",
        y="Length (m)",
        panel=1,
    )

    p.line("probability", "length", panel=2, marker="o")
    p.axis_scale("x", "logit", panel=2)
    p.ticks(
        "x",
        {
            "locator": {"kind": "logit"},
            "formatter": {"kind": "percent", "xmax": 1, "decimals": 1},
        },
        panel=2,
    )
    p.ticks("x", {"locator": {"kind": "logit"}}, which="minor", panel=2)
    p.labels(
        title="Logit geometry, percentage labels",
        x="Probability",
        y="Length (m)",
        panel=2,
    )

    p.line("local_day", "length", panel=3, marker="o")
    p.date_axis("x", timezone="+05:30", panel=3)
    p.ticks(
        "x",
        {
            "locator": {"kind": "calendar", "unit": "day", "interval": 2},
            "formatter": {"kind": "concise_date"},
        },
        panel=3,
    )
    p.ticks(
        "x",
        {
            "locator": {"kind": "calendar", "unit": "day", "interval": 1},
            "formatter": {"kind": "none"},
        },
        which="minor",
        panel=3,
    )
    p.secondary_xaxis(
        {"kind": "unix_seconds"},
        label="Unix seconds (UTC), not source ISO text",
        major_ticks={
            "locator": {"kind": "linear", "count": 3},
            "formatter": {"kind": "number", "notation": "fixed", "precision": 0},
        },
        panel=3,
    )
    p.labels(
        title="Declared local calendar / canonical UTC conversion",
        x="Local midnight (+05:30)",
        y="Length (m)",
        panel=3,
    )

    p.line(
        "celsius",
        "length",
        panel=4,
        marker="o",
        label="Known observations",
        citation="known2026",
        href="https://example.org/axis-controls",
    )
    p.xlim(-40, 120, panel=4)
    p.ticks(
        "x",
        {
            "locator": {"kind": "multiple", "step": 40},
            "formatter": {"kind": "number", "notation": "fixed", "precision": 0},
        },
        panel=4,
    )
    p.secondary_xaxis(
        {"kind": "celsius_fahrenheit"},
        label="Temperature (°F)",
        major_ticks={
            "locator": {"kind": "linear", "count": 5},
            "formatter": {"kind": "number", "notation": "fixed", "precision": 0},
        },
        panel=4,
    )
    p.labels(
        title="Analytic Celsius ↔ Fahrenheit",
        x="Temperature (°C)",
        y="Length (m)",
        panel=4,
    )
    p.legend(location="upper left", panel=4)

    p.line("frequency", "length", panel=5, marker="o")
    p.xscale("log", options={"base": 2, "subs": [math.sqrt(2)]}, panel=5).xlim(
        1, 256, panel=5
    )
    p.ticks(
        "x",
        {"locator": {"kind": "log"}, "formatter": {"kind": "log", "style": "mathtext"}},
        panel=5,
    )
    p.secondary_xaxis(
        {"kind": "hertz_period"},
        label="Period (s), decreasing conversion",
        major_ticks={
            "locator": {"kind": "fixed", "values": [1 / 256, 1 / 64, 1 / 16, 1 / 4, 1]},
            "formatter": {"kind": "engineering", "unit": "s", "precision": 1},
        },
        panel=5,
    )
    p.secondary_axis(
        "y",
        {
            "kind": "affine",
            "factor": 100,
            "offset": 0,
            "source_unit": "m",
            "target_unit": "cm",
        },
        label="Length (cm)",
        major_ticks={
            "locator": {"kind": "linear", "count": 5},
            "formatter": {"kind": "number", "notation": "fixed", "precision": 0},
        },
        panel=5,
    )
    p.labels(
        title="Base-two frequency / reciprocal period",
        x="Frequency (Hz)",
        y="Length (m)",
        panel=5,
    )
    return p


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="artifacts/v2_axis_controls")
    directory = Path(parser.parse_args().directory)
    directory.mkdir(parents=True, exist_ok=True)
    p = build_plot()
    before = p.to_json()
    p.axis_scale(
        "x", "symlog", options={"base": 10, "linthresh": 2, "linscale": 1.5}, panel=0
    )
    edited = p.to_json()
    p.store.undo()
    assert p.to_json() == before
    p.store.redo()
    assert p.to_json() == edited and mp.apply(p.action_log) == p.spec
    mp.save_spec(p.spec, directory / "axis_controls.mplot.json")
    reopened = mp.Plot.from_json(
        mp.to_json(mp.load_spec(directory / "axis_controls.mplot.json"))
    )
    assert reopened.spec == p.spec
    for extension in ("png", "svg", "pdf"):
        plt.close(reopened.save(str(directory / f"axis_controls.{extension}")))
    print(
        "PASS N12 six-panel scales/ticks/clock/derived units + "
        "action edit/history/reopen/PNG SVG PDF"
    )


if __name__ == "__main__":
    main()
