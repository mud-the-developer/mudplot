import mudplot as mp

data = {
    "position": [0, 1, 2, 3, 4, 5],
    "response": [0.5, 1.2, -0.4, 0.8, -0.2, 0.1],
}
plot = (
    mp.plot(data)
    .stem("position", "response", baseline=0, marker_size=5, line_width=1.2)
    .labels(x="Position", y="Response (a.u.)", title="Synthetic discrete observations")
    .legend(show=False)
    .size(4.5, 3.5)
)
