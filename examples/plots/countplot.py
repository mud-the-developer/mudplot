import mudplot as mp

# Unequal sample sizes; countplot needs no y column and does not infer a CI.
data = {
    "dose": ["Control"] * 7 + ["Low"] * 6 + ["High"] * 5,
    "cell": ["A"] * 4 + ["B"] * 3 + ["A"] * 2 + ["B"] * 4 + ["A"] * 3 + ["B"] * 2,
}
plot = (
    mp.plot(data)
    .theme("publication")
    .countplot("dose", group="cell", bar_width=0.72, edge_color="white", line_width=0.5)
    .labels(x="Dose", y="Observations", title="Raw observation counts")
    .legend(title="Cell line", location="upper right")
    .ylim(0, 5)
    .size(5.2, 3.5)
)
