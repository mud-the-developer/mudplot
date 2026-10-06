import mudplot as mp
import numpy as np

rng = np.random.default_rng(8)
data = {
    "value": np.r_[rng.normal(-0.5, 0.8, 120), rng.normal(0.9, 0.6, 120)],
    "group": ["Before"] * 120 + ["After"] * 120,
}
plot = (
    mp.plot(data)
    .kde("value", group="group", line_width=2)
    .labels(x="Value", y="Density", title="Gaussian KDE")
    .legend()
    .size(4.5, 3.2)
)
