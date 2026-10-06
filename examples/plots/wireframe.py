import mudplot as mp
import numpy as np

x, y = np.meshgrid(np.linspace(-2.5, 2.5, 28), np.linspace(-2.5, 2.5, 28))
field = np.cos(x) * np.sin(y) * np.exp(-(x**2 + y**2) / 12)
plot = (
    mp.plot()
    .matrix("field", field)
    .projection3d()
    .wireframe("field", color="#336699", alpha=0.8)
    .labels(x="Column", y="Row", title="3-D wireframe")
    .zlabel("Height")
    .size(4.8, 3.8)
)
