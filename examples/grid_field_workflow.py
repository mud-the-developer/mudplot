"""Export a small synthetic native grid workflow with explicit physical axes."""

import sys
from pathlib import Path

import mudplot as mp


def build():
    plot = mp.plot().theme("paper").layout(2, 2).size(8, 6.1)
    plot.matrix("cells", [[1, None, 3], [4, 5, 6]])
    plot.pcolormesh(
        "cells",
        grid=mp.GridFieldSpec(
            x=[0, 1, 4, 8], y=[-2, 1, 5], position="edges", shading="flat"
        ),
        colorbar=True,
        clabel="Signal (mV)",
    )
    plot.labels(x="Easting (m)", y="Northing (m)", title="Masked cell mesh")
    plot.imshow(
        grid=mp.GridFieldSpec(
            pixels=[
                [[0.1, 0.5, 0.55, 1], [0.38, 0.66, 0.68, 0.5]],
                [[0.79, 0.4, 0.3, 1], [0.42, 0.45, 0.56, 1]],
            ],
            mask=[[False, False], [False, True]],
            extent=[0, 4, 0, 3],
            origin="upper",
        ),
        panel=1,
    )
    plot.labels(x="Easting (m)", y="Northing (m)", title="Direct RGBA image", panel=1)
    plot.matrix("samples", [[0, 2, 6], [0, 2, 6], [0, 2, 6]])
    plot.contour(
        "samples",
        grid=mp.GridFieldSpec(
            x=[0, 2, 7],
            y=[0, 4, 9],
            position="centers",
            label_levels=[4],
            label_format=".1f",
        ),
        levels=[1, 4],
        colorbar=False,
        panel=2,
    )
    plot.labels(
        x="Easting (m)", y="Northing (m)", title="Declared contour levels", panel=2
    )
    plot.matrix("entries", [[0, 99, -3], [2, -4, None]])
    plot.spy(
        "entries",
        grid=mp.GridFieldSpec(
            mask=[[False, True, False], [False, False, False]],
            threshold=2,
            origin="upper",
        ),
        panel=3,
    )
    return plot.labels(
        x="Column index", y="Row index", title="Entries with |value| > 2", panel=3
    )


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    plot = build()
    (out / "grid-field.mplot.json").write_text(plot.to_json(), encoding="utf-8")
    for ext in ("png", "svg", "pdf"):
        plot.save(str(out / f"grid-field.{ext}"))
