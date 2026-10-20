import mudplot as mp

data = {"start": [0.0, 0.5, 2.4, 2.8], "duration": [1.2, 0.5, 1.5, 0.6]}
plot = (
    mp.plot(data)
    .broken_barh("start", "duration", bottom=1, height=0.7, alpha=0.7)
    .labels(
        x="Interval position (a.u.)", y="Raw band", title="Synthetic interval overlaps"
    )
    .legend(show=False)
    .size(4.5, 3.5)
)
