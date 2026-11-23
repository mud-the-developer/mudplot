import mudplot as mp

plot = (
    mp.plot()
    .vlines(mp.SegmentSpec([1, 3, 5], [1, 2, 1], [4, 6, 3]))
    .labels(x="Station", y="Range (m)")
).size(4.8, 3.6)
