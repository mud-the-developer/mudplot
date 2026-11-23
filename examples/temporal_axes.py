"""Explicit F02 calendar axes; irregular sampling and source timestamps survive."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import mudplot as mp


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("artifacts/temporal_axes"))
    out = parser.parse_args().out
    out.mkdir(parents=True, exist_ok=True)
    source = {
        "time": [
            "2026-01-01T01:00:00+01:00",
            "2026-01-02T00:00:00Z",
            "2026-01-04T00:00:00Z",
            "2026-01-08T00:00:00Z",
            "2026-01-11T00:00:00Z",
        ],
        "signal": [2.0, 2.3, 2.1, 2.7, 2.6],
    }
    plots = {
        "irregular_signal": (
            mp.plot(source)
            .line("time", "signal", marker="o")
            .date_axis("x", timezone="UTC")
            .labels(x="Observation date (UTC)", y="Declared signal (a.u.)")
            .size(6.5, 3)
        ),
        "event_density": (
            mp.plot(source)
            .hist(
                "time", bins=["2026-01-01", "2026-01-05", "2026-01-12"], stat="density"
            )
            .date_axis("x", timezone="UTC")
            .labels(x="Observation date (UTC)", y="Event density (day⁻¹)")
            .size(6.5, 3)
        ),
        "signal_with_density": (
            mp.plot(source)
            .line("time", "signal", marker="o")
            .secondary_yaxis("Observation density (day⁻¹)")
            .hist(
                "time",
                axis="y2",
                bins=["2026-01-01", "2026-01-05", "2026-01-12"],
                stat="density",
                alpha=0.25,
            )
            .date_axis("x", timezone="UTC")
            .labels(x="Observation date (UTC)", y="Declared signal (a.u.)")
            .size(6.5, 3)
        ),
    }
    for name, plot in plots.items():
        before = plot.to_json()
        mp.save_spec(plot.spec, out / f"{name}.mplot.json")
        restored = mp.Plot.from_json(
            (out / f"{name}.mplot.json").read_text(encoding="utf-8")
        )
        assert restored.spec == plot.spec and restored.spec.data.columns == source
        for extension in ("png", "svg", "pdf"):
            plt.close(restored.save(out / f"{name}.{extension}", layout_policy="smart"))
        assert plot.to_json() == before and restored.to_json() == before
    print(out)


if __name__ == "__main__":
    main()
