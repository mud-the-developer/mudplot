"""Synthetic shared raw hue across points, curves, counts and histogram bodies."""

from argparse import ArgumentParser
from pathlib import Path

import mudplot as mp


def build():
    data = {
        "x": [0.1, 0.2, 0.3, 1.5, 1.8, 4.0],
        "y": [1, 2, 3, 4, 5, 6],
        "category": ["A", "A", "A", "B", "B", "B"],
        "hue": [10, 10, 20, 20, 20, 10],
        "mass": [1, 3, 2, 3, 1, 9],
        "precision": [1, 2, 1, 1, 2, 1],
        "method": ["A", "B", "A", "A", "B", "A"],
    }
    roles = mp.SemanticSpec(
        scale_id="measurement",
        hue="hue",
        hue_kind="numeric",
        hue_norm=[0, 30],
        size="precision",
        sizes=[1.5, 3],
        style="method",
    )
    p = mp.plot(data).theme("publication").size(11, 8).layout(2, 2)
    p.scatter(
        "x",
        "y",
        semantics=roles,
        colorbar=True,
        clabel="Raw reading",
        edge_color="#30343b",
        line_width=0.35,
    )
    p.labels(title="Observed points", x="Measurement", y="Response")
    p.line("x", "y", semantics=roles, panel=1)
    p.labels(title="Supplied trajectories", x="Measurement", y="Response", panel=1)
    p.countplot("category", weights="mass", semantics=roles, panel=2)
    p.labels(title="Weighted count bodies", x="Category", y="Mass", panel=2)
    p.hist(
        "x",
        bins=[0, 1, 3],
        stat="density",
        weights="mass",
        semantics=roles,
        multiple="dodge",
        panel=3,
    )
    p.labels(
        title="Density before dodge",
        x="Measurement",
        y="Density per input unit",
        panel=3,
    )
    return p.shared_guides(
        [mp.SharedGuideSpec("measurement", location="outside right")]
    )


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path)
    out = parser.parse_args().out
    out.mkdir(parents=True, exist_ok=True)
    p = build()
    (out / "semantic-bodies.mplot.json").write_text(p.to_json(), encoding="utf-8")
    from matplotlib import pyplot as plt

    for fmt in ("png", "svg", "pdf"):
        plt.close(p.save(str(out / f"semantic-bodies.{fmt}")))
