import mudplot as mp

plot = (
    mp.plot({"site": ["North", "West", "South"], "delta": [3, -2, 4]})
    .barh("site", "delta")
    .labels(x="Change (mV)", y="Site")
).size(4.8, 3.6)
