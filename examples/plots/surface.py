import mudplot as mp
import numpy as np

x, y = np.meshgrid(np.linspace(-3, 3, 34), np.linspace(-3, 3, 34))
field = np.sinc(np.hypot(x, y))
plot = (
    mp.plot()
    .matrix("field", field)
    .projection3d()
    .surface("field", cmap_kind="diverging", clabel="Height")
    .labels(x="Column", y="Row", title="3-D surface")
    .zlabel("Height")
    .size(4.8, 3.8)
)
