import mudplot as mp

# Synthetic replicates. CI is pointwise at each predictor, not simultaneous.
data = {
    "time": [1, 1, 2, 2, 4, 4, 8, 8] * 2,
    "response": [
        1,
        1.4,
        1.5,
        2,
        2.5,
        3.2,
        3.8,
        4.7,
        1.4,
        1.8,
        2,
        2.4,
        3.2,
        3.6,
        4.7,
        5.6,
    ],
    "method": ["Control"] * 8 + ["Treatment"] * 8,
}
plot = (
    mp.plot(data)
    .theme("publication")
    .lineplot("time", "response", group="method", errorbar="ci", n_boot=251, seed=17)
    .labels(x="Time (h)", y="Response", title="Means / pointwise 95% bootstrap CI")
    .legend(title="Method", location="upper left")
    .size(5.4, 3.5)
)
