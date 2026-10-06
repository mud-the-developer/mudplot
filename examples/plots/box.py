import mudplot as mp
import numpy as np

rng = np.random.default_rng(5)
data = {
    "value": np.r_[
        rng.normal(0, 1, 70), rng.normal(0.8, 0.7, 70), rng.normal(1.5, 1.15, 70)
    ],
    "group": np.repeat(["A", "B", "C"], 70),
}
plot = (
    mp.plot(data)
    .box("value", group="group")
    .labels(y="Value", title="Grouped box plot")
    .size(4.5, 3.2)
)
