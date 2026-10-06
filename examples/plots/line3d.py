import mudplot as mp
import numpy as np

t = np.linspace(0, 5 * np.pi, 160)
data = {"x": np.cos(t), "y": np.sin(t), "z": t / (2 * np.pi)}
plot = (
    mp.plot(data)
    .projection3d()
    .line3d("x", "y", "z", line_width=2)
    .labels(x="x", y="y", title="Helical trajectory")
    .zlabel("z")
    .size(4.8, 3.8)
)
