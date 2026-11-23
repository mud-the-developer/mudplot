"""Synthetic, source-retaining regression inference and held-out diagnostics.

Run: python -m examples.regression_workflow --output-directory PATH
No external data, preprocessing, hidden outlier removal or global RNG is used.
"""

from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

import mudplot as mp
import numpy as np


def weighted_partial():
    x = np.linspace(-2, 2, 129)
    z = np.cos(np.arange(129) * 0.73)
    data = {
        "id": list(range(129)),
        "x": x,
        "z": z,
        "response": 1
        + 2 * x
        + 0.6 * x * x
        + 0.7 * z
        + 0.13 * np.sin(np.arange(129) * 0.83),
        "mass": 1 + np.arange(129) % 3,
    }
    return (
        mp.plot(data)
        .size(8, 5)
        .regplot(
            "x",
            "response",
            degree=2,
            weights="mass",
            confidence=95,
            regression={
                "partial": {"columns": ["z"], "reference": {"z": 0}},
                "bootstrap": {"n_boot": 99, "seed": 43},
                "components": {
                    "fit": {"color": "#075985", "line_width": 1.8},
                    "scatter": {"color": "#64748b", "marker_size": 3},
                },
            },
        )
        .labels(
            x="Predictor (a.u.)",
            y="Response at z=0 (a.u.)",
            title="Conditional polynomial and adjusted observations",
        )
    )


def robust_binary():
    x = np.linspace(-2, 2, 129)
    response = 1 + 2 * x + 0.12 * np.sin(np.arange(129) * 0.83)
    response[5] += 1
    response[101] -= 1
    binary_x = np.repeat(np.arange(-3, 4, dtype=float), 16)
    binary_y = np.concatenate(
        [np.array([1.0] * n + [0.0] * (16 - n)) for n in [3, 4, 6, 8, 10, 12, 13]]
    )
    # One shared source table, with explicit selectors for the two scientific
    # questions. Unused columns remain source, never overwritten by predictions.
    n = len(x)
    q = len(binary_x)
    data = {
        "x": np.concatenate((x, binary_x)),
        "response": np.concatenate((response, binary_y)),
        "mass": 1 + np.arange(n + q) % 3,
        "experiment": ["huber"] * n + ["binary"] * q,
    }
    plot = mp.plot(data).layout(1, 2).size(12, 4.8)
    for panel, model, selector, title, ylabel in (
        (0, "robust", "huber", "Huber with retained outliers", "Response (a.u.)"),
        (
            1,
            "logistic",
            "binary",
            "Binomial probability, paired physical cases",
            "Probability",
        ),
    ):
        plot = plot.regplot(
            "x",
            "response",
            weights="mass",
            confidence=95,
            panel=panel,
            regression={
                "model": model,
                "sampling": {
                    "train": {"experiment": selector},
                    "query": {"experiment": "absent"},
                },
                "bootstrap": {"n_boot": 19, "seed": 43},
                "components": {
                    "fit": {"color": "#0f766e", "line_width": 1.7},
                    "scatter": {"color": "#475569", "marker_size": 3},
                },
            },
        )
        plot = plot.labels(x="Predictor (a.u.)", y=ylabel, title=title, panel=panel)
    return plot


def lowess_two_stage():
    x = np.linspace(-2, 2, 97)
    z = np.cos(np.arange(97) * 0.73)
    data = {
        "x": x + 0.2 * z,
        "z": z,
        "response": 0.4 * z + np.sin(1.2 * x) + 0.05 * np.sin(np.arange(97)),
        "mass": 1 + np.arange(97) % 3,
    }
    return (
        mp.plot(data)
        .size(8, 5)
        .regplot(
            "x",
            "response",
            weights="mass",
            confidence=95,
            regression={
                "model": "lowess",
                "frac": 2 / 3,
                "iterations": 3,
                "partial": {
                    "columns": ["z"],
                    "reference": {"z": 0},
                    "method": "two_stage",
                },
                "bootstrap": {"n_boot": 19, "seed": 43},
                "components": {
                    "fit": {"color": "#92400e", "line_width": 1.8},
                    "scatter": {"color": "#64748b", "marker_size": 3},
                },
            },
        )
        .labels(
            x="Original predictor (a.u.)",
            y="Adjusted response at z=0 (a.u.)",
            title="Two-stage weighted LOWESS, not nonlinear FWL",
        )
    )


def held_out_calendar():
    n, q = 96, 32
    index = np.arange(n + q)
    x = np.linspace(-2, 2, n + q)
    z = np.cos(index * 0.73)
    origin = date(2026, 1, 1)
    # Interleave the cohorts in predictor space without inferring a random split.
    split = ["query" if i % 4 == 0 else "train" for i in range(n + q)]
    data = {
        "id": [True, 1, "duplicate", "duplicate", *range(4, n + q)],
        "date": [(origin + timedelta(days=int(i))).isoformat() for i in index],
        "response": 1 + 2 * x + 0.7 * z + 0.12 * np.sin(index * 0.83),
        "z": z,
        "mass": 1 + index % 3,
        "split": split,
    }
    return (
        mp.plot(data)
        .size(8, 6)
        .secondary_yaxis("UTC predictor")
        .date_axis("y2", timezone="UTC")
        .residplot(
            "date",
            "response",
            weights="mass",
            confidence=95,
            orient="h",
            axis="y2",
            regression={
                "partial": {"columns": ["z"], "reference": {"z": 0}},
                "sampling": {"train": {"split": "train"}, "query": {"split": "query"}},
                "bootstrap": {"n_boot": 19, "seed": 43},
                "diagnostics": {
                    "kind": "raw",
                    "trend": {
                        "model": "lowess",
                        "frac": 1,
                        "iterations": 0,
                        "style": {"color": "#9f1239", "line_width": 1.8},
                    },
                },
                "components": {
                    "scatter": {"color": "#475569", "marker_size": 4},
                    "fit": {"color": "#075985", "line_width": 1},
                },
            },
        )
        .labels(
            x="Held-out raw residual (a.u.)",
            title="Training-only fit; full independently refitted trend",
        )
        .legend(location="outside bottom")
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-directory", type=Path, default=Path("regression-workflow-output")
    )
    args = parser.parse_args()
    args.output_directory.mkdir(parents=True, exist_ok=True)
    plots = {
        "weighted_partial": weighted_partial(),
        "robust_binary": robust_binary(),
        "lowess_two_stage": lowess_two_stage(),
        "held_out_calendar": held_out_calendar(),
    }
    for name, plot in plots.items():
        (args.output_directory / f"{name}.mplot.json").write_text(
            plot.to_json(), encoding="utf-8"
        )
        for suffix in ("png", "svg", "pdf"):
            plot.save(args.output_directory / f"{name}.{suffix}")
    (args.output_directory / "meaning.json").write_text(
        json.dumps(
            {
                "synthetic": True,
                "uncertainty": "nominal pointwise paired physical cases, "
                "not simultaneous/future observations",
                "partial": "full basis/joint conditional or explicitly named "
                "two-stage; actual query nuisance",
                "source": "original columns/typed IDs/duplicates retained; "
                "no computed result store",
                "held_out": "train/query explicit; all stages refitted per replicate; "
                "actual horizontal/y2 UTC predictor",
                "resource": "actual managed/provider-reserve estimate is not "
                "process RSS or opaque native allocation guarantee",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
