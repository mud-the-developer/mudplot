import mudplot as mp

plot = (
    mp.plot()
    .hlines(mp.SegmentSpec([1, 2, 3], [0, 1, 2], [5, 4, 6]))
    .labels(x="Time (s)", y="Level")
).size(4.8, 3.6)
