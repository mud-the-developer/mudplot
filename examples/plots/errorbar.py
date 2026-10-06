import mudplot as mp

data = {
    "time": [0, 1, 2, 3, 4],
    "mean": [1.0, 1.35, 1.72, 1.88, 2.15],
    "error": [0.08, 0.12, 0.1, 0.15, 0.13],
}
plot = (
    mp.plot(data)
    .errorbar("time", "mean", yerr="error", capsize=4, marker="o", marker_size=5)
    .labels(x="Time (h)", y="Mean ± supplied error", title="Measured uncertainty")
    .size(4.5, 3.2)
)
