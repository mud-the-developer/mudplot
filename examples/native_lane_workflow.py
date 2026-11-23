"""Export two native views of synthetic sensor activity."""

import sys
from pathlib import Path

import mudplot as mp


def build():
    source = {
        "time": [0, 2.0, 1.0, 2.8, 3.2],
        "duration": [0.85, 0.5, 1.5, 0.4, 0.6],
        "sensor": ["Sensor A", "Sensor B", "Sensor A", "Sensor A", "Sensor B"],
        "quality": [1, 3, 2, 3, 2],
    }
    lanes = {
        "locator": {"kind": "fixed", "values": [1, 3]},
        "formatter": {"kind": "fixed", "labels": ["Sensor A", "Sensor B"]},
    }
    clock = {"unit": "day", "origin": "2026-01-02T00:00:00Z"}
    order = ["Sensor A", "Sensor B"]
    return (
        mp.plot(source)
        .theme("paper")
        .layout(2, 1)
        .share(x="all")
        .eventplot(
            "time",
            offset=1,
            length=0.7,
            group="sensor",
            hue_order=order,
            lane_step=2,
            semantics=mp.SemanticSpec(
                hue="sensor",
                hue_order=order,
                size="quality",
                sizes=[1.25, 2.5],
                style="sensor",
                style_order=order,
                dashes=["-", "--"],
                legend=False,
            ),
        )
        .date_axis("x", **clock)
        .ticks("y", lanes)
        .labels(title="Event times")
        .broken_barh(
            "time",
            "duration",
            bottom=0.65,
            height=0.7,
            group="sensor",
            hue_order=order,
            lane_step=2,
            alpha=0.65,
            edge_color="#30343b",
            line_width=0.65,
            panel=1,
        )
        .date_axis("x", panel=1, **clock)
        .ticks("y", lanes, panel=1)
        .labels(x="Date (UTC)", title="Activity intervals", panel=1)
        .legend(show=False)
        .legend(show=False, panel=1)
        .size(6.6, 4.7)
    )


if __name__ == "__main__":
    directory = Path(sys.argv[1])
    directory.mkdir(parents=True, exist_ok=True)
    plot = build()
    (directory / "native-lanes.mplot.json").write_text(plot.to_json(), encoding="utf-8")
    for extension in ("png", "svg", "pdf"):
        plot.save(str(directory / f"native-lanes.{extension}"))
