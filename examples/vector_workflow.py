"""Export a synthetic four-panel native vector workflow."""

import sys
from pathlib import Path

import mudplot as mp


def build():
    source = {
        "x": [1, 3, 5, 2],
        "y": [1, 3, 2, 4],
        "z": [0, 1, 4, 2],
        "u": [2, 1, -2, 1],
        "v": [1, 2, 1, -1],
        "w": [1, 0, -1, 2],
        "speed_u": [2, 1, -2, 1],
        "speed_v": [1, 2, 1, -1],
        "group": ["North", "South", "North", "South"],
    }
    p = mp.plot(source).theme("paper").layout(2, 2).size(8.4, 6.8)
    p.quiver(
        "x",
        "y",
        "u",
        "v",
        vector=mp.VectorSpec(mode="data"),
        group="group",
        width=0.012,
    )
    p.labels(x="Easting (m)", y="Northing (m)", title="Planar displacements")
    p.barbs(
        "x",
        "y",
        "speed_u",
        "speed_v",
        vector=mp.VectorSpec(length=11, half=0.5, full=1, flag=2.5),
        color="#1b6d73",
        panel=1,
    )
    p.labels(x="Easting (m)", y="Northing (m)", title="Speed barbs (m/s)", panel=1)
    p.xlim(-1.7, 7.7, panel=1).ylim(-0.75, 6.8, panel=1)
    u = [[1, 1, 1, 1, 1] for _ in range(4)]
    v = [[0, 0, 0, 0, 0] for _ in range(4)]
    u[3][4] = v[3][4] = None
    p.matrix("flow_u", u).matrix("flow_v", v)
    p.streamplot(
        vector=mp.VectorSpec(
            x_coords=[0, 1, 2, 3, 4],
            y_coords=[0, 1, 2, 3],
            u_matrix="flow_u",
            v_matrix="flow_v",
            start_points=[[0.2, 0.4], [0.2, 1.5], [0.2, 2.5]],
            integration_direction="forward",
            density=0.5,
            arrowsize=1.1,
        ),
        color="#1b6d73",
        panel=2,
    )
    p.labels(x="Easting (m)", y="Northing (m)", title="Seeded streamlines", panel=2)
    p.projection3d(panel=3).quiver3d(
        "x",
        "y",
        "z",
        "u",
        "v",
        "w",
        vector=mp.VectorSpec(length=0.65),
        color="#284e63",
        panel=3,
    )
    p.labels(x="Easting (m)", y="Northing (m)", title="Spatial displacements", panel=3)
    return (
        p.xlim(0, 6, panel=3)
        .ylim(0, 5, panel=3)
        .zlabel("Height (m)", limits=[0, 5], panel=3)
    )


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    p = build()
    (out / "vectors.mplot.json").write_text(p.to_json(), encoding="utf-8")
    for suffix in ("png", "svg", "pdf"):
        p.save(str(out / f"vectors.{suffix}"))
