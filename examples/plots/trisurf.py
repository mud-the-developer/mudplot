import mudplot as mp

data = {"x": [0, 2, 0, 2, 1], "y": [0, 0, 2, 2, 1], "z": [0, 2, 1, 4, 2]}
faces = [[0, 1, 4], [1, 3, 4], [3, 2, 4], [2, 0, 4]]
plot = (
    mp.plot(data)
    .projection3d()
    .trisurf("x", "y", "z", triangulation=mp.TriangulationSpec(faces))
    .labels(x="Easting", y="Northing")
    .zlabel("Height")
).size(5.8, 4.5)
