import mudplot as mp

grid = {"x_coords": [0, 1, 4], "y_coords": [0, 2, 3]}
plot = (
    mp.plot()
    .matrix("z", [[0, 1, 4], [1, 2, 5], [2, 3, 6]])
    .projection3d()
    .contourf3d("z", spatial={**grid, "offset": 0}, levels=[0, 2, 4, 6])
    .labels(x="Easting", y="Northing")
    .zlabel("Projection plane", limits=[0, 3])
).size(5.8, 4.5)
