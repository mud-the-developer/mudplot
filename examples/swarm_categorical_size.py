"""Categorical ranks are visual classes, not estimated counts or weights."""

import mudplot as mp


def build_plot() -> mp.Plot:
    data = {
        "dose": ["A"] * 6 + ["B"] * 6,
        "response": [1, 1, 1.04, 1.04, 1.08, 1.08, 1.25, 1.25, 1.3, 1.3, 1.35, 1.35],
        "grade": ["small", "medium", "large", "small", "medium", "large"] * 2,
        "group": ["u", "v"] * 6,
    }
    return (
        mp.plot(data)
        .swarmplot(
            "dose",
            "response",
            group="group",
            dodge=0,
            semantics={
                "size": "grade",
                "size_kind": "categorical",
                "size_order": ["small", "reserved", "medium", "large"],
                "sizes": [4, 10],
            },
        )
        .labels(x="Dose", y="Response (a.u.)", title="Synthetic ordered size classes")
        .legend(location="outside right", title="Group / observed class")
        .size(6, 4)
    )
