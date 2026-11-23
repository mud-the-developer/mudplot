import mudplot as mp

data = {"x": [0, 2, 0, 2, 1], "y": [0, 0, 2, 2, 1], "z": [0, 2, 1, 4, 2]}
faces = [[0, 1, 4], [1, 3, 4], [3, 2, 4], [2, 0, 4]]
plot = (
    mp.plot(data)
    .tricontour(
        "x",
        "y",
        "z",
        triangulation=mp.TriangulationSpec(faces, None, "vertex"),
        levels=[1, 2, 3],
    )
    .labels(x="Easting (m)", y="Northing (m)")
).size(4.8, 3.6)
