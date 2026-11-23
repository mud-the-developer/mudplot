import mudplot as mp

plot = (
    mp.plot()
    .matrix("z", [[0, -4, 2, 0], [3, None, 0, 5], [0, 0, -3, 0]])
    .spy("z", grid={"threshold": 2})
    .labels(x="Column", y="Row")
).size(4.8, 3.6)
