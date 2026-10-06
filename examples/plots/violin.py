import mudplot as mp
import numpy as np

rng = np.random.default_rng(6)
data = {
    "value": np.r_[
        rng.normal(0, 0.7, 100), rng.normal(1.0, 0.45, 100), rng.normal(1.8, 0.9, 100)
    ],
    "group": np.repeat(["A", "B", "C"], 100),
}
plot = (
    mp.plot(data)
    .violin("value", group="group")
    .labels(y="Value", title="Grouped violin plot")
    .size(4.5, 3.2)
)
