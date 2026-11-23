"""Literal native paths and notes with independent coordinate frames."""

import sys
from pathlib import Path

import mudplot as mp


def build():
    paths = mp.PatchSpec(
        "path",
        [
            [0.7, 0.5],
            [2, 3.7],
            [3.1, 2.3],
            [3.8, 3.3],
            [4.9, 1.2],
            [5.5, 0.6],
            [0.7, 0.5],
        ],
        codes=["MOVETO", "CURVE3", "CURVE3", "CURVE4", "CURVE4", "CURVE4", "CLOSEPOLY"],
    )
    none = mp.TickSpec(locator=mp.LocatorSpec(kind="none"))
    return (
        mp.plot()
        .size(11, 5)
        .layout(1, 2)
        .xlim(0, 6)
        .ylim(0, 4)
        .patch(
            paths,
            native_style=mp.ComponentStyleSpec(
                color="#69a9b7", edge_color="#30515c", line_width=1.25
            ),
            path_effects=[mp.PathEffectSpec("shadow", offset=[2, -2], alpha=0.23)],
        )
        .vspan(
            mp.SpanSpec(2.8, 3.3, [0.0, 0.15]),
            native_style=mp.ComponentStyleSpec(
                color="#d7b274", alpha=0.5, line_width=0
            ),
        )
        .annotate(
            "Measured transition",
            [0.12, 0.83],
            to=[3.1, 2.3],
            annotation=mp.AnnotationSpec(
                at_coordinates="axes", to_coordinates="data", arrow="filled"
            ),
            color="#233941",
            path_effects=[mp.PathEffectSpec("stroke", color="white", width=2)],
        )
        .labels(
            x="Position (m)",
            y="Amplitude",
            title="Native shape and observed transition",
        )
        .ticks("x", none, panel=1)
        .ticks("y", none, panel=1)
        .table(
            mp.LiteralTableSpec(
                [["2.3", "m"], ["4", "samples"], ["Reviewed", "yes"]],
                [0.09, 0.28, 0.82, 0.47],
                row_labels=["Span", "Run", "QC"],
                column_labels=["Value", "Unit / state"],
                font_size=10,
                header_color="#e1ecef",
                cell_color="#f7faf9",
                text_color="#233941",
            ),
            panel=1,
        )
        .text(
            "Companion notes",
            [0.09, 0.83],
            annotation=mp.AnnotationSpec(at_coordinates="axes", font_size=12),
            color="#233941",
            panel=1,
        )
        .text(
            "Supplied geometry; no fitted interpolation",
            [0.52, 0.025],
            annotation=mp.AnnotationSpec(
                at_coordinates="figure", align="center", font_size=9
            ),
            color="#4f6970",
            panel=1,
        )
        .labels(title="Literal measurement record", panel=1)
    )


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    p = build()
    (out / "annotations.mplot.json").write_text(p.to_json(), encoding="utf-8")
    for fmt in ("png", "svg", "pdf"):
        p.save(out / f"annotations.{fmt}")
