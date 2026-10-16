import mudplot as mp

plot = (
    mp.plot()
    .matrix("profiles", [[1, 2, 5], [2, 1, 4], [8, 7, 2], [9, 8, 1]])
    .clustermap(
        "profiles",
        cluster={"method": "average", "row_colors": ["#00858a"] * 2 + ["#ba4056"] * 2},
        heatmap={"xlabels": ["A", "B", "C"], "ylabels": ["N1", "N2", "S1", "S2"]},
        clabel="Response",
    )
    .labels(title="Hierarchical profiles — synthetic")
    .size(6, 5)
)
