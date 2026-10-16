"""One question across two sites: automatic facets, cell-local pointwise CIs.

Run from the checkout: uv run python -m examples.faceted_responses
All data are synthetic; each site has six observations per method/timepoint.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
from examples.publication_showcase import REPLICATES, save_and_assess, synthetic_data
from mudplot import actions as A

ROOT = Path(__file__).resolve().parents[1]


def build_plot() -> mp.Plot:
    columns = synthetic_data()
    columns["site"] = [
        "North" if index % REPLICATES < REPLICATES // 2 else "South"
        for index in range(len(columns["time"]))
    ]
    plot = (
        mp.plot(columns)
        .theme("publication")
        .palette(preset=None, lightness=48, chroma=55, hue_start=20, cvd_safe=True)
        .font(size=11, label_size=11, title_size=12, tick_size=10.5)
        .lineplot(
            "time",
            "response",
            group="method",
            errorbar=("ci", 95),
            n_boot=399,
            seed=17,
            line_width=1.6,
            error_alpha=0.12,
        )
        .labels(x="Time (h)", y="Mean response (a.u.)")
        .xlim(0, 12)
        .ylim(0, 1.6)
        .legend(False)
        .suptitle("Response curves by site — synthetic observations")
        .facet(col="site", col_order=["North", "South"])
        .size(9, 3.6)
        .dispatch(A.SetDpi(200))
    )
    plot.legend(location="upper left", panel=0)
    return plot


def render_example(directory: str | Path) -> None:
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    plot = build_plot()
    mp.assert_valid(plot.spec)
    assert (
        mp.apply(plot.action_log) == mp.Plot.from_json(plot.to_json()).spec == plot.spec
    )
    report = save_and_assess(
        plot, destination / "faceted_responses.png", display_width_px=900
    )
    assert report["content_bounds_ok"] and report["font_floor_14px_ok"]
    assert report["text_overlap_ok"], report["overlapping_text"]
    for extension in ("pdf", "svg"):
        plt.close(plot.save(str(destination / f"faceted_responses.{extension}")))
    mp.save_spec(plot.spec, destination / "faceted_responses.mplot.json")
    print("OK: faceted responses, six independent observations per cell; 900px review")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path, default=ROOT / "docs/images")
    render_example(parser.parse_args().directory)
