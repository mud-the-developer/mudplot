"""Reserved empty facet frames and a common selected numeric size domain."""

import mudplot as mp


def build_plot() -> mp.Plot:
    data = {
        "category": ["A", "A", "B", "B"] * 2,
        "response": [1, 1, 1.1, 1.1, 1.8, 1.8, 1.9, 1.9],
        "mass": [0, 5, 10, 5, 10, None, 0, 5],
        "group": ["u", "v"] * 4,
        "cohort": ["left"] * 4 + ["right"] * 4,
    }
    return (
        mp.plot(data)
        .swarmplot(
            "category",
            "response",
            group="group",
            dodge=0,
            semantics={"size": "mass", "sizes": [4, 10]},
        )
        .labels(x="Category", y="Response (a.u.)")
        .facet(
            col="cohort",
            col_order=["empty", "left", "right"],
            col_wrap=2,
            share_y="none",
        )
        .size(8, 6)
    )
