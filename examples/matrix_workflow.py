"""Export a synthetic matrix and selected clustered profiles (mudplot[cluster])."""

from __future__ import annotations

import argparse
from pathlib import Path

import mudplot as mp


def track(track_id, title, values, key_colors):
    return mp.ClusterTrackSpec(
        track_id,
        title,
        values,
        [
            mp.ClusterTrackLevelSpec(key, label, color)
            for key, label, color in key_colors
        ],
    )


def build_plot() -> mp.Plot:
    return (
        mp.plot()
        .size(12, 6)
        .layout(1, 2, width_ratios=[1, 1.8])
        .matrix("changes", [[-3, 0, 5], [-1, 2, 9]])
        .heatmap(
            "changes",
            cmap_kind="diverging",
            clabel="Response change",
            heatmap=mp.HeatmapSpec(
                norm="boundary",
                boundaries=[-4, 0, 4, 10],
                xlabels=["Early", "Middle", "Late"],
                ylabels=["A", "B"],
                xrotation=28,
                annot=True,
                annot_data=[["fell", "even", "rose"], ["fell", "rose", "rose"]],
                colorbar_options=mp.ColorbarOptionsSpec(
                    location="bottom", ticks=[-4, 0, 4, 10], tick_format="g"
                ),
            ),
        )
        .labels(title="Response bands", panel=0)
        .matrix(
            "profiles",
            [[0, 2, None, 4], [0, None, 9, 7], [None, 6, 9, 4], [1, 6, 9, 7]],
        )
        .clustermap(
            "profiles",
            panel=1,
            clabel="Recorded response",
            heatmap=mp.HeatmapSpec(
                xlabels=["Q1", "Q2", "Q3", "Q4"],
                ylabels=["Zulu", "Echo", "Alpha", "Beta"],
                colorbar_options=mp.ColorbarOptionsSpec(
                    location="bottom", ticks=[0, 3, 6, 9], tick_format="g"
                ),
            ),
            cluster=mp.ClusterSpec(
                missing="complete_features",
                row_distances=mp.CondensedDistanceSpec(
                    "Independent survey distance", [1, 8, 8, 8, 8, 2]
                ),
                row_cut=mp.ClusterCutSpec(1, 1),
                row_dendrogram_ratio=0.21,
                col_dendrogram_ratio=0.16,
                row_tracks=[
                    track(
                        "site",
                        "Site",
                        ["n", "s", "s", "n"],
                        [("n", "North", "#4060a0"), ("s", "South", "#934728")],
                    ),
                    track(
                        "design",
                        "Design",
                        ["a", "a", "b", "b"],
                        [("a", "A", "#247b61"), ("b", "B", "#66558a")],
                    ),
                ],
            ),
        )
        .labels(title="Synthetic profiles and selected original rows", panel=1)
    )


def render_example(directory: Path) -> None:
    import matplotlib.pyplot as plt

    directory.mkdir(parents=True, exist_ok=True)
    spec = build_plot().spec
    mp.save_spec(spec, directory / "matrix_workflow.mplot.json")
    for suffix in ("png", "svg", "pdf"):
        plt.close(mp.save(spec, directory / f"matrix_workflow.{suffix}"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    render_example(parser.parse_args().directory)
