"""Different local observations share only their numeric size domain."""

import mudplot as mp


def build_plot() -> mp.Plot:
    data = {
        "category": ["A"] * 5,
        "left": [1.0, None, 1.04, None, 1.08],
        "right": [None, 1.25, 1.29, 1.33, None],
        "mass": [0, 2, 5, 8, 10],
        "group": ["u", "v", "u", "v", "u"],
    }
    p = mp.plot(data).layout(1, 2).size(8, 4)
    for panel, value in enumerate(("left", "right")):
        p.swarmplot(
            "category",
            value,
            group="group",
            hue_order=["u", "v"],
            dodge=0,
            panel=panel,
            semantics={"size": "mass", "scale_id": "shared_mass", "sizes": [4, 10]},
        ).labels(x="Category", y="Response (a.u.)", title=value.title(), panel=panel)
    return p
