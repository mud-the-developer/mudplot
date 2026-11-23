import mudplot as mp

plot = (
    mp.plot({"t": [0, 1, 2, 3, 4], "v": [1, 2, 2.8, 2, 3.4]})
    .hspan(
        mp.SpanSpec(1.6, 2.5),
        native_style=mp.ComponentStyleSpec(color="#d6e8ea", line_width=0),
    )
    .line("t", "v", color="#225761")
    .labels(x="Time (s)", y="Signal (mV)")
).size(4.8, 3.6)
