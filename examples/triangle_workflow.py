"""Export a small explicit triangle workflow with one intentionally masked face."""

import sys
from pathlib import Path

import mudplot as mp


def build():
    data = {
        "x": [0, 6, 0, 1, 2],
        "y": [0, 0, 6, 1, 2],
        "signal": [0, 3, 6, 9, 12],
        "height": [1, 2, 3, 5, 7],
    }
    faces = [[0, 1, 3], [1, 2, 4], [2, 3, 4], [3, 1, 4], [2, 0, 3]]
    mask = [False, True, False, False, False]
    topology = mp.TriangulationSpec(faces, mask)
    vertex = mp.TriangulationSpec(faces, mask, "vertex")
    face = mp.TriangulationSpec(faces, mask, "face", [4, 6, 8, 3, 5])
    p = mp.plot(data).theme("paper").size(8, 6.4).layout(2, 2)
    p.triplot("x", "y", triangulation=topology, color="#304552")
    p.tripcolor(
        "x",
        "y",
        triangulation=face,
        colorbar=True,
        clabel="Signal per face (mV)",
        panel=1,
    )
    p.tricontourf(
        "x",
        "y",
        "signal",
        triangulation=vertex,
        levels=[0, 3, 6, 9, 12],
        colorbar=True,
        clabel="Vertex signal (mV)",
        panel=2,
    )
    p.projection3d(panel=3).trisurf("x", "y", "height", triangulation=topology, panel=3)
    for i, title in enumerate(
        (
            "Visible edges",
            "Explicit face values",
            "Vertex signal bands",
            "Triangulated surface",
        )
    ):
        p.labels(x="Easting (m)", y="Northing (m)", title=title, panel=i)
    return p.zlabel("Height (m)", panel=3)


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    p = build()
    (out / "triangles.mplot.json").write_text(p.to_json(), encoding="utf-8")
    for suffix in ("png", "svg", "pdf"):
        p.save(str(out / f"triangles.{suffix}"))
