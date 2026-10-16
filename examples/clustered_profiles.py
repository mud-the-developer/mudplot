"""One synthetic profile-pattern question, standardized and hierarchically ordered.

Run: uv run python -m examples.clustered_profiles (requires mudplot[cluster]).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
from examples.publication_showcase import save_and_assess
from mudplot import actions as A

ROOT = Path(__file__).resolve().parents[1]


def build_plot() -> mp.Plot:
    values = [
        [1.0, 1.2, 4.0, 4.5, 0.8],
        [1.3, 1.0, 3.8, 4.7, 1.1],
        [4.8, 4.2, 1.1, 0.9, 4.6],
        [5.1, 4.0, 0.8, 1.3, 4.3],
        [0.9, 1.4, 4.2, 4.3, 1.0],
        [4.7, 4.5, 1.2, 1.0, 4.8],
    ]
    return (
        mp.plot()
        .matrix("profiles", values)
        .theme("publication")
        .font(size=11, label_size=11, title_size=12, tick_size=10.5)
        .clustermap(
            "profiles",
            cmap_kind="diverging",
            clabel="Row z-score",
            cluster=mp.ClusterSpec(
                z_score="row",
                optimal_ordering=True,
                row_colors=[
                    "#00858a",
                    "#00858a",
                    "#ba4056",
                    "#ba4056",
                    "#00858a",
                    "#ba4056",
                ],
                col_colors=["#94a3b8", "#94a3b8", "#00858a", "#00858a", "#94a3b8"],
            ),
            heatmap=mp.HeatmapSpec(
                annot=True,
                fmt=".1f",
                center=0,
                mask=[[False, False, False, True, False]]
                + [[False] * 5 for _ in range(5)],
                xlabels=["M1", "M2", "M3", "M4", "M5"],
                ylabels=["A1", "A2", "B1", "B2", "A3", "B3"],
            ),
            line_width=0.5,
            edge_color="#ffffff",
        )
        .labels(title="Row-standardised profiles — synthetic")
        .size(7, 6.5)
        .dispatch(A.SetDpi(200))
    )


def render_example(directory: str | Path) -> None:
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    plot = build_plot()
    mp.assert_valid(plot.spec)
    assert (
        mp.apply(plot.action_log) == mp.Plot.from_json(plot.to_json()).spec == plot.spec
    )
    report = save_and_assess(
        plot, destination / "clustered_profiles.png", display_width_px=700
    )
    assert report["content_bounds_ok"] and report["font_floor_14px_ok"]
    assert report["text_overlap_ok"], report["overlapping_text"]
    for extension in ("pdf", "svg"):
        plt.close(plot.save(str(destination / f"clustered_profiles.{extension}")))
    mp.save_spec(plot.spec, destination / "clustered_profiles.mplot.json")
    print("OK: clustered source profiles and aligned metadata; 700px desktop review")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path, default=ROOT / "docs/images")
    render_example(parser.parse_args().directory)
