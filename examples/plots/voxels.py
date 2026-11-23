import mudplot as mp

plot = (
    mp.plot()
    .projection3d()
    .voxels(
        spatial={
            "occupancy": [
                [[True, True], [False, True]],
                [[False, True], [False, False]],
            ],
            "x_coords": [0, 1, 3],
            "y_coords": [0, 1, 2],
            "z_coords": [0, 1, 3],
        },
        color="#39878c",
        edge_color="#254d55",
        line_width=0.6,
    )
    .labels(x="Easting", y="Northing")
    .zlabel("Height")
).size(5.8, 4.5)
