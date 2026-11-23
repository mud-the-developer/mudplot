"""One retained dataset maps hue, physical size and style across four families."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mudplot as mp


def build_plot() -> mp.Plot:
    data = {
        "predictor": [0, 1, 2, 0, 1, 2],
        "response": [1, 1, 2, 1, 4, 4],
        "category": ["alpha", "beta", "alpha", "alpha", "beta", "alpha"],
        "temperature": [-10] * 3 + [10] * 3,
        "mass": [1] * 3 + [3] * 3,
        "method": ["A"] * 3 + ["B"] * 3,
        "weight": [1, 2, 1, 2, 1, 1],
    }
    plot = mp.plot(data).theme("publication").layout(2, 2).size(13, 8)
    semantics = mp.SemanticSpec(
        scale_id="four-families",
        hue="temperature",
        hue_kind="numeric",
        hue_norm=[-10, 10],
        size="mass",
        size_norm=[1, 3],
        sizes=[3, 7],
        style="method",
        markers=["o", "s"],
    )
    common = {
        "semantics": semantics,
        "cmap_kind": "diverging",
        "colorbar": True,
        "clabel": "Temperature (degrees C)",
    }
    plot.scatter(
        "predictor", "response", edge_color="black", line_width=0.5, panel=0, **common
    )
    plot.lineplot(
        "predictor", "response", weights="weight", errorbar=None, panel=1, **common
    )
    plot.stripplot(
        "category", "response", dodge=0.8, strip={"seed": 17}, panel=2, **common
    )
    plot.ecdf("response", weights="weight", marker_size=4, panel=3, **common)
    titles = [
        "Scatter: diameter in pt",
        "Estimate: stroke in pt",
        "Strip: diameter in pt",
        "Weighted ECDF: stroke in pt",
    ]
    for panel, title in enumerate(titles):
        plot.labels(title=title, panel=panel)
    plot.labels(x="Predictor", y="Observed response", panel=0)
    plot.labels(x="Predictor", y="Weighted mean response", panel=1)
    plot.labels(x="Category", y="Observed response", panel=2)
    plot.labels(x="Observed response", y="Empirical proportion", panel=3)
    return plot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="docs/images")
    directory = Path(parser.parse_args().directory)
    directory.mkdir(parents=True, exist_ok=True)
    plot = build_plot()
    mp.assert_valid(plot.spec)
    before = plot.to_json()
    assert mp.Plot.from_json(before).spec == mp.apply(plot.action_log) == plot.spec
    for extension in ("png", "svg", "pdf"):
        plt.close(plot.save(str(directory / f"shared_semantic_families.{extension}")))
    mp.save_spec(plot.spec, directory / "shared_semantic_families.mplot.json")
    assert before == plot.to_json()
    print(
        "PASS shared scatter/line/strip/ECDF roles, units, weighted ties, "
        "source/JSON/actions"
    )


if __name__ == "__main__":
    main()
