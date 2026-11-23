"""Synthetic measurements: transform samples, then use native statistics and moves."""

from argparse import ArgumentParser
from pathlib import Path

import mudplot as mp


def build():
    source = {
        "dose": [1, 1, 10, 10, 1, 1, 10, 10],
        "response": [1, 10, 100, 10, 10, 100, 100, 1000],
        "hue": ["Control"] * 4 + ["Treatment"] * 4,
        "mass": [1, 3, 2, 1, 2, 1, 1, 3],
    }
    log_response = [mp.TransformSpec("y", "log")]
    log_observation = [mp.TransformSpec("x", "log")]
    plot = mp.plot(source).theme("publication").size(12, 8).layout(2, 2)
    plot.pointplot(
        "dose",
        "response",
        estimator="mean",
        errorbar=None,
        weights="mass",
        group="hue",
        native_scale=True,
        dodge=0.4,
        transforms=log_response,
    ).axis_scale("x", "log", options={"base": 10})
    plot.labels(
        title="Weighted means in log coordinates", x="Dose (native)", y="log10 response"
    )
    plot.hist(
        "response",
        weights="mass",
        group="hue",
        stat="density",
        bins=[0, 1, 2, 3],
        multiple="dodge",
        element="step",
        transforms=log_observation,
        panel=1,
    ).labels(title="Density then raw-bin dodge", x="log10 response", panel=1)
    plot.kde(
        "response",
        weights="mass",
        group="hue",
        kernel="epanechnikov_product",
        transforms=log_observation,
        panel=2,
    ).labels(title="Named kernel in transformed space", x="log10 response", panel=2)
    plot.ecdf(
        "response",
        weights="mass",
        group="hue",
        transforms=log_observation,
        panel=3,
    ).labels(
        title="Weighted empirical mass", x="log10 response", y="Proportion", panel=3
    )
    return plot


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "output", type=Path, help="Directory for the editable example and exports"
    )
    out = parser.parse_args().output
    out.mkdir(parents=True, exist_ok=True)
    plot = build()
    (out / "coordinate-pipeline.mplot.json").write_text(
        plot.to_json(), encoding="utf-8"
    )
    from matplotlib import pyplot as plt

    for extension in ("png", "svg", "pdf"):
        plt.close(plot.save(str(out / f"coordinate-pipeline.{extension}")))


if __name__ == "__main__":
    main()
