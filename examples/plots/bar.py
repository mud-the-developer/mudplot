import mudplot as mp

data = {
    "dose": ["Control", "Low", "High"] * 3,
    "response": [1.0, 1.4, 1.9, 0.9, 1.6, 2.3, 1.1, 1.3, 1.7],
    "sd": [0.10, 0.13, 0.16, 0.09, 0.14, 0.18, 0.11, 0.12, 0.15],
    "cell": ["A"] * 3 + ["B"] * 3 + ["C"] * 3,
}
plot = (
    mp.plot(data)
    .theme("publication")
    .encoding(redundant_encoding=False)  # clean fills; omit for hatch encoding
    .bar(
        "dose",
        "response",
        group="cell",
        yerr="sd",
        bar_width=0.72,
        edge_color="white",
        line_width=0.5,
    )
    .labels(x="Dose", y="Response (a.u.)", title="Mean ± SD")
    .legend(title="Cell line", location="upper left")
    .ylim(0, 2.8)
    .size(5.2, 3.5)
)
