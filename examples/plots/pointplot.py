import mudplot as mp

# No manual summary table: one observation per row.
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
    .pointplot("dose", "response", group="cell", errorbar="se", dodge=0.18)
    .labels(x="Dose", y="Response (a.u.)", title="Raw replicates: mean ± sample SE")
    .legend(title="Cell line", location="upper left")
    .ylim(0, 2.8)
    .size(5.2, 3.5)
)
