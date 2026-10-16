"""Render an original-style bar chart, SD, and an explicitly estimated 95% CI.

Run from the repository root:
    uv run python examples/bar_uncertainty.py

All observations are synthetic. The example (NOT the renderer) computes
sample SD with ddof=1 and a 95% percentile-bootstrap interval of the mean
from 4,000 resamples of 12 observations per cell/dose. SD is not a CI.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import mudplot as mp
import numpy as np
from mudplot import actions as A

ROOT = Path(__file__).resolve().parents[1]
MEANS = [1.0, 1.4, 1.9, 0.9, 1.6, 2.3, 1.1, 1.3, 1.7]
SDS = [0.10, 0.13, 0.16, 0.09, 0.14, 0.18, 0.11, 0.12, 0.15]
N = 12
RESAMPLES = 4_000
BAR_STYLE = {"bar_width": 0.72, "edge_color": "white", "line_width": 0.5}


def synthetic_summaries() -> dict:
    """Preserve the gallery means; estimate intervals from seeded observations."""
    rng = np.random.default_rng(2026)
    lower, upper, measured_sd = [], [], []
    for mean, sd in zip(MEANS, SDS, strict=True):
        # Synthetic observations with the specified sample mean and SD.
        centered = rng.normal(size=N)
        centered -= centered.mean()
        observations = mean + sd * centered / centered.std(ddof=1)
        measured_sd.append(float(observations.std(ddof=1)))
        bootstrap_means = rng.choice(observations, size=(RESAMPLES, N)).mean(axis=1)
        lo, hi = np.quantile(bootstrap_means, [0.025, 0.975])
        lower.append(float(lo))
        upper.append(float(hi))
    return {
        "dose": ["Control", "Low", "High"] * 3,
        "response": list(MEANS),
        "cell": ["A"] * 3 + ["B"] * 3 + ["C"] * 3,
        "sd": measured_sd,
        "ci_low": lower,
        "ci_high": upper,
        "n": [N] * len(MEANS),
    }


def build_plot(kind: str, data: dict | None = None) -> mp.Plot:
    """Same synthetic means, displayed in the old style, with SD, or with CI."""
    if kind not in {"before", "sd", "ci95"}:
        raise ValueError("kind must be before, sd or ci95")
    plot = mp.plot(synthetic_summaries() if data is None else data)
    if kind == "before":
        plot.bar("dose", "response", group="cell")
        title = "Original grouped bars"
    else:
        plot.theme("publication").encoding(redundant_encoding=False)
        if kind == "sd":
            plot.bar("dose", "response", group="cell", yerr="sd", **BAR_STYLE)
            title = "Mean ± SD"
        else:
            plot.bar(
                "dose",
                "response",
                group="cell",
                y_lower="ci_low",
                y_upper="ci_high",
                **BAR_STYLE,
            )
            title = "Mean with 95% CI"
    return (
        plot.labels(x="Dose", y="Response (a.u.)", title=title)
        .legend(title="Cell line", location="upper left")
        .ylim(0, 2.8)
        .size(5.2, 3.5)
        .dispatch(A.SetDpi(180))
    )


def build_comparison(data: dict | None = None) -> mp.Plot:
    """Side-by-side SD and bootstrap CI with identical data and y scales."""
    plot = (
        mp.plot(synthetic_summaries() if data is None else data)
        .theme("publication")
        .encoding(redundant_encoding=False)
        .layout(1, 2)
        .size(9.4, 3.5)
        .dispatch(A.SetDpi(180))
    )
    plot.bar("dose", "response", group="cell", yerr="sd", panel=0, **BAR_STYLE)
    plot.bar(
        "dose",
        "response",
        group="cell",
        y_lower="ci_low",
        y_upper="ci_high",
        panel=1,
        **BAR_STYLE,
    )
    for panel, title in enumerate(("Mean ± SD", "Mean with 95% CI")):
        plot.labels(x="Dose", y="Response (a.u.)", title=title, panel=panel)
        plot.legend(title="Cell line", location="upper left", panel=panel)
        plot.ylim(0, 2.8, panel=panel)
    return plot


def render_examples(directory: str | Path) -> None:
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    data = synthetic_summaries()
    plots = {f"bar_{kind}": build_plot(kind, data) for kind in ("before", "sd", "ci95")}
    plots["bar_uncertainty"] = build_comparison(data)
    for name, plot in plots.items():
        mp.assert_valid(plot.spec)
        assert mp.Plot.from_json(plot.to_json()).spec == plot.spec
        mp.save_spec(plot.spec, destination / f"{name}.mplot.json")
        for fmt in ("png", "svg"):
            plt.close(plot.save(str(destination / f"{name}.{fmt}")))
        print(f"OK {name}: PNG, SVG, editable JSON; n={N}; seed=2026")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "images")
    render_examples(parser.parse_args().out)
