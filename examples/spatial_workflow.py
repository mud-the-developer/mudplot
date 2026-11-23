"""Save editable native 3D geometry and paper PNG, SVG and PDF exports."""

import sys
from pathlib import Path

import mudplot as mp


def build():
    x = [0, 0.8, 2.1, 4.6, 6.0]
    y = [0, 1.0, 3.1, 4.1, 5.0]
    z = [[0.65 * a + 0.2 * b + 0.085 * b * (a - 0.8) for a in x] for b in y]
    p = (
        mp.plot(
            {
                "x": [0.5, 2.7, 4.2],
                "y": [0.5, 1.8, 3.3],
                "base": [0, 3.6, 0],
                "dx": [1.25, 0.9, 1.15],
                "dy": [0.8, 1.2, 1.25],
                "dz": [3, -2.1, 4.6],
            }
        )
        .theme("paper")
        .layout(2, 3)
        .size(12.3, 8.9)
        .matrix("height", z)
    )
    grid = {"x_coords": x, "y_coords": y}
    p.projection3d().surface("height", spatial=grid, colorbar=False, alpha=0.95)
    p.projection3d(panel=1).wireframe("height", spatial=grid, color="#236c76", panel=1)
    p.projection3d(panel=2).bar3d(
        "x",
        "y",
        "base",
        spatial={"dx": "dx", "dy": "dy", "dz": "dz"},
        color="#236c76",
        panel=2,
    )
    p.projection3d(panel=3).contour3d(
        "height", levels=[1, 2, 3, 4, 5], spatial=grid, line_width=1.8, panel=3
    )
    p.projection3d(panel=4).contourf3d(
        "height",
        levels=[0, 1, 2.5, 4, 6],
        spatial={**grid, "direction": "x", "offset": 5.6},
        panel=4,
    )
    p.projection3d(panel=5).voxels(
        spatial={
            "x_coords": [0.3, 1.5, 3.3, 5.7],
            "y_coords": [0.3, 2, 4.8],
            "z_coords": [0, 1.5, 3.8],
            "occupancy": [
                [[True, True, False], [False, True, False]],
                [[False, True, False], [False, True, True]],
            ],
        },
        color="#39878c",
        edge_color="#23444c",
        line_width=0.65,
        panel=5,
    )
    titles = (
        "Nonuniform surface",
        "Full grid wires",
        "Signed bar intervals",
        "Height isolines",
        "Easting bands at x = 5.6 m",
        "Occupied cells",
    )
    for i, title in enumerate(titles):
        p.labels(x="Easting (m)", y="Northing (m)", title=title, panel=i)
        p.xlim(0, 6.1, panel=i).ylim(0, 5.1, panel=i).zlabel(
            "Height (m)", limits=[0, 7.5], panel=i
        )
        p.camera3d(
            {
                "elevation": 29,
                "azimuth": -54,
                "projection": "ortho",
                "box_aspect": [1.2, 1, 1],
                "zoom": 0.82,
            },
            panel=i,
        )
    return p


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    plot = build()
    (out / "spatial.mplot.json").write_text(plot.to_json(), encoding="utf-8")
    for suffix in ("png", "svg", "pdf"):
        plot.save(str(out / f"spatial.{suffix}"))
