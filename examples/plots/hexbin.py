import mudplot as mp
import numpy as np

rng = np.random.default_rng(13)
x = rng.normal(size=700)
data = {"x": x, "y": np.sin(x * 1.8) + rng.normal(scale=0.35, size=len(x))}
plot = (
    mp.plot(data)
    .hexbin("x", "y", gridsize=24, mincnt=1, colorbar=True, clabel="Count")
    .labels(x="x", y="y", title="Hexagonal binning")
    .size(4.5, 3.3)
)
