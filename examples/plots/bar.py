import mudplot as mp

data = {
    "dose": ["Control", "Low", "High"] * 3,
    "response": [1.0, 1.4, 1.9, 0.9, 1.6, 2.3, 1.1, 1.3, 1.7],
    "cell": ["A"] * 3 + ["B"] * 3 + ["C"] * 3,
}
plot = (
    mp.plot(data)
    .bar("dose", "response", group="cell")
    .labels(x="Dose", y="Response", title="Grouped bars")
    .legend(title="Cell line")
    .size(4.5, 3.2)
)
