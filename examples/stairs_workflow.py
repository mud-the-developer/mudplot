"""Export a source and target grid containing the same synthetic interval mass."""

import sys
from pathlib import Path

import mudplot as mp


def build():
    return (
        mp.plot({"mass": [4, 9]})
        .theme("paper")
        .stairs("mass", [0, 2, 5], label="Supplied intervals", line_width=1.15)
        .stairs(
            "mass",
            [0, 2, 5],
            label="Rebinned intervals",
            color="#087e82",
            line_style="--",
            line_width=1.25,
            stairs=mp.StairsSpec(rebin=mp.StairsRebinSpec([0, 1, 3, 5])),
        )
        .labels(
            x="Time (days)",
            y="Mass per interval (g)",
            title="Conservative interval rebinning",
        )
        .legend(location="upper left")
        .size(5.2, 3.5)
    )


if __name__ == "__main__":
    directory = Path(sys.argv[1])
    directory.mkdir(parents=True, exist_ok=True)
    plot = build()
    (directory / "stairs-workflow.mplot.json").write_text(
        plot.to_json(), encoding="utf-8"
    )
    for extension in ("png", "svg", "pdf"):
        plot.save(str(directory / f"stairs-workflow.{extension}"))
