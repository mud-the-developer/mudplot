import mudplot as mp

source = {
    "x": [0, 0, 1, 2, 2, 3],
    "y": [0, 1, 1, 0, 2, 3],
    "weight": [1, 3, 2, 1, 2, 3],
    "row_id": ["a", "b", "c", "d", "e", "f"],
}
plot = (
    mp.plot(source)
    .ecdf2d(
        "x",
        "y",
        weights="weight",
        stat="percent",
        complementary=True,
        bounds=[[-0.5, 3.5], [-0.5, 3.5]],
        query_x=[0.5, 1.5],
        query_y=[0.5, 1.5],
        colorbar=True,
        clabel="Strict OR mass, %",
    )
    .labels(x="Original x", y="Original y", title="Paired empirical OR complement")
    .size(4.5, 3.3)
)
