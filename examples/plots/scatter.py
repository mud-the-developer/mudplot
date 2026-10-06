import mudplot as mp
import numpy as np

rng = np.random.default_rng(11)
x = rng.normal(size=90)
y = 0.65 * x + rng.normal(scale=0.7, size=len(x))
data = {"x": x, "y": y, "score": np.hypot(x, y)}
plot = (
    mp.plot(data)
    .scatter(
        "x", "y", c="score", colorbar=True, clabel="Distance", marker_size=5, alpha=0.8
    )
    .labels(x="Feature 1", y="Feature 2", title="Continuous colour")
    .size(4.5, 3.2)
)
