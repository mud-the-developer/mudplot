"""Export an editable sampled experiment with one raw scalar facet calibration."""

import sys
from pathlib import Path

import mudplot as mp
from mudplot.actions import SetAxisTicks


def build():
    rows = {
        "clock": [0, 86400, 172800, 0, 86400, 172800],
        "response": [1, 2.5, 5, 3, 5.5, 7],
        "site": ["North"] * 3 + ["South"] * 3,
    }
    plot = (
        mp.plot(rows)
        .theme("paper")
        .size(10.8, 4.8)
        .secondary_yaxis("Response (mV)")
        .date_axis("x", unit="s", origin="2026-01-01T00:00:00Z")
        .xlim(20453.8, 20456.2)
        .labels(x="UTC date")
    )
    plot.dispatch(
        SetAxisTicks(
            "x",
            "major",
            mp.TickSpec(
                locator=mp.LocatorSpec(kind="fixed", values=[20454, 20455, 20456]),
                formatter=mp.FormatterSpec(
                    kind="fixed", labels=["Jan 1", "Jan 2", "Jan 3"]
                ),
            ),
        )
    )
    return plot.relplot(
        "clock",
        "response",
        axis="y2",
        c="clock",
        colorbar=True,
        clabel="Elapsed seconds",
        col="site",
        col_order=["North", "South", "Reserved"],
        marker_size=8,
        line_width=0.45,
        edge_color="#263844",
    )


if __name__ == "__main__":
    output = Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=True)
    plot = build()
    (output / "facet-builders.mplot.json").write_text(plot.to_json(), encoding="utf-8")
    for extension in ("png", "svg", "pdf"):
        plot.save(str(output / f"facet-builders.{extension}"))
