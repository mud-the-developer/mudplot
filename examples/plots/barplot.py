import mudplot as mp

# Each condition/cell contains three raw replicates, not a supplied mean.
data = {
    "dose": (["Control"] * 3 + ["Low"] * 3 + ["High"] * 3) * 3,
    "response": [
        0.9,
        1.0,
        1.1,
        1.2,
        1.4,
        1.6,
        1.7,
        1.9,
        2.1,
        0.8,
        0.9,
        1.0,
        1.3,
        1.6,
        1.9,
        2.0,
        2.3,
        2.6,
        1.0,
        1.1,
        1.2,
        1.1,
        1.3,
        1.5,
        1.4,
        1.7,
        2.0,
    ],
    "cell": ["A"] * 9 + ["B"] * 9 + ["C"] * 9,
}
plot = (
    mp.plot(data)
    .theme("publication")
    .encoding(redundant_encoding=False)
    .barplot(
        "dose",
        "response",
        group="cell",
        errorbar=("ci", 95),
        seed=42,
        bar_width=0.72,
        edge_color="white",
        line_width=0.5,
    )
    .labels(
        x="Dose",
        y="Response (a.u.)",
        title="Raw replicates: mean with 95% bootstrap CI",
    )
    .legend(title="Cell line", location="upper left")
    .ylim(0, 3.0)
    .size(5.2, 3.5)
)
