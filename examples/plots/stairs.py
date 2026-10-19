import mudplot as mp

data = {"height": [2.0, 1.0, 3.0, -0.5]}
plot = (
    mp.plot(data)
    .stairs("height", [0, 1, 2, 4, 5], baseline=0, line_width=1.4)
    .labels(x="Bin edges", y="Supplied height", title="Synthetic pre-binned values")
    .legend(show=False)
    .size(4.5, 3.5)
)
