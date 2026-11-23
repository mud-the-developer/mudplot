import mudplot as mp

plot = (
    mp.plot({"x": [1, 2, 3], "y": [1, 2, 1], "u": [5, -10, 8], "v": [2, 4, -6]})
    .barbs("x", "y", "u", "v", vector=mp.VectorSpec(length=7))
    .xlim(0, 4)
    .ylim(0, 3)
    .labels(x="Easting (m)", y="Northing (m)")
).size(4.8, 3.6)
