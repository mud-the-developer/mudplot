import mudplot as mp

grid = {"x": [0, 1, 3, 6], "y": [0, 1, 3], "position": "edges", "shading": "flat"}
plot = (
    mp.plot()
    .matrix("z", [[1, 2, 3], [4, 5, 6]])
    .pcolormesh("z", grid=grid)
    .labels(x="Easting (m)", y="Northing (m)")
).size(4.8, 3.6)
