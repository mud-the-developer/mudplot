"""Synthetic size-only swarm; sizes are mapped diameters, not observation counts."""

import mudplot as mp


def build_plot() -> mp.Plot:
    data = {
        "dose": ["A"] * 6 + ["B"] * 6,
        "response": [1, 1, 1.04, 1.04, 1.08, 1.08, 1.25, 1.25, 1.3, 1.3, 1.35, 1.35],
        "mass": [0, 2, 4, 6, 8, 10, 10, 8, 6, 4, 2, 0],
        "group": ["u", "v"] * 6,
    }
    return (
        mp.plot(data)
        .swarmplot(
            "dose",
            "response",
            group="group",
            dodge=0,
            semantics={"size": "mass", "size_norm": [0, 10], "sizes": [4, 10]},
        )
        .labels(
            x="Dose", y="Response (a.u.)", title="Synthetic size-mapped observations"
        )
        .legend(location="outside right", title="Group / numeric size")
        .size(6, 4)
    )
