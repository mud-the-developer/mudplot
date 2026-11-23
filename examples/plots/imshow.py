import mudplot as mp

plot = (
    mp.plot()
    .matrix("z", [[1, 3, 2], [4, 6, 5]])
    .imshow("z", grid={"extent": [0, 6, 0, 4], "origin": "lower"})
    .labels(x="Easting (m)", y="Northing (m)")
).size(4.8, 3.6)
