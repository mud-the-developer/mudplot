import mudplot as mp

plot = (
    mp.plot(
        {"x": [1, 2], "y": [1, 2], "z": [1, 2], "u": [1, 0], "v": [0, 1], "w": [1, 1]}
    )
    .projection3d()
    .quiver3d("x", "y", "z", "u", "v", "w", vector=mp.VectorSpec(length=1))
    .xlim(0, 4)
    .ylim(0, 4)
    .labels(x="Easting", y="Northing")
    .zlabel("Height", limits=[0, 4])
).size(5.8, 4.5)
