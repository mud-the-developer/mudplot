import mudplot as mp

plot = (
    mp.plot(
        {
            "x": [1, 3],
            "y": [1, 2],
            "z": [0, 4],
            "dx": [1, 1],
            "dy": [1, 1],
            "dz": [3, -2],
        }
    )
    .projection3d()
    .bar3d("x", "y", "z", spatial={"dx": "dx", "dy": "dy", "dz": "dz"}, color="#317885")
    .labels(x="Easting", y="Northing")
    .zlabel("Height", limits=[0, 5])
).size(5.8, 4.5)
