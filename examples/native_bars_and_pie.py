"""Aligned signed bar segments and annotated wedges from one raw table."""

import sys
from pathlib import Path

import mudplot as mp


def build():
    data = {
        "Station": ["North", "South", "North", "South", "North", "South"],
        "Phase": ["A", "A", "B", "B", "C", "C"],
        "Delta": [2, -3, 4, -2, -1, 5],
        "Reference": [10, 20, 10, 20, 10, 20],
        "Slice": ["New", "Reused", "Repair", None, None, None],
        "Items": [24, 38, 18, None, None, None],
    }
    faces = ["#579aad", "#50a795", "#d38957"]
    wedge = [
        mp.ComponentStyleSpec(color=c, edge_color="white", line_width=1.6)
        for c in faces
    ]
    return (
        mp.plot(data)
        .size(11, 5)
        .layout(1, 2)
        .xlim(7.8, 27.2)
        .barh(
            "Station",
            "Delta",
            group="Phase",
            bar_width=0.53,
            geometry=mp.BarGeometrySpec(
                bottom="Reference", multiple="stack", value_format="g"
            ),
        )
        .labels(
            x="Observed position (m)", title="Signed changes from station reference"
        )
        .legend(location="upper left")
        .pie(
            "Slice",
            "Items",
            panel=1,
            geometry=mp.PieGeometrySpec(
                start_angle=98,
                width=0.43,
                value="raw",
                value_format=".0f",
                value_distance=0.78,
                annotations=[None, "Largest share", None, None, None, None],
                styles=[*wedge, None, None, None],
                label_distance=0.40,
            ),
        )
        .labels(title="Inventory (original item counts)", panel=1)
        .legend(False, panel=1)
    )


if __name__ == "__main__":
    dest = Path(sys.argv[1])
    dest.mkdir(parents=True, exist_ok=True)
    p = build()
    (dest / "bar-pie.mplot.json").write_text(p.to_json(), encoding="utf-8")
    for fmt in ("png", "svg", "pdf"):
        p.save(dest / f"bar-pie.{fmt}")
