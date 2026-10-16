"""Three synthetic variables: univariate diagonals and pairwise raw scatter.

Run: uv run python -m examples.pair_observations
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
from examples.publication_showcase import save_and_assess
from mudplot import actions as A

ROOT = Path(__file__).resolve().parents[1]


def build_plot() -> mp.Plot:
    rng = np.random.default_rng(2026)
    data = {"Dose": [], "Response": [], "Delay": [], "condition": []}
    for condition, shift in (("Reference", 0), ("Treatment", 0.6)):
        dose = rng.normal(3.5 + shift, 0.7, 40)
        response = 0.8 * dose + shift + rng.normal(0, 0.45, 40)
        delay = 12 - response + rng.normal(0, 0.7, 40)
        for name, values in (("Dose", dose), ("Response", response), ("Delay", delay)):
            data[name].extend(values.tolist())
        data["condition"].extend([condition] * 40)
    plot = (
        mp.plot(data)
        .theme("publication")
        .palette(preset=None, lightness=48, chroma=55, hue_start=20, cvd_safe=True)
        .font(size=11, label_size=11, title_size=12, tick_size=10.5)
        .legend(False)
        .suptitle("Numeric pair matrix — synthetic observations")
        .pair(["Dose", "Response", "Delay"], group="condition", bins=10)
        .size(9, 9)
        .dispatch(A.SetDpi(200))
    )
    plot.legend(location="upper left", panel=1)
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
        plot, destination / "pair_observations.png", display_width_px=900
    )
    assert report["content_bounds_ok"] and report["font_floor_14px_ok"]
    assert report["text_overlap_ok"], report["overlapping_text"]
    for extension in ("pdf", "svg"):
        plt.close(plot.save(str(destination / f"pair_observations.{extension}")))
    mp.save_spec(plot.spec, destination / "pair_observations.mplot.json")
    print("OK: numeric pair matrix, 80 synthetic observations; 900px desktop review")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path, default=ROOT / "docs/images")
    render_example(parser.parse_args().directory)
