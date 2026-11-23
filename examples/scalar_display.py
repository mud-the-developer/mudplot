"""Export a locally styled figure with a shared raw-voltage calibration."""

import sys
from pathlib import Path

import mudplot as mp


def build():
    cfg = {
        "colors": ["#16384b", "#4b9ea1", "#f2d587"],
        "under": "#753145",
        "over": "#485225",
        "bad": "#adb6bf",
        "vmin": 0,
        "vmax": 10,
        "scale_id": "voltage",
    }
    p = (
        mp.plot(
            {
                "x": [1, 2, 3, 4, 5],
                "y": [1.8, 2.6, 1.4, 2.2, 2.9],
                "mv": [-2, 2.5, 5, 12, None],
            }
        )
        .theme("paper")
        .context("paper")
        .layout(1, 2)
        .size(9.8, 4.7)
        .matrix("sample", [[-2, 2.5, 5], [12, None, 9]])
    )
    p.scatter(
        "x",
        "y",
        c="mv",
        colorbar=True,
        clabel="Probe signal (mV)",
        marker_size=9,
        edge_color="#253845",
        line_width=0.55,
        scalar_display={
            **cfg,
            "colorbar_options": {
                "location": "bottom",
                "ticks": [0, 5, 10],
                "extend": "both",
            },
        },
    )
    p.labels(x="Distance (m)", y="Depth (m)", title="Point measurements")
    p.xlim(0.5, 5.5).ylim(0.85, 3.4)
    p.pcolormesh(
        "sample",
        grid={
            "x": [0, 1, 3, 5],
            "y": [0, 1, 3],
            "position": "edges",
            "shading": "flat",
        },
        scalar_display={
            **cfg,
            "colorbar_options": {
                "location": "right",
                "ticks": [0, 2.5, 10],
                "extend": "both",
            },
        },
        colorbar=True,
        clabel="Cell signal (mV)",
        panel=1,
    )
    p.labels(
        x="Distance (m)", y="Depth (m)", title="Rectilinear cell measurements", panel=1
    )
    return p


if __name__ == "__main__":
    target = Path(sys.argv[1])
    target.mkdir(parents=True, exist_ok=True)
    plot = build()
    (target / "scalar-display.mplot.json").write_text(plot.to_json(), encoding="utf-8")
    for name in ("png", "svg", "pdf"):
        plot.save(str(target / f"scalar-display.{name}"))
