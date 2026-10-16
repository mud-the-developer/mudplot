import mudplot as mp
import numpy as np

rng = np.random.default_rng(41)
cloud = rng.multivariate_normal([0, 0], [[1, 0.65], [0.65, 0.8]], size=160)
data = {"x": cloud[:, 0], "y": cloud[:, 1], "weight": rng.integers(1, 5, len(cloud))}
plot = (
    mp.plot(data)
    .kde2d(
        "x",
        "y",
        weights="weight",
        gridsize=61,
        levels=[0.5, 0.8, 0.95],
        fill=True,
        alpha=0.65,
        line_width=0.8,
        label="Weighted joint density",
    )
    .labels(x="Observed x", y="Observed y", title="Gaussian KDE / conditional grid HDR")
    .legend()
    .size(4.5, 3.2)
)
