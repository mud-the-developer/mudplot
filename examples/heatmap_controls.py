"""Masked, annotated diverging heatmap; synthetic values, no inference claim.

Run: uv run python -m examples.heatmap_controls
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
        [-0.24, -0.08, 0.02, 0.12, 0.21],
        [-0.12, 0.03, 0.18, 0.25, 0.34],
        [-0.04, 0.14, 0.22, 0.31, 0.43],
    ]
    return (
        mp.plot()
        .matrix("change", values)
        .theme("publication")
        .font(size=12, label_size=12, title_size=14, tick_size=12)
        .heatmap(
            "change",
            cmap_kind="diverging",
            clabel="Change from baseline",
            heatmap=mp.HeatmapSpec(
                annot=True,
                fmt=".1%",
                center=0,
                vmin=-0.5,
                vmax=0.5,
                mask=[[False, False, True, False, False], [False] * 5, [False] * 5],
                xlabels=["Day 1", "Day 2", "Day 3", "Day 4", "Day 5"],
                ylabels=["Reference", "Method A", "Method B"],
            ),
            line_width=0.7,
            edge_color="#ffffff",
        )
        .labels(title="Change by method and day — synthetic")
        .size(7, 4.3)
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
        plot, destination / "heatmap_controls.png", display_width_px=700
    )
    assert report["content_bounds_ok"] and report["font_floor_14px_ok"]
    assert report["text_overlap_ok"], report["overlapping_text"]
    for extension in ("pdf", "svg"):
        plt.close(plot.save(str(destination / f"heatmap_controls.{extension}")))
    mp.save_spec(plot.spec, destination / "heatmap_controls.mplot.json")
    print("OK: masked annotated heatmap; 700px desktop review")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path, default=ROOT / "docs/images")
    render_example(parser.parse_args().directory)
