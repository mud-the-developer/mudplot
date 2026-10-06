import mudplot as mp
import numpy as np

rng = np.random.default_rng(12)
x = rng.normal(size=600)
data = {"x": x, "y": 0.7 * x + rng.normal(scale=0.65, size=len(x))}
plot = (
    mp.plot(data)
    .hist2d("x", "y", bins=22, colorbar=True, clabel="Count")
    .labels(x="x", y="y", title="Bivariate histogram")
    .size(4.5, 3.3)
)
