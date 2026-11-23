"""Finite segment, asymmetric uncertainty and native band examples."""

import sys
from pathlib import Path

import mudplot as mp


def build():
    data = {
        "time": [0, 1, 2, 3, 4, 5, 6],
        "signal": [1.3, 1.7, 2.0, None, 2.4, 2.1, 2.6],
        "low": [1.1, 1.4, 1.6, None, 2.0, 1.7, 2.3],
        "high": [1.6, 2.0, 2.4, None, 2.8, 2.4, 3.0],
        "before": [0.12, 0.15, 0.22, 0, 0.2, 0.12, 0.18],
        "after": [0.19, 0.30, 0.15, 0, 0.16, 0.19, 0.18],
        "lower_error": [0.14, 0.21, 0.12, 0, 0.26, 0.13, 0.18],
        "upper_error": [0.24, 0.10, 0.23, 0, 0.13, 0.19, 0.14],
        "show": [True, True, True, False, True, True, True],
    }
    body = mp.ComponentStyleSpec(color="#5aa8ba", alpha=0.32, line_width=0)
    outline = mp.ComponentStyleSpec(
        edge_color="#223c46",
        face_color="#d9f1ec",
        marker="s",
        marker_size=5,
        marker_edge_width=0.9,
    )
    return (
        mp.plot(data)
        .size(10, 4.3)
        .layout(1, 2)
        .vspan(
            mp.SpanSpec(2.7, 3.3),
            native_style=mp.ComponentStyleSpec(color="#eee4d2", alpha=0.55),
        )
        .band(
            "time",
            "low",
            "high",
            fill=mp.FillSpec(where="show", step="mid"),
            native_style=body,
        )
        .errorbar(
            "time",
            "signal",
            magnitudes=mp.ErrorMagnitudesSpec(
                x=["before", "after"], y=["lower_error", "upper_error"]
            ),
            native_style=outline,
        )
        .hlines(
            mp.SegmentSpec([1.1], [0], [6]),
            native_style=mp.ComponentStyleSpec(
                color="#587074", line_style="--", line_width=1
            ),
        )
        .labels(x="Time (s)", y="Signal (mV)", title="Asymmetric measurement intervals")
        .band(
            "time",
            "low",
            "high",
            orient="h",
            fill=mp.FillSpec(where="show"),
            native_style=body,
            panel=1,
        )
        .labels(x="Signal (mV)", y="Time (s)", title="Paired horizontal bands", panel=1)
    )


if __name__ == "__main__":
    dest = Path(sys.argv[1])
    dest.mkdir(parents=True, exist_ok=True)
    plot = build()
    (dest / "planar.mplot.json").write_text(plot.to_json(), encoding="utf-8")
    for extension in ("png", "svg", "pdf"):
        plot.save(dest / f"planar.{extension}")
