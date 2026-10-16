"""One paired question with aligned histogram marginals; all data are synthetic.

Run: uv run python -m examples.joint_observations
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
    columns = {"dose": [], "response": [], "condition": []}
    for condition, shift in (("Reference", 0), ("Treatment", 0.6)):
        dose = rng.normal(3.5 + shift, 0.7, 40)
        response = 0.8 * dose + shift + rng.normal(0, 0.45, 40)
        columns["dose"].extend(dose.tolist())
        columns["response"].extend(response.tolist())
        columns["condition"].extend([condition] * 40)
    return (
        mp.plot(columns)
        .theme("publication")
        .palette(preset=None, lightness=48, chroma=55, hue_start=20, cvd_safe=True)
        .font(size=11, label_size=11, title_size=12, tick_size=10.5)
        .scatter("dose", "response", group="condition", marker_size=3.5, alpha=0.8)
        .labels(
            x="Dose (mg)", y="Response (a.u.)", title="Paired observations — synthetic"
        )
        .legend(location="upper left")
        .joint(bins=10, ratio=3, marginal_stat="density")
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
        plot, destination / "joint_observations.png", display_width_px=700
    )
    assert report["content_bounds_ok"] and report["font_floor_14px_ok"]
    assert report["text_overlap_ok"], report["overlapping_text"]
    for extension in ("pdf", "svg"):
        plt.close(plot.save(str(destination / f"joint_observations.{extension}")))
    mp.save_spec(plot.spec, destination / "joint_observations.mplot.json")
    print("OK: joint scatter and paired histogram marginals; 700px desktop review")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path, default=ROOT / "docs/images")
    render_example(parser.parse_args().directory)
