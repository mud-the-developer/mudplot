"""Weighted pairwise comparisons and paired marginal distributions."""

from pathlib import Path

import mudplot as mp


def figures():
    raw = {
        "Dose": [0, 0, 1, 1, 1, 2, 2, 2, None, 3],
        "Response": [0, 0, 1, 1, 1, 2, 2, None, 3, 4],
        "Delay": [0.1, 0.3, None, 1.2, 1.6, 2.0, None, 3.0, 3.4, 4.3],
        "Arm": ["A", "A", "A", "A", "B", "B", "B", "B", "B", "B"],
        "Weight": [1, 3, 2, 1, 3, 2, 4, 2, 3, 0],
    }
    pair = (
        mp.plot(raw)
        .size(11, 9)
        .pair(
            ["Dose", "Response", "Delay"],
            corner=True,
            weights="Weight",
            semantics=mp.SemanticSpec(hue="Arm", hue_order=["A", "B"]),
            diag_kind="ecdf",
            diag_stat="probability",
            complementary=True,
        )
        .suptitle("Weighted pairwise comparisons")
    )
    joint = (
        mp.plot(raw)
        .size(10, 7)
        .hexbin("Dose", "Response", gridsize=5, mincnt=2, alpha=0.78)
        .xlim(-0.25, 2.25)
        .ylim(-0.45, 2.45)
        .legend(location="lower right")
        .joint(group="Arm", weights="Weight", bins=5, marginal_stat="count")
        .suptitle("Paired mass and weighted marginals")
    )
    return pair, joint


def main():
    for name, plot in zip(("weighted_pair", "weighted_joint"), figures(), strict=True):
        Path(f"{name}.mplot.json").write_text(plot.to_json(), encoding="utf-8")
        plot.save(f"{name}.png")


if __name__ == "__main__":
    main()
