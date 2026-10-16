"""Configured KDE joint marginals and pair diagonals on the same synthetic data.

Run: uv run python -m examples.kde_grids
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
from examples.joint_observations import build_plot as source_plot
from examples.publication_showcase import save_and_assess
from mudplot import actions as A

ROOT = Path(__file__).resolve().parents[1]


def build_plots() -> dict[str, mp.Plot]:
    columns = source_plot().spec.data.columns
    config = mp.KDESpec(bw_method="silverman", bw_adjust=0.8, cut=0, gridsize=128)
    plots = {}
    for name in ("kde_joint", "kde_pair"):
        plot = (
            mp.plot(columns)
            .theme("publication")
            .palette(preset=None, lightness=48, chroma=55, hue_start=20, cvd_safe=True)
            .font(size=11, label_size=11, title_size=12, tick_size=10.5)
            .dispatch(A.SetDpi(200))
        )
        if name == "kde_joint":
            plot.scatter(
                "dose", "response", group="condition", marker_size=3.5, alpha=0.8
            )
            plot.labels(
                x="Dose (mg)",
                y="Response (a.u.)",
                title="Paired observations — KDE marginals",
            )
            plot.legend(location="upper left").joint(
                marginal_kind="kde", kde=config
            ).size(7, 6.5)
        else:
            plot.legend(False).pair(
                ["dose", "response"], group="condition", diag_kind="kde", kde=config
            )
            plot.size(7, 7).suptitle("Raw pairs and KDE diagonals — synthetic")
            plot.legend(location="upper left", panel=1)
        plots[name] = plot
    return plots


def render_examples(directory: str | Path) -> None:
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    for name, plot in build_plots().items():
        mp.assert_valid(plot.spec)
        assert (
            mp.apply(plot.action_log)
            == mp.Plot.from_json(plot.to_json()).spec
            == plot.spec
        )
        report = save_and_assess(
            plot, destination / f"{name}.png", display_width_px=700
        )
        assert report["content_bounds_ok"] and report["font_floor_14px_ok"]
        assert report["text_overlap_ok"], report["overlapping_text"]
        for extension in ("pdf", "svg"):
            plt.close(plot.save(str(destination / f"{name}.{extension}")))
        mp.save_spec(plot.spec, destination / f"{name}.mplot.json")
    print("OK: configured KDE joint/pair grids; 700px desktop review")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path, default=ROOT / "docs/images")
    render_examples(parser.parse_args().directory)
