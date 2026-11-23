"""Fixed classic rules and declared-unit discrete histograms; source stays raw."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
from mudplot._histogram import histogram_summary


def build_plot() -> mp.Plot:
    source = {
        "value": [0, 1, 2, 3, 100],
        "weight": [1, 2, 3, 4, 5],
        "state": [-2, 0, 2, 0, 2],
        "seconds": [0, 1, 2, 3, 4],
        "milliseconds": [0, 1, 2, 3, 4],
        "date": ["2026-01-01", "2026-01-02", "2026-01-04", "2026-01-04", "2026-01-05"],
    }
    plot = mp.plot(source).theme("publication").layout(3, 2).size(13, 12)
    plot.hist("value", bins="auto", weights="weight", panel=0)
    plot.labels(
        x="Measured amplitude (a.u.)",
        y="Weighted count (a.u.)",
        title="Fixed classic auto: 43 bins",
        panel=0,
    )
    plot.hist("state", discrete=True, panel=1)
    plot.labels(
        x="Discrete state (integer)",
        y="Count",
        title="Unit cells include empty states -1 and 1",
        panel=1,
    )
    for panel, column, unit in ((2, "seconds", "s"), (3, "milliseconds", "ms")):
        plot.hist(column, bins="discrete", panel=panel)
        plot.date_axis("x", unit=unit, origin="2026-01-01", timezone="UTC", panel=panel)
        plot.labels(
            x=f"UTC clock / input offset ({unit})",
            y="Count",
            title=f"One declared {unit} per cell",
            panel=panel,
        )
    plot.hist("date", bins="discrete", panel=4)
    plot.date_axis("x", timezone="UTC", panel=4)
    plot.labels(
        x="UTC midnight date", y="Count", title="One display-clock day", panel=4
    )
    # Separate numeric proof avoids pretending millisecond clock ticks show widths.
    plot.hist("milliseconds", bins="discrete", panel=5)
    plot.labels(
        x="Input offset (ms, no time conversion)",
        y="Count",
        title="Numeric proof: one millisecond cells",
        panel=5,
    )
    result = histogram_summary(source, plot.spec.panels[0].layers[0])
    assert len(result.edges) == 44 and sum(result.curves[0].heights) == 15
    result = histogram_summary(source, plot.spec.panels[1].layers[0])
    assert result.edges == (-2.5, -1.5, -0.5, 0.5, 1.5, 2.5)
    assert result.curves[0].heights == (1, 0, 2, 0, 2)
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
        plt.close(plot.save(str(directory / f"histogram_binning.{extension}")))
    mp.save_spec(plot.spec, directory / "histogram_binning.mplot.json")
    assert plot.to_json() == before
    print("PASS auto43, empty cells, s+ms, UTC midnight; source unchanged")


if __name__ == "__main__":
    main()
