"""Shared raw hue domains with physical-size guides, exact constants/extremes."""

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
        "x": [0, 1, 2, 0, 1, 2],
        "value": [1, 2, 3, 3, 2, 4],
        "temperature": [-10] * 3 + [10] * 3,
        "mass": [1] * 3 + [3] * 3,
        "constant": [7] * 6,
        "extreme": [-1e308] * 3 + [1e308] * 3,
    }
    p = mp.plot(data).theme("publication").layout(2, 2).size(14, 8)
    mapping = mp.SemanticSpec(
        scale_id="shared",
        hue="temperature",
        hue_kind="numeric",
        hue_norm=[-10, 10],
        size="mass",
        sizes=[2, 5],
    )
    p.scatter(
        "x",
        "value",
        semantics=mapping,
        colorbar=True,
        cmap_kind="diverging",
        clabel="Temperature (degrees C)",
        edge_color="black",
        line_width=0.5,
        panel=0,
    )
    p.labels(x="Predictor", y="Observed response", title="Diameter in points", panel=0)
    p.lineplot(
        "x",
        "value",
        semantics=mapping,
        errorbar=None,
        colorbar=True,
        cmap_kind="diverging",
        clabel="Temperature (degrees C)",
        panel=1,
    )
    p.labels(x="Predictor", y="Mean response", title="Stroke width in points", panel=1)
    p.scatter(
        "x",
        "value",
        semantics={"hue": "constant", "hue_kind": "numeric"},
        colorbar=True,
        clabel="Constant: exact midpoint swatch",
        panel=2,
    )
    p.labels(x="Predictor", y="Observed response", title="No invented range", panel=2)
    p.scatter(
        "x",
        "value",
        semantics={"hue": "extreme", "hue_kind": "numeric"},
        cmap_kind="diverging",
        colorbar=True,
        clabel="Raw signed domain",
        panel=3,
    )
    p.labels(x="Predictor", y="Observed response", title="Finite extreme hue", panel=3)
    return p


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="docs/images")
    directory = Path(parser.parse_args().directory)
    directory.mkdir(parents=True, exist_ok=True)
    p = build_plot()
    mp.assert_valid(p.spec)
    before = p.to_json()
    assert mp.Plot.from_json(before).spec == mp.apply(p.action_log) == p.spec
    for extension in ("png", "svg", "pdf"):
        plt.close(p.save(str(directory / f"semantic_colourbars.{extension}")))
    mp.save_spec(p.spec, directory / "semantic_colourbars.mplot.json")
    assert before == p.to_json()
    print("PASS shared hue/size, explicit outline, signed extremes, constant swatch")


if __name__ == "__main__":
    main()
