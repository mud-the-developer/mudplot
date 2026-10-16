"""One question per figure: residual, log-x, Huber, logistic and LOWESS.

Run: uv run python -m examples.regression_modes (requires mudplot[regression]).
All observations are synthetic; no causal or bootstrap-inference claim.
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


def build_plots() -> dict[str, mp.Plot]:
    rng = np.random.default_rng(2026)
    x = np.linspace(1, 10, 60)
    ordinary = 1 + 0.5 * x + 0.07 * x**2 + rng.normal(0, 0.35, len(x))
    logx = np.geomspace(0.1, 100, 60)
    robust = 2 + 1.1 * x + rng.normal(0, 0.4, len(x))
    robust[[7, 25, 47]] += [6, -7, 8]
    logistic_x = np.linspace(-3, 3, 100)
    binary = rng.binomial(1, 1 / (1 + np.exp(-0.85 * logistic_x)))
    lowess_x = np.linspace(0, 12, 70)
    cases = {
        "residual": (
            {"x": x, "y": ordinary},
            "poly",
            "Polynomial residuals",
            "Residual (a.u.)",
        ),
        "logx": (
            {"x": logx, "y": 3 + 1.5 * np.log(logx) + rng.normal(0, 0.3, 60)},
            "logx",
            "Response vs log predictor",
            "Response (a.u.)",
        ),
        "robust": (
            {"x": x, "y": robust},
            "robust",
            "Huber fit with retained outliers",
            "Response (a.u.)",
        ),
        "logistic": (
            {"x": logistic_x, "y": binary},
            "logistic",
            "Binary observations and fitted probability",
            "Response / probability",
        ),
        "lowess": (
            {"x": lowess_x, "y": np.sin(lowess_x / 2) + rng.normal(0, 0.15, 70)},
            "lowess",
            "Local response trend",
            "Response (a.u.)",
        ),
    }
    plots = {}
    for name, (columns, model, title, ylabel) in cases.items():
        plot = (
            mp.plot(columns)
            .theme("publication")
            .font(size=11, label_size=11, title_size=12, tick_size=10.5)
            .dispatch(A.SetDpi(200))
            .size(7, 4.5)
        )
        config = mp.RegressionSpec(model=model)
        if name == "residual":
            plot.residplot(
                "x", "y", degree=2, regression=config, marker_size=3.5, alpha=0.8
            )
        else:
            if name == "lowess":
                config.frac = 0.4
            plot.regplot("x", "y", regression=config, marker_size=3.5, alpha=0.8)
        if name == "logx":
            plot.xscale("log")
        if name == "logistic":
            plot.ylim(-0.05, 1.05)
        plot.labels(x="Predictor (a.u.)", y=ylabel, title=title + " — synthetic")
        plots["regression_" + name] = plot
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
    print(
        "OK: five separate regression questions, synthetic data; 700px desktop review"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path, default=ROOT / "docs/images")
    render_examples(parser.parse_args().directory)
