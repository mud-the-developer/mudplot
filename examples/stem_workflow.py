"""Horizontal stem plot of synthetic detections, rendered in three formats."""

import sys
from pathlib import Path

import mudplot as mp


def build():
    return (
        mp.plot(
            {
                "time": [
                    "2026-01-02T00:00:00Z",
                    "2026-01-06T00:00:00Z",
                    "2026-01-02T00:00:00Z",
                ],
                "response": [2.8, 1.4, 2.0],
                "channel": ["Reference", "Test", "Test"],
                "confidence": [0.8, 0.6, 0.4],
            }
        )
        .theme("paper")
        .stem(
            "time",
            "response",
            orient="h",
            baseline=0.5,
            semantics=mp.SemanticSpec(
                hue="channel",
                style="channel",
                markers=["o", "s"],
                dashes=["-", "--"],
                size="confidence",
                sizes=[1, 2.5],
                legend=False,
            ),
        )
        .date_axis("y")
        .labels(x="Response (a.u.)", y="Detection date", title="Synthetic detections")
        .size(5, 3.2)
    )


if __name__ == "__main__":
    directory = Path(sys.argv[1])
    directory.mkdir(parents=True, exist_ok=True)
    plot = build()
    (directory / "stem-workflow.mplot.json").write_text(
        plot.to_json(), encoding="utf-8"
    )
    for extension in ("png", "svg", "pdf"):
        plot.save(str(directory / f"stem-workflow.{extension}"))
