import mudplot as mp

grid = {"x_coords": [0, 1, 4], "y_coords": [0, 2, 3]}
plot = (
    mp.plot()
    .matrix("z", [[0, 1, 4], [1, 2, 5], [2, 3, 6]])
    .projection3d()
    .contour3d("z", spatial=grid, levels=[1, 3, 5])
    .labels(x="Easting", y="Northing")
    .zlabel("Height")
).size(5.8, 4.5)
