import mudplot as mp
import numpy as np

rng = np.random.default_rng(16)
xyz = rng.normal(size=(90, 3))
data = {
    "x": xyz[:, 0],
    "y": xyz[:, 1],
    "z": xyz[:, 2],
    "radius": np.linalg.norm(xyz, axis=1),
}
plot = (
    mp.plot(data)
    .projection3d()
    .scatter3d(
        "x",
        "y",
        "z",
        c="radius",
        colorbar=True,
        clabel="Radius",
        marker_size=4,
        alpha=0.8,
    )
    .labels(x="x", y="y", title="3-D point cloud")
    .zlabel("z")
    .size(4.8, 3.8)
)
