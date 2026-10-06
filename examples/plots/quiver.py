import mudplot as mp
import numpy as np

x, y = np.meshgrid(np.linspace(-2, 2, 9), np.linspace(-2, 2, 9))
u, v = -y, x
data = {
    "x": x.ravel(),
    "y": y.ravel(),
    "u": u.ravel(),
    "v": v.ravel(),
    "speed": np.hypot(u, v).ravel(),
}
plot = (
    mp.plot(data)
    .quiver(
        "x",
        "y",
        "u",
        "v",
        c="speed",
        colorbar=True,
        clabel="Speed",
        scale=8,
        width=0.007,
    )
    .labels(x="x", y="y", title="Rotational vector field")
    .size(4.5, 3.5)
)
