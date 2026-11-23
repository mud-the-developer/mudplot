"""Explicit ISO clocks in joint/pair grids; source rows and timestamps survive."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import mudplot as mp


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("artifacts/temporal_grids"))
    out = parser.parse_args().out
    out.mkdir(parents=True, exist_ok=True)
    source = {
        "time": ["2026-01-01", "2026-01-02", "2026-01-04", "2026-01-08", "2026-01-11"],
        "signal": [2.0, 2.3, 2.1, 2.7, 2.6],
    }
    joint = (
        mp.plot(source)
        .scatter("time", "signal")
        .date_axis("x", timezone="UTC")
        .labels(x="Date (UTC)", y="Signal (a.u.)")
        .joint(bins=3)
        .size(7.2, 6)
    )
    joint.labels(x="Date (UTC)", y="Signal (a.u.)", panel=0)
    joint.labels(x="Density (a.u.⁻¹)", panel=1)
    joint.labels(y="Density (day⁻¹)", panel=2)
    pair = (
        mp.plot(source)
        .pair(["time", "signal"], temporal={"time": {"timezone": "UTC"}}, bins=3)
        .size(12, 7.5)
    )
    for index, panel in enumerate(pair.spec.panels):
        x = "Date (UTC)" if panel.layers[0].x == "time" else "Signal (a.u.)"
        if index in (0, 3):
            y = "Density (day⁻¹)" if index == 0 else "Density (a.u.⁻¹)"
        else:
            y = "Date (UTC)" if panel.layers[0].y == "time" else "Signal (a.u.)"
        pair.labels(x=x, y=y, panel=index)
    for name, plot in (("temporal_joint", joint), ("temporal_pair", pair)):
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
